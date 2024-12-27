# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


import addFC_Preference as P
import FreeCAD
import os


class addFC(FreeCAD.Gui.Workbench):

    MenuText = 'addFC'
    ToolTip = 'addFC Workbench'
    Icon = os.path.join(P.AFC_PATH_ICON, 'workbench.svg')

    import addFC

    def Initialize(self):
        self.list = [
            # core:
            'AddFCOpenRecentFile',
            'AddFCDisplay',
            'AddFCModelControl',
            'AddFCSpecification',
            'AddFCProperties',
            'AddFCInsert',
            'AddFCAssistant',
            # utils:
            'AddFCLibrary',
            'AddFCExplode',
            'AddFCPipe',
        ]

        self.appendToolbar('addFC', self.list)
        self.appendMenu('addFC', self.list)

        global P

        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceSpecification, 'addFC')
        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceMaterials, 'addFC')
        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceSM, 'addFC')
        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceOther, 'addFC')

        FreeCAD.Gui.addIconPath(P.AFC_PATH_ICON)

        font = P.pref_configuration['interface_font']
        if font[0] and font[1] != '':
            from PySide import QtGui
            QtGui.QApplication.setFont(QtGui.QFont(font[1], font[2]))

    def Activated(self): return

    def Deactivated(self): return

    def ContextMenu(self, recipient):
        self.appendContextMenu('addFC', self.list)

    def GetClassName(self): return 'Gui::PythonWorkbench'


FreeCAD.Gui.addWorkbench(addFC())
