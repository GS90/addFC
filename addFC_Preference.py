# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


from PySide import QtGui, QtCore
import copy
import FreeCAD
import json
import math
import os


add_base: str = os.path.dirname(__file__)
add_icon: str = os.path.join(add_base, 'repo', 'icon')

pref_configuration: str = os.path.join(add_base, 'pref', 'configuration.json')
pref_properties: str = os.path.join(add_base, 'pref', 'properties.json')
pref_steel: str = os.path.join(add_base, 'pref', 'steel.json')
pref_explosion: str = os.path.join(add_base, 'pref', 'explosion.json')


reserved_str: str = 'Body'


configuration: dict = {
    'interface_font': [False, 'Sans Serif', 10],
    'working_directory': '',
    'properties_group': 'Add',
    # unfold:
    'unfold_dxf': True,
    'unfold_svg': False,
    'unfold_stp': False,
    'unfold_file_name': 'Index',
    'unfold_file_signature': 'None',
    'unfold_prefix': 'Unfold',
    # export specification:
    'spec_export_type': 'Spreadsheet',
    'spec_export_json_use_alias': False,
    'spec_export_csv_use_alias': True,
    'spec_export_spreadsheet_use_alias': True,
    'spec_export_merger': 'Type',
    'spec_export_sort': 'Name',
    'spec_export_skip': ['Body',],
    # sheet metal part:
    'smp_density': 7800,
    'smp_color': tuple(int('b4c0c8'[i:i + 2], 16) for i in (0, 2, 4)),
    # ru std: template
    'ru_std_tpl_drawing': 'RU_Portrait_A4.svg',
    'ru_std_tpl_text': 'RU_Portrait_A4_T_1.svg',
    'ru_std_tpl_stamp': {
        'Author': 'Иванов И. И.',
        'Inspector': '',
        'Control 1': '',
        'Control 2': '',
        'Approver': '',
        'Designation': 'XXXX.XXXXXX.XXX',
        'Company 1': '',
        'Company 2': 'Организация',
        'Company 3': '',
        'Letter 1': 'П',
        'Letter 2': '',
        'Letter 3': '',
    },
}


# specification_properties: title: [type, addition, [enumeration], alias]

specification_properties_core: dict = {
    # required:
    'Name': ['String', False, [], ''],
    # core:
    'Code': ['String', False, [], ''],
    'Index': ['String', False, [], ''],
    'Material': ['Enumeration', False, [
        '-', 'Steel', 'Galvanized', 'Stainless', 'AISI 304', 'AISI 316'], ''],
    'MetalThickness': ['Float', False, [], ''],
    'Quantity': ['Float', True, [], ''],
    'Unfold': ['Bool', False, [], ''],
    'Unit': ['Enumeration', False, ['-', 'm', 'kg', 'm²', 'm³'], ''],
}

specification_properties_add: dict = {  # recommended
    'Format': ['Enumeration', False, ['A0', 'A1', 'A2', 'A3', 'A4'], ''],
    'Id': ['String', False, [], ''],
    'Note': ['String', False, [], ''],
    'Price': ['Float', True, [], ''],
    'Type': ['Enumeration', False, [
        '-', 'Node', 'Part', 'Sheet metal part', 'Fastener', 'Material'], ''],
    'Weight': ['Float', True, [], ''],
    # разделы спецификации ЕСКД:
    'Section': ['Enumeration', False, [
        '-',
        'Документация',
        'Комплексы',
        'Сборочные единицы',
        'Детали',
        'Стандартные изделия',
        'Прочие изделия',
        'Материалы',
        'Комплекты',
    ], ''],
}

available_properties: tuple = (
    'Bool',
    'Enumeration',
    'Float',
    'Integer',
    'String',
)


# ------------------------------------------------------------------------------


def check_configuration() -> None:
    d = os.path.dirname(pref_configuration)
    if not os.path.exists(d):
        os.makedirs(d)
    if not os.path.exists(pref_configuration):
        file = open(pref_configuration, 'w+', encoding='utf-8')
        json.dump(configuration, file, ensure_ascii=False, indent=4)
        file.close()
    elif not os.path.isfile(pref_configuration):
        os.remove(pref_configuration)
        check_properties()


