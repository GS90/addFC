# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


from importlib.metadata import version
from PySide import QtGui, QtCore
import addFC_Data as Data
import addFC_Logger as Logger
import copy
import FreeCAD
import json
import math
import os
import re
import subprocess
import xml.etree.ElementTree as ET


# ------------------------------------------------------------------------------


afc_additions = {
    'ezdxf': [True, '', 'color: #005500'],
    'ffmpeg': [True, '', 'color: #005500'],
    'numpy': [True, '', 'color: #005500'],
    'sm': [True, '', 'color: #005500'],
}


try:
    afc_additions['ezdxf'][1] = version('ezdxf')
except ImportError:
    afc_additions['ezdxf'][0] = False
    afc_additions['ezdxf'][2] = 'color: #aa0000'

try:
    # todo: Windows, macOS
    cp = subprocess.run(
        ['ffmpeg', '-version'],
        stdout=subprocess.DEVNULL,
    )
    if cp.returncode == 0:
        # todo: version number
        pass
    else:
        afc_additions['ffmpeg'][0] = False
        afc_additions['ffmpeg'][2] = 'color: #aa0000'
except BaseException:
    afc_additions['ffmpeg'][0] = False
    afc_additions['ffmpeg'][2] = 'color: #aa0000'

try:
    afc_additions['numpy'][1] = version('numpy')
except ImportError:
    afc_additions['numpy'][0] = False
    afc_additions['numpy'][2] = 'color: #aa0000'

try:
    import smwb_locator
    f = os.path.join(os.path.dirname(smwb_locator.__file__), 'package.xml')
    root = ET.parse(f).getroot()
    for i in root:
        if 'version' in i.tag:
            afc_additions['sm'][1] = i.text
            break
except ImportError:
    afc_additions['sm'][0] = False
    afc_additions['sm'][2] = 'color: #aa0000'


# ------------------------------------------------------------------------------


FC_VERSION = tuple(FreeCAD.Version()[0:3])

AFC_PATH = os.path.normpath(os.path.dirname(__file__))
AFC_PATH_ICON = os.path.join(AFC_PATH, 'repo', 'icon')

PATH_CONFIGURATION = os.path.join(AFC_PATH, 'pref', 'configuration.json')
PATH_EXPLOSION = os.path.join(AFC_PATH, 'pref', 'explosion.json')
PATH_MATERIALS = os.path.join(AFC_PATH, 'pref', 'materials.json')
PATH_PROPERTIES = os.path.join(AFC_PATH, 'pref', 'properties.json')
PATH_STEEL = os.path.join(AFC_PATH, 'pref', 'steel.json')

AVAILABLE_PROPERTY_TYPES = (
    'Bool',
    'Enumeration',
    'Float',
    'Integer',
    'String',
)

SYSTEM_PROPERTIES = ('!Body', '!Trace')

AVAILABLE_CHARACTERS = re.compile('[^A-Za-z0-9]')


# ------------------------------------------------------------------------------


def check_pref(path: str, std: dict) -> None:
    d = os.path.dirname(path)
    if not os.path.exists(d):
        os.makedirs(d)
    if not os.path.exists(path):
        file = open(path, 'w+', encoding='utf-8')
        json.dump(std, file, ensure_ascii=False, indent=4)
        file.close()
    elif not os.path.isfile(path):
        os.remove(path)
        check_pref(path, std)


def load_pref(path: str, std: dict, conf=False) -> dict:
    check_pref(path, std)
    try:
        file = open(path, 'r', encoding='utf-8')
        result = std | json.load(file)
        file.close()
        if conf:
            # outdated parameters:
            for i in list(result):
                if i not in Data.configuration:
                    _ = result.pop(i, None)
            # completeness:
            for i in Data.configuration:
                if i not in result:
                    result[i] = Data.configuration[i]
                value = Data.configuration[i]
                if type(value) is dict:
                    if type(result[i]) is not dict:
                        result[i] = value
                    else:
                        for j in value:
                            if j not in result[i]:
                                result[i][j] = value[j]
        return result
    except BaseException as e:
        Logger.error(f'load, pref: {e}')
        return std


