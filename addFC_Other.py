# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


from PySide import QtGui
import FreeCAD
import re


DIGIT = re.compile('\\d+')

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


# required for correct recalculation of configuration tables in FreeCAD 0.21
def recompute_configuration_tables() -> None:
    for doc in FreeCAD.listDocuments():
        objects = FreeCAD.getDocument(doc).findObjects('Spreadsheet::Sheet')
        for obj in objects:
            for e in obj.ExpressionEngine:
                s = e[0][len('.cells.Bind.'):].split('.')[0]
                d = re.search(DIGIT, s).group(0)
                c = ALPHABET[ALPHABET.index(s.replace(d, '')) - 1] + d
            obj.recomputeCells(c)
    FreeCAD.ActiveDocument.recompute()


def error(message: str, header: str = 'ERROR') -> None:
    QtGui.QMessageBox.critical(
        None,
        header,
        message,
        QtGui.QMessageBox.StandardButton.Ok,
    )
