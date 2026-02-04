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


import csv
import datetime
import FreeCAD
import json
import os

from addon.addFC import Logger, Other, Preference as P


BASE_ENUMERATION = tuple(['',] + [str(i).rjust(3, '0') for i in range(1, 51)])


def define_thickness(body, bind=False, property='') -> float | str:
    thickness, base, null = 0, '', '-'

    try:
        for i in BASE_ENUMERATION:
            o = body.getObject('BaseBend' + i)
            if o is not None:
                if 'thickness' in o.PropertiesList:
                    t = 'thickness'
                else:
                    t = 'Thickness'
                thickness = o.getPropertyByName(t).Value
                base = f'{o.Name}.{t}'
                break
            o = body.getObject('BaseShape' + i)
            if o is not None:
                if 'thickness' in o.PropertiesList:
                    t = 'thickness'
                else:
                    t = 'Thickness'
                thickness = o.getPropertyByName(t).Value
                base = f'{o.Name}.{t}'
                break
            o = body.getObject('Pad' + i)
            if o is not None:
                thickness = float(o.Length)
                base = f'{o.Name}.Length'
                break
            o = body.getObject('BaseFeature' + i)
            if o is not None:
                thickness = float(o.BaseFeature.Value)
                base = f'{o.BaseFeature.Name}.Value'
    except BaseException:
        pass

    thickness = round(thickness, 2)

    if thickness == 0:
        Logger.warning(f"'{body.Label}' metal thickness not defined")
        return null
    else:
        if bind:
            body.setExpression(property, base)
        return thickness


# ------------------------------------------------------------------------------


def weight_equation(obj, material: list) -> None:
    w, u, q = 'Add_Weight', 'Add_Unit', 'Add_Quantity'
    if 'Tip' in obj.PropertiesList:
        v = '.Tip.Shape.Volume'
    else:
        v = '.Shape.Volume'
    if q in obj.PropertiesList:
        if u in obj.PropertiesList:
            if obj.getPropertyByName(u) == '-':
                obj.setExpression(w, f'{v} * {material[1]} * {q} / 10 ^ 9')
        else:
            obj.setExpression(w, f'{v} * {material[1]} * {q} / 10 ^ 9')
    else:
        obj.setExpression(w, f'{v} * {material[1]} / 10 ^ 9')


def price_equation(obj, material: list) -> None:
    price = material[3]
    if price == 0:
        return
    p = 'Add_Price'
    match material[2]:
        case '-':
            return
        case 'm':
            u = 'Add_Unit'
            if u in obj.PropertiesList:
                if obj.getPropertyByName(u) == 'm':
                    obj.setExpression(p, f'{u} * {price}')
        case 'kg':
            w = 'Add_Weight'
            if w in obj.PropertiesList:
                obj.setExpression(p, f'{w} * {price}')
        case 'm^2':
            u, t = 'Add_Unfold', 'Add_MetalThickness'
            if 'Tip' in obj.PropertiesList:
                v, z = '.Tip.Shape.Volume', '.Tip.Shape.BoundBox.ZLength'
            else:
                v, z = '.Shape.Volume', '.Shape.BoundBox.ZLength'
            if u in obj.PropertiesList and t in obj.PropertiesList:
                # sheet metal part:
                obj.setExpression(p, f'{v} / 10 ^ 6 / {t} * {price}')
            else:
                obj.setExpression(p, f'{v} / 10 ^ 6 / {z} * {price}')
        case 'm^3':
            if 'Tip' in obj.PropertiesList:
                v = '.Tip.Shape.Volume'
            else:
                v = '.Shape.Volume'
            obj.setExpression(p, f'{v} / 10 ^ 9 * {price}')


def get_doc_name(dn: str) -> str:
    label = FreeCAD.getDocument(dn).Label
    return dn if label == '' else label


# ------------------------------------------------------------------------------


rounding = 2