def load_properties() -> dict:
    check_pref(PATH_PROPERTIES, Data.properties_core | Data.properties_add)
    try:
        file = open(PATH_PROPERTIES, 'r', encoding='utf-8')
        result = json.load(file)
        file.close()
    except BaseException as e:
        Logger.error(f'load, prop: {e}')
        result = Data.properties_add
    properties = copy.deepcopy(Data.properties_core)
    for key in result:
        if key not in properties:
            properties[re.sub(AVAILABLE_CHARACTERS, '', key)] = result[key]
            if len(properties[key][2]) > 0:  # enumeration
                # remove duplicates:
                enum = list(dict.fromkeys(properties[key][2]))
                # default value:
                if '-' not in enum:
                    enum.insert(0, '-')
                else:
                    i = enum.index('-')
                    if i != 0:
                        enum[i], enum[0] = enum[0], enum[i]
                #
                properties[key][2] = enum
    return properties


def load_steel() -> dict:
    check_pref(PATH_STEEL, Data.steel)
    try:
        file = open(PATH_STEEL, 'r', encoding='utf-8')
        result = json.load(file)
        file.close()
    except BaseException as e:
        Logger.error(f'load steel: {e}')
        result = Data.steel
    steel = {}
    for i in result:
        steel[i] = {}
        for j in result[i]:
            try:
                steel[i][float(j)] = result[i][j]
            except ValueError:
                pass
    return steel


def save_pref(path: str, pref: dict, indent=4) -> None:
    try:
        file = open(path, 'w+', encoding='utf-8')
        json.dump(pref, file, ensure_ascii=False, indent=indent)
        file.close()
    except BaseException as e:
        Logger.error(f'save pref: {e}')


pref_configuration = load_pref(PATH_CONFIGURATION, Data.configuration, True)
pref_explosion = load_pref(PATH_EXPLOSION, Data.explosion)
pref_materials = load_pref(PATH_MATERIALS, Data.materials)
pref_properties = load_properties()
pref_steel = load_steel()


# ------------------------------------------------------------------------------


