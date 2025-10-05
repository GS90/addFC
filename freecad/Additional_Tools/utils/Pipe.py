# -*- coding: utf-8 -*-
# Copyright 2025 Golodnikov Sergey


from freecad.Additional_Tools.Other import error
from PySide import QtCore
import Arch
import Draft
import FreeCAD
import os
import Part


ad = FreeCAD.activeDocument()


PIPE_VARIATIONS = {
    'Other': {'Other': (20.0, 1.0)},  # default

    'OD - Copper pipe': {
        # thread: (outer diameter, wall thickness)
        '1/4"': (6.35, 0.76),
        '3/8"': (9.52, 0.81),
        '1/2"': (12.70, 0.81),
        '5/8"': (15.90, 0.90),
        '3/4"': (19.05, 0.89),
        '7/8"': (22.23, 1.14),
        '1"': (25.40, 1.14),
        '1 1/8"': (28.58, 1.27),
        '1 3/8"': (34.93, 1.40),
        '1 5/8"': (41.27, 1.53),
        '2 1/8"': (53.98, 1.78),
        '2 5/8"': (66.68, 2.03),
        '3 1/8"': (79.39, 2.30),
        '3 5/8"': (92.08, 2.54),
        '4 1/8"': (104.74, 2.80),
    },
    'DN - Nominal pipe size': {
        # nominal diameter: outer diameter
        'DN 6': 10.29,
        'DN 8': 13.72,
        'DN 10': 17.15,
        'DN 15': 21.34,
        'DN 20': 26.67,
        'DN 25': 33.40,
        'DN 32': 42.16,
        'DN 40': 48.26,
        'DN 50': 60.33,
        'DN 65': 73.03,
        'DN 80': 88.90,
        'DN 90': 101.60,
        'DN 100': 114.30,
        'DN 115': 127.00,
        'DN 125': 141.30,
        'DN 150': 168.28,
        'DN 200': 219.08,
        'DN 250': 273.05,
        'DN 300': 323.85,
        'DN 350': 355.60,
        'DN 400': 406.40,
        'DN 450': 457.20,
        'DN 500': 508.00,
        'DN 550': 558.80,
        'DN 600': 609.60,
        'DN 650': 660.40,
        'DN 700': 711.20,
        'DN 750': 762.00,
        'DN 800': 812.80,
        'DN 850': 863.60,
        'DN 900': 914.40,
        'DN 1000': 1016.00,
        'DN 1050': 1066.80,
        'DN 1100': 1117.60,
        'DN 1150': 1168.40,
        'DN 1200': 1219.20,
        'DN 1300': 1320.80,
        'DN 1400': 1422.40,
        'DN 1500': 1524.00,
        'DN 1600': 1625.60,
        'DN 1700': 1727.20,
        'DN 1800': 1828.80,
        'DN 1900': 1930.40,
        'DN 2000': 2032.00,
        'DN 2200': 2235.20,
        'DN 2300': 2336.80,
        'DN 2400': 2438.40,
        'DN 2500': 2540.00,
        'DN 2600': 2641.60,
        'DN 2700': 2743.20,
    },
    'DN - ВГП (водогазопроводная)': {
        # диаметр условного прохода: внешний диаметр
        'DN 6': 10.2,
        'DN 8': 13.5,
        'DN 10': 17.0,
        'DN 15': 21.3,
        'DN 20': 26.8,
        'DN 25': 33.5,
        'DN 32': 42.3,
        'DN 40': 48.0,
        'DN 50': 60.0,
        'DN 65': 75.5,
        'DN 80': 88.5,
        'DN 90': 101.3,
        'DN 100': 114.0,
        'DN 125': 140.0,
        'DN 150': 165.0,
    },
}


PIPE_MATERIALS = {
    'Default': (None, None),
    'Copper': (tuple(int('d78866'[i:i + 2], 16) for i in (0, 2, 4)), 8900),
    'Plastic': (tuple(int('d2d2d2'[i:i + 2], 16) for i in (0, 2, 4)), 900),
    'Steel': (tuple(int('b4c0c8'[i:i + 2], 16) for i in (0, 2, 4)), 7800),
}

