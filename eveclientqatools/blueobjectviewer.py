#Embedded file name: eveclientqatools\blueobjectviewer.py
from eve.client.script.ui.control import entries as listentry
import carbonui.const as uiconst
import uicontrols
import trinity
TYPE_UNKNOWN = 'unknown'
TYPE_BLUE_LIST = 'blue.List'

class BlueTreeMaster(object):

    def __init__(self, maxRecursion = 20):
        self.blueObjects = {}
        self.maxRecursion = maxRecursion

    def GetNodeForBlueObject(self, blueObject):
        return self.blueObjects.get(blueObject, None)

    def RegisterBlueObject(self, blueObjectNode):
        self.blueObjects[blueObjectNode.value] = blueObjectNode


class BaseNode(object):
    _nextID = 0

    def __init__(self, treeMaster):
        self.displayName = '<empty>'
        self._id = BaseNode._nextID
        self.master = treeMaster
        self.value = None
        BaseNode._nextID += 1

    def GetDisplayName(self):
        return self.displayName

    def GetID(self):
        return self._id

    def SetValue(self, value):
        pass


class BlueListNode(BaseNode):

    def __init__(self, treeMaster, parent, parentAttr):
        BaseNode.__init__(self, treeMaster)
        self.parent = parent
        self.parentAttr = parentAttr
        self.members = []
        self.displayName = parentAttr
        self.typeName = 'blue.List'
        self.value = None

    def Refresh(self, cnt = 0):
        if cnt > self.master.maxRecursion:
            return
        self.value = getattr(self.parent, self.parentAttr)
        del self.members[:]
        for each in self.value:
            m = BlueObjectRootNode(self.master, each, each.__bluetype__)
            m.Refresh(cnt + 1)
            self.members.append((m.displayName, m))


class BlueObjectNode(BaseNode):

    def __init__(self, treeMaster):
        BaseNode.__init__(self, treeMaster)
        self.members = []
        self.value = None
        self.master.RegisterBlueObject(self)

    def Refresh(self, cnt = 0):
        if cnt > self.master.maxRecursion:
            return
        self.members = []
        if self.value is None:
            return
        for attr in self.value.__members__:
            if not attr.startswith('__') and self.GetMemberByAttr(attr) is None:
                m = GetMember(self.master, self.value, attr)
                if m is not None:
                    self.members.append((attr, m))

        for each in self.members:
            each[1].Refresh(cnt + 1)

    def GetMemberByAttr(self, attr):
        for k, val in self.members:
            if k == attr:
                return val


class BlueObjectChildNode(BlueObjectNode):

    def __init__(self, treeMaster, parent, parentAttr, blueType):
        BlueObjectNode.__init__(self, treeMaster)
        self.parent = parent
        self.parentAttr = parentAttr
        self.displayName = parentAttr
        self.typeName = blueType

    def Refresh(self, cnt = 0):
        if cnt > self.master.maxRecursion:
            return
        self.value = getattr(self.parent, self.parentAttr)
        BlueObjectNode.Refresh(self, cnt + 1)


class BlueObjectRootNode(BlueObjectNode):

    def __init__(self, treeMaster, obj, blueType):
        BlueObjectNode.__init__(self, treeMaster)
        self.typeName = blueType
        self.value = obj
        self.displayName = getattr(obj, 'name', str(obj)) or obj.__typename__


class ValueNode(BaseNode):

    def __init__(self, treeMaster, parent, parentAttr):
        BaseNode.__init__(self, treeMaster)
        self.displayName = parentAttr
        self.parent = parent
        self.attr = parentAttr
        self.value = None

    def Refresh(self, cnt = 0):
        self.value = getattr(self.parent, self.attr, None)


class ChooserNode(ValueNode):

    def __init__(self, treeMaster, parent, parentAttr, options):
        ValueNode.__init__(self, treeMaster, parent, parentAttr)
        self.displayName = parentAttr
        self.options = options

    def Refresh(self, cnt = 0):
        current = getattr(self.parent, self.attr, None)
        if current is None:
            self.value = None
        else:
            self.value = self.options[current]


def GetMember(master, obj, attr):
    if obj is None:
        return
    val = getattr(obj, attr)
    trinityType = None
    try:
        iid = obj.TypeInfo()[2][attr]['iid_name']
        if iid and hasattr(trinity, iid):
            trinityType = 'trinity.' + iid
    except:
        pass

    blueType = getattr(val, '__bluetype__', None)
    if blueType == TYPE_BLUE_LIST:
        return BlueListNode(master, obj, attr)
    if trinityType is not None:
        node = master.GetNodeForBlueObject(val)
        if node is None or val is None:
            return BlueObjectChildNode(master, obj, attr, trinityType)
        else:
            return node
    if type(val) == int:
        if obj.TypeInfo()[2][attr]['choosers']:
            choosers = obj.TypeInfo()[2][attr]['choosers']
            options = {}
            for name, value, desc in choosers:
                options[value] = name

            return ChooserNode(master, obj, attr, options)
        else:
            return ValueNode(master, obj, attr)
    else:
        if type(val) == str or type(val) == unicode:
            return ValueNode(master, obj, attr)
        if type(val) == float:
            return ValueNode(master, obj, attr)
        if type(val) == bool:
            return ValueNode(master, obj, attr)
        if type(val) == tuple:
            return ValueNode(master, obj, attr)


class TreeListWnd:

    def __init__(self, tree):
        self.tree = tree
        self.headers = ['', 'value']

    def Show(self):
        winID = 'MyTreeListWnd'
        uicontrols.Window.CloseIfOpen(windowID=winID)
        wnd = uicontrols.Window.Open(windowID=winID)
        wnd.SetTopparentHeight(0)
        wnd.height = 400
        wnd.SetMinSize([400, 300])
        wnd.width = 510
        wnd.SetCaption('Blue Object Viewer')
        main = wnd.GetMainArea()
        self.scroll = uicontrols.Scroll(parent=main, align=uiconst.TOALL, padding=(5, 5, 5, 5))
        self.scroll.sr.id = 'somerandomid'
        self.DoSomeContent()

    def GetAContainerNode(self, sublevel, map_node):
        node = {'label': map_node.displayName,
         'sublevel': sublevel,
         'id': (123, map_node),
         'RefreshScroll': self.Dummy,
         'GetSubContent': self.GroupGetSubContent}
        return listentry.Get('Group', node)

    def Dummy(self, *args):
        return []

    def GetAnEntryNode(self, sublevel, map_node):
        node = {'label': '%s<t>%s' % (map_node.displayName, str(map_node.value)),
         'sublevel': sublevel,
         'id': (123, map_node)}
        return listentry.Get('Generic', node)

    def GetEntryFor(self, map_node, sublevel):
        if len(getattr(map_node, 'members', [])) > 0:
            return self.GetAContainerNode(sublevel, map_node)
        else:
            return self.GetAnEntryNode(sublevel, map_node)

    def GroupGetSubContent(self, node, newitems = 0):
        ret = []
        sublevel = node.get('sublevel', 0)
        map_node = node.id[1]
        if sublevel > 10:
            return []
        for attr, obj in map_node.members:
            ret.append(self.GetEntryFor(obj, sublevel + 1))

        return ret

    def GetContent(self):
        return [self.GetEntryFor(self.tree, 0)]

    def DoSomeContent(self):
        self.scroll.Load(contentList=self.GetContent(), headers=self.headers, fixedEntryHeight=None)


def Show(obj):
    born = BlueObjectRootNode(BlueTreeMaster(), obj, obj.__bluetype__)
    born.Refresh()
    wnd = TreeListWnd(born)
    wnd.Show()
