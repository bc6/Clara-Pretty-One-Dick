#Embedded file name: eve/client/script/ui/control\baseListEntry.py
from carbonui.control.scrollentries import OPACITY_IDLE, OPACITY_HOVER, OPACITY_SELECTED, OPACITY_MOUSEDOWN, SE_BaseClassCore
from carbonui.primitives.container import Container
import carbonui.const as uiconst
from carbonui.primitives.line import Line
from carbonui.primitives.fill import Fill
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.control.eveWindowUnderlay import FillUnderlay

class BaseListEntry(SE_BaseClassCore):
    """ 
    An abstract list entry class with hover effects and basic interaction events
    """
    default_name = 'BaseListEntry'
    default_align = uiconst.TOPLEFT
    default_height = 20
    isDragObject = True

    def Load(self, *args):
        pass

    def ApplyAttributes(self, attributes):
        SE_BaseClassCore.ApplyAttributes(self, attributes)
        self.node = self.sr.node = attributes.node
        if not self.node.Get('hideLines', None):
            Line(align=uiconst.TOBOTTOM, parent=self, color=uiconst.ENTRY_LINE_COLOR)
        if self.node.selected:
            self.Select()

    @classmethod
    def GetCopyData(cls, node):
        return ''

    def GetHint(self):
        return self.node.hint

    @classmethod
    def GetDynamicHeight(cls, node, width = None):
        return node.height or cls.default_height

    def OnMouseHover(self, *args):
        if self.node.Get('OnMouseHover', None):
            self.node.OnMouseHover(self)

    def OnMouseEnter(self, *args):
        SE_BaseClassCore.OnMouseEnter(self, *args)
        if self.node.Get('OnMouseEnter', None):
            self.node.OnMouseEnter(self)

    def OnMouseExit(self, *args):
        SE_BaseClassCore.OnMouseExit(self, *args)
        if self.node.Get('OnMouseExit', None):
            self.node.OnMouseExit(self)

    def OnClick(self, *args):
        sm.GetService('audio').SendUIEvent('wise:/msg_ListEntryClick_play')
        if self.node.Get('selectable', 1):
            self.node.scroll.SelectNode(self.node)
        if self.node.Get('OnClick', None):
            self.node.OnClick(self)

    def OnDblClick(self, *args):
        self.node.scroll.SelectNode(self.node)
        if self.node.Get('OnDblClick', None):
            if isinstance(self.node.OnDblClick, tuple):
                func = self.node.OnDblClick[0]
                func(self, *self.node.OnDblClick[1:])
            else:
                self.node.OnDblClick(self)

    def OnMouseDown(self, *args):
        SE_BaseClassCore.OnMouseDown(self, *args)
        if self.node.Get('OnMouseDown', None):
            self.node.OnMouseDown(self)

    def OnMouseUp(self, *args):
        SE_BaseClassCore.OnMouseUp(self, *args)
        if self.node.Get('OnMouseUp', None):
            self.node.OnMouseUp(self)

    def GetMenu(self):
        if not self.node.Get('ignoreRightClick', 0):
            self.OnClick()
        if self.node.Get('GetMenu', None):
            return self.node.GetMenu(self)
        return []

    def OnDropData(self, dragObj, nodes):
        if self.node.OnDropData:
            self.node.OnDropData(dragObj, nodes)

    def DoSelectNode(self, toggle = 0):
        self.node.scroll.GetSelectedNodes(self.node, toggle=toggle)

    def GetRadialMenuIndicator(self, create = True, *args):
        indicator = getattr(self, 'radialMenuIndicator', None)
        if indicator and not indicator.destroyed:
            return indicator
        if not create:
            return
        self.radialMenuIndicator = Fill(bgParent=self, color=(1, 1, 1, 0.25), name='radialMenuIndicator')
        return self.radialMenuIndicator

    def ShowRadialMenuIndicator(self, slimItem, *args):
        indicator = self.GetRadialMenuIndicator(create=True)
        indicator.display = True

    def HideRadialMenuIndicator(self, slimItem, *args):
        indicator = self.GetRadialMenuIndicator(create=False)
        if indicator:
            indicator.display = False


class BaseListEntryCustomColumns(BaseListEntry):
    """ A base list entry where each column is a ui container, allowing for more flexibility """
    default_name = 'BaseListEntryCustomColumns'

    def ApplyAttributes(self, attributes):
        BaseListEntry.ApplyAttributes(self, attributes)
        self.columns = []

    def AddColumnContainer(self):
        """ Add a container column """
        column = Container(align=uiconst.TOLEFT, parent=self, clipChildren=True, padRight=1)
        self.columns.append(column)
        return column

    def AddColumnText(self, text):
        """ Add a standard label column """
        column = self.AddColumnContainer()
        return Label(parent=column, text=text, align=uiconst.CENTERLEFT, left=6)

    def OnColumnResize(self, newCols):
        for i, width in enumerate(newCols):
            self.columns[i].width = width - 1
