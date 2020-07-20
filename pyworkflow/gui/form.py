# **************************************************************************
# *
# * Authors:     J.M. De la Rosa Trevin (delarosatrevin@scilifelab.se) [1]
# *              Jose Gutierrez (jose.gutierrez@cnb.csic.es) [2]
# *
# * [1] SciLifeLab, Stockholm University
# * [2] Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program.  If not, see <https://www.gnu.org/licenses/>.
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************
"""
This modules implements the automatic
creation of protocol form GUI from its
params definition.
"""
import os
import tkinter as tk
import tkinter.ttk as ttk
import webbrowser
from collections import OrderedDict
from datetime import datetime

import pyworkflow as pw
import pyworkflow.utils as pwutils
import pyworkflow.object as pwobj
import pyworkflow.protocol as pwprot
from pyworkflow.mapper import Mapper
from pyworkflow.viewer import DESKTOP_TKINTER
from pyworkflow.protocol.constants import MODE_RESTART

from . import gui
from pyworkflow.gui.project.utils import getStatusColorFromRun
from .gui import configureWeigths, Window
from .browser import FileBrowserWindow
from .widgets import Button, HotButton, IconButton
from .dialog import (showInfo, showError, showWarning, EditObjectDialog,
                     ListDialog, askYesNo, Dialog,RESULT_CANCEL,
                     askSingleAllCancel, RESULT_RUN_ALL, RESULT_RUN_SINGLE)
from .canvas import Canvas
from .tree import TreeProvider, BoundTree
from .text import Text
from ..project.project import ModificationNotAllowedException

THREADS = 'Threads'
MPI = 'MPI'


# ----------------- Variables wrappers around more complex objects ------------
class BoolVar:
    """Wrapper around tk.IntVar"""
    def __init__(self, value=None):
        self.tkVar = tk.IntVar()
        self.set(value)
        self.trace = self.tkVar.trace
        
    def set(self, value):
        if value is None:
            self.tkVar.set(-1)
        elif value:
            self.tkVar.set(1)
        else:
            self.tkVar.set(0)    
            
    def get(self):
        if self.tkVar.get() == -1:
            return None

        return self.tkVar.get() == 1    
    
    
class PointerVar:
    """ Wrapper around tk.StringVar to hold object pointers. """
    def __init__(self, protocol):
        self.tkVar = tk.StringVar()
        self._pointer = pwobj.Pointer()
        self.trace = self.tkVar.trace
        self._protocol = protocol
        
    def set(self, value):
        if value is None:
            value = pwobj.Pointer(None)
        if not isinstance(value, pwobj.Pointer):
            raise Exception('Pointer var should be used with pointers!!!\n'
                            ' Passing: %s, type: %s' % (value, type(value)))
        self._pointer.copy(value)
            
        label, _ = getPointerLabelAndInfo(self._pointer,
                                          self._protocol.getMapper())
        self.tkVar.set(label)   
     
    def get(self):
        return self._pointer
    
    def getPointer(self):
        return self._pointer
    
    def remove(self):
        self.set(None)


class ScalarWithPointerVar(tk.StringVar):
    """ tk.StringVar to hold object pointers and scalars. """

    def __init__(self, protocol, changeListener):

        self._pointer = None
        self._protocol = protocol
        self.inInit = True
        tk.StringVar.__init__(self)
        self.inInit = False
        self.insideSet = False
        self.listeners = []

        # Register inner listener
        tk.StringVar.trace(self, 'w', self._listenDirectEntryChanges)
        self.trace('w', changeListener)

    def trace(self, mode, callback):

        # let's ignore the mode for now all are "w"
        self.listeners.append(callback)

    def _listenDirectEntryChanges(self, *args):
        """ We need to be aware of any change done in the entry.
        When the user type anything, the set is not invoked.
        We need to distinguish when this is invoked from the set(),
        in this case we do nothing"""
        if not self.insideSet:
            self._pointer = None

        # Call the listeners
        for callback in self.listeners:
            callback(*args)

    def set(self, value):
        # Flag we are inside the set method to avoid
        # triggering _listenDirectEntryChanges
        self.insideSet = True
        if self.inInit:
            return

        # If a scalar is being set
        if not isinstance(value, pwobj.Pointer):

            # Reset the pointer
            self._pointer = None
            label = value
        # it's a pointer
        else:

            self._pointer = value
            label, _ = getPointerLabelAndInfo(self._pointer,
                                              self._protocol.getMapper())

        tk.StringVar.set(self, label)

        # Cancel the flag.
        self.insideSet = False

    def get(self):

        if self.hasPointer():
            return self._pointer
        else:
            return tk.StringVar.get(self)

    def hasPointer(self):
        return self._pointer is not None

    def getPointer(self):
        return self._pointer if self.hasPointer() else None

    
class MultiPointerVar:
    """
    Wrapper around tk.StringVar to hold object pointers.
    This class is related with MultiPointerTreeProvider, which
    stores the list of pointed objects and have the logic to
    add and remove from the list.
    """
    def __init__(self, provider, tree):
        # keep a reference to tree provider to add or remove objects
        self.provider = provider
        self.tree = tree
        self.tkVar = tk.StringVar()
        self.trace = self.tkVar.trace
        
    def _updateObjectsList(self):
        self.tkVar.set(str(datetime.now()))  # cause a trace to notify changes
        self.tree.update()  # Update the tkinter tree gui
        
    def set(self, value):
        if isinstance(value, pwobj.Object) or isinstance(value, list):
            self.provider.addObject(value)
            self._updateObjectsList()
          
    def remove(self):
        """ Remove first element selected. """
        values = self.getSelectedObjects()
        for v in values:
            self.provider.removeObject(v)
        self._updateObjectsList()
        
    def getSelectedObjects(self):
        return self.tree.getSelectedObjects()
        
    def get(self):
        return self.provider.getObjects()
    
    
class MultiPointerTreeProvider(TreeProvider):
    """
    Store several pointers to objects to be used in a BoundTree and as
    storage from MultiPointerVar. 
    """
    def __init__(self, mapper):
        TreeProvider.__init__(self)
        self._objectDict = OrderedDict()
        self._mapper = mapper
        
    def _getObjKey(self, obj):
        """ 
        This method will create an unique key to 
        identify the pointed object. The objId is not
        enough because of pointers and extended values
        to items inside a set or properties.
        """
        strId = None
        
        if isinstance(obj, pwobj.Pointer):
            
            if obj.hasValue():
                strId = obj.getObjValue().strId()
            
                if obj.hasExtended():
                    strId += obj.getExtended()
                
        else:
            strId = obj.strId()
            
        if strId is None:
            raise Exception('ERROR: strId is None for MultiPointerTreeProvider!!!')
        
        return strId
        
    def _getObjPointer(self, obj):
        """ If obj is a pointer return obj. If not
        create a pointer and return it.
        """
        if isinstance(obj, pwobj.Pointer):
            ptr = obj
        else:
            ptr = pwobj.Pointer(value=obj)
            
        return ptr

    def _addObject(self, obj):
        strId = self._getObjKey(obj)
        ptr = self._getObjPointer(obj)
        ptr._strId = strId
        
        self._objectDict[strId] = ptr
           
    def addObject(self, obj):
        if isinstance(obj, list):
            for o in obj:
                self._addObject(o)
        else:
            self._addObject(obj) 
        
    def removeObject(self, obj):
        strId = self._getObjKey(obj)
        if strId in self._objectDict:
            del self._objectDict[strId]
     
    def getObjects(self):
        return list(self._objectDict.values())
        
    def getColumns(self):
        return [('Object', 250), ('Info', 150)]
    
    def getObjectInfo(self, obj):
        label, info = getPointerLabelAndInfo(obj, self._mapper)
        return {'key': obj._strId, 'text': label, 'values': ('  ' + info,)}
   
   
class ComboVar:
    """ Create a variable that display strings (for combobox)
    but the values are integers (for the underlying EnumParam).
    """
    def __init__(self, enum):
        self.tkVar = tk.StringVar()
        self.enum = enum
        self.value = None
        self.trace = self.tkVar.trace
        
    def set(self, value):
        self.value = value
        if isinstance(value, int):
            # self.enum.choices is an object of type odict_values, which
            # cannot be indexed, so a type cast to list is required
            self.tkVar.set(list(self.enum.choices)[value])
        else:
            self.tkVar.set(value)  # also support string values
                    
    def get(self):
        v = self.tkVar.get()
        self.value = None
        for i, c in enumerate(list(self.enum.choices)):
            if c == v:
                self.value = i
            
        return self.value         


class TextVar:
    """Wrapper around tk.StringVar to bind the value of a Text widget. """
    def __init__(self, text, value=''):
        """
        Params:
            text: Text widget associated with this variable.
            value: initial value for the widget.
            """
        self.text = text
        text.bind('<KeyRelease>', self._onTextChanged)
        self.tkVar = tk.StringVar()
        self.set(value)
        self.trace = self.tkVar.trace

    def set(self, value):
        self.tkVar.set(value)
        if value is None:
            value = ''
        self.text.setText(value)

    def get(self):
        return self.tkVar.get()

    def _onTextChanged(self, e=None):
        self.tkVar.set(self.text.getText().strip())        


# ---------------- Some used providers for the TREES --------------------------
class ProtocolClassTreeProvider(TreeProvider):
    """Will implement the methods to provide the object info
    of subclasses objects(of className) found by mapper"""
    def __init__(self, protocolClassName):
        TreeProvider.__init__(self)
        self.protocolClassName = protocolClassName
     
    def getObjects(self):
        # FIXME: Maybe find a way to pass the current domain?
        # FIXME: Or we just rely on the one defined in pw.Config?
        domain = pw.Config.getDomain()
        return [pwobj.String(s)
                for s in domain.findSubClasses(domain.getProtocols(),
                                               self.protocolClassName).keys()]
        
    def getColumns(self):
        return [('Protocol', 250)]
    
    def getObjectInfo(self, obj):
        return {'key': obj.get(),
                'values': (obj.get(),)}


def getPointerLabelAndInfo(pobj, mapper):
    """ 
    Return a string to represent selected objects
    that are stored by pointers.
    This function will be used from PointerVar and MultiPointerVar.
    """
    label = getObjectLabel(pobj, mapper)
    obj = pobj.get()
    info = str(obj) if obj is not None else ''
    
    return label, info
    
    
def getObjectLabel(pobj, mapper):
    """ We will try to show in the list the string representation
    that is more readable for the user to pick the desired object.
    """
    # FIXME: maybe we can remove this function
    obj = pobj.get()
    prot = pobj.getObjValue()
        
    if prot is None:
        label = ''
    elif obj is None:
        label = '%s.%s' % (prot.getRunName(), pobj.getExtended())
    else:
        # This is for backward compatibility
        # Now always the pobj.getObjValue() should
        # be the protocol
        extended = pobj.getExtended() if isinstance(prot, pwprot.Protocol) else ''
        while not isinstance(prot, pwprot.Protocol):
            extended = '%s.%s' % (prot.getLastName(), extended)
            prot = mapper.getParent(prot)
        label = obj.getObjLabel().strip()
        if not len(label):
            label = '%s.%s' % (prot.getRunName(), extended)

    label = label.replace("\n", " ")
    # if obj is not None:
    #     return label + " (%d)" % obj.getObjId()
    return label

    
