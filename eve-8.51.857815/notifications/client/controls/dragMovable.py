#Embedded file name: notifications/client/controls\dragMovable.py
import blue
import uthread
import carbonui.const as uiconst

class DragMovable(object):

    def __init__(self, object, buttonObject, onDrag, onDragEnter, onDragFinished, startPosition):
        self._dragObject = object
        self._buttonObject = buttonObject
        self._onDragCallback = onDrag
        self._onDragEnter = onDragEnter
        self._onDragFinished = onDragFinished
        self.customX, self.customY = startPosition
        self._clickedInMeanTime = False
        self._buttonObject.OnMouseDown = self._OnMouseDown
        self._buttonObject.OnMouseUp = self._OnMouseUp
        self._positioning = False
        self._dragDelayTimer = 300
        self._disabled = False
        self._animationLength = 0.25
        self._rotateAnimation = None
        self._enableRotation = False
        self._isMouseDown = False

    def _OnMouseDown(self, buttonFlag, *args):
        if self._disabled or self._isMouseDown or buttonFlag is not uiconst.MOUSELEFT:
            return
        self._isMouseDown = True
        self.mouseCookie = None
        self._startX = uicore.uilib.x
        self._startY = uicore.uilib.y
        self._clickedInMeanTime = False
        uthread.new(self._ShouldIDragTimer)

    def _OnMouseUp(self, buttonFlag, *args):
        if buttonFlag is uiconst.MOUSELEFT:
            self._isMouseDown = False
            self.StopDragMode()

    def Interrupt(self):
        self._clickedInMeanTime = True

    def _ShouldIDragTimer(self):
        blue.synchro.SleepWallclock(self._dragDelayTimer)
        if self._clickedInMeanTime or self._disabled:
            return
        dx = self._startX - uicore.uilib.x
        dy = self._startY - uicore.uilib.y
        totaldelta = abs(dx) + abs(dy)
        if totaldelta < 5:
            self._EnterDragMode()

    def _StartAnimations(self):
        obj = self._dragObject
        obj.scalingCenter = (0.5, 0.5)
        uicore.animations.Tr2DScaleTo(obj, startScale=(1.0, 1.0), endScale=(1.25, 1.25), duration=self._animationLength, loops=1, curveType=2, callback=None, sleep=False, timeOffset=0.0, curveSet=None)
        if self._enableRotation:
            self._rotateAnimation = uicore.animations.Tr2DRotateTo(obj, startAngle=0.0, endAngle=0.183185307179586, duration=0.25, loops=999, curveType=4, callback=None, sleep=False, timeOffset=0.0, curveSet=None)

    def SetEnabled(self, enabled):
        self._disabled = not enabled

    def _EnterDragMode(self):
        self._onDragEnter()
        self._positioning = True
        self.clickInterruptedByDrag = True
        self._StartAnimations()
        uthread.new(self._WhileDragging, uicore.uilib.x, uicore.uilib.y)

    def IsDragging(self):
        return self._positioning

    def _WhileDragging(self, startX, startY, *args):
        startCustomX = self.customX
        startCustomY = self.customY
        while self._positioning:
            if uicore.uilib.leftbtn is False:
                self.StopDragMode()
                return
            mx = uicore.uilib.x
            my = uicore.uilib.y
            dx = startX - mx
            dy = startY - my
            self.customX = dx + startCustomX
            self.customY = dy + startCustomY
            self._onDragCallback(self.customX, self.customY)
            blue.synchro.SleepWallclock(1)

    def _StopDragAnimation(self, finishedCallback = None):
        obj = self._dragObject
        uicore.animations.Tr2DScaleTo(obj, startScale=(1.25, 1.25), endScale=(1.0, 1.0), duration=self._animationLength, loops=1, curveType=2, callback=finishedCallback, sleep=False, timeOffset=0.0, curveSet=None)
        if self._rotateAnimation:
            self._rotateAnimation.Stop()
            uicore.animations.Tr2DRotateTo(obj, startAngle=obj.rotation, endAngle=0.0, duration=self._animationLength, loops=1, curveType=2, callback=None, sleep=False, timeOffset=0.0, curveSet=None)

    def StopDragMode(self):
        if self._positioning:
            self._positioning = False
            self._StopDragAnimation(finishedCallback=self._onDragFinished)
