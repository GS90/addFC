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


def info(message: str) -> None:
    FreeCAD.Console.PrintMessage(f'addFC, info: {message}\n')


def unfold(message: str) -> None:
    FreeCAD.Console.PrintMessage(f'addFC, unfold: {message}\n')


def warning(message: str) -> None:
    FreeCAD.Console.PrintWarning(f'addFC, warning: {message}\n')


def error(message: str) -> None:
    FreeCAD.Console.PrintError(f'addFC, error: {message}\n')


def log(message: str) -> None:
    FreeCAD.Console.PrintLog(message + '\n')
