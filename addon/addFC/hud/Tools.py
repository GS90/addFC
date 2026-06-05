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


if int(P.FC_VERSION[0]) > 0:
    pd_tools_std = [
        ('Measure',
         'Std_Measure', 'umf-measurement', 1),
        ('Go to Linked Object',
         'Std_LinkSelectLinked', 'LinkSelect', 1),
        ('Align to Selection',
         'Std_AlignToSelection', 'align-to-selection', 1),
        ('Fit Selection',
         'Std_ViewFitSelection', 'zoom-selection', 1),
        ('Toggle Transparency',
         'Std_ToggleTransparency', 'Std_ToggleTransparency', 1),
        ('Variable Set',
         'Std_VarSet', 'VarSet', 1),
    ]
else:
    pd_tools_std = [
        ('Measure', 'Part_Measure_Linear', 'Part_Measure_Linear', 1),
        ('Go to Linked Object', 'Std_LinkSelectLinked', 'LinkSelect', 1),
        ('Fit Selection', 'Std_ViewFitSelection', 'zoom-selection', 1),
    ]

pd_tools_std.extend([
    # base
    ('Create Group', 'Std_Group', 'Group', 1),
    ('Create Part', 'Std_Part', 'Geofeaturegroup', 1),
    ('Create Body', 'PartDesign_Body', 'PartDesign_Body', 1),
    # other
    ('Transform', 'Std_TransformManip', 'Std_TransformManip', 1),
    ('Appearance', 'Std_SetAppearance', 'Std_SetAppearance', 1),
    ('Random Color', 'Std_RandomColor', 'Std_RandomColor', 1),
    ('Toggle Visibility', 'Std_ToggleVisibility', 'Std_ToggleVisibility', 1),
    ('Set Tip', 'PartDesign_MoveTip', 'PartDesign_MoveTip', 1),
    ('Make Link', 'Std_LinkMake', 'Link', 1),
    # pd:sketch
    ('New Sketch', 'PartDesign_NewSketch', 'Sketcher_NewSketch', 1),
    ('Edit Sketch', 'Sketcher_EditSketch', 'Sketcher_EditSketch', 1),
    ('Validate Sketch',
     'Sketcher_ValidateSketch', 'Sketcher_ValidateSketch', 1),
    # spreadsheet
    ('New Spreadsheet', 'Spreadsheet_CreateSheet', 'Spreadsheet', 1),
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
    ('Revolution', 'PartDesign_Revolution', 'PartDesign_Revolution', 2),
    ('Additive Loft', 'PartDesign_AdditiveLoft', 'PartDesign_AdditiveLoft', 2),
    ('Pocket', 'PartDesign_Pocket', 'PartDesign_Pocket', 2),
    ('Hole', 'PartDesign_Hole', 'PartDesign_Hole', 2),
    # pd:dos
    ('Fillet', 'PartDesign_Fillet', 'PartDesign_Fillet', 2),
    ('Chamfer', 'PartDesign_Chamfer', 'PartDesign_Chamfer', 2),
    ('Draft', 'PartDesign_Draft', 'PartDesign_Draft', 2),
    ('Thickness', 'PartDesign_Thickness', 'PartDesign_Thickness', 2),
    # pd:subsequent
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
     'SheetMetal_UnattendedUnfold', 'SheetMetal_UnfoldUnattended', 1),
]

pd_tools_part = [
    ('Create Simple Copy', 'Part_SimpleCopy', 'PartWorkbench', 1),
]

pd_tools_draft = [  # other cmd
    ('Draft Clone', '', 'Draft_Clone', 1),
    ('Draft Mirror', '', 'Draft_Mirror', 1),
    ('Draft Array Ortho', '', 'Draft_Array', 1),
    ('Draft Array Polar', '', 'Draft_PolarArray', 1),
    ('Draft Array Circular', '', 'Draft_CircularArray', 1),
]


# ------------------------------------------------------------------------------


