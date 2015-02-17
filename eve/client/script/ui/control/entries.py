#Embedded file name: eve/client/script/ui/control\entries.py
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.control.scrollentries import SE_BaseClassCore
from carbonui.primitives.container import Container
from carbonui.util.color import Color
from eve.client.script.ui.control.buttons import ButtonIcon
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.glowSprite import GlowSprite
from eve.client.script.ui.control.infoIcon import InfoIcon, MoreInfoIcon
from eve.client.script.ui.control.themeColored import FillThemeColored
from eve.common.script.util.industryCommon import IsBlueprintCategory
import moniker
import uicontrols
import uiprimitives
import uix
import uiutil
import util
import blue
import base
from eve.client.script.ui.shared.traits import HasTraits, TraitsContainer
import uthread
import carbonui.const as uiconst
import log
import trinity
import telemetry
import localization
import fontConst
import geo2
import const
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.gauge import Gauge
from eve.client.script.ui.control.listgroup import ListGroup
from carbon.common.script.sys.service import ROLE_GMH
from eve.client.script.ui.shared.monetization.trialPopup import ORIGIN_CERTIFICATES, ORIGIN_UNKNOWN
events = ('OnClick',
 'OnMouseDown',
 'OnMouseUp',
 'OnDblClick',
 'OnMouseHover')

def IsResultWithinWarpDistance(result):
    """
    check whether the result is with in warp distance of the current players ship
    """
    ballpark = sm.GetService('michelle').GetBallpark()
    egoBall = ballpark.GetBall(ballpark.ego)
    egoPos = geo2.Vector(egoBall.x, egoBall.y, egoBall.z)
    distance = result.GetDistance(egoPos)
    return distance > const.minWarpDistance


class Space(SE_BaseClassCore):
    __guid__ = 'listentry.Space'
    __params__ = ['height']
    default_showHilite = False

    def Load(self, node):
        self.sr.node = node

    def GetHeight(self, *args):
        node, width = args
        node.height = node.height
        return node.height


class Generic(SE_BaseClassCore):
    __guid__ = 'listentry.Generic'
    __params__ = ['label']

    def _OnClose(self):
        for eventName in events:
            setattr(self.sr, eventName, None)

        uicontrols.SE_BaseClassCore._OnClose(self)

    def Startup(self, *args):
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=self, left=5, state=uiconst.UI_DISABLED, color=None, maxLines=1, align=uiconst.CENTERLEFT)
        for eventName in events:
            setattr(self.sr, eventName, None)

        self.sr.infoicon = None

    def Load(self, node):
        self.sr.node = node
        data = node
        self.UpdateHint()
        self.confirmOnDblClick = data.Get('confirmOnDblClick', 0)
        self.typeID = data.Get('typeID', None)
        self.itemID = data.Get('itemID', None)
        if node.selected:
            self.Select()
        else:
            self.Deselect()
        if node.showinfo and node.typeID:
            if not self.sr.infoicon:
                self.sr.infoicon = InfoIcon(left=1, parent=self, idx=0, align=uiconst.CENTERRIGHT)
                self.sr.infoicon.OnClick = self.ShowInfo
            self.sr.infoicon.state = uiconst.UI_NORMAL
        elif self.sr.infoicon:
            self.sr.infoicon.state = uiconst.UI_HIDDEN
        for eventName in events:
            if data.Get(eventName, None):
                setattr(self.sr, eventName, data.Get(eventName, None))

        preAutoUpdateFlag = self.sr.label.autoUpdate
        self.sr.label.autoUpdate = False
        self.sr.label.maxLines = data.Get('maxLines', 1)
        self.sr.label.left = 5 + 16 * data.Get('sublevel', 0)
        self.sr.label.fontsize = data.Get('fontsize', fontConst.EVE_MEDIUM_FONTSIZE)
        self.sr.label.letterspace = data.Get('hspace', 0)
        self.sr.label.SetTextColor(data.Get('fontColor', uicontrols.EveLabelMedium.default_color))
        self.sr.label.text = data.label
        self.sr.label.Update()
        self.sr.label.autoUpdate = preAutoUpdateFlag

    def UpdateHint(self):
        data = self.sr.node
        hint = data.hint
        if hint is not None:
            self.hint = hint

    def GetHeight(self, *args):
        node, width = args
        if node.vspace is not None:
            node.height = uix.GetTextHeight(node.label, maxLines=1) + node.vspace
        else:
            node.height = uix.GetTextHeight(node.label, maxLines=1) + 4
        return node.height

    def OnMouseHover(self, *args):
        if self.sr.node and self.sr.node.Get('OnMouseHover', None):
            self.sr.node.OnMouseHover(self)

    def OnMouseEnter(self, *args):
        SE_BaseClassCore.OnMouseEnter(self, *args)
        if self.sr.node:
            eve.Message('ListEntryEnter')
            if self.sr.node.Get('OnMouseEnter', None):
                self.sr.node.OnMouseEnter(self)

    def OnMouseExit(self, *args):
        SE_BaseClassCore.OnMouseExit(self, *args)
        if self.sr.node:
            if self.sr.node.Get('OnMouseExit', None):
                self.sr.node.OnMouseExit(self)

    def OnClick(self, *args):
        if util.GetAttrs(self, 'sr', 'node'):
            if self.sr.node.Get('selectable', 1):
                self.sr.node.scroll.SelectNode(self.sr.node)
            eve.Message('ListEntryClick')
            if not self or self.destroyed:
                return
            if self.sr.node.Get('OnClick', None):
                self.sr.node.OnClick(self)

    def OnDblClick(self, *args):
        if self.sr.node:
            self.sr.node.scroll.SelectNode(self.sr.node)
            if self.sr.node.Get('OnDblClick', None):
                if isinstance(self.sr.node.OnDblClick, tuple):
                    func = self.sr.node.OnDblClick[0]
                    func(self, *self.sr.node.OnDblClick[1:])
                else:
                    self.sr.node.OnDblClick(self)
            elif getattr(self, 'confirmOnDblClick', None):
                uicore.registry.Confirm()
            elif self.sr.node.Get('typeID', None):
                self.ShowInfo()

    def OnMouseDown(self, *args):
        uicontrols.SE_BaseClassCore.OnMouseDown(self, *args)
        if self.sr.node and self.sr.node.Get('OnMouseDown', None):
            self.sr.node.OnMouseDown(self)

    def OnMouseUp(self, *args):
        uicontrols.SE_BaseClassCore.OnMouseUp(self, *args)
        if not self or self.destroyed:
            return
        if self.sr.node and self.sr.node.Get('OnMouseUp', None):
            self.sr.node.OnMouseUp(self)

    def ShowInfo(self, *args):
        if self.sr.node.Get('isStation', 0):
            stationinfo = sm.RemoteSvc('stationSvc').GetStation(self.itemID)
            sm.GetService('info').ShowInfo(stationinfo.stationTypeID, self.itemID)
            return
        if self.sr.node.Get('typeID', None):
            abstractinfo = self.sr.node.Get('abstractinfo', util.KeyVal())
            typeID = self.sr.node.Get('typeID', None)
            itemID = self.sr.node.Get('itemID', None)
            if IsBlueprintCategory(cfg.invtypes.Get(typeID).categoryID):
                isCopy = self.sr.node.isCopy
                abstractinfo.bpData = sm.GetService('blueprintSvc').GetBlueprintTypeCopy(typeID=typeID, original=not isCopy)
            sm.GetService('info').ShowInfo(typeID, itemID, abstractinfo=abstractinfo)

    def GetMenu(self):
        if not self.sr.node.Get('ignoreRightClick', 0):
            self.OnClick()
        if hasattr(self, 'sr'):
            if self.sr.node and self.sr.node.Get('GetMenu', None):
                return self.sr.node.GetMenu(self)
            if getattr(self, 'itemID', None) or getattr(self, 'typeID', None):
                return sm.GetService('menu').GetMenuFormItemIDTypeID(getattr(self, 'itemID', None), getattr(self, 'typeID', None))
        return []

    def OnDropData(self, dragObj, nodes):
        data = self.sr.node
        if data.OnDropData:
            data.OnDropData(dragObj, nodes)

    def DoSelectNode(self, toggle = 0):
        self.sr.node.scroll.GetSelectedNodes(self.sr.node, toggle=toggle)

    def GetRadialMenuIndicator(self, create = True, *args):
        indicator = getattr(self, 'radialMenuIndicator', None)
        if indicator and not indicator.destroyed:
            return indicator
        if not create:
            return
        self.radialMenuIndicator = uiprimitives.Fill(bgParent=self, color=(1, 1, 1, 0.25), name='radialMenuIndicator')
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


class CorpOfficeEntry(Generic):

    def Startup(self, *args):
        self.unrentButton = None
        Generic.Startup(self, *args)

    def Load(self, node):
        Generic.Load(self, node)
        self.unrentButton = ButtonIcon(texturePath='res:/UI/Texture/Icons/73_16_210.png', pos=(0, 0, 16, 16), align=uiconst.CENTERRIGHT, parent=self, hint=localization.GetByLabel('UI/Station/Hangar/UnrentOffice'), idx=0, func=self.UnrentOffice)
        self.unrentButton.display = False

    def UnrentOffice(self):
        if eve.Message('crpUnrentOffice', {}, uiconst.YESNO) != uiconst.ID_YES:
            return
        corpStationMgr = moniker.GetCorpStationManagerEx(self.itemID)
        corpStationMgr.CancelRentOfOffice()

    def OnMouseEnter(self, *args):
        Generic.OnMouseEnter(self, *args)
        if not self.unrentButton:
            return
        if self.IsDirector():
            self.mouseovertimer = AutoTimer(1, self.UpdateMouseOver)
            self.unrentButton.display = True

    def UpdateMouseOver(self):
        mo = uicore.uilib.mouseOver
        if mo in (self, self.unrentButton):
            return
        self.mouseovertimer = None
        self.unrentButton.display = False

    def IsDirector(self):
        return session.corprole & const.corpRoleDirector == const.corpRoleDirector


class ComboEntry(Generic):

    def Load(self, node):
        Generic.Load(self, node)
        if node.icon is not None:
            icon = Icon(parent=self, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, pos=(4, 0, 16, 16), icon=node.icon, ignoreSize=True)
            self.sr.label.left = 24
        else:
            icon = None
        if node.indentLevel:
            left = node.indentLevel * 10
            if icon:
                icon.left += left
            self.sr.label.left += left
            self.sr.label.SetRGB(*Color.GRAY7)


class ItemWithLocation(Generic):
    __guid__ = 'listentry.ItemWithLocation'
    __params__ = ['itemRow', 'jumps']

    def Startup(self, *args):
        Generic.Startup(self, args)
        self.sr.label.maxLines = 2
        self.sr.infoicon = InfoIcon(left=2, parent=self, idx=0, align=uiconst.CENTERRIGHT)
        self.sr.infoicon.OnClick = self.ShowInfo
        self.sr.icon = uicontrols.Icon(parent=self, pos=(1, 2, 24, 24), align=uiconst.TOPLEFT, idx=0)
        self.sr.techIcon = uiprimitives.Sprite(name='techIcon', parent=self, left=1, width=16, height=16, idx=0)
        for eventName in events:
            setattr(self.sr, eventName, None)

    def Load(self, node):
        self.sr.node = node
        data = node
        self.itemID = data.itemRow.itemID
        self.typeID = data.itemRow.typeID
        self.locationID = data.itemRow.locationID
        self.jumps = data.jumps
        if node.selected:
            self.Select()
        else:
            self.Deselect()
        self.sr.techIcon.state = uiconst.UI_HIDDEN
        self.sr.icon.state = uiconst.UI_NORMAL
        self.sr.icon.LoadIconByTypeID(typeID=self.typeID, size=24, ignoreSize=True, isCopy=getattr(data.itemRow, 'isCopy', False))
        self.sr.icon.SetSize(48, 48)
        self.sr.label.left = self.height + 4
        techSprite = uix.GetTechLevelIcon(self.sr.techIcon, 1, self.typeID)
        self.sr.label.text = cfg.invtypes.Get(self.typeID).name
        self.sr.label.text += '<br>' + cfg.evelocations.Get(self.locationID).name
        self.hint = localization.GetByLabel('UI/Common/NumJumpsAway', numJumps=self.jumps)
        for eventName in events:
            if data.Get(eventName, None):
                setattr(self.sr, eventName, data.Get(eventName, None))

        self.sr.label.Update()

    def GetHeight(self, *args):
        node, width = args
        node.height = 50
        return node.height

    def GetMenu(self):
        if not self.sr.node.Get('ignoreRightClick', 0):
            self.OnClick()
        if self.sr.node.Get('GetMenu', None):
            return self.sr.node.GetMenu(self)
        if self.itemID:
            return sm.GetService('menu').GetMenuFormItemIDTypeID(self.itemID, self.typeID, ignoreMarketDetails=0)
        if self.typeID:
            return sm.GetService('menu').GetMenuFormItemIDTypeID(None, self.typeID, ignoreMarketDetails=0)
        return []


class Item(Generic):
    __guid__ = 'listentry.Item'
    __params__ = ['itemID', 'typeID', 'label']
    isDragObject = True

    def Startup(self, *args):
        Generic.Startup(self, args)
        self.sr.label.left = 8
        self.sr.infoicon = InfoIcon(left=2, parent=self, idx=0, align=uiconst.CENTERRIGHT)
        self.sr.infoicon.OnClick = self.ShowInfo
        self.sr.icon = uicontrols.Icon(parent=self, pos=(1, 2, 24, 24), align=uiconst.TOPLEFT, idx=0)
        self.sr.techIcon = uiprimitives.Sprite(name='techIcon', parent=self, left=1, width=16, height=16, idx=0)
        for eventName in events:
            setattr(self.sr, eventName, None)

    def Load(self, node):
        self.sr.node = node
        data = node
        self.itemID = data.itemID
        self.typeID = data.typeID
        self.isStation = data.Get('isStation', 0)
        self.confirmOnDblClick = data.Get('confirmOnDblClick', 0)
        self.sr.techIcon.state = uiconst.UI_HIDDEN
        if data.getIcon and self.typeID:
            self.sr.icon.state = uiconst.UI_NORMAL
            self.sr.icon.LoadIconByTypeID(typeID=self.typeID, size=24, ignoreSize=True, isCopy=getattr(data, 'isCopy', False))
            self.sr.icon.SetSize(24, 24)
            self.sr.label.left = self.height + 4 + node.get('sublevel', 0) * 16
            self.sr.icon.left = node.get('sublevel', 0) * 16
            techSprite = uix.GetTechLevelIcon(self.sr.techIcon, 1, self.typeID)
            self.sr.techIcon.left = node.get('sublevel', 0) * 16
        else:
            self.sr.icon.state = uiconst.UI_HIDDEN
            self.sr.label.left = 8 + node.get('sublevel', 0) * 16
        self.sr.label.text = data.label
        self.hint = data.Get('hint', '')
        if self.typeID or self.isStation:
            self.sr.infoicon.state = uiconst.UI_NORMAL
        else:
            self.sr.infoicon.state = uiconst.UI_HIDDEN
        for eventName in events:
            if data.Get(eventName, None):
                setattr(self.sr, eventName, data.Get(eventName, None))

        if node.Get('selected', 0):
            self.Select()
        else:
            self.Deselect()
        self.sr.label.Update()

    def GetHeight(self, *args):
        node, width = args
        node.height = 29
        return node.height

    def GetMenu(self):
        if not self.sr.node.Get('ignoreRightClick', 0):
            self.OnClick()
        if self.sr.node.Get('GetMenu', None):
            return self.sr.node.GetMenu(self)
        if self.itemID:
            return sm.GetService('menu').GetMenuFormItemIDTypeID(self.itemID, self.typeID, ignoreMarketDetails=0)
        if self.typeID:
            if getattr(self.sr.node, 'isCopy', False):
                bpData = sm.GetService('blueprintSvc').GetBlueprintTypeCopy(self.typeID, original=False)
                abstractInfo = util.KeyVal(bpData=bpData)
            else:
                abstractInfo = None
            return sm.GetService('menu').GetMenuFormItemIDTypeID(None, self.typeID, ignoreMarketDetails=0, abstractInfo=abstractInfo)
        return []

    def GetDragData(self, *args):
        return [self.sr.node]

    def LoadTooltipPanel(self, tooltipPanel, *args):
        if HasTraits(self.typeID):
            tooltipPanel.LoadGeneric1ColumnTemplate()
            tooltipPanel.AddSpacer(width=300, height=1)
            TraitsContainer(parent=tooltipPanel, typeID=self.typeID, padding=7)


