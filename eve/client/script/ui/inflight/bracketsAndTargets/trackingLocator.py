#Embedded file name: eve/client/script/ui/inflight/bracketsAndTargets\trackingLocator.py
import uiprimitives
import carbonui.const as uiconst
import uicontrols
import uix
import uthread
import blue

class TrackingLocator(uiprimitives.Container):
    default_width = 64
    default_height = 64

    def ApplyAttributes(self, attributes):
        self.mouseCookie = None
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.isInteractive = attributes.get('interactive', True)
        self.positionCallback = attributes.get('positionCallback', None)
        self.boundary = attributes.get('boundary', None)
        x, y = attributes.get('desiredPosition', (0, 0))
        sx = uicore.ReverseScaleDpi(x)
        sy = uicore.ReverseScaleDpi(y)
        self.left = sx - self.width / 2
        self.top = sy - self.height / 2
        if self.isInteractive:
            icon = uiprimitives.Sprite(state=uiconst.UI_DISABLED, parent=self, pos=(0, 0, 64, 64), texturePath='res:/UI/Texture/classes/Bracket/customTrackerIndicator.png')
            uicore.animations.BlinkIn(self, startVal=1.0, endVal=0.0, duration=0.2, loops=3, curveType=uiconst.ANIM_WAVE, callback=self.StartFadeSlow)
        else:
            icon = uiprimitives.Sprite(state=uiconst.UI_DISABLED, parent=self, pos=(0, 0, 64, 64), texturePath='res:/UI/Texture/classes/Bracket/centerTrackerIndicator.png')
            uicore.animations.BlinkIn(self, startVal=1.0, endVal=0.0, duration=0.2, loops=3, curveType=uiconst.ANIM_WAVE, callback=self.StartFade)
        self.UpdateTrackingData(persist=False)

    def StartFadeSlow(self):
        uicore.animations.FadeOut(obj=self, duration=2.0, callback=self.Close)

    def StartFade(self):
        uicore.animations.FadeOut(obj=self, duration=1.0, callback=self.Close)

    def SetBoundaries(self, boundaries):
        self.boundary = boundaries

    def OnMouseDown(self, *args):
        if not self.isInteractive:
            return
        self.StopAnimations()
        uicore.animations.FadeIn(obj=self, duration=0.1)
        absX, absY = self.GetAbsolutePosition()
        diffX = absX - uicore.uilib.x
        diffY = absY - uicore.uilib.y
        self.dragPositionOffset = (diffX, diffY)
        self.dragging = 1
        uthread.new(self.BeginDrag, diffX, diffY)
        self.mouseCookie = uicore.uilib.RegisterForTriuiEvents(uiconst.UI_MOUSEUP, self.OnGlobalMouseUp)

    def GetCenterPoint(self):
        return (self.left + self.width / 2, self.top + self.height / 2)

    def UpdateTrackingData(self, persist):
        if self.positionCallback:
            x, y = self.GetCenterPoint()
            self.positionCallback(uicore.ScaleDpi(x), uicore.ScaleDpi(y), persist=persist)

    def BeginDrag(self, diffX, diffY, *args):
        while not self.destroyed and getattr(self, 'dragging', 0):
            mx = uicore.uilib.x
            my = uicore.uilib.y
            w, h = uicore.desktop.width, uicore.desktop.height
            if self.boundary:
                leftBoundary = self.boundary[0]
                topBoundary = self.boundary[1]
                rightBoundary = self.boundary[2]
                bottomBoundary = self.boundary[3]
                x = max(leftBoundary, min(rightBoundary, uicore.uilib.x))
                y = max(topBoundary, min(bottomBoundary, uicore.uilib.y))
                self.left = diffX + x
                self.top = diffY + y
            self.UpdateTrackingData(persist=False)
            blue.synchro.SleepWallclock(1)

    def OnGlobalMouseUp(self, *args):
        self.UpdateTrackingData(persist=True)
        self.StopDragging()
        uicore.animations.FadeOut(obj=self, callback=self.Close)

    def StopDragging(self):
        self.dragging = 0
        if self.mouseCookie:
            uicore.event.UnregisterForTriuiEvents(self.mouseCookie)
        self.mouseCookie = None

    def Close(self):
        self.StopDragging()
        super(TrackingLocator, self).Close()
