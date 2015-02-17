#Embedded file name: eve/client/script/ui/shared/infoPanels\infoPanelSvc.py
from eve.client.script.ui.shared.infoPanels.infoPanelAchievements import InfoPanelAchievements
from eveexceptions.exceptionEater import ExceptionEater
import service
import uicls
import carbonui.const as uiconst
import uiprimitives
import uthread
import blue
import uiutil
import util
import localization
import crimewatchTimers
import log
import telemetry
import const
from eve.client.script.ui.view.viewStateConst import ViewState
from infoPanelConst import PANEL_LOCATION_INFO, PANEL_ROUTE, PANEL_MISSIONS, PANEL_INCURSIONS, PANEL_FACTIONAL_WARFARE, PANEL_PLANETARY_INTERACTION, PANEL_SHIP_TREE, PANEL_ACHIEVEMENTS
import infoPanelConst
from infoPanelShipTree import InfoPanelShipTree
from infoPanelLocationInfo import InfoPanelLocationInfo
from infoPanelRoute import InfoPanelRoute
from infoPanelIncursions import InfoPanelIncursions
from infoPanelMissions import InfoPanelMissions
from infoPanelFactionalWarfare import InfoPanelFactionalWarfare
from infoPanelPlanetaryInteraction import InfoPanelPlanetaryInteraction
from eve.client.script.ui.shared.infoPanels.infoPanelContainer import InfoPanelContainer
from collections import defaultdict