def load_configuration() -> dict:
    check_configuration()
    try:
        file = open(pref_configuration, 'r', encoding='utf-8')
        result = configuration | json.load(file)
        file.close()
    except BaseException as e:
        FreeCAD.Console.PrintError(str(e) + '\n')
        result = configuration
    return result


def save_configuration(conf: dict) -> dict:
    check_configuration()
    result = load_configuration() | conf
    try:
        file = open(pref_configuration, 'w+', encoding='utf-8')
        json.dump(result, file, ensure_ascii=False, indent=4)
        file.close()
    except BaseException as e:
        FreeCAD.Console.PrintError(str(e) + '\n')


# ------------------------------------------------------------------------------


def check_properties() -> None:
    d = os.path.dirname(pref_properties)
    if not os.path.exists(d):
        os.makedirs(d)
    if not os.path.exists(pref_properties):
        file = open(pref_properties, 'w+', encoding='utf-8')
        result = specification_properties_core | specification_properties_add
        json.dump(result, file, ensure_ascii=False, indent=4)
        file.close()
    elif not os.path.isfile(pref_properties):
        os.remove(pref_properties)
        check_properties()


def load_properties() -> dict:
    check_properties()
    try:
        file = open(pref_properties, 'r', encoding='utf-8')
        result = json.load(file)
        file.close()
    except BaseException as e:
        FreeCAD.Console.PrintError(str(e) + '\n')
        result = specification_properties_add
    properties = result | copy.deepcopy(specification_properties_core)
    # processing values:
    for key in result:
        value = result[key]
        if result[key][0] == 'Enumeration':
            # removing duplicate values:
            value[2] = list(dict.fromkeys(value[2]))
        if key == 'Material':
            # checking the required values:
            for i in value[2]:
                if i not in properties[key][2]:
                    properties[key][2].append(i)
        if len(value) > 3:  # alias
            properties[key][3] = value[3]
    return properties


def save_properties(properties: dict, init: bool = False) -> None:
    check_properties()
    if init:
        return
    try:
        file = open(pref_properties, 'w+', encoding='utf-8')
        json.dump(properties, file, ensure_ascii=False, indent=4)
        file.close()
    except BaseException as e:
        FreeCAD.Console.PrintError(str(e) + '\n')


# ------------------------------------------------------------------------------


