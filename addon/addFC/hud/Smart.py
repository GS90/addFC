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
    ('Go to Linked Object', 'Std_LinkSelectLinked', 'LinkSelect'),
    ('Fit Selection', 'Std_ViewFitSelection', 'zoom-selection'),
    ('Transform', 'Std_TransformManip', 'Std_TransformManip'),
    # pd:sketch
    ('New Sketch', 'PartDesign_NewSketch', 'Sketcher_NewSketch'),
    ('Edit Sketch', 'Sketcher_EditSketch', 'Sketcher_EditSketch'),
    # pd:uno
    ('Pad', 'PartDesign_Pad', 'PartDesign_Pad'),
    ('Pocket', 'PartDesign_Pocket', 'PartDesign_Pocket'),
    ('Hole', 'PartDesign_Hole', 'PartDesign_Hole'),
    # pd:dos
    ('Fillet', 'PartDesign_Fillet', 'PartDesign_Fillet'),
    ('Chamfer', 'PartDesign_Chamfer', 'PartDesign_Chamfer'),
    ('Draft', 'PartDesign_Draft', 'PartDesign_Draft'),
    ('Thickness', 'PartDesign_Thickness', 'PartDesign_Thickness'),
]

tools_access = {
    'PartDesignWorkbench': {
        'Other': [
            'Align to Selection',  # 1+
            'Go to Linked Object',
            'Transform',
            'Fit Selection',
        ],
        'Outline': [
            'Edit Sketch',  # exception
            'Pad',
            'Pocket',
            'Hole',
            'SMBase',
        ],
        'Edge': [
            'Fillet',
            'Chamfer',
            'Make Wall',
        ],
        'Face': [
            'Align to Selection',  # 1+
            'Edit Sketch',         # exception
            'New Sketch',
            'Pad',
            'Pocket',
            'Draft',
            'Thickness',
            'Extend Face',
            'Unattended Unfold',
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
    'Make Base Wall': (QtWidgets.QAbstractSpinBox, 'spinLength', 100),
    'Make Wall': (QtWidgets.QAbstractSpinBox, 'Length', 10),
    'Extend Face': (QtWidgets.QAbstractSpinBox, 'Length', 10),
}

tools_check = {
    # pd:uno
    'Pad': (
        (QtWidgets.QCheckBox, 'checkBoxMidplane', False, 'Symmetric'),
        (QtWidgets.QCheckBox, 'checkBoxReversed', False, 'Reversed'),
    ),
    'Pocket': (
        (QtWidgets.QCheckBox, 'checkBoxMidplane', False, 'Symmetric'),
        (QtWidgets.QCheckBox, 'checkBoxReversed', False, 'Reversed'),
    ),
    # pd:dos
    'Fillet': (
        (QtWidgets.QCheckBox, 'checkBoxUseAllEdges', False, 'All Edges'),
    ),
    'Chamfer': (
        (QtWidgets.QCheckBox, 'checkBoxUseAllEdges', False, 'All Edges'),
    ),
    'Draft': (
        (QtWidgets.QCheckBox, 'checkReverse', False, 'Reverse'),
    ),
    'Thickness': (
        (QtWidgets.QCheckBox, 'checkIntersection', False, 'Intersection'),
        (QtWidgets.QCheckBox, 'checkReverse', False, 'Inwards'),
    ),
}

# differences in version 1.2+
tools_check_exception = (QtWidgets.QComboBox, 'sidesMode', False, 'Symmetric')


def configure():
    global tools_all

    if int(P.FC_VERSION[0]) > 0:
        tools_all.insert(0, ('Align to Selection',
                             'Std_AlignToSelection',
                             'align-to-selection'))

    if P.afc_additions['sm'][0]:
        import SheetMetalTools
        Gui.addIconPath(SheetMetalTools.icons_path)
        sm = (
            ('Make Base Wall',
             'SheetMetal_AddBase',
             'SheetMetal_AddBase'),
            ('Make Wall',
             'SheetMetal_AddWall',
             'SheetMetal_AddWall'),
            ('Extend Face',
             'SheetMetal_Extrude',
             'SheetMetal_Extrude'),
            ('Unattended Unfold',
             'SheetMetal_UnattendedUnfold',
             'SheetMetal_UnfoldUnattended'),
        )
        tools_all.extend(sm)


# ------------------------------------------------------------------------------


def generate_css(app_theme, hud_theme) -> tuple[str, str]:

    if hud_theme == 'Standard':
        if app_theme == 'dark':
            background_color = 'rgba(45, 45, 45, 180)'
            background_color_box = 'rgba(60, 60, 60, 180)'
            background_color_box_hover = 'rgba(20, 20, 20, 140)'
            border = '1px solid #282d2d'
            border_box = '1px solid #282d2d'
            # appy
            css_apply = (
                'QToolButton {'
                'border: 1px solid #282d2d;'
                'border-left: none;'
                '}'
                'QToolButton:hover {'
                'background-color: rgba(20, 20, 20, 140);'
                '}'
            )
        else:
            background_color = 'rgba(248, 248, 248, 120)'
            background_color_box = 'rgba(248, 248, 248, 120)'
            background_color_box_hover = 'rgba(248, 248, 248, 200)'
            border = '1px solid #646464'
            border_box = '1px solid #8c8c8c'
            # appy
            css_apply = (
                'QToolButton {'
                'background-color: #bebebe;'
                'border: 1px solid #8c8c8c;'
                'border-left: none;'
                '}'
                'QToolButton:hover {'
                'background-color: #a0a0a0;'
                '}'
            )
        border_radius = '0'
        border_radius_button = '0'
        padding_button = '2px'
        spin_box_radius = 'border-radius: 0;'
    else:
        if app_theme == 'dark':
            background_color = 'rgba(45, 45, 45, 200)'
            background_color_box = 'rgba(45, 45, 45, 220)'
            background_color_box_hover = 'rgba(25, 25, 25, 220)'
            border = '1px solid #141414'
            # appy
            css_apply = (
                'QToolButton {'
                'background-color: #232828;'
                'border-radius: 0;'
                'border-top-right-radius: 4px;'
                'border-bottom-right-radius: 4px;'
                '}'
                'QToolButton:hover {'
                'background-color: #141818;'
                '}'
            )
        else:
            background_color = 'rgba(248, 248, 248, 120)'
            background_color_box = 'rgba(248, 248, 248, 120)'
            background_color_box_hover = 'rgba(248, 248, 248, 180)'
            border = 'none'
            # appy
            css_apply = (
                'QToolButton {'
                'background-color: #a0a0a0;'
                'border-radius: 0;'
                'border-top-right-radius: 6px;'
                'border-bottom-right-radius: 6px;'
                '}'
                'QToolButton:hover {'
                'background-color: #8c8c8c;'
                '}'
            )
        border_box = 'none'
        border_radius = '6px'
        border_radius_button = '6px'
        padding_button = '4px'
        spin_box_radius = (
            'border-radius: 0;'
            'border-top-left-radius: 6px;'
            'border-bottom-left-radius: 6px;'
        )

    css = (
        'QWidget#HUD {'
        f'background-color: {background_color};'
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
        f'background-color: {background_color_box};'
        f'{spin_box_radius}'
        f'border: {border_box};'
        'padding: 2px 4px;'
        '}'
        'QDoubleSpinBox:hover {'
        f'background-color: {background_color_box_hover};'
        '}'
        'QCheckBox {'
        'padding: 2px 4px;'
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

        configure()

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
        self.b_layout.setSpacing(2)
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
        self.spinbox.setFixedHeight(26)
        self.spinbox.setFixedWidth(80)
        self.spinbox.valueChanged.connect(self.value_changed)
        self.spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.c_layout.addWidget(self.spinbox)

        # control: apply
        self.apply = QtWidgets.QToolButton()
        self.apply.setText('OK')
        self.apply.setStyleSheet(css_apply)
        self.apply.setFixedHeight(26)
        self.apply.clicked.connect(self.apply_values)
        self.c_layout.addWidget(self.apply)

        # control: spacer
        self.c_layout.addStretch(1)

        # wrapper
        self.wrapper = QtWidgets.QVBoxLayout()
        self.wrapper.setContentsMargins(4, 4, 4, 4)
        self.wrapper.setSpacing(2)
        self.wrapper.addWidget(self.b_widget)
        self.wrapper.addWidget(self.c_widget)

        # check: uno & dos
        self.check_uno = QtWidgets.QCheckBox()
        self.check_uno.setText('CheckBoxUno')
        self.check_uno.setVisible(False)
        self.check_uno.stateChanged.connect(self.state_changed)
        self.wrapper.addWidget(self.check_uno)
        self.check_dos = QtWidgets.QCheckBox()
        self.check_dos.setText('CheckBoxDos')
        self.check_dos.setVisible(False)
        self.check_dos.stateChanged.connect(self.state_changed)
        self.wrapper.addWidget(self.check_dos)

        # building
        self.container.setLayout(self.wrapper)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.container)

        self.is_visible = False
        self.position_init = None
        self.position_current = None
        self.active_workbench = Gui.activeWorkbench().name()
        self.sketch_profile = None

        self.current_button = None
        self.current_tool = None
        self.dialog = None
        self.content = None

        self.freeze = False

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
            btn.clicked.connect(lambda checked=False,
                                n=name,
                                c=cmd,
                                b=btn: self.run_cmd(c, n, b))
            self.b_layout.addWidget(btn)
        # add spacer
        self.b_layout.addStretch(1)

    def run_cmd(self, cmd, name, btn):
        if self.current_button and self.current_tool:
            return  # if the button is already pressed

        # editing the basic sketch
        if name == 'Edit Sketch' and self.sketch_profile:
            Gui.activeDocument().setEdit(self.sketch_profile)
            self.collapse()
            return

        # reset
        self.c_widget.setVisible(False)
        self.check_uno.setVisible(False)
        self.check_dos.setVisible(False)
        self.max_distance_y = 90

        # adjustment
        self.freeze = True
        if name in tools_control or name in tools_check:

            self.current_tool = name
            # button style: active
            btn.setStyleSheet('background-color: rgba(0, 0, 0, 30);')
            btn.setToolTip(None)
            self.current_button = btn

            if name in tools_control:
                self.c_widget.setVisible(True)
                self.max_distance_y = 120
                self.spinbox.setValue(tools_control[name][-1])
            if name in tools_check:
                self.max_distance_y = 150
                check = tools_check[name]
                # there is always one element
                self.check_uno.setVisible(True)
                b, n = check[0][-2:]
                self.check_uno.setText(n)
                self.check_uno.setChecked(b)
                if len(check) > 1:
                    self.max_distance_y = 180
                    self.check_dos.setVisible(True)
                    b, n = check[1][-2:]
                    self.check_dos.setText(n)
                    self.check_dos.setChecked(b)
        else:
            self.current_tool = None
            self.dialog = None
            self.content = None
            self.collapse()
        self.freeze = False

        # initializing
        Gui.runCommand(cmd)
        if self.current_tool:
            self.get_dialog_content()

    def get_dialog_content(self):
        Gui.updateGui()
        self.raise_()  # ...features of version 1+
        self.dialog = Gui.Control.activeTaskDialog()
        if self.dialog:
            content = self.dialog.getDialogContent()
            if content:
                self.content = content[0]  # todo: always 0?
                return
        self.dialog = None
        self.content = None

    def update_position(self):
        if self.is_visible:
            cursor_position = QtGui.QCursor.pos()
            x = abs(cursor_position.x() - self.position_init.x())
            y = abs(cursor_position.y() - self.position_init.y())
            if x > self.max_distance_x or y > self.max_distance_y:
                self.collapse()
            # else:
            #     todo: display when the cursor returns

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
                self.apply_values()
        else:
            super().keyPressEvent(event)

    # --------------------------------------------------------------------------

    def selection_add(self, doc, obj, sub, pos):
        try:
            if not self.is_available():
                return
            if not self.selection_parsing(doc, obj, sub, pos):
                return
        except BaseException:
            return  # todo: error?
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
            entity_set.remove('Edit Sketch')

        # available buttons
        distance_x = 0
        buttons = self.b_widget.findChildren(QtWidgets.QToolButton)
        for btn in buttons:
            if btn.objectName() in entity_set:
                distance_x += 40
                btn.setVisible(True)
            else:
                btn.setVisible(False)
        self.max_distance_x = max(200, distance_x)

    def selection_remove(self, doc, obj, sub):
        if not self.current_button:
            self.collapse()

    def selection_clear(self):
        if not self.current_button:
            self.collapse()

    # --------------------------------------------------------------------------

    def activate(self, position):
        if self.isVisible():
            self.move_to_cursor(position)
        else:
            self.move_to_cursor(position)
            self.show()
            self.position_init = QtGui.QCursor.pos()
            self.is_visible = True
            self.timer.start(400)  # 200, set a higher value, 400?

    def move_to_cursor(self, cursor_local):
        x = cursor_local.x() + OFFSET_FROM_CURSOR
        y = cursor_local.y() + OFFSET_FROM_CURSOR
        w = Gui.getMainWindow()
        x = max(0, min(x, w.width() - self.width()))
        y = max(0, min(y, w.height() - self.height()))
        self.move(int(x), int(y))
        self.raise_()

    # --------------------------------------------------------------------------

    def collapse(self):
        if self.current_button:
            self.current_button.setToolTip(self.current_button.objectName())
            self.current_button.setStyleSheet('')
            self.current_button = None
        self.c_widget.setVisible(False)
        self.check_uno.setVisible(False)
        self.check_dos.setVisible(False)
        self.dialog = None
        self.content = None
        self.hide()
        self.is_visible = False
        self.timer.stop()

    def clear(self):
        Gui.Selection.removeObserver(self.observer)

    # --------------------------------------------------------------------------

    # hint, search:
    #     from PySide import QtWidgets
    #     content = Gui.Control.activeTaskDialog().getDialogContent()[0]
    #     content.findChildren(QtWidgets.QAbstractSpinBox)
    #     content.findChildren(QtWidgets.QCheckBox)

    def value_changed(self, value):
        current_tool = self.check_changed()
        if not current_tool:
            return
        widget, name = tools_control[current_tool][:2]
        target = self.content.findChild(widget, name)
        if target:
            target.setProperty('rawValue', value)

    def state_changed(self, state):
        current_tool = self.check_changed()
        if not current_tool:
            return
        check_tuple = tools_check[current_tool]
        checkbox = self.sender()
        text = checkbox.text()
        if int(P.FC_VERSION[0]) > 0 and int(P.FC_VERSION[1]) > 1:
            if text == 'Symmetric':
                if current_tool == 'Pad' or current_tool == 'Pocket':
                    widget, name = tools_check_exception[:2]
                    target = self.content.findChild(widget, name)
                    if state:
                        target.setCurrentText('Symmetric')
                    else:
                        target.setCurrentText('One sided')
                    return
        check_sender = None
        for i in check_tuple:
            if i[3] == text:
                check_sender = i
                break
        if not check_sender:
            return
        widget, name = check_sender[:2]
        target = self.content.findChild(widget, name)
        if target:
            target.setChecked(state)

    def check_changed(self) -> None | str:
        if self.freeze:
            return
        if not self.current_tool:
            return None
        if not self.dialog:
            # ? self.get_dialog_content()
            return None
        if not self.content:
            return None
        return self.current_tool

    def apply_values(self):
        if self.dialog:
            self.dialog.accept()
        self.collapse()


# ------------------------------------------------------------------------------


init = True

app = Gui.getMainWindow()
for child in app.children():
    if type(child).__name__ == 'SmartHUD':
        try:
            child.clear()
        except BaseException:
            pass
        child.deleteLater()
        init = False
        Logger.info('HUD (beta) is disabled')

if init:
    overlay = SmartHUD(app)
    overlay.adjustSize()
    Logger.info('HUD (beta) is activated')
