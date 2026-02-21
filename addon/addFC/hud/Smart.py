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
from addon.addFC.hud.Theme import generate_css


tools_all = [
    # other
    ('Go to Linked Object', 'Std_LinkSelectLinked', 'LinkSelect', 1),
    ('Fit Selection', 'Std_ViewFitSelection', 'zoom-selection', 1),

    # todo: use active_object
    # ('Transform', 'Std_TransformManip', 'Std_TransformManip', 1),
    # ('Random Color', 'Std_RandomColor', 'Std_RandomColor', 1),

    # datum
    ('Datum Point',
     'PartDesign_Point', 'PartDesign_Point', 1),
    ('Datum Line',
     'PartDesign_Line', 'PartDesign_Line', 1),
    ('Datum Plane',
     'PartDesign_Plane', 'PartDesign_Plane', 1),
    ('Coordinate System',
     'PartDesign_CoordinateSystem', 'PartDesign_CoordinateSystem', 1),
    # pd:sketch
    ('New Sketch', 'PartDesign_NewSketch', 'Sketcher_NewSketch', 1),
    ('Edit Sketch', 'Sketcher_EditSketch', 'Sketcher_EditSketch', 1),
    # pd:binder
    ('Binder', 'PartDesign_SubShapeBinder', 'PartDesign_SubShapeBinder', 1),
    # pd:uno
    ('Pad', 'PartDesign_Pad', 'PartDesign_Pad', 2),
    ('Pocket', 'PartDesign_Pocket', 'PartDesign_Pocket', 2),
    ('Hole', 'PartDesign_Hole', 'PartDesign_Hole', 2),
    # pd:dos
    ('Fillet', 'PartDesign_Fillet', 'PartDesign_Fillet', 2),
    ('Chamfer', 'PartDesign_Chamfer', 'PartDesign_Chamfer', 2),
    ('Draft', 'PartDesign_Draft', 'PartDesign_Draft', 2),
    ('Thickness', 'PartDesign_Thickness', 'PartDesign_Thickness', 2),
    # pd:secondary
    ('Mirror',
     'PartDesign_Mirrored', 'PartDesign_Mirrored', 2),
    ('Linear Pattern',
     'PartDesign_LinearPattern', 'PartDesign_LinearPattern', 1),
    ('Polar Pattern',
     'PartDesign_PolarPattern', 'PartDesign_PolarPattern', 1),
    ('Multi Transform',
     'PartDesign_MultiTransform', 'PartDesign_MultiTransform', 1),
]

activity_ban = (
    'Go to Linked Object',
    'Fit Selection',
    'Transform',
    'Binder',
)

tools_access = {
    'PartDesignWorkbench': {
        'Other': [
            'Measure',              # 2 entities
            'Go to Linked Object',  # link
            'Align to Selection',   # 1+
            'Fit Selection',
            'Transform',            # active_object
        ],
        'Outline': [
            'Measure',      # 2 entities
            'Edit Sketch',  # exception
            'Pad',
            'Pocket',
            'Hole',
            'Make Base Wall',
        ],
        'Edge': [
            'Measure',       # 2 entities
            'Datum Point',
            'Datum Line',
            'Fillet',
            'Chamfer',
            'Make Wall',
        ],
        'Face': [
            'Align to Selection',  # 1+
            'Measure',             # 2 entities
            'Edit Sketch',         # exception
            'Binder',
            'New Sketch',
            'Datum Plane',
            'Pad',
            'Pocket',
            'Fillet',
            'Chamfer',
            'Draft',
            'Thickness',
            'Extend Face',
            'Unattended Unfold',
            'Transform',           # active_object
        ],
        'Vertex': [
            'Measure',  # 2 entities
        ],
        'Datum': [
            'New Sketch',
        ],
        'Secondary': [
            'Mirror',
            'Linear Pattern',
            'Polar Pattern',
            'Multi Transform',
        ]
    },
}

tools_before = (
    'Pad',
    'Pocket',
)

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
        (QtWidgets.QComboBox, 'changeMode', False, 'Through all'),
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
    # sm
    'Make Wall': (
        (QtWidgets.QPushButton, 'buttRevWall', False, 'Reverse'),
    ),
    'Make Base Wall': (
        (QtWidgets.QCheckBox, 'checkSymetric', False, 'Symmetric'),
        (QtWidgets.QCheckBox, 'checkRevDirection', False, 'Reversed'),
    ),
}