class AutoPilotItem(Item):
    __guid__ = 'listentry.AutoPilotItem'
    isDragObject = True

    def Startup(self, *args):
        Item.Startup(self, args)
        self.sr.posIndicatorCont = uiprimitives.Container(name='posIndicator', parent=self, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, height=2)
        self.sr.posIndicatorNo = uiprimitives.Fill(parent=self.sr.posIndicatorCont, color=(0.61, 0.05, 0.005, 1.0))
        self.sr.posIndicatorNo.state = uiconst.UI_HIDDEN
        self.sr.posIndicatorYes = uiprimitives.Fill(parent=self.sr.posIndicatorCont, color=(1.0, 1.0, 1.0, 0.5))
        self.sr.posIndicatorYes.state = uiconst.UI_HIDDEN

    def GetDragData(self, *args):
        if not self.sr.node.canDrag:
            return
        self.sr.node.scroll.SelectNode(self.sr.node)
        return [self.sr.node]

    def OnDropData(self, dragObj, nodes, *args):
        self.sr.posIndicatorNo.state = uiconst.UI_HIDDEN
        self.sr.posIndicatorYes.state = uiconst.UI_HIDDEN
        if util.GetAttrs(self, 'parent', 'OnDropData'):
            node = nodes[0]
            if self.sr.node.canDrag:
                if util.GetAttrs(node, 'panel'):
                    self.parent.OnDropData(dragObj, nodes, orderID=self.sr.node.orderID)

    def OnDragEnter(self, dragObj, nodes, *args):
        node = nodes[0]
        if self.sr.node.canDrag:
            self.sr.posIndicatorYes.state = uiconst.UI_DISABLED
        else:
            self.sr.posIndicatorNo.state = uiconst.UI_DISABLED

    def OnDragExit(self, *args):
        self.sr.posIndicatorNo.state = uiconst.UI_HIDDEN
        self.sr.posIndicatorYes.state = uiconst.UI_HIDDEN


class Push(SE_BaseClassCore):
    __guid__ = 'listentry.Push'
    __params__ = []
    default_showHilite = False

    def Startup(self, *etc):
        pass

    def Load(self, node):
        self.sr.node = node

    def GetHeight(self, *args):
        node, width = args
        node.height = node.Get('height', 0) or 12
        return node.height


class Divider(SE_BaseClassCore):
    __guid__ = 'listentry.Divider'
    __params__ = []
    default_showHilite = False

    def Load(self, node):
        self.sr.node = node

    def GetHeight(self, *args):
        node, width = args
        node.height = node.Get('height', 0) or 12
        return node.height


class ScanProbeEntry(SE_BaseClassCore):
    __guid__ = 'listentry.ScanProbeEntry'
    __params__ = []

    def Startup(self, *etc):
        self.framebox = uiprimitives.Container(parent=self, name='framebox', align=uiconst.TOALL)
        self.nameBox = uiprimitives.Container(parent=self.framebox, name='nameBox', align=uiconst.TOLEFT_PROP, width=0.3, height=17)
        self.stateBox = uiprimitives.Container(parent=self.framebox, name='statebox', align=uiconst.TOLEFT_PROP, width=0.16, height=17)
        self.expireBox = uiprimitives.Container(parent=self.framebox, name='exprireBox', align=uiconst.TOLEFT_PROP, width=0.22, height=17)
        self.rightbox = uiprimitives.Container(parent=self.framebox, name='rangeBox', align=uiconst.TOLEFT_PROP, width=0.32, height=17)
        self.icon = uicontrols.Icon(parent=self.nameBox, pos=(1, 2, 24, 24), align=uiconst.TOLEFT, idx=0)
        self.probeName = uicontrols.EveLabelMediumBold(parent=self.nameBox, align=uiconst.TOLEFT, state=uiconst.UI_DISABLED, padding=(0, 1, 0, 0))
        self.probeState = uicontrols.EveLabelMediumBold(parent=self.stateBox, align=uiconst.TOLEFT, state=uiconst.UI_DISABLED, padding=(0, 1, 0, 0))
        self.probeExpiry = uicontrols.EveLabelMediumBold(parent=self.expireBox, align=uiconst.TOLEFT, state=uiconst.UI_DISABLED, width=100, padding=(0, 1, 0, 0))
        self.menuBox = uiprimitives.Container(parent=self.rightbox, align=uiconst.TORIGHT, width=16, state=uiconst.UI_NORMAL, padding=(0, 1, 0, 0))
        self.probeRange = uicontrols.EveLabelMedium(parent=self.rightbox, align=uiconst.TORIGHT, state=uiconst.UI_DISABLED, width=90, padding=(0, 1, 0, 0))
        probeMenu = uicontrols.MenuIcon()
        probeMenu.GetMenu = self.GetMenu
        probeMenu.hint = ''
        self.menuBox.children.append(probeMenu)

    def Load(self, node):
        if node.Get('selectable', 1) and node.Get('selected', 0):
            self.Select()
        else:
            self.Deselect()
        self.sr.node = node
        self.icon.LoadIconByTypeID(node.probe.typeID, ignoreSize=True)
        self.icon.hint = cfg.invtypes.Get(node.probe.typeID).typeName
        self.probeName.text = node.texts[0]
        self.probeExpiry.text = node.texts[2]
        self.probeState.text = node.texts[3]
        self.probeRange.text = localization.GetByLabel('UI/Inflight/Scanner/Range') + ' ' + node.texts[1]

    def Resize(self):
        pass

    def OnDblClick(self, *args):
        if sm.GetService('viewState').IsViewActive('systemmap'):
            uicore.layer.systemmap.SetInterest(self.sr.node.probeID)

    def GetHeight(self, *args):
        node, width = args
        node.height = node.Get('height', 0) or 23
        return node.height

    def OnMouseEnter(self, *args):
        SE_BaseClassCore.OnMouseEnter(self, *args)
        if self.sr.node:
            if self.sr.node.Get('OnMouseEnter', None):
                self.sr.node.OnMouseEnter(self)

    def OnMouseExit(self, *args):
        SE_BaseClassCore.OnMouseExit(self, *args)
        if self.sr.node:
            if self.sr.node.Get('OnMouseExit', None):
                self.sr.node.OnMouseExit(self)

    def OnClick(self, *args):
        if self.sr.node:
            if self.sr.node.Get('selectable', 1):
                self.sr.node.scroll.SelectNode(self.sr.node)
            eve.Message('ListEntryClick')
            if self.sr.node.Get('OnClick', None):
                self.sr.node.OnClick(self)

    def GetMenu(self):
        if hasattr(self, 'sr'):
            if self.sr.node and self.sr.node.Get('GetMenu', None):
                return self.sr.node.GetMenu(self)
            if getattr(self, 'itemID', None) or getattr(self, 'typeID', None):
                return sm.GetService('menu').GetMenuFormItemIDTypeID(getattr(self, 'itemID', None), getattr(self, 'typeID', None))
        return []


