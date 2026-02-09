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


import FreeCAD
import os

import addon.addFC.Preference as P


class addFC(FreeCAD.Gui.Workbench):

    MenuText = 'addFC'
    ToolTip = 'addFC Workbench'
    Icon = os.path.join(P.AFC_DIR_ICON, 'workbench.svg')

    font = P.pref_configuration['interface_font']
    if font[0] and font[1] != '':
        from PySide import QtGui
        QtGui.QApplication.setFont(QtGui.QFont(font[1], font[2]))

    import addon.addFC.Main

    def Initialize(self):

        self.list = [
            'AddFCOpenRecentFile',
            'AddFCDisplay',
            'AddFCModelControl',
            'AddFCModelInfo',
            'AddFCProperties',
            'AddFCInsert',
            'AddFCLinker',
            'AddFCIsolation',
            'AddFCLibrary',
            'AddFCSummary',
            'AddFCExplode',
            'AddFCPipe',
            'AddFCViewer',
            'AddFCRecording',
            'AddFCHeadUpDisplay',
            'AddFCAssistant',
        ]

        self.appendToolbar('addFC', self.list)
        self.appendMenu('addFC', self.list)

        global P

        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceProperties, 'addFC')
        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceMaterials, 'addFC')
        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceSM, 'addFC')
        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceOther, 'addFC')
        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceRU, 'addFC')

        FreeCAD.Gui.addIconPath(P.AFC_DIR_ICON)

        # application theme:
        pref_str = 'User parameter:BaseApp/Preferences/MainWindow'
        app_theme = str(FreeCAD.ParamGet(pref_str).GetString('Theme')).lower()
        if 'dark' in app_theme:
            P.afc_theme['current'] = 'dark'
        elif 'light' in app_theme:
            P.afc_theme['current'] = 'light'
        else:
            P.afc_theme['current'] = 'std'

        if P.pref_configuration['hud_autoload']:
            from addon.addFC.Main import AddFCHeadUpDisplay
            AddFCHeadUpDisplay().Activated()

    def Activated(self):
        return

    def Deactivated(self):
        return

    def ContextMenu(self, recipient):
        self.appendContextMenu('addFC', self.list)

    def GetClassName(self):
        return 'Gui::PythonWorkbench'


FreeCAD.Gui.addWorkbench(addFC())
