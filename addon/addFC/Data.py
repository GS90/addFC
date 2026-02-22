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


import os


configuration = {
    'interface_font': [False, 'Sans Serif', 10],
    'working_directory': '',
    'default_material': 'Galvanized',
    'add_properties_nl': False,
    'add_properties_eq': True,
    # hud:
    'hud_autoload': False,
    'hud_panels': ['smart',],
    'hud_theme': 'Standard',  # 'Standard' or 'Rounded'
    'hud_opacity': 0,
    'hud_value_step': '1.0',
    'hud_tools_sequential': False,
    'hud_smart_cursor_offset': 10,
    'hud_smart_position': 'Below',  # 'Above' or 'Below'
    'hud_tools_ban_smart': [
        'Appearance',
        'Datum Line',
        'Datum Plane',
        'Coordinate System',
    ],
    # unfold:
    'unfold_dxf': True,
    'unfold_svg': False,
    'unfold_stp': False,
    'unfold_centering': False,
    'unfold_along_x': False,
    'unfold_file_name': 'Index',
    'unfold_file_signature': 'None',
    'unfold_prefix': 'Unfold',
    # bill of materials:
    'bom_export_type': 'Spreadsheet',
    'bom_export_alias': ['csv', 'spreadsheet'],
    'bom_export_merger': 'Type',
    'bom_export_sort': 'Name',
    'bom_export_skip': [],
    # 3d export:
    '3d_export_file_name': 'Name',
    '3d_export_prefix': '',
    '3d_export_save_by_type': False,
    '3d_export_save_copies': False,
    # 3d export, tessellation:
    'tessellation': {
        'mesher': 'standard',  # or mefisto
        'linear_deflection': 0.01,
        'angular_deflection': 30.0,
        'max_length': 1.0,  # mefisto only
    },
    # sheet metal part:
    'smp_color': tuple(int('b4c0c8'[i:i + 2], 16) for i in (0, 2, 4)),
    # insert:
    'drawing_templates_user': '',
    'drawing_templates_resource': 'stdRU',
    'insert_switch': True,
    # USDD:
    'ru_std_tpl_drawing': 'RU_Portrait_A4.svg',
    'ru_std_tpl_text': 'RU_Portrait_A4_T_1.svg',
    'ru_std_tpl_stamp': {
        'Designation': 'XXXX.XXXXXX.XXX',
        'Author': 'Иванов И. И.',
        'Inspector': '',
        'Control 1': '',
        'Control 2': '',
        'Approver': '',
        'Material 1': '',
        'Material 2': '',
        'Company 1': '',
        'Company 2': 'Организация',
        'Company 3': '',
        'Title 1': '',
        'Title 2': 'Изделие',
        'Title 3': '',
        'Weight': '',
        'Scale': '1:1',
        'Letter 1': '',
        'Letter 2': '',
        'Letter 3': '',
    },
    # library preferences:
    'library': {
        'debug': False,
        'lcoc': 'Enabled',
        'panel': True,
        'parameters': True,
        'recent': 'DIN',
        'sic': False,
        'variation': 'Simple',
    },
    'library_list': {
        'DIN': None,
        'ISO': None,
        'ГОСТ': None,
    },
}


# materials = title: [category, density, unit, price per unit]

materials = {
    '-': None,
    # standard:
    'Galvanized': ['Sheet metal', 7870, 'm^2', 0],
    'Stainless': ['Sheet metal', 7900, 'm^2', 0],
    # general:
    'Aluminum': ['General', 2700, 'kg', 0],
    'Brass': ['General', 8600, 'kg', 0],
    'Cast iron': ['General', 7300, 'kg', 0],
    'Ceramic': ['General', 2300, 'kg', 0],
    'Concrete': ['General', 2410, 'm^3', 0],
    'Copper': ['General', 8900, 'kg', 0],
    'Glass': ['General', 2530, 'kg', 0],
    'Mineral wool': ['General', 100, 'm^2', 0],
    'Rubber': ['General', 1000, 'kg', 0],
    'Steel': ['General', 7800, 'kg', 0],
    # aisi:
    'AISI 201': ['Sheet metal', 7860, 'm^2', 0],
    'AISI 304': ['Sheet metal', 7950, 'm^2', 0],
    'AISI 316': ['Sheet metal', 7970, 'm^2', 0],
    'AISI 321': ['Sheet metal', 8020, 'm^2', 0],
    'AISI 430': ['Sheet metal', 7720, 'm^2', 0],
    # plastic:
    'ABS': ['Plastic', 1040, 'kg', 0],
    'PETG': ['Plastic', 1340, 'kg', 0],
    'PLA': ['Plastic', 1240, 'kg', 0],
    'PP': ['Plastic', 900, 'kg', 0],
    'PVC': ['Plastic', 1330, 'kg', 0],
    # rubber:
    'EPDM': ['Rubber', 155, 'kg', 0],
    'Natural rubber': ['Rubber', 920, 'kg', 0],
    'Neoprene': ['Rubber', 1230, 'kg', 0],
    # wood:
    'Wood, low density': ['Wood', 500, 'm^3', 0],
    'Wood, medium density': ['Wood', 700, 'm^3', 0],
    'Wood, high density': ['Wood', 900, 'm^3', 0],
}


