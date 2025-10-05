# -*- coding: utf-8 -*-
# Copyright 2025 Golodnikov Sergey


from PySide import QtGui, QtCore, QtWidgets
from zipfile import ZipFile
import freecad.Additional_Tools.Logger as Logger
import freecad.Additional_Tools.Other as Other
import freecad.Additional_Tools.Preference as P
import FreeCAD
import FreeCADGui as Gui
import json
import os
import Part
import shutil
import subprocess
import sys


VERSION = 4


DIR = os.path.join(P.AFC_PATH, 'repo', 'add', 'Library')
ZIP = os.path.join(P.AFC_PATH, 'repo', 'add', 'Library.zip')


if not os.path.exists(DIR):
    z = ZipFile(ZIP, 'r')
    z.extractall(os.path.join(P.AFC_PATH, 'repo', 'add'))
    z.close()


ui = os.path.join(os.path.dirname(__file__), 'Library.ui')
ls = os.path.join(os.path.dirname(__file__), 'Library_set.ui')


library_title = ''
library_path = ''
library_cache = ''
library_thumbnails = ''

freeze = False


def set_library_location(title: str, path=''):
    title = 'DIN' if title == '' else title
    match title:
        case 'DIN' | 'ISO' | 'ГОСТ': standard = True
        case _: standard = False
    global library_title
    global library_path
    global library_cache
    global library_thumbnails
    library_title = title
    if standard:
        library_path = os.path.join(
            P.AFC_PATH, 'repo', 'add', 'Library', title)
        library_cache = os.path.join(library_path, f'{title}_library.json')
        library_thumbnails = os.path.join(DIR, 'thumbnails')
    else:
        library_path = path if path != '' else library_list.get(title, '')
        if library_path == '':
            Logger.error(f"'{title}' unknown library...")
            return
        library_cache = os.path.join(library_path, f'{title}_library.json')
        library_thumbnails = os.path.join(library_path, 'thumbnails')
    if not os.path.exists(library_path):
        Logger.error(f"'{title}' library not found...")


configuration = P.pref_configuration

debug = configuration['library']['debug']
panel = configuration['library']['panel']
parameters_set = configuration['library']['parameters'],

library_list = configuration['library_list']
library_recent = configuration['library']['recent']


set_library_location(library_recent)


AVAILABLE_THUMBNAILS = ('.png', '.jpg', '.jpeg')

AVAILABLE_TYPES = (
    'App::Part',
    'Part::Feature',
    'Part::FeaturePython',
    'PartDesign::Body',
)

VARIATIONS = ('Link', 'Simple', 'Copy')

LCOC_VALUES = ('Disabled', 'Enabled', 'Owned', 'Tracking')

SELECT = 'Select a library ...'

SEPARATOR = '\t'


ad = FreeCAD.activeDocument()


# ------------------------------------------------------------------------------


def library_upgrade() -> None:
    shutil.rmtree(DIR, ignore_errors=True)
    z = ZipFile(ZIP, 'r')
    z.extractall(os.path.join(P.AFC_PATH, 'repo', 'add'))
    z.close()


def logger(msg: str) -> None:
    if debug:
        Logger.log('Library ' + msg)


def grouping(expression_engine: list) -> list:
    conf = []
    if len(expression_engine) == 0:
        return conf
    for e in expression_engine:
        if len(e) < 2:
            continue
        # todo: VarSet
        if '.Enum' in e[0] and 'Spreadsheet' in e[1]:
            conf.append(str(e[0][1:].replace('.Enum', '')))
    return conf


def dissection(dp: str, close: bool) -> dict:
    structure = {}
    doc = FreeCAD.openDocument(dp, True)
    FreeCAD.setActiveDocument(ad.Name)
    for t in AVAILABLE_TYPES:
        for o in doc.findObjects(t):
            if 'Add_Name' not in o.PropertiesList:
                continue
            group = {}
            for g in grouping(o.ExpressionEngine):
                if g != '' and g in o.PropertiesList:
                    group[g] = o.getEnumerationsOfProperty(g)
            structure[o.Label] = group
    if close:
        FreeCAD.closeDocument(doc.Name)
    return structure