class SubclassesTreeProvider(TreeProvider):
    """Will implement the methods to provide the object info
    of subclasses objects(of className) found by mapper"""
    CREATION_COLUMN = 'Creation'
    INFO_COLUMN = 'Info'
    ID_COLUMN = 'Protocol Id'

    def __init__(self, protocol, pointerParam, selected=None):
        TreeProvider.__init__(self, sortingColumnName=self.CREATION_COLUMN,
                              sortingAscending=False)

        self.param = pointerParam
        self.selected = selected  # FIXME
        self.selectedDict = {}
        self.protocol = protocol
        self.mapper = protocol.mapper
        self.maxNum = 200

    def getObjects(self):
        # Retrieve all objects of type className
        project = self.protocol.getProject()
        className = self.param.pointerClass.get()
        condition = self.param.pointerCondition.get()
        # Get the classes that are valid as input object in this Domain
        domain = pw.Config.getDomain()
        classes = [domain.findClass(c.strip()) for c in className.split(",")]
        objects = []

        # Do no refresh again and take the runs that are loaded
        # already in the project. We will prefer to save time
        # here than have the 'very last' version of the runs and objects
        runs = project.getRuns(refresh=False)
        
        for prot in runs:
            # Make sure we don't include previous output of the same 
            # protocol, it will cause a recursive loop
            if prot.getObjId() != self.protocol.getObjId():
                # Check if the protocol itself is one of the desired classes
                if any(issubclass(prot.getClass(), c) for c in classes):
                    p = pwobj.Pointer(prot)
                    objects.append(p)
                
                try:
                    # paramName and attr must be set to None 
                    # Otherwise, if a protocol has failed and the corresponding output object of type XX does not exist 
                    # any other protocol that uses objects of type XX as input will not be able to choose then using
                    # the magnifier glass (object selector of type XX)
                    paramName = None  
                    attr = None
                    for paramName, attr in prot.iterOutputAttributes():
                        print(paramName)
                        print(attr.getObjCreation())
                        def _checkParam(paramName, attr):
                            # If attr is a sub-classes of any desired one, add it to the list
                            # we should also check if there is a condition, the object
                            # must comply with the condition
                            p = None
                            if (any(isinstance(attr, c) for c in classes) and
                                (not condition or
                                 attr.evalCondition(condition))):
                                p = pwobj.Pointer(prot, extended=paramName)
                                p._allowsSelection = True
                                objects.append(p)

                            # JMRT: For all sets, we don't want to include the
                            # subitems here for performance reasons (e.g SetOfParticles)
                            # Thus, a Set class can define EXPOSE_ITEMS = True
                            # to enable the inclusion of its items here
                            if getattr(attr, 'EXPOSE_ITEMS', False):
                                # If the ITEM type match any of the desired classes
                                # we will add some elements from the set
                                if (attr.ITEM_TYPE is not None and
                                   any(issubclass(attr.ITEM_TYPE, c) for c in classes)):
                                    if p is None:  # This means the set have not be added
                                        p = pwobj.Pointer(prot, extended=paramName)
                                        p._allowsSelection = False
                                        objects.append(p)
                                    # Add each item on the set to the list of objects
                                    try:
                                        for i, item in enumerate(attr):
                                            if i == self.maxNum:  # Only load up to NUM particles
                                                break
                                            pi = pwobj.Pointer(prot, extended=paramName)
                                            pi.addExtended(item.getObjId())
                                            pi._parentObject = p
                                            objects.append(pi)
                                    except Exception as ex:
                                        print("Error loading items from:")
                                        print("  protocol: %s, attribute: %s"
                                              % (prot.getRunName(), paramName))
                                        print("  dbfile: ",
                                              os.path.join(project.getPath(),
                                                           attr.getFileName()))
                                        print(ex)

                        _checkParam(paramName, attr)
                        # The following is a dirty fix for the RCT case where there
                        # are inner output, maybe we should consider extend this for
                        # in a more general manner
                        for subParam in ['_untilted', '_tilted']:
                            if hasattr(attr, subParam):
                                _checkParam('%s.%s' % (paramName, subParam),
                                            getattr(attr, subParam))
                except Exception as e:
                    print("Cannot read attributes for %s (%s)" % (prot.getClass(), e))

        # Sort objects before returning them
        self._sortObjects(objects)

        return objects

    def _sortObjects(self, objects):
        objects.sort(key=self.objectKey, reverse=not self.isSortingAscending())

    def objectKey(self, pobj):

        obj = self._getParentObject(pobj, pobj)

        if self._sortingColumnName == SubclassesTreeProvider.CREATION_COLUMN:
            return self._getObjectCreation(obj.get())
        elif self._sortingColumnName == SubclassesTreeProvider.INFO_COLUMN:
            return self._getObjectInfoValue(obj.get())
        elif self._sortingColumnName == SubclassesTreeProvider.ID_COLUMN:
            return self._getObjectId(pobj)
        else:
            return self._getPointerLabel(obj)

    def getColumns(self):
        return [('Object', 300), (SubclassesTreeProvider.INFO_COLUMN, 250),
                (SubclassesTreeProvider.CREATION_COLUMN, 150),
                (SubclassesTreeProvider.ID_COLUMN, 100)]
    
    def isSelected(self, obj):
        """ Check if an object is selected or not. """
        if self.selected:
            for s in self.selected:
                if s and s.getObjId() == obj.getObjId():
                    return True
        return False

    @staticmethod
    def _getParentObject(pobj, default=None):
        return getattr(pobj, '_parentObject', default)

    def getObjectInfo(self, pobj):
        parent = self._getParentObject(pobj)

        # Get the label
        label = self._getPointerLabel(pobj, parent)
            
        obj = pobj.get()
        objId = pobj.getUniqueId()
        isSelected = objId in self.selectedDict
        self.selectedDict[objId] = True
            
        return {'key': objId, 'text': label,
                'values': (self._getObjectInfoValue(obj),
                           self._getObjectCreation(obj),
                           self._getObjectId(pobj)),
                'selected': isSelected, 'parent': parent}

    @staticmethod
    def _getObjectId(pobj):
        return pobj.getObjValue().getObjId()

    @staticmethod
    def _getObjectCreation(obj):

        return obj.getObjCreation() if obj.getObjCreation() else "Empty"

    @staticmethod
    def _getObjectInfoValue(obj):

        return str(obj).replace(obj.getClassName(), '')

    def _getPointerLabel(self, pobj, parent=None):

        # If parent is not provided, try to get it, it might have none.
        if parent is None:
            parent = self._getParentObject(pobj)

        # If there is no parent
        if parent is None:
            return getObjectLabel(pobj, self.mapper)
        else:  # This is an item coming from a set
            # If the object has label include the label
            if pobj.get().getObjLabel():
                return 'item %s - %s' % (pobj.get().strId(), pobj.get().getObjLabel())
            else:
                return 'item %s' % pobj.get().strId()

    def getObjectActions(self, pobj):
        obj = pobj.get()
        actions = []    
        domain = pw.Config.getDomain()
        viewers = domain.findViewers(obj.getClassName(), DESKTOP_TKINTER)
        proj = self.protocol.getProject()
        for v in viewers:
            actions.append(('Open with %s' % v.__name__, 
                            lambda: v(project=proj).visualize(obj)))
        return actions
    
    
# TODO: check if need to inherit from SubclassesTreeProvider
class RelationsTreeProvider(SubclassesTreeProvider):
    """Will implement the methods to provide the object info
    of subclasses objects(of className) found by mapper"""
    def __init__(self, protocol, relationParam, selected=None):
        SubclassesTreeProvider.__init__(self, protocol, relationParam, selected)
        self.item = protocol.getAttributeValue(relationParam.getAttributeName())
        self.direction = relationParam.getDirection()
        self.relationParam = relationParam
        
    def getObjects(self):
        objects = []
        if self.item is not None:
            project = self.protocol.getProject()
            for pobj in project.getRelatedObjects(self.relationParam.getName(),
                                                  self.item, self.direction,
                                                  refresh=True):
                objects.append(pobj.clone())

        # Sort objects
        self._sortObjects(objects)

        return objects


class ScalarTreeProvider(TreeProvider):
    """Will implement the methods to provide the object info
    of scalar outputs"""
    CREATION_COLUMN = 'Creation'
    INFO_COLUMN = 'Info'

    def __init__(self, protocol, scalarParam, selected=None):
        TreeProvider.__init__(self, sortingColumnName=self.CREATION_COLUMN,
                              sortingAscending=False)

        self.param = scalarParam
        self.selected = selected
        self.selectedDict = {}
        self.protocol = protocol
        self.mapper = protocol.mapper
        self.maxNum = 200

    def getObjects(self):
        # Retrieve all objects of type className
        project = self.protocol.getProject()
        className = self.param.paramClass
        # Get the classes that are valid as input object
        # em.findClass is very tight to the EMObjects...Since scalars are not
        # EM object can't be used unless we do something
        # For now this will work with exact class.
        classes = [className]
        objects = []

        # Do no refresh again and take the runs that are loaded
        # already in the project. We will prefer to save time
        # here than have the 'very last' version of the runs and objects
        runs = project.getRuns(refresh=False)

        for prot in runs:
            # Make sure we don't include previous output of the same
            # protocol, it will cause a recursive loop
            if prot.getObjId() != self.protocol.getObjId():

                for paramName, attr in prot.iterOutputAttributes():
                    def _checkParam(paramName, attr):
                        # If attr is a sub-classes of any desired one, add it to the list
                        # we should also check if there is a condition, the object
                        # must comply with the condition
                        p = None
                        if any(isinstance(attr, c) for c in classes):
                            p = pwobj.Pointer(prot, extended=paramName)
                            p._allowsSelection = True
                            objects.append(p)

                    _checkParam(paramName, attr)

        # Sort objects before returning them
        self._sortObjects(objects)

        return objects

    def _sortObjects(self, objects):
        objects.sort(key=self.objectKey, reverse=not self.isSortingAscending())

    def objectKey(self, pobj):

        obj = self._getParentObject(pobj, pobj)

        if self._sortingColumnName == ScalarTreeProvider.CREATION_COLUMN:
            return self._getObjectCreation(obj.get())
        elif self._sortingColumnName == ScalarTreeProvider.INFO_COLUMN:
            return self._getObjectInfoValue(obj.get())
        else:
            return self._getPointerLabel(obj)

    def getColumns(self):
        return [('Object', 300), (ScalarTreeProvider.INFO_COLUMN, 250),
                (ScalarTreeProvider.CREATION_COLUMN, 150)]

    def isSelected(self, obj):
        """ Check if an object is selected or not. """
        if self.selected:
            for s in self.selected:
                if s and s.getObjId() == obj.getObjId():
                    return True
        return False

    @staticmethod
    def _getParentObject(pobj, default=None):
        return getattr(pobj, '_parentObject', default)

    def getObjectInfo(self, pobj):
        parent = self._getParentObject(pobj)

        # Get the label
        label = self._getPointerLabel(pobj, parent)

        obj = pobj.get()
        objId = pobj.getUniqueId()

        isSelected = objId in self.selectedDict
        self.selectedDict[objId] = True

        return {'key': objId, 'text': label,
                'values': (self._getObjectInfoValue(obj),
                           self._getObjectCreation(obj)),
                'selected': isSelected, 'parent': parent}

    @staticmethod
    def _getObjectCreation(obj):

        return obj.getObjCreation()

    @staticmethod
    def _getObjectInfoValue(obj):

        return str(obj).replace(obj.getClassName(), '')

    def _getPointerLabel(self, pobj, parent=None):

        # If parent is not provided, try to get it, it might have none.
        if parent is None:
            parent = self._getParentObject(pobj)

        # If there is no parent
        if parent is None:
            return getObjectLabel(pobj, self.mapper)
        else:  # This is an item coming from a set
            # If the object has label include the label
            if pobj.get().getObjLabel():
                return 'item %s - %s' % (
                    pobj.get().strId(), pobj.get().getObjLabel())
            else:
                return 'item %s' % pobj.get().strId()