class addFCPreferenceProperties():
    def __init__(self):
        self.form = FreeCAD.Gui.PySideUic.loadUi(os.path.join(
            AFC_PATH, 'repo', 'ui', 'pref_uProp.ui'))

        headers_properties = ('Title', 'Type', 'Addition', 'Alias')
        headers_values = ('Property', 'Values')

        color_black = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        color_blue = QtGui.QBrush(QtGui.QColor(0, 0, 150))
        color_grey = QtGui.QBrush(QtGui.QColor(100, 100, 100))
        color_red = QtGui.QBrush(QtGui.QColor(150, 0, 0))

        table_properties = self.form.tableProperties
        table_values = self.form.tableValues

        def align(t, i: int) -> None:
            t.resizeColumnsToContents()
            t.resizeRowsToContents()
            t.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)

        # ---------- #
        # properties #
        # ---------- #

        table_properties.setColumnCount(len(headers_properties))
        table_properties.setHorizontalHeaderLabels(headers_properties)
        table_properties.setRowCount(len(pref_properties))

        enum = {}

        addition_flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        x = 0
        for key in pref_properties:
            value = pref_properties[key]
            if value[0] == 'Enumeration':
                enum[key] = value[2]
            core = True if key in Data.properties_core else False
            # title:
            i = QtGui.QTableWidgetItem(key)
            if core:
                i.setFlags(QtCore.Qt.NoItemFlags)
            table_properties.setItem(x, 0, i)
            # type:
            i = QtGui.QTableWidgetItem(value[0])
            if core:
                i.setFlags(QtCore.Qt.NoItemFlags)
            else:
                if value[0] in AVAILABLE_PROPERTY_TYPES:
                    i.setForeground(color_blue)
                else:
                    i.setForeground(color_red)
            table_properties.setItem(x, 1, i)
            # addition:
            b = value[1]
            i = QtGui.QTableWidgetItem(str(b))
            if core:
                i.setFlags(QtCore.Qt.NoItemFlags)
            else:
                i.setFlags(addition_flags)
                i.setForeground(color_black if b else color_grey)
            table_properties.setItem(x, 2, i)
            # alias:
            i = QtGui.QTableWidgetItem(str(value[3]))
            table_properties.setItem(x, 3, i)
            #
            x += 1

        align(table_properties, headers_properties.index('Title'))

        # ------ #
        # values #
        # ------ #

        table_values.setColumnCount(len(headers_values))
        table_values.setHorizontalHeaderLabels(headers_values)
        table_values.setRowCount(len(enum))

        x = 0
        for key in enum:
            i = QtGui.QTableWidgetItem(key)
            i.setFlags(QtCore.Qt.NoItemFlags)
            table_values.setItem(x, 0, i)
            if key == 'Material':
                i = QtGui.QTableWidgetItem('... use the materials tab')
                i.setFlags(QtCore.Qt.NoItemFlags)
                table_values.setItem(x, 1, i)
            elif key == 'Unit':
                i = QtGui.QTableWidgetItem(', '.join(enum[key]))
                i.setFlags(QtCore.Qt.NoItemFlags)
                table_values.setItem(x, 1, i)
            else:
                i = QtGui.QTableWidgetItem(', '.join(enum[key]))
                table_values.setItem(x, 1, i)
            x += 1

        align(table_values, headers_values.index('Values'))

        # ------- #
        # actions #
        # ------- #

        def remove() -> None:
            table_properties.removeRow(table_properties.currentRow())
            check_values()
        self.form.pushButtonRemove.clicked.connect(remove)

        def add() -> None:
            count = table_properties.rowCount()
            table_properties.insertRow(count)
            i = QtGui.QTableWidgetItem('String')  # type
            i.setForeground(color_blue)
            table_properties.setItem(count, 1, i)
            i = QtGui.QTableWidgetItem('False')  # addition
            i.setFlags(addition_flags)
            i.setForeground(color_grey)
            table_properties.setItem(count, 2, i)
        self.form.pushButtonAdd.clicked.connect(add)

        def check_values(r: None | str = None) -> None:
            prop, backup = [], None
            for row in range(table_properties.rowCount()):
                i = table_properties.item(row, 1)  # type
                if i is not None:
                    if i.text() == 'Enumeration':
                        title = table_properties.item(row, 0)
                        if title is None:
                            return
                        if title.text() == '':
                            return
                        prop.append(title.text())
            for row in range(table_values.rowCount()):
                i = table_values.item(row, 0).text()  # title
                if i not in prop:
                    if r is None:
                        table_values.removeRow(row)
                    else:  # renaming
                        if table_values.item(row, 1) is not None:
                            backup = table_values.item(row, 1).text()
                        table_values.removeRow(row)
                else:
                    prop.remove(i)
            for i in prop:
                count = table_values.rowCount()
                table_values.insertRow(count)
                item = QtGui.QTableWidgetItem(i)
                item.setFlags(QtCore.Qt.NoItemFlags)
                table_values.setItem(count, 0, item)
                if backup is not None:
                    item = QtGui.QTableWidgetItem(backup)
                    table_values.setItem(count, 1, item)

        def changed(item) -> None | str:  # title, if renaming
            if item is None:
                return
            text = item.text()

            if item.column() == 0:
                t = table_properties.item(item.row(), 1)  # type
                t = '' if t is None else t.text()
                text = re.sub(AVAILABLE_CHARACTERS, '', text)
                if text == '':
                    return
                # duplicates:
                for row in range(table_properties.rowCount()):
                    if row == item.row():
                        continue
                    i = table_properties.item(row, 0)
                    if i is not None:
                        if i.text() == text:
                            text += ' (duplicate)'
                #
                item.setText(text)
                return text if t == 'Enumeration' else None

            if item.column() != 1:
                return
            elif text == '':
                return

            title = table_properties.item(item.row(), 0)
            if title is None:
                return
            elif title.text() == '':
                return

            if text in AVAILABLE_PROPERTY_TYPES:
                item.setForeground(color_blue)
            else:
                replaced = False
                for i in AVAILABLE_PROPERTY_TYPES:
                    if text.lower() in i.lower():
                        item.setText(i)
                        replaced = True
                if not replaced:
                    item.setForeground(color_red)
                    return
            if text == 'Enumeration':
                # duplicates:
                for row in range(table_values.rowCount()):
                    if table_values.item(row, 0).text() == title.text():
                        return
                # insert:
                count = table_values.rowCount()
                table_values.insertRow(count)
                i = QtGui.QTableWidgetItem(title.text())
                i.setFlags(QtCore.Qt.NoItemFlags)
                table_values.setItem(count, 0, i)

        def changed_wrapper(item) -> None:
            check_values(changed(item))
            align(table_properties, headers_properties.index('Title'))
            align(table_values, headers_values.index('Values'))

        def switch(item) -> None:
            if item is None:
                return
            if item.column() == 2:
                if item.text() == 'True':
                    item.setText('False')
                    item.setForeground(color_grey)
                else:
                    item.setText('True')
                    item.setForeground(color_black)

        self.form.tableProperties.itemChanged.connect(changed_wrapper)
        self.form.tableProperties.itemDoubleClicked.connect(switch)

        def check_current_value(item):
            if item.column() != 1:
                return
            values = table_values.item(item.row(), 1)
            if values is None:
                return
            values = values.text()
            if values == '':
                return
            split, enum = values.split(','), []
            for s in split:
                v = s.strip()
                if v != '' and v not in enum:
                    enum.append(v)
            if '-' not in enum:
                enum.insert(0, '-')
            else:
                index = enum.index('-')
                if index != 0:
                    enum[index], enum[0] = enum[0], enum[index]
            item.setText(', '.join(enum))

        self.form.tableValues.itemChanged.connect(check_current_value)

        return

    def saveSettings(self):
        table_properties = self.form.tableProperties
        table_values = self.form.tableValues

        properties = {}

        for row in range(table_properties.rowCount()):
            # title and type:
            p_title = table_properties.item(row, 0)
            p_type = table_properties.item(row, 1)
            if p_title is None or p_type is None:
                continue
            p_title = p_title.text().strip()
            p_type = p_type.text().strip()
            if p_title == '' or p_type not in AVAILABLE_PROPERTY_TYPES:
                continue
            # addition:
            p_addition = table_properties.item(row, 2)
            if p_addition is None:
                p_addition = 'False'
            else:
                p_addition = p_addition.text().strip()
            p_addition = True if p_addition == 'True' else False
            # alias:
            p_alias = table_properties.item(row, 3)
            if p_alias is None:
                p_alias = ''
            else:
                p_alias = p_alias.text().strip()
            # result:
            properties[p_title] = [p_type, p_addition, [], p_alias]

        for row in range(table_values.rowCount()):
            p_title = table_values.item(row, 0).text()
            if p_title not in properties or table_values.item(row, 1) is None:
                continue
            if p_title == 'Material':
                # core, only:
                properties[p_title][2] = Data.properties_core['Material'][2]
            else:
                split = table_values.item(row, 1).text().split(',')
                for s in split:
                    v = s.strip()
                    if v != '':
                        properties[p_title][2].append(v)

        global pref_properties
        pref_properties = properties
        save_pref(PATH_PROPERTIES, pref_properties, None)


