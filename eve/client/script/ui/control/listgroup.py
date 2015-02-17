#Embedded file name: eve/client/script/ui/control\listgroup.py
from carbonui.control.scrollentries import SE_ListGroupCore
from eve.client.script.ui.control.glowSprite import GlowSprite
from eve.client.script.ui.control.themeColored import FillThemeColored
import uicontrols
import uiprimitives
import util
import uix
import uiutil
import carbonui.const as uiconst
import log
import localization
import const
import telemetry
from eve.client.script.ui.control.eveWindow import Window

class VirtualGroupWindow(Window):
    __guid__ = 'form.VirtualGroupWindow'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        node = attributes.node
        caption = attributes.caption or 'List window'
        self.SetScope('station_inflight')
        self.SetMinSize((200, 200))
        self.SetTopparentHeight(0)
        self.sr.data = node.copy()
        main = uiutil.GetChild(self, 'main')
        main.Flush()
        icon = getattr(self.sr.data, 'showicon', '')
        if icon == 'hide':
            self.SetCaption(caption)
            self.SetWndIcon('ui_9_64_14')
        elif icon and icon[0] == '_':
            self.SetWndIcon(icon[1:], 1, size=32)
            self.SetCaption(caption)
        else:
            self.SetCaption(caption)
            self.SetWndIcon('res:/ui/Texture/WindowIcons/smallfolder.png', 1, size=32)
            if icon:
                mainicon = uiutil.GetChild(self, 'mainicon')
                mainicon.LoadIcon(icon, ignoreSize=True)
                mainicon.SetSize(32, 32)
                mainicon.state = uiconst.UI_DISABLED
            else:
                self.SetWndIcon('res:/ui/Texture/WindowIcons/smallfolder.png', 1, size=32)
        self.sr.scroll = uicontrols.Scroll(name='scroll', parent=main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding), align=uiconst.TOALL)
        self.sr.scroll.sr.iconMargin = getattr(self.sr.data, 'iconMargin', 0)
        ignoreTabTrimming = util.GetAttrs(node, 'scroll', 'sr', 'ignoreTabTrimming') or 0
        self.sr.scroll.sr.ignoreTabTrimming = ignoreTabTrimming
        minColumnWidth = util.GetAttrs(node, 'scroll', 'sr', 'minColumnWidth') or {}
        self.sr.scroll.sr.minColumnWidth = minColumnWidth
        self.sr.scroll.sr.content.OnDropData = self.OnDropData

    def _OnClose(self, *args):
        self.sr.data = None

    def LoadContent(self, newNode = None, newCaption = None):
        if not self or self.destroyed:
            return
        if newNode:
            self.sr.data = newNode.Copy()
        if newCaption:
            self.SetCaption(newCaption)
        if self.sr.data.GetSubContent:
            content = self.sr.data.GetSubContent(self.sr.data, 1)
        else:
            raise RuntimeError('LoadContent: WTF')
        if self.sr.data.scroll.sr.id:
            self.sr.scroll.sr.id = '%s_%s' % (self.sr.data.scroll.sr.id, self.sr.data.id)
        self.sr.scroll.sr.fixedColumns = self.sr.data.scroll.sr.fixedColumns.copy()
        self.sr.scroll.Load(contentList=content, headers=self.sr.data.scroll.GetColumns(), fixedEntryHeight=self.sr.data.scroll.sr.fixedEntryHeight, scrolltotop=0)

    def OnDropData(self, dragObj, nodes):
        if getattr(self.sr.data, 'DropData', None):
            self.sr.data.DropData(self.sr.data.id, nodes)
            return
        ids = []
        myListGroupID = self.sr.data.id
        for node in nodes:
            if node.__guid__ not in self.sr.data.get('allowGuids', []):
                log.LogWarn('dropnode.__guid__ has to be listed in group.node.allowGuids', node.__guid__, getattr(self.sr.data, 'allowGuids', []))
                continue
            if not node.Get('itemID', None):
                log.LogWarn('dropitem data has to have itemID')
                continue
            currentListGroupID = node.Get('listGroupID', None)
            ids.append((node.itemID, currentListGroupID, myListGroupID))

        for itemID, currentListGroupID, myListGroupID in ids:
            if currentListGroupID and itemID:
                uicore.registry.RemoveFromListGroup(currentListGroupID, itemID)
            uicore.registry.AddToListGroup(myListGroupID, itemID)

        uicore.registry.ReloadGroupWindow(myListGroupID)
        if getattr(self.sr.data, 'RefreshScroll', None):
            self.sr.data.RefreshScroll()


