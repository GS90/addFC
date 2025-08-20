# -*- coding: utf-8 -*-
# Copyright 2025 Golodnikov Sergey


from addFC_Data import summary as std_pref
from addFC_Logger import error as log_err
import addFC_Preference as P
import FreeCAD
import FreeCADGui as Gui
import os


freeze = True


units_weight = {
    'g': 1000000,
    'kg': 1000000000,
    't': 1000000000000,
}

units_length = {
    'mm': 1,
    'cm': 10,
    'm': 1000,
    'km': 1000000,
}

units_area = {
    'mm^2': 1,
    'cm^2': 100,
    'm^2': 1000000,
}

units_volume = {
    'mm^3': 1,
    'cm^3': 1000,
    'l': 1000000,
    'm^3': 1000000000,
}


# ------------------------------------------------------------------------------


class SelectionObserver:
    def addSelection(self, doc, obj, sub, pos):
        try:
            info.add_selection(doc, obj, sub)
            info.fill()
        except BaseException:
            Gui.Selection.removeObserver(self)

    def removeSelection(self, doc, obj, sub):
        try:
            info.remove_selection(doc, obj, sub)
            info.fill()
        except BaseException:
            Gui.Selection.removeObserver(self)

    def clearSelection(self, doc):
        try:
            info.clear_selection()
            info.fill()
        except BaseException:
            Gui.Selection.removeObserver(self)


observer = SelectionObserver()


# ------------------------------------------------------------------------------


class Info():
    area = 0
    bound_box = [0, 0, 0]
    center_of_MG = None
    conf = P.pref_configuration
    decimals = 2
    designation = ['', '', '']
    diagonal = 0
    diameter = 0
    length = 0
    materials = P.pref_materials
    objects = {}
    perimeter = 0
    radius = 0
    sub_title = ''
    subobjects = {}
    volume = 0
    weight = 0

    last_selection = None

    def __init__(self):
        self.form = Gui.PySideUic.loadUi(
            os.path.join(os.path.dirname(__file__), 'addFC_Summary.ui'))

        Gui.Selection.addObserver(observer)

        pref = P.load_pref(P.PATH_SUMMARY, std_pref)

        # decimals
        self.decimals = pref.get('Decimals', 2)
        self.form.Decimals.setValue(self.decimals)
        self.set_decimals()

        # units of measurement
        self.form.BB_U.addItems(units_length)
        self.form.Volume_U.addItems(units_volume)
        self.form.Weight_U.addItems(units_weight)
        self.form.Area_U.addItems(units_area)
        self.form.Perimeter_U.addItems(units_length)
        self.form.DLRD_U.addItems(units_length)

        # material
        self.form.Material.addItems(self.materials.keys())

        def change_material(value):
            material = self.materials.get(value, None)
            if material is None or value == '-':
                self.form.Material.setCurrentText('-')
                self.form.Density_Value.setEnabled(True)
                self.form.Density_Value.setValue(0)
            else:
                self.form.Material.setCurrentText(value)
                self.form.Density_Value.setEnabled(False)
                self.form.Density_Value.setValue(material[1])
            self.set_mass()

        self.form.Material.currentTextChanged.connect(change_material)

        def change_density():
            self.set_mass()
        self.form.Density_Value.valueChanged.connect(change_density)

        # previously used values
        self.form.Area_U.setCurrentText(pref['Area_U'])
        self.form.BB_U.setCurrentText(pref['BB_U'])
        self.form.DLRD_U.setCurrentText(pref['DLRD_U'])
        self.form.Perimeter_U.setCurrentText(pref['Perimeter_U'])
        self.form.Volume_U.setCurrentText(pref['Volume_U'])
        self.form.Weight_U.setCurrentText(pref['Weight_U'])
        change_material(pref.get('Material', '-'))

        # changing units of measurement
        def change_unit(target):
            match target:
                case 'bb': self.set_bb()
                case 'mass': self.set_mass()
                case 'so': self.set_subobjects_value()

        def change_unit_bb():
            change_unit('bb')

        def change_unit_mass():
            change_unit('mass')

        def change_unit_so():
            change_unit('so')

        self.form.BB_U.currentTextChanged.connect(change_unit_bb)
        self.form.Volume_U.currentTextChanged.connect(change_unit_mass)
        self.form.Weight_U.currentTextChanged.connect(change_unit_mass)
        self.form.Area_U.currentTextChanged.connect(change_unit_so)
        self.form.Perimeter_U.currentTextChanged.connect(change_unit_so)
        self.form.DLRD_U.currentTextChanged.connect(change_unit_so)

        # set the center of mass
        def set_com():
            if self.center_of_MG is None:
                return

            ad, obj = FreeCAD.ActiveDocument, None

            objects = ad.findObjects('Part::Sphere')
            for i in objects:
                if i.Label2 == self.center_of_MG[0]:
                    obj = i
                    break
            if obj is None:
                obj = ad.addObject('Part::Sphere', self.center_of_MG[4][0])
                obj.Label2 = self.center_of_MG[0]

            obj.ViewObject.ShapeColor = self.center_of_MG[4][1]
            obj.ViewObject.DisplayMode = 'Shaded'
            position = self.center_of_MG[1] + self.center_of_MG[3]
            obj.Placement.Base = position
            radius = round(
                self.center_of_MG[2] * self.form.CoMG_Size.value() / 100)
            obj.Radius = radius
            obj.recompute(True)

        self.form.CoMG_Set.clicked.connect(set_com)

        # select similar subobjects
        self.form.SelectSimilar.clicked.connect(self.select_similar)

        def change_decimals(value):
            self.decimals = value
            self.set_decimals()
        self.form.Decimals.valueChanged.connect(change_decimals)

        global freeze
        freeze = False

        self.add_selection(FreeCAD.ActiveDocument.Name, '', '')
        self.fill()

