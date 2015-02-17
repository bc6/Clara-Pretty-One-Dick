#Embedded file name: eve/client/script/ui/shared/mapView/mapViewMarkers\mapViewMarkerBase_Icon.py
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.base import ScaleDpi
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.layoutGrid import LayoutGridRow, LayoutGrid
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.eveLabel import EveLabelMedium, EveLabelSmall
from eve.client.script.ui.control.infoIcon import InfoIcon
from eve.client.script.ui.control.pointerPanel import RefreshPanelPosition
from eve.client.script.ui.shared.mapView.mapViewMarkers.mapViewMarkerBase import MarkerBase
import carbonui.const as uiconst
import math
import weakref
import uthread
import blue

class MarkerIconBase(MarkerBase):
    minVisibleRange = 0.0
    maxVisibleRange = 1000000.0
    texturePath = None
    hintString = None
    distanceFadeAlpha = True
    width = 20
    height = 20
    overlapStackContainer = None
    overlapMarkers = None
    celestialData = None

    def __init__(self, *args, **kwds):
        MarkerBase.__init__(self, *args, **kwds)
        self.texturePath = kwds.get('texturePath', None)
        self.hintString = kwds.get('hintString', None)
        self.distanceFadeAlpha = kwds.get('distanceFadeAlpha', self.distanceFadeAlpha)
        self.projectBracket.offsetY = -ScaleDpi(self.height)

    def Load(self):
        if self.isLoaded:
            return
        self.isLoaded = True
        self.iconSprite = Sprite(parent=self.markerContainer, texturePath=self.texturePath, pos=(2, 2, 16, 16), state=uiconst.UI_DISABLED)
        self.backgroundSprite = Sprite(parent=self.markerContainer, texturePath='res:/UI/Texture/classes/MapView/tagBackground.png', pos=(-22, -9, 64, 64), state=uiconst.UI_DISABLED)
        self.markerContainer.pos = (0,
         0,
         self.width,
         self.height)
        self.markerContainer.hint = self.hintString

    def OnMapMarkerUpdated(self, *args):
        if self.displayStateOverride == False:
            if self.markerContainer:
                self.DestroyRenderObject()
        elif not self.distanceFadeAlpha:
            if self.markerContainer:
                self.markerContainer.opacity = 1.0
            else:
                self.CreateRenderObject()
        else:
            MarkerBase.OnMapMarkerUpdated(self, *args)

    def RegisterOverlapMarkers(self, overlapMarkers):
        if self.overlapMarkers == overlapMarkers:
            return
        self.overlapMarkers = overlapMarkers
        self.iconSprite.opacity = 1.0
        self.backgroundSprite.opacity = 1.0
        if self.markerContainer:
            self.markerContainer.pickState = uiconst.TR2_SPS_ON
        amount = len(overlapMarkers)
        if self.overlapStackContainer is None:
            self.overlapStackContainer = Container(parent=self.markerContainer, align=uiconst.TOPLEFT, pos=(0, 0, 20, 20))
        if len(self.overlapStackContainer.children) != amount:
            self.overlapStackContainer.Flush()
            for i in xrange(min(5, amount)):
                Sprite(parent=self.overlapStackContainer, texturePath='res:/UI/Texture/classes/MapView/tagBackgroundStackIndicator.png', pos=(0,
                 -9 - i * 3,
                 20,
                 20), state=uiconst.UI_DISABLED, opacity=1.0 - i / 5.0)

    def SetOverlappedState(self, overlapState):
        self.overlapMarkers = None
        if self.overlapStackContainer:
            overlapStackContainer = self.overlapStackContainer
            self.overlapStackContainer = None
            overlapStackContainer.Close()
        if overlapState:
            self.iconSprite.opacity = 0.0
            self.backgroundSprite.opacity = 0.0
            if self.markerContainer:
                self.markerContainer.pickState = uiconst.TR2_SPS_OFF
        else:
            self.iconSprite.opacity = 1.0
            self.backgroundSprite.opacity = 1.0
            if self.markerContainer:
                self.markerContainer.pickState = uiconst.TR2_SPS_ON

    def LoadMarkerTooltipPanel(self, tooltipPanel, *args, **kwds):
        tooltipPanel.state = uiconst.UI_NORMAL
        tooltipPanel.columns = 1
        tooltipPanel.margin = 2
        scrollContainer = ScrollContainer(parent=tooltipPanel, pos=(0, 0, 200, 200), align=uiconst.TOPLEFT)
        self.tooltipScrollContainer = weakref.ref(scrollContainer)
        grid = LayoutGrid(parent=scrollContainer)
        grid.OnGridSizeChanged = self.OnGridSizeChanged
        grid.cellPadding = 4
        grid.state = uiconst.UI_NORMAL
        grid.columns = 3
        if self.overlapMarkers:
            sortList = []
            for markerObject in self.overlapMarkers:
                if getattr(markerObject, 'celestialData', None):
                    label = cfg.evelocations.Get(markerObject.celestialData.itemID).name
                    sortList.append(((markerObject.celestialData.groupID, label.lower()), markerObject))
                else:
                    sortList.append(((0, 0), markerObject))

            for _label, markerObject in sorted(sortList):
                grid.AddRow(rowClass=CelestialTooltipRow, markerObject=markerObject)

        grid.AddRow(rowClass=CelestialTooltipRow, markerObject=self)
        scrollContainer.ScrollToVertical(1.0)
        uthread.new(self.UpdateTooltipPosition, tooltipPanel)

    def UpdateTooltipPosition(self, tooltipPanel):
        while not tooltipPanel.destroyed:
            RefreshPanelPosition(tooltipPanel)
            blue.synchro.Yield()

    def OnGridSizeChanged(self, width, height):
        if self.tooltipScrollContainer:
            tooltipScrollContainer = self.tooltipScrollContainer()
            if tooltipScrollContainer and not tooltipScrollContainer.destroyed:
                if height < 200:
                    tooltipScrollContainer.width = width
                    tooltipScrollContainer.height = height
                else:
                    tooltipScrollContainer.width = width + 12
                    tooltipScrollContainer.height = 200