# --------------------- Other widgets ----------------------------------------
# http://tkinter.unpythonic.net/wiki/VerticalScrolledFrame


class VerticalScrolledFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)            

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)


class SectionFrame(tk.Frame):
    """This class will be used to create a frame for the Section
    That will have a header with red color and a content frame
    with white background
    """
    def __init__(self, master, label, callback=None, height=15, **args):
        headerBgColor = args.get('headerBgColor', gui.cfgButtonBgColor)
        if 'headerBgColor' in args:
            del args['headerBgColor']
        self.height = height
        tk.Frame.__init__(self, master, **args)
        configureWeigths(self, row=1)
        self._createHeader(label, headerBgColor)
        self._createContent()
        tk.Frame.grid(self, row=0, column=0, sticky="new")
        
    def _createHeader(self, label, bgColor):
        self.headerFrame = tk.Frame(self, bd=2, relief=tk.RAISED, bg=bgColor,
                                    name="sectionheaderframe")
        self.headerFrame.grid(row=0, column=0, sticky='new')
        configureWeigths(self.headerFrame)
        self.headerFrame.columnconfigure(1, weight=1)
        self.headerLabel = tk.Label(self.headerFrame, text=label, fg='white',
                                    bg=bgColor, name="sectionheaderlabel")
        self.headerLabel.grid(row=0, column=0, sticky='nw')
        
    def _createContent(self):
        canvasFrame = tk.Frame(self, name="sectioncontentframe")
        configureWeigths(canvasFrame)
        self.canvas = Canvas(canvasFrame, width=625, height=self.height,
                             name="sectioncanvas")
        self.canvas.grid(row=0, column=0, sticky='news')
        canvasFrame.grid(row=1, column=0, sticky='news')
        
        configureWeigths(self.canvas)
                
        self.contentFrame = tk.Frame(self.canvas, bg='white', bd=0,
                                     name="sectioncanvasframe")
        self.contentFrame.grid(row=1, column=0, sticky='news')
        self.contentId = self.canvas.create_window(0, 0, anchor=tk.NW,
                                                   window=self.contentFrame)

        self.contentFrame.bind('<Configure>', self._configure_interior)
        self.canvas.bind('<Configure>', self._configure_canvas)
        
        self.contentFrame.columnconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def _getReqSize(self, widget):
        return widget.winfo_reqwidth(), widget.winfo_reqheight()
    
    def _getSize(self, widget):
        return widget.winfo_width(), widget.winfo_height()
    # track changes to the canvas and frame width and sync them,
    # also updating the scrollbar
    def _configure_interior(self, event=None):

        # update the scrollbars to match the size of the inner frame
        fsize = self._getReqSize(self.contentFrame)
        csize = self._getSize(self.canvas)
        if fsize != csize:
            # update the canvas's width to fit the inner frame
            self.canvas.config(width=fsize[0], height=fsize[1])
            self.canvas.config(scrollregion="0 0 %s %s" % fsize)

    def _configure_canvas(self, event=None):
        fsize = self._getReqSize(self.contentFrame)
        csize = self._getSize(self.canvas)
        if fsize != csize:
            # update the inner frame's width to fill the canvas
            self.canvas.itemconfigure(self.contentId, width=csize[0])
            if csize[1] < fsize[1]:
                self.canvas.itemconfigure(self.contentId, height=fsize[1])
                self.canvas.config(scrollregion="0 0 %s %s" % csize)
                
    def adjustContent(self):
        self._configure_interior()
        self.update_idletasks()
        self._configure_canvas()

                    
class SectionWidget(SectionFrame):
    """This class will be used to create a section in FormWindow"""
    def __init__(self, form, master, section, height, callback=None, **args):
        self.form = form
        self.section = section
        self.callback = callback
        SectionFrame.__init__(self, master, self.section.label.get(),
                              height=height, **args)
        
    def _createHeader(self, label, bgColor):
        SectionFrame._createHeader(self, label, bgColor)        
        
        if self.section.hasQuestion():
            question = self.section.getQuestion() 
            self.paramName = self.section.getQuestionName()            
            self.var = BoolVar()
            self.var.set(question.get())
            self.var.trace('w', self._onVarChanged)
            
            self.chbLabel = tk.Label(self.headerFrame, text=question.label.get(),
                                     fg='white', bg=bgColor)
            self.chbLabel.grid(row=0, column=1, sticky='e', padx=2)
            
            self.chb = tk.Checkbutton(self.headerFrame, variable=self.var.tkVar, 
                                      bg=bgColor,
                                      activebackground=gui.cfgButtonActiveBgColor)
            self.chb.grid(row=0, column=2, sticky='e')
        
    def show(self):
        self.contentFrame.grid(row=1, column=0, sticky='news', padx=5, pady=5)
        
    def hide(self):
        self.contentFrame.grid_remove()
        
    def _onVarChanged(self, *args):
        if self.get():
            self.show()
        else:
            self.hide()
            
        if self.callback is not None:
            self.callback(self.paramName) 
            
    def get(self):
        """Return boolean value if is selected"""
        return self.var.get()
    
    def set(self, value):
        self.var.set(value)
    
               
