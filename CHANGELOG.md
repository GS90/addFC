# addFC - additional tools for FreeCAD

## Release notes

#### 2024.05.12 (**0.1.0**):
* Initial release.

#### 2024.05.17 (**0.1.1**):
* Fixed: AddFCProperties - selection.
* Fixed: Explode - animation.

#### 2024.05.22 (**0.2.0**):
* Refactoring.
* Added: Explode - export animation to video file.
* Added: New example - belt roller support assembly.
* A new optional dependency: FFmpeg.

#### 2024.05.25 (**0.3.0**):
* Fixes.
* BOM: Export settings.
* BOM: Export to spreadsheet.
* BOM: Export to CSV.

#### 2024.06.02 (**0.3.1**):
* Fixes.

#### 2024.06.29 (**0.4.2**):
* Minor changes.
* The "Code" property has been renamed to "Index".
* Added: Sheet metal settings: radius, k-factor calculation.
* Added: Sheet metal part settings: color and density.
* HotFix.

#### 2024.07.17 (**0.4.4**):
* Minor changes and fixes.
* Refactoring.
* Documentation on main functions is available in English and Russian.

#### 2024.08.02 (**0.6.1**):
* Updating standard properties (added: Code, Format, Note, Section).
* Preferences: Ability to change FreeCAD font.
* BOM: Automatic indexing of element positions.
* BOM: Updating enumerations properties in objects.
* Unified System for Design Documentation, USDD - Russia:
    + BOM: Possibility of export according to standard.
    + New function: Create a drawing based on a template.
    + Automatic filling of the template stamp.
    + Additional files added: [templates and font](/repo/add/stdRU)
    + Added a special example of work and design: stdRU.
* Updating documentation and fixes.
* Fixes.

#### 2024.08.04 (**0.6.3**):
* Fixes: explode, pipe, templates.
* Readme update.

#### 2024.08.25 (**0.7.0**):
* Documentation completed.
* Template updates (USDD - Russia).
* Various fixes and updates.

#### 2024.10.13 (**0.7.3**):
* Additions: processing and display in preferences.
* Changes to the preferences interface.
* Fixes: unfold and metal thickness.
* Improvement: OpenRecentFile.

#### 2024.10.19 (**0.7.4**):
* Fix unfold and auto indexing.

#### 2024.10.28 (**0.7.5**):
* Fixes: unfold and BOM.

#### 2025.01.04 (**1.0.6**):
* The name for the property group is now standard and unchangeable: __Add__.
* The properties __Weight__ and __Price__ have been moved to the basic group.
* Added basic property __Node__ to separate bill of materials.
* Added materials for automatic calculation of mass and cost of objects.
* The value of some properties can be edited in the graphical interface.
* Increased stability in batch processing of sheet metal parts.
* Added experimental version of the component library.
* The workbench contains an internal library.
* __SheetMetal Workbench__ has been removed from required dependencies.
* Many other changes, fixes and improvements.
* Backward compatibility may be broken...