class widget():
    library = {}
    info = {}
    target = []
    cache_search = {}
    cache_conf = {}
    cache_objects = []
    thumbnails = {}

    def __init__(self):
        self.form = Gui.PySideUic.loadUi(ui)
        if not panel:
            self.form.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.form.show()
            self.form.search.setFocus()

        self.form.choice.addItems(library_list.keys())
        self.form.choice.addItem(SELECT)
        self.form.choice.setCurrentText(library_title)

        self.form.variation.addItems(VARIATIONS)
        self.form.lcoc.addItems(LCOC_VALUES)

        def variance(var) -> None:
            self.form.lcoc.setEnabled(True if var == 'Link' else False)

        self.form.variation.setCurrentText(
            configuration['library']['variation'])
        self.form.lcoc.setCurrentText(
            configuration['library']['lcoc'])

        variance(configuration['library']['variation'])

        self.form.refreshLibrary.clicked.connect(self.refresh)
        self.refresh()

        keys = list(self.library.keys())
        if len(keys) == 0:
            keys.append('The library is empty')

        # files:

        def fileLibrary(catalog) -> None:
            self.form.fileLibrary.clear()
            self.form.group.clear()
            self.form.configuration.clear()
            self.form.group.setEnabled(False)
            self.form.configuration.setEnabled(False)
            if catalog in self.library:
                self.form.fileLibrary.addItems(self.library[catalog].keys())

        self.form.catalogLibrary.currentTextChanged.connect(fileLibrary)
        fileLibrary(keys[0])

        # objects:

        model = QtGui.QStandardItemModel()

        def objects() -> None:
            self.target.clear()
            self.form.add.setEnabled(False)

            self.form.group.clear()
            self.form.configuration.clear()
            self.form.group.setEnabled(False)
            self.form.configuration.setEnabled(False)

            model.clear()
            self.form.objects.setModel(model)

            catalog = self.form.catalogLibrary.currentText()
            file = self.form.fileLibrary.currentText()

            if catalog not in self.library:
                return
            if file not in self.library[catalog]:
                return

            if 'objects' in self.library[catalog][file]:
                for obj in self.library[catalog][file]['objects']:
                    i = QtGui.QStandardItem(obj)
                    t = self.thumbnails.get(obj)
                    if t is not None:
                        i.setToolTip(f'<img src="{t}">')
                    model.appendRow(i)

        self.form.fileLibrary.currentTextChanged.connect(objects)
        objects()

        # configurations:

        def conf(item) -> None:
            self.target.clear()
            self.form.add.setEnabled(False)

            self.form.group.clear()
            self.form.configuration.clear()
            self.form.group.setEnabled(False)
            self.form.configuration.setEnabled(False)

            conf_search = self.form.searchInConf.isChecked()

            object = model.index(item.row(), item.column()).data()

            if not conf_search:
                conf = ''
            else:
                sp = object.split(SEPARATOR)
                if len(sp) == 2:
                    conf, object = sp[0], sp[1]
                else:
                    conf = ''  # todo: error?

            catalog, file = None, None
            for i in self.cache_objects:
                if object == i[0]:
                    catalog, file = i[2], i[1]
            if catalog is None or file is None:
                return

            self.cache_conf = self.library[catalog][file]['objects'][object]
            self.target = [catalog, file, object]

            self.form.add.setEnabled(True)

            groups = list(self.cache_conf.keys())
            if len(groups) == 0:
                return
            obj_configurations = self.cache_conf[groups[0]]

            self.form.group.addItems(groups)

            if len(groups) > 1:
                self.form.group.setEnabled(True)
            if len(obj_configurations) > 0:
                self.form.configuration.setEnabled(True)
            if conf != '':
                self.form.configuration.setEnabled(False)
                self.form.configuration.setCurrentText(conf)

        self.form.objects.clicked.connect(conf)

        # grouping:

        def grouping(group) -> None:
            self.form.configuration.clear()
            self.form.configuration.setEnabled(False)
            if group in self.cache_conf:
                self.form.configuration.addItems(self.cache_conf[group])
                self.form.configuration.setEnabled(True)

        self.form.group.currentTextChanged.connect(grouping)

        # object search:

        def search(s) -> None:
            # todo: dictionary search faster...
            model.clear()
            if s == '':
                objects()
            else:
                if not self.form.searchInConf.isChecked():
                    # standard search:
                    for i in self.cache_objects:
                        if s.lower() in i[0].lower():
                            model.appendRow(QtGui.QStandardItem(i[0]))
                else:
                    # search in configurations:
                    for i in self.cache_search:
                        if s.lower() in i.lower():
                            for j in self.cache_search[i]:
                                model.appendRow(QtGui.QStandardItem(
                                    i + SEPARATOR + j[2]))

        self.form.search.textEdited.connect(search)

        # variations:

        self.form.variation.currentTextChanged.connect(variance)

        # change library root directory:

        def choice_update():
            global freeze
            freeze = True
            self.form.choice.clear()
            self.form.choice.addItems(library_list.keys())
            self.form.choice.addItem(SELECT)
            self.form.choice.setCurrentText(library_title)
            freeze = False

        def change(target) -> None:
            global freeze
            if freeze or target == library_title:
                return
            if target == SELECT:
                d = os.path.normcase(QtGui.QFileDialog.getExistingDirectory())
                if d == '':
                    return
                path = d
            else:
                path = ''

            self.clear()

            if path == '':
                # library from the list:
                set_library_location(target)
            else:
                # new library:
                title = os.path.basename(path)
                set_library_location(title, path)
                global library_list
                library_list[title] = path

            # saving the configuration:
            global configuration
            configuration['library']['recent'] = library_title
            configuration['library_list'] = library_list
            P.save_pref(P.PATH_CONFIGURATION, configuration)

            self.refresh()
            choice_update()

        self.form.choice.currentTextChanged.connect(change)

        # open library root directory:

        def open_library() -> None:
            match sys.platform:
                case 'win32': subprocess.run(['explorer', library_path])
                case 'darwin': subprocess.run(['open', library_path])
                case _: subprocess.run(['xdg-open', library_path])

        self.form.openLibrary.clicked.connect(open_library)

        # add or replace object:

        def integration(replace: bool) -> None:
            catalog, file, label = self.target
            file += '.FCStd'

            bn = os.path.basename(library_path)
            if catalog == bn:
                dp = os.path.join(library_path, file)
            else:
                dp = os.path.join(library_path, catalog, file)

            placement, root, placement_eq, replacement = extra(replace)

            if (replace and not replacement):
                Logger.warning('the object cannot be replaced...')
                return

            add_object(
                dp,
                label,
                self.form.group.currentText(),
                self.form.configuration.currentText(),
                self.form.variation.currentText(),
                self.form.lcoc.currentText(),
                placement,
                root,
                placement_eq,
            )

        def add() -> None:
            integration(False)

        def replace() -> None:
            # the button is always active...
            if len(FreeCAD.Gui.Selection.getSelection()) > 0:
                try:
                    integration(True)
                except BaseException:
                    pass

        self.form.add.clicked.connect(add)
        self.form.replace.clicked.connect(replace)

        # preferences:

        def preferences() -> None:
            pref = {
                'debug': configuration['library']['debug'],
                'panel': configuration['library']['panel'],
                'parameters': configuration['library']['parameters'],
            }

            u = FreeCAD.Gui.PySideUic.loadUi(ls)

            u.debug.setChecked(pref['debug'])
            u.panel.setChecked(pref['panel'])
            u.parameters.setChecked(pref['parameters'])

            # information about the library:

            u.name.setText(library_title)
            u.catalogs.setText(f"Catalogs - {self.info['catalogs']}")
            u.files.setText(f"Files - {self.info['files']}")
            u.objects.setText(f"Objects - {self.info['objects']}")

            # standard library:
            update = False
            try:
                f = open(os.path.join(DIR, 'Version'), 'r')
                s = f.readline().strip('\n')
                f.close()
                v = int(s)
                if v < VERSION:
                    update = True
                elif v > VERSION:
                    v = 'error'
                    update = True
            except BaseException:
                v = 'error'
                update = True

            u.workbench.setText(f'Workbench version - {VERSION}')
            u.local.setText(f'Local version - {v}')

            if v == 'error' or update:
                u.local.setStyleSheet('color: #960000')

            u.refresh.setEnabled(update)

            def library_upgrade_wrapper() -> None:
                library_upgrade()
                u.local.setText(f'Local version - {VERSION}')
                u.local.setStyleSheet('')
                u.restart.setText(
                    'Update complete, library needs to be restarted')
                u.refresh.setEnabled(False)

            u.refresh.clicked.connect(library_upgrade_wrapper)

            # u.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            u.show()

            def apply() -> None:
                pref['debug'] = u.debug.isChecked()
                pref['panel'] = u.panel.isChecked()
                pref['parameters'] = u.parameters.isChecked()
                global debug
                debug = pref['debug']
                global parameters_set
                parameters_set = pref['parameters']
                global configuration
                configuration['library'].update(pref)
                P.save_pref(P.PATH_CONFIGURATION, configuration)
                u.close()

            u.apply.clicked.connect(apply)

        self.form.preferences.clicked.connect(preferences)

    # save and restore library:

    def storage(self) -> None:
        if len(self.library) != 0:
            file = open(library_cache, 'w+', encoding='utf-8')
            json.dump(self.library, file, ensure_ascii=False)
            file.close()

    def recovery(self):
        if os.path.exists(library_cache):
            try:
                file = open(library_cache, 'r', encoding='utf-8')
                self.library = json.load(file)
                file.close()
            except BaseException as e:
                Logger.error(str(e))

    # library update:

    def refresh(self):
        self.clear()
        self.recovery()

        # update:

        ld = tuple(FreeCAD.listDocuments().keys())

        fresh = {'catalogs': [], 'files': []}

        for address, _, files in os.walk(library_path):
            catalog = os.path.basename(address)
            fresh['catalogs'].append(catalog)

            if catalog not in self.library:
                new_catalog = True
                self.library[catalog] = {}
            else:
                new_catalog = False

            for f in files:
                fn, fe = os.path.splitext(f)
                if fe != '.FCStd':
                    continue

                fresh['files'].append(fn)

                dp = os.path.join(address, f)
                t = os.path.getmtime(dp)

                if fn in self.library[catalog]:
                    if t == self.library[catalog][fn]['timestamp']:
                        continue
                    else:
                        _ = self.library[catalog].pop(fn, None)
                        logger('[file] update: ' + fn)
                else:
                    logger('[file] add: ' + fn)

                objects = dissection(dp, False if fn in ld else True)

                self.library[catalog][fn] = {
                    'timestamp': t,
                    'objects': objects
                }

            if len(self.library[catalog]) == 0:
                _ = self.library.pop(catalog, None)
                fresh['catalogs'].remove(catalog)
            elif new_catalog:
                logger('[catalog] add: ' + catalog)

        # check:

        bn = os.path.basename(library_path)
        for catalog in list(self.library.keys()):
            if bn != catalog:
                if catalog not in fresh['catalogs']:
                    _ = self.library.pop(catalog, None)
                    logger('[catalog] deleted: ' + catalog)
            for f in list(self.library[catalog].keys()):
                if f not in fresh['files']:
                    _ = self.library[catalog].pop(f, None)
                    logger('[file] deleted: ' + f)

        # updating cache and structure information:

        files, objects = 0, 0
        for catalog in self.library:
            for file in self.library[catalog]:
                files += 1
                if 'objects' in self.library[catalog][file]:
                    for obj in self.library[catalog][file]['objects']:
                        objects += 1
                        self.cache_objects.append((obj, file, catalog))
                        # to search in configurations:
                        value = self.library[catalog][file]['objects'][obj]
                        if 'Conf' in value:
                            for conf in value['Conf']:
                                i = [catalog, file, obj]
                                if conf in self.cache_search:
                                    self.cache_search[conf].append(i)
                                else:
                                    self.cache_search[conf] = [i,]

        self.info['catalogs'] = len(list(self.library.keys()))
        self.info['files'] = files
        self.info['objects'] = objects

        # thumbnails:

        self.thumbnails.clear()
        if os.path.exists(library_thumbnails):
            for i in os.listdir(library_thumbnails):
                fn, fe = os.path.splitext(i)
                if fe in AVAILABLE_THUMBNAILS:
                    self.thumbnails[fn] = os.path.join(library_thumbnails, i)

        # init and save:

        keys = list(self.library.keys())
        if len(keys) == 0:
            keys.append('The library is empty')
            self.form.catalogLibrary.setEnabled(False)
            self.form.fileLibrary.setEnabled(False)
        else:
            self.form.catalogLibrary.setEnabled(True)
            self.form.fileLibrary.setEnabled(True)
        self.form.catalogLibrary.addItems(keys)
        self.form.catalogLibrary.setCurrentText(keys[0])

        self.storage()

    # other:

    def clear(self) -> None:
        self.library.clear()
        self.cache_search.clear()
        self.cache_conf.clear()
        self.cache_objects.clear()
        self.form.catalogLibrary.clear()
        self.form.fileLibrary.clear()
        self.form.group.clear()
        self.form.configuration.clear()

    def accept(self):
        global configuration
        configuration['library'].update({
            'lcoc': self.form.lcoc.currentText(),
            'recent': library_title,
            'sic': self.form.searchInConf.isChecked(),
            'variation': self.form.variation.currentText(),
        })
        P.save_pref(P.PATH_CONFIGURATION, configuration)
        Gui.Control.closeDialog()


