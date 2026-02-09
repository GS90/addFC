# addFC; additional tools for FreeCAD
#
# Copyright 2026 Golodnikov Sergey
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


from PySide import QtCore, QtGui, QtWidgets
import FreeCAD
import FreeCADGui as Gui

from addon.addFC import Logger, Preference as P


OFFSET_FROM_CURSOR = 10

P_STR_UNITS = 'User parameter:BaseApp/Preferences/Units'

OUTLINE = ('Sketcher::SketchObject', 'Part::Part2DObjectPython')


# ------------------------------------------------------------------------------


tools_all = [
    # other
    ('SelectLinked', 'Std_LinkSelectLinked', 'LinkSelect'),
    ('Transform', 'Std_TransformManip', 'Std_TransformManip'),
    # pd:sketch
    ('NewSketch', 'PartDesign_NewSketch', 'Sketcher_NewSketch'),
    ('EditSketch', 'Sketcher_EditSketch', 'Sketcher_EditSketch'),
    # binder
    # ('SSBinder', 'PartDesign_SubShapeBinder', 'PartDesign_SubShapeBinder'),
    # pd:uno
    ('Pad', 'PartDesign_Pad', 'PartDesign_Pad'),
    ('Pocket', 'PartDesign_Pocket', 'PartDesign_Pocket'),
    ('Hole', 'PartDesign_Hole', 'PartDesign_Hole'),
    # pd:dos
    ('Fillet', 'PartDesign_Fillet', 'PartDesign_Fillet'),
    ('Chamfer', 'PartDesign_Chamfer', 'PartDesign_Chamfer'),
    ('Draft', 'PartDesign_Draft', 'PartDesign_Draft'),
    ('Thickness', 'PartDesign_Thickness', 'PartDesign_Thickness'),
    # sm
    ('SM_Wall', 'SheetMetal_AddWall', 'SheetMetal_AddWall'),
    ('SM_Extrude', 'SheetMetal_Extrude', 'SheetMetal_Extrude'),
    ('SM_UU', 'SheetMetal_UnattendedUnfold', 'SheetMetal_UnfoldUnattended'),
]

tools_access = {
    'PartDesignWorkbench': {
        'Other': [
            'AlignTo',  # 1+
            'SelectLinked',
            'Transform',
        ],
        'Outline': [
            'EditSketch',  # exception
            'Pad',
            'Pocket',
            'Hole',
        ],
        'Edge': [
            'Fillet',
            'Chamfer',
            'SM_Wall',
        ],
        'Face': [
            'AlignTo',     # 1+
            'EditSketch',  # exception
            'NewSketch',
            # 'SSBinder',
            'Pad',
            'Pocket',
            'Draft',
            'Thickness',
            'SM_Extrude',
            'SM_UU',
        ],
    },
}

tools_control = {
    # pd:uno
    'Pad': (QtWidgets.QAbstractSpinBox, 'lengthEdit', 10),
    'Pocket': (QtWidgets.QAbstractSpinBox, 'lengthEdit', 5),
    # pd:dos
    'Fillet': (QtWidgets.QAbstractSpinBox, 'filletRadius', 1),
    'Chamfer': (QtWidgets.QAbstractSpinBox, 'chamferSize', 1),
    'Draft': (QtWidgets.QAbstractSpinBox, 'draftAngle', 1),
    'Thickness': (QtWidgets.QAbstractSpinBox, 'Value', 1),
    # sm
    'SM_Wall': (QtWidgets.QAbstractSpinBox, 'Length', 10),
    'SM_Extrude': (QtWidgets.QAbstractSpinBox, 'Length', 10),
}


def preparation():
    if int(P.FC_VERSION[0]) > 0:
        global tools_all
        i = ('AlignTo', 'Std_AlignToSelection', 'align-to-selection')
        tools_all.insert(0, i)


# ------------------------------------------------------------------------------


