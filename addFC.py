# -*- coding: utf-8 -*-
# Copyright 2025 Golodnikov Sergey


from PySide import QtGui, QtCore
from zipfile import ZipFile
import addFC_Data as Data
import addFC_Logger as Logger
import addFC_Other as Other
import addFC_Preference as P
import addFC_Info as Info
import addFC_Unfold
import datetime
import difflib
import FreeCAD
import importlib.machinery
import os
import subprocess
import sys


EXPORTING = {
    'JSON': ['JSON (*.json)'],
    'CSV': ['CSV (*.csv)'],
    'Spreadsheet': [],
    'RU std: Spreadsheet': [],
    'RU std: TechDraw': [],
}

UNFOLD_NAME = (
    'Name',
    'Code',
    'Index',
    'Code + Name',
    'Index + Name',
)

UNFOLD_SIGNATURE = (
    'None',
    'Code',
    'Prefix',
    'Prefix + Code',
)


freeze_table, freeze_nodes = True, True

user_modification = False

structure = []

index_bom_title = 0
index_details_title = 0
index_details_unfold = 0

properties_last = ['Name',]


# ------------------------------------------------------------------------------


class AddFCOpenRecentFile():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.AFC_PATH_ICON, 'resent.svg'),
                'Accel': 'R',
                'MenuText': FreeCAD.Qt.translate(
                    'addFC', 'Recent File'),
                'ToolTip': FreeCAD.Qt.translate(
                    'addFC', 'Open recent file')}

    def Activated(self):
        ld = tuple(FreeCAD.listDocuments().keys())
        p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/RecentFiles")
        n = p.GetInt('RecentFiles')
        for i in range(n):
            f = p.GetString('MRU' + str(i))
            if f != '' and os.path.exists(f) and os.path.isfile(f):
                r, _ = os.path.splitext(os.path.basename(f))
                if r in ld:
                    continue
                FreeCAD.openDocument(f)
                FreeCAD.Gui.activeDocument().activeView().viewIsometric()
                FreeCAD.Gui.SendMsgToActiveView('ViewFit')
                return

        FreeCAD.Gui.runCommand('Std_Open')

    def IsActive(self): return True


FreeCAD.Gui.addCommand('AddFCOpenRecentFile', AddFCOpenRecentFile())


# ----


class AddFCDisplay():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.AFC_PATH_ICON, 'display.svg'),
                'Accel': 'D',
                'MenuText': FreeCAD.Qt.translate(
                    'addFC', 'Display'),
                'ToolTip': FreeCAD.Qt.translate(
                    'addFC', 'Isometry and fit all')}

    def Activated(self):
        try:
            FreeCAD.Gui.activeDocument().activeView().viewIsometric()
        except BaseException:
            pass
        FreeCAD.Gui.SendMsgToActiveView('ViewFit')
        return

    def IsActive(self): return True if FreeCAD.ActiveDocument else False


FreeCAD.Gui.addCommand('AddFCDisplay', AddFCDisplay())


# ----


class AddFCModelControl():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.AFC_PATH_ICON, 'control.svg'),
                'Accel': 'C',
                'MenuText': FreeCAD.Qt.translate(
                    'addFC', 'Model Control'),
                'ToolTip': FreeCAD.Qt.translate(
                    'addFC', 'Run the model control file')}

    def Activated(self):
        file = str(FreeCAD.ActiveDocument.getFileName())
        file = file.replace('.FCStd', '.py')
        if not os.path.isfile(file):
            Other.error('The model control file was not found.')
            return
        loader = importlib.machinery.SourceFileLoader('control', file)
        _ = loader.load_module()
        return

    def IsActive(self): return True if FreeCAD.ActiveDocument else False


FreeCAD.Gui.addCommand('AddFCModelControl', AddFCModelControl())


# ------------------------------------------------------------------------------


