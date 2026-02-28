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


from PySide import QtWidgets
from addon.addFC import Preference as P


# todo: Gui.runCommand('Std_TreeSelection')


if int(P.FC_VERSION[0]) > 0:
    pd_tools_std = [
        ('Measure', 'Std_Measure', 'umf-measurement', 1),
        ('Go to Linked Object', 'Std_LinkSelectLinked', 'LinkSelect', 1),
        ('Align to Selection',
         'Std_AlignToSelection', 'align-to-selection', 1),
        ('Fit Selection', 'Std_ViewFitSelection', 'zoom-selection', 1),
        ('Toggle Transparency',
         'Std_ToggleTransparency', 'Std_ToggleTransparency', 1),
    ]
else:
    pd_tools_std = [
        ('Measure', 'Part_Measure_Linear', 'Part_Measure_Linear', 1),
        ('Go to Linked Object', 'Std_LinkSelectLinked', 'LinkSelect', 1),
        ('Fit Selection', 'Std_ViewFitSelection', 'zoom-selection', 1),
    ]

pd_tools_std.extend([
    # other
    ('Transform', 'Std_TransformManip', 'Std_TransformManip', 1),
    ('Appearance', 'Std_SetAppearance', 'Std_SetAppearance', 1),
    ('Random Color', 'Std_RandomColor', 'Std_RandomColor', 1),
    # pd:sketch
    ('New Sketch', 'PartDesign_NewSketch', 'Sketcher_NewSketch', 1),
    ('Edit Sketch', 'Sketcher_EditSketch', 'Sketcher_EditSketch', 1),
    # datum
    ('Datum Point', 'PartDesign_Point', 'PartDesign_Point', 1),
    ('Datum Line', 'PartDesign_Line', 'PartDesign_Line', 1),
    ('Datum Plane', 'PartDesign_Plane', 'PartDesign_Plane', 1),
    ('Coordinate System',
     'PartDesign_CoordinateSystem', 'PartDesign_CoordinateSystem', 1),
    # pd:binder
    ('Binder', 'PartDesign_SubShapeBinder', 'PartDesign_SubShapeBinder', 1),
    # pd:uno
    ('Pad', 'PartDesign_Pad', 'PartDesign_Pad', 2),
    ('Pocket', 'PartDesign_Pocket', 'PartDesign_Pocket', 2),
    ('Hole', 'PartDesign_Hole', 'PartDesign_Hole', 2),
    # pd:dos
    ('Fillet', 'PartDesign_Fillet', 'PartDesign_Fillet', 2),
    ('Chamfer', 'PartDesign_Chamfer', 'PartDesign_Chamfer', 2),
    ('Draft', 'PartDesign_Draft', 'PartDesign_Draft', 2),
    ('Thickness', 'PartDesign_Thickness', 'PartDesign_Thickness', 2),
    # pd:secondary
    ('Mirror',
     'PartDesign_Mirrored', 'PartDesign_Mirrored', 1),
    ('Linear Pattern',
     'PartDesign_LinearPattern', 'PartDesign_LinearPattern', 1),
    ('Polar Pattern',
     'PartDesign_PolarPattern', 'PartDesign_PolarPattern', 1),
    ('Multi Transform',
     'PartDesign_MultiTransform', 'PartDesign_MultiTransform', 1),
])

pd_tools_sm = [
    ('Make Base Wall',
     'SheetMetal_AddBase', 'SheetMetal_AddBase', 2),
    ('Make Wall',
     'SheetMetal_AddWall', 'SheetMetal_AddWall', 2),
    ('Extend Face',
     'SheetMetal_Extrude', 'SheetMetal_Extrude', 2),
    ('Unattended Unfold',
     'SheetMetal_UnattendedUnfold', 'SheetMetal_UnfoldUnattended', 2),
]

pd_tools_draft = [  # other cmd
    ('Draft Clone', '', 'Draft_Clone', 1),
    ('Draft Mirror', '', 'Draft_Mirror', 1),
    ('Draft Array Ortho', '', 'Draft_Array', 1),
    ('Draft Array Polar', '', 'Draft_PolarArray', 1),
    ('Draft Array Circular', '', 'Draft_CircularArray', 1),
]

pd_activity_ban = (
    'Measure',
    'Go to Linked Object',
    'Align to Selection',
    'Fit Selection',
    'Toggle Transparency',
    'Transform',
    'Appearance',
    'Random Color',
    'Binder',
    # Draft
    'Draft Clone',
    'Draft Mirror',
    'Draft Array Ortho',
    'Draft Array Polar',
    'Draft Array Circular',
)

pd_tools_continuation = (
    'Pad',
    'Pocket',
)

