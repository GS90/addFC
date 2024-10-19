# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


import addFC_Preference as P
import csv
import datetime
import FreeCAD
import json
import os


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
        o = body.getObject('BaseFeature' + i)
        if o is not None:
            thickness = float(o.BaseFeature.Value)
            base = f'{o.BaseFeature.Name}.Value'
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


def get_specification(strict: bool = True,
                      indexing: bool = False,
                      update_enumerations: bool = False,
                      ) -> tuple[dict, dict, dict, dict]:

    configuration = P.load_configuration()
    properties = P.load_properties()

    group = configuration['properties_group'] + '_'

    index_pt = 'App::PropertyString'  # important, type: string
    index_exception = (group + 'Section', 'Документация')

    # required:
    name = group + 'Name'
    index = group + 'Index'
    thickness = group + 'MetalThickness'
    quantity = group + 'Quantity'
    unfold = group + 'Unfold'

    required = (name, index, thickness, quantity, unfold)

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
                case 'TechDraw::DrawPage':
                    analysis(i)  # active drawing
        elif i.TypeId == 'TechDraw::DrawPage':
            analysis(i)  # inactive drawing

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

    info, count = {}, 1

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

            # indexing duplicates:
            if indexing:
                original = index.replace(group, '')
                if original in info[key]:
                    if index not in i.PropertiesList:
                        i.addProperty(index_pt, index, group[:-1])
                        setattr(i, index, info[key][original])

        else:
            if indexing:
                exception = False
                if index_exception[0] in i.PropertiesList:
                    value = i.getPropertyByName(index_exception[0])
                    if index_exception[1] == value:
                        exception = True
                if not exception:
                    if index not in i.PropertiesList:
                        i.addProperty(index_pt, index, group[:-1])
                    setattr(i, index, str(count).rjust(2, '0'))
                    count += 1

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

                    # enumeration, checking and filling:
                    if update_enumerations:
                        _p = p.lstrip(f'{group}_')
                        if _p in properties:
                            _e = properties[_p][2]
                            if len(_e) > 0:
                                _e.sort()
                                try:
                                    _ep = i.getEnumerationsOfProperty(p)
                                    _ep.sort()
                                    if _e != _ep and len(_e) > len(_ep):
                                        setattr(i, p, _e)
                                except BaseException:
                                    pass

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

    FreeCAD.activeDocument().recompute()

    details, info_headers, details_headers = {}, {}, {}

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


unit_ru: dict = {
    '-': '',
    'm': 'м.',
    'kg': 'кг.',
    'm²': 'м²',
    'm³': 'м³',
}

# order and alignment:
section_ru: dict = {
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
def organize(merger: str, sort: str, skip: list, specification: dict):
    result = {}

    for i in specification:
        unit = specification[i]

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
        sort = {}
        for i in section_ru:
            if i in result:
                sort[i] = result[i]
        result = sort
    else:
        result = dict(sorted(result.items()))

    for i in result:
        try:
            result[i] = sorted(result[i], key=lambda x: x[sort])
        except BaseException:
            pass

    return result


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

    center = 'center|vcenter|vimplied'

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

        case 'Spreadsheet':
            result = organize(merger, sort, skip, specification[0])

            ad = FreeCAD.ActiveDocument
            s = ad.getObjectsByLabel('addFC_BOM')
            if len(s) == 0:
                s = ad.addObject('Spreadsheet::Sheet', 'addFC_BOM')
            else:
                s = s[0]
                s.clearAll()

            alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

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

        case 'RU std: TechDraw' | 'RU std: Spreadsheet':
            result = organize('Section', sort, skip, specification[0])

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
                                v = v.replace('.', ',')
                            r[k] = v

                    # empty note is replaced by unit of measurement:
                    if r['Note'] == '':
                        if 'Unit' in j:
                            u = j['Unit']
                            if u != '' and u != '-':
                                if u in unit_ru:
                                    r['Note'] = unit_ru[u]
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

            ############
            # TechDraw #
            ############

            if target == 'RU std: TechDraw':

                path_tpl = os.path.join(
                    P.add_base, 'repo', 'add', 'stdRU', 'tpl', 'ЕСКД',
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
                    w = 'The allowed number of elements has been exceeded!\n'
                    FreeCAD.Console.PrintWarning(w)

                if count > limit[0] + limit[1]:
                    pages['n'] = 3
                elif count > limit[0]:
                    pages['n'] = 2

                for i in range(pages['n']):
                    postfix = '' if pages['n'] == 1 else '_' + str(i + 1)
                    label = f'RU_addFC_BOM{postfix}'
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
                        if i in section_ru:
                            w = section_ru[i]
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
                        if len(n) > 34:
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
                            pages['e'][p][f'Name {x}'] = dos
                        else:
                            pages['e'][p][f'Name {x}'] = n

                        pages['e'][p][f'Quantity {x}'] = info[i][j]['Quantity']
                        pages['e'][p][f'Note {x}'] = info[i][j]['Note']
                        x += 1
                        count += 1

                conf = P.load_configuration()
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

            ###############
            # Spreadsheet #
            ###############

            elif target == 'RU std: Spreadsheet':

                s = ad.getObjectsByLabel('RU_addFC_BOM_S')
                if len(s) == 0:
                    s = ad.addObject('Spreadsheet::Sheet', 'RU_addFC_BOM_S')
                else:
                    s = s[0]
                    s.clearAll()

                headers = {
                    'A': ('Формат', 70),
                    'B': ('Зона', 60),
                    'C': ('Позиция', 70),
                    'D': ('Обозначение', 160),
                    'E': ('Наименование', 280),
                    'F': ('Кол-во', 60),
                    'G': ('Примечание', 100),
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