class addFCPreferenceSpecification():
    def __init__(self):
        ui = os.path.join(add_base, 'repo', 'ui', 'pref_specification.ui')
        self.form = FreeCAD.Gui.PySideUic.loadUi(ui)

        conf = load_configuration()
        self.form.lineEditGroup.setText(conf['properties_group'])

        properties, enumerated = load_properties(), {}

        headers_properties = ('Title', 'Type', 'Addition', 'Alias')
        headers_values = ('Property', 'Values')

        color_red = QtGui.QBrush(QtGui.QColor(150, 0, 0))
        color_blue = QtGui.QBrush(QtGui.QColor(0, 0, 150))

        tableProperties = self.form.tableProperties
        tableValues = self.form.tableValues

        def align(t, i: int) -> None:
            t.resizeColumnsToContents()
            t.resizeRowsToContents()
            t.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)

        #####################
        # table: properties #
        #####################

        tableProperties.setColumnCount(len(headers_properties))
        tableProperties.setHorizontalHeaderLabels(headers_properties)
        tableProperties.setRowCount(len(properties))

        addition_flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        x = 0
        for key in properties:
            value = properties[key]
            if value[0] == 'Enumeration':
                enumerated[key] = value[2]
            core = True if key in specification_properties_core else False
            # title:
            i = QtGui.QTableWidgetItem(key)
            if core:
                i.setFlags(QtCore.Qt.NoItemFlags)
            tableProperties.setItem(x, 0, i)
            # type:
            i = QtGui.QTableWidgetItem(value[0])
            if core:
                i.setFlags(QtCore.Qt.NoItemFlags)
            else:
                i.setForeground(color_blue)
            tableProperties.setItem(x, 1, i)
            # addition:
            i = QtGui.QTableWidgetItem(str(value[1]))
            if core:
                i.setFlags(QtCore.Qt.NoItemFlags)
            else:
                i.setFlags(addition_flags)
            tableProperties.setItem(x, 2, i)
            # alias:
            i = QtGui.QTableWidgetItem(str(value[3]))
            tableProperties.setItem(x, 3, i)
            #
            x += 1

        align(tableProperties, headers_properties.index('Title'))

        #################
        # table: values #
        #################

        tableValues.setColumnCount(len(headers_values))
        tableValues.setHorizontalHeaderLabels(headers_values)
        tableValues.setRowCount(len(enumerated))

        x = 0
        for key in enumerated:
            i = QtGui.QTableWidgetItem(key)
            i.setFlags(QtCore.Qt.NoItemFlags)
            tableValues.setItem(x, 0, i)
            i = QtGui.QTableWidgetItem(', '.join(enumerated[key]))
            if key == 'Unit':
                i.setFlags(QtCore.Qt.NoItemFlags)
            tableValues.setItem(x, 1, i)
            x += 1

        align(tableValues, headers_values.index('Values'))

        ###########
        # actions #
        ###########

        def remove() -> None:
            tableProperties.removeRow(tableProperties.currentRow())
            check_values()
        self.form.pushButtonRemove.clicked.connect(remove)

        def add() -> None:
            tableProperties.insertRow(tableProperties.rowCount())
            align(tableProperties, headers_properties.index('Title'))
        self.form.pushButtonAdd.clicked.connect(add)

        def check_values() -> None:
            properties = []
            for row in range(tableProperties.rowCount()):
                t = tableProperties.item(row, 1)
                if t is not None:
                    if t.text() == 'Enumeration':
                        properties.append(tableProperties.item(row, 0).text())
            for row in range(tableValues.rowCount()):
                n = tableValues.item(row, 0).text()
                if n not in properties:
                    tableValues.removeRow(row)
                else:
                    properties.remove(n)
            for n in properties:
                count = tableValues.rowCount()
                tableValues.insertRow(count)
                i = QtGui.QTableWidgetItem(n)
                i.setFlags(QtCore.Qt.NoItemFlags)
                tableValues.setItem(count, 0, i)

        def changed(item) -> None:
            if item.column() == 0:
                if item is not None:
                    # reserved:
                    if item.text() == reserved_str:
                        item.setText(f'{item.text()} (reserved)')
                    # duplicates:
                    for row in range(tableProperties.rowCount()):
                        if row == item.row():
                            continue
                        i = tableProperties.item(row, 0)
                        if i is not None:
                            if i.text() == item.text():
                                item.setText(f'{item.text()} (duplicate)')
                return

            if item.column() != 1:
                return
            elif item is None:
                return
            elif item.text() == '':
                return

            n = tableProperties.item(item.row(), 0)
            if n is None:
                return
            elif n.text() == '':
                return

            if item.text() in available_properties:
                item.setForeground(color_blue)
            else:
                item.setForeground(color_red)
                return
            if item.text() == 'Enumeration':
                # duplicates:
                for row in range(tableValues.rowCount()):
                    if tableValues.item(row, 0).text() == n.text():
                        return
                # add:
                count = tableValues.rowCount()
                tableValues.insertRow(count)
                i = QtGui.QTableWidgetItem(n.text())
                i.setFlags(QtCore.Qt.NoItemFlags)
                tableValues.setItem(count, 0, i)

        def changed_wrapper(item) -> None:
            changed(item)
            check_values()
            align(tableProperties, headers_properties.index('Title'))
            align(tableValues, headers_values.index('Values'))

        def switch(item) -> None:
            if item.column() == 2:
                if item is not None:
                    v = 'True' if item.text() == 'False' else 'False'
                    item.setText(v)

        self.form.tableProperties.itemChanged.connect(changed_wrapper)
        self.form.tableProperties.itemDoubleClicked.connect(switch)

        return

    def __del__(self):
        # configuration:
        properties_group = self.form.lineEditGroup.text().strip()
        if properties_group != '':
            global configuration
            if properties_group != configuration['properties_group']:
                configuration['properties_group'] = properties_group
                save_configuration(configuration)

        tableProperties = self.form.tableProperties
        tableValues = self.form.tableValues
        properties = {}

        for row in range(tableProperties.rowCount()):
            # title and type:
            p_title = tableProperties.item(row, 0)
            p_type = tableProperties.item(row, 1)
            if p_title is None or p_type is None:
                continue
            p_title = p_title.text().strip()
            p_type = p_type.text().strip()
            if p_title == '' or p_type == '':
                continue
            # addition:
            p_addition = tableProperties.item(row, 2)
            if p_addition is None:
                p_addition = 'False'
            else:
                p_addition = p_addition.text().strip()
            if p_type != 'Float' and p_type != 'Integer':
                p_addition = 'False'
            p_addition = False if p_addition == 'False' else True
            # alias:
            p_alias = tableProperties.item(row, 3)
            if p_alias is None:
                p_alias = ''
            else:
                p_alias = p_alias.text().strip()
            # result:
            properties[p_title] = [p_type, p_addition, [], p_alias]

        for row in range(tableValues.rowCount()):
            p_title = tableValues.item(row, 0).text()
            if p_title in properties:
                if tableValues.item(row, 1) is None:
                    continue
                split = tableValues.item(row, 1).text().split(',')
                for s in split:
                    v = s.strip()
                    if v != '':
                        properties[p_title][2].append(v)

        save_properties(properties)


