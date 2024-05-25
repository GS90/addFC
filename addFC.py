# -*- coding: utf-8 -*-
# Copyright 2024 Golodnikov Sergey


from PySide import QtGui, QtCore
from zipfile import ZipFile
import addFC_Preference as P
import addFC_Specification as S
import addFC_Unfold
import FreeCAD
import importlib.machinery
import os


exporting: dict = {
    'JSON': ['JSON (*.json)'],
    'CSV': ['CSV (*.csv)'],
    'Spreadsheet': [],
}

unfold_name: tuple = ('Code', 'Name')
unfold_signature: tuple = ('None', 'Code', 'Prefix', 'Prefix + Code')

unfold_index: int = 0
name_index: int = 0


def error(message: str) -> None:
    QtGui.QMessageBox.critical(
        None,
        'ERROR',
        message,
        QtGui.QMessageBox.StandardButton.Ok,
    )


# ------------------------------------------------------------------------------


class AddFCOpenRecentFile():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.add_icon, 'resent.svg'),
                'Accel': 'Alt+Shift+R',
                'MenuText': 'Recent File',
                'ToolTip': 'Open recent file'}

    def Activated(self):
        p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/RecentFiles")
        f = p.GetString('MRU0')
        e = 'The file cannot be opened...\n'

        if f == '':
            FreeCAD.Console.PrintError(e)
            return
        elif not os.path.exists(f):
            FreeCAD.Console.PrintError(e)
            return
        elif not os.path.isfile(f):
            FreeCAD.Console.PrintError(e)
            return

        FreeCAD.openDocument(f)
        FreeCAD.Gui.activeDocument().activeView().viewIsometric()
        FreeCAD.Gui.SendMsgToActiveView('ViewFit')
        return

    def IsActive(self): return True


FreeCAD.Gui.addCommand('AddFCOpenRecentFile', AddFCOpenRecentFile())


class AddFCDisplay():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.add_icon, 'display.svg'),
                'Accel': 'Alt+Shift+D',
                'MenuText': 'Display',
                'ToolTip': 'Isometry and fit all'}

    def Activated(self):
        try:
            FreeCAD.Gui.activeDocument().activeView().viewIsometric()
        except BaseException:
            pass
        FreeCAD.Gui.SendMsgToActiveView('ViewFit')
        return

    def IsActive(self): return True if FreeCAD.ActiveDocument else False


FreeCAD.Gui.addCommand('AddFCDisplay', AddFCDisplay())


# ------------------------------------------------------------------------------


class AddFCModelControl():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.add_icon, 'control.svg'),
                'Accel': 'Alt+Shift+C',
                'MenuText': 'Model Control',
                'ToolTip': 'Run the model control file'}

    def Activated(self):
        file = str(FreeCAD.ActiveDocument.getFileName())
        file = file.replace('.FCStd', '.py')
        if not os.path.isfile(file):
            error('The model control file was not found.')
            return
        loader = importlib.machinery.SourceFileLoader('control', file)
        _ = loader.load_module()
        return

    def IsActive(self): return True if FreeCAD.ActiveDocument else False


FreeCAD.Gui.addCommand('AddFCModelControl', AddFCModelControl())


# ------------------------------------------------------------------------------


