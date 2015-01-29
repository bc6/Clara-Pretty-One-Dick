#Embedded file name: eve/client/script/ui/shared/mapView/mapViewMarkers\mapViewMarkerBase.py
from carbon.common.script.util.commonutils import StripTags
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.primitives.base import ScaleDpi, ReverseScaleDpi, ScaleDpiF
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.frame import Frame
from carbonui.primitives.sprite import Sprite
from carbonui.util.bunch import Bunch
from eve.client.script.ui.control.eveBaseLink import BaseLink
from eve.client.script.ui.control.eveLabel import EveLabelMedium
from eve.client.script.ui.shared.mapView.mapViewConst import MARKER_POINT_BOTTOM, MARKER_POINT_TOP, MARKER_POINT_LEFT, MARKER_POINT_RIGHT
import trinity
import blue
import weakref
import carbonui.const as uiconst
import math

class MarkerContainerBase(Container):
    """
    Dynamically loaded container intended to hold the map marker content
    and handling mouse events for that marker
    """
    default_align = uiconst.NOALIGN
    default_opacity = 1.0
    default_state = uiconst.UI_NORMAL
    markerObject = None
    isDragObject = True

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.markerObject = attributes.markerObject
        self.renderObject.displayY = -1000

    def Close(self, *args):
        Container.Close(self, *args)
        self.markerObject = None

    def OnClick(self, *args):
        self.clickTimer = AutoTimer(250, self.ClickMarker, uicore.uilib.Key(uiconst.VK_CONTROL))

    def OnDblClick(self, *args):
        self.ClickMarker(True)

    def ClickMarker(self, zoomTo):
        self.clickTimer = None
        if self.markerObject:
            self.markerObject.OnMapMarkerContainerClicked(self, zoomTo)

    def OnMouseEnter(self, *args):
        if not self.IsNavigating() and self.markerObject.hilightCallback:
            self.markerObject.hilightCallback(self.markerObject)

    def IsNavigating(self):
        return uicore.uilib.leftbtn or uicore.uilib.rightbtn

    def GetMenu(self):
        return self.markerObject.GetMenu()

    def LoadTooltipPanel(self, *args, **kwds):
        self.markerObject.LoadMarkerTooltipPanel(*args, **kwds)

    @apply
    def opacity():
        doc = 'Opacity of map marker container, intended to override distance opacity if needed'

        def fget(self):
            return self._opacity

        def fset(self, value):
            self._opacity = value
            if self.markerObject and (self.markerObject.activeState or self.markerObject.hilightState):
                renderOpacity = 1.0
            else:
                renderOpacity = value
            self.renderObject.opacity = renderOpacity

        return property(**locals())

    def UpdateBackgrounds(self):
        for each in self.background:
            pl, pt, pr, pb = each.padding
            each.displayRect = (ScaleDpiF(pl),
             ScaleDpiF(pt),
             self._displayWidth - ScaleDpiF(pl + pr),
             self._displayHeight - ScaleDpiF(pt + pb))

    def GetDragData(self, *args):
        return self.markerObject.GetDragData(self, *args)

    @classmethod
    def PrepareDrag(cls, *args):
        return BaseLink.PrepareDrag(*args)


