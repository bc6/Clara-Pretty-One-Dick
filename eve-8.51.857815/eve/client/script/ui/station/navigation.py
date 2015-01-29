#Embedded file name: eve/client/script/ui/station\navigation.py
import uicontrols
import blue
import geo2
import mathCommon
import uix
import uthread
import util
import carbonui.const as uiconst
from carbon.common.script.util.timerstuff import AutoTimer
import localization
import evegraphics.settings as gfxsettings
from carbonui.control.layer import LayerCore

class HangarLayer(LayerCore):
    __guid__ = 'uicls.HangarLayer'

    def __init__(self, *args, **kwds):
        LayerCore.__init__(self, *args, **kwds)
        self.looking = 0
        self.blockDisable = 0
        self.scene = None
        self.camera = None
        self.maxZoom = 750.0
        self.minZoom = 150.0
        self.isMouseMoving = False
        self.startYaw = None
        self.prevYaw = None
        self.prevDirection = None
        self.numSpins = 0
        self.spinThread = None
        self.prevSpinTime = None

    def Startup(self):
        pass

    def GetMenu(self):
        x, y = uicore.ScaleDpi(uicore.uilib.x), uicore.ScaleDpi(uicore.uilib.y)
        scene = sm.StartService('sceneManager').GetRegisteredScene('hangar')
        if scene:
            projection, view, viewport = uix.GetFullscreenProjectionViewAndViewport()
            pick = scene.PickObject(x, y, projection, view, viewport)
            if pick and pick.name == str(util.GetActiveShip()):
                return self.GetShipMenu()

    def OnMouseEnter(self, *args):
        if not self.blockDisable and not uicore.cmd.IsUIHidden():
            uicore.layer.main.state = uiconst.UI_PICKCHILDREN

    def OnDropData(self, dragObj, nodes):
        sm.GetService('loading').StopCycle()
        station = sm.GetService('station')
        if len(nodes) == 1:
            node = nodes[0]
            if getattr(node, '__guid__', None) not in ('xtriui.InvItem', 'listentry.InvItem'):
                return
            if eve.session.shipid == node.item.itemID:
                eve.Message('CantMoveActiveShip', {})
                return
            if node.item.categoryID == const.categoryShip and node.item.singleton:
                if not node.item.ownerID == eve.session.charid:
                    eve.Message('CantDoThatWithSomeoneElsesStuff')
                    return
                station.TryActivateShip(node.item)

    def GetShipMenu(self):
        if util.GetActiveShip():
            hangarInv = sm.GetService('invCache').GetInventory(const.containerHangar)
            hangarItems = hangarInv.List()
            for each in hangarItems:
                if each.itemID == util.GetActiveShip():
                    return sm.GetService('menu').InvItemMenu(each)

        return []

    def OnDblClick(self, *args):
        uicore.cmd.OpenCargoHoldOfActiveShip()

    def OnMouseDown(self, *args):
        if not self.staticEnv:
            self.looking = 1
        if not self.blockDisable and not uicore.cmd.IsUIHidden():
            uicore.layer.main.state = uiconst.UI_DISABLED
        self.cursor = uiconst.UICURSOR_DRAGGABLE
        uicore.uilib.ClipCursor(0, 0, uicore.desktop.width, uicore.desktop.height)
        uicore.uilib.SetCapture(self)

    def OnMouseUp(self, button, *args):
        sm.ScatterEvent('OnCameraDragEnd')
        self.isMouseMoving = False
        if not self.blockDisable and not uicore.cmd.IsUIHidden():
            uicore.layer.main.state = uiconst.UI_PICKCHILDREN
        if not self.staticEnv:
            if self.camera is None:
                return
            self.camera.interest = None
            self.camera.friction = 7.0
            if not uicore.uilib.rightbtn:
                self.camera.rotationOfInterest = geo2.QuaternionIdentity()
            if not uicore.uilib.leftbtn:
                self.looking = 0
        self.cursor = None
        uicore.uilib.UnclipCursor()
        if uicore.uilib.GetCapture() == self:
            uicore.uilib.ReleaseCapture()

    def OnMouseWheel(self, *args):
        self.ZoomBy(uicore.uilib.dz)

    def ZoomBy(self, amount):
        if not self.staticEnv:
            if self.camera is None:
                return
            if self.camera.__typename__ == 'EveCamera':
                self.camera.Dolly(amount * 0.001 * abs(self.camera.translationFromParent))
                self.camera.translationFromParent = min(self.maxZoom, max(self.camera.translationFromParent, self.minZoom))

    def OnMouseMove(self, *args):
        if uicore.IsDragging():
            return
        if self.looking and not self.staticEnv:
            if not self.isMouseMoving:
                sm.ScatterEvent('OnCameraDragStart')
            self.isMouseMoving = True
            lib = uicore.uilib
            dx = lib.dx
            dy = lib.dy
            if self.camera is None:
                return
            fov = self.camera.fieldOfView
            ctrl = lib.Key(uiconst.VK_CONTROL)
            if lib.rightbtn and not lib.leftbtn:
                self.camera.RotateOnOrbit(-dx * fov * 0.2, dy * fov * 0.2)
            if lib.leftbtn and not lib.rightbtn:
                self._ActivateSpinThread()
                self.camera.OrbitParent(-dx * fov * 0.2, dy * fov * 0.2)
            if lib.leftbtn and lib.rightbtn:
                self.camera.Dolly(-0.01 * dy * abs(self.camera.translationFromParent))
                self.camera.translationFromParent = min(self.maxZoom, max(self.camera.translationFromParent, self.minZoom))
                if ctrl:
                    self.camera.fieldOfView = -dx * 0.01 + fov
                    if self.camera.fieldOfView > 1.0:
                        self.camera.fieldOfView = 1.0
                    if self.camera.fieldOfView < 0.1:
                        self.camera.fieldOfView = 0.1
                else:
                    self.camera.OrbitParent(-dx * fov * 0.2, 0.0)
        else:
            self.cursor = None

    def GetShipSpins(self):
        return self.numSpins

    def OnOpenView(self, *args):
        self.staticEnv = gfxsettings.Get(gfxsettings.MISC_LOAD_STATION_ENV) == 0
        self._ActivateSpinThread()
        self.spinCounterLabel = uicontrols.EveLabelLargeBold(parent=self, align=uiconst.CENTERBOTTOM, top=14, hint=localization.GetByLabel('UI/Station/Hangar/ShipSpinCounter'), state=uiconst.UI_NORMAL, color=(1, 1, 1, 1))
        self.spinCounterLabel.Hide()
        self.spinCounterLabel.startSpinCount = self.numSpins
        self.spinCounterLabel.displayTriggered = False
        self.spinCounterTimer = None

    def OnCloseView(self, *args):
        self.KillSpinThread()
        if self.spinCounterLabel:
            self.spinCounterLabel.Close()

    def HideSpinCounter(self):
        if self.spinCounterTimer:
            self.spinCounterTimer = None
        uicore.animations.FadeOut(self.spinCounterLabel, duration=0.5, sleep=True)
        self.spinCounterLabel.displayTriggered = False

    def _CountRotations(self, curYaw):
        """
        Count the number of full ship rotations that have occurred.
          fetch positive or negative from direction (float)
          fetch the yaw from the camera rotation quaternion
        """
        spinDirection = mathCommon.GetLesserAngleBetweenYaws(self.prevYaw, curYaw)
        if spinDirection == 0.0:
            return
        if self.prevDirection is None:
            self.prevDirection = spinDirection
        if self.prevDirection * spinDirection < 0.0:
            self.prevYaw = self.startYaw = curYaw
            self.prevDirection = spinDirection
        caughtSpin = False
        if self.prevYaw < curYaw:
            caughtSpin = self.prevYaw < self.startYaw < curYaw and spinDirection > 0.0
        elif self.prevYaw > curYaw:
            caughtSpin = self.prevYaw > self.startYaw > curYaw and spinDirection < 0.0
        if caughtSpin:
            self.numSpins += 1
            self.spinCounterLabel.text = util.FmtAmt(self.numSpins)
            self.spinCounterTimer = AutoTimer(30000, self.HideSpinCounter)
            if self.numSpins >= self.spinCounterLabel.startSpinCount + 10 and not self.spinCounterLabel.displayTriggered:
                self.spinCounterLabel.Show()
                uicore.animations.BlinkIn(self.spinCounterLabel, duration=0.5, endVal=0.6, loops=2)
                self.spinCounterLabel.displayTriggered = True
            elif self.numSpins % 1000 == 0 and self.spinCounterLabel.displayTriggered:
                uicore.animations.SpColorMorphTo(self.spinCounterLabel, startColor=(1.0, 1.0, 1.0, 0.6), endColor=(0.0, 1.0, 1.0, 1.0), duration=1.0, sleep=True)
                uicore.animations.SpColorMorphTo(self.spinCounterLabel, startColor=(0.0, 1.0, 1.0, 1.0), endColor=(1.0, 1.0, 1.0, 0.6), duration=1.0)
            elif self.numSpins % 100 == 0 and self.spinCounterLabel.displayTriggered:
                uicore.animations.SpColorMorphTo(self.spinCounterLabel, startColor=(1.0, 1.0, 1.0, 0.6), endColor=(1.0, 1.0, 1.0, 1.0), duration=0.75, sleep=True)
                uicore.animations.SpColorMorphTo(self.spinCounterLabel, startColor=(1.0, 1.0, 1.0, 1.0), endColor=(1.0, 1.0, 1.0, 0.6), duration=0.75)
        self.prevYaw = curYaw

    def _ActivateSpinThread(self):
        """
        Make sure the spin thread is actively watching the ship rotation.
        self.spinThread can be None (meaning waiting to restart),
          or it can be a tasklet (meaning it's running),
          or something else (meaning it's killed and shouldn't restart)
        """
        if self.spinThread is None:
            self.spinThread = uthread.new(self._PollCamera)

    def KillSpinThread(self):
        """
        Force-stop counting camera spins.
        """
        if self.spinThread:
            self.spinThread.kill()
            self.spinThread = None

    def _IsCameraSpinning(self, curYaw):
        now = blue.os.GetSimTime()
        if self.prevSpinTime is None:
            self.prevSpinTime = now
        if self.prevYaw is None:
            self.startYaw = self.prevYaw = curYaw
        notIdleFor1Sec = now < self.prevSpinTime + const.SEC
        cameraMoved = self.prevYaw != curYaw
        if cameraMoved:
            self.prevSpinTime = now
        return notIdleFor1Sec or cameraMoved

    def _PollCamera(self):
        cameraStillSpinning = True
        while cameraStillSpinning:
            blue.pyos.synchro.Yield()
            if self.camera is None:
                cameraStillSpinning = False
                break
            curYaw, pitch, roll = geo2.QuaternionRotationGetYawPitchRoll(self.camera.rotationAroundParent)
            cameraStillSpinning = self._IsCameraSpinning(curYaw)
            if cameraStillSpinning:
                self._CountRotations(curYaw)

        self.spinThread = None