# ------------------------------------------------------------------------------


def add_object(dp: str,
               label: str,
               group: str,
               conf: str,
               var: str,
               lcoc: str,
               placement: FreeCAD.Placement,
               root: str,
               placement_eq: None | list) -> None:

    ld = FreeCAD.listDocuments()

    doc = FreeCAD.openDocument(dp, True)
    FreeCAD.setActiveDocument(ad.Name)

    opened = True if doc.Name in ld else False

    try:
        src = doc.getObjectsByLabel(label)[0]
    except BaseException as e:
        Logger.error(str(e))
        return

    if var != 'Link':
        if conf != '' and group != '' and group in src.PropertiesList:
            setattr(src, group, conf)  # apply configuration
            doc.recompute()
    else:
        if not ad.isSaved():
            Other.error('Owner document not saved', 'Create link failed')
            return

    match var:
        case 'Link':
            dst = ad.addObject('App::Link', 'Link')
            dst.setLink(src)
            dst.LinkCopyOnChange = lcoc
            if conf != '' and group != '' and group in src.PropertiesList:
                setattr(dst, group, conf)  # apply configuration
            if parameters_set:
                properties = parameters(src)
                if properties is not None:
                    for p in properties:
                        setattr(dst, 'Library_' + p, properties[p][1])
            ad.recompute()
            dst.Placement = placement
            rename(src, dst)

        case 'Simple':
            if parameters_set:
                properties = parameters(src)
                if properties is not None:
                    for p in properties:
                        setattr(src, 'Library_' + p, properties[p][1])
                        src.recompute(True)
            shape = Part.getShape(src, '', needSubElement=False, refine=False)
            dst = ad.addObject('Part::Feature', 'Feature')
            dst.Shape = shape
            dst.Placement = placement
            rename(src, dst)
            try:
                dst.ViewObject.ShapeColor = src.ViewObject.ShapeColor
                dst.ViewObject.LineColor = src.ViewObject.LineColor
                dst.ViewObject.PointColor = src.ViewObject.PointColor
            except BaseException:
                pass
            for p in src.PropertiesList:
                if 'Add_' in p:
                    dst.addProperty(src.getTypeIdOfProperty(p), p, 'Add')
                    dst.restorePropertyContent(p, src.dumpPropertyContent(p))
            if not opened:
                FreeCAD.closeDocument(doc.Name)

        case 'Copy':
            dst = ad.copyObject(src, True, True)
            dst[-1].Placement = placement
            rename(src, dst[-1])
            if parameters_set:
                properties = parameters(src)
                if properties is not None:
                    for p in properties:
                        setattr(dst[-1], 'Library_' + p, properties[p][1])
            if not opened:
                FreeCAD.closeDocument(doc.Name)

        case _:
            return  # todo: error?

    if root != '':
        ad.getObject(root).addObject(dst)

    if placement_eq is not None:
        dst.setExpression(placement_eq[0], placement_eq[1])

    ad.recompute()

    # required for correct recalculation of configuration tables:
    if P.FC_VERSION[1] == '21':
        try:
            Other.recompute_configuration_tables()
        except BaseException:
            pass