class AddFCModelInfo():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.AFC_PATH_ICON, 'info.svg'),
                'Accel': 'I',
                'MenuText': FreeCAD.Qt.translate(
                    'addFC', 'Model Information'),
                'ToolTip': FreeCAD.Qt.translate(
                    'addFC', 'Model information (BOM)')}

    def Activated(self):
        w = FreeCAD.Gui.PySideUic.loadUi(os.path.join(
            P.AFC_PATH, 'repo', 'ui', 'info.ui'))

        if not P.afc_additions['sm'][0]:
            w.tabWidget.setTabEnabled(1, False)

        global structure
        structure = Info.compilation()

        conf, prop = P.pref_configuration, P.pref_properties

        materials_list = list(P.pref_materials.keys())

        if conf['working_directory'] == '':
            conf['working_directory'] = os.path.expanduser('~/Desktop')
        w.target.setText(
            f"... {os.path.basename(conf['working_directory'])}")

        w.comboBoxExport.addItems(EXPORTING.keys())
        w.comboBoxName.addItems(UNFOLD_NAME)
        w.comboBoxSignature.addItems(UNFOLD_SIGNATURE)

        w.DXF.setChecked(conf['unfold_dxf'])
        w.SVG.setChecked(conf['unfold_svg'])
        w.STP.setChecked(conf['unfold_stp'])
        w.comboBoxExport.setCurrentText(conf['bom_export_type'])
        w.checkBoxCentering.setChecked(conf['unfold_centering'])
        w.checkBoxAlongX.setChecked(conf['unfold_along_x'])
        w.comboBoxName.setCurrentText(conf['unfold_file_name'])
        w.comboBoxSignature.setCurrentText(conf['unfold_file_signature'])
        w.lineEditPrefix.setText(conf['unfold_prefix'])

        table, table_details = w.infoTable, w.detailsTable

        color_blue = QtGui.QBrush(QtGui.QColor(0, 0, 150))
        color_red = QtGui.QBrush(QtGui.QColor(150, 0, 0))

        FORBIDDEN = ('!Body', '!Trace', 'Unit')

        PROHIBIT_EDITING = (
            'MetalThickness'
            'MT',
            'Name',
            'Price',
            'Quantity',
            'Qty',
            'Weight',
        )

        def get_node_name() -> str:
            if w.checkBoxNodes.isChecked():
                return w.comboBoxNodes.currentText()
            else:
                return ''

        def state_node(checked) -> None:
            w.comboBoxNodes.setEnabled(checked)
            structure_update_wrapper()
        w.checkBoxNodes.stateChanged.connect(state_node)

        def changed_node() -> None:
            if freeze_nodes:
                return
            node_name = get_node_name()
            if node_name == '':
                return
            global structure
            structure = Info.compilation(
                strict=w.checkBoxStrict.isChecked(),
                node_name=node_name,
            )
            structure_update()
            w.info.setText(f'Updated, node: {node_name}')

        w.comboBoxNodes.currentTextChanged.connect(changed_node)

        # bill of materials:

        def structure_update() -> None:

            global freeze_table
            freeze_table = True
            global freeze_nodes
            freeze_nodes = True

            w.info.setText('...')
            structure_purge()
            FreeCAD.Gui.updateGui()

            spec, spec_h, details, details_h, nodes = structure

            _node = w.comboBoxNodes.currentText()
            w.comboBoxNodes.clear()
            w.comboBoxNodes.addItems(nodes)
            w.comboBoxNodes.setCurrentText(_node)

            if len(spec) == 0:
                freeze_table, freeze_nodes = False, False
                return

            for i in spec:
                if spec[i]['Unit'] != '-':
                    value = f"{spec[i]['Quantity']} {spec[i]['Unit']}"
                    spec[i]['Quantity'] = value

            for i in FORBIDDEN:
                if i in spec_h:
                    del spec_h[i]
                if i in details_h:
                    del details_h[i]
            if 'Unfold' in spec_h:
                del spec_h['Unfold']

            # --- #
            # all #
            # --- #

            labels = list(spec_h.keys())
            global index_bom_title
            index_bom_title = labels.index('Name')

            table.setColumnCount(len(spec_h))
            table.setRowCount(len(spec))
            table.setHorizontalHeaderLabels(labels)
            table.horizontalHeader().setResizeMode(
                index_bom_title, QtGui.QHeaderView.Stretch)

            f_std = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

            q = QtGui.QTableWidgetItem
            x = 0
            for i in spec:
                for j in spec[i]:
                    if j in FORBIDDEN or j == 'Unfold':
                        continue
                    if prop[j][0] == 'Float' or prop[j][0] == 'Integer':
                        q = QtGui.QTableWidgetItem()
                        q.setTextAlignment(QtCore.Qt.AlignCenter)
                        q.setData(QtCore.Qt.DisplayRole, spec[i][j])
                    else:
                        q = QtGui.QTableWidgetItem()
                        q.setData(QtCore.Qt.DisplayRole, str(spec[i][j]))
                    if j in PROHIBIT_EDITING:
                        q.setFlags(f_std)
                    else:
                        q.setForeground(color_blue)
                    table.setItem(x, labels.index(j), q)
                x += 1

            labels.clear()
            for i in spec_h:
                value = spec_h[i]
                if value > 0:
                    labels.append(f'{i}\n{value}')
                else:
                    if i == 'MetalThickness':
                        labels.append('MT')
                    elif i == 'Quantity':
                        labels.append('Qty')
                    else:
                        labels.append(i)
            table.setHorizontalHeaderLabels(labels)

            table.resizeColumnsToContents()
            table.resizeRowsToContents()
            table.horizontalHeader().setResizeMode(
                index_bom_title, QtGui.QHeaderView.Stretch)

            table.sortItems(index_bom_title)
            table.setSortingEnabled(True)
            table.horizontalHeader().setSortIndicatorShown(False)

            # ------- #
            # details #
            # ------- #

            if len(details) == 0:
                w.pushButtonExit.setFocus()
                freeze_table, freeze_nodes = False, False
                return

            labels = list(details_h.keys())
            global index_details_title
            index_details_title = labels.index('Name')
            global index_details_unfold
            index_details_unfold = labels.index('Unfold')

            table_details.setColumnCount(len(details_h))
            table_details.setRowCount(len(details))
            table_details.setHorizontalHeaderLabels(labels)
            table_details.horizontalHeader().setResizeMode(
                labels.index('Name'), QtGui.QHeaderView.Stretch)

            x = 0
            for i in details:
                for j in details[i]:
                    if j in FORBIDDEN:
                        continue
                    v = str(details[i][j])
                    q = QtGui.QTableWidgetItem(v)
                    if j == 'Unfold':
                        q.setTextAlignment(QtCore.Qt.AlignCenter)
                        match v:
                            case 'True': q.setForeground(color_blue)
                            case 'False': q.setForeground(color_red)
                    if j == 'MetalThickness':
                        if v == '-':
                            q.setForeground(color_red)
                    if prop[j][0] == 'Float' or prop[j][0] == 'Integer':
                        if v != '-':
                            q.setTextAlignment(QtCore.Qt.AlignCenter)
                            q.setData(QtCore.Qt.DisplayRole, v)
                    table_details.setItem(x, labels.index(j), q)
                x += 1

            labels.clear()
            for i in details_h:
                value = details_h[i]
                if value > 0:
                    labels.append(f'{i}\n{value}')
                else:
                    if i == 'MetalThickness':
                        labels.append('MT')
                    elif i == 'Quantity':
                        labels.append('Qty')
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

            freeze_table, freeze_nodes = False, False

            w.pushButtonExit.setFocus()

        def structure_update_wrapper() -> None:
            global structure
            structure = Info.compilation(
                strict=w.checkBoxStrict.isChecked(),
                node_name=get_node_name(),
            )
            structure_update()
            w.info.setText(FreeCAD.Qt.translate('addFC', 'Updated'))

        def structure_purge() -> None:
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

        def structure_purge_wrapper() -> None:
            structure_purge()
            w.info.setText(FreeCAD.Qt.translate('addFC', 'Cleared'))

        structure_update()
        w.info.setText('...')

        # ----------------- #
        # editing via table #
        # ----------------- #

        def changed(item) -> None:
            if freeze_table:
                return

            header = w.infoTable.horizontalHeaderItem(item.column())
            if header is None:
                return
            header = header.text()

            row = item.row()

            value = w.infoTable.item(row, item.column())
            if value is None:
                return
            value = value.text()

            title = w.infoTable.item(row, index_bom_title)
            if title is None:
                return
            title = title.text()

            p = prop.get(header)

            enum = materials_list if header == 'Material' else p[2]

            match p[0]:
                case 'Bool':
                    v = True if 't' in value.lower() else False
                case 'Enumeration':
                    if value == '':
                        v = '-'
                    else:
                        choice = difflib.get_close_matches(value, enum, 1, 0)
                        if len(choice) > 0:
                            v = choice[0]
                        else:
                            v = '-'
                    item.setText(v)
                case 'Float':
                    try:
                        v = float(value)
                    except ValueError:
                        v = 0
                case 'Integer':
                    try:
                        v = int(value)
                    except ValueError:
                        v = 0
                case _:
                    v = str(value)

            i = structure[0].get(title)

            try:
                i[header] = v
                pt = 'App::Property' + p[0]
                pn = 'Add_' + header
                objects = i.get('!Trace')
                for obj in objects:
                    o = FreeCAD.getDocument(obj[0]).getObject(obj[1])
                    if pn not in o.PropertiesList:
                        o.addProperty(pt, pn, 'Add')
                        if len(enum) > 0:
                            setattr(o, pn, enum)
                    setattr(o, pn, v)
                    o.recompute(True)
                item.setForeground(color_blue)
                global user_modification
                user_modification = True
            except BaseException as e:
                Logger.error(str(e))

        w.infoTable.itemChanged.connect(changed)

        def switch_tab(i) -> None:
            global user_modification
            if user_modification:
                if i == 1:  # details
                    structure_update()
                user_modification = False
        w.tabWidget.currentChanged.connect(switch_tab)

        # checking the functionality:
        if not P.afc_additions['sm'][0]:
            w.pushButtonUnfold.setEnabled(False)
        if not P.afc_additions['ezdxf'][0]:
            w.comboBoxSignature.setCurrentText('None')
            w.comboBoxSignature.setEnabled(False)

        w.show()

        w.pushButtonUpdate.clicked.connect(structure_update_wrapper)
        w.pushButtonClear.clicked.connect(structure_purge_wrapper)

        def indexing() -> None:
            global structure
            structure = Info.compilation(
                strict=w.checkBoxStrict.isChecked(),
                node_name=get_node_name(),
                indexing=True,
            )
            structure_update()
            w.info.setText(FreeCAD.Qt.translate(
                'addFC', 'Elements are indexed'))
        w.pushButtonIndexing.clicked.connect(indexing)

        def update_enumerations() -> None:
            global structure
            structure = Info.compilation(
                strict=w.checkBoxStrict.isChecked(),
                node_name=get_node_name(),
                update_enumerations=True,
            )
            structure_update()
            w.info.setText(FreeCAD.Qt.translate(
                'addFC', 'Enumerations updated'))
        w.pushButtonUEnum.clicked.connect(update_enumerations)

        def update_equations() -> None:
            global structure
            structure = Info.compilation(
                strict=w.checkBoxStrict.isChecked(),
                node_name=get_node_name(),
                update_equations=True,
            )
            structure_update()
            w.info.setText(FreeCAD.Qt.translate('addFC', 'Equations updated'))
        w.pushButtonUEq.clicked.connect(update_equations)

        def spec_export_settings() -> None:
            es = FreeCAD.Gui.PySideUic.loadUi(os.path.join(
                P.AFC_PATH, 'repo', 'ui', 'info_set.ui'))

            for i in conf['bom_export_alias']:
                match i:
                    case 'json':  es.JSON.setChecked(True)
                    case 'csv': es.CSV.setChecked(True)
                    case 'spreadsheet': es.Spreadsheet.setChecked(True)

            es.comboBoxMerger.addItems(prop.keys())
            es.comboBoxSorting.addItems(prop.keys())

            value = conf['bom_export_merger']
            if value in prop:
                es.comboBoxMerger.setCurrentText(value)
            value = conf['bom_export_sort']
            if value in prop:
                es.comboBoxSorting.setCurrentText(value)

            model = QtGui.QStandardItemModel()
            es.listView.setModel(model)
            for i in prop:
                item = QtGui.QStandardItem(i)
                item.setCheckable(True)
                if i == 'Name':
                    item.setEnabled(False)
                    item.setCheckState(QtCore.Qt.Checked)
                else:
                    if i in conf['bom_export_skip']:
                        item.setCheckState(QtCore.Qt.Unchecked)
                    else:
                        item.setCheckState(QtCore.Qt.Checked)
                model.appendRow(item)

            es.show()
            es.pushButtonApply.setFocus()

            def apply() -> None:
                conf['bom_export_type'] = w.comboBoxExport.currentText()
                conf['bom_export_merger'] = es.comboBoxMerger.currentText()
                conf['bom_export_sort'] = es.comboBoxSorting.currentText()

                conf['bom_export_alias'].clear()
                if es.JSON.isChecked():
                    conf['bom_export_alias'].append('json')
                if es.CSV.isChecked():
                    conf['bom_export_alias'].append('csv')
                if es.Spreadsheet.isChecked():
                    conf['bom_export_alias'].append('spreadsheet')

                conf['bom_export_skip'].clear()
                for index in range(model.rowCount()):
                    item = model.item(index)
                    if item.checkState() != QtCore.Qt.Checked:
                        conf['bom_export_skip'].append(item.text())

                P.save_pref(P.PATH_CONFIGURATION, conf)
                es.close()

            es.pushButtonApply.clicked.connect(apply)

        w.pushButtonExportSettings.clicked.connect(spec_export_settings)

        def structure_export() -> None:
            target = w.comboBoxExport.currentText()
            match target:
                case 'JSON' | 'CSV':
                    fd = QtGui.QFileDialog()
                    fd.setDefaultSuffix(target.lower())
                    fd.setAcceptMode(QtGui.QFileDialog.AcceptSave)
                    fd.setNameFilters(EXPORTING[target])
                    if fd.exec_() == QtGui.QDialog.Accepted:
                        path = fd.selectedFiles()[0]
                        w.info.setText('...')
                        FreeCAD.Gui.updateGui()
                        w.info.setText(Info.export(
                            path, target, structure))
                case 'Spreadsheet':
                    w.info.setText('...')
                    FreeCAD.Gui.updateGui()
                    w.info.setText(Info.export(
                        '', target, structure))
                # USDD:
                case 'RU std: Spreadsheet' | 'RU std: TechDraw':
                    w.info.setText('...')
                    FreeCAD.Gui.updateGui()
                    w.info.setText(Info.export(
                        '', target, structure))
        w.pushButtonExport.clicked.connect(structure_export)

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
                item = table_details.item(row, index_details_unfold)
                if item is None:
                    continue
                if item.text() == 'False':
                    item.setText('True')
                    item.setForeground(color_blue)
        w.pushButtonTrue.clicked.connect(select_unfold_all)

        def select_unfold_none() -> None:
            for row in range(table_details.rowCount()):
                item = table_details.item(row, index_details_unfold)
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
                P.save_pref(P.PATH_CONFIGURATION, conf)
                w.target.setText(f'... {os.path.basename(d)}')
        w.pushButtonDir.clicked.connect(directory)

        def redefinition() -> list:
            skip = []
            for row in range(table_details.rowCount()):
                item = table_details.item(row, index_details_unfold)
                if item is None:
                    continue
                if item.text() == 'False':
                    n = table_details.item(row, index_details_title)
                    if n is not None:
                        skip.append(n.text())
            return skip

        def unfold() -> None:
            prefix = str(w.lineEditPrefix.text()).strip()
            if prefix == '':
                prefix = 'Result'
            # remember options:
            conf['unfold_dxf'] = w.DXF.isChecked()
            conf['unfold_svg'] = w.SVG.isChecked()
            conf['unfold_stp'] = w.STP.isChecked()
            conf['unfold_centering'] = w.checkBoxCentering.isChecked()
            conf['unfold_along_x'] = w.checkBoxAlongX.isChecked()
            conf['unfold_file_name'] = w.comboBoxName.currentText()
            conf['unfold_file_signature'] = w.comboBoxSignature.currentText()
            conf['unfold_prefix'] = prefix
            P.save_pref(P.PATH_CONFIGURATION, conf)
            # unfold:
            path = os.path.join(conf['working_directory'], prefix)
            addFC_Unfold.unfold(w, structure[2], path, redefinition())
        w.pushButtonUnfold.clicked.connect(unfold)

        return

    def IsActive(self): return True if FreeCAD.ActiveDocument else False