class AddFCSpecification():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.add_icon, 'specification.svg'),
                'Accel': 'Alt+Shift+S',
                'MenuText': 'Specification',
                'ToolTip': 'Model Specification'}

    def Activated(self):
        ui = os.path.join(P.add_base, 'repo', 'ui', 'specification.ui')
        w = FreeCAD.Gui.PySideUic.loadUi(ui)

        conf = P.load_configuration()

        if conf['working_directory'] == '':
            conf['working_directory'] = os.path.expanduser('~/Desktop')
        if conf['unfold_prefix'] != '':
            w.lineEditPrefix.setText(conf['unfold_prefix'])
        w.labelTarget.setText(
            f"... {os.path.basename(conf['working_directory'])}")

        w.comboBoxExport.addItems(exporting.keys())
        w.comboBoxExport.setCurrentText(conf['spec_export_type'])
        w.comboBoxName.addItems(unfold_name)
        w.comboBoxSignature.addItems(unfold_signature)

        table = w.specificationTable
        table_details = w.detailsTable

        color_red = QtGui.QBrush(QtGui.QColor(150, 0, 0))
        color_blue = QtGui.QBrush(QtGui.QColor(0, 0, 150))

        forbidden = ('Unit', 'Body')

        def specification_update(startup=False) -> None:
            specification_purge(startup)

            strict = True if w.checkBoxStrict.isChecked() else False
            info, info_h, details, details_h = S.get_specification(strict)

            if len(info) == 0:
                return

            for i in info:
                if info[i]['Unit'] != '-':
                    value = f"{info[i]['Quantity']} {info[i]['Unit']}"
                    info[i]['Quantity'] = value

            for i in forbidden:
                if i in info_h:
                    del info_h[i]
                if i in details_h:
                    del details_h[i]
            if 'Unfold' in info_h:
                del info_h['Unfold']

            #################
            # specification #
            #################

            labels = list(info_h.keys())

            table.setColumnCount(len(info_h))
            table.setRowCount(len(info))
            table.setHorizontalHeaderLabels(labels)
            table.horizontalHeader().setResizeMode(
                labels.index('Name'), QtGui.QHeaderView.Stretch)

            q = QtGui.QTableWidgetItem
            x = 0
            for i in info:
                for j in info[i]:
                    if j in forbidden or j == 'Unfold':
                        continue
                    table.setItem(x, labels.index(j), q(str(info[i][j])))
                x += 1

            labels.clear()
            for i in info_h:
                value = info_h[i]
                if value > 0:
                    labels.append(f'{i}\n{value}')
                else:
                    labels.append(i)
            table.setHorizontalHeaderLabels(labels)

            table.resizeColumnsToContents()
            table.resizeRowsToContents()
            table.horizontalHeader().setResizeMode(
                labels.index('Name'), QtGui.QHeaderView.Stretch)

            table.sortItems(labels.index('Name'))
            table.setSortingEnabled(True)
            table.horizontalHeader().setSortIndicatorShown(False)

            ###########
            # details #
            ###########

            if len(details) == 0:
                w.pushButtonExit.setFocus()
                return

            labels = list(details_h.keys())
            global unfold_index
            unfold_index = labels.index('Unfold')
            global name_index
            name_index = labels.index('Name')

            table_details.setColumnCount(len(details_h))
            table_details.setRowCount(len(details))
            table_details.setHorizontalHeaderLabels(labels)
            table_details.horizontalHeader().setResizeMode(
                labels.index('Name'), QtGui.QHeaderView.Stretch)

            x = 0
            for i in details:
                for j in details[i]:
                    if j in forbidden:
                        continue
                    v = str(details[i][j])
                    q = QtGui.QTableWidgetItem(v)
                    if j == 'Unfold':
                        match v:
                            case 'True': q.setForeground(color_blue)
                            case 'False': q.setForeground(color_red)
                    if j == 'MetalThickness':
                        if v == '-':
                            q.setForeground(color_red)
                    table_details.setItem(x, labels.index(j), q)
                x += 1

            labels.clear()
            for i in details_h:
                value = details_h[i]
                if value > 0:
                    labels.append(f'{i}\n{value}')
                else:
                    labels.append(i)
            table_details.setHorizontalHeaderLabels(labels)

            table_details.resizeColumnsToContents()
            table_details.resizeRowsToContents()
            table_details.horizontalHeader().setResizeMode(
                labels.index('Name'), QtGui.QHeaderView.Stretch)

            table_details.sortItems(labels.index('Name'))
            table_details.setSortingEnabled(True)
            table_details.horizontalHeader().setSortIndicatorShown(False)

            if not startup:
                w.info.setText('Updated')
            w.pushButtonExit.setFocus()

        def specification_purge(startup=False) -> None:
            table.setSortingEnabled(False)
            table.clearSelection()
            table.clearContents()
            table.setColumnCount(0)
            table.setRowCount(0)
            table_details.setSortingEnabled(False)
            table_details.clearSelection()
            table_details.clearContents()
            table_details.setColumnCount(0)
            table_details.setRowCount(0)
            if not startup:
                w.info.setText('Cleared')

        specification_update(True)

        w.show()

        w.pushButtonUpdate.clicked.connect(specification_update)
        w.pushButtonClear.clicked.connect(specification_purge)

        def spec_export_settings() -> None:
            properties = P.load_properties()
            es = FreeCAD.Gui.PySideUic.loadUi(
                os.path.join(P.add_base, 'repo', 'ui', 'specification_es.ui'))

            es.JSON.setChecked(
                conf['spec_export_json_use_alias'])
            es.CSV.setChecked(
                conf['spec_export_csv_use_alias'])
            es.Spreadsheet.setChecked(
                conf['spec_export_spreadsheet_use_alias'])

            es.comboBoxMerger.addItems(properties.keys())
            es.comboBoxSorting.addItems(properties.keys())

            value = conf['spec_export_merger']
            if value in properties:
                es.comboBoxMerger.setCurrentText(value)
            value = conf['spec_export_sort']
            if value in properties:
                es.comboBoxSorting.setCurrentText(value)

            model = QtGui.QStandardItemModel()
            es.listView.setModel(model)
            for i in properties:
                item = QtGui.QStandardItem(i)
                item.setCheckable(True)
                if i == 'Name':
                    item.setEnabled(False)
                    item.setCheckState(QtCore.Qt.Checked)
                else:
                    if i in conf['spec_export_skip']:
                        item.setCheckState(QtCore.Qt.Unchecked)
                    else:
                        item.setCheckState(QtCore.Qt.Checked)
                model.appendRow(item)

            es.show()
            es.pushButtonApply.setFocus()

            def apply() -> None:
                conf['spec_export_type'] = w.comboBoxExport.currentText()
                conf['spec_export_json_use_alias'] = es.JSON.isChecked()
                conf['spec_export_csv_use_alias'] = es.CSV.isChecked()
                conf['spec_export_spreadsheet_use_alias'] = \
                    es.Spreadsheet.isChecked()
                conf['spec_export_merger'] = es.comboBoxMerger.currentText()
                conf['spec_export_sort'] = es.comboBoxSorting.currentText()
                conf['spec_export_skip'].clear()
                conf['spec_export_skip'].append('Body')  # required
                for index in range(model.rowCount()):
                    item = model.item(index)
                    if item.checkState() != QtCore.Qt.Checked:
                        conf['spec_export_skip'].append(item.text())
                P.save_configuration(conf)
                es.close()
            es.pushButtonApply.clicked.connect(apply)

        w.pushButtonExportSettings.clicked.connect(spec_export_settings)

        def specification_export() -> None:
            target = w.comboBoxExport.currentText()
            match target:
                case 'JSON' | 'CSV':
                    fd = QtGui.QFileDialog()
                    fd.setDefaultSuffix(target.lower())
                    fd.setAcceptMode(QtGui.QFileDialog.AcceptSave)
                    fd.setNameFilters(exporting[target])
                    if fd.exec_() == QtGui.QDialog.Accepted:
                        path = fd.selectedFiles()[0]
                        w.info.setText(S.export_specification(
                            path, target, w.checkBoxStrict.isChecked()))
                case 'Spreadsheet':
                    w.info.setText(S.export_specification(
                        '', target, w.checkBoxStrict.isChecked()))
        w.pushButtonExport.clicked.connect(specification_export)

        def switch_unfold(item) -> None:
            h = table_details.horizontalHeaderItem(item.column())
            if h is None:
                return
            if h.text() == 'Unfold':
                match item.text():
                    case 'True':
                        item.setText('False')
                        item.setForeground(color_red)
                    case 'False':
                        item.setText('True')
                        item.setForeground(color_blue)
        table_details.itemDoubleClicked.connect(switch_unfold)

        def select_unfold_all() -> None:
            for row in range(table_details.rowCount()):
                item = table_details.item(row, unfold_index)
                if item is None:
                    continue
                if item.text() == 'False':
                    item.setText('True')
                    item.setForeground(color_blue)
        w.pushButtonTrue.clicked.connect(select_unfold_all)

        def select_unfold_none() -> None:
            for row in range(table_details.rowCount()):
                item = table_details.item(row, unfold_index)
                if item is None:
                    continue
                if item.text() == 'True':
                    item.setText('False')
                    item.setForeground(color_red)
        w.pushButtonFalse.clicked.connect(select_unfold_none)

        def check_format() -> None:
            if not w.SVG.isChecked() and not w.STP.isChecked():
                w.DXF.setChecked(True)
                w.DXF.setEnabled(False)
            else:
                w.DXF.setEnabled(True)
        w.DXF.stateChanged.connect(check_format)
        w.SVG.stateChanged.connect(check_format)
        w.STP.stateChanged.connect(check_format)
        check_format()

        def directory() -> None:
            d = os.path.normcase(QtGui.QFileDialog.getExistingDirectory())
            if d != '':
                conf['working_directory'] = d
                P.save_configuration(conf)
                w.labelTarget.setText(f'... {os.path.basename(d)}')
        w.pushButtonDir.clicked.connect(directory)

        def redefinition() -> list:
            skip = []
            for row in range(table_details.rowCount()):
                item = table_details.item(row, unfold_index)
                if item is None:
                    continue
                if item.text() == 'False':
                    n = table_details.item(row, name_index)
                    if n is not None:
                        skip.append(n.text())
            return skip

        def unfold() -> None:
            strict = True if w.checkBoxStrict.isChecked() else False
            spec = S.get_specification(strict)
            prefix = str(w.lineEditPrefix.text()).strip()
            if prefix == '':
                prefix = 'Result'
            conf['unfold_prefix'] = prefix
            P.save_configuration(conf)
            path = os.path.join(conf['working_directory'], prefix)
            addFC_Unfold.unfold(w, spec[2], path, redefinition())
        w.pushButtonUnfold.clicked.connect(unfold)

        return

    def IsActive(self): return True if FreeCAD.ActiveDocument else False