class ScanResult(SE_BaseClassCore):
    __guid__ = 'listentry.ScanResult'
    __params__ = []

    def DelegateToParent(self, objects, functions):
        for obj in objects:
            for function in functions:
                setattr(obj, function, getattr(obj.parent, function))

    def Startup(self, *etc):
        self.buttonbox = uiprimitives.Container(parent=self, name='buttonbox', align=uiconst.TORIGHT, width=55, padding=(0, 2, 0, 2))
        self.distancebox = uiprimitives.Container(parent=self, name='distancebox', align=uiconst.TOLEFT, width=70, padding=(0, 2, 0, 2))
        self.framebox = uiprimitives.Container(parent=self, name='framebox', align=uiconst.TOALL, padding=(0, 2, 0, 2), state=uiconst.UI_NORMAL)
        self.textboxID = uiprimitives.Container(parent=self.framebox, name='textboxID', padding=(0, 0, 0, 0), align=uiconst.TOLEFT, width=60, clipChildren=True)
        self.textbox = uiprimitives.Container(parent=self.framebox, name='textbox', padding=(0, 0, 0, 0), align=uiconst.TOALL, clipChildren=True)
        self.textboxLeft = uiprimitives.Container(parent=self.textbox, name='textboxLeft', padding=(0, 0, 0, 0), align=uiconst.TOLEFT, width=100, clipChildren=True)
        self.textboxMiddle = uiprimitives.Container(parent=self.textbox, name='textboxMiddle', padding=(0, 0, 0, 0), align=uiconst.TOLEFT, width=100, clipChildren=True)
        self.textboxRight = uiprimitives.Container(parent=self.textbox, name='textboxRight', padding=(0, 0, 0, 0), align=uiconst.TOLEFT, width=100, clipChildren=True)
        self.distance = uicontrols.EveLabelMedium(parent=self.distancebox, align=uiconst.TORIGHT, state=uiconst.UI_NORMAL, padding=(0, 0, 5, 0))
        self.scanID = uicontrols.EveLabelMedium(parent=self.textboxID, align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL, padding=(5, 0, 0, 0))
        self.scanGroupName = uicontrols.EveLabelMedium(name='scanGroupName', parent=self.textboxLeft, align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL, padding=(5, 0, 0, 0))
        self.groupName = uicontrols.EveLabelMedium(name='groupName', parent=self.textboxMiddle, align=uiconst.TOLEFT, state=uiconst.UI_NORMAL, padding=(5, 0, 0, 0))
        self.typeName = uicontrols.EveLabelMedium(name='typeName', parent=self.textboxRight, align=uiconst.TOLEFT, state=uiconst.UI_NORMAL, padding=(5, 0, 0, 0))
        self.barbox = uiprimitives.Container(parent=self.framebox, name='barbox', align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        self.certainty = uiprimitives.Container(parent=self.barbox, name='certainty', align=uiconst.TOLEFT_PROP, width=0, state=uiconst.UI_NORMAL)
        self.posChange = uiprimitives.Container(parent=self.barbox, name='poschange', align=uiconst.TOLEFT_PROP, width=0, state=uiconst.UI_DISABLED)
        self.negChange = uiprimitives.Container(parent=self.certainty, name='negchange', align=uiconst.TORIGHT_PROP, width=0, state=uiconst.UI_DISABLED)
        self.DelegateToParent((self.buttonbox,
         self.distancebox,
         self.framebox,
         self.textboxID,
         self.textbox,
         self.textboxLeft,
         self.textboxMiddle,
         self.textboxRight,
         self.distance,
         self.scanID,
         self.scanGroupName,
         self.groupName,
         self.typeName,
         self.barbox,
         self.certainty,
         self.posChange,
         self.negChange), ('GetMenu', 'OnClick', 'OnDblClick'))
        self.backGround = uiprimitives.Container(parent=self.framebox, name='background', align=uiconst.TOALL)
        self.backGround1 = uiprimitives.Container(parent=self.backGround, name='back1', align=uiconst.TOLEFT_PROP, bgColor=(1, 1, 1, 0.02), width=0.25, state=uiconst.UI_DISABLED)
        self.backGround2 = uiprimitives.Container(parent=self.backGround, name='back2', align=uiconst.TOLEFT_PROP, bgColor=(1, 1, 1, 0.04), width=0.5, state=uiconst.UI_DISABLED)
        self.backGround3 = uiprimitives.Container(parent=self.backGround, name='back3', align=uiconst.TOLEFT_PROP, bgColor=(1, 1, 1, 0.08), width=0.25, state=uiconst.UI_DISABLED)
        self.red = (0.611, 0.0, 0.0, 0.5)
        self.redHi = (0.611, 0.0, 0.0, 0.8)
        self.redLo = (0.611, 0.0, 0.0, 0.15)
        self.orange = (0.84, 0.45, 0.0, 0.5)
        self.orangeHi = (0.84, 0.45, 0.0, 0.8)
        self.orangeLo = (0.84, 0.45, 0.0, 0.15)
        self.green = (0.0, 0.5, 0.0, 0.5)
        self.greenHi = (0.0, 0.5, 0.0, 0.8)
        self.greenLo = (0.0, 0.5, 0.0, 0.15)

    def Load(self, node):
        w1, w2, w3, w4, w5, w6 = node.GetColumnWidths()
        self.distancebox.width = w1
        self.textboxID.width = w2
        self.textboxLeft.width = w3
        self.textboxMiddle.width = w4
        self.textboxRight.width = 500
        self.buttonbox.width = w6
        if node.selected:
            self.Select()
        else:
            self.Deselect()
        newResult = False
        if hasattr(node, 'newResult'):
            if node.newResult:
                newResult = True
        self.sr.node = node
        normalColor, hiColor, loColor = self.red, self.redHi, self.redLo
        if 0.25 < node.result.certainty <= 0.75:
            normalColor, hiColor, loColor = self.orange, self.orangeHi, self.orangeLo
        if node.result.certainty > 0.75:
            normalColor, hiColor, loColor = self.green, self.greenHi, self.greenLo
        self.certaintyFill = uiprimitives.Fill(parent=self.certainty, color=normalColor)
        self.posChangeFill = uiprimitives.Fill(parent=self.posChange, color=hiColor)
        self.negChangeFill = uiprimitives.Fill(parent=self.negChange, color=loColor)
        self.newCert = node.result.certainty
        self.oldCert = node.result.prevCertainty
        self.distance.text = util.FmtDist(node.distance)
        self.certChange = self.newCert - self.oldCert
        if node.result.isPerfect and IsResultWithinWarpDistance(node.result):
            if not hasattr(self, 'warpButton'):
                self.warpButton = uicontrols.ButtonIcon(name='warpButton', func=self.WarpToAction, parent=self.buttonbox, align=uiconst.CENTER, width=22, iconSize=22, texturePath='res:/UI/Texture/Icons/44_32_18.png', padding=(0, 0, 0, 0), hint=localization.GetByLabel('UI/Commands/WarpTo'))
                if newResult:
                    uicore.animations.SpGlowFadeIn(self.warpButton.icon, glowFactor=1, glowColor=(0.8, 0.8, 0.8, 0.6), glowExpand=0, duration=1, loops=3)
        elif not hasattr(self, 'percentage'):
            self.percentage = uicontrols.EveLabelMedium(parent=self.buttonbox, text=localization.GetByLabel('UI/Common/Percentage', percentage=self.newCert * 100), align=uiconst.TORIGHT, tate=uiconst.UI_DISABLED, padding=(0, 2, 0, 0))
        else:
            self.percentage.text = localization.GetByLabel('UI/Common/Percentage', percentage=self.newCert * 100)
        if self.certChange > 0:
            self.certainty.width = self.oldCert
            self.negChange.width = 0
            if newResult == True:
                uicore.animations.MorphScalar(self.posChange, 'width', 0, self.certChange, duration=1)
                if node.result.certainty != 1.0:
                    uicore.animations.SpGlowFadeIn(self.posChangeFill, glowFactor=0.8, glowExpand=0, duration=3, loops=1)
                    uicore.animations.SpGlowFadeOut(self.posChangeFill, glowFactor=0.8, glowExpand=0, duration=3, loops=1)
            self.posChange.width = self.certChange
        else:
            self.certainty.width = self.newCert
            self.posChange.width = 0
            if self.sr.node.new == True:
                uicore.animations.MorphScalar(self.negChange, 'width', 0, abs(self.certChange), duration=1)
                if node.result.certainty != const.probeResultPerfect:
                    uicore.animations.SpGlowFadeIn(self.negChangeFill, glowFactor=0.8, glowExpand=0, duration=3, loops=1)
                    uicore.animations.SpGlowFadeOut(self.negChangeFill, glowFactor=0.8, glowExpand=0, duration=3, loops=1)
            else:
                self.negChange.width = abs(self.certChange)
        if node.result.id:
            self.scanID.text = node.result.id
        if node.scanGroupName:
            self.scanGroupName.text = node.scanGroupName
            self.scanGroupName.hint = node.scanGroupName
        if node.groupName:
            self.groupName.text = node.groupName
            self.groupName.hint = node.groupName
        if node.typeName:
            self.typeName.text = node.typeName
            self.typeName.hint = node.typeName
        if newResult:
            node.newResult = False

    def WarpToAction(self, *args):
        sm.GetService('menu').WarpToScanResult(self.sr.node.result.id)

    def Resize(self):
        pass

    def GetHeight(self, *args):
        node, width = args
        node.height = node.Get('height', 0) or 20
        return node.height

    def OnMouseEnter(self, *args):
        SE_BaseClassCore.OnMouseEnter(self, *args)
        if self.sr.node and self.sr.node.Get('OnMouseEnter', None):
            self.sr.node.OnMouseEnter(self)

    def OnMouseExit(self, *args):
        SE_BaseClassCore.OnMouseExit(self, *args)
        if self.sr.node and self.sr.node.Get('OnMouseExit', None):
            self.sr.node.OnMouseExit(self)

    def OnClick(self, *args):
        if self.sr.node:
            if self.sr.node.Get('selectable', 1):
                self.sr.node.scroll.SelectNode(self.sr.node)
            eve.Message('ListEntryClick')
            if self.sr.node.Get('OnClick', None):
                self.sr.node.OnClick(self)

    def OnDblClick(self, *args):
        if self.sr.node and self.sr.node.Get('CenterMapOnResult', None):
            if isinstance(self.sr.node.result.data, tuple):
                self.sr.node.CenterMapOnResult(self.sr.node.result.data)

    def GetMenu(self):
        if hasattr(self, 'sr'):
            if self.sr.node.scroll.GetSelectedNodes(self.sr.node) == 0:
                self.OnClick()
            if self.sr.node and self.sr.node.Get('GetMenu', None):
                return self.sr.node.GetMenu(self)
            if getattr(self, 'itemID', None) or getattr(self, 'typeID', None):
                return sm.GetService('menu').GetMenuFormItemIDTypeID(getattr(self, 'itemID', None), getattr(self, 'typeID', None))
        return []

    @classmethod
    def GetCopyData(cls, node):
        displayOrder = settings.user.ui.Get('columnDisplayOrder_%s' % node.columnID, None) or [ i for i in xrange(len(node.texts)) ]
        retString = []
        for i in displayOrder:
            if i <= len(node.texts) - 1:
                retString.append(node.texts[i])

        return '<t>'.join(retString)


class Slider(Generic):
    __guid__ = 'listentry.Slider'
    __params__ = ['cfgname', 'retval']
    __update_on_reload__ = 1

    def Startup(self, *args):
        Generic.Startup(self, args)
        mainpar = uiprimitives.Container(name='listentry_slider', align=uiconst.TOTOP, width=0, height=10, left=0, top=14, state=uiconst.UI_NORMAL, parent=self)
        mainpar._OnResize = self.Resize
        slider = Slider(parent=mainpar, align=uiconst.TOPLEFT, top=20, state=uiconst.UI_NORMAL)
        lbl = uicontrols.EveLabelSmall(text='', parent=mainpar, width=200, left=5, top=-12)
        lbl.name = 'label'
        self.sr.lbl = lbl
        slider.SetSliderLabel = self.SetSliderLabel
        slider.GetSliderHint = lambda idname, dname, value: localization.formatters.FormatNumeric(int(value))
        self.sr.slider = slider

    def Resize(self):
        if self.sr.slider.valueproportion:
            self.sr.slider.SlideTo(self.sr.slider.valueproportion)

    def Load(self, args):
        Generic.Load(self, args)
        data = self.sr.node
        slider = self.sr.slider
        lbl = self.sr.lbl
        if data.Get('hint', None) is not None:
            lbl.hint = data.hint
        if data.Get('getvaluefunc', None) is not None:
            slider.GetSliderValue = data.getvaluefunc
        if data.Get('endsetslidervalue', None) is not None:
            slider.EndSetSliderValue = data.endsetslidervalue
        slider.Startup(data.Get('sliderID', 'slider'), data.Get('minValue', 0), data.Get('maxValue', 10), data.Get('config', None), data.Get('displayName', None), data.Get('increments', None), data.Get('usePrefs', 0), data.Get('startVal', None))

    def SetSliderLabel(self, label, idname, dname, value):
        self.sr.lbl.text = dname
        if self.sr.node.Get('setsliderlabel', None) is not None:
            self.sr.node.setsliderlabel(label, idname, dname, value)

    def GetHeight(self, *args):
        node, width = args
        node.height = node.Get('height', 0) or 32
        return node.height


class Checkbox(Generic):
    __guid__ = 'listentry.Checkbox'
    __params__ = ['cfgname', 'retval']

    def Startup(self, *args):
        Generic.Startup(self, args)
        cbox = uicontrols.Checkbox(align=uiconst.CENTERLEFT)
        cbox.left = 6
        cbox.width = 16
        cbox.height = 16
        cbox.data = {}
        cbox.OnChange = self.CheckBoxChange
        self.children.insert(0, cbox)
        self.sr.checkbox = cbox
        self.sr.checkbox.state = uiconst.UI_DISABLED
        self.sr.label.top = 0
        self.sr.label.SetAlign(uiconst.CENTERLEFT)

    def Load(self, args):
        Generic.Load(self, args)
        data = self.sr.node
        self.sr.checkbox.SetGroup(data.Get('group', None))
        self.sr.checkbox.SetChecked(data.checked, 0)
        self.sr.checkbox.data.update({'key': data.cfgname,
         'retval': data.retval})
        self.sr.label.text = data.label
        self.sr.checkbox.left = 6 + 16 * data.Get('sublevel', 0)
        self.sr.label.left = 24 + 16 * data.Get('sublevel', 0)
        self.sr.label.Update()

    def CheckBoxChange(self, *args):
        self.sr.node.checked = self.sr.checkbox.checked
        self.sr.node.OnChange(*args)

    def OnClick(self, *args):
        if not self or self.destroyed:
            return
        if self.sr.checkbox.checked:
            eve.Message('DiodeDeselect')
        else:
            eve.Message('DiodeClick')
        if self.sr.checkbox.groupName is None:
            self.sr.checkbox.SetChecked(not self.sr.checkbox.checked)
            return
        for node in self.sr.node.scroll.GetNodes():
            if node.Get('__guid__', None) in ('listentry.Checkbox', 'listentry.ImgCheckbox') and node.Get('group', None) == self.sr.checkbox.groupName:
                if node.panel:
                    node.panel.sr.checkbox.SetChecked(0, 0)
                    node.checked = 0
                else:
                    node.checked = 0

        if not self.destroyed:
            self.sr.checkbox.SetChecked(1)

    def GetHeight(self, *args):
        node, width = args
        height = Checkbox.GetDynamicHeight(node, width)
        node.height = height
        return height

    def OnCharSpace(self, enteredChar, *args):
        uthread.pool('checkbox::OnChar', self.OnClick, self)
        return 1

    def GetDynamicHeight(node, width):
        height = max(19, uix.GetTextHeight(node.label, maxLines=1) + 4)
        return height

    def OnMouseEnter(self, *args):
        Generic.OnMouseEnter(self, *args)
        self.sr.checkbox.OnMouseEnter(*args)

    def OnMouseExit(self, *args):
        Generic.OnMouseExit(self, *args)
        self.sr.checkbox.OnMouseExit(*args)

    def OnMouseDown(self, *args):
        Generic.OnMouseDown(self, *args)
        self.sr.checkbox.OnMouseDown(*args)

    def OnMouseUp(self, *args):
        Generic.OnMouseUp(self, *args)
        self.sr.checkbox.OnMouseUp(*args)


class Progress(SE_BaseClassCore):
    __guid__ = 'listentry.Progress'
    __params__ = ['header', 'startTime', 'duration']

    def Startup(self, args):
        header = uicontrols.EveLabelMedium(text='', parent=self, left=2, top=2, state=uiconst.UI_DISABLED)
        p = uiprimitives.Container(name='gauge', parent=self, width=84, height=14, left=6, top=20, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0)
        t = uicontrols.EveLabelSmall(text='', parent=p, left=6, top=7, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
        f = uiprimitives.Fill(parent=p, align=uiconst.RELATIVE, width=1, height=10, left=2, top=2, color=(1.0, 1.0, 1.0, 0.25))
        uicontrols.Frame(parent=p, color=(1.0, 1.0, 1.0, 0.5))
        self.sr.progress = p
        self.sr.progressFill = f
        self.sr.progressHeader = header
        self.sr.progressText = t

    def Load(self, node):
        self.sr.node = node
        self.sr.progressHeader.text = node.header
        import uthread
        uthread.new(self.LoadProgress)

    def LoadProgress(self):
        if not hasattr(self, 'sr'):
            return
        startTime = self.sr.node.startTime
        duration = self.sr.node.duration
        maxWidth = self.sr.progress.width - self.sr.progressFill.left * 2
        self.sr.progress.state = uiconst.UI_DISABLED
        while self and not self.destroyed:
            msFromStart = max(0, blue.os.TimeDiffInMs(startTime, blue.os.GetSimTime()))
            portion = 1.0
            if msFromStart:
                portion -= float(msFromStart) / duration
            self.sr.progressFill.width = int(maxWidth * portion)
            diff = max(0, duration - msFromStart)
            self.sr.progressText.text = localization.GetByLabel('UI/Control/Entries/Seconds', seconds=diff / 1000.0)
            if msFromStart > duration:
                break
            blue.pyos.synchro.Yield()

    def GetHeight(self, *args):
        node, width = args
        node.height = 40
        return node.height


MINCOLWIDTH = 16

class ColumnLine(SE_BaseClassCore):
    __guid__ = 'listentry.ColumnLine'

    @telemetry.ZONE_METHOD
    def Startup(self, args):
        self._clicks = 0
        self.sr.clickTimer = None
        self.sr.columns = []
        self.cursor = 0

    @telemetry.ZONE_METHOD
    def Load(self, node):
        self.LoadLite(node)
        node.needReload = 0
        if node.Get('selectable', 1) and node.Get('selected', 0):
            self.Select()
        else:
            self.Deselect()
        if self.sr.Get('overlay', None):
            if self.sr.overlay in self.children:
                self.children.remove(self.sr.overlay)
            self.sr.overlay = None
        if node.Get('overlay', None) is not None:
            uiutil.Transplant(node.overlay, self, 0)
            self.sr.overlay = node.overlay
        self.UpdateOverlay()
        self.UpdateTriangles()

    def _OnSizeChange_NoBlock(self, *args):
        self.UpdateOverlay()

    def UpdateOverlay(self):
        if self.sr.Get('overlay', None):
            customTabstops = GetCustomTabstops(self.sr.node.columnID)
            if customTabstops:
                totalColWidth = sum(customTabstops)
            else:
                totalColWidth = sum([ each.width for each in self.sr.columns ])
            self.sr.overlay.left = max(totalColWidth, self.width - self.sr.overlay.width)

    def LoadLite(self, node):
        i = 0
        for each in node.texts:
            self.LoadColumn(i, each)
            i += 1

        for each in self.sr.columns[i:]:
            each.Close()

        self.sr.columns = self.sr.columns[:i]
        self.UpdateColumnOrder(0)

    @telemetry.ZONE_METHOD
    def UpdateColumnOrder(self, updateEntries = 1, onlyVisible = False):
        displayOrder = settings.user.ui.Get('columnDisplayOrder_%s' % self.sr.node.columnID, None) or [ i for i in xrange(len(self.sr.columns)) ]
        customTabstops = GetCustomTabstops(self.sr.node.columnID)
        if displayOrder is not None and len(displayOrder) == len(self.sr.columns):
            left = 0
            for columnIdx in displayOrder:
                colWidth = customTabstops[columnIdx]
                col = self.sr.columns[columnIdx]
                col.left = left
                col.width = colWidth
                if not self.sr.node.Get('editable', 0):
                    col.width -= 2
                left += colWidth

        self.sr.node.customTabstops = customTabstops
        if updateEntries:
            associates = self.FindAssociatingEntries()
            for node in associates:
                if node.panel and (not onlyVisible or onlyVisible and node.panel.state != uiconst.UI_HIDDEN):
                    node.panel.UpdateColumnOrder(0)
                    node.panel.UpdateOverlay()

    def OnMouseEnter(self, *args):
        SE_BaseClassCore.OnMouseEnter(self, *args)
        if self.sr.node:
            if self.sr.node.Get('OnMouseEnter', None):
                self.sr.node.OnMouseEnter(self)

    def OnMouseExit(self, *args):
        SE_BaseClassCore.OnMouseExit(self, *args)
        if self.sr.node:
            if self.sr.node.Get('OnMouseExit', None):
                self.sr.node.OnMouseExit(self)

    def OnClick(self, *args):
        if self.sr.node:
            if self.sr.node.Get('selectable', 1):
                self.sr.node.scroll.SelectNode(self.sr.node)
            eve.Message('ListEntryClick')
            if self.sr.node.Get('OnClick', None):
                self.sr.node.OnClick(self)

    def GetMenu(self):
        if self.sr.node and self.sr.node.Get('scroll', None) and getattr(self.sr.node.scroll, 'GetSelectedNodes', None):
            self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        if self.sr.node and self.sr.node.Get('GetMenu', None):
            return self.sr.node.GetMenu(self)
        if getattr(self, 'itemID', None) or getattr(self, 'typeID', None):
            return sm.GetService('menu').GetMenuFormItemIDTypeID(getattr(self, 'itemID', None), getattr(self, 'typeID', None))
        return []

    def LoadColumn(self, idx, textOrObject):
        node = self.sr.node
        if len(self.sr.columns) > idx:
            col = self.sr.columns[idx]
            col.height = self.height
        else:
            col = uiprimitives.Container(name='column_%s' % idx, parent=self, align=uiconst.TOPLEFT, height=self.height, clipChildren=1, state=uiconst.UI_PICKCHILDREN, idx=0)
            col.sr.textCtrl = uicontrols.Label(text='', parent=col, fontsize=self.sr.node.Get('fontsize', 12), letterspace=self.sr.node.Get('letterspace', 0), uppercase=self.sr.node.Get('uppercase', 0), state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, maxLines=1)
            col.sr.textCtrl.left = self.sr.node.Get('padLeft', 6)
            col.sr.editHandle = None
            col.sr.triangle = None
            col.columnIdx = idx
            col.OnDblClick = (self.OnHeaderDblClick, col)
            col.OnClick = (self.OnHeaderClick, col)
            col.GetMenu = lambda *args: self.OnHeaderGetMenu(col)
            col.cursor = 0
            self.sr.columns.append(col)
        for each in col.children[:]:
            if each not in (col.sr.textCtrl,
             col.sr.editHandle,
             col.sr.triangle,
             textOrObject):
                each.Close()

        if isinstance(textOrObject, basestring):
            col.sr.textCtrl.state = uiconst.UI_DISABLED
            col.sr.textCtrl.text = textOrObject
        else:
            col.sr.textCtrl.state = uiconst.UI_HIDDEN
            if textOrObject not in col.children:
                uiutil.Transplant(textOrObject, col, 0)
        if self.sr.node.Get('editable', 0):
            col.state = uiconst.UI_NORMAL
            if col.sr.editHandle:
                col.sr.editHandle.state = uiconst.UI_NORMAL
            else:
                par = uiprimitives.Container(name='scaleHandle_%s' % idx, parent=col, align=uiconst.TOPRIGHT, height=self.height - 2, width=5, idx=0, state=uiconst.UI_NORMAL)
                par.OnMouseDown = (self.StartScaleCol, par)
                par.OnMouseUp = (self.EndScaleCol, par)
                par.OnMouseMove = (self.ScalingCol, par)
                par.cursor = 18
                par.columnIdx = idx
                col.sr.editHandle = par
        else:
            col.state = uiconst.UI_PICKCHILDREN
            if col.sr.editHandle:
                col.sr.editHandle.state = uiconst.UI_HIDDEN

    def FindAssociatingEntries(self):
        ret = []
        for node in self.sr.node.scroll.GetNodes()[self.sr.node.idx + 1:]:
            if node.Get('columnID', None) == self.sr.node.columnID:
                ret.append(node)

        return ret

    def GetHeight(self, *args):
        node, _ = args
        node.height = uix.GetTextHeight(''.join([ text for text in node.texts if isinstance(text, basestring) ]), maxLines=1) + 1
        return node.height

    def StartScaleCol(self, sender, *args):
        if uicore.uilib.rightbtn:
            return
        l, t, w, h = sender.parent.GetAbsolute()
        sl, st, sw, sh = sender.GetAbsolute()
        associates = self.FindAssociatingEntries()
        self._startScalePosition = uicore.uilib.x
        self._startScalePositionDiff = sl - uicore.uilib.x
        self._scaleColumnIdx = sender.columnIdx
        self._scaleColumnInitialWidth = sender.parent.width
        self._minLeft = l + MINCOLWIDTH
        self.sr.scaleEntries = associates
        self.ScalingCol(sender)

    def ScalingCol(self, sender, *args):
        if getattr(self, '_startScalePosition', None):
            diff = uicore.uilib.x - self._startScalePosition
            sender.parent.width = max(MINCOLWIDTH, self._scaleColumnInitialWidth + diff)
            self.sr.node.customTabstops[self._scaleColumnIdx] = sender.parent.width
            self.UpdateColumnOrder(onlyVisible=True)

    def EndScaleCol(self, sender, *args):
        prefsID = self.sr.node.Get('columnID', None)
        if prefsID:
            current = settings.user.ui.Get('listentryColumns_%s' % prefsID, self.sr.node.customTabstops)
            current[self._scaleColumnIdx] = sender.parent.width
            settings.user.ui.Set('listentryColumns_%s' % prefsID, current)
        self.sr.node.customTabstops[self._scaleColumnIdx] = sender.parent.width
        self.sr.scaleEntries = None
        self._startScalePosition = 0

    def ChangeSort(self, sender, *args):
        columnID = self.sr.node.Get('columnID', None)
        if columnID:
            current = settings.user.ui.Get('columnSorts_%s' % columnID, {})
            if sender.columnIdx in current:
                direction = not current[sender.columnIdx]
            else:
                direction = False
            current[sender.columnIdx] = direction
            settings.user.ui.Set('columnSorts_%s' % columnID, current)
            current = settings.user.ui.Get('activeSortColumns', {})
            current[columnID] = sender.columnIdx
            settings.user.ui.Set('activeSortColumns', current)
        self.UpdateTriangles()
        self.UpdateColumnOrder()
        associates = self.FindAssociatingEntries()
        self.UpdateColumnSort(associates, columnID)
        callback = self.sr.node.Get('OnSortChange', None)
        if callback:
            callback()

    def UpdateColumnSort(self, entries, columnID):
        if not entries:
            return
        startIdx = entries[0].idx
        endIdx = entries[-1].idx
        entries = SortColumnEntries(entries, columnID)
        self.sr.node.scroll.sr.nodes = self.sr.node.scroll.sr.nodes[:startIdx] + entries + self.sr.node.scroll.sr.nodes[endIdx + 1:]
        idx = 0
        for entry in self.sr.node.scroll.GetNodes()[startIdx:]:
            if entry.Get('needReload', 0) and entry.panel:
                entry.panel.LoadLite(entry)
            idx += 1

        self.sr.node.scroll.UpdatePosition()

    def GetSortDirections(self):
        prefsID = self.sr.node.Get('columnID', None)
        if prefsID:
            return settings.user.ui.Get('columnSorts_%s' % prefsID, {})
        return {}

    def OnHeaderDblClick(self, sender, *args):
        self._clicks += 1
        self.ExecClick(sender)

    def OnHeaderClick(self, sender, *args):
        self._clicks += 1
        self.sr.clickTimer = base.AutoTimer(250, self.ExecClick, sender)

    def OnHeaderGetMenu(self, sender, *args):
        m = [(localization.GetByLabel('UI/Control/Entries/ColumnMoveForward'), self.ChangeColumnOrder, (sender, -1)), (localization.GetByLabel('UI/Control/Entries/ColumnMoveBackward'), self.ChangeColumnOrder, (sender, 1))]
        return m

    def ChangeColumnOrder(self, column, direction):
        currentDisplayOrder = settings.user.ui.Get('columnDisplayOrder_%s' % self.sr.node.columnID, None) or [ i for i in xrange(len(self.sr.node.texts)) ]
        newDisplayOrder = currentDisplayOrder[:]
        currentlyInDisplayOrder = currentDisplayOrder.index(column.columnIdx)
        newDisplayOrder.pop(currentlyInDisplayOrder)
        newDisplayOrder.insert(max(0, direction + currentlyInDisplayOrder), column.columnIdx)
        settings.user.ui.Set('columnDisplayOrder_%s' % self.sr.node.columnID, newDisplayOrder)
        self.UpdateColumnOrder()

    def ExecClick(self, sender, *args):
        if self._clicks > 1:
            self.ResetColumn(sender)
        elif self._clicks == 1:
            self.ChangeSort(sender)
        if not self.destroyed:
            self._clicks = 0
            self.sr.clickTimer = None

    def ResetColumn(self, sender, *args):
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        if shift:
            idxs = []
            for i in xrange(len(self.sr.node.texts)):
                idxs.append(i)

        else:
            idxs = [sender.columnIdx]
        associates = self.FindAssociatingEntries()
        for columnIdx in idxs:
            textsInColumn = []
            columnWidths = []
            for node in [self.sr.node] + associates:
                text = node.texts[columnIdx]
                textsInColumn.append(text)
                padLeft = node.Get('padLeft', 6)
                padRight = node.Get('padRight', 6)
                fontsize = node.Get('fontsize', 12)
                hspace = node.Get('letterspace', 0)
                uppercase = node.Get('uppercase', 0)
                extraSpace = 0
                if node is self.sr.node and self.sr.node.Get('editable', 0):
                    extraSpace = 10
                if isinstance(text, basestring):
                    textWidth = uicore.font.GetTextWidth(text, fontsize, hspace, uppercase)
                    if text:
                        columnWidths.append(padLeft + textWidth + padRight + 3 + extraSpace)
                    else:
                        columnWidths.append(3 + extraSpace)
                else:
                    textWidth = text.width
                    columnWidths.append(text.width)

            self.sr.node.customTabstops[columnIdx] = newWidth = max(columnWidths)
            self.UpdateColumnOrder()

    def UpdateTriangles(self):
        activeColumn = settings.user.ui.Get('activeSortColumns', {}).get(self.sr.node.columnID, 0)
        sortDirections = self.GetSortDirections()
        for column in self.sr.columns:
            direction = sortDirections.get(column.columnIdx, True)
            if column.columnIdx == activeColumn and self.sr.node.Get('editable', 0):
                if not column.sr.triangle:
                    column.sr.triangle = uicontrols.Icon(align=uiconst.CENTERRIGHT, pos=(3, 0, 16, 16), parent=column, idx=0, name='directionIcon', icon='ui_1_16_16')
                column.sr.triangle.state = uiconst.UI_DISABLED
                if direction == 1:
                    uiutil.MapIcon(column.sr.triangle, 'ui_1_16_16')
                else:
                    uiutil.MapIcon(column.sr.triangle, 'ui_1_16_15')
            elif column.sr.triangle:
                column.sr.triangle.state = uiconst.UI_HIDDEN

    @classmethod
    def GetCopyData(cls, node):
        displayOrder = settings.user.ui.Get('columnDisplayOrder_%s' % node.columnID, None) or [ i for i in xrange(len(node.texts)) ]
        retString = []
        for i in displayOrder:
            if i <= len(node.texts) - 1:
                retString.append(node.texts[i])

        return '<t>'.join(retString)


class Header(SE_BaseClassCore):
    __guid__ = 'listentry.Header'
    __params__ = ['label']
    default_showHilite = False

    def Startup(self, args):
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=self, left=8, top=0, state=uiconst.UI_DISABLED, maxLines=1, align=uiconst.CENTERLEFT, bold=True)
        self.sr.mainFill = FillThemeColored(parent=self, padBottom=1, colorType=uiconst.COLORTYPE_UIHEADER)

    def Load(self, node):
        self.sr.node = node
        self.sr.label.text = self.sr.node.label

    def GetHeight(self, *args):
        node, width = args
        node.height = uix.GetTextHeight(node.label, maxLines=1) + 6
        return node.height

    @classmethod
    def GetCopyData(cls, node):
        return node.label


class Subheader(SE_BaseClassCore):
    __guid__ = 'listentry.Subheader'
    __params__ = ['label']
    default_showHilite = False

    def Startup(self, args):
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=self, left=8, top=0, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, bold=True)
        self.sr.fill = FillThemeColored(parent=self, padding=(1, 1, 1, 1), colorType=uiconst.COLORTYPE_UIHEADER)

    def Load(self, node):
        self.sr.node = node
        self.sr.label.text = self.sr.node.label

    def GetHeight(self, *args):
        node, width = args
        node.height = uix.GetTextHeight(node.label, maxLines=1) + 6
        return node.height


