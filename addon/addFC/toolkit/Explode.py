# addFC; additional tools for FreeCAD
#
# Copyright 2024-2026 Golodnikov Sergey
#
# This addon is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 2.1
# of the License, or (at your option) any later version.
#
# This addon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this addon. If not, see https://www.gnu.org/licenses
#
# SPDX-License-Identifier: LGPL-2.1-or-later


from PySide import QtGui, QtCore
import FreeCAD
import os
import re
import time

from Data import video_pref_std
from Other import video_export_settings, video_make
import Logger
import Preference as P

if P.afc_additions['numpy'][0]:
    import numpy as np
else:
    np = None


ad = FreeCAD.ActiveDocument

w = FreeCAD.Gui.PySideUic.loadUi(os.path.join(
    os.path.normpath(os.path.dirname(__file__)), 'Explode.ui'))

storage = None
explosion = {}
freeze = False
frame = 1

pref_background = ''
pref_export_storyboard = ''
pref_height = ''
pref_image_format = ''
pref_width = ''

PATTERN = re.compile('[0-9]+$')
CCS_STR = 'User parameter:BaseApp/Preferences/View'


# ------------------------------------------------------------------------------


def obj_get(doc: str, name: str):
    return FreeCAD.getDocument(doc).getObject(name)


def ccs_get() -> bool:
    return FreeCAD.ParamGet(CCS_STR).GetBool('CornerCoordSystem')


def ccs_set(state: bool):
    FreeCAD.ParamGet(CCS_STR).SetBool('CornerCoordSystem', state)


def pref_refresh():
    video_pref = P.load_pref(P.PATH_VIDEO, video_pref_std)
    global pref_background
    global pref_export_storyboard
    global pref_height
    global pref_image_format
    global pref_width
    pref_background = video_pref['background']
    pref_export_storyboard = video_pref['export_storyboard']
    pref_height = video_pref['height']
    pref_image_format = video_pref['image_format']
    pref_width = video_pref['width']