# ------------------------------------------------------------------------------


class addFCPreferenceMaterials():
    def __init__(self):
        self.form = FreeCAD.Gui.PySideUic.loadUi(os.path.join(
            AFC_PATH, 'repo', 'ui', 'pref_materials.ui'))

        headers = ('Title', 'Category', 'Density', 'Unit', 'Price per unit')

        table = self.form.tableMaterials
        units = Data.properties_core['Unit'][2]  # standard

        color_black = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        color_blue = QtGui.QBrush(QtGui.QColor(0, 0, 150))
        color_grey = QtGui.QBrush(QtGui.QColor(100, 100, 100))
        color_red = QtGui.QBrush(QtGui.QColor(150, 0, 0))

        def set_default_material(default='') -> None:
            current = self.form.comboBoxDM.currentText()
            materials = []
            for row in range(table.rowCount()):
                i = table.item(row, 0)
                if i is not None:
                    text = i.text()
                    if text != '-':
                        materials.append(text)
            self.form.comboBoxDM.clear()
            self.form.comboBoxDM.addItems(materials)
            if default != '' and default in materials:
                self.form.comboBoxDM.setCurrentText(default)
            elif current in materials:
                self.form.comboBoxDM.setCurrentText(current)

        def align(t, i: int) -> None:
            t.resizeColumnsToContents()
            t.resizeRowsToContents()
            t.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)

        def purge() -> None:
            table.setSortingEnabled(False)
            table.clearSelection()
            table.clearContents()
            table.setColumnCount(0)
            table.setRowCount(0)

        def fill() -> None:
            purge()
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            table.setRowCount(len(pref_materials) - 1)  # without '-'
            x = 0
            for key in pref_materials:
                if key == '-':
                    continue
                if key == 'Galvanized' or key == 'Stainless':
                    std = True
                else:
                    std = False
                value = pref_materials[key]
                # title and category:
                i = QtGui.QTableWidgetItem(key)
                if std:
                    i.setFlags(QtCore.Qt.NoItemFlags)
                else:
                    if ' (duplicate)' in key:
                        i.setForeground(color_red)
                    else:
                        i.setForeground(color_black)
                table.setItem(x, 0, i)  # title
                i = QtGui.QTableWidgetItem(value[0])
                if std:
                    i.setFlags(QtCore.Qt.NoItemFlags)
                table.setItem(x, 1, i)  # category
                # density:
                density = value[1]
                i = QtGui.QTableWidgetItem(str(density))
                i.setForeground(color_grey if density == 0 else color_black)
                table.setItem(x, 2, i)
                # unit:
                unit = value[2]
                if unit not in units:
                    unit = '-'
                i = QtGui.QTableWidgetItem(unit)
                i.setForeground(color_blue)
                table.setItem(x, 3, i)
                # price:
                price = value[3]
                i = QtGui.QTableWidgetItem(str(price))
                i.setForeground(color_grey if price == 0 else color_black)
                table.setItem(x, 4, i)
                #
                x += 1
            align(table, headers.index('Title'))
            table.setSortingEnabled(True)

        fill()
        set_default_material(pref_configuration['default_material'])

        def default() -> None:
            global pref_materials
            pref_materials = Data.materials
            save_pref(PATH_MATERIALS, pref_materials, None)
            fill()
            set_default_material(pref_configuration['default_material'])
        self.form.pushButtonDefault.clicked.connect(default)

        def remove() -> None:
            title = table.item(table.currentRow(), 0)
            if title is not None:
                title = title.text()
                if title == 'Galvanized' or title == 'Stainless':  # standard
                    return
            table.removeRow(table.currentRow())
            set_default_material()
        self.form.pushButtonRemove.clicked.connect(remove)

        def add() -> None:
            x = table.rowCount()
            table.insertRow(x)
            table.setItem(x, 1, QtGui.QTableWidgetItem('User'))  # category
            table.setItem(x, 2, QtGui.QTableWidgetItem('0'))     # density
            table.setItem(x, 3, QtGui.QTableWidgetItem('kg'))    # unit
            table.setItem(x, 4, QtGui.QTableWidgetItem('0'))     # price
        self.form.pushButtonAdd.clicked.connect(add)

        def changed(item) -> None:
            if item is None:
                return
            text = item.text()
            match item.column():
                case 0:  # title
                    if text == '':
                        return
                    # duplicate = False
                    for row in range(table.rowCount()):
                        if row == item.row():
                            continue
                        i = table.item(row, 0)
                        if i is not None:
                            if i.text() == text:
                                text += ' (duplicate)'
                                # duplicate = True
                    item.setText(text)
                    if ' (duplicate)' in text:
                        item.setForeground(color_red)
                    else:
                        item.setForeground(color_black)
                case 1:  # category
                    if text == '':
                        item.setText('User')
                case 2 | 4:  # density and price
                    try:
                        i = int(text)
                        color = color_grey if i == 0 else color_black
                    except BaseException:
                        i = 0
                        color = color_grey
                    item.setText(str(i))
                    item.setForeground(color)
                case 3:  # unit
                    if text not in units:
                        if text == '':
                            item.setText('kg')
                        else:
                            item.setForeground(color_red)
                    else:
                        item.setForeground(color_blue)

        def changed_wrapper(item) -> None:
            changed(item)
            set_default_material()
            align(table, headers.index('Title'))

        self.form.tableMaterials.itemChanged.connect(changed_wrapper)

        return

    def saveSettings(self):
        dm = self.form.comboBoxDM.currentText()
        if pref_configuration['default_material'] != dm:
            pref_configuration['default_material'] = dm
            save_pref(PATH_CONFIGURATION, pref_configuration)

        table = self.form.tableMaterials
        units = Data.properties_core['Unit'][2]  # standard

        materials = {}

        for row in range(table.rowCount()):
            # title and category:
            title, category = table.item(row, 0), table.item(row, 1)
            if title is None or category is None:
                continue
            title, category = title.text().strip(), category.text().strip()
            if title == '':
                continue
            if category == '':
                category = 'User'
            # density:
            density = table.item(row, 2)
            if density is None:
                density = 0
            else:
                try:
                    density = int(density.text())
                except ValueError:
                    density = 0
            # unit, price per unit:
            unit, price = table.item(row, 3), table.item(row, 4)
            if unit is None:
                unit = '-'
            else:
                unit = unit.text()
                if unit not in units:
                    unit = '-'
            if price is None:
                price = 0
            else:
                try:
                    price = int(price.text())
                except ValueError:
                    price = 0
            # store:
            materials[title] = [category, density, unit, price]

        # standard values:
        materials['-'] = None
        if 'Galvanized' not in materials:
            materials['Galvanized'] = Data.materials['Galvanized']
        if 'Stainless' not in materials:
            materials['Stainless'] = Data.materials['Stainless']

        global pref_materials
        pref_materials = materials
        save_pref(PATH_MATERIALS, pref_materials, None)


