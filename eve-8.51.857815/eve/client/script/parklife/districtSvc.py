#Embedded file name: eve/client/script/parklife\districtSvc.py
import geo2
import util
import xtriui
import uthread
import states as state
import blue
import decometaclass
import trinity
import service
import planet
import localization
from carbon.common.script.sys.row import Row

class DistrictTargetBall(decometaclass.WrapBlueClass('destiny.ClientBall')):

    def __init__(self):
        self.model = trinity.EveRootTransform()


class DistrictSvc(service.Service):
    """
    Client side service which synchronizes state with the server side districtManager
    to fetch information on districts in the current system.
    """
    __guid__ = 'svc.district'
    __servicename__ = 'District'
    __displayname__ = 'District Service'
    __exportedcalls__ = {}
    __dependencies__ = ['michelle']
    __notifyevents__ = ['OnSessionChanged',
     'DoBallsAdded',
     'DoBallRemove',
     'OnOrbitalStrikeTargets',
     'OnOrbitalStrikeDamage',
     'OnDistrictBattle',
     'OnDistrictDisconnect',
     'DoBallsRemove']

    def Run(self, *args, **kwargs):
        self.balls = {}
        self.districts = {}
        self.district = None
        self.targets = {}
        self.connected = False
        self.brackets = None
        self.Reload()
        self.state = service.SERVICE_RUNNING

    def GetDistricts(self):
        """
        Returns a list of districts for the current system (if any)
        """
        return self.districts.values()

    def GetDistrictByPlanet(self, planetID):
        """
        Filters the list of districts by planetID.
        """
        districts = [ (district['index'], district) for district in self.GetDistricts() if district['planetID'] == planetID ]
        return [ district for index, district in sorted(districts) ]

    def GetDistrict(self, districtID):
        return self.districts.get(districtID)

    def GetTargetBall(self, ballID):
        return self.balls.get(ballID)

    def Reload(self):
        """
        Queries the district manager using RemoteSvc. We need to be careful with this for now
        because this service is designed to be called using ServiceProxy and we do not have an
        impementation of that for the EVE client yet. RemoteSvc will work for any methods with
        the resolve param marked const.cluster.NODE_ANY_SERVER.
        """
        self.DisableDistrict()
        self.districts = {}
        if session.solarsystemid is not None:
            self.districts = sm.RemoteSvc('districtLocation').GetDistrictsBySolarSystem(session.solarsystemid2)
            for district in self.districts.itervalues():
                district['name'] = localization.GetImportantByLabel('UI/Locations/LocationDistrictFormatter', solarSystemID=district['solarSystemID'], romanCelestialIndex=util.IntToRoman(district['celestialIndex']), districtIndex=district['index'])

            self._AddDistrictsToPlanets()

    def EnableDistrict(self, districtID, force = False):
        self.district = self.GetDistrict(districtID)
        if not self.district.get('interactable', False) and not force:
            self.district = None
            return
        if self.district:
            if self.brackets:
                self.brackets.Close()
            self.brackets = xtriui.DistrictBracket(self.district)

    def DisableDistrict(self, districtID = None):
        if districtID and self.district and districtID != self.district['districtID']:
            return
        with util.ExceptionEater('DisconnectDistrict'):
            self.DisconnectDistrict()
        if self.brackets:
            self.brackets.Close()
        self.brackets = None
        self.district = None
        self.battle = None

    def ReloadDistrict(self):
        if self.district:
            districtID = self.district['districtID']
            self.DisableDistrict(districtID)
            self.EnableDistrict(districtID)

    def ConnectDistrict(self):
        if self.district and not self.connected:
            try:
                self.OnOrbitalStrikeTargets(sm.RemoteSvc('orbitalStrikeMgr').Connect(self.district['districtID']))
                self.connected = True
                if self.brackets:
                    self.brackets.SetConnected(True)
            finally:
                if self.brackets:
                    self.brackets.SetPending(False)

    def DisconnectDistrict(self):
        try:
            if self.connected:
                sm.RemoteSvc('orbitalStrikeMgr').Disconnect()
                self.connected = False
            if self.brackets:
                self.brackets.SetConnected(False)
            if len(self.targets):
                self.OnOrbitalStrikeTargets({})
        finally:
            if self.brackets:
                self.brackets.SetPending(False)

    def OnOrbitalStrikeTargets(self, targets):
        self.targets = targets
        for targetID, target in self.targets.iteritems():
            target['targetID'] = targetID

        sm.ScatterEvent('OnDistrictTargets', targets)
        uthread.new(self._LoadTargetBalls)

    def OnOrbitalStrikeDamage(self, request, report):
        """
        Called whenever we get damage feedback from an orbital strike.
        """
        for damage in report or []:
            invType = cfg.invtypes.GetIfExists(damage.get('typeID'))
            if invType is None:
                continue
            elif invType.groupID == const.groupInfantryDropsuit and damage.get('characterName') is not None:
                name = damage.get('characterName')
            else:
                name = invType.typeName
            target = sm.GetService('bracket').DisplayName(util.KeyVal(charID=damage.get('characterID'), corpID=damage.get('corporationID'), typeID=damage.get('typeID'), itemID=request['planetID'], allianceID=None), name)
            sm.GetService('logger').AddCombatMessage('AttackHits', {'isBanked': request['count'] > 1,
             'hitQualityText': '',
             'weapon': request['moduleTypeID'],
             'splash': '',
             'attackType': 'me',
             'damage': damage['shieldDamage'] + damage['armorDamage'],
             'target': target})
            blue.pyos.synchro.SleepWallclock(1200)

    def OnDistrictBattle(self, solarSystemID, districtID, battleID, status):
        district = self.GetDistrict(districtID)
        if district:
            if status == const.battleStatusCompleted:
                district['battles'].discard(battleID)
            else:
                district['battles'].add(battleID)
            self._DisplayDistrictBattles(district)

    def OnDistrictDisconnect(self, solarSystemID, districtID, userError = None):
        if self.district and districtID == self.district['districtID']:
            self.DisconnectDistrict()
            if userError:
                raise UserError(userError)

    def OnSessionChanged(self, isremote, session, change):
        """
        We need to reload districts whenever the solarsystem changes.
        """
        if 'solarsystemid' in change:
            self.Reload()
        if 'shipid' in change:
            self.DisconnectDistrict()

    def DoBallsAdded(self, balls):
        """
        Listens for when planet balls are added into the ballpark and creates balls
        for the districts on that planet.
        """
        if len([ ball for ball, item in balls if item.typeID == const.typePlanetEarthlike ]):
            self._AddDistrictsToPlanets()

    def DoBallsRemove(self, pythonBalls, isRelease):
        for ball, slimItem, terminal in pythonBalls:
            self.DoBallRemove(ball, slimItem, terminal)

    def DoBallRemove(self, ball, item, terminal):
        """
        Cleans up district balls whenever a planet ball is removed.
        """
        if item.typeID == const.typePlanetEarthlike:
            self._AddDistrictsToPlanets()

    def _AddDistrictsToPlanets(self):
        """
        Make sure that each district has been added to a planet ball so they display. Also
        update the state of any ongoing district battles.
        """
        ballpark = self.michelle.GetBallpark()
        if ballpark is None:
            return
        for district in self.districts.itervalues():
            if district.get('planet'):
                continue
            district['planet'] = ballpark.GetBall(district.get('planetID'))
            if district.get('planet'):
                direction = geo2.Vec3Normalize(planet.SurfacePoint(phi=district['latitude'], theta=district['longitude']).GetAsXYZTuple())
                district['uniqueName'] = 'district-%s' % district['districtID']
                district['planet'].AddDistrict(district['uniqueName'], direction, 0.1, False)
                self._DisplayDistrictBattles(district)

    def _LoadTargetBalls(self):
        """
        Make sure for each target we have a client side ball, and remove any
        targets that have been removed.
        """
        ballpark = self.michelle.GetBallpark()
        for targetID, target in self.targets.iteritems():
            district = self.districts.get(target['districtID'])
            if ballpark and district and district['planet'] and targetID not in self.balls:
                targetBall = self._CreateTargetBall(district, targetID)
                header = ['itemID',
                 'typeID',
                 'ownerID',
                 'groupID',
                 'categoryID',
                 'quantity',
                 'singleton',
                 'stacksize',
                 'locationID',
                 'flagID',
                 'charID',
                 'corpID',
                 'allianceID',
                 'securityStatus',
                 'jumps',
                 'orbitalState',
                 'planetID']
                targetItem = Row(header, [targetBall.id,
                 const.typeOrbitalTarget,
                 target['characterID'],
                 const.groupOrbitalTarget,
                 const.categoryCelestial,
                 1,
                 -1,
                 1,
                 target['districtID'],
                 0,
                 target['characterID'],
                 target['corporationID'],
                 None,
                 0,
                 [],
                 None,
                 None])
                ballpark.slimItems[targetBall.id] = targetItem
                cfg.evelocations.Hint(targetBall.id, [targetBall.id,
                 cfg.eveowners.Get(target['characterID']).name,
                 targetBall.x,
                 targetBall.y,
                 targetBall.z,
                 None])
                sm.GetService('target').OnTargetAdded(targetBall.id)

        for itemID, ball in self.balls.items():
            if itemID not in self.targets:
                sm.GetService('target').OnTargetLost(ball.id, None)
                sm.GetService('target').ArrangeTargets()
                uthread.new(self._DestroyTargetBall, itemID)

    def _CreateTargetBall(self, district, itemID):
        """
        Creates a new client side district ball. Used for targeting / gun tracking etc.
        """
        if itemID not in self.balls:
            ballpark = self.michelle.GetBallpark()
            if district and ballpark and district['planet']:
                direction = geo2.Vec3Normalize(planet.SurfacePoint(phi=district['latitude'], theta=district['longitude']).GetAsXYZTuple())
                translation = geo2.Vec3Scale(direction, district['planet'].radius)
                position = (district['planet'].x + translation[0], district['planet'].y + translation[1], district['planet'].z + translation[2])
                ball = DistrictTargetBall(ballpark.AddClientSideBall(position, True))
                ball.model.name = 'DistrictBall_%s' % itemID
                ball.model.translationCurve = ball
                ball.model.rotationCurve = ball
                scene = sm.GetService('sceneManager').GetRegisteredScene('default')
                scene.objects.append(ball.model)
                self.balls[itemID] = ball
        return self.balls.get(itemID)

    def _DestroyTargetBall(self, itemID):
        blue.synchro.SleepSim(5000)
        ball = self.balls.pop(itemID, None)
        if ball is None:
            return
        scene = sm.GetService('sceneManager').GetRegisteredScene('default')
        if scene and ball.model in scene.objects:
            scene.objects.remove(ball.model)
        ball.model = None
        ballpark = self.michelle.GetBallpark()
        if ballpark:
            ballpark.RemoveClientSideBall(ball.id)
            ballpark.slimItems.pop(ball.id, None)

    def _DisplayDistrictBattles(self, district):
        if district['planet']:
            district['planet'].EnableBattleForDistrict(district['uniqueName'], len(district['battles']) > 0)

    def _GetItemIDFromBallID(self, ballID):
        if self.balls:
            for itemID, ball in self.balls.iteritems():
                if ball.id == ballID:
                    return itemID

    def ActivateModule(self, moduleID):
        """
        Called from the shipUI whenever a weapon loaded with orbital ammo is triggered.
        """
        ballID = sm.GetService('state').GetExclState(state.activeTarget)
        targetID = self._GetItemIDFromBallID(ballID)
        if not targetID:
            raise UserError('OrbitalStrikeInvalidTarget')
        if not self.connected:
            return False
        sm.RemoteSvc('orbitalStrikeMgr').ActivateModule(moduleID, targetID)
        return True
