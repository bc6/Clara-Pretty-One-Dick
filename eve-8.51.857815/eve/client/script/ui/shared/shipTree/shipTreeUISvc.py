#Embedded file name: eve/client/script/ui/shared/shipTree\shipTreeUISvc.py
import service
from eve.client.script.ui.shared.shipTree.infoBubble import InfoBubbleShip, InfoBubbleShipGroup
from eve.client.script.ui.station.lobby import Lobby
import carbonui.util.various_unsorted as uiutil
import blue
import uthread
import shipTreeConst
from eve.client.script.ui.control.historyBuffer import HistoryBuffer

class ShipTreeUI(service.Service):
    """
    Takes care of all visualization components of the ship tree, both 3d and UI
    """
    __guid__ = 'svc.shipTreeUI'
    __servicename__ = 'Ship tree UI service'
    __displayname__ = 'Ship tree UI service'
    __notifyevents__ = ('OnSkillLevelChanged', 'OnSkillStarted', 'OnSkillQueueRefreshed')
    __dependencies__ = []

    def Run(self, *args):
        self.selectedFaction = None
        self.infoBubble = None
        self.infoBubbleUIObj = None
        self.infoBubbleCloseThread = None
        self._isSelectingFaction = False
        self.showInfoBubbleThread = None

    def OpenAndShowShip(self, typeID):
        """ Open up the ship tree focused on certain ship defined by typeID """
        shipType = cfg.fsdTypeOverrides.Get(typeID)
        factionID = shipType.factionID
        shipGroupID = shipType.isisGroupID
        settings.char.ui.Set('shipTreeSelectedFaction', factionID)
        vsSvc = sm.GetService('viewState')
        animate = True
        if not vsSvc.IsViewActive('shiptree'):
            animate = False
            vsSvc.ToggleSecondaryView('shiptree')
        if factionID != self.selectedFaction:
            animate = False
        self.SelectFaction(factionID)
        uicore.layer.shiptree.PanToShipGroup(shipGroupID, animate=animate)
        sm.ScatterEvent('OnShipTreeShipFocused', typeID)

    def OpenAndShowShipGroup(self, factionID, shipGroupID):
        settings.char.ui.Set('shipTreeSelectedFaction', factionID)
        vsSvc = sm.GetService('viewState')
        animate = True
        if not vsSvc.IsViewActive('shiptree'):
            animate = False
            vsSvc.ToggleSecondaryView('shiptree')
        if factionID != self.selectedFaction:
            animate = False
        self.SelectFaction(factionID)
        uicore.layer.shiptree.PanToShipGroup(shipGroupID, animate=animate)
        sm.ScatterEvent('OnShipTreeShipGroupFocused', factionID, shipGroupID)

    def OnShipTreeOpened(self):
        self.history = HistoryBuffer()
        sm.GetService('skills').MySkills(renew=True)
        self.SelectFaction(self.GetDefaultFactionID())
        lobbyWnd = Lobby.GetIfOpen()
        if lobbyWnd:
            lobbyWnd.Minimize(animate=False)
        sm.GetService('audio').SendUIEvent('isis_start')

    def GetDefaultFactionID(self):
        default = sm.GetService('facwar').GetFactionIDByRaceID(session.raceID)
        return settings.char.ui.Get('shipTreeSelectedFaction', default)

    def OnShipTreeClosed(self):
        self.factionTreesByFactionID = {}
        self.selectedFaction = None
        sm.GetService('audio').SendUIEvent('isis_end')
        lobbyWnd = Lobby.GetIfOpen()
        if lobbyWnd:
            lobbyWnd.Maximize(animate=False)

    def GetEntityByID(self, factionID = None, shipGroupID = None, typeID = None):
        if typeID:
            return self.GetFactionTree(factionID).GetShipGroup(shipGroupID).GetShip(typeID)
        elif shipGroupID:
            return self.GetFactionTree(factionID).GetShipGroup(shipGroupID)
        else:
            return self.GetFactionTree(factionID)

    def GetFactionTree(self, factionID):
        return self.factionTreesByFactionID[factionID]

    def GetSelectedFaction(self):
        return self.selectedFaction or self.GetDefaultFactionID()

    def SelectFaction(self, factionID, appendHistory = True, doLog = False):
        if self.selectedFaction == factionID:
            return
        if self._isSelectingFaction:
            return
        self._isSelectingFaction = True
        try:
            oldFactionID = self.selectedFaction
            self.selectedFaction = factionID
            sm.ScatterEvent('OnBeforeShipTreeFactionSelected', factionID)
            uicore.layer.shiptree.SelectFaction(factionID, oldFactionID)
            settings.char.ui.Set('shipTreeSelectedFaction', factionID)
            sm.ScatterEvent('OnShipTreeFactionSelected', factionID)
            eventID = shipTreeConst.GetAudioEventIDForFaction(factionID)
            sm.GetService('audio').SendUIEvent(eventID)
            if appendHistory:
                self.history.Append(factionID)
            uicore.registry.SetFocus(uicore.layer.shiptree)
        finally:
            self._isSelectingFaction = False

        if doLog:
            sm.GetService('shipTree').LogIGS('FactionSwitch')

    def IsGroupLocked(self, factionID, shipGroupID):
        group = self.GetEntityByID(factionID, shipGroupID)
        return group.data.IsLocked()

    def ShowInfoBubble(self, uiObj, factionID = None, node = None, typeID = None):
        if uicore.layer.shiptree.isZooming:
            return
        if uiObj == self.infoBubbleUIObj:
            return
        if self.showInfoBubbleThread:
            self.showInfoBubbleThread.kill()
        self.showInfoBubbleThread = uthread.new(self._ShowInfoBubble, uiObj, factionID, node, typeID)

    def _ShowInfoBubble(self, uiObj, factionID = None, node = None, typeID = None):
        blue.synchro.SleepWallclock(150)
        mo = uicore.uilib.mouseOver
        if mo == self.infoBubble or uiutil.IsUnder(mo, self.infoBubble):
            return
        if uicore.layer.menu.children:
            return
        if self.infoBubble:
            self.CloseInfoBubble()
        self.infoBubbleUIObj = uiObj
        if self.ShouldInfoBubbleClose():
            self.CloseInfoBubble()
            return
        if node:
            self.infoBubble = InfoBubbleShipGroup(factionID=factionID, node=node, parent=uicore.layer.infoBubble, parentObj=uiObj)
        else:
            self.infoBubble = InfoBubbleShip(factionID=factionID, typeID=typeID, parent=uicore.layer.infoBubble, parentObj=uiObj)
        self.infoBubbleCloseThread = uthread.new(self.InfoBubbleCloseThread)
        self.showInfoBubbleThread = None

    def InfoBubbleCloseThread(self, *args):
        while not self.ShouldInfoBubbleClose():
            blue.synchro.Sleep(500)

        self.CloseInfoBubble()

    def ShouldInfoBubbleClose(self):
        if uicore.layer.shiptree.isZooming:
            return True
        mo = uicore.uilib.mouseOver
        if mo == self.infoBubbleUIObj or uiutil.IsUnder(mo, self.infoBubbleUIObj):
            return False
        if mo == self.infoBubble or uiutil.IsUnder(mo, self.infoBubble):
            return False
        if uicore.layer.menu.children:
            return False
        return True

    def CloseInfoBubble(self):
        if self.infoBubble:
            self.infoBubble.Close()
        self.infoBubble = None
        self.infoBubbleUIObj = None
        if self.infoBubbleCloseThread:
            self.infoBubbleCloseThread.kill()
            self.infoBubbleCloseThread = None

    def GetZoomLevel(self):
        return uicore.layer.shiptree.zoomLevel

    def PanTo(self, x, y, animate = True):
        uicore.layer.shiptree.PanToPropCoords(x, y, animate)

    def GoBack(self):
        factionID = self.history.GoBack()
        if factionID:
            self.SelectFaction(factionID, appendHistory=False)

    def GoForward(self):
        factionID = self.history.GoForward()
        if factionID:
            self.SelectFaction(factionID, appendHistory=False)

    def OnSkillStarted(self, *args):
        self._UpdateActiveTreeSkills()

    def OnSkillLevelChanged(self, *args):
        sm.GetService('shipTree').FlushRecentlyChangedSkillsCache()
        self._UpdateActiveTreeSkills()

    def OnSkillQueueRefreshed(self):
        self._UpdateActiveTreeSkills()

    def _UpdateActiveTreeSkills(self):
        if sm.GetService('viewState').IsViewActive('shiptree'):
            uicore.layer.shiptree.shipTreeCont.UpdateTreeSkills()
            sm.ScatterEvent('OnShipTreeSkillTrained')
