#Embedded file name: trinity\takeScreenshot.py
"""
Utility module for taking a screenshot. Currently contains a single method to take
a screenshot.
"""
import wx
import trinity
import math
import os
from trinity.sceneRenderJobBase import SceneRenderJobBase
from trinity.eveSceneRenderJobInterior import EveSceneRenderJobInterior
from trinity.sceneRenderJobSpace import SceneRenderJobSpace
import app.Common.Wrapper.TrinityPanelWrapper as TrinityPanelWrapper
AVAILABLE_RENDERJOB_TYPES = [EveSceneRenderJobInterior, SceneRenderJobSpace, SceneRenderJobBase]
oldProjections = {}
oldViewports = {}
noSetProjectionRjList = []
noSetViewportRjList = []

def GetProjection(rj):
    """
    Tries several methods to get at the current projection matrix in the renderjob.  If
    it all fails, just return None.
    """
    if hasattr(rj, 'GetCameraProjection'):
        proj = rj.GetCameraProjection()
        if proj is not None:
            if hasattr(proj, 'object'):
                proj = proj.object
            if proj is not None:
                return proj
    if hasattr(rj, 'GetStep'):
        projStep = rj.GetStep('SET_PROJECTION')
        if projStep is not None:
            if projStep.projection is not None:
                return projStep.projection
    for step in rj.steps:
        if type(step) is trinity.TriStepRunJob:
            if step is not None and step.job is not None:
                for step2 in step.job.steps:
                    if step2.name == 'SET_PROJECTION':
                        if step2.projection is not None:
                            return step2.projection

    noSetProjectionRjList.append(rj)


def GetViewport(rj):
    """
    Tries several methods to get at the current viewport in the renderjob.  If it all 
    fails, just return None.
    """
    if hasattr(rj, 'GetViewport'):
        vp = rj.GetViewport()
        if vp is not None:
            if hasattr(vp, 'object'):
                vp = vp.object
            if vp is not None:
                return vp
    if hasattr(rj, 'GetStep'):
        vpStep = rj.GetStep('SET_VIEWPORT')
        if vpStep is not None:
            if vpStep.viewport is not None:
                return vpStep.viewport
    for step in rj.steps:
        if type(step) is trinity.TriStepRunJob:
            if step is not None and step.job is not None:
                for step2 in step.job.steps:
                    if step2.name == 'SET_VIEWPORT':
                        if step2.viewport is not None:
                            return step2.viewport

    if TrinityPanelWrapper.GetViewport() is not None:
        return TrinityPanelWrapper.GetViewport()
    noSetViewportRjList.append(rj)


def SetProjection(rj, newProj):
    """
    Tries several methods to set the projection matrix on the renderjob.
    """
    if hasattr(rj, 'CallMethodOnChildren'):
        rj.CallMethodOnChildren('SetCameraProjection', newProj)
        rj.CallMethodOnChildren('AddStep', 'SET_PROJECTION', trinity.TriStepSetProjection(newProj))
        return
    if hasattr(rj, 'SetCameraProjection'):
        rj.SetCameraProjection(newProj)
        return
    if hasattr(rj, 'GetStep'):
        projStep = rj.GetStep('SET_PROJECTION')
        if projStep is not None:
            projStep.projection = newProj


def SetViewport(rj, newVP):
    """
    Tries several methods to set the viewport on the renderjob.
    """
    if hasattr(rj, 'CallMethodOnChildren'):
        rj.CallMethodOnChildren('AddStep', 'SET_VIEWPORT', trinity.TriStepSetViewport(newVP))
        return
    if hasattr(rj, 'GetStep'):
        vpStep = rj.GetStep('SET_VIEWPORT')
        if vpStep is not None:
            vpStep.viewport = newVP
        else:
            rj.SetViewport(newVP)
    TrinityPanelWrapper.SetViewport(newVP)


def BackupAllProjectionsAndViewports(rjList):
    """
    Visits each renderjob in the list and attempts to make a backup of the current
    projection matrix and viewport.
    """
    global oldViewports
    global oldProjections
    for rj in rjList:
        oldProjections[rj] = GetProjection(rj)
        oldViewports[rj] = GetViewport(rj)