FreeCAD.Gui.addCommand('AddFCModelInfo', AddFCModelInfo())


# ------------------------------------------------------------------------------


def parse_label(label: str) -> tuple[str, str]:
    # name template: 'Index (sep) Name (sep?) Copy|Index'
    index = ''
    if len(label) > 3:
        if '. ' in label[:4]:
            try:
                sp = label.split('. ', 1)
                if len(sp) > 1:
                    if len(sp[1].strip()) > 1:
                        index = sp[0].replace('0', '').strip()
                        label = sp[1].strip()
            except BaseException:
                pass
        if ' - ' in label[:6]:
            try:
                sp = label.split(' - ', 1)
                if len(sp) > 1:
                    if len(sp[1].strip()) > 1:
                        index = sp[0].replace('0', '').strip()
                        label = sp[1].strip()
            except BaseException:
                pass
    sp = label.rsplit(' - ', 1)
    if len(sp) > 1:
        if len(sp[1]) < 5:
            label = sp[0].strip()
    if len(label) > 3:
        if '0' in label[-3:]:
            if index == '':
                try:
                    index = str(int(label[-3:].replace('0', '')))
                    label = label[:-3]
                except ValueError:
                    pass
    return index, label


class AddFCProperties():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.AFC_PATH_ICON, 'properties.svg'),
                'Accel': 'A',
                'MenuText': FreeCAD.Qt.translate(
                    'addFC', 'Add Properties'),
                'ToolTip': FreeCAD.Qt.translate(
                    'addFC', 'Add properties to an object')}

    def Activated(self):
        w = FreeCAD.Gui.PySideUic.loadUi(os.path.join(
            P.AFC_PATH, 'repo', 'ui', 'properties.ui'))
        w.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        configuration = P.pref_configuration
        materials = P.pref_materials
        properties = P.pref_properties

        core = Data.properties_core

        default_material = configuration['default_material']
        if default_material not in materials:
            default_material = '-'

        # sheet metal part, materials:
        smp_materials = core['Material'][2]
        for key in materials:
            if key == '-' or key in smp_materials:
                continue
            if materials[key][0] == 'Sheet metal':
                smp_materials.append(key)
        w.comboBoxSMP.addItems(smp_materials)

        # sheet metal part, guessing game:
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

        def set_color(obj, color: tuple) -> None:
            obj.ViewObject.ShapeColor = tuple(i / 255 for i in color)

        # ---------- #
        # properties #
        # ---------- #

        color_black = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        color_blue = QtGui.QBrush(QtGui.QColor(0, 0, 150))

        table = w.tableWidget

        labels = ('Property', 'Value')
        table.setColumnCount(len(labels))
        table.setHorizontalHeaderLabels(labels)
        table.setRowCount(len(properties))

        def cb_changed(text) -> None:
            if text == '-':
                return
            indexes = table.selectedIndexes()
            if len(indexes) < 1:
                return
            p = table.item(indexes[0].row(), 0)
            if p.checkState() != QtCore.Qt.Checked:
                p.setCheckState(QtCore.Qt.CheckState.Checked)
                p.setForeground(color_blue)

        f = QtCore.Qt.ItemFlag

        cb_materials, cb_type = QtGui.QComboBox(), QtGui.QComboBox()

        x = 0
        for key in properties:
            # property:
            q = QtGui.QTableWidgetItem(str(key))
            q.setFlags(f.ItemIsUserCheckable | f.ItemIsEnabled)
            if key == 'Name':
                q.setCheckState(QtCore.Qt.CheckState.Checked)
                q.setFlags(QtCore.Qt.NoItemFlags)
            else:
                q.setCheckState(QtCore.Qt.CheckState.Unchecked)
            table.setItem(x, 0, q)
            # value:
            if properties[key][0] == 'Enumeration':
                cb = QtGui.QComboBox()
                if key == 'Material':
                    cb_materials.addItems(materials.keys())
                    cb_materials.setCurrentText(default_material)
                    cb_materials.setStyleSheet('border: none')
                    table.setCellWidget(x, 1, cb_materials)
                    cb_materials.currentTextChanged.connect(cb_changed)
                elif key == 'Type':
                    cb_type.addItems(properties[key][2])
                    cb_type.setStyleSheet('border: none')
                    table.setCellWidget(x, 1, cb_type)
                    cb_type.currentTextChanged.connect(cb_changed)
                else:
                    cb.addItems(properties[key][2])
                    cb.setStyleSheet('border: none')
                    table.setCellWidget(x, 1, cb)
                    cb.currentTextChanged.connect(cb_changed)
            elif properties[key][0] == 'Bool':
                cb = QtGui.QComboBox()
                cb.addItems(('True', 'False'))
                cb.setStyleSheet('border: none')
                table.setCellWidget(x, 1, cb)
                cb.currentTextChanged.connect(cb_changed)
            else:
                table.setItem(x, 1, QtGui.QTableWidgetItem())
            x += 1

        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        table.horizontalHeader().setResizeMode(
            labels.index('Value'), QtGui.QHeaderView.Stretch)

        def item_changed(item) -> None:
            if item is None:
                return
            if item.column() == 0:
                if item.checkState() != QtCore.Qt.Unchecked:
                    item.setForeground(color_blue)
                else:
                    item.setForeground(color_black)
            elif item.column() == 1:
                if item.text() != '':
                    i = table.item(item.row(), 0)
                    if i.checkState() != QtCore.Qt.Checked:
                        i.setCheckState(QtCore.Qt.CheckState.Checked)
                        i.setForeground(color_blue)

        table.itemChanged.connect(item_changed)

        # ------------ #
        # add property #
        # ------------ #

        def add() -> None:
            if len(FreeCAD.Gui.Selection.getSelection()) < 1:
                w.info.setText(FreeCAD.Qt.translate(
                    'addFC', 'You need to select an object'))
                return
            w.info.setText('')

            smp = w.checkBoxSMP.isChecked()

            selection = FreeCAD.Gui.Selection.getSelectionEx('')
            if len(selection) == 0:
                return
            for s in selection:
                if s.HasSubObjects:
                    i = s.Object.InList[0]
                else:
                    i = s.Object

                if i.TypeId == 'App::Link':
                    i = i.LinkedObject
                if smp:
                    # sheet metal part, color:
                    set_color(i, configuration['smp_color'])

                stuff, material = {}, []

                global properties_last
                properties_last.clear()

                for row in range(table.rowCount()):
                    prop = table.item(row, 0)
                    if prop.checkState() != QtCore.Qt.Checked:
                        continue
                    prop, value = prop.text(), table.item(row, 1)
                    if value is not None:
                        value = value.text()
                    else:
                        value = table.cellWidget(row, 1)
                        value = value.currentText()
                    if prop == 'Material':
                        enum = list(materials.keys())
                        enum.sort()
                        if value != '-':
                            material = materials[value]
                    else:
                        enum = properties[prop][2]
                    properties_last.append(prop)
                    # property: (type, enumeration, value)
                    stuff['Add_' + prop] = (
                        'App::Property' + properties[prop][0],
                        enum,
                        value,
                    )

                index, name = parse_label(i.Label)
                eq = w.checkBoxEq.isChecked()

                keys = list(stuff.keys())
                keys.sort()

                if 'Add_Price' in keys:
                    # castling:
                    keys.remove('Add_Price')
                    keys.append('Add_Price')

                for k in keys:
                    v = stuff[k]  # 0:type, 1:enumeration, 2:value

                    if k in i.PropertiesList:
                        old = i.getPropertyByName(k)
                        if len(v[1]) > 0:
                            e = v[1].sort()
                            try:
                                ep = i.getEnumerationsOfProperty(k)
                                ep.sort()
                                if e != ep and len(e) > len(ep):
                                    setattr(i, k, e)  # update
                            except BaseException:
                                pass
                    else:
                        old = ''
                        i.addProperty(v[0], k, 'Add')
                        if len(v[1]) > 0:
                            setattr(i, k, v[1])

                    match k:
                        case 'Add_Name':
                            if old == '':
                                i.Add_Name = name if v[2] == '' else v[2]
                            elif old != v[2] and v[2] != '':
                                i.Add_Name = v[2]
                        case 'Add_Index':
                            if old == '':
                                i.Add_Index = index if v[2] == '' else v[2]
                            elif old != v[2] and v[2] != '':
                                i.Add_Index = v[2]
                        case 'Add_Quantity':
                            try:
                                _f = float(v[2])
                            except ValueError:
                                _f = 1
                            if old != _f:
                                i.Add_Quantity = _f
                        case 'Add_Unfold':
                            _b = True if v[2] == 'True' else False
                            if old != _b:
                                i.Add_Unfold = _b
                        case 'Add_MetalThickness':
                            bind = w.checkBoxLT.isChecked()
                            try:
                                _f = float(v[2])
                            except ValueError:
                                _f = Info.define_thickness(i, bind, k)
                                if _f == '-':
                                    _f = 0
                            if not bind:
                                i.Add_MetalThickness = _f
                        # equations:
                        case 'Add_Weight' | 'Add_Price':
                            try:
                                _f = float(v[2])
                            except ValueError:
                                _f = 0
                            if old == 0 or old == '':
                                if eq or _f == 0:
                                    if len(material) > 0:
                                        if k == 'Add_Weight':
                                            Info.weight_equation(i, material)
                                        else:
                                            Info.price_equation(i, material)
                                else:
                                    setattr(i, k, _f)
                        # default:
                        case _:
                            match v[0]:
                                case 'App::PropertyFloat':
                                    try:
                                        _f = float(v[2])
                                    except ValueError:
                                        _f = 0
                                    if old != _f and f != 0:
                                        setattr(i, k, _f)
                                case 'App::PropertyInteger':
                                    try:
                                        _i = int(v[2])
                                    except ValueError:
                                        _i = 0
                                    if old != _i and _i != 0:
                                        setattr(i, k, _i)
                                case 'App::PropertyBool':
                                    _b = True if v[2] == 'True' else False
                                    if old != _b:
                                        setattr(i, k, _b)
                                case _:
                                    if old != v[2] and v[2] != '':
                                        setattr(i, k, v[2])

            FreeCAD.activeDocument().recompute()

        w.pushButtonAdd.clicked.connect(add)

        def select_all() -> None:
            for r in range(table.rowCount()):
                i = table.item(r, 0)
                if i is None:
                    continue
                if i.checkState() != QtCore.Qt.Checked:
                    i.setCheckState(QtCore.Qt.CheckState.Checked)
                    i.setForeground(color_blue)
        w.pushButtonAll.clicked.connect(select_all)

        def select_prev() -> None:
            for r in range(table.rowCount()):
                i = table.item(r, 0)
                if i is None:
                    continue
                if i.text() in properties_last:
                    if i.checkState() != QtCore.Qt.Checked:
                        i.setCheckState(QtCore.Qt.CheckState.Checked)
                        i.setForeground(color_blue)
                else:
                    if i.checkState() != QtCore.Qt.Unchecked:
                        i.setCheckState(QtCore.Qt.CheckState.Unchecked)
                        i.setForeground(color_black)
        w.pushButtonPrev.clicked.connect(select_prev)

        def select_core() -> None:
            for r in range(table.rowCount()):
                i = table.item(r, 0)
                if i is None:
                    continue
                if i.text() in core:
                    if i.checkState() != QtCore.Qt.Checked:
                        i.setCheckState(QtCore.Qt.CheckState.Checked)
                        i.setForeground(color_blue)
                else:
                    if i.checkState() != QtCore.Qt.Unchecked:
                        i.setCheckState(QtCore.Qt.CheckState.Unchecked)
                        i.setForeground(color_black)
        w.pushButtonCore.clicked.connect(select_core)

        def select_none() -> None:
            for r in range(table.rowCount()):
                i = table.item(r, 0)
                if i is None:
                    continue
                if i.text() == 'Name':
                    continue
                if i.checkState() != QtCore.Qt.Unchecked:
                    i.setCheckState(QtCore.Qt.CheckState.Unchecked)
                    i.setForeground(color_black)
        w.pushButtonNone.clicked.connect(select_none)

        def state_smp(state) -> None:
            if state == QtCore.Qt.CheckState.Unchecked:
                w.comboBoxSMP.setCurrentText('-')
                w.comboBoxSMP.setEnabled(False)
                w.checkBoxLT.setChecked(False)
                w.checkBoxLT.setEnabled(False)
                cb_materials.setEnabled(True)
                return
            w.comboBoxSMP.setCurrentText('Galvanized')
            w.comboBoxSMP.setEnabled(True)
            w.checkBoxLT.setEnabled(True)
            w.checkBoxLT.setChecked(True)
            cb_materials.setEnabled(False)
            values = [
                'Code',
                'Index',
                'Material',
                'MetalThickness',
                'Unfold',
                'Weight',
            ]
            if 'Type' in properties:
                values.append('Type')
                cb_type.setCurrentText(smp_type)
            for r in range(table.rowCount()):
                i = table.item(r, 0)
                if i is None:
                    continue
                if i.text() in values:
                    if i.checkState() != QtCore.Qt.Checked:
                        i.setCheckState(QtCore.Qt.CheckState.Checked)
                        i.setForeground(color_blue)
        w.checkBoxSMP.stateChanged.connect(state_smp)

        def changed_material(text) -> None:
            cb_materials.setCurrentText(text)
        w.comboBoxSMP.currentTextChanged.connect(changed_material)

        w.show()
        w.pushButtonAdd.setFocus()

        return

    def IsActive(self): return True if FreeCAD.ActiveDocument else False


