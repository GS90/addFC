# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


from PySide import QtGui, QtCore
import copy
import FreeCAD
import json
import os


add_base: str = os.path.dirname(__file__)
add_icon: str = os.path.join(add_base, 'repo', 'icon')


add_configuration: str = os.path.join(add_base, 'pref', 'configuration.json')
add_properties: str = os.path.join(add_base, 'pref', 'properties.json')
add_steel: str = os.path.join(add_base, 'pref', 'steel.json')

reserved: str = 'Body'


configuration: dict = {
    'unfold_prefix': 'Result',
    'properties_group': 'Add',
    'working_directory': '',
}

sheet_metal_part: dict = {
    'density': 7800,
    'color': tuple(int('b4c0c8'[i:i + 2], 16) for i in (0, 2, 4))
}


# specification_properties: title: [type, addition, [enumeration], alias]

specification_properties_core: dict = {
    # required:
    'Name': ['String', False, [], ''],
    # core:
    'Code': ['String', False, [], ''],
    'Material': ['Enumeration', False, [
        '-', 'Steel', 'Galvanized', 'Stainless', 'AISI 304', 'AISI 316'], ''],
    'MetalThickness': ['Float', False, [], ''],
    'Quantity': ['Float', True, [], ''],
    'Unfold': ['Bool', False, [], ''],
    'Unit': ['Enumeration', False, ['-', 'm', 'kg', 'm²', 'm³'], ''],
}

specification_properties_add: dict = {
    'Id': ['Integer', False, [], ''],
    'Price': ['Float', True, [], ''],
    'Type': ['Enumeration', False, [
        '-', 'Node', 'Part', 'Sheet metal part', 'Fastener', 'Material'], ''],
    'Weight': ['Float', True, [], ''],
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
    d = os.path.dirname(add_configuration)
    if not os.path.exists(d):
        os.makedirs(d)
    if not os.path.exists(add_configuration):
        file = open(add_configuration, 'w+', encoding='utf-8')
        json.dump(configuration, file, ensure_ascii=False)
        file.close()
    elif not os.path.isfile(add_configuration):
        os.remove(add_configuration)
        check_properties()


def load_configuration() -> dict:
    check_configuration()
    try:
        file = open(add_configuration, 'r', encoding='utf-8')
        result = configuration | json.load(file)
        file.close()
    except BaseException as e:
        FreeCAD.Console.PrintError(str(e) + '\n')
        result = configuration
    return result


def save_configuration(conf: dict) -> dict:
    check_configuration()
    result = configuration | load_configuration() | conf
    try:
        file = open(add_configuration, 'w+', encoding='utf-8')
        json.dump(result, file, ensure_ascii=False)
        file.close()
    except BaseException as e:
        FreeCAD.Console.PrintError(str(e) + '\n')


# ------------------------------------------------------------------------------


def check_properties() -> None:
    d = os.path.dirname(add_properties)
    if not os.path.exists(d):
        os.makedirs(d)
    if not os.path.exists(add_properties):
        file = open(add_properties, 'w+', encoding='utf-8')
        result = specification_properties_core | specification_properties_add
        json.dump(result, file, ensure_ascii=False)
        file.close()
    elif not os.path.isfile(add_properties):
        os.remove(add_properties)
        check_properties()


def load_properties() -> dict:
    check_properties()
    try:
        file = open(add_properties, 'r', encoding='utf-8')
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
        file = open(add_properties, 'w+', encoding='utf-8')
        json.dump(properties, file, ensure_ascii=False)
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
                    if item.text() == reserved:
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
                split = tableValues.item(row, 1).text().split(', ')
                for s in split:
                    v = s.strip()
                    if v != '':
                        properties[p_title][2].append(v)

        save_properties(properties)


# ------------------------------------------------------------------------------


steel: dict = {
    # title: {thickness: k-factor, alias}
    'galvanized': {
        0.5: [0.472, 'AG',],
        0.8: [0.448, 'BG',],
        1.0: [0.425, 'CG',],
        1.5: [0.412, 'DG',],
        2.0: [0.425, 'EG',],
        3.0: [0.414, 'FG',],
    },
    'stainless': {
        0.5: [0.472, 'AS',],
        0.8: [0.448, 'BS',],
        1.0: [0.425, 'CS',],
        1.5: [0.412, 'DS',],
        2.0: [0.425, 'ES',],
        3.0: [0.414, 'FS',],
    },
}


def check_steel() -> None:
    d = os.path.dirname(add_steel)
    if not os.path.exists(d):
        os.makedirs(d)
    if not os.path.exists(add_steel):
        file = open(add_steel, 'w+', encoding='utf-8')
        json.dump(steel, file, ensure_ascii=False)
        file.close()
    elif not os.path.isfile(add_steel):
        os.remove(add_steel)
        check_properties()


def load_steel() -> dict:
    check_steel()
    try:
        file = open(add_steel, 'r', encoding='utf-8')
        result = steel | json.load(file)
        file.close()
    except BaseException as e:
        FreeCAD.Console.PrintError(str(e) + '\n')
        result = steel
    return result


def save_steel(s: dict) -> dict:
    check_steel()
    result = steel | load_steel() | s
    try:
        file = open(add_steel, 'w+', encoding='utf-8')
        json.dump(result, file, ensure_ascii=False)
        file.close()
    except BaseException as e:
        FreeCAD.Console.PrintError(str(e) + '\n')


class addFCPreferenceSM():
    def __init__(self):
        ui = os.path.join(add_base, 'repo', 'ui', 'pref_sm.ui')
        self.form = FreeCAD.Gui.PySideUic.loadUi(ui)

        tableGalvanized = self.form.tableGalvanized
        tableStainless = self.form.tableStainless

        headers = ('Thickness', 'K-Factor', 'Alias')

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
                t.setItem(x, 0, i(str(key)))
                t.setItem(x, 1, i(str(value[0])))
                t.setItem(x, 2, i(value[1]))
                x += 1
            align(t, headers.index('Alias'))

        fill(tableGalvanized, d['galvanized'])
        fill(tableStainless, d['stainless'])

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

        return

    def __del__(self):
        result = {'galvanized': {}, 'stainless': {}}

        def read(table, key: str) -> None:
            for row in range(table.rowCount()):
                thickness = table.item(row, 0)
                factor = table.item(row, 1)
                if thickness is None or factor is None:
                    continue
                alias = table.item(row, 2)
                if alias is None:
                    alias == ''
                else:
                    alias = alias.text().strip()
                try:
                    thickness = float(thickness.text().replace(',', '.'))
                except BaseException:
                    continue
                try:
                    factor = abs(float(factor.text().replace(',', '.')))
                    factor = max(0.0, min(factor, 1.0))
                except BaseException:
                    factor = 0.5
                result[key][thickness] = [factor, alias]

        read(self.form.tableGalvanized, 'galvanized')
        read(self.form.tableStainless, 'stainless')

        save_steel(result)
        return
