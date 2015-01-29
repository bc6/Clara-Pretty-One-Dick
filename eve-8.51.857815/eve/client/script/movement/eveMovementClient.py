#Embedded file name: eve/client/script/movement\eveMovementClient.py
"""
This service extends the common movement service and adds the client specific functionality.
"""
import GameWorld
import geo2
import log
import sys
from carbon.common.script.movement.movementStates import MovementStates
from carbon.common.script.movement.movementService import CommonMovementComponent
from carbon.client.script.movement.movementClient import MovementClient

class MovementClientComponent(CommonMovementComponent):
    __guid__ = 'movement.MovementClientComponent'

    def __init__(self):
        CommonMovementComponent.__init__(self)
        self.IsFlyMode = False
        self.flySpeed = 0.15
        self.relay = None


class EveMovementClient(MovementClient):
    __guid__ = 'svc.eveMovementClient'
    __replaceservice__ = 'movementClient'
    __exportedcalls__ = MovementClient.__exportedcalls__.copy()
    __exportedcalls__.update({})
    __notifyevents__ = MovementClient.__notifyevents__[:]
    __notifyevents__.extend(['OnEntityTeleport'])
    __dependencies__ = MovementClient.__dependencies__[:]
    __dependencies__.extend(['worldSpaceClient', 'mouseInput'])

    def Run(self, *etc):
        MovementClient.Run(self)
        self.movementStates = MovementStates()
        self.cameraClient = sm.GetService('cameraClient')
        self.gameWorldClient = sm.GetService('gameWorldClient')
        self.mouseInput.RegisterCallback(const.INPUT_TYPE_MOUSEDOWN, self.OnMouseDown)
        self.mouseInput.RegisterCallback(const.INPUT_TYPE_MOUSEUP, self.OnMouseUp)
        self.mouseInput.RegisterCallback(const.INPUT_TYPE_MOUSEMOVE, self.OnMouseMove)
        self.mouseInput.RegisterCallback(const.INPUT_TYPE_DOUBLECLICK, self.OnDoubleClick)

    def Stop(self, stream):
        if sm.IsServiceRunning('mouseInput'):
            self.mouseInput.UnRegisterCallback(const.INPUT_TYPE_MOUSEDOWN, self.OnMouseDown)
            self.mouseInput.UnRegisterCallback(const.INPUT_TYPE_MOUSEUP, self.OnMouseUp)
            self.mouseInput.UnRegisterCallback(const.INPUT_TYPE_MOUSEMOVE, self.OnMouseMove)
            self.mouseInput.UnRegisterCallback(const.INPUT_TYPE_DOUBLECLICK, self.OnDoubleClick)

    def CreateComponent(self, name, state):
        component = MovementClientComponent()
        component.InitializeCapsuleInfo(state)
        component.characterControllerInfo.stepHeight = const.AVATAR_STEP_HEIGHT
        return component

    def SetupComponent(self, entity, component):
        """
        Gets called once all components have been registered.
        Use this to setup stuff which references other components
        """
        MovementClient.SetupComponent(self, entity, component)
        component.moveModeManager.movementBroadcastEnabled = not self.entityService.IsClientSideOnly(entity.scene.sceneID)
        component.IsFlyMode = False
        component.flySpeed = 0.15

    def UnRegisterComponent(self, entity, component):
        MovementClient.UnRegisterComponent(self, entity, component)

    def ToggleFlyMode(self):
        myMovement = self.entityService.GetPlayerEntity().GetComponent('movement')
        myMovement.IsFlyMode = not myMovement.IsFlyMode
        if myMovement.IsFlyMode:
            my_mode = GameWorld.FlyMode()
            my_mode.velocity = (0.0, 0.01, 0.0)
        else:
            my_mode = GameWorld.PlayerInputMode()
        myMovement.moveModeManager.PushMoveMode(my_mode)

    def TryFlyUpdate(self):
        """Update my FlyMode velocity, but only if I'm actually *in* FlyMode."""
        me = self.entityService.GetPlayerEntity()
        if me is not None:
            myMovement = me.GetComponent('movement')
            if myMovement and myMovement.IsFlyMode:
                newVel = (0, 0, 0)
                if self.drive:
                    activeCamera = self.cameraClient.GetActiveCamera()
                    cameraDir = geo2.Vec3Subtract(activeCamera.GetPointOfInterest(), activeCamera.GetPosition())
                    newVel = geo2.Vec3Scale(geo2.Vec3Normalize(cameraDir), myMovement.flySpeed)
                try:
                    myMovement.moveModeManager.GetCurrentMode().velocity = newVel
                except AttributeError:
                    log.LogException()
                    sys.exc_clear()
                    myMovement.IsFlyMode = False

    def OnMouseDown(self, button, posX, posY, entityID):
        self.drive = True
        self.TryFlyUpdate()

    def OnMouseMove(self, deltaX, deltaY, entityID):
        self.TryFlyUpdate()

    def OnMouseUp(self, button, posX, posY, entityID):
        self.drive = False
        self.TryFlyUpdate()

    def OnDoubleClick(self, entityID):
        self.PathPlayerToCursorLocation()

    def ProcessEntityMove(self, entid):
        pass

    def OnEntityTeleport(self, charid, newPosition, newRotation):
        entity = self.entityService.FindEntityByID(charid)
        if entity:
            positionComponent = entity.GetComponent('position')
            positionComponent.rotation = newRotation
            positionComponent.position = newPosition

    def _PickPointToPath(self):
        """
        Picks the point currently under the cursor and does some fancywork to try and 
        find the floor. Returns a tuple representing the position to path too.
        """
        picked = self.cameraClient.GetActiveCamera().PerformPick(uicore.uilib.x, uicore.uilib.y, session.charid)
        if picked is None:
            return
        else:
            point = geo2.Vector(*picked[0])
            height = self.gameWorldClient.GetFloorHeight(point, session.worldspaceid)
            destination = geo2.Vector(point.x, height, point.z)
            return destination

    def PathPlayerToCursorLocation(self):
        """
        Makes use of the Kynapse path finding move mode to saunter along to the correct 
        point. Selects point currently under cursor.
        """
        playerEntity = self.entityService.GetPlayerEntity()
        if playerEntity is None:
            return
        aoSvc = sm.GetService('actionObjectClientSvc')
        if aoSvc.IsEntityUsingActionObject(playerEntity.entityID) is True:
            return
        myMovement = playerEntity.GetComponent('movement')
        destination = self._PickPointToPath()
        if destination is None:
            return
        sm.GetService('debugRenderClient').ClearAllShapes()
        sm.GetService('debugRenderClient').RenderSphere(destination, 0.2, 65280)
        sm.GetService('infoGatheringSvc').LogInfoEvent(eventTypeID=const.infoEventDoubleclickToMove, itemID=session.charid, int_1=1)
        if isinstance(myMovement.moveModeManager.GetCurrentMode(), GameWorld.PathToMode):
            myMovement.moveModeManager.GetCurrentMode().SetDestination(destination)
        else:
            pathToMode = GameWorld.PathToMode(destination, 0.1, False, True)
            myMovement.moveModeManager.PushMoveMode(pathToMode)

    def ToggleExtrapolation(self):
        for entity in self.entityService.GetEntityScene(session.worldspaceid).entities.values():
            if entity.HasComponent('movement'):
                m = entity.GetComponent('movement')
                mm = m.moveModeManager.GetCurrentMode()
                if hasattr(mm, 'enableExtrapolation'):
                    mm.enableExtrapolation = not mm.enableExtrapolation
