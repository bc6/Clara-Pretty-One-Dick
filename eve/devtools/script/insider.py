#Embedded file name: eve/devtools/script\insider.py
import math
from achievements.client.achievementWindow import AchievementWindow
from eve.devtools.script.colorThemeEditor import ColorThemeEditor
from eve.devtools.script.uiPerformanceTestWnd import UIPerformanceTestWnd
import uiprimitives
import uicontrols
import blue
import uix
import uiutil
import sys
import form
import util
import menu
import service
import os
from carbon.client.script.util.debugSelectionClient import DebugSelectionWindow
from eve.devtools.script import bdqmonitor
from eve.devtools.script.autobot import AutoBotWindow
import eve.devtools.script.behaviortools.clientdebugadaptors
import trinity
import types
import uicls
import cameras
import uthread
import weakref
import materialTypes
import log
import random
import carbonui.const as uiconst
import localizationTools
import eveclientqatools.gfxpreviewer as gfxpreviewer
import eveclientqatools.tablereports as gfxreports
import eveclientqatools.misc as gfxmisc
import eveclientqatools.corpseviewer as corpseviewer
import eveclientqatools.blueobjectviewer as blueobjviewer
from eve.devtools.script.uiControlCatalog.controlCatalogWindow import ControlCatalogWindow
from eve.devtools.script.cycleNebulaPanel import CycleNebulaPanel
import eve.devtools.script.taskletMonitor as taskletMonitor
import evegraphics.settings as gfxsettings
from carbon.client.script.animation.animationDebugClient import AnimationDebugWindow
from carbon.client.script.entities.AI.AIDebugClient import AIDebugWindow
from carbon.client.script.entities.combatLogWindow import CombatLogWindow
from UITree import UITree
BUTTONSPACING = 70
WINDOWHEIGHT = 45
WINDOWWIDTH = 150
FILE_BUNKERS = 'Bunkers.txt'
FILE_ENTITIES = 'Entities.txt'
FILE_GATES = 'GateTest.txt'
FILE_STELLAR = 'StellarReport.txt'
FILE_BELTS = 'BeltTest.txt'
FILE_FWREPORT = 'FacWarReport.txt'
Progress = lambda title, text, current, total: sm.GetService('loading').ProgressWnd(title, text, current, total)

class InsiderWnd(uicontrols.Window):
    __guid__ = 'form.InsiderWnd'
    default_top = 0
    default_left = '__center__'
    default_windowID = 'insider'
    default_iconNum = 'res:/UI/Texture/windowIcons/insider.png'
    default_pinned = True
    default_fixedWidth = 676
    default_fixedHeight = 54

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.MakeUnResizeable()
        self.HideMainIcon()
        self.SetTopparentHeight(0)
        self.SetCaption('Insider')

    def _OnClose(self, *args):
        settings.public.ui.Set('Insider', False)

    def OnResizeUpdate(self, *args):
        pass

    def Reload(self, *args):
        pass


