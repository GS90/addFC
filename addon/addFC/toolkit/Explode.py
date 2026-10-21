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


from PySide import QtCore, QtGui
import FreeCAD
import os
import re
import time

from addon.addFC import Logger, Preference as P
from addon.addFC.Data import video_pref_std
from addon.addFC.Other import video_export_settings, video_make

if P.afc_additions['numpy'][0]:
    import numpy as np
else:
    np = None


PATTERN = re.compile('[0-9]+$')
CCS_STR = 'User parameter:BaseApp/Preferences/View'


# -----------------------------------------------------------------------------


def obj_get(doc: str, name: str):
    return FreeCAD.getDocument(doc).getObject(name)


def ccs_get() -> bool:
    return FreeCAD.ParamGet(CCS_STR).GetBool('CornerCoordSystem')


def ccs_set(state: bool):
    FreeCAD.ParamGet(CCS_STR).SetBool('CornerCoordSystem', state)


def color_convert(hex: str):
    rgb = tuple(int(hex.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
    linear = tuple(i / 255 for i in rgb)
    return rgb, linear


def placement_save(obj):
    exp, base_obj = [], None
    for i in obj.ExpressionEngine:
        if 'Placement' in i[0]:
            exp.append((i[0], i[1]))
            obj.setExpression(i[0], None)
    if 'BaseObject' in obj.PropertiesList:
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
        return (FreeCAD.ActiveDocument.getObject(baseObject[0]), baseObject[1])
    except Exception as err:
        Logger.error(str(err))
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


# -----------------------------------------------------------------------------


class ExplodeDialog:

    def __init__(self, panel):
        self.ad = FreeCAD.ActiveDocument

        self.w = FreeCAD.Gui.PySideUic.loadUi(os.path.join(
            os.path.normpath(os.path.dirname(__file__)), 'Explode.ui'))

        self.storage = None
        self.explosion = {}
        self.freeze = False
        self.frame = 1

        self.pref_background = ''
        self.pref_export_storyboard = ''
        self.pref_height = ''
        self.pref_image_format = ''
        self.pref_width = ''

        self.model = QtGui.QStandardItemModel()
        self.w.groups.setModel(self.model)

        # -----------------
        # panel preparation
        # -----------------

        if not P.afc_additions['ffmpeg'][0]:
            self.w.error.setText('FFmpeg is not available!')
            self.w.animationExport.setEnabled(False)
            self.w.exportSettings.setEnabled(False)

        if not P.afc_additions['numpy'][0]:
            self.w.error.setText('NumPy is not available!')
            self.w.animate.setEnabled(False)
            self.w.animateAll.setEnabled(False)

        selection_styles = ('Shape', 'BoundBox', 'None')

        guide_styles = (
            'Solid',
            'Dashed',
            'Dotted',
            'Dashdot',
        )

        self.w.groupSelection.addItems(selection_styles)
        self.w.guidesStyle.addItems(guide_styles)
        self.w.guidesStyle.setCurrentText('Dashed')
        self.color_set((170, 0, 0))

        # -------
        # signals
        # -------

        self.w.guidesColor.clicked.connect(self.color_get)
        self.w.groupSelection.currentTextChanged.connect(
            self.selection_style)

        self.w.groupAdd.clicked.connect(self.group_add)
        self.w.groupRemove.clicked.connect(self.group_remove)
        self.w.groupDown.clicked.connect(self.group_down)
        self.w.groupUp.clicked.connect(self.group_up)

        # rename: double-click; activate the group: right-click
        self.rename_item = None
        self.rename_old = ''
        self.w.groups.doubleClicked.connect(self.group_rename_ready)
        self.model.itemChanged.connect(self.group_rename)
        self.w.groups.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.w.groups.customContextMenuRequested.connect(
            self.group_active)

        # movements
        self.w.positionX.valueChanged.connect(self.group_moving)
        self.w.positionY.valueChanged.connect(self.group_moving)
        self.w.positionZ.valueChanged.connect(self.group_moving)
        self.w.rotationX.valueChanged.connect(self.group_moving)
        self.w.rotationY.valueChanged.connect(self.group_moving)
        self.w.rotationZ.valueChanged.connect(self.group_moving)

        # combine & explode
        self.w.groupCombine.clicked.connect(self.group_combine)
        self.w.groupExplode.clicked.connect(self.group_explode)
        self.w.combineAll.clicked.connect(self.combine_all)
        self.w.explodeAll.clicked.connect(self.explode_all)

        # guides
        self.w.guidesRemove.clicked.connect(self.guides_remove)
        self.w.guidesCreate.clicked.connect(self.guides_create)

        # animation
        self.w.animationClear.clicked.connect(self.animation_clear)
        self.w.animationAddKey.clicked.connect(self.animation_add)
        self.w.animate.clicked.connect(
            lambda: self.animation_play_wrapper(True))
        self.w.animateAll.clicked.connect(self.animate_all)

        self.w.exportSettings.clicked.connect(video_export_settings)

        def toggle_panel(state):
            try:
                configuration = P.pref_configuration
                configuration['explode_panel'] = state
                P.save_pref(P.PATH_CONFIGURATION, configuration)
            except Exception as err:
                Logger.error(str(err))
        self.w.panelMode.toggled.connect(toggle_panel)

        # --------------
        # initialization
        # --------------

        p = P.pref_configuration.get('explode_panel')
        if p is not None:
            self.w.panelMode.setChecked(p)

        self.storage = self.ad.getObject('Explosion')
        if self.storage is None:
            self.storage = self.ad.addObject(
                'App::DocumentObjectGroup', 'Explosion')
        if 'Storage' not in self.storage.PropertiesList:
            self.storage.addProperty(
                'App::PropertyPythonObject', 'Storage', 'Base')
        if self.storage.Storage is not None:
            self.explosion = self.storage.Storage
            for i in self.explosion:
                self.model.appendRow(QtGui.QStandardItem(i))
        # invisibility in a tree:
        self.storage.ViewObject.ShowInTree = False

        self.form = self.w

    # -----------
    # preferences
    # -----------

    def pref_refresh(self):
        video_pref = P.load_pref(P.PATH_VIDEO, video_pref_std)
        self.pref_background = video_pref['background']
        self.pref_export_storyboard = video_pref['export_storyboard']
        self.pref_height = video_pref['height']
        self.pref_image_format = video_pref['image_format']
        self.pref_width = video_pref['width']

    # -------
    # helpers
    # -------

    def color_set(self, color: tuple | list):
        color = QtGui.QColor(*color).name()
        self.w.guidesColor.setText(color)
        self.w.guidesColor.setStyleSheet(
            'QPushButton {color:' + str(color) + '}')

    def color_get(self):
        color = QtGui.QColorDialog.getColor()
        if color.isValid():
            self.color_set(color.getRgb()[:-1])

    def update_placement(self, position, rotation, silent: bool):
        if silent:
            self.freeze = True
        self.w.positionX.setValue(position[0])
        self.w.positionY.setValue(position[1])
        self.w.positionZ.setValue(position[2])
        self.w.rotationX.setValue(rotation[0])
        self.w.rotationY.setValue(rotation[1])
        self.w.rotationZ.setValue(rotation[2])
        if silent:
            self.freeze = False

    # ----------------
    # group operations
    # ----------------

    def group_add(self):
        title = self.w.groupTitle.text().strip()
        if title == '':
            return
        if title in self.explosion:
            self.w.groupTitle.setText(title + ' (duplicate)')
            return
        self.update_placement((0, 0, 0), (0, 0, 0), True)

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
                'style': self.w.guidesStyle.currentText(),
                'color': color_convert(self.w.guidesColor.text()),
                'width': self.w.guidesWidth.value(),
                'size': self.w.guidesSize.value(),
                'lines': [],
            },
            'animation': {
                'keyframes': 0,
                'step': self.w.animationStep.value(),
                'split': self.w.animationSplit.isChecked(),
                'guides': self.w.animationGuides.isChecked(),
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
                    tree['ypr'].append(
                        so.Placement.Rotation.getYawPitchRoll())
                except Exception:
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
                    'baseObject': p[1],
                    'start': p[2:],
                    'finish': p[2:],
                    'keyframes': [p[2:], ],
                    'line': '',
                })

            except Exception as e:
                Logger.warning(str(e))
                continue

        if len(group['fuses']) == 0:
            return

        self.explosion[title] = group
        self.model.appendRow(QtGui.QStandardItem(title))
        self.w.target.setText(title)
        self.w.animationKeys.setText('Key frames: 0')
        self.save()

        self.w.groups.selectionModel().clearSelection()

        try:
            title = re.sub(
                PATTERN,
                lambda x: f'{str(int(x.group())+1).zfill(len(x.group()))}',
                title)
            self.w.groupTitle.setText(title)
        except Exception:
            pass

    def group_remove(self):
        indexes = self.w.groups.selectedIndexes()
        if len(indexes) < 1:
            return
        target = self.w.groups.model().itemFromIndex(indexes[0])
        if target.text() not in self.explosion:
            return
        self.update_placement((0, 0, 0), (0, 0, 0), True)
        del self.explosion[target.text()]
        self.model.clear()
        if self.storage is not None:
            if self.storage.Storage is not None:
                for i in self.explosion:
                    self.model.appendRow(QtGui.QStandardItem(i))
        self.save()

    def group_down(self):
        indexes = self.w.groups.selectedIndexes()
        if len(indexes) < 1:
            return
        row = indexes[0].row()
        if row > len(self.explosion) - 2:
            return
        item = self.model.takeItem(row)
        item_up = self.model.takeItem(row + 1)
        self.model.setItem(row + 1, item)
        self.model.setItem(row, item_up)
        self.w.groups.setCurrentIndex(item.index())
        self.save()

    def group_up(self):
        indexes = self.w.groups.selectedIndexes()
        if len(indexes) < 1:
            return
        row = indexes[0].row()
        if row == 0:
            return
        item = self.model.takeItem(row)
        item_down = self.model.takeItem(row - 1)
        self.model.setItem(row - 1, item)
        self.model.setItem(row, item_down)
        self.w.groups.setCurrentIndex(item.index())
        self.save()

    # ----

    def group_rename_ready(self, index):
        if not index.isValid():
            return
        item = self.model.itemFromIndex(index)
        if item is None or item.text() not in self.explosion:
            return
        self.rename_item = item
        self.rename_old = item.text()
        self.w.groups.edit(index)

    def group_rename(self, item):
        if self.rename_item is None or item is not self.rename_item:
            return
        old = self.rename_old
        self.rename_item = None
        self.rename_old = ''
        new = item.text().strip()
        if not new or new == old:
            if new != old:
                item.setText(old)
            return
        if new in self.explosion:
            Logger.warning(f'Rename failed: "{new}" already exists')
            item.setText(old)
            return
        self.explosion[new] = self.explosion.pop(old)
        if self.w.target.text() == old:
            self.w.target.setText(new)
        self.save()

    # ----

    def group_active(self, position):
        index = self.w.groups.indexAt(position)
        if not index.isValid():
            return
        self.w.groups.setCurrentIndex(index)
        self.group_select(index)

    def group_select(self, item, select: bool = True):
        target = self.model.index(item.row(), item.column()).data()
        self.w.target.setText(target)
        if target not in self.explosion:
            return

        FreeCAD.Gui.Selection.clearSelection()
        group = self.explosion[target]
        if select:
            if self.w.groupSelection.currentText() != 'None':
                for i in group['fuses']:
                    for j in i['selection'][1]:
                        FreeCAD.Gui.Selection.addSelection(
                            self.ad.Name, i['selection'][0], j)
        if group['exploded']:
            self.update_placement(
                group['placement'][0], group['placement'][1], True)
        else:
            self.update_placement(
                (0, 0, 0), (0, 0, 0), True)

        self.w.guidesStyle.setCurrentText(group['guides']['style'])
        self.color_set(group['guides']['color'][0])
        self.w.guidesWidth.setValue(group['guides']['width'])
        self.w.guidesSize.setValue(group['guides']['size'])

        self.w.animationKeys.setText(
            f"Key frames: {group['animation']['keyframes']}")
        self.w.animationStep.setValue(group['animation']['step'])
        self.w.animationSplit.setChecked(group['animation']['split'])
        self.w.animationGuides.setChecked(group['animation']['guides'])

    # ---------
    # movements
    # ---------

    def group_moving(self):
        if self.freeze:
            return
        target = self.w.target.text()
        if target == '':
            return
        if target not in self.explosion:
            return
        group = self.explosion[target]
        group['exploded'] = True
        group['placement'][0][0] = self.w.positionX.value()
        group['placement'][0][1] = self.w.positionY.value()
        group['placement'][0][2] = self.w.positionZ.value()
        group['placement'][1][0] = self.w.rotationX.value()
        group['placement'][1][1] = self.w.rotationY.value()
        group['placement'][1][2] = self.w.rotationZ.value()
        position = FreeCAD.Vector(
            group['placement'][0][0],
            group['placement'][0][1],
            group['placement'][0][2],
        )
        x = FreeCAD.Rotation(
            FreeCAD.Vector(1, 0, 0), group['placement'][1][0])
        y = FreeCAD.Rotation(
            FreeCAD.Vector(0, 1, 0), group['placement'][1][1])
        z = FreeCAD.Rotation(
            FreeCAD.Vector(0, 0, 1), group['placement'][1][2])
        rotation = x.multiply(y)
        rotation = rotation.multiply(z)
        for i in group['fuses']:
            obj = obj_get(i['doc'], i['name'])
            start = placement_load(i['start'])
            obj.Placement.Base = start.Base + position
            r = start.Rotation.multiply(rotation)
            obj.Placement.Rotation = r
            i['finish'] = [
                list(obj.Placement.Base),
                list(obj.Placement.Rotation.getYawPitchRoll()),
            ]

    # -----------------
    # combine & explode
    # -----------------

    def group_combine(self):
        target = self.w.target.text()
        if target == '':
            return
        if target not in self.explosion:
            return
        group = self.explosion[target]
        guides = self.ad.getObject(group['guides']['title'])
        if guides is not None:
            guides.Visibility = False
        self.update_placement((0, 0, 0), (0, 0, 0), True)
        for i in group['fuses']:
            fuse_combine(i)
        group['exploded'] = False
        self.ad.recompute()

    def group_explode(self):
        target = self.w.target.text()
        if target == '':
            return
        if target not in self.explosion:
            return
        group = self.explosion[target]
        if group['exploded']:
            return
        guides = self.ad.getObject(group['guides']['title'])
        if guides is not None:
            guides.Visibility = True
        self.update_placement(
            group['placement'][0], group['placement'][1], True)
        for i in group['fuses']:
            obj = obj_get(i['doc'], i['name'])
            fuse_explode(obj, i['finish'])
            if i['line'] != '':
                line = self.ad.getObject(i['line'])
                if line is None:
                    i['line'] = ''
                    continue
        group['exploded'] = True
        self.ad.recompute()

    def combine_all(self):
        for index in range(self.model.rowCount()):
            self.w.target.setText(self.model.item(index).text())
            self.group_combine()
        self.w.target.setText('...')

    def explode_all(self):
        for index in range(self.model.rowCount()):
            self.w.target.setText(self.model.item(index).text())
            self.group_explode()
        self.w.target.setText('...')

    # ------
    # guides
    # ------

    def guides_remove(self) -> bool:
        target = self.w.target.text()
        if target not in self.explosion:
            return False
        guides = self.ad.getObject(
            self.explosion[target]['guides']['title'])
        if guides is None:
            return False
        self.explosion[target]['guides']['lines'].clear()
        for i in guides.Group:
            self.ad.removeObject(i.Name)
            self.ad.recompute()
        time.sleep(0.2)
        self.ad.removeObject(guides.Name)
        self.ad.recompute()
        return True

    def guide_position(self, fuse) -> tuple[list, list] | None:
        start = list(fuse['start'][0])
        finish = list(obj_get(fuse['doc'], fuse['name']).Placement.Base)
        if start == finish:
            return
        uno = list(fuse['tree']['base'][:-1][-1])
        dos = list(fuse['tree']['base'][:-1][-1])
        ypr = (
            round(fuse['tree']['ypr'][:-1][-1][0]),
            round(fuse['tree']['ypr'][:-1][-1][1]),
            round(fuse['tree']['ypr'][:-1][-1][2]),
        )
        if ypr[0] == -180:
            start[0] = -start[0]
            start[1] = -start[1]
            finish[0] = -finish[0]
            finish[1] = -finish[1]
        uno[0] += start[0]
        uno[1] += start[1]
        uno[2] += start[2]
        dos[0] += finish[0]
        dos[1] += finish[1]
        dos[2] += finish[2]
        return uno, dos

    def guides_create(self):
        target = self.w.target.text()
        if target not in self.explosion:
            return
        if self.guides_remove():
            time.sleep(0.2)
            FreeCAD.Gui.updateGui()

        d = self.ad.addObject(
            'App::DocumentObjectGroup', f'Guides_{target}')
        d.adjustRelativeLinks(self.storage)
        if self.storage is not None:
            self.storage.addObject(d)

        group = self.explosion[target]
        group['guides']['style'] = self.w.guidesStyle.currentText()
        group['guides']['color'] = color_convert(
            self.w.guidesColor.text())
        group['guides']['width'] = self.w.guidesWidth.value()
        group['guides']['size'] = self.w.guidesSize.value()

        for i in group['fuses']:
            position = self.guide_position(i)
            if position is None:
                continue
            uno, dos = position[0], position[1]
            i['line'] = f"Line_{i['name']}"
            line = self.ad.addObject('Part::Line', i['line'])
            line.X1 = uno[0]
            line.Y1 = uno[1]
            line.Z1 = uno[2]
            line.X2 = dos[0]
            line.Y2 = dos[1]
            line.Z2 = dos[2]
            line.ViewObject.DrawStyle = group['guides']['style']
            line.ViewObject.LineColor = group['guides']['color'][1]
            line.ViewObject.PointColor = group['guides']['color'][1]
            line.ViewObject.LineWidth = group['guides']['width']
            line.ViewObject.PointSize = group['guides']['size']
            group['guides']['lines'].append(line.Name)
            line.adjustRelativeLinks(d)
            d.addObject(line)

        group['guides']['title'] = d.Name
        self.ad.recompute()

    # ---------
    # animation
    # ---------

    def animation_clear(self):
        target = self.w.target.text()
        if target == '':
            return
        if target not in self.explosion:
            return
        group = self.explosion[target]
        for i in group['fuses']:
            i['keyframes'].clear()
        group['animation']['keyframes'] = 0
        self.w.animationKeys.setText(
            f"Key frames: {group['animation']['keyframes']}")

    def animation_add(self):
        target = self.w.target.text()
        if target not in self.explosion:
            return
        group = self.explosion[target]
        for i in group['fuses']:
            i['keyframes'].append(
                placement_save(
                    obj_get(i['doc'], i['name']))[2:])
        group['animation']['step'] = self.w.animationStep.value()
        group['animation']['split'] = self.w.animationSplit.isChecked()
        group['animation']['guides'] = self.w.animationGuides.isChecked()
        group['animation']['keyframes'] += 1
        self.w.animationKeys.setText(
            f"Key frames: {group['animation']['keyframes']}")

    def animation_update_line(self, fuse):
        group = self.explosion[self.w.target.text()]
        guides = self.ad.getObject(group['guides']['title'])
        if guides is not None:
            guide = self.ad.getObject(fuse['line'])
            guide.Visibility = True
            position = self.guide_position(fuse)
            if position is None:
                return
            dos = position[1]
            if guide.X1 != dos[0]:
                guide.X2 = dos[0]
            if guide.Y1 != dos[1]:
                guide.Y2 = dos[1]
            if guide.Z1 != dos[2]:
                guide.Z2 = dos[2]

    def animation_play(self, single: bool = True):
        target = self.w.target.text()
        if target not in self.explosion or np is None:
            return

        group = self.explosion[target]
        if not group['fuses']:
            Logger.warning(f'Group "{target}": no fuses available')
            return

        FreeCAD.Gui.Selection.clearSelection()
        reverse = self.w.animationReverse.isChecked()
        fit = self.w.animationFit.isChecked()
        export = self.w.animationExport.isChecked()

        self.w.animate.setEnabled(False)
        self.w.animationReverse.setEnabled(False)
        self.w.animationExport.setEnabled(False)
        self.w.exportSettings.setEnabled(False)
        if export:
            self.w.animationStatus.setText('... export')
        else:
            self.w.animationStatus.setText('... playback')

        av = FreeCAD.Gui.activeDocument().activeView()

        animations = FreeCAD.ParamGet(
            CCS_STR).GetBool('UseNavigationAnimations')
        FreeCAD.ParamGet(
            CCS_STR).SetBool('UseNavigationAnimations', False)

        if single:
            group['animation']['step'] = self.w.animationStep.value()
            group['animation']['split'] = \
                self.w.animationSplit.isChecked()
            group['animation']['guides'] = \
                self.w.animationGuides.isChecked()
            if export:
                self.frame = 1

        def shot():
            file = str(self.frame).rjust(6, '0') + \
                self.pref_image_format
            av.saveImage(
                os.path.join(
                    self.pref_export_storyboard, file),
                self.pref_width,
                self.pref_height,
                self.pref_background)

        if reverse:
            self.group_explode()
            for i in group['fuses']:
                i['keyframes'].reverse()
        else:
            self.group_combine()

        if group['animation']['guides']:
            guides = self.ad.getObject(group['guides']['title'])
            if guides is not None:
                guides.Visibility = True
                for i in guides.Group:
                    i.Visibility = False

        step = round(group['animation']['step'] / 100000, 5)
        if step <= 0:
            step = 0.01
        result = np.arange(0.0, 1.0 + step, step)

        if group['animation']['split']:
            for i in group['fuses']:
                for j in i['keyframes']:
                    j = placement_load(j)
                    entity = obj_get(i['doc'], i['name'])
                    diff = True
                    for k in result:
                        if not diff:
                            break
                        entity.Placement = \
                            entity.Placement.sclerp(j, k)
                        equal = entity.Placement.Base.isEqual(
                            j.Base, 0.1)
                        same = entity.Placement.Rotation.isSame(
                            j.Rotation, 0.000001)
                        if not equal or not same:
                            if group['animation']['guides']:
                                self.animation_update_line(i)
                            FreeCAD.Gui.updateGui()
                            if fit:
                                FreeCAD.Gui.SendMsgToActiveView(
                                    'ViewFit')
                            if export:
                                shot()
                                self.frame += 1
                        else:
                            diff = False
        else:
            count = len(group['fuses'][0]['keyframes'])
            for i in range(count):
                done = [False] * len(group['fuses'])
                for j in result:
                    if all(done):
                        break
                    moved = False
                    for n, k in enumerate(group['fuses']):
                        if done[n] or i > len(k['keyframes']) - 1:
                            continue
                        p = placement_load(k['keyframes'][i])
                        entity = obj_get(k['doc'], k['name'])
                        entity.Placement = \
                            entity.Placement.slerp(p, j)
                        equal = entity.Placement.Base.isEqual(
                            p.Base, 0.1)
                        same = entity.Placement.Rotation.isSame(
                            p.Rotation, 0.000001)
                        if equal and same:
                            done[n] = True
                        else:
                            moved = True
                            if group['animation']['guides']:
                                self.animation_update_line(k)
                    if moved:                # один кадр на шаг, а не на fuse
                        FreeCAD.Gui.updateGui()
                        if fit:
                            FreeCAD.Gui.SendMsgToActiveView('ViewFit')
                        if export:
                            shot()
                            self.frame += 1

        if reverse:
            self.group_combine()
            group['exploded'] = False
            for i in group['fuses']:
                i['keyframes'].reverse()
        else:
            self.group_explode()
            group['exploded'] = True

        self.ad.recompute()

        FreeCAD.ParamGet(CCS_STR).SetBool(
            'UseNavigationAnimations', animations)

        if single and export:
            video_make(self.ad.Name, ' - ' + target)

        self.w.animate.setEnabled(True)
        self.w.animationReverse.setEnabled(True)
        self.w.animationReverse.setChecked(reverse)
        if P.afc_additions['ffmpeg'][0]:
            self.w.animationExport.setEnabled(True)
            self.w.animationExport.setChecked(export)
            self.w.exportSettings.setEnabled(True)
        self.w.animationStatus.setText('...')

    def animation_prepare(self):
        self.pref_refresh()
        export = self.w.animationExport.isChecked()
        if export and not os.path.exists(
                self.pref_export_storyboard):
            os.makedirs(self.pref_export_storyboard)

    def animation_play_wrapper(self, single: bool):
        if single:
            ccs = ccs_get()
            ccs_set(False)
            self.animation_prepare()
        self.animation_play(single)
        if single:
            ccs_set(ccs)

    def animate_all(self):
        self.frame, order = 1, []
        export = self.w.animationExport.isChecked()
        for index in range(self.model.rowCount()):
            order.append(self.model.item(index).text())
        if self.w.animationReverse.isChecked():
            self.explode_all()
            order.reverse()
        else:
            self.combine_all()
        ccs = ccs_get()
        ccs_set(False)
        self.animation_prepare()
        for i in order:
            self.w.target.setText(i)
            self.animation_play_wrapper(False)
        ccs_set(ccs)
        self.w.target.setText('...')
        if export:
            video_make(self.ad.Name, '')

    # ----
    # save
    # ----

    def save(self):
        db = {}
        for index in range(self.model.rowCount()):
            title = self.model.item(index).text()
            if title in self.explosion:
                db[title] = self.explosion[title]
        if self.storage is not None:
            self.storage.Storage = db
        self.ad.recompute()

    # ---------------
    # selection style
    # ---------------

    def selection_style(self, select):
        if select == 'None':
            FreeCAD.Gui.Selection.clearSelection()
            return
        target = self.w.target.text()
        if target == '':
            return
        if target not in self.explosion:
            return
        group = self.explosion[target]
        for i in group['fuses']:
            obj_get(i['doc'], i['name']).ViewObject.SelectionStyle = select
            for j in i['selection'][1]:
                FreeCAD.Gui.Selection.addSelection(
                    self.ad.Name, i['selection'][0], j)

# -----------------------------------------------------------------------------


panel = P.pref_configuration['explode_panel']

explode = ExplodeDialog(panel)
if panel:
    FreeCAD.Gui.Control.showDialog(explode)
else:
    explode.form.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    explode.form.show()