# ------------------------------------------------------------------------------

    def add_selection(self, doc, obj, sub) -> None:
        flat_objects = ('Sketcher::SketchObject', 'Part::Part2DObjectPython')

        selection = Gui.Selection.getSelection()
        if len(selection) == 0:
            return
        selection = selection[0]
        if selection.TypeId in flat_objects:
            flat = True
            s = Gui.Selection.getSelectionEx('', 0)[0]
            if s.HasSubObjects:
                object = selection
                sub_object_shape = s.SubObjects[-1]
                sub = s.SubElementNames[-1]
                # exception...
                sp = sub.split('.')
                if len(sp) == 2:
                    if sp[1] == '':
                        sub = ''
            else:
                object, sub = selection, ''
        else:
            flat = False

        if not flat:
            selection = Gui.Selection.getSelectionEx('', 0)
            if len(selection) == 0:
                return
            selection = selection[0]

            sub_object_shape = None
            if selection.HasSubObjects:
                sub_object_shape = selection.SubObjects[-1]
                shape_type = sub_object_shape.ShapeType
                if len(selection.SubElementNames) > 0:
                    sen = selection.SubElementNames[-1]
                    sol = selection.Object.getSubObjectList(sen)
                    if shape_type == 'Solid' or len(sol) == 1:
                        object = sol[-1]
                        if obj == '' and sub == '':  # init
                            obj, sub = object.Name, sen
                    else:
                        object = sol[-2]
                        if obj == '' and sub == '':  # init
                            sp = sen.split('.')
                            sub = sp[-1]
                            if len(sp) > 1:
                                obj = sp[-2]
                else:
                    object = selection.Object
            else:
                object = selection.Object

        key = f'{doc}.{object.Name}'

        if object.TypeId == 'App::Link':
            object = object.getLinkedObject()

        self.objects[key] = object
        if sub != '':
            key = f'{key}.{sub}'
            if sub_object_shape is not None:
                self.subobjects[key] = sub_object_shape
                self.last_selection = [object, sub_object_shape]
            else:
                log_err('object "sub_object_shape" is none...')
        else:
            if flat:
                n = 1
                for edge in object.Shape.Edges:
                    self.subobjects[f'{key}.Edge{str(n)}'] = edge
                    if n == 1:
                        self.last_selection = [object, edge]
                    n += 1
            else:
                self.last_selection = None

    def remove_selection(self, doc, obj, sub) -> None:
        _ = self.objects.pop(f'{doc}.{obj}', None)
        if sub != '':
            _ = self.subobjects.pop(f'{doc}.{obj}.{sub}', None)

    def clear_selection(self) -> None:
        self.objects.clear()
        self.subobjects.clear()

