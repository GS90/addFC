# -*- coding: utf-8 -*-
# Copyright 2026 Golodnikov Sergey


import FreeCAD
import ImportGui
import math
import Mesh
import MeshPart
import os
import Part
import re
import shutil
import stepZ
import time

import Logger
import Preference as P


REPRODUCTION = 'Reproduction'

ZERO = FreeCAD.Placement()

FORBIDDEN = re.escape('<>:"?*/|\\')


def export_list(file: str, quantity: int | None, ext: str) -> list:
    if quantity is None:
        return [file + '.' + ext,]
    else:
        files = []
        for i in range(quantity):
            files.append(f'{file} ({i + 1}).{ext}')
        return files


def batch_export_3d(w, parts: dict, path: str, skip: list, binding: dict):
    if len(parts) == 0 or len(parts) == len(skip):
        w.progressExport.setValue(100)
        w.statusExport.setText(FreeCAD.Qt.translate(
            'addFC', 'No objects for export'))
        return

    ad = FreeCAD.ActiveDocument

    tessellation = P.pref_configuration['tessellation']

    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

    name_variant = w.comboBoxExportName.currentText()

    progress_value = 0
    progress_step = int(100 / (len(parts) - len(skip)))

    start = time.time()
    w.progressExport.setValue(progress_value)
    FreeCAD.Gui.updateGui()

    doc = FreeCAD.newDocument(label='Export', hidden=True)

    for p in parts:

        if p in skip:
            continue

        spec, purpose = parts[p], binding[p]

        w.statusExport.setText(f'Processing: {p}')
        FreeCAD.Gui.updateGui()

        trace = spec['!Trace'][0]
        obj = FreeCAD.getDocument(trace[0]).getObject(trace[1])

        path_dir = path
        if w.checkBoxSaveByType.isChecked():
            t = re.sub(FORBIDDEN, '_', spec.get('Type', ''))
            if t != '':
                path_dir = os.path.join(path, t)
                if not os.path.exists(path_dir):
                    os.makedirs(path_dir)

        file, code, index = re.sub(FORBIDDEN, '_', p), '', ''

        if 'Code' in spec and spec['Code'] != '':
            code = re.sub(FORBIDDEN, '_', spec['Code'])
        if 'Index' in spec and spec['Index'] != '':
            index = re.sub(FORBIDDEN, '_', spec['Index'])

        match name_variant:
            case 'Code':
                if code != '':
                    file = code
            case 'Index':
                if index != '':
                    file = index
            case 'Code + Name':
                if code != '':
                    file = f'({code}) {file}'
            case 'Index + Name':
                if index != '':
                    file = f'({index}) {file}'

        quantity = None
        if w.checkBoxSaveCopies.isChecked():
            if spec.get('Unit', '-') == '-':
                quantity = int(spec['Quantity'])

        files = export_list(file, quantity, purpose[1])

        match purpose[0]:
            # print:
            case 'p':
                # reproduction:
                shape = Part.getShape(
                    obj, '', needSubElement=False, refine=False)
                body = doc.addObject('Part::Feature', REPRODUCTION)
                body.Shape = shape
                body.Placement = ZERO
                body.recompute(True)
                # mesher:
                mesh = doc.addObject('Mesh::Feature', 'Mesh')
                if tessellation['mesher'] == 'mefisto':
                    mesh.Mesh = MeshPart.meshFromShape(
                        Shape=Part.getShape(body),
                        MaxLength=tessellation['max_length'])
                else:
                    _ad = math.radians(tessellation['angular_deflection'])
                    mesh.Mesh = MeshPart.meshFromShape(
                        Shape=Part.getShape(body),
                        LinearDeflection=tessellation['linear_deflection'],
                        AngularDeflection=_ad,
                        Relative=False)
                mesh.recompute(True)
                # export:
                match purpose[1]:
                    case 'stl' | '3mf':
                        for f in files:
                            Mesh.export([mesh], os.path.join(path_dir, f))
                    case _:
                        Logger.error(f'"{p}" unknown format: {purpose[1]}')
                # cleaning:
                objects = doc.findObjects()
                objects.reverse()
                for obj in objects:
                    try:
                        doc.removeObject(obj.Name)
                    except BaseException:
                        pass
            # vector:
            case 'v':
                match purpose[1]:
                    case 'step':
                        for f in files:
                            ImportGui.export([obj], os.path.join(path_dir, f))
                    case 'stpZ':
                        for f in files:
                            stepZ.export([obj], os.path.join(path_dir, f))
                    case 'iges':
                        for f in files:
                            Part.export([obj], os.path.join(path_dir, f))
                    case _:
                        Logger.error(f'"{p}" unknown format: {purpose[1]}')
            # graphics:
            case 'g':
                match purpose[1]:
                    case 'glb':
                        for f in files:
                            ImportGui.export([obj], os.path.join(path_dir, f))
                    case _:
                        Logger.error(f'"{p}" unknown format: {purpose[1]}')
            case _:
                Logger.error(f'"{p}" unknown type: {purpose[0]}')

        progress_value += progress_step
        w.progressExport.setValue(progress_value)
        FreeCAD.Gui.updateGui()

    doc.clearDocument()
    FreeCAD.closeDocument(doc.Name)
    FreeCAD.setActiveDocument(ad.Name)

    w.progressExport.setValue(100)
    stop = time.strftime('%M:%S', time.gmtime(time.time() - start))
    w.statusExport.setText(f'Export completed, time - {stop}')

    FreeCAD.Gui.updateGui()
