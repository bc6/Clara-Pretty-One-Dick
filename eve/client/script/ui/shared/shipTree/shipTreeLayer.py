#Embedded file name: eve/client/script/ui/shared/shipTree\shipTreeLayer.py
import uicls
import carbonui.const as uiconst
from shipTreeContainer import ShipTreeContainer
from carbonui.primitives.fill import Fill
from eve.client.script.ui.shared.shipTree.shipTreeConst import ZOOMED_IN, ZOOMED_OUT, COLOR_BG, MAIN_FACTIONS, PAD_SIDE, PAD_TOP
from eve.client.script.ui.control.panContainer import PanContainer
import blue

class ShipTreeLayer(uicls.LayerCore):
    """
    The ship tree layer. Takes care of forwarding input events.
    """
    __guid__ = 'uicls.ShipTreeLayer'
    isTabStop = True
    cursor = uiconst.UICURSOR_DRAGGABLE
    __notifyevents__ = ('OnEndChangeDevice', 'OnGraphicSettingsChanged')

    def OnOpenView(self):
        sm.RegisterNotify(self)
        self.Flush()
        for child in self.background:
            child.Close()

        self.isZooming = False
        self.isPanning = False
        self.zoomLevel = ZOOMED_IN
        self.shipTreeCont = None
        self.isFadingFrame = False
        self.bg = Fill(name='bg', bgParent=self, color=COLOR_BG)
        self.panCont = PanContainer(parent=self, state=uiconst.UI_PICKCHILDREN, callback=self.OnPanContainer)
        self.UpdatePanContainerBorder()

    def UpdatePanContainerBorder(self):
        """ Deal with camera center offset """
        camOffset = settings.user.ui.Get('cameraOffset', 0) / 100.0
        offset = uicore.desktop.width / 2 * camOffset
        padLeft = max(PAD_SIDE, PAD_SIDE - offset)
        padRight = max(PAD_SIDE, PAD_SIDE + offset)
        self.panCont.border = (padLeft,
         PAD_TOP,
         padRight,
         PAD_TOP)

    def OnEndChangeDevice(self, *args):
        self.UpdatePanContainerBorder()

    def OnGraphicSettingsChanged(self, *args):
        self.UpdatePanContainerBorder()

    def SelectFaction(self, factionID, oldFactionID = None):
        if self.shipTreeCont:
            uicore.animations.FadeOut(self.shipTreeCont, callback=self.shipTreeCont.Close, duration=0.15)
        blue.synchro.Sleep(200)
        self.shipTreeCont = ShipTreeContainer(parent=self.panCont.mainCont, align=uiconst.TOPLEFT, factionID=factionID, idx=0, callback=self.OnMainContResize, alignMode=uiconst.TOPLEFT, opacity=0.0)
        self.shipTreeCont.SetSizeAutomatically()
        uicore.animations.FadeIn(self.shipTreeCont, duration=0.3)
        self.panCont.mainCont.SetSizeAutomatically()
        uicore.animations.FadeTo(self.bg, self.bg.opacity, 1.0, duration=1.0)
        self.panTarget = None
        if not oldFactionID:
            panTo = settings.user.ui.Get('ShipTreePanPosition', None)
            if panTo:
                self.panCont.PanTo(panTo[0], panTo[1], animate=False)
            else:
                self.PanToFirstNode()
        elif not (factionID in MAIN_FACTIONS and oldFactionID in MAIN_FACTIONS):
            self.PanToFirstNode()

    def OnMainContResize(self):
        width = self.panCont.mainCont.width
        self.shipTreeCont.bgCont.width = width + 128
        self.shipTreeCont.bgCont.height = self.panCont.mainCont.height + 128

    def OnPanContainer(self):
        """ Move grid based on pan amount for parallax effect """
        if not self.shipTreeCont:
            return
        k = 0.05
        left = self.panCont.panLeft
        moveAmount = k * (self.shipTreeCont.width - 2 * PAD_SIDE)
        self.shipTreeCont.bgCont.left = int(moveAmount * (0.5 - left))
        top = self.panCont.panTop
        moveAmount = k * (self.shipTreeCont.height - 2 * PAD_TOP)
        self.shipTreeCont.bgCont.top = int(moveAmount * (0.5 - top))
        if self.zoomLevel != ZOOMED_IN:
            self.shipTreeCont.bgCont.left -= self.shipTreeCont.bgCont.left % 2
            self.shipTreeCont.bgCont.top -= self.shipTreeCont.bgCont.top % 2
        self.shipTreeCont.factionBG.left = self.shipTreeCont.bgCont.left * 0.5
        self.shipTreeCont.factionBG.top = self.shipTreeCont.bgCont.top * 0.5
        if self.panCont.panTop in (0.0, 1.0):
            if self.isFadingFrame:
                return
            self.isFadingFrame = True
            if self.panCont.panTop == 0.0:
                uicore.animations.FadeTo(self.shipTreeCont.topFrame, 3.0, 1.0, duration=0.3, loops=1)
            else:
                uicore.animations.FadeTo(self.shipTreeCont.bottomFrame, 3.0, 1.0, duration=0.3, loops=1)
        else:
            self.isFadingFrame = False

    def OnCloseView(self):
        sm.UnregisterNotify(self)
        if self.bg:
            self.bg.Close()
        if self.shipTreeCont:
            self.shipTreeCont.Close()
        settings.user.ui.Set('ShipTreePanPosition', (self.panCont.panLeft, self.panCont.panTop))
        sm.GetService('shipTree').EmptyRecentlyChangedSkillsCache()

    def OnMouseDown(self, *args):
        self.isPanning = True

    def OnMouseUp(self, *args):
        self.isPanning = False

    def OnMouseMove(self, *args):
        if not self.isPanning:
            return
        PanContainer.OnMouseMove(self.panCont)
        if uicore.uilib.leftbtn and uicore.uilib.rightbtn:
            dy = uicore.uilib.dy
            if dy < 0:
                self.ZoomTo(ZOOMED_OUT)
            elif dy > 0:
                self.ZoomTo(ZOOMED_IN)
        elif uicore.uilib.leftbtn:
            sm.GetService('shipTreeUI').CloseInfoBubble()

    def PanToNode(self, node, animate = True):
        x, y = node.GetPositionProportional()
        s = 0.1
        x = (1.0 + 2 * s) * x - s
        x = max(0.0, min(x, 1.0))
        y = (1.0 + 2 * s) * y - s
        y = max(0.0, min(y, 1.0))
        self.panCont.PanTo(x, y, animate)

    def PanToFirstNode(self):
        node = self.shipTreeCont.rootNode.children[0]
        self.PanToNode(node, animate=False)

    def PanToShipGroup(self, shipGroupID, animate = True):
        node = self.shipTreeCont.rootNode.GetChildByID(shipGroupID)
        self.PanToNode(node, animate)

    def OnDblClick(self, *args):
        if self.zoomLevel == ZOOMED_OUT:
            self.ZoomTo(ZOOMED_IN)
        else:
            self.ZoomTo(ZOOMED_OUT)

    def OnMouseWheel(self, *args):
        self.OnZoom(uicore.uilib.dz)

    def OnZoom(self, dz):
        if self.isZooming:
            return
        if dz < 0:
            self.ZoomTo(ZOOMED_IN)
        else:
            self.ZoomTo(ZOOMED_OUT)

    def ZoomTo(self, zoomLevel):
        if self.isZooming or zoomLevel == self.zoomLevel:
            return
        try:
            duration = 0.6
            self.isZooming = True
            self.zoomLevel = zoomLevel
            uicore.animations.MorphScalar(self.panCont, 'scale', self.panCont.scale, self.zoomLevel, duration=duration, callback=self.OnZoomingDone)
            sm.ScatterEvent('OnShipTreeZoomChanged', self.zoomLevel)
            sm.GetService('shipTreeUI').CloseInfoBubble()
        except:
            self.isZooming = False
            raise

    def OnZoomingDone(self):
        self.isZooming = False

    def OnBack(self):
        sm.GetService('shipTreeUI').GoBack()

    def OnForward(self):
        sm.GetService('shipTreeUI').GoForward()