def compilation(strict: bool = True,
                node_name: str = '',
                indexing: bool = False,
                update_enumerations: bool = False,
                update_equations: bool = False,
                ) -> tuple[dict, dict, dict, dict, dict]:

    global rounding
    rounding = FreeCAD.ParamGet(
        'User parameter:BaseApp/Preferences/Units').GetInt('Decimals')

    index_pt = 'App::PropertyString'  # important, type: string
    index_exception = ('Add_Section', 'Документация')

    group = 'Add_'

    property_index = 'Add_Index'
    property_material = 'Add_Material'
    property_name = 'Add_Name'
    property_node = 'Add_Node'
    property_price = 'Add_Price'
    property_quantity = 'Add_Quantity'
    property_thickness = 'Add_MetalThickness'
    property_unfold = 'Add_Unfold'
    property_weight = 'Add_Weight'

    properties = {}
    for p in P.pref_properties:
        properties[group + p] = P.pref_properties[p][1]

    heap, selection = [], []

    def analysis(obj, count=1, doc='') -> None:
        if not obj.Visibility:
            # link is visible, the element is not
            # it's better not to do that...
            if obj.TypeId == 'App::Part':
                for g in obj.Group:
                    if property_name in g.PropertiesList and g.Visibility:
                        analysis(g, 1, g.Document.Name)
                    elif g.TypeId == 'App::Link' and g.Visibility:
                        analysis(g.getLinkedObject(), 1, g.Document.Name)
                    elif g.TypeId == 'Part::FeaturePython':  # array?
                        try:
                            lo = g.Base.getLinkedObject()
                            if lo.TypeId == 'App::Part':
                                # example: assembly of a fastener in an array
                                for i in lo.Group:
                                    if i.Visibility:
                                        if i.TypeId == 'App::Link':
                                            analysis(i.getLinkedObject(),
                                                     g.Count,
                                                     lo.Document.Name)
                            elif lo.TypeId == 'PartDesign::Body':
                                # example: fastening element in the array
                                analysis(lo, g.Count, lo.Document.Name)
                        except BaseException:
                            pass  # todo: think about it
        # standard:
        if property_name in obj.PropertiesList:
            dn = obj.Document.Name if doc == '' else doc
            if count > 1:
                for _ in range(count):
                    selection.append((obj, dn))
            else:
                selection.append((obj, dn))

    def visibility_full(inList: list) -> bool:
        for i in inList:
            if not i.Visibility:
                match i.TypeId:
                    case 'App::Link' | 'PartDesign::SubShapeBinder': pass
                    case _: return False
        return True

    for i in FreeCAD.ActiveDocument.findObjects():
        dn = i.Document.Name
        if i.Visibility:
            if not visibility_full(i.InList):
                continue
            match i.TypeId:
                case 'App::Link':
                    heap.append(i)
                case 'App::Part' | 'PartDesign::Body' | 'Part::Feature':
                    analysis(i, doc=dn)
                case 'Part::FeaturePython':
                    if 'Base' in i.PropertiesList:
                        if 'Count' in i.PropertiesList:
                            # array:
                            analysis(i.Base.getLinkedObject(), i.Count, dn)
                        else:
                            # single element:
                            analysis(i, doc=dn)
                    else:
                        analysis(i, doc=dn)
                case 'TechDraw::DrawPage':
                    analysis(i, doc=dn)  # active drawing
        elif i.TypeId == 'TechDraw::DrawPage':
            analysis(i, doc=dn)  # inactive drawing

    for i in heap:
        o, dn = i.getLinkedObject(), i.Document.Name
        if not o.Visibility:
            analysis(o, doc=dn)  # the base object can be hidden
            continue
        if i.TypeId != o.TypeId:
            match o.TypeId:
                case 'App::DocumentObjectGroup':
                    for g in o.Group:
                        if g.Visibility:
                            heap.append(g)
                case 'App::Part':
                    analysis(o, doc=dn)
                    # elements inside the part:
                    for g in o.Group:
                        if g.Visibility:
                            heap.append(g)
                case 'Part::FeaturePython':  # link to the array
                    analysis(o.Base.getLinkedObject(), o.Count, dn)
                case _:
                    analysis(o, doc=dn)
        else:
            match o.TypeId:
                case 'Part::FeaturePython':
                    lo = o.Base.getLinkedObject()
                    analysis(lo, o.Count, dn)
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
                        analysis(s, doc=dn)
                case 'App::Part':
                    for g in o.Group:
                        if g.Visibility:
                            heap.append(g)
                case _:
                    analysis(o, doc=dn)

    info, nodes, count = {}, {}, 1

    for s in selection:
        i, dn = s

        if property_node in i.PropertiesList:
            if i.Add_Node == '':
                i.Add_Node = get_doc_name(dn)
                i.recompute(True)
            node = i.Add_Node
        else:
            node = get_doc_name(dn)

        nodes[node] = None

        if node_name != '' and node_name != node:
            continue

        key = i.Add_Name

        if key in info:
            # information for finding an object:
            objects = (i.Document.Name, i.Name)
            if info[key]['!Trace'][-1] != objects:
                info[key]['!Trace'].append(objects)

            if property_quantity in i.PropertiesList:
                value = i.Add_Quantity
                if value != 0:
                    info[key]['Quantity'] += value
            else:
                info[key]['Quantity'] += 1

            for p in i.PropertiesList:
                if group not in p or p == property_quantity:
                    continue
                if strict and p not in properties:
                    continue
                if p in properties and properties[p]:
                    value = i.getPropertyByName(p)
                    if type(value) is float or type(value) is int:
                        if value != 0:
                            info[key][p.replace(group, '')] += value

            # indexing duplicates:
            if indexing:
                if 'Index' in info[key]:
                    if property_index not in i.PropertiesList:
                        i.addProperty(index_pt, property_index, 'Add')
                        setattr(i, property_index, info[key]['Index'])

        else:
            if indexing:
                exception = False
                if index_exception[0] in i.PropertiesList:
                    value = i.getPropertyByName(index_exception[0])
                    if index_exception[1] == value:
                        exception = True
                if not exception:
                    if property_index not in i.PropertiesList:
                        i.addProperty(index_pt, property_index, 'Add')
                    setattr(i, property_index, str(count).rjust(2, '0'))
                    count += 1

            q = 1
            if property_quantity in i.PropertiesList:
                value = i.Add_Quantity
                if type(value) is float or type(value) is int:
                    q = value
                else:
                    Logger.warning(f"'{key}' incorrect quantity type")

            info[key] = {
                '!Trace': [(i.Document.Name, i.Name),],
                'Quantity': q,
                'Node': node,
            }

            if update_equations:
                if property_material in i.PropertiesList:
                    value = i.getPropertyByName(property_material)
                    if value != '' and value in P.pref_materials:
                        stuff = P.pref_materials[value]
                        if property_weight in i.PropertiesList:
                            for e in i.ExpressionEngine:
                                if property_weight in e:
                                    weight_equation(i, stuff)
                        if property_price in i.PropertiesList:
                            for e in i.ExpressionEngine:
                                if property_price in e:
                                    price_equation(i, stuff)
                        i.recompute(True)

            for p in i.PropertiesList:
                if group in p and p != property_quantity and \
                        p != property_thickness:

                    # enumeration, checking and filling:
                    if update_enumerations:
                        prop = p.lstrip(group)
                        materials_list = list(P.pref_materials.keys())
                        if prop in P.pref_properties:
                            if prop == 'Material':
                                enum = materials_list
                            else:
                                enum = P.pref_properties[prop][2]
                            if len(enum) > 0:
                                enum.sort()
                                try:
                                    ep = i.getEnumerationsOfProperty(p)
                                    ep.sort()
                                    if enum != ep and len(enum) > len(ep):
                                        setattr(i, p, enum)
                                except BaseException:
                                    pass

                    # sheet metal part:
                    if p == property_unfold:
                        info[key]['!Body'] = i
                        if property_thickness in i.PropertiesList:
                            t = i.Add_MetalThickness
                            redefined = False
                            try:
                                t = float(t)
                            except ValueError:
                                t = 0
                            if t == 0:
                                t = define_thickness(i)
                                if t != 0 and t != '-':
                                    setattr(i, property_thickness, t)
                                    i.recompute(True)
                                    redefined = True
                            if t == 0 or t == '-':
                                t = '-'
                            elif redefined:
                                w = f"'{key}' redefined metal thickness"
                                Logger.warning(w)
                            info[key]['MetalThickness'] = t
                        else:
                            info[key]['MetalThickness'] = define_thickness(i)

                    # other:
                    if strict and p not in properties:
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

    FreeCAD.ActiveDocument.recompute()

    # required for correct recalculation of configuration tables:
    if P.FC_VERSION[1] == '21':
        try:
            Other.recompute_configuration_tables()
        except BaseException:
            pass  # todo: ...

    details, info_headers, details_headers = {}, {}, {}

    def addition(s: str) -> bool | None:
        if s == 'Quantity':
            return False  # different units of measurement
        if group + s in properties:
            return properties[group + s]

    for i in info:
        if 'Unit' not in info[i] or '!Body' in info[i]:
            info[i]['Unit'] = '-'
        for j in info[i]:
            if j not in info_headers:
                info_headers[j] = 0
            value = info[i][j]
            if type(value) is float:
                if addition(j):
                    info_headers[j] += value
                value = round(value, rounding)
                info[i][j] = int(value) if value.is_integer() else value
            elif type(value) is int:
                if addition(j):
                    info_headers[j] += value
        if '!Body' in info[i]:
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
                value = round(value, rounding)
                i[j] = int(value) if value.is_integer() else value

    info_headers = dict(sorted(info_headers.items()))
    details_headers = dict(sorted(details_headers.items()))

    return info, info_headers, details, details_headers, nodes


