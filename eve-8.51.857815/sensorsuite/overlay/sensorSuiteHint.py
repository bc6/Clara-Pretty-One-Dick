#Embedded file name: sensorsuite/overlay\sensorSuiteHint.py
from math import sqrt, pi
from carbon.common.lib.const import SEC, MSEC
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.fill import Fill
from carbonui.primitives.gradientSprite import GradientSprite
from carbonui.primitives.line import Line
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.transform import Transform
from carbonui.primitives.vectorlinetrace import VectorLineTrace
from carbonui.uianimations import animations
from carbonui.util.various_unsorted import IsUnder
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.eveIcon import LogoIcon, Icon, GetOwnerLogo
import carbonui.const as uiconst
import blue
from eve.client.script.ui.control.eveLabel import EveLabelMediumBold, EveCaptionMedium
from inventorycommon.const import typeCosmicAnomaly, typeFaction, typeCorporation
import uthread
import trinity
import localization
from sensorsuite.overlay.brackets import SensorSuiteBracket
import probescanning.formations as formations
from sensorsuite.error import InvalidClientStateError
from eve.client.script.ui.services.menuSvcExtras.movementFunctions import WarpToItem
HINT_FRAME_COLOR = (1.0, 1.0, 1.0, 0.25)
HINT_BACKGROUND_COLOR = (0, 0, 0, 0.85)
DOCK_POINTER_LENGTH = 16
DOCK_MARGIN = 4

def OpenProbeScanner(*_):
    from eve.client.script.ui.inflight.scanner import Scanner
    wnd = Scanner.GetIfOpen()
    if wnd is None:
        wnd = Scanner.Open()
    blue.pyos.synchro.Yield()
    wnd.SelectProbeScanner()
    sm.GetService('viewState').ActivateView('systemmap')
    wnd.LaunchFormation(formations.PINPOINT_FORMATION, 4)


def IsRectBWithinA(a, b):
    al, at, aw, ah = a
    bl, bt, bw, bh = b
    if at > bt:
        return False
    if al > bl:
        return False
    if at + ah < bt + bh:
        return False
    if al + aw < bl + bw:
        return False
    return True


class DockPlacement:
    """
    Dock placement enumeration for PointerContainer to lign up the arrow
    #    4  5  6
    #    _______
    # 1 |       | 7
    # 2 |       | 8
    # 3 |______ | 9
    #   10 11 12 
    """
    LeftCenter = 2
    TopCenter = 5
    RightCenter = 8
    BottomCenter = 11


