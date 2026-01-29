# addFC; additional tools for FreeCAD
#
# Copyright 2024-2026 Golodnikov Sergey
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


from PySide import QtGui
import FreeCAD
import os
import re
import shutil
import subprocess
import sys

from Data import video_options, video_pref_std
import Logger
import Preference as P


DIGIT = re.compile('\\d+')

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


# required for correct recalculation of configuration tables in FreeCAD 0.21
def recompute_configuration_tables() -> None:
    for doc in FreeCAD.listDocuments():
        objects = FreeCAD.getDocument(doc).findObjects('Spreadsheet::Sheet')
        for obj in objects:
            for e in obj.ExpressionEngine:
                s = e[0][len('.cells.Bind.'):].split('.')[0]
                d = re.search(DIGIT, s)
                if d is not None:
                    d = d.group(0)
                    c = ALPHABET[ALPHABET.index(s.replace(d, '')) - 1] + d
                    obj.recomputeCells(c)


def error(message: str, header: str = 'ERROR') -> None:
    QtGui.QMessageBox.critical(
        None,
        header,
        message,
        QtGui.QMessageBox.StandardButton.Ok,
    )


def open(path: str, fallback: bool) -> subprocess.CompletedProcess:
    cp = None
    match sys.platform:
        case 'win32': cp = subprocess.run(['explorer', path])
        case 'darwin': cp = subprocess.run(['open', path])
        case _: cp = subprocess.run(['xdg-open', path])
    if cp.returncode != 0 and fallback:
        cp = open(os.path.dirname(path), False)
    return cp


# ------------------------------------------------------------------------------


def video_export_settings():
    form = FreeCAD.Gui.PySideUic.loadUi(
        os.path.join(P.AFC_DIR, 'toolkit', 'Video_set.ui'))

    form.comboBoxSize.clear()
    form.comboBoxBackground.clear()
    form.comboBoxMethod.clear()
    form.comboBoxImageFormat.clear()

    form.comboBoxSize.addItems(video_options['size'].keys())
    form.comboBoxBackground.addItems(video_options['background'])
    form.comboBoxMethod.addItems(video_options['method'].keys())
    form.comboBoxImageFormat.addItems(video_options['image_format'].keys())

    def resize(size) -> None:
        if size not in video_options['size']:
            size = '1080p (FHD)'
        form.comboBoxSize.setCurrentText(size)
        s = video_options['size'][size]
        form.spinBoxWidth.setValue(s[0])
        form.spinBoxHeight.setValue(s[1])
    form.comboBoxSize.currentTextChanged.connect(resize)

    # es.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    form.show()

    video_pref = P.load_pref(P.PATH_VIDEO, video_pref_std)

    resize(video_pref['size'])

    form.comboBoxBackground.setCurrentText(video_pref['background'])
    form.comboBoxMethod.setCurrentText(video_pref['method'])
    for k, v in video_options['image_format'].items():
        if v == video_pref['image_format']:
            form.comboBoxImageFormat.setCurrentText(k)
            break
    form.spinBoxFramerate.setValue(video_pref['framerate'])
    form.labelDir.setText(f"... {os.path.basename(video_pref['export_dir'])}")

    def directory() -> None:
        d = os.path.normcase(QtGui.QFileDialog.getExistingDirectory())
        if d != '':
            video_pref['export_dir'] = d
            video_pref['export_storyboard'] = os.path.join(d, '_storyboard')
            form.labelDir.setText(f'... {os.path.basename(d)}')
    form.pushButtonDir.clicked.connect(directory)

    def apply() -> None:
        video_pref['size'] = form.comboBoxSize.currentText()
        video_pref['width'] = form.spinBoxWidth.value()
        video_pref['height'] = form.spinBoxHeight.value()
        video_pref['background'] = form.comboBoxBackground.currentText()
        video_pref['method'] = form.comboBoxMethod.currentText()
        video_pref['image_format'] = video_options['image_format'][
            form.comboBoxImageFormat.currentText()]
        video_pref['framerate'] = form.spinBoxFramerate.value()
        P.save_pref(P.PATH_VIDEO, video_pref)
        export_method = video_options['method'][video_pref['method']]
        ps = 'User parameter:BaseApp/Preferences/View'
        FreeCAD.ParamGet(ps).SetString('SavePicture', export_method)
        form.close()
    form.apply.clicked.connect(apply)

    return video_pref


def video_make(title: str, postfix: str) -> str | None:
    video_pref = P.load_pref(P.PATH_VIDEO, video_pref_std)
    storyboard = video_pref['export_storyboard']
    file = f'../{title}{postfix}.mkv'
    result = subprocess.run([
        'ffmpeg',
        '-framerate', str(video_pref['framerate']),
        '-pattern_type', 'glob',
        '-y', '-i', '*' + video_pref['image_format'],
        '-codec', 'copy', file],
        cwd=storyboard, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if '_storyboard' in storyboard:
        shutil.rmtree(storyboard)
    if result.returncode != 0:
        Logger.error(result.stderr.decode('utf-8').strip())
        return None
    else:
        Logger.info('video creation successful')
        return os.path.join(os.path.dirname(storyboard), file[3:])