# ------------------------------------------------------------------------------


UNIT_CONVERSION = {
    'm^3': 1000000000,
    'm^2': 1000000,
    'm': 1000,
    'kg': 1,
}

UNIT_RU = {
    '-': '',
    'm': 'м.',
    'kg': 'кг.',
    'm^2': 'м^2',
    'm^3': 'м^3',
}

# order and alignment:
SECTION_RU: dict = {
    'Документация': 16,
    'Комплексы': 18,
    'Сборочные единицы': 14,
    'Детали': 20,
    'Стандартные изделия': 12,
    'Прочие изделия': 15,
    'Материалы': 18,
    'Комплекты': 18,
}


# todo: natural sort?
def organize(merger: str, sort: str, skip: list, bom: dict) -> dict:
    result = {}

    for i in bom:
        unit = bom[i]

        if merger == 'Section':  # USDD
            if 'Section' in unit:
                if unit['Section'] == '-':
                    unit['Section'] = 'Прочие изделия'
            else:
                unit['Section'] = 'Прочие изделия'

        for j in skip:
            if j in unit:
                unit.pop(j)
        if merger not in unit:
            unit[merger] = '-'  # null
        if unit[merger] in result:
            result[unit[merger]].append(unit)
        else:
            result[unit[merger]] = [unit,]

    if merger == 'Section':  # USDD
        sections = {}
        for i in SECTION_RU:
            if i in result:
                sections[i] = result[i]
        result = sections
    else:
        result = dict(sorted(result.items()))

    for i in result:
        try:
            result[i] = sorted(result[i], key=lambda x: x[sort])
        except BaseException:
            pass

    return result


