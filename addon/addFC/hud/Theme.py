# addFC; additional tools for FreeCAD
#
# Copyright 2026 Golodnikov Sergey
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


def generate_css(panel, app_theme, hud_theme) -> tuple[str, str]:

    if hud_theme == 'Standard':
        if app_theme == 'dark':
            background_color = 'rgba(45, 45, 45, 180)'
            background_color_box = 'rgba(60, 60, 60, 180)'
            background_color_box_hover = 'rgba(20, 20, 20, 140)'
            border = '1px solid #282d2d'
            border_box = '1px solid #282d2d'
            # appy
            css_apply = (
                'QToolButton {'
                'border: 1px solid #282d2d;'
                'border-left: none;'
                '}'
                'QToolButton:hover {'
                'background-color: rgba(20, 20, 20, 140);'
                '}'
            )
        else:
            background_color = 'rgba(248, 248, 248, 120)'
            background_color_box = 'rgba(248, 248, 248, 120)'
            background_color_box_hover = 'rgba(248, 248, 248, 200)'
            border = '1px solid #646464'
            border_box = '1px solid #8c8c8c'
            # appy
            css_apply = (
                'QToolButton {'
                'background-color: #bebebe;'
                'border: 1px solid #8c8c8c;'
                'border-left: none;'
                '}'
                'QToolButton:hover {'
                'background-color: #a0a0a0;'
                '}'
            )
        border_radius = '0'
        border_radius_button = '0'
        padding_button = '2px'
        spin_box_radius = 'border-radius: 0;'
    else:
        if app_theme == 'dark':
            background_color = 'rgba(45, 45, 45, 200)'
            background_color_box = 'rgba(45, 45, 45, 220)'
            background_color_box_hover = 'rgba(25, 25, 25, 220)'
            border = '1px solid #141414'
            # appy
            css_apply = (
                'QToolButton {'
                'background-color: #232828;'
                'border-radius: 0;'
                'border-top-right-radius: 4px;'
                'border-bottom-right-radius: 4px;'
                '}'
                'QToolButton:hover {'
                'background-color: #141818;'
                '}'
            )
        else:
            background_color = 'rgba(248, 248, 248, 120)'
            background_color_box = 'rgba(248, 248, 248, 120)'
            background_color_box_hover = 'rgba(248, 248, 248, 180)'
            border = 'none'
            # appy
            css_apply = (
                'QToolButton {'
                'background-color: #a0a0a0;'
                'border-radius: 0;'
                'border-top-right-radius: 6px;'
                'border-bottom-right-radius: 6px;'
                '}'
                'QToolButton:hover {'
                'background-color: #8c8c8c;'
                '}'
            )
        border_box = 'none'
        border_radius = '6px'
        border_radius_button = '6px'
        padding_button = '4px'
        spin_box_radius = (
            'border-radius: 0;'
            'border-top-left-radius: 6px;'
            'border-bottom-left-radius: 6px;'
        )

    css = (
        'QWidget#HUD {'
        f'background-color: {background_color};'
        f'border-radius: {border_radius};'
        f'border: {border};'
        '}'
        'QToolButton {'
        'background: transparent;'
        f'border-radius: {border_radius_button};'
        'border: none;'
        f'padding: {padding_button};'
        '}'
        'QToolButton:hover {'
        'background-color: rgba(0, 0, 0, 60);'
        '}'
        'QDoubleSpinBox {'
        f'background-color: {background_color_box};'
        f'{spin_box_radius}'
        f'border: {border_box};'
        'padding: 2px 4px;'
        '}'
        'QDoubleSpinBox:hover {'
        f'background-color: {background_color_box_hover};'
        '}'
        'QCheckBox {'
        'padding: 2px 4px;'
        '}'
    )

    return css, css_apply
