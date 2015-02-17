#Embedded file name: eve/client/script/ui/maingame\eveNavigationService.py
import math
import trinity
import carbonui.const as uiconst
import GameWorld
import geo2
import blue
import carbonui.maingame.navigationService as navsvc
from eve.client.script.movement.eveInputMap import EveInputMap
STOP_DELAY = int(0.05 * const.SEC)

class EveNavigationService(navsvc.CoreNavigationService):
    __guid__ = 'svc.eveNavigation'
    __replaceservice__ = 'navigation'
    __dependencies__ = ['movementClient', 'entityClient', 'mouseInput']

    def Run(self, memStream = None):
        navsvc.CoreNavigationService.Run(self, memStream)
        self.inputMap = None
        self.lastHeading = None
        self.delayTimerActive = False
        self.delayTimerEnd = 0
        self.leftMouseDown = False
        self.rightMouseDown = False
        self.lastForwardBackward = None
        self.lastLeftRight = None
        self.aoClient = sm.GetService('actionObjectClientSvc')
        self.mouseInput.RegisterCallback(const.INPUT_TYPE_MOUSEDOWN, self.OnMouseDown)
        self.mouseInput.RegisterCallback(const.INPUT_TYPE_MOUSEUP, self.OnMouseUp)

    def Stop(self, stream):
        if sm.IsServiceRunning('mouseInput'):
            self.mouseInput.UnRegisterCallback(const.INPUT_TYPE_MOUSEDOWN, self.OnMouseDown)
            self.mouseInput.UnRegisterCallback(const.INPUT_TYPE_MOUSEUP, self.OnMouseUp)

    def OnMouseDown(self, button, posX, posY, entityID):
        if button is const.INPUT_TYPE_LEFTCLICK:
            self.leftMouseDown = True
        elif button is const.INPUT_TYPE_RIGHTCLICK:
            self.rightMouseDown = True

    def OnMouseUp(self, button, posX, posY, entityID):
        if button is const.INPUT_TYPE_LEFTCLICK:
            self.leftMouseDown = False
        elif button is const.INPUT_TYPE_RIGHTCLICK:
            self.rightMouseDown = False

    def _UpdateMovement(self, vkey):
        """
        Called by the command service. Primes the navigation keys and updates last input 
        values. This still goes through the old path of yielding execution thrice, but
        that is something that counts for all of the stuff anyway.
        """
        focus = uicore.registry.GetFocus()
        if focus and focus != self.controlLayer:
            return False
        fwdKey, backKey, moveLKey, moveRKey = self.PrimeNavKeys()
        if vkey in self.navKeys:
            self.hasFocus = True
            if vkey == fwdKey:
                self.lastForwardBackward = const.MOVDIR_FORWARD
            elif vkey == backKey:
                self.lastForwardBackward = const.MOVDIR_BACKWARD
            elif vkey == moveLKey:
                self.lastLeftRight = const.MOVDIR_LEFT
            elif vkey == moveRKey:
                self.lastLeftRight = const.MOVDIR_RIGHT
            return True

    def RecreatePlayerMovement(self):
        """
        Decides local heading values from given input; also switches from pathin to kb
        move mode if needed.
        """
        heading = [0, 0, 0]
        if self.navKeys is None:
            self.PrimeNavKeys()
        if self.inputMap is None:
            self.inputMap = EveInputMap()
        if getattr(self, '_delayedMouseUpStillPending', False):
            return
        player = self.entityClient.GetPlayerEntity()
        if player:
            isPathing = isinstance(player.movement.moveModeManager.GetCurrentMode(), GameWorld.PathToMode)
            if self.HasControl() and trinity.app.IsActive() and player.movement.moveModeManager.allowedToMove:
                curKeyState = self.GetKeyState()
                fwdActive, backActive, moveLActive, moveRActive = curKeyState
                isKeyPressed = fwdActive or backActive or moveLActive or moveRActive
                isMouseDriving = self.leftMouseDown and self.rightMouseDown
                if isKeyPressed or isMouseDriving:
                    if isPathing:
                        player.movement.moveModeManager.PushMoveMode(GameWorld.PlayerInputMode())
                        isPathing = False
                    if self.aoClient.IsEntityUsingActionObject(player.entityID):
                        self.aoClient.ExitActionObject(player.entityID)
                        return
                heading[1] = 0.0
                heading[2] = 0.0
                if backActive and fwdActive and self.lastForwardBackward == const.MOVDIR_BACKWARD or backActive and not fwdActive:
                    heading[2] = -1.0
                elif fwdActive or isMouseDriving:
                    heading[2] = 1.0
                heading[0] = 0.0
                if moveLActive and moveRActive and self.lastLeftRight == const.MOVDIR_LEFT or moveLActive and not moveRActive:
                    heading[0] = 1.0
                elif moveRActive:
                    heading[0] = -1.0
                if not isPathing:
                    heading = self.CheckForStop(heading)
                    mode = player.movement.moveModeManager.GetCurrentMode()
                    cc = sm.GetService('cameraClient')
                    cameraOrbitMode = self.rightMouseDown and not self.leftMouseDown
                    if cameraOrbitMode:
                        yawValue, trash, trash = geo2.QuaternionRotationGetYawPitchRoll(player.GetComponent('position').rotation)
                        moving = 1 if heading[2] == 1 else 0
                        self.inputMap.SetIntendedState(0, moving, 0, False, yawValue)
                    else:
                        yawValue = -math.pi / 2.0 - cc.GetActiveCamera().yaw
                        self.inputMap.SetIntendedState(heading[0], heading[2], int(isMouseDriving), False, yawValue)
                    if hasattr(mode, 'SetDynamicState'):
                        if heading[0] != 0 or heading[2] != 0:
                            mode.SetDynamicState(yawValue)
            elif not isPathing:
                self.inputMap.SetIntendedState(0, 0, 0, 0, 0)
        self.lastHeading = heading

    def CheckForStop(self, heading):
        """
        if the player is going to stop we want to delay a fraction in case they press a
        new key, if that happens then we want to change to the new direction and stop
        the timer
        """
        returnValue = heading
        headingLength = geo2.Vec3Length(heading)
        if not self.delayTimerActive and headingLength < const.FLOAT_TOLERANCE and geo2.Vec3Length(self.lastHeading) > 0:
            returnValue = self.lastHeading
            self.StartStopDelayTimer()
        if self.delayTimerActive and self.delayTimerEnd > blue.os.GetWallclockTime():
            if headingLength < const.FLOAT_TOLERANCE:
                returnValue = self.lastHeading
            else:
                self.StopStopDelayTimer()
        if self.delayTimerActive and self.delayTimerEnd <= blue.os.GetWallclockTime():
            self.StopStopDelayTimer()
        return returnValue

    def StartStopDelayTimer(self):
        self.delayTimerEnd = blue.os.GetWallclockTime() + STOP_DELAY
        self.delayTimerActive = True

    def StopStopDelayTimer(self):
        self.delayTimerEnd = 0
        self.delayTimerActive = False

    def _TurnPlayerToCamera(self):
        pass

    def SetMovementKey(self, direction, keyDown = True):
        """
        Supporting automated tests.
        """
        triapp = trinity.app
        triapp.SetActive()
        fwdKey, backKey, moveLKey, moveRKey = self.PrimeNavKeys()
        movementMaps = {'FORWARD': fwdKey,
         'BACKWARD': backKey,
         'LEFT': moveLKey,
         'RIGHT': moveRKey,
         'SHIFT': uiconst.VK_SHIFT}
        uicore.uilib.SetKey(movementMaps[direction], keyDown)

    def GetKeyState(self):
        """
        Calls said Windows API function for all movement related keys.
        """
        fwdKey, backKey, moveLKey, moveRKey = self.navKeys
        fwdActive = uicore.uilib.Key(fwdKey) if fwdKey is not None else False
        backActive = uicore.uilib.Key(backKey) if backKey is not None else False
        moveLActive = uicore.uilib.Key(moveLKey) if moveLKey is not None else False
        moveRActive = uicore.uilib.Key(moveRKey) if moveRKey is not None else False
        return (fwdActive,
         backActive,
         moveLActive,
         moveRActive)

    def PrimeNavKeys(self):
        """
        Primes the navigation control keys by asking the command service for the keycode.
        This should get refreshed automatically since priming tries to update on every
        keydown event. There could probably be a smarter way of doing this by having the
        command service broadcast such updates, but I don't want to couple these two too
        tightly for the moment.
        """
        if not hasattr(uicore, 'cmd'):
            self.navKeys = []
            return []
        fwdCommand = uicore.cmd.GetShortcutByFuncName('CmdMoveForward')
        backCommand = uicore.cmd.GetShortcutByFuncName('CmdMoveBackward')
        moveLCommand = uicore.cmd.GetShortcutByFuncName('CmdMoveLeft')
        moveRCommand = uicore.cmd.GetShortcutByFuncName('CmdMoveRight')
        self.navKeys = []
        for each in (fwdCommand,
         backCommand,
         moveLCommand,
         moveRCommand):
            if each is not None:
                self.navKeys.append(each[-1])
            else:
                self.navKeys.append(None)

        return self.navKeys

    def Reset(self):
        self.navKeys = None
        self.leftMouseDown = False
        self.rightMouseDown = False

    def Focus(self):
        """
        Give the charControl layer focus and also sets a flag in this service telling it it has focus
        """
        charControlLayer = sm.GetService('viewState').GetView('station').layer
        uicore.registry.SetFocus(charControlLayer)
        self.hasFocus = True