# ------------------------------------------------------------------------------

    def select_similar(self) -> None:
        if self.last_selection is None:
            log_err('object "last_selection" is none...')
            return

        obj, sub = self.last_selection

        similar = []

        if sub.ShapeType == 'Face':
            area = round(sub.Area, self.decimals)
            x = 1
            for i in obj.Shape.Faces:
                if area == round(i.Area, self.decimals):
                    similar.append(('Face' + str(x), i))
                x += 1
        elif sub.ShapeType == 'Edge':
            if sub.Curve.TypeId == 'Part::GeomCircle':
                radius = round(sub.Curve.Radius, self.decimals)
                x = 1
                for i in obj.Shape.Edges:
                    if sub.Curve.isClosed() == i.isClosed():
                        if hasattr(i.Curve, 'Radius'):
                            if radius == round(i.Curve.Radius, self.decimals):
                                similar.append(('Edge' + str(x), i))
                    x += 1
            elif sub.Curve.TypeId == 'Part::GeomLine':
                length = round(sub.Length, self.decimals)
                x = 1
                for i in obj.Shape.Edges:
                    if length == round(i.Length, self.decimals):
                        similar.append(('Edge' + str(x), i))
                    x += 1

        dn = FreeCAD.ActiveDocument.Name
        on = obj.Tip.Name if hasattr(obj, 'Tip') else obj.Name

        FreeCAD.Gui.Selection.clearSelection()
        for i in similar:
            FreeCAD.Gui.Selection.addSelection(dn, on, i[0], 0, 0, 0)

