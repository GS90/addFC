# -*- coding: utf-8 -*-
# Copyright 2025 Golodnikov Sergey


import addFC_Logger as Logger
import FreeCAD


ad = FreeCAD.ActiveDocument


FEATURES = ('Part::Feature', 'Part::FeaturePython')
CONTAINERS = ('App::Part', 'Assembly::AssemblyObject')


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
    if _selection.HasSubObjects:
        sen = _selection.SubElementNames[0]
        sol = _selection.Object.getSubObjectList(sen)
        if len(sol) > 1:
            if sol[-2].TypeId == 'App::Link':
                link = sol[-2]
        for i in sol:
            if i.TypeId == 'App::Link':
                # todo: guess which link is correct...
                dn = i.Document.Name
                if dn in links:
                    links[dn].append(i.Name)
                else:
                    links[dn] = [i.Name,]

    target = {}

    def insert(dn, on):
        if dn in target:
            if on not in target[dn]:
                target[dn].append(on)
        else:
            target[dn] = [on,]

    for s in selection:
        dn, obj = s.DocumentName, None

        if link is not None:
            obj, link = link, None

        elif not s.HasSubObjects:
            obj = s.Object
            if obj.TypeId in CONTAINERS:
                for i in obj.Group:
                    insert(dn, i.Name)
            else:
                if len(obj.InList) > 0:
                    if obj.InList[0].TypeId == 'PartDesign::Body':
                        insert(dn, obj.InList[0].Name)

        else:
            if s.Object.TypeId in FEATURES:
                obj = s.Object
            else:
                if s.HasSubObjects:
                    if len(s.Object.InList) > 0:
                        obj = s.Object.InList[0]
                    else:
                        obj = s.Object
                else:
                    obj = s.Object

        if obj is None:
            Logger.warning('Isolation: the object is not defined')
            return
        insert(dn, obj.Name)

    heap = []

    def visibility(dn, on):
        if dn in target:
            for o in target[dn]:
                if o == on:
                    return True
        heap.append((dn, on))
        return False

    if len(obj.InListRecursive) == 0:
        inList = [obj,]
    else:
        inList = obj.InListRecursive

    for i in inList:
        dn = i.Document.Name
        doc = FreeCAD.getDocument(dn)
        for obj in doc.findObjects():
            if not obj.Visibility:
                continue
            on = obj.Name
            if on == i.Name:
                if i.TypeId == 'App::Link':
                    if on == i.LinkedObject.Name:
                        continue
                else:
                    continue
            if hasattr(obj, 'Tip'):
                obj.Visibility = visibility(dn, on)
            else:
                match obj.TypeId:
                    case 'Part::Feature' | 'Part::FeaturePython':
                        obj.Visibility = visibility(dn, on)
                    case 'App::Link':
                        if dn in links:
                            if on not in links[dn]:
                                heap.append((dn, on))
                                obj.Visibility = False
                        else:
                            heap.append((dn, on))
                            obj.Visibility = False
                    case _:
                        if 'Part::' in obj.TypeId:
                            obj.Visibility = visibility(dn, on)

    group.Isolation = heap


def show():
    isolation = group.Isolation
    if isolation is not None:
        for i in isolation:
            FreeCAD.getDocument(i[0]).getObject(i[1]).Visibility = True
    ad.removeObject('Isolation')


show() if hidden else hide()