FreeCAD.Gui.addCommand('AddFCProperties', AddFCProperties())


# ------------------------------------------------------------------------------


def stamp_fill(ed: dict) -> dict:
    conf = P.pref_configuration
    today = datetime.date.today().strftime('%d.%m.%y')
    dt = ('Author', 'Inspector', 'Control 1', 'Control 2', 'Approver')
    stamp = conf['ru_std_tpl_stamp']
    for i in stamp:
        if i in ed:
            v = stamp[i]
            ed[i] = v
            if i in dt:
                ed[f'{i} - date'] = today if v != '' else ''
    return ed


class AddFCInsert():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.AFC_PATH_ICON, 'insert.svg'),
                'MenuText': FreeCAD.Qt.translate(
                    'addFC', 'Creating a Drawing'),
                'ToolTip': FreeCAD.Qt.translate(
                    'addFC', 'Create a drawing based on a template')}

    def Activated(self):
        w = FreeCAD.Gui.PySideUic.loadUi(os.path.join(
            P.AFC_PATH, 'repo', 'ui', 'list.ui'))

        if not FreeCAD.ActiveDocument:
            FreeCAD.newDocument('Unnamed')
            FreeCAD.Gui.activeDocument().activeView().viewDefaultOrientation()

        ad = FreeCAD.ActiveDocument

        _, _, tpl = P.get_tpl()
        tpl = dict(sorted(tpl.items()))

        model = QtGui.QStandardItemModel()
        w.listView.setModel(model)
        for i in tpl.keys():
            model.appendRow(QtGui.QStandardItem(i.rstrip('.svg')))

        w.label.setText('Select a template to create a drawing.')
        w.pushButton.setText(FreeCAD.Qt.translate('addFC', 'Create'))
        w.show()

        def create() -> None:
            for i in w.listView.selectedIndexes():
                item = w.listView.model().itemFromIndex(i).text()
                w.close()
                p = ad.addObject('TechDraw::DrawPage', 'Page')
                t = ad.addObject('TechDraw::DrawSVGTemplate', 'Template')
                t.Template = tpl[item + '.svg']
                t.EditableTexts = stamp_fill(t.EditableTexts)
                p.Template = t
                ad.recompute()
                # display:
                FreeCAD.Gui.activateWorkbench('TechDrawWorkbench')
                p.ViewObject.doubleClicked()
                FreeCAD.Gui.updateGui()
                FreeCAD.Gui.SendMsgToActiveView('ViewFit')

        w.pushButton.clicked.connect(create)
        w.listView.doubleClicked.connect(create)

    def IsActive(self): return True