# ------------------------------------------------------------------------------

    def set_decimals(self) -> None:
        self.form.X_Value.setDecimals(self.decimals)
        self.form.Y_Value.setDecimals(self.decimals)
        self.form.Z_Value.setDecimals(self.decimals)
        self.form.Volume_Value.setDecimals(self.decimals)
        self.form.Weight_Value.setDecimals(self.decimals)
        self.form.Area_Value.setDecimals(self.decimals)
        self.form.Perimeter_Value.setDecimals(self.decimals)
        self.form.Diagonal_Value.setDecimals(self.decimals)
        self.form.Length_Value.setDecimals(self.decimals)
        self.form.Radius_Value.setDecimals(self.decimals)
        self.form.Diameter_Value.setDecimals(self.decimals)

    def set_designation(self) -> None:
        self.form.addFCName.setText(self.designation[0])
        self.form.InternalName.setText(self.designation[1])
        self.form.ObjectLabel.setText(self.designation[2])

    def set_bb(self) -> None:
        unit = self.form.BB_U.currentText()
        u = units_length[unit]
        value_x = round(self.bound_box[0] / u, self.decimals)
        value_y = round(self.bound_box[1] / u, self.decimals)
        value_z = round(self.bound_box[2] / u, self.decimals)
        self.form.X_Value.setMaximum(value_x)
        self.form.Y_Value.setMaximum(value_y)
        self.form.Z_Value.setMaximum(value_z)
        self.form.X_Value.setValue(value_x)
        self.form.Y_Value.setValue(value_y)
        self.form.Z_Value.setValue(value_z)

    def set_mass(self) -> None:
        if freeze:
            return
        unit_volume = self.form.Volume_U.currentText()
        unit_weight = self.form.Weight_U.currentText()
        u_volume = units_volume[unit_volume]
        u_weight = units_weight[unit_weight]
        value_volume = round(self.volume / u_volume, self.decimals)
        self.form.Volume_Value.setMaximum(value_volume)
        self.form.Volume_Value.setValue(value_volume)
        density = self.form.Density_Value.value()  # important: kg/m^3
        value_weight = round(self.volume * density / u_weight, self.decimals)
        self.form.Weight_Value.setMaximum(value_weight)
        self.form.Weight_Value.setValue(value_weight)

    def set_subobjects_title(self) -> None:
        if self.sub_title == '':
            self.form.Subobjects_Title.setText('...')
        else:
            self.form.Subobjects_Title.setText(self.sub_title)

    def set_subobjects_value(self) -> None:
        # area
        unit = self.form.Area_U.currentText()
        u = units_area[unit]
        value = round(self.area / u, self.decimals)
        self.form.Area_Value.setMaximum(value)
        self.form.Area_Value.setValue(value)
        # perimeter
        unit = self.form.Perimeter_U.currentText()
        u = units_length[unit]
        value = round(self.perimeter / u, self.decimals)
        self.form.Perimeter_Value.setMaximum(value)
        self.form.Perimeter_Value.setValue(value)
        # diagonal, length, radius, diameter
        unit = self.form.DLRD_U.currentText()
        u = units_length[unit]
        diagonal = round(self.diagonal / u, self.decimals)
        length = round(self.length / u, self.decimals)
        radius = round(self.radius / u, self.decimals)
        diameter = round(self.diameter / u, self.decimals)
        self.form.Diagonal_Value.setMaximum(diagonal)
        self.form.Diagonal_Value.setValue(diagonal)
        self.form.Length_Value.setMaximum(length)
        self.form.Length_Value.setValue(length)
        self.form.Radius_Value.setMaximum(radius)
        self.form.Radius_Value.setValue(radius)
        self.form.Diameter_Value.setMaximum(diameter)
        self.form.Diameter_Value.setValue(diameter)

    def fill(self) -> None:
        # objects
        designation = [[], [], []]
        bound_box = [0, 0, 0]
        volume = 0
        center_of_MG = None

        for k, v in self.objects.items():
            # designation
            if 'Add_Name' in v.PropertiesList:
                designation[0].append(v.Add_Name)
            designation[1].append(v.Name)
            designation[2].append(v.Label)
            # shape
            if hasattr(v, 'Tip'):
                shape = v.Tip.Shape
            else:
                shape = v.Shape
            bound_box[0] += shape.BoundBox.XLength
            bound_box[1] += shape.BoundBox.YLength
            bound_box[2] += shape.BoundBox.ZLength
            volume += shape.Volume
            # center of mass
            if hasattr(shape, 'CenterOfMass'):
                center = shape.CenterOfMass
                extra = (f'{v.Label}_CoM_001', (170, 0, 0))
            else:
                center = shape.CenterOfGravity
                extra = (f'{v.Label}_CoG_001', (0, 85, 255))
            # result
            center_of_MG = [
                k,
                center,
                shape.BoundBox.DiagonalLength,
                v.Placement.Base,
                extra,
            ]

        self.designation[0] = ', '.join(designation[0])
        self.designation[1] = ', '.join(designation[1])
        self.designation[2] = ', '.join(designation[2])

        self.bound_box = bound_box
        self.volume = volume
        self.center_of_MG = center_of_MG

        self.set_designation()
        self.set_bb()
        self.set_mass()

        # subobjects
        sub_title = []
        area = 0
        perimeter = 0
        diagonal = 0
        length = 0
        radius = 0
        diameter = 0

        for k, v in self.subobjects.items():
            sub_title.append(k.split('.')[-1])
            match v.ShapeType:
                case 'Face':
                    area += v.Area
                    perimeter += v.Length
                    diagonal = v.BoundBox.DiagonalLength
                case 'Edge':
                    length += v.Length
                    if v.Curve.TypeId == 'Part::GeomCircle':
                        radius = v.Curve.Radius
                        diameter = radius * 2

        self.sub_title = ', '.join(sub_title)

        self.area = area
        self.perimeter = perimeter
        self.diagonal = diagonal
        self.length = length
        self.radius = radius
        self.diameter = diameter

        self.set_subobjects_title()
        self.set_subobjects_value()

    def accept(self):
        Gui.Selection.removeObserver(observer)
        P.save_pref(P.PATH_SUMMARY, {
            # units of measurement
            'Area_U': self.form.Area_U.currentText(),
            'BB_U': self.form.BB_U.currentText(),
            'DLRD_U': self.form.DLRD_U.currentText(),
            'Perimeter_U': self.form.Perimeter_U.currentText(),
            'Volume_U': self.form.Volume_U.currentText(),
            'Weight_U': self.form.Weight_U.currentText(),
            # last used material and precision
            'Material': self.form.Material.currentText(),
            'Decimals': self.form.Decimals.value(),
        })
        return True

    def reject(self):
        Gui.Selection.removeObserver(observer)
        return True


# ------------------------------------------------------------------------------


info = Info()
Gui.Control.showDialog(info)