# ------------------------------------------------------------------------------


steel: dict = {
    # title: {thickness: radius, k-factor, alias}
    'galvanized': {
        0.5: [1.3, 0.473, 'A',],
        0.8: [1.3, 0.460, 'B',],
        1.0: [1.3, 0.453, 'C',],
        1.2: [1.7, 0.456, 'D',],
        1.5: [1.7, 0.448, 'D',],
        2.0: [2.7, 0.454, 'E',],
        3.0: [3.3, 0.446, 'F',],
    },
    'stainless': {
        0.5: [1.3, 0.473, 'AS',],
        0.8: [1.3, 0.460, 'BS',],
        1.0: [1.3, 0.453, 'CS',],
        1.2: [1.7, 0.456, 'DS',],
        1.5: [1.7, 0.448, 'DS',],
        2.0: [2.7, 0.454, 'ES',],
        3.0: [3.3, 0.446, 'FS',],
    },
}


def check_steel() -> None:
    d = os.path.dirname(pref_steel)
    if not os.path.exists(d):
        os.makedirs(d)
    if not os.path.exists(pref_steel):
        file = open(pref_steel, 'w+', encoding='utf-8')
        json.dump(steel, file, ensure_ascii=False, indent=4)
        file.close()
    elif not os.path.isfile(pref_steel):
        os.remove(pref_steel)
        check_properties()


def load_steel() -> dict:
    check_steel()
    try:
        file = open(pref_steel, 'r', encoding='utf-8')
        result = steel | json.load(file)
        file.close()
    except BaseException as e:
        FreeCAD.Console.PrintError(str(e) + '\n')
        result = steel
    return result


def save_steel(s: dict) -> dict:
    check_steel()
    result = load_steel() | s
    try:
        file = open(pref_steel, 'w+', encoding='utf-8')
        json.dump(result, file, ensure_ascii=False, indent=4)
        file.close()
    except BaseException as e:
        FreeCAD.Console.PrintError(str(e) + '\n')