FreeCAD.Gui.addCommand('AddFCInsert', AddFCInsert())


# ------------------------------------------------------------------------------


DOCUMENTATION_PATH = os.path.join(P.AFC_PATH, 'repo', 'doc')
EXAMPLES_PATH_ZIP = os.path.join(P.AFC_PATH, 'repo', 'example.zip')
EXAMPLES_PATH = os.path.join(P.AFC_PATH, 'repo', 'example')


examples: dict = {
    'addFC - Additional files': (
        os.path.join(P.AFC_PATH, 'repo', 'add'),
        FreeCAD.Qt.translate(
            'addFC', 'Supporting files such as templates, fonts.'),
    ),
    # documentation:
    'Documentation - English': (
        os.path.join(DOCUMENTATION_PATH, 'documentation_EN.pdf'),
        'Documentation in PDF format - English.',
    ),
    'Documentation - Russian': (
        os.path.join(DOCUMENTATION_PATH, 'documentation_RU.pdf'),
        'Документация в формате PDF на русском языке.',
    ),
    # examples:
    'Assembly': (
        os.path.join(EXAMPLES_PATH, 'noAssembly.FCStd'),
        'An example of a complex parametric assembly, '
        'bill of materials, batch processing of sheet metal, '
        'and an exploded view.\nAttention! Sheet metal currently '
        'does not work in version 1 and above.',
    ),
    'Belt Roller Support': (
        os.path.join(EXAMPLES_PATH, 'beltRollerSupport.FCStd'),
        'Simple assembly example: bill of materials, exploded view '
        'and fasteners workbench support.\nFastenersWB required.'
    ),
    'Pipe': (
        os.path.join(EXAMPLES_PATH, 'pipe.FCStd'),
        'An example for creating a pipeline by points.',
    ),
    'RU std: ЕСКД - Модель': (
        os.path.join(EXAMPLES_PATH, 'stdRU.FCStd'),
        'Простой пример оформления конструкторской документации по '
        'стандартам ЕСКД.',
    ),
    'RU std: ЕСКД - Конструкторская документация': (
        os.path.join(DOCUMENTATION_PATH, 'stdRU.pdf'),
        'Простой пример оформления конструкторской документации по '
        'стандартам ЕСКД.',
    ),
}