pd_tools_parent = (
    'Toggle Transparency',
    'Transform',
    'Appearance',
    'Random Color',
    # Draft
    'Draft Clone',
    'Draft Mirror',
    'Draft Array Ortho',
    'Draft Array Polar',
    'Draft Array Circular',
)


# ------------------------------------------------------------------------------


tools_access = {
    'PartDesignWorkbench': {
        'Other': [  # link
            'Measure',              # 2 entities
            'Go to Linked Object',
            'Align to Selection',
            'Fit Selection',
        ],
        'Outline': [
            'Measure',            # 2 entities
            'Edit Sketch',        # exception
            'Datum Point',
            'Datum Line',
            'Datum Plane',        # 2 entities
            'Coordinate System',
            'Pad',
            'Pocket',
            'Hole',
            'Make Base Wall',
        ],
        'Edge': [
            'Measure',            # 2 entities
            'Datum Point',
            'Datum Line',
            'Datum Plane',
            'Coordinate System',
            'Fillet',
            'Chamfer',
            'Make Wall',
        ],
        'Face': [
            'Measure',             # 2 entities
            'Align to Selection',
            'Edit Sketch',         # exception
            'Datum Point',
            'Datum Line',
            'Datum Plane',
            'Binder',
            'New Sketch',
            'Pad',
            'Pocket',
            'Fillet',
            'Chamfer',
            'Draft',
            'Thickness',
            'Extend Face',
            'Unattended Unfold',
        ],
        'Vertex': [
            'Measure',            # 2 entities
            'Datum Point',
            'Coordinate System',
        ],
        'Solid': [  # or 'Compound'
            'Measure',              # 2 entities
            'Toggle Transparency',
            'Transform',
            'Appearance',
            'Random Color',
            # draft
            'Draft Clone',
            'Draft Mirror',
            'Draft Array Ortho',
            'Draft Array Polar',
            'Draft Array Circular',
        ],
        'Plane': [
            'New Sketch',
            'Datum Plane',
        ],
        'Datum': [
            'New Sketch',
        ],
        'Secondary': [
            'Mirror',
            'Linear Pattern',
            'Polar Pattern',
            'Multi Transform',
        ]
    },
}


# ------------------------------------------------------------------------------


tools_value = {
    # pd:uno
    'Pad': (QtWidgets.QAbstractSpinBox, 'lengthEdit', 10),
    'Pocket': (QtWidgets.QAbstractSpinBox, 'lengthEdit', 5),
    # pd:dos
    'Fillet': (QtWidgets.QAbstractSpinBox, 'filletRadius', 1),
    'Chamfer': (QtWidgets.QAbstractSpinBox, 'chamferSize', 1),
    'Draft': (QtWidgets.QAbstractSpinBox, 'draftAngle', 1),
    'Thickness': (QtWidgets.QAbstractSpinBox, 'Value', 1),
    # sm
    'Make Base Wall': (QtWidgets.QAbstractSpinBox, 'spinLength', 100),
    'Make Wall': (QtWidgets.QAbstractSpinBox, 'Length', 10),
    'Extend Face': (QtWidgets.QAbstractSpinBox, 'Length', 10),
}

tools_checkbox = {
    # pd:uno
    'Pad': (
        (QtWidgets.QCheckBox, 'checkBoxMidplane', False, 'Symmetric'),
        (QtWidgets.QCheckBox, 'checkBoxReversed', False, 'Reversed'),
    ),
    'Pocket': (
        (QtWidgets.QCheckBox, 'checkBoxMidplane', False, 'Symmetric'),
        (QtWidgets.QCheckBox, 'checkBoxReversed', False, 'Reversed'),
        (QtWidgets.QComboBox, 'changeMode', False, 'Through all'),
    ),
    # pd:dos
    'Fillet': (
        (QtWidgets.QCheckBox, 'checkBoxUseAllEdges', False, 'All Edges'),
    ),
    'Chamfer': (
        (QtWidgets.QCheckBox, 'checkBoxUseAllEdges', False, 'All Edges'),
    ),
    'Draft': (
        (QtWidgets.QCheckBox, 'checkReverse', False, 'Reverse'),
    ),
    'Thickness': (
        (QtWidgets.QCheckBox, 'checkIntersection', False, 'Intersection'),
        (QtWidgets.QCheckBox, 'checkReverse', False, 'Inwards'),
    ),
    # sm
    'Make Wall': (
        (QtWidgets.QPushButton, 'buttRevWall', False, 'Reverse'),
    ),
    'Make Base Wall': (
        (QtWidgets.QCheckBox, 'checkSymetric', False, 'Symmetric'),
        (QtWidgets.QCheckBox, 'checkRevDirection', False, 'Reversed'),
    ),
}

# differences in version 1.2+
tools_checkbox_exception = (
    QtWidgets.QComboBox, 'sidesMode', False, 'Symmetric',
)