class PointerContainer(Container):
    """
    This is a frame with a pointer on one edge
    """
    default_name = 'PointerContainer'
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOPLEFT
    default_width = 200
    default_height = 100
    default_dockPlacement = DockPlacement.LeftCenter
    default_dockPointerLength = 16
    default_dockMargin = 8
    default_hintBgColor = (0.1, 0.1, 0.1, 0.85)
    default_hintFrameColor = (1.0, 1.0, 1.0, 0.25)

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.dockPointerLength = attributes.get('dockPointerLength', self.default_dockPointerLength)
        self.dockMargin = attributes.get('dockMargin', self.default_dockMargin)
        self.hintBgColor = attributes.get('hintBgColor', self.default_hintBgColor)
        self.hintFrameColor = attributes.get('hintFrameColor', self.default_hintFrameColor)
        self.anchor = attributes.anchor
        self.dockPlacement = attributes.get('dockPlacement', self.default_dockPlacement)
        self.lineTrace = None
        self._BindToAnchor(self.anchor)
        self.SetDockPlacement(self.dockPlacement)

    def _BindToAnchor(self, anchor):
        """
        When eve our anchor changes we want to update the hint location
        """
        cs = uicore.uilib.bracketCurveSet
        self.bindings = []
        self.bindings.append(trinity.CreateBinding(cs, anchor.renderObject, 'displayX', None, ''))
        self.bindings.append(trinity.CreateBinding(cs, anchor.renderObject, 'displayY', None, ''))
        for binding in self.bindings:
            binding.copyValueCallable = self._UpdateBoundValues

    def _UpdateBoundValues(self, *args):
        self.UpdatePosition()

    def UpdatePosition(self):
        anchorRect = self.anchor.GetAbsolute()
        dockPlacement = self.GetBestDockPlacement()
        left, top = self.CalcPosition(dockPlacement, anchorRect)
        self.top = top
        self.left = left

    def CalcPosition(self, dockPlacement, anchorRect):
        left, top, width, height = anchorRect
        newLeft, newTop = (0, 0)
        if dockPlacement == DockPlacement.TopCenter:
            newTop = top + (height + self.dockPointerLength + self.dockMargin)
            newLeft = left + (width - self.width) / 2
        elif dockPlacement == DockPlacement.BottomCenter:
            newTop = top - (self.height + self.dockPointerLength + self.dockMargin)
            newLeft = left + (width - self.width) / 2
        elif dockPlacement == DockPlacement.LeftCenter:
            newTop = top + (height - self.height) / 2
            newLeft = left + (width + self.dockPointerLength + self.dockMargin)
        elif dockPlacement == DockPlacement.RightCenter:
            newTop = top + (height - self.height) / 2
            newLeft = left - (self.width + self.dockPointerLength + self.dockMargin)
        return (newLeft, newTop)

    def GetBestDockPlacement(self):
        return self.dockPlacement

    def SetDockPlacement(self, dockPlacement):
        """
        places the selector window on around the anchor as appropriate
        """
        self.dockPlacement = dockPlacement
        self.DoUpdateLayout(dockPlacement)
        self.UpdatePosition()

    def DoUpdateLayout(self, dockPlacement):
        pointerWidth = self.dockPointerLength * 2
        if dockPlacement == DockPlacement.TopCenter:
            pointList = ((0, 0),
             ((self.width - pointerWidth) * 0.5, 0),
             (self.width * 0.5, -self.dockPointerLength),
             ((self.width + pointerWidth) * 0.5, 0),
             (self.width, 0),
             (self.width, self.height),
             (0, self.height))
        elif dockPlacement == DockPlacement.BottomCenter:
            pointList = ((0, 0),
             (self.width, 0),
             (self.width, self.height),
             ((self.width + pointerWidth) * 0.5, self.height),
             (self.width * 0.5, self.height + pointerWidth),
             ((self.width - pointerWidth) * 0.5, self.height),
             (0, self.height))
        elif dockPlacement == DockPlacement.LeftCenter:
            pointList = ((0, 0),
             (self.width, 0),
             (self.width, self.height),
             (0, self.height),
             (0, (self.height + pointerWidth) * 0.5),
             (-self.dockPointerLength, self.height * 0.5),
             (0, (self.height - pointerWidth) * 0.5))
        elif dockPlacement == DockPlacement.RightCenter:
            pointList = ((0, 0),
             (self.width, 0),
             (self.width, (self.height - pointerWidth) * 0.5),
             (self.width + self.dockPointerLength, self.height * 0.5),
             (self.width, (self.height + pointerWidth) * 0.5),
             (self.width, self.height),
             (0, self.height))
        else:
            raise NotImplementedError('This case of dock placement has not been implemented yet')
        if self.lineTrace is not None:
            self.lineTrace.Close()
        self.lineTrace = VectorLineTrace(parent=self, lineWidth=1.0, spriteEffect=trinity.TR2_SFX_FILL)
        self.lineTrace.isLoop = True
        for point in pointList:
            x, y = point
            x, y = uicore.ScaleDpi(x), uicore.ScaleDpi(y)
            self.lineTrace.AddPoint((x, y), self.hintFrameColor)

        pointerSideWidth = int(self.dockPointerLength * 2 / sqrt(2))
        pointerSideWidthHalf = pointerSideWidth / 2
        if dockPlacement == DockPlacement.TopCenter:
            clipperAlign = uiconst.CENTERTOP
            transformAlign = uiconst.CENTERBOTTOM
            horizontal = False
        elif dockPlacement == DockPlacement.BottomCenter:
            clipperAlign = uiconst.CENTERBOTTOM
            transformAlign = uiconst.CENTERTOP
            horizontal = False
        elif dockPlacement == DockPlacement.LeftCenter:
            clipperAlign = uiconst.CENTERLEFT
            transformAlign = uiconst.CENTERRIGHT
            horizontal = True
        elif dockPlacement == DockPlacement.RightCenter:
            clipperAlign = uiconst.CENTERRIGHT
            transformAlign = uiconst.CENTERLEFT
            horizontal = True
        else:
            raise NotImplementedError('This case of dock placement has not been implemented yet')
        clipperCont = Container(name='clipper', parent=self, width=self.dockPointerLength if horizontal else pointerWidth, height=pointerWidth if horizontal else self.dockPointerLength, clipChildren=True, align=clipperAlign, top=0 if horizontal else -self.dockPointerLength, left=-self.dockPointerLength if horizontal else 0)
        transform = Transform(name='transform', parent=clipperCont, align=transformAlign, rotation=pi / 4, width=pointerSideWidth, height=pointerSideWidth, top=0 if horizontal else -pointerSideWidthHalf, left=-pointerSideWidthHalf if horizontal else 0)
        Fill(bgParent=transform, color=self.hintBgColor)

    def _OnClose(self):
        self._UnbindAnchor()
        Container._OnClose(self)

    def _UnbindAnchor(self):
        cs = uicore.uilib.bracketCurveSet
        if cs:
            for binding in self.bindings:
                if binding in cs.bindings:
                    cs.bindings.remove(binding)

    def FixPosition(self):
        self._UnbindAnchor()