class AddFCAssistant():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.AFC_PATH_ICON, 'help.svg'),
                'MenuText': FreeCAD.Qt.translate(
                    'addFC', 'Help and Example'),
                'ToolTip': FreeCAD.Qt.translate(
                    'addFC', 'Help, examples and additional files')}

    def Activated(self):
        w = FreeCAD.Gui.PySideUic.loadUi(os.path.join(
            P.AFC_PATH, 'repo', 'ui', 'list.ui'))

        model = QtGui.QStandardItemModel()
        w.listView.setModel(model)
        for i in examples:
            model.appendRow(QtGui.QStandardItem(i))

        w.pushButton.setText(FreeCAD.Qt.translate('addFC', 'Open'))
        w.show()

        def unzip(reset: bool) -> None:
            if reset or not os.path.exists(EXAMPLES_PATH):
                z = ZipFile(EXAMPLES_PATH_ZIP, 'r')
                z.extractall(os.path.join(P.AFC_PATH, 'repo'))
                z.close()

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
                if 'files' in item:
                    run(path)
                elif path.endswith('.pdf'):
                    cp = run(path)
                    if cp.returncode != 0:
                        run(os.path.dirname(path))
                else:
                    unzip(True if not os.path.exists(path) else False)
                    FreeCAD.openDocument(path)
        w.pushButton.clicked.connect(open)
        w.listView.doubleClicked.connect(open)

    def IsActive(self): return True


