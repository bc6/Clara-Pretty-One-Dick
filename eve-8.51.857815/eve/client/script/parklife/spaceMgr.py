#Embedded file name: eve/client/script/parklife\spaceMgr.py
import math
import sys
import states as state
import service
import uicontrols
import uthread
import blue
import uix
import trinity
import util
import base
import log
import geo2
import carbonui.const as uiconst
import localization
import destiny
import telemetry
import evegraphics.settings as gfxsettings
import eve.client.script.environment.spaceObject.repository as repository
import eve.client.script.environment.spaceObject.spaceObject as spaceObject

class SpaceMgr(service.Service):
    __guid__ = 'svc.space'
    __update_on_reload__ = 0
    __exportedcalls__ = {'CanWarp': [],
     'StartPartitionDisplayTimer': [],
     'StopPartitionDisplayTimer': [],
     'WarpDestination': [],
     'IndicateWarp': [],
     'StartWarpIndication': [],
     'StopWarpIndication': []}
    __notifyevents__ = ['DoBallsAdded',
     'DoBallRemove',
     'OnDamageStateChange',
     'OnSpecialFX',
     'OnDockingAccepted',
     'ProcessSessionChange',
     'OnBallparkCall',
     'OnNotifyPreload',
     'OnWormholeJumpCancel',
     'DoBallsRemove',
     'OnRemoteMessage']
    __dependencies__ = ['michelle',
     'FxSequencer',
     'transmission',
     'settings',
     'state',
     'sceneManager']

    def __init__(self):
        service.Service.__init__(self)
        self.warpDestinationCache = [None,
         None,
         None,
         None,
         None]
        self.lazyLoadQueueCount = 0
        self.maxTimeInDoBallsAdded = 10 * const.MSEC
        self.prioritizedIDs = set()
        self.planetManager = PlanetManager()
        self.asteroids = {}

    def Run(self, memStream = None):
        service.Service.Run(self, memStream)
        sm.FavourMe(self.DoBallsAdded)
        for each in uicore.layer.shipui.children[:]:
            if each.name in ('caption', 'indicationtext'):
                each.Close()

        self.indicationtext = None
        self.setIndicationText = None
        self.caption = None
        self.indicateTimer = base.AutoTimer(250, self.Indicate_thread)
        self.shortcutText = None
        self.shortcutSubText = None

    def Stop(self, stream):
        self.ClearIndicateText()
        self.ClearShortcutText()
        self.indicateTimer = None
        service.Service.Stop(self)

    def ProcessSessionChange(self, *args):
        self.ClearIndicateText()
        self.ClearShortcutText()

    def OnWormholeJumpCancel(self):
        self.ClearIndicateText()
        self.ClearShortcutText()
        eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/Wormholes/EnterCollapsed')})

    def GetTypeData(self, slimItem):
        data = {}
        data['slimItem'] = slimItem
        data['typeID'] = slimItem.typeID
        data['groupID'] = slimItem.groupID
        objType = cfg.invtypes.Get(slimItem.typeID)
        data['typeName'] = objType._typeName
        graphicFile = objType.GraphicFile()
        data['graphicID'] = objType.graphicID
        data['graphicFile'] = graphicFile
        graphicInfo = cfg.graphics.GetIfExists(objType.graphicID)
        data['sofRaceName'] = getattr(graphicInfo, 'sofRaceName', None)
        dunRotation = getattr(slimItem, 'dunRotation', None)
        data['dunRotation'] = dunRotation
        dunDirection = getattr(slimItem, 'dunDirection', None)
        data['dunDirection'] = dunDirection
        return data

    @telemetry.ZONE_METHOD
    def LoadObject(self, ball, slimItem, ob):
        if slimItem is None:
            return
        if getattr(ob, 'released', 1):
            self.LogWarn(slimItem.itemID, 'has already been released')
            return
        try:
            ob.Prepare()
        except Exception:
            log.LogException('Error adding SpaceObject of type', str(ob.__klass__), 'to scene')
            sys.exc_clear()

    def HandleAsteroidParticles(self):
        if not (gfxsettings.Get(gfxsettings.UI_ASTEROID_ATMOSPHERICS) and gfxsettings.Get(gfxsettings.UI_ASTEROID_PARTICLES)):
            return
        scene = self.GetScene()
        if scene is None:
            return
        if len(self.asteroids) == 0:
            scene.staticParticles.ClearClusters()
            return
        particles = scene.staticParticles
        if particles.transform is None:
            particles.transform = trinity.Load('res:/dx9/scene/asteroidrockfield.red')
            particles.maxParticleCount = 50000
            particles.maxSize = 100.0
            particles.minSize = 5.0
            particles.clusterParticleDensity = 1.0
        for id, asteroid in self.asteroids.iteritems():
            ball, slimItem, isAdded = asteroid
            if isAdded:
                continue
            self.asteroids[id] = (ball, slimItem, True)
            groupData = cfg.groupGraphics.get(int(slimItem.groupID), None)
            color = getattr(groupData, 'color', None)
            baseColor = (0.13, 0.13, 0.12, 1.0)
            if color is None:
                if hasattr(groupData, 'typeIDs'):
                    typeData = groupData.typeIDs.get(int(slimItem.typeID), None)
                    color = typeData.color
                    baseColor = (0.4, 0.6, 0.7, 1.0)
            if color is None:
                continue
            seed = int(id % 123456)
            particles.AddCluster((ball.x, ball.y, ball.z), ball.radius, (color.r,
             color.g,
             color.b,
             color.a), baseColor, seed)

        particles.Rebuild()

    @telemetry.ZONE_METHOD
    def DoBallsAdded(self, *args, **kw):
        lst = []
        ballsToAdd = args[0]
        for ball, slimItem in ballsToAdd:
            try:
                groupID = slimItem.groupID
                categoryID = slimItem.categoryID
                if slimItem.categoryID == const.categoryAsteroid:
                    self.asteroids[ball.id] = (ball, slimItem, False)
                klass = repository.GetClass(groupID, categoryID)
                if klass is None:
                    self.LogError('SpaceObject class not specified for group: ', groupID, '- defaulting to basic SpaceObject')
                    klass = spaceObject.SpaceObject
                ob = klass(ball)
                ob.typeData = self.GetTypeData(slimItem)
                ob.SetServices(self, sm)
                if groupID == const.groupPlanet or groupID == const.groupMoon:
                    self.planetManager.RegisterPlanetBall(ob)
                lst.append((ball, slimItem, ob))
                if ball.id == session.shipid and ball.mode == destiny.DSTBALL_WARP:
                    self.OnBallparkCall('WarpTo', (ball.id,
                     ball.gotoX,
                     ball.gotoY,
                     ball.gotoZ))
                    self.FxSequencer.OnSpecialFX(ball.id, None, None, None, None, 'effects.Warping', 0, 1, 0)
            except Exception:
                self.LogError('DoBallsAdded - failed to add ball', (ball, slimItem))
                log.LogException()
                sys.exc_clear()

        if settings.public.generic.Get('lazyLoading', 1):
            uthread.new(self.DoBallsAdded_, lst)
        else:
            self.DoBallsAdded_(lst)
        uthread.new(self.HandleAsteroidParticles)

    @telemetry.ZONE_METHOD
    def SplitListByThreat(self, bp, ballsToAdd):
        """
        Split the 'ballsToAdd' list in two lists, non-threatening and threatening.
        Returns (nonThreatening, threatening, numLostBalls).
        """
        threatening = []
        nonThreatening = []
        numLostBalls = 0
        stateSvc = sm.GetService('state')
        for each in ballsToAdd:
            ball, slimItem, ob = each
            itemID = slimItem.itemID
            slimItem = bp.GetInvItem(slimItem.itemID)
            if slimItem is None:
                self.LogInfo('Lost ball', itemID)
                numLostBalls += 1
                continue
            itemID = slimItem.itemID
            if slimItem.categoryID == const.categoryShip and getattr(slimItem, 'charID', None) or slimItem.categoryID == const.categoryEntity:
                attacking, hostile = stateSvc.GetStates(itemID, [state.threatAttackingMe, state.threatTargetsMe])
                if attacking or hostile:
                    threatening.append(each)
                else:
                    nonThreatening.append(each)
            else:
                nonThreatening.append(each)

        return (nonThreatening, threatening, numLostBalls)

    def PrioritizeLoadingForIDs(self, ids):
        self.prioritizedIDs.update(ids)

    def _LoadObjects(self, objects, info = 'Loading'):
        """
        Loads objects in the list without yielding
        """
        numBallsAdded = 0
        numLostBalls = 0
        michelle = sm.GetService('michelle')
        for each in objects:
            ball, slimItem, ob = each
            bp = michelle.GetBallpark()
            if bp is None:
                return (numBallsAdded, numLostBalls)
            itemID = slimItem.itemID
            slimItem = bp.GetInvItem(slimItem.itemID)
            if slimItem is None:
                self.LogInfo('Lost ball', itemID)
                numLostBalls += 1
                continue
            itemID = slimItem.itemID
            self.LogInfo(info, itemID)
            self.LoadObject(ball, slimItem, ob)
            numBallsAdded += 1

        return (numBallsAdded, numLostBalls)

    def GetScene(self):
        """Returns the space scene
        
        @return: The current space scene
        """
        return sm.GetService('sceneManager').GetRegisteredScene('default')

    @telemetry.ZONE_METHOD
    def DoBallsAdded_(self, ballsToAdd):
        bp = sm.GetService('michelle').GetBallpark()
        if bp is None:
            return
        self.LogInfo('DoBallsAdded_ - Starting to add', len(ballsToAdd), ' balls. lazy = ', settings.public.generic.Get('lazyLoading', 1))
        numBallsToAdd = len(ballsToAdd)
        numLostBalls = 0
        numBallsAdded = 0
        preEmptiveLoads = []
        self.lazyLoadQueueCount = len(ballsToAdd)
        timeStarted = blue.os.GetWallclockTimeNow()
        nonPrioritized = []
        prioritized = []
        for each in ballsToAdd:
            ball, slimItem, ob = each
            itemID = slimItem.itemID
            slimItem = bp.GetInvItem(slimItem.itemID)
            if slimItem is None:
                self.LogInfo('Lost ball', itemID)
                numLostBalls += 1
                continue
            itemID = slimItem.itemID
            if slimItem.groupID == const.groupSun:
                prioritized.append(each)
            elif itemID == session.shipid:
                prioritized.append(each)
            elif itemID in self.prioritizedIDs:
                prioritized.append(each)
                self.prioritizedIDs.remove(itemID)
            else:
                nonPrioritized.append(each)

        ballsToAdd = nonPrioritized
        added, lost = self._LoadObjects(prioritized, 'Preemtively loading prioritized')
        numBallsAdded += added
        numLostBalls += lost
        startOfTimeSlice = blue.os.GetWallclockTimeNow()
        nextThreatCheck = startOfTimeSlice + 500 * const.MSEC
        while len(ballsToAdd):
            try:
                ball, slimItem, ob = ballsToAdd.pop(0)
                self.LogInfo('Handling ball', slimItem.itemID)
                self.lazyLoadQueueCount = len(ballsToAdd)
                bp = sm.GetService('michelle').GetBallpark()
                if bp is None:
                    return
                itemID = slimItem.itemID
                slimItem = bp.GetInvItem(slimItem.itemID)
                if slimItem is None:
                    self.LogInfo('Lost ball', itemID)
                    numLostBalls += 1
                    continue
                itemID = slimItem.itemID
                self.LogInfo('Loading', itemID)
                self.LoadObject(ball, slimItem, ob)
                numBallsAdded += 1
                if blue.os.GetWallclockTimeNow() > nextThreatCheck:
                    ballsToAdd, threatening, lost = self.SplitListByThreat(bp, ballsToAdd)
                    numLostBalls += lost
                    added, lost = self._LoadObjects(threatening, 'Preemptively loading threat')
                    numBallsAdded += added
                    numLostBalls += lost
                    nextThreatCheck = blue.os.GetWallclockTimeNow() + 500 * const.MSEC
                self.lazyLoadQueueCount = len(ballsToAdd)
                if settings.public.generic.Get('lazyLoading', 1):
                    if blue.os.GetWallclockTimeNow() > startOfTimeSlice + self.maxTimeInDoBallsAdded:
                        blue.synchro.Yield()
                        startOfTimeSlice = blue.os.GetWallclockTimeNow()
            except:
                self.LogError('DoBallsAdded - failed to add ball', (ball, slimItem))
                log.LogException()
                sys.exc_clear()

        self.LogInfo('DoBallsAdded_ - Done adding', numBallsToAdd, ' balls in', util.FmtDate(blue.os.GetWallclockTimeNow() - timeStarted, 'nl'), '.', numLostBalls, 'balls were lost. lazy = ', settings.public.generic.Get('lazyLoading', 1))
        if numBallsAdded + numLostBalls != numBallsToAdd:
            self.LogError("DoBallsAdded - balls don't add up! numBallsAdded:", numBallsAdded, 'numLostBalls:', numLostBalls, 'numBallsToAdd:', numBallsToAdd)

    @telemetry.ZONE_METHOD
    def DoBallsRemove(self, pythonBalls, isRelease):
        if isRelease:
            for ball, slimItem, terminal in pythonBalls:
                if hasattr(ball, 'Release'):
                    uthread.new(ball.Release)
                if slimItem.categoryID == const.categoryAsteroid:
                    if ball.id in self.asteroids:
                        self.asteroids.pop(ball.id)

            uthread.new(self.HandleAsteroidParticles)
            self.planetManager.Release()
            return
        for ball, slimItem, terminal in pythonBalls:
            if slimItem.categoryID == const.categoryAsteroid:
                if ball.id in self.asteroids:
                    self.asteroids.pop(ball.id)
            self.DoBallRemove(ball, slimItem, terminal)

        uthread.new(self.HandleAsteroidParticles)

    @telemetry.ZONE_METHOD
    def DoBallRemove(self, ball, slimItem, terminal):
        if ball is None:
            return
        self.LogInfo('DoBallRemove::spaceMgr', ball.id)
        if hasattr(ball, 'Release'):
            uthread.new(ball.Release)
        if slimItem.groupID == const.groupPlanet or slimItem.groupID == const.groupMoon:
            self.planetManager.UnRegisterPlanetBall(ball)

    @telemetry.ZONE_METHOD
    def OnBallparkCall(self, functionName, args):
        if functionName == 'WarpTo' and args[0] == session.shipid:
            x = args[1]
            y = args[2]
            z = args[3]
            if not self.warpDestinationCache:
                self.warpDestinationCache = [None,
                 None,
                 None,
                 (x, y, z)]
            else:
                self.warpDestinationCache[3] = (x, y, z)
            if self.planetManager is not None:
                self.planetManager.CheckPlanetPreloadingOnWarp(self.warpDestinationCache[3])
        elif functionName == 'SetBallRadius':
            ballID = args[0]
            newRadius = args[1]
            ball = sm.GetService('michelle').GetBall(ballID)
            if hasattr(ball, 'SetRadius'):
                ball.SetRadius(newRadius)

    @telemetry.ZONE_METHOD
    def OnNotifyPreload(self, typeIDList):
        pass

    def OnDamageStateChange(self, shipID, damageState):
        ball = sm.GetService('michelle').GetBall(shipID)
        if ball:
            if hasattr(ball, 'OnDamageState'):
                ball.OnDamageState(damageState)

    def OnTutorialStateChange(self, inTutorial):
        self.inTutorial = inTutorial

    def OnRemoteMessage(self, msgID, *args, **kwargs):
        if msgID == 'FleetWarp':
            warpInfoDict = args[0]
            self.LogInfo('Setting local warp destination for fleet warp')
            celestialID = warpInfoDict.get('celestialID', None)
            self.WarpDestination(celestialID=celestialID)

    def WarpDestination(self, celestialID = None, bookmarkID = None, fleetMemberID = None):
        self.warpDestinationCache[0] = celestialID
        self.warpDestinationCache[1] = bookmarkID
        self.warpDestinationCache[2] = fleetMemberID

    def StartWarpIndication(self):
        self.ConfirmWarpDestination()
        eve.Message('WarpDriveActive')
        self.LogNotice('StartWarpIndication', self.warpDestText, 'autopilot =', sm.GetService('autoPilot').GetState())

    def OnSpecialFX(self, shipID, moduleID, moduleTypeID, targetID, otherTypeID, guid, isOffensive, start, active, duration = -1, repeat = None, startTime = None, timeFromStart = 0, graphicInfo = None):
        self.LogInfo('Space::OnSpecialFX - ', guid)
        if util.IsFullLogging():
            self.LogInfo(shipID, moduleID, moduleTypeID, targetID, otherTypeID, guid, isOffensive, start, active, duration, repeat)
        if shipID == eve.session.shipid:
            if guid == 'effects.JumpOut':
                bp = sm.StartService('michelle').GetBallpark()
                slimItem = bp.GetInvItem(targetID)
                locations = [slimItem.jumps[0].locationID, slimItem.jumps[0].toCelestialID]
                cfg.evelocations.Prime(locations)
                solID = slimItem.jumps[0].locationID
                destID = slimItem.jumps[0].toCelestialID
                sm.GetService('logger').AddText(localization.GetByLabel('UI/Inflight/Messages/LoggerJumpingToGateInSystem', gate=destID, system=solID))
                self.IndicateAction(localization.GetByLabel('UI/Inflight/Messages/Jumping'), localization.GetByLabel('UI/Inflight/Messages/DestinationInSystem', gate=destID, system=solID))
            elif guid == 'effects.JumpOutWormhole':
                if otherTypeID is None:
                    otherTypeID = 0
                wormholeClasses = {0: 'UI/Wormholes/Classes/Space',
                 1: 'UI/Wormholes/Classes/UnknownSpace',
                 2: 'UI/Wormholes/Classes/UnknownSpace',
                 3: 'UI/Wormholes/Classes/UnknownSpace',
                 4: 'UI/Wormholes/Classes/UnknownSpace',
                 5: 'UI/Wormholes/Classes/DeepUnknownSpace',
                 6: 'UI/Wormholes/Classes/DeepUnknownSpace',
                 7: 'UI/Wormholes/Classes/HighSecuritySpace',
                 8: 'UI/Wormholes/Classes/LowSecuritySpace',
                 9: 'UI/Wormholes/Classes/NullSecuritySpace',
                 12: 'UI/Wormholes/Classes/DeepUnknownSpace',
                 13: 'UI/Wormholes/Classes/UnknownSpace'}
                wormholeClassLabelName = wormholeClasses.get(otherTypeID, 'UI/Wormholes/Classes/Space')
                wormholeClassName = localization.GetByLabel(wormholeClassLabelName)
                self.IndicateAction(localization.GetByLabel('UI/Inflight/Messages/JumpingThroughWormhole'), localization.GetByLabel('UI/Inflight/Messages/NotifyJumpingThroughWormhole', wormholeClass=wormholeClassName))
            elif guid in ('effects.JumpDriveOut', 'effects.JumpDriveOutBO'):
                self.IndicateAction(localization.GetByLabel('UI/Inflight/Messages/Jumping'), localization.GetByLabel('UI/Inflight/Messages/NotifyJumpingToBeacon'))

    def OnDockingAccepted(self, dockingStartPos, dockingEndPos, stationID):
        eve.Message('DockingAccepted')
        self.IndicateAction(localization.GetByLabel('UI/Inflight/Messages/Docking'), localization.GetByLabel('UI/Inflight/Messages/DestinationStation', station=stationID))

    def CanWarp(self, targetID = None, forTut = False):
        tutorialBrowser = sm.GetService('tutorial').GetTutorialBrowser(create=0)
        if tutorialBrowser and not forTut and hasattr(tutorialBrowser, 'current'):
            _tutorialID, _pageNo, _pageID, _pageCount, _sequenceID, _VID, _pageActionID = tutorialBrowser.current
            if _tutorialID is not None and _sequenceID is not None:
                return sm.GetService('tutorial').CheckWarpDriveActivation(_sequenceID, _tutorialID)
        return 1

    def OnReleaseBallpark(self):
        self.flashTransform = None

    def CheckWarpDestination(self, warpPoint, destinationPoint, egoPoint, angularTolerance, distanceTolerance):
        destinationOffset = [destinationPoint[0] - warpPoint[0], destinationPoint[1] - warpPoint[1], destinationPoint[2] - warpPoint[2]]
        destinationDirection = [warpPoint[0] - egoPoint[0], warpPoint[1] - egoPoint[1], warpPoint[2] - egoPoint[2]]
        warpDirection = [destinationPoint[0] - egoPoint[0], destinationPoint[1] - egoPoint[1], destinationPoint[2] - egoPoint[2]]
        vlen = self.VectorLength(destinationDirection)
        destinationDirection = [ x / vlen for x in destinationDirection ]
        vlen = self.VectorLength(warpDirection)
        warpDirection = [ x / vlen for x in warpDirection ]
        angularDifference = warpDirection[0] * destinationDirection[0] + warpDirection[1] * destinationDirection[1] + warpDirection[2] * destinationDirection[2]
        angularDifference = min(max(-1.0, angularDifference), 1.0)
        angularDifference = math.acos(angularDifference)
        if abs(angularDifference) < angularTolerance or self.VectorLength(destinationOffset) < distanceTolerance:
            return True
        else:
            return False

    def VectorLength(self, vector):
        result = 0
        for i in vector:
            result += pow(i, 2)

        return pow(result, 0.5)

    def GetWarpDestinationName(self, id):
        """
            returns the evelocations name if available, otherwise a typeName
            with some special-casing for specific groupID's
        """
        name = None
        item = uix.GetBallparkRecord(id)
        if item is None or item.categoryID not in [const.groupAsteroid]:
            name = cfg.evelocations.Get(id).name
        if not name and item:
            name = cfg.invtypes.Get(item.typeID).typeName
        return name

    def ConfirmWarpDestination(self):
        destinationItemID, destinationBookmarkID, destinationfleetMemberID, destinationPosition, actualDestinationPosition = self.warpDestinationCache
        self.warpDestText = ''
        self.warpDestinationCache[4] = None
        ballPark = sm.GetService('michelle').GetBallpark()
        if not ballPark:
            return
        egoball = ballPark.GetBall(ballPark.ego)
        if destinationItemID:
            if destinationItemID in ballPark.balls:
                b = ballPark.balls[destinationItemID]
                if self.CheckWarpDestination(destinationPosition, (b.x, b.y, b.z), (egoball.x, egoball.y, egoball.z), math.pi / 32, 20000000):
                    self.warpDestinationCache[4] = (b.x, b.y, b.z)
                    name = self.GetWarpDestinationName(destinationItemID)
                    self.warpDestText = localization.GetByLabel('UI/Inflight/Messages/WarpDestination', destinationName=name) + '<br>'
        elif destinationBookmarkID:
            bookmark = sm.GetService('addressbook').GetBookmark(destinationBookmarkID)
            if bookmark is not None:
                if bookmark.x is None:
                    if bookmark.memo:
                        titleEndPosition = bookmark.memo.find('\t')
                        if titleEndPosition > -1:
                            memoTitle = bookmark.memo[:titleEndPosition]
                        else:
                            memoTitle = bookmark.memo
                        self.warpDestText = localization.GetByLabel('UI/Inflight/Messages/WarpDestination', destinationName=memoTitle) + '<br>'
                        if bookmark.itemID is not None:
                            b = ballPark.balls[bookmark.itemID]
                            if self.CheckWarpDestination(destinationPosition, (b.x, b.y, b.z), (egoball.x, egoball.y, egoball.z), math.pi / 32, 20000000):
                                self.warpDestinationCache[4] = (b.x, b.y, b.z)
                elif self.CheckWarpDestination(destinationPosition, (bookmark.x, bookmark.y, bookmark.z), (egoball.x, egoball.y, egoball.z), math.pi / 32, 20000000):
                    if bookmark.memo:
                        titleEndPosition = bookmark.memo.find('\t')
                        if titleEndPosition > -1:
                            memoTitle = bookmark.memo[:titleEndPosition]
                        else:
                            memoTitle = bookmark.memo
                        self.warpDestText = localization.GetByLabel('UI/Inflight/Messages/WarpDestination', destinationName=memoTitle) + '<br>'
                        self.warpDestinationCache[4] = (bookmark.x, bookmark.y, bookmark.z)

    def IndicateWarp(self):
        """
            returns the header text and subtext to display above HUD when ship is warping.
            Can return None, None which means there is nothing to display
        """
        destinationItemID, destinationBookmarkID, destinationfleetMemberID, destinationPosition, actualDestinationPosition = self.warpDestinationCache
        if not destinationPosition:
            self.LogError('Space::IndicateWarp: Something is messed up, didnt get ballpark coordinates to verify warp')
            return (None, None)
        ballPark = sm.GetService('michelle').GetBallpark()
        if not ballPark:
            self.LogWarn('Space::IndicateWarp: Trying to indicate warp without a ballpark?')
            return (None, None)
        centeredDestText = '<center>' + getattr(self, 'warpDestText', '')
        text = centeredDestText
        egoball = ballPark.GetBall(ballPark.ego)
        if actualDestinationPosition is not None:
            warpDirection = [actualDestinationPosition[0] - egoball.x, actualDestinationPosition[1] - egoball.y, actualDestinationPosition[2] - egoball.z]
        else:
            warpDirection = [destinationPosition[0] - egoball.x, destinationPosition[1] - egoball.y, destinationPosition[2] - egoball.z]
        dist = self.VectorLength(warpDirection)
        if dist:
            distanceText = '<center>' + localization.GetByLabel('UI/Inflight/ActiveItem/SelectedItemDistance', distToItem=util.FmtDist(dist))
            if actualDestinationPosition is None:
                text = localization.GetByLabel('UI/Inflight/Messages/WarpIndicatorWithDistanceAndBubble', warpDestination=centeredDestText, distance=distanceText)
            else:
                text = localization.GetByLabel('UI/Inflight/Messages/WarpIndicatorWithDistance', warpDestination=centeredDestText, distance=distanceText)
        self.LogInfo('Space::IndicateWarp', text)
        return (localization.GetByLabel('UI/Inflight/Messages/WarpDriveActive'), text)

    def Indicate_thread(self, *args):
        indicateProperties = self.GetHUDActionIndicateProperties()
        oldIndicateProperties = getattr(self, 'indicateProperties', None)
        if oldIndicateProperties is None or indicateProperties != oldIndicateProperties:
            wasDisplayed = self.UpdateHUDActionIndicator(storeText=False)
            if wasDisplayed:
                self.indicateProperties = indicateProperties

    def GetHUDActionIndicateProperties(self, *args):
        """
            The indicate properties will tell us if actually need to update the indicate text.
        """
        ballpark = sm.GetService('michelle').GetBallpark()
        if not ballpark:
            return
        ball = ballpark.GetBall(ballpark.ego)
        if ball is None:
            return
        if ball.mode == destiny.DSTBALL_STOP:
            speed = ball.GetVectorDotAt(blue.os.GetSimTime()).Length()
        else:
            speed = None
        alignTargetID, aligningToBookmark = sm.GetService('menu').GetLastAlignTarget()
        return (ball.followId,
         ball.mode,
         ball.followRange,
         alignTargetID or aligningToBookmark,
         speed)

    def UpdateHUDActionIndicator(self, storeText = False, *args):
        header, subText = self.GetHeaderAndSubtextFromBall()
        if header is not None and subText is not None:
            return self.IndicateAction(header, subText, storeText=storeText)
        if not self.setIndicationText:
            self.ClearIndicateText()

    def GetHeaderAndSubtextFromBall(self, *args):
        """
            returns the header text and subtext for the ship's actions.
            Can return None, None which means there is nothing to display
        """
        ballpark = sm.GetService('michelle').GetBallpark()
        if not ballpark:
            return (None, None)
        ball = ballpark.GetBall(ballpark.ego)
        if ball is None:
            return (None, None)
        return self.GetHeaderAndSubtextForActionIndication(ball.mode, ball.followId, ball.followRange, ball=ball)

    def GetHeaderAndSubtextForActionIndication(self, ballMode, followId, followRange, ball = None, *args):
        """
            returns the header text and subtext for the ship's actions.
            Can return None, None which means there is nothing to display
        """
        headerText = None
        subText = None
        if ballMode != destiny.DSTBALL_GOTO and ball is not None:
            sm.GetService('menu').ClearAlignTargets()
        if followId != 0 and ballMode in (destiny.DSTBALL_ORBIT, destiny.DSTBALL_FOLLOW):
            name = sm.GetService('space').GetWarpDestinationName(followId)
            myRange = followRange
            rangeText = util.FmtDist(myRange, maxdemicals=0)
            if ballMode == destiny.DSTBALL_ORBIT:
                headerText = localization.GetByLabel('UI/Inflight/Messages/OrbitingHeader')
                subText = localization.GetByLabel('UI/Inflight/Messages/OrbitingSubText', targetName=name, rangeText=rangeText)
            elif ballMode == destiny.DSTBALL_FOLLOW:
                if myRange in (const.approachRange, 0):
                    headerText = localization.GetByLabel('UI/Inflight/Messages/ApproachingHeader')
                    subText = localization.GetByLabel('UI/Inflight/Messages/ApproachingSubText', targetName=name)
                else:
                    headerText = localization.GetByLabel('UI/Inflight/Messages/KeepingAtRangeHeader')
                    subText = localization.GetByLabel('UI/Inflight/Messages/KeepingAtRangeSubText', targetName=name, rangeText=rangeText)
        elif ballMode == destiny.DSTBALL_GOTO:
            alignTargetID, aligningToBookmark = sm.GetService('menu').GetLastAlignTarget()
            if not alignTargetID and not aligningToBookmark:
                return (None, None)
            headerText = localization.GetByLabel('UI/Inflight/Messages/AligningHeader')
            if alignTargetID:
                if util.IsCharacter(alignTargetID):
                    subText = localization.GetByLabel('UI/Inflight/Messages/AligningToPlayerSubText', charID=alignTargetID)
                else:
                    try:
                        name = sm.GetService('space').GetWarpDestinationName(alignTargetID)
                        subText = localization.GetByLabel('UI/Inflight/Messages/AligningToLocationSubText', targetName=name)
                    except:
                        subText = localization.GetByLabel('UI/Inflight/Messages/AligningUnknownSubText')

            elif aligningToBookmark:
                subText = localization.GetByLabel('UI/Inflight/Messages/AligningToBookmarkSubText')
            else:
                subText = localization.GetByLabel('UI/Inflight/Messages/AligningUnknownSubText')
        elif ballMode == destiny.DSTBALL_WARP:
            return self.IndicateWarp()
        return (headerText, subText)

    def SetIndicationTextForcefully(self, ballMode, followId, followRange):
        """
            this function will forcefully set the text to what we tell it. That's needed to show the player
            right away what actions they took, even before the server can take the action.
            The ball info is given time to update, and then the set text is cleared and the function
            that updates the HUD automatically takes care of the rest.
        """
        header, subText = self.GetHeaderAndSubtextForActionIndication(ballMode, followId, followRange)
        self.DoSetIndicationTextForcefully(header, subText)

    def DoSetIndicationTextForcefully(self, headerText, subText):
        self.ClearShortcutText()
        if headerText:
            self.CreateIndicationTextsIfNeeded()
            self.IndicateAction(headerText, subText, storeText=True)
            self.caption.SetRGB(0.5, 0.5, 0.5, 1.0)
            uicore.animations.BlinkOut(self.caption, startVal=1.0, endVal=0.3, duration=0.8, loops=2, curveType=uiconst.ANIM_WAVE)
            uicore.animations.BlinkOut(self.indicationtext, startVal=1.0, endVal=0.3, duration=0.8, loops=2, curveType=uiconst.ANIM_WAVE)
        uthread.new(self.ClearForcefullySetText_thread, headerText, subText)

    def ClearForcefullySetText_thread(self, header, subText, *args):
        blue.pyos.synchro.SleepWallclock(2000)
        if self.setIndicationText is None:
            return
        if self.setIndicationText == (header, subText):
            sm.GetService('space').ClearIndicateText()
            sm.GetService('space').UpdateHUDActionIndicator()
            uicore.animations.SpColorMorphToWhite(self.caption, duration=0.2)
            uicore.animations.SpColorMorphToWhite(self.indicationtext, duration=0.2)

    def ClearIndicateText(self, *args):
        self.indicateProperties = None
        if self.indicationtext is not None and not self.indicationtext.destroyed:
            self.indicationtext.display = False
            self.indicationtext.text = ''
        if self.caption is not None and not self.caption.destroyed:
            self.caption.display = False
            self.caption.text = ''
        self.setIndicationText = None

    def IndicateAction(self, header = None, subText = None, storeText = True, *args):
        if not storeText and self.setIndicationText or getattr(self, 'displayingShortcut', False):
            return False
        if storeText:
            self.setIndicationText = (header, subText)
            self.indicateProperties = None
        if header is None and subText is None:
            if self.indicationtext is not None and not self.indicationtext.destroyed:
                self.indicationtext.display = False
            if self.caption is not None and not self.caption.destroyed:
                self.caption.display = False
            return False
        if uicore.layer.shipui.sr.indicationContainer is None or uicore.layer.shipui.sr.indicationContainer.destroyed:
            self.indicateProperties = None
            return False
        if self.indicationtext is None or self.indicationtext.destroyed or self.indicationtext.parent is None:
            self.CreateIndicationTextsIfNeeded()
        else:
            self.indicationtext.display = True
            self.caption.display = True
        self.indicationtext.text = '<center>' + subText
        self.caption.text = header
        if uicore.layer.shipui.sr.indicationContainer is None:
            self.indicateProperties = None
            return False
        self.indicationtext.left = (uicore.layer.shipui.sr.indicationContainer.width - self.indicationtext.width) / 2
        self.indicationtext.top = self.caption.top + self.caption.height
        return True

    def CreateIndicationTextsIfNeeded(self, *args):
        if self.indicationtext is None or self.indicationtext.destroyed:
            self.indicationtext = uicontrols.EveLabelMedium(parent=uicore.layer.shipui.sr.indicationContainer, name='indicationtext2', text='', align=uiconst.TOPLEFT, width=400, state=uiconst.UI_DISABLED)
        if self.caption is None or self.caption.destroyed:
            self.caption = uicontrols.CaptionLabel(text='', parent=uicore.layer.shipui.sr.indicationContainer, align=uiconst.CENTERTOP, state=uiconst.UI_DISABLED, top=1)

    def OnShipUIReset(self, *args):
        """
            called when the the shipui is reset and indicationContainer is destroyed, because we need to refresh some things
            to make sure our text continues to display when a new one has been created
        """
        self.indicateProperties = None
        if self.indicationtext:
            self.indicationtext.Close()
        if self.caption:
            self.caption.Close()

    def ChangeHUDActionVisiblity(self, doDisplay = True):
        if doDisplay:
            if self.indicationtext:
                self.indicationtext.display = True
            if self.caption:
                self.caption.display = True
        else:
            if self.indicationtext:
                self.indicationtext.display = False
            if self.caption:
                self.caption.display = False

    def SetShortcutText(self, headerText, text, delayMs = 0, *args):
        if uicore.layer.shipui.sr.indicationContainer is None or uicore.layer.shipui.sr.indicationContainer.destroyed:
            self.shortcutText = None
            self.shortcutSubText = None
            return
        if self.shortcutText is None or self.shortcutText.destroyed:
            self.shortcutText = uicontrols.CaptionLabel(text='', parent=uicore.layer.shipui.sr.indicationContainer, align=uiconst.CENTERTOP, state=uiconst.UI_DISABLED, top=1)
        else:
            self.shortcutText.display = True
        if self.shortcutSubText is None or self.shortcutSubText.destroyed:
            self.shortcutSubText = uicontrols.EveLabelMedium(parent=uicore.layer.shipui.sr.indicationContainer, name='shortcutSubText', text='', align=uiconst.CENTERTOP, width=400, state=uiconst.UI_DISABLED, top=-20)
        else:
            self.shortcutSubText.display = True
            self.shortcutSubText.SetAlpha(1.0)
        self.shortcutText.text = headerText
        self.shortcutSubText.text = text
        self.shortcutSubText.left = (uicore.layer.shipui.sr.indicationContainer.width - self.shortcutSubText.width) / 2
        self.shortcutSubText.top = self.shortcutText.top + self.shortcutText.height
        self.displayingShortcut = True
        if delayMs:
            uthread.new(self._DelayShowShortcutMsg, delayMs)
        else:
            self.ChangeHUDActionVisiblity(doDisplay=False)

    def _DelayShowShortcutMsg(self, delayMs):
        if self.shortcutSubText is None or self.shortcutSubText.destroyed:
            return
        self.shortcutSubText.SetAlpha(0.0)
        self.shortcutText.SetAlpha(0.0)
        blue.pyos.synchro.SleepWallclock(delayMs)
        if self.displayingShortcut:
            self.ChangeHUDActionVisiblity(doDisplay=False)
        if self.shortcutSubText:
            self.shortcutSubText.SetAlpha(1.0)
        if self.shortcutText:
            self.shortcutText.SetAlpha(1.0)

    def ClearShortcutText(self, *args):
        self.displayingShortcut = False
        self.ChangeHUDActionVisiblity(doDisplay=True)
        if self.shortcutText and not self.shortcutText.destroyed:
            self.shortcutText.display = False
            self.shortcutText.text = ''
        if self.shortcutSubText and not self.shortcutSubText.destroyed:
            self.shortcutSubText.display = False
            self.shortcutSubText.text = ''

    def GetHeader(self):
        if self.caption is None or self.caption.destroyed:
            return
        return self.caption.text

    def StopWarpIndication(self):
        self.LogNotice('StopWarpIndication', getattr(self, 'warpDestText', '-'), 'autopilot =', sm.GetService('autoPilot').GetState())
        self.warpDestinationCache = [None,
         None,
         None,
         None,
         None]
        self.ClearIndicateText()
        self.transmission.StopWarpIndication()
        if self.planetManager is not None:
            self.planetManager.StopPlanetPreloading()

    def KillIndicationTimer(self, guid):
        self.warpDestinationCache = [None,
         None,
         None,
         None,
         None]
        if hasattr(self, guid):
            delattr(self, guid)
            self.ClearIndicateText()

    def StartPartitionDisplayTimer(self, boxsize = 7):
        self.StopPartitionDisplayTimer()
        settings.user.ui.Set('partition_box_size', boxsize)
        self.partitionDisplayTimer = base.AutoTimer(50, self.UpdatePartitionDisplay)

    def StopPartitionDisplayTimer(self):
        self.partitionDisplayTimer = None
        self.CleanPartitionDisplay()

    def UpdatePartitionDisplay(self):
        if getattr(self, 'partitionTF', None) is None:
            scene = sm.GetService('sceneManager').GetRegisteredScene('default')
            self.partitionTF = trinity.EveTransform()
            scene.objects.append(self.partitionTF)
        boxRange = settings.user.ui.Get('partition_box_size', 7)
        allboxes = settings.user.ui.Get('partition_box_showall', 1)
        ballpark = sm.GetService('michelle').GetBallpark()
        if not ballpark:
            self.StopPartitionDisplayTimer()
            return
        egoball = ballpark.GetBall(ballpark.ego)
        if allboxes == 1:
            boxRange = range(boxRange, 8)
        else:
            boxRange = [boxRange]
        numChildren = len(self.partitionTF.children)
        count = [0]

        def GetTransform():
            if count[0] >= numChildren:
                tf = blue.resMan.LoadObject('res:/model/global/partitionBox.red')
                self.partitionTF.children.append(tf)
                count[0] += 1
                return tf
            tf = self.partitionTF.children[count[0]]
            count[0] += 1
            return tf

        for boxSize in boxRange:
            boxes = ballpark.GetActiveBoxes(boxSize)
            width, coords = boxes
            if not boxes:
                continue
            for x, y, z in coords:
                tf = GetTransform()
                x = x - egoball.x + width / 2
                y = y - egoball.y + width / 2
                z = z - egoball.z + width / 2
                tf.scaling = (width, width, width)
                tf.translation = (x, y, z)

        while count[0] < numChildren:
            numChildren -= 1
            self.partitionTF.children.removeAt(numChildren)

    def CleanPartitionDisplay(self):
        if getattr(self, 'partitionTF', None) is None:
            return
        scene = sm.GetService('sceneManager').GetRegisteredScene('default')
        scene.objects.fremove(self.partitionTF)
        self.partitionTF = None

    def GetNebulaTextureForType(self, nebulaType):
        sceneName = cfg.graphics.Get(nebulaType).graphicFile
        sceneManager = sm.GetService('sceneManager')
        return sceneManager.DeriveTextureFromSceneName(sceneName)


