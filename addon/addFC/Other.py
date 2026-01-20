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
                d = re.search(DIGIT, s)
                if d is not None:
                    d = d.group(0)
                    c = ALPHABET[ALPHABET.index(s.replace(d, '')) - 1] + d
                    obj.recomputeCells(c)


def error(message: str, header: str = 'ERROR') -> None:
    QtGui.QMessageBox.critical(
        None,
        header,
        message,
        QtGui.QMessageBox.StandardButton.Ok,
    )