FreeCAD.Gui.addCommand('AddFCAssistant', AddFCAssistant())


def run(path: str) -> subprocess.CompletedProcess:
    match sys.platform:
        case 'win32': return subprocess.run(['explorer', path])
        case 'darwin': return subprocess.run(['open', path])
        case _: return subprocess.run(['xdg-open', path])


# ------------------------------------------------------------------------------


class AddFCLibrary():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.AFC_PATH_ICON, 'library.svg'),
                'Accel': 'L',
                'MenuText': FreeCAD.Qt.translate(
                    'addFC', 'Library'),
                'ToolTip': FreeCAD.Qt.translate(
                    'addFC', 'Component library')}

    def Activated(self):
        file = os.path.join(P.AFC_PATH, 'utils', 'addFC_Library.py')
        loader = importlib.machinery.SourceFileLoader('addFC_Library', file)
        _ = loader.load_module()
        return

    def IsActive(self): return True if FreeCAD.ActiveDocument else False


FreeCAD.Gui.addCommand('AddFCLibrary', AddFCLibrary())


# ----


class AddFCExplode():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.AFC_PATH_ICON, 'explode.svg'),
                'Accel': 'E',
                'MenuText': FreeCAD.Qt.translate(
                    'addFC', 'Explode'),
                'ToolTip': FreeCAD.Qt.translate(
                    'addFC', 'Exploded view')}

    def Activated(self):
        file = os.path.join(P.AFC_PATH, 'utils', 'addFC_Explode.py')
        loader = importlib.machinery.SourceFileLoader('addFC_Explode', file)
        _ = loader.load_module()
        return

    def IsActive(self): return True if FreeCAD.ActiveDocument else False


