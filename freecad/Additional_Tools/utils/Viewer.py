# -*- coding: utf-8 -*-
# Copyright 2025 Golodnikov Sergey


from PySide import QtGui, QtCore
from string import Template
import addFC_Logger as Logger
import addFC_Preference as P
import base64
import FreeCAD
import ImportGui
import os
import Part
import tempfile


ad = FreeCAD.ActiveDocument


mv_src = 'https://ajax.googleapis.com/ajax/libs/model-viewer/' \
    '4.0.0/model-viewer.min.js'

mv_template_css_add = """
    menu {
      display: block;
      left: 20px;
      margin: 0;
      position: absolute;
      top: 40px;
      z-index: 2;
    }
    menu label {
      cursor: pointer;
    }
    input[type="checkbox"] {
      cursor: pointer;
      margin-right: 6px;
    }
    .hotspot {
      background-color: black;
      border-radius: 4px;
      border: none;
      box-sizing: border-box;
      color: white;
      display: none;
      font-size: 12px;
      opacity: 0.2;
      padding: 4px 8px;
      white-space: nowrap;
    }
    .hotspot:hover {
      opacity: 1;
    }
    :not(:defined)>* {
      display: none;
    }"""

mv_ths = FreeCAD.Qt.translate('addFC', 'Display element names')

mv_template_menu = """
    <menu>
      <label>
        <input type="checkbox" id="hotspots" onclick="toggleHotspots()">$ths
      </label>
    </menu>"""

mv_template_script = """
    <script>
      function toggleHotspots() {
        const hotspots = document.querySelectorAll('.hotspot');
        hotspots.forEach(hotspot => {
          if (document.getElementById('hotspots').checked) {
            hotspot.style.display = 'block';
          } else {
            hotspot.style.display = 'none';
          }
        });
      }
      toggleHotspots();
    </script>"""

mv_template = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>$title</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      user-select: none;
    }
    h1 {
      display: block;
      font-size: 24px;
      left: 0;
      margin-top: 10px;
      position: absolute;
      text-align: center;
      top: 0;
      width: 100vw;
      z-index: 2;
    }
    model-viewer {
      height: 100vh;
      left: 0;
      position: absolute;
      top: 0;
      width: 100vw;
      z-index: 1;
    }$css_add
  </style>
  <script type="module" src="$mv_src"></script>
</head>
  <body>
    <h1>$label</h1>$menu
    <model-viewer
      alt="$label"
      camera-controls
      touch-action="pan-y"
      shadow-intensity="1"
      shadow-softness="1"
      camera-orbit="45deg 55deg 8m"
      tone-mapping="agx"
      exposure="0.5"
      src="data:model/gltf-binary;base64,$glb">$hotspots
    </model-viewer>$script
  </body>