class Text(SE_BaseClassCore):
    __guid__ = 'listentry.Text'
    __params__ = ['text']
    default_showHilite = False

    def Startup(self, *args):
        self.sr.text = self.sr.label = uicontrols.EveLabelMedium(text='', parent=self, left=8, top=0, state=uiconst.UI_DISABLED, color=None, maxLines=1, align=uiconst.CENTERLEFT)
        self.sr.infoicon = InfoIcon(left=2, parent=self, idx=0, align=uiconst.CENTERRIGHT)
        self.sr.infoicon.OnClick = self.ShowInfo
        self.sr.icon = uicontrols.Icon(parent=self, pos=(1, 2, 24, 24), align=uiconst.TOPLEFT, idx=0, ignoreSize=True)

    def Load(self, node):
        self.sr.node = node
        data = node
        if node.tabs:
            self.sr.text.tabs = node.tabs
        if node.tabMargin:
            self.sr.text.SetTabMargin(node.tabMargin)
        self.sr.text.text = unicode(data.text)
        self.typeID = data.Get('typeID', None)
        self.itemID = data.Get('itemID', None)
        self.isStation = data.Get('isStation', 0)
        if node.Get('hint', None):
            self.hint = node.hint
        if self.typeID or self.isStation and self.itemID:
            self.sr.infoicon.state = uiconst.UI_NORMAL
        else:
            self.sr.infoicon.state = uiconst.UI_HIDDEN
        gid = node.Get('iconID', None)
        iid = node.Get('icon', None)
        if gid or iid:
            if gid:
                self.sr.icon.LoadIcon(node.iconID, ignoreSize=True)
            elif iid:
                self.sr.icon.LoadIcon(node.icon, ignoreSize=True)
            self.sr.icon.SetSize(24, 24)
            self.sr.icon.state = uiconst.UI_NORMAL
            self.sr.text.left = self.height + 4
        else:
            self.sr.icon.state = uiconst.UI_HIDDEN
            self.sr.text.left = 8
        if uiutil.GetAsUnicode(self.sr.text.text).find('<url') != -1:
            self.sr.text.state = uiconst.UI_NORMAL
        else:
            self.sr.text.state = uiconst.UI_DISABLED

    def OnClick(self, *args):
        OnClick = self.sr.node.Get('OnClick', None)
        if OnClick:
            if callable(OnClick):
                OnClick()
            else:
                OnClick[0](*OnClick[1:])

    def OnDblClick(self, *args):
        if self.sr.node.Get('OnDblClick', None):
            self.sr.node.OnDblClick(self)
        elif self.sr.node.Get('canOpen', None):
            uix.TextBox(self.sr.node.canOpen, uiutil.GetAsUnicode(self.sr.node.text).replace('<t>', '<br>').replace('\r', ''), preformatted=1)

    def ShowInfo(self, *args):
        if self.sr.node.Get('isStation', 0) and self.itemID:
            stationinfo = sm.RemoteSvc('stationSvc').GetStation(self.itemID)
            sm.GetService('info').ShowInfo(stationinfo.stationTypeID, self.itemID)
            return
        if self.sr.node.Get('typeID', None):
            sm.GetService('info').ShowInfo(self.sr.node.typeID, self.sr.node.Get('itemID', None))

    def GetHeight(self, *args):
        node, width = args
        node.height = uix.GetTextHeight(node.text, maxLines=1) + 6
        return node.height

    def CopyText(self):
        text = uiutil.GetAsUnicode(self.sr.node.text)
        blue.pyos.SetClipboardData(uiutil.StripTags(text.replace('<t>', ' ')))

    def GetMenu(self):
        m = []
        if self.sr.node.GetMenu:
            m = self.sr.node.GetMenu()
        typeID = self.sr.node.Get('typeID', None)
        if self.sr.node.Get('isStation', 0) and self.itemID or typeID is not None:
            try:
                if self.itemID and typeID is not None:
                    m += sm.GetService('menu').GetMenuFormItemIDTypeID(self.itemID, typeID)
                else:
                    hasShowInfo = False
                    for item in m:
                        if item is not None and item[0][0] == 'UI/Commands/ShowInfo':
                            hasShowInfo = True
                            break

                    if not hasShowInfo:
                        m += [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo), None]
            except:
                pass

        return m + [(uiutil.MenuLabel('UI/Common/Copy'), self.CopyText)]

    @classmethod
    def GetCopyData(cls, node):
        return node.text


