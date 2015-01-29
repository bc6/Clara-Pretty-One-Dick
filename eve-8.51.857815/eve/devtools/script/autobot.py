#Embedded file name: eve/devtools/script\autobot.py
from itertools import chain
import random
from carbon.common.lib.const import HOUR, MSEC, SEC
from carbon.common.script.sys.service import Service
from carbon.common.script.util.format import FmtSimpleDateUTC
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.primitives.container import Container
from carbonui.primitives.flowcontainer import FlowContainer
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.checkbox import Checkbox
from eve.client.script.ui.control.eveEditPlainText import EditPlainText
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from eve.client.script.ui.control.eveWindow import Window
import carbonui.const as uiconst
from eve.client.script.ui.control.utilMenu import UtilMenu
from eve.common.script.sys.eveCfg import IsRegion, IsConstellation, IsSolarSystem
from eve.devtools.script.dna import Ship
import localization
from inventorycommon import const
import os
import blue
import re
import uthread
SERVICENAME = 'AutoBot'

def GetConfig():
    return sm.GetService('autobot').GetConfig()


def GetPassConfig():
    return GetConfig()['passes']


def SetPassMinTime(textValue, passNumber):
    try:
        GetPassConfig()[passNumber]['minTime'] = int(textValue)
    except ValueError:
        pass


def SetPass(checkbox, passNumber):
    GetPassConfig()[passNumber]['enabled'] = checkbox.GetValue()


def ToggleNuke(passNumber):
    passConfig = GetPassConfig()[passNumber]
    passConfig['nuke'] = not passConfig['nuke']


def ToggleLocationGroupForPass(passNumber, groupId):
    locations = GetPassConfig()[passNumber]['locations']
    if groupId in locations:
        locations.remove(groupId)
    else:
        locations.add(groupId)


def SplitLocationsText(locText):
    return [ w.strip().lower() for w in re.split(',|:|\n|\r', locText) if w is not None and len(w) > 0 ]


def GetLocations(locationGroupIDs):
    m = sm.GetService('michelle')
    bp = m.GetBallpark()
    locations = []
    for locationID in bp.globals:
        if locationID > 0 and bp.slimItems[locationID].groupID in locationGroupIDs:
            locations.append(locationID)

    return locations


def MatchLocationNameToId(locationText):
    for locationId, loc in chain(cfg.mapRegionCache.iteritems(), cfg.mapConstellationCache.iteritems(), cfg.mapSystemCache.iteritems()):
        if localization.GetByMessageID(loc.nameID).lower() == locationText:
            return locationId


def ConvertLocationsToSolarSystemIds(locationStringList):
    solarSystemIds = set()
    for locationText in locationStringList:
        try:
            locationId = int(locationText)
        except ValueError:
            locationId = MatchLocationNameToId(locationText)

        if locationId is None:
            continue
        if IsRegion(locationId):
            solarSystemIds.update(cfg.mapRegionCache[locationId].solarSystemIDs)
        elif IsConstellation(locationId):
            solarSystemIds.update(cfg.mapConstellationCache[locationId].solarSystemIDs)
        elif IsSolarSystem(locationId):
            solarSystemIds.add(locationId)

    return solarSystemIds


def GetLogFileName():
    return os.path.join(sm.GetService('insider').GetInsiderDir(), 'autobot_%s.log' % blue.os.GetWallclockTime())


