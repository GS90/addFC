# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


import addFC_Logger as Logger
import addFC_Preference as P
import FreeCAD
import importDXF
import ImportGui
import importSVG
import math
import os
import Part
import re
import shutil
import time


if P.afc_additions['sm'][0]:
    from SheetMetalUnfoldCmd import SMUnfoldUnattendedCommandClass as u
else:
    u = None

if P.afc_additions['ezdxf'][0]:
    import ezdxf.filemanagement
else:
    ezdxf = None


REPRODUCTION = 'Reproduction'
UNFOLD_SKETCH = 'Unfold_Sketch'
VERIFICATION_SKETCH = 'Unfold_Sketch_Outline'

GARBAGE = (
    # case sensitive!
    REPRODUCTION,
    UNFOLD_SKETCH,
    VERIFICATION_SKETCH,
    'Unfold_Sketch_bends',
    'Unfold_Sketch_Internal',
    'Unfold',  # object
)

FORBIDDEN = re.escape('<>:"?*/|\\')


def add_signature(file, sign: str, width: float, size: int) -> None:
    if ezdxf is None:
        return
    file = ezdxf.filemanagement.readfile(file)
    model = file.modelspace()
    x = -width / 2 + size / 2
    y = -size / 2
    model.add_text(sign, height=size).set_placement((x, y))
    file.save()


