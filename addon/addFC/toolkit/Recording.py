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


from datetime import datetime
from PySide import QtCore
import FreeCAD
import os

from addon.addFC.Data import video_pref_std
from addon.addFC.Other import video_export_settings, video_make, open
import addon.addFC.Preference as P


CCS_STR = 'User parameter:BaseApp/Preferences/View'

ALLOWED_TYPES = (
    'App::Part',
    'Assembly::AssemblyObject',
    'Part::Compound',
    'PartDesign::Body',
)


class ViewportRecording():
    def __init__(self):
        self.form = FreeCAD.Gui.PySideUic.loadUi(
            os.path.join(os.path.dirname(__file__), 'Recording.ui'))

        self.ad = FreeCAD.ActiveDocument
        self.av = FreeCAD.Gui.activeDocument().activeView()

        self.axes = {
            'X': FreeCAD.Base.Vector(1, 0, 0),
            'Y': FreeCAD.Base.Vector(0, 1, 0),
            'Z': FreeCAD.Base.Vector(0, 0, 1),
        }

        self.timer = QtCore.QTimer()

        self.record = False
        self.frame = 0
        self.result = None
        self.start = None

        self.ccs = FreeCAD.ParamGet(CCS_STR).GetBool('CornerCoordSystem')

        # export settings:
        self.v_background = ''
        self.v_format = ''
        self.v_framerate = 60
        self.v_height = ''
        self.v_storyboard = ''
        self.v_width = ''
        self.preparation()

        self.form.comboBoxAxis.addItems(self.axes.keys())
        self.form.comboBoxAxis.setCurrentText('Z')

        def change_cycle(value):
            state = True if value % 2 == 0 else False
            self.form.checkBoxPendulum.setChecked(state)
            self.form.checkBoxPendulum.setEnabled(state)
        self.form.spinBoxCycles.valueChanged.connect(change_cycle)

        self.form.pushButtonES.clicked.connect(video_export_settings)

        objects = {}
        for obj in self.ad.findObjects():
            if obj.TypeId in ALLOWED_TYPES:
                objects[obj.Label] = obj

        self.form.comboBoxObject.addItems(objects.keys())

        selection = FreeCAD.Gui.Selection.getSelection()
        if selection:
            s = selection[0]
            if hasattr(s, 'Label'):
                if s.Label in objects:
                    self.form.comboBoxObject.setCurrentText(s.Label)

        self.form.pushButtonPreview.clicked.connect(
            lambda _: self.rotation(False))
        self.form.pushButtonExport.clicked.connect(
            lambda _: self.rotation(True))

        color_default = P.afc_theme_get('css-default')
        color_red = P.afc_theme_get('css-red')

        text_default = self.form.pushButtonRecord.text()

        def record_start():
            self.record = True
            self.form.pushButtonRecord.setEnabled(False)
            self.form.pushButtonStop.setEnabled(True)
            self.form.pushButtonStop.setFocus()
            self.form.pushButtonRecord.setStyleSheet(color_red)
            self.form.pushButtonRecord.setText(text_default + ' ...')
            self.start = datetime.now()
            self.free_camera_record()
        self.form.pushButtonRecord.clicked.connect(record_start)

        def record_stop():
            self.record = False
            self.form.pushButtonRecord.setEnabled(True)
            self.form.pushButtonStop.setEnabled(False)
            self.form.pushButtonRecord.setFocus()
            self.form.pushButtonRecord.setStyleSheet(color_default)
            self.form.pushButtonRecord.setText(text_default)
            stop = datetime.now()
            timestamp = '_'.join((
                self.start.strftime("%H:%M:%S"),
                stop.strftime("%H:%M:%S"),
            ))
            self.result = video_make(self.ad.Name, '_' + timestamp)
            if self.result is not None:
                self.form.pushButtonOpen.setEnabled(True)
        self.form.pushButtonStop.clicked.connect(record_stop)

        def open_file():
            if self.result is not None:
                open(self.result, True)
        self.form.pushButtonOpen.clicked.connect(open_file)

    # --------------------------------------------------------------------------

    def preparation(self):
        video_pref = P.load_pref(P.PATH_VIDEO, video_pref_std)
        self.v_background = video_pref['background']
        self.v_format = video_pref['image_format']
        self.v_framerate = int(video_pref['framerate'])
        self.v_height = video_pref['height']
        self.v_storyboard = video_pref['export_storyboard']
        self.v_width = video_pref['width']
        self.av = FreeCAD.Gui.activeDocument().activeView()
        self.ccs = FreeCAD.ParamGet(CCS_STR).GetBool('CornerCoordSystem')
        self.frame = 0
        if not os.path.exists(self.v_storyboard):
            os.makedirs(self.v_storyboard)

    def create_frame(self):
        self.frame += 1
        fn = str(self.frame).rjust(6, '0') + self.v_format
        fp = os.path.join(self.v_storyboard, fn)
        self.av.saveImage(fp, self.v_width, self.v_height, self.v_background)

    # --------------------------------------------------------------------------

    def free_camera_record(self):
        self.preparation()
        FreeCAD.ParamGet(CCS_STR).SetBool('CornerCoordSystem', False)
        self.timer.timeout.connect(self.capture_frame)
        self.timer.start(1000 / self.v_framerate)

    def capture_frame(self):
        if self.record:
            self.frame += 1
            self.create_frame()
        else:
            self.timer.stop()
            FreeCAD.ParamGet(CCS_STR).SetBool('CornerCoordSystem', self.ccs)

    # --------------------------------------------------------------------------

    def rotation(self, record: bool):
        target = self.form.comboBoxObject.currentText()
        objects = self.ad.getObjectsByLabel(target)
        if not objects:
            return  # todo: error

        object = objects[0]
        original = object.Placement
        base = original.Base
        if record:
            self.preparation()
            FreeCAD.ParamGet(CCS_STR).SetBool('CornerCoordSystem', False)

        angle = self.form.spinBoxAngle.value()
        vector = self.axes[self.form.comboBoxAxis.currentText()]
        pendulum = self.form.checkBoxPendulum.isChecked()
        cycles = self.form.spinBoxCycles.value()
        if pendulum:
            cycles = int(cycles / 2)

        for _ in range(cycles):
            for j in range(0, int(angle + 1), 1):
                if record:
                    self.create_frame()
                rotation = FreeCAD.Base.Rotation(vector, j)
                object.Placement = FreeCAD.Base.Placement(base, rotation)
                FreeCAD.Gui.updateGui()
            if pendulum:
                for j in range(int(angle) - 1, -1, -1):
                    if record:
                        self.create_frame()
                    rotation = FreeCAD.Base.Rotation(vector, j)
                    object.Placement = FreeCAD.Base.Placement(base, rotation)
                    FreeCAD.Gui.updateGui()

        object.Placement = original

        if record:
            FreeCAD.ParamGet(CCS_STR).SetBool('CornerCoordSystem', self.ccs)
            video_make(self.ad.Name, '')


vr = ViewportRecording()
FreeCAD.Gui.Control.showDialog(vr)