class addFCPreferenceSM():
    def __init__(self):
        ui = os.path.join(add_base, 'repo', 'ui', 'pref_sm.ui')
        self.form = FreeCAD.Gui.PySideUic.loadUi(ui)

        tableGalvanized = self.form.tableGalvanized
        tableStainless = self.form.tableStainless

        headers = ('Thickness', 'Radius', 'K-Factor', 'Alias')

        d = load_steel()

        def align(t, i: int) -> None:
            t.resizeColumnsToContents()
            t.resizeRowsToContents()
            t.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)

        def fill(t, d: dict) -> None:
            t.setColumnCount(len(headers))
            t.setHorizontalHeaderLabels(headers)
            t.setRowCount(len(d))
            x = 0
            i = QtGui.QTableWidgetItem
            for key in d:
                value = d[key]
                t.setItem(x, 0, i(str(key)))       # Thickness
                t.setItem(x, 1, i(str(value[0])))  # Radius
                t.setItem(x, 2, i(str(value[1])))  # K-Factor
                t.setItem(x, 3, i(value[2]))       # Alias
                x += 1
            align(t, headers.index('Alias'))

        fill(tableGalvanized, d['galvanized'])
        fill(tableStainless, d['stainless'])

        def calculate_factor() -> None:
            for table in (tableGalvanized, tableStainless):
                for row in range(table.rowCount()):
                    t = table.item(row, 0)  # Thickness
                    if t is None:
                        continue
                    try:
                        t = max(0.1, float(t.text().replace(',', '.')))
                    except BaseException:
                        continue
                    r = table.item(row, 1)  # Radius
                    if r is None:
                        r = t
                    else:
                        try:
                            r = max(0.1, float(r.text().replace(',', '.')))
                        except BaseException:
                            r = t
                    k = 1 / math.log(1 + t / r) - r / t
                    i = table.item(row, 2)
                    i.setText(str(round(k, 3)))  # K-Factor
        self.form.calculate.clicked.connect(calculate_factor)

        def galvanized_default() -> None:
            fill(tableGalvanized, steel['galvanized'])
        self.form.galvanizedDefault.clicked.connect(galvanized_default)

        def galvanized_remove() -> None:
            tableGalvanized.removeRow(tableGalvanized.currentRow())
        self.form.galvanizedRemove.clicked.connect(galvanized_remove)

        def galvanized_add() -> None:
            tableGalvanized.insertRow(tableGalvanized.rowCount())
            align(tableGalvanized, headers.index('Alias'))
        self.form.galvanizedAdd.clicked.connect(galvanized_add)

        def stainless_default() -> None:
            fill(tableStainless, steel['stainless'])
        self.form.stainlessDefault.clicked.connect(stainless_default)

        def stainless_remove() -> None:
            tableStainless.removeRow(tableStainless.currentRow())
        self.form.stainlessRemove.clicked.connect(stainless_remove)

        def stainless_add() -> None:
            tableStainless.insertRow(tableStainless.rowCount())
            align(tableStainless, headers.index('Alias'))
        self.form.stainlessAdd.clicked.connect(stainless_add)

        def color_set(color: tuple | list) -> None:
            color = QtGui.QColor(*color).name()
            self.form.color.setText(color)
            self.form.color.setStyleSheet('QPushButton {color:' + color + '}')

        def color_get() -> None:
            color = QtGui.QColorDialog.getColor()
            if color.isValid():
                color_set(color.getRgb()[:-1])
        self.form.color.clicked.connect(color_get)

        return

    def __del__(self):
        result = {'galvanized': {}, 'stainless': {}}

        def read(table, key: str) -> None:
            for row in range(table.rowCount()):
                thickness = table.item(row, 0)
                radius = table.item(row, 1)
                factor = table.item(row, 2)
                if thickness is None or factor is None:
                    continue
                if radius is None:
                    radius = thickness
                alias = table.item(row, 3)
                if alias is None:
                    alias == ''
                else:
                    alias = alias.text().strip()
                try:
                    thickness = float(thickness.text().replace(',', '.'))
                except BaseException:
                    continue
                try:
                    radius = float(radius.text().replace(',', '.'))
                except BaseException:
                    continue
                try:
                    factor = abs(float(factor.text().replace(',', '.')))
                    factor = max(0.0, min(factor, 1.0))
                except BaseException:
                    factor = 0.42
                result[key][thickness] = [radius, factor, alias]

        read(self.form.tableGalvanized, 'galvanized')
        read(self.form.tableStainless, 'stainless')

        save_steel(result)

        color = self.form.color.text().lstrip('#')
        save_configuration({
            'smp_density': int(self.form.density.value()),
            'smp_color': tuple(int(color[i:i + 2], 16) for i in (0, 2, 4)),
        })

        return


# ------------------------------------------------------------------------------


ru_std_tpl_path: str = os.path.join(add_base, 'repo', 'add', 'stdRU', 'tpl')