def generate_css(app_theme, hud_theme) -> tuple[str, str]:

    if hud_theme == 'Standard':
        border = '1px solid #646464'
        border_box = '1px solid #646464'
        border_radius = '0'
        border_radius_button = '0'
        padding_button = '2px'
        spin_box_radius = 'border-radius: 0;'
        css_apply = 'border: 1px solid #646464; border-left: none;'
    else:
        border = 'none'
        border_box = 'none'
        border_radius = '8px'
        border_radius_button = '6px'
        padding_button = '4px'
        spin_box_radius = (
            'border-radius: 0;'
            'border-top-left-radius: 6px;'
            'border-bottom-left-radius: 6px;'
        )
        css_apply = (
            'QToolButton {'
            'background-color: #a0a0a0;'
            'border-radius: 0;'
            'border-top-right-radius: 6px;'
            'border-bottom-right-radius: 6px;'
            '}'
            'QToolButton:hover {'
            'background-color: #828282;'
            '}'
        )

    css = (
        'QWidget#HUD {'
        'background-color: rgba(248, 248, 248, 120);'
        f'border-radius: {border_radius};'
        f'border: {border};'
        '}'
        'QToolButton {'
        'background: transparent;'
        f'border-radius: {border_radius_button};'
        'border: none;'
        f'padding: {padding_button};'
        '}'
        'QToolButton:hover {'
        'background-color: rgba(0, 0, 0, 60);'
        '}'
        'QDoubleSpinBox {'
        'background-color: rgba(248, 248, 248, 120);'
        f'{spin_box_radius}'
        f'border: {border_box};'
        'padding: 2px 4px;'
        '}'
        'QDoubleSpinBox:hover {'
        'background-color: #f0f0f0;'
        '}'
        'QDoubleSpinBox::up-button,'
        'QDoubleSpinBox::down-button {'
        'height: 0;'
        'margin: 0;'
        'padding: 0;'
        'width: 0;'
        '}'
        'QDoubleSpinBox::up-arrow,'
        'QDoubleSpinBox::down-arrow {'
        'height: 0;'
        'image: none;'
        'width: 0;'
        '}'
    )

    return css, css_apply


# ------------------------------------------------------------------------------


class SelectionObserverHUD:

    def addSelection(self, doc, obj, sub, pos):
        try:
            overlay.selection_add(doc, obj, sub, pos)
        except BaseException as err:
            Logger.error(str(err))
            Gui.Selection.removeObserver(self)

    def removeSelection(self, doc, obj, sub):
        try:
            overlay.selection_remove(doc, obj, sub)
        except BaseException as err:
            Logger.error(str(err))
            Gui.Selection.removeObserver(self)

    def clearSelection(self, doc):
        try:
            overlay.selection_clear()
        except BaseException as err:
            Logger.error(str(err))
            Gui.Selection.removeObserver(self)


# ------------------------------------------------------------------------------