FreeCAD.Gui.addCommand('AddFCSpecification', AddFCSpecification())


# ------------------------------------------------------------------------------


class AddFCProperties():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.add_icon, 'properties.svg'),
                'Accel': 'Alt+Shift+A',
                'MenuText': 'Add Properties',
                'ToolTip': 'Add properties to an object'}

    def Activated(self):
        ui = os.path.join(P.add_base, 'repo', 'ui', 'properties.ui')
        w = FreeCAD.Gui.PySideUic.loadUi(ui)
        w.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        configuration = P.load_configuration()
        properties = P.load_properties()

        group = configuration['properties_group']

        # sheet metal part:
        smp_material = ['-',]
        if 'Material' in properties:
            smp_material = properties['Material'][2]  # enumeration
        w.comboBoxSMP.addItems(smp_material)

        # guessing game:
        smp_type = '-'
        if 'Type' in properties:
            for i in properties['Type'][2]:  # enumeration
                if 'sheet metal part' in str(i).lower() or \
                        'sheet metal' in str(i).lower():
                    smp_type = i
                    break
                if 'листово' in str(i).lower():
                    smp_type = i
                    break

        def set_weight(obj, p: str) -> None:
            density = P.sheet_metal_part['density']
            if 'Tipe' in obj.PropertiesList:
                src = '.Tip.Shape.Volume'
            else:
                src = '.Shape.Volume'
            obj.setExpression(p, f'{src} / 1000000000 * {density}')

        def set_color(obj) -> None:
            color = tuple(i / 255 for i in P.sheet_metal_part['color'])
            obj.ViewObject.ShapeColor = color

        model = QtGui.QStandardItemModel()
        w.listView.setModel(model)
        for i in properties:
            item = QtGui.QStandardItem(i)
            item.setCheckable(True)
            item.setCheckState(QtCore.Qt.Unchecked)
            if i == 'Name':
                item.setEnabled(False)
                item.setCheckState(QtCore.Qt.Checked)
            model.appendRow(item)

        def add() -> None:
            if len(FreeCAD.Gui.Selection.getSelection()) < 1:
                return
            selection = FreeCAD.Gui.Selection.getSelection()
            _list, _smp = [], w.checkBoxSMP.isChecked()
            for i in selection:
                _list.clear()
                for j in i.InList:
                    if j.TypeId != 'App::Link':
                        _list.append(j)
                if FreeCAD.ActiveDocument.Name != i.Document.Name:
                    if len(_list) > 1:
                        i = _list[0]
                else:
                    try:
                        if i.BaseFeature is not None:
                            i = _list[0]
                        else:
                            match i.TypeId:
                                case 'PartDesign::Body' | 'App::Link':
                                    pass
                                case _:
                                    i = _list[0]
                    except BaseException:
                        pass
                if i.TypeId == 'App::Link':
                    i = i.LinkedObject
                if _smp:  # sheet metal part
                    set_color(i)
                for index in range(model.rowCount()):
                    item = model.item(index)
                    if item.checkState() != QtCore.Qt.Checked:
                        continue
                    text = item.text()
                    p = group + '_' + text
                    if p not in i.PropertiesList:
                        t = 'App::Property' + properties[text][0]
                        e = properties[text][2]
                        if len(e) > 0:  # enumeration
                            i.addProperty(t, p, group)
                            setattr(i, p, e)
                            if _smp:  # sheet metal part
                                if text == 'Material':
                                    setattr(i, p, w.comboBoxSMP.currentText())
                                elif text == 'Type':
                                    setattr(i, p, smp_type)
                        else:
                            i.addProperty(t, p, group)
                            match text:
                                # name template: '1. Body - 01'
                                case 'Name':
                                    if '. ' in i.Label[:int(len(i.Label) / 2)]:
                                        sp = i.Label.split('. ', 1)
                                        if len(sp) > 1:
                                            n = sp[1].rsplit(' - ', 1)
                                            setattr(i, p, n[0])
                                        else:
                                            n = sp[0].rsplit(' - ', 1)
                                            setattr(i, p, n[0])
                                    else:
                                        n = i.Label.rsplit(' - ', 1)
                                        setattr(i, p, n[0])
                                case 'Code':
                                    sp = i.Label.split('. ', 1)
                                    if len(sp) > 1:
                                        setattr(i, p, sp[0])
                                case 'Quantity':
                                    setattr(i, p, 1)
                                case 'Unfold':
                                    setattr(i, p, True)
                                case 'MetalThickness':
                                    bind = w.checkBoxLT.isChecked()
                                    try:
                                        thickness = float(
                                            S.define_thickness(i, bind, p))
                                        if not bind:
                                            setattr(i, p, thickness)
                                    except BaseException:
                                        pass
                            # sheet metal part:
                            if _smp and text == 'Weight':
                                set_weight(i, p)
            FreeCAD.activeDocument().recompute()
        w.pushButtonAdd.clicked.connect(add)

        def select_all() -> None:
            for index in range(model.rowCount()):
                item = model.item(index)
                if item.checkState() != QtCore.Qt.Checked:
                    item.setCheckState(QtCore.Qt.Checked)
        w.pushButtonAll.clicked.connect(select_all)

        def select_core() -> None:
            core = P.specification_properties_core
            for index in range(model.rowCount()):
                item = model.item(index)
                if item.text() in core:
                    if item.checkState() != QtCore.Qt.Checked:
                        item.setCheckState(QtCore.Qt.Checked)
                else:
                    if item.checkState() == QtCore.Qt.Checked:
                        item.setCheckState(QtCore.Qt.Unchecked)
        w.pushButtonCore.clicked.connect(select_core)

        def select_none() -> None:
            for index in range(model.rowCount()):
                item = model.item(index)
                if item.checkState() == QtCore.Qt.Checked:
                    if item.text() != 'Name':
                        item.setCheckState(QtCore.Qt.Unchecked)
        w.pushButtonNone.clicked.connect(select_none)

        def sheet_metal_part(state) -> None:
            if state == QtCore.Qt.CheckState.Unchecked:
                w.comboBoxSMP.setEnabled(False)
                w.checkBoxLT.setChecked(False)
                w.checkBoxLT.setEnabled(False)
                return
            w.comboBoxSMP.setEnabled(True)
            w.checkBoxLT.setEnabled(True)
            w.checkBoxLT.setChecked(True)
            values = ['Code', 'Material', 'MetalThickness', 'Unfold']  # core
            for key in properties:
                if key == 'Type' or key == 'Weight':
                    values.append(key)
            for index in range(model.rowCount()):
                item = model.item(index)
                if item.text() in values:
                    if item.checkState() != QtCore.Qt.Checked:
                        item.setCheckState(QtCore.Qt.Checked)
        w.checkBoxSMP.stateChanged.connect(sheet_metal_part)

        w.show()
        w.pushButtonAdd.setFocus()

        return

    def IsActive(self): return True if FreeCAD.ActiveDocument else False


