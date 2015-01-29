#Embedded file name: carbonui/util\cameraUtils.py
"""
Utility functions for the client camera
"""
import geo2
import mathCommon
import math

def GetEntityYaw(entity):
    entityRot = entity.GetComponent('position').rotation
    yaw, pitch, roll = geo2.QuaternionRotationGetYawPitchRoll(entityRot)
    yaw += math.pi / 2
    if yaw > 2.0 * math.pi:
        yaw = yaw - 2.0 * math.pi
    elif yaw < 0.0:
        yaw = yaw + 2.0 * math.pi
    if yaw <= math.pi:
        return math.pi - yaw
    else:
        return -(yaw - math.pi)


def ReverseCameraYaw(yaw):
    """
    Given a yaw, turns it around 180\xb0 while respecting the camera yaw space
    """
    if yaw <= 0:
        yaw = math.pi - abs(yaw)
    else:
        yaw = -(math.pi - yaw)
    return yaw


def GetAngleFromEntityToCamera(entity, overrideYaw = None, offset = None):
    """
        Return the theta angle from the player entity to the camera angle.
    """
    activeCamera = sm.GetService('cameraClient').GetActiveCamera()
    cameraYaw = -activeCamera.yaw
    if overrideYaw:
        cameraYaw = overrideYaw
    if offset:
        cameraYaw = offset + cameraYaw
    playerYaw = GetEntityYaw(entity)
    retval = 0.0
    if playerYaw != None and cameraYaw != None:
        lesserYaw = mathCommon.GetLesserAngleBetweenYaws(playerYaw, cameraYaw)
        retval = lesserYaw
    return retval


def CalcDesiredPlayerHeading(heading):
    """
    The players movement is 8 directional relative to the facing direction of the
    camera. We need to work out as a worldspace yaw the direction the player should be
    moving in.
    
    heading - 3D vector represents the control inputs. 
            z, is forward and backwards. 
            x, is left and right.
    """
    headingYaw = mathCommon.GetYawAngleFromDirectionVector(heading)
    activeCamera = sm.GetService('cameraClient').GetActiveCamera()
    cameraYaw = -activeCamera.yaw
    desiredYaw = cameraYaw + headingYaw
    return desiredYaw


def GetAngleFromEntityToYaw(entity, yaw):
    """
    Returns the shortest angle between the entity's facing direction and a specified yaw.
    """
    lesserYaw = mathCommon.GetLesserAngleBetweenYaws(GetEntityYaw(entity), yaw)
    return lesserYaw


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('cameraUtils', globals())