# differences in version 1.2+
tools_check_exception = (QtWidgets.QComboBox, 'sidesMode', False, 'Symmetric')


# ----

tools_next = (
    ('Measure', 'Std_Measure', 'umf-measurement', 1),
    ('Align to Selection', 'Std_AlignToSelection', 'align-to-selection', 1),
    ('Transparency', 'Std_ToggleTransparency', 'Std_ToggleTransparency', 1),
)

toold_old = (
    ('Measure', 'Part_Measure_Linear', 'Part_Measure_Linear', 1),
)

tools_sm = (
    ('Make Base Wall',
     'SheetMetal_AddBase', 'SheetMetal_AddBase', 2),
    ('Make Wall',
     'SheetMetal_AddWall', 'SheetMetal_AddWall', 2),
    ('Extend Face',
     'SheetMetal_Extrude', 'SheetMetal_Extrude', 2),
    ('Unattended Unfold',
     'SheetMetal_UnattendedUnfold', 'SheetMetal_UnfoldUnattended', 2),
)

# ----


def configure():
    global tools_all
    if int(P.FC_VERSION[0]) > 0:
        tools_all[:0] = tools_next
    else:
        tools_all.insert(0, toold_old[0])
    if P.afc_additions['sm'][0]:
        if not P.pref_configuration['hud_tools_sm']:
            return
        import SheetMetalTools
        Gui.addIconPath(SheetMetalTools.icons_path)
        tools_all.extend(tools_sm)


# ------------------------------------------------------------------------------


class SelectionObserverHUD:
    def __init__(self, parent):
        self.overlay = parent

    def addSelection(self, doc, obj, sub, pos):
        try:
            self.overlay.selection_add(doc, obj, sub, pos)
        except Exception as err:
            Logger.error('HUD, addSelection: ' + str(err))
            Gui.Selection.removeObserver(self)

    def removeSelection(self, doc, obj, sub):
        try:
            self.overlay.selection_remove(doc, obj, sub)
        except Exception as err:
            Logger.error('HUD, removeSelection: ' + str(err))
            Gui.Selection.removeObserver(self)

    def clearSelection(self, doc):
        try:
            self.overlay.selection_clear()
        except Exception as err:
            Logger.error('HUD, clearSelection: ' + str(err))
            Gui.Selection.removeObserver(self)


# ------------------------------------------------------------------------------