class AutoBotService(Service):
    """AutoBot pilot autopilot"""
    __dependencies__ = []
    __guid__ = 'svc.autobot'
    __servicename__ = SERVICENAME
    __displayname__ = SERVICENAME

    def Run(self, memStream = None):
        Service.Run(self, memStream)
        self.logLines = []
        self.passConfigByNumber = {}
        self.workerThread = None
        self.isWorking = False
        self.config = {'passes': {},
         'shipDna': None,
         'solarsystems': set(),
         'locations': ''}
        self.slash = sm.RemoteSvc('slash')

    def Tr(self, solarSystemID):
        try:
            self.slash.SlashCmd('/tr me %d' % solarSystemID)
        except UserError as e:
            if e.msg == 'SystemCheck_TransferFailed_Loading':
                self.Log('System %s is still loading...' % solarSystemID)
                blue.pyos.synchro.SleepWallclock(5000)
                self.slash.SlashCmd('/tr me %d' % solarSystemID)
            else:
                raise

        self.Log('Tr to %s successful' % solarSystemID)
        blue.pyos.synchro.SleepWallclock(7000)
        self.slash.SlashCmd('/stop')

    def Move(self, locationID):
        self.slash.SlashCmd('/tr me %d' % locationID)
        self.Log('Move to %s successful' % locationID)
        blue.pyos.synchro.SleepWallclock(3000)

    def SetupShip(self):
        from eve.client.script.ui.services.menuSvcExtras import menuFunctions
        dnaString = GetConfig()['shipDna']
        self.Log('Ship setup based on dna: %s' % dnaString)
        dnaShip = Ship(dnaKey=dnaString)
        shipId = dnaShip.Assemble()
        self.Log('Ship %s assembled' % shipId)
        blue.pyos.synchro.SleepWallclock(5000)
        menuFunctions.Board(shipId)
        self.Log('Ship %s boarded' % shipId)
        blue.pyos.synchro.SleepWallclock(5000)
        self.slash.SlashCmd('/online me')
        self.Log('Ship %s onlined everything' % shipId)
        blue.pyos.synchro.SleepWallclock(5000)

    def Nuke(self):
        self.slash.SlashCmd('/nuke')
        self.Log('Nuking the place...')
        blue.pyos.synchro.SleepWallclock(1000)

    def GetConfig(self):
        return self.config

    def StartBot(self):
        self.Log('Start autobot script')
        if self.isWorking:
            return
        self.isWorking = True
        self.Log('Starting worker thread')
        self.workerThread = uthread.new(self._WorkerThread)

    def StopBot(self):
        self.Log('Stop autobot script')
        self.StopWorkerThread()
        self.WriteLogFile()

    def Log(self, text):
        self.logLines.append('%s %s' % (FmtSimpleDateUTC(blue.os.GetWallclockTime()), text))

    def WriteLogFile(self):
        with open(GetLogFileName(), 'w') as f:
            f.writelines(self.logLines)

    def ClearLogs(self):
        self.logLines = []

    def _WorkerThread(self):
        try:
            self.Log('worker thread started')
            config = self.GetConfig().copy()
            solarSystemIds = ConvertLocationsToSolarSystemIds(config['locations'])
            minSec = config['minSecurity']
            maxSec = config['maxSecurity']
            self.Log('Security limits [%0.1f, %0.1f]' % (minSec, maxSec))
            solarSystemIds = [ ssId for ssId in solarSystemIds if minSec <= cfg.mapSystemCache[ssId].securityStatus <= maxSec ]
            random.shuffle(solarSystemIds)
            if len(solarSystemIds) == 0:
                self.Log('No valid systems to process. Exiting')
            self.Log('Starting test run of %d solar systems' % len(solarSystemIds))
            self.Tr(solarSystemIds[0])
            if config['shipDna'] is not None:
                self.SetupShip()
            times = []
            startTime = blue.os.GetWallclockTime()
            lastTime = startTime
            passes = config['passes']
            passNumbers = sorted([ pNum for pNum, passConfig in passes.iteritems() if passConfig['enabled'] ])
            for i, solarSystemID in enumerate(solarSystemIds):
                for passNumber in passNumbers:
                    passConfig = passes[passNumber]
                    self.Log('Starting pass %d in location %d%s' % (passNumber, solarSystemID, ' with nuke' if passConfig['nuke'] else ''))
                    self.Log('Autobot processing system %d of %d: %d %s and has been active for %.1f hours' % (i + 1,
                     len(solarSystemIds),
                     solarSystemID,
                     cfg.evelocations.Get(solarSystemID).locationName,
                     (blue.os.GetWallclockTime() - startTime) / float(HOUR)))
                    self.Tr(solarSystemID)
                    locationGroupIds = passConfig['locations']
                    for locationID in GetLocations(locationGroupIds):
                        self.Move(locationID)
                        if passConfig['nuke']:
                            message = 'clearing out location (%d) %s' % (locationID, cfg.evelocations.Get(locationID).locationName)
                            self.Log(message)
                            self.Nuke()

                    minTime = passConfig['minTime']
                    elapsedTime = blue.os.GetWallclockTime() - lastTime
                    remainingTime = SEC * minTime - elapsedTime
                    if remainingTime > 0:
                        self.Log('Waiting for %s sec to enforce %s sec min time before next pass' % (remainingTime / SEC, minTime))
                        blue.pyos.synchro.SleepWallclock(remainingTime / MSEC)
                    nowTime = blue.os.GetWallclockTime()
                    times.append(float(nowTime - lastTime) / SEC)
                    lastTime = nowTime

                message = 'system process in %.1f sec. ' % times[-1]
                message += 'average processsing time: %.1f sec' % (sum(times) / len(times))
                self.Log(message)

            self.Log('All done in %.1f sec' % ((lastTime - startTime) / SEC))
        except Exception as e:
            self.Log('Error: ' + str(e))
        finally:
            self.CleanWorkerThread()

    def StopWorkerThread(self):
        if self.workerThread:
            self.workerThread.kill()
        self.CleanWorkerThread()

    def CleanWorkerThread(self):
        self.workerThread = None
        self.isWorking = False