# ------------------------------------------------------------------------------


class addFCPreferenceSM():
    def __init__(self):
        self.form = FreeCAD.Gui.PySideUic.loadUi(os.path.join(
            AFC_PATH, 'repo', 'ui', 'pref_sm.ui'))

        table_galvanized = self.form.tableGalvanized
        table_stainless = self.form.tableStainless

        headers = ('Thickness', 'Radius', 'K-Factor')

        def align(t) -> None:
            t.resizeColumnsToContents()
            t.resizeRowsToContents()
            t.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)

        def fill(t, d: dict) -> None:
            t.setColumnCount(len(headers))
            t.setHorizontalHeaderLabels(headers)
            t.setRowCount(len(d))
            x = 0
            i = QtGui.QTableWidgetItem
            for key in d:
                value = d[key]
                t.setItem(x, 0, i(str(key)))       # thickness
                t.setItem(x, 1, i(str(value[0])))  # radius
                t.setItem(x, 2, i(str(value[1])))  # k-factor
                x += 1
            align(t)

        fill(table_galvanized, pref_steel['Galvanized'])
        fill(table_stainless, pref_steel['Stainless'])

        def calculate_factor() -> None:
            for table in (table_galvanized, table_stainless):
                for row in range(table.rowCount()):
                    t = table.item(row, 0)  # thickness
                    if t is None:
                        continue
                    try:
                        t = max(0.1, float(t.text().replace(',', '.')))
                    except BaseException:
                        continue
                    r = table.item(row, 1)  # radius
                    if r is None:
                        r = t
                    else:
                        try:
                            r = max(0.1, float(r.text().replace(',', '.')))
                        except BaseException:
                            r = t
                    k = 1 / math.log(1 + t / r) - r / t
                    i = table.item(row, 2)
                    i.setText(str(round(k, 3)))  # k-factor
        self.form.calculate.clicked.connect(calculate_factor)

        def galvanized_default() -> None:
            fill(table_galvanized, Data.steel['Galvanized'])
        self.form.galvanizedDefault.clicked.connect(galvanized_default)

        def galvanized_remove() -> None:
            table_galvanized.removeRow(table_galvanized.currentRow())
        self.form.galvanizedRemove.clicked.connect(galvanized_remove)

        def galvanized_add() -> None:
            table_galvanized.insertRow(table_galvanized.rowCount())
            align(table_galvanized)
        self.form.galvanizedAdd.clicked.connect(galvanized_add)

        def stainless_default() -> None:
            fill(table_stainless, Data.steel['Stainless'])
        self.form.stainlessDefault.clicked.connect(stainless_default)

        def stainless_remove() -> None:
            table_stainless.removeRow(table_stainless.currentRow())
        self.form.stainlessRemove.clicked.connect(stainless_remove)

        def stainless_add() -> None:
            table_stainless.insertRow(table_stainless.rowCount())
            align(table_stainless)
        self.form.stainlessAdd.clicked.connect(stainless_add)

        def color_set(color: tuple | list) -> None:
            color = QtGui.QColor(*color).name()
            self.form.color.setText(color)
            self.form.color.setStyleSheet(
                'QPushButton {color:' + str(color) + '}')

        def color_get() -> None:
            color = QtGui.QColorDialog.getColor()
            if color.isValid():
                color_set(color.getRgb()[:-1])
        self.form.color.clicked.connect(color_get)

        color = QtGui.QColor(*pref_configuration['smp_color'])
        color_set(color.getRgb()[:-1])

        return

    def saveSettings(self):
        steel = {'Galvanized': {}, 'Stainless': {}}

        def read(table, key: str) -> None:
            for row in range(table.rowCount()):
                thickness = table.item(row, 0)
                radius = table.item(row, 1)
                factor = table.item(row, 2)
                if thickness is None or factor is None:
                    continue
                if radius is None:
                    radius = thickness
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
                steel[key][thickness] = [radius, factor]

        read(self.form.tableGalvanized, 'Galvanized')
        read(self.form.tableStainless, 'Stainless')

        global pref_steel
        pref_steel = steel
        save_pref(PATH_STEEL, pref_steel, None)

        color = self.form.color.text().lstrip('#')
        color = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
        pref_configuration['smp_color'] = color
        save_pref(PATH_CONFIGURATION, pref_configuration)
        return


