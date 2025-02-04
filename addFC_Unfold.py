# -*- coding: utf-8 -*-
# Copyright 2025 Golodnikov Sergey


import addFC_Logger as Logger
import addFC_Preference as P
import FreeCAD
import importDXF
import ImportGui
import importSVG
import os
import Part
import re
import shutil
import time


if P.afc_additions['ezdxf'][0]:
    import ezdxf.filemanagement
else:
    ezdxf = None


REPRODUCTION = 'Reproduction'

UNFOLD_OBJECT = 'Unfold'
UNFOLD_SKETCH = 'Unfold_Sketch'

FORBIDDEN = re.escape('<>:"?*/|\\')


def dxf_postprocessor(file, sign: str, bb) -> None:
    if ezdxf is None:
        return
    file = ezdxf.filemanagement.readfile(file)

    # cleaning:
    file.layers.remove('none')
    file.layers.remove('Defpoints')
    if sign == '':
        file.save()
        return

    # signing:
    model = file.modelspace()
    x, y = bb.XLength, bb.YLength

    size = int(abs(x) / len(sign))
    size = max(2, min(size, 200))
    size_verify = int(abs(y) - 10)
    if size > size_verify:
        size = size_verify

    sign_width = len(sign) * (size / 100 * 87)  # theoretical width...

    x = int(bb.Center.x - sign_width / 2)
    y = int(bb.Center.y - size / 2)

    model.add_text(sign,
                   height=size,
                   dxfattribs={'layer': 'Text'}).set_placement((x, y))
    file.save()


def cleaning(garbage: tuple, skip: str = '') -> None:
    for i in garbage:
        if i != skip:
            try:
                FreeCAD.ActiveDocument.removeObject(i)
            except BaseException:
                pass