class KillMailCondensed(Generic):
    __guid__ = 'listentry.KillMailCondensed'
    isDragObject = True

    def GetDragData(self, *args):
        nodes = [self.sr.node]
        return nodes


class KillMail(SE_BaseClassCore):
    __guid__ = 'listentry.KillMail'
    __params__ = ['mail']
    __nonpersistvars__ = ['selection', 'id']
    ACTION_ICON_SIZE = 16
    isDragObject = True

    def Startup(self, *args):
        sub = uiprimitives.Container(name='sub', parent=self, pos=(0, 0, 0, 0))
        self.sr.leftbox = uiprimitives.Container(parent=sub, align=uiconst.TOLEFT, width=42, height=42, padding=(0, 2, 4, 2))
        self.sr.middlebox = uiprimitives.Container(parent=sub, align=uiconst.TOALL, padding=(0, 2, 0, 0))
        self.sr.icon = uicontrols.Icon(parent=self.sr.leftbox, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        uicontrols.Frame(parent=self.sr.leftbox, color=(0.4, 0.4, 0.4, 0.5))
        self.sr.copyicon = ButtonIcon(parent=sub, align=uiconst.TOPRIGHT, pos=(const.defaultPadding,
         const.defaultPadding,
         self.ACTION_ICON_SIZE,
         self.ACTION_ICON_SIZE), texturePath='res:/UI/Texture/Icons/73_16_1.png', hint=localization.GetByLabel('UI/Control/Entries/CopyKillInfo'), func=self.CopyCombatText)
        self.sr.linkicon = ButtonIcon(parent=sub, align=uiconst.TOPRIGHT, pos=(const.defaultPadding,
         2 * const.defaultPadding + self.ACTION_ICON_SIZE,
         self.ACTION_ICON_SIZE,
         self.ACTION_ICON_SIZE), texturePath='res:/UI/Texture/Icons/hyperlink.png', hint=localization.GetByLabel('UI/Control/Entries/CopyExternalKillLink'), func=self.GetCrestUrl)

    def Load(self, node):
        self.sr.node = node
        self.FillTextAndIcons()

    def UpdateAlignment(self, *args, **kwargs):
        alignment = super(KillMail, self).UpdateAlignment(*args, **kwargs)
        self.UpdateLabelRightFade()
        return alignment

    def UpdateLabelRightFade(self):
        availableWidth = self.sr.middlebox.displayWidth - const.defaultPadding - self.ACTION_ICON_SIZE
        for label in self.sr.middlebox.children:
            label.SetRightAlphaFade(fadeEnd=availableWidth, maxFadeWidth=20)

    def FillTextAndIcons(self):
        kill = self.sr.node.mail
        if self.height == 64:
            expanded = 1
        else:
            expanded = 0
        topLine = 14
        if eve.session.charid == kill.victimCharacterID or eve.session.corpid == kill.victimCorporationID:
            text = localization.GetByLabel('UI/Control/Entries/KillMailShipAndTime', shipTypeID=kill.victimShipTypeID, killTime=max(blue.os.GetWallclockTime() - kill.killTime, 0L))
            self.AddOrSetTextLine(text, configName='killMailsShipAndTimeLabel')
            text = ''
            if kill.victimShipTypeID is not None:
                self.sr.icon.LoadIconByTypeID(kill.victimShipTypeID, ignoreSize=True)
            text = self._GetCorpAndOrAllianceText(kill.finalCorporationID, kill.finalAllianceID)
            self.AddOrSetTextLine(text, configName='killerCorpOrAllianceLabel', top=topLine)
            text = ''
            if kill.finalShipTypeID is not None and kill.finalWeaponTypeID is not None:
                text = localization.GetByLabel('UI/Control/Entries/KillMailShipAndWeapon', shipTypeID=kill.finalShipTypeID, weaponTypeID=kill.finalWeaponTypeID)
            elif kill.finalShipTypeID is not None:
                text = cfg.invtypes.Get(kill.finalShipTypeID).name
            elif kill.finalWeaponTypeID is not None:
                text = cfg.invtypes.Get(kill.finalWeaponTypeID).name
            self.AddOrSetTextLine(text, configName='killerShipOrWeaponLabel', top=topLine * 2)
        elif eve.session.charid == kill.finalCharacterID or eve.session.corpid == kill.finalCorporationID:
            if kill.victimCharacterID is not None or kill.victimCorporationID is not None:
                if kill.victimCharacterID is not None:
                    text = localization.GetByLabel('UI/Control/Entries/KillMailCharacterAndTime', characterID=kill.victimCharacterID, killTime=max(blue.os.GetWallclockTime() - kill.killTime, 0L))
                else:
                    text = util.FormatTimeAgo(kill.killTime)
                self.AddOrSetTextLine(text, configName='victimNameOrTimeLabel')
                text = ''
                text = self._GetCorpAndOrAllianceText(kill.victimCorporationID, kill.victimAllianceID)
                self.AddOrSetTextLine(text, configName='victimCorpOrAllianceLabel', top=topLine)
                text = ''
                if kill.victimShipTypeID and kill.solarSystemID:
                    mapSvc = sm.GetService('map')
                    regionID = mapSvc.GetParent(mapSvc.GetParent(kill.solarSystemID))
                    text = localization.GetByLabel('UI/Control/Entries/KillMailShipAndSolarSystem', shipTypeID=kill.victimShipTypeID, solarSystemID=kill.solarSystemID, regionID=regionID, security=sm.GetService('map').GetSecurityStatus(kill.solarSystemID))
                elif kill.victimShipTypeID:
                    text = cfg.invtypes.Get(kill.victimShipTypeID).name
                elif kill.solarSystemID:
                    mapSvc = sm.GetService('map')
                    regionID = mapSvc.GetParent(mapSvc.GetParent(kill.solarSystemID))
                    text = localization.GetByLabel('UI/Control/Entries/KillMailSolarSystem', solarSystemID=kill.solarSystemID, regionID=regionID, security=sm.GetService('map').GetSecurityStatus(kill.solarSystemID))
                self.AddOrSetTextLine(text, configName='shipNameAndSolarSystemLabel', top=topLine * 2)
            else:
                self.AddOrSetTextLine(localization.GetByLabel('UI/Control/Entries/KillMailUnknown'), configName='unknownLabel')
            if kill.victimShipTypeID is not None:
                self.sr.icon.LoadIconByTypeID(kill.victimShipTypeID, ignoreSize=True)
        else:
            text = localization.GetByLabel('UI/Control/Entries/KillMailError')
            self.sr.icon.LoadIcon('res:/ui/Texture/WindowIcons/personalstandings.png', ignoreSize=True)
            self.sr.copyicon.state = uiconst.UI_HIDDEN
            self.sr.linkicon.state = uiconst.UI_HIDDEN
            self.GetMenu = None

    def _GetCorpAndOrAllianceText(self, corpID, allianceID):
        corpName = None
        corpTicker = ''
        allianceName = None
        allianceTicker = ''
        text = None
        if corpID is not None:
            corpName = cfg.eveowners.Get(corpID).name
            try:
                corpTicker = cfg.corptickernames.Get(corpID).tickerName
            except KeyError as e:
                pass

        if allianceID is not None:
            allianceName = cfg.eveowners.Get(allianceID).name
            try:
                allianceTicker = cfg.allianceshortnames.Get(allianceID).shortName
            except KeyError as e:
                pass

        if corpName and allianceName:
            text = localization.GetByLabel('UI/Control/Entries/KillMailCorpAndAlliance', corpName=corpName, corpTicker=corpTicker, allianceName=allianceName, allianceTicker=allianceTicker)
        elif corpName:
            text = localization.GetByLabel('UI/Control/Entries/KillMailCorpOrAlliance', name=corpName, ticker=corpTicker)
        elif allianceName:
            text = localization.GetByLabel('UI/Control/Entries/KillMailCorpOrAlliance', name=allianceName, ticker=allianceTicker)
        return text

    def AddOrSetTextLine(self, text, configName = '', top = 0):
        if text:
            label = getattr(self, configName, None)
            if label is not None:
                label.text = text
            else:
                label = uicontrols.EveLabelSmall(text=text, parent=self.sr.middlebox, align=uiconst.TOPLEFT, top=top)
                if configName:
                    setattr(self, configName, label)

    def GetMenu(self):
        m = []
        if self.sr.node.GetMenu:
            m = self.sr.node.GetMenu()
        return m + [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.RedirectToInfo, (1,)),
         None,
         (uiutil.MenuLabel('UI/Control/Entries/CopyKillInformation'), self.GetCombatText, (1,)),
         (uiutil.MenuLabel('UI/Control/Entries/CopyExternalKillLink'), self.GetCrestUrl, ())]

    def RedirectToInfo(self, *args):
        kill = self.sr.node.mail
        if kill.victimCharacterID == session.charid:
            baddieGuyID = None
            if kill.finalCharacterID is None:
                baddieGuyID = kill.finalCorporationID
            else:
                baddieGuyID = kill.finalCharacterID
            char = cfg.eveowners.Get(baddieGuyID)
            sm.StartService('info').ShowInfo(int(char.Type()), baddieGuyID)
        elif kill.victimCharacterID is not None:
            char = cfg.eveowners.Get(kill.victimCharacterID)
            sm.StartService('info').ShowInfo(int(char.Type()), kill.victimCharacterID)
        elif kill.victimCorporationID is not None:
            sm.StartService('info').ShowInfo(const.typeCorporation, kill.victimCorporationID)
        elif kill.allianceID is not None:
            sm.StartService('info').ShowInfo(const.typeAlliance, kill.victimAllianceID)

    def GetCombatText(self, isCopy = 0, *args):
        mail = self.sr.node.mail
        ret = util.CombatLog_CopyText(mail)
        if isCopy:
            blue.pyos.SetClipboardData(util.CleanKillMail(ret))
        else:
            return ret

    def CopyCombatText(self):
        text = self.GetCombatText()
        blue.pyos.SetClipboardData(util.CleanKillMail(text))

    def GetCrestUrl(self, *args):
        crest_url = util.GetPublicCrestUrl('killmails', self.sr.node.mail.killID, util.GetKillReportHashValue(self.sr.node.mail))
        blue.pyos.SetClipboardData(crest_url)

    def _OnClose(self):
        self.timer = None
        uicontrols.SE_BaseClassCore.Close(self)

    def GetHeight(self, *args):
        node, width = args
        node.height = 46
        return node.height

    def OnDblClick(self, *args):
        mail = self.sr.node.mail
        kill = mail
        if kill is not None:
            from eve.client.script.ui.shared.killReportUtil import OpenKillReport
            OpenKillReport(kill)

    def GetDragData(self, *args):
        nodes = [self.sr.node]
        return nodes


class LabelText(SE_BaseClassCore):
    __guid__ = 'listentry.LabelText'

    def Startup(self, args):
        self.sr.label = uicontrols.EveLabelSmall(text='', parent=self, left=8, top=4, state=uiconst.UI_DISABLED, bold=True)
        self.sr.text = uicontrols.EveLabelMedium(text='', parent=self, left=0, top=4, align=uiconst.TOALL, state=uiconst.UI_DISABLED)

    def Load(self, node):
        self.sr.node = node
        self.sr.label.text = self.name = self.sr.node.label
        self.sr.text.left = int(self.sr.node.Get('textpos', 128)) + 4
        self.sr.text.text = self.sr.node.text
        if self.sr.node.Get('labelAdjust', 0):
            self.sr.label.width = self.sr.node.Get('labelAdjust', 0)

    def GetHeight(self, *args):
        node, width = args
        descwidth = min(256 - int(node.Get('textpos', 128)), width - int(node.Get('textpos', 128)) - 8)
        height = uix.GetTextHeight(node.text, fontsize=fontConst.EVE_MEDIUM_FONTSIZE, width=descwidth, hspace=0, linespace=12)
        height = max(height, uix.GetTextHeight(node.label, fontsize=fontConst.EVE_MEDIUM_FONTSIZE, width=width, hspace=0, linespace=12))
        node.height = max(19, height + 4)
        return node.height


class IconLabelText(SE_BaseClassCore):
    __guid__ = 'listentry.IconLabelText'
    ICON_POS_REPLACES_LABEL = 0
    ICON_POS_REPLACES_TEXT = 1
    ICON_POS_IN_FRONT_OF_LABEL = 2
    ICON_POS_BEHIND_LABEL = 3
    ICON_POS_IN_FRONT_OF_TEXT = 4
    ICON_POS_BEHIND_TEXT = 5
    ICON_POS_NO_ICON = 6
    iconSize = 16
    margin = 4
    defaultTextWidth = 128

    def Startup(self, args):
        self.sr.label = uicontrols.EveLabelSmallBold(text='', parent=self, left=8, top=4, state=uiconst.UI_DISABLED)
        self.sr.text = uicontrols.EveLabelSmall(text='', parent=self, left=0, top=4, align=uiconst.TOALL, state=uiconst.UI_DISABLED)

    def Load(self, node):
        self.sr.node = node
        iconPositioning = self.sr.node.Get('iconPositioning', IconLabelText.ICON_POS_IN_FRONT_OF_LABEL)
        self.iconID = self.sr.node.Get('icon', None)
        if self.iconID is None:
            iconPositioning = IconLabelText.ICON_POS_NO_ICON
        hasLabel = True
        hasText = True
        if iconPositioning == IconLabelText.ICON_POS_REPLACES_LABEL:
            hasLabel = False
            textOffset = self.margin
            self.InsertIcon(textOffset)
        elif iconPositioning == IconLabelText.ICON_POS_REPLACES_TEXT:
            hasText = False
            textOffset = int(self.sr.node.Get('textpos', self.defaultTextWidth)) + self.margin
            self.InsertIcon(textOffset)
        elif iconPositioning == IconLabelText.ICON_POS_IN_FRONT_OF_LABEL:
            textOffset = self.margin
            self.InsertIcon(textOffset)
            textOffset += self.sr.icon.width
            self.sr.label.left = textOffset + self.margin
        elif iconPositioning == IconLabelText.ICON_POS_IN_FRONT_OF_TEXT:
            textOffset = self.margin + self.sr.text.left
            self.InsertIcon(textOffset)
            textOffset += self.sr.icon.width
            self.sr.text.left = textOffset + self.margin
        if hasLabel:
            self.sr.label.text = self.name = self.sr.node.label
            if self.sr.node.Get('labelAdjust', 0):
                self.sr.label.width = self.sr.node.Get('labelAdjust', 0)
        if hasText:
            self.sr.text.left = int(self.sr.node.Get('textpos', self.defaultTextWidth)) + self.margin
            self.sr.text.text = self.sr.node.text
        if iconPositioning == IconLabelText.ICON_POS_BEHIND_LABEL:
            textOffset = self.margin + self.sr.label.left + self.sr.label.width
            self.InsertIcon(textOffset)
        elif iconPositioning == IconLabelText.ICON_POS_BEHIND_TEXT:
            textOffset = self.margin + self.sr.text.left + self.sr.text.width
            self.InsertIcon(textOffset)

    def InsertIcon(self, offset):
        self.sr.icon = uicontrols.Icon(icon=self.iconID, parent=self, pos=(offset,
         1,
         self.iconSize,
         self.iconSize), align=uiconst.TOPLEFT, idx=0)

    def GetHeight(self, *args):
        node, width = args
        height = IconLabelText.GetDynamicHeight(node, width)
        node.height = height
        return height

    def GetDynamicHeight(node, width):
        textpos = node.Get('textpos', 128)
        labelWidth, labelHeight = uicontrols.EveLabelSmallBold.MeasureTextSize(node.label, width=width)
        descWidth, descHeight = uicontrols.EveLabelSmall.MeasureTextSize(node.text, width=width - textpos)
        height = max(19, labelHeight, descHeight)
        return height + 8


