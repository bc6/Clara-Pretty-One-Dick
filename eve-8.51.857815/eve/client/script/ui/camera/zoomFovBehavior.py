#Embedded file name: eve/client/script/ui/camera\zoomFovBehavior.py
import cameras
MAX_FOV = 1.0
MIN_FOV = 0.7
FOV_POWER = 0.2

class ZoomFovBehavior(cameras.CameraBehavior):
    __guid__ = 'cameras.ZoomFovBehavior'

    def __init__(self):
        cameras.CameraBehavior.__init__(self)

    def ProcessCameraUpdate(self, camera, now, frameTime):
        """
        Applies a linear modifier to the fov of the camera based on the camera's zoom position
        within minZoom and maxZoom
        """
        zoom = camera.zoom
        if zoom < camera.minZoom:
            zoom = camera.minZoom
        range = camera.maxZoom - camera.minZoom
        curr = camera.maxZoom - zoom
        zoomPerc = curr / range
        camera.SetFieldOfView(MIN_FOV + (MAX_FOV - zoomPerc) * FOV_POWER)