class SmartHUD(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        preparation()

        app_theme = P.afc_theme['current']  # std, dark, light
        hud_theme = P.afc_theme['hud']      # Standard, Rounded

        _f = QtCore.Qt.FramelessWindowHint | QtCore.Qt.SubWindow
        self.setWindowFlags(_f)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        css, css_apply = generate_css(app_theme, hud_theme)
        self.setStyleSheet(css)

        self.container = QtWidgets.QWidget()
        self.container.setObjectName('HUD')

        # buttons
        self.b_layout = QtWidgets.QHBoxLayout()
        self.b_layout.setContentsMargins(2, 2, 2, 2)
        self.b_layout.setSpacing(0)
        self.b_widget = QtWidgets.QWidget()
        self.b_widget.setObjectName('HUD_buttons')
        self.b_widget.setLayout(self.b_layout)

        self.add_buttons()

        # control
        self.c_layout = QtWidgets.QHBoxLayout()
        self.c_layout.setContentsMargins(2, 2, 2, 2)
        self.c_layout.setSpacing(0)
        self.c_widget = QtWidgets.QWidget()
        self.c_widget.setObjectName('HUD_control')
        self.c_widget.setLayout(self.c_layout)
        self.c_widget.setVisible(False)

        # control: value
        self.spinbox = QtWidgets.QDoubleSpinBox()
        self.spinbox.setToolTip('Set the value')
        self.spinbox.setRange(0, 1000)
        self.spinbox.setValue(1)
        self.spinbox.setSingleStep(1)
        _d = FreeCAD.ParamGet(P_STR_UNITS).GetInt('Decimals')
        self.spinbox.setDecimals(_d)
        self.spinbox.setFixedHeight(25)
        self.spinbox.setFixedWidth(80)
        self.spinbox.valueChanged.connect(self.value_changed)
        self.c_layout.addWidget(self.spinbox)

        # control: apply
        self.apply = QtWidgets.QToolButton()
        self.apply.setText('OK')
        self.apply.setStyleSheet(css_apply)
        self.apply.setFixedHeight(25)
        self.apply.clicked.connect(self.value_apply)
        self.c_layout.addWidget(self.apply)

        # control: spacer
        self.c_layout.addStretch(1)

        # wrapper
        self.wrapper = QtWidgets.QVBoxLayout()
        self.wrapper.setContentsMargins(2, 2, 2, 2)
        self.wrapper.setSpacing(2)
        self.wrapper.addWidget(self.b_widget)
        self.wrapper.addWidget(self.c_widget)

        # building
        self.container.setLayout(self.wrapper)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.container)

        self.is_visible = False
        self.position_init = None
        self.position_current = None
        self.active_workbench = Gui.activeWorkbench().name()
        self.current_tool = None
        self.dialog = None
        self.sketch_profile = None

        self.max_distance_x = 400
        self.max_distance_y = 100

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_position)

        self.observer = SelectionObserverHUD()
        Gui.Selection.addObserver(self.observer)

        self.get_view()

    # --------------------------------------------------------------------------

    def add_buttons(self):
        # todo: if the 'cmd' is not available?
        for name, cmd, icon in tools_all:
            btn = QtWidgets.QToolButton()
            btn.setObjectName(name)
            btn.setToolTip(name)
            btn.setIconSize(QtCore.QSize(24, 24))
            i = Gui.getIcon(icon)
            if i is None:
                continue  # todo: error?
            btn.setIcon(i)
            btn.clicked.connect(
                lambda checked=False, n=name, c=cmd: self.run_cmd(c, n))
            self.b_layout.addWidget(btn)
        # add spacer
        self.b_layout.addStretch(1)

    def run_cmd(self, cmd, name):
        # editing the basic sketch
        if name == 'EditSketch' and self.sketch_profile:
            Gui.activeDocument().setEdit(self.sketch_profile)
            self.collapse()
            return
        # displaying controls
        if name in tools_control:
            self.c_widget.setVisible(True)
            self.max_distance_y = 140
            self.current_tool = name
            self.spinbox.setValue(tools_control[name][-1])
        else:
            self.c_widget.setVisible(False)
            self.max_distance_y = 100
            self.current_tool = None
            self.dialog = None
            self.collapse()
        # initializing
        Gui.runCommand(cmd)
        if self.current_tool:
            self.get_dialog()

    def get_dialog(self):
        Gui.updateGui()
        dialog = Gui.Control.activeTaskDialog()
        self.dialog = dialog if dialog else None

    def update_position(self):
        if self.is_visible:
            cursor_position = QtGui.QCursor.pos()
            x = abs(cursor_position.x() - self.position_init.x())
            y = abs(cursor_position.y() - self.position_init.y())
            if x > self.max_distance_x or y > self.max_distance_y:
                self.collapse()

    def get_view(self):
        try:
            w = Gui.getMainWindow()
            area = w.centralWidget()
            self.view = area.currentSubWindow()
            self.view.installEventFilter(self)
        except BaseException:
            pass  # todo: error?

    def eventFilter(self, obj, event):
        self.adjustSize()  # performance issue?
        if obj == self.view and event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            if self.current_tool:
                self.value_apply()
        else:
            super().keyPressEvent(event)

    # --------------------------------------------------------------------------

    def selection_add(self, doc, obj, sub, pos):
        if not self.is_available():
            return
        if not self.selection_parsing(doc, obj, sub, pos):
            return
        w = Gui.getMainWindow()
        position_local = w.mapFromGlobal(self.position_current)
        self.activate(position_local)

    def is_available(self):
        self.get_view()
        if not self.view:
            return False
        # todo: add other workbenches
        self.active_workbench = Gui.activeWorkbench().name()
        if self.active_workbench == 'PartDesignWorkbench':
            return self.is_viewport()
        return False

    def is_viewport(self) -> bool:
        self.position_current = QtGui.QCursor.pos()
        view_global = self.view.mapToGlobal(QtCore.QPoint(0, 0))
        view_rect = QtCore.QRect(view_global, self.view.size())
        return view_rect.contains(self.position_current)

    def selection_parsing(self, doc, obj, sub, pos) -> bool:
        ad = FreeCAD.ActiveDocument

        if ad.Name != doc:
            self.preparation('Other', None)
            return True

        selection = Gui.Selection.getSelection(doc)
        if len(selection) == 0:
            return False
        selection = selection[0]
        if selection.TypeId in OUTLINE:
            self.preparation('Outline', selection.TypeId)
            return True

        self.sketch_profile = None
        parent = selection.getParentGeoFeatureGroup()
        if hasattr(parent, 'Profile'):
            self.sketch_profile = selection.Profile[0]
        else:
            if hasattr(parent, 'Group'):
                for g in parent.Group:
                    if g.TypeId == 'Sketcher::SketchObject':
                        self.sketch_profile = g
                        break

        selection = Gui.Selection.getSelectionEx(doc, 0)
        if len(selection) == 0:
            return False
        selection = selection[0]
        if not selection.HasSubObjects:
            return False

        so = selection.SubObjects[-1]
        match so.ShapeType:
            case 'Edge' | 'Face':
                self.preparation(so.ShapeType, so.ShapeType)
                return True
            case 'Vertex':
                return False  # todo: what to do with this?
            case _:
                return False  # todo: what could it be?

    def preparation(self, entity, type_id):

        workbench_set = tools_access.get(self.active_workbench)
        if not workbench_set:
            return  # todo: debug?
        entity_set = workbench_set.get(entity)
        if not entity_set:
            return  # todo: debug?

        # exception
        if entity == 'Outline' and type_id == 'Part::Part2DObjectPython':
            entity_set.remove('EditSketch')

        # available buttons
        distance_x = 0
        buttons = self.b_widget.findChildren(QtWidgets.QToolButton)
        for btn in buttons:
            if btn.objectName() in entity_set:
                distance_x += 40
                btn.setVisible(True)
            else:
                btn.setVisible(False)
        self.max_distance_x = distance_x

    def selection_remove(self, doc, obj, sub):
        pass  # print('... selection_remove ...')

    def selection_clear(self):
        pass  # print('... selection_clear ...')

    # --------------------------------------------------------------------------

    def activate(self, position):
        # reset
        self.c_widget.setVisible(False)
        self.max_distance_y = 100
        self.spinbox.setValue(1)
        # position
        if self.isVisible():
            self.move_to_cursor(position)
        else:
            self.move_to_cursor(position)
            self.show()
            self.raise_()
            self.position_init = QtGui.QCursor.pos()
            self.is_visible = True
            self.timer.start(200)  # set a higher value?

    def move_to_cursor(self, cursor_local):
        x = cursor_local.x() + OFFSET_FROM_CURSOR
        y = cursor_local.y() + OFFSET_FROM_CURSOR
        w = Gui.getMainWindow()
        x = max(0, min(x, w.width() - self.width()))
        y = max(0, min(y, w.height() - self.height()))
        self.move(int(x), int(y))

    # --------------------------------------------------------------------------

    def collapse(self):
        self.dialog = None
        self.hide()
        self.is_visible = False
        self.timer.stop()

    def clear(self):
        Gui.Selection.removeObserver(self.observer)

    # --------------------------------------------------------------------------

    def value_changed(self, value):
        if not self.dialog:
            self.get_dialog()
        if not self.dialog:
            return
        content = self.dialog.getDialogContent()
        if not content:
            return
        content = content[0]
        if not self.current_tool:
            return
        target = content.findChild(*tools_control[self.current_tool][:2])
        target.setProperty('rawValue', value)
        # debug, search:
        #     task = Gui.Control.activeTaskDialog()
        #     content = task.getDialogContent()[0]
        #     content.children()
        #     content.findChildren(QtWidgets.QAbstractSpinBox)

    def value_apply(self):
        if not self.dialog:
            self.get_dialog()
        if self.dialog:
            self.dialog.accept()
        self.collapse()

# ------------------------------------------------------------------------------


init = True

app = Gui.getMainWindow()
for child in app.children():
    if type(child).__name__ == 'SmartHUD':
        child.clear()
        child.deleteLater()
        init = False
        Logger.info('HUD is disabled')

if init:
    overlay = SmartHUD(app)
    overlay.adjustSize()
    Logger.info('HUD is activated')