class ParamWidget:
    """For each one in the Protocol parameters, there will be
    one of this in the Form GUI.
    It is mainly composed by:
    A Label: put in the left column
    A Frame(content): in the middle column and container
      of the specific components for this parameter
    A Frame(buttons): a container for available actions buttons
    It will also have a Variable that should be set when creating 
      the specific components"""
    def __init__(self, row, paramName, param, window, parent, value,
                 callback=None, visualizeCallback=None, column=0,
                 showButtons=True):
        self.window = window
        self._protocol = self.window.protocol
        if self._protocol.getProject() is None:
            print(">>> ERROR: Project is None for protocol: %s, "
                  "start winpdb to debug it" % self._protocol)
            pwutils.startDebugger()
        self.row = row
        self.column = column
        self.paramName = paramName
        self.param = param
        self.parent = parent
        self.visualizeCallback = visualizeCallback
        self.var = None

        self._btnCol = 0
        self._labelFont = self.window.font

        self._initialize(showButtons)
        self._createLabel()  # self.label should be set after this
        self._createContent()  # self.content and self.var should be set after this

        if self.var:  # Groups have not self.var
            self.set(value)
            self.callback = callback
            self.var.trace('w', self._onVarChanged)

    def _initialize(self, showButtons):
        # Show buttons = False means the widget is inside a Line group
        # then, some of the properties change accordingly
        if showButtons:
            self._labelSticky = 'ne'
            self._padx, self._pady = 2, 2
            self._entryWidth = 10
            if self.param.isImportant():
                self._labelFont = self.window.fontBold
            self.parent.columnconfigure(0, minsize=250)
            self.parent.columnconfigure(1, minsize=250)
            self.btnFrame = tk.Frame(self.parent, bg='white')
        else:
            self.btnFrame = None
            self._labelSticky = 'ne'
            self._padx, self._pady = 2, 0
            self._labelFont = self.window.fontItalic
            self._entryWidth = 8
        self._onlyLabel = False

    def _getParamLabel(self):
        return self.param.label.get()

    def _createLabel(self):
        bgColor = 'white'

        if self.param.isExpert():
            bgColor = 'lightgrey'

        self.label = tk.Label(self.parent, text=self._getParamLabel(),
                              bg=bgColor, font=self._labelFont, wraplength=500)

    def _createContent(self):
        self.content = tk.Frame(self.parent, bg='white')
        gui.configureWeigths(self.content)
        # self.var should be set after this
        self._createContentWidgets(self.param, self.content)

    def _addButton(self, text, imgPath, cmd):
        if self.btnFrame:
            btn = IconButton(self.btnFrame, text, imgPath,
                             highlightthickness=0, command=cmd)
            btn.grid(row=0, column=self._btnCol, sticky='nes', padx=1, pady=4)
            self.btnFrame.columnconfigure(self._btnCol, weight=1)
            self._btnCol += 1

    def _showHelpMessage(self, e=None):
        showInfo("Help", self.param.help.get(), self.parent)

    def _showInfo(self, msg):
        showInfo("Info", msg, self.parent)

    def _showError(self, msg):
        showError("Error", msg, self.parent)

    def _showWarning(self, msg):
        showWarning("Warning", msg, self.parent)

    def _showWizard(self, e=None):
        wizClass = self.window.wizards[self.wizParamName]
        wizard = wizClass()
        wizard.show(self.window)

    def _findParamWizard(self):
        """ Search if there are registered wizards for this param
        or any of its subparams (for the case of Line groups)
        """
        if self.paramName in self.window.wizards:
            self.wizParamName = self.paramName
            return True

        if isinstance(self.param, pwprot.Line):
            for name, _ in self.param.iterParams():
                if name in self.window.wizards:
                    self.wizParamName = name
                    return True
        # Search in sub-params
        return False

    @staticmethod
    def createBoolWidget(parent, **args):
        """ Return a BoolVar associated with a yes/no selection.
        **args: extra arguments passed to tk.Radiobutton and tk.Frame
            constructors.
        """
        var = BoolVar()
        frameArgs = dict(args)
        if 'font' in frameArgs:
            del frameArgs['font']
        frame = tk.Frame(parent, **frameArgs)
        rb1 = tk.Radiobutton(frame, text='Yes', variable=var.tkVar,
                             highlightthickness=0, value=1, **args)
        rb1.grid(row=0, column=0, padx=2, sticky='w')
        rb2 = tk.Radiobutton(frame, text='No', variable=var.tkVar,
                             highlightthickness=0, value=0, **args)
        rb2.grid(row=0, column=1, padx=2, sticky='w')

        return var, frame

    def _createContentWidgets(self, param, content):
        """Create the specific widgets inside the content frame"""
        # Create widgets for each type of param
        t = type(param)
        entryWidth = 30
        sticky = "we"

        # functions to select and remove
        selectFunc = None
        removeFunc = None

        if t is pwprot.HiddenBooleanParam:
            var = 0

        elif t is pwprot.BooleanParam:
            var, frame = ParamWidget.createBoolWidget(content, bg='white',
                                                      font=self.window.font)
            frame.grid(row=0, column=0, sticky='w')

        elif t is pwprot.EnumParam:
            var = ComboVar(param)
            if param.display == pwprot.EnumParam.DISPLAY_COMBO:
                combo = ttk.Combobox(content, textvariable=var.tkVar,
                                     state='readonly', font=self.window.font)
                combo['values'] = param.choices
                combo.grid(row=0, column=0, sticky='we')
            elif param.display == pwprot.EnumParam.DISPLAY_LIST:
                for i, opt in enumerate(param.choices):
                    rb = tk.Radiobutton(content, text=opt, variable=var.tkVar,
                                        value=opt, font=self.window.font,
                                        bg='white', highlightthickness=0)
                    rb.grid(row=i, column=0, sticky='w')
            elif param.display == pwprot.EnumParam.DISPLAY_HLIST:
                rbFrame = tk.Frame(content, bg='white')
                rbFrame.grid(row=0, column=0, sticky='w')
                for i, opt in enumerate(param.choices):
                    rb = tk.Radiobutton(rbFrame, text=opt, variable=var.tkVar,
                                        value=opt, font=self.window.font,
                                        bg='white')
                    rb.grid(row=0, column=i, sticky='w', padx=(0, 5))
            else:
                raise Exception("Invalid display value '%s' for EnumParam"
                                % str(param.display))

        elif t is pwprot.MultiPointerParam:
            tp = MultiPointerTreeProvider(self._protocol.mapper)
            tree = BoundTree(content, tp, height=5)
            var = MultiPointerVar(tp, tree)
            tree.grid(row=0, column=0, sticky='we')
            self._addButton("Select", pwutils.Icon.ACTION_SEARCH, self._browseObject)
            self._addButton("Remove", pwutils.Icon.ACTION_DELETE, self._removeObject)
            self._selectmode = 'extended'  # allows multiple object selection
            self.visualizeCallback = self._visualizeMultiPointerParam

        elif t is pwprot.PointerParam or t is pwprot.RelationParam:
            var = PointerVar(self._protocol)
            var.trace('w', self.window._onPointerChanged)
            entry = tk.Label(content, textvariable=var.tkVar,
                             font=self.window.font, anchor="w")
            entry.grid(row=0, column=0, sticky='we')

            if t is pwprot.RelationParam:
                selectFunc = self._browseRelation
                removeFunc = self._removeRelation
            else:
                selectFunc = self._browseObject
                removeFunc = self._removeObject

                self.visualizeCallback = self._visualizePointerParam
            self._selectmode = 'browse'  # single object selection

        elif t is pwprot.ProtocolClassParam:
            var = tk.StringVar()
            entry = tk.Label(content, textvariable=var, font=self.window.font,
                             anchor="w")
            entry.grid(row=0, column=0, sticky='we')

            protClassName = self.param.protocolClassName.get()

            if self.param.allowSubclasses:
                classes = pw.Config.getDomain().findSubClasses(
                    pw.Config.getDomain().getProtocols(), protClassName).keys()
            else:
                classes = [protClassName]

            if len(classes) > 1:
                self._addButton("Select", pwutils.Icon.ACTION_SEARCH,
                                self._browseProtocolClass)
            else:
                var.set(classes[0])

            self._addButton("Edit", pwutils.Icon.ACTION_EDIT, self._openProtocolForm)

        elif t is pwprot.Line:
            var = None

        elif t is pwprot.LabelParam:
            var = None
            self._onlyLabel = True

        elif t is pwprot.TextParam:
            w = max(entryWidth, param.width)
            text = Text(content, font=self.window.font, width=w,
                        height=param.height)
            var = TextVar(text)
            text.grid(row=0, column=0, sticky='w')

        else:

            if not param.allowsPointers:
                var = tk.StringVar()

                if issubclass(t, pwprot.FloatParam) or issubclass(t, pwprot.IntParam):

                    # Reduce the entry width for numbers entries
                    entryWidth = self._entryWidth
                    sticky = 'w'
            else:
                selectFunc = self._browseScalar
                var = ScalarWithPointerVar(self._protocol,
                                           self.window._onPointerChanged)
                self._selectmode = 'browse'
                sticky = 'ew'

            entry = tk.Entry(content, width=entryWidth, textvariable=var,
                             font=self.window.font)

            # Select all content on focus
            entry.bind("<FocusIn>",
                       lambda event: entry.selection_range(0, tk.END))

            entry.grid(row=0, column=0, sticky=sticky)

            if issubclass(t, pwprot.PathParam):
                self._entryPath = entry
                self._addButton('Browse', pwutils.Icon.ACTION_BROWSE,
                                self._browsePath)

        if selectFunc is not None:
            self._addButton("Select", pwutils.Icon.ACTION_SEARCH, selectFunc)

        if removeFunc is not None:
            self._addButton("Remove", pwutils.Icon.ACTION_DELETE, removeFunc)

        if self.visualizeCallback is not None:
            self._addButton(pwutils.Message.LABEL_BUTTON_VIS,
                            pwutils.Icon.ACTION_VISUALIZE,
                            self._visualizeVar)

        if self._findParamWizard():
            self._addButton(pwutils.Message.LABEL_BUTTON_WIZ,
                            pwutils.Icon.ACTION_WIZ,
                            self._showWizard)

        if param.help.hasValue():
            self._addButton(pwutils.Message.LABEL_BUTTON_HELP,
                            pwutils.Icon.ACTION_HELP,
                            self._showHelpMessage)

        self.var = var

    def _visualizeVar(self, e=None):
        """ Visualize specific variable. """
        self.visualizeCallback(self.paramName)

    def _visualizePointer(self, pointer):
        obj = pointer.get()

        if obj is None:
            label, _ = getPointerLabelAndInfo(pointer, self._protocol.getMapper())
            self._showInfo('*%s* points to *None*' % label)
        else:
            viewers = pw.Config.getDomain().findViewers(obj.getClassName(), DESKTOP_TKINTER)
            if len(viewers):
                ViewerClass = viewers[0]  # Use the first viewer registered
                # Instantiate the viewer and visualize object
                viewer = ViewerClass(project=self._protocol.getProject(),
                                     protocol=self._protocol,
                                     parent=self.window)
                viewer.visualize(obj)
            else:
                self._showInfo("There is no viewer registered for "
                               "*%s* object class." % obj.getClassName())

    def _visualizePointerParam(self, paramName):
        pointer = self.var.get()
        if pointer.hasValue():
            self._visualizePointer(pointer)
        else:
            self._showInfo("Select input first.")

    def _visualizeMultiPointerParam(self, paramName):
        selection = self.var.getSelectedObjects()
        for pointer in selection:
            self._visualizePointer(pointer)

    def _browseObject(self, e=None):
        """Select an object from DB
        This function is suppose to be used only for PointerParam"""
        value = self.get()
        selected = []
        if isinstance(value, list):
            selected = value
        else:

            selected = [value]
        tp = SubclassesTreeProvider(self._protocol, self.param,
                                    selected=selected)

        def validateSelected(selectedItems):
            for item in selectedItems:
                if not getattr(item, '_allowsSelection', True):
                    return ("Please select object of types: %s"
                            % self.param.pointerClass.get())

        title = "Select object of types: %s" % self.param.pointerClass.get()

        pointerCond = self.param.pointerCondition.get()

        if pointerCond:
            title += " (condition: %s)" % pointerCond

        dlg = ListDialog(self.parent, title, tp,
                         "Double click selects the item, right-click allows "
                         "you to visualize it",
                         validateSelectionCallback=validateSelected,
                         selectmode=self._selectmode, selectOnDoubleClick=True)

        if dlg.values:
            if isinstance(self.param, pwprot.MultiPointerParam):
                self.set(dlg.values)
            elif isinstance(self.param, pwprot.PointerParam):
                self.set(dlg.values[0])
            else:
                raise Exception('Invalid param class: %s' % type(self.param))

    def _browseScalar(self, e=None):
        """Select a scalar from outputs
        This function is suppose to be used only for Scalar Params
        It's a copy of browseObject...so there could be a refactor here."""
        value = self.get()
        selected = []
        if isinstance(value, list):
            selected = value
        else:
            selected = [value]
        tp = ScalarTreeProvider(self._protocol, self.param,
                                selected=selected)

        def validateSelected(selectedItems):
            for item in selectedItems:
                if not getattr(item, '_allowsSelection', True):
                    return ("Please select object of types: %s"
                            % self.param.paramClass.get())

        title = "Select object of types: %s" % self.param.paramClass.__name__

        # Let's ignore conditions so far
        # pointerCond = self.param.pointerCondition.get()
        # if pointerCond:
        #    title += " (condition: %s)" % pointerCond

        dlg = ListDialog(self.parent, title, tp,
                         "Double click selects the item",
                         validateSelectionCallback=validateSelected,
                         selectOnDoubleClick=True)

        if dlg.values:
            self.set(dlg.values[0])

    def _removeObject(self, e=None):
        """ Remove an object from a MultiPointer param. """
        self.var.remove()

    def _browseRelation(self, e=None):
        """Select a relation from DB
        This function is suppose to be used only for RelationParam. """
        try:
            tp = RelationsTreeProvider(self._protocol, self.param,
                                       selected=self.get())
            dlg = ListDialog(self.parent, "Select object", tp,
                             "Double click selects the item, right-click "
                             "allows you to visualize it",
                             selectmoded=self._selectmode,
                             selectOnDoubleClick=True)
            if dlg.values:
                self.set(dlg.values[0])
        except AttributeError:
            self._showError("Error loading possible inputs. "
                            "This usually happens because the parameter "
                            "needs info from other parameters... are "
                            "previous mandatory parameters set?")

    def _removeRelation(self, e=None):
        self.var.remove()

    def _browseProtocolClass(self, e=None):
        tp = ProtocolClassTreeProvider(self.param.protocolClassName.get())
        dlg = ListDialog(self.parent, "Select protocol", tp,
                         selectmode=self._selectmode)
        if dlg.value is not None:
            self.set(dlg.value)
            self._openProtocolForm()

    def _browsePath(self, e=None):
        def onSelect(obj):
            self.set(obj.getPath())

        v = self.get().strip()
        path = None
        if v:
            v = os.path.dirname(v)
            if os.path.exists(v):
                path = v
        if not path:
            path = pwutils.getHomePath()
        browser = FileBrowserWindow("Browsing", self.window, path=path,
                                    onSelect=onSelect)
        browser.show()

    def _openProtocolForm(self, e=None):
        className = self.get().strip()
        if len(className):
            instanceName = self.paramName + "Instance"
            protocol = self._protocol
            # TODO: check if is present and is selected a different
            # class, so we need to delete that and create a new instance
            if not hasattr(protocol, instanceName):
                cls = pw.Config.getDomain().findClass(className)
                protocol._insertChild(instanceName, cls())

            prot = getattr(protocol, instanceName)

            prot.allowHeader.set(False)
            f = FormWindow("Sub-Protocol: " + instanceName, prot,
                           self._protocolFormCallback, self.window,
                           childMode=True)
            f.show()
        else:
            self._showInfo("Select the protocol class first")

    def _protocolFormCallback(self, e=None):
        pass

    def _onVarChanged(self, *args):
        if self.callback is not None:
            self.callback(self.paramName)

    def show(self):
        """Grid the label and content in the specified row"""
        c = self.column
        if self._onlyLabel:
            # Use two columns for this case since we are only displaying a label
            self.label.grid(row=self.row, column=c, sticky=self._labelSticky,
                            padx=self._padx, pady=self._pady, columnspan=2)
        else:
            self.label.grid(row=self.row, column=c, sticky=self._labelSticky,
                            padx=self._padx, pady=self._pady)

            # Note: for params without label: 1st param in a line param,
            # label usually but take space and pushes the content, avoid
            # this by using it's column
            offset = 1 if not self._getParamLabel() else 0

            self.content.grid(row=self.row, column=c+1-offset,
                              columnspan=1+offset, sticky='news',
                              padx=self._padx, pady=self._pady)
        if self.btnFrame:
            self.btnFrame.grid(row=self.row, column=c+2, padx=self._padx,
                               pady=self._pady, sticky='nsew')

    def hide(self):
        self.label.grid_remove()
        self.content.grid_remove()
        if self.btnFrame:
            self.btnFrame.grid_remove()

    def display(self, condition):
        """ show or hide depending on the condition. """
        if condition:
            self.show()
        else:
            self.hide()

    def set(self, value):
        if value is not None:
            self.var.set(value)

        if hasattr(self, '_entryPath'):
            self._entryPath.xview_moveto(1)

    def get(self):
        return self.var.get()


