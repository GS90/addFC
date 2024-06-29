# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


import addFC_Preference as P
import FreeCAD
import json
import csv


base_enumeration = tuple(['',] + [str(i).rjust(3, '0') for i in range(1, 51)])


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

    info_headers, details_headers = {}, {}

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


def export_specification(path: str, target: str, strict: bool) -> str:
    specification = get_specification(strict)
    if len(specification[0]) == 0:
        return 'The specification is empty...'

    conf, properties = P.load_configuration(), P.load_properties()

    json_use_alias = conf['spec_export_json_use_alias']
    csv_use_alias = conf['spec_export_csv_use_alias']
    spreadsheet_use_alias = conf['spec_export_spreadsheet_use_alias']

    merger = conf['spec_export_merger']
    sort = conf['spec_export_sort']
    skip = conf['spec_export_skip']

    match target:

        case 'JSON' | 'CSV':
            result, headers = {}, []

            if target == 'JSON':
                use_alias = json_use_alias
            if target == 'CSV':
                use_alias = csv_use_alias

            for i in specification[0]:
                if 'Body' in specification[0][i]:
                    del specification[0][i]['Body']
                result[i] = {}
                for j in specification[0][i]:
                    key = j
                    if key in skip:
                        continue
                    if j in properties:
                        alias = properties[j][3]
                        if use_alias and alias != '':
                            key = properties[j][3]
                    if key not in headers:
                        headers.append(key)
                    result[i][key] = specification[0][i][j]

            match target:
                case 'JSON':
                    file = open(path, 'w+', encoding='utf-8')
                    json.dump(result, file, ensure_ascii=False, indent=4)
                    file.close()
                case 'CSV':
                    file = open(path, 'w+', encoding='utf-8-sig')
                    writer = csv.DictWriter(file, fieldnames=headers)
                    writer.writeheader()
                    for i in result:
                        for j in result[i]:
                            if type(result[i][j]) is float:
                                result[i][j] = str(
                                    result[i][j]).replace('.', ',')
                        writer.writerow(result[i])
                    file.close()
            return 'Export complete'

        case 'Spreadsheet':
            result = {}
            for i in specification[0]:
                unit = specification[0][i]
                for j in skip:
                    if j in unit:
                        unit.pop(j)
                if merger not in unit:
                    unit[merger] = '-'  # null
                if unit[merger] in result:
                    result[unit[merger]].append(unit)
                else:
                    result[unit[merger]] = [unit,]
            result = dict(sorted(result.items()))
            for i in result:
                try:
                    result[i] = sorted(result[i], key=lambda x: x[sort])
                except BaseException:
                    pass

            ad = FreeCAD.ActiveDocument
            s = ad.getObjectsByLabel('addFC_BOM')
            if len(s) == 0:
                s = ad.addObject('Spreadsheet::Sheet', 'addFC_BOM')
            else:
                s = s[0]
                s.clearAll()

            alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            center = 'center|vcenter|vimplied'

            columns, columns_width = {}, {}

            x = -1
            for i in specification[1]:
                if i not in skip:
                    x += 1
                    columns[i] = alphabet[x]
                    if i in properties:
                        if spreadsheet_use_alias and properties[i][3] != '':
                            i = properties[i][3]
                        elif i == 'MetalThickness':
                            i = 'MT'
                    s.set(f'{alphabet[x]}{1}', i)
                    columns_width[alphabet[x]] = [0, True]  # width, empty

            # style:
            s.setAlignment(f'A1:{alphabet[x]}1', center)
            s.setStyle(f'A1:{alphabet[x]}1', 'bold')

            y = 2
            for i in result:
                for j in result[i]:
                    for k in j:
                        if k in columns:
                            value = str(j[k])
                            w = max(columns_width[columns[k]][0], len(value))
                            columns_width[columns[k]][0] = w
                            if value != '-':
                                columns_width[columns[k]][1] = False
                            cell = f'{columns[k]}{y}'
                            s.set(cell, value)
                            # style:
                            match j[k]:
                                case int() | float():
                                    s.setAlignment(cell, center)
                                case _:
                                    if j[k] == '-' or j[k].isdigit():
                                        s.setAlignment(cell, center)
                    y += 1

            for i in columns_width:
                s.setColumnWidth(i, max(80, columns_width[i][0] * 8))
                if columns_width[i][1]:
                    s.removeColumns(i, 1)

            ad.recompute()
            return 'Export complete'