sk_tools_std = [
    ('Horizontal Distance',
     'Sketcher_ConstrainDistanceX', 'Constraint_HorizontalDistance', 1),
    ('Vertical Distance',
     'Sketcher_ConstrainDistanceY', 'Constraint_VerticalDistance', 1),
    ('Distance',
     'Sketcher_ConstrainDistance', 'Constraint_Length', 1),
    ('Radius',
     'Sketcher_CompConstrainRadDia', 'Constraint_Radius', 1),    # value 0
    ('Diameter',
     'Sketcher_CompConstrainRadDia', 'Constraint_Diameter', 1),  # value 1
    ('Angle',
     'Sketcher_ConstrainAngle', 'Constraint_InternalAngle', 1),
    ('Symmetric',
     'Sketcher_ConstrainSymmetric', 'Constraint_Symmetric', 1),
    ('Vertically',
     'Sketcher_ConstrainVertical', 'Constraint_Vertical', 1),
    ('Horizontally',
     'Sketcher_ConstrainHorizontal', 'Constraint_Horizontal', 1),
    ('Parallel',
     'Sketcher_ConstrainParallel', 'Constraint_Parallel', 1),
    ('Perpendicular',
     'Sketcher_ConstrainPerpendicular', 'Constraint_Perpendicular', 1),
    ('Tangent',
     'Sketcher_ConstrainTangent', 'Constraint_Tangent', 1),
    ('Equal',
     'Sketcher_ConstrainEqual', 'Constraint_EqualLength', 1),
    ('Coincident',
     'Sketcher_ConstrainCoincident', 'Constraint_PointOnPoint', 1),
    ('Point Onto Object',
     'Sketcher_ConstrainPointOnObject', 'Constraint_PointOnObject', 1),
    ('Block',
     'Sketcher_ConstrainBlock', 'Constraint_Block', 1),
    ('Lock',
     'Sketcher_ConstrainLock', 'Constraint_Lock', 1),
    ('Toggle Construction',
     'Sketcher_ToggleConstruction', 'Sketcher_ToggleConstruction', 1),
]

if int(P.FC_VERSION[0]) > 0:
    sk_tools_std.extend([
        ('Create External Geometry',
         'Sketcher_CompExternal', 'Sketcher_Projection_Constr', 1),
    ])
else:
    sk_tools_std.extend([
        ('Create External Geometry',
         'Sketcher_External', 'Sketcher_External', 1),
    ])


# ------------------------------------------------------------------------------


tools_access = {
    'PartDesignWorkbench': {
        'Base': [
            'Variable Set',
            'Create Group',
            'Create Part',
            'Create Body',
            'New Sketch',
            'New Spreadsheet',
        ],
        'Other': [  # or 'Link'
            'Measure',
            'Go to Linked Object',
            'Fit Selection',
            'Create Simple Copy',
        ],
        'Outline': [
            'Measure',
            'Fit Selection',
            'Toggle Visibility',
            'Additive Loft',
            'Edit Sketch',
            'Validate Sketch',
            'Datum Point',
            'Datum Line',
            'Datum Plane',
            'Coordinate System',
            'Pad',
            'Revolution',
            'Pocket',
            'Hole',
            'Make Base Wall',
        ],
        'OutlineUsed': [
            'Measure',
            'Fit Selection',
            'Toggle Visibility',
            'Edit Sketch',
            'Datum Point',
            'Datum Line',
            'Datum Plane',
            'Coordinate System',
        ],
        'Edge': [
            'Measure',
            'Fit Selection',
            'Datum Point',
            'Datum Line',
            'Datum Plane',
            'Coordinate System',
            'Fillet',
            'Chamfer',
            'Make Wall',
        ],
        'Face': [
            'Measure',
            'Fit Selection',
            'Align to Selection',
            'Edit Sketch',
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
            'Measure',
            'Fit Selection',
            'Datum Point',
            'Coordinate System',
        ],
        'Solid': [  # or 'Compound'
            'Measure',
            'Fit Selection',
            'Toggle Visibility',
            'Toggle Transparency',
            'Transform',
            'Appearance',
            'Random Color',
            'Make Link',
            # part
            'Create Simple Copy',
            # sm
            'Unattended Unfold',
            # draft
            'Draft Clone',
            'Draft Mirror',
            'Draft Array Ortho',
            'Draft Array Polar',
            'Draft Array Circular',
        ],
        'Plane': [
            'Toggle Visibility',
            'New Sketch',
            'Datum Plane',
        ],
        'Datum': [
            'Toggle Visibility',
            'New Sketch',
        ],
        'Sequential': [
            'Mirror',
            'Linear Pattern',
            'Polar Pattern',
            'Multi Transform',
        ],
        # treeView
        'TreeEntity': [
            'Toggle Visibility',
            'Set Tip',
            'Edit Sketch',
            'Mirror',
            'Linear Pattern',
            'Polar Pattern',
            'Multi Transform',
        ],
        'TreeLink': [
            'Go to Linked Object',
            'Fit Selection',
            'Toggle Visibility',
            'Create Simple Copy',
        ],
        'TreePart': [
            'Fit Selection',
            'Toggle Visibility',
            'Transform',
            'Make Link',
            # part
            'Create Simple Copy',
            # draft
            'Draft Clone',
            'Draft Mirror',
            'Draft Array Ortho',
            'Draft Array Polar',
            'Draft Array Circular',
        ],
        'TreeParent': [
            'Fit Selection',
            'Toggle Visibility',
            'Toggle Transparency',
            'Transform',
            'Appearance',
            'Random Color',
            'Make Link',
            # part
            'Create Simple Copy',
            # draft
            'Draft Clone',
            'Draft Mirror',
            'Draft Array Ortho',
            'Draft Array Polar',
            'Draft Array Circular',
        ],
    },
    'SketcherWorkbench': {
        # Axis, Line, Curve, Point, Root (N)
        'Axis': [],
        'Axis|N': [],
        'Line': [
            'Block',
            'Distance',
            'Horizontal Distance',
            'Horizontally',
            'Toggle Construction',
            'Vertical Distance',
            'Vertically',
        ],
        'Line|N': [
            'Angle',
            'Block',
            'Equal',
            'Horizontally',
            'Parallel',
            'Perpendicular',
            'Tangent',
            'Toggle Construction',
            'Vertically',
        ],
        'Curve': [
            'Block',
            'Diameter',
            'Radius',
            'Toggle Construction',
        ],
        'Curve|N': [
            'Block',
            'Diameter',
            'Equal',
            'Radius',
            'Tangent',
            'Toggle Construction',
        ],
        'Point': [
            'Horizontal Distance',
            'Lock',
            'Vertical Distance',
        ],
        'Point|N': [
            'Coincident',
            'Horizontal Distance',
            'Horizontally',
            'Lock',
            'Vertical Distance',
            'Vertically',
        ],
        'Root': [],
        'Root|N': [],
        # Axis|Curve|Line|Point|Root
        'Axis|Curve': [
            'Tangent',
        ],
        'Axis|Line': [
            'Parallel',
            'Perpendicular',
        ],
        'Axis|Point': [
            'Point Onto Object',
        ],
        'Axis|Root': [],
        'Curve|Line': [
            'Block',
            'Tangent',
        ],
        'Curve|Point': [
            'Point Onto Object',
        ],
        'Curve|Root': [
            'Point Onto Object',
        ],
        'Line|Point': [
            'Distance',
            'Point Onto Object',
            'Symmetric',
        ],
        'Line|Root': [
            'Distance',
            'Point Onto Object',
            'Symmetric',
        ],
        'Point|Root': [
            'Coincident',
            'Horizontal Distance',
            'Horizontally',
            'Lock',
            'Vertical Distance',
            'Vertically',
        ],
    },
}


