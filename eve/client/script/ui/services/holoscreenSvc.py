#Embedded file name: eve/client/script/ui/services\holoscreenSvc.py
"""
    This service controls the Captains Quarters Main screen, decides which templates to
    play. All data for the templates comes through this service as well.
"""
import uiprimitives
import blue
import telemetry
import const
import copy
import log
import service
import uthread
import util
import cqscreen
import cqscreentemplates
import random
import corebrowserutil
import uicls
import carbonui.const as uiconst
import urllib2
import os
import localization

class HoloscreenSvc(service.Service):
    __guid__ = 'svc.holoscreen'
    __displayname__ = 'Holoscreen service'
    RSS_FEEDS = ['http://newsfeed.eveonline.com/en-US/42/articles/page/1/20']
    __notifyevents__ = ['OnSessionChanged', 'OnUIScalingChange']
    __dependencies__ = ['clientPathfinderService']

    def Run(self, memStream = None):
        self.mainScreen = None
        self.corpFinderScreen = None
        self.piScreen = None
        self.playlist = []
        self.currTemplate = 0
        self.mainScreenDesktop = None
        self.corpFinderScreenDesktop = None
        self.piScreenDesktop = None
        self.playThread = None
        self.holoscreenMgr = sm.RemoteSvc('holoscreenMgr')

    def Restart(self):
        self.SetDefaultPlaylist()
        if self.mainScreenDesktop:
            self.mainScreenDesktop.Flush()
        if self.mainScreen:
            self.mainScreen.Close()
            self.mainScreen = cqscreen.MainScreen(parent=self.mainScreenDesktop)
        if self.playThread:
            self.StopTemplates()
            self.PlayTemplates()

    def OnEntitySceneUnloaded(self, sceneID):
        if self.playThread:
            self.playThread.kill()
            self.playThread = None
        self.mainScreen = None
        self.corpFinderScreen = None
        self.piScreen = None
        self.mainScreenDesktop = None
        self.corpFinderScreenDesktop = None
        self.piScreenDesktop = None

    def OnMainScreenDesktopCreated(self, desktop, entityID):
        self.mainScreenDesktop = desktop
        if prefs.GetValue('cqScreensEnabled', True):
            self.mainScreen = cqscreen.MainScreen(parent=desktop, entityID=entityID)
            self.PlayTemplates()
        else:
            self.mainScreen = uiprimitives.Sprite(name='screenCenterFallback', parent=desktop, texturePath='res:/UI/Texture/classes/CQLoadingScreen/loadingScreen.png', align=uiconst.TOALL)
            self.mainScreen.entityID = entityID

    def ReloadMainScreen(self):
        if not self.mainScreen:
            return
        self.StopTemplates()
        entityID = self.mainScreen.entityID
        self.mainScreen.Close()
        self.OnMainScreenDesktopCreated(self.mainScreenDesktop, entityID=entityID)

    def OnCorpFinderScreenDesktopCreated(self, desktop, entityID, newCorpID = None):
        if newCorpID is None:
            newCorpID = session.corpid
        self.corpFinderScreenDesktop = desktop
        if prefs.GetValue('cqScreensEnabled', True):
            self.corpFinderScreen = cqscreen.CorpFinderScreen(parent=self.corpFinderScreenDesktop, corpID=newCorpID, entityID=entityID)
        else:
            self.corpFinderScreen = uiprimitives.Sprite(name='screenLeftFallback', parent=desktop, texturePath='res:/UI/Texture/classes/CQSideScreens/corpRecruitmentScreenBG.png', align=uiconst.TOALL)
            self.corpFinderScreen.entityID = entityID

    def OnSessionChanged(self, isremote, sess, change):
        """
            This method should handle dynamically changing any screen content based
            on session-dependant information. Currently only handles changing the
            corporation logo when the character switches corporations.
        """
        if 'corpid' in change and change['corpid'][1]:
            if self.corpFinderScreen is not None:
                self.corpFinderScreen.ConstructCorpLogo(change['corpid'][1])

    def OnUIScalingChange(self, *args):
        if self.mainScreen is not None:
            self.ReloadMainScreen()

    def ReloadCorpFinderScreen(self, newCorpID = None):
        """ Use this to reload during development """
        entityID = self.corpFinderScreen.entityID
        try:
            self.corpFinderScreen.Close()
        finally:
            self.OnCorpFinderScreenDesktopCreated(self.corpFinderScreenDesktop, entityID, newCorpID)

    def OnPIScreenDesktopCreated(self, desktop, entityID):
        self.piScreenDesktop = desktop
        if prefs.GetValue('cqScreensEnabled', True):
            self.piScreen = cqscreen.PIScreen(parent=desktop, entityID=entityID)
        else:
            self.piScreen = uiprimitives.Sprite(name='screenRightFallback', parent=desktop, texturePath='res:/UI/Texture/classes/CQSideScreens/PIScreenBG.png', align=uiconst.TOALL)
            self.piScreen.entityID = entityID

    def ReloadPIScreen(self):
        """ Use this to reload during development """
        entityID = self.piScreen.entityID
        try:
            self.piScreen.Close()
        finally:
            self.OnPIScreenDesktopCreated(self.piScreenDesktop, entityID)

    def PlayTemplates(self):
        """ Start playing the templates in self.playlist """
        self.SetDefaultPlaylist()
        self.playThread = uthread.new(self._PlayTemplates)
        self.mainScreen.SetNewsTickerData(*self.GetNewsTickerData())

    @telemetry.ZONE_METHOD
    def _PlayTemplates(self):
        while not self.mainScreen.destroyed:
            template, data = self.GetNextTemplate()
            self.mainScreen.PlayTemplate(template, data)
            self.currTemplate += 1
            blue.pyos.synchro.Yield()

    def StopTemplates(self):
        if self.playThread:
            self.playThread.kill()
        self.currTemplate = 0

    def GetNextTemplate(self):
        if self.currTemplate >= len(self.playlist):
            self.currTemplate = 0
        template, dataSource = self.playlist[self.currTemplate]
        try:
            if callable(dataSource):
                returnData = dataSource()
            else:
                returnData = dataSource
        except:
            log.LogException()
            returnData = None

        return (template, returnData)

    def SetTemplates(self, templateList):
        self.playlist = templateList

    def SetDefaultPlaylist(self):
        self.playlist = [(cqscreentemplates.SOV, self.GetSOVTemplateData),
         (cqscreentemplates.CareerAgent, self.GetCareerAgentTemplateData),
         (cqscreentemplates.Incursion, self.GetIncursionTemplateData),
         (cqscreentemplates.ShipExposure, self.GetShipExposureTemplateData),
         (cqscreentemplates.RacialEpicArc, self.GetRacialEpicArcTemplateData),
         (cqscreentemplates.CharacterInfo, self.GetNPEEpicArcTemplateData),
         (cqscreentemplates.CharacterInfo, self.GetWantedTemplateData),
         (cqscreentemplates.Plex, self.GetPlexTemplateData),
         (cqscreentemplates.AuraMessage, self.GetSkillTrainingTemplateData)]
        customVideos = self.GetCustomVideoPlaylist()
        if customVideos:
            self.playlist = customVideos + self.playlist

    def GetCustomVideoPlaylist(self):
        """ Returns a playlist of .bik videos added to 'cache:/CQScreenVideos' by players """
        path = blue.paths.ResolvePath(u'cache:/CQScreenVideos')
        if not os.path.isdir(path):
            try:
                os.mkdir(path)
            except:
                pass

            return None
        playlist = []
        for fileName in os.listdir(path):
            if fileName.endswith('.bik'):
                videoPath = str(path + '/' + fileName)
                data = util.KeyVal(videoPath=videoPath)
                playlist.append((cqscreentemplates.FullscreenVideo, data))

        return playlist

    @telemetry.ZONE_METHOD
    def GetSOVTemplateData(self):
        sovList = self.holoscreenMgr.GetTwoHourCache().sovChangesReport
        if sovList is not None and len(sovList) > 0:
            data = copy.deepcopy(random.choice(sovList))
            regionID = sm.GetService('map').GetRegionForSolarSystem(data.solarSystemID)
            solarSystemName = cfg.evelocations.Get(data.solarSystemID).name
            oldOwnerName = cfg.eveowners.Get(data.oldOwnerID).ownerName
            newOwnerName = cfg.eveowners.Get(data.newOwnerID).ownerName
            data.middleText = localization.GetByLabel('UI/Station/Holoscreen/SOV/AllianceControlsSystem', alliance=newOwnerName, system='<color=WHITE>' + solarSystemName + '</color>')
            data.bottomText = localization.GetByLabel('UI/Station/Holoscreen/SOV/AllianceSoverigntySwitch', oldAlliance=oldOwnerName, newAlliance=newOwnerName, system=data.solarSystemID, region=regionID)
            data.clickFunc = uicore.cmd.OpenSovDashboard
            data.clickFuncLabel = localization.GetByLabel('UI/Station/Holoscreen/SOV/OpenSovereigntyPanel')
            data.clickArgs = (data.solarSystemID,)
            return data

    @telemetry.ZONE_METHOD
    def GetCareerAgentTemplateData(self):
        chosenCareerType = random.choice([const.agentDivisionBusiness,
         const.agentDivisionExploration,
         const.agentDivisionIndustry,
         const.agentDivisionMilitary,
         const.agentDivisionAdvMilitary])
        careerAgents = sm.GetService('agents').GetAgentsByType(const.agentTypeCareerAgent)
        careerAgents = [ a for a in careerAgents if a.divisionID == chosenCareerType ]
        if chosenCareerType == const.agentDivisionBusiness:
            careerText = localization.GetByLabel('UI/Tutorial/Business')
            careerDesc = localization.GetByLabel('UI/Tutorial/BusinessDesc')
        elif chosenCareerType == const.agentDivisionExploration:
            careerText = localization.GetByLabel('UI/Tutorial/Exploration')
            careerDesc = localization.GetByLabel('UI/Tutorial/ExplorationDesc')
        elif chosenCareerType == const.agentDivisionIndustry:
            careerText = localization.GetByLabel('UI/Tutorial/Industry')
            careerDesc = localization.GetByLabel('UI/Tutorial/IndustryDesc')
        elif chosenCareerType == const.agentDivisionMilitary:
            careerText = localization.GetByLabel('UI/Tutorial/Military')
            careerDesc = localization.GetByLabel('UI/Tutorial/MilitaryDesc')
        elif chosenCareerType == const.agentDivisionAdvMilitary:
            careerText = localization.GetByLabel('UI/Tutorial/AdvMilitary')
            careerDesc = localization.GetByLabel('UI/Tutorial/AdvMilitaryDesc')
        nearAgentList = []
        nearestDist = 9999999
        for row in careerAgents:
            dist = self.clientPathfinderService.GetJumpCountFromCurrent(row.solarsystemID)
            if dist < nearestDist:
                nearAgentList = []
                nearestDist = dist
            if dist == nearestDist:
                nearAgentList.append((row.agentID, row.stationID))

        if not nearAgentList:
            return None
        chosenAgentID, chosenStationID = random.choice(nearAgentList)
        careerAdData = util.KeyVal()
        careerAdData.agentID = chosenAgentID
        careerAdData.stationID = chosenStationID
        careerAdData.jumpDistance = nearestDist
        careerVideoPath = {const.agentDivisionBusiness: 'res:/video/cq/CQ_TEMPLATE_CAREER_TRADE_BUSINESS.bik',
         const.agentDivisionExploration: 'res:/video/cq/CQ_TEMPLATE_CAREER_EXPLORATION.bik',
         const.agentDivisionIndustry: 'res:/video/cq/CQ_TEMPLATE_CAREER_INDUSTRY.bik',
         const.agentDivisionMilitary: 'res:/video/cq/CQ_TEMPLATE_CAREER_MILITARY.bik',
         const.agentDivisionAdvMilitary: 'res:/video/cq/CQ_TEMPLATE_CAREER_ADVANCED_MILITARY.bik'}.get(chosenCareerType)
        data = util.KeyVal()
        data.charID = chosenAgentID
        data.headingText = '<fontsize=60>' + careerText
        data.subHeadingText = localization.GetByLabel('UI/Station/Holoscreen/CareerAgent/CareerAgentTitle')
        data.mainText = '<fontsize=20>' + careerDesc + '\n\n' + localization.GetByLabel('UI/Station/Holoscreen/CareerAgent/AgentInfo', station=careerAdData.stationID)
        data.clickFunc = sm.StartService('tutorial').ShowCareerFunnel
        data.clickFuncLabel = localization.GetByLabel('UI/Station/Holoscreen/CareerAgent/OpenCareerAgentDirectory')
        data.introVideoPath = 'res:/video/cq/LOGO_CONCORD.bik'
        data.careerVideoPath = careerVideoPath
        return data

    @telemetry.ZONE_METHOD
    def GetIncursionTemplateData(self):
        incursionList = self.holoscreenMgr.GetTwoHourCache().incursionReport
        if not incursionList:
            return
        chosenIncursion = random.choice(incursionList)
        solarSystemName = cfg.evelocations.Get(chosenIncursion.stagingSolarSystemID).name
        constellationID = sm.GetService('map').GetConstellationForSolarSystem(chosenIncursion.stagingSolarSystemID)
        constellationName = cfg.evelocations.Get(constellationID).name
        securityLevel = str(sm.GetService('map').GetSecurityStatus(chosenIncursion.stagingSolarSystemID))
        jumpDistance = self.clientPathfinderService.GetJumpCountFromCurrent(chosenIncursion.stagingSolarSystemID)
        jumpDistanceText = localization.GetByLabel('UI/Station/Holoscreen/Incursion/NumberOfJumps', jumps=jumpDistance)
        data = util.KeyVal()
        data.headingText = localization.GetByLabel('UI/Station/Holoscreen/Incursion/IncursionWarning')
        data.introVideoPath = 'res:/video/cq/LOGO_CONCORD.bik'
        data.videoPath = 'res:/video/cq/CQ_TEMPLATE_INCURSION.bik'
        data.constellationText = '<color=orange>' + constellationName
        data.systemInfoText = '<color=red>' + securityLevel
        data.systemInfoText += ' <color=orange>' + solarSystemName
        data.systemInfoText += ' <color=white>' + jumpDistanceText
        data.influence = chosenIncursion.influence
        data.bottomText = localization.GetByLabel('UI/Station/Holoscreen/Incursion/IncursionNewsFeed', constellation=constellationID)
        data.clickFunc = sm.GetService('journal').ShowIncursionTab
        data.clickArgs = (None,
         None,
         None,
         True)
        data.clickFuncLabel = localization.GetByLabel('UI/Station/Holoscreen/Incursion/IncursionLabel')
        return data

    @telemetry.ZONE_METHOD
    def GetShipExposureTemplateData(self):
        if not eve.stationItem:
            return
        racialShips = {const.raceAmarr: [2006,
                           20183,
                           24696,
                           24692,
                           597,
                           1944,
                           624],
         const.raceCaldari: [621,
                             20185,
                             24698,
                             640,
                             602,
                             648,
                             623],
         const.raceGallente: [627,
                              20187,
                              24700,
                              641,
                              593,
                              650,
                              626],
         const.raceMinmatar: [629,
                              20189,
                              24702,
                              644,
                              587,
                              653,
                              622]}
        oreShipsList = [17478, 17476, 2998]
        racialIntroVideos = {const.raceAmarr: 'res:/video/cq/LOGO_AMARR.bik',
         const.raceCaldari: 'res:/video/cq/LOGO_CALDARI.bik',
         const.raceGallente: 'res:/video/cq/LOGO_GALLENTE.bik',
         const.raceMinmatar: 'res:/video/cq/LOGO_MINMATAR.bik'}
        data = util.KeyVal()
        if random.random() <= 0.3:
            data.introVideoPath = 'res:/video/cq/LOGO_ORE.bik'
            data.shipTypeID = random.choice(oreShipsList)
        else:
            stationType = cfg.invtypes.Get(eve.stationItem.stationTypeID)
            stationRace = stationType['raceID']
            if stationRace not in racialShips:
                stationRace = const.raceGallente
            data.introVideoPath = racialIntroVideos[stationRace]
            data.shipTypeID = random.choice(racialShips[stationRace])
        shipCachedInfo = cfg.invtypes.Get(data.shipTypeID)
        data.shipName = shipCachedInfo.name
        data.shipGroupName = shipCachedInfo.Group().groupName
        data.buttonText = localization.GetByLabel('UI/Station/Holoscreen/Common/AvailableOnMarketNow')
        data.mainText = '<fontsize=30>' + localization.GetByLabel('UI/Station/Holoscreen/Ship/ShipDetailsTitle')
        data.mainText += '\n<fontsize=25>' + shipCachedInfo.description
        data.clickFunc = sm.GetService('marketutils').ShowMarketDetails
        data.clickArgs = (data.shipTypeID, None)
        data.clickFuncLabel = localization.GetByLabel('UI/Station/Holoscreen/Ship/OpenMarketForShip', ship=data.shipTypeID)
        return data

    @telemetry.ZONE_METHOD
    def GetRacialEpicArcTemplateData(self):
        epicArcList = self.holoscreenMgr.GetRuntimeCache().epicArcAgents
        if not epicArcList:
            return
        if not eve.stationItem:
            return
        epicArcData = random.choice(epicArcList)
        data = util.KeyVal()
        data.charID = epicArcData.agentID
        data.headingText = ''
        solarSystemID = sm.GetService('agents').GetSolarSystemOfAgent(epicArcData.agentID)
        regionID = sm.GetService('map').GetRegionForSolarSystem(solarSystemID)
        securityLevel = sm.GetService('map').GetSecurityStatus(solarSystemID)
        data.mainText = '<fontsize=30><color=WHITE>' + localization.GetByLabel('UI/Station/Holoscreen/RacialEpicArc/AgentAdvert', system=solarSystemID, region=regionID, securityLevel=securityLevel)
        epicArcDict = {48: (const.factionAmarrEmpire, localization.GetByLabel('UI/Station/Holoscreen/RacialEpicArc/AmarrNews')),
         52: (const.factionGallenteFederation, localization.GetByLabel('UI/Station/Holoscreen/RacialEpicArc/GallenteNews')),
         40: (const.factionCaldariState, localization.GetByLabel('UI/Station/Holoscreen/RacialEpicArc/CaldariNews')),
         29: (const.factionSistersOfEVE, localization.GetByLabel('UI/Station/Holoscreen/RacialEpicArc/SistersNews')),
         53: (const.factionMinmatarRepublic, localization.GetByLabel('UI/Station/Holoscreen/RacialEpicArc/MinmatarNews')),
         56: (const.factionAngelCartel, localization.GetByLabel('UI/Station/Holoscreen/RacialEpicArc/AngelsNews')),
         55: (const.factionGuristasPirates, localization.GetByLabel('UI/Station/Holoscreen/RacialEpicArc/GuristasNews'))}
        if epicArcData.epicArcID not in epicArcDict:
            return
        data.factionID, data.bottomText = epicArcDict.get(epicArcData.epicArcID, '')
        data.factionNameText = cfg.eveowners.Get(data.factionID).ownerName
        data.introVideoPath = {const.factionAmarrEmpire: 'res:/video/cq/LOGO_AMARR.bik',
         const.factionCaldariState: 'res:/video/cq/LOGO_CALDARI.bik',
         const.factionGallenteFederation: 'res:/video/cq/LOGO_GALLENTE.bik',
         const.factionMinmatarRepublic: 'res:/video/cq/LOGO_MINMATAR.bik',
         const.factionAngelCartel: 'res:/video/cq/LOGO_ANGELCARTEL.bik',
         const.factionGuristasPirates: 'res:/video/cq/LOGO_GURISTAS.bik',
         const.factionSistersOfEVE: 'res:/video/cq/LOGO_SISTERSOFEVE.bik'}.get(data.factionID, None)
        videoDict = {const.factionAmarrEmpire: 'res:/video/cq/CQ_TEMPLATE_EPICARC_AMARR.bik',
         const.factionCaldariState: 'res:/video/cq/CQ_TEMPLATE_EPICARC_CALDARI.bik',
         const.factionGallenteFederation: 'res:/video/cq/CQ_TEMPLATE_EPICARC_GALLENTE.bik',
         const.factionMinmatarRepublic: 'res:/video/cq/CQ_TEMPLATE_EPICARC_MINMATAR.bik',
         const.factionAngelCartel: 'res:/video/cq/CQ_TEMPLATE_EPICARC_MINMATAR.bik',
         const.factionGuristasPirates: 'res:/video/cq/CQ_TEMPLATE_EPICARC_CALDARI.bik'}
        factionKey = data.factionID
        if factionKey not in videoDict:
            stationItem = cfg.invtypes.Get(eve.stationItem.stationTypeID)
            factionKey = {const.raceAmarr: const.factionAmarrEmpire,
             const.raceCaldari: const.factionCaldariState,
             const.raceGallente: const.factionGallenteFederation,
             const.raceMinmatar: const.factionMinmatarRepublic}.get(stationItem['raceID'], const.factionGallenteFederation)
        data.videoPath = videoDict.get(factionKey, 'res:/video/cq/CQ_TEMPLATE_EPICARC_GALLENTE.bik')
        data.clickFunc = sm.GetService('agents').InteractWith
        data.clickArgs = (data.charID,)
        data.clickFuncLabel = localization.GetByLabel('UI/Station/Holoscreen/RacialEpicArc/StartAgentConversation')
        return data

    @telemetry.ZONE_METHOD
    def GetNPEEpicArcTemplateData(self):
        rookieList = self.holoscreenMgr.GetRecentEpicArcCompletions()
        if not rookieList:
            rookieData = util.KeyVal(characterID=session.charid, completionDate=blue.os.GetWallclockTime())
        else:
            rookieData = random.choice(rookieList)
        data = util.KeyVal(charID=rookieData.characterID)
        charInfo = cfg.eveowners.Get(data.charID)
        completionDate = util.FmtDate(rookieData.completionDate)
        data.introVideoPath = 'res:/video/cq/LOGO_CONCORD.bik'
        data.heading = localization.GetByLabel('UI/Station/Holoscreen/NPEEpicArc/NewPilotCertification')
        data.mainText = '<fontsize=25>' + localization.GetByLabel('UI/Station/Holoscreen/NPEEpicArc/CapsuleerStatus', owner=data.charID, completionDate=completionDate)
        data.mainText += '<br><fontsize=20>' + localization.GetByLabel('UI/Station/Holoscreen/NPEEpicArc/CertificationDisclaimer')
        data.bottomText = localization.GetByLabel('UI/Station/Holoscreen/NPEEpicArc/NewPilotCertificationCompletion', pilot=data.charID)
        data.isWanted = False
        data.clickFunc = sm.GetService('info').ShowInfo
        data.clickArgs = (charInfo.Type().typeID, data.charID)
        data.clickFuncLabel = localization.GetByLabel('UI/Station/Holoscreen/NPEEpicArc/ViewCharacterInformation')
        return data

    @telemetry.ZONE_METHOD
    def GetWantedTemplateData(self):
        topBounties = sm.GetService('bountySvc').GetTopPilotBounties()
        if not topBounties:
            return None
        chosenBounty = random.choice(topBounties)
        bountyAmount = util.FmtISK(chosenBounty.bounty, 0)
        data = util.KeyVal()
        data.introVideoPath = 'res:/video/cq/LOGO_SCOPE.bik'
        data.charID = chosenBounty.targetID
        data.heading = localization.GetByLabel('UI/Station/Holoscreen/Wanted/BountyOffer')
        data.mainText = '<fontsize=30>' + localization.GetByLabel('UI/Station/Holoscreen/Wanted/BountyPost') + '\n'
        data.mainText += '<fontsize=40><color=yellow>' + localization.GetByLabel('UI/Station/Holoscreen/Wanted/WantedCharacter', wanted=data.charID)
        data.mainText += '</color>\n'
        data.mainText += '<fontsize=30>' + localization.GetByLabel('UI/Station/Holoscreen/Wanted/BountyOffer') + '\n'
        data.mainText += '<fontsize=40>' + localization.GetByLabel('UI/Station/Holoscreen/Wanted/BountyAmount', amount=bountyAmount) + '\n'
        data.mainText += '<fontsize=20>' + localization.GetByLabel('UI/Station/Holoscreen/Wanted/WantedDisclaimer')
        data.bottomText = localization.GetByLabel('UI/Station/Holoscreen/Wanted/MostWantedNewsFeed')
        data.isWanted = True
        data.wantedHeading = localization.GetByLabel('UI/Station/Holoscreen/Wanted/Header')
        data.wantedText = localization.GetByLabel('UI/Station/Holoscreen/Wanted/Warning')
        data.clickFunc = uicore.cmd.OpenBountyOffice
        data.clickFuncLabel = localization.GetByLabel('UI/Station/Holoscreen/Wanted/ShowBountyOffice')
        return data

    @telemetry.ZONE_METHOD
    def GetPlexTemplateData(self):
        data = util.KeyVal()
        data.introVideoPath = 'res:/video/cq/LOGO_CONCORD.bik'
        data.headingText = '<fontsize=60>' + localization.GetByLabel('UI/Station/Holoscreen/PLEX/BuyPLEX')
        data.subHeadingText = '<fontsize=25>' + localization.GetByLabel('UI/Station/Holoscreen/PLEX/PLEX')
        data.buttonText = localization.GetByLabel('UI/Station/Holoscreen/Common/AvailableOnMarketNow')
        data.mainText = localization.GetByLabel('UI/Station/Holoscreen/PLEX/PLEXInformation')
        data.clickFunc = sm.GetService('marketutils').ShowMarketDetails
        data.clickArgs = (const.typePilotLicence, None)
        data.clickFuncLabel = localization.GetByLabel('UI/Station/Holoscreen/PLEX/ViewMarketForPLEX')
        return data

    @telemetry.ZONE_METHOD
    def GetSkillTrainingTemplateData(self):
        if sm.GetService('skills').SkillInTraining() is not None:
            return
        data = util.KeyVal()
        data.introVideoPath = 'res:/video/cq/LOGO_CONCORD.bik'
        data.headingText = localization.GetByLabel('UI/Station/Holoscreen/SkillTraining/Title')
        data.subHeadingText = localization.GetByLabel('UI/Station/Holoscreen/SkillTraining/Notification')
        data.clickFunc = uicore.cmd.OpenSkillQueueWindow
        data.clickFuncLabel = localization.GetByLabel('UI/Station/Holoscreen/SkillTraining/OpenSkillQueue')
        return data

    @telemetry.ZONE_METHOD
    def GetVirtualGoodsStoreTemplateData(self):
        data = util.KeyVal()
        data.introVideoPath = 'res:/video/cq/LOGO_QUAFE.bik'
        data.headingText = localization.GetByLabel('UI/Station/Holoscreen/VirtualGoods/VisitNeX')
        data.clickFunc = uicore.cmd.OpenStore
        data.clickFuncLabel = localization.GetByLabel('UI/Commands/OpenStore')
        return data

    def GetNewsTickerData(self):
        newsData = []
        for url in self.RSS_FEEDS:
            try:
                rssData = corebrowserutil.GetStringFromURL(url)
            except urllib2.HTTPError:
                failData = util.KeyVal()
                failData.date = blue.os.GetWallclockTime()
                failData.link = 'http://www.eveonline.com'
                failData.title = 'The news service is temporarily unavailable.'
                newsData = [failData]
                clickFuncList = [ uicore.cmd.OpenBrowser for entry in newsData ]
                funcKeywordsList = [ {'url': entry.link} for entry in newsData ]
                return (newsData, clickFuncList, funcKeywordsList)
            except:
                log.LogException('Uncaught (non-http) error with the mainscreen news ticker in GetNewsTickerData()')
                failData = util.KeyVal()
                failData.date = blue.os.GetWallclockTime()
                failData.link = 'http://www.eveonline.com'
                failData.title = 'The news service is unavailable.'
                newsData = [failData]
                clickFuncList = [ uicore.cmd.OpenBrowser for entry in newsData ]
                funcKeywordsList = [ {'url': entry.link} for entry in newsData ]
                return (newsData, clickFuncList, funcKeywordsList)

            while True:
                line = rssData.readline()
                if not line:
                    break
                line = line.strip()
                if not line.startswith('<entry>'):
                    continue
                entry = util.KeyVal()
                while line != '</entry>':
                    line = rssData.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line.startswith('<title'):
                        entry.title = line.lstrip('<title type="html">').rstrip('</title>')
                        entry.title = entry.title.decode('ascii', 'ignore')
                    elif line.startswith('<id>'):
                        entry.link = line.lstrip('<id>').rstrip('</id>')
                    elif line.startswith('<updated>'):
                        line = line.lstrip('<updated>').rstrip('</updated>')
                        year, month, line = line.split('-')
                        day, line = line.split('T')
                        hour, minute, line = line.split(':')
                        second = line.rstrip('Z')
                        entry.date = blue.os.GetTimeFromParts(int(year), int(month), int(day), int(hour), int(minute), 0, 0)

                if not hasattr(entry, 'date'):
                    entry.date = 0
                newsData.append(entry)
                if not line:
                    break

        newsData.sort(key=lambda x: x.date, reverse=True)
        newsData = newsData[:15]
        clickFuncList = [ uicore.cmd.OpenBrowser for entry in newsData ]
        funcKeywordsList = [ {'url': entry.link} for entry in newsData ]
        return (newsData, clickFuncList, funcKeywordsList)