class TextTimer(Text):
    __guid__ = 'listentry.TextTimer'

    def Startup(self, *args):
        Text.Startup(self, args)
        self.sr.label = uicontrols.EveLabelSmall(text='', parent=self, left=8, top=2, state=uiconst.UI_DISABLED)
        self.sr.text.SetAlign(uiconst.TOPLEFT)
        self.sr.text.top = 12

    def Load(self, node):
        Text.Load(self, node)
        self.sr.label.text = self.sr.node.label
        self.sr.label.left = self.sr.text.left
        self.sr.text.top = self.sr.label.top + self.sr.label.textheight - 2
        countdownTime = node.Get('countdownTime', None)
        countupTime = node.Get('countupTime', None)
        finalText = node.Get('finalText', None)
        if countdownTime is not None or countupTime is not None:
            self.UpdateTime(countdownTime, countupTime)
            self.sr.timeOutTimer = base.AutoTimer(1000, self.UpdateTime, countdownTime, countupTime, finalText)
        else:
            self.sr.text.text = localization.GetByLabel('UI/Control/Entries/TimeUnknown')
            self.sr.timeOutTimer = None

    def GetHeight(self, *args):
        node, width = args
        labelheight = uix.GetTextHeight(node.label, fontsize=fontConst.EVE_SMALL_FONTSIZE, maxLines=1, uppercase=1)
        textheight = uix.GetTextHeight(node.text, fontsize=fontConst.EVE_MEDIUM_FONTSIZE, maxLines=1)
        node.height = 2 + labelheight + textheight
        return node.height

    def UpdateTime(self, countdownTime = None, countupTime = None, finalText = None):
        if countupTime:
            timerText = localization.GetByLabel('UI/Control/Entries/TimeAgo', time=blue.os.GetWallclockTime() - countupTime)
            self.sr.text.text = timerText
            self.hint = timerText
        elif countdownTime:
            if finalText is not None and countdownTime - blue.os.GetWallclockTime() < 0:
                timerText = finalText
                self.sr.timeOutTimer = None
            else:
                timerText = localization.GetByLabel('UI/Control/Entries/TimeIn', time=max(0L, countdownTime - blue.os.GetWallclockTime()))
            self.sr.text.text = timerText
            self.hint = timerText
        if getattr(self.sr.node, 'text', None) is not None:
            self.sr.node.text = self.sr.text.text


class LabelTextTop(Text):
    __guid__ = 'listentry.LabelTextTop'
    default_showHilite = True

    def Startup(self, *args):
        self.sr.infoicon = InfoIcon(left=2, parent=self, idx=0, align=uiconst.CENTERRIGHT)
        self.sr.infoicon.OnClick = self.ShowInfo
        self.sr.icon = uicontrols.Icon(parent=self, pos=(1, 2, 24, 24), align=uiconst.TOPLEFT, idx=0, ignoreSize=True)
        self.sr.label = uicontrols.EveLabelSmall(text='', parent=self, left=8, top=2, state=uiconst.UI_DISABLED)
        self.textClipper = Container(parent=self)
        self.sr.text = uicontrols.EveLabelMedium(parent=self.textClipper, left=8, top=12, state=uiconst.UI_DISABLED, color=None, maxLines=1, align=uiconst.TOPLEFT, autoFadeSides=32)

    def Load(self, node):
        Text.Load(self, node)
        if self.sr.infoicon.display:
            self.textClipper.padRight = 20
        else:
            self.textClipper.padRight = 0
        self.sr.label.text = self.sr.node.label
        self.sr.label.left = self.sr.text.left
        self.sr.text.top = self.sr.label.top + self.sr.label.textheight

    def GetHeight(self, *args):
        node, width = args
        labelheight = uix.GetTextHeight(node.label, fontsize=fontConst.EVE_SMALL_FONTSIZE, maxLines=1, uppercase=1)
        textheight = uix.GetTextHeight(node.text, fontsize=fontConst.EVE_MEDIUM_FONTSIZE, maxLines=1)
        node.height = 2 + labelheight + textheight
        return node.height

    @classmethod
    def GetCopyData(cls, node):
        return '%s\t%s' % (node.label, unicode(node.text))


class LabelTextSides(Text):
    __guid__ = 'listentry.LabelTextSides'
    default_showHilite = True

    def Startup(self, *args):
        Text.Startup(self, args)
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=self, left=8, top=0, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
        self.sr.text.SetAlign(uiconst.CENTERRIGHT)
        self.sr.text.top = 0
        self.sr.infoicon.SetAlign(uiconst.CENTERRIGHT)
        self.sr.infoicon.top = 0
        self.sr.infoicon.left = 6

    def Load(self, node):
        Text.Load(self, node)
        self.sr.label.text = self.sr.node.label
        if self.sr.infoicon.display:
            self.sr.text.left = 26
        else:
            self.sr.text.left = 8
        self.sr.text.top = 0
        if not self.sr.icon.display and node.get('iconID', None) is None:
            self.sr.label.left = 8
        else:
            self.sr.label.left = self.sr.icon.width + 4

    def GetHeight(self, *args):
        node, width = args
        node.height = 30
        return 30

    def _OnSizeChange_NoBlock(self, newWidth, newHeight):
        textWidth = self.sr.text.textwidth
        availableTextWidth = newWidth - textWidth - self.sr.label.left - 10
        self.sr.label.SetRightAlphaFade(fadeEnd=availableTextWidth, maxFadeWidth=20)

    @classmethod
    def GetCopyData(cls, node):
        return '%s\t%s' % (node.label, unicode(node.text))


class LabelTextSidesMoreInfo(LabelTextSides):
    __guid__ = 'listentry.LabelTextSidesMoreInfo'
    default_showHilite = True

    def Startup(self, *args):
        LabelTextSides.Startup(self, args)
        self.sr.moreinfoicon = MoreInfoIcon(left=2, parent=self, idx=0, align=uiconst.CENTERRIGHT)
        self.sr.moreinfoicon.SetAlign(uiconst.CENTERRIGHT)
        self.sr.moreinfoicon.top = 0
        self.sr.moreinfoicon.left = 6
        self.sr.infoicon.display = False

    def Load(self, node):
        LabelTextSides.Load(self, node)
        self.sr.text.left = 26
        self.sr.moreinfoicon.hint = node.get('moreInfoHint', '')


class StatusBar(LabelTextSides):
    __guid__ = 'listentry.StatusBar'
    default_gradientBrightnessFactor = 1.5
    default_color = util.Color.GRAY

    def Startup(self, *args):
        LabelTextSides.Startup(self, args)
        self.sr.gauge = Gauge(parent=self, gaugeHeight=28, align=uiconst.TOTOP, top=1, padding=(1, 0, 1, 0), state=uiconst.UI_DISABLED)

    def Load(self, node):
        LabelTextSides.Load(self, node)
        self.sr.gauge.gradientBrightnessFactor = node.Get('gradientBrightnessFactor', self.default_gradientBrightnessFactor)
        color = node.Get('color', self.default_color)
        self.sr.gauge.SetColor(color)
        self.sr.gauge.SetBackgroundColor(color)
        self.sr.gauge.SetValueInstantly(node.Get('value', 0.0))


class LabelMultilineTextTop(LabelTextSides):
    """
    This was created to solve multiline attribute entries for show info, if used in a wider context adaptation may be requried.
    """
    __guid__ = 'listentry.LabelMultilineTextTop'

    def Startup(self, *args):
        LabelTextSides.Startup(self, args)
        self.sr.label.SetAlign(uiconst.TOPLEFT)
        self.sr.label.top = 10
        self.sr.text.maxLines = None

    def Load(self, node):
        LabelTextSides.Load(self, node)
        labelheight = uix.GetTextHeight(node.label, fontsize=fontConst.EVE_SMALL_FONTSIZE, maxLines=1, uppercase=1)
        textheight = uix.GetTextHeight(node.text, fontsize=fontConst.EVE_MEDIUM_FONTSIZE, maxLines=1)
        textWidth = self.sr.text.textwidth
        self.sr.text.width = textWidth
        self.sr.text.text = '<right>' + self.sr.text.text

    def GetHeight(self, *args):
        node, width = args
        labelheight = uix.GetTextHeight(node.label, fontsize=fontConst.EVE_SMALL_FONTSIZE, maxLines=1, uppercase=1)
        textheight = uix.GetTextHeight(node.text, fontsize=fontConst.EVE_MEDIUM_FONTSIZE, maxLines=None)
        node.height = 2 + labelheight + textheight
        return node.height


class LocationTextEntry(Text):
    __guid__ = 'listentry.LocationTextEntry'
    isDragObject = True
    default_showHilite = True

    def GetDragData(self, *args):
        nodes = [self.sr.node]
        return nodes


class LabelLocationTextTop(LabelTextTop):
    __guid__ = 'listentry.LabelLocationTextTop'
    isDragObject = True

    def GetDragData(self, *args):
        nodes = [self.sr.node]
        return nodes


class LocationGroup(ListGroup):
    __guid__ = 'listentry.LocationGroup'
    isDragObject = True

    def GetDragData(self, *args):
        dragDataFunc = self.sr.node.get('GetDragDataFunc', None)
        if dragDataFunc:
            return dragDataFunc(self.sr.node)
        nodes = [self.sr.node]
        return nodes

    def Load(self, node):
        ListGroup.Load(self, node)
        if node.inMyPath:
            self.sr.label.color = util.Color.YELLOW


class Button(SE_BaseClassCore):
    __guid__ = 'listentry.Button'
    __params__ = ['label', 'caption', 'OnClick']
    default_showHilite = False

    def Startup(self, args):
        self.sr.label = uicontrols.EveLabelMedium(parent=self, left=8, top=-1, state=uiconst.UI_DISABLED, maxLines=1, align=uiconst.CENTERLEFT)
        self.sr.button = uicontrols.Button(parent=self, label='', align=uiconst.TOPRIGHT, pos=(2, 2, 0, 0), idx=0)

    def Load(self, node):
        self.sr.node = node
        maxLines = node.Get('maxLines', 1)
        self.sr.label.maxLines = maxLines
        btnWidth = 0
        if self.sr.node.Get('OnClick', None):
            node = self.sr.node
            butt = self.sr.button
            ags = node.Get('args', (None,))
            self.sr.button.OnClick = lambda *args: node.OnClick(*(ags + (butt,)))
            self.sr.button.SetLabel(self.sr.node.caption)
            self.sr.button.state = uiconst.UI_NORMAL
            btnWidth = self.sr.button.width
        else:
            self.sr.button.state = uiconst.UI_HIDDEN
        if maxLines != 1:
            l, t, w, h = self.GetAbsolute()
            self.sr.label.width = w - btnWidth - self.sr.label.left * 2
        self.sr.label.text = self.sr.node.label

    def GetHeight(self, *args):
        node, width = args
        if node.Get('OnClick', None):
            btnLabelWidth = uix.GetTextWidth(node.caption, fontsize=fontConst.EVE_MEDIUM_FONTSIZE)
            btnWidth = min(256, max(48, btnLabelWidth + 24))
            btnLabelHeight = uix.GetTextHeight(node.caption, fontsize=fontConst.EVE_MEDIUM_FONTSIZE)
            btnHeight = min(32, btnLabelHeight + 9)
        else:
            btnWidth = 0
            btnHeight = 0
        maxLines = node.Get('maxLines', 1)
        if maxLines == 1:
            mainLabelHeight = uix.GetTextHeight(node.label, fontsize=fontConst.EVE_MEDIUM_FONTSIZE, maxLines=1)
            node.height = max(16, mainLabelHeight + 4, btnHeight + 2)
        else:
            width = node.Get('entryWidth', 100) - btnWidth
            mainLabelHeight = uix.GetTextHeight(node.label, width=width, fontsize=fontConst.EVE_MEDIUM_FONTSIZE)
            node.height = max(16, mainLabelHeight + 4, btnHeight + 2)
        return node.height


class Line(SE_BaseClassCore):
    __guid__ = 'listentry.Line'
    __params__ = []
    default_showHilite = False

    def Load(self, node):
        self.sr.node = node
        self.sr.node.height = 1

    def GetHeight(self, *args):
        node, width = args
        return node.height


class Combo(SE_BaseClassCore):
    __guid__ = 'listentry.Combo'
    __params__ = ['OnChange', 'label', 'options']
    default_showHilite = False

    def Startup(self, args):
        uiprimitives.Container(name='push', parent=self, height=5, align=uiconst.TOTOP, idx=0)
        self.sr.combo = uicontrols.Combo(parent=self, label='', options=[], name='', callback=self.OnComboChange, align=uiconst.TOTOP)
        self.sr.push = uiprimitives.Container(name='push', parent=self, width=128, align=uiconst.TOLEFT, idx=0)
        self.sr.label = uicontrols.EveLabelSmall(text='', parent=self, left=8, top=5, width=112, state=uiconst.UI_DISABLED)
        uiprimitives.Container(name='push', parent=self, width=3, align=uiconst.TORIGHT, idx=0)

    def Load(self, node):
        self.sr.node = node
        self.sr.combo.LoadOptions(self.sr.node.options, self.sr.node.Get('setValue', None))
        self.sr.label.text = self.sr.node.label
        self.sr.push.width = max(128, self.sr.label.textwidth + 10)
        if self.sr.node.Get('name', ''):
            self.sr.combo.name = self.sr.node.name

    def OnComboChange(self, combo, header, value, *args):
        if self.sr.node.Get('settingsUser', 0):
            settings.user.ui.Set(self.sr.node.cfgName, value)
        self.sr.node.setValue = value
        self.sr.node.OnChange(combo, header, value)

    def GetHeight(self, *args):
        node, width = args
        node.height = max(22, uix.GetTextHeight(node.label, width=112)) + 6
        return node.height


class Edit(SE_BaseClassCore):
    __guid__ = 'listentry.Edit'
    __params__ = ['label']
    default_showHilite = False

    def Startup(self, args):
        uiprimitives.Container(name='push', parent=self, height=3, align=uiconst.TOTOP)
        uiprimitives.Container(name='push', parent=self, width=128, align=uiconst.TOLEFT)
        uiprimitives.Container(name='push', parent=self, width=3, align=uiconst.TORIGHT)
        self.sr.edit = uicontrols.SinglelineEdit(name='edit', parent=self, align=uiconst.TOTOP)
        self.sr.label = uicontrols.EveLabelSmall(text='', parent=self, left=8, top=5, width=112, state=uiconst.UI_DISABLED)

    def Load(self, node):
        self.sr.node = node
        self.sr.label.text = self.sr.node.label
        self.sr.edit.floatmode = None
        self.sr.edit.integermode = None
        if self.sr.node.Get('lines', 1) != 1:
            log.LogError('listentry.Edit is not multi line')
        if self.sr.node.Get('intmode', 0):
            minInt, maxInt = self.sr.node.intmode
            self.sr.edit.IntMode(minInt, maxInt)
        elif self.sr.node.Get('floatmode', 0):
            minFloat, maxFloat = self.sr.node.floatmode
            self.sr.edit.FloatMode(minFloat, maxFloat)
        if self.sr.node.Get('setValue', None) is None:
            self.sr.node.setValue = ''
        self.sr.edit.SetValue(self.sr.node.setValue)
        if self.sr.node.Get('maxLength', None):
            self.sr.edit.SetMaxLength(self.sr.node.maxLength)
        if self.sr.node.Get('name', ''):
            self.sr.edit.name = self.sr.node.name
        self.sr.edit.OnChange = self.OnChange

    def OnChange(self, *args):
        if self is not None and not self.destroyed and self.sr.node is not None:
            self.sr.node.setValue = self.sr.edit.GetValue()

    def GetHeight(self, *args):
        node, width = args
        node.height = max(22, uix.GetTextHeight(node.label, width=112)) + 6
        return node.height