class SmartHUD(QtWidgets.QWidget):

    OUTLINE = ('Sketcher::SketchObject', 'Part::Part2DObjectPython')
    P_STR_UNITS = 'User parameter:BaseApp/Preferences/Units'

    OFFSET_CURSOR = 10

    DISTANCE_FADE = 300
    DISTANCE_MIN = 200
    DISTANCE_STEP = 30

    TIMER_SLOW = 400
    TIMER_FAST = 60

    OPACITY_MIN = 0.0
    OPACITY_MAX = 1.0

    HEIGHT_CONTROL = 28

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('SmartHUD')
        self.parent = parent

        self.is_raised = False

        configure()

        _f = QtCore.Qt.FramelessWindowHint | QtCore.Qt.SubWindow
        self.setWindowFlags(_f)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        conf = P.pref_configuration

        app_theme = P.afc_theme['current']  # std, dark, light
        hud_theme = conf['hud_theme']       # Standard, Rounded

        css, css_apply, self.css_active = generate_css(
            'smart', app_theme, hud_theme)

        # panel background transparency
        _transparency = conf.get('hud_transparency')
        if _transparency:
            css = css.replace('#e6e6e6;', 'rgba(230, 230, 230, 220);')
            css = css.replace('#2e3436;', 'rgba(46, 52, 54, 220);')

        # value step
        _step = conf.get('hud_value_step')
        if _step:
            try:
                _step_value = float(_step)
            except ValueError as err:
                Logger.warning('HUD, value step: ' + str(err))
                _step_value = 1

        self.setStyleSheet(css)

        self.container = QtWidgets.QWidget()
        self.container.setObjectName('HUD')

        # buttons

        self.b_layout = QtWidgets.QVBoxLayout()
        self.b_layout.setContentsMargins(2, 2, 2, 2)
        self.b_layout.setSpacing(2)
        # uno
        self.uno_layout = QtWidgets.QHBoxLayout()
        self.uno_layout.setSpacing(2)
        # dos
        self.dos_layout = QtWidgets.QHBoxLayout()
        self.dos_layout.setSpacing(2)
        # add
        self.b_layout.addLayout(self.uno_layout)
        self.b_layout.addLayout(self.dos_layout)
        # button container
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
        self.spinbox.setSingleStep(_step_value)
        _d = FreeCAD.ParamGet(self.P_STR_UNITS).GetInt('Decimals')
        self.spinbox.setDecimals(_d)
        self.spinbox.setFixedHeight(self.HEIGHT_CONTROL)
        self.spinbox.setFixedWidth(80)
        self.spinbox.valueChanged.connect(self.value_changed)
        self.spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.c_layout.addWidget(self.spinbox)

        # control: apply
        self.apply = QtWidgets.QToolButton()
        self.apply.setText('OK')
        self.apply.setStyleSheet(css_apply)
        self.apply.setFixedHeight(self.HEIGHT_CONTROL)
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

        # check: uno, dos and tres
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
        self.check_tres = QtWidgets.QCheckBox()
        self.check_tres.setText('CheckBoxTres')
        self.check_tres.setVisible(False)
        self.check_tres.stateChanged.connect(self.state_changed)
        self.wrapper.addWidget(self.check_tres)

        # building
        self.container.setLayout(self.wrapper)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.container)

        self.freeze = False
        self.new_sketch = False

        self.active_workbench = Gui.activeWorkbench().name()

        self.position_init = None
        self.position_current = None
        self.active_object = None
        self.sketch_profile = None
        self.current_button = None
        self.current_control = None
        self.selected_widget = None
        self.dialog = None
        self.content = None
        self.transaction = None

        if int(P.FC_VERSION[0]) > 0 and int(P.FC_VERSION[1]) > 1:
            self.draggers = True
        else:
            self.draggers = False

        self.selected_count = 0

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_panel)

        self.distance_max = self.DISTANCE_MIN
        self.distance_offset = self.distance_max / 2

        # opacity
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade = QtCore.QPropertyAnimation(self.opacity_effect, b'opacity')
        self.fade.setEasingCurve(QtCore.QEasingCurve.OutQuad)

        self.observer = SelectionObserverHUD(self)
        Gui.Selection.addObserver(self.observer)

        parent.workbenchActivated.connect(self.workbench_changed)

        self.get_view()

    # --------------------------------------------------------------------------

    def add_buttons(self):
        for name, cmd, icon, row in tools_all:
            btn = QtWidgets.QToolButton()
            btn.setObjectName(name)
            btn.setToolTip(name)
            btn.setIconSize(QtCore.QSize(24, 24))
            i = Gui.getIcon(icon)
            if i is None:
                continue  # todo: ..?
            btn.setIcon(i)
            btn.clicked.connect(lambda checked=False,
                                n=name,
                                c=cmd,
                                b=btn: self.run_cmd(c, n, b))
            self.b_layout.addWidget(btn)
            if row == 1:
                self.uno_layout.addWidget(btn)
            else:
                self.dos_layout.addWidget(btn)
        # add spacer
        self.uno_layout.addStretch(1)
        self.dos_layout.addStretch(1)

    def run_cmd(self, cmd, name, btn):
        if self.current_button and self.current_control:
            return  # button already pressed

        # editing the basic sketch
        if name == 'Edit Sketch' and self.sketch_profile:
            Gui.activeDocument().setEdit(self.sketch_profile)
            self.collapse()
            return
        # make the 'PartDesign::Body' active
        if self.active_object:
            if name not in activity_ban:
                Gui.ActiveDocument.ActiveView.setActiveObject(
                    'pdbody', self.active_object)
        # reset
        self.c_widget.setVisible(False)
        self.check_uno.setVisible(False)
        self.check_dos.setVisible(False)
        self.check_tres.setVisible(False)
        self.new_sketch = False

        # adaptation
        self.freeze = True
        if name in tools_control or name in tools_check:
            self.current_control = name
            # button style: active
            btn.setStyleSheet(self.css_active)
            btn.setToolTip(None)
            self.current_button = btn
            # control & check
            if name in tools_control:
                self.c_widget.setVisible(True)
                self.spinbox.setValue(tools_control[name][-1])
            if name in tools_check:
                check = tools_check[name]
                # there is always one element
                self.check_uno.setVisible(True)
                b, n = check[0][-2:]
                self.check_uno.setText(n)
                self.check_uno.setChecked(b)
                if len(check) > 1:
                    self.check_dos.setVisible(True)
                    b, n = check[1][-2:]
                    self.check_dos.setText(n)
                    self.check_dos.setChecked(b)
                    if len(check) > 2:
                        self.check_tres.setVisible(True)
                        b, n = check[2][-2:]
                        self.check_tres.setText(n)
                        self.check_tres.setChecked(b)
        else:
            self.current_control = None
            self.collapse()
            if name == 'New Sketch':
                self.new_sketch = True
        self.freeze = False

        # initializing
        Gui.runCommand(cmd)
        if self.current_control:
            self.get_dialog_and_content()

    def get_dialog_and_content(self):
        self.clear_dialog_and_content()
        self.raise_()
        self.dialog = Gui.Control.activeTaskDialog()
        if self.dialog:
            content = self.dialog.getDialogContent()
            if content:
                # todo: get all the content, not just the first one [0]
                self.content = content[0]
                # focus
                Gui.updateGui()
                self.spinbox.setFocus()
                self.spinbox.selectAll()
                # value, transaction
                if self.current_control:
                    try:
                        widget, name = tools_control[self.current_control][:2]
                        _transaction = self.content.findChild(widget, name)
                        if _transaction:
                            self.transaction = _transaction
                            self.transaction.valueChanged.connect(
                                self.transaction_changed)
                        else:
                            self.transaction = None
                    except BaseException as err:
                        Logger.warning('transaction, add: ' + str(err))
                        self.transaction = None
                return
        self.clear_dialog_and_content()

    def clear_dialog_and_content(self):
        self.dialog, self.content, self.transaction = None, None, None

    def update_panel(self):
        if not self.isVisible():
            return
        # synchronization of values
        if self.draggers and self.transaction:
            self.transaction_verification()
        cursor_position = QtGui.QCursor.pos()
        # position difference
        position_x = self.position_init.x() + self.distance_offset
        position_y = self.position_init.y() + self.distance_offset
        dx = cursor_position.x() - position_x
        dy = cursor_position.y() - position_y
        # Euclidean distance
        distance = (dx ** 2 + dy ** 2) ** 0.5
        # fade distance
        max_distance_fade = self.distance_max + self.DISTANCE_FADE
        if distance > self.distance_max:
            if distance > max_distance_fade:
                self.collapse()
            else:
                self.timer.setInterval(self.TIMER_FAST)
                fade_range = max_distance_fade - self.distance_max
                adjusted_distance = distance - self.distance_max
                opacity = self.OPACITY_MAX - (adjusted_distance / fade_range)
                self.opacity_effect.setOpacity(opacity)
        else:
            self.timer.setInterval(self.TIMER_SLOW)
            self.opacity_effect.setOpacity(self.OPACITY_MAX)

    def get_view(self):
        try:
            area = self.parent.centralWidget()
            self.view = area.currentSubWindow()
            self.view.installEventFilter(self)
        except BaseException:
            pass  # todo: error?

    def workbench_changed(self, workbench_name):
        if not self.new_sketch:
            return
        if workbench_name != 'PartDesignWorkbench':
            return
        selection = Gui.Selection.getSelection()
        if not selection:
            return
        s = selection[0]
        if hasattr(s, 'TypeId'):
            if s.TypeId == 'Sketcher::SketchObject':
                if self.is_viewport():
                    self.preparation_panel('Outline', s.TypeId)
                    position_local = self.parent.mapFromGlobal(
                        self.position_current)
                    self.activate(position_local)
                    self.new_sketch = False

    def eventFilter(self, obj, event):
        if self.isVisible():
            current_size = self.size()
            preferred_size = self.sizeHint()
            if current_size != preferred_size:
                self.adjustSize()
            if not self.is_raised:
                self.raise_()
                self.is_raised = True
        return super().eventFilter(obj, event)

    def hideEvent(self, event):
        self.is_raised = False
        super().hideEvent(event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.collapse()
        elif event.key() == QtCore.Qt.Key_Return:
            if self.current_control:
                self.apply_values()
        else:
            super().keyPressEvent(event)

    # --------------------------------------------------------------------------

    def selection_add(self, doc, obj, sub, pos):
        self.active_object = None
        self.sketch_profile = None
        try:
            if not self.is_available():
                return  # todo: working with the construction tree
            if not self.selection_parsing(doc, obj, sub, pos):
                return
        except BaseException as err:
            Logger.warning('HUD, selection parsing: ' + str(err))
            return
        position_local = self.parent.mapFromGlobal(self.position_current)
        self.activate(position_local)
        self.raise_()

    def is_available(self):
        self.get_view()
        if not self.view:
            return False
        self.active_workbench = Gui.activeWorkbench().name()
        if self.active_workbench == 'PartDesignWorkbench':
            return self.is_viewport()
        return False

    def is_viewport(self) -> bool:
        self.position_current = QtGui.QCursor.pos()

        widget = QtGui.QApplication.widgetAt(self.position_current)
        if widget:
            # overlay treeView: 'qt_scrollarea_viewport'
            self.selected_widget = widget.objectName().lower()
        else:
            self.selected_widget = None

        view_global = self.view.mapToGlobal(QtCore.QPoint(0, 0))
        view_rect = QtCore.QRect(view_global, self.view.size())
        return view_rect.contains(self.position_current)

    def selection_parsing(self, doc, obj, sub, pos) -> bool:
        self.selected_count = len(Gui.Selection.getCompleteSelection())

        ad = FreeCAD.ActiveDocument

        if ad.Name != doc:
            self.preparation_panel('Other', None)
            return True

        selection = Gui.Selection.getSelection(doc)
        if len(selection) == 0:
            return False
        selection = selection[0]

        parent = selection.getParentGeoFeatureGroup()
        if hasattr(parent, 'TypeId'):
            if parent.TypeId == 'PartDesign::Body':
                self.active_object = parent

        if selection.TypeId in self.OUTLINE:
            self.preparation_panel('Outline', selection.TypeId)
            if self.selected_widget == 'qt_scrollarea_viewport':
                return False  # overlay treeView
            else:
                return True

        self.sketch_profile = None

        if hasattr(parent, 'Profile'):
            self.sketch_profile = selection.Profile[0]
        else:
            if hasattr(parent, 'Group'):
                for g in parent.Group:
                    if hasattr(g, 'TypeId'):
                        if g.TypeId == 'Sketcher::SketchObject':
                            if self.sketch_profile:
                                self.sketch_profile = None
                                break
                            self.sketch_profile = g

        selection = Gui.Selection.getSelectionEx(doc, 0)
        if len(selection) == 0:
            return False
        selection = selection[0]
        if not selection.HasSubObjects:
            return False

        try:
            so = selection.SubObjects[-1]
        except BaseException:
            return False

        # overlay treeView
        if self.selected_widget == 'qt_scrollarea_viewport':
            if so.ShapeType not in ('Edge', 'Face'):
                return False

        # datum
        try:
            sen = selection.SubElementNames[-1]
            if 'datumplane' in sen.lower():
                self.preparation_panel('Datum', None)
                return True
            elif 'datum' in sen.lower():
                return False
        except BaseException:
            pass

        match so.ShapeType:
            # todo: add 'Solid'
            case 'Edge' | 'Face':
                self.preparation_panel(so.ShapeType, so.TypeId)
                return True
            case 'Vertex':
                if self.selected_count > 1:  # only 'Measure'
                    self.preparation_panel(so.ShapeType, so.TypeId)
                    return True
                else:
                    return False
            case _:
                return False  # todo: what could it be?

    def preparation_panel(self, entity, type_id):
        workbench_set = tools_access.get(self.active_workbench)
        if not workbench_set:
            return  # todo: debug?
        entity_set = workbench_set.get(entity).copy()
        if not entity_set:
            return  # todo: debug?

        # exceptions
        if entity == 'Outline' and type_id == 'Part::Part2DObjectPython':
            if 'Edit Sketch' in entity_set:
                entity_set.remove('Edit Sketch')
        if entity == 'Face' and not self.sketch_profile:
            if 'Edit Sketch' in entity_set:
                entity_set.remove('Edit Sketch')

        # available buttons
        max_distance = 0
        buttons = self.b_widget.findChildren(QtWidgets.QToolButton)
        for btn in buttons:
            object_name = btn.objectName()
            if object_name in entity_set:
                if object_name == 'Measure' and self.selected_count < 2:
                    btn.setVisible(False)
                    continue
                max_distance += self.DISTANCE_STEP
                btn.setVisible(True)
            else:
                btn.setVisible(False)
        self.distance_max = max(self.DISTANCE_MIN, max_distance)
        self.distance_offset = self.distance_max / 2

    def selection_remove(self, doc, obj, sub):
        if not self.current_button:
            self.collapse()

    def selection_clear(self):
        if not self.current_button:
            self.collapse()

    # --------------------------------------------------------------------------

    def activate(self, position):
        if self.current_button and self.current_control:
            return  # button already pressed
        if self.isVisible():
            self.move_to_cursor(position)
        else:
            self.move_to_cursor(position)
            self.opacity_effect.setOpacity(self.OPACITY_MAX)
            self.show()
            self.timer.start(self.TIMER_SLOW)

    def move_to_cursor(self, cursor_local):
        self.position_init = QtGui.QCursor.pos()
        x = cursor_local.x() + self.OFFSET_CURSOR
        y = cursor_local.y() + self.OFFSET_CURSOR
        x = max(0, min(x, self.parent.width() - self.width()))
        y = max(0, min(y, self.parent.height() - self.height()))
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
        self.check_tres.setVisible(False)
        self.clear_dialog_and_content()
        self.selected_widget = None
        self.opacity_effect.setOpacity(self.OPACITY_MIN)
        self.hide()
        self.timer.stop()

    def clear(self):
        try:
            if self.observer:
                Gui.Selection.removeObserver(self.observer)
                self.observer = None
        except Exception as err:
            Logger.warning('HUD, observer removal: ' + str(err))
        finally:
            self.timer.stop()

    # --------------------------------------------------------------------------

    # hint, search:
    #     from PySide import QtWidgets
    #     content = Gui.Control.activeTaskDialog().getDialogContent()[0]
    #     content.findChildren(QtWidgets.QAbstractSpinBox)
    #     content.findChildren(QtWidgets.QCheckBox)
    #     content.findChildren(QtWidgets.QComboBox)

    def transaction_verification(self):
        try:
            value_fc = self.transaction.property('rawValue')
            value_p = self.spinbox.value()
            if value_fc != value_p:
                self.spinbox.setValue(value_fc)
        except BaseException as err:
            Logger.warning('transaction, verification: ' + str(err))
            self.transaction = None

    def transaction_changed(self, value):
        if self.freeze:
            return
        self.spinbox.setValue(value)

    def value_changed(self, value):
        if self.freeze:
            return
        if self.transaction:
            try:
                self.transaction.setProperty('rawValue', value)
                return
            except BaseException as err:
                Logger.warning('transaction, changed: ' + str(err))
                self.transaction = None
        current_tool = self.check_changed()
        if not current_tool:
            return
        widget, name = tools_control[current_tool][:2]
        target = self.content.findChild(widget, name)
        if target:
            target.setProperty('rawValue', value)

    def state_changed(self, state):
        if self.freeze:
            return
        current_tool = self.check_changed()
        if not current_tool:
            return
        check_tuple = tools_check[current_tool]
        checkbox = self.sender()
        text = checkbox.text()

        if text == 'Through all' and current_tool == 'Pocket':
            widget, name = tools_check['Pocket'][2][:2]
            target = self.content.findChild(widget, name)
            if state:
                target.setCurrentIndex(1)  # Through all
            else:
                target.setCurrentIndex(0)  # Dimension
            return

        if int(P.FC_VERSION[0]) > 0 and int(P.FC_VERSION[1]) > 1:
            if text == 'Symmetric':
                if current_tool == 'Pad' or current_tool == 'Pocket':
                    widget, name = tools_check_exception[:2]
                    target = self.content.findChild(widget, name)
                    if state:
                        target.setCurrentIndex(2)  # Symmetric
                    else:
                        target.setCurrentIndex(0)  # One sided
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
            if current_tool == 'Make Wall':
                # exception, button
                target.click()
            else:
                target.setChecked(state)

    def check_changed(self) -> None | str:
        if not self.current_control:
            return None
        if not self.dialog:
            return None
        if not self.content:
            return None
        return self.current_control

    def apply_values(self):
        if self.dialog:
            try:
                self.dialog.accept()
            except BaseException:
                pass

        # # the ability to continue working with the panel
        # if self.active_object:
        #     if self.current_control in tools_before:
        #         Gui.Selection.clearSelection()
        #         Gui.Selection.addSelection(FreeCAD.ActiveDocument.Name,
        #                                    self.active_object.Tip.Name, '')
        #         self.preparation_panel('Secondary', '')
        #         position_local = self.parent.mapFromGlobal(
        #             self.position_current)
        #         self.collapse()
        #         self.activate(position_local)
        #         return

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
        Logger.info('SmartHUD: disabled')

if init:
    overlay = SmartHUD(app)
    overlay.adjustSize()
    Logger.info('SmartHUD: activated')