# ------------------------------------------------------------------------------


pd_activity_ban = (
    'Measure',
    'Go to Linked Object',
    'Align to Selection',
    'Fit Selection',
    'Toggle Transparency',
    'Transform',
    'Appearance',
    'Random Color',
    'Toggle Visibility',
    'Set Tip',
    'Make Link',
    'Binder',
    # part
    'Create Simple Copy',
    # draft
    'Draft Clone',
    'Draft Mirror',
    'Draft Array Ortho',
    'Draft Array Polar',
    'Draft Array Circular',
)

pd_tools_continuation = (
    'Pad',
    'Pocket',
    'Hole',
)

pd_tools_parent = (
    'Toggle Transparency',
    'Transform',
    'Appearance',
    'Random Color',
    'Make Link',
    'Toggle Visibility',
    # part
    'Create Simple Copy',
    # draft
    'Draft Clone',
    'Draft Mirror',
    'Draft Array Ortho',
    'Draft Array Polar',
    'Draft Array Circular',
)

pd_tree_entity_sketch = (
    'PartDesign::Pad',
    'PartDesign::Revolution',
    'PartDesign::AdditiveHelix',
    'PartDesign::Pocket',
    'PartDesign::Hole',
    'PartDesign::Groove',
    'PartDesign::SubtractiveHelix',
)

pd_tree_entity = (
    'PartDesign::AdditiveLoft',
    'PartDesign::AdditivePipe',
    'PartDesign::SubtractiveLoft',
    'PartDesign::SubtractivePipe',
    'PartDesign::Fillet',
    'PartDesign::Chamfer',
    'PartDesign::Draft',
    'PartDesign::Thickness',
)

tools_multiple_selection_ok = (
    'Measure',
    'Fit Selection',
    'Toggle Transparency',
    'Appearance',
    'Random Color',
    'Toggle Visibility',
    'Make Link',
    'Binder',
    'Pad',
    'Additive Loft',
    'Pocket',
    'Fillet',
    'Chamfer',
    'Draft',
    'Thickness',
    'Mirror',
    'Linear Pattern',
    'Polar Pattern',
    'Multi Transform',
    'Make Wall',
    'Extend Face',
    'Create Simple Copy',
)

tools_single_selection_ban = (
    'Measure',
    'Additive Loft',
)

sk_symmetry = (
    'Line|Point',
    'Line|Root',
    'Point|N',
    'Point|Root',
)


# ------------------------------------------------------------------------------

# todo: Revolution, Additive Loft


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
