# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


import addFC_Preference as P
import FreeCAD
import json


base_enumeration: tuple[str] = (
    '', '001', '002', '003', '004', '005', '006', '007', '008', '009', '010',
    '011', '012', '013', '014', '015', '016', '017', '018', '019', '020',
    '021', '022', '023', '024', '025', '026', '027', '028', '029', '030',
    '031', '032', '033', '034', '035', '036', '037', '038', '039', '040',
    '041', '042', '043', '044', '045', '046', '047', '048', '049', '050',
)


def define_thickness(body, bind=False, property='') -> float | int | str:
    thickness, base = 0.0, ''
    for i in base_enumeration:
        o = body.getObject('BaseBend' + i)
        if o is not None:
            thickness = float(o.thickness)
            base = f'{o.Name}.thickness'
            break
        o = body.getObject('BaseShape' + i)
        if o is not None:
            thickness = float(o.thickness)
            base = f'{o.Name}.thickness'
            break
        o = body.getObject('Pad' + i)
        if o is not None:
            thickness = float(o.Length)
            base = f'{o.Name}.Length'
            break
    thickness = round(thickness, 2)
    if thickness == 0:
        w = f'{body.Label}: metal thickness is not determined\n'
        FreeCAD.Console.PrintWarning(w)
        return '-'  # empty default value
    else:
        if bind:
            body.setExpression(property, base)
        return thickness


# ------------------------------------------------------------------------------