def unfold(w, details: dict, path: str, skip: list = []) -> None:
    # checking the functionality:
    if not P.afc_additions['sm'][0]:
        w.error.setText('Warning: SheetMetal Workbench is not available!')
        return
    if not P.afc_additions['ezdxf'][0]:
        w.error.setText('Warning: ezdxf is not available!')

    if len(details) == 0 or len(details) == len(skip):
        w.progress.setValue(100)
        w.status.setText('No sheet metal parts')
        return

    steel = P.pref_steel

    def nearest(scope, t) -> float:
        return scope[min(range(len(scope)), key=lambda i: abs(scope[i] - t))]

    # directory:
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

    save_dxf = w.DXF.isChecked()
    save_svg = w.SVG.isChecked()
    save_stp = w.STP.isChecked()

    signature = [False, '']  # prefix
    if w.comboBoxSignature.currentText() != 'None':
        signature[0] = True
        if 'Prefix' in w.comboBoxSignature.currentText():
            signature[1] = str(w.lineEditPrefix.text()).strip()

    ad = FreeCAD.ActiveDocument

    # required values:
    FreeCAD.ParamGet(
        'User parameter:BaseApp/Preferences/Mod/SheetMetal').SetString(
        'kFactorStandard', 'ansi')
    FreeCAD.ParamGet(
        'User parameter:BaseApp/Preferences/Mod/SheetMetal').SetBool(
        'genSketch', True)
    FreeCAD.ParamGet(
        'User parameter:BaseApp/Preferences/Mod/SheetMetal').SetBool(
        'separateSketches', True)
    FreeCAD.ParamGet(
        'User parameter:BaseApp/Preferences/Mod/SheetMetal').SetBool(
        'exportEn', False)

    progress_value = 0
    progress_step = int(100 / (len(details) - len(skip)))

    start = time.time()
    w.progress.setValue(progress_value)
    FreeCAD.Gui.updateGui()

    for d in details:

        if d in skip:
            continue

        w.status.setText(f'Processing: {d}')
        FreeCAD.Gui.updateGui()

        body = details[d]['!Body']

        try:
            thickness = float(details[d]['MetalThickness'])
        except BaseException:
            Logger.error(f"'{d}' incorrect metal thickness")
            continue

        try:
            material = details[d]['Material']
        except BaseException:
            material = 'Galvanized'  # default
            w = f"'{d}' incorrect material, replaced by 'Galvanized'"
            Logger.warning(w)

        if 'stainless' in material.lower() or 'aisi' in material.lower():
            variant = 'Stainless'
        else:
            variant = 'Galvanized'

        k_factor = 0.42

        if thickness in steel[variant]:
            k_factor = steel[variant][thickness][1]
        else:
            t = nearest(P.pref_steel['Stainless'], thickness)
            k_factor = steel['Stainless'][t][1]

        # reproduction:
        shape = Part.getShape(body, '', needSubElement=False, refine=False)
        ad.addObject('Part::Feature', REPRODUCTION).Shape = shape
        body = ad.ActiveObject

        # find the largest face:
        faces = body.Shape.Faces
        target = [0.0, 0, 0]  # [area, base, spare]
        a, n = 0, 0
        for f in faces:
            a = round(f.Area, 2)
            n += 1
            if a > target[0]:
                # spare:
                if target[1] == 0:
                    target[2] = n
                else:
                    target[2] = target[1]
                # base:
                target[0] = a
                target[1] = n
            elif a == target[0]:
                # spare:
                target[2] = n

        # selection:
        face = 'Face' + str(target[1])  # base
        FreeCAD.Gui.Selection.addSelection(ad.Name, body.Name, face, 0, 0, 0)

        # k-factor:
        FreeCAD.ParamGet(
            'User parameter:BaseApp/Preferences/Mod/SheetMetal').SetFloat(
            'manualKFactor', k_factor)

        # unfold:
        Logger.log(f'{d}: {material} ({thickness}) {k_factor}')
        if u is not None:
            u.Activated(None)
        FreeCAD.Gui.Selection.clearSelection()

        # correctness check:
        if ad.getObject(VERIFICATION_SKETCH) is None:
            Logger.warning("wrong, let's try a spare face...")
            for i in GARBAGE:
                try:
                    ad.removeObject(i)
                except BaseException:
                    pass
            # switching to spare:
            face = 'Face' + str(target[2])
            FreeCAD.Gui.Selection.addSelection(
                ad.Name, body.Name, face, 0, 0, 0)
            if u is not None:
                u.Activated(None)
            FreeCAD.Gui.Selection.clearSelection()
            # verify:
            if ad.getObject(VERIFICATION_SKETCH) is None:
                Logger.error(f"'{d}' unfold error...")
                continue

        us = ad.getObject(UNFOLD_SKETCH)
        bb = us.Shape.BoundBox

        # location along the Y axis:
        if bb.XLength < bb.YLength:
            unfold_width = math.ceil(bb.YLength)
            unfold_height = math.ceil(bb.XLength)
            # centering:
            x = bb.Center.y
            y = bb.Center.x
            y = abs(y) if y < 0 else -y
            # change position:
            r = FreeCAD.Rotation(FreeCAD.Vector(0.00, 0.00, 1.00), 90.00)
            p = FreeCAD.Placement(FreeCAD.Vector(x, y, 0.00), r)
            try:
                us.Placement = p
            except BaseException:
                pass
        else:
            unfold_width = math.ceil(bb.XLength)
            unfold_height = math.ceil(bb.YLength)
            # centering:
            x = bb.Center.x
            x = abs(x) if x < 0 else -x
            y = bb.Center.y
            y = abs(y) if y < 0 else -y
            # change position:
            r = FreeCAD.Rotation(FreeCAD.Vector(0.00, 0.00, 1.00), 0.00)
            p = FreeCAD.Placement(FreeCAD.Vector(x, y, 0.00), r)
            try:
                us.Placement = p
            except BaseException:
                pass

        # directory:
        target = os.path.join(path, f'{material} ({thickness})')
        if not os.path.exists(target):
            os.makedirs(target)

        file = re.sub(FORBIDDEN, '_', d)

        code, index, sign = '', '', signature[1]  # prefix

        if 'Code' in details[d] and details[d]['Code'] != '':
            code = re.sub(FORBIDDEN, '_', details[d]['Code'])
        if 'Index' in details[d] and details[d]['Index'] != '':
            index = re.sub(FORBIDDEN, '_', details[d]['Index'])

        match w.comboBoxName.currentText():
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

        if signature[0]:
            match w.comboBoxSignature.currentText():
                case 'Code':
                    if code != '':
                        sign = code
                case 'Prefix + Code':
                    if code != '':
                        sign = f'{signature[1]}_{code}'

        # checking empty signature:
        if sign == '':
            signature[0] = False

        # save:
        for i in range(int(details[d]['Quantity'])):
            if save_dxf:
                f = os.path.join(target, f'{file} ({i + 1}).dxf')
                importDXF.export([us], f)
                # signature:
                if signature[0] and len(sign) > 0:
                    size = int(abs(unfold_width) / len(sign))
                    size = max(6, min(size, 120))
                    size_verify = int(abs(unfold_height) - 10)
                    if size > size_verify:
                        size = size_verify
                    if P.afc_additions['ezdxf'][0]:
                        add_signature(f, sign, unfold_width, size)
            if save_svg:
                f = os.path.join(target, f'{file} ({i + 1}).svg')
                importSVG.export([us], f)
            if save_stp:
                f = os.path.join(target, f'{file} ({i + 1}).step')
                ImportGui.export([body], f)

        # clearing:
        for i in GARBAGE:
            try:
                ad.removeObject(i)
            except BaseException:
                pass

        Logger.log('...done')

        progress_value += progress_step
        w.progress.setValue(progress_value)
        FreeCAD.Gui.updateGui()

    w.progress.setValue(100)

    stop = time.strftime('%M:%S', time.gmtime(time.time() - start))
    w.status.setText(f'Unfold completed, time - {stop}')

    FreeCAD.Gui.updateGui()
