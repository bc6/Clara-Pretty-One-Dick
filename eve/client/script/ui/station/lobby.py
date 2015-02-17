#Embedded file name: eve/client/script/ui/station\lobby.py
import blue
from carbon.common.script.util.format import FmtAmt, CaseFoldCompare
from carbonui.control.basicDynamicScroll import BasicDynamicScroll
from carbonui.control.scrollentries import SE_BaseClassCore
from carbonui.primitives.container import Container
from carbonui.primitives.flowcontainer import FlowContainer
from carbonui.primitives.frame import Frame
from carbonui.primitives.line import Line
from carbonui.primitives.sprite import Sprite
from carbonui.util.various_unsorted import SortListOfTuples, NiceFilter
from eve.client.script.ui.control.buttonGroup import ButtonGroup
from eve.client.script.ui.control.buttons import BigButton, ToggleButtonGroup, ToggleButtonGroupButton, Button
from eve.client.script.ui.control.entries import Get as GetListEntry
from eve.client.script.ui.control.eveIcon import GetLogoIcon, CheckCorpID
from eve.client.script.ui.control.eveLabel import CaptionLabel, EveLabelSmall, EveLabelMedium, Label
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.control.infoIcon import InfoIcon
from eve.client.script.ui.control.tabGroup import TabGroup
from eve.client.script.ui.control.themeColored import LineThemeColored
from eve.client.script.ui.control.utilMenu import UtilMenu
from eve.client.script.ui.quickFilter import QuickFilterEdit
import log
import sys
from inventorycommon.util import IsNPC
import uthread
import carbonui.const as uiconst
import localization
import telemetry
import collections
import invCont
import invCtrl
import const
import evegraphics.settings as gfxsettings
from eve.client.script.ui.shared.inventory.invWindow import Inventory as InventoryWindow
from utillib import KeyVal
COLOR_UNDOCK = (0.75,
 0.6,
 0.0,
 1.0)
COLOR_CQ = (0.0,
 0.713,
 0.75,
 1.0)
MAX_CORP_DESC_LENGTH = 140
MAX_CORP_DESC_LINES = 1
BIGBUTTONSIZE = 48
SMALLBUTTONSIZE = 32
BUTTONGAP = 4
AGENTSPANEL = 'agentsPanel'
GUESTSPANEL = 'guestsPanel'
OFFICESPANEL = 'officesPanel'
INVENTORYPANEL = 'inventoryPanel'

class LobbyToggleButtonGroupButton(ToggleButtonGroupButton):

    @apply
    def displayRect():
        fget = ToggleButtonGroupButton.displayRect.fget

        def fset(self, value):
            ToggleButtonGroupButton.displayRect.fset(self, value)
            self.label.width = uicore.ReverseScaleDpi(self.displayWidth) - 12

        return property(**locals())


class CounterBox(Container):
    _number = 0

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.label = Label(parent=self, align=uiconst.CENTER, fontPath='res:/UI/Fonts/EveSansNeue-Expanded.otf', fontsize=10)
        Frame(bgParent=self, texturePath='res:/UI/Texture/Shared/counterFrame.png', cornerSize=8, offset=-1, color=(0.2, 0.2, 0.2, 1))
        if 'text' in attributes:
            self.text = attributes.text
        else:
            self.display = False

    @apply
    def text():

        def fget(self):
            return self._number

        def fset(self, value):
            self._number = value
            self.label.text = value
            self.width = max(14, self.label.textwidth + 8)
            self.height = max(14, self.label.textheight)
            if self.label.text:
                self.display = True
            else:
                self.display = False

        return property(**locals())


