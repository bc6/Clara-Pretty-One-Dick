#Embedded file name: carbon/common/script/entities\entityProcs.py
"""
Code required to create and manage ActionProcs for Entity system.
"""
import service
import GameWorld
import uthread
import geo2
from carbon.common.script.zaction.zactionCommon import ProcTypeDef, ProcPropertyTypeDef
MOTIONSTATE_NO_CHANGE = 0
MOTIONSTATE_KEY_FRAME = 1
MOTIONSTATE_CHARACTER = 2

class EntityProcSvc(service.Service):
    __guid__ = 'svc.entityProcSvc'
    __machoresolve__ = 'location'

    def Run(self, *args):
        service.Service.Run(self, *args)
        GameWorld.RegisterPythonActionProc('SetEntityPosition', self._SetEntityPosition, ('ENTID', 'ALIGN_POSITION', 'ALIGN_ROTATION', 'MotionState'))
        GameWorld.RegisterPythonActionProc('GetEntitySceneID', self._GetEntitySceneID, ('ENTID',))
        GameWorld.RegisterPythonActionProc('GetBonePosRot', self._GetBonePosRot, ('ENTID', 'boneName', 'posProp', 'rotProp'))
        GameWorld.RegisterPythonActionProc('AllowPlayerMoveControl', self._AllowPlayerMoveControl, ('inControl',))

    def _GetEntitySceneID(self, ENTID):
        entity = self.entityService.FindEntityByID(ENTID)
        if entity is None:
            self.LogError('GetEntitySceneID: Entity with ID ', ENTID, ' not found!')
            return False
        GameWorld.AddPropertyForCurrentPythonProc({'entitySceneID': entity.scene.sceneID})
        return True

    def _GetBonePosRot(self, ENTID, boneName, posProp, rotProp):
        entity = self.entityService.FindEntityByID(ENTID)
        if entity is None:
            self.LogError('GetBonePosRot: Entity with ID ', ENTID, ' not found!')
            return False
        animClient = entity.GetComponent('animation')
        posComp = entity.GetComponent('position')
        if animClient is not None and posComp is not None:
            if animClient.controller is not None:
                boneTransform = animClient.controller.animationNetwork.GetBoneTransform(boneName)
                if boneTransform:
                    translation, orientation = boneTransform
                    translation = geo2.QuaternionTransformVector(posComp.rotation, translation)
                    translation = geo2.Vec3Add(posComp.position, translation)
                    orientation = geo2.QuaternionMultiply(posComp.rotation, orientation)
                    translation = list(translation)
                    orientation = list(orientation)
                    GameWorld.AddPropertyForCurrentPythonProc({posProp: translation})
                    GameWorld.AddPropertyForCurrentPythonProc({rotProp: orientation})
                    return True
        self.LogError('GetBonePosRot: Missing critical data in entity!')
        return False

    def _SetEntityPosition(self, ENTID, ALIGN_POSITION, ALIGN_ROTATION, MotionState):
        uthread.worker('_SetEntityPosition', self._SetEntityPositionTasklet, ENTID, ALIGN_POSITION, ALIGN_ROTATION, MotionState)
        return True

    def _SetEntityPositionTasklet(self, ENTID, ALIGN_POSITION, ALIGN_ROTATION, MotionState):
        entity = self.entityService.FindEntityByID(ENTID)
        if entity is not None:
            if MotionState is MOTIONSTATE_NO_CHANGE:
                positionComponent = entity.GetComponent('position')
                if positionComponent is not None:
                    positionComponent.rotation = ALIGN_ROTATION
                    positionComponent.position = ALIGN_POSITION
            else:
                movementComponent = entity.GetComponent('movement')
                if movementComponent is not None:
                    if MotionState is MOTIONSTATE_KEY_FRAME:
                        movementComponent.moveModeManager.PushMoveMode(GameWorld.KeyFrameMode(ALIGN_POSITION, ALIGN_ROTATION))
                    elif MotionState is MOTIONSTATE_CHARACTER:
                        movementComponent.moveModeManager.RestoreDefaultMode()

    def _AllowPlayerMoveControl(self, inControl):
        nav = sm.GetService('navigation')
        nav.hasControl = inControl
        return True


MotionStateList = [('No Change', MOTIONSTATE_NO_CHANGE, ''), ('Key Frame', MOTIONSTATE_KEY_FRAME, ''), ('Character', MOTIONSTATE_CHARACTER, '')]
TargetTypeList = [('Me', 0, 'me'), ('My Target', 1, 'target'), ('Buff Source', 2, 'buffSource')]

def CreateLocatorList(self):
    from locator import Locator
    locatorList = []
    locatorObjs = Locator.GetAllLocators()
    for loc in locatorObjs:
        locatorList.append((loc.GetName(), loc.GetName(), ''))

    return locatorList


MotionState = ('list', MotionStateList)
TargetTypeList = ('list', TargetTypeList)
LocatorList = ('listMethod', CreateLocatorList)
SetEntityPosition = ProcTypeDef(isMaster=True, procCategory='Entity', properties=[ProcPropertyTypeDef('MotionState', 'I', userDataType='MotionState', isPrivate=True)], description='Sets the requesting entity\'s position. This uses the ALIGN_POSITION and ALIGN_ROTATION properties right now, though could be altered to use specified properties. The "MotionState" corresponds to move modes -- Keyframe and Character.')
GetEntitySceneID = ProcTypeDef(isMaster=True, procCategory='Entity', description='Gets the entity scene ID of the entity performing this action.')
GetBonePosRot = ProcTypeDef(isMaster=True, procCategory='Entity', properties=[ProcPropertyTypeDef('boneName', 'S', userDataType='Bone Name', isPrivate=True), ProcPropertyTypeDef('posProp', 'S', userDataType='Position Property', isPrivate=True), ProcPropertyTypeDef('rotProp', 'S', userDataType='Rotation Property', isPrivate=True)], description='Gets the position and rotation of a specified bone. The output is stored into properties with the specified names to be accessed later.')
TeleportToLocator = ProcTypeDef(isMaster=True, procCategory='Entity', properties=[ProcPropertyTypeDef('TargetType', 'I', userDataType='TargetTypeList', isPrivate=True), ProcPropertyTypeDef('LocatorName', 'S', userDataType='LocatorList', isPrivate=True)])
SetAllowedToMove = ProcTypeDef(isMaster=False, procCategory='Entity', properties=[ProcPropertyTypeDef('allowedToMove', 'B', userDataType=None, isPrivate=True)], description='Sets the enable movement flag on the MoveModeManager.  Use this to disable movement when an avatar is disabled, for example: unconscious.')
AllowPlayerMoveControl = ProcTypeDef(isMaster=False, procCategory='Entity', properties=[ProcPropertyTypeDef('inControl', 'B', userDataType=None, isPrivate=True)], description='Sets the a flag that enables/disables movement input on the navigation service. This affects movement controls on the local player only.')
exports = {'actionProperties.MotionState': MotionState,
 'actionProperties.TargetTypeList': TargetTypeList,
 'actionProperties.LocatorList': LocatorList,
 'actionProcTypes.SetEntityPosition': SetEntityPosition,
 'actionProcTypes.GetEntitySceneID': GetEntitySceneID,
 'actionProcTypes.GetBonePosRot': GetBonePosRot,
 'actionProcTypes.TeleportToLocator': TeleportToLocator,
 'actionProcTypes.SetAllowedToMove': SetAllowedToMove,
 'actionProcTypes.AllowPlayerMoveControl': AllowPlayerMoveControl}