def RestoreAllProjectionsAndViewports():
    """
    Restores the backed-up projection matrices and viewports.
    """
    for rj, projection in oldProjections.iteritems():
        SetProjection(rj, projection)

    for rj in noSetProjectionRjList:
        rj.SetCameraProjection(None)

    for rj, viewport in oldViewports.iteritems():
        SetViewport(rj, viewport)

    for rj in noSetViewportRjList:
        rj.SetViewport(None)


def OverrideAllProjectionsAndViewports(rjList, newProj, newVP):
    """
    Visits each rendersob in the list and overrides the projection matrix and viewport.
    """
    for rj in rjList:
        SetProjection(rj, newProj)
        SetViewport(rj, newVP)


def FreezeInteriorFlares():
    """
    Disable updates for all interior flares and return their previous update state.
    """
    flareList = trinity.device.Find('trinity.Tr2InteriorFlare')
    flarePreviousState = {}
    for flare in flareList:
        if flare not in flarePreviousState:
            flarePreviousState[flare] = flare.updateVisibility
            flare.updateVisibility = False

    return flarePreviousState


def RestoreInteriorFlares(flarePreviousState):
    """
    Restore updates for interior flares.
    """
    for flare in flarePreviousState:
        flare.updateVisibility = flarePreviousState[flare]
        flare.OverrideViewport(None)


def OverrideInteriorFlareViewports(flarePreviousState, x, y, width, height):
    viewport = trinity.TriViewport()
    viewport.x = int(x)
    viewport.y = int(y)
    viewport.width = int(width)
    viewport.height = int(height)
    for flare in flarePreviousState:
        flare.OverrideViewport(viewport)


class HostBitmapSaver:
    """
    A screenshot saver class passed to TakeScreenshot function. This implementation
    uses Tr2HostBitmap to save the screenshot. It supports many image formats, but
    require the full screenshot bitmap in memory.
    """

    def __init__(self, filename, width, height, pixelFormat):
        self.filename = filename
        self.screenShot = trinity.Tr2HostBitmap(width, height, 1, pixelFormat)
        if not self.screenShot.isValid:
            params = (width, height, trinity.PIXEL_FORMAT.GetNameFromValue(pixelFormat))
            raise Exception('Failed to create screenshot target image, size(%ix%i), format(%s)' % params)

    def StartBatch(self, tileHeight):
        pass

    def EndBatch(self):
        pass

    def EndSaving(self):
        baseDir = os.path.dirname(self.filename)
        if not os.path.exists(baseDir):
            os.makedirs(baseDir)
        if not self.screenShot.Save(self.filename):
            raise Exception('Failed to save image to %s' % self.filename)

    def CopyFromRenderTargetRegion(self, rt, left, top, right, bottom, offsetx, offsety):
        self.screenShot.CopyFromRenderTargetRegion(rt, left, top, right, bottom, offsetx, offsety)


class StreamingBitmapSaver:
    """
    A screenshot saver class passed to TakeScreenshot function. This implementation
    uses trinity streaming saver to save the screenshot. It only supports TGA format, but
    has doe not require the full screenshot bitmap in memory, so it can be used for very
    large screenshots.
    """

    def __init__(self, filename, width, height, pixelFormat):
        baseDir = os.path.dirname(filename)
        if not os.path.exists(baseDir):
            os.makedirs(baseDir)
        self.screenShot = trinity.StartStreamingBitmap(filename, width, height, pixelFormat)

    def StartBatch(self, tileHeight):
        self.screenShot.StartBatch(tileHeight)

    def EndBatch(self):
        self.screenShot.FlushBatch()

    def EndSaving(self):
        self.screenShot.EndSaving()

    def CopyFromRenderTargetRegion(self, rt, left, top, right, bottom, offsetx, offsety):
        self.screenShot.CopyFromRenderTargetRegion(rt, left, top, right, bottom, offsetx, offsety)


