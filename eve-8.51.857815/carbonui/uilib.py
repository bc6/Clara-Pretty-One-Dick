#Embedded file name: carbonui\uilib.py
import carbonui.const as uiconst
from carbonui.control.menu import CloseContextMenus
import uthread
import blue
from carbon.common.script.util.timerstuff import AutoTimer
import trinity
import log
import math
import carbon.client.script.util.weakrefutil as weakrefutil
import eve.client.script.ui.camera.baseCamera as baseCamera
import weakref
import carbonui.control
import telemetry
from carbonui.util.various_unsorted import GetWindowAbove
from carbonui.primitives.desktop import UIRoot
from carbonui.primitives.dragdrop import DragDropObject
from carbonui.control.layer import LayerCore
from trinity.windowsEvents import *
import evegraphics.settings as gfxsettings
from trinity.renderJobUtils import renderTargetManager
DBLCLICKDELAY = 250.0
CLICKCOUNTRESETTIME = 250
HOVERTIME = 250

class Uilib(object):
    __members__ = ['x',
     'y',
     'z',
     'dx',
     'dy',
     'dz',
     'rootObjects',
     'mouseOver',
     'renderJob',
     'desktop']
    __notifyevents__ = ['OnWindowBlurSettingChanged', 'OnUIScalingChange']
    __guid__ = 'uicls.Uilib'
    UTHREADEDEVENTS = (uiconst.UI_CLICK,
     uiconst.UI_DBLCLICK,
     uiconst.UI_TRIPLECLICK,
     uiconst.UI_KEYUP,
     uiconst.UI_KEYDOWN,
     uiconst.UI_MOUSEMOVE,
     uiconst.UI_MOUSEWHEEL)
    EVENTMAP = {uiconst.UI_MOUSEHOVER: 'OnMouseHover',
     uiconst.UI_MOUSEMOVE: 'OnMouseMove',
     uiconst.UI_MOUSEMOVEDRAG: 'OnMouseMoveDrag',
     uiconst.UI_MOUSEENTER: 'OnMouseEnter',
     uiconst.UI_MOUSEEXIT: 'OnMouseExit',
     uiconst.UI_MOUSEDOWN: 'OnMouseDown',
     uiconst.UI_MOUSEDOWNDRAG: 'OnMouseDownDrag',
     uiconst.UI_MOUSEUP: 'OnMouseUp',
     uiconst.UI_MOUSEWHEEL: 'OnMouseWheel',
     uiconst.UI_CLICK: 'OnClick',
     uiconst.UI_DBLCLICK: 'OnDblClick',
     uiconst.UI_TRIPLECLICK: 'OnTripleClick',
     uiconst.UI_KEYDOWN: 'OnKeyDown',
     uiconst.UI_KEYUP: 'OnKeyUp'}
    activateAppHandler = None
    inputLangChangeHandler = None
    imeSetContextHandler = None
    imeStartCompositionHandler = None
    imeCompositionHandler = None
    imeEndCompositionHandler = None
    imeNotifyHandler = None
    tooltipHandler = None
    auxiliaryTooltip = None
    auxiliaryTooltipPosition = None
    cursorPos = (-1, -1)

    def __init__(self, paparazziMode = False):
        if not paparazziMode:
            sm.RegisterNotify(self)
        if len(trinity.textureAtlasMan.atlases) == 0:
            trinity.textureAtlasMan.AddAtlas(trinity.PIXEL_FORMAT.B8G8R8A8_UNORM, 2048, 2048)
        self.textureAtlas = trinity.textureAtlasMan.atlases[0]
        self.textureAtlas.optimizeOnRemoval = False
        self.renderObjectToPyObjectDict = weakref.WeakValueDictionary()
        self.x = -1
        self.y = -1
        self.z = 0
        self.dx = 0
        self.dy = 0
        self.dz = 0
        self._mouseOver = None
        self._auxMouseOverRO = None
        self._capturingMouseItem = None
        self._clickItem = None
        self._mouseTargetObject = None
        self.exclusiveMouseFocusActive = False
        self.appfocusitem = None
        self.selectedCursorType = uiconst.UICURSOR_DEFAULT
        self.centerMouse = False
        self.ignoreDeadChar = None
        self._lastEventTime = None
        self._globalClickCounter = 0
        self._globalKeyDownCounter = 0
        self._clickTime = None
        self._clickCount = 0
        self._clickTimer = None
        self._clickPosition = None
        self.rootObjects = []
        self.rootObjectsByName = {}
        self._triuiRegs = {}
        self._triuiRegsByMsgID = {}
        self._mouseButtonStates = {}
        self._mouseDownPosition = {}
        self._appfocusitem = None
        self._modkeysOff = tuple([ 0 for x in uiconst.MODKEYS ])
        self._expandMenu = None
        self._keyDownAcceleratorThread = None
        self.blurredBackBufferRenderJob = None
        self.blurredBackBufferAtlas = None
        self.desktopBlurredBg = None
        self._pickProjection = trinity.TriProjection()
        self._pickView = trinity.TriView()
        self._pickViewport = trinity.TriViewport()
        self.cursorCache = {}
        self.alignIslands = []
        uicore.uilib = self
        trinity.fontMan.loadFlag = 32
        if not paparazziMode:
            self._SetupRenderJob()
            self.desktop = self.CreateRootObject('Desktop', isFullscreen=True)
            uthread.new(self.EnableEventHandling)
            from eve.client.script.ui.tooltips.tooltipHandler import TooltipHandler
            self.tooltipHandler = TooltipHandler()
        trinity.device.RegisterResource(self)
        self._hoverThread = None

    def __del__(self, *args):
        trinity.app.eventHandler = None
        if self.renderJob:
            self.renderJob.UnscheduleRecurring()

    def EnableEventHandling(self):
        while not uicore.IsReady():
            blue.synchro.SleepWallclock(1)

        trinity.app.eventHandler = self.OnAppEvent
        log.LogInfo('Uilib event handling enabled')

    def OnInvalidate(self, *args):
        self.cursorCache = {}

    def OnCreate(self, *args):
        """
        Device reset handler
        """
        uthread.new(self.PrepareBlurredBackBuffer)

    def OnWindowBlurSettingChanged(self, *args):
        self.PrepareBlurredBackBuffer()

    def CreateTexture(self, width, height):
        tex = self.textureAtlas.CreateTexture(int(width), int(height))
        return tex

    def CreateRootObject(self, name, width = None, height = None, depthMin = None, depthMax = None, isFullscreen = False, renderTarget = None, renderJob = None):
        desktop = UIRoot(pos=(0,
         0,
         width or trinity.app.width,
         height or trinity.app.height), name=name, state=uiconst.UI_NORMAL, depthMin=depthMin, depthMax=depthMax, isFullscreen=isFullscreen, renderTarget=renderTarget, renderJob=renderJob)
        self.AddRootObject(desktop)
        return desktop

    def GetRenderJob(self):
        return self.desktopRenderJob

    def GetVideoJob(self):
        return self.videoJob

    def OnUIScalingChange(self, *args):
        self.PrepareBlurredBackBuffer()

    def PrepareBlurredBackBuffer(self):
        if self.blurredBackBufferRenderJob:
            renderJob = self.blurredBackBufferRenderJob
            renderJob.enabled = True
            for step in renderJob.steps[:]:
                renderJob.steps.remove(step)

        else:
            renderJob = trinity.CreateRenderJob()
            renderJob.name = 'Blurred Back Buffer'
            renderJob.ScheduleRecurring(insertFront=True)
            self.blurredBackBufferRenderJob = renderJob
        if not settings.char.windows.Get('enableWindowBlur', True):
            if self.blurredBackBufferRenderJob:
                self.blurredBackBufferRenderJob.enabled = False
            return
        backbuffer = trinity.device.GetRenderContext().GetDefaultBackBuffer()
        self.spaceSceneBackBufferCopy = trinity.Tr2RenderTarget()
        self.spaceSceneBackBufferCopy.Create(trinity.app.width, trinity.app.height, 1, backbuffer.format)
        self.spaceSceneBackBufferDownSizedCopy = trinity.Tr2RenderTarget()
        self.spaceSceneBackBufferDownSizedCopy.name = 'spaceSceneBackBufferDownSizedCopy'
        self.spaceSceneBackBufferDownSizedCopy.Create(trinity.app.width / 4, trinity.app.height / 4, 1, backbuffer.format)
        step = trinity.TriStepResolve(self.spaceSceneBackBufferCopy, backbuffer)
        step.name = 'Resolve back buffer'
        renderJob.steps.append(step)
        if self.desktopBlurredBg:
            self.RemoveRootObject(self.desktopBlurredBg)
            self.desktopBlurredBg.Close()
        self.desktopBlurredBg = self.CreateRootObject(name='desktopBlurred', renderTarget=self.spaceSceneBackBufferCopy, renderJob=renderJob, isFullscreen=True)
        self.desktopBlurredBg.renderObject.clearBackground = False
        renderJob.PushDepthStencil().pushCurrent = False
        renderJob.SetVariableStore('BlitCurrent', self.spaceSceneBackBufferCopy).name = 'Set BlitCurrent variable'
        value = (1.0 / trinity.app.width,
         1.0 / trinity.app.height,
         trinity.app.width,
         trinity.app.height)
        renderJob.SetVariableStore('g_texelSize', value).name = 'Set g_texelSize variable'
        renderJob.PushRenderTarget(self.spaceSceneBackBufferDownSizedCopy)
        renderJob.Clear((0, 0, 0, 0))
        effect = trinity.Tr2Effect()
        effect.effectFilePath = 'res:/Graphics/Effect/Managed/Space/PostProcess/ColorDownFilter4.fx'
        renderJob.RenderEffect(effect)
        renderJob.PopRenderTarget()
        renderJob.PopDepthStencil()
        textureRes = trinity.TriTextureRes()
        textureRes.SetFromRenderTarget(self.spaceSceneBackBufferDownSizedCopy)
        atlasTexture = trinity.Tr2AtlasTexture()
        atlasTexture.textureRes = textureRes
        self.blurredBackBufferAtlas = atlasTexture
        sm.ScatterEvent('OnBlurredBufferCreated')

    def _SetupRenderJob(self):
        self.renderJob = trinity.CreateRenderJob()
        self.renderJob.name = 'UI'
        self.PrepareBlurredBackBuffer()
        self.sceneViewStep = self.renderJob.SetView()
        self.scaledViewportStep = self.renderJob.SetViewport()
        self.sceneProjectionStep = self.renderJob.SetProjection()
        videoJobStep = self.renderJob.RunJob()
        videoJobStep.name = 'Videos'
        self.videoJob = trinity.CreateRenderJob()
        self.videoJob.name = 'Update videos job'
        videoJobStep.job = self.videoJob
        self.bracketCurveSet = trinity.TriCurveSet()
        self.bracketCurveSet.Play()
        self.renderJob.Update(self.bracketCurveSet).name = 'Update brackets'
        self.renderJob.SetViewport()
        self.renderJob.PythonCB(self.Update).name = 'Update uilib'
        self.desktopRenderJob = trinity.CreateRenderJob()
        self.desktopRenderJob.name = 'Desktop'
        self.renderJob.steps.append(trinity.TriStepRunJob(self.desktopRenderJob))
        isFpsEnabled = trinity.IsFpsEnabled()
        if isFpsEnabled:
            trinity.SetFpsEnabled(False)
        self.renderJob.ScheduleRecurring()
        if isFpsEnabled:
            trinity.SetFpsEnabled(True)

    def _GetMouseTravel(self):
        if self._mouseButtonStates.get(uiconst.MOUSELEFT, False):
            x, y, z = self._mouseDownPosition[uiconst.MOUSELEFT]
            return math.sqrt(abs((x - self.x) * (x - self.x) + (y - self.y) * (y - self.y)))
        return 0

    mouseTravel = property(_GetMouseTravel)

    def _GetRightBtn(self):
        return self._mouseButtonStates.get(uiconst.MOUSERIGHT, False)

    rightbtn = property(_GetRightBtn)

    def _GetLeftBtn(self):
        return self._mouseButtonStates.get(uiconst.MOUSELEFT, False)

    leftbtn = property(_GetLeftBtn)

    def _GetMiddleBtn(self):
        return self._mouseButtonStates.get(uiconst.MOUSEMIDDLE, False)

    midbtn = property(_GetMiddleBtn)

    def ReleaseObject(self, object):
        try:
            del self.renderObjectToPyObjectDict[object.renderObject]
        except KeyError:
            pass

    def GetMouseOver(self):
        if self._mouseOver:
            mouseOver = self._mouseOver()
            if mouseOver and not mouseOver.destroyed:
                return mouseOver
            self._mouseOver = None
        return uicore.desktop

    mouseOver = property(GetMouseOver)

    def GetAuxMouseOver(self):
        if self._auxMouseOverRO:
            return self.GetPyObjectFromRenderObject(self._auxMouseOverRO())

    auxMouseOver = property(GetAuxMouseOver)

    def CheckWindowEnterExit(self):
        item = self.GetMouseOver()
        while item.parent:
            if isinstance(item, carbonui.control.window.WindowCore) and item.state == uiconst.UI_NORMAL:
                item.ShowHeaderButtons()
                break
            if not item.parent:
                break
            item = item.parent

    def CheckAppFocus(self, hasFocus):
        if getattr(uicore, 'registry', None) is None:
            return
        uicore.UpdateCursor(self.GetMouseOver(), 1)
        if hasFocus:
            modal = uicore.registry.GetModalWindow()
            if modal:
                uicore.registry.SetFocus(modal)
            elif self.appfocusitem and self.appfocusitem():
                f = self.appfocusitem()
                if f is not None and not f.destroyed:
                    uicore.registry.SetFocus(f)
                self.appfocusitem = None
        else:
            focus = uicore.registry.GetFocus()
            if focus:
                self.appfocusitem = weakref.ref(focus)
                uicore.registry.SetFocus(None)
            mouseCaptureItem = self.GetMouseCapture()
            if mouseCaptureItem:
                self.ReleaseCapture()
                self.centerMouse = False
                self._mouseButtonStates = {}
                self._mouseDownPosition = {}
                self._TryExecuteHandler(uiconst.UI_MOUSEUP, mouseCaptureItem, (uiconst.MOUSELEFT,))
        return 1

    def CheckAccelerators(self, vkey, flag):
        modkeys = self.GetModifierKeyState(vkey)
        if self.CheckMappedAccelerators(modkeys, vkey, flag):
            return True
        if self.CheckDirectionalAccelerators(vkey):
            return True
        return False

    def GetModifierKeyState(self, vkey = None):
        """
        Get the state of the shortcut modifier keys, defined in uiconst.MODKEYS
        """
        ret = []
        for key in uiconst.MODKEYS:
            ret.append(trinity.app.Key(key) and key != vkey)

        return tuple(ret)

    def CheckMappedAccelerators(self, modkeys, vkey, flag):
        """ The return value is whether an accelerator is used or not. If the accelerator 
        returns True the key should not be passed further"""
        if not uicore.commandHandler:
            return False
        ctrl = self.Key(uiconst.VK_CONTROL)
        if not ctrl and (self._modkeysOff, vkey) in uicore.commandHandler.commandMap.accelerators:
            cmd = uicore.commandHandler.commandMap.accelerators[self._modkeysOff, vkey]
            if cmd.ignoreModifierKey:
                if not cmd.repeatable and flag & 1073741824:
                    return False
                sm.ScatterEvent('OnCommandExecuted', cmd.name)
                ret = uicore.cmd.ExecuteCommand(cmd)
                if ret:
                    return ret
        if (modkeys, vkey) in uicore.commandHandler.commandMap.accelerators:
            cmd = uicore.commandHandler.commandMap.accelerators[modkeys, vkey]
            if not cmd.repeatable and flag & 1073741824:
                return False
            sm.ScatterEvent('OnCommandExecuted', cmd.name)
            return uicore.cmd.ExecuteCommand(cmd)
        return False

    def CheckDirectionalAccelerators(self, vkey):
        """ The return value is whether an accelerator is found. """
        active = uicore.registry.GetActive()
        focus = uicore.registry.GetFocus()
        focusOrActive = focus or active
        if vkey == uiconst.VK_UP and hasattr(focusOrActive, 'OnUp'):
            uthread.pool('uisvc::CheckDirectionalAccelerators OnUp', focusOrActive.OnUp)
            return True
        if vkey == uiconst.VK_DOWN and hasattr(focusOrActive, 'OnDown'):
            uthread.pool('uisvc::CheckDirectionalAccelerators OnDown', focusOrActive.OnDown)
            return True
        if vkey == uiconst.VK_LEFT and hasattr(focusOrActive, 'OnLeft'):
            uthread.pool('uisvc::CheckDirectionalAccelerators OnLeft', focusOrActive.OnLeft)
            return True
        if vkey == uiconst.VK_RIGHT and hasattr(focusOrActive, 'OnRight'):
            uthread.pool('uisvc::CheckDirectionalAccelerators OnRight', focusOrActive.OnRight)
            return True
        if vkey == uiconst.VK_HOME and hasattr(focusOrActive, 'OnHome'):
            uthread.pool('uisvc::CheckDirectionalAccelerators OnHome', focusOrActive.OnHome)
            return True
        if vkey == uiconst.VK_END and hasattr(focusOrActive, 'OnEnd'):
            uthread.pool('uisvc::CheckDirectionalAccelerators OnEnd', focusOrActive.OnEnd)
            return True

    def RegisterForTriuiEvents(self, msgIDlst, function, *args, **kw):
        """
            Register a callable globally for one or more types of TriUI events.
        
            When a TriUI event of one of the types in msgIDlst is triggered (on any
            window), the given function will get called in the form
                func(wnd, msgID, param, *args, **kw)
        
            Where
                wnd is the target of the event (an UIWindow).
                msgID is the ID of the event type (e.g. triui.UI_CLICK)
                param is whatever TriUI sends along as additional info on the event
                        (e.g. the mouse button ID for triui.UI_MOUSEUP)
                args and kw are the additional arguments you have passed to me.
        
            When the callback is made, the registration will die unless the
            callback function returns a true value. (This is like this because
            one-shot registrations are the rule, and longer ones are the exception
            as of this writing.)
        
            Return a cookie which you must pass to UnregisterForTriuiEvents if
            you want to kill this registration in other way.
        """
        if type(msgIDlst) == int:
            msgIDlst = [msgIDlst]
        cookie = uthread.uniqueId() or uthread.uniqueId()
        self._triuiRegs[cookie] = msgIDlst
        ref = weakrefutil.CallableWeakRef(function)
        for id_ in msgIDlst:
            self._triuiRegsByMsgID.setdefault(id_, {})[cookie] = (ref, args, kw)

        log.LogInfo('RegisterForTriuiEvents', cookie, msgIDlst, function, args, kw)
        return cookie

    def UnregisterForTriuiEvents(self, cookie):
        """
            Kill a registration generated with RegisterForTriuiEvents.
            cookie must be the value returned by RegisterForTriuiEvents when
            you created the registration, and is meaningless after I return.
        """
        if cookie not in self._triuiRegs:
            return
        log.LogInfo('UnregisterForTriuiEvents', cookie)
        try:
            for msgID_ in self._triuiRegs[cookie]:
                del self._triuiRegsByMsgID[msgID_][cookie]

            del self._triuiRegs[cookie]
        except KeyError as what:
            log.LogError('UnregisterForTriuiEvents: Tried to kill unexisting registration?', cookie)
            log.LogException()

    @telemetry.ZONE_METHOD
    def RegisterObject(self, pyObject, renderObject):
        self.renderObjectToPyObjectDict[renderObject] = pyObject

    def GetPyObjectFromRenderObject(self, RO):
        pyObject = self.renderObjectToPyObjectDict.get(RO, None)
        if pyObject and not pyObject.destroyed:
            return pyObject

    def AddRootObject(self, obj):
        if self.rootObjectsByName.has_key(obj.name):
            raise AttributeError('Root object already exists with this name (%s)' % obj.name)
        self.rootObjectsByName[obj.name] = obj
        if obj not in self.rootObjects:
            self.rootObjects.append(obj)

    def RemoveRootObject(self, obj):
        if obj.name in self.rootObjectsByName:
            del self.rootObjectsByName[obj.name]
        if obj in self.rootObjects:
            self.rootObjects.remove(obj)

    def FindRootObject(self, name):
        return self.rootObjectsByName.get(name, None)

    def AddMouseTargetObject(self, mouseTargetObject):
        """
        When uiObject is active mouse target area, picking (mouseover update) is ignored
        to other objects if the cursor is heading on the target area.
        """
        self._mouseTargetObject = mouseTargetObject

    def GetMouseTargetObject(self):
        if self._mouseTargetObject:
            if self._mouseTargetObject.GetOwner():
                return self._mouseTargetObject
            self._mouseTargetObject = None

    @telemetry.ZONE_METHOD
    def Update(self, *args):
        if getattr(self, 'updatingFromRoot', False):
            return
        vp = trinity.TriViewport()
        vp.width = trinity.device.width
        vp.height = trinity.device.height
        self.scaledViewportStep.viewport = vp
        self.cursorPos = trinity.GetCursorPos()
        self.UpdateMouseOver()
        if self.tooltipHandler:
            self.tooltipHandler.RefreshTooltip()
        for root in self.rootObjects:
            root.UpdateAlignmentAsRoot('uilib.Update')

        for island in self.alignIslands:
            if not island.destroyed:
                island.UpdateAlignmentAsRoot('uilib.Update Islands')

        self.alignIslands = []

    def SetSceneCamera(self, camera):
        if isinstance(camera, baseCamera.Camera):
            self.sceneViewStep.view = camera.viewMatrix
            self.sceneViewStep.camera = None
            self.sceneProjectionStep.projection = camera.projectionMatrix
        else:
            self.sceneViewStep.view = None
            self.sceneViewStep.camera = camera
            self.sceneProjectionStep.projection = camera.projectionMatrix

    def SetSceneView(self, view, projection):
        self.sceneViewStep.camera = None
        self.sceneViewStep.view = view
        self.sceneProjectionStep.projection = projection

    @telemetry.ZONE_METHOD
    def UpdateMouseOver(self, *args):
        pyObject = None
        auxRenderObject = None
        cursorX, cursorY = self.cursorPos
        if 0 <= cursorX <= trinity.app.width and 0 <= cursorY <= trinity.app.height:
            mouseTargetObject = self.GetMouseTargetObject()
            if mouseTargetObject and mouseTargetObject.IsMouseHeadingTowards():
                return
            triobj, pyObject = self.PickScreenPosition(int(uicore.ScaleDpi(self.x)), int(uicore.ScaleDpi(self.y)))
            if getattr(triobj, 'auxMouseover', None):
                auxRenderObject = triobj.auxMouseover
        newMouseOver = pyObject or uicore.desktop
        currentMouseOver = self.GetMouseOver()
        currentAuxiliaryTooltip = getattr(self, 'auxiliaryTooltip', None)
        if auxRenderObject:
            self._auxMouseOverRO = weakref.ref(auxRenderObject)
            pyAuxObject = self.GetPyObjectFromRenderObject(auxRenderObject)
            if pyAuxObject and hasattr(pyAuxObject, 'GetAuxiliaryTooltip'):
                self.auxiliaryTooltip = pyAuxObject.GetAuxiliaryTooltip()
                self.auxiliaryTooltipPosition = pyAuxObject.GetAuxiliaryTooltipPosition()
            else:
                self.auxiliaryTooltip = None
                self.auxiliaryTooltipPosition = None
        else:
            self.auxiliaryTooltip = None
            self.auxiliaryTooltipPosition = None
            self._auxMouseOverRO = None
        mouseCaptureItem = self.GetMouseCapture()
        if newMouseOver is not self.mouseOver:
            self._mouseOver = weakref.ref(newMouseOver)
        if currentMouseOver is not newMouseOver or currentAuxiliaryTooltip != self.auxiliaryTooltip:
            self.FlagTooltipsDirty()
        if not mouseCaptureItem and currentMouseOver is not newMouseOver:
            if self._hoverThread:
                self._hoverThread.kill()
            uicore.HideHint()
            if currentMouseOver:
                if uicore.IsDragging() and isinstance(currentMouseOver, DragDropObject) and uicore.dragObject is not currentMouseOver:
                    currentMouseOver.OnDragExit(uicore.dragObject, uicore.dragObject.dragData)
                else:
                    self._TryExecuteHandler(uiconst.UI_MOUSEEXIT, currentMouseOver, param=None)
            if newMouseOver:
                if uicore.IsDragging() and isinstance(newMouseOver, DragDropObject) and uicore.dragObject is not newMouseOver:
                    newMouseOver.OnDragEnter(uicore.dragObject, uicore.dragObject.dragData)
                else:
                    self._TryExecuteHandler(uiconst.UI_MOUSEENTER, newMouseOver, param=None)
                hoverHandlerArgs, hoverHandler = self.FindEventHandler(newMouseOver, self.EVENTMAP[uiconst.UI_MOUSEHOVER])
                if hoverHandler:
                    self._hoverThread = uthread.new(self._HoverThread)
            uicore.CheckCursor()
            self.CheckWindowEnterExit()

    def PickScreenPosition(self, x, y):
        triobj = None
        pyObject = None
        for root in self.rootObjects:
            RO = root.GetRenderObject()
            if not RO:
                continue
            camera = root.GetCamera()
            if root.renderTargetStep:
                pass
            elif camera:
                triobj = RO.PickObject(x, y, camera.projectionMatrix, camera.viewMatrix, trinity.device.viewport)
            elif hasattr(root, 'PickObject'):
                triobj = root.PickObject(x, y)
            else:
                triobj = RO.PickObject(x, y, self._pickProjection, self._pickView, self._pickViewport)
            if triobj:
                pyObject = self.GetPyObjectFromRenderObject(triobj)
                if pyObject:
                    overridePick = getattr(pyObject, 'OverridePick', None)
                    if overridePick:
                        overrideObject = overridePick(x, y)
                        if overrideObject:
                            pyObject = overrideObject
                if pyObject and not isinstance(pyObject, LayerCore):
                    break

        return (triobj, pyObject)

    def FlagTooltipsDirty(self, instant = False):
        if self.tooltipHandler:
            self.tooltipHandler.FlagTooltipsDirty(instant)

    UpdateTooltip = FlagTooltipsDirty

    def RefreshTooltipForOwner(self, owner):
        if self.tooltipHandler:
            self.tooltipHandler.RefreshTooltipForOwner(owner)

    @telemetry.ZONE_METHOD
    def OnAppEvent(self, msgID, wParam, lParam):
        """ 
        This method receives window events from trinity, and forwards them appropriately 
        to the UI. There are two ways of consuming such events: 
        1) Having appropriate methods defined within UI classes, such as OnClick (see EVENTMAP for full list).
        2) Using RegisterForTriUIEvent to capture global events 
        """
        try:
            returnValue = 0
            currentMouseOver = self.GetMouseOver()
            if msgID == WM_MOUSEMOVE:
                mouseX = uicore.ReverseScaleDpi(lParam & 65535)
                mouseY = uicore.ReverseScaleDpi(lParam >> 16)
                if self.x != mouseX or self.y != mouseY:
                    self.dx = mouseX - self.x
                    self.dy = mouseY - self.y
                    self.x = mouseX
                    self.y = mouseY
                    self.z = 0
                    if self.centerMouse:
                        self.SetCursorPos(uicore.desktop.width / 2, uicore.desktop.height / 2)
                    mouseCaptureItem = self.GetMouseCapture()
                    if mouseCaptureItem:
                        self._TryExecuteHandler(uiconst.UI_MOUSEMOVE, mouseCaptureItem, param=(wParam, lParam))
                        self._TryExecuteHandler(uiconst.UI_MOUSEMOVEDRAG, mouseCaptureItem, param=(wParam, lParam))
                    elif currentMouseOver:
                        self._TryExecuteHandler(uiconst.UI_MOUSEMOVE, currentMouseOver, param=(wParam, lParam))
                        self._TryExecuteHandler(uiconst.UI_MOUSEMOVEDRAG, currentMouseOver, param=(wParam, lParam))
            elif msgID == WM_LBUTTONDOWN:
                self._globalClickCounter += 1
                self.RegisterAppEventTime()
                self._expandMenu = uiconst.MOUSELEFT
                self._mouseButtonStates[uiconst.MOUSELEFT] = True
                self._mouseDownPosition[uiconst.MOUSELEFT] = (self.x, self.y, self.z)
                if self.exclusiveMouseFocusActive:
                    self._TryExecuteHandler(uiconst.UI_MOUSEDOWN, self.GetMouseCapture(), (uiconst.MOUSELEFT,), param=(uiconst.MOUSELEFT, wParam))
                    self._TryExecuteHandler(uiconst.UI_MOUSEDOWNDRAG, self.GetMouseCapture(), (uiconst.MOUSELEFT,), param=(uiconst.MOUSELEFT, wParam))
                else:
                    self._TryExecuteHandler(uiconst.UI_MOUSEDOWN, currentMouseOver, (uiconst.MOUSELEFT,), param=(uiconst.MOUSELEFT, wParam))
                    self._TryExecuteHandler(uiconst.UI_MOUSEDOWNDRAG, currentMouseOver, (uiconst.MOUSELEFT,), param=(uiconst.MOUSELEFT, wParam))
                    self.SetCapture(currentMouseOver, retainFocus=self.exclusiveMouseFocusActive)
                    if not currentMouseOver.IsUnder(uicore.layer.menu):
                        CloseContextMenus()
                        currentFocus = uicore.registry.GetFocus()
                        if currentFocus != currentMouseOver:
                            uicore.registry.SetFocus(currentMouseOver)
            elif msgID == WM_MBUTTONDOWN:
                self._globalClickCounter += 1
                self.RegisterAppEventTime()
                self._expandMenu = None
                self._mouseButtonStates[uiconst.MOUSEMIDDLE] = True
                self._mouseDownPosition[uiconst.MOUSEMIDDLE] = (self.x, self.y, self.z)
                self._TryExecuteHandler(uiconst.UI_MOUSEDOWN, currentMouseOver, (uiconst.MOUSEMIDDLE,), param=(uiconst.MOUSEMIDDLE, wParam))
                uthread.new(self.CheckAccelerators, uiconst.VK_MBUTTON, lParam)
            elif msgID == WM_RBUTTONDOWN:
                self._globalClickCounter += 1
                self.RegisterAppEventTime()
                self._expandMenu = uiconst.MOUSERIGHT
                self._mouseButtonStates[uiconst.MOUSERIGHT] = True
                self._mouseDownPosition[uiconst.MOUSERIGHT] = (self.x, self.y, self.z)
                if self.exclusiveMouseFocusActive:
                    self._TryExecuteHandler(uiconst.UI_MOUSEDOWN, self.GetMouseCapture(), (uiconst.MOUSERIGHT,), param=(uiconst.MOUSERIGHT, wParam))
                else:
                    self._TryExecuteHandler(uiconst.UI_MOUSEDOWN, currentMouseOver, (uiconst.MOUSERIGHT,), param=(uiconst.MOUSERIGHT, wParam))
                if not currentMouseOver.IsUnder(uicore.layer.menu):
                    CloseContextMenus()
                    currentFocus = uicore.registry.GetFocus()
                    if currentFocus is not currentMouseOver:
                        uicore.registry.SetFocus(currentMouseOver)
            elif msgID == WM_XBUTTONDOWN:
                self._globalClickCounter += 1
                self.RegisterAppEventTime()
                if wParam & 65536:
                    self._mouseButtonStates[uiconst.MOUSEXBUTTON1] = True
                    self._TryExecuteHandler(uiconst.UI_MOUSEDOWN, currentMouseOver, (uiconst.MOUSEXBUTTON1,), param=(uiconst.MOUSEXBUTTON1, wParam))
                    uthread.new(self.CheckAccelerators, uiconst.VK_XBUTTON1, lParam)
                else:
                    self._mouseButtonStates[uiconst.MOUSEXBUTTON2] = True
                    self._TryExecuteHandler(uiconst.UI_MOUSEDOWN, currentMouseOver, (uiconst.MOUSEXBUTTON2,), param=(uiconst.MOUSEXBUTTON2, wParam))
                    uthread.new(self.CheckAccelerators, uiconst.VK_XBUTTON2, lParam)
            elif msgID == WM_LBUTTONUP:
                self.RegisterAppEventTime()
                self._mouseButtonStates[uiconst.MOUSELEFT] = False
                mouseCaptureItem = self.GetMouseCapture()
                if mouseCaptureItem:
                    if not self.exclusiveMouseFocusActive:
                        if getattr(mouseCaptureItem, 'expandOnLeft', 0) and not self.rightbtn and self._expandMenu == uiconst.MOUSELEFT and getattr(mouseCaptureItem, 'GetMenu', None):
                            x, y, z = self._mouseDownPosition[uiconst.MOUSELEFT]
                            if abs(self.x - x) < 3 and abs(self.y - y) < 3:
                                self.FlagTooltipsDirty(True)
                                uthread.new(carbonui.control.menu.ShowMenu, mouseCaptureItem, self.GetAuxMouseOver())
                        self._expandMenu = False
                    self._TryExecuteHandler(uiconst.UI_MOUSEUP, mouseCaptureItem, (uiconst.MOUSELEFT,), param=(uiconst.MOUSELEFT, wParam))
                    if not self.exclusiveMouseFocusActive:
                        self.ReleaseCapture()
                    if currentMouseOver is not mouseCaptureItem:
                        self._TryExecuteHandler(uiconst.UI_MOUSEEXIT, mouseCaptureItem, param=(wParam, lParam))
                        self._TryExecuteHandler(uiconst.UI_MOUSEENTER, currentMouseOver, param=(wParam, lParam))
                    else:
                        self._TryExecuteClickHandler(wParam, lParam)
            elif msgID == WM_RBUTTONUP:
                self._mouseButtonStates[uiconst.MOUSERIGHT] = False
                if self.exclusiveMouseFocusActive:
                    self._TryExecuteHandler(uiconst.UI_MOUSEUP, self.GetMouseCapture(), (uiconst.MOUSERIGHT,), param=(uiconst.MOUSERIGHT, wParam))
                else:
                    if not self.leftbtn and self._expandMenu == uiconst.MOUSERIGHT and (getattr(currentMouseOver, 'GetMenu', None) or self._auxMouseOverRO is not None):
                        x, y, z = self._mouseDownPosition[uiconst.MOUSERIGHT]
                        if abs(self.x - x) < 3 and abs(self.y - y) < 3:
                            self.FlagTooltipsDirty(True)
                            uthread.new(carbonui.control.menu.ShowMenu, currentMouseOver, self.GetAuxMouseOver())
                    self._expandMenu = None
                    self._TryExecuteHandler(uiconst.UI_MOUSEUP, currentMouseOver, (uiconst.MOUSERIGHT,), param=(uiconst.MOUSERIGHT, wParam))
            elif msgID == WM_MBUTTONUP:
                self._mouseButtonStates[uiconst.MOUSEMIDDLE] = False
                self._TryExecuteHandler(uiconst.UI_MOUSEUP, currentMouseOver, (uiconst.MOUSEMIDDLE,), param=(uiconst.MOUSEMIDDLE, wParam))
            elif msgID == WM_XBUTTONUP:
                if wParam & 65536:
                    self._mouseButtonStates[uiconst.MOUSEXBUTTON1] = False
                    self._TryExecuteHandler(uiconst.UI_MOUSEUP, currentMouseOver, (uiconst.MOUSEXBUTTON1,), param=(uiconst.MOUSEXBUTTON1, wParam))
                else:
                    self._mouseButtonStates[uiconst.MOUSEXBUTTON2] = False
                    self._TryExecuteHandler(uiconst.UI_MOUSEUP, currentMouseOver, (uiconst.MOUSEXBUTTON2,), param=(uiconst.MOUSEXBUTTON2, wParam))
            elif msgID == WM_MOUSEWHEEL:
                self.RegisterAppEventTime()
                mouseZ = wParam >> 16
                self.dz = mouseZ
                if self.mouseOver:
                    mo = self.mouseOver
                    mwHandlerArgs, mwHandler = self.FindEventHandler(mo, 'OnMouseWheel')
                    while not mwHandler:
                        if not mo.parent or mo is uicore.uilib.desktop:
                            break
                        mo = mo.parent
                        mwHandlerArgs, mwHandler = self.FindEventHandler(mo, 'OnMouseWheel')

                    calledMethod = None
                    if mo:
                        calledMethod = self._TryExecuteHandler(uiconst.UI_MOUSEWHEEL, mo, (mouseZ,), param=(wParam, lParam))
                    if not calledMethod:
                        focus = uicore.registry.GetFocus()
                        if focus and GetWindowAbove(self.mouseOver) == uicore.registry.GetActive():
                            self._TryExecuteHandler(uiconst.UI_MOUSEWHEEL, focus, (mouseZ,), param=(wParam, lParam))
            elif msgID in (WM_KEYDOWN, WM_SYSKEYDOWN):
                self._globalKeyDownCounter += 1
                self.RegisterAppEventTime()
                focus = uicore.registry.GetFocus()
                if focus:
                    self._TryExecuteHandler(uiconst.UI_KEYDOWN, focus, (wParam, lParam), param=(wParam, lParam))
                self._keyDownAcceleratorThread = uthread.new(self.CheckAccelerators, wParam, lParam)
            elif msgID == WM_CHAR:
                char = wParam
                ignoreChar = False
                if char <= 32 or char == self.ignoreDeadChar:
                    ctrl = trinity.app.Key(uiconst.VK_CONTROL)
                    if char not in (uiconst.VK_RETURN, uiconst.VK_BACK, uiconst.VK_SPACE) or ctrl:
                        ignoreChar = True
                if not ignoreChar:
                    calledOn = self.ResolveOnChar(wParam, lParam)
                    if calledOn and self._keyDownAcceleratorThread:
                        self._keyDownAcceleratorThread.kill()
                self.ignoreDeadChar = None
            elif msgID == WM_DEADCHAR:
                focus = uicore.registry.GetFocus()
                if focus and focus.HasEventHandler('OnChar') and focus.IsVisible():
                    self._keyDownAcceleratorThread.kill()
                else:
                    self.ignoreDeadChar = wParam
            elif msgID in (WM_KEYUP, WM_SYSKEYUP):
                focus = uicore.registry.GetFocus()
                if focus:
                    self._TryExecuteHandler(uiconst.UI_KEYUP, focus, (wParam, lParam), param=(wParam, lParam))
                if wParam == uiconst.VK_SNAPSHOT and uicore.commandHandler:
                    uicore.commandHandler.PrintScreen()
            elif msgID == WM_ACTIVATE:
                self.CheckAppFocus(hasFocus=wParam > 0)
                self.CheckCallbacks(obj=uicore.registry.GetFocus(), msgID=uiconst.UI_ACTIVE, param=(wParam, lParam))
            elif msgID == WM_ACTIVATEAPP:
                if self.activateAppHandler:
                    returnValue = self.activateAppHandler(wParam, lParam)
            elif msgID == WM_INPUTLANGCHANGE:
                if self.inputLangChangeHandler:
                    returnValue = self.inputLangChangeHandler(wParam, lParam)
            elif msgID == WM_IME_SETCONTEXT:
                if self.imeSetContextHandler:
                    returnValue = self.imeSetContextHandler(wParam, lParam)
            elif msgID == WM_IME_STARTCOMPOSITION:
                if self.imeStartCompositionHandler:
                    returnValue = self.imeStartCompositionHandler(wParam, lParam)
            elif msgID == WM_IME_COMPOSITION:
                if self.imeCompositionHandler:
                    returnValue = self.imeCompositionHandler(wParam, lParam)
            elif msgID == WM_IME_ENDCOMPOSITION:
                if self.imeEndCompositionHandler:
                    returnValue = self.imeEndCompositionHandler(wParam, lParam)
            elif msgID == WM_IME_NOTIFY:
                if self.imeNotifyHandler:
                    returnValue = self.imeNotifyHandler(wParam, lParam)
            elif msgID == WM_CLOSE and uicore.commandHandler:
                uthread.new(uicore.commandHandler.CmdQuitGame)
                returnValue = 1
            else:
                returnValue = None
            return returnValue
        except:
            log.LogException()

    def CheckCallbacks(self, obj, msgID, param):
        for cookie, (wr, args, kw) in self._triuiRegsByMsgID.get(msgID, {}).items():
            try:
                if not wr() or not wr()(*(args + (obj, msgID, param)), **kw):
                    self.UnregisterForTriuiEvents(cookie)
            except UserError as what:

                def f():
                    raise what

                uthread.new(f)
            except:
                log.LogError('OnAppEvent (cookie', cookie, '): Exception when trying to process callback!')
                log.LogException()

    def GetGlobalKeyDownCount(self):
        return self._globalKeyDownCounter

    def GetGlobalClickCount(self):
        return self._globalClickCounter

    def RegisterAppEventTime(self):
        self._lastEventTime = blue.os.GetWallclockTime()

    def GetLastAppEventTime(self):
        return self._lastEventTime

    def ResetClickCounter(self, *args):
        self._clickTimer = None
        self._clickCount = 0

    def KillClickThreads(self):
        self._clickTimer = None

    def ResolveOnChar(self, char, flag):
        ignore = (uiconst.VK_RETURN, uiconst.VK_BACK)
        if char < 32 and char not in ignore:
            return False
        focus = uicore.registry.GetFocus()
        if focus and focus.HasEventHandler('OnChar') and focus.IsVisible():
            ret = focus.OnChar(char, flag)
            if ret:
                return focus

    def _TryExecuteClickHandler(self, wParam, lParam):
        """ 
        Execute OnClick, OnDblClick or OnTripleclick for the object under the mouse
        """
        self._clickTimer = None
        self._clickCount += 1
        currentMouseOver = self.GetMouseOver()
        if self._clickCount > 1:
            clickObject = self.GetClickObject()
            if clickObject is None:
                self.ResetClickCounter()
                return
            x, y = self._clickPosition
            distanceOK = abs(self.x - x) < 5 and abs(self.y - y) < 5
            clickPosOK = clickObject is currentMouseOver and distanceOK
            dblHandlerArgs, dblHandler = self.FindEventHandler(clickObject, 'OnDblClick')
            tripHandlerArgs, tripleHandler = self.FindEventHandler(clickObject, 'OnTripleClick')
            if self._clickCount == 2 and dblHandler and clickPosOK:
                self._TryExecuteHandler(uiconst.UI_DBLCLICK, currentMouseOver, param=(wParam, lParam))
            elif self._clickCount == 3 and tripleHandler and clickPosOK:
                self._TryExecuteHandler(uiconst.UI_TRIPLECLICK, currentMouseOver, param=(wParam, lParam))
            else:
                self._clickCount = 1
        if self._clickCount == 1:
            handlerArgs, handler = self.FindEventHandler(currentMouseOver, 'OnClick')
            if handler:
                self._TryExecuteHandler(uiconst.UI_CLICK, currentMouseOver, param=(wParam, lParam))
                self.SetClickObject(currentMouseOver)
                self._clickPosition = (self.x, self.y)
        self._clickTimer = AutoTimer(CLICKCOUNTRESETTIME, self.ResetClickCounter)

    def _TryExecuteHandler(self, eventID, object, eventArgs = None, param = None):
        """Delegate event to uiobject """
        functionName = self.EVENTMAP.get(eventID, None)
        if functionName is None:
            raise NotImplementedError
        itemCapturingMouse = self.GetMouseCapture()
        if itemCapturingMouse:
            object = itemCapturingMouse
        retObject = None
        handlerArgs, handler = self.FindEventHandler(object, functionName)
        if handler:
            retObject = object
            if eventArgs:
                args = handlerArgs + eventArgs
            else:
                args = handlerArgs
            if eventID in self.UTHREADEDEVENTS:
                uthread.new(handler, *args)
            else:
                try:
                    handler(*args)
                except:
                    log.LogException()
                    raise

        self.CheckCallbacks(retObject, eventID, param)
        return retObject

    def SetWindowOrder(self, *args):
        return trinity.app.uilib.SetWindowOrder(*args)

    def FindEventHandler(self, object, handlerName):
        return object.FindEventHandler(handlerName)

    def GetMouseButtonState(self, buttonFlag):
        return self._mouseButtonStates.get(buttonFlag, False)

    def Key(self, vkey):
        return trinity.app.Key(vkey)

    def SetCursorProperties(self, cursor):
        trinity.app.mouseCursor = cursor

    def SetCursorPos(self, x, y):
        self.x = x
        self.y = y
        return trinity.app.SetCursorPos(uicore.ScaleDpi(x), uicore.ScaleDpi(y))

    def SetCursor(self, cursorIx):
        if self.exclusiveMouseFocusActive:
            return
        cursorName = 'res:/UI/Cursor/cursor{0:02}.dds'.format(cursorIx)
        cursor = self.cursorCache.get(cursorName, None)
        if cursor is None:
            bmp = trinity.Tr2HostBitmap()
            bmp.CreateFromFile(cursorName)
            cursor = trinity.Tr2MouseCursor(bmp, 16, 15)
            self.cursorCache[cursorName] = cursor
        self.SetCursorProperties(cursor)

    def FindWindow(self, wndName, fromParent):
        return trinity.app.uilib.FindWindow(wndName, fromParent)

    def SetMouseCapture(self, item, retainFocus = False):
        """
            Setting retainFocus to True means that the item will not loose focus no matter what until an
            explicit ReleaseCapture call is made
        """
        self._capturingMouseItem = weakref.ref(item)
        self.exclusiveMouseFocusActive = retainFocus
        self.FlagTooltipsDirty()

    SetCapture = SetMouseCapture

    def GetMouseCapture(self):
        if self._capturingMouseItem:
            captureItem = self._capturingMouseItem()
            if captureItem and not captureItem.destroyed:
                return captureItem
            self._capturingMouseItem = None
            self.exclusiveMouseFocusActive = False

    GetCapture = GetMouseCapture
    capture = property(GetMouseCapture)

    def SetClickObject(self, item):
        self._clickItem = weakref.ref(item)

    def GetClickObject(self):
        if self._clickItem:
            return self._clickItem()

    def ReleaseCapture(self, itemReleasing = None):
        self._capturingMouseItem = None
        self.exclusiveMouseFocusActive = False
        self.FlagTooltipsDirty()

    def ClipCursor(self, *rect):
        self._cursorClip = rect
        l, t, r, b = rect
        trinity.app.ClipCursor(uicore.ScaleDpi(l), uicore.ScaleDpi(t), uicore.ScaleDpi(r), uicore.ScaleDpi(b))

    def UnclipCursor(self, *args):
        self._cursorClip = None
        trinity.app.UnclipCursor()

    def _HoverThread(self):
        """
        Execute OnMouseHover event of self.mouseOver if it exists every {HOVERTIME} ms
        This thread is killed in UpdateMoseOver()
        """
        while True:
            if trinity.app.IsHidden():
                return
            blue.synchro.SleepWallclock(HOVERTIME)
            self._TryExecuteHandler(uiconst.UI_MOUSEHOVER, self.mouseOver)