def color_convert(hex: str):
    rgb = tuple(int(hex.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
    linear = tuple(i / 255 for i in rgb)
    return rgb, linear


def placement_save(obj):
    exp, base_obj = [], None
    for i in obj.ExpressionEngine:
        if 'Placement' in i[0]:
            # saving and cleaning expressions:
            exp.append((i[0], i[1]))
            obj.setExpression(i[0], None)
    if 'BaseObject' in obj.PropertiesList:  # fasteners?
        # save and clean:
        base_obj = base_object_get(obj.BaseObject)
        obj.BaseObject = None
    p_base = (
        obj.Placement.Base.x,
        obj.Placement.Base.y,
        obj.Placement.Base.z,
    )
    return exp, base_obj, p_base, obj.Placement.Rotation.getYawPitchRoll()


def placement_load(placement) -> FreeCAD.Placement:
    p = FreeCAD.Placement()
    p.Base = placement[0]
    p.Rotation.setYawPitchRoll(*placement[1])
    return p


def base_object_get(BaseObject) -> tuple | None:
    if BaseObject is not None:
        return (BaseObject[0].Name, BaseObject[1])
    else:
        return None


def base_object_set(baseObject: tuple) -> tuple | None:
    try:
        return (ad.getObject(baseObject[0]), baseObject[1])
    except BaseException as e:
        Logger.error(str(e))
        return None


def fuse_combine(fuse):
    obj = obj_get(fuse['doc'], fuse['name'])
    obj.Placement = placement_load(fuse['start'])
    for i in fuse['expressions']:
        obj.setExpression(i[0], i[1])
    if 'BaseObject' in obj.PropertiesList:
        if fuse['baseObject'] is not None:
            baseObject = base_object_set(fuse['baseObject'])
            if baseObject is not None:
                obj.BaseObject = baseObject


def fuse_explode(obj, finish):
    for i in obj.ExpressionEngine:
        if 'Placement' in i[0]:
            obj.setExpression(i[0], None)
    if 'BaseObject' in obj.PropertiesList:
        obj.BaseObject = None
    obj.Placement = placement_load(finish)


# ------------------------------------------------------------------------------


def dialog():

    if not P.afc_additions['ffmpeg'][0]:
        w.error.setText('FFmpeg is not available!')
        w.animationExport.setEnabled(False)
        w.exportSettings.setEnabled(False)

    if not P.afc_additions['numpy'][0]:
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

    def color_set(color: tuple | list):
        color = QtGui.QColor(*color).name()
        w.guidesColor.setText(color)
        w.guidesColor.setStyleSheet('QPushButton {color:' + str(color) + '}')

    def color_get():
        color = QtGui.QColorDialog.getColor()
        if color.isValid():
            color_set(color.getRgb()[:-1])
    w.guidesColor.clicked.connect(color_get)

    model = QtGui.QStandardItemModel()
    w.groups.setModel(model)

    w.groupSelection.addItems(selection_styles)
    w.guidesStyle.addItems(guide_styles)
    w.guidesStyle.setCurrentText('Dashed')
    color_set((170, 0, 0))

    w.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    w.show()

    def selection_style(select):
        if select == 'None':
            FreeCAD.Gui.Selection.clearSelection()
            return
        target = w.target.text()
        if target == '':
            return
        global explosion
        if target not in explosion:  # error?
            return
        group = explosion[target]
        for i in group['fuses']:
            obj_get(i['doc'], i['name']).ViewObject.SelectionStyle = select
            for j in i['selection'][1]:
                FreeCAD.Gui.Selection.addSelection(
                    ad.Name, i['selection'][0], j)
    w.groupSelection.currentTextChanged.connect(selection_style)

    def update_placement(position, rotation, silent: bool):
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

    # -------------- #
    # adding a group #
    # -------------- #

    def group_add():
        title = w.groupTitle.text().strip()
        if title == '':
            return
        global explosion
        if title in explosion:
            w.groupTitle.setText(title + ' (duplicate)')
            return
        update_placement((0, 0, 0), (0, 0, 0), True)

        selection = FreeCAD.Gui.Selection.getSelectionEx('', 0)
        if len(selection) == 0:
            Logger.warning(
                'To create a group, you need to select the elements...')
            return

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
                p = placement_save(i)  # (exp, (base_obj), p_base, ypr)
                group['fuses'].append({
                    'doc': i.Document.Name,
                    'name': i.Name,
                    'tree': tree,
                    'selection': (
                        selection[0].ObjectName,
                        selection[0].SubElementNames,
                    ),
                    'expressions': p[0],
                    'baseObject': p[1],
                    'start': p[2:],
                    'finish': p[2:],
                    'keyframes': [p[2:],],
                    'line': '',
                })

            except BaseException as e:
                Logger.warning(str(e))
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
                PATTERN,
                lambda x: f'{str(int(x.group())+1).zfill(len(x.group()))}',
                title)
            w.groupTitle.setText(title)
        except BaseException:
            pass

    w.groupAdd.clicked.connect(group_add)

    # ---------------- #
    # deleting a group #
    # ---------------- #

    def group_remove():
        indexes = w.groups.selectedIndexes()
        if len(indexes) < 1:
            return
        target = w.groups.model().itemFromIndex(indexes[0])
        global explosion
        if target.text() not in explosion:  # error?
            return
        update_placement((0, 0, 0), (0, 0, 0), True)
        del explosion[target.text()]
        model.clear()
        global storage
        if storage is not None:
            if storage.Storage is not None:
                for i in explosion:
                    model.appendRow(QtGui.QStandardItem(i))
    w.groupRemove.clicked.connect(group_remove)

    # ----------- #
    # group order #
    # ----------- #

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

    # --------------- #
    # group selection #
    # --------------- #

    def group_select(item, select: bool = True):
        target = model.index(item.row(), item.column()).data()
        w.target.setText(target)
        global explosion
        if target not in explosion:  # error?
            return

        FreeCAD.Gui.Selection.clearSelection()
        group = explosion[target]
        if select:
            if w.groupSelection.currentText() != 'None':
                for i in group['fuses']:
                    for j in i['selection'][1]:
                        FreeCAD.Gui.Selection.addSelection(
                            ad.Name, i['selection'][0], j)
        if group['exploded']:
            update_placement(
                group['placement'][0], group['placement'][1], True)
        else:
            update_placement(
                (0, 0, 0), (0, 0, 0), True)

        # get guides:
        w.guidesStyle.setCurrentText(group['guides']['style'])
        color_set(group['guides']['color'][0])  # rgb
        w.guidesWidth.setValue(group['guides']['width'])
        w.guidesSize.setValue(group['guides']['size'])

        # get animation:
        w.animationKeys.setText(
            f"Key frames: {group['animation']['keyframes']}")
        w.animationStep.setValue(group['animation']['step'])
        w.animationSplit.setChecked(group['animation']['split'])
        w.animationGuides.setChecked(group['animation']['guides'])

    w.groups.doubleClicked.connect(group_select)

    # -------------- #
    # moving a group #
    # -------------- #

    def group_moving():
        global freeze
        if freeze:
            return
        target = w.target.text()
        if target == '':
            return
        global explosion
        if target not in explosion:  # error?
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
            obj_get(i['doc'], i['name']).Placement.Base = start.Base + position
            r = start.Rotation.multiply(rotation)
            obj_get(i['doc'], i['name']).Placement.Rotation = r
            i['finish'] = placement_save(obj_get(i['doc'], i['name']))[2:]

    w.positionX.valueChanged.connect(group_moving)
    w.positionY.valueChanged.connect(group_moving)
    w.positionZ.valueChanged.connect(group_moving)
    w.rotationX.valueChanged.connect(group_moving)
    w.rotationY.valueChanged.connect(group_moving)
    w.rotationZ.valueChanged.connect(group_moving)

    # ------------------------ #
    # combine & explode: group #
    # ------------------------ #

    def group_combine():
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
            fuse_combine(i)
        group['exploded'] = False
        ad.recompute()
    w.groupCombine.clicked.connect(group_combine)

    def group_explode():
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
            obj = obj_get(i['doc'], i['name'])
            fuse_explode(obj, i['finish'])
            if i['line'] != '':
                line = ad.getObject(i['line'])
                if line is None:
                    i['line'] = ''
                    continue
        group['exploded'] = True
        ad.recompute()
    w.groupExplode.clicked.connect(group_explode)

    # ---------------------- #
    # combine & explode: all #
    # ---------------------- #

    def combine_all():
        for index in range(model.rowCount()):
            w.target.setText(model.item(index).text())
            group_combine()
        w.target.setText('...')
    w.combineAll.clicked.connect(combine_all)

    def explode_all():
        for index in range(model.rowCount()):
            w.target.setText(model.item(index).text())
            group_explode()
        w.target.setText('...')
    w.explodeAll.clicked.connect(explode_all)

    # ------ #
    # guides #
    # ------ #

    def guides_remove() -> bool:
        target = w.target.text()
        global explosion
        if target not in explosion:  # error?
            return False
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

    def guide_position(fuse) -> None | tuple:
        start = list(fuse['start'][0])
        finish = list(obj_get(fuse['doc'], fuse['name']).Placement.Base)
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
        # todo: need to think about this...
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
        # result:
        return uno, dos

    def guides_create():
        target = w.target.text()
        global explosion
        if target not in explosion:  # error?
            return
        if guides_remove():
            time.sleep(0.2)
            FreeCAD.Gui.updateGui()

        d = ad.addObject('App::DocumentObjectGroup', f'Guides_{target}')
        global storage
        d.adjustRelativeLinks(storage)
        if storage is not None:
            storage.addObject(d)

        group = explosion[target]
        group['guides']['style'] = w.guidesStyle.currentText()
        group['guides']['color'] = color_convert(w.guidesColor.text())
        group['guides']['width'] = w.guidesWidth.value()
        group['guides']['size'] = w.guidesSize.value()

        for i in group['fuses']:
            position = guide_position(i)
            if position is None:
                return
            uno, dos = position[0], position[1]
            i['line'] = f"Line_{i['name']}"
            line = ad.addObject('Part::Line', i['line'])
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

    # --------- #
    # animation #
    # --------- #

    def animation_clear():
        target = w.target.text()
        if target == '':
            return
        global explosion
        if target not in explosion:  # error?
            return
        group = explosion[target]
        for i in group['fuses']:
            i['keyframes'].clear()
        group['animation']['keyframes'] = 0
        w.animationKeys.setText(
            f"Key frames: {group['animation']['keyframes']}")
    w.animationClear.clicked.connect(animation_clear)

    def animation_add():
        target = w.target.text()
        global explosion
        if target not in explosion:  # error?
            return
        group = explosion[target]
        for i in group['fuses']:
            i['keyframes'].append(
                placement_save(obj_get(i['doc'], i['name']))[2:])
        group['animation']['step'] = w.animationStep.value()
        group['animation']['split'] = w.animationSplit.isChecked()
        group['animation']['guides'] = w.animationGuides.isChecked()
        group['animation']['keyframes'] += 1
        w.animationKeys.setText(
            f"Key frames: {group['animation']['keyframes']}")
    w.animationAddKey.clicked.connect(animation_add)

    def animation_play(single: bool = True):
        target = w.target.text()
        global explosion
        if target not in explosion or np is None:  # error
            return

        FreeCAD.Gui.Selection.clearSelection()
        reverse = w.animationReverse.isChecked()
        fit = w.animationFit.isChecked()
        export = w.animationExport.isChecked()

        w.animate.setEnabled(False)
        w.animationReverse.setEnabled(False)
        w.animationExport.setEnabled(False)
        w.exportSettings.setEnabled(False)
        if export:
            w.animationStatus.setText('... export')
        else:
            w.animationStatus.setText('... playback')

        # def update_line(line: str, entity):
        #     guides = ad.getObject(group['guides']['title'])
        #     if guides is not None:
        #         i = ad.getObject(line)
        #         i.Visibility = True
        #         if i.X1 != entity.Placement.Base.x:
        #             i.X2 = entity.Placement.Base.x
        #         if i.Y1 != entity.Placement.Base.y:
        #             i.Y2 = entity.Placement.Base.y
        #         if i.Z1 != entity.Placement.Base.z:
        #             i.Z2 = entity.Placement.Base.z

        def update_line(fuse):
            guides = ad.getObject(group['guides']['title'])
            if guides is not None:
                guide = ad.getObject(fuse['line'])
                guide.Visibility = True
                # todo: is it working?
                position = guide_position(fuse)
                if position is None:
                    return
                dos = position[1]
                if guide.X1 != dos[0]:
                    guide.X2 = dos[0]
                if guide.Y1 != dos[1]:
                    guide.Y2 = dos[1]
                if guide.Z1 != dos[2]:
                    guide.Z2 = dos[2]

        group = explosion[target]

        global frame  # frame counter

        av = FreeCAD.Gui.activeDocument().activeView()

        # freeze camera animation temporarily:
        animations = FreeCAD.ParamGet(
            'User parameter:BaseApp/Preferences/View').GetBool(
            'UseNavigationAnimations')
        FreeCAD.ParamGet(
            'User parameter:BaseApp/Preferences/View').SetBool(
            'UseNavigationAnimations', False)

        if single:
            group['animation']['step'] = w.animationStep.value()
            group['animation']['split'] = w.animationSplit.isChecked()
            group['animation']['guides'] = w.animationGuides.isChecked()
            if export:
                frame = 1

        def shot():
            file = str(frame).rjust(6, '0') + pref_image_format
            av.saveImage(
                os.path.join(pref_export_storyboard, file),
                pref_width,
                pref_height,
                pref_background)

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
                    entity = obj_get(i['doc'], i['name'])
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
                                update_line(i)
                            FreeCAD.Gui.updateGui()
                            if fit:
                                FreeCAD.Gui.SendMsgToActiveView('ViewFit')
                            if export:
                                shot()
                                frame += 1
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
                        entity = obj_get(k['doc'], k['name'])
                        entity.Placement = entity.Placement.slerp(p, j)
                        # compare:
                        equal = entity.Placement.Base.isEqual(
                            p.Base, 0.1)
                        same = entity.Placement.Rotation.isSame(
                            p.Rotation, 0.000001)
                        # display:
                        if not equal or not same:
                            if group['animation']['guides']:
                                update_line(k)
                            FreeCAD.Gui.updateGui()
                            if fit:
                                FreeCAD.Gui.SendMsgToActiveView('ViewFit')
                            if export:
                                shot()
                                frame += 1
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

        ad.recompute()

        FreeCAD.ParamGet(
            'User parameter:BaseApp/Preferences/View').SetBool(
            'UseNavigationAnimations', animations)

        if single and export:
            video_make(ad.Name, ' - ' + target)

        w.animate.setEnabled(True)
        w.animationReverse.setEnabled(True)
        w.animationReverse.setChecked(reverse)
        if P.afc_additions['ffmpeg'][0]:
            w.animationExport.setEnabled(True)
            w.animationExport.setChecked(export)
            w.exportSettings.setEnabled(True)
        w.animationStatus.setText('...')

    def animation_prepare():
        pref_refresh()
        export = w.animationExport.isChecked()
        if export and not os.path.exists(pref_export_storyboard):
            os.makedirs(pref_export_storyboard)

    def animation_play_wrapper(single: bool):
        if single:
            ccs = ccs_get()
            ccs_set(False)
            animation_prepare()
        animation_play(single)
        if single:
            ccs_set(ccs)
    w.animate.clicked.connect(lambda: animation_play_wrapper(True))

    def animate_all():
        global frame
        frame, order = 1, []
        export = w.animationExport.isChecked()
        for index in range(model.rowCount()):
            order.append(model.item(index).text())
        if w.animationReverse.isChecked():
            explode_all()
            order.reverse()
        else:
            combine_all()
        ccs = ccs_get()
        ccs_set(False)
        animation_prepare()
        for i in order:
            w.target.setText(i)
            animation_play_wrapper(False)
        ccs_set(ccs)
        w.target.setText('...')
        if export:
            video_make(ad.Name, '')
    w.animateAll.clicked.connect(animate_all)

    # ---- #
    # save #
    # ---- #

    def save():
        global storage
        global explosion
        db = {}
        for index in range(model.rowCount()):
            title = model.item(index).text()
            db[title] = explosion[title]
        if storage is not None:
            storage.Storage = db
        ad.recompute()

    # --------------- #
    # export settings #
    # --------------- #

    w.exportSettings.clicked.connect(video_export_settings)


dialog()