def TakeScreenshot(filename, tilesAcross, saverClass = HostBitmapSaver):
    """
    Method for taking a screenshot. Old code moved from the screenshot macro.
    """
    successful = False
    errorHint = ''
    performanceOverlayRJ = 0
    camera = TrinityPanelWrapper.GetCamera()
    dev = trinity.device
    fov = camera.fieldOfView
    aspect = camera.aspectRatio
    zNear = camera.frontClip
    zFar = camera.backClip
    height = 2.0 * zNear * math.tan(fov / 2.0)
    width = height * aspect
    disabledJobsStates = {}
    sceneRenderJobs = []
    for rj in trinity.renderJobs.recurring:
        legalRenderJob = False
        if issubclass(rj, trinity.sceneRenderJobBase.SceneRenderJobBase):
            sceneRenderJobs.append(rj)
        else:
            disabledJobsStates[rj] = rj.enabled
            rj.enabled = False

    BackupAllProjectionsAndViewports(sceneRenderJobs)
    flarePreviousState = FreezeInteriorFlares()
    try:
        if filename == None or filename == '':
            raise ValueError('No filename given')
        if not tilesAcross or tilesAcross == 0:
            raise ValueError('tilesAcross must be greater than 0')
        tilesAcross = int(tilesAcross)
        heightSlice = height / tilesAcross
        widthSlice = width / tilesAcross
        backBuffer = TrinityPanelWrapper.GetBackBuffer()
        tileWidth = backBuffer.width
        tileHeight = backBuffer.height
        twd4 = math.floor(tileWidth / 4)
        thd4 = math.floor(tileHeight / 4)
        diffW = tileWidth - twd4 * 4
        diffH = tileHeight - thd4 * 4
        if not backBuffer.isReadable:
            tempRT = trinity.Tr2RenderTarget(tileWidth, tileHeight, 1, backBuffer.format, 1, 0)
        screenShot = saverClass(filename, tileWidth * tilesAcross, tileHeight * tilesAcross, backBuffer.format)
        info = wx.BusyInfo('Hold on, generating snazzy snapshot ...')
        tileOffset = trinity.TriPoint()
        halfAcross = tilesAcross / 2.0
        for y in range(tilesAcross - 1, -1, -1):
            top = (halfAcross - y) * heightSlice
            bottom = top - heightSlice
            tileOffset.y = y * tileHeight
            screenShot.StartBatch(tileHeight)
            for x in range(tilesAcross):
                left = (x - halfAcross) * widthSlice
                right = left + widthSlice
                tileOffset.x = x * tileWidth
                for x_off in [(-widthSlice / 4, -twd4, 0), (widthSlice / 4, twd4, diffW)]:
                    for y_off in [(heightSlice / 4, -thd4, 0), (-heightSlice / 4, thd4, diffH)]:
                        newProj = trinity.TriProjection()
                        newProj.PerspectiveOffCenter(left + x_off[0], right + x_off[0], bottom + y_off[0], top + y_off[0], zNear, zFar)
                        newViewport = trinity.TriViewport()
                        newViewport.x = 0
                        newViewport.y = 0
                        newViewport.width = tileWidth
                        newViewport.height = tileHeight
                        newViewport.minZ = 0.0
                        newViewport.maxZ = 1.0
                        OverrideAllProjectionsAndViewports(sceneRenderJobs, newProj, newViewport)
                        OverrideInteriorFlareViewports(flarePreviousState, int(x_off[1] + tileOffset.x), int(y_off[1] + tileOffset.y), tileWidth * tilesAcross, tileHeight * tilesAcross)
                        dev.Render()
                        dev.Render()
                        offset = trinity.TriPoint(int(x_off[1] + tileOffset.x), int(y_off[1] + tileOffset.y))
                        rect = trinity.TriRect(int(twd4), int(thd4), int(3 * twd4 + x_off[2]), int(3 * thd4 + y_off[2]))
                        if not backBuffer.isReadable:
                            backBuffer.Resolve(tempRT)
                            screenShot.CopyFromRenderTargetRegion(tempRT, rect.left, rect.top, rect.right, rect.bottom, offset.x, offset.y)
                        else:
                            screenShot.CopyFromRenderTargetRegion(backBuffer, rect.left, rect.top, rect.right, rect.bottom, offset.x, offset.y)

            RestoreAllProjectionsAndViewports()
            screenShot.EndBatch()

        screenShot.EndSaving()
        del info
        successful = True
    except Exception as e:
        import traceback
        traceback.print_exc()
        errorHint = 'An exception occurred: ' + e.message

    RestoreInteriorFlares(flarePreviousState)
    for rj, state in disabledJobsStates.iteritems():
        rj.enabled = state

    return (successful, errorHint)