class PlanetManager():

    def __init__(self):
        self.renderTarget = None
        self.processingList = []
        self.planets = []
        self.planetWarpingList = []
        self.worker = None
        self.format = trinity.PIXEL_FORMAT.B8G8R8A8_UNORM
        self.maxSize = 2048
        self.maxSizeLimit = 2048

    def Release(self):
        self.planets = []

    def RegisterPlanetBall(self, planet):
        self.planets.append(planet)

    def UnRegisterPlanetBall(self, planet):
        planet = self.GetPlanet(planet.id)
        if planet is not None:
            self.planets.remove(planet)

    def DoPlanetPreprocessing(self, planet, size):
        self.processingList.append((planet, size))
        if self.worker is not None:
            if self.worker.alive:
                return
        self.worker = uthread.new(self.PreProcessAll)

    def CreateRenderTarget(self):
        textureQuality = gfxsettings.Get(gfxsettings.GFX_TEXTURE_QUALITY)
        self.maxSizeLimit = size = self.maxSize >> textureQuality
        rt = None
        while rt is None or not rt.isValid:
            rt = trinity.Tr2RenderTarget(2 * size, size, 0, self.format)
            if not rt.isValid:
                if size < 2:
                    return
                self.maxSizeLimit = size = size / 2
                rt = None

        return rt

    def PreProcessAll(self):
        if self.renderTarget is None:
            self.renderTarget = self.CreateRenderTarget()
        while len(self.processingList) > 0:
            planet, size = self.processingList.pop(0)
            if size > self.maxSizeLimit:
                size = self.maxSizeLimit
            planet.DoPreProcessEffect(size, self.format, self.renderTarget)

    def GetPlanet(self, ballid):
        for planet in self.planets:
            if planet.id == ballid:
                return planet

    def StopPlanetPreloading(self):
        for planet in self.planets:
            planet.WarpStopped()

    def DistanceFromSegment(self, p, p0, p1, v, c2):
        w = geo2.Vec3Subtract(p, p0)
        c1 = geo2.Vec3Dot(v, w)
        if c1 <= 0:
            return None
        if c2 <= c1:
            return geo2.Vec3Distance(p, p1)
        return geo2.Vec3Distance(p, geo2.Vec3Add(p0, geo2.Vec3Scale(v, c1 / c2)))

    def CheckPlanetPreloadingOnWarp(self, destinationWarpPoint):
        uthread.new(self._CheckPlanetPreloadingOnWarp, destinationWarpPoint)

    def _CheckPlanetPreloadingOnWarp(self, destinationWarpPoint):
        ballpark = sm.GetService('michelle').GetBallpark()
        if ballpark is None:
            return
        shipBall = ballpark.GetBall(eve.session.shipid)
        if shipBall is None:
            return
        p1 = destinationWarpPoint
        p0 = (shipBall.x, shipBall.y, shipBall.z)
        v = geo2.Vec3Subtract(p1, p0)
        c2 = geo2.Vec3Dot(v, v)
        for planet in self.planets:
            blue.pyos.BeNice()
            planetBall = ballpark.GetBall(planet.id)
            if planetBall is not None:
                p = (planetBall.x, planetBall.y, planetBall.z)
                distance = self.DistanceFromSegment(p, p0, p1, v, c2)
                if distance is not None:
                    planet.PrepareForWarp(distance, destinationWarpPoint)


space = SpaceMgr