FreeCAD.Gui.addCommand('AddFCExplode', AddFCExplode())


# ----


class AddFCPipe():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.AFC_PATH_ICON, 'pipe.svg'),
                'Accel': 'P',
                'MenuText': FreeCAD.Qt.translate(
                    'addFC', 'Pipe'),
                'ToolTip': FreeCAD.Qt.translate(
                    'addFC', 'Creating a pipe by points')}

    def Activated(self):
        file = os.path.join(P.AFC_PATH, 'utils', 'addFC_Pipe.py')
        loader = importlib.machinery.SourceFileLoader('addFC_Pipe', file)
        _ = loader.load_module()
        return

    def IsActive(self):
        return True if len(FreeCAD.Gui.Selection.getSelection()) > 0 else False


FreeCAD.Gui.addCommand('AddFCPipe', AddFCPipe())


# ----


class AddFCSummary():

    def GetResources(self):
        return {'Pixmap': os.path.join(P.AFC_PATH_ICON, 'summary.svg'),
                'Accel': 'S',
                'MenuText': FreeCAD.Qt.translate(
                    'addFC', 'Summary'),
                'ToolTip': FreeCAD.Qt.translate(
                    'addFC', 'Information about selected elements')}

    def Activated(self):
        f = os.path.join(P.AFC_PATH, 'utils', 'addFC_Summary.py')
        loader = importlib.machinery.SourceFileLoader('addFC_Summary', f)
        _ = loader.load_module()
        return

    def IsActive(self): return True if FreeCAD.ActiveDocument else False


FreeCAD.Gui.addCommand('AddFCSummary', AddFCSummary())