def get_specification(strict: bool) -> tuple[dict, dict, dict, dict]:
    configuration = P.load_configuration()
    properties = P.load_properties()

    group = configuration['properties_group'] + '_'

    # required:
    name = group + 'Name'
    quantity = group + 'Quantity'
    unfold = group + 'Unfold'
    thickness = group + 'MetalThickness'

    required = (name, quantity, unfold, thickness)

    # extra:
    properties_extra = {}
    for p in properties:
        if p not in required:
            properties_extra[group + p] = properties[p][1]

    heap, selection = [], []

    def analysis(obj, count=1) -> None:
        if not obj.Visibility:
            # link is visible, the element is not
            # it's better not to do that...
            if obj.TypeId == 'App::Part':
                for g in obj.Group:
                    if name in g.PropertiesList and g.Visibility:
                        analysis(g)
                    elif g.TypeId == 'App::Link' and g.Visibility:
                        analysis(g.getLinkedObject())
                    elif g.TypeId == 'Part::FeaturePython':  # array
                        lo = g.Base.getLinkedObject()
                        if lo.TypeId == 'App::Part':
                            # example: assembly of a fastener in an array
                            for i in lo.Group:
                                if i.Visibility and i.TypeId == 'App::Link':
                                    analysis(i.getLinkedObject(), g.Count)
                        elif lo.TypeId == 'PartDesign::Body':
                            # example: fastening element in the array
                            analysis(lo, g.Count)
        # standard:
        if name in obj.PropertiesList:
            if count > 1:
                for _ in range(count):
                    selection.append(obj)
            else:
                selection.append(obj)

    for i in FreeCAD.ActiveDocument.findObjects():
        if i.Visibility:
            match i.TypeId:
                case 'App::Link':
                    heap.append(i)
                case 'App::Part' | 'PartDesign::Body' | 'Part::Feature':
                    analysis(i)
                case 'Part::FeaturePython':
                    if 'Base' in i.PropertiesList:
                        if 'Count' in i.PropertiesList:
                            # array:
                            analysis(i.Base.getLinkedObject(), i.Count)
                    else:
                        analysis(i)

    for i in heap:
        o = i.getLinkedObject()
        if not o.Visibility:
            analysis(o)  # the base object can be hidden
            continue
        if i.TypeId != o.TypeId:
            match o.TypeId:
                case 'App::DocumentObjectGroup':
                    for g in o.Group:
                        if g.Visibility:
                            heap.append(g)
                case 'App::Part':
                    analysis(o)
                    # elements inside the part:
                    for g in o.Group:
                        if g.Visibility:
                            heap.append(g)
                case 'Part::FeaturePython':  # link to the array
                    analysis(o.Base.getLinkedObject(), o.Count)
                case _:
                    analysis(o)
        else:
            match o.TypeId:
                case 'Part::FeaturePython':
                    lo = o.Base.getLinkedObject()
                    analysis(lo, o.Count)
                    if lo.TypeId == 'App::Part':
                        # elements inside the part:
                        for g in lo.Group:
                            if g.Visibility:
                                for _ in range(o.Count):
                                    heap.append(g)
                case 'Part::Mirroring':
                    s = o.Source
                    if s.TypeId == 'App::Link':
                        heap.append(o.Source)
                    elif s.TypeId == 'PartDesign::Body':
                        analysis(s)
                case 'App::Part':
                    for g in o.Group:
                        if g.Visibility:
                            heap.append(g)
                case _:
                    analysis(o)

    info = {}

    for i in selection:

        key = i.getPropertyByName(name)

        if key in info:
            if quantity in i.PropertiesList:
                value = i.getPropertyByName(quantity)
                if value != 0:
                    info[key][quantity.replace(group, '')] += value
            else:
                info[key][quantity.replace(group, '')] += 1

            for p in i.PropertiesList:
                if group not in p or p == quantity:
                    continue
                if strict and p not in properties_extra:
                    continue
                if p in properties_extra and properties_extra[p]:
                    value = i.getPropertyByName(p)
                    if type(value) is float or type(value) is int:
                        if value != 0:
                            info[key][p.replace(group, '')] += value

        else:
            q = 1
            if quantity in i.PropertiesList:
                value = i.getPropertyByName(quantity)
                if type(value) is float or type(value) is int:
                    if value == 0:
                        continue
                    else:
                        q = value
                else:
                    w = f'{key}: quantity: wrong type\n'
                    FreeCAD.Console.PrintWarning(w)

            info[key] = {'Quantity': q}

            for p in i.PropertiesList:
                if group in p and p != quantity and p != thickness:

                    # sheet metal part:
                    if p == unfold:
                        info[key]['Body'] = i
                        if thickness in i.PropertiesList:
                            redefined = False
                            t = i.getPropertyByName(thickness)
                            try:
                                t = float(t)
                                if t == 0:
                                    t = define_thickness(i)
                                    if t != '-':
                                        setattr(i, thickness, t)
                                        i.recompute(True)
                                        redefined = True
                            except BaseException:
                                t = define_thickness(i)
                                if t != '-':
                                    setattr(i, thickness, t)
                                    i.recompute(True)
                                    redefined = True
                            if t == 0 or t == '-':
                                t = '-'
                                w = f'{key}: incorrect metal thickness\n'
                                FreeCAD.Console.PrintWarning(w)
                            elif redefined:
                                w = f'{key}: redefined metal thickness\n'
                                FreeCAD.Console.PrintWarning(w)
                            info[key]['MetalThickness'] = t
                        else:
                            info[key]['MetalThickness'] = define_thickness(i)

                    # other:
                    if strict and p not in properties_extra:
                        continue
                    value = i.getPropertyByName(p)
                    if type(value) is bool:
                        info[key][p.replace(group, '')] = value
                    if type(value) is str:
                        if value != '':
                            info[key][p.replace(group, '')] = value
                    if type(value) is float or type(value) is int:
                        if value != 0:
                            info[key][p.replace(group, '')] = value

    details = {}

    info_headers = {}
    details_headers = {}

    def addition(s: str) -> bool:
        if s == 'Quantity':
            return False  # different units of measurement
        if group + s in properties_extra:
            return properties_extra[group + s]

    for i in info:
        if 'Unit' not in info[i] or 'Body' in info[i]:
            info[i]['Unit'] = '-'
        for j in info[i]:
            if j not in info_headers:
                info_headers[j] = 0
            value = info[i][j]
            if type(value) is float:
                if addition(j):
                    info_headers[j] += value
                value = round(value, 2)
                info[i][j] = int(value) if value.is_integer() else value
            elif type(value) is int:
                if addition(j):
                    info_headers[j] += value
        if 'Body' in info[i]:
            details[i] = info[i]

    for i in details:
        for j in details[i]:
            if j not in details_headers:
                details_headers[j] = 0
            value = details[i][j]
            if type(value) is float or type(value) is int:
                if addition(j):
                    details_headers[j] += value

    for i in (info_headers, details_headers):
        for j in i:
            value = i[j]
            if type(value) is float:
                value = round(value, 2)
                i[j] = int(value) if value.is_integer() else value

    info_headers = dict(sorted(info_headers.items()))
    details_headers = dict(sorted(details_headers.items()))

    return info, info_headers, details, details_headers


# ------------------------------------------------------------------------------


def export_specification(path: str, target: str, strict: bool) -> None:
    properties = P.load_properties()
    match target:
        case 'json':
            specification = get_specification(strict)
            result = {}
            for i in specification[0]:
                if 'Body' in specification[0][i]:
                    del specification[0][i]['Body']
                result[i] = {}
                for j in specification[0][i]:
                    key = j
                    if j in properties:
                        alias = properties[j][3]
                        if alias != '':
                            key = properties[j][3]
                    result[i][key] = specification[0][i][j]
            file = open(path, 'w+', encoding='utf-8')
            json.dump(result, file, ensure_ascii=False, indent=4)
            file.close()
