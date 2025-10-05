# -*- coding: utf-8 -*-
# Copyright 2025 Golodnikov Sergey


import addFC_Preference as P
import FreeCAD
import os


class addFC(FreeCAD.Gui.Workbench):

    MenuText = 'addFC'
    ToolTip = 'addFC Workbench'
    Icon = os.path.join(P.AFC_PATH_ICON, 'workbench.svg')

    import freecad.Additional_Tools.addFC

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
            'AddFCAssistant',
        ]

        self.appendToolbar('addFC', self.list)
        self.appendMenu('addFC', self.list)

        global P

        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceProperties, 'addFC')
        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceMaterials, 'addFC')
        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceSM, 'addFC')
        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceOther, 'addFC')

        FreeCAD.Gui.addIconPath(P.AFC_PATH_ICON)

        font = P.pref_configuration['interface_font']
        if font[0] and font[1] != '':
            from PySide import QtGui
            QtGui.QApplication.setFont(QtGui.QFont(font[1], font[2]))

        # application theme:
        pref_str = 'User parameter:BaseApp/Preferences/MainWindow'
        app_theme = str(FreeCAD.ParamGet(pref_str).GetString('Theme')).lower()
        if 'dark' in app_theme:
            P.afc_theme['current'] = 'dark'
        elif 'light' in app_theme:
            P.afc_theme['current'] = 'light'
        else:
            P.afc_theme['current'] = 'std'

    def Activated(self):
        return

    def Deactivated(self):
        return

    def ContextMenu(self, recipient):
        self.appendContextMenu('addFC', self.list)

    def GetClassName(self):
        return 'Gui::PythonWorkbench'


FreeCAD.Gui.addWorkbench(addFC())