class TextEdit(SE_BaseClassCore):
    __guid__ = 'listentry.TextEdit'
    __params__ = ['label']
    default_showHilite = False

    def Startup(self, args):
        uiprimitives.Container(name='push', parent=self, height=4, align=uiconst.TOTOP)
        uiprimitives.Container(name='push', parent=self, height=4, align=uiconst.TOBOTTOM)
        uiprimitives.Container(name='push', parent=self, width=127, align=uiconst.TOLEFT)
        uiprimitives.Container(name='push', parent=self, width=2, align=uiconst.TORIGHT)
        import uicls
        self.sr.edit = uicls.EditPlainText(setvalue='', parent=self, align=uiconst.TOALL)
        self.sr.label = uicontrols.EveLabelSmall(text='', parent=self, left=8, top=3, width=112, state=uiconst.UI_DISABLED)

    def Load(self, node):
        self.sr.node = node
        self.sr.label.text = self.sr.node.label
        if self.sr.node.Get('readonly', None):
            self.sr.edit.ReadOnly()
        else:
            self.sr.edit.Editable(0)
        if self.sr.node.Get('setValue', None) is None:
            self.sr.node.setValue = ''
        self.sr.edit.SetValue(self.sr.node.setValue)
        if self.sr.node.Get('maxLength', None):
            self.sr.edit.SetMaxLength(self.sr.node.maxLength)
        if self.sr.node.Get('name', ''):
            self.sr.edit.name = self.sr.node.name
        self.sr.edit.OnChange = self.OnChange
        if getattr(self.sr.node, 'killFocus', None):
            self.sr.edit.OnKillFocus()

    def OnChange(self, *args):
        if self is not None and not self.destroyed and self.sr.node is not None:
            self.sr.node.setValue = self.sr.edit.GetValue()

    def GetHeight(self, *args):
        node, width = args
        node.height = node.Get('lines', 1) * 14 + 10
        return node.height


class ImplantEntry(SE_BaseClassCore):
    __guid__ = 'listentry.ImplantEntry'
    __params__ = ['label']

    def Startup(self, *etc):
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=self, left=32, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED)
        self.sr.timeLabel = uicontrols.EveLabelMedium(text='', parent=self, left=6, top=2, state=uiconst.UI_DISABLED, align=uiconst.BOTTOMRIGHT)
        self.sr.icon = uicontrols.Icon(icon='ui_22_32_30', parent=self, size=32, align=uiconst.RELATIVE, state=uiconst.UI_DISABLED)
        self.sr.infoicon = InfoIcon(left=2, parent=self, idx=0, align=uiconst.CENTERRIGHT)
        self.sr.infoicon.OnClick = self.ShowInfo

    def Load(self, node):
        self.sr.node = node
        data = node
        if cfg.invtypes.Get(self.sr.node.implant_booster.typeID).groupID == const.groupBooster:
            slot = getattr(sm.GetService('godma').GetType(node.implant_booster.typeID), 'boosterness', None)
            timeToEnd = node.implant_booster.expiryTime
        else:
            slot = getattr(sm.GetService('godma').GetType(node.implant_booster.typeID), 'implantness', None)
            timeToEnd = None
        if slot is None:
            self.sr.label.text = data.label
        else:
            self.sr.label.text = localization.GetByLabel('UI/Control/Entries/ImplantLabel', implantName=data.label, slotNum=int(slot))
        self.sr.icon.LoadIcon(cfg.invtypes.Get(node.implant_booster.typeID).iconID, ignoreSize=True)
        self.sr.icon.SetSize(32, 32)
        if timeToEnd is not None:
            self.UpdateTime(timeToEnd)
            self.sr.timeOutTimer = base.AutoTimer(1000, self.UpdateTime, timeToEnd)
        else:
            self.sr.timeLabel.text = ''
            self.sr.timeOutTimer = None

    def UpdateTime(self, timeToEnd):
        timeInterval = timeToEnd - blue.os.GetWallclockTime()
        if timeInterval > const.MONTH30:
            timeBreakAt = 'hour'
        elif timeInterval > const.DAY:
            timeBreakAt = 'min'
        else:
            timeBreakAt = 'sec'
        self.sr.timeLabel.text = util.FmtTimeInterval(timeInterval, timeBreakAt)

    def GetMenu(self):
        m = [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo)]
        if not cfg.invtypes.Get(self.sr.node.implant_booster.typeID).groupID == const.groupBooster and getattr(self.sr.node.implant_booster, 'itemID', None):
            m.append((uiutil.MenuLabel('UI/Control/Entries/ImplantUnplug'), self.RemoveImplant, (self.sr.node.implant_booster.itemID,)))
        return m

    def OnDblClick(self, *args):
        self.ShowInfo()

    def ShowInfo(self, *args):
        sm.GetService('info').ShowInfo(self.sr.node.implant_booster.typeID, getattr(self.sr.node.implant_booster, 'itemID', None))

    def RemoveImplant(self, itemID):
        if eve.Message('ConfirmUnPlugInImplant', {}, uiconst.OKCANCEL) == uiconst.ID_OK:
            sm.GetService('godma').GetSkillHandler().RemoveImplantFromCharacter(itemID)

    def GetDynamicHeight(self, width):
        text = localization.GetByLabel('UI/Control/Entries/ImplantLabel', implantName=self.label, slotNum=0)
        _, textHeight = uicontrols.EveLabelMedium.MeasureTextSize(text)
        return max(32, textHeight + const.defaultPadding)


class IconEntry(SE_BaseClassCore):
    __guid__ = 'listentry.IconEntry'
    __params__ = ['label']

    def Startup(self, *etc):
        self.labelleft = 32
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=self, left=self.labelleft, top=0, width=512, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
        self.sr.icon = GlowSprite(icon='ui_5_64_10', parent=self, pos=(0, 0, 0, 0), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)

    def Load(self, node):
        self.sr.node = node
        data = node
        self.sr.label.width = data.Get('maxLabelWidth', 512)
        self.sr.label.text = data.label
        if data.Get('icon', None) is not None:
            self.sr.icon.LoadIcon(data.icon, ignoreSize=True)
        iconoffset = node.Get('iconoffset', 0)
        self.sr.icon.left = iconoffset
        iconsize = node.Get('iconsize', 32)
        labeloffset = node.Get('labeloffset', 0)
        self.sr.icon.width = self.sr.icon.height = iconsize
        self.sr.label.left = iconsize + iconoffset + labeloffset
        if node.Get('selectable', 1) and node.Get('selected', 0):
            self.Select()
        else:
            self.Deselect()
        if node.Get('hint', None):
            self.hint = data.hint

    def OnClick(self, *args):
        if self.sr.node and self.sr.node.Get('selectable', 1):
            self.BlinkOff()
            self.sr.node.scroll.SelectNode(self.sr.node)
            eve.Message('ListEntryClick')
            if self.sr.node.Get('OnClick', None):
                self.sr.node.OnClick(self)

    def GetHeight(self, *args):
        node, width = args
        iconsize = node.Get('iconsize', 32)
        node.height = iconsize
        return node.height

    def Blink(self, hint = None, force = 1, blinkcount = 3, frequency = 750, bright = 0):
        blink = self.GetBlink()
        blink.state = uiconst.UI_DISABLED
        sm.GetService('ui').BlinkSpriteRGB(blink, min(1.0, self.r * (1.0 + bright * 0.25)), min(1.0, self.g * (1.0 + bright * 0.25)), min(1.0, self.b * (1.0 + bright * 0.25)), frequency, blinkcount, passColor=1)

    def BlinkOff(self):
        if self.sr.Get('blink', None) is not None:
            self.sr.blink.state = uiconst.UI_HIDDEN

    def GetBlink(self):
        if self.sr.Get('blink', None):
            return self.sr.blink
        blink = uiprimitives.Fill(bgParent=self, name='hiliteFrame', state=uiconst.UI_HIDDEN, color=(0.28, 0.3, 0.35, 1.0), align=uiconst.TOALL)
        self.sr.blink = blink
        self.r = 0.28
        self.g = 0.3
        self.b = 0.35
        return self.sr.blink

    @classmethod
    def GetCopyData(cls, node):
        return node.label

    def OnMouseEnter(self, *args):
        SE_BaseClassCore.OnMouseEnter(self, *args)
        self.sr.icon.OnMouseEnter()

    def OnMouseExit(self, *args):
        SE_BaseClassCore.OnMouseExit(self, *args)
        self.sr.icon.OnMouseExit()