def export(path: str, target: str, bom) -> str:
    if len(bom[0]) == 0:
        return 'The BOM is empty...'

    conf, properties = P.pref_configuration, P.pref_properties

    alias = conf['bom_export_alias']
    json_use_alias = True if 'json' in alias else False
    csv_use_alias = True if 'csv' in alias else False
    spreadsheet_use_alias = True if 'spreadsheet' in alias else False

    merger = conf['bom_export_merger']
    sort = conf['bom_export_sort']
    skip = conf['bom_export_skip']

    center = 'center|vcenter|vimplied'

    match target:

        case 'JSON' | 'CSV':
            result, headers = {}, []

            match target:
                case 'JSON': use_alias = json_use_alias
                case 'CSV': use_alias = csv_use_alias
                case _: use_alias = False

            for i in bom[0]:
                for p in P.SYSTEM_PROPERTIES:
                    if p in bom[0][i]:
                        del bom[0][i][p]
                result[i] = {}
                for j in bom[0][i]:
                    key = j
                    if key in skip:
                        continue
                    if j in properties:
                        alias = properties[j][3]
                        if use_alias and alias != '':
                            key = properties[j][3]
                    if key not in headers:
                        headers.append(key)
                    result[i][key] = bom[0][i][j]

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

        case 'Spreadsheet':
            result = organize(merger, sort, skip, bom[0])

            ad = FreeCAD.ActiveDocument
            s = ad.getObjectsByLabel('addFC_BOM')
            if len(s) == 0:
                s = ad.addObject('Spreadsheet::Sheet', 'addFC_BOM')
            else:
                s = s[0]
                s.clearAll()

            alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

            columns, columns_width = {}, {}

            quantity_column, weight_column = '', ''

            x = -1
            for i in bom[1]:
                if i not in skip:
                    x += 1
                    columns[i] = alphabet[x]
                    if i in properties:
                        # special columns:
                        if i == 'Quantity':
                            quantity_column = alphabet[x]
                        elif i == 'Weight':
                            weight_column = alphabet[x]
                        # aliases or abbreviations:
                        if spreadsheet_use_alias and properties[i][3] != '':
                            i = properties[i][3]
                        else:
                            if i == 'MetalThickness':
                                i = 'MT'
                            elif i == 'Quantity':
                                i = 'Qty'
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
                            if columns[k] == quantity_column:
                                value_len = len(value) + rounding + 4
                            elif columns[k] == weight_column:
                                value_len = len(value) + rounding + 2
                            else:
                                value_len = len(value)
                            cw = max(columns_width[columns[k]][0], value_len)
                            columns_width[columns[k]][0] = cw
                            if value != '-':
                                columns_width[columns[k]][1] = False
                            cell = f'{columns[k]}{y}'
                            # check unit conversion:
                            value_conv = None
                            if columns[k] == quantity_column:
                                sp = value.split(' ')
                                if len(sp) == 2:
                                    if sp[1] != '-':
                                        try:
                                            conv = UNIT_CONVERSION[sp[1]]
                                            v = float(sp[0]) * conv
                                            value_conv = (str(v), sp[1])
                                        except ValueError:
                                            pass
                            elif columns[k] == weight_column:
                                s.setDisplayUnit(cell, 'kg')  # standard
                            # value entry:
                            if value_conv is None:
                                s.set(cell, value)
                            else:
                                s.set(cell, value_conv[0])
                                s.setDisplayUnit(cell, value_conv[1])
                                s.setAlignment(cell, center)
                            # style:
                            match j[k]:
                                case int() | float():
                                    s.setAlignment(cell, center)
                                case _:
                                    if j[k] == '-' or j[k].isdigit():
                                        s.setAlignment(cell, center)
                    y += 1

            for i in columns_width:
                s.setColumnWidth(i, max(70, columns_width[i][0] * 9))
                if columns_width[i][1]:
                    s.removeColumns(i, 1)

            ad.recompute()

        case 'RU std: TechDraw' | 'RU std: Spreadsheet':
            result = organize('Section', sort, skip, bom[0])

            info, count = {}, 0

            for i in result:
                for j in result[i]:
                    count += 1
                    r = {
                        'Format': '',
                        'Index': '',
                        'Code': '',
                        'Name': '',
                        'Quantity': '',
                        'Note': '',
                    }

                    if 'Section' in j:
                        section = j['Section']
                        if section == '-':
                            section = 'Прочие изделия'
                    else:
                        section = 'Прочие изделия'

                    for k in j:
                        if k in r:
                            v = str(j[k])
                            if v == '-':
                                continue
                            if k == 'Quantity':
                                sp = v.split(' ')
                                if len(sp) == 2:
                                    v = sp[0].replace('.', ',')
                                else:
                                    v = v.replace('.', ',')
                            r[k] = v

                    # empty note is replaced by unit of measurement:
                    if r['Note'] == '':
                        if 'Unit' in j:
                            u = j['Unit']
                            if u != '' and u != '-':
                                if u in UNIT_RU:
                                    r['Note'] = UNIT_RU[u]
                                else:
                                    r['Note'] = u

                    if section in info:
                        info[section].append(r)
                    else:
                        info[section] = [r,]
                        count += 1

            separation = True
            if len(info) == 1:
                separation = False
                count -= 1

            ad = FreeCAD.ActiveDocument

            # -------- #
            # TechDraw #
            # -------- #

            if target == 'RU std: TechDraw':

                path_tpl = os.path.join(
                    P.AFC_DIR_EXTRA, 'stdRU', 'tpl', 'ЕСКД',
                )

                dp, dt = 'TechDraw::DrawPage', 'TechDraw::DrawSVGTemplate'

                tpl = conf['ru_std_tpl_text']

                uno_tpl = os.path.join(path_tpl, tpl)
                dos_tpl = os.path.join(path_tpl, 'RU_Portrait_A4_T_1a.svg')

                pages = {'n': 1, 'p': [], 't': [], 'e': {}}

                limit = (29, 61)  # uno, dos
                if tpl == 'RU_Portrait_A4_T_1_Full.svg':
                    limit = (25, 57)

                # do you need more pages?
                if count > limit[0] + limit[1] * 2:
                    e = 'The allowed number of elements has been exceeded!'
                    Logger.error(e)

                if count > limit[0] + limit[1]:
                    pages['n'] = 3
                elif count > limit[0]:
                    pages['n'] = 2

                for i in range(pages['n']):
                    postfix = '' if pages['n'] == 1 else '_' + str(i + 1)
                    label = f'addFC_BOM_RU{postfix}'
                    if len(ad.getObjectsByLabel(label)) > 0:
                        # cleaning:
                        ad.removeObject(label)
                        ad.recompute()
                    pages['p'].append(ad.addObject(dp, label))
                    pages['t'].append(ad.addObject(dt, f'RU_Tpl{postfix}'))
                    pages['t'][i].Template = uno_tpl if i == 0 else dos_tpl
                    pages['p'][i].Template = pages['t'][i]
                    pages['e'][i] = pages['t'][i].EditableTexts

                p, x, count = 0, 1, 1

                for i in info:

                    if count > limit[0] and p == 0:  # go to the second page
                        p, x = 1, 1
                    if count > limit[1] and p == 1:  # go to the third page
                        p, x = 2, 1

                    if separation:
                        # center alignment:
                        if i in SECTION_RU:
                            w = SECTION_RU[i]
                        else:
                            w = int((45 - len(i)) / 2)
                        n = str(i).rjust(w + len(i), ' ')
                        pages['e'][p][f'Name {x}'] = n
                        x += 1
                        count += 1

                    for j in range(len(info[i])):

                        if count > limit[0] and p == 0:
                            # go to the second page:
                            p, x = 1, 1
                        if count > limit[1] and p == 1:
                            # go to the third page:
                            p, x = 2, 1

                        pages['e'][p][f'Format {x}'] = info[i][j]['Format']
                        pages['e'][p][f'Index {x}'] = info[i][j]['Index']
                        pages['e'][p][f'Code {x}'] = info[i][j]['Code']

                        # name length check:
                        n = str(info[i][j]['Name'])
                        if len(n) > 32:
                            sp = int(len(n) / 2)
                            uno, dos = n[:sp], n[sp:]
                            s_uno = uno.rsplit(' ', 1)
                            if len(s_uno) == 2:
                                uno = s_uno[0]
                                dos = s_uno[-1] + dos
                            else:
                                s_dos = dos.split(' ', 1)
                                if len(s_dos) == 2:
                                    uno = uno + dos[0]
                                    dos = s_dos[-1]
                            pages['e'][p][f'Name {x}'] = uno
                            x += 1
                            count += 1
                            pages['e'][p][f'Name {x}'] = '  ' + dos
                        else:
                            pages['e'][p][f'Name {x}'] = n

                        pages['e'][p][f'Quantity {x}'] = info[i][j]['Quantity']
                        pages['e'][p][f'Note {x}'] = info[i][j]['Note']
                        x += 1
                        count += 1

                stamp = conf['ru_std_tpl_stamp']
                today = datetime.date.today().strftime('%d.%m.%y')

                fields = {
                    'Author': True,
                    'Inspector': True,
                    'Control 2': True,
                    'Approver': True,
                    'Company 1': False,
                    'Company 2': False,
                    'Company 3': False,
                    'Letter 1': False,
                    'Letter 2': False,
                    'Letter 3': False,
                }

                for i in range(pages['n']):
                    pages['e'][i]['Designation'] = stamp['Designation']
                    pages['e'][i]['Sheet'] = str(i + 1)
                    if i == 0:
                        # general page:
                        pages['e'][i]['Sheets'] = str(pages['n'])
                        for j in fields:
                            if j in stamp:
                                v = stamp[j]
                                pages['e'][i][j] = v
                                if fields[j]:
                                    if v != '':
                                        pages['e'][i][f'{j} - date'] = today
                                    else:
                                        pages['e'][i][f'{j} - date'] = ''
                    # fill:
                    pages['t'][i].EditableTexts = pages['e'][i]

            # ----------- #
            # Spreadsheet #
            # ----------- #

            elif target == 'RU std: Spreadsheet':

                s = ad.getObjectsByLabel('RU_addFC_BOM_S')
                if len(s) == 0:
                    s = ad.addObject('Spreadsheet::Sheet', 'addFC_BOM_RU_S')
                else:
                    s = s[0]
                    s.clearAll()

                headers = {
                    'A': ('Формат', 70),
                    'B': ('Зона', 60),
                    'C': ('Позиция', 80),
                    'D': ('Обозначение', 160),
                    'E': ('Наименование', 280),
                    'F': ('Кол-во', 70),
                    'G': ('Примечание', 110),
                }

                for i in headers:
                    s.set(f'{i}1', headers[i][0])
                    s.setColumnWidth(i, headers[i][1])

                s.setRowHeight('1', 40)
                s.setAlignment('A1:G1', center)

                x = 2
                for i in info:
                    if separation:
                        s.set(f'E{x}', str(i))
                        s.setAlignment(f'E{x}', center)
                        x += 1
                    for j in range(len(info[i])):
                        s.set(f'A{x}', info[i][j]['Format'])
                        s.set(f'C{x}', info[i][j]['Index'])
                        s.set(f'D{x}', info[i][j]['Code'])
                        s.set(f'E{x}', info[i][j]['Name'])
                        s.set(f'F{x}', info[i][j]['Quantity'])
                        s.set(f'G{x}', info[i][j]['Note'])
                        x += 1

                x -= 1
                s.setAlignment(f'A2:A{x}', center)
                s.setAlignment(f'B2:B{x}', center)
                s.setAlignment(f'C2:C{x}', center)
                s.setAlignment(f'F2:F{x}', center)

            ad.recompute()

    return 'Export complete'