class InsiderService(service.Service):
    __module__ = __name__
    __doc__ = 'Insider v2.0'
    __exportedcalls__ = {'Show': [],
     'WarpTo': [service.ROLE_IGB],
     'TravelTo': [service.ROLE_IGB]}
    __guid__ = 'svc.insider'
    __servicename__ = 'insider'
    __displayname__ = 'Insider Service'
    __notifyevents__ = ['OnSessionChanged', 'OnUIRefresh']

    def HealRemoveAllContainers(self):
        containers = [const.groupAuditLogSecureContainer,
         const.groupCargoContainer,
         const.groupFreightContainer,
         const.groupSecureCargoContainer,
         const.groupWreck]
        for entry in containers:
            self.HealRemove(entry)

    def HealRemove(self, type, group = True):
        targets = []
        bp = sm.GetService('michelle').GetBallpark()
        if bp:
            if group:
                for ballID in bp.balls.keys():
                    item = bp.GetInvItem(ballID)
                    if item and item.groupID == type:
                        targets.append(item.itemID)

            else:
                for ballID in bp.balls.keys():
                    item = bp.GetInvItem(ballID)
                    if item and item.categoryID == type:
                        if type == const.categoryStructure:
                            if sm.GetService('pwn').GetStructureState(item)[0] == 'unanchored':
                                targets.append(item.itemID)
                        elif type == const.categoryShip:
                            if not bp.GetBall(ballID).isInteractive:
                                targets.append(item.itemID)
                        else:
                            targets.append(item.itemID)

            for itemID in targets:
                sm.GetService('slash').SlashCmd('heal %d 0' % itemID)

            blue.pyos.synchro.SleepSim(250)

    def SlashBtnClick(self, cmd):
        return lambda : sm.GetService('slash').SlashCmd(cmd)

    def GetInsiderDir(self, *args):
        path = os.path.normpath(blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL))
        path = os.path.join(path, 'EVE\\insider')
        return path

    def GetTimestamp(self, *args):
        invalidChars = '\\/:*?"<>| '
        timestamp = util.FmtDate(blue.os.GetWallclockTime())
        for char in invalidChars:
            timestamp = timestamp.replace(char, '.')

        return timestamp

    def WaitOutSession(self, *args):
        if blue.os.GetSimTime() <= session.nextSessionChange:
            ms = 1000 + 1000L * (session.nextSessionChange - blue.os.GetSimTime()) / 10000000L
            blue.pyos.synchro.SleepSim(ms)

    def MakeMenu(self, list, anchor):
        mv = menu.CreateMenuView(menu.CreateMenuFromList(list), None, None)
        anchorwindow = form.InsiderWnd.GetIfOpen()
        x = max(uiutil.GetChild(anchorwindow, anchor).GetAbsolute()[0], 0)
        y = anchorwindow.top + anchorwindow.height
        if anchorwindow.top + anchorwindow.height + mv.height > uicore.desktop.height:
            mv.top = min(anchorwindow.top - mv.height, y)
        else:
            mv.top = min(uicore.desktop.width - mv.height, y)
        mv.left = min(uicore.desktop.width - mv.width, x)
        uicore.layer.menu.children.insert(0, mv)

    def TravelTo(self, destination, *args):
        try:
            sm.GetService('slash').SlashCmd('/tr me %s' % destination)
        except UserError as e:
            if e.msg == 'SystemCheck_TransferFailed_Loading':
                uicore.Message('CustomNotify', {'notify': 'Spooling up system. Please wait.'})
                blue.pyos.synchro.SleepSim(10000)
                sm.GetService('slash').SlashCmd('/tr me %s' % destination)
            sys.exc_clear()

    def TravelToLocation(self, destination, *args):
        if util.IsSolarSystem(destination):
            currentSys = session.solarsystemid2
            while currentSys != destination:
                self.TravelTo(destination)
                currentSys = session.solarsystemid2

        else:
            try:
                self.TravelTo(destination)
            except UserError as e:
                uicore.Message('CustomNotify', {'notify': 'Spooling up system. Please wait.'})
                blue.pyos.synchro.SleepSim(10000)
                self.TravelTo(destination)

            sys.exc_clear()

    def RegionBunkerTest(self, positive = True, faction = 'All', *args):
        amarr = [10000036, 10000038]
        caldari = [10000033, 10000069]
        gallente = [10000064, 10000068, 10000048]
        minmatar = [10000030, 10000042]
        all = amarr + caldari + gallente + minmatar
        lookUp = {'amarr': amarr,
         'caldari': caldari,
         'gallente': gallente,
         'minmatar': minmatar,
         'all': all}

        def Populate(regionID):
            constellations = []
            systems = []
            constellations = sm.GetService('map').GetChildren(regionID)
            for sys in constellations:
                systems += sm.GetService('map').GetChildren(sys)

            return systems

        allSystems = []
        systemsInFacWar = []
        systemsNotInFacWar = []
        if faction:
            regions = lookUp[faction.lower()]
            for region in regions:
                allSystems += Populate(region)

            facwarSystems = sm.RemoteSvc('facWarMgr').GetFacWarSystems()
            for system in allSystems:
                if system in facwarSystems:
                    systemsInFacWar.append(system)
                else:
                    systemsNotInFacWar.append(system)

            if positive:
                testSystems = systemsInFacWar
                testType = 'Positive'
            else:
                testSystems = systemsNotInFacWar
                testType = 'Negative'
            testLength = len(testSystems)
            testMinutes = testLength / 2
            if uicore.Message('CustomQuestion', {'header': 'Search for bunkers?',
             'question': 'Do you really want to search the region for bunkers? It is %d systems, and will take approximately %d minutes to run.' % (testLength, testMinutes)}, uiconst.YESNO) == uiconst.ID_YES:
                filename = '%s.%s.%s.%s' % (self.GetTimestamp(),
                 faction,
                 testType,
                 FILE_BUNKERS)
                TARGET = os.path.join(self.GetInsiderDir(), filename)
                f = blue.classes.CreateInstance('blue.ResFile')
                if not f.Open(TARGET, 0):
                    f.Create(TARGET)
                f.Write('Bunker typeID\tBunker Name\tBunker itemID\tSystem Occupier\tSystem Sovereignty\tSystem Name\tSystem ID\tConstellation Name\tConstellation ID\tRegion Name\tRegion ID')
                f.Write('\r\n')
                for system in testSystems:
                    self.WaitOutSession()
                    self.TravelToLocation(system)
                    bunkers = []
                    blue.pyos.synchro.SleepSim(5000)
                    bp = sm.GetService('michelle').GetBallpark()
                    if bp:
                        for ballID in bp.balls.keys():
                            item = bp.GetInvItem(ballID)
                            if item and item.groupID in (const.groupControlBunker,):
                                bunkers.append(item)

                    systemName = cfg.evelocations.Get(system).name
                    constellation = cfg.evelocations.Get(session.constellationid).name
                    region = cfg.evelocations.Get(session.regionid).name
                    systemSov = cfg.eveowners.Get(sm.RemoteSvc('stationSvc').GetSolarSystem(system).factionID).name
                    if bunkers:
                        for bunker in bunkers:
                            bunkertypeID = bunker.typeID
                            bunkerName = cfg.invtypes.Get(bunkertypeID).name
                            bunkeritemID = bunker.itemID
                            occupierID = sm.GetService('facwar').GetSystemOccupier(system)
                            systemOccupier = cfg.eveowners.Get(occupierID).name
                            f.Write('%s' % bunkertypeID)
                            f.Write('\t%s' % bunkerName.encode('utf8'))
                            f.Write('\t%s' % bunkeritemID)
                            f.Write('\t%s' % systemOccupier.encode('utf8'))
                            f.Write('\t%s' % systemSov.encode('utf8'))
                            f.Write('\t%s' % systemName.encode('utf8'))
                            f.Write('\t%s' % system)
                            f.Write('\t%s' % constellation.encode('utf8'))
                            f.Write('\t%s' % session.constellationid)
                            f.Write('\t%s' % region.encode('utf8'))
                            f.Write('\t%s' % session.regionid)
                            f.Write('\r\n')

                    else:
                        bunkertypeID = '-'
                        bunkerName = '-'
                        bunkeritemID = '-'
                        systemOccupier = '-'
                        f.Write('%s' % bunkertypeID)
                        f.Write('\t%s' % bunkerName.encode('utf8'))
                        f.Write('\t%s' % bunkeritemID)
                        f.Write('\t%s' % systemOccupier.encode('utf8'))
                        f.Write('\t%s' % systemSov.encode('utf8'))
                        f.Write('\t%s' % systemName.encode('utf8'))
                        f.Write('\t%s' % system)
                        f.Write('\t%s' % constellation.encode('utf8'))
                        f.Write('\t%s' % session.constellationid)
                        f.Write('\t%s' % region.encode('utf8'))
                        f.Write('\t%s' % session.regionid)
                        f.Write('\r\n')

        try:
            f.Close()
        except:
            sys.exc_clear()

    def EntitySpawn(self, label = None, chosenGroup = None, *args):
        entityDict = {}
        lootEntities = []
        respawnEntities = []
        if label:
            label = label.replace(' ', '_')
            label = label.replace("'", '')
        if chosenGroup.__class__ != list:
            chosenGroup = [chosenGroup]
        for group in chosenGroup:
            if cfg.invgroups.Get(group).categoryID in (const.categoryEntity,):
                entityDict[group] = []

        for type in cfg.invtypes:
            if type.groupID in entityDict:
                entityDict[type.groupID].append(type.typeID)

        for values in entityDict.itervalues():
            for typeID in values:
                name = cfg.invtypes.Get(typeID).name
                if not name.lower().__contains__('test'):
                    lootEntities.append(typeID)

        if uicore.Message('CustomQuestion', {'header': 'Spawn NPCs?',
         'question': "Do you really want to spawn all those NPCs? It's quite alot (%d entities in %d groups)" % (len(lootEntities), len(entityDict))}, uiconst.YESNO) == uiconst.ID_YES:
            filename = '%s.%s.%s' % (self.GetTimestamp(), label, FILE_ENTITIES)
            TARGET = os.path.join(self.GetInsiderDir(), filename)
            f = blue.classes.CreateInstance('blue.ResFile')
            if not f.Open(TARGET, 0):
                f.Create(TARGET)
            f.Write('Status\tLoot\tEmpty\tTypeID\tEntity Type\tWreck Type\tEntity Name\tWreck Name\tWreck State')
            f.Write('\r\n')
            for entity in lootEntities:
                dudSpawn = False
                if cfg.invgroups.Get(cfg.invtypes.Get(entity).groupID).anchored:
                    respawnEntities.append(entity)
                    print 'appended entity %s' % entity
                    continue
                else:
                    blue.pyos.synchro.SleepSim(1000)
                    sm.GetService('slash').SlashCmd('/entity deploy 10 %d' % entity)
                blue.pyos.synchro.SleepSim(1000)
                sm.GetService('slash').SlashCmd('/nuke')
                blue.pyos.synchro.SleepSim(2000)
                wrecks = []
                count = 1000
                while not wrecks and count:
                    count -= 1
                    bp = sm.GetService('michelle').GetBallpark()
                    for ballID in bp.balls.keys():
                        item = bp.GetInvItem(ballID)
                        if item and item.groupID in (const.groupWreck, const.groupCargoContainer):
                            wrecks.append(item.itemID)

                if not wrecks:
                    blue.pyos.synchro.SleepSim(5000)
                    bp = sm.GetService('michelle').GetBallpark()
                    for ballID in bp.balls.keys():
                        item = bp.GetInvItem(ballID)
                        if item and item.groupID in (const.groupWreck, const.groupCargoContainer):
                            wrecks.append(item.itemID)

                if not wrecks:
                    dudSpawn = True
                emptyWreck = int()
                okWreck = int()
                entityType = cfg.invgroups.Get(cfg.invtypes.Get(entity).groupID).name
                entityName = cfg.invtypes.Get(entity).name
                idealWreckName = '%s Wreck' % entityName
                if not dudSpawn:
                    actualWreckName = 'None'
                    for wreckID in wrecks:
                        empty = sm.GetService('state').CheckWreckEmpty(bp.GetInvItem(wreckID))
                        if empty:
                            emptyWreck += 1
                        else:
                            okWreck += 1
                        actualWreckName = cfg.evelocations.Get(wreckID).name
                        wreckType = cfg.invtypes.Get(sm.GetService('michelle').GetBallpark().GetInvItem(wreckID).typeID).name

                    wreckNameState = 'Error'
                    if idealWreckName == actualWreckName:
                        wreckNameState = 'OK'
                    try:
                        if okWreck > emptyWreck:
                            f.Write('OK')
                            f.Write('\t%s' % okWreck)
                            f.Write('\t%s' % emptyWreck)
                            f.Write('\t%s' % entity)
                            f.Write('\t%s' % entityType.encode('utf8'))
                            f.Write('\t%s' % wreckType.encode('utf8'))
                            f.Write('\t%s' % entityName.encode('utf8'))
                            f.Write('\t%s' % actualWreckName.encode('utf8'))
                            f.Write('\t%s' % wreckNameState)
                            f.Write('\r\n')
                        elif not okWreck:
                            f.Write('Critical')
                            f.Write('\t-\t-\t%s' % entity)
                            f.Write('\t%s' % entityType.encode('utf8'))
                            f.Write('\t%s' % wreckType.encode('utf8'))
                            f.Write('\t%s' % entityName.encode('utf8'))
                            f.Write('\t%s' % actualWreckName.encode('utf8'))
                            f.Write('\t%s' % wreckNameState)
                            f.Write('\r\n')
                        else:
                            f.Write('Warning')
                            f.Write('\t%s' % okWreck)
                            f.Write('\t%s' % emptyWreck)
                            f.Write('\t%s' % entity)
                            f.Write('\t%s' % entityType.encode('utf8'))
                            f.Write('\t%s' % wreckType.encode('utf8'))
                            f.Write('\t%s' % entityName.encode('utf8'))
                            f.Write('\t%s' % actualWreckName.encode('utf8'))
                            f.Write('\t%s' % wreckNameState)
                            f.Write('\r\n')
                    except:
                        sys.exc_clear()
                        f.Write('\r\n')
                        f.Write('Fail')
                        f.Write('\t-\t-\t%s' % entity)
                        f.Write('\t%s' % entityType.encode('utf8'))
                        f.Write('\t%s' % entityName.encode('utf8'))
                        f.Write('\r\n')

                else:
                    f.Write('Null')
                    f.Write('\t-\t-\t%s' % entity)
                    f.Write('\t%s' % entityType.encode('utf8'))
                    f.Write('\t%s' % entityName.encode('utf8'))
                    f.Write('\tNone\tNone\tNone')
                    f.Write('\r\n')
                self.HealRemove(const.groupWreck)
                self.HealRemove(const.groupCargoContainer)

            if respawnEntities:
                f.Write('\r\n')
                f.Write('The following entities respawn over time and were not tested:')
                f.Write('\r\n')
                for entity in respawnEntities:
                    entityType = cfg.invgroups.Get(cfg.invtypes.Get(entity).groupID).name
                    entityName = cfg.invtypes.Get(entity).name
                    f.Write('Unspawned')
                    f.Write('\t\t\t%s' % entity)
                    f.Write('\t%s' % entityType.encode('utf8'))
                    f.Write('\t%s' % entityName.encode('utf8'))
                    f.Write('\r\n')

        try:
            f.Close()
        except:
            sys.exc_clear()

    def RegionGateTest(self, constellation = None, *args):

        def Populate(areaOfInterest):
            data = {}
            systems = []
            mapSvc = sm.GetService('map')
            systemmapSvc = sm.GetService('systemmap')
            if areaOfInterest.__class__ != list:
                areaOfInterest = [areaOfInterest]
            for constellation in areaOfInterest:
                systems += mapSvc.GetChildren(constellation)

            for system in systems:
                title = 'Examining Systems...'
                systemName = cfg.evelocations.Get(system).name
                constellationID = cfg.evelocations.Get(mapSvc.GetParent(system))
                constellationName = cfg.evelocations.Get(constellationID).name
                regionID = cfg.evelocations.Get(mapSvc.GetParent(constellationID.id))
                regionName = cfg.evelocations.Get(regionID).name
                text = '%s, %s, %s' % (systemName, constellationName, regionName)
                Progress(title, text, systems.index(system), len(systems))
                systemItems = systemmapSvc.GetSolarsystemData(system)
                systemItems = systemItems.Index('itemID')
                stargates = {}
                for object in systemItems:
                    item = systemItems[object]
                    if cfg.invtypes.Get(item.typeID).groupID in (const.groupStargate,):
                        stargates[item.itemName] = {'gateID': item.itemID,
                         'destGateID': item.destinations[0]}

                data[system] = stargates

            Progress('Mapping Complete!', 'Done!', 1, 1)
            return data

        def Wait(count, *args):
            blue.pyos.synchro.SleepSim(count * 1000)

        sysCount = int()
        jumpCount = int()
        regionData = Populate(constellation)
        for k, v in regionData.iteritems():
            sysCount += 1
            jumpCount += len(v)

        approxDuration = jumpCount * 0.5
        if uicore.Message('CustomQuestion', {'header': 'Travel the universe?',
         'question': 'Do you really want to visit all the gates in this region? It will take approximately %d minutes.' % approxDuration}, uiconst.YESNO) == uiconst.ID_YES:
            filename = '%s.%s.%s' % (self.GetTimestamp(), cfg.evelocations.Get(session.regionid).name, FILE_GATES)
            f = blue.classes.CreateInstance('blue.ResFile')
            TARGET = os.path.join(self.GetInsiderDir(), filename)
            if not f.Open(TARGET, 0):
                f.Create(TARGET)
            gok = int()
            gfail = int()
            sok = int()
            sfail = int()
            stargates = []
            self.WaitOutSession()
            for system, gates in regionData.iteritems():
                f.Write('%s' % cfg.evelocations.Get(system).name.encode('utf8'))
                f.Write('\r\n')
                for name, info in gates.iteritems():
                    sysdest = name.split('(')[1].split(')')[0]
                    f.Write('-> %s' % sysdest.encode('utf8'))
                    f.Write('\r\n')
                    sysdestID = sm.RemoteSvc('lookupSvc').LookupLocationsByGroup(const.groupSolarSystem, sysdest)
                    for each in sysdestID:
                        sysdestID = each.itemID

                    Wait(5)
                    self.TravelToLocation(system)
                    Wait(5)
                    bp = sm.GetService('michelle').GetBallpark()
                    for ballID in bp.balls.keys():
                        item = bp.GetInvItem(ballID)
                        if item and item.groupID in (const.groupStargate,):
                            stargates.append(item.itemID)

                    if info['gateID'] in stargates:
                        self.TravelToLocation(info['gateID'])
                        self.WaitOutSession()
                        Wait(5)
                        try:
                            sm.GetService('sessionMgr').PerformSessionChange('autopilot', sm.GetService('michelle').GetRemotePark().CmdStargateJump, info['gateID'], info['destGateID'], session.shipid)
                            Wait(10)
                        except:
                            sys.exc_clear()
                            f.Write('\t\tERROR: Jump failed')
                            f.Write('\r\n')

                    stargates = []
                    bp = sm.GetService('michelle').GetBallpark()
                    for ballID in bp.balls.keys():
                        item = bp.GetInvItem(ballID)
                        if item and item.groupID in (const.groupStargate,):
                            data = sm.GetService('tactical').GetEntryData(item, bp.GetBall(item.itemID))
                            distance = data.ball().surfaceDist
                            stargates.append(item.itemID)

                    if info['destGateID'] in stargates:
                        item = bp.GetInvItem(info['destGateID'])
                        distance = sm.GetService('tactical').GetEntryData(item, bp.GetBall(item.itemID)).ball().surfaceDist
                        if distance < 50000:
                            gok += 1
                            f.Write('\t\tGate: OK')
                            f.Write('\r\n')
                        else:
                            f.Write('\t\tGate: There, but distant')
                            f.Write('\r\n')
                    else:
                        gfail += 1
                        f.Write('\t\tGate: FAIL')
                        f.Write('\r\n')
                    if cfg.evelocations.Get(session.locationid).name == sysdest:
                        sok += 1
                        f.Write('\t\tSystem: OK')
                        f.Write('\r\n')
                    else:
                        sfail += 1
                        f.Write('\t\tSystem: FAIL')
                        f.Write('\r\n')
                    self.WaitOutSession()

                f.Write('-----------------')
                f.Write('\r\n')

            f.Write('Gates:')
            f.Write('\r\n')
            f.Write('\tOK: %s' % gok)
            f.Write('\r\n')
            f.Write('\tFAIL: %s' % gfail)
            f.Write('\r\n')
            f.Write('Systems:')
            f.Write('\r\n')
            f.Write('\tOK: %s' % sok)
            f.Write('\r\n')
            f.Write('\tFAIL: %s' % sfail)
            f.Write('\r\n')
            f.Close()

    def FacWarStatus(self, *args):
        facWar = sm.RemoteSvc('facWarMgr')
        map = sm.GetService('map')
        systems = facWar.GetAllSolarSystemsData()
        f = blue.classes.CreateInstance('blue.ResFile')
        filename = '%s.%s' % (self.GetTimestamp(), FILE_FWREPORT)
        TARGET = os.path.join(self.GetInsiderDir(), filename)
        if not f.Open(TARGET, 0):
            f.Create(TARGET)
        f.Write('System ID\tSystem Name\tConstellation ID\tConstellation Name\tRegion ID\tRegion Name\tOccupier\tSovereignty\tConquered')
        f.Write('\r\n')
        for k, v in systems.iteritems():
            systemID = k
            systemName = cfg.evelocations.Get(systemID).name
            constellationID = map.GetParent(systemID)
            constellationName = cfg.evelocations.Get(constellationID).name
            regionID = map.GetParent(constellationID)
            regionName = cfg.evelocations.Get(regionID).name
            occupierName = cfg.eveowners.Get(v['occupierID']).name
            factionName = cfg.eveowners.Get(v['factionID']).name
            state = v['occupierID'] == v['factionID']
            f.Write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (systemID,
             systemName,
             constellationID,
             constellationName,
             regionID,
             regionName,
             occupierName,
             factionName,
             not state))
            f.Write('\r\n')

        try:
            f.Close()
        except:
            sys.exc_clear()

    def StoreRegionData(self, *args):
        constellations = []
        systems = []
        constellations = sm.GetService('map').GetChildren(session.regionid)
        for sys in constellations:
            systems += sm.GetService('map').GetChildren(sys)

        regionName = cfg.evelocations.Get(session.regionid).name
        filename = '%s.%s.%s' % (self.GetTimestamp(), regionName, FILE_STELLAR)
        f = blue.classes.CreateInstance('blue.ResFile')
        TARGET = os.path.join(self.GetInsiderDir(), filename)
        if not f.Open(TARGET, 0):
            f.Create(TARGET)
        f.Write('Object itemID\tObject typeID\tObject Type\tName\tLocation ID\tDestination\tx\ty\tz\tObject orbitID')
        f.Write('\r\n')
        for system in systems:
            title = 'Examining Systems...'
            systemName = cfg.evelocations.Get(system).name
            constellationID = cfg.evelocations.Get(sm.GetService('map').GetParent(system))
            constellationName = cfg.evelocations.Get(constellationID).name
            text = '%s, %s' % (systemName, constellationName)
            Progress(title, text, systems.index(system), len(systems))
            systemItems = sm.GetService('systemmap').GetSolarsystemData(system)
            for object in systemItems:
                f.Write('%s' % object.itemID)
                f.Write('\t%s' % object.typeID)
                f.Write('\t%s' % cfg.invtypes.Get(object.typeID).name.encode('utf8'))
                f.Write('\t%s' % object.itemName.encode('utf8'))
                f.Write('\t%s' % object.locationID)
                f.Write('\t%s' % object.destinations.__str__())
                f.Write('\t%g' % object.x)
                f.Write('\t%g' % object.y)
                f.Write('\t%g' % object.z)
                f.Write('\t%s' % object.orbitID)
                f.Write('\r\n')

        try:
            f.Close()
        except:
            sys.exc_clear()

        Progress('Mapping Complete!', 'Done!', 1, 1)

    def RegionBeltTest(self, constellation = None, *args):

        def Populate(areaOfInterest):
            systems = []
            belts = []
            if areaOfInterest.__class__ != list:
                areaOfInterest = [areaOfInterest]
            for constellation in areaOfInterest:
                systems += sm.GetService('map').GetChildren(constellation)

            for system in systems:
                title = 'Examining Systems...'
                systemName = cfg.evelocations.Get(system).name
                constellationID = cfg.evelocations.Get(sm.GetService('map').GetParent(system))
                constellationName = cfg.evelocations.Get(constellationID).name
                regionID = cfg.evelocations.Get(sm.GetService('map').GetParent(constellationID.id))
                regionName = cfg.evelocations.Get(regionID).name
                text = '%s, %s, %s' % (systemName, constellationName, regionName)
                Progress(title, text, systems.index(system), len(systems))
                systemItems = sm.GetService('systemmap').GetSolarsystemData(system)
                systemItems = systemItems.Index('itemID')
                for object in systemItems:
                    item = systemItems[object]
                    if cfg.invtypes.Get(item.typeID).groupID in (const.groupAsteroidBelt,):
                        belts.append(item.itemID)

            Progress('Mapping Complete!', 'Done!', 1, 1)
            return (belts, systems)

        def Wait(count, *args):
            blue.pyos.synchro.SleepSim(count * 1000)

        if not constellation:
            return
        regionBeltData, regionSystemData = Populate(constellation)
        sysCount = len(regionSystemData)
        approxDuration = sysCount * 0.5
        if uicore.Message('CustomQuestion', {'header': 'Travel the universe?',
         'question': 'Do you really want to visit all the belts in this region? It will take approximately %d minutes.' % approxDuration}, uiconst.YESNO) == uiconst.ID_YES:
            filename = '%s.%s.%s' % (self.GetTimestamp(), cfg.evelocations.Get(session.regionid).name, FILE_BELTS)
            f = blue.classes.CreateInstance('blue.ResFile')
            TARGET = os.path.join(self.GetInsiderDir(), filename)
            if not f.Open(TARGET, 0):
                f.Create(TARGET)
            asteroidGroups = []
            for asteroid in cfg.invgroups:
                if asteroid.categoryID in (const.categoryAsteroid,):
                    asteroidGroups.append(asteroid.id)

            f.Write('Solarsystem itemID\tSolarsystem Name\tBelt itemID\tBelt Name\tAsteroid Types Present')
            f.Write('\r\n')
            for belt in regionBeltData:
                survey = []
                try:
                    self.TravelToLocation(belt)
                except:
                    sys.exc_clear()
                    self.WaitOutSession()
                    self.TravelToLocation(belt)

                Wait(5)
                bp = sm.GetService('michelle').GetBallpark()
                gotBelt = False
                bpCount = int()
                while not gotBelt:
                    for ballID in bp.balls.keys():
                        item = bp.GetInvItem(ballID)
                        if item and item.itemID == belt:
                            gotBelt = True
                            break

                    bpCount += 1
                    if bpCount > 10:
                        break
                    Wait(5)
                    bp = sm.GetService('michelle').GetBallpark()

                if gotBelt:
                    for ballID in bp.balls.keys():
                        item = bp.GetInvItem(ballID)
                        if item and item.groupID in asteroidGroups:
                            if survey.__contains__(item.typeID):
                                pass
                            else:
                                survey.append(item.typeID)

                    if not survey:
                        Wait(5)
                        bp = sm.GetService('michelle').GetBallpark()
                        for ballID in bp.balls.keys():
                            item = bp.GetInvItem(ballID)
                            if item and item.groupID in asteroidGroups:
                                if survey.__contains__(item.typeID):
                                    pass
                                else:
                                    survey.append(item.typeID)

                    survey.sort()
                    f.Write('%s' % session.locationid)
                    f.Write('\t%s' % cfg.evelocations.Get(session.solarsystemid2).name.encode('utf8'))
                    f.Write('\t%s' % belt)
                    f.Write('\t%s' % cfg.evelocations.Get(belt).name.encode('utf8'))
                    f.Write('\t')
                    for asteroid in survey:
                        f.Write('%s, ' % cfg.invtypes.Get(asteroid).name.encode('utf8'))

                    f.Write('\r\n')

            try:
                f.Close()
            except:
                sys.exc_clear()

    def _V3TestingLoop(self, path):
        myShip = sm.GetService('michelle').GetBallpark().GetBall(eve.session.shipid)
        myShip.model.display = False
        f = open(path, 'rt')
        fc = f.readlines()
        errorCount = 0
        i = 1
        scene = sm.StartService('sceneManager').GetRegisteredScene('default')
        if scene is not None:
            for li in fc:
                log.LogError('LOADING ' + str(i) + ' of ' + str(len(fc)) + ' : ' + str(int(li)))
                redFile = util.GraphicFile(int(li))
                log.LogError(redFile)
                if redFile is None:
                    errorCount += 1
                else:
                    ship = trinity.Load(redFile)
                    scene.objects.append(ship)
                    blue.synchro.Sleep(2000)
                    scene.objects.remove(ship)
                i += 1

        log.LogError('FINISHED V3 testing...')
        log.LogError('DETECTED at least ' + str(errorCount) + ' problems!')
        myShip.model.display = True

    def CycleNebulas(self, *args):
        CycleNebulaPanel(parent=uicore.layer.main, name='CycleNebulaPanel', caption='Cycle Nebulas')

    def V3Testing(self, *args):
        log.LogError('Starting V3 testing...')
        dlgRes = uix.GetFileDialog(fileExtensions=['.txt'], multiSelect=False, selectionType=uix.SEL_FILES)
        if dlgRes is not None:
            scriptPath = dlgRes.Get('files')[0]
            log.LogWarn('script: ' + str(scriptPath))
            uthread.new(self._V3TestingLoop, str(scriptPath))

    def Automated(self, *args):
        fw = []
        allIDs = []
        usedIDs = []
        spawnMenu = []
        entitySpawnGroups = ['Asteroid Angel Cartel',
         'Asteroid Blood Raiders',
         'Asteroid Guristas',
         'Asteroid Rogue Drone',
         "Asteroid Sansha's Nation",
         'Asteroid Serpentis',
         'Deadspace Angel Cartel',
         'Deadspace Blood Raiders',
         'Deadspace Guristas',
         'Deadspace Overseer',
         'Deadspace Rogue Drone',
         "Deadspace Sansha's Nation",
         'Deadspace Serpentis',
         'Mission Amarr Empire',
         'Mission CONCORD',
         'Mission Caldari State',
         'Mission Drone',
         'Mission Gallente Federation',
         'Mission Generic',
         'Mission Khanid',
         'Mission Minmatar Republic',
         'Mission Mordu',
         'Mission Thukker',
         'Storyline',
         'Other']
        noLootEntities = [const.groupConcordDrone, const.groupFactionDrone, const.groupPoliceDrone]
        dontSpawn = [const.groupBillboard,
         const.groupSentryGun,
         const.groupCapturePointTower,
         const.groupProtectiveSentryGun,
         const.groupCustomsOfficial]
        entitiesDict = {}
        nameDict = {}
        entityByGroup = {}
        for group in cfg.invgroups:
            if group.categoryID in (const.categoryEntity,):
                if group.groupID not in noLootEntities:
                    if group.groupID not in dontSpawn:
                        entitiesDict[group.groupID] = []

        for type in cfg.invtypes:
            if type.groupID in entitiesDict:
                entitiesDict[type.groupID].append(type.typeID)

        for id in entitiesDict.iterkeys():
            nameDict[id] = [cfg.invgroups.Get(id).name]

        for group in entitySpawnGroups:
            for id, name in nameDict.iteritems():
                if name[0].lower().startswith(group.lower()):
                    if entityByGroup.has_key(group):
                        entityByGroup[group].append(id)
                        usedIDs.append(id)
                        allIDs.append(id)
                    else:
                        entityByGroup[group] = [id]
                        usedIDs.append(id)
                        allIDs.append(id)

        for id in nameDict.iterkeys():
            if id not in usedIDs:
                if entityByGroup.has_key('Other'):
                    entityByGroup['Other'].append(id)
                    allIDs.append(id)
                else:
                    entityByGroup['Other'] = [id]
                    allIDs.append(id)

        for displayName, idList in entityByGroup.iteritems():
            spawnMenu.append((displayName, lambda label = displayName, ids = idList: self.EntitySpawn(label, ids)))

        spawnMenu.sort()
        spawnMenu.append(None)
        spawnMenu.append(('No loot entities', lambda label = 'noloot', ids = noLootEntities: self.EntitySpawn(label, ids)))
        spawnMenu.append(None)
        spawnMenu.append(('<color=0xffff8080>All', lambda label = 'All', ids = allIDs: self.EntitySpawn(label, ids)))
        beltMenu = []
        constellationInRegion = cfg.mapRegionCache[session.regionid].constellationIDs
        for constellationID in constellationInRegion:
            label = cfg.evelocations.Get(constellationID).name
            beltMenu.append((label, lambda ids = constellationID: self.RegionBeltTest(ids)))

        beltMenu.sort()
        beltMenu.append(None)
        beltMenu.append(('<color=0xffff8080>All', lambda ids = constellationInRegion: self.RegionBeltTest(ids)))
        gateMenu = []
        for constellationID in constellationInRegion:
            label = cfg.evelocations.Get(constellationID).name
            gateMenu.append((label, lambda ids = constellationID: self.RegionGateTest(ids)))

        gateMenu.sort()
        gateMenu.append(None)
        gateMenu.append(('<color=0xffff8080>All', lambda ids = constellationInRegion: self.RegionGateTest(ids)))
        (fw.append(('FW Bunker Locations', [('Amarr - Positive', lambda : self.RegionBunkerTest(True, 'Amarr')),
           ('Amarr - Negative', lambda : self.RegionBunkerTest(False, 'Amarr')),
           None,
           ('Caldari - Positive', lambda : self.RegionBunkerTest(True, 'Caldari')),
           ('Caldari - Negative', lambda : self.RegionBunkerTest(False, 'Caldari')),
           None,
           ('Gallente - Positive', lambda : self.RegionBunkerTest(True, 'Gallente')),
           ('Gallente - Negative', lambda : self.RegionBunkerTest(False, 'Gallente')),
           None,
           ('Minmatar - Positive', lambda : self.RegionBunkerTest(True, 'Minmatar')),
           ('Minmatar - Negative', lambda : self.RegionBunkerTest(False, 'Minmatar')),
           None,
           ('<color=0xffff8080>All - Positive', lambda : self.RegionBunkerTest(True, 'All')),
           ('<color=0xffff8080>All - Negative', lambda : self.RegionBunkerTest(False, 'All'))])),)
        fw.append(None)
        fw.append(('NPC Loot Test', spawnMenu))
        fw.append(None)
        fw.append(('Belt Contents Survey', beltMenu))
        fw.append(('Gate Jump Test', gateMenu))
        fw.append(None)
        fw.append(('Client ReConnection Loop', lambda : form.ConnLoop.Open()))
        fw.append(None)
        fw.append(('Stellar Objects Report', lambda : self.StoreRegionData()))
        fw.append(('FacWar Status Report', lambda : self.FacWarStatus()))
        fw.append(None)
        fw.append(('Spambot 2000', lambda : sm.GetService('cspam').Show()))
        return fw

    def ExpoMenu(self, *args):
        defaults = [(60005659,
          1,
          True,
          'Set as Team 1, Player 1'),
         (60005659,
          4,
          True,
          'Set as Team 1, Player 2'),
         (60005659,
          6,
          True,
          'Set as Team 1, Player 3'),
         None,
         (60005595,
          2,
          True,
          'Set as Team 2, Player 1'),
         (60005595,
          5,
          True,
          'Set as Team 2, Player 2'),
         (60005595,
          7,
          True,
          'Set as Team 2, Player 3'),
         None,
         (60005659,
          3,
          False,
          'Set as Administrator')]
        m = []
        n = []

        def ExpoPrefsSet(station, forcestation, setup):
            if forcestation:
                if util.IsStation(station):
                    prefs.SetValue('expoStartLocation', station)
                    prefs.SetValue('expoFittingID', setup)
                else:
                    uicore.Message('CustomNotify', {'notify': 'The stationID %s is invalid.' % station})
                    return
            else:
                prefs.SetValue('expoStartLocation', station)
                prefs.SetValue('expoFittingID', setup)

        for entry in defaults:
            if entry is None:
                n.append(None)
            else:
                sID, eID, force, text = entry
                n.append((text, ExpoPrefsSet, (sID, force, eID)))

        m.append(('Setup characters', n))
        return m

    def OnSessionChanged(self, isRemote, sess, change):
        debugRenderJob = None
        for job in trinity.renderJobs.recurring:
            if job.name == 'DebugRender':
                debugRenderJob = job
                break

        if debugRenderJob:
            trinity.renderJobs.recurring.remove(debugRenderJob)

    def CreateDebugRenderer(self):
        job = getattr(self, 'DebugRenderJob', None)
        if not job:
            import GameWorld
            g = sm.GetService('gameWorldClient').GetGameWorld(session.worldspaceid)
            render_job = trinity.CreateRenderJob('DebugRender')
            callBackStep = trinity.TriStepPythonCB()
            callBackStep.SetCallback(g.PhysXRenderDebugInfo)
            render_job.steps.append(callBackStep)
            dr = trinity.TriStepRenderDebug()
            render_job.steps.append(dr)
            sm.services['sceneManager'].incarnaRenderJob.AddStep('RENDER_INFO', trinity.TriStepRunJob(render_job))
            GameWorld.SetDebugRenderer(dr)
            setattr(self, 'DebugRenderJob', True)

    def IncarnaMenu(self, *args):
        m = []
        movementItems = []
        debuggingEntries = []
        cameraEntries = []
        entitiesEntries = []
        graphicsEntries = []
        athenaEntries = []

        def ToggleDebugRenderClient():
            debugRender = sm.GetService('debugRenderClient')
            debugRender.SetDebugRendering(not debugRender.GetDebugRendering())

        debuggingEntries.append(('Toggle debugRenderClient Rendering', ToggleDebugRenderClient))

        def ConnectToPhysXDebugger():
            gw = sm.GetService('gameWorldClient').GetGameWorld(session.worldspaceid)
            gw.ConnectToRemoteVisualDebugger('localhost', 5425)

        debuggingEntries.append(('Connect to PhysXDebugger', ConnectToPhysXDebugger))

        def ConnectToTelemetry():
            blue.statistics.StartTelemetry('localhost')

        debuggingEntries.append(('Start Telemetry', ConnectToTelemetry))

        def StopTelemetry():
            blue.statistics.StopTelemetry()

        debuggingEntries.append(('Stop Telemetry', StopTelemetry))

        def OpenAIDebugWindow():
            self.CreateDebugRenderer()
            AIDebugWindow(parent=uicore.layer.main, name='AIDebugWindow', caption='AI Debug', windowID='AIDebugWindow')

        m.append(('Open AI Debug', OpenAIDebugWindow))

        def ChangeCameraZoom():
            cameras.DebugChangeCameraSettingsWindow.Open()

        cameraEntries.append(('Change camera settings', ChangeCameraZoom))

        def ToogleProximityTreeRendering():
            self.CreateDebugRenderer()
            g = sm.GetService('gameWorldClient').GetGameWorld(session.worldspaceid)
            current = getattr(self, 'ProximityTreeCurrentlyRendering', False)
            if current:
                g.ProximityTreeDebugRendering = 0
                setattr(self, 'ProximityTreeCurrentlyRendering', False)
            else:
                g.ProximityTreeDebugRendering = 1
                setattr(self, 'ProximityTreeCurrentlyRendering', True)

        debuggingEntries.append(('Toogle Proximity Rendering', ToogleProximityTreeRendering))

        def ToggleAvatarCollisionVisualization():
            player = sm.GetService('entityClient').GetPlayerEntity()
            player.GetComponent('animation').controller.ToggleDebugRenderCollisionCapsules()

        debuggingEntries.append(('Toggle Avatar Collision Visualization', ToggleAvatarCollisionVisualization))

        def ToggleAvatarControlParameterVisualization():
            player = sm.GetService('entityClient').GetPlayerEntity()
            player.GetComponent('animation').controller.ToggleDebugRenderControlParameters()

        debuggingEntries.append(('Toggle Avatar Animation Control Parameter Visualization', ToggleAvatarControlParameterVisualization))

        def ToggleAvatarRendering():
            sm.GetService('paperDollClient').ToogleRenderAvatars()

        graphicsEntries.append(('Toggle Avatar Rendering', ToggleAvatarRendering))

        def TeleportToSafeSpot():
            wsc = sm.GetService('worldSpaceClient')
            ec = sm.GetService('entityClient')
            safespot = wsc.GetWorldSpaceSafeSpot(session.worldspaceid)
            if ec.IsClientSideOnly(session.worldspaceid):
                ec.GetPlayerEntity().GetComponent('position').position = safespot[0]
            else:
                ret = sm.RemoteSvc('movementServer').RequestTeleport(safespot[0], safespot[1])
                if not ret:
                    uicore.Message('CustomNotify', {'notify': 'Teleport failed'})

        movementItems.append(('Teleport To Safespot', TeleportToSafeSpot))

        def ShowPathingToggle():
            device = trinity.device
            for job in device.scheduledRecurring:
                if job.name == 'DebugKynapseRender':
                    device.scheduledRecurring.remove(job)
                    return

            dr = trinity.TriStepRenderDebug()
            dr.autoClear = True
            render_job = trinity.CreateRenderJob('DebugKynapseRender')
            render_job.steps.append(dr)
            render_job.ScheduleRecurring()
            gw = sm.GetService('gameWorldClient').GetGameWorld(session.worldspaceid)
            gw.DrawKynapseInfo(dr)

        movementItems.append(('Toggle PathData Display', ShowPathingToggle))

        def ToggleMaterialCheck():
            testThreadWeakRef = getattr(self, 'testThreadWeakRef', None)
            if testThreadWeakRef is None or testThreadWeakRef() is None:
                testThread = uthread.new(_MaterialCheckLoop)
                testThread.context = 'MaterialHackCheck'
                self.testThreadWeakRef = weakref.ref(testThread)
                sm.GetService('debugRenderClient').SetDebugRendering(True)
            else:
                testThreadWeakRef().kill()

        def _MaterialCheckLoop():
            namesByID = {}
            for name, ID in materialTypes.MATERIAL_NAMES.iteritems():
                namesByID[ID] = name

            while True:
                entityClient = sm.GetService('entityClient')
                gameWorldClient = sm.GetService('gameWorldClient')
                entity = entityClient.FindEntityByID(session.charid)
                if not entity:
                    continue
                positionComponent = entity.GetComponent('position')
                if not positionComponent:
                    continue
                gameWorld = gameWorldClient.GetGameWorld(session.worldspaceid)
                if not gameWorld:
                    continue
                topPosition = (positionComponent.position[0], positionComponent.position[1] + 0.1, positionComponent.position[2])
                bottomPosition = (positionComponent.position[0], positionComponent.position[1] - 0.1, positionComponent.position[2])
                hitResult = gameWorld.MultiHitLineTestWithMaterials(topPosition, bottomPosition)
                sm.GetService('debugRenderClient').RenderRay(topPosition, bottomPosition, time=250)
                if hitResult:
                    print len(hitResult), 'Material Found! ID:', hitResult[0][2], ', Name:', namesByID[hitResult[0][2]]
                    sm.GetService('debugRenderClient').RenderSphere(hitResult[0][0], 0.01, time=250)
                    playerEntity = sm.GetService('entityClient').GetPlayerEntity()
                    if playerEntity and playerEntity.HasComponent('audioEmitter') and playerEntity.audioEmitter.emitter is not None:
                        playerEntity.audioEmitter.emitter.SetSwitch(u'Materials', namesByID[hitResult[0][2]])
                        playerEntity.audioEmitter.emitter.SendEvent(u'footfall_loud_play')
                else:
                    playerEntity = sm.GetService('entityClient').GetPlayerEntity()
                    if playerEntity and playerEntity.HasComponent('audioEmitter') and playerEntity.audioEmitter.emitter is not None:
                        print 'no material found'
                        playerEntity.audioEmitter.emitter.SetSwitch(u'Materials', u'Invalid')
                        playerEntity.audioEmitter.emitter.SendEvent(u'footfall_loud_play')
                blue.synchro.SleepWallclock(500)

        graphicsEntries.append(('Toggle Material Check', ToggleMaterialCheck))

        def OpenEntityBrowser():
            uicls.EntityBrowser(parent=uicore.layer.main)

        entitiesEntries.append(('Open Entity Browser', OpenEntityBrowser))

        def OpenAnimationDebugWindow():
            AnimationDebugWindow(parent=uicore.layer.main, name='AnimationDebugWindow', caption='Animation Debug', windowID='AnimationDebugWindow')

        movementItems.append(('Open Animation Debug', OpenAnimationDebugWindow))

        def ToggleFlyMode():
            import GameWorld
            player = sm.GetService('entityClient').GetPlayerEntity()
            camClient = sm.GetService('cameraClient')
            activeCam = camClient.GetActiveCamera()
            if activeCam.__class__ is cameras.FlyModeCamera:
                camClient.PopActiveCamera()
                player.GetComponent('movement').moveModeManager.PushMoveMode(GameWorld.PlayerInputMode())
            else:
                camClient.PushActiveCamera(cameras.FlyModeCamera())
                player.GetComponent('movement').moveModeManager.PushMoveMode(GameWorld.IdleMode())

        cameraEntries.append(('Toggle Fly Mode Camera', ToggleFlyMode))

        def OpenDebugSelectionWindow():
            DebugSelectionWindow(parent=uicore.layer.main, name='DebugSelectionWindow', caption='Debug Selection', windowID='DebugSelectionWindow')

        debuggingEntries.append(('Open Debug Selection', OpenDebugSelectionWindow))

        def OpenZactionPanel():
            uicls.ZactionHackWindow.Open()

        m.append(('Open Zaction Panel', OpenZactionPanel))

        def ToggleADM():
            import GameWorld
            player = sm.GetService('entityClient').GetPlayerEntity()
            mode = player.movement.avatar.GetActiveMoveMode()
            if isinstance(mode, GameWorld.KBMouseMode):
                mode.isAnimationDriven = not mode.isAnimationDriven
            if mode.isAnimationDriven:
                animClient = sm.GetService('animationClient')
                animClient.UnRegisterComponent(player, player.animation)
                animClient.CreateComponent('animation', {})
                animClient.PrepareComponent(0, player.entityID, player.animation)
                animClient.SetupComponent(player, player.animation)
                player.paperdoll.doll.avatar.animationUpdater = player.animation.updater
                player.movement.avatar.animation = player.animation.updater
                player.game.GetAnimObject().animController = player.animation.controller
            else:
                player.paperdoll.doll.avatar.animationUpdater = GameWorld.GWAnimation(None)
                player.animation.controller.animationNetwork = None
                player.movement.avatar.animation = None
                player.game.GetAnimObject().animController = None

        movementItems.append(('Toggle Animation Driven Movement', ToggleADM))

        def InitializeLiveLink():
            import GameWorld
            if getattr(self, 'liveLinkRef', None) is None:
                self.liveLinkRef = GameWorld.LiveLinkManager()
                self.liveLinkRef.InitLiveLinkManager()

        def ConnectTargetToLiveLink():
            InitializeLiveLink()
            ent = sm.GetService('debugSelectionClient').GetSelectedEntity()
            if ent.GetComponent('animation') is not None:
                network = ent.animation.controller.animationNetwork
                self.liveLinkRef.AddNetDef(network)
                self.liveLinkRef.AddNetwork(network, ent.info.name)

        movementItems.append(('Add To LiveLink', ConnectTargetToLiveLink))

        def IncrementTestCounter():
            server = sm.RemoteSvc('netStateServer')
            server.IncrementTestCounter()

        m.append(('Increment Test Counter', IncrementTestCounter))

        def TimeControlWindow():
            uicls.TimeControlWindow.Open()

        m.append(('Time Control Window', TimeControlWindow))

        def ToggleStickPhysXController():
            sm.GetService('movementClient').ToggleCharacterController()

        movementItems.append(('Toggle Pogo', ToggleStickPhysXController))

        def ToggleExtrapolation():
            sm.GetService('movementClient').ToggleExtrapolation()

        movementItems.append(('Toggle Extrapolation', ToggleExtrapolation))

        def SwitchAttitude():
            player = sm.GetService('entityClient').GetPlayerEntity()
            ac = player.GetComponent('animation')
            idx = ac.updater.network.GetAnimationSetIndex()
            ac.updater.network.SetAnimationSetIndex((idx + 4) % 16)

        movementItems.append(('Switch Attitude', SwitchAttitude))

        def ReloadActionTree():
            sm.RemoteSvc('zactionServer').QA_ResetTree()

        movementItems.append(('Reload Action tree (For server and all connected clients)', ReloadActionTree))

        def OpenAthenaServerLogWindow():
            wnd = uicore.registry.GetWindow('combatLogWindowServer')
            if wnd and not wnd.destroyed:
                wnd.Close()
            else:
                wnd = CombatLogWindow(service=sm.RemoteSvc('zactionLoggerSvc'), parent=uicore.layer.main, name='combatLogWindowServer', caption='athena log - server', windowID='combatLogWindowServer')

        athenaEntries.append(('Open Athena Server Log', OpenAthenaServerLogWindow))

        def OpenAthenaClientLogWindow():
            wnd = uicore.registry.GetWindow('combatLogWindowClient')
            if wnd and not wnd.destroyed:
                wnd.Close()
            else:
                wnd = CombatLogWindow(service=sm.GetService('zactionLoggerSvc'), parent=uicore.layer.main, name='combatLogWindowClient', caption='athena log - client', windowID='combatLogWindowClient')

        athenaEntries.append(('Open Athena Client Log', OpenAthenaClientLogWindow))
        m.append(('Movement/Animation', movementItems))
        m.append(('Debugging', debuggingEntries))
        m.append(('Camera', cameraEntries))
        m.append(('Graphics', graphicsEntries))
        m.append(('Entities', entitiesEntries))
        m.append(('Athena', athenaEntries))
        m.append(('Interior', self.GetInteriorMenu()))
        m.append(('Encounter', self.GetEncounterMenu()))
        self.MakeMenu(m, 'Incarna_Btn')
        return m

    def GetInteriorMenu(self, *args):
        m = []
        sceneManager = sm.GetService('sceneManager')
        visualizations = sceneManager.GetIncarnaRenderJobVisualizationsMenu()

        def SpawnCharacters(numToSpawn):
            area = ((-15, -22), (25, 36))
            typeToRecipe = [(3, 1373),
             (4, 1374),
             (28, 1375),
             (29, 1376),
             (30, 1377),
             (31, 1378),
             (32, 1379),
             (33, 1380),
             (6, 1383),
             (39, 1384),
             (7, 1385),
             (41, 1386)]
            for i in range(numToSpawn):
                x = random.uniform(area[0][0], area[0][1])
                y = random.uniform(area[1][0], area[1][1])
                recipeID, typeID = random.choice(typeToRecipe)
                sm.RemoteSvc('slash').SlashCmd('/entityspawn {0} {1} {2} 0 {3}'.format(recipeID, typeID, x, y))
                blue.pyos.synchro.SleepWallclock(1000)

        visualizations.append(('Spawn 8 characters', lambda : SpawnCharacters(8)))
        visualizations.append(('Spawn 31 characters', lambda : SpawnCharacters(31)))
        return visualizations

    def ToggleCameraIdleMovement(self):
        sceneManager = sm.services.get('sceneManager', None)
        if sceneManager:
            camera = sceneManager.GetRegisteredCamera('hangar') or sceneManager.GetRegisteredCamera('default')
            if camera:
                camera.idleMove = not camera.idleMove

    def QAMenu(self, *args):
        m = []
        m.append(('Automated Tasks', self.Automated()))
        m.append(None)

        def ToggleDynamicClipPlanes():
            scene = sm.GetService('sceneManager').GetActiveScene()
            scene.dynamicClipPlanes = not scene.dynamicClipPlanes

        def GetAsteroidEnvToggler(settingsKey, flag):

            def AsteroidToggler():
                current = gfxsettings.Get(settingsKey)
                gfxsettings.Set(settingsKey, flag, False)
                sm.ScatterEvent('OnGraphicSettingsChanged', [settingsKey])

            return AsteroidToggler

        m.append(('Graphics', [('V3 testing', lambda : self.V3Testing()),
          ('Cycle nebulas', lambda : self.CycleNebulas()),
          ('Cube of Death: ships', gfxmisc.CubeOfDeath),
          ('Corpse Previewer', corpseviewer.CorpsePreviewer(sm.GetService('sceneManager')).ShowUI),
          ('Asset Previewer', gfxpreviewer.AssetPreviewer(sm.GetService('sceneManager')).ShowUI),
          ('Warp Effect Debug', gfxreports.ShowWarpEffectReport),
          ('Flight Controls Debug', sm.GetService('flightControls').simulation.ToggleDebug),
          ('Toggle Dynamic Clip Planes', ToggleDynamicClipPlanes),
          ('Gamma slider', gfxmisc.TestGammaSlider),
          ('Asteroid Environment', (('Enable Environment', GetAsteroidEnvToggler(gfxsettings.UI_ASTEROID_ATMOSPHERICS, True)),
            ('Disable Environment', GetAsteroidEnvToggler(gfxsettings.UI_ASTEROID_ATMOSPHERICS, False)),
            ('Enable Godrays', GetAsteroidEnvToggler(gfxsettings.UI_ASTEROID_GODRAYS, True)),
            ('Disable Godrays', GetAsteroidEnvToggler(gfxsettings.UI_ASTEROID_GODRAYS, False)),
            ('Enable Cloudfield', GetAsteroidEnvToggler(gfxsettings.UI_ASTEROID_CLOUDFIELD, True)),
            ('Disable Cloudfield', GetAsteroidEnvToggler(gfxsettings.UI_ASTEROID_CLOUDFIELD, False)),
            ('Enable Fog', GetAsteroidEnvToggler(gfxsettings.UI_ASTEROID_FOG, True)),
            ('Disable Fog', GetAsteroidEnvToggler(gfxsettings.UI_ASTEROID_FOG, False)),
            ('Enable Rock Particles', GetAsteroidEnvToggler(gfxsettings.UI_ASTEROID_PARTICLES, True)),
            ('Disable Rock Particles', GetAsteroidEnvToggler(gfxsettings.UI_ASTEROID_PARTICLES, False)))),
          None,
          ('Managed RT Report', gfxreports.ShowManagedRTReport),
          ('Blue Resources', gfxreports.ShowBlueResourceReport),
          None,
          ('LOD Report', gfxreports.ShowLODOverviewReport),
          ('Explosion Pool Report', gfxreports.ShowExplosionPoolReport),
          ('Effect Activation Report', gfxreports.ShowEffectActivationReport),
          None,
          ('Planet Texture Report', gfxreports.ShowPlanetTextureReport),
          ('Planet Status Report', gfxreports.ShowPlanetStatusReport),
          None,
          ('Inspect Scene', lambda : blueobjviewer.Show(sm.GetService('sceneManager').GetActiveScene())),
          ('Inspect RenderJob', lambda : blueobjviewer.Show(sm.GetService('sceneManager').fisRenderJob))]))
        m.append(None)
        m.append(('Starmap', [('Clear cache', lambda : sm.GetService('starmap').ClearMapCache())]))
        m.append(None)
        m.append(('Store', [('Clear cache', lambda : sm.GetService('vgsService').ClearCache())]))
        m.append(None)
        m.append(('Camera', [('Toggle Camera Idle Movement', self.ToggleCameraIdleMovement)]))
        m.append(None)
        m.append(('Auto Bot', AutoBotWindow.Open))
        self.MakeMenu(m, 'QA_Btn')

    def GetEncounterMenu(self, *args):
        m = []

        def OpenEncounterDebugWindow():
            uicls.EncounterDebugWindow(parent=uicore.layer.main, name='EncounterDebugWindow', caption='Encounter Debug', windowID='EncounterDebugWindow')

        m.append(('Open Encounter Debug', OpenEncounterDebugWindow))
        return m

    def ImplantsMenu(self, *args):
        m = []
        implantsmenu = sm.GetService('implant').ImplantMenu()
        for entry in implantsmenu:
            try:
                m.append((entry[0], entry[1]))
            except:
                sys.exc_clear()
                m.append(None)

        self.MakeMenu(m, 'Implants_Btn')

    def DroneMenu(self, *args):
        m = []
        dronemenu = sm.GetService('charge').DroneMenu()
        for entry in dronemenu:
            try:
                m.append((entry[0], entry[1]))
            except:
                sys.exc_clear()
                m.append(None)

        self.MakeMenu(m, 'Drones_Btn')

    def ChargeMenu(self, *args):
        m = []
        chargemenu = sm.GetService('charge').ChargeMenu()
        for entry in chargemenu:
            try:
                if entry.__class__ == dict:
                    m.append((entry['label'], None))
                    m.append(None)
                else:
                    m.append((entry[0], entry[1]))
            except:
                sys.exc_clear()
                m.append(None)

        self.MakeMenu(m, 'Charges_Btn')

    def ToggleMyShip(self):
        ship = sm.GetService('michelle').GetBall(session.shipid)
        if ship and ship.model:
            ship.model.display = not ship.model.display

    def ShipMenu(self, *args):
        shipmenu = sm.StartService('copycat').GetMenu_Ship()
        if shipmenu is None:
            return
        shipmenu += [None, ('Show/Hide My Ship', self.ToggleMyShip)]
        menu = []
        submenu = []
        for menuentry in shipmenu:
            if isinstance(menuentry, types.TupleType):
                if len(menuentry) == 2:
                    display, func = menuentry
                    if isinstance(func, types.TupleType):
                        subFunc = func[1]()
                        for entry in subFunc:
                            if isinstance(entry, types.TupleType):
                                submenu.append((entry, None))
                                submenu.append(None)
                            elif isinstance(entry, types.DictType):
                                submenu.append((entry['label'], entry['action'], entry['args']))

                        if len(submenu) == 0:
                            submenu = [('Nothing found', None)]
                        menu.append((display, submenu))
                        submenu = []
                    else:
                        menu.append((display, func))
                elif len(menuentry) == 3:
                    display, func, args = menuentry
                    menu.append((display, func, args))
            elif isinstance(menuentry, types.NoneType):
                menu.append(None)

        self.MakeMenu(menu, 'Ship_Btn')

    def MacroMenu(self, *args):
        m = []
        lines = sm.GetService('slash').GetMacros()
        lines.sort()
        for macroName, comseq in lines:
            m.append((macroName, self.SlashBtnClick(comseq)))

        self.MakeMenu(m, 'Macro_Btn')

    def UIMenu(self, *args):
        toolMenu = []
        from notifications.client.development.notificationDevUI import NotificationDevWindow
        toolMenu.append(('Notification Dev', lambda : NotificationDevWindow.Open()))
        toolMenu.append(('Window Manager', lambda : form.WindowManager.Open()))
        toolMenu.append(('Window Monitor', lambda : form.WindowMonitor.Open()))
        toolMenu.append(('Debugger', lambda : form.UIDebugger.Open()))
        toolMenu.append(('Tree', lambda : UITree.Open()))
        toolMenu.append(('Control Catalog', lambda : ControlCatalogWindow.Open()))
        toolMenu.append(('Event listener', lambda : form.UIEventListener.Open()))
        toolMenu.append(('Performance test', lambda : UIPerformanceTestWnd.Open()))
        toolMenu.append(('Sprite test', lambda : form.UISpriteTest.Open()))
        toolMenu.append(('Color picker', lambda : form.UIColorPicker.Open()))
        toolMenu.append(('Color Theme Editor', lambda : ColorThemeEditor.Open()))
        toolMenu.append(('Animation test', lambda : form.UIAnimationTest.Open()))
        toolMenu.append(('Alignment test', lambda : form.AlignmentTester.Open()))
        toolMenu.append(('Gradient Editor', lambda : form.GradientEditor.Open()))
        toolMenu.append(('Text style test', lambda : uicls.LoadFlagTester.Open()))
        toolMenu.append(('Scaling    ', lambda : form.UIScaling.Open()))
        toolMenu.append(('Opportunities   ', lambda : AchievementWindow.Open()))
        toolMenu.append(None)
        toolMenu.append(('Toggle Black Background', self.ToggleBlackBackground))
        toolMenu.append(('Toggle Camera Wobble', self.ToggleCameraWobble))
        toolMenu.append(('Reload UI textures', self.ReloadUITextures))
        toolMenu.append(('Reload UI Pixel Shader', self.ReloadUIShader))
        toolMenu.append(None)
        toolMenu.append(('Localization Editor', self.OpenLocalizationWindow))
        toolMenu.append(('Reload FSD localization pickles', self.ReloadFSDLocalizationPickles))
        toolMenu.append(('Rebuild FSD localization pickles', self.RebuildFSDLocalizationPickles))
        self.MakeMenu(toolMenu, 'UI_Btn')

    def OpenLocalizationWindow(self):
        if blue.pyos.packaged:
            raise UserError('CustomError', {'error': "Localization editor can't be run from this client."})
        else:
            form.UILocalizationWindow.Open()

    def ReloadFSDLocalizationPickles(self):
        localizationTools.ReloadFSDLocalizationPickle()
        msg = 'FSD localization pickles successfully reloaded on client'
        if sm.RemoteSvc('localizationServer').ReloadFSDPickle():
            msg += ' and server'
        sm.GetService('gameui').Say(msg)

    def RebuildFSDLocalizationPickles(self):
        question = "Would you like to rebuild localization pickles now? Note that this will block the main gameplay thread for about 30 seconds, so don't panic!"
        if uicore.Message('CustomQuestion', {'header': 'Build?',
         'question': question}, uiconst.YESNO) == uiconst.ID_YES:
            uthread.pool('RebuildLocalizationFiles', self.__LocalizationBuild_OutputThread)

    def __LocalizationBuild_OutputThread(self):
        p = localizationTools.RebuildFSDLocalizationPickles()
        print '*** REBUILDING FSD LOCALIZATION FILES ***'
        stdout, stderr = p.communicate()
        if 'FAILED' in stdout:
            stdout = stdout.replace('\n', '<br>')
            raise UserError('CustomError', {'error': 'Error building file, see output below. Pickles not built!<br><br>%s' % stdout})
        if stdout:
            print stdout
        print '*** BUILD COMPLETE ***'
        self.ReloadFSDLocalizationPickles()

    def ReloadUITextures(self):
        for resPath in blue.motherLode.GetNonCachedKeys():
            if resPath.startswith('res:/ui/texture') or 'ubershader' in resPath:
                res = blue.motherLode.Lookup(resPath)
                if res:
                    if hasattr(res, 'Reload'):
                        res.Reload()

    def ReloadUIShader(self):
        res = blue.motherLode.Lookup('res:/graphics/effect.dx11/ui/ubershader.sm_hi')
        if res:
            res.Reload()
        res = blue.motherLode.Lookup('res:/graphics/effect.dx11/ui/ubershader.sm_lo')
        if res:
            res.Reload()

    def ToggleBlackBackground(self):
        for c in uicore.desktop.children:
            if c.name == 'colorFill':
                c.Close()
                break
        else:
            color = util.Color.FUCHSIA if uicore.uilib.Key(uiconst.VK_SHIFT) else util.Color.BLACK
            c = uiprimitives.Fill(name='colorFill', parent=uicore.desktop, color=color)

    def ToggleCameraWobble(self):
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        camera.idleMove = not camera.idleMove

    def ToolMenu(self, *args):

        def CallMethod(*args):
            objectName, callMethodOrNewWindow, isService = args
            if isService:
                return CallServiceMethod(*args)
            else:
                return lambda : CallFormMethod(*args)

        def CallServiceMethod(svcName, method, *args):
            return lambda : getattr(sm.GetService(svcName), method)()

        def CallFormMethod(formName, new, *args):
            windowClass = form.__getattribute__(formName)
            if new:
                windowClass.CloseIfOpen()
            return windowClass.Open()

        def GatherInsiderTools():
            import svc, form
            neocomGuid = '__neocommenuitem__'
            insiderObjects = []
            for key, value in svc.__dict__.iteritems():
                isService = True
                if hasattr(value, neocomGuid):
                    insiderTool = getattr(value, neocomGuid)
                    insiderObjects.append((key, insiderTool, isService))

            for key, value in form.__dict__.iteritems():
                isService = False
                if hasattr(value, neocomGuid):
                    insiderTool = getattr(value, neocomGuid)
                    insiderObjects.append((key, insiderTool, isService))

            return insiderObjects

        toolMenu = []
        insiderTools = GatherInsiderTools()
        for tool in insiderTools:
            try:
                objectName, menuItem, isService = tool
                windowInfo, callMethodOrNewWindow, requiredRole = menuItem
                windowName, itemClassOrFormName = menuItem[0]
                if len(menuItem) >= 3 and requiredRole & session.role or len(menuItem) == 2:
                    toolMenu.append((windowName, CallMethod(objectName, callMethodOrNewWindow, isService)))
            except (IndexError, ValueError):
                sys.exc_clear()
                continue

        settingsSubMenu = []
        settingsSubMenu.append(('Export', sm.GetService('settingsLoader').Export, ()))
        settingsSubMenu.append(('Load', sm.GetService('settingsLoader').Load, ()))
        toolMenu.append(('Settings', settingsSubMenu))
        toolMenu.append(('Effect Camera', uicls.EffectCameraWindow.Open, ()))
        toolMenu.sort()
        if toolMenu[0][0] == '<color=0xffff8080>Python Console':
            toolMenu.append(None)
            toolMenu.append(toolMenu.pop(0))
        toolMenu.append(None)
        action = 'gd/npc.py?action=BrowseSolarSystem&solarSystemID=' + str(session.solarsystemid2)
        toolMenu.append(('Solar system NPC info', sm.StartService('menu').GetFromESP, (action,)))
        if trinity.IsFpsEnabled():
            toolMenu.append(('Turn FPS Monitor OFF', trinity.SetFpsEnabled, (False,)))
        else:
            toolMenu.append(('Turn FPS Monitor ON', trinity.SetFpsEnabled, (True,)))
        toolMenu.append(('Blue stats graphs', lambda : form.GraphsWindow.Open()))
        toolMenu.append(('Telemetry panel', lambda : form.TelemetryPanel.Open()))
        toolMenu.append(('Tasklet monitor', lambda : taskletMonitor.TaskletMonitor.Open()))
        toolMenu.append(('Background download queue monitor', lambda : bdqmonitor.BackgroundDownloadQueueMonitor.Open()))
        toolMenu.append(('Report Bug', lambda : sm.GetService('bugReporting').StartCreateBugReport()))
        toolMenu.append(('Get camera distance', lambda : self.GetDistanceFromCamera()))
        toolMenu.append(None)
        toolMenu += self.ExpoMenu()
        self.MakeMenu(toolMenu, 'Tools_Btn')

    def CreateDefect(self, *args):
        sm.GetService('bugReporting').StartCreateBugReport()

    def Hide(self, *args):
        self.Show(show=False)

    def Reload(self):
        self.Hide()
        self.Show(force=True)
        uicore.Message('CustomNotify', {'notify': 'Insider has been reloaded.'})

    def OnUIRefresh(self):
        form.InsiderWnd.CloseIfOpen()
        self.Show(force=True)

    def Show(self, show = True, force = False):
        if not session.role & service.ROLEMASK_ELEVATEDPLAYER:
            return
        INSIDERDIR = self.GetInsiderDir()
        if not os.path.exists(INSIDERDIR):
            os.mkdir(INSIDERDIR)
        form.InsiderWnd.CloseIfOpen()
        if not show:
            return
        settings.public.ui.Set('Insider', show)
        btn = []
        menus = [['Tools', self.ToolMenu, service.ROLEMASK_ELEVATEDPLAYER],
         ['Macro', self.MacroMenu, service.ROLE_GML],
         ['Ship', self.ShipMenu, service.ROLEMASK_ELEVATEDPLAYER],
         ['Charges', self.ChargeMenu, service.ROLE_GML],
         ['Drones', self.DroneMenu, service.ROLE_GML],
         ['Implants', self.ImplantsMenu, service.ROLE_GML],
         ['QA', self.QAMenu, service.ROLE_QA],
         ['Incarna', self.IncarnaMenu, service.ROLE_QA],
         ['UI', self.UIMenu, service.ROLEMASK_ELEVATEDPLAYER],
         ['Defect', self.CreateDefect, service.ROLE_GML]]
        for label, func, role in menus:
            if session.role & role:
                btn.append([label,
                 func,
                 None,
                 None])

        wnd = form.InsiderWnd.Open()
        if wnd:
            btn = uicontrols.ButtonGroup(btns=btn, parent=wnd.sr.main, line=0, unisize=1, align=uiconst.CENTER)

    def Toggle(self, forceShow = False, *args):
        if settings.public.ui.Get('Insider', False):
            self.Hide()
        else:
            self.Show(force=forceShow)

    def WarpTo(self, itemID = None):
        """Will warp the current player to the itemID"""
        if itemID:
            sm.GetService('slash').SlashCmd('warpto %d' % itemID)

    def GetDistanceFromCamera(self):
        """Calculates the distance from the camera to it's point of interest and shows it in an info window in the game"""
        registeredCamera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        cameraPosition = registeredCamera.pos
        interestPosition = registeredCamera.parent.translation
        distance = math.sqrt(pow(cameraPosition.x - interestPosition.x, 2) + pow(cameraPosition.y - interestPosition.y, 2) + pow(cameraPosition.z - interestPosition.z, 2))
        distance = math.trunc(distance)
        distance = '{:,}'.format(distance)
        uicore.Message('CustomInfo', {'info': 'The distance from camera to subject is %s meters' % distance})

    exports = {'insider.Show': Show,
     'insider.Hide': Hide,
     'insider.Toggle': Toggle}
