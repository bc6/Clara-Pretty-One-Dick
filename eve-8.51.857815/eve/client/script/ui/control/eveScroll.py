#Embedded file name: eve/client/script/ui/control\eveScroll.py
from carbonui.control.menu import HasContextMenu, GetContextMenuOwner
from carbonui.util import various_unsorted
from carbonui.control.scroll import ScrollCore, ScrollHandle
from carbonui.control.scroll import ScrollControlsCore
from carbonui.control.scroll import ColumnHeaderCore
from eve.client.script.ui.control.eveLabel import EveCaptionMedium
from eve.client.script.ui.control.eveWindowUnderlay import BumpedUnderlay, FillUnderlay
from eve.client.script.ui.control.eveLabel import EveLabelSmall
import uiprimitives
import carbonui.const as uiconst
import util
import blue
import uthread
import fontConst
SCROLLMARGIN = 0
MINCOLUMNWIDTH = 24

class Scroll(ScrollCore):
    """
    A sortable multi column table with scrolling. Populated with entries for the listentry namespace.
    If scrolling is the only functionality required (no columns, sorting, etc.) use ScrollContainer instead. 
    """
    __guid__ = 'uicontrols.Scroll'
    headerFontSize = fontConst.EVE_SMALL_FONTSIZE
    sortGroups = False

    def Prepare_ScrollControls_(self):
        self.sr.scrollcontrols = ScrollControls(name='__scrollcontrols', parent=self.sr.maincontainer, align=uiconst.TORIGHT, width=7, state=uiconst.UI_HIDDEN, idx=0, clipChildren=True)
        self.sr.scrollcontrols.Startup(self)

    def Prepare_Underlay_(self):
        self.sr.underlay = BumpedUnderlay(parent=self, name='background')

    def Startup(self, minZ = None):
        pass

    def HideBackground(self, alwaysHidden = 0):
        frame = None
        if various_unsorted.GetAttrs(self, 'sr', 'underlay'):
            self.sr.underlay.state = uiconst.UI_HIDDEN
            frame = self.sr.underlay
        if frame and getattr(frame, 'parent'):
            underlayFrame = frame.parent.FindChild('underlayFrame')
            underlayFill = frame.parent.FindChild('underlayFill')
            if underlayFrame:
                underlayFrame.state = uiconst.UI_HIDDEN
            if underlayFill:
                underlayFill.state = uiconst.UI_HIDDEN
        if alwaysHidden:
            self.SetNoBackgroundFlag(alwaysHidden)

    def OnMouseWheel(self, *etc):
        if getattr(self, 'wheeling', 0):
            return 1
        if HasContextMenu():
            menuOwner = GetContextMenuOwner()
            if menuOwner and menuOwner.IsUnder(self):
                return 1
        self.wheeling = 1
        self.Scroll(uicore.uilib.dz / 240.0)
        self.wheeling = 0
        self.sr.scrollcontrols.AnimFade()
        return 1

    def GetNoItemNode(self, text, sublevel = 0, *args):
        import listentry
        return listentry.Get('Generic', {'label': text,
         'sublevel': sublevel})

    def ShowHint(self, hint = None):
        isNew = self.sr.hint is None or self.sr.hint.text != hint
        if self.sr.hint is None and hint:
            clipperWidth = self.GetContentWidth()
            self.sr.hint = EveCaptionMedium(parent=self.sr.clipper, align=uiconst.TOPLEFT, left=16, top=32, width=clipperWidth - 32, text=hint)
        elif self.sr.hint is not None and hint:
            self.sr.hint.text = hint
            self.sr.hint.state = uiconst.UI_DISABLED
            isNew = isNew or self.sr.hint.display == False
        elif self.sr.hint is not None and not hint:
            self.sr.hint.state = uiconst.UI_HIDDEN
        if self.sr.hint and self.sr.hint.display and isNew:
            uicore.animations.FadeTo(self.sr.hint, 0.0, 0.5, duration=0.3)

    def RecyclePanel(self, panel, fromWhere = None):
        if panel.__guid__ == 'listentry.VirtualContainerRow':
            subnodes = [ node for node in panel.sr.node.internalNodes if node is not None ]
            for node in subnodes:
                node.panel = None

        ScrollCore.RecyclePanel(self, panel, fromWhere)


class ScrollControls(ScrollControlsCore):
    __guid__ = 'uicontrols.ScrollControls'

    def ApplyAttributes(self, attributes):
        ScrollControlsCore.ApplyAttributes(self, attributes)
        self.animFadeThread = None

    def Prepare_(self):
        self.Prepare_ScrollHandle_()
        FillUnderlay(name='underlay', bgParent=self)

    def Prepare_ScrollHandle_(self):
        subparent = uiprimitives.Container(name='subparent', parent=self, align=uiconst.TOALL, padding=(0, 0, 0, 0))
        self.sr.scrollhandle = ScrollHandle(name='__scrollhandle', parent=subparent, align=uiconst.TOPLEFT, pos=(0, 0, 0, 0), state=uiconst.UI_NORMAL)

    def AnimFade(self):
        self.fadeEndTime = blue.os.GetTime() + 0.3 * const.SEC
        if not self.animFadeThread:
            self.sr.scrollhandle.OnMouseEnter()
            uthread.new(self._AnimFadeThread)

    def _AnimFadeThread(self):
        while blue.os.GetTime() < self.fadeEndTime:
            blue.synchro.Yield()

        if uicore.uilib.mouseOver != self.sr.scrollhandle:
            self.sr.scrollhandle.OnMouseExit()
        self.animFadeThread = None


class ColumnHeader(ColumnHeaderCore):
    __guid__ = 'uicontrols.ScrollColumnHeader'

    def Prepare_Label_(self):
        textclipper = uiprimitives.Container(name='textclipper', parent=self, align=uiconst.TOALL, padding=(6, 2, 6, 0), state=uiconst.UI_PICKCHILDREN, clipChildren=1)
        self.sr.label = EveLabelSmall(text='', parent=textclipper, hilightable=1, state=uiconst.UI_DISABLED)


from carbonui.control.scroll import ScrollCoreOverride, ColumnHeaderCoreOverride
ScrollCoreOverride.__bases__ = (Scroll,)
ColumnHeaderCoreOverride.__bases__ = (ColumnHeader,)