# ------------------------------------------------------------------------------


PATH_RU_TPL = os.path.join(AFC_PATH, 'repo', 'add', 'stdRU', 'tpl')


def get_tpl() -> tuple[list, list, dict]:
    drawing, text, tpl = [], [], {}
    dirs = (
        os.path.join(PATH_RU_TPL, 'ЕСКД'),
        os.path.join(PATH_RU_TPL, 'СПДС'),
    )
    for d in dirs:
        if os.path.exists(d):
            for i in os.listdir(d):
                if i.endswith('.svg'):
                    text.append(i) if '_T_' in i else drawing.append(i)
                    tpl[i] = os.path.join(d, i)
    return drawing, text, tpl


class addFCPreferenceOther():
    def __init__(self):
        self.form = FreeCAD.Gui.PySideUic.loadUi(os.path.join(
            AFC_PATH, 'repo', 'ui', 'pref_other.ui'))

        font = pref_configuration['interface_font']

        self.form.fontCheckBox.setChecked(font[0])
        self.form.fontComboBox.setCurrentText(font[1])
        self.form.fontSpinBox.setValue(font[2])

        # additions:
        self.form.sm.setChecked(afc_additions['sm'][0])
        self.form.sm.setStyleSheet(afc_additions['sm'][2])
        if afc_additions['sm'][0]:
            self.form.sm.setText(f"SheetMetal ({afc_additions['sm'][1]})")
        self.form.ezdxf.setChecked(afc_additions['ezdxf'][0])
        self.form.ezdxf.setStyleSheet(afc_additions['ezdxf'][2])
        if afc_additions['ezdxf'][0]:
            self.form.ezdxf.setText(f"ezdxf ({afc_additions['ezdxf'][1]})")
        self.form.numpy.setChecked(afc_additions['numpy'][0])
        self.form.numpy.setStyleSheet(afc_additions['numpy'][2])
        if afc_additions['numpy'][0]:
            self.form.numpy.setText(f"NumPy ({afc_additions['numpy'][1]})")
        self.form.ffmpeg.setChecked(afc_additions['ffmpeg'][0])
        self.form.ffmpeg.setStyleSheet(afc_additions['ffmpeg'][2])

        stamp = pref_configuration['ru_std_tpl_stamp']

        self.form.Designation.setText(stamp['Designation'])
        self.form.Author.setText(stamp['Author'])
        self.form.Inspector.setText(stamp['Inspector'])
        self.form.Control1.setText(stamp['Control 1'])
        self.form.Control2.setText(stamp['Control 2'])
        self.form.Approver.setText(stamp['Approver'])
        self.form.Material1.setText(stamp['Material 1'])
        self.form.Material2.setText(stamp['Material 2'])
        self.form.Company1.setText(stamp['Company 1'])
        self.form.Company2.setText(stamp['Company 2'])
        self.form.Company3.setText(stamp['Company 3'])
        self.form.Title1.setText(stamp['Title 1'])
        self.form.Title2.setText(stamp['Title 2'])
        self.form.Title3.setText(stamp['Title 3'])
        self.form.Weight.setText(stamp['Weight'])
        self.form.Scale.setText(stamp['Scale'])
        self.form.Letter1.setText(stamp['Letter 1'])
        self.form.Letter2.setText(stamp['Letter 2'])
        self.form.Letter3.setText(stamp['Letter 3'])

        drawing, text, _ = get_tpl()

        self.form.Drawing.addItems(drawing)
        self.form.Text.addItems(text)

        self.form.Drawing.setCurrentText(
            pref_configuration['ru_std_tpl_drawing'])
        self.form.Text.setCurrentText(
            pref_configuration['ru_std_tpl_text'])

        return

    def saveSettings(self):
        if self.form.fontCheckBox.isChecked():
            add_autoload()
        fresh = {
            'interface_font': [
                self.form.fontCheckBox.isChecked(),
                self.form.fontComboBox.currentText(),
                self.form.fontSpinBox.value(),
            ],
            'ru_std_tpl_drawing': self.form.Drawing.currentText(),
            'ru_std_tpl_text': self.form.Text.currentText(),
            'ru_std_tpl_stamp': {
                'Designation': self.form.Designation.text(),
                'Author': self.form.Author.text(),
                'Inspector': self.form.Inspector.text(),
                'Control 1': self.form.Control1.text(),
                'Control 2': self.form.Control2.text(),
                'Approver': self.form.Approver.text(),
                'Material 1': self.form.Material1.text(),
                'Material 2': self.form.Material2.text(),
                'Company 1': self.form.Company1.text(),
                'Company 2': self.form.Company2.text(),
                'Company 3': self.form.Company3.text(),
                'Title 1': self.form.Title1.text(),
                'Title 2': self.form.Title2.text(),
                'Title 3': self.form.Title3.text(),
                'Weight': self.form.Weight.text(),
                'Scale': self.form.Scale.text(),
                'Letter 1': self.form.Letter1.text(),
                'Letter 2': self.form.Letter1.text(),
                'Letter 3': self.form.Letter1.text(),
            }}
        pref_configuration.update(fresh)
        save_pref(PATH_CONFIGURATION, pref_configuration)


def add_autoload() -> None:
    autoload = FreeCAD.ParamGet(
        'User parameter:BaseApp/Preferences/General').GetString(
            'BackgroundAutoloadModules')
    if 'addFC' not in autoload:
        autoload += ',addFC'
        FreeCAD.ParamGet(
            'User parameter:BaseApp/Preferences/General').SetString(
                'BackgroundAutoloadModules', autoload)
