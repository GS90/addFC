# addFC - additional tools for FreeCAD

Current version 1.0.0 beta - [release notes](CHANGELOG.md).


### Overview

This workbench contains tools that simplify the solution of some tasks in FreeCAD.

At the moment it is:

1. Generate a BOM based on the model.
2. Batch processing of sheet metal parts.
3. Library of elements and nodes - [standard](repo/add/Library.md).
4. Assistance in creating design documentation.
5. Exploded view (creation and visualization) - [preview](https://youtu.be/G9eikdejY6g).
6. Creating a pipeline.
7. Process automation.

### Preview

Bill of materials - BOM

![Bill of materials - BOM](repo/doc/img/specification_all.png)

Library of elements and nodes - beta

![Library](repo/doc/img/library.png)

Pipeline and pipe fittings

![Pipeline and pipe fittings](repo/doc/img/pipe_result.png)

Explosion (30 FPS)

![Explosion (30 FPS)](repo/doc/other/explosion.gif)


## Description

### Toolbox

![](repo/doc/img/toolbar.svg)

1. Open last working file
2. Isometry and fit all
3. Run the model control file
4. Bill of materials - BOM
5. Add properties to an object
6. Create a drawing based on a template
7. Library of elements and nodes
8. Exploded view
9. Creating a pipe by points
10. Documentation, help and examples


### Documentation

[Documentation](repo/doc) available in PDF format:

* [English](https://digiroad.tech/share/addFC/documentation_EN.pdf)
* [Russian](https://digiroad.tech/share/addFC/documentation_RU.pdf)

[FreeCAD forum thread](https://forum.freecad.org/viewtopic.php?t=91329)

[FreeCAD форум на русском языке](https://forum.freecad.org/viewtopic.php?t=91598)


### Notes

The workbench is under development.

Testing is performed on stable versions (0.20 and 0.21) of FreeCAD.

__Potential sheet metal issues when working in version 1.0...__

If you encounter problems after the update, try deleting the preferences directory:

`FreeCAD/Mod/addFC/pref`


## Installation

### Addon Manager

This workbench is available through the FreeCAD [Addon Manager](https://github.com/FreeCAD/FreeCAD-addons/#1-builtin-addon-manager) (menu __Tools__ > __Addon Manager__). It is called __addFC Workbench__ in the Addon Repository.

<details>
<summary><b>Manual Installation (Click to expand)</b></summary>

### Manual installation

Download the [archive](https://github.com/GS90/addFC/archive/main.zip), unzip it and move the __addFC__ folder to the directory containing all additional FreeCAD modules:

* Linux: `~/.local/share/FreeCAD/Mod`
* MacOS: `~/Library/Preferences/FreeCAD/Mod`
* Windows: `C:\Users\***\AppData\Roaming\FreeCAD\Mod`

Or, while in the directory with modules, use [git](https://git-scm.com):

`git clone https://github.com/GS90/addFC`

To update the module, while in the __addFC__ directory, use:

`git pull -r`

</details>

### Dependencies

Requirements:

* FreeCAD >= 0.20
* Python >= 3.10

For full functionality, you need:

* [FreeCAD SheetMetal Workbench](https://github.com/shaise/FreeCAD_SheetMetal)
* Additional Python Modules: [ezdxf](https://pypi.org/project/ezdxf) and [numpy](https://pypi.org/project/numpy)
* [FFmpeg](https://ffmpeg.org)

When installing the workbench using __Addon Manager__, all dependencies (except FFmpeg) will be installed automatically.

To install additional Python modules manually, the easiest way is to use [pip](https://en.wikipedia.org/wiki/Pip_(package_manager)):

* `pip install numpy ezdxf`


## License

[LGPL-2.1-or-later](LICENSE)

[Workbench icons](https://en.wikipedia.org/wiki/Tango_Desktop_Project)
