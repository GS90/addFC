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


def generate_css(panel, app_theme, hud_theme) -> tuple[str, str, str, str]:
    # todo: panel

    if app_theme == 'dark':
        if hud_theme == 'Rounded':
            css = (
                'QWidget#HUD {'
                'background-color: #2e3436;'
                'border-radius: 6px;'
                'border: none;'
                '}'
                'QToolButton {'
                'background: none;'
                'border-radius: 6px;'
                'border: none;'
                'padding: 4px;'
                '}'
                'QToolButton:hover {'
                'background-color: #1c2223;'
                '}'
                'QDoubleSpinBox {'
                'background-color: #1c2223;'
                'border-radius: 0;'
                'border: none;'
                'border-top-left-radius: 6px;'
                'border-bottom-left-radius: 6px;'
                'padding: 2px 4px;'
                '}'
                'QCheckBox {'
                'padding: 2px 4px;'
                '}'
            )
            css_apply = (
                'QToolButton {'
                'background-color: #121819;'
                'border-radius: 0;'
                'border-top-right-radius: 6px;'
                'border-bottom-right-radius: 6px;'
                '}'
                'QToolButton:hover {'
                'background-color: #000000;'
                '}'
            )
        else:
            # Standard
            css = (
                'QWidget#HUD {'
                'background-color: #2e3436;'
                'border-radius: 0;'
                'border: 1px solid #1c2223;'
                '}'
                'QToolButton {'
                'background: none;'
                'border-radius: 0;'
                'border: none;'
                'padding: 2px;'
                '}'
                'QToolButton:hover {'
                'background-color: #1c2223;'
                '}'
                'QDoubleSpinBox {'
                'background-color: #1c2223;'
                'border-radius: 0;'
                'border: 1px solid #080e0f;'
                'padding: 2px 4px;'
                '}'
                'QCheckBox {'
                'padding: 2px 4px;'
                '}'
            )
            css_apply = (
                'QToolButton {'
                'background-color: #121819;'
                'border: 1px solid #080e0f;'
                'border-left: none;'
                '}'
                'QToolButton:hover {'
                'background-color: #000000;'
                '}'
            )
        css_fx = (
            'QToolButton {'
            'background-color: #1c2223;'
            'border-radius: 0;'
            'border: none;'
            '}'
            'QToolButton:hover {'
            'background-color: #2e3436;'
            '}'
        )
        css_active = 'background-color: #1c2223;'
    else:
        # std, light
        if hud_theme == 'Rounded':
            css = (
                'QWidget#HUD {'
                'background-color: #e6e6e6;'
                'border-radius: 6px;'
                'border: none;'
                '}'
                'QToolButton {'
                'background: none;'
                'border-radius: 6px;'
                'border: none;'
                'padding: 4px;'
                '}'
                'QToolButton:hover {'
                'background-color: #b4b4b4;'
                '}'
                'QDoubleSpinBox {'
                'background-color: #ffffff;'
                'border-radius: 0;'
                'border: none;'
                'border-bottom-left-radius: 6px;'
                'border-top-left-radius: 6px;'
                'padding: 2px 4px;'
                '}'
                'QCheckBox {'
                'padding: 2px 4px;'
                '}'
            )
            css_apply = (
                'QToolButton {'
                'background-color: #b4b4b4;'
                'border-radius: 0;'
                'border-top-right-radius: 6px;'
                'border-bottom-right-radius: 6px;'
                '}'
                'QToolButton:hover {'
                'background-color: #a0a0a0;'
                '}'
            )
        else:
            # Standard
            css = (
                'QWidget#HUD {'
                'background-color: #e6e6e6;'
                'border-radius: 0;'
                'border: 1px solid #505050;'
                '}'
                'QToolButton {'
                'background: none;'
                'border-radius: 0;'
                'border: none;'
                'padding: 2px;'
                '}'
                'QToolButton:hover {'
                'background-color: #b4b4b4;'
                '}'
                'QDoubleSpinBox {'
                'background-color: #ffffff;'
                'border-radius: 0;'
                'border: 1px solid #8c8c8c;'
                'padding: 2px 4px;'
                '}'
                'QCheckBox {'
                'padding: 2px 4px;'
                '}'
            )
            css_apply = (
                'QToolButton {'
                'background-color: #c8c8c8;'
                'border: 1px solid #8c8c8c;'
                'border-left: none;'
                '}'
                'QToolButton:hover {'
                'background-color: #b4b4b4;'
                '}'
            )
        css_fx = (
            'QToolButton {'
            'background-color: #ffffff;'
            'border-radius: 0;'
            '}'
            'QToolButton:hover {'
            'background-color: #e6e6e6;'
            '}'
        )
        css_active = 'background-color: #b4b4b4;'

    return css, css_fx, css_apply, css_active
