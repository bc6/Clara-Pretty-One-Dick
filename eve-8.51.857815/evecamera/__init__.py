#Embedded file name: evecamera\__init__.py
"""
Helpers and utilities for the eve inflight camera
"""
PRIORITY_NONE = 0
PRIORITY_LOW = 1
PRIORITY_NORMAL = 2
PRIORITY_HIGH = 3
FOV_MIN = 0.05
FOV_MAX = 1.0
DEFAULT_MAX_SPEED = 0.07
DEFAULT_FRICTION = 7.0
DEFAULT_FRONT_CLIP = 6.0
DEFAULT_BACK_CLIP = 10000000.0
DEFAULT_IDLE_SCALE = 0.65

def ApplyCameraDefaults(camera):
    camera.fieldOfView = FOV_MAX
    camera.friction = DEFAULT_FRICTION
    camera.maxSpeed = DEFAULT_MAX_SPEED
    camera.frontClip = DEFAULT_FRONT_CLIP
    camera.backClip = DEFAULT_BACK_CLIP
    camera.idleScale = DEFAULT_IDLE_SCALE
    for each in camera.zoomCurve.keys:
        each.value = FOV_MAX