class CelestialTooltipRow(LayoutGridRow):
    default_state = uiconst.UI_NORMAL
    callback = None

    def ApplyAttributes(self, attributes):
        LayoutGridRow.ApplyAttributes(self, attributes)
        self.markerObject = attributes.markerObject
        self.icon = Sprite(pos=(0, 0, 16, 16), texturePath=self.markerObject.texturePath, state=uiconst.UI_DISABLED)
        self.AddCell(cellObject=self.icon, cellPadding=(3, 1, 4, 1))
        self.highLight = Fill(bgParent=self, color=(1, 1, 1, 0.1), state=uiconst.UI_HIDDEN)
        if self.markerObject.celestialData:
            labelText = cfg.evelocations.Get(self.markerObject.celestialData.itemID).name
            label = EveLabelSmall(text=labelText, align=uiconst.CENTERLEFT, width=150, autoFitToText=True)
            self.AddCell(cellObject=label, cellPadding=(0, 1, 6, 1))
            infoIcon = InfoIcon(size=14, align=uiconst.CENTERRIGHT, itemID=self.markerObject.celestialData.itemID, typeID=self.markerObject.celestialData.typeID)
            self.AddCell(cellObject=infoIcon, cellPadding=(0, 1, 1, 1))
        else:
            labelText = self.markerObject.hintString
            label = EveLabelSmall(text=labelText, align=uiconst.CENTERLEFT, width=150, autoFitToText=True)
            self.AddCell(cellObject=label, cellPadding=(0, 1, 6, 1))
            self.FillRow()

    def Close(self, *args):
        LayoutGridRow.Close(self, *args)
        self.markerObject = None

    def OnMouseEnter(self, *args):
        self.highLight.display = True

    def OnMouseExit(self, *args):
        self.highLight.display = False

    def OnClick(self, *args):
        return self.markerObject.OnClick()

    def GetMenu(self):
        return self.markerObject.GetMenu()
