#Embedded file name: carbonui/primitives\backgroundList.py
import weakref
from .base import Base

class BackgroundList(object):
    """
    BackgroundList is used by Container to hold UI objects intended for the
    background of a container. This is essentially a wrapper around a Python
    list with callbacks to the owner object when items are added or removed.
    These callbacks then mirror the change over to the render object.
    
    Note that this class is almost an exact copy of ChildreList, but rather
    than having one class with bound functions for the callbacks we duplicate
    the code. This prevents a circular reference.
    """
    __guid__ = 'uiprimitives.BackgroundList'

    def __init__(self, owner):
        self._childrenObjects = []
        self._ownerRef = weakref.ref(owner)

    def GetOwner(self):
        if self._ownerRef:
            return self._ownerRef()

    def append(self, obj):
        return self.insert(None, obj)

    def insert(self, idx, obj):
        if not isinstance(obj, Base):
            print 'Someone trying to add item which is not of correct type', obj
            return
        owner = self.GetOwner()
        if owner:
            obj._parentRef = weakref.ref(owner)
            if idx == -1 or idx is None:
                self._childrenObjects.append(obj)
                owner.AppendBackgroundObject(obj)
            else:
                self._childrenObjects.insert(idx, obj)
                owner.InsertBackgroundObject(idx, obj)
            owner.UpdateBackgrounds()
            return self

    def remove(self, obj):
        try:
            self._childrenObjects.remove(obj)
        except ValueError:
            pass

        obj._parentRef = None
        owner = self.GetOwner()
        if owner:
            owner.RemoveBackgroundObject(obj)
        return self

    def index(self, obj):
        return self._childrenObjects.index(obj)

    def __getitem__(self, key):
        return self._childrenObjects[key]

    def __len__(self):
        return len(self._childrenObjects)

    def __iter__(self):
        return iter(self._childrenObjects)

    def __getslice__(self, f, t):
        return self._childrenObjects[f:t]

    def __contains__(self, obj):
        return obj in self._childrenObjects

    def __cmp__(self, other):
        return cmp(other, self._childrenObjects)

    def __reversed__(self):
        return reversed(self._childrenObjects)

    def __delitem__(self, key):
        del self._childrenObjects[key]