PIPE_MATERIALS_FITTINGS = (
    tuple(int('cc6c54'[i:i + 2], 16) for i in (0, 2, 4)), 8900,
)


PIPE_RELATIONSHIP = {
    'Other': 'Default',
    'OD - Copper pipe': 'Copper',
    'DN - Nominal pipe size': 'Steel',
    'DN - ВГП (водогазопроводная)': 'Steel',
}


ROTATIONS = {
    # X
    '+X+Y': FreeCAD.Rotation(FreeCAD.Vector(0.00, 0.00, 1.00), 180.00),
    '+X+Z': FreeCAD.Rotation(FreeCAD.Vector(0.58, 0.58, 0.58), -120.00),
    '+X-Y': FreeCAD.Rotation(FreeCAD.Vector(0.00, 0.00, 1.00), -90.00),
    '+X-Z': FreeCAD.Rotation(FreeCAD.Vector(-0.58, -0.58, 0.58), 240.00),
    '-X+Y': FreeCAD.Rotation(FreeCAD.Vector(1.00, 0.00, 0.00), 180.00),
    '-X+Z': FreeCAD.Rotation(FreeCAD.Vector(1.00, 0.00, 0.00), 270.00),
    '-X-Y': FreeCAD.Rotation(FreeCAD.Vector(0.00, 0.00, 1.00), 0.00),
    '-X-Z': FreeCAD.Rotation(FreeCAD.Vector(0.00, -1.00, 0.00), 90.00),
    # Y
    '+Y+X': FreeCAD.Rotation(FreeCAD.Vector(0.00, 0.00, 1.00), 0.00),
    '+Y+Z': FreeCAD.Rotation(FreeCAD.Vector(0.00, 1.00, 0.00), -90.00),
    '+Y-X': FreeCAD.Rotation(FreeCAD.Vector(0.00, -1.00, 0.00), 180.00),
    '+Y-Z': FreeCAD.Rotation(FreeCAD.Vector(0.00, 1.00, 0.00), 90.00),
    '-Y+X': FreeCAD.Rotation(FreeCAD.Vector(1.00, 0.00, 0.00), 180.00),
    '-Y+Z': FreeCAD.Rotation(FreeCAD.Vector(0.71, 0.00, 0.71), 180.00),
    '-Y-X': FreeCAD.Rotation(FreeCAD.Vector(0.00, 0.00, 1.00), 180.00),
    '-Y-Z': FreeCAD.Rotation(FreeCAD.Vector(-0.71, 0.00, 0.71), 180.00),
    # Z
    '+Z+X': FreeCAD.Rotation(FreeCAD.Vector(-1.00, 0.00, 0.00), 270.00),
    '+Z+Y': FreeCAD.Rotation(FreeCAD.Vector(0.58, 0.58, 0.58), -240.00),
    '+Z-X': FreeCAD.Rotation(FreeCAD.Vector(0.00, 0.71, 0.71), -180.00),
    '+Z-Y': FreeCAD.Rotation(FreeCAD.Vector(-0.58, 0.58, 0.58), 240.00),
    '-Z+X': FreeCAD.Rotation(FreeCAD.Vector(1.00, 0.00, 0.00), 270.00),
    '-Z+Y': FreeCAD.Rotation(FreeCAD.Vector(-0.58, -0.58, 0.58), 120.00),
    '-Z-X': FreeCAD.Rotation(FreeCAD.Vector(0.00, -0.71, 0.71), 180.00),
    '-Z-Y': FreeCAD.Rotation(FreeCAD.Vector(-0.58, 0.58, -0.58), 120.00),
}


fittings = {
    'allowed': False,
    'color': None,
    'parent': '',
    'pipe': '',
    'points': [],
    'thread': '',
}


