# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


from PySide import QtGui, QtCore
import FreeCAD
import os
import re
import time


is_available_NP: bool = True

try:
    import numpy as np
except ImportError:
    is_available_NP = False


ad = FreeCAD.ActiveDocument

ui = os.path.join(os.path.dirname(__file__), 'addFC_Explode.ui')
w = FreeCAD.Gui.PySideUic.loadUi(ui)

storage = None
explosion = {}
freeze = False


def get(doc: str, name: str): return FreeCAD.getDocument(doc).getObject(name)


def dialog() -> None:

    if not is_available_NP:
        w.error.setText('NumPy is not available!')
        w.animate.setEnabled(False)
        w.animateAll.setEnabled(False)

    selection_styles = ('Shape', 'BoundBox', 'None')

    guide_styles = (
        'Solid',
        'Dashed',
        'Dotted',
        'Dashdot',
    )

    def color_set(color: tuple | list) -> None:
        color = QtGui.QColor(*color).name()
        w.guidesColor.setText(color)
        w.guidesColor.setStyleSheet('QPushButton {color:' + color + '}')

    def color_get() -> None:
        color = QtGui.QColorDialog.getColor()
        if color.isValid():
            color_set(color.getRgb()[:-1])
    w.guidesColor.clicked.connect(color_get)

    def color_convert(hex: str):
        rgb = tuple(int(hex.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
        linear = tuple(i / 255 for i in rgb)
        return rgb, linear

    def placement_save(obj):
        expressions = []
        for i in obj.ExpressionEngine:
            if 'Placement' in i[0]:
                # saving and cleaning expressions:
                expressions.append((i[0], i[1]))
                obj.setExpression(i[0], None)
        placement = (
            obj.Placement.Base.x,
            obj.Placement.Base.y,
            obj.Placement.Base.z,
        )
        return expressions, placement, obj.Placement.Rotation.getYawPitchRoll()

    def placement_load(placement) -> FreeCAD.Placement:
        p = FreeCAD.Placement()
        p.Base = placement[0]
        p.Rotation.setYawPitchRoll(*placement[1])
        return p

    def obj_combine(fuse) -> None:
        obj = get(fuse['doc'], fuse['name'])
        obj.Placement = placement_load(fuse['start'])
        for i in fuse['expressions']:
            obj.setExpression(i[0], i[1])

    def obj_explode(obj, finish) -> None:
        for i in obj.ExpressionEngine:
            if 'Placement' in i[0]:
                obj.setExpression(i[0], None)
        obj.Placement = placement_load(finish)

    model = QtGui.QStandardItemModel()
    w.groups.setModel(model)

    w.groupSelection.addItems(selection_styles)
    w.guidesStyle.addItems(guide_styles)
    w.guidesStyle.setCurrentText('Dashed')
    color_set((170, 0, 0))

    w.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    w.show()

    def selection_style(select) -> None:
        if select == 'None':
            FreeCAD.Gui.Selection.clearSelection()
            return
        target = w.target.text()
        if target == '':
            return
        global explosion
        if target not in explosion:
            return
        group = explosion[target]
        for i in group['fuses']:
            get(i['doc'], i['name']).ViewObject.SelectionStyle = select
            for j in i['selection'][1]:
                FreeCAD.Gui.Selection.addSelection(
                    ad.Name, i['selection'][0], j
                )
    w.groupSelection.currentTextChanged.connect(selection_style)

    def update_placement(position, rotation, silent: bool) -> None:
        if silent:
            global freeze
            freeze = True
        w.positionX.setValue(position[0])
        w.positionY.setValue(position[1])
        w.positionZ.setValue(position[2])
        w.rotationX.setValue(rotation[0])
        w.rotationY.setValue(rotation[1])
        w.rotationZ.setValue(rotation[2])
        if silent:
            freeze = False

    # initialization:
    global storage
    storage = ad.getObject('Explosion')
    if storage is None:
        storage = ad.addObject('App::DocumentObjectGroup', 'Explosion')
    if 'Storage' not in storage.PropertiesList:
        storage.addProperty('App::PropertyPythonObject', 'Storage', 'Base')
    if storage.Storage is not None:
        global explosion
        explosion = storage.Storage
        for i in explosion:
            model.appendRow(QtGui.QStandardItem(i))

    ##################
    # adding a group #
    ##################

    def group_add() -> None:
        title = w.groupTitle.text().strip()
        if title == '':
            return
        global explosion
        if title in explosion:
            w.groupTitle.setText(title + ' (duplicate)')
            return
        update_placement((0, 0, 0), (0, 0, 0), True)

        group = {
            'fuses': [],
            'placement': [[0, 0, 0], [0, 0, 0]],
            'guides': {
                'title': '',
                'style': w.guidesStyle.currentText(),
                'color': color_convert(w.guidesColor.text()),  # rgb, linear
                'width': w.guidesWidth.value(),
                'size': w.guidesSize.value(),
                'lines': [],
            },
            'animation': {
                'keyframes': 0,
                'step': w.animationStep.value(),
                'split': w.animationSplit.isChecked(),
                'guides': w.animationGuides.isChecked(),
            },
            'exploded': False,
        }

        selection = FreeCAD.Gui.Selection.getSelectionEx('', 0)
        if len(selection) == 0:
            return
        for s in selection[0].SubElementNames:
            sub = selection[0].Object.getSubObjectList(s)

            i = sub[-1]

            tree = {'base': [], 'ypr': []}
            for so in sub:
                try:
                    tree['base'].append(tuple(so.Placement.Base))
                    tree['ypr'].append(so.Placement.Rotation.getYawPitchRoll())
                except BaseException:
                    pass

            try:
                p = placement_save(i)
                group['fuses'].append({
                    'doc': i.Document.Name,
                    'name': i.Name,
                    'tree': tree,
                    'selection': (
                        selection[0].ObjectName,
                        selection[0].SubElementNames,
                    ),
                    'expressions': p[0],
                    'start': p[1:],
                    'finish': p[1:],
                    'keyframes': [p[1:],],
                    'line': '',
                })

            except BaseException as e:
                FreeCAD.Console.PrintWarning(str(e) + '\n')
                continue

        if len(group['fuses']) == 0:
            return

        explosion[title] = group
        model.appendRow(QtGui.QStandardItem(title))
        w.target.setText(title)
        w.animationKeys.setText('Key frames: 0')
        save()

        w.groups.selectionModel().clearSelection()

        try:
            title = re.sub(
                r'[0-9]+$',
                lambda x: f'{str(int(x.group())+1).zfill(len(x.group()))}',
                title)
            w.groupTitle.setText(title)
        except BaseException:
            pass

    w.groupAdd.clicked.connect(group_add)

    ####################
    # deleting a group #
    ####################

    def group_remove() -> None:
        indexes = w.groups.selectedIndexes()
        if len(indexes) < 1:
            return
        target = w.groups.model().itemFromIndex(indexes[0])
        global explosion
        if target.text() not in explosion:  # error
            return
        update_placement((0, 0, 0), (0, 0, 0), True)
        del explosion[target.text()]
        model.clear()
        global storage
        if storage.Storage is not None:
            for i in explosion:
                model.appendRow(QtGui.QStandardItem(i))
    w.groupRemove.clicked.connect(group_remove)

    ###############
    # group order #
    ###############

    def group_down():
        indexes = w.groups.selectedIndexes()
        if len(indexes) < 1:
            return
        row = indexes[0].row()
        global explosion
        if row > len(explosion) - 2:
            return
        item = model.takeItem(row)
        item_up = model.takeItem(row + 1)
        model.setItem(row + 1, item)
        model.setItem(row, item_up)
        w.groups.setCurrentIndex(item.index())
        save()
    w.groupDown.clicked.connect(group_down)

    def group_up():
        indexes = w.groups.selectedIndexes()
        if len(indexes) < 1:
            return
        row = indexes[0].row()
        if row == 0:
            return
        item = model.takeItem(row)
        item_down = model.takeItem(row - 1)
        model.setItem(row - 1, item)
        model.setItem(row, item_down)
        w.groups.setCurrentIndex(item.index())
        save()
    w.groupUp.clicked.connect(group_up)

    ###################
    # group selection #
    ###################

    def group_select(item, select: bool = True) -> None:
        target = model.index(item.row(), item.column()).data()
        w.target.setText(target)
        global explosion
        if target not in explosion:  # error
            return

        FreeCAD.Gui.Selection.clearSelection()
        group = explosion[target]
        if select:
            if w.groupSelection.currentText() != 'None':
                for i in group['fuses']:
                    for j in i['selection'][1]:
                        FreeCAD.Gui.Selection.addSelection(
                            ad.Name, i['selection'][0], j
                        )
        if group['exploded']:
            update_placement(
                group['placement'][0], group['placement'][1], True
            )
        else:
            update_placement((0, 0, 0), (0, 0, 0), True)

        # get guides:
        w.guidesStyle.setCurrentText(group['guides']['style'])
        color_set(group['guides']['color'][0])  # rgb
        w.guidesWidth.setValue(group['guides']['width'])
        w.guidesSize.setValue(group['guides']['size'])

        # get animation:
        w.animationKeys.setText(
            f"Key frames: {group['animation']['keyframes']}"
        )
        w.animationStep.setValue(group['animation']['step'])
        w.animationSplit.setChecked(group['animation']['split'])
        w.animationGuides.setChecked(group['animation']['guides'])

    w.groups.doubleClicked.connect(group_select)

    ##################
    # moving a group #
    ##################

    def group_moving() -> None:
        global freeze
        if freeze:
            return
        target = w.target.text()
        if target == '':
            return
        global explosion
        if target not in explosion:  # error
            return
        group = explosion[target]
        group['exploded'] = True
        # placement:
        group['placement'][0][0] = w.positionX.value()
        group['placement'][0][1] = w.positionY.value()
        group['placement'][0][2] = w.positionZ.value()
        group['placement'][1][0] = w.rotationX.value()
        group['placement'][1][1] = w.rotationY.value()
        group['placement'][1][2] = w.rotationZ.value()
        # position:
        position = FreeCAD.Vector(
            group['placement'][0][0],
            group['placement'][0][1],
            group['placement'][0][2],
        )
        # rotation:
        x = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), group['placement'][1][0])
        y = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), group['placement'][1][1])
        z = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), group['placement'][1][2])
        rotation = x.multiply(y)
        rotation = rotation.multiply(z)
        # moving:
        for i in group['fuses']:
            start = placement_load(i['start'])
            get(i['doc'], i['name']).Placement.Base = start.Base + position
            r = start.Rotation.multiply(rotation)
            get(i['doc'], i['name']).Placement.Rotation = r
            i['finish'] = placement_save(get(i['doc'], i['name']))[1:]

    w.positionX.valueChanged.connect(group_moving)
    w.positionY.valueChanged.connect(group_moving)
    w.positionZ.valueChanged.connect(group_moving)
    w.rotationX.valueChanged.connect(group_moving)
    w.rotationY.valueChanged.connect(group_moving)
    w.rotationZ.valueChanged.connect(group_moving)

    ############################
    # combine & explode: group #
    ############################

    def group_combine() -> None:
        target = w.target.text()
        if target == '':
            return
        global explosion
        if target not in explosion:  # error
            return
        group = explosion[target]
        guides = ad.getObject(group['guides']['title'])
        if guides is not None:
            guides.Visibility = False
        update_placement((0, 0, 0), (0, 0, 0), True)
        for i in group['fuses']:
            obj_combine(i)
        group['exploded'] = False
        ad.recompute()
    w.groupCombine.clicked.connect(group_combine)

    def group_explode() -> None:
        target = w.target.text()
        if target == '':
            return
        global explosion
        if target not in explosion:  # error
            return
        group = explosion[target]
        if group['exploded']:
            return
        guides = ad.getObject(group['guides']['title'])
        if guides is not None:
            guides.Visibility = True
        update_placement(group['placement'][0], group['placement'][1], True)
        for i in group['fuses']:
            entity = get(i['doc'], i['name'])
            obj_explode(entity, i['finish'])
            if i['line'] != '':
                line = ad.getObject(i['line'])
                if line is None:
                    i['line'] = ''
                    continue
                # TODO зачем это..?
                # line.X2 = entity.Placement.Base.x
                # line.Y2 = entity.Placement.Base.y
                # line.Z2 = entity.Placement.Base.z
        group['exploded'] = True
        ad.recompute()
        update_placement((0, 0, 0), (0, 0, 0), True)
    w.groupExplode.clicked.connect(group_explode)

    ##########################
    # combine & explode: all #
    ##########################

    def combine_all() -> None:
        for index in range(model.rowCount()):
            w.target.setText(model.item(index).text())
            group_combine()
        w.target.setText('...')
    w.combineAll.clicked.connect(combine_all)

    def explode_all() -> None:
        for index in range(model.rowCount()):
            w.target.setText(model.item(index).text())
            group_explode()
        w.target.setText('...')
    w.explodeAll.clicked.connect(explode_all)

    ##########
    # guides #
    ##########

    def guides_remove() -> bool:
        target = w.target.text()
        global explosion
        if target not in explosion:  # error
            return
        guides = ad.getObject(explosion[target]['guides']['title'])
        if guides is None:
            return False
        explosion[target]['guides']['lines'].clear()
        for i in guides.Group:
            ad.removeObject(i.Name)
            ad.recompute()
        time.sleep(0.2)
        ad.removeObject(guides.Name)
        ad.recompute()
        return True
    w.guidesRemove.clicked.connect(guides_remove)

    def guide_position(fuse) -> None:
        start = list(fuse['start'][0])
        finish = list(get(fuse['doc'], fuse['name']).Placement.Base)
        if start == finish:
            return
        # position-base:
        uno = list(fuse['tree']['base'][:-1][-1])
        dos = list(fuse['tree']['base'][:-1][-1])
        # yaw-pitch-roll:
        ypr = (
            round(fuse['tree']['ypr'][:-1][-1][0]),
            round(fuse['tree']['ypr'][:-1][-1][1]),
            round(fuse['tree']['ypr'][:-1][-1][2]),
        )

        # TODO what the fuck is this..?
        if ypr[0] == -180:
            start[0] = -start[0]    # X
            start[1] = -start[1]    # Y
            finish[0] = -finish[0]  # X
            finish[1] = -finish[1]  # Y

        # addition:
        uno[0] += start[0]   # X
        uno[1] += start[1]   # Y
        uno[2] += start[2]   # Z
        dos[0] += finish[0]  # X
        dos[1] += finish[1]  # Y
        dos[2] += finish[2]  # Z

        return uno, dos

    def guides_create() -> None:
        target = w.target.text()
        global explosion
        if target not in explosion:  # error
            return
        if guides_remove():
            time.sleep(0.2)
            FreeCAD.Gui.updateGui()

        d = ad.addObject('App::DocumentObjectGroup', f'Guides_{target}')
        global storage
        d.adjustRelativeLinks(storage)
        storage.addObject(d)

        group = explosion[target]
        group['guides']['style'] = w.guidesStyle.currentText()
        group['guides']['color'] = color_convert(w.guidesColor.text())
        group['guides']['width'] = w.guidesWidth.value()
        group['guides']['size'] = w.guidesSize.value()

        for i in group['fuses']:
            uno, dos = guide_position(i)
            i['line'] = f"Line_{i['name']}"
            line = FreeCAD.ActiveDocument.addObject('Part::Line', i['line'])
            # placement:
            line.X1 = uno[0]
            line.Y1 = uno[1]
            line.Z1 = uno[2]
            line.X2 = dos[0]
            line.Y2 = dos[1]
            line.Z2 = dos[2]
            # display:
            line.ViewObject.DrawStyle = group['guides']['style']
            line.ViewObject.LineColor = group['guides']['color'][1]
            line.ViewObject.PointColor = group['guides']['color'][1]
            line.ViewObject.LineWidth = group['guides']['width']
            line.ViewObject.PointSize = group['guides']['size']
            # add:
            group['guides']['lines'].append(line.Name)
            line.adjustRelativeLinks(d)
            d.addObject(line)

        group['guides']['title'] = d.Name
        ad.recompute()

    w.guidesCreate.clicked.connect(guides_create)

    #############
    # animation #
    #############

    def animation_clear() -> None:
        target = w.target.text()
        if target == '':
            return
        global explosion
        if target not in explosion:  # error
            return
        group = explosion[target]
        for i in group['fuses']:
            i['keyframes'].clear()
        group['animation']['keyframes'] = 0
        w.animationKeys.setText(
            f"Key frames: {group['animation']['keyframes']}"
        )
    w.animationClear.clicked.connect(animation_clear)

    def animation_add() -> None:
        target = w.target.text()
        global explosion
        if target not in explosion:  # error
            return
        group = explosion[target]
        for i in group['fuses']:
            i['keyframes'].append(placement_save(get(i['doc'], i['name']))[1:])
        group['animation']['step'] = w.animationStep.value()
        group['animation']['split'] = w.animationSplit.isChecked()
        group['animation']['guides'] = w.animationGuides.isChecked()
        group['animation']['keyframes'] += 1
        w.animationKeys.setText(
            f"Key frames: {group['animation']['keyframes']}"
        )
    w.animationAddKey.clicked.connect(animation_add)

    def animation_play(conservation: bool = True) -> None:
        target = w.target.text()
        global explosion
        if target not in explosion:  # error
            return

        FreeCAD.Gui.Selection.clearSelection()
        reverse = w.animationReverse.isChecked()
        fit = w.animationFit.isChecked()

        w.animate.setEnabled(False)
        w.animationReverse.setEnabled(False)
        w.animationStatus.setText('... animation')

        def update_line_old(line: str, entity) -> None:
            guides = ad.getObject(group['guides']['title'])
            if guides is not None:
                i = ad.getObject(line)
                i.Visibility = True
                # TODO так не работает..?
                if i.X1 != entity.Placement.Base.x:
                    i.X2 = entity.Placement.Base.x
                if i.Y1 != entity.Placement.Base.y:
                    i.Y2 = entity.Placement.Base.y
                if i.Z1 != entity.Placement.Base.z:
                    i.Z2 = entity.Placement.Base.z

        def update_line(fuse) -> None:
            guides = ad.getObject(group['guides']['title'])
            if guides is not None:
                guide = ad.getObject(fuse['line'])
                guide.Visibility = True
                _, dos = guide_position(fuse)
                if guide.X1 != dos[0]:
                    guide.X2 = dos[0]
                if guide.Y1 != dos[1]:
                    guide.Y2 = dos[1]
                if guide.Z1 != dos[2]:
                    guide.Z2 = dos[2]

        group = explosion[target]

        if conservation:
            group['animation']['step'] = w.animationStep.value()
            group['animation']['split'] = w.animationSplit.isChecked()
            group['animation']['guides'] = w.animationGuides.isChecked()

        if reverse:
            group_explode()
            for i in group['fuses']:
                i['keyframes'].reverse()
        else:
            group_combine()

        if group['animation']['guides']:
            guides = ad.getObject(group['guides']['title'])
            if guides is not None:
                guides.Visibility = True
                for i in guides.Group:
                    i.Visibility = False

        step = round(group['animation']['step'] / 100000, 5)

        if group['animation']['split']:
            for i in group['fuses']:
                for j in i['keyframes']:
                    j = placement_load(j)
                    entity = get(i['doc'], i['name'])
                    result = np.arange(0.0, 1.0 + step, step)
                    diff = True
                    for k in result:
                        if not diff:
                            break
                        entity.Placement = entity.Placement.sclerp(j, k)
                        # compare:
                        equal = entity.Placement.Base.isEqual(
                            j.Base, 0.1)
                        same = entity.Placement.Rotation.isSame(
                            j.Rotation, 0.000001)
                        # display:
                        if not equal or not same:
                            if group['animation']['guides']:
                                # update_line_old(i['line'], entity)
                                update_line(i)
                            FreeCAD.Gui.updateGui()
                            if fit:
                                FreeCAD.Gui.SendMsgToActiveView('ViewFit')
                        else:
                            diff = False
        else:
            count = len(group['fuses'][0]['keyframes'])
            for i in range(count):
                result = np.arange(0.0, 1.0 + step, step)
                diff = True
                for j in result:
                    if not diff:
                        break
                    for k in group['fuses']:
                        if i > len(k['keyframes']) - 1:
                            continue
                        p = placement_load(k['keyframes'][i])
                        entity = get(k['doc'], k['name'])
                        entity.Placement = entity.Placement.sclerp(p, j)
                        # compare:
                        equal = entity.Placement.Base.isEqual(
                            p.Base, 0.1)
                        same = entity.Placement.Rotation.isSame(
                            p.Rotation, 0.000001)
                        # display:
                        if not equal or not same:
                            if group['animation']['guides']:
                                # update_line_old(k['line'], entity)
                                update_line(k)
                            FreeCAD.Gui.updateGui()
                            if fit:
                                FreeCAD.Gui.SendMsgToActiveView('ViewFit')
                        else:
                            diff = False

        if reverse:
            group_combine()
            group['exploded'] = False
            for i in group['fuses']:
                i['keyframes'].reverse()
        else:
            group_explode()
            group['exploded'] = True

        w.animate.setEnabled(True)
        w.animationReverse.setEnabled(True)
        w.animationReverse.setChecked(reverse)
        w.animationStatus.setText('...')
        ad.recompute()

    w.animate.clicked.connect(lambda: animation_play(True))

    def animate_all() -> None:
        order = []
        for index in range(model.rowCount()):
            order.append(model.item(index).text())
        if w.animationReverse.isChecked():
            explode_all()
            order.reverse()
        else:
            combine_all()
        for i in order:
            w.target.setText(i)
            animation_play(False)
        w.target.setText('...')
    w.animateAll.clicked.connect(animate_all)

    ########
    # save #
    ########

    def save() -> None:
        global storage
        global explosion
        db = {}
        for index in range(model.rowCount()):
            title = model.item(index).text()
            db[title] = explosion[title]
        storage.Storage = db
        ad.recompute()


dialog()