# properties = title: [type, addition, [enumeration], alias]

properties_core = {
    # required:
    'Name': ['String', False, [], ''],
    # core:
    'Code': ['String', False, [], ''],
    'Index': ['String', False, [], ''],
    'Material': ['Enumeration', False, ['-', 'Galvanized', 'Stainless', ], ''],
    'MetalThickness': ['Float', False, [], ''],
    'Node': ['String', False, [], ''],
    'Price': ['Float', True, [], ''],
    'Quantity': ['Float', True, [], ''],
    'Unfold': ['Bool', False, [], ''],
    'Unit': ['Enumeration', False, ['-', 'm', 'kg', 'm^2', 'm^3'], ''],
    'Weight': ['Float', True, [], ''],
}

properties_add = {
    # additional:
    'Format': ['Enumeration', False, ['-', 'A0', 'A1', 'A2', 'A3', 'A4'], ''],
    'Id': ['String', False, [], ''],
    'Note': ['String', False, [], ''],
    'Type': ['Enumeration', False, [
        '-',
        'Part',
        'Sheet metal part',
        'Fastener',
        'Material',
    ], ''],
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


# steel = title: {thickness: [radius, k-factor]}

steel = {
    'Galvanized': {
        '0.35': [1.0, 0.475],
        '0.4': [1.0, 0.472],
        '0.45': [1.0, 0.469],
        '0.5': [1.0, 0.466],
        '0.55': [1.0, 0.464],
        '0.6': [1.0, 0.461],
        '0.65': [1.0, 0.458],
        '0.7': [1.3, 0.464],
        '0.75': [1.3, 0.462],
        '0.8': [1.3, 0.460],
        '0.9': [1.3, 0.456],
        '1.0': [1.3, 0.453],
        '1.2': [1.7, 0.456],
        '1.4': [1.7, 0.450],
        '1.5': [1.7, 0.448],
        '1.8': [1.7, 0.440],
        '2.0': [2.7, 0.454],
        '2.5': [2.7, 0.446],
        '3.0': [3.3, 0.446],
        '3.5': [3.3, 0.440],
    },
    'Stainless': {
        '0.4': [1.0, 0.472],
        '0.5': [1.0, 0.466],
        '0.6': [1.0, 0.461],
        '0.7': [1.3, 0.464],
        '0.8': [1.3, 0.460],
        '0.9': [1.3, 0.456],
        '1.0': [1.3, 0.453],
        '1.2': [1.7, 0.456],
        '1.5': [1.7, 0.448],
        '2.0': [2.7, 0.454],
        '2.5': [2.7, 0.446],
        '3.0': [3.3, 0.446],
        '4.0': [5.3, 0.453],
        '5.0': [6.7, 0.454],
        '6.0': [8.3, 0.455],
        '8.0': [10.5, 0.453],
        '10.0': [13.3, 0.454],
        '12.0': [16.7, 0.455],
    },
}


# summary, previously used values

summary = {
    # units of measurement
    'Area_U': 'mm^2',
    'BB_U': 'mm',
    'DLRD_U': 'mm',
    'Perimeter_U': 'mm',
    'Volume_U': 'mm^3',
    'Weight_U': 'g',
    # last used material and precision
    'Material': '-',
    'Decimals': 2,
}


# video

video_options = {
    'size': {
        '480p (SD)': (640, 480),
        '720p (HD)': (1280, 720),
        '1080p (FHD)': (1920, 1080),
        '1440p (QHD)': (2560, 1440),
        '2K video': (2048, 1080),
        '4K video': (3840, 2160),
        '8K video': (7680, 4320),
    },
    'background': ('Current', 'White', 'Black', 'Transparent'),
    'method': {
        'Offscreen': 'QtOffscreenRenderer',
        'Framebuffer': 'FramebufferObject',
    },
    'image_format': {'PNG': '.png', 'JPG': '.jpg'}
}

video_pref_std = {
    'size': '1080p (FHD)',
    'width': 1920,
    'height': 1080,
    'background': 'Current',
    'method': 'Framebuffer',
    'image_format': 'PNG',
    'framerate': 60,
    'export_dir': os.path.expanduser('~/Desktop'),
    'export_storyboard': os.path.join(
        os.path.expanduser('~/Desktop'), '_storyboard'),
}