class AutoBotWindow(Window):
    """ An Insider window which makes it easy to debug UI containers """
    default_windowID = 'AutoBotWindow'
    default_width = 360
    default_height = 300
    default_topParentHeight = 0
    default_minSize = (default_width, default_height)
    default_caption = 'AutoBot Control Box'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.CreateLocationSelector()
        self.CreateSecurityFilter()
        self.CreateShipSelector()
        self.CreatePasses()
        self.CreateButtons()
        self.CreateLogDisplay()

    def CreateButtons(self):
        buttonCont = FlowContainer(name='SubCategoryButtons', parent=self.sr.main, centerContent=True, align=uiconst.TOBOTTOM, contentSpacing=(2, 1), state=uiconst.UI_PICKCHILDREN, padding=(0, 4, 0, 4))
        Button(parent=buttonCont, label='Roll out!!', func=self.StartBot, align=uiconst.NOALIGN, padding=2)
        Button(parent=buttonCont, label='Stop', func=self.StopBot, align=uiconst.NOALIGN, padding=2)
        Button(parent=buttonCont, label='Clear Log', func=self.ClearLogs, align=uiconst.NOALIGN, padding=2)

    def CreateLocationSelector(self):
        EveLabelSmall(parent=self.sr.main, text='<color=orange>This is a tool for automating visits to solar systems and locations within them. There are several actions available while visiting each location.', align=uiconst.TOTOP, padding=4)
        EveLabelSmall(parent=self.sr.main, text='Systems, Constellations or Regions', align=uiconst.TOTOP, padding=4)
        self.locationsEdit = EditPlainText(parent=self.sr.main, align=uiconst.TOTOP, height=50, padding=4)

    def CreateSecurityFilter(self):
        secCont = Container(parent=self.sr.main, height=20, padding=2, align=uiconst.TOTOP)
        EveLabelSmall(parent=secCont, text='Security Band:', align=uiconst.TOLEFT, padding=4)
        EveLabelSmall(parent=secCont, text='Min Security', align=uiconst.TOLEFT, padding=4)
        self.minSecEdit = SinglelineEdit(parent=secCont, name='minSec', width=30, floats=(-1.0, 1.0, 1), align=uiconst.TOLEFT, padTop=-3, setvalue='-1.0')
        EveLabelSmall(parent=secCont, text='Max Security', align=uiconst.TOLEFT, padding=4)
        self.maxSecEdit = SinglelineEdit(parent=secCont, name='maxSec', width=30, floats=(-1.0, 1.0, 1), align=uiconst.TOLEFT, padTop=-3, setvalue='1.0')

    def CreateShipSelector(self):
        cont = Container(parent=self.sr.main, name='ship_options', align=uiconst.TOTOP, height=20)
        self.spawnShipCheckbox = Checkbox(parent=cont, align=uiconst.TOLEFT, text='Spawn new ship', checked=False, padLeft=8, callback=self.OnChangeSpawnShip, width=150)
        Container(parent=cont, width=16, align=uiconst.TOLEFT)
        EveLabelSmall(parent=cont, text='DNA', align=uiconst.TOLEFT, padding=4)
        self.dnaEdit = SinglelineEdit(parent=cont, setvalue='DNA:593:2528:20197', align=uiconst.TOLEFT, width=200)

    def CreatePasses(self):
        EveLabelSmall(parent=self.sr.main, text='Actions for each system visited', align=uiconst.TOTOP, padding=4)
        self.CreateSystemPass(1)
        self.CreateSystemPass(2)

    def CreateSystemPass(self, passNumber):

        def GetLocationsMenu(menuParent):
            passConfig = GetPassConfig()[passNumber]
            menuParent.AddHeader(text='Locations to visit')
            for groupId in (const.groupAsteroidBelt, const.groupStargate, const.groupStation):
                menuParent.AddCheckBox(text=cfg.invgroups.Get(groupId).groupName, checked=groupId in passConfig['locations'], callback=(ToggleLocationGroupForPass, passNumber, groupId))

            menuParent.AddDivider()
            menuParent.AddHeader(text='Actions')
            menuParent.AddCheckBox(text='Nuke location', checked=passConfig['nuke'], callback=(ToggleNuke, passNumber))

        passConfig = {'locations': {const.groupAsteroidBelt},
         'nuke': False,
         'enabled': passNumber == 1,
         'minTime': 1}
        GetPassConfig()[passNumber] = passConfig
        menuCont = Container(name='pass%d' % passNumber, parent=self.sr.main, align=uiconst.TOTOP, height=20, padLeft=4)
        cont = Container(parent=menuCont, width=100, align=uiconst.TOLEFT)
        Checkbox(parent=cont, text='Enable Pass %s' % passNumber, align=uiconst.CENTERLEFT, checked=passConfig['enabled'], callback=lambda checkbox: SetPass(checkbox, passNumber), width=200)
        cont = Container(parent=menuCont, width=100, align=uiconst.TOLEFT)
        EveLabelSmall(parent=cont, text='Min time (sec)', align=uiconst.CENTERRIGHT, left=4)
        SinglelineEdit(parent=menuCont, ints=(1, 999), OnChange=lambda textValue: SetPassMinTime(textValue, passNumber), setvalue=passConfig['minTime'], align=uiconst.TOLEFT, width=50)
        UtilMenu(menuAlign=uiconst.TOPRIGHT, parent=menuCont, align=uiconst.TOLEFT, GetUtilMenu=GetLocationsMenu, label='Options', texturePath='res:/UI/Texture/Icons/38_16_229.png', closeTexturePath='res:/UI/Texture/Icons/38_16_230.png')

    def CreateLogDisplay(self):
        self.logEdit = EditPlainText(parent=self.sr.main, align=uiconst.TOALL, readonly=True, padTop=4)

    def OnChangeSpawnShip(self, checkbox):
        if checkbox.GetValue():
            self.dnaEdit.SetReadOnly(False)
            self.dnaEdit.opacity = 1.0
        else:
            self.dnaEdit.SetReadOnly(True)
            self.dnaEdit.opacity = 0.5

    def StartBot(self, *args):
        config = GetConfig()
        locations = SplitLocationsText(self.locationsEdit.GetValue())
        config['locations'] = locations
        config['minSecurity'] = self.minSecEdit.GetValue()
        config['maxSecurity'] = self.maxSecEdit.GetValue()
        if self.spawnShipCheckbox.GetValue():
            config['shipDna'] = self.dnaEdit.GetValue()
        else:
            config['shipDna'] = None
        sm.GetService('autobot').StartBot()
        self.logUpdated = AutoTimer(2000, self.UpdateLogText)

    def PauseBot(self, *args):
        sm.GetService('autobot').PauseBot()

    def StopBot(self, *args):
        sm.GetService('autobot').StopBot()
        self.logUpdated = None

    def ClearLogs(self, *args):
        sm.GetService('autobot').ClearLogs()

    def UpdateLogText(self):
        logLines = sm.GetService('autobot').logLines
        self.logEdit.SetValue('\n'.join([ str(x) for x in reversed(logLines) ]))