class LineWidget(ParamWidget):
    def __init__(self, row, paramName, param, window, parent, value, 
                 callback=None, visualizeCallback=None, column=0,
                 showButtons=True):
        ParamWidget.__init__(self, row, paramName, param, window, parent, None)
        self.show()
        
    def show(self):
        self.label.grid(row=self.row, column=0, sticky=self._labelSticky, padx=2)
        self.content.grid(row=self.row, column=1, sticky='new', columnspan=1,
                          padx=2)
        if self.btnFrame:
            self.btnFrame.grid(row=self.row, column=2, padx=2, sticky='new')
       

class GroupWidget(ParamWidget):
    def __init__(self, row, paramName, param, window, parent):
        ParamWidget.__init__(self, row, paramName, param, window, parent, None)
        
    def _initialize(self, showButtons):
        pass
        
    def _createLabel(self):
        pass
               
    def _createContent(self):
        self.content = tk.LabelFrame(self.parent, text=self.param.getLabel(),
                                     bg='white')
        gui.configureWeigths(self.content, column=1)
        
    def show(self):
        self.content.grid(row=self.row, column=0, sticky='news', columnspan=6,
                          padx=5, pady=5)
        
    def hide(self):
        self.content.grid_remove()  
            
            
class Binding:
    def __init__(self, paramName, var, protocol, *callbacks):
        self.paramName = paramName
        self.var = var
        self.var.set(protocol.getAttributeValue(paramName, ''))
        self.var.trace('w', self._onVarChanged)
        self.callbacks = callbacks
        
    def _onVarChanged(self, *args):
        for cb in self.callbacks:
            cb(self.paramName)
            
    