class Icons(SE_BaseClassCore):
    __guid__ = 'listentry.Icons'
    __params__ = ['icons']

    def Load(self, node):
        i = 0
        for each in node.icons:
            icon, color, identifier, click = each
            if i >= len(self.children):
                newicon = uiprimitives.Container(parent=self, pos=(0,
                 0,
                 self.height,
                 self.height), name='glassicon', state=uiconst.UI_NORMAL, align=uiconst.RELATIVE)
                uiprimitives.Sprite(parent=newicon, name='dot', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/shared/windowDOT.png', align=uiconst.TOALL, spriteEffect=trinity.TR2_SFX_DOT, blendMode=trinity.TR2_SBM_ADD)
                newicon.sr.icon = uiprimitives.Sprite(parent=newicon, name='picture', state=uiconst.UI_NORMAL, align=uiconst.TOALL)
                newicon.sr.color = uiprimitives.Fill(parent=newicon, name='color', state=uiconst.UI_DISABLED, color=(0.45, 0.5, 1.0, 1.0))
                newicon.left = i * self.height
            else:
                newicon = self.children[i]
            if icon:
                newicon.sr.icon.LoadTexture(icon)
                newicon.sr.icon.state = uiconst.UI_DISABLED
            else:
                newicon.sr.icon.state = uiconst.UI_HIDDEN
            if color:
                newicon.sr.color.SetRGB(*color)
                newicon.sr.color.state = uiconst.UI_DISABLED
            else:
                newicon.sr.color.state = uiconst.UI_HIDDEN
            newicon.OnClick = (click, newicon)
            newicon.sr.identifier = identifier
            i += 1


class CheckEntry(Text):
    __guid__ = 'listentry.CheckEntry'

    def Startup(self, *args):
        Text.Startup(self, args)
        self.sr.text.color.SetRGB(1.0, 1.0, 1.0, 0.75)
        self.sr.have = uicontrols.Icon(parent=self, align=uiconst.CENTERLEFT, left=5, top=0, height=16, width=16, state=uiconst.UI_DISABLED)

    def Load(self, args):
        Text.Load(self, args)
        data = self.sr.node
        if data.checked:
            self.sr.have.LoadIcon('ui_38_16_193')
        else:
            self.sr.have.LoadIcon('ui_38_16_194')
        self.sr.have.left = 15 * data.sublevel - 11
        self.sr.text.left = 15 * data.sublevel + 5

    def GetMenu(self):
        m = []
        data = self.sr.node
        if data is not None:
            if data.Get('typeID', 0):
                m = sm.StartService('menu').GetMenuFormItemIDTypeID(None, data.typeID, ignoreMarketDetails=0)
        return m


class FittingEntry(Generic):
    __guid__ = 'listentry.FittingEntry'
    isDragObject = True

    def GetDragData(self, *args):
        nodes = [self.sr.node]
        return nodes

    def Startup(self, *args):
        parent = uiprimitives.Container(name='parent', parent=self, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.sr.infoContainer = uiprimitives.Container(name='infoContainer', parent=parent, align=uiconst.TORIGHT, width=16)
        self.sr.infoicon = InfoIcon(left=1, top=1, parent=self.sr.infoContainer, idx=0)
        self.sr.have = uicontrols.Icon(parent=parent, align=uiconst.TORIGHT, left=0, top=0, height=16, width=16)
        self.sr.label = uicontrols.EveLabelMedium(parent=parent, left=5, state=uiconst.UI_DISABLED, maxLines=1, align=uiconst.CENTERLEFT)
        self.sr.infoicon.OnClick = self.ShowInfo
        self.hints = [localization.GetByLabel('UI/Control/Entries/FittingSkillMissing'), localization.GetByLabel('UI/Control/Entries/FittingSkillOK')]
        for eventName in events:
            setattr(self.sr, eventName, None)

    def Load(self, node):
        Generic.Load(self, node)
        hasSkill = self.HasSkill(node)
        if hasSkill:
            iconNum = 'ui_38_16_193'
        else:
            iconNum = 'ui_38_16_194'
        hint = self.hints[hasSkill]
        if node.Get('typeID', None) is None:
            self.sr.infoContainer.state = uiconst.UI_HIDDEN
        self.sr.have.LoadIcon(iconNum, ignoreSize=True)
        self.sr.have.SetSize(16, 16)
        self.sr.have.hint = hint
        self.sr.label.Update()

    def GetHeight(self, *args):
        node, width = args
        if node.Get('vspace', None):
            node.height = uix.GetTextHeight(node.label, maxLines=1) + node.vspace
        else:
            node.height = uix.GetTextHeight(node.label, maxLines=1) + 4
        return node.height

    def HasSkill(self, node):
        return sm.StartService('fittingSvc').HasSkillForFit(node.fitting)


class FittingEntryNonDraggable(FittingEntry):
    __guid__ = 'listentry.FittingEntryNonDraggable'

    def Startup(self, *args):
        FittingEntry.Startup(self, args)


class FittingModuleEntry(Item):
    __guid__ = 'listentry.FittingModuleEntry'

    def Startup(self, *args):
        Item.Startup(self, args)
        self.padLeft = 2
        self.sr.haveIcon = uicontrols.Icon(parent=self, align=uiconst.CENTERRIGHT, pos=(18, 0, 16, 16))
        self.hints = [localization.GetByLabel('UI/Control/Entries/FittingModuleSkillMissing'), localization.GetByLabel('UI/Control/Entries/FittingModuleSkillOK')]

    def HasSkill(self, node):
        if node.effectID == const.effectRigSlot:
            return True
        godma = sm.StartService('godma')
        return godma.CheckSkillRequirementsForType(node.typeID)

    def Load(self, node):
        Item.Load(self, node)
        hasSkill = self.HasSkill(node)
        if hasSkill:
            iconNum = 'ui_38_16_193'
        else:
            iconNum = 'ui_38_16_194'
        hint = self.hints[hasSkill]
        self.sr.haveIcon.LoadIcon(iconNum, ignoreSize=True)
        self.sr.haveIcon.hint = hint

    def GetMenu(self):
        if self.sr.node and self.sr.node.Get('GetMenu', None):
            return self.sr.node.GetMenu(self)
        if getattr(self, 'itemID', None) or getattr(self, 'typeID', None):
            return sm.GetService('menu').GetMenuFormItemIDTypeID(getattr(self, 'itemID', None), getattr(self, 'typeID', None), ignoreMarketDetails=0)
        return []


class SkillTreeEntry(Text):
    __guid__ = 'listentry.SkillTreeEntry'
    isDragObject = True
    default_showHilite = True
    COLOR_NOTTRAINED = (0.15, 0.07, 0.07, 0.5)
    COLOR_PARTIAL = (0.2, 0.15, 0.0, 0.5)
    COLOR_TRAINED = (0.122, 0.188, 0.235, 1.0)
    COLOR_RESTRICTED = (0.965, 0.467, 0.157, 1.0)

    def Startup(self, *args):
        Text.Startup(self, args)
        self.sr.text.color.SetRGB(1.0, 1.0, 1.0, 0.75)
        self.sr.have = uicontrols.Icon(parent=self, left=5, top=0, height=16, width=16, align=uiconst.CENTERLEFT)
        self.bgPattern = Sprite(bgParent=self, align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/Skills/hatchPattern.png', tileX=True, tileY=True, color=self.COLOR_RESTRICTED, opacity=0.0, padding=(1, 1, 1, 0))
        self.bgFill = uiprimitives.Fill(bgParent=self, padding=(1, 1, 1, 0), opacity=0.0)

    def Load(self, data):
        data.text = self.GetSkillText(data.typeID, data.lvl)
        Text.Load(self, data)
        skills = sm.GetService('skills').MySkills(byTypeID=True)
        isTrialRestricted = sm.GetService('skills').IsTrialRestricted(data.typeID)
        if isTrialRestricted:
            self.sr.have.LoadTexture('res:/UI/Texture/classes/Skills/trial-restricted-16.png')
            self.sr.have.hint = localization.GetByLabel('UI/InfoWindow/SkillRestrictedForTrial')
            self.sr.have.color = self.COLOR_RESTRICTED

            def OpenSubscriptionPage(*args):
                uicore.cmd.OpenSubscriptionPage(origin=getattr(data, 'origin') or ORIGIN_UNKNOWN, reason=':'.join(['skill', str(data.typeID)]))

            self.sr.have.OnClick = OpenSubscriptionPage
            self.bgFill.SetRGBA(0.2, 0.1, 0.05, 1.0)
            self.bgPattern.opacity = 0.15
        elif skills is not None and data.typeID in skills:
            if skills[data.typeID].skillLevel >= data.lvl:
                self.sr.have.LoadIcon('ui_38_16_193')
                self.sr.have.hint = localization.GetByLabel('UI/InfoWindow/TrainedAndOfRequiredLevel')
                if data.indent != 1:
                    self.sr.text.opacity = 0.15
                else:
                    self.bgFill.SetRGBA(*self.COLOR_TRAINED)
            else:
                self.sr.have.LoadIcon('ui_38_16_195')
                self.sr.have.hint = localization.GetByLabel('UI/InfoWindow/TrainedButNotOfRequiredLevel')
                self.bgFill.SetRGBA(*self.COLOR_PARTIAL)
        else:
            self.sr.have.LoadIcon('ui_38_16_194')
            self.sr.have.hint = localization.GetByLabel('UI/InfoWindow/NotTrained')
            self.bgFill.SetRGBA(*self.COLOR_NOTTRAINED)
        self.sr.have.left = 15 * data.indent - 11
        self.sr.text.left = 15 * data.indent + 7

    def GetSkillText(self, typeID, lvl):
        if int(lvl) <= 0:
            romanNumber = '-'
        else:
            romanNumber = util.IntToRoman(min(5, int(lvl)))
        return localization.GetByLabel('UI/InfoWindow/SkillAndLevelInRoman', skill=typeID, levelInRoman=romanNumber)

    def GetMenu(self):
        return sm.GetService('menu').GetMenuForSkill(self.typeID)

    def OnDblClick(self, *args):
        sm.GetService('info').ShowInfo(self.sr.node.typeID)

    def GetDragData(self, *args):
        nodes = [self.sr.node]
        return nodes

    def GetHeight(self, *args):
        return 28


HEIGHT = 28

class CertEntry(ListGroup):
    __guid__ = 'listentry.CertEntry'
    isDragObject = True
    default_iconSize = 22

    def Startup(self, *args):
        ListGroup.Startup(self, *args)
        self.progressIcon = uiprimitives.Sprite(name='progressIcon', parent=self, align=uiconst.CENTERRIGHT, pos=(2, 0, 16, 16))

    def Load(self, node):
        node.showlen = False
        ListGroup.Load(self, node)
        self.certificate = node.certificate
        self.certID = self.certificate.certificateID
        self.level = node.level
        self.sr.label.text = self.certificate.GetLabel(self.level)
        currLevel = self.certificate.GetLevel()
        if currLevel >= self.level:
            self.progressIcon.LoadIcon('ui_38_16_193')
            self.progressIcon.hint = localization.GetByLabel('UI/InfoWindow/TrainedAndOfRequiredLevel')
        elif self.certificate.HasAllSkills(self.level):
            self.progressIcon.LoadIcon('ui_38_16_195')
            self.progressIcon.hint = localization.GetByLabel('UI/InfoWindow/TrainedButNotOfRequiredLevel')
        else:
            self.progressIcon.LoadIcon('ui_38_16_194')
            self.progressIcon.hint = localization.GetByLabel('UI/InfoWindow/NotTrained')

    def GetMenu(self):
        m = [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (self.certID,))]
        if session.role & ROLE_GMH == ROLE_GMH:
            m.append(('GM: Give all skills', self.GMGiveAllSkills, ()))
        return m

    def GMGiveAllSkills(self):
        skills = sm.GetService('certificates').GetCertificate(self.certID).SkillsByTypeAndLevel(self.level)
        for typeID, level in skills:
            if sm.GetService('skills').MySkillLevel(typeID) < level:
                sm.RemoteSvc('slash').SlashCmd('/giveskill me %s %s' % (typeID, level))

    def GetHeight(self, *args):
        node, _ = args
        node.height = HEIGHT
        return node.height

    def ShowInfo(self, *args):
        abstractinfo = util.KeyVal(certificateID=self.certID, level=self.level)
        sm.StartService('info').ShowInfo(const.typeCertificate, abstractinfo=abstractinfo)

    def OnDblClick(self, *args):
        self.ShowInfo()

    @staticmethod
    def GetSubContent(node, *args):
        skillSvc = sm.GetService('skills')
        filterAcquired = settings.user.ui.Get('masteries_filter_acquired', False)
        scrolllist = []
        skills = sm.GetService('certificates').GetCertificate(node.certificate.certificateID).SkillsByTypeAndLevel(node.level)
        for typeID, lvl in skills:
            try:
                if filterAcquired and skillSvc.GetMySkillsFromTypeID(typeID).skillLevel >= lvl:
                    continue
            except AttributeError:
                pass

            data = util.KeyVal(line=True, typeID=typeID, lvl=lvl, indent=2, hint=sm.GetService('skills').GetSkillToolTip(typeID, lvl), origin=ORIGIN_CERTIFICATES)
            scrolllist.append(Get(data=data, decoClass=SkillTreeEntry))

        return scrolllist

    def GetHint(self):
        return self.certificate.GetDescription()

    def GetDragData(self, *args):
        return (self.sr.node,)


class CertEntryBasic(SE_BaseClassCore):
    __guid__ = 'listentry.CertEntryBasic'
    __params__ = ['label']
    isDragObject = True

    def Startup(self, *etc):
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=self, left=40, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED)
        self.sr.icon = uicontrols.Icon(parent=self, align=uiconst.CENTERLEFT, left=12, state=uiconst.UI_DISABLED)
        self.sr.infoicon = InfoIcon(left=2, parent=self, idx=0, align=uiconst.CENTERRIGHT)
        self.sr.infoicon.OnClick = self.ShowInfo

    def Load(self, node):
        self.node = node
        self.sr.label.text = self.node.label
        self.sr.icon.LoadIcon(self.node.iconID, ignoreSize=True)
        iconSize = node.Get('iconSize', 20)
        self.sr.icon.SetSize(iconSize, iconSize)

    def GetMenu(self):
        return [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo, (self.node.certID,))]

    def OnDblClick(self, *args):
        self.ShowInfo()

    def ShowInfo(self, *args):
        abstractinfo = util.KeyVal(certificateID=self.node.certID, level=self.node.level)
        sm.StartService('info').ShowInfo(const.typeCertificate, abstractinfo=abstractinfo)

    def GetDynamicHeight(self, width):
        return 24

    def GetHint(self):
        return sm.GetService('certificates').GetCertificate(self.node.certID).GetDescription()

    def GetDragData(self, *args):
        return (self.sr.node,)


class PermissionEntry(Generic):
    __guid__ = 'listentry.PermissionEntry'
    __params__ = ['label', 'itemID']

    def ApplyAttributes(self, attributes):
        Generic.ApplyAttributes(self, attributes)
        self.columns = [0, 1, 2]

    def Startup(self, *args):
        Generic.Startup(self)
        self.sr.checkBoxes = {}
        i = 220
        for column in self.columns:
            cbox = uicontrols.Checkbox(text='', parent=self, configName='', retval=column, callback=self.VisibilityFlagsChange, align=uiconst.TOPLEFT, pos=(i + 7,
             1,
             16,
             0))
            self.sr.checkBoxes[column] = cbox
            i += 30

        self.sr.label.top = 0
        self.sr.label.left = 6
        self.sr.label.SetAlign(uiconst.CENTERLEFT)
        self.flag = 0

    def Load(self, node):
        Generic.Load(self, node)
        data = self.sr.node
        self.flag = data.visibilityFlags
        if data.Get('tempFlag', None) is not None:
            self.flag = data.tempFlag
        for cboxID, cbox in self.sr.checkBoxes.iteritems():
            cbox.state = uiconst.UI_NORMAL
            cbox.SetGroup(data.itemID)
            cbox.data.update({'key': data.itemID})
            if self.flag == cboxID:
                cbox.SetChecked(1, 0)
            else:
                cbox.SetChecked(0, 0)

        if self.sr.node.scroll.sr.tabs:
            self.OnColumnChanged()

    def OnColumnChanged(self, *args):
        tabs = self.sr.node.scroll.sr.tabs
        for i, key in enumerate(self.columns):
            width = tabs[i + 1] - tabs[i]
            self.sr.checkBoxes[key].left = self.sr.node.scroll.sr.tabs[i] + width / 2 - 8

    def GetHeight(self, *args):
        node, _ = args
        node.height = max(19, uix.GetTextHeight(node.label, maxLines=1) + 4)
        return node.height

    def VisibilityFlagsChange(self, checkbox):
        self.flag = checkbox.data['value']

    def HasChanged(self):
        return self.flag != self.sr.node.visibilityFlags


class CorpAllianceEntry(Generic):
    __guid__ = 'listentry.CorpAllianceEntry'
    isDragObject = True

    def GetDragData(self, *args):
        return [self.sr.node]


class DraggableItem(Item):
    __guid__ = 'listentry.DraggableItem'
    isDragObject = True

    def GetDragData(self, *args):
        return self.sr.node.scroll.GetSelectedNodes(self.sr.node)


def Get(entryType = None, settings = {}, data = None, decoClass = None):
    if data is None:
        if isinstance(settings, util.KeyVal):
            data = settings.__dict__
        else:
            data = settings
    elif isinstance(data, util.KeyVal):
        data = data.__dict__
    import listentry
    if decoClass is None:
        if entryType is not None:
            decoClass = getattr(listentry, entryType)
        else:
            log.LogError('decoClass missing')
    data['__guid__'] = getattr(decoClass, '__guid__', None)
    data['decoClass'] = decoClass
    return uicontrols.ScrollEntryNode(**data)


def GetFromClass(entryType, settings = {}, data = None):
    if data is None:
        if isinstance(settings, util.KeyVal):
            data = settings.__dict__
        else:
            data = settings
    elif isinstance(data, util.KeyVal):
        data = data.__dict__
    data['__guid__'] = getattr(entryType, '__guid__', None)
    data['decoClass'] = entryType
    return uicontrols.ScrollEntryNode(**data)


def SortNodeList(nodes, columnID, reverse = False):
    if not nodes:
        return nodes
    displayOrder = settings.user.ui.Get('columnDisplayOrder_%s' % columnID, None) or [ i for i in xrange(len(nodes[0].sortData)) ]
    c = 0
    sortData = []
    for node in nodes:
        if not c:
            c = len(node.sortData)
        elif c != len(node.sortData):
            raise RuntimeError('Mismatch in column sizes')
        sortData.append((ReorderSortData(node.sortData[:], columnID, displayOrder), node))

    sortData = uiutil.SortListOfTuples(sortData, reverse)
    return sortData


def SortColumnEntries(nodes, columnID):
    if not nodes:
        return nodes
    displayOrder = settings.user.ui.Get('columnDisplayOrder_%s' % columnID, None) or [ i for i in xrange(len(nodes[0].sortData)) ]
    c = 0
    sortData = []
    for node in nodes:
        if not c:
            c = len(node.sortData)
        elif c != len(node.sortData):
            raise RuntimeError('Mismatch in column sizes')
        sortData.append((ReorderSortData(node.sortData[:], columnID, displayOrder), node))

    sortDirections = settings.user.ui.Get('columnSorts_%s' % columnID, [0, {}])
    sortData = uiutil.SortListOfTuples(sortData)
    activeColumn = settings.user.ui.Get('activeSortColumns', {}).get(columnID, 0)
    if activeColumn in sortDirections and sortDirections[activeColumn] is False:
        sortData.reverse()
    return sortData


def ReorderSortData(sortData, columnID, displayOrder):
    if not sortData:
        return sortData
    if len(displayOrder) != len(sortData):
        return sortData
    ret = []
    activeColumn = settings.user.ui.Get('activeSortColumns', {}).get(columnID, 0)
    if activeColumn in displayOrder:
        di = displayOrder.index(activeColumn)
    else:
        di = 0
    for columnIdx in displayOrder[di:]:
        ret.append(sortData[columnIdx])

    return ret


def InitCustomTabstops(columnID, entries):
    idxs = []
    for i in xrange(len(entries[0].texts)):
        idxs.append(i)

    if not len(idxs):
        return
    current = GetCustomTabstops(columnID)
    if current is not None:
        if len(current) == len(idxs):
            return
    retval = []
    for columnIdx in idxs:
        textsInColumn = []
        columnWidths = []
        for node in entries:
            text = node.texts[columnIdx]
            textsInColumn.append(text)
            padLeft = node.Get('padLeft', 6)
            padRight = node.Get('padRight', 6)
            fontsize = node.Get('fontsize', 12)
            hspace = node.Get('letterspace', 0)
            uppercase = node.Get('uppercase', 0)
            if isinstance(text, basestring):
                textWidth = uicore.font.GetTextWidth(text, fontsize, hspace, uppercase)
            else:
                textWidth = text.width
            extraSpace = 0
            if node.Get('editable', 0):
                extraSpace = 10
            columnWidths.append(padLeft + textWidth + padRight + 3 + extraSpace)

        retval.append(max(columnWidths))

    settings.user.ui.Set('listentryColumns_%s' % columnID, retval)


def GetCustomTabstops(columnID):
    return settings.user.ui.Get('listentryColumns_%s' % columnID, None)


exports = {'listentry.Get': Get,
 'listentry.GetFromClass': GetFromClass,
 'listentry.SortColumnEntries': SortColumnEntries,
 'listentry.SortNodeList': SortNodeList,
 'listentry.InitCustomTabstops': InitCustomTabstops,
 'listentry.GetCustomTabstops': GetCustomTabstops,
 'listentry.DraggableItem': DraggableItem}
