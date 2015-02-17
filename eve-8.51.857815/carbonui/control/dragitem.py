#Embedded file name: carbonui/control\dragitem.py
import blue
import carbonui.const as uiconst
from carbonui.primitives.container import Container

class DragContainerCore(Container):
    __guid__ = 'uicontrols.DragContainerCore'
    _dragInited = False

    def _OnClose(self, *args):
        if getattr(self, 'dragSound', None):
            uicore.audioHandler.StopSoundLoop(self.dragSound)
        Container._OnClose(self, *args)
        self.dragData = None

    def InitiateDrag(self, mouseOffset):
        if not self or self.destroyed or self._dragInited:
            return
        self._dragInited = True
        mx, my = mouseOffset
        while uicore.uilib.leftbtn and not self.destroyed and uicore.IsDragging():
            self.state = uiconst.UI_DISABLED
            self.left = uicore.uilib.x - mx
            self.top = uicore.uilib.y - my
            blue.pyos.synchro.Yield()
