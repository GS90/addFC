# -*- coding: utf-8 -*-
# Copyright 2025 Golodnikov Sergey


import FreeCAD


ad = FreeCAD.ActiveDocument


group = ad.getObject('Isolation')
if group is None:
    group = ad.addObject('App::DocumentObjectGroup', 'Isolation')
    group.addProperty('App::PropertyPythonObject', 'Isolation', 'Base')
    hidden = False
else:
    hidden = True


def hide():
    selection = FreeCAD.Gui.Selection.getSelectionEx('')
    if len(selection) == 0:
        return

    links, link = {}, None

    _selection = FreeCAD.Gui.Selection.getSelectionEx('', 0)[0]
    sen = _selection.SubElementNames[0]
    sol = _selection.Object.getSubObjectList(sen)
    if len(sol) > 1:
        if sol[-2].TypeId == 'App::Link':
            link = sol[-2]

    for s in sol:
        if s.TypeId == 'App::Link':  # todo: guess which link is correct...
            dn = s.Document.Name
            if dn in links:
                links[dn].append(s.Name)
            else:
                links[dn] = [s.Name,]

    target = {}

    for s in selection:
        dn = s.DocumentName
        if link is not None:
            obj, link = link, None
        else:
            if s.Object.TypeId == 'Part::FeaturePython':  # todo: why?
                obj = s.Object
            else:
                obj = s.Object.InList[0] if s.HasSubObjects else s.Object
        if s.DocumentName in target:
            target[dn].append(obj.Name)
        else:
            target[dn] = [obj.Name,]

    heap = []

    def visibility(dn, on):
        if dn in target:
            for o in target[dn]:
                if o == on:
                    return True
        heap.append((dn, on))
        return False

    for i in obj.InListRecursive:
        dn = i.Document.Name
        doc = FreeCAD.getDocument(dn)
        for obj in doc.findObjects():
            if not obj.Visibility:
                continue
            on = obj.Name
            if on == i.Name:
                continue
            if hasattr(obj, 'Tip'):
                obj.Visibility = visibility(dn, on)
            else:
                match obj.TypeId:
                    case 'Part::FeaturePython':
                        obj.Visibility = visibility(dn, on)
                    case 'App::Link':
                        if dn in links:
                            if on not in links[dn]:
                                heap.append((dn, on))
                                obj.Visibility = False
                        else:
                            heap.append((dn, on))
                            obj.Visibility = False

    group.Isolation = heap


def show():
    isolation = group.Isolation
    if isolation is not None:
        for i in isolation:
            FreeCAD.getDocument(i[0]).getObject(i[1]).Visibility = True
    ad.removeObject('Isolation')


show() if hidden else hide()
