#Embedded file name: eve/client/script/ui/control\treeData.py


class TreeData:

    def __init__(self, label = None, parent = None, children = None, icon = None, isRemovable = False, settings = None, **kw):
        self._label = label
        self._children = children or []
        if isinstance(self._children, tuple):
            self._children = list(self._children)
        self._parent = parent
        if parent:
            parent.AddChild(self)
        for child in self._children:
            child._parent = self

        self._kw = kw
        self._icon = icon
        self._isRemovable = isRemovable
        self._settings = settings

    def GetSettings(self):
        return self._settings

    settings = property(GetSettings)

    def GetParent(self):
        return self._parent

    parent = property(GetParent)

    def GetRootNode(self):
        if not self.parent:
            return self
        return self.parent.GetRootNode()

    def GetLabel(self):
        return self._label or ''

    def GetIcon(self):
        return self._icon

    def GetMenu(self):
        return []

    def GetHint(self):
        return None

    def GetID(self):
        return (self._label, tuple(self._kw.keys()))

    def GetChildren(self):
        return self._children

    children = property(GetChildren)

    def AddChild(self, child):
        if child not in self._children:
            self._children.append(child)

    def RemoveChild(self, child):
        if child in self._children:
            self._children.remove(child)

    def GetChildByID(self, dataID, recursive = True):
        if dataID == self.GetID():
            return self
        if self.IsForceCollapsed():
            return None
        children = self.GetChildren()
        for child in children:
            if child.GetID() == dataID:
                return child

        for child in children:
            ret = child.GetChildByID(dataID)
            if ret:
                return ret

    def IsDraggable(self):
        return False

    def HasChildren(self):
        return bool(self._children)

    def IsRemovable(self):
        return self._isRemovable

    def IsForceCollapsed(self):
        return False

    def GetPathToDescendant(self, dataID, forceGetChildren = False):
        """ Returns a list representing the path from this node to it's child if found """
        if self.GetID() == dataID:
            return [self]
        if self.HasChildren():
            if not forceGetChildren and self.IsForceCollapsed():
                return None
            for child in self.GetChildren():
                found = child.GetPathToDescendant(dataID, forceGetChildren)
                if found:
                    return [self] + found

    def GetAncestors(self):
        parent = self.GetParent()
        if parent:
            ancestors = parent.GetAncestors()
            ancestors.append(parent)
            return ancestors
        else:
            return []

    def GetDescendants(self, forceGetChildren = False):
        """ Returns all descendants of node """
        ret = {}
        if self.HasChildren():
            if not forceGetChildren and self.IsForceCollapsed():
                return {}
            for child in self.GetChildren():
                ret[child.GetID()] = child
                ret.update(child.GetDescendants())

        return ret

    def IsDescendantOf(self, invID):
        parent = self.GetParent()
        if not parent:
            return False
        if invID == parent.GetID():
            return True
        return parent.IsDescendantOf(invID)