class FormWindow(Window):
    """ This class will create the Protocol params GUI to fill in the parameters.
    The creation of input parameters will be based on the Protocol Form definition.
    This class will serve as a connection between the GUI variables (tk vars) and 
    the Protocol variables.
    
    Layout:
        There are 4 main blocks that goes each one in a different row1.
        1. Header: will contains the logo, title and some link buttons.
        2. Common: common execution parameters of each run.
        3. Params: the expert level and tabs with the Protocol parameters.
        4. Buttons: buttons at bottom for close, save and execute.
    """
    def __init__(self, title, protocol, callback, master=None,
                 hostList=['localhost'], **kwargs):
        """ Constructor of the Form window. 
        Params:
         title: title string of the windows.
         protocol: protocol from which the form will be generated.
         callback: callback function to call when Save or Execute are press.
        """
        Window.__init__(self, title, master, icon=pwutils.Icon.SCIPION_ICON_PROT,
                        weight=False, minsize=(600, 450), **kwargs)

        # Some initialization
        self.callback = callback
        self.widgetDict = {}  # Store tkVars associated with params
        self.visualizeDict = kwargs.get('visualizeDict', {})
        self.bindings = []
        self.hostList = hostList
        self.protocol = protocol
        # This control when to close or not after execute
        self.visualizeMode = kwargs.get('visualizeMode', False)
        self.headerBgColor = pwutils.Color.RED_COLOR
        if self.visualizeMode:
            self.headerBgColor = pwutils.Color.DARK_GREY_COLOR
        # Allow to open child protocols form (for workflows)
        self.childMode = kwargs.get('childMode', False)
        self.updateProtocolCallback = kwargs.get('updateProtocolCallback', None)
        domain = pw.Config.getDomain()
        self.wizards = domain.findWizards(protocol, DESKTOP_TKINTER)

        # Call legacy for compatibility on protocol
        protocol.legacyCheck()
        self._createGUI()
        
    def _createGUI(self):
        mainFrame = tk.Frame(self.root, name="main")
        configureWeigths(mainFrame, row=2)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # "Protocol: XXXXX  - Cite Help
        headerFrame = self._createHeader(mainFrame)
        headerFrame.grid(row=0, column=0, sticky='new')
        
        if self.protocol.allowHeader:
            # Run Section with common attributes (parallel,...)
            commonFrame = self._createCommon(mainFrame)
            commonFrame.grid(row=1, column=0, sticky='new')

        if self._isLegacyProtocol():
            paramsFrame = self._createLegacyInfo(mainFrame)
        else:
            paramsFrame = self._createParams(mainFrame)
        paramsFrame.grid(row=2, column=0, sticky='news')
        
        buttonsFrame = self._createButtons(mainFrame)
        buttonsFrame.grid(row=3, column=0, sticky='se')
        
        mainFrame.grid(row=0, column=0, sticky='news')

    def _createHeader(self, parent):
        """ Fill the header frame with the logo, title and cite-help buttons."""
        headerFrame = tk.Frame(parent, name="header")
        headerFrame.columnconfigure(0, weight=1)
        prot = self.protocol  # shortcut
        package = prot.getClassPackage()

        # Consider legacy protocols
        if self._isLegacyProtocol():
            t = ('  Missing protocol: %s'
                 % (Mapper.getObjectPersistingClassName(prot)))
        else:
            t = '  Protocol: %s' % (prot.getClassLabel())

        logoPath = prot.getPluginLogoPath() or getattr(package, '_logo', '')

        if logoPath and os.path.exists(logoPath):
            headerLabel = tk.Label(headerFrame, text=t, font=self.fontBig, 
                                   image=self.getImage(logoPath, maxheight=40),
                                   compound=tk.LEFT)
        else:
            headerLabel = tk.Label(headerFrame, text=t, font=self.fontBig)
        headerLabel.grid(row=0, column=0, padx=5, pady=(5, 0), sticky='nw')

        # Add status label
        status = prot.status.get()
        # For viewers and new protocols (status less object): skip this
        if status is not None:
            color = getStatusColorFromRun(prot)
            stLabel = tk.Label(headerFrame, text=status, background=color)
            stLabel.grid(row=0, column=1, padx=5, pady=5, sticky='e')

        def _addButton(text, icon, command, col):
            btn = tk.Label(headerFrame, text=text, image=self.getImage(icon), 
                           compound=tk.LEFT, cursor='hand2', name=text.lower())
            btn.bind('<Button-1>', command)
            btn.grid(row=0, column=col, padx=5, sticky='e')

        _addButton(pwutils.Message.LABEL_CITE,
                   pwutils.Icon.ACTION_REFERENCES,
                   self._showReferences, 2)
        _addButton(pwutils.Message.LABEL_HELP,
                   pwutils.Icon.ACTION_HELP, self._showHelp, 3)

        return headerFrame
        
    def _showReferences(self, e=None):
        """ Show the list of references of the protocol. """
        self.showInfo('\n'.join(self.protocol.citations()), "References")
        
    def _showHelp(self, e=None):
        """ Show the protocol help. """
        prot = self.protocol
        text = prot.getHelpText()

        # Add protocol url
        url = prot.getUrl()

        # If not empty...
        if url:
            text += "\nDocumentation or forum url for this protocol:\n" +url

        self.showInfo(text, "Help")
        
    def _createParallel(self, runFrame, r):
        """ Create the section for MPI, threads and GPU. """

        # Legacy protocols retrieved from the DB may not have this param
        # and legacy mode will fail. Thus the try block
        try:

            # some short notation
            prot = self.protocol  # shortcut notation
            allowThreads = prot.allowThreads  # short notation
            allowMpi = prot.allowMpi  # short notation
            allowGpu = prot.allowsGpu()
            numberOfMpi = prot.numberOfMpi.get()
            numberOfThreads = prot.numberOfThreads.get()
            mode = prot.stepsExecutionMode

            if not (allowThreads or allowMpi or allowGpu):
                return

            self._createHeaderLabel(runFrame, pwutils.Message.LABEL_PARALLEL, bold=True,
                                    sticky='e', row=r, pady=0)

            if allowThreads or allowMpi:
                procFrame = tk.Frame(runFrame, bg='white')
                r2 = 0
                c2 = 0
                sticky = 'e'

                if mode == pwprot.STEPS_PARALLEL:
                    self.procTypeVar = tk.StringVar()

                    if allowThreads and allowMpi:
                        if numberOfMpi > 1:
                            procs = numberOfMpi
                            self.procTypeVar.set(MPI)
                            prot.numberOfThreads.set(1)
                        else:
                            procs = numberOfThreads
                            self.procTypeVar.set(THREADS)
                            prot.numberOfMpi.set(1)

                        self.procTypeVar.trace('w', self._setThreadsOrMpi)
                        procCombo = tk.Frame(procFrame, bg='white')
                        for i, opt in enumerate([THREADS, MPI]):
                            rb = tk.Radiobutton(procCombo, text=opt,
                                                variable=self.procTypeVar,
                                                value=opt, bg='white',
                                                highlightthickness=0)
                            rb.grid(row=0, column=i, sticky='w', padx=(0, 5))

                        procCombo.grid(row=r2, column=0, sticky='w', pady=15)
                        procEntry = self._createBoundEntry(procFrame,
                                                           pwutils.Message.VAR_THREADS,
                                                           func=self._setThreadsOrMpi,
                                                           value=procs)
                        procEntry.grid(row=r2, column=1, padx=(0, 5), sticky='w')
                    else:
                        # Show an error message
                        self.showInfo(" If protocol execution is set to "
                                      "STEPS_PARALLEL number of threads and mpi "
                                      "should not be set to zero.")

                else:
                    # ---- THREADS----
                    if allowThreads:
                        self._createHeaderLabel(procFrame, pwutils.Message.LABEL_THREADS,
                                                sticky=sticky, row=r2, column=c2,
                                                pady=0)
                        entry = self._createBoundEntry(procFrame,
                                                       pwutils.Message.VAR_THREADS)
                        entry.grid(row=r2, column=c2 + 1, padx=(0, 5), sticky='w')
                        # Modify values to be used in MPI entry
                        c2 += 2
                        sticky = 'w'
                    # ---- MPI ----
                    if allowMpi:
                        self._createHeaderLabel(procFrame, pwutils.Message.LABEL_MPI,
                                                sticky=sticky, row=r2, column=c2,
                                                pady=0)
                        entry = self._createBoundEntry(procFrame, pwutils.Message.VAR_MPI)
                        entry.grid(row=r2, column=c2 + 1, padx=(0, 5), sticky='w')

                btnHelp = IconButton(procFrame, pwutils.Message.TITLE_COMMENT,
                                     pwutils.Icon.ACTION_HELP,
                                     highlightthickness=0,
                                     command=self._createHelpCommand(
                                         pwutils.Message.HELP_MPI_THREADS))
                btnHelp.grid(row=0, column=4, padx=(5, 0), pady=2, sticky='e')

                procFrame.columnconfigure(0, minsize=60)
                procFrame.grid(row=r, column=1, sticky='ew', columnspan=2)

                r += 1

            if allowGpu:
                self._createHeaderLabel(runFrame, "GPU IDs", bold=True,
                                        sticky='e', row=r, column=0, pady=0)
                gpuFrame = tk.Frame(runFrame, bg='white')
                gpuFrame.grid(row=r, column=1, sticky='ew', columnspan=2)

                self.useGpuVar = tk.IntVar()

                # For protocols that require GPU, there is not the option to choose
                if not prot.requiresGpu():
                    self.useGpuVar.set(int(prot.useGpu.get()))
                    for i, opt in enumerate(['Yes', 'No']):
                        rb = tk.Radiobutton(gpuFrame, text=opt,
                                            variable=self.useGpuVar,
                                            value=1-i, bg='white',
                                            highlightthickness=0)
                        rb.grid(row=0, column=i, sticky='w', padx=(0, 5), pady=5)

                self.gpuListVar = tk.StringVar()
                self.gpuListVar.set(prot.getAttributeValue(pwprot.GPU_LIST, ''))
                gpuEntry = tk.Entry(gpuFrame, width=9, font=self.font,
                                    textvariable=self.gpuListVar)
                gpuEntry.grid(row=0, column=2, sticky='w',
                              padx=(0, 5), pady=(0, 5))

                # Legacy protocols retrieved from the DB will not have this param
                # and legacy mode will fail. try added at the top.
                gpuListParam = prot.getParam(pwprot.GPU_LIST)
                btnHelp = IconButton(gpuFrame, pwutils.Message.TITLE_COMMENT,
                                     pwutils.Icon.ACTION_HELP,
                                     highlightthickness=0,
                                     command=self._createHelpCommand(
                                         gpuListParam.getHelp()))
                btnHelp.grid(row=0, column=3, padx=(5, 0), pady=2, sticky='e')

                # Trace changes in GPU related widgets to store values in protocol
                self.useGpuVar.trace('w', self._setGpu)
                self.gpuListVar.trace('w', self._setGpu)
        except Exception as e:
            print("Parallel section couldn't be created. %s" % e.message)

    def _createCommon(self, parent):
        """ Create the second section with some common parameters. """
        commonFrame = tk.Frame(parent, name="commonparams")
        configureWeigths(commonFrame)

        # ---------- Run section ---------
        runSection = SectionFrame(commonFrame, label=pwutils.Message.TITLE_RUN,
                                  headerBgColor=self.headerBgColor,
                                  name="runsection")

        runFrame = tk.Frame(runSection.contentFrame, bg='white', name="runframe")
        runFrame.grid(row=0, column=0, sticky='new')

        r = 0  # Run name
        self._createHeaderLabel(runFrame, pwutils.Message.LABEL_RUNNAME, bold=True,
                                sticky='ne')
        self.runNameVar = tk.StringVar()
        entry = tk.Label(runFrame, font=self.font, width=25,
                         textvariable=self.runNameVar, anchor="w")
        entry.grid(row=r, column=1, padx=(0, 5), pady=5, sticky='ew')
        btn = IconButton(runFrame, pwutils.Message.TITLE_COMMENT, pwutils.Icon.ACTION_EDIT,
                         highlightthickness=0, command=self._editObjParams)
        btn.grid(row=r, column=2, padx=(5, 0), pady=5, sticky='w')
        
        c = 3  # Comment
        self._createHeaderLabel(runFrame, pwutils.Message.TITLE_COMMENT, sticky='e',
                                column=c)
        self.commentVar = tk.StringVar()
        entry = tk.Label(runFrame, font=self.font, width=25,
                         textvariable=self.commentVar, anchor="w")
        entry.grid(row=r, column=c+1, pady=5, sticky='ew')
        btn = IconButton(runFrame, pwutils.Message.TITLE_COMMENT, pwutils.Icon.ACTION_EDIT,
                         highlightthickness=0, command=self._editObjParams)
        btn.grid(row=r, column=c+2, padx=(5, 0), pady=5, sticky='w')
        
        self.updateLabelAndCommentVars()

        r = 1  # Execution

        modeFrame = tk.Frame(runFrame, bg='white')

        if not self.protocol.isSaved():
            self._createHeaderLabel(runFrame, pwutils.Message.LABEL_EXECUTION,
                                    bold=True,
                                    sticky='e', row=r, pady=0)

            runMode = self._createBoundOptions(modeFrame, pwutils.Message.VAR_RUN_MODE,
                                               pwprot.MODE_CHOICES,
                                               self.protocol.runMode.get(),
                                               self._onRunModeChanged,
                                               bg='white', font=self.font)
            runMode.grid(row=0, column=0, sticky='e', padx=(0, 5), pady=5)
            btnHelp = IconButton(modeFrame, pwutils.Message.TITLE_COMMENT, pwutils.Icon.ACTION_HELP,
                                 highlightthickness=0,
                                 command=self._createHelpCommand(pwutils.Message.HELP_RUNMODE))
            btnHelp.grid(row=0, column=2, padx=(5, 0), pady=2, sticky='e')
        modeFrame.columnconfigure(0, weight=1)
        modeFrame.grid(row=r, column=1, sticky='ew', columnspan=2)
        
        # ---- Host---- 
        self._createHeaderLabel(runFrame, pwutils.Message.LABEL_HOST, row=r, column=c,
                                sticky='e')
        # Keep track of hostname selection
        self.hostVar = tk.StringVar()
        protHost = self.protocol.getHostName()
        hostName = protHost if protHost in self.hostList else self.hostList[0]
        self.hostVar.trace('w', self._setHostName)
        self.hostCombo = ttk.Combobox(runFrame, textvariable=self.hostVar, 
                                      state='readonly', width=10, font=self.font)
        self.hostCombo['values'] = self.hostList
        self.hostVar.set(hostName)
        self.hostCombo.grid(row=r, column=c+1, pady=0, sticky='we')
        r = 2
        self._createParallel(runFrame, r)

        # ---- QUEUE ----

        self._createHeaderLabel(runFrame, pwutils.Message.LABEL_QUEUE, row=r,
                                sticky='e',
                                column=c)

        var, frame = ParamWidget.createBoolWidget(runFrame, bg='white',
                                                  font=self.font)
        self._addVarBinding(pwutils.Message.VAR_QUEUE, var)
        frame.grid(row=r, column=c + 1, pady=5, sticky='ew')

        btnHelp = IconButton(runFrame, pwutils.Message.TITLE_COMMENT, pwutils.Icon.ACTION_HELP,
                             highlightthickness=0,
                             command=self._createHelpCommand(pwutils.Message.HELP_USEQUEUE))

        btnHelp.grid(row=r, column=c + 2, padx=(5, 0), pady=5, sticky='w')

        r = 3  # ---- Wait for other protocols (SCHEDULE) ----
        self._createHeaderLabel(runFrame, pwutils.Message.LABEL_WAIT_FOR, row=r, sticky='e',
                                column=c, padx=(15, 5), pady=0)
        self.waitForVar = tk.StringVar()
        self.waitForVar.set(', '.join(self.protocol.getPrerequisites()))
        entryWf = tk.Entry(runFrame, font=self.font, width=25,
                           textvariable=self.waitForVar)
        entryWf.grid(row=r, column=c+1, padx=(0, 5), pady=5, sticky='ew')

        self.waitForVar.trace('w', self._setWaitFor)

        btnHelp = IconButton(runFrame, pwutils.Message.TITLE_COMMENT, pwutils.Icon.ACTION_HELP,
                             highlightthickness=0,
                             command=self._createHelpCommand(pwutils.Message.HELP_WAIT_FOR))
        btnHelp.grid(row=r, column=c+2, padx=(5, 0), pady=2, sticky='e')
        
        # Run Name not editable
        # entry.configure(state='readonly')
        # Run mode
        # self._createHeaderLabel(runFrame, pwutils.Message.LABEL_RUNMODE).grid(row=1, column=0, sticky='ne', padx=5, pady=5)
        # runSection.addContent()
        runSection.grid(row=0, column=0, sticky='news', padx=5, pady=5)
        
        return commonFrame 
 
    def _createHelpCommand(self, msg):
        """ Show the help of some value of the header. """
        return lambda: showInfo("Help", msg, self.root)
    
    def _editObjParams(self, e=None):
        """ Show a Text area to edit the protocol label and comment. """
        self.updateProtocolLabel()        
        d = EditObjectDialog(self.root, pwutils.Message.TITLE_EDIT_OBJECT, 
                             self.protocol, self.protocol.mapper,
                             labelText=pwutils.Message.LABEL_RUNNAME)
        
        if d.resultYes():
            self.updateLabelAndCommentVars()
            if self.updateProtocolCallback:
                self.updateProtocolCallback(self.protocol)
                
    def _getHostConfig(self):
        """ Retrieve the hostConfig object for the select hostname"""
        return self.protocol.getProject().getHostConfig(self.protocol.getHostName())
        
    def _editQueueParams(self, e=None):
        """ Open the dialog to edit the queue parameters. """
        # Grab the host config from the project, since it 
        # have not been set in the protocol
        hostConfig = self._getHostConfig()
        queues = OrderedDict(sorted(hostConfig.queueSystem.queues.items()))
        # If there is only one Queue and it has no parameters
        # don't bother to showing the QueueDialog
        noQueueChoices = len(queues) == 1 and len(list(queues.values())[0]) == 0
        if noQueueChoices:
            result = list(queues.keys())[0], {}
        else:
            dlg = QueueDialog(self, queues)

            if not dlg.resultYes():
                return False
            result = dlg.value
        
        self.protocol.setQueueParams(result)
        return True

    def _createParams(self, parent):
        paramsFrame = tk.Frame(parent, name="params")
        configureWeigths(paramsFrame, row=1, column=0)
        # Expert level (only if the protocol has some param with expert level)
        if self.protocol.hasExpert():
            expFrame = tk.Frame(paramsFrame, name="expert")
            expLabel = tk.Label(expFrame, text=pwutils.Message.LABEL_EXPERT, font=self.fontBold)
            expLabel.grid(row=0, column=0, sticky='nw', padx=5)
            expCombo = self._createBoundOptions(expFrame, pwutils.Message.VAR_EXPERT, pwprot.LEVEL_CHOICES,
                                                self.protocol.expertLevel.get(),
                                                self._onExpertLevelChanged, font=self.font)
            expCombo.grid(row=0, column=1, sticky='nw', pady=5)
            expFrame.grid(row=0, column=0, sticky='nw')

        contentFrame = self._createSections(paramsFrame)
        contentFrame.grid(row=1, column=0, sticky='news')
        
        return paramsFrame

    def _isLegacyProtocol(self):
        return isinstance(self.protocol, pwprot.LegacyProtocol)

    def _createLegacyInfo(self, parent):
        frame = tk.Frame(parent, name="legacy")
        t = tk.Label(frame,
                     text="This protocol is missing from the installation. "
                          "\nThis could be because you are opening an old "
                          "project and some of \nthe executed protocols does "
                          "not exist in the current version and were deprecated"
                          ",\n or because your scipion installation requires a "
                          "plugin where this protocol can be found.\n\n"
                          "If you are a developer, it could be the case that "
                          "you have changed \nto another branch where the "
                          "protocol does not exist.\n\n"
                          "Anyway, you can still inspect the parameters by "
                          "opening the DB from the toolbar."
                     )
        t.grid(row=0, column=0, padx=5, pady=5)

        return frame

    def _createSections(self, parent):
        """Create section widgets"""
        r = 0
        sectionsFrame = tk.Frame(parent) 
        configureWeigths(sectionsFrame)
        tab = ttk.Notebook(sectionsFrame)
        tab.grid(row=0, column=0, sticky='news',
                 padx=5, pady=5)
        self._sections = []
        
        for section in self.protocol.iterDefinitionSections():
            label = section.getLabel()
            if label != 'General' and label != 'Parallelization':
                frame = SectionWidget(self, tab, section, height=150,
                                      callback=self._checkChanges,
                                      headerBgColor=self.headerBgColor)
                
                tab.add(frame, text=section.getLabel())
                frame.columnconfigure(0, minsize=400)
                self._fillSection(section, frame)
                self._sections.append(frame)
                r += 1
        self._checkAllChanges()
        
        return sectionsFrame    
        
    def _createButtons(self, parent):
        """ Create the bottom buttons: Close, Save and Execute. """
        btnFrame = tk.Frame(parent)

        btnClose = self.createCloseButton(btnFrame)
        btnClose.grid(row=0, column=0, padx=5, pady=5, sticky='se')
        # Save button is not added in VISUALIZE or CHILD modes
        # Neither in the case of a LegacyProtocol
        if (not self.visualizeMode and not self.childMode and
                not self._isLegacyProtocol()):

            # Check editable or not:
            btnState = tk.DISABLED if (self.protocol.isActive()
                                       and not self.protocol.isInteractive()) \
                                   else tk.NORMAL

            self.btnSave = Button(btnFrame, pwutils.Message.LABEL_BUTTON_RETURN,
                                  pwutils.Icon.ACTION_SAVE, command=self.save,
                                  state=btnState)
            self.btnSave.grid(row=0, column=1, padx=5, pady=5, sticky='se')
            self.btnExecute = HotButton(btnFrame, pwutils.Message.LABEL_BUTTON_EXEC,
                                        pwutils.Icon.ACTION_EXECUTE,
                                        command=self.execute, state=btnState)
            self.btnExecute.grid(row=0, column=2, padx=(5, 28),
                                 pady=5, sticky='se')
            self._onPointerChanged()
            
        return btnFrame
        
    def _addVarBinding(self, paramName, var, func=None, *callbacks):
        if func is None:
            func = self.setParamFromVar
        binding = Binding(paramName, var, self.protocol, 
                          func, *callbacks)
        self.widgetDict[paramName] = var
        self.bindings.append(binding)
        
    def _createBoundEntry(self, parent, paramName, width=5, 
                          func=None, value=None, **kwargs):
        var = tk.StringVar()
        setattr(self, paramName + 'Var', var)
        self._addVarBinding(paramName, var, func)
        if value is not None:
            var.set(value)
        return tk.Entry(parent, font=self.font, width=width, 
                        textvariable=var, **kwargs)
    
    def _createEnumBinding(self, paramName, choices, value=None, *callbacks):
        param = pwprot.EnumParam(choices=choices)
        var = ComboVar(param)
        if value is not None:
            var.set(value)
        self._addVarBinding(paramName, var, None, *callbacks)
        return param, var
        
    def _createBoundOptions(self, parent, paramName, choices, value, *callbacks, **kwargs):
        param, var = self._createEnumBinding(paramName, choices, value, *callbacks)
        rbArgs = {}
        frameArgs = dict(kwargs)
        if 'bg' in kwargs:
            rbArgs['bg'] = kwargs['bg']
            
        if 'font' in kwargs:
            rbArgs['font'] = kwargs['font']
            del frameArgs['font']
            
        frame = tk.Frame(parent, **frameArgs)
        for i, opt in enumerate(param.choices):
            rb = tk.Radiobutton(frame, text=opt, variable=var.tkVar, value=opt, highlightthickness=0, **rbArgs)
            rb.grid(row=0, column=i, sticky='nw', padx=(0, 5))  
        
        return frame
        
    def _createHeaderLabel(self, parent, text, bold=False, **gridArgs):
        font = self.font
        if bold:
            font = self.fontBold
        label = tk.Label(parent, text=text, font=font, bg='white')
        if gridArgs:
            gridDefaults = {'row': 0, 'column': 0, 'padx': 5, 'pady': 5}
            gridDefaults.update(gridArgs)
            label.grid(**gridDefaults)
        return label
    
    def resize(self, frame):
        self.root.update_idletasks()
        MaxHeight = 1200
        MaxWidth = 1600
        rh = frame.winfo_reqheight()
        rw = frame.winfo_reqwidth()
        height = min(rh + 100, MaxHeight)
        width = min(rw, MaxWidth)
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry("%dx%d%+d%+d" % (width, height, x, y))

        return width, height
    
    def adjustSize(self):
        self.resize(self.root)        
        
    def save(self, e=None):
        self._close(onlySave=True)

    def schedule(self):
        if self.protocol.useQueue():
            if not self._editQueueParams():
                return

        self._close(doSchedule=True)

    def execute(self, e=None):

        if self.protocol.useQueue():
            if not self._editQueueParams():
                return
        else:  # use queue = No
            hostConfig = self._getHostConfig()
            cores = self.protocol.numberOfMpi.get(1) * self.protocol.numberOfThreads.get(1)
            mandatory = hostConfig.queueSystem.getMandatory()

            if mandatory and cores >= mandatory:
                self.showWarning("You need to submit the job to queue since you \n"
                                 "are requesting a total of *%d* cores (MPI * threads)\n\n"
                                 "*Note*: Your system is configured with MANDATORY = %d.\n"  
                                 "        This value can be changed in Scipion/config/hosts.conf" % (cores, mandatory))
                return
        if self.protocol.getRunMode() == MODE_RESTART:
            protocolList = ""
            if self.protocol.getObjId():
                project = self.protocol.getProject()
                errorProList, workflowProtocolList = self.protocol.getProject()._checkWorkflowErrors(self.protocol)
                for prot in workflowProtocolList:
                    protocolList += ("\n* " + self.protocol.getProject().getProtocol(prot).getRunName())
                if len(workflowProtocolList) > 1:
                    result = askSingleAllCancel(pwutils.Message.TITLE_RESTART_FORM,
                                 pwutils.Message.LABEL_RESTART_FORM % ('%s\n' % protocolList),
                                 self.root)
                    if result == RESULT_RUN_ALL:
                        self.protocol._store()
                        self.protocol.getProject()._storeProtocol(self.protocol)
                        project.launchWorkflow(self.protocol, mode=MODE_RESTART)
                        self.close()
                        return
                    elif result == RESULT_RUN_SINGLE and not self.protocol.isSaved():
                         project.resetWorkFlow(self.protocol)
                    elif result == RESULT_CANCEL:
                        return
                elif not askYesNo(pwutils.Message.TITLE_RESTART_FORM,
                             pwutils.Message.LABEL_RESTART_FORM % (
                                         '*%s*' % self.protocol.getRunName()),
                             self.root):
                    return

        errors = self.protocol.validate()
        
        if errors:
            self.showInfo(errors)
        else:
            warns = self.protocol.warnings()
            if warns and not self.askYesNo("There are some warnings",
                                           '\n'.join(warns + ['\nDo you want to continue?'])):
                return
            self._close()
        
    def _close(self, onlySave=False, doSchedule=False):
        try:
            # Set the protocol label
            self.updateProtocolLabel()
            
            message = self.callback(self.protocol, onlySave, doSchedule)
            if not self.visualizeMode:
                if len(message):
                    self.showInfo(message, "Protocol action")
                if not onlySave:
                    self.close()
        except ModificationNotAllowedException as ex:
            self.showInfo("Save not allowed. There are protocols executed "
                          "hanging from this one. Modifying values will break"
                          " traceability.\n\n %s\n" % ex)
        except Exception as ex:
            import traceback
            traceStr = traceback.format_exc()
            action = "EXECUTE"
            if onlySave:
                action = "SAVE"
            self.showError("Error during %s: %s\n\nTraceback:\n%s" % (action, ex, traceStr))

    def getWidgetValue(self, protVar, param):
        widgetValue = ""                
        if (isinstance(param, pwprot.PointerParam) or 
            isinstance(param, pwprot.MultiPointerParam) or
                isinstance(param, pwprot.RelationParam)):
            widgetValue = protVar
        # For Scalar params that allowPointers
        elif param.allowsPointers:
            if protVar.hasPointer():
                # Get the pointer
                widgetValue = protVar.getPointer()
            else:
                widgetValue = protVar.get()
        else:
            widgetValue = protVar.get(param.default.get())  
        return widgetValue
          
    def _visualize(self, paramName):
        protVar = getattr(self.protocol, paramName)
        if protVar.hasValue():
            obj = protVar.get()  # Get the reference to the object
            viewers = pw.Config.getDomain().findViewers(obj.getClassName(), DESKTOP_TKINTER)
            if len(viewers):
                ViewerClass = viewers[0]  # Use the first viewer registered
                v = ViewerClass(project=self.protocol.getProject(),
                                protocol=self.protocol, parent=self)
                v.visualize(obj)  # Instantiate the viewer and visualize object
            else:
                self.showInfo("There is no viewer registered for this object")
        else:
            self.showInfo("Select the object before visualize")
         
    def _fillSection(self, sectionParam, sectionWidget):
        parent = sectionWidget.contentFrame
        r = 0
        for paramName, param in sectionParam.iterParams():
            if isinstance(param, pwprot.Group):
                widget = GroupWidget(r, paramName, param, self, parent)
                self._fillGroup(param, widget)
            elif isinstance(param, pwprot.Line):
                widget = LineWidget(r, paramName, param, self, parent, None)
                self._fillLine(param, widget)
            else:
                protVar = getattr(self.protocol, paramName, None)
                
                if protVar is None:
                    raise Exception("_fillSection: param '%s' not found in protocol" % paramName)
                
                if sectionParam.getQuestionName() == paramName:
                    widget = sectionWidget
                    if not protVar:
                        widget.hide()  # Show only if question var is True
                else:
                    if isinstance(param, pwprot.PointerParam):
                        visualizeCallback = self._visualize  # Add visualize icon for pointer params
                    else:
                        visualizeCallback = self.visualizeDict.get(paramName, None)
                    
                    widget = ParamWidget(r, paramName, param, self, parent, 
                                         value=self.getWidgetValue(protVar, param),
                                         callback=self._checkChanges,
                                         visualizeCallback=visualizeCallback)
                        
                    widget.show()  # Show always, conditions will be checked later
            r += 1         
            self.widgetDict[paramName] = widget
        # Ensure width and height needed
        w, h = parent.winfo_reqwidth(), parent.winfo_reqheight()
        sectionWidget.columnconfigure(0, minsize=w)
        sectionWidget.rowconfigure(0, minsize=h)

    def _fillGroup(self, groupParam, groupWidget):
        parent = groupWidget.content
        r = 0
        for paramName, param in groupParam.iterParams():
            if isinstance(param, pwprot.Line):
                widget = LineWidget(r, paramName, param, self, parent, None)
                self._fillLine(param, widget)
            else:
                protVar = getattr(self.protocol, paramName, None)
                
                if protVar is None:
                    raise Exception("_fillSection: param '%s' not found in protocol" % paramName)
                
                if isinstance(param, pwprot.PointerParam):
                    visualizeCallback = self._visualize  # Add visualize icon for pointer params
                else:
                    visualizeCallback = self.visualizeDict.get(paramName, None)
                
                widget = ParamWidget(r, paramName, param, self, parent, 
                                     value=self.getWidgetValue(protVar, param),
                                     callback=self._checkChanges,
                                     visualizeCallback=visualizeCallback)
                widget.show()  # Show always, conditions will be checked later
            r += 1         
            self.widgetDict[paramName] = widget
 
    def _fillLine(self, groupParam, groupWidget):
        parent = groupWidget.content
        c = 0
        for paramName, param in groupParam.iterParams():
            protVar = getattr(self.protocol, paramName, None)
            
            if protVar is None:
                raise Exception("_fillSection: param '%s' not found in protocol" % paramName)
            
            if isinstance(param, pwprot.PointerParam):
                visualizeCallback = self._visualize  # Add visualize icon for pointer params
            else:
                visualizeCallback = self.visualizeDict.get(paramName, None)
            
            widget = ParamWidget(0, paramName, param, self, parent, 
                                 value=self.getWidgetValue(protVar, param),
                                 callback=self._checkChanges, visualizeCallback=visualizeCallback,
                                 column=c, showButtons=False)
            widget.show()  # Show always, conditions will be checked later
            c += 2
            self.widgetDict[paramName] = widget

    def _checkCondition(self, paramName):
        """Check if the condition of a param is statisfied 
        hide or show it depending on the result"""
        widget = self.widgetDict.get(paramName, None)
        
        if isinstance(widget, ParamWidget):  # Special vars like MPI, threads or runName are not real widgets
            if isinstance(widget, LineWidget) or isinstance(widget, GroupWidget):
                param = widget.param
            else:
                param = self.protocol.getParam(paramName)
            cond = self.protocol.evalParamCondition(paramName) and self.protocol.evalParamExpertLevel(param)
            widget.display(cond)
            
    def _checkChanges(self, paramName):
        """Check the conditions of all params affected
        by this param"""
        self.setParamFromVar(paramName)
        param = self.protocol.getParam(paramName)
        
        for d in param._dependants:
            self._checkCondition(d)
            
    def _checkAllChanges(self):
        for paramName in self.widgetDict:
            self._checkCondition(paramName)
            
    def _onExpertLevelChanged(self, *args):
        self._checkAllChanges()
        self.root.update_idletasks()
        for s in self._sections:
            s.adjustContent()
            
    def _setThreadsOrMpi(self, *args):
        mode = self.procTypeVar.get()
        prot = self.protocol  # shortcut notation
        try:
            procs = int(self.widgetDict['numberOfThreads'].get())
            if mode == THREADS:  # threads mode
                prot.numberOfThreads.set(procs)
                prot.numberOfMpi.set(min(1, prot.numberOfMpi.get()))  # 0 or 1
            else:
                prot.numberOfMpi.set(procs)
                m = min(1, prot.numberOfThreads.get())  # 0 or 1
                prot.numberOfThreads.set(m)
        except Exception:
            pass

    def _setGpu(self, *args):
        prot = self.protocol  # shortcut notation
        if not prot.requiresGpu():  # Only set this if gpu is optional
            prot.useGpu.set(self.useGpuVar.get())
        prot.gpuList.set(self.gpuListVar.get())

    def _setWaitFor(self, *args):
        l1 = self.waitForVar.get().split(',')
        idList = []
        for p1 in l1:
            idList.extend([p2.strip() for p2 in p1.split(' ') if p2])
        try:
            idIntList = map(int, idList)
            self.protocol.setPrerequisites(*idIntList)
        except Exception as ex:
            pass

    def _setHostName(self, *args):
        self.protocol.setHostName(self.hostVar.get())        
        
    def _onRunModeChanged(self, paramName):
        self.setParamFromVar(paramName)
        
    def getVarValue(self, varName):
        """This method should retrieve a value from """
        pass
        
    def setVar(self, paramName, value):
        var = self.widgetDict[paramName]
        var.set(value)
        
    def setVarFromParam(self, paramName):
        var = self.widgetDict[paramName]
        param = getattr(self.protocol, paramName, None)
        if param is not None:
            # Special treatment to pointer params
            if isinstance(param, pwobj.Pointer):
                var.set(param)
            else:
                var.set(param.get(''))
           
    def setParamFromVar(self, paramName):
        param = getattr(self.protocol, paramName, None)
        if param is not None:
            widget = self.widgetDict[paramName]
            try:
                value = widget.get()

                # Special treatment for pointer params
                if isinstance(param, pwobj.Pointer):
                    param.copy(value)
                # Special treatment for Scalars that allow pointers
                # Combo widgets do not have .param!
                elif hasattr(widget, "param") and widget.param.allowsPointers:
                    if isinstance(value, pwobj.Pointer):
                        # Copy the pointer, otherwise changes in the
                        # widget pointer will be reflected
                        pointerCopy = pwobj.Pointer()
                        pointerCopy.copy(value)
                        param.setPointer(pointerCopy)
                    else:
                        param.setPointer(None)
                        param.set(value)

                elif isinstance(param, pwobj.Object):
                    param.set(value)
            except ValueError:
                if len(value):
                    print(">>> ERROR: setting param for: ", paramName,
                          "value: '%s'" % value)
                param.set(None)
                
    def updateLabelAndCommentVars(self):
        """ Read the label and comment first line to update
        the entry boxes in the form.
        """
        self.runNameVar.set(self.protocol.getObjLabel())
        # Get only the first comment line
        comment = self.protocol.getObjComment()
        if comment:
            lines = comment.split('\n')
            if lines:
                comment = lines[0]
        self.commentVar.set(comment)
        
    def updateProtocolLabel(self):
        self.protocol.setObjLabel(self.runNameVar.get())
             
    def updateProtocolParams(self):
        """ This method is only used from WEB, since in Tk all params
        are updated when they are changed.
        """
        for paramName, _ in self.protocol.iterDefinitionAttributes():
            self.setParamFromVar(paramName)

    def _onPointerChanged(self, *args):
        btnExecute = getattr(self, 'btnExecute', None)

        # This event can be fired even before the button is created
        if btnExecute is None:
            return

        if self.protocol.hasLinkedInputs():
            btnText = 'Schedule'
            cmd = self.schedule
        else:
            btnText = pwutils.Message.LABEL_BUTTON_EXEC
            cmd = self.execute

        btnExecute.config(text=btnText, command=cmd)