# ------------------------------------------------------------------------------


def parameters(src) -> dict | None:
    properties = {}
    for p in src.PropertiesList:
        if p.startswith('Library_'):
            properties[p[len('Library_'):]] = [
                src.getTypeIdOfProperty(p), src.getPropertyByName(p)]
    if len(properties) == 0:
        return None
    dialog = Dialog(properties)
    dialog.exec_()
    values = dialog.values
    for p in properties:
        if p in values:
            match properties[p][0]:
                case 'App::PropertyInteger' | 'App::PropertyFloat':
                    properties[p][1] = values[p].value()
                case _:
                    properties[p][1] = values[p].text()
    if len(properties) == 0:
        return None
    return properties


class Dialog(QtWidgets.QDialog):
    def __init__(self, properties):
        super(Dialog, self).__init__()

        self.values = {}

        self.setWindowTitle('Parameters')
        layout_v = QtWidgets.QVBoxLayout()

        for p in properties:
            layout_h = QtWidgets.QHBoxLayout()
            self.label = QtWidgets.QLabel(self)
            self.label.setText(p)
            layout_h.addWidget(self.label)
            match properties[p][0]:
                case 'App::PropertyInteger':
                    self.input = QtWidgets.QSpinBox(self)
                    self.input.setMinimum(2)
                    self.input.setMaximum(300)
                    self.input.setValue(int(properties[p][1]))
                case 'App::PropertyFloat':
                    self.input = QtWidgets.QDoubleSpinBox(self)
                    self.input.setMinimum(2)
                    self.input.setMaximum(300)
                    self.input.setValue(float(properties[p][1]))
                case _:
                    self.input = QtWidgets.QLineEdit(self)
                    self.input.setText(str(properties[p][1]))
            layout_h.addWidget(self.input)
            layout_v.addLayout(layout_h)
            self.values[p] = self.input

        layout_h = QtWidgets.QHBoxLayout()
        layout_h.addItem(QtGui.QSpacerItem(
            40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))

        self.button = QtWidgets.QPushButton('Apply', self)
        self.button.clicked.connect(self.submit)
        layout_h.addWidget(self.button)
        layout_v.addLayout(layout_h)
        self.setLayout(layout_v)

    def submit(self):
        self.accept()


