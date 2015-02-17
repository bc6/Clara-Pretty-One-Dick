#Embedded file name: eve/client/script/environment/spaceObject\Drone.py
"""
Drones are ships, but have overrides of some functions to make them simpler
"""
import blue
import eve.client.script.environment.spaceObject.ship as ship
import evegraphics.settings as gfxsettings
import eveSpaceObject
import eve.client.script.environment.model.turretSet as turretSet

class Drone(ship.Ship):
    """
        This class represents all drones: mining, utility, combat, fighter, fighterbombers
    """

    def LoadModel(self, fileName = None, loadedModel = None):
        """
        just calls the Ship-class's LoadModel(), but might override the redfile path
        """
        if self.IsDroneModelEnabled():
            fileName = self.typeData.get('graphicFile')
        else:
            fileName = 'res:/dx9/model/drone/DroneModelsDisabled.red'
        droneModel = blue.resMan.LoadObject(fileName)
        ship.Ship.LoadModel(self, fileName, droneModel)

    def Assemble(self):
        """
        stripped down version of Assemble
        """
        if not self.IsDroneModelEnabled():
            return
        self.FitBoosters(alwaysOn=True, enableTrails=False)
        self.SetupAmbientAudio()
        if hasattr(self.model, 'ChainAnimationEx'):
            self.model.ChainAnimationEx('NormalLoop', 0, 0, 1.0)

    def FitHardpoints(self, blocking = False):
        if self.fitted:
            return
        if self.model is None:
            self.LogWarn('FitHardpoints - No model')
            return
        self.fitted = True
        if not gfxsettings.Get(gfxsettings.UI_TURRETS_ENABLED):
            return
        groupID = self.typeData.get('groupID', None)
        raceName = self.typeData.get('sofRaceName', None)
        droneGroup = eveSpaceObject.droneGroupFromTypeGroup.get(groupID, None)
        if droneGroup is None:
            self.LogError('FitHardpoints - no gfx drone group for groupID ' + str(groupID))
            return
        turretGfxIDs = eveSpaceObject.droneTurretGfxID.get(droneGroup, None)
        if turretGfxIDs is None:
            self.LogError('FitHardpoints - no turret gfxID info for drone group ' + str(droneGroup))
            return
        turretGraphicID = turretGfxIDs[1]
        if turretGfxIDs[0] is not None:
            if raceName is not None:
                turretGraphicID = turretGfxIDs[0].get(raceName, turretGfxIDs[1])
        if turretGraphicID is not None:
            ts = turretSet.TurretSet.AddTurretToModel(self.model, turretGraphicID, 1)
            if ts is not None and self.modules is not None:
                self.modules[self.id] = ts

    def Explode(self):
        if not self.IsDroneModelEnabled() or not gfxsettings.Get(gfxsettings.UI_EXPLOSION_EFFECTS_ENABLED):
            return False
        return ship.Ship.Explode(self)

    def IsDroneModelEnabled(self):
        """
        returns if we show this drone model
        """
        groupID = self.typeData.get('groupID', None)
        droneGroup = eveSpaceObject.droneGroupFromTypeGroup.get(groupID, None)
        if droneGroup == eveSpaceObject.gfxDroneGroupNpc:
            return True
        return gfxsettings.Get(gfxsettings.UI_DRONE_MODELS_ENABLED)