def detect_rotation(uno, dos, tres) -> FreeCAD.Rotation | bool:
    r = ''
    # input:
    if uno.x < dos.x:
        r += '+X'
    elif uno.x > dos.x:
        r += '-X'
    else:
        if uno.y < dos.y:
            r += '+Y'
        elif uno.y > dos.y:
            r += '-Y'
        else:
            if uno.z < dos.z:
                r += '+Z'
            elif uno.z > dos.z:
                r += '-Z'
    # output:
    if dos.x < tres.x:
        r += '+X'
    elif dos.x > tres.x:
        r += '-X'
    else:
        if dos.y < tres.y:
            r += '+Y'
        elif dos.y > tres.y:
            r += '-Y'
        else:
            if dos.z < tres.z:
                r += '+Z'
            elif dos.z > tres.z:
                r += '-Z'
    # result:
    return ROTATIONS[r] if r in ROTATIONS else False


def dialog() -> None:
    sl = FreeCAD.Gui.Selection.getSelection()[0]
    match sl.TypeId:
        case 'App::Part' | 'App::DocumentObjectGroup':
            pass
        case _:
            error('Invalid type!\nAvailable types: part, group.')
            return

    w = FreeCAD.Gui.PySideUic.loadUi(os.path.join(
        os.path.normpath(os.path.dirname(__file__)), 'Pipe.ui'))
    w.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    w.comboBoxVariations.addItems(PIPE_VARIATIONS.keys())
    w.comboBoxMaterial.addItems(PIPE_MATERIALS.keys())

    w.show()

    default_value = ('Other', 'Other')

    def select_variation(select) -> None:
        w.comboBoxPipe.clear()
        w.comboBoxPipe.addItems(PIPE_VARIATIONS[select])
        w.comboBoxMaterial.setCurrentText(PIPE_RELATIONSHIP[select])
    w.comboBoxVariations.currentTextChanged.connect(select_variation)
    select_variation(default_value[0])

    def select_pipe(select) -> None:
        if select != '':
            pipe = PIPE_VARIATIONS[w.comboBoxVariations.currentText()][select]
            global fittings
            if type(pipe) is tuple:  # default value or copper pipe
                diameter, radius = pipe[0], pipe[0]
                thickness = pipe[1]
                if select != 'Other':  # copper pipe
                    fittings['thread'] = select
            else:
                diameter = pipe
                # minimum bending radius of the pipe:
                if diameter < 20:
                    radius = diameter * 2.5 + diameter / 2
                else:
                    radius = diameter * 3.5 + diameter / 2
                thickness = (pipe - int(select.replace('DN ', ''))) / 2
                fittings['thread'] = ''
            w.doubleSpinBoxDiameter.setValue(diameter)
            w.doubleSpinBoxRadius.setValue(radius)
            w.doubleSpinBoxThickness.setValue(thickness)
    w.comboBoxPipe.currentTextChanged.connect(select_pipe)
    select_pipe(default_value[1])

    def fittings_add() -> None:
        add_fittings()
        w.addFittings.setEnabled(fittings['allowed'])
    w.addFittings.clicked.connect(fittings_add)
    w.addFittings.setEnabled(fittings['allowed'])

    def fittings_remove() -> None:
        remove_fittings()
        w.addFittings.setEnabled(fittings['allowed'])
    w.removeFittings.clicked.connect(fittings_remove)

    def create() -> None:
        remove_fittings()
        try:
            create_pipe(
                w.doubleSpinBoxDiameter.value(),
                w.doubleSpinBoxRadius.value(),
                w.doubleSpinBoxThickness.value(),
                PIPE_MATERIALS[w.comboBoxMaterial.currentText()][0],
                PIPE_MATERIALS[w.comboBoxMaterial.currentText()][1])
            w.addFittings.setEnabled(fittings['allowed'])
        except Exception as e:
            error(str(e))

    w.pushButtonCreate.clicked.connect(create)


