# -*- coding: utf-8 -*-
# Copyright 2026 Golodnikov Sergey


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
