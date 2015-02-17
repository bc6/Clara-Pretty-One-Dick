#Embedded file name: eve/client/script/ui/shared/infoPanels\infoPanelMissions.py
import ast
import uicontrols
import uicls
import carbonui.const as uiconst
import util
import localization
import state
from carbonui.primitives.container import Container
from eve.client.script.ui.control.eveIcon import Icon
from eve.devtools.script import uiEventListenerConsts
import infoPanelConst
import const
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import ApproachLocation
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import WarpToBookmark
from carbonui.primitives.sprite import Sprite
import trinity
import uiutil

class MissionInfo(Container):

    def GetTypeName(self, typeID):
        name = cfg.invtypes[typeID]
        return name['typeName']

    def LoadTooltipPanel(self, panel, *args):
        if not self.missionHint:
            return
        panel.state = uiconst.UI_NORMAL
        panel.margin = 8
        panel.columns = 2
        if self.iconTypeID:
            agentIcon = Icon(parent=panel, opacity=0.7, size=48, left=0, top=0, state=uiconst.UI_DISABLED)
            sm.GetService('photo').GetIconByType(agentIcon, self.iconTypeID, self.iconItemID, ignoreSize=True)
        panel.AddLabelMedium(text=self.missionHint, cellPadding=(6, 0, 0, 2), colSpan=2, align=uiconst.CENTER, state=uiconst.UI_NORMAL)

    def GetWarpToMenu(self, *args):
        m = []
        actionText, actionFuncAndArgs, actionIcon = self.infoPanelMissions.FindButtonAction(self.bm.itemID, self.bm.solarsystemID, self.bm)
        m += [(actionText, actionFuncAndArgs), None]
        return m

    def OnClick(self, *args):
        if self.iconItemID:
            sm.GetService('state').SetState(self.iconItemID, state.selected, 1)

    def OnMouseEnter(self, *args):
        self.icon.opacity = 0.9

    def OnMouseExit(self, *args):
        self.icon.opacity = 0.7

    def _GetDungeonBookmark(self, bmInfo):
        for bm in bmInfo.bookmarks:
            if bm['locationType'] == 'dungeon':
                return bm

    def ShowHintIcon(self, parent, missionInfo, bmInfo):
        if missionInfo[0] == 'TravelTo':
            locationID = int(self.missionInfo[1])
            sm.GetService('infoPanel').SetDestinationNotificationTrigger(locationID, bmInfo.agentID)
            if locationID != session.locationid:
                self.iconItemID = locationID
                locationName = cfg.evelocations.Get(locationID).locationName
                self.icon = Sprite(parent=parent, opacity=0.7, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_destination.png')
                destinationLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=locationName, info=('showinfo', const.typeSolarSystem, locationID))
                self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/TravelTo', destination=destinationLink)
                return
            else:
                self.bm = self._GetDungeonBookmark(bmInfo)
                if not self.bm:
                    return
                self.iconItemID = self.bm['itemID']
                self.iconTypeID = self.bm['typeID']
                self.icon = Sprite(parent=parent, opacity=0.7, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_destination.png')
                self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/WarpTo')
                return
        if missionInfo[0] == 'MissionFetch':
            typeID = int(self.missionInfo[1])
            self.iconTypeID = typeID
            typeName = self.GetTypeName(typeID)
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_pickup.png')
            itemLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=typeName, info=('showinfo', typeID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/FetchItem', item=itemLink)
            return
        if missionInfo[0] == 'MissionFetchContainer':
            typeID = int(self.missionInfo[1])
            containerID = long(self.missionInfo[2])
            self.iconTypeID = typeID
            self.iconItemID = containerID
            typeName = self.GetTypeName(typeID)
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_pickup.png')
            itemLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=typeName, info=('showinfo', typeID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/RetrieveFromContainer', item=itemLink)
            return
        if self.missionInfo[0] == 'MissionFetchMine':
            typeID = int(self.missionInfo[1])
            quantity = int(self.missionInfo[2])
            self.iconTypeID = typeID
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_mining.png')
            typeName = self.GetTypeName(typeID)
            itemLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=typeName, info=('showinfo', typeID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/FetchMine', item=itemLink) + ' (%s)' % format(quantity, ',d')
            return
        if self.missionInfo[0] == 'MissionFetchMineTrigger':
            typeID = int(self.missionInfo[1])
            self.iconTypeID = typeID
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_mining.png')
            typeName = self.GetTypeName(typeID)
            itemLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=typeName, info=('showinfo', typeID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/FetchMine', item=itemLink)
            return
        if self.missionInfo[0] == 'MissionFetchTarget':
            itemTypeID = int(self.missionInfo[1])
            itemTypeName = self._GetTypeName(itemTypeID)
            targetTypeID = int(self.missionInfo[2])
            targetTypeName = self._GetTypeName(targetTypeID)
            targetLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=targetTypeName, info=('showinfo', targetTypeID))
            itemLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=itemTypeName, info=('showinfo', itemTypeID))
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_kill.png')
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/FetchTarget', npc=targetLink, item=itemLink)
            return
        if missionInfo[0] == 'AllObjectivesComplete':
            self.iconItemID = agentID = long(self.missionInfo[1])
            self.iconTypeID = agentTypeID = cfg.eveowners.Get(self.iconItemID).typeID
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, color=util.Color.GREEN, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_check.png')
            agentLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=cfg.eveowners.Get(agentID).name, info=('showinfo', agentTypeID, agentID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/MissionComplete', agent=agentLink)
            return
        if self.missionInfo[0] == 'TransportItemsPresent':
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_dropoff.png')
            self.iconTypeID = itemTypeID = int(self.missionInfo[1])
            stationID = int(self.missionInfo[2])
            sm.GetService('infoPanel').SetDestinationNotificationTrigger(stationID, bmInfo.agentID)
            stationTypeID = cfg.eveowners.Get(stationID).typeID
            stationName = cfg.evelocations.Get(stationID).name
            itemTypeName = self.GetTypeName(self.iconTypeID)
            destinationLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=stationName, info=('showinfo', stationTypeID, stationID))
            itemLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=itemTypeName, info=('showinfo', itemTypeID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/TransportItems', item=itemLink, destination=destinationLink)
            return
        if self.missionInfo[0] == 'TransportItemsMissing':
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_pickup.png')
            self.iconTypeID = itemTypeID = int(self.missionInfo[1])
            itemTypeName = self.GetTypeName(self.iconTypeID)
            itemLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=itemTypeName, info=('showinfo', itemTypeID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/TransportItemsMissing', item=itemLink)
            return
        if self.missionInfo[0] == 'FetchObjectAcquiredDungeonDone':
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_dropoff.png')
            self.iconTypeID = itemTypeID = int(self.missionInfo[1])
            itemTypeName = self.GetTypeName(self.iconTypeID)
            itemLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=itemTypeName, info=('showinfo', itemTypeID))
            agentID = long(self.missionInfo[2])
            stationID = ast.literal_eval(self.missionInfo[3])
            if stationID is not None:
                stationID = long(stationID)
                sm.GetService('infoPanel').SetDestinationNotificationTrigger(stationID, bmInfo.agentID)
            agentTypeID = cfg.eveowners.Get(agentID).typeID
            agentLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=cfg.eveowners.Get(agentID).name, info=('showinfo', agentTypeID, agentID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/FetchItemReturn', item=itemLink, agent=agentLink)
            return
        if self.missionInfo[0] == 'GoToGate':
            self.iconItemID = long(self.missionInfo[1])
            self.iconTypeID = const.typeAccelerationGate
            self.icon = Sprite(parent=parent, opacity=0.7, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_destination.png')
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/GoToGate')
            return
        if self.missionInfo[0] == 'KillTrigger':
            self.iconTypeID = targetTypeID = int(self.missionInfo[1])
            self.iconItemID = targetItemID = long(self.missionInfo[2])
            eventTypeName = self.missionInfo[3]
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_kill.png')
            targetName = self.GetTypeName(targetTypeID)
            targetLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=targetName, info=('showinfo', targetTypeID, targetItemID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/KillTrigger', target=targetLink) + ' ' + eventTypeName
            return
        if self.missionInfo[0] == 'DestroyLCSAndAll':
            self.iconTypeID = targetTypeID = int(self.missionInfo[1])
            self.iconItemID = targetItemID = long(self.missionInfo[2])
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_kill.png')
            targetName = self.GetTypeName(targetTypeID)
            targetLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=targetName, info=('showinfo', targetTypeID, targetItemID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/DestroyLCSAndAll', lcs=targetLink)
            return
        if self.missionInfo[0] == 'Destroy':
            self.iconTypeID = targetTypeID = int(self.missionInfo[1])
            self.iconItemID = targetItemID = long(self.missionInfo[2])
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_kill.png')
            targetName = self.GetTypeName(targetTypeID)
            targetLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=targetName, info=('showinfo', targetTypeID, targetItemID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/Destroy', lcs=targetLink)
            return
        if self.missionInfo[0] == 'Attack':
            self.iconTypeID = targetTypeID = int(self.missionInfo[1])
            self.iconItemID = targetItemID = long(self.missionInfo[2])
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_kill.png')
            targetName = self.GetTypeName(targetTypeID)
            targetLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=targetName, info=('showinfo', targetTypeID, targetItemID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/Attack', target=targetLink)
            return
        if self.missionInfo[0] == 'Approach':
            self.iconTypeID = targetTypeID = int(self.missionInfo[1])
            self.iconItemID = targetItemID = long(self.missionInfo[2])
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_approach.png')
            targetName = self.GetTypeName(targetTypeID)
            targetLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=targetName, info=('showinfo', targetTypeID, targetItemID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/Approach', target=targetLink)
            return
        if self.missionInfo[0] == 'Hack':
            self.iconTypeID = targetTypeID = int(self.missionInfo[1])
            self.iconItemID = targetItemID = long(self.missionInfo[2])
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_hack.png')
            targetName = self.GetTypeName(targetTypeID)
            targetLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=targetName, info=('showinfo', targetTypeID, targetItemID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/Hack', target=targetLink)
            return
        if self.missionInfo[0] == 'Salvage':
            self.iconTypeID = targetTypeID = int(self.missionInfo[1])
            self.iconItemID = targetItemID = long(self.missionInfo[2])
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_kill.png')
            targetName = self.GetTypeName(targetTypeID)
            targetLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=targetName, info=('showinfo', targetTypeID, targetItemID))
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/Approach', target=targetLink)
            return
        if self.missionInfo[0] == 'DestroyAll':
            self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_kill.png')
            self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/DestroyAll')
            return
        self.missionHint = localization.GetByLabel('UI/Agents/MissionTracker/ReadJournal')
        self.icon = Sprite(parent=parent, opacity=0.6, width=20, height=20, left=0, top=0, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/MissionTracker/tracker_read.png')

    def IsTypeIDInBallpark(self, typeID):
        ballpark = sm.GetService('michelle').GetBallpark()
        balls = ballpark.GetBallsAndItems()
        for b in balls:
            if b[1].typeID == typeID:
                return b[1].itemID

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        bmInfo = attributes.bmInfo
        self.infoPanelMissions = attributes.infoPanelMissions
        self.bm = None
        self.icon = None
        self.state = uiconst.UI_NORMAL
        self.width = 20
        self.height = 20
        self.iconTypeID = None
        self.iconItemID = None
        self.missionHint = None
        self.missionInfo, previousInfo = sm.GetService('infoPanel').GetAgentMissionInfo(bmInfo.agentID)
        self.ShowHintIcon(self, self.missionInfo, bmInfo)
        if self.icon and previousInfo != self.missionInfo:
            uicore.animations.SpGlowFadeTo(self.icon, loops=5, glowExpand=0.0, duration=0.5)


class InfoPanelMissions(uicls.InfoPanelBase):
    __guid__ = 'uicls.InfoPanelMissions'
    default_name = 'InfoPanelMissions'
    panelTypeID = infoPanelConst.PANEL_MISSIONS
    label = 'UI/PeopleAndPlaces/AgentMissions'
    default_iconTexturePath = 'res:/UI/Texture/Classes/InfoPanels/Missions.png'
    hasSettings = False

    def ApplyAttributes(self, attributes):
        uicls.InfoPanelBase.ApplyAttributes(self, attributes)
        self.headerCls(name='agentHeader', parent=self.headerCont, align=uiconst.CENTERLEFT, text='<color=white>' + localization.GetByLabel(self.label))

    @staticmethod
    def IsAvailable():
        """ Is this info panel currently available for viewing """
        return bool(sm.GetService('infoPanel').GetAgentMissions())

    def ConstructNormal(self):
        """
            adding the menus for all the active missions
        """
        self.mainCont.Flush()
        self.state = uiconst.UI_NORMAL
        top = 0
        for bmInfo in sm.GetService('infoPanel').GetAgentMissions():
            if isinstance(bmInfo.missionNameID, (int, long)):
                missionName = localization.GetByMessageID(bmInfo.missionNameID)
            else:
                missionName = bmInfo.missionNameID
            missionHint = MissionInfo(parent=self.mainCont, infoPanelMissions=self, align=uiconst.TOPLEFT, bmInfo=bmInfo, left=0, top=top)
            m = uicls.UtilMenu(menuAlign=uiconst.TOPLEFT, parent=self.mainCont, align=uiconst.TOPLEFT, top=top, left=20, label=missionName, texturePath='res:/UI/Texture/Icons/38_16_229.png', closeTexturePath='res:/UI/Texture/Icons/38_16_230.png', GetUtilMenu=(self.MissionMenu, bmInfo), maxWidth=infoPanelConst.PANELWIDTH - infoPanelConst.LEFTPAD)
            left = m.width + 4
            top += 20

    def MissionMenu(self, menuParent, bmInfo, *args):
        bookmarks = bmInfo.bookmarks
        agentID = bmInfo.agentID
        startInfoColorTag = '<color=-2039584>'
        endColorTag = '</color>'
        endInfoTag = '</url>'
        for bm in bookmarks:
            bmTypeID = bm.typeID
            headerText = ''
            systemName = cfg.evelocations.Get(bm.solarsystemID).name
            headerText = bm.hint.replace(systemName, '')
            headerText = headerText.strip(' ').strip('-').strip(' ')
            menuParent.AddHeader(text=headerText)
            menuCont = menuParent.AddContainer(name='menuCont', align=uiconst.TOTOP, height=40)
            menuCont.GetEntryWidth = lambda mc = menuCont: self.GetContainerEntryWidth(mc)
            startLocationInfoTag = '<url=showinfo:%d//%d>' % (bmTypeID, bm.itemID)
            locationName = self.GetColorCodedSecurityStringForLocation(bm.solarsystemID, cfg.evelocations.Get(bm.itemID).name)
            locationText = localization.GetByLabel('UI/Agents/InfoLink', startInfoTag=startLocationInfoTag, startColorTag=startInfoColorTag, objectName=locationName, endColorTag=endColorTag, endnfoTag=endInfoTag)
            locationLabel = uicontrols.EveLabelMedium(text=locationText, parent=menuCont, name='location', align=uiconst.TOTOP, padLeft=6, state=uiconst.UI_NORMAL, maxLines=1)
            locationLabel.GetMenu = (self.GetLocationMenu, bm)
            if bm.itemID != session.stationid2:
                actionText, actionFuncAndArgs, actionIcon = self.FindButtonAction(bm.itemID, bm.solarsystemID, bm)
                menuParent.AddIconEntry(icon=actionIcon, text=actionText, callback=actionFuncAndArgs)
            menuParent.AddSpace()

        menuParent.AddDivider()
        menuParent.AddIconEntry(icon='res:/UI/Texture/Icons/38_16_190.png', text=localization.GetByLabel('UI/Agents/Commands/ReadDetails'), callback=(self.ReadDetails, agentID))
        menuParent.AddIconEntry(icon='res:/UI/Texture/classes/Chat/AgentChat.png', text=localization.GetByLabel('UI/Chat/StartConversationAgent'), callback=(self.TalkToAgent, agentID))

    def FindButtonAction(self, itemID, solarsystemID, bookmark, *args):
        text = ''
        if solarsystemID != session.solarsystemid:
            text = localization.GetByLabel('UI/Inflight/SetDestination')
            funcAndArgs = (sm.StartService('starmap').SetWaypoint, itemID, True)
            icon = 'res:/UI/Texture/classes/LocationInfo/destination.png'
        elif util.IsStation(itemID):
            text = localization.GetByLabel('UI/Inflight/DockInStation')
            funcAndArgs = (sm.GetService('menu').Dock, itemID)
            icon = 'res:/ui/texture/icons/44_32_9.png'
        else:
            bp = sm.StartService('michelle').GetBallpark()
            ownBall = bp and bp.GetBall(session.shipid) or None
            dist = sm.GetService('menu').FindDist(0, bookmark, ownBall, bp)
            checkApproachDist = dist and dist < const.minWarpDistance
            if checkApproachDist:
                text = localization.GetByLabel('UI/Inflight/ApproachObject')
                funcAndArgs = (ApproachLocation, bookmark)
                icon = 'res:/ui/texture/icons/44_32_23.png'
            else:
                defaultWarpDist = sm.GetService('menu').GetDefaultActionDistance('WarpTo')
                text = localization.GetByLabel('UI/Inflight/WarpToBookmark')
                funcAndArgs = (WarpToBookmark, bookmark, defaultWarpDist)
                icon = 'res:/ui/texture/icons/44_32_18.png'
        return (text, funcAndArgs, icon)

    def GetColorCodedSecurityStringForLocation(self, solarsystemID, itemName):
        sec, col = util.FmtSystemSecStatus(sm.GetService('map').GetSecurityStatus(solarsystemID), 1)
        col.a = 1.0
        color = util.StrFromColor(col)
        text = '%s <color=%s>%s</color>' % (itemName, color, sec)
        return text

    def GetAgentMenu(self, agentID, *args):
        m = sm.GetService('menu').CharacterMenu(agentID)
        return m

    def GetLocationMenu(self, bm):
        m = sm.GetService('menu').CelestialMenu(bm.itemID, None, None, 0, None, None, bm)
        return m

    def ReadDetails(self, agentID, *args):
        sm.GetService('agents').PopupMissionJournal(agentID)

    def TalkToAgent(self, agentID, *args):
        sm.StartService('agents').InteractWith(agentID)

    def GetContainerEntryWidth(self, menuCont, *args):
        longestText = 0
        for child in menuCont.children:
            if isinstance(child, uicontrols.Label):
                if longestText < child.textwidth:
                    longestText = child.textwidth

        return longestText + 20
