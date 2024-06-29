# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


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


is_available_SMU: bool = True
is_available_ezdxf: bool = True

try:
    from SheetMetalUnfoldCmd import SMUnfoldUnattendedCommandClass as u
except ImportError:
    is_available_SMU = False

try:
    import ezdxf
except ImportError:
    is_available_ezdxf = False


garbage: tuple[str] = (
    # case sensitive!
    'Reproduction',
    'Unfold_Sketch_bends',
    'Unfold_Sketch_Internal',
    'Unfold_Sketch_Outline',
    'Unfold_Sketch',
    'Unfold',
)


chars: str = re.escape('<>:"?*/|\\')


def add_signature(file: str, sign: str, width: float, size: int) -> None:
    file = ezdxf.readfile(file)
    model = file.modelspace()
    x = -width / 2 + size / 2
    y = -size / 2
    model.add_text(sign, height=size).set_placement((x, y))
    file.save()


def unfold(w, details: dict, path: str, skip: list = []) -> None:
    # checking the functionality:
    if not is_available_SMU:
        w.error.setText('Error: SheetMetalUnfold is not available!')
        return
    if not is_available_ezdxf:
        w.error.setText('Warning: ezdxf is not available!')

    if len(details) == 0 or len(details) == len(skip):
        w.progress.setValue(100)
        w.status.setText('No sheet metal parts')
        return

    conf_steel = P.load_steel()

    # directory:
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

    save_dxf = w.DXF.isChecked()
    save_svg = w.SVG.isChecked()
    save_stp = w.STP.isChecked()

    signature = [False, '']  # prefix
    match w.comboBoxSignature.currentText():
        case 'Index':
            signature[0] = True
        case 'Prefix' | 'Prefix + Index':
            prefix = str(w.lineEditPrefix.text()).strip()
            if prefix != '':
                signature = [True, prefix]

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

        body = details[d]['Body']

        try:
            thickness = float(details[d]['MetalThickness'])
        except BaseException:
            FreeCAD.Console.PrintError(f'{d}: incorrect metal thickness\n')
            continue

        try:
            material = details[d]['Material']
        except BaseException:
            material = 'galvanized'  # default

        stainless = [False, '']  # [stainless, 'aisi']

        if 'stainless' in material.lower():
            stainless[0] = True
        if 'aisi' in material.lower():
            stainless[0] = True
            stainless[1] = material.lower().replace('aisi', '').strip()

        steel = [thickness, 0.5, '']  # thickness, k-factor, alias

        err = False
        if stainless[0]:
            v = []
            for key in conf_steel['stainless'].keys():
                try:
                    v.append(float(key))
                except BaseException:
                    err = True
            steel[0] = min(sorted(v), key=lambda n: abs(thickness - n))
            # float or string?
            if steel[0] in conf_steel['stainless']:
                _steel = conf_steel['stainless'][steel[0]]
            elif str(steel[0]) in conf_steel['stainless']:
                _steel = conf_steel['stainless'][str(steel[0])]
            else:
                err = True
            steel[1], steel[2] = _steel[0], _steel[1]
        else:
            v = []
            for key in conf_steel['galvanized'].keys():
                try:
                    v.append(float(key))
                except BaseException:
                    err = True
            steel[0] = min(sorted(v), key=lambda n: abs(thickness - n))
            # float or string?
            if steel[0] in conf_steel['galvanized']:
                _steel = conf_steel['galvanized'][steel[0]]
            elif str(steel[0]) in conf_steel['galvanized']:
                _steel = conf_steel['galvanized'][str(steel[0])]
            else:
                err = True
            steel[1], steel[2] = _steel[0], _steel[1]
        if err:
            e = f'{d}: error in sheet metal preference\n'
            FreeCAD.Console.PrintError(e)
            continue

        # alias:
        if steel[2] == '':
            steel[2] = str(thickness)
        if stainless[0]:
            if stainless[1] != '':
                steel[2] = f'{steel[2]}_{stainless[1]}'
        else:
            if material == 'Steel':
                steel[2] = f'{steel[2]}_Steel'

        # reproduction:
        shape = Part.getShape(body, '', needSubElement=False, refine=True)
        ad.addObject('Part::Feature', 'Reproduction').Shape = shape
        body = ad.ActiveObject

        # find the largest face:
        target = [0.0, 0]
        faces = body.Shape.Faces
        n = 0
        for f in faces:
            n += 1
            # TODO f.Orientation: Forward, Reversed
            if f.Area > target[0]:
                target[0] = f.Area
                target[1] = n

        # selection:
        FreeCAD.Gui.Selection.clearSelection()
        face = 'Face' + str(target[1])
        FreeCAD.Gui.Selection.addSelection(ad.Name, body.Name, face, 0, 0, 0)

        # k-factor:
        FreeCAD.ParamGet(
            'User parameter:BaseApp/Preferences/Mod/SheetMetal').SetFloat(
            'manualKFactor', steel[1])

        # unfold:
        msg = f'{d}: {material} ({steel[0]}) {steel[1]}\n'
        FreeCAD.Console.PrintMessage(msg)
        u.Activated(None)
        FreeCAD.Gui.Selection.clearSelection()

        # size:
        bb = ad.Unfold_Sketch_Outline.Shape.BoundBox

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
                ad.getObject('Unfold_Sketch').Placement = p
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
                ad.getObject('Unfold_Sketch').Placement = p
            except BaseException:
                pass

        # directory:
        target = os.path.join(path, steel[2])
        if not os.path.exists(target):
            os.makedirs(target)

        sign = signature[1]
        file = re.sub('[' + chars + ']', '_', d)

        if 'Index' in details[d] and details[d]['Index'] != '':
            index = re.sub('[' + chars + ']', '_', details[d]['Index'])
            if signature[0]:
                match w.comboBoxSignature.currentText():
                    case 'Index':
                        sign = index
                    case 'Prefix + Index':
                        sign = f'{signature[1]}_{index}'

        if w.comboBoxName.currentText() == 'Index':
            file = index
        elif w.comboBoxName.currentText() == 'Index + Name':
            file = f'({index}) {file}'

        # save:
        for i in range(int(details[d]['Quantity'])):
            if save_dxf:
                f = os.path.join(target, f'{file} ({i + 1}).dxf')
                importDXF.export([ad.getObject('Unfold_Sketch')], f)
                # signature:
                if signature[0]:
                    size = int(abs(unfold_width) / len(sign))
                    size = max(6, min(size, 120))
                    size_verify = int(abs(unfold_height) - 10)
                    if size > size_verify:
                        size = size_verify
                    if is_available_ezdxf:
                        add_signature(f, sign, unfold_width, size)
            if save_svg:
                f = os.path.join(target, f'{file} ({i + 1}).svg')
                importSVG.export([ad.getObject('Unfold_Sketch')], f)
            if save_stp:
                f = os.path.join(target, f'{file} ({i + 1}).step')
                ImportGui.export([body], f)

        # clearing:
        for i in garbage:
            try:
                ad.removeObject(i)
            except BaseException:
                pass

        FreeCAD.Console.PrintMessage('...done\n')

        progress_value += progress_step
        w.progress.setValue(progress_value)
        FreeCAD.Gui.updateGui()

    w.progress.setValue(100)

    stop = time.strftime('%M:%S', time.gmtime(time.time() - start))
    w.status.setText(f'Unfold completed, time - {stop}')

    FreeCAD.Gui.updateGui()