# ------------------------------------------------------------------------------


def rename(src, dst) -> None:
    if 'Add_Name' in src.PropertiesList:
        dst.Label = src.getPropertyByName('Add_Name') + ' 001'
    else:
        dst.Label = src.Label + ' 001'


def extra(replace: bool):

    placement = FreeCAD.Placement()
    root = ''
    placement_eq = None
    replacement = False

    objects = ad.findObjects('App::Part')
    if len(objects) > 0:
        obj = objects[0]
        match obj.TypeId:
            case 'App::Part' | 'Assembly::AssemblyObject': root = obj.Name

    vector, obj = FreeCAD.Vector(), None

    selection = FreeCAD.Gui.Selection.getSelectionEx('', 0)

    try:
        if len(selection) == 0:
            return placement, root, placement_eq, replacement
        selection = selection[0]
        if selection.HasSubObjects:
            vector += selection.SubObjects[0].BoundBox.Center
        placement.Base += vector

        try:
            sen = selection.SubElementNames[0]
            sol = selection.Object.getSubObjectList(sen)
            # anchor to point placement:
            if not replace:
                s = sol[-1]
                if s.TypeId == 'PartDesign::Point':
                    placement_eq = [
                        '.Placement.Base',
                        f'{s.Name}.Placement.Base',
                    ]
                    if len(sol) > 1:
                        s = sol[-2]
                        if s.TypeId == 'PartDesign::Body':
                            placement_eq[1] += f' + {s.Name}.Placement.Base'
            # substitution and addition:
            sol.reverse()
            for s in sol:
                match s.TypeId:
                    case 'App::Link' | 'Part::Feature':
                        obj = s
                        break
            for s in sol:
                match s.TypeId:
                    case 'App::Part' | 'Assembly::AssemblyObject':
                        root = s.Name
                        break
        except BaseException as exception:
            Logger.warning(str(exception))
            return placement, root, placement_eq, replacement

    except BaseException as exception:
        Logger.warning(str(exception))
        placement.Base += selection.PickedPoints[0]

    if (replace and obj is not None):
        placement = obj.Placement
        match obj.TypeId:
            case 'App::Link':
                lo = obj.getLinkedObject()
                if 'Add_Name' in lo.PropertiesList:
                    ad.removeObject(obj.Name)
                    replacement = True
            case 'Part::Feature':
                if 'Add_Name' in obj.PropertiesList:
                    ad.removeObject(obj.Name)
                    replacement = True
        ad.recompute()

    return placement, root, placement_eq, replacement


# ------------------------------------------------------------------------------


if panel:
    w = widget()
    Gui.Control.showDialog(w)
    w.form.search.setFocus()
else:
    widget()