class Lobby(Window):
    __guid__ = 'form.Lobby'
    __notifyevents__ = ['OnCharNowInStation',
     'OnCharNoLongerInStation',
     'OnProcessStationServiceItemChange',
     'OnAgentMissionChange',
     'OnStandingSet',
     'OnCorporationChanged',
     'OnCorporationMemberChanged',
     'OnPrimaryViewChanged',
     'OnSetDevice']
    default_windowID = 'lobby'
    default_top = 16
    default_width = 223
    default_captionLabelPath = 'UI/Station/StationServices'
    default_pinned = True
    selectedGroupButtonID = None

    @staticmethod
    def default_height(*args):
        return uicore.desktop.height - 100

    @staticmethod
    def default_left(*args):
        return uicore.desktop.width - Lobby.default_width - 16

    def OnPrimaryViewChanged(self, oldViewInfo, newViewInfo):
        """
        Since the view states happen so late in all transitions we
        need to rehook the function and label to the station mode button.
        """
        self.UpdateCQButton(newViewInfo.name)

    def OnSetDevice(self):
        bottom = self.top + self.height
        if bottom > uicore.desktop.height:
            self.height = max(self.default_minSize[1], uicore.desktop.height - self.top)
        right = self.left + self.width
        if right > uicore.desktop.width:
            self.width = max(self.default_minSize[0], uicore.desktop.width - self.left)

    def ApplyAttributes(self, attributes):
        self.viewState = sm.GetService('viewState')
        if not settings.user.ui.Get('stationservicebtns', 1):
            minWidth = BIGBUTTONSIZE + (BIGBUTTONSIZE + BUTTONGAP) * 3 + 14
            minHeight = 495
        else:
            minWidth = SMALLBUTTONSIZE + (SMALLBUTTONSIZE + BUTTONGAP) * 5 + 10
            minHeight = 470
        self.default_minSize = (minWidth, minHeight)
        Window.ApplyAttributes(self, attributes)
        self.stationSvc = sm.GetService('station')
        self.guestScroll = None
        self.sr.serviceAccessCache = {}
        self.SetWndIcon(None)
        self.HideHeader()
        self.scope = 'station'
        self.MakeUnKillable()
        self.MakeUnstackable()
        self.SetTopparentHeight(0)
        main = self.sr.main
        main.clipChildren = True
        self.corpLogoParent = Container(name='corpLogoParent', align=uiconst.TOTOP, height=160, parent=main)
        self.corpName = CaptionLabel(parent=main, align=uiconst.TOTOP, name='corpName', uppercase=False)
        self.undockparent = Container(name='undockparent', align=uiconst.TOTOP, height=78, parent=main)
        self.AddCQButton(parent=self.undockparent)
        self.AddUndockButton(parent=self.undockparent)
        EveLabelMedium(text=localization.GetByLabel('UI/Station/StationServices'), align=uiconst.TOTOP, parent=main, bold=True, padding=(6, 6, 6, 0))
        self.serviceButtons = FlowContainer(name='serviceButtons', align=uiconst.TOTOP, parent=main, contentSpacing=(BUTTONGAP, BUTTONGAP), padding=(6, 6, 3, 6))
        btnGroup = ToggleButtonGroup(name='btnGroup', parent=main, align=uiconst.TOTOP, height=32, padding=(6, 6, 6, 6), idx=-1, callback=self.OnButtonGroupSelection)
        self.mainButtonGroup = btnGroup
        self.guestsPanel = Container(name=GUESTSPANEL, parent=main, padding=const.defaultPadding)
        self.quickFilter = QuickFilterEdit(name='quickFilterEdit', parent=self.guestsPanel)
        self.quickFilter.ReloadFunction = lambda : self.ShowGuests()
        self.guestScroll = BasicDynamicScroll(parent=self.guestsPanel, padTop=const.defaultPadding + self.quickFilter.height)
        guestSettingsMenu = UtilMenu(menuAlign=uiconst.TOPRIGHT, parent=self.guestsPanel, align=uiconst.TOPRIGHT, GetUtilMenu=self.SettingMenu, texturePath='res:/UI/Texture/SettingsCogwheel.png', width=18, height=18, iconSize=18)
        self.userType = settings.user.ui.Get('guestCondensedUserList', False)
        self.agentsPanel = Container(name=AGENTSPANEL, parent=main, padding=const.defaultPadding)
        self.agentFinderBtn = Button(label=localization.GetByLabel('UI/AgentFinder/AgentFinder'), parent=self.agentsPanel, align=uiconst.CENTERTOP, func=uicore.cmd.OpenAgentFinder)
        self.agentScroll = Scroll(parent=self.agentsPanel, padTop=const.defaultPadding + self.agentFinderBtn.height)
        self.officesPanel = Container(name=OFFICESPANEL, parent=main, padding=const.defaultPadding)
        self.officesButtons = FlowContainer(name='officesButtons', align=uiconst.TOTOP, parent=self.officesPanel, contentSpacing=(4, 4), centerContent=True)
        self.officesScroll = Scroll(parent=self.officesPanel, padTop=const.defaultPadding)
        agentsButton = btnGroup.AddButton(AGENTSPANEL, '<center>' + localization.GetByLabel('UI/Station/Lobby/Agents'), self.agentsPanel, btnClass=LobbyToggleButtonGroupButton, hint=localization.GetByLabel('Tooltips/StationServices/AgentsTab_descrtiption'))
        agentsButton.name = 'stationInformationTabAgents'
        guestsButton = btnGroup.AddButton(GUESTSPANEL, '<center>' + localization.GetByLabel('UI/Station/Lobby/Guests'), self.guestsPanel, btnClass=LobbyToggleButtonGroupButton, hint=localization.GetByLabel('Tooltips/StationServices/GuestsTab_description'))
        guestsButton.counter = CounterBox(parent=guestsButton, align=uiconst.TOPRIGHT, left=2, top=-5)
        self.guestsButton = guestsButton
        btnGroup.AddButton(OFFICESPANEL, '<center>' + localization.GetByLabel('UI/Station/Lobby/Offices'), self.officesPanel, btnClass=LobbyToggleButtonGroupButton, hint=localization.GetByLabel('Tooltips/StationServices/OfficesTab_description'))
        activePanel = settings.user.ui.Get('stationsLobbyTabs', AGENTSPANEL)
        if settings.char.windows.Get('dockshipsanditems', 0):
            self.inventoryPanel = Container(name=INVENTORYPANEL, parent=main)
            self.sr.shipsContainer = Container(parent=self.inventoryPanel, state=uiconst.UI_HIDDEN, padding=const.defaultPadding)
            self.sr.itemsContainer = Container(parent=self.inventoryPanel, state=uiconst.UI_HIDDEN, padding=const.defaultPadding)
            tabs = [[localization.GetByLabel('UI/Station/Ships'),
              self.sr.shipsContainer,
              self,
              'lobby_ships'], [localization.GetByLabel('UI/Station/Items'),
              self.sr.itemsContainer,
              self,
              'lobby_items']]
            self.inventoryTabs = TabGroup(name='inventoryPanel', parent=self.inventoryPanel, idx=0)
            self.inventoryTabs.Startup(tabs, 'lobbyInventoryPanel', autoselecttab=True, UIIDPrefix='lobbyInventoryPanelTab')
            self.invButton = btnGroup.AddButton(INVENTORYPANEL, '<center>' + localization.GetByLabel('UI/Station/Lobby/Hangars'), self.inventoryPanel, btnClass=LobbyToggleButtonGroupButton, hint='<b>%s</b><br>%s' % (localization.GetByLabel('Tooltips/StationServices/Hangars'), localization.GetByLabel('Tooltips/StationServices/Hangars_description')))
        elif activePanel == INVENTORYPANEL:
            activePanel = AGENTSPANEL
        btnGroup.SelectByID(activePanel)
        myDefaultView = 'hangar' if session.userid % 2 == 1 else 'station'
        curView = collections.namedtuple('FakeViewInfo', ['name'])(settings.user.ui.Get('defaultDockingView', myDefaultView))
        self.OnPrimaryViewChanged(curView, curView)
        self.LoadOwnerInfo()
        self.LoadServiceButtons()
        if self.destroyed:
            return
        sm.RegisterNotify(self)
        self.UpdateGuestTabText()

    def OnButtonGroupSelection(self, buttonID):
        settings.user.ui.Set('stationsLobbyTabs', buttonID)
        self.selectedGroupButtonID = buttonID
        if buttonID == AGENTSPANEL:
            self.ShowAgents()
        elif buttonID == GUESTSPANEL:
            self.ShowGuests()
        elif buttonID == OFFICESPANEL:
            self.ShowOffices()
        elif buttonID == INVENTORYPANEL:
            if not len(self.sr.shipsContainer.children):
                self.LayoutShipsAndItems()

    def SettingMenu(self, menuParent):
        showCompact = settings.user.ui.Get('guestCondensedUserList', False)
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Chat/ShowCompactMemberList'), checked=bool(showCompact), callback=(self.ShowGuests, not showCompact))

    def AddCQButton(self, parent):
        """
        Creates the undock button at the bottom of the lobby
        """
        scale = 1.0
        self.cqCont = Container(name='cqCont', align=uiconst.TOLEFT_PROP, width=0.5, parent=parent, state=uiconst.UI_PICKCHILDREN, padding=3)
        width = 63 * scale
        height = 34 * scale
        self.cqSpriteCont = Container(name='cq', align=uiconst.CENTERTOP, width=width, height=height, top=3, parent=self.cqCont, state=uiconst.UI_NORMAL)
        self.cqSprites = []
        spacing = 30 * scale
        for i in xrange(3):
            s = Sprite(parent=self.cqSpriteCont, texturePath='res:/UI/Texture/classes/Lobby/{0}.png'.format(i + 1), align=uiconst.CENTERTOP, width=-width, height=height, left=0, state=uiconst.UI_DISABLED)
            s.color = COLOR_CQ
            self.cqSprites.insert(0, s)

        self.cqLabel = EveLabelMedium(parent=self.cqCont, align=uiconst.CENTERTOP, top=8 + height, width=100)
        self.UpdateCQButton()
        if gfxsettings.Get(gfxsettings.MISC_LOAD_STATION_ENV):
            self.cqSpriteCont.OnClick = self.OnCQClicked
            self.cqSpriteCont.OnMouseEnter = self.OnCQMouseEnter
            self.cqSpriteCont.OnMouseExit = self.OnCQMouseExit
        else:
            self.cqSpriteCont.hint = localization.GetByLabel('UI/Station/CannotEnterCaptainsQuarters')
            for s in self.cqSprites:
                s.opacity = 0.2

    def OnCQClicked(self, *args):
        self.OnCQMouseExit()
        for i, s in enumerate(self.cqSprites):
            uicore.animations.SpGlowFadeIn(s, glowColor=(0.8, 0.8, 0.1, 0.3), glowExpand=1, loops=1, duration=1.0, curveType=uiconst.ANIM_WAVE, timeOffset=(3 - i) * 0.1)

        if self.IsInCQ():
            self.EnterHangar()
        else:
            self.EnterCQ()

    def OnCQMouseEnter(self, *args):
        self.AnimateCQSprites((0.8, 1, 1))

    def OnCQMouseExit(self, *args):
        self.AnimateCQSprites(COLOR_CQ[:3])

    def AnimateCQSprites(self, endColor):
        for i, s in enumerate(self.cqSprites):
            uicore.animations.SpColorMorphTo(s, startColor=(s.color.r, s.color.g, s.color.b), endColor=endColor, duration=0.1)

    def UpdateCQButton(self, viewName = None):
        isInCQ = False
        if viewName is not None:
            isInCQ = viewName == 'station'
        else:
            isInCQ = self.IsInCQ()
        if isInCQ:
            self.cqLabel.text = '<center>' + localization.GetByLabel('UI/Commands/EnterHangar') + '</center>'
        else:
            self.cqLabel.text = '<center>' + localization.GetByLabel('UI/Commands/EnterCQ') + '</center>'
        self.cqCont.height = self.cqLabel.height + self.cqSpriteCont.height + 6

    def IsInCQ(self):
        viewStateSvc = sm.GetService('viewState')
        currentView = viewStateSvc.GetCurrentView()
        if currentView is not None and currentView.name == 'station':
            return True
        else:
            return False

    def AddUndockButton(self, parent):
        """
        Creates the undock button at the bottom of the lobby
        """
        scale = 1.0
        self.undockCont = Container(name='undockCont', align=uiconst.TORIGHT_PROP, width=0.5, parent=parent, state=uiconst.UI_PICKCHILDREN, padding=3)
        width = 63 * scale
        height = 34 * scale
        self.undockSpriteCont = Container(name='undock', align=uiconst.CENTERTOP, width=width, height=height, top=3, parent=self.undockCont, state=uiconst.UI_NORMAL)
        self.undockSprites = []
        spacing = 30 * scale
        for i in xrange(3):
            s = Sprite(parent=self.undockSpriteCont, texturePath='res:/UI/Texture/classes/Lobby/{0}.png'.format(i + 1), align=uiconst.CENTERTOP, width=width, height=height, left=0, state=uiconst.UI_DISABLED)
            s.color = COLOR_UNDOCK
            self.undockSprites.append(s)

        self.undockLabel = EveLabelMedium(parent=self.undockCont, align=uiconst.CENTERTOP, top=8 + height, width=100)
        self.UpdateUndockButton()
        self.undockCont.height = self.undockLabel.height + height + 6
        self.undockSpriteCont.OnClick = self.OnUndockClicked
        self.undockSpriteCont.OnMouseEnter = self.OnUndockMouseEnter
        self.undockSpriteCont.OnMouseExit = self.OnUndockMouseExit

    def OnUndockClicked(self, *args):
        if sm.GetService('station').PastUndockPointOfNoReturn():
            return
        uthread.new(self.AttemptToUndock).context = 'UndockButtonThread'

    def LockCQButton(self):
        self.cqCont.opacity = 0.5
        self.cqCont.state = uiconst.UI_DISABLED

    def UnlockCQButton(self):
        self.cqCont.opacity = 1.0
        self.cqCont.state = uiconst.UI_NORMAL

    def AttemptToUndock(self):
        exiting = sm.GetService('station').Exit()
        if exiting:
            self.LockCQButton()

    def OnUndockMouseEnter(self, *args):
        self.AnimateUndockSprites((1, 1, 0.8))

    def OnUndockMouseExit(self, *args):
        self.AnimateUndockSprites(COLOR_UNDOCK[:3])

    def AnimateUndockSprites(self, endColor):
        if sm.GetService('station').PastUndockPointOfNoReturn():
            return
        for i, s in enumerate(self.undockSprites):
            uicore.animations.SpColorMorphTo(s, startColor=(s.color.r, s.color.g, s.color.b), endColor=endColor, duration=0.1)

    def SetUndockProgress(self, undockProgress):
        if undockProgress is None:
            self.UpdateUndockButton()
            return
        i = int(undockProgress * 3)
        if i < 3:
            self.UpdateUndockButton()
            uicore.animations.SpGlowFadeIn(self.undockSprites[i], glowColor=(1.0, 1.0, 0.8, 0.2), glowExpand=1, loops=1, duration=0.2)
        else:
            self.undockLabel.text = '<center>' + localization.GetByLabel('UI/Station/UndockingConfirmed') + '</center>'
            for i, s in enumerate(self.undockSprites):
                uicore.animations.StopAllAnimations(s)
                s.glowColor = (0, 0, 0, 0)
                uicore.animations.SpColorMorphTo(s, startColor=(1, 0.8, 0), endColor=(1, 0, 0), loops=1000, duration=1, curveType=uiconst.ANIM_WAVE, timeOffset=i * 0.1 - 0.5, includeAlpha=False)
                uicore.animations.SpGlowFadeIn(s, glowColor=(1.0, 1.0, 0.8, 0.2), glowExpand=1, loops=1000, duration=1, curveType=uiconst.ANIM_WAVE, timeOffset=i * 0.1)

    def UpdateUndockButton(self):
        if self.stationSvc.exitingstation:
            self.undockLabel.text = '<center>' + localization.GetByLabel('UI/Station/AbortUndock') + '</center>'
            self.LockCQButton()
        else:
            self.undockLabel.text = '<center>' + localization.GetByLabel('UI/Neocom/UndockBtn') + '</center>'
            self.UnlockCQButton()

    def EnterCQ(self, *args):
        if self.viewState.HasActiveTransition():
            return
        sm.GetService('cmd').CmdEnterCQ()

    def EnterHangar(self, *args):
        if self.viewState.HasActiveTransition():
            return
        sm.GetService('cmd').CmdEnterHangar()

    def OnScale_(self, *args):
        return
        height = 0
        for each in self.sr.main.children:
            if each.align in (uiconst.TOTOP, uiconst.TOBOTTOM):
                height += each.padTop + each.height + each.padBottom

        height += 160
        self.SetMinSize([self.minsize[0], height])

    def LayoutShipsAndItems(self):
        self.sr.itemsContainer.Flush()
        itemsContainer = invCont.StationItems(name='stationItems', parent=self.sr.itemsContainer, showControls=True, state=uiconst.UI_NORMAL)
        self.sr.shipsContainer.Flush()
        shipsContainer = invCont.StationShips(name='stationShips', parent=self.sr.shipsContainer, showControls=True, state=uiconst.UI_NORMAL)
        self.invButton.OnDropData = itemsContainer.OnDropData
        self.sr.itemsContainer.OnDropData = itemsContainer.OnDropData
        self.sr.shipsContainer.OnDropData = shipsContainer.OnDropData

    def OnProcessStationServiceItemChange(self, stationID, solarSystemID, serviceID, stationServiceItemID, isEnabled):
        if self.destroyed or stationID != eve.session.stationid:
            return
        for icon in self.serviceButtons.children:
            if hasattr(icon, 'stationServiceIDs') and serviceID in icon.stationServiceIDs:
                self.SetServiceButtonState(icon, [serviceID])

    def OnAgentMissionChange(self, actionID, agentID, tutorialID = None):
        """
        When a mission is declined or completed, that might change which agents
        are available, so update that portion of the lobby if it is displayed.
        """
        if self.selectedGroupButtonID == AGENTSPANEL:
            self.ShowAgents()

    def OnCorporationChanged(self, corpID, change):
        blue.pyos.synchro.Yield()
        self.LoadButtons()

    def OnStandingSet(self, fromID, toID, rank):
        """
        Notification that a standing has been set directly (probably from the
        debug admin window).  Might need to update agent availability.
        """
        if self.selectedGroupButtonID == AGENTSPANEL:
            self.ShowAgents()

    def SetServiceButtonState(self, button, serviceIDs):
        for serviceID in serviceIDs:
            currentstate = sm.GetService('station').GetServiceState(serviceID)
            if currentstate is not None:
                if self.sr.serviceAccessCache.has_key(serviceID):
                    del self.sr.serviceAccessCache[serviceID]
                if not currentstate.isEnabled:
                    button.Disable()
                    button.serviceStatus = localization.GetByLabel('UI/Station/Lobby/Disabled')
                    button.serviceEnabled = False
                else:
                    button.Enable()
                    button.serviceStatus = localization.GetByLabel('UI/Station/Lobby/Enabled')
                    button.serviceEnabled = True

    def LoadServiceButtons(self):
        parent = self.serviceButtons
        parent.Flush()
        services = sm.GetService('station').GetStationServiceInfo()
        serviceMask = eve.stationItem.serviceMask
        icon = None
        stationservicebtns = settings.user.ui.Get('stationservicebtns', 1)
        btnsize = BIGBUTTONSIZE
        if stationservicebtns:
            btnsize = SMALLBUTTONSIZE
        haveServices = []
        for service in services:
            hasStationService = False
            combinedServiceMask = sum(service.serviceIDs)
            if serviceMask & combinedServiceMask > 0:
                hasStationService = True
                if service.name == 'navyoffices':
                    if not sm.GetService('facwar').CheckStationElegibleForMilitia():
                        hasStationService = False
                elif service.name == 'securityoffice':
                    if not sm.GetService('securityOfficeSvc').CanAccessServiceInStation(session.stationid2):
                        hasStationService = False
            if hasStationService or -1 in service.serviceIDs:
                haveServices.append(service)

        for service in reversed(haveServices):
            button = BigButton(parent=parent, width=btnsize, height=btnsize, name=service.name, align=uiconst.NOALIGN)
            button.Startup(btnsize, btnsize, iconOpacity=0.75)
            button.cmdStr = service.command
            button.stationServiceIDs = service.serviceIDs
            button.displayName = service.label
            button.OnClick = (self.OnSvcBtnClick, button)
            button.serviceStatus = localization.GetByLabel('UI/Station/Lobby/Enabled')
            button.serviceEnabled = True
            if hasattr(service, 'iconID'):
                button.SetTexturePath(service.iconID)
            else:
                button.SetTexturePath(service.texturePath)
            self.SetServiceButtonState(button, service.serviceIDs)
            button.LoadTooltipPanel = self.LoadServiceButtonTooltipPanel

    def LoadServiceButtonTooltipPanel(self, tooltipPanel, tooltipOwner, *args):
        tooltipPanel.LoadGeneric3ColumnTemplate()
        command = uicore.cmd.commandMap.GetCommandByName(tooltipOwner.cmdStr)
        tooltipPanel.AddCommandTooltip(command)
        if not tooltipOwner.serviceEnabled:
            tooltipPanel.AddLabelMedium(text=localization.GetByLabel('UI/Station/Lobby/Disabled'), color=(1, 0, 0, 1), bold=True, colSpan=tooltipPanel.columns)

    def OnSvcBtnClick(self, btn, *args):
        self.CheckCanAccessService(btn.name)
        sm.GetService('station').LoadSvc(btn.name)

    def CheckCanAccessService(self, serviceName):
        services = sm.GetService('station').GetStationServiceInfo()
        for service in services:
            if service.name == serviceName:
                corpStationMgr = None
                now = blue.os.GetWallclockTime()
                for stationServiceID in service.serviceIDs:
                    doCheck = 1
                    time, result = (None, None)
                    if self.sr.serviceAccessCache.has_key(stationServiceID):
                        time, result = self.sr.serviceAccessCache[stationServiceID]
                        if time + const.MIN * 5 > now:
                            doCheck = 0
                    if doCheck:
                        if corpStationMgr is None:
                            corpStationMgr = sm.GetService('corp').GetCorpStationManager()
                        try:
                            corpStationMgr.DoStandingCheckForStationService(stationServiceID)
                            self.sr.serviceAccessCache[stationServiceID] = (now, None)
                        except Exception as e:
                            self.sr.serviceAccessCache[stationServiceID] = (now, e)
                            sys.exc_clear()

                    time, result = self.sr.serviceAccessCache[stationServiceID]
                    if result is not None:
                        raise result

    def LoadButtons(self):
        if self.destroyed:
            return
        btns = []
        officeExists = sm.GetService('corp').GetOffice() is not None
        canRent = session.corprole & const.corpRoleCanRentOffice == const.corpRoleCanRentOffice
        canMove = session.corprole & const.corpRoleDirector == const.corpRoleDirector
        if canRent and not officeExists:
            rentLabel = localization.GetByLabel('UI/Station/Lobby/RentOffice')
            btns.append([rentLabel, self.RentOffice, None])
        if canMove and officeExists:
            btns.append([localization.GetByLabel('UI/Station/Hangar/UnrentOffice'), self.UnrentOffice, None])
        if canMove:
            isHQHere = sm.GetService('corp').GetCorporation().stationID == session.stationid2
            if not isHQHere:
                hqLabel = localization.GetByLabel('UI/Station/Lobby/MoveHeadquartersHere')
                btns.append([hqLabel, self.SetHQ, None])
            if not officeExists and sm.GetService('corp').HasCorpImpoundedItemsAtStation():
                btns.append([localization.GetByLabel('UI/Inventory/ReleaseItems'), self.ReleaseImpoundedItems, None])
        if sm.GetService('corp').DoesCharactersCorpOwnThisStation():
            mgmtLabel = localization.GetByLabel('UI/Station/Lobby/StationManagement')
            btns.append([mgmtLabel, self.OpenStationManagement, None])
        if self.destroyed:
            return
        self.officesButtons.Flush()
        for label, func, args in btns:
            Button(parent=self.officesButtons, label=label, func=func, args=args, align=uiconst.NOALIGN)

    def ReleaseImpoundedItems(self, *args):
        corpStationMgr = sm.GetService('corp').GetCorpStationManager()
        cost = corpStationMgr.GetQuoteForGettingCorpJunkBack()
        if eve.Message('CrpJunkAcceptCost', {'cost': FmtAmt(cost)}, uiconst.YESNO) != uiconst.ID_YES:
            return
        corpStationMgr.PayForReturnOfCorpJunk(cost)
        sm.GetService('corp').hasImpoundedItemsCacheTime = None
        self.LoadButtons()

    def UnrentOffice(self, *args):
        items = invCtrl.StationCorpHangar(divisionID=None).GetItems()
        asked = False
        if len([ item for item in items if item.ownerID == session.corpid ]):
            asked = True
            if eve.Message('crpUnrentOfficeWithContent', {}, uiconst.YESNO) != uiconst.ID_YES:
                return
        if not asked:
            if eve.Message('crpUnrentOffice', {}, uiconst.YESNO) != uiconst.ID_YES:
                return
        corpStationMgr = sm.GetService('corp').GetCorpStationManager()
        sm.GetService('corp').hasImpoundedItemsCacheTime = None
        corpStationMgr.CancelRentOfOffice()

    def OpenStationManagement(self, *args):
        uthread.new(uicore.cmd.OpenStationManagement)

    def LoadOwnerInfo(self):
        parent = self.corpLogoParent
        parent.Flush()
        corpID = eve.stationItem.ownerID
        size = 128 if CheckCorpID(corpID) else 64
        logo = GetLogoIcon(itemID=corpID, parent=parent, acceptNone=False, state=uiconst.UI_DISABLED, pos=(0,
         8,
         size,
         size), align=uiconst.CENTERTOP)
        InfoIcon(typeID=const.typeCorporation, itemID=corpID, left=const.defaultPadding, top=20, align=uiconst.TOPRIGHT, parent=parent, idx=0)
        self.corpLogoParent.height = logo.top + logo.height
        if not CheckCorpID(corpID):
            self.corpName.text = '<center>' + cfg.eveowners.Get(corpID).name
            self.corpName.display = True
        else:
            self.corpName.display = False

    def ImVisible(self):
        return bool(self.state != uiconst.UI_HIDDEN and not self.IsCollapsed() and not self.IsMinimized())

    def Load(self, key):
        pass

    @telemetry.ZONE_METHOD
    def OnCharNowInStation(self, rec):
        if self.destroyed or not session.stationid2:
            return
        self.UpdateGuestTabText()
        if self.selectedGroupButtonID == GUESTSPANEL:
            charID, corpID, allianceID, warFactionID = rec
            cfg.eveowners.Prime([charID])
            if self.destroyed:
                return
            newcharinfo = cfg.eveowners.Get(charID)
            idx = 0
            for each in self.guestScroll.GetNodes():
                if each.charID == charID:
                    return
                if CaseFoldCompare(each.info.name, newcharinfo.name) > 0:
                    break
                idx += 1

            filteredGuest = None
            guestFilter = self.quickFilter.GetValue()
            if len(guestFilter):
                filteredGuest = NiceFilter(self.quickFilter.QuickFilter, newcharinfo.name)
            if filteredGuest or len(guestFilter) == 0:
                entry = GetListEntry(self.userEntry, {'charID': charID,
                 'info': newcharinfo,
                 'label': newcharinfo.name,
                 'corpID': corpID,
                 'allianceID': allianceID,
                 'warFactionID': warFactionID})
                self.guestScroll.AddNodes(idx, [entry])

    @telemetry.ZONE_METHOD
    def OnCharNoLongerInStation(self, rec):
        if self.destroyed or not session.stationid2:
            return
        self.UpdateGuestTabText()
        charID, corpID, allianceID, warFactionID = rec
        if self.selectedGroupButtonID == GUESTSPANEL:
            for entry in self.guestScroll.GetNodes():
                if entry.charID == charID:
                    self.guestScroll.RemoveNodes([entry])
                    return

    def ShowGuests(self, condensed = None, *args):
        if self.selectedGroupButtonID != GUESTSPANEL:
            return
        if condensed is not None:
            settings.user.ui.Set('guestCondensedUserList', condensed)
        self.SetGuestEntryType()
        guests = sm.GetService('station').GetGuests()
        owners = []
        for charID in guests.keys():
            if charID not in owners:
                owners.append(charID)

        cfg.eveowners.Prime(owners)
        guestsNames = [ KeyVal(name=cfg.eveowners.Get(charID).name, charID=charID) for charID in guests ]
        guestFilter = self.quickFilter.GetValue()
        if len(guestFilter):
            guestsNames = NiceFilter(self.quickFilter.QuickFilter, guestsNames)
        if self.destroyed:
            return
        scrolllist = []
        for guest in guestsNames:
            charID = guest.charID
            corpID, allianceID, warFactionID = guests[charID]
            charinfo = cfg.eveowners.Get(charID)
            scrolllist.append((charinfo.name.lower(), GetListEntry(self.userEntry, {'charID': charID,
              'info': charinfo,
              'label': charinfo.name,
              'corpID': corpID,
              'allianceID': allianceID,
              'warFactionID': warFactionID})))

        scrolllist = SortListOfTuples(scrolllist)
        self.guestScroll.Clear()
        self.guestScroll.AddNodes(0, scrolllist)
        self.UpdateGuestTabText()

    def UpdateGuestTabText(self):
        numGuests = len(sm.GetService('station').GetGuests())
        self.guestsButton.counter.text = numGuests

    def SetGuestEntryType(self):
        if settings.user.ui.Get('guestCondensedUserList', False):
            self.userEntry = 'ChatUserSimple'
        else:
            self.userEntry = 'User'

    def ShowAgents(self):
        try:
            agentsSvc = sm.GetService('agents')
            journalSvc = sm.GetService('journal')
            facWarSvc = sm.StartService('facwar')
            standingSvc = sm.StartService('standing')
            epicArcStatusSvc = sm.RemoteSvc('epicArcStatus')
            if self.selectedGroupButtonID != AGENTSPANEL:
                return
            agentMissions = journalSvc.GetMyAgentJournalDetails()[:1][0]
            agentsInStation = agentsSvc.GetAgentsByStationID()[session.stationid2]
            relevantAgents = []
            missionStateDict = {}
            for each in agentMissions:
                missionState, importantMission, missionType, missionName, agentID, expirationTime, bookmarks, remoteOfferable, remoteCompletable, contentID = each
                agent = agentsSvc.GetAgentByID(agentID)
                missionStateDict[agentID] = missionState
                if missionState not in (const.agentMissionStateAllocated, const.agentMissionStateOffered) or agent.agentTypeID in (const.agentTypeGenericStorylineMissionAgent,
                 const.agentTypeStorylineMissionAgent,
                 const.agentTypeEventMissionAgent,
                 const.agentTypeCareerAgent,
                 const.agentTypeEpicArcAgent):
                    relevantAgents.append(agentID)

            localRelevantAgents = []
            for agent in agentsInStation:
                if agent.agentID in relevantAgents:
                    localRelevantAgents.append(agent.agentID)

            if self.destroyed:
                return
            scrolllist = []
            sortlist = []
            for agentID in relevantAgents:
                if not eve.rookieState or agentID in const.rookieAgentList:
                    if agentID not in localRelevantAgents:
                        missionState = missionStateDict.get(agentID)
                        sortlist.append((cfg.eveowners.Get(agentID).name, GetListEntry('AgentEntry', {'charID': agentID,
                          'missionState': missionState})))

            if sortlist:
                agentLabel = localization.GetByLabel('UI/Station/Lobby/AgentsOfInterest')
                scrolllist.append(GetListEntry('Header', {'label': agentLabel}))
                scrolllist += SortListOfTuples(sortlist)
            unavailableAgents = []
            availableAgents = []
            for agent in agentsInStation:
                if agent.agentID in const.rookieAgentList:
                    continue
                if not eve.rookieState or agent.agentID in const.rookieAgentList:
                    isLimitedToFacWar = False
                    if agent.agentTypeID == const.agentTypeFactionalWarfareAgent and facWarSvc.GetCorporationWarFactionID(agent.corporationID) != session.warfactionid:
                        isLimitedToFacWar = True
                    if agent.agentTypeID in (const.agentTypeResearchAgent,
                     const.agentTypeBasicAgent,
                     const.agentTypeEventMissionAgent,
                     const.agentTypeCareerAgent,
                     const.agentTypeFactionalWarfareAgent):
                        standingIsValid = standingSvc.CanUseAgent(agent.factionID, agent.corporationID, agent.agentID, agent.level, agent.agentTypeID)
                        haveMissionFromAgent = agent.agentID in relevantAgents
                        if not isLimitedToFacWar and (standingIsValid or haveMissionFromAgent):
                            availableAgents.append(agent.agentID)
                        else:
                            unavailableAgents.append(agent.agentID)
                    elif agent.agentTypeID == const.agentTypeEpicArcAgent:
                        standingIsValid = standingSvc.CanUseAgent(agent.factionID, agent.corporationID, agent.agentID, agent.level, agent.agentTypeID)
                        haveMissionFromAgent = agent.agentID in relevantAgents
                        epicAgentAvailable = False
                        if haveMissionFromAgent:
                            epicAgentAvailable = True
                        elif standingIsValid:
                            if agent.agentID in relevantAgents or epicArcStatusSvc.AgentHasEpicMissionsForCharacter(agent.agentID):
                                epicAgentAvailable = True
                        if epicAgentAvailable:
                            availableAgents.append(agent.agentID)
                        else:
                            unavailableAgents.append(agent.agentID)
                    if agent.agentTypeID == const.agentTypeAura:
                        if sm.GetService('experimentClientSvc').IsTutorialEnabled():
                            availableAgents.append(agent.agentID)
                    elif agent.agentTypeID in (const.agentTypeGenericStorylineMissionAgent, const.agentTypeStorylineMissionAgent):
                        if agent.agentID in localRelevantAgents:
                            availableAgents.append(agent.agentID)
                        else:
                            unavailableAgents.append(agent.agentID)

            if availableAgents:
                availableLabel = localization.GetByLabel('UI/Station/Lobby/AvailableToYou')
                scrolllist.append(GetListEntry('Header', {'label': availableLabel}))
                sortlist = []
                for agentID in availableAgents:
                    missionState = missionStateDict.get(agentID)
                    sortlist.append((cfg.eveowners.Get(agentID).name, GetListEntry('AgentEntry', {'charID': agentID,
                      'missionState': missionState})))

                scrolllist += SortListOfTuples(sortlist)
            if unavailableAgents:
                unavailableLabel = localization.GetByLabel('UI/Station/Lobby/NotAvailableToYou')
                scrolllist.append(GetListEntry('Header', {'label': unavailableLabel}))
                sortlist = []
                for agentID in unavailableAgents:
                    missionState = missionStateDict.get(agentID)
                    sortlist.append((cfg.eveowners.Get(agentID).name, GetListEntry('AgentEntry', {'charID': agentID,
                      'missionState': missionState})))

                scrolllist += SortListOfTuples(sortlist)
            if self.destroyed:
                return
            self.agentScroll.Load(fixedEntryHeight=40, contentList=scrolllist)
        except:
            log.LogException()
            sys.exc_clear()

    def InteractWithAgent(self, agentID, *args):
        sm.StartService('agents').InteractWith(agentID)

    def SetHQ(self, *args):
        if sm.GetService('godma').GetType(eve.stationItem.stationTypeID).isPlayerOwnable == 1:
            raise UserError('CanNotSetHQAtPlayerOwnedStation')
        if eve.Message('MoveHQHere', {}, uiconst.YESNO) == uiconst.ID_YES:
            sm.GetService('corp').GetCorpStationManager().MoveCorpHQHere()

    def RentOffice(self, *args):
        if not self.sr.Get('isRentOfficeOpening') or not self.sr.isRentOfficeOpening:
            self.sr.isRentOfficeOpening = 1
            try:
                cost = sm.GetService('corp').GetCorpStationManager().GetQuoteForRentingAnOffice()
                if eve.Message('AskPayOfficeRentalFee', {'cost': cost,
                 'duration': const.rentalPeriodOffice * const.DAY}, uiconst.YESNO) == uiconst.ID_YES:
                    officeID = sm.GetService('corp').GetCorpStationManager().RentOffice(cost)
                    if officeID:
                        office = sm.GetService('corp').GetOffice()
                        invCache = sm.GetService('invCache')
                        invCache.InvalidateLocationCache(officeID)
                        if office is not None:
                            folder = invCache.GetInventoryFromId(office.officeFolderID, locationID=session.stationid2)
                            folder.List()
                            wnd = InventoryWindow.GetIfOpen()
                            if not wnd:
                                InventoryWindow.OpenOrShow()
                uthread.new(self.LoadButtons)
                if self.selectedGroupButtonID == OFFICESPANEL:
                    self.ShowOffices()
            finally:
                self.sr.isRentOfficeOpening = 0

    def ShowShips(self):
        if self.sr.shipsContainer is None:
            return
        self.mainButtonGroup.SelectByID(INVENTORYPANEL)
        self.inventoryTabs.ShowPanel(self.sr.shipsContainer)

    def ShowItems(self):
        if self.sr.itemsContainer is None:
            return
        self.mainButtonGroup.SelectByID(INVENTORYPANEL)
        self.inventoryTabs.ShowPanel(self.sr.itemsContainer)

    def ReloadOfficesIfVisible(self):
        if self.selectedGroupButtonID == OFFICESPANEL:
            self.ShowOffices()

    def ShowOffices(self):
        if self.selectedGroupButtonID != OFFICESPANEL:
            return
        self.LoadButtons()
        corpsWithOffices = sm.GetService('corp').GetCorporationsWithOfficesAtStation()
        cfg.corptickernames.Prime([ c.corporationID for c in corpsWithOffices ])
        scrolllist = []
        for corp in corpsWithOffices:
            data = KeyVal()
            data.corpName = corp.corporationName
            data.corpID = corp.corporationID
            data.corporation = corp
            scrolllist.append((data.corpName.lower(), GetListEntry('OfficeEntry', data=data)))

        scrolllist = SortListOfTuples(scrolllist)
        numUnrentedOffices = self.GetNumberOfUnrentedOffices()
        availOfficesLabel = localization.GetByLabel('UI/Station/Lobby/NumAvailableOffices', numOffices=numUnrentedOffices)
        scrolllist.insert(0, GetListEntry('Header', {'label': availOfficesLabel}))
        if not self.destroyed:
            self.officesScroll.Load(contentList=scrolllist)

    def GetNumberOfUnrentedOffices(self):
        return sm.GetService('corp').GetCorpStationManager().GetNumberOfUnrentedOffices()

    def OnCorporationMemberChanged(self, corporationID, memberID, change):
        if memberID == session.charid:
            self.LoadButtons()

    def StopAllBlinkButtons(self):
        for each in self.serviceButtons.children:
            if hasattr(each, 'Blink'):
                each.Blink(0)

    def BlinkButton(self, whatBtn):
        for each in self.serviceButtons.children:
            if each.name.lower() == whatBtn.lower():
                each.Blink(blinks=40)