class BaseSensorSuiteHint(PointerContainer):
    """
    This is the base implementation of a sensor suite hint
    """
    default_name = 'BaseSensorSuiteHint'
    default_height = 122
    default_width = 300
    default_minDisplayTime = SEC
    default_outsideBoundsTime = 400 * MSEC
    default_updateLoopTimeMSec = 200
    default_captionLabel = None
    default_iconTexturePath = None

    def GetCaptionText(self):
        raise NotImplementedError()

    def CreateIconSpite(self):
        self.ownerIcon = Sprite(parent=self.iconCont, pos=(0, 0, 32, 32), state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT)

    def ApplyAttributes(self, attributes):
        PointerContainer.ApplyAttributes(self, attributes)
        self.data = attributes.data
        self.callback = attributes.callback
        self.minDisplayTime = attributes.Get('minDisplayTime', self.default_minDisplayTime)
        self.outsideBoundsTime = attributes.Get('outsideBoundsTime', self.default_outsideBoundsTime)
        self.updateLoopTimeMSec = attributes.Get('updateLoopTimeMSec', self.default_updateLoopTimeMSec)
        self._updateThread = None
        self.michelle = sm.GetService('michelle')
        self.sensorSuite = sm.GetService('sensorSuite')
        self.topContainer = Container(parent=self, height=20, align=uiconst.TOTOP)
        self.bottomContainer = Container(parent=self, align=uiconst.TOALL)
        self.contentContainer = Container(parent=self.bottomContainer, align=uiconst.TOALL, padLeft=16)
        Fill(bgParent=self.bottomContainer, color=(0, 0, 0, 0.4))
        Line(parent=self.bottomContainer, align=uiconst.TOBOTTOM)
        leftPadContainer = Container(parent=self.topContainer, align=uiconst.TOLEFT, width=12)
        Line(parent=leftPadContainer, align=uiconst.TORIGHT)
        Line(parent=leftPadContainer, align=uiconst.TOBOTTOM)
        textContainer = Container(parent=self.topContainer, align=uiconst.TOLEFT, width=150)
        Fill(bgParent=textContainer, color=(0, 0, 0, 0.5))
        Line(parent=textContainer, align=uiconst.TOTOP)
        Line(parent=textContainer, align=uiconst.TORIGHT)
        self.captionLabel = EveLabelMediumBold(parent=textContainer, text=self.GetCaptionText(), align=uiconst.CENTER)
        textContainer.width = self.captionLabel.textwidth + 16
        rightPadContainer = Container(parent=self.topContainer, align=uiconst.TOALL)
        Line(parent=rightPadContainer, align=uiconst.TOBOTTOM)
        self.iconCont = Container(parent=self.contentContainer, pos=(8, 8, 32, 32), state=uiconst.UI_DISABLED, align=uiconst.TOPRIGHT)
        if self.default_iconTexturePath:
            self.CreateIconSpite()
            self.ownerIcon.SetTexturePath(self.default_iconTexturePath)
            self.ownerIcon.state = uiconst.UI_DISABLED
        topTextCont = ContainerAutoSize(top=8, name='topTextCont', parent=self.contentContainer, align=uiconst.TOTOP)
        self.mainLabel = EveCaptionMedium(name='mainLabel', parent=topTextCont, color=(0.235, 0.745, 0.765), text='', align=uiconst.TOTOP, singleline=True)
        self.mainLabel.SetRightAlphaFade(fadeEnd=250, maxFadeWidth=30)
        self.subLabel = EveLabelMediumBold(name='subLabel', parent=topTextCont, align=uiconst.TOTOP, text='', singleline=True)
        self.subLabel.SetRightAlphaFade(fadeEnd=250, maxFadeWidth=30)
        bottomTextCont = ContainerAutoSize(top=2, name='bottomTextCont', parent=self.contentContainer, align=uiconst.TOBOTTOM)
        self.dataLabel = EveLabelMediumBold(name='dataLabel', parent=bottomTextCont, align=uiconst.TOBOTTOM, text='')
        self.rangeLabel = EveLabelMediumBold(name='rangeLabel', parent=bottomTextCont, align=uiconst.TOBOTTOM, text='')
        self.buttonContainer = Container(parent=self.contentContainer, align=uiconst.BOTTOMRIGHT, heigh=32)
        GradientSprite(parent=self.bottomContainer, align=uiconst.TOALL, rotation=-pi / 2, rgbData=[(0, (0.25, 0.25, 0.25)), (0.3, (0.0, 0.0, 0.0))], alphaData=[(0, 0.5)], state=uiconst.UI_DISABLED)
        self.warpButton = Button(parent=self.contentContainer, top=8, left=88, icon='res:/UI/Texture/Icons/44_32_18.png', func=self.WarpToAction, hint=localization.GetByLabel('UI/Commands/WarpTo'), align=uiconst.BOTTOMRIGHT)
        self.bookmarkButton = Button(parent=self.contentContainer, top=8, left=48, icon='res:/UI/Texture/Icons/bookmark.png', func=self.BookmarkSite, hint=localization.GetByLabel('UI/Inflight/BookmarkLocation'), align=uiconst.BOTTOMRIGHT)
        self.probeScannerButton = Button(parent=self.contentContainer, top=8, left=4, icon='res:/UI/Texture/Icons/probe_scan.png', func=OpenProbeScanner, hint=localization.GetByLabel('UI/Inflight/Scanner/SensorOverlayProbeScanButtonHint'), align=uiconst.BOTTOMRIGHT)
        uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEDOWN, self.OnGlobalMouseDown)
        self._updateThread = uthread.new(self.UpdateHint)

    def SetFactionIcon(self, factionID):
        iconID = LogoIcon.GetFactionIconID(factionID, isSmall=True)
        if iconID is not None:
            resPath = Icon.ConvertIconNoToResPath(iconID)
            if resPath is not None:
                self.CreateIconSpite()
                self.ownerIcon.SetTexturePath(resPath[0])
                self.iconCont.state = uiconst.UI_NORMAL
                self.iconCont.OnClick = lambda : sm.GetService('info').ShowInfo(itemID=factionID, typeID=typeFaction)

    def SetOwnerIcon(self, ownerID):
        GetOwnerLogo(self.iconCont, ownerID, size=32)
        self.iconCont.state = uiconst.UI_NORMAL
        self.iconCont.OnClick = lambda : sm.GetService('info').ShowInfo(itemID=ownerID, typeID=typeCorporation)

    def GetBestDockPlacement(self):
        dockPlacementOrder = (DockPlacement.LeftCenter,
         DockPlacement.RightCenter,
         DockPlacement.TopCenter,
         DockPlacement.BottomCenter)
        screenRect = uicore.layer.sensorsuite.GetAbsolute()
        anchorRect = self.anchor.GetAbsolute()
        bestDockPlacement = self.dockPlacement
        for dockPlacement in dockPlacementOrder:
            left, top = self.CalcPosition(dockPlacement, anchorRect)
            hintRect = (left,
             top,
             self.width,
             self.height)
            if IsRectBWithinA(screenRect, hintRect):
                bestDockPlacement = dockPlacement
                break

        return bestDockPlacement

    def UpdateWidth(self):
        buttonOffset = 144
        listWidths = (self.default_width,
         self.mainLabel.textwidth + 16 + 32 + 8 + 4,
         self.rangeLabel.textwidth + buttonOffset,
         self.dataLabel.textwidth + buttonOffset)
        self.width = max(listWidths)

    def WarpToAction(self, *args):
        WarpToItem(self.data.siteID)

    def BookmarkSite(self, *args):
        sm.GetService('addressbook').BookmarkLocationPopup(self.data.siteID, typeCosmicAnomaly, session.solarsystemid, locationName=localization.GetByMessageID(self.data.dungeonNameID))

    def UpdateHint(self):
        """
        This is the hint automatic fade out logic
        """
        startTime = blue.os.GetSimTime() + self.minDisplayTime
        outsideBoundsEndTime = None
        doUpdates = True
        try:
            while doUpdates:
                timeNow = blue.os.GetSimTime()
                if not self or self.destroyed:
                    return
                if timeNow > startTime:
                    if not (uicore.uilib.mouseOver in (self, self.anchor) or IsUnder(uicore.uilib.mouseOver, self) or IsUnder(uicore.uilib.mouseOver, self.anchor)):
                        if outsideBoundsEndTime is None:
                            outsideBoundsEndTime = timeNow + self.outsideBoundsTime
                        elif timeNow > outsideBoundsEndTime:
                            doUpdates = False
                    else:
                        outsideBoundsEndTime = None
                if self.sensorSuite.activeBracketHint is not self:
                    doUpdates = False
                if doUpdates:
                    try:
                        self.OnUpdateHint()
                        self.UpdateWarpButton()
                        blue.pyos.synchro.SleepWallclock(self.updateLoopTimeMSec)
                    except InvalidClientStateError:
                        doUpdates = False

        finally:
            if self and not self.destroyed:
                animations.FadeOut(self, sleep=True)
                uthread.new(self.Close)

    def OnUpdateHint(self):
        """
        This is for auto-magical update of data in the hint
        """
        pass

    def UpdateWarpButton(self):
        if self.data.IsAccurate() and self.michelle.IsPositionWithinWarpDistance(self.data.position):
            self.warpButton.Enable()
        else:
            self.warpButton.Disable()

    def _OnClose(self, *args):
        PointerContainer._OnClose(self, *args)
        if self._updateThread is not None:
            self._updateThread.kill()
        self.callback()

    def DoUpdateLayout(self, dockPlacement):
        pass

    def IsMouseOverHint(self):
        isMouseOverHint = False
        if uicore.uilib.mouseOver is self or IsUnder(uicore.uilib.mouseOver, self):
            isMouseOverHint = True
        elif self.sensorSuite.HasActiveOverlapContainerInstance():
            overlapContainer = self.sensorSuite.GetOverlapContainerInstance()
            if uicore.uilib.mouseOver is overlapContainer or IsUnder(uicore.uilib.mouseOver, overlapContainer):
                isMouseOverHint = True
        return isMouseOverHint

    def OnGlobalMouseDown(self, cont, *_):
        if self.IsMouseOverHint() or isinstance(cont, SensorSuiteBracket):
            return True
        else:
            self.Close()
            return False