def create_pipe(diameter: float,
                radius: float,
                thickness: float,
                color: tuple,
                density: tuple) -> None:

    group, weight = 'Add_', 'Add_Weight'

    sl = FreeCAD.Gui.Selection.getSelection()
    if len(sl) < 1:
        raise Exception('No objects selected.')
    sl = sl[0]

    src, points, properties = [], [], {}

    for g in sl.Group:
        if 'Pipe' in g.Label:
            for i in g.PropertiesList:
                if group in i and i != weight:
                    properties[i] = (
                        g.getTypeIdOfProperty(i), i, g.dumpPropertyContent(i))
            try:
                ad.removeObject(g.Base.Name)
            except BaseException:
                pass
            ad.removeObject(g.Name)
        elif g.TypeId == 'Part::FeaturePython':
            src.append(g.Label)
        elif g.TypeId == 'PartDesign::Body':
            for i in g.Group:
                if i.TypeId == 'PartDesign::Point':
                    src.append(i.Label)

    ad.recompute()

    if len(src) < 2:
        raise Exception('Two or more points are needed.')

    for i in sorted(src):
        o = ad.getObjectsByLabel(i)[0]
        match o.TypeId:
            case 'Part::FeaturePython':
                points.append(o.Placement.Base)
            case 'PartDesign::Point':
                points.append(o.getGlobalPlacement().Base)

    wire = Draft.make_wire(points)
    wire.FilletRadius = radius
    pipe = Arch.makePipe(wire, diameter)
    pipe.WallThickness = thickness

    ad.recompute()

    pipe.adjustRelativeLinks(sl)
    sl.addObject(pipe)

    global fittings
    fittings['color'] = None
    fittings['parent'] = sl.Label
    fittings['points'] = points
    fittings['pipe'] = pipe.Label
    if fittings['thread'] != '':
        fittings['allowed'] = True

    if color is not None:
        pipe.ViewObject.ShapeColor = tuple(i / 255 for i in color)
        fittings['color'] = PIPE_MATERIALS_FITTINGS[0]

    if density is not None:
        pipe.addProperty('App::PropertyFloat', weight, 'Add')
        pipe.setExpression(weight, ''.join((
            f'(pi * {density} * WallThickness.Value * (Diameter.Value - ',
            'WallThickness.Value) * Length.Value) / 10 ^ 9')))

    for i in properties:
        pipe.addProperty(properties[i][0], properties[i][1], group)
        pipe.restorePropertyContent(properties[i][1], properties[i][2])

    ad.recompute()
    FreeCAD.Gui.Selection.clearSelection()
    FreeCAD.Gui.Selection.addSelection(sl)


def remove_fittings() -> None:
    group = []
    for i in FreeCAD.ActiveDocument.findObjects():
        if '_fittings' in i.Label and i.TypeId == 'App::DocumentObjectGroup':
            for j in i.Group:
                group.append(j.Name)
            group.append(i.Name)
    for i in group:
        ad.removeObject(i)
    global fittings
    if fittings['pipe'] != '':
        fittings['allowed'] = True
    ad.recompute()


def add_fittings() -> None:
    pd = os.path.join(os.path.normpath(
        os.path.dirname(__file__)), 'Pipe.FCStd')
    d = FreeCAD.openDocument(pd, True)
    FreeCAD.setActiveDocument(ad.Name)

    global fittings

    # group:
    group_name = f'{fittings["pipe"]}_fittings'
    try:
        group = ad.getObjectsByLabel(group_name)[0]
    except BaseException:
        group = ad.addObject('App::DocumentObjectGroup', group_name)
    parent = ad.getObjectsByLabel(fittings['parent'])[0]
    group.adjustRelativeLinks(parent)
    parent.addObject(group)

    # configuration:
    d.Body.Conf = 'Thread ' + fittings['thread'].replace('"', '')
    d.recompute()

    x = 1
    for i in fittings['points'][1:-1]:
        rotation = detect_rotation(
            fittings['points'][x - 1],
            fittings['points'][x],
            fittings['points'][x + 1]
        )
        if not rotation:
            x += 1
            continue
        shape = Part.getShape(d.Body, '', needSubElement=False, refine=True)
        ad.addObject('Part::Feature', f'{d.Body.Label}_{x}').Shape = shape
        if fittings['color'] is not None:
            color = tuple(i / 255 for i in fittings['color'])
            ad.ActiveObject.ViewObject.ShapeColor = color
        ad.ActiveObject.Placement.Base = i
        ad.ActiveObject.Placement.Rotation = rotation
        x += 1
        # adding to a group:
        ad.ActiveObject.adjustRelativeLinks(group)
        group.addObject(ad.ActiveObject)

    fittings['allowed'] = False
    FreeCAD.closeDocument(d.Name)
    ad.recompute()


dialog()
