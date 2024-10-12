# addFC - additional tools for FreeCAD

Current version 0.7.2 - [release notes](CHANGELOG.md).


### Overview

This workbench contains tools that simplify the solution of some tasks in FreeCAD.

At the moment it is:

1. Generate a BOM based on the model.
2. Batch processing of sheet metal parts.
3. Creation of design documentation.
4. Exploded view (creation and visualization) - [preview](https://youtu.be/G9eikdejY6g).
5. Creating a pipeline.
6. Process automation.

### Preview

Bill of materials - BOM:

![Bill of materials - BOM](repo/doc/img/specification_all.png)

Pipeline and pipe fittings:

![Pipeline and pipe fittings](repo/doc/img/pipe_result.png)

Explosion (30 FPS):

![Explosion (30 FPS)](repo/doc/other/explosion.gif)


## Description

### Toolbox

![](repo/doc/img/toolbar.svg)

1. Open last working file
2. Isometry and fit all
3. Run the model control file
4. Bill of materials - BOM
5. Add properties to an object
6. Creating a pipe by points
7. Exploded view
8. Create a drawing based on a template
9. Documentation, help and examples


### Documentation

[Documentation](repo/doc) available in PDF format:

* [English](https://digiroad.tech/share/addFC/documentation_EN.pdf)
* [Russian](https://digiroad.tech/share/addFC/documentation_RU.pdf)

[FreeCAD forum thread](https://forum.freecad.org/viewtopic.php?t=91329)


### Notes

The workbench is under development.

Testing is performed on stable versions of FreeCAD.

__Potential sheet metal issues when working in version 1.0...__

If you encounter problems after the update, try deleting the preferences directory:

`FreeCAD/Mod/addFC/pref`


## Installation

Download the [archive](https://github.com/GS90/addFC/archive/main.zip), unzip it and move the __addFC__ folder to the directory containing all additional FreeCAD modules:

* Linux: `~/.local/share/FreeCAD/Mod`
* MacOS: `~/Library/Preferences/FreeCAD/Mod`
* Windows: `C:\Users\***\AppData\Roaming\FreeCAD\Mod`

Or, while in the directory with modules, use [git](https://git-scm.com):

`git clone https://github.com/GS90/addFC`

To update the module, while in the __addFC__ directory, use:

`git pull -r`


### Dependencies

Requirements:

* FreeCAD >= 0.20
* Python >= 3.10

For full functionality, you need:

* [FreeCAD SheetMetal Workbench](https://github.com/shaise/FreeCAD_SheetMetal)
* Additional Python Modules: [ezdxf](https://pypi.org/project/ezdxf) and [numpy](https://pypi.org/project/numpy)
* [FFmpeg](https://ffmpeg.org)

The easiest way to install is to use the Python package management system - [pip](https://en.wikipedia.org/wiki/Pip_(package_manager)):

* `pip install numpy ezdxf`


## License

[LGPL-2.1-or-later](LICENSE)

[Workbench icons](https://en.wikipedia.org/wiki/Tango_Desktop_Project)