class ListGroup(uicontrols.SE_ListGroupCore):
    __guid__ = 'listentry.Group'
    default_iconSize = 16

    @telemetry.ZONE_METHOD
    def Startup(self, *etc):
        self.sr.expander = GlowSprite(parent=self, pos=(3, 0, 16, 16), name='expander', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Shared/expanderDown.png', align=uiconst.CENTERLEFT)
        self.sr.expander.OnClick = self.Toggle
        self.sr.icon = uicontrols.Icon(parent=self, pos=(4, 0, 16, 16), name='icon', state=uiconst.UI_DISABLED, icon='ui_22_32_28', align=uiconst.CENTERLEFT, ignoreSize=True)
        self.sr.labelClipper = uiprimitives.Container(parent=self, name='labelClipper', align=uiconst.TOALL, pos=(0,
         0,
         const.defaultPadding,
         0), clipChildren=1)
        self.sr.labelClipper.OnClick = self.OnClick
        self.sr.labelClipper.GetMenu = self.GetMenu
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=self.sr.labelClipper, left=5, state=uiconst.UI_DISABLED, maxLines=1, align=uiconst.CENTERLEFT)
        if self.sr.node.sublevel > 0:
            self.sr.fill = None
        else:
            self.sr.fill = FillThemeColored(parent=self, padding=(1, 0, 1, 1), colorType=uiconst.COLORTYPE_UIHEADER, opacity=0.15)
        mainLinePar = uiprimitives.Container(parent=self, name='mainLinePar', align=uiconst.TOALL, idx=0, pos=(0, 0, 0, 0), state=uiconst.UI_DISABLED)

    def GetHeight(self, *args):
        node, _ = args
        node.height = uix.GetTextHeight(node.label, maxLines=1) + 6
        return node.height

    @telemetry.ZONE_METHOD
    def Load(self, node):
        """
        id : id of the group
        subitems : list of items within group
        groupItems : alias for the above
        hint : hint for group
        sublevel : what level is this group at
        selectGroup : is the group selectable ?
        selected : is the group selected ?
        hideExpander : hide the collapse/expand button ?
        hideFill : hide the background fill ?
        hideTopLine : hide line at top ?
        labelstyle : style of the label (dict)
        showicon : is the icon visible ?
        iconID : id of the icon
        openByDefault : if True, always initialise as expanded
        """
        self.sr.node = node
        self.sr.id = node.id
        self.sr.subitems = node.get('subitems', []) or node.get('groupItems', [])
        iconSize = node.Get('iconSize', self.default_iconSize)
        self.UpdateLabel()
        self.hint = node.Get('hint', '')
        sublevel = node.Get('sublevel', 0)
        self.sr.expander.left = 16 * sublevel + 3
        self.sr.label.left = 24 + (1 + sublevel) * iconSize
        self.sr.icon.left = 16 * sublevel + 20
        self.sr.node.selectable = node.Get('selectGroup', 0)
        if node.Get('selected', 0):
            self.Select()
        else:
            self.Deselect()
        self.sr.expander.state = [uiconst.UI_NORMAL, uiconst.UI_HIDDEN][node.Get('hideExpander', 0)]
        if self.sr.fill:
            self.sr.fill.state = [uiconst.UI_DISABLED, uiconst.UI_HIDDEN][node.Get('hideFill', False)]
        if self.sr.expander.state == uiconst.UI_HIDDEN:
            self.sr.labelClipper.width = 0
        for k, v in node.Get('labelstyle', {}).iteritems():
            setattr(self.sr.label, k, v)

        icon = node.Get('showicon', '')
        iconID = node.Get('iconID', None)
        if iconID:
            self.sr.icon.LoadIcon(iconID, ignoreSize=True)
            self.sr.icon.SetSize(iconSize, iconSize)
            self.sr.icon.state = uiconst.UI_DISABLED
        elif icon == 'hide':
            self.sr.icon.state = uiconst.UI_HIDDEN
            self.sr.label.left -= iconSize + 4
        elif icon and icon[0] == '_':
            self.sr.icon.LoadIcon(icon[1:], ignoreSize=True)
            self.sr.icon.SetSize(iconSize, iconSize)
            self.sr.icon.state = uiconst.UI_DISABLED
        else:
            if icon:
                self.sr.icon.LoadIcon(icon, ignoreSize=True)
                self.sr.icon.SetSize(iconSize, iconSize)
            else:
                self.sr.icon.LoadIcon('res:/ui/Texture/WindowIcons/smallfolder.png', ignoreSize=True)
                self.sr.icon.SetSize(iconSize, iconSize)
            self.sr.icon.state = uiconst.UI_DISABLED
            self.sr.icon.width = iconSize
        if self.sr.expander.state == uiconst.UI_HIDDEN:
            self.sr.label.left -= iconSize
            self.sr.icon.left -= iconSize + 2
        if node.panel is not self or self is None:
            return
        self.ShowOpenState(node.get('forceOpen', False) or uicore.registry.GetListGroupOpenState(self.sr.id, default=node.Get('openByDefault', False)))
        self.RefreshGroupWindow(0)

    def OnDblClick(self, *args):
        if self.sr.node.Get('OnDblClick', None):
            self.sr.node.OnDblClick(self)
            return
        if self.sr.node.Get('BlockOpenWindow', 0):
            return
        self.RefreshGroupWindow(create=1)

    def RefreshGroupWindow(self, create):
        import form
        if self.sr.node:
            if create:
                wnd = form.VirtualGroupWindow.Open(windowID=unicode(self.sr.node.id), node=self.sr.node, caption=self.sr.node.label.replace('<t>', '-'))
            else:
                wnd = form.VirtualGroupWindow.GetIfOpen(windowID=unicode(self.sr.node.id))
            if wnd:
                wnd.LoadContent(self.sr.node, newCaption=self.sr.node.label)
                if create:
                    wnd.Maximize()
                if not self or self.destroyed:
                    return
                node = self.sr.node
                if node.open:
                    self.Toggle()

    def GetNoItemEntry(self):
        import listentry
        return listentry.Get('Generic', {'label': localization.GetByLabel('/Carbon/UI/Controls/Common/NoItem'),
         'sublevel': self.sr.node.Get('sublevel', 0) + 1})

    def GetMenu(self):
        m = []
        if not self.sr.node.Get('BlockOpenWindow', 0):
            import form
            wnd = form.VirtualGroupWindow.GetIfOpen(windowID=unicode(self.sr.node.id))
            if wnd:
                m = [(uiutil.MenuLabel('/Carbon/UI/Controls/ScrollEntries/ShowWindow'), self.RefreshGroupWindow, (1,))]
            else:
                m = [(uiutil.MenuLabel('/Carbon/UI/Controls/ScrollEntries/OpenGroupWindow'), self.RefreshGroupWindow, (1,))]
        node = self.sr.node
        expandable = node.Get('expandable', 1)
        if expandable:
            if not node.open:
                m += [(uiutil.MenuLabel('UI/Common/Expand'), self.Toggle, ())]
            else:
                m += [(uiutil.MenuLabel('UI/Common/Collapse'), self.Toggle, ())]
        if node.Get('state', None) != 'locked':
            m += [(uiutil.MenuLabel('/Carbon/UI/Controls/ScrollEntries/ChangeLabel'), self.ChangeLabel)]
            m += [(uiutil.MenuLabel('/Carbon/UI/Controls/ScrollEntries/DeleteFolder'), self.DeleteFolder)]
        if node.Get('MenuFunction', None):
            cm = node.MenuFunction(node)
            m += cm
        return m

    def GetNewGroupName(self):
        return uiutil.NamePopup(localization.GetByLabel('/Carbon/UI/Controls/ScrollEntries/TypeInNewName'), localization.GetByLabel('/Carbon/UI/Controls/ScrollEntries/TypeInNewFolderName'))

    def CloseWindow(self, windowID):
        import form
        form.VirtualGroupWindow.CloseIfOpen(windowID=windowID)

    def OnDragEnter(self, dragObj, drag, *args):
        if self.sr.node.Get('DragEnterCallback', None):
            self.sr.node.DragEnterCallback(self, drag)
        elif drag and getattr(drag[0], '__guid__', None) in self.sr.node.Get('allowGuids', []) + ['xtriui.DragIcon']:
            self.Select()

    def OnDragExit(self, dragObj, drag, *args):
        if not self.sr.node.selected:
            self.Deselect()

    def ShowOpenState(self, open_):
        if self.sr.expander:
            if open_:
                self.sr.expander.LoadIcon('res:/UI/Texture/Icons/38_16_229.png')
            else:
                self.sr.expander.LoadIcon('res:/UI/Texture/Icons/38_16_228.png')

    def OnMouseEnter(self, *args):
        SE_ListGroupCore.OnMouseEnter(self, *args)
        self.sr.expander.OnMouseEnter()

    def OnMouseExit(self, *args):
        SE_ListGroupCore.OnMouseExit(self, *args)
        self.sr.expander.OnMouseExit()

    def GetRadialMenuIndicator(self, create = True, *args):
        indicator = getattr(self, 'radialMenuIndicator', None)
        if indicator and not indicator.destroyed:
            return indicator
        if not create:
            return
        self.radialMenuIndicator = uiprimitives.Fill(bgParent=self, color=(1, 1, 1, 0.1), name='radialMenuIndicator')
        return self.radialMenuIndicator

    def ShowRadialMenuIndicator(self, slimItem, *args):
        indicator = self.GetRadialMenuIndicator(create=True)
        indicator.display = True

    def HideRadialMenuIndicator(self, slimItem, *args):
        indicator = self.GetRadialMenuIndicator(create=False)
        if indicator:
            indicator.display = False

    @classmethod
    def GetCopyData(cls, node):
        return node.label