class OfficeEntry(SE_BaseClassCore):
    __guid__ = 'listentry.OfficeEntry'

    def Startup(self, *args):
        self.Flush()
        main = Container(parent=self, align=uiconst.TOTOP, height=30, state=uiconst.UI_PICKCHILDREN)
        left = Container(parent=main, align=uiconst.TOLEFT, width=50, state=uiconst.UI_PICKCHILDREN)
        icon = Container(parent=left, align=uiconst.TOPLEFT, width=32, height=32, left=3, top=3, state=uiconst.UI_PICKCHILDREN)
        par = Container(parent=main, align=uiconst.TOTOP, height=17, state=uiconst.UI_PICKCHILDREN)
        label = localization.GetByLabel('UI/Station/Lobby/CorpName')
        fieldName = 'corpName'
        l = EveLabelSmall(text=label, parent=par, left=5, top=2, state=uiconst.UI_DISABLED)
        t = EveLabelMedium(text='', parent=par, left=5, state=uiconst.UI_NORMAL)
        setattr(self.sr, fieldName + '_Label', l)
        setattr(self.sr, fieldName + '_Text', t)
        setattr(self.sr, fieldName, par)
        LineThemeColored(parent=self, align=uiconst.TOBOTTOM)
        self.sr.buttonCnt = Container(parent=self, align=uiconst.TOTOP, height=25, state=uiconst.UI_HIDDEN)
        self.sr.icon = icon
        self.sr.main = main
        self.sr.infoicon = InfoIcon(left=32, top=3, parent=left, idx=0)

    def Load(self, node):
        self.sr.node = node
        data = node
        self.sr.infoicon.UpdateInfoLink(const.typeCorporation, data.corpID)
        mainHeight = 0
        fieldName = 'corpName'
        infofield = self.sr.Get(fieldName, None)
        fieldText = self.sr.Get(fieldName + '_Text', None)
        fieldLabel = self.sr.Get(fieldName + '_Label', None)
        fieldText.text = data.Get(fieldName, '')
        fieldText.top = fieldLabel.textheight
        infofield.height = fieldText.top + fieldText.textheight + 2
        if infofield.state != uiconst.UI_HIDDEN:
            mainHeight += infofield.height
        self.sr.main.height = mainHeight + 10
        self.sr.icon.Flush()

        def LogoThread():
            if not self.destroyed:
                GetLogoIcon(itemID=data.corpID, parent=self.sr.icon, acceptNone=False, align=uiconst.TOALL)

        uthread.new(LogoThread)
        self.sr.buttonCnt.Flush()
        if not IsNPC(node.corpID):
            buttonEntries = []
            if eve.session.corpid != node.corpID:
                if sm.GetService('corp').GetActiveApplication(node.corpID) is not None:
                    applyLabel = localization.GetByLabel('UI/Corporations/CorpApplications/ViewApplication')
                else:
                    applyLabel = localization.GetByLabel('UI/Corporations/CorporationWindow/Alliances/Rankings/ApplyToJoin')
                buttonEntries.append((applyLabel,
                 sm.GetService('corp').ApplyForMembership,
                 (node.corpID,),
                 80))
            if len(buttonEntries) > 0:
                self.sr.buttonCnt.state = uiconst.UI_PICKCHILDREN
                self.sr.buttons = ButtonGroup(btns=buttonEntries, parent=self.sr.buttonCnt, unisize=0, line=0)
                self.sr.buttons.top -= 1
            else:
                self.sr.buttonCnt.state = uiconst.UI_PICKCHILDREN
        else:
            self.sr.buttonCnt.state = uiconst.UI_HIDDEN

    def GetHeight(self, *args):
        node, width = args
        height = 2
        lw, lh = EveLabelSmall.MeasureTextSize(text=localization.GetByLabel('UI/Station/Lobby/CorpName'))
        tw, th = EveLabelMedium.MeasureTextSize(text=node.corpName)
        multiplier = 1
        height += (lh + th + 15) * multiplier
        height += 5
        if not IsNPC(node.corpID) and eve.session.corpid != node.corpID:
            height += 30
        node.height = height
        return node.height