def unfold(w, details: dict, path: str, skip: list = []) -> None:

    if len(details) == 0 or len(details) == len(skip):
        w.progress.setValue(100)
        w.status.setText('No sheet metal parts')
        return

    # checking the functionality:
    if not P.afc_additions['sm'][0]:
        w.error.setText('Warning: SheetMetal Workbench is not available!')
        return
    try:
        from SheetMetalUnfoldCmd import SMUnfoldUnattendedCommandClass as u
    except ImportError as error:
        P.afc_additions['sm'] = [False, '', 'color: #aa0000']
        Logger.error(error)
        return

    # unfolder, version check:
    if P.FC_VERSION[0] == '0' and int(P.FC_VERSION[1]) < 21:
        new_unfolder = False
    else:
        if FreeCAD.ParamGet(
                'User parameter:BaseApp/Preferences/Mod/SheetMetal').GetBool(
                'UseOldUnfolder'):
            new_unfolder = False
        else:
            new_unfolder = True

    # required values:
    if new_unfolder:
        sketch_verification = UNFOLD_SKETCH
        garbage = (
            # case sensitive!
            REPRODUCTION,
            sketch_verification,
            'Unfold_Sketch_Bends',
            'Unfold_Sketch_Holes',
            'Unfold_Sketch_Internal',
            UNFOLD_OBJECT,  # the object must be the last
        )
    else:
        sketch_verification = 'Unfold_Sketch_Outline'
        garbage = (
            # case sensitive!
            REPRODUCTION,
            UNFOLD_SKETCH,
            'Unfold_Sketch_Bends', 'Unfold_Sketch_bends',
            'Unfold_Sketch_Internal',
            sketch_verification,
            UNFOLD_OBJECT,  # the object must be the last
        )

    centering = w.checkBoxCentering.isChecked()
    along_x = w.checkBoxAlongX.isChecked()

    turn = FreeCAD.Rotation(FreeCAD.Vector(0.0, 0.0, 1.0), 90.0)

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

    zero = FreeCAD.Placement()

    doc = FreeCAD.newDocument(label='Unfold')
    getattr(w, "raise")()

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

        try:
            thickness = float(details[d]['MetalThickness'])
        except BaseException:
            Logger.error(f"'{d}' incorrect metal thickness, skip")
            continue

        try:
            material = details[d]['Material']
        except BaseException:
            material = 'Galvanized'  # default
            Logger.warning(
                f"'{d}' incorrect material, replaced by 'Galvanized'")

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
        shape = Part.getShape(
            details[d]['!Body'], '', needSubElement=False, refine=False)
        body = doc.addObject('Part::Feature', REPRODUCTION)
        body.Shape = shape
        body.Placement = zero
        body.recompute(True)

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
        FreeCAD.Gui.Selection.addSelection(doc.Name, body.Name, face, 0, 0, 0)

        # unfold:
        Logger.unfold(f'{d}: {material} ({thickness}) {k_factor}')
        u.Activated(None)
        FreeCAD.Gui.Selection.clearSelection()

        # unfold, parameters:
        unfold_obj = doc.getObject(UNFOLD_OBJECT)

        if not unfold_obj.GenerateSketch:
            unfold_obj.GenerateSketch = True
        if not unfold_obj.SeparateSketchLayers:
            unfold_obj.SeparateSketchLayers = True
        if not unfold_obj.ManualRecompute:
            unfold_obj.ManualRecompute = False

        if unfold_obj.KFactorStandard != 'aisi':
            unfold_obj.KFactorStandard = 'ansi'
        if unfold_obj.KFactor != k_factor:
            unfold_obj.KFactor = k_factor

        unfold_obj.recompute(True)

        # correctness check:
        if doc.getObject(sketch_verification) is None:
            # todo: how to check 'new_unfolder' correctly?
            Logger.warning("wrong, let's try a spare face...")
            cleaning(garbage, REPRODUCTION)
            # switching to spare:
            face = 'Face' + str(target[2])
            FreeCAD.Gui.Selection.addSelection(
                doc.Name, body.Name, face, 0, 0, 0)
            if u is not None:
                u.Activated(None)
            FreeCAD.Gui.Selection.clearSelection()
            # verify:
            if doc.getObject(sketch_verification) is None:
                cleaning(garbage)
                Logger.error(f"'{d}' unfold error... skip")
                continue

        us = doc.getObject(UNFOLD_SKETCH)
        if us is None:
            cleaning(garbage)
            Logger.error(f"'{d}' unfold error... skip")
            continue
        us.recompute(True)

        sketches = [us]
        if new_unfolder:
            for sketch in ('Unfold_Sketch_Holes', 'Unfold_Sketch_Internal'):
                obj = doc.getObject(sketch)
                if obj is not None:
                    obj.recompute(True)
                    if obj.Placement.Rotation.Angle == 0:
                        sketches[0].Geometry += obj.Geometry
                        sketches[0].recompute(True)
                    else:
                        along_x = False  # turning is prohibited
                        sketches.append(obj)

        bb = sketches[0].Shape.BoundBox

        if along_x and bb.XLength < bb.YLength:
            # position along the X axis:
            for sketch in sketches:
                sketch.Placement.Rotation = turn
                sketch.recompute(True)
            bb = sketches[0].Shape.BoundBox

        x = bb.Center.x if centering else bb.XMin
        x = abs(x) if x < 0 else -x
        y = bb.Center.y if centering else bb.YMin
        y = abs(y) if y < 0 else -y
        if round(x, 6) != 0 or round(y, 6) != 0:
            for sketch in sketches:
                sketch.Placement.Base.x = x
                sketch.Placement.Base.y = y
                sketch.Placement.Base.z = 0
                sketch.recompute(True)

        bb = sketches[0].Shape.BoundBox

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

        # save:
        for i in range(int(details[d]['Quantity'])):
            if save_dxf:
                f = os.path.join(target, f'{file} ({i + 1}).dxf')
                importDXF.export(sketches, f)
                # postprocessor:
                if P.afc_additions['ezdxf'][0]:
                    dxf_postprocessor(f, sign, bb)
            if save_svg:
                f = os.path.join(target, f'{file} ({i + 1}).svg')
                importSVG.export(sketches, f)
            if save_stp:
                f = os.path.join(target, f'{file} ({i + 1}).step')
                ImportGui.export([body], f)

        cleaning(garbage)
        Logger.log('...done')

        progress_value += progress_step
        w.progress.setValue(progress_value)
        FreeCAD.Gui.updateGui()

    doc.clearDocument()
    FreeCAD.closeDocument(doc.Name)
    getattr(w, "raise")()

    w.progress.setValue(100)
    stop = time.strftime('%M:%S', time.gmtime(time.time() - start))
    w.status.setText(f'Unfold completed, time - {stop}')

    FreeCAD.Gui.updateGui()
