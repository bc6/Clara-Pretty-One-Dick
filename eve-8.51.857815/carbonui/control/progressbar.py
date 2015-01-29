#Embedded file name: carbonui/control\progressbar.py
import mathUtil
import blue
import carbonui.const as uiconst
import uthread
import types
from carbonui.primitives.container import Container
from carbonui.primitives.frame import FrameCoreOverride as Frame

class ProgressbarCore(Container):
    __guid__ = 'uicls.ProgressbarCore'
    PB_OFFSET = 2

    def ApplyAttributes(self, attributes):
        super(ProgressbarCore, self).ApplyAttributes(attributes)
        self._stop = False
        self._countDown = False
        self._lastPortion = None
        self.Prepare_()

    def Prepare_(self, *args, **kw):
        prParent = Container(parent=self, align=uiconst.TOALL)
        self.sr.progressBar = Container(parent=prParent, clipChildren=True, align=uiconst.TOLEFT)
        self.PBGRAPHICMARGIN = -3
        self.PBGRAPHICCORNER = 7
        self.sr.progressBarGraphic = Frame(parent=self.sr.progressBar, frameConst=('ui_1_16_111', self.PBGRAPHICCORNER, self.PBGRAPHICMARGIN), state=uiconst.UI_DISABLED, color=(1.0, 0.0, 0.0, 1.0), align=uiconst.TOALL)
        Frame(parent=self, frameConst=uiconst.FRAME_FILLED_CORNER9, state=uiconst.UI_DISABLED, color=(0.0, 0.0, 0.0, 1.0), align=uiconst.TOALL)

    def StartProgress(self, startTime, endTime, countDown = False, color = (1.0, 0.0, 0.0, 1.0), callback = None):
        """
        Start progress with fixed start and endtime which should be blue time.
        pb.StartProgress(t, t+SEC*1) would display progress of one second
        """
        self.sr.progressBarGraphic.SetState(uiconst.UI_HIDDEN)
        self.Stop()
        self.sr.progressBarGraphic.SetRGB(*color)
        self._lastPortion = None
        self._countDown = countDown
        uthread.new(self._Progress, startTime, endTime, callback)

    def StartProgressLoop(self, loopSpeed, countDown = False, color = (1.0, 0.0, 0.0, 1.0), callback = None):
        """
        Start progress with fixed loopSpeed which should be in milliseconds.
        pb.StartProgressLoop(1000.0) would display looping progress of one second
        """
        self.sr.progressBarGraphic.SetState(uiconst.UI_HIDDEN)
        self.Stop()
        self._lastPortion = None
        self.sr.progressBarGraphic.SetRGB(*color)
        self._countDown = countDown
        uthread.new(self._Loop, loopSpeed, callback)

    def Stop(self):
        """
        Stop current progress
        """
        self._stop = True

    def _Progress(self, startTime, endTime, callback = None):
        if self.destroyed:
            return
        speed = float(endTime - startTime) / 10000.0
        ndt = 0.0
        self._stop = False
        while ndt != 1.0:
            try:
                ndt = max(ndt, min(blue.os.TimeDiffInMs(startTime, blue.os.GetWallclockTime()) / speed, 1.0))
            except:
                ndt = 1.0

            self.UpdateProgress_(ndt)
            self.sr.progressBarGraphic.SetState(uiconst.UI_DISABLED)
            blue.pyos.synchro.Yield()
            if self.destroyed or self._stop:
                return

        if callback:
            if type(callback) == types.TupleType:
                callback, args = callback
                callback(*args)
            else:
                callback()

    def _Loop(self, speed, callback = None):
        self._stop = False
        while not self.destroyed:
            startTime = blue.os.GetWallclockTime()
            self._Progress(startTime, startTime + speed * 10000.0)
            if self.destroyed or self._stop:
                return

        if callback:
            if type(callback) == types.TupleType:
                callback, args = callback
                callback(*args)
            else:
                callback()

    def _OnResize(self, *args, **kw):
        Container._OnResize(self, *args, **kw)
        if self._lastPortion is not None:
            self.UpdateProgress_(self._lastPortion)

    def UpdateProgress_(self, ndt):
        l, t, w, h = self.GetAbsolute()
        if self._countDown:
            self.sr.progressBar.width = w - int(mathUtil.Lerp(0, w, ndt))
        else:
            self.sr.progressBar.width = int(mathUtil.Lerp(0, w, ndt))
        minWidth = self.PBGRAPHICMARGIN * 2 + self.sr.progressBarGraphic.rectWidth
        if self.sr.progressBar.width <= minWidth:
            self.sr.progressBarGraphic.width = self.PBGRAPHICMARGIN + (self.sr.progressBar.width - minWidth)
        else:
            self.sr.progressBarGraphic.width = self.PBGRAPHICMARGIN
        self._lastPortion = ndt