class InfoPanelSvc(service.Service):
    """
    Takes care of constructing and updating the left-hand side info panels such as location info, agent missions, etc.
    """
    __update_on_reload__ = 1
    __guid__ = 'svc.infoPanel'
    __notifyevents__ = ['OnSessionChanged',
     'OnViewStateChanged',
     'OnAgentMissionChange',
     'OnSovereigntyChanged',
     'OnSystemStatusChanged',
     'OnEntitySelectionChanged',
     'OnPostCfgDataChanged',
     'OnMissionTrackerUpdate',
     'OnItemsChanged']

    def OnItemsChanged(self, items, change):
        shipHold = [const.flagCargo,
         const.flagSpecializedOreHold,
         const.flagSpecializedGasHold,
         const.flagSpecializedMineralHold,
         const.flagSpecializedSalvageHold,
         const.flagSpecializedShipHold,
         const.flagSpecializedSmallShipHold,
         const.flagSpecializedMediumShipHold,
         const.flagSpecializedLargeShipHold,
         const.flagSpecializedIndustrialShipHold]
        agentList = []
        for item in items:
            if item.flagID in shipHold and item.typeID in self.waitingForTypeIDs.keys():
                agentList += self.waitingForTypeIDs[item.typeID]

        if agentList:
            self.UpdateMissionStatusData(agentList)

    def NotifyTrackerWhenTypeIDArrives(self, agentID, typeID):
        self.agentsWaitingForStuff[agentID] = typeID
        if agentID not in self.waitingForTypeIDs[typeID]:
            self.waitingForTypeIDs[typeID].append(agentID)

    def StopNotifyingTrackerForTypeID(self, agentID):
        if not self.agentsWaitingForStuff.has_key(agentID):
            return
        typeID = self.agentsWaitingForStuff[agentID]
        if agentID in self.waitingForTypeIDs[typeID]:
            self.waitingForTypeIDs[typeID].remove(agentID)
            del self.agentsWaitingForStuff[agentID]

    def OnMissionTrackerUpdate(self, missionInfo):
        agentID = missionInfo['agentID']
        info = missionInfo['info']
        infoList = info.split(',')
        if infoList and 'MissionFetch' in infoList[0] or 'TransportItemsMissing' in infoList[0]:
            self.NotifyTrackerWhenTypeIDArrives(agentID, int(infoList[1]))
        else:
            self.StopNotifyingTrackerForTypeID(agentID)
        self.previousMissionInfo[agentID] = self.agentMissionInfo[agentID] if self.agentMissionInfo.has_key(agentID) else ''
        self.agentMissionInfo[agentID] = info
        self.UpdateMissionsPanel()

    def GetAgentMissionInfo(self, agentID):
        current = self.agentMissionInfo[agentID].split(',') if self.agentMissionInfo.has_key(agentID) else ['']
        previous = self.previousMissionInfo[agentID].split(',') if self.previousMissionInfo.has_key(agentID) else ['']
        return (current, previous)

    def Run(self, *args):
        self.missionTrackerMgr = sm.RemoteSvc('missionTrackerMgr')
        self.agentMissionInfo = {}
        self.agentList = []
        self.destinationTriggers = defaultdict(lambda : [])
        self.waitingForTypeIDs = defaultdict(lambda : [])
        self.agentsWaitingForStuff = {}
        self.previousMissionInfo = {}
        self.sidePanel = None
        self.infoPanelContainer = None
        self.sessionTimer = None
        self.sessionTimerUpdatePending = False

    def Reload(self):
        """ Reload info panels for development purposes """
        if self.sidePanel:
            self.sidePanel.Close()
        if self.sessionTimer:
            self.sessionTimer.Close()
        self.ConstructSidePanel()

    @telemetry.ZONE_FUNCTION
    def ConstructSidePanel(self):
        self.sidePanel = uiprimitives.Container(parent=uicore.layer.sidePanels, name='sidePanel', align=uiconst.TOLEFT, width=infoPanelConst.PANELWIDTH, padding=(0, 12, 0, 0))
        self.sidePanel.cacheContents = True
        self.combatTimerContainer = crimewatchTimers.TimerContainer(parent=self.sidePanel, left=infoPanelConst.LEFTPAD)
        self.infoPanelContainer = InfoPanelContainer(parent=self.sidePanel, align=uiconst.TOTOP)
        self.sessionTimer = uicls.SessionTimeIndicator(parent=self.sidePanel, pos=(16, 35, 24, 24), state=uiconst.UI_HIDDEN, align=uiconst.TOPLEFT)
        if self.sessionTimerUpdatePending:
            self.UpdateSessionTimer()
        self.RegisterMissionTracking()

    def UpdateSessionTimer(self):
        if self.sessionTimer:
            uthread.new(self.sessionTimer.AnimSessionChange)
            self.sessionTimerUpdatePending = False
        else:
            self.sessionTimerUpdatePending = True

    def ShowHideSidePanel(self, hide = 1, *args):
        if self.sidePanel is not None and not self.sidePanel.destroyed:
            if hide:
                self.sidePanel.state = uiconst.UI_HIDDEN
            else:
                self.sidePanel.state = uiconst.UI_PICKCHILDREN

    def GetCurrentPanelClasses(self):
        """ Get the UI classes representing all currently available panels """
        panelSettings = self.GetPanelModeSettings()
        ret = []
        for panel in panelSettings:
            cls = self.GetPanelClassByPanelTypeID(panel[0])
            if cls.IsAvailable():
                ret.append(cls)

        return ret

    def GetCurrentPanelTypes(self):
        """ Get panelTypeIDs for all currently available panels """
        return [ panel.panelTypeID for panel in self.GetCurrentPanelClasses() ]

    def GetPanelClassByPanelTypeID(self, panelTypeID):
        if panelTypeID == PANEL_LOCATION_INFO:
            return InfoPanelLocationInfo
        if panelTypeID == PANEL_ROUTE:
            return InfoPanelRoute
        if panelTypeID == PANEL_INCURSIONS:
            return InfoPanelIncursions
        if panelTypeID == PANEL_MISSIONS:
            return InfoPanelMissions
        if panelTypeID == PANEL_FACTIONAL_WARFARE:
            return InfoPanelFactionalWarfare
        if panelTypeID == PANEL_PLANETARY_INTERACTION:
            return InfoPanelPlanetaryInteraction
        if panelTypeID == PANEL_SHIP_TREE:
            return InfoPanelShipTree
        if panelTypeID == PANEL_ACHIEVEMENTS:
            return InfoPanelAchievements

    def GetModeForPanel(self, panelTypeID):
        settingsEntry = self.GetPanelSettingsEntryByTypeID(panelTypeID)
        if settingsEntry:
            return settingsEntry[1]
        cls = self.GetPanelClassByPanelTypeID(panelTypeID)
        return cls.default_mode

    def GetPanelSettingsEntryByTypeID(self, panelTypeID):
        panelSettings = self.GetPanelModeSettings()
        for settingsEntry in panelSettings:
            if settingsEntry[0] == panelTypeID:
                return settingsEntry

    def GetPanelModeSettings(self):
        """ 
        Returns a list of all panels and their modes for the current view state
        This list will include panels that are currently hidden 
        """
        panels = settings.char.ui.Get(self.GetCurrentPanelSettingsID(), self.GetCurrentDefaultPanelSettings())
        panels = [ panel for panel in panels if panel[0] in infoPanelConst.PANELTYPES ]
        panelTypeIDs = [ panel[0] for panel in panels ]
        for panelTypeID in infoPanelConst.PANELTYPES:
            if panelTypeID not in panelTypeIDs:
                cls = self.GetPanelClassByPanelTypeID(panelTypeID)
                panels.append([panelTypeID, cls.default_mode])

        return panels

    def SavePanelModeSetting(self, panelTypeID, mode):
        panelSettings = self.GetPanelModeSettings()
        panelSettingsEntry = self.GetPanelSettingsEntryByTypeID(panelTypeID)
        panelSettingsEntry[1] = mode
        settings.char.ui.Set(self.GetCurrentPanelSettingsID(), panelSettings)
        sm.ScatterEvent('OnInfoPanelSettingChanged', panelTypeID, mode)

    def GetCurrViewName(self):
        currViewName = sm.GetService('viewState').GetCurrentView().name
        if currViewName == ViewState.Station:
            currViewName = ViewState.Hangar
        return currViewName

    def GetCurrentPanelSettingsID(self):
        """ Get current panel settings ID depending on current view state """
        currViewName = self.GetCurrViewName()
        return 'InfoPanelModes_%s' % currViewName

    def GetCurrentDefaultPanelSettings(self):
        """ Returns a dict containing the default panel settings for the current view state """
        currViewName = self.GetCurrViewName()
        infoPanelSettings = infoPanelConst.PANEL_DEFAULT_SETTINGS.get(currViewName)
        if infoPanelSettings is None:
            log.LogWarn('InfoPanelSvc.GetCurrentDefaultPanelSettings: Unhandled viewstate: %s' % currViewName)
            infoPanelSettings = []
        return infoPanelSettings

    @telemetry.ZONE_FUNCTION
    def CheckAllPanelsFit(self, triggeredByPanel = None):
        if self.infoPanelContainer:
            uthread.new(self._CheckAllPanelsFit, triggeredByPanel)

    @telemetry.ZONE_FUNCTION
    def _CheckAllPanelsFit(self, triggeredByPanel = None):
        panels = self.GetPanelModeSettings()[:]
        panels.reverse()
        for mode in (infoPanelConst.MODE_COMPACT, infoPanelConst.MODE_COLLAPSED):
            for panelTypeID, panelMode in panels:
                if panelMode == infoPanelConst.MODE_COLLAPSED:
                    continue
                if not self.infoPanelContainer.IsLastPanelClipped():
                    return
                if panelTypeID == triggeredByPanel:
                    continue
                panel = self.GetPanelByTypeID(panelTypeID)
                if panel:
                    panel.SetMode(mode)

    @telemetry.ZONE_FUNCTION
    def MovePanelInFrontOf(self, infoPanelCls, oldTypeID = None):
        """ Move a panel to the position previously held by oldTypeID (appended if None) """
        panelSettings = self.GetPanelModeSettings()
        entry = self.GetPanelSettingsEntryByTypeID(infoPanelCls.panelTypeID)
        if oldTypeID:
            idx = panelSettings.index(self.GetPanelSettingsEntryByTypeID(oldTypeID))
        else:
            idx = -1
        oldIdx = panelSettings.index(self.GetPanelSettingsEntryByTypeID(infoPanelCls.panelTypeID))
        if idx > oldIdx:
            idx -= 1
        if oldIdx == idx:
            return
        panelSettings = self.GetPanelModeSettings()
        panelSettings.pop(oldIdx)
        panelSettings.insert(idx, entry)
        settings.char.ui.Set(self.GetCurrentPanelSettingsID(), panelSettings)
        self.ReconstructAllPanels(animate=True)

    def GetPanelByTypeID(self, panelTypeID):
        if self.infoPanelContainer:
            return self.infoPanelContainer.GetPanelByTypeID(panelTypeID)

    def GetPanelButtonByTypeID(self, panelTypeID):
        if self.infoPanelContainer:
            return self.infoPanelContainer.GetPanelButtonByTypeID(panelTypeID)

    def OnPanelContainerIconPressed(self, panelTypeID):
        panel = self.GetPanelByTypeID(panelTypeID)
        if panel:
            if panel.isInModeTransition:
                return
            if panel.mode == infoPanelConst.MODE_COLLAPSED:
                panel.SetMode(infoPanelConst.MODE_NORMAL)
            elif panel.isCollapsable:
                panel.SetMode(infoPanelConst.MODE_COLLAPSED)
            elif panel.mode == infoPanelConst.MODE_NORMAL:
                panel.SetMode(infoPanelConst.MODE_COMPACT)
            else:
                panel.SetMode(infoPanelConst.MODE_NORMAL)

    @telemetry.ZONE_FUNCTION
    def OnViewStateChanged(self, oldView, newView):
        if not session.charid:
            return
        if not self.sidePanel:
            self.ConstructSidePanel()
        else:
            self.ReconstructAllPanels(True)

    @telemetry.ZONE_FUNCTION
    def ReconstructAllPanels(self, animate = False):
        if not session.charid:
            return
        if not self.sidePanel:
            self.ConstructSidePanel()
        elif self.infoPanelContainer:
            self.infoPanelContainer.Reconstruct(animate)

    def UpdateAllPanels(self):
        if not session.charid or not self.sidePanel:
            return
        sm.ChainEvent('ProcessUpdateInfoPanel', None)

    def UpdateTopIcons(self):
        if self.infoPanelContainer:
            self.infoPanelContainer.ConstructTopIcons()

    def OnAgentMissionChange(self, what, agentID, tutorialID = None, *args):
        with ExceptionEater('exception during - missiontracker remove/add agent'):
            if what == 'quit':
                if agentID in self.agentList:
                    self.agentList.remove(agentID)
                    self.RemoveDestinationNotificationTrigger(agentID)
            if what == 'accepted':
                self.agentList.append(agentID)
                self.UpdateMissionStatusData((agentID,))
        self.UpdateMissionsPanel()

    @telemetry.ZONE_FUNCTION
    def OnSessionChanged(self, isRemote, sess, change):
        if not session.charid:
            return
        if change.has_key('locationid'):
            if change['locationid'][0] in self.destinationTriggers.keys():
                self.UpdateMissionStatusData(self.destinationTriggers[change['locationid'][0]])
            if change['locationid'][1] in self.destinationTriggers.keys():
                self.UpdateMissionStatusData(self.destinationTriggers[change['locationid'][1]])
        self.UpdateMissionsPanel()
        self.UpdateSessionTimer()
        self.UpdateFactionalWarfarePanel()
        self.UpdateLocationInfoPanel()

    def OnSovereigntyChanged(self, solarSystemID, allianceID):
        self.UpdateAllPanels()

    def OnSystemStatusChanged(self, *args):
        self.UpdateAllPanels()

    def OnEntitySelectionChanged(self, entityID):
        self.UpdateAllPanels()

    def OnPostCfgDataChanged(self, what, data):
        if what == 'evelocations':
            self.UpdateAllPanels()

    @telemetry.ZONE_FUNCTION
    def UpdateMissionsPanel(self):
        uthread.new(self.UpdatePanel, PANEL_MISSIONS)

    @telemetry.ZONE_FUNCTION
    def UpdateFactionalWarfarePanel(self):
        self.UpdatePanel(PANEL_FACTIONAL_WARFARE)

    @telemetry.ZONE_FUNCTION
    def UpdateLocationInfoPanel(self):
        self.UpdatePanel(PANEL_LOCATION_INFO)

    @telemetry.ZONE_FUNCTION
    def UpdateIncursionsPanel(self):
        self.UpdatePanel(PANEL_INCURSIONS)

    @telemetry.ZONE_FUNCTION
    def UpdatePanel(self, panelTypeID):
        if not session.charid:
            return
        sm.ChainEvent('ProcessUpdateInfoPanel', panelTypeID)
        if not self.infoPanelContainer:
            return
        panel = self.GetPanelByTypeID(panelTypeID)
        if not panel:
            panelCls = self.GetPanelClassByPanelTypeID(panelTypeID)
            if panelCls.IsAvailable():
                self.ReconstructAllPanels()
        elif panel and not panel.IsAvailable():
            self.infoPanelContainer.ClosePanel(panelTypeID)
        self.UpdateTopIcons()

    def UpdateMissionStatusData(self, agentList):
        with ExceptionEater('Exception during missiontracker.UpdateAllMissions'):
            if agentList:
                self.missionTrackerMgr.UpdateAllMissions(agentList)

    def RegisterMissionTracking(self):
        with ExceptionEater('exception during RegisterMissionTracking'):
            missions = sm.GetService('journal').GetMyAgentJournalDetails()[0]
            for mission in missions:
                missionState, importantMission, missionType, missionNameID, agentID, expirationTime, bookmarks, remoteOfferable, remoteCompletable, contentID = mission
                if missionState != const.agentMissionStateAccepted or expirationTime and expirationTime < blue.os.GetWallclockTime():
                    continue
                else:
                    self.agentList.append(agentID)

            self.UpdateMissionStatusData(self.agentList)

    def SetDestinationNotificationTrigger(self, locationID, agentID):
        if agentID not in self.destinationTriggers[locationID]:
            self.destinationTriggers[locationID].append(agentID)

    def RemoveDestinationNotificationTrigger(self, agentID):
        for locationID in self.destinationTriggers.keys():
            if agentID in self.destinationTriggers[locationID]:
                self.destinationTriggers[locationID].remove(agentID)

    def GetAgentMissions(self, *args):
        """ Returns a list of current agent missions. Used by the missions info panel """
        allMissionsList = []
        missions = sm.GetService('journal').GetMyAgentJournalDetails()[0]
        HOMEBASE = 0
        NOTHOMEBASE = 1
        if missions:
            for mission in missions:
                missionState, importantMission, missionType, missionNameID, agentID, expirationTime, bookmarks, remoteOfferable, remoteCompletable, contentID = mission
                if missionState != const.agentMissionStateAccepted or expirationTime and expirationTime < blue.os.GetWallclockTime():
                    continue
                homeBaseBms = []
                otherBms = []
                foundHomeBaseBm = False
                for bm in bookmarks:
                    if bm.locationType == 'agenthomebase':
                        homeBaseBms.append((HOMEBASE, bm))
                    elif 'isAgentBase' in bm.__dict__ and bm.isAgentBase:
                        foundHomeBaseBm = True
                        otherBms.append((HOMEBASE, bm))
                    else:
                        otherBms.append((NOTHOMEBASE, bm))

                bookmarksIwant = otherBms
                if not foundHomeBaseBm:
                    bookmarksIwant.extend(homeBaseBms)
                bookmarksIwant = uiutil.SortListOfTuples(bookmarksIwant)
                bmInfo = uiutil.Bunch(missionNameID=missionNameID, bookmarks=bookmarksIwant, agentID=agentID)
                allMissionsList.append((expirationTime, bmInfo))

            allMissionsList = uiutil.SortListOfTuples(allMissionsList)
        return allMissionsList

    def GetSolarSystemTrace(self, itemID, altText = None, traceFontSize = 12):
        if util.IsStation(itemID):
            solarSystemID = cfg.stations.Get(itemID).solarSystemID
        else:
            solarSystemID = itemID
        try:
            sec, col = util.FmtSystemSecStatus(sm.GetService('map').GetSecurityStatus(solarSystemID), 1)
            col.a = 1.0
            securityLabel = "</b> <color=%s><hint='%s'>%s</hint></color>" % (util.StrFromColor(col), localization.GetByLabel('UI/Map/StarMap/SecurityStatus'), sec)
        except KeyError:
            self.LogError('Neocom failed to get security status for item', solarSystemID, 'displaying BROKEN')
            log.LogException()
            sys.exc_clear()
            securityLabel = ''

        si = cfg.mapSystemCache.Get(solarSystemID)
        constellationID = si.constellationID
        regionID = si.regionID
        if altText:
            solarSystemAlt = " alt='%s'" % uiutil.StripTags(altText, stripOnly=['localized'])
        else:
            solarSystemAlt = ''
        locationTrace = '<url=showinfo:%s//%s%s>%s</url>%s' % (const.typeSolarSystem,
         solarSystemID,
         solarSystemAlt,
         cfg.evelocations.Get(solarSystemID).locationName,
         securityLabel)
        if traceFontSize:
            locationTrace += '<fontsize=12>'
        if not util.IsWormholeRegion(regionID):
            seperator = '<fontsize=%(fontsize)s> </fontsize>&lt;<fontsize=%(fontsize)s> </fontsize>' % {'fontsize': 8}
            locationTrace += seperator
            locationTrace += '<url=showinfo:%s//%s>%s</url>' % (const.typeConstellation, constellationID, cfg.evelocations.Get(constellationID).locationName)
            locationTrace += seperator
            locationTrace += '<url=showinfo:%s//%s>%s</url>' % (const.typeRegion, regionID, cfg.evelocations.Get(regionID).locationName)
        return locationTrace

    def GetLocationInfoSettings(self):
        inView = settings.char.windows.Get('neocomLocationInfo_3', None)
        if inView is None:
            inView = ['nearest', 'sovereignty']
        return inView

    def GetSolarSystemStatusText(self, systemStatus = None, returnNone = False):
        if systemStatus is None:
            systemStatus = sm.StartService('facwar').GetSystemStatus()
        xtra = ''
        if systemStatus == const.contestionStateCaptured:
            xtra = localization.GetByLabel('UI/Neocom/SystemLost')
        elif systemStatus == const.contestionStateVulnerable:
            xtra = localization.GetByLabel('UI/Neocom/Vulnerable')
        elif systemStatus == const.contestionStateContested:
            xtra = localization.GetByLabel('UI/Neocom/Contested')
        elif systemStatus == const.contestionStateNone and returnNone:
            xtra = localization.GetByLabel('UI/Neocom/Uncontested')
        return xtra