FreeCAD.Gui.addCommand('AddFCProperties', AddFCProperties())


# ------------------------------------------------------------------------------


class AddFCPipe():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.add_icon, 'pipe.svg'),
                'Accel': 'Alt+Shift+P',
                'MenuText': 'Pipe',
                'ToolTip': 'Creating a pipe by points'}

    def Activated(self):
        file = os.path.join(P.add_base, 'utils', 'addFC_Pipe.py')
        loader = importlib.machinery.SourceFileLoader('addFC_Pipe', file)
        _ = loader.load_module()
        return

    def IsActive(self):
        return True if len(FreeCAD.Gui.Selection.getSelection()) > 0 else False


FreeCAD.Gui.addCommand('AddFCPipe', AddFCPipe())


# ------------------------------------------------------------------------------


class AddFCExplode():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.add_icon, 'explode.svg'),
                'Accel': 'Alt+Shift+E',
                'MenuText': 'Explode',
                'ToolTip': 'Exploded view'}

    def Activated(self):
        file = os.path.join(P.add_base, 'utils', 'addFC_Explode.py')
        loader = importlib.machinery.SourceFileLoader('addFC_Explode', file)
        _ = loader.load_module()
        return

    def IsActive(self): return True if FreeCAD.ActiveDocument else False


FreeCAD.Gui.addCommand('AddFCExplode', AddFCExplode())


