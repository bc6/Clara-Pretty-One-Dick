#Embedded file name: notifications/client/controls\notificationScrollContainer.py
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.base import ReverseScaleDpi, ScaleDpiF
from carbonui.primitives.container import Container
import carbonui.const as uiconst
from carbonui.primitives.frame import Frame

class NotificationScrollContainer(ScrollContainer):
    entryLoadEnabled = True
    contentHeight = 0
    mainContTopHeight = (0, 0)

    def ApplyAttributes(self, attributes):
        ScrollContainer.ApplyAttributes(self, attributes)
        self.mainCont.Close()
        self.mainCont = Container(name='mainCont', parent=self.clipCont, state=uiconst.UI_NORMAL, align=uiconst.TOPLEFT)
        self.mainContTopHeight = (0, 0)
        self.mainCont._OnResize = self._OnMainContResize

    def EnableEntryLoad(self):
        self.entryLoadEnabled = True
        self.LoadVisibleEntries()

    def DisableEntryLoad(self):
        self.entryLoadEnabled = False

    def _OnMainContResize(self, *args):
        newTopHeight = (self.mainCont.top, self.mainCont.height)
        if newTopHeight != self.mainContTopHeight:
            self.mainContTopHeight = newTopHeight
            self.LoadVisibleEntries()

    def LoadVisibleEntries(self):
        if not self.entryLoadEnabled:
            return
        for each in self.mainCont.children:
            self.LoadEntryIfVisible(each)

    def LoadEntryIfVisible(self, entry):
        topOffset = self.mainCont.top
        visibleHeight = ReverseScaleDpi(self.clipCont.displayHeight)
        if topOffset + entry.top + entry.height >= 0 and topOffset + entry.top <= visibleHeight:
            entry.UpdateAlignmentAsRoot()
            entry.LoadContent()
            entry.display = True
        else:
            entry.display = False

    def _OnVerticalScrollBar(self, posFraction):
        posFraction = max(0.0, min(posFraction, 1.0))
        self.mainCont.top = -posFraction * (self.mainCont.height - ReverseScaleDpi(self.clipCont.displayHeight))

    def _InsertChild(self, idx, obj):
        self.mainCont.children.insert(idx, obj)
        contentWidth = ReverseScaleDpi(self.displayWidth)
        minContentHeight = ReverseScaleDpi(self.clipCont.displayHeight)
        self.mainCont.width = contentWidth
        obj.top = self.contentHeight
        obj.width = contentWidth
        obj.displayY = ScaleDpiF(self.contentHeight)
        obj.displayWidth = ScaleDpiF(contentWidth)
        self.contentHeight += obj.height
        self.mainCont.height = max(minContentHeight, self.contentHeight)
        self._UpdateScrollbars()
        self.LoadEntryIfVisible(obj)

    def Flush(self):
        ScrollContainer.Flush(self)
        self.contentHeight = 0