class MarkerBase(object):
    isLoaded = False
    maxVisibleRange = 1000000.0
    minVisibleRange = 0.0
    markerID = None
    position = (0, 0, 0)
    overridePosition = None
    destroyed = False
    displayStateOverride = None
    markerContainer = None
    parentContainer = None
    extraContainer = None
    curveSet = None
    selectionCallback = None
    hilightCallback = None
    eventHandler = None
    scaledCenter = None
    solarSystemID = None
    positionPickable = False
    hilightState = False
    activeState = False

    def __init__(self, markerID, markerHandler, parentContainer, position, curveSet, selectionCallback = None, hilightCallback = None, eventHandler = None, **kwds):
        self.markerID = markerID
        projectBracket = trinity.EveProjectBracket()
        curveSet.curves.append(projectBracket)
        self.maxVisibleRange = kwds.get('maxVisibleRange', self.maxVisibleRange)
        projectBracket.maxDispRange = self.maxVisibleRange
        self.projectBracket = projectBracket
        self.parentContainer = weakref.ref(parentContainer)
        self.curveSet = weakref.ref(curveSet)
        projectBracket.bracketUpdateCallback = self.OnMapMarkerUpdated
        projectBracket.displayChangeCallback = self.OnMapMarkerDisplayChange
        self.selectionCallback = selectionCallback
        self.hilightCallback = hilightCallback
        self.markerHandler = markerHandler
        self.eventHandler = eventHandler
        self.SetPosition(position)

    def Close(self):
        self.DestroyRenderObject()
        if self.curveSet:
            curveSet = self.curveSet()
            if curveSet:
                curveSet.curves.fremove(self.projectBracket)
        self.selectionCallback = None
        self.hilightCallback = None
        self.markerHandler = None
        self.eventHandler = None
        self.curveSet = None
        self.projectBracket = None
        self.parentContainer = None
        self.markerContainer = None

    def FadeOutAndClose(self):
        if self.markerContainer and not self.markerContainer.destroyed and self.markerContainer.opacity:
            uicore.animations.FadeTo(self.markerContainer, startVal=self.markerContainer.opacity, endVal=0.0, callback=self.Close)
        else:
            self.Close()

    def GetExtraMouseOverInfo(self):
        if self.markerHandler:
            return self.markerHandler.GetExtraMouseOverInfoForMarker(self.markerID)

    def SetHilightState(self, hilightState):
        self.hilightState = hilightState
        self.lastUpdateCameraValues = None

    def SetActiveState(self, activeState):
        self.activeState = activeState
        self.lastUpdateCameraValues = None

    def UpdateActiveAndHilightState(self, *args, **kwds):
        pass

    def MoveToFront(self):
        if self.parentContainer:
            parentContainer = self.parentContainer()
            if not parentContainer or parentContainer.destroyed:
                return
            if self.markerContainer and not self.markerContainer.destroyed:
                renderObject = self.markerContainer.renderObject
                parentContainer.renderObject.children.remove(renderObject)
                parentContainer.renderObject.children.insert(0, renderObject)
            if self.extraContainer and not self.extraContainer.destroyed:
                renderObject = self.extraContainer.renderObject
                parentContainer.renderObject.children.remove(renderObject)
                parentContainer.renderObject.children.insert(0, renderObject)

    def GetBoundaries(self):
        mx, my = self.projectBracket.rawProjectedPosition
        return (mx - 4,
         my - 4,
         mx + 4,
         my + 4)

    def GetCameraDistance(self):
        return self.projectBracket.cameraDistance

    def SetPosition(self, position):
        self.position = position
        self.UpdatePosition()

    def SetPositionOverride(self, overridePosition):
        self.overridePosition = overridePosition
        self.UpdatePosition()

    def SetSolarSystemID(self, solarSystemID):
        self.solarSystemID = solarSystemID

    def GetSolarSystemID(self):
        return self.solarSystemID

    def OnMapMarkerDisplayChange(self, projectBracket, displayState):
        if displayState == False:
            self.DestroyRenderObject()

    def OnMapMarkerUpdated(self, projectBracket):
        if self.displayStateOverride == False:
            if self.markerContainer:
                self.DestroyRenderObject()
        else:
            cameraTranslationFromParent = self.markerHandler.cameraTranslationFromParent
            if (cameraTranslationFromParent, projectBracket.cameraDistance) != getattr(self, 'lastUpdateCameraValues', None):
                self.lastUpdateCameraValues = (cameraTranslationFromParent, projectBracket.cameraDistance)
                if self.markerHandler.IsActiveOfHilighted(self.markerID):
                    opacity = 1.0
                    self.MoveToFront()
                else:
                    if projectBracket.cameraDistance < self.minVisibleRange:
                        baseOpacity = projectBracket.cameraDistance / self.minVisibleRange
                    elif projectBracket.cameraDistance < self.maxVisibleRange:
                        baseOpacity = min(1.0, max(0.0, 1.0 - projectBracket.cameraDistance / self.maxVisibleRange))
                    else:
                        self.DestroyRenderObject()
                        return
                    nearFactor = min(1.0, cameraTranslationFromParent / projectBracket.cameraDistance)
                    opacity = round(baseOpacity * nearFactor, 2)
                if opacity > 0.05:
                    self.CreateRenderObject()
                    self.markerContainer.opacity = opacity
                    self.UpdateExtraContainer()
                elif self.markerContainer:
                    self.DestroyRenderObject()

    def OnMapMarkerContainerClicked(self, markerContainer, *args, **kwds):
        if self.selectionCallback:
            self.selectionCallback(self, *args, **kwds)

    def OnClick(self, *args, **kwds):
        if self.selectionCallback:
            self.selectionCallback(self, *args, **kwds)

    def CreateRenderObject(self):
        if self.parentContainer and (not self.markerContainer or self.markerContainer.destroyed):
            parent = self.parentContainer()
            if not parent:
                return
            container = MarkerContainerBase(parent=parent, markerObject=self)
            self.markerContainer = container
            self.projectBracket.bracket = container.renderObject
            self.Load()

    def Reload(self):
        self.DestroyRenderObject()
        self.lastUpdateCameraValues = None

    def DestroyRenderObject(self):
        self.projectBracket.bracket = None
        if self.markerContainer and not self.markerContainer.destroyed:
            markerContainer = self.markerContainer
            self.markerContainer = None
            markerContainer.Close()
        if self.extraContainer and not self.extraContainer.destroyed:
            self.extraContainer.Close()
            self.extraContainer = None
        self.isLoaded = False
        self.lastUpdateCameraValues = None

    def UpdatePosition(self):
        if self.position is None:
            return
        yScaleFactor = self.markerHandler.yScaleFactor
        if self.overridePosition:
            x, y, z = self.overridePosition
        else:
            x, y, z = self.position
        self.projectBracket.trackPosition = (x, y * yScaleFactor, z)
        self.scaledCenter = (x, y * yScaleFactor, z)

    def UpdateExtraContainer(self):
        if not self.extraContainer or not self.markerContainer:
            return
        self.extraContainer.renderObject.displayX = self.markerContainer.renderObject.displayX
        self.extraContainer.renderObject.displayY = self.markerContainer.renderObject.displayY + self.markerContainer.renderObject.displayHeight

    def Load(self):
        pass

    def GetMenu(self):
        try:
            objectID = int(self.markerID)
            return self.eventHandler.GetMenuForObjectID(objectID)
        except:
            pass

    def LoadMarkerTooltipPanel(self, *args, **kwds):
        pass

    def GetDragData(self, *args):
        return None