# ------------------------------------------------------------------------------


examples_path: str = os.path.join(P.add_base, 'repo', 'example')
examples_path_zip: str = os.path.join(P.add_base, 'repo', 'example.zip')


examples: dict = {
    'Assembly': (
        os.path.join(examples_path, 'noAssembly.FCStd'),
        'An example of a complex parametric assembly, '
        'bill of materials, batch processing of sheet metal, '
        'and an exploded view.',
    ),
    'Belt Roller Support': (
        os.path.join(examples_path, 'beltRollerSupport.FCStd'),
        'Simple assembly example: bill of materials, exploded view '
        'and fasteners workbench support.'
    ),
    'Pipe': (
        os.path.join(examples_path, 'pipe.FCStd'),
        'An example for creating a pipeline by points.',
    ),
}


class OpenExample():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.add_icon, 'example.svg'),
                'MenuText': 'Open an example',
                'ToolTip': 'Open an example'}

    def Activated(self):
        ui = os.path.join(P.add_base, 'repo', 'ui', 'list.ui')
        w = FreeCAD.Gui.PySideUic.loadUi(ui)
        w.show()
        model = QtGui.QStandardItemModel()
        w.listView.setModel(model)
        for i in examples:
            model.appendRow(QtGui.QStandardItem(i))

        def unzip(reset: bool) -> None:
            if reset or not os.path.exists(examples_path):
                z = ZipFile(examples_path_zip, 'r')
                z.extractall(os.path.join(P.add_base, 'repo'))

        def select() -> None:
            for index in w.listView.selectedIndexes():
                item = w.listView.model().itemFromIndex(index).text()
                w.label.setText(examples[item][1])
        w.listView.clicked.connect(select)

        def open() -> None:
            for index in w.listView.selectedIndexes():
                item = w.listView.model().itemFromIndex(index).text()
                path = examples[item][0]
                w.close()
                unzip(True if not os.path.exists(path) else False)
                FreeCAD.openDocument(path)
        w.pushButtonOpen.clicked.connect(open)
        w.listView.doubleClicked.connect(open)

    def IsActive(self): return True


FreeCAD.Gui.addCommand('OpenExample', OpenExample())
