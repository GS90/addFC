# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


import FreeCAD
import os
import addFC


add_base_path: str = os.path.dirname(addFC.__file__)
add_icon_path: str = os.path.join(add_base_path, 'repo', 'icon')


class addFC(FreeCAD.Gui.Workbench):

    global add_base_path, add_icon_path

    MenuText = 'addFC'
    ToolTip = 'addFC Workbench'
    Icon = os.path.join(add_icon_path, 'workbench.svg')

    def Initialize(self):
        self.list = [
            'AddFCOpenRecentFile',
            'AddFCDisplay',
            'AddFCModelControl',
            'AddFCSpecification',
            'AddFCProperties',
            'AddFCPipe',
            'AddFCExplode',
            'OpenExample',
        ]
        self.appendToolbar('addFC', self.list)
        self.appendMenu('addFC', self.list)

        import addFC_Preference as P

        P.save_configuration({})
        P.save_properties({}, init=True)
        P.save_steel({})
        P.save_explosion({})

        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceSpecification, 'addFC')
        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceSM, 'addFC')
        FreeCAD.Gui.addIconPath(add_icon_path)

    def Activated(self): return

    def Deactivated(self): return

    def ContextMenu(self, recipient):
        self.appendContextMenu('addFC', self.list)

    def GetClassName(self): return 'Gui::PythonWorkbench'


FreeCAD.Gui.addWorkbench(addFC())