</html>"""

# environment-image="data:image/jpeg;base64,$hdr"

hotspot = '      <button class="hotspot" slot="hotspot-$mark" ' \
    'data-position="$position" data-normal="$normal">$id</button>'


class Viewer():

    export_formats = (
        'HTML (model-viewer)',
    )

    pref_str = 'User parameter:BaseApp/Preferences/Document'
    duplicate = FreeCAD.ParamGet(pref_str).GetBool('DuplicateLabels')

    def __init__(self):
        self.form = FreeCAD.Gui.PySideUic.loadUi(
            os.path.join(os.path.dirname(__file__), 'Viewer.ui'))

        prop = P.pref_properties

        self.form.comboBoxEF.addItems(self.export_formats)

        model = QtGui.QStandardItemModel()
        self.form.listView.setModel(model)
        types = list(prop['Type'][2])
        for i in types:
            if i != '-':
                item = QtGui.QStandardItem(i)
                item.setCheckable(True)
                item.setCheckState(QtCore.Qt.Checked)
                model.appendRow(item)

        def toggle_uno(v):
            if v == 0:
                self.form.checkBoxEONStrict.setChecked(False)
                self.form.checkBoxEONStrict.setEnabled(False)
            else:
                self.form.checkBoxEONStrict.setEnabled(True)
            v = self.form.checkBoxEONStrict.isChecked()
            self.form.listView.setEnabled(False if v == 0 else True)
        toggle_uno(0)
        self.form.checkBoxEON.stateChanged.connect(toggle_uno)

        def toggle_dos(v):
            self.form.listView.setEnabled(False if v == 0 else True)
        toggle_dos(0)
        self.form.checkBoxEONStrict.stateChanged.connect(toggle_dos)

        def export():
            self.form.error.setText('')
            selection = FreeCAD.Gui.Selection.getSelectionEx('')

            if len(selection) < 1:
                self.form.error.setText(FreeCAD.Qt.translate(
                    'addFC', 'First you need to select the objects!'))
                return

            match self.form.comboBoxEF.currentText():
                case 'HTML (model-viewer)':
                    if self.form.checkBoxEON.isChecked():
                        forbidden = []
                        for index in range(model.rowCount()):
                            item = model.item(index)
                            if item.checkState() != QtCore.Qt.Checked:
                                forbidden.append(item.text())
                        self.duplicates_allow()
                        try:
                            strict = self.form.checkBoxEONStrict.isChecked()
                            mv_export(selection, strict, forbidden)
                        except BaseException as exception:
                            Logger.error(str(exception))
                        self.duplicate_default()
                    else:
                        try:
                            mv_export_simple(selection)
                        except BaseException as exception:
                            Logger.error(str(exception))
            FreeCAD.Gui.Control.closeDialog()

        self.form.pushButtonExport.clicked.connect(export)

    def duplicates_allow(self):
        FreeCAD.ParamGet(self.pref_str).SetBool(
            'DuplicateLabels', True)

    def duplicate_default(self):
        FreeCAD.ParamGet(self.pref_str).SetBool(
            'DuplicateLabels', self.duplicate)


viewer = Viewer()
FreeCAD.Gui.Control.showDialog(viewer)


# ------------------------------------------------------------------------------


def mv_export_simple(selection):
    path_dir = tempfile.TemporaryDirectory()
    path_glb = os.path.join(path_dir.name, 'viewer.glb')

    objects, labels = [], []

    for s in selection:
        objects.append(s.Object)
        labels.append(s.Object.Label)

    title = objects[0].Label
    label = ', '.join(labels)

    ImportGui.export(objects, path_glb)

    file = open(path_glb, 'rb')
    data = base64.b64encode(file.read())
    file.close()
    glb = data.decode('utf-8')

    path_dir.cleanup()

    tpl = Template(mv_template)
    result = tpl.substitute({
        'title': title,
        'css_add': '',
        'mv_src': mv_src,
        'label': label,
        'menu': '',
        'glb': glb,
        'hotspots': '',
        'script': '',
    })

    fd = QtGui.QFileDialog()
    fd.setDefaultSuffix('html')
    fd.selectFile(title + '.html')
    fd.setAcceptMode(QtGui.QFileDialog.AcceptSave)
    fd.setNameFilters(['HTML (*.html)'])
    if fd.exec_() == QtGui.QDialog.Accepted:
        path = fd.selectedFiles()[0]
        if path == '':
            path = 'viewer.html'
        file = open(path, 'w')
        file.write(result)
        file.close()
    else:
        return


# ------------------------------------------------------------------------------


def mv_export(selection, strict, forbidden):
    path_dir = tempfile.TemporaryDirectory()
    path_stp = os.path.join(path_dir.name, 'viewer.step')
    path_glb = os.path.join(path_dir.name, 'viewer.glb')

    objects, labels, hotspots = [], [], []

    for s in selection:
        objects.append(s.Object)
        labels.append(s.Object.Label)

    title = objects[0].Label
    label = ', '.join(labels)

    # export & import: step
    ImportGui.export(objects, path_stp)
    del objects
    doc_step = FreeCAD.newDocument(name='step', label='step', hidden=True)
    ImportGui.insert(path_stp, doc_step.Name)
    doc_step.recompute()

    # dissection
    doc_copy = FreeCAD.newDocument(name='copy', label='copy', hidden=True)

    for obj in doc_step.findObjects('Part::Feature'):

        if strict:
            id_export, id_obj = False, obj.Label
            for doc in FreeCAD.listDocuments():
                for i in FreeCAD.getDocument(doc).findObjects(Label=id_obj):
                    if hasattr(i, 'Add_Name'):
                        id_export, id_obj = True, i.Add_Name
                    if hasattr(i, 'Add_Type'):
                        if i.Add_Type in forbidden:
                            id_export = False
        else:
            id_export, id_obj = True, obj.Label

        s = Part.getShape(obj, needSubElement=False, refine=False)
        o = doc_copy.addObject('Part::Feature', 'obj')
        o.Shape = s
        o.Label = obj.Label
        o.ViewObject.LineColor = obj.ViewObject.ShapeColor
        o.ViewObject.PointColor = obj.ViewObject.PointColor
        o.ViewObject.ShapeColor = obj.ViewObject.ShapeColor
        o.Placement = obj.getGlobalPlacement()

        o.recompute()

        if id_export:
            pos = ' '.join((
                str(o.Shape.CenterOfGravity.x / 1000),
                str(o.Shape.CenterOfGravity.z / 1000),
                str(-o.Shape.CenterOfGravity.y / 1000),
            ))
            hotspots.append(Template(hotspot).substitute({
                'mark': o.Name,
                'position': pos,
                'normal': '0 0 0',
                'id': id_obj,
            }))

    doc_copy.recompute()

    # export & encoding: glb
    ImportGui.export(doc_copy.Objects, path_glb)
    file = open(path_glb, 'rb')
    data = base64.b64encode(file.read())
    file.close()
    glb = data.decode('utf-8')

    # cleanup
    path_dir.cleanup()
    doc_step.clearDocument()
    doc_copy.clearDocument()
    FreeCAD.closeDocument(doc_step.Name)
    FreeCAD.closeDocument(doc_copy.Name)
    FreeCAD.setActiveDocument(ad.Name)

    menu = Template(mv_template_menu).substitute({'ths': mv_ths})

    tpl = Template(mv_template)
    result = tpl.substitute({
        'title': title,
        'css_add': mv_template_css_add,
        'mv_src': mv_src,
        'label': label,
        'menu': menu,
        'glb': glb,
        'hotspots': '\n'.join(hotspots),
        'script': mv_template_script,
    })

    fd = QtGui.QFileDialog()
    fd.setDefaultSuffix('html')
    fd.selectFile(title + '.html')
    fd.setAcceptMode(QtGui.QFileDialog.AcceptSave)
    fd.setNameFilters(['HTML (*.html)'])
    if fd.exec_() == QtGui.QDialog.Accepted:
        path = fd.selectedFiles()[0]
        if path == '':
            path = 'viewer.html'
        file = open(path, 'w')
        file.write(result)
        file.close()

    return
