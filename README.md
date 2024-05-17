# addFC - additional tools for FreeCAD

Current version 0.1.2



### Overview

This workbench contains tools that simplify the solution of some tasks in FreeCAD.

At the moment it is:

1. Bill of materials (BOM).
2. Batch processing of sheet metal parts.
3. Exploded view (creation and visualization).
4. Creating a pipeline.


## Description

### Toolbox

![](repo/doc/icon.png)

1. Open recent file
2. Isometry and fit all
3. Run the model control file
4. Bill of materials (BOM)
5. Add properties to an object
6. Creating a pipe by points
7. Exploded view
8. Open an example

Documentation: [english](documentation_EN.md), [russian](documentation_RU.md).

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

The easiest way to install is to use the Python package management system - [pip](https://en.wikipedia.org/wiki/Pip_(package_manager)):

* `pip install ezdxf`
* `pip install numpy`


## License

[LGPL-2.1-or-later](LICENSE)

[Workbench icons](https://en.wikipedia.org/wiki/Tango_Desktop_Project)