def editObject(self, title, root, obj, mapper):
    """ Show a Text area to edit the protocol label and comment. """    
    return EditObjectDialog(root, title, obj, mapper)
    

class QueueDialog(Dialog):
    """ Dialog to entry the queue parameters. """
    def __init__(self, window, queueDict):
        self.value = None
        self.widgets = []  # widget list
        self.vars = []
        self.queueDict = queueDict
        self.window = window
        self.queueName, queueParams = window.protocol.getQueueParams()
        # If there is only one queue and not one selected, use the first one
        if not self.queueName and len(queueDict.keys()) == 1:
            self.queueName = list(queueDict.keys())[0]
            queueParams = {}
        # Store all selected queue parameters to 
        # preserve values when temporarily changed
        # from one queue to another    
        self.allQueueParams = {self.queueName: queueParams}
        
        Dialog.__init__(self, window.root, "Queue parameters")
        
    def body(self, bodyFrame):
        bodyFrame.config(bg='white')
        self.content = tk.Frame(bodyFrame, bg='white')
        self.content.grid(row=0, column=0, padx=20, pady=20)
        
        label = tk.Label(self.content, text='Submit to queue', 
                         font=self.window.fontBold, bg='white')
        label.grid(row=0, column=0, sticky='ne', padx=5, pady=5)
        self.queueVar = tk.StringVar()
        self.queueVar.trace('w', self._onQueueChanged)
        combo = ttk.Combobox(self.content, textvariable=self.queueVar, 
                             state='readonly', width=14)
        combo.grid(row=0, column=1, sticky='nw', padx=5, pady=5)
        queueKeys = list(self.queueDict.keys())
        combo['values'] = queueKeys
        self.queueVar.set(self.queueName)  # This will trigger queue params setup
        self.initial_focus = combo
        
    def _onQueueChanged(self, *args):
        for w in self.widgets:
            w.destroy()
            
        selected = self.queueVar.get()
        
        if selected != self.queueName:
            # Store previous selection 
            _, previousParams = self._getSelectedParams(self.queueName)
            self.allQueueParams[self.queueName] = previousParams
            self.queueName = selected
            
        # Load default params from the queues
        params = self.queueDict.get(selected, {})
        # Load previous selected params
        selectedParams = self.allQueueParams.get(selected, {})
        
        self.widgets = []  # clear the widget list
        self.vars = []
        r = 1  # starting row to place params
        for p in params:
            if len(p) == 3:  # No help provided
                name, value, label = p
                helpMsg = None
            elif len(p) == 4:
                name, value, label, helpMsg = p
            else:
                raise Exception('Incorrect number of params for %s, expected 3 or 4' % p[0])
            
            label = tk.Label(self.content, text=label, bg='white')
            label.grid(row=r, column=0, sticky='ne', padx=5, pady=(0, 5))
            var = tk.StringVar()
            # Set the value coming in the protocol 
            var.set(selectedParams.get(name, value))
            
            entry = tk.Entry(self.content, textvariable=var, width=15)
            entry.grid(row=r, column=1, sticky='nw', padx=5, pady=(0, 5))
            
            if helpMsg:
                def addHelpButton(name, helpMsg):
                    def showHelp():
                        showInfo("Help", helpMsg, self)
                    
                    btn = IconButton(self.content, pwutils.Message.LABEL_BUTTON_HELP, 
                                     pwutils.Icon.ACTION_HELP,
                                     command=showHelp)
                    btn.grid(row=r, column=2, sticky='ne', padx=5, pady=(0, 5))
                    self.widgets.append(btn)
                addHelpButton(name, helpMsg)
            
            self.vars.append(var)
            self.widgets.append(label)
            self.widgets.append(entry)
            r += 1
        
    def _getSelectedParams(self, selected):
        if selected in self.queueDict:
            paramsDict = {}
            params = self.queueDict[selected]
            for p, v in zip(params, self.vars):
                if len(p) == 3:
                    name, value, label = p
                else: 
                    name, value, label, _ = p 
                paramsDict[name] = v.get()  # get the value from the corresponding tk var
            return selected, paramsDict
        return '', {}
            
    def apply(self):
        # Set as value the queue selected and a dictionary 
        # with the values of each parameter
        selected = self.queueVar.get()
        self.value = self._getSelectedParams(selected)
        
    def validate(self):
        return True