class addFCPreferenceOther():
    def __init__(self):
        ui = os.path.join(add_base, 'repo', 'ui', 'pref_other.ui')
        self.form = FreeCAD.Gui.PySideUic.loadUi(ui)

        conf = load_configuration()
        if 'interface_font' not in conf:
            return
        font = conf['interface_font']

        self.form.fontCheckBox.setChecked(font[0]),
        self.form.fontComboBox.setCurrentText(font[1]),
        self.form.fontSpinBox.setValue(font[2]),

        if 'ru_std_tpl_stamp' not in conf:
            return
        stamp = conf['ru_std_tpl_stamp']

        self.form.Author.setText(stamp['Author'])
        self.form.Inspector.setText(stamp['Inspector'])
        self.form.Control1.setText(stamp['Control 1'])
        self.form.Control2.setText(stamp['Control 2'])
        self.form.Approver.setText(stamp['Approver'])
        self.form.Designation.setText(stamp['Designation'])
        self.form.Company1.setText(stamp['Company 1'])
        self.form.Company2.setText(stamp['Company 2'])
        self.form.Company3.setText(stamp['Company 3'])
        self.form.Letter.setText(stamp['Letter 1'])

        drawing, text = [], []

        for i in os.listdir(os.path.join(ru_std_tpl_path, 'ЕСКД')):
            if i.endswith('.svg'):
                text.append(i) if '_T_' in i else drawing.append(i)
        for i in os.listdir(os.path.join(ru_std_tpl_path, 'СПДС')):
            if i.endswith('.svg'):
                text.append(i) if '_T_' in i else drawing.append(i)

        self.form.Drawing.addItems(drawing)
        self.form.Text.addItems(text)

        self.form.Drawing.setCurrentText(conf['ru_std_tpl_drawing'])
        self.form.Text.setCurrentText(conf['ru_std_tpl_text'])

        return

    def __del__(self):
        save_configuration(
            {
                'interface_font': [
                    self.form.fontCheckBox.isChecked(),
                    self.form.fontComboBox.currentText(),
                    self.form.fontSpinBox.value(),
                ],
                'ru_std_tpl_drawing': self.form.Drawing.currentText(),
                'ru_std_tpl_text': self.form.Text.currentText(),
                'ru_std_tpl_stamp': {
                    'Author': self.form.Author.text(),
                    'Inspector': self.form.Inspector.text(),
                    'Control 1': self.form.Control1.text(),
                    'Control 2': self.form.Control2.text(),
                    'Approver': self.form.Approver.text(),
                    'Designation': self.form.Designation.text(),
                    'Company 1': self.form.Company1.text(),
                    'Company 2': self.form.Company2.text(),
                    'Company 3': self.form.Company3.text(),
                    'Letter 1': self.form.Letter.text(),
                    'Letter 2': '',
                    'Letter 3': '',
                }}
        )


# ------------------------------------------------------------------------------


exploded: dict = {
    'export_size': '1080p (FHD)',
    'export_width': 1920,
    'export_height': 1080,
    'export_background': 'Current',
    'export_method': 'Framebuffer',
    'export_ccs': False,
    'export_image_format': 'PNG',
    'export_framerate': 60,
    'export_dir': os.path.expanduser('~/Desktop'),
}


def check_explosion() -> None:
    d = os.path.dirname(pref_explosion)
    if not os.path.exists(d):
        os.makedirs(d)
    if not os.path.exists(pref_explosion):
        file = open(pref_explosion, 'w+', encoding='utf-8')
        json.dump(exploded, file, ensure_ascii=False, indent=4)
        file.close()
    elif not os.path.isfile(pref_explosion):
        os.remove(pref_explosion)
        check_properties()


def load_explosion() -> dict:
    check_explosion()
    try:
        file = open(pref_explosion, 'r', encoding='utf-8')
        result = exploded | json.load(file)
        file.close()
    except BaseException as e:
        FreeCAD.Console.PrintError(str(e) + '\n')
        result = exploded
    return result


def save_explosion(d: dict) -> dict:
    check_explosion()
    result = load_explosion() | d
    try:
        file = open(pref_explosion, 'w+', encoding='utf-8')
        json.dump(result, file, ensure_ascii=False, indent=4)
        file.close()
    except BaseException as e:
        FreeCAD.Console.PrintError(str(e) + '\n')
