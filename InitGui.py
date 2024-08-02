# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


import addFC
import FreeCAD
import os


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
            'addFCInsert',
            'addFCAssistant',
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
        FreeCAD.Gui.addPreferencePage(P.addFCPreferenceOther, 'addFC')

        FreeCAD.Gui.addIconPath(add_icon_path)

        # interface font:
        conf = P.load_configuration()
        if 'interface_font' in conf:
            font = conf['interface_font']
            if font[0] and font[1] != '':
                from PySide import QtGui
                QtGui.QApplication.setFont(QtGui.QFont(font[1], font[2]))

    def Activated(self): return

    def Deactivated(self): return

    def ContextMenu(self, recipient):
        self.appendContextMenu('addFC', self.list)

    def GetClassName(self): return 'Gui::PythonWorkbench'


FreeCAD.Gui.addWorkbench(addFC())
