#Embedded file name: eve/client/script/ui/inflight\scanner.py
from carbon.common.script.util.format import FmtDist, FmtDate
from carbon.common.script.util.mathUtil import Lerp
from carbon.common.script.util.timerstuff import AutoTimer
import carbonui.const as uiconst
from carbonui.control.menuLabel import MenuLabel
from carbonui.primitives.bracket import Bracket
from carbonui.primitives.fill import Fill
from carbonui.primitives.line import Line
from carbonui.uianimations import animations
from carbonui.util.various_unsorted import MapIcon, IsVisible, GetAttrs
from eve.client.script.ui.control.checkbox import Checkbox
from eve.client.script.ui.control.eveCombo import Combo
from eve.client.script.ui.control.eveIcon import MenuIcon, Icon
from eve.client.script.ui.control.eveLabel import EveLabelSmall, EveLabelMedium, EveLabelMediumBold
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from eve.client.script.ui.inflight.bracket import SimpleBracket
from eve.client.script.ui.inflight.probeControl import BaseProbeControl, ProbeControl
from eve.client.script.ui.inflight.scannerfiltereditor import ScannerFilterEditor
from eve.client.script.ui.inflight.warpableResultBracket import WarpableResultBracket
from eve.client.script.ui.shared.maps.mapcommon import SYSTEMMAP_SCALE
from eve.client.script.ui.shared.maps.maputils import GetVisibleSolarsystemBrackets, GetHintsOnSolarsystemBrackets
from eve.client.script.ui.util.uix import GetBigButton
from eve.common.lib.appConst import defaultPadding, AU, minWarpDistance
from eve.common.script.util.eveFormat import FmtProbeState
from eveexceptions import UserError
from inventorycommon.const import groupScannerProbe, groupCosmicAnomaly, groupCosmicSignature, groupFrigate, groupSurveyProbe
from inventorycommon.const import groupScanProbeLauncher, categoryShip
from inventorycommon.util import IsShipFittingFlag
from probescanning.const import probeStateIdle, probeStateInactive, probeScanGroupAnomalies, probeResultPerfect, probeResultInformative, probeResultGood
from sensorsuite.overlay.controllers.probescanner import SiteDataFromScanResult
import uthread
import blue
import trinity
import service
import probescanning.customFormations
from carbonui.primitives.container import Container
from eve.client.script.ui.control.utilMenu import UtilMenu
from eve.client.script.ui.control import entries as listentry
from carbonui.primitives.gradientSprite import GradientConst, GradientSprite
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.control.divider import Divider
from eve.client.script.ui.control.buttons import BigButton, ButtonIcon, Button
import math
import geo2
import itertools
from math import pi, cos, sin, sqrt
import functools
import localization
import probescanning.formations as formations
from probescanning.util import IsIntersecting
from utillib import KeyVal
CIRCLE_SCALE = 0.01
CIRCLE_COLOR = (1.0, 0.0, 0.0, 1.0)
POINT_ICON_PROPS = ('ui_38_16_254', 0, 0.0, 1e+32, 0, 1)
POINT_ICON_DUNGEON = ('ui_38_16_14', 0.0, 0, 0.0, 1e+32, 0, 1)
POINT_COLOR_RED = (1.0, 0.0, 0.0, 1.0)
POINT_COLOR_YELLOW = (1.0, 1.0, 0.0, 1.0)
POINT_COLOR_GREEN = (0.0, 1.0, 0.0, 1.0)
SET_PROBE_DESTINATION_TIMEOUT = 3000
AXIS_Y = geo2.Vector(0.0, 1.0, 0.0)
LINESET_EFFECT = 'res:/Graphics/Effect/Managed/Space/SpecialFX/LinesAdditive.fx'
INTERSECTION_COLOR = (0.3, 0.5, 0.7, 1.0)
RANGE_INDICATOR_CIRCLE_COLOR = (INTERSECTION_COLOR[0] * 0.5,
 INTERSECTION_COLOR[1] * 0.5,
 INTERSECTION_COLOR[2] * 0.5,
 1.0)
RANGE_INDICATOR_CROSS_COLOR = (INTERSECTION_COLOR[0] * 0.25,
 INTERSECTION_COLOR[1] * 0.25,
 INTERSECTION_COLOR[2] * 0.25,
 1.0)
INTERSECTION_ACTIVE = 1.0
INTERSECTION_FADED = 0.4
INTERSECTION_INACTIVE = 0.15
CIRCLE_NUM_POINTS = 256
CIRCLE_ANGLE_SIZE = 2.0 * pi / CIRCLE_NUM_POINTS
CIRCLE_POINTS = []
for i in xrange(CIRCLE_NUM_POINTS):
    x, y = cos(CIRCLE_ANGLE_SIZE * i), sin(CIRCLE_ANGLE_SIZE * i)
    CIRCLE_POINTS.append((x, 0.0, y))

MIN_WARP_DISTANCE_SQUARED = minWarpDistance ** 2
CENTROID_LINE_COLOR = (0.1, 1.0, 0.1, 0.75)
CENTROID_LINE_WIDTH = 1.5
DISTRING_LINE_WIDTH = 1.0
DISTANCE_RING_RANGES = [1,
 2,
 4,
 8,
 16,
 32,
 64,
 128]
MAX_DIST_RING_RANGE = DISTANCE_RING_RANGES[-1]
SQRT_05 = sqrt(0.5)
FORMATION_CONTROL_ID = 'formationControl'

def AddFilter(*args):
    editor = ScannerFilterEditor.Open()
    editor.LoadData(None)


def UserErrorIfScanning(action, *args, **kwargs):
    """
    decorator checking if we are curerntly scanning and raising a UserError if so
    """

    @functools.wraps(action)
    def wrapper(*args, **kwargs):
        if sm.GetService('scanSvc').IsScanning():
            raise UserError('ScanInProgressGeneric')
        return action(*args, **kwargs)

    return wrapper


def IsResultWithinWarpDistance(result):
    """
    check whether the result is with in warp distance of the current players ship
    """
    ballpark = sm.GetService('michelle').GetBallpark()
    egoBall = ballpark.GetBall(ballpark.ego)
    egoPos = geo2.Vector(egoBall.x, egoBall.y, egoBall.z)
    resultPos = geo2.Vector(*result.data)
    distanceSquared = geo2.Vec3LengthSq(egoPos - resultPos)
    return distanceSquared > MIN_WARP_DISTANCE_SQUARED


class FormationButton(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.align = uiconst.TOPLEFT
        self.height = 32
        self.width = 55
        self.btn = BigButton(parent=self, left=0, top=0, width=48, height=32, hint='', align=0, iconAlign=uiconst.TOALL)
        self.btn.Startup(48, 32, 0)
        self.btn.Click = self.LaunchClick
        self.btn.sr.icon.padding = (0,
         -1,
         self.btn.width - self.btn.height,
         1)
        self.btn.sr.icon.LoadIcon('ui_112_64_5')
        self.utilMenu = UtilMenu(menuAlign=uiconst.TOPLEFT, parent=self.btn, align=uiconst.TOLEFT, GetUtilMenu=self.FormationMenu, texturePath='res:/UI/Texture/Icons/73_16_50.png', left=28)
        self.btn.hint = self.selectedFormationName
        self.UpdateButton()

    @property
    def selectedFormationID(self):
        return probescanning.customFormations.GetSelectedFormationID()

    @property
    def selectedFormationName(self):
        return probescanning.customFormations.GetSelectedFormationName()

    def Disable(self):
        self.disabled = True
        self.btn.sr.icon.opacity = 0.25

    def Enable(self):
        self.disabled = False
        self.btn.sr.icon.opacity = 1.0

    def LaunchClick(self, *args):
        if not self.disabled and self.selectedFormationID is not None:
            sm.GetService('scanSvc').MoveProbesToFormation(self.selectedFormationID)

    def Highlight(self, selection, highlight):
        selection.display = highlight

    def DeleteFormation(self, formation):
        probescanning.customFormations.DeleteFormation(formation[0])
        self.utilMenu._menu().ReloadMenu()
        self.UpdateButton()

    def GetFormationEntry(self, formation, parent, menuParent):
        formationName = '%s (%i)' % (formation[1], formation[2])
        formationLabel = EveLabelSmall(text=formationName, parent=parent, name='formation', width=120, padding=(5, 5, 0, 0), state=uiconst.UI_DISABLED, maxLines=1)
        parent.hint = formationName
        deleteButton = ButtonIcon(parent=parent, texturePath='res:/UI/Texture/Icons/38_16_111.png', padding=(0, 5, 0, 0), pos=(3, 3, 16, 16), align=uiconst.TOPRIGHT)
        deleteButton.OnClick = (self.DeleteFormation, formation)
        selectionFill = Fill(bgParent=parent, color=(0.15, 0.15, 0.15))
        selectionFill.display = False
        parent.OnMouseEnter = (self.Highlight, selectionFill, True)
        parent.OnMouseExit = (self.Highlight, selectionFill, False)
        parent.OnClick = (self.SelectFormation, formation)
        return formationLabel

    def GetFormationInput(self, parent):
        entry = SinglelineEdit(parent=parent, width=100, padding=(5, 0, 0, 0))
        entry.OnReturn = self.SaveFormation
        label = localization.GetByLabel('UI/Inflight/Scanner/Save')
        hint = localization.GetByLabel('UI/Inflight/Scanner/SaveCurrentFormation')
        saveButton = Button(parent=parent, label=label, hint=hint, align=uiconst.TORIGHT)
        if not sm.GetService('scanSvc').GetActiveProbes():
            saveButton.Disable()
        saveButton.OnClick = self.SaveFormation
        return entry

    def FormationMenu(self, menuParent):
        formations = probescanning.customFormations.GetCustomFormationsInfo()
        for formation in formations:
            cont = menuParent.AddContainer(align=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN)
            innerCont = Container(parent=cont, align=uiconst.TOTOP, height=25, state=uiconst.UI_NORMAL, clipChildren=True)
            cont.GetEntryWidth = lambda mc = cont: 150
            self.GetFormationEntry(formation, innerCont, menuParent)

        if len(formations) < 10:
            menuParent.AddDivider()
            cont = menuParent.AddContainer(align=uiconst.TOTOP)
            cont.GetEntryWidth = lambda mc = cont: 150
            innerCont = Container(parent=cont, align=uiconst.TOTOP, height=25, state=uiconst.UI_NORMAL)
            self.formationNameInput = self.GetFormationInput(innerCont)

    def SaveFormation(self):
        if len(self.formationNameInput.text) >= 1:
            sm.GetService('scanSvc').PersistCurrentFormation(self.formationNameInput.text)
            self.utilMenu._menu().ReloadMenu()
            self.UpdateFormationButton()
        else:
            return

    def UpdateFormationButton(self):
        if sm.GetService('scanSvc').CanLaunchFormation(self.selectedFormationID):
            self.btn.disabled = True
        else:
            self.btn.disabled = False
        self.utilMenu.CloseMenu()
        self.btn.hint = self.selectedFormationName
        self.UpdateButton()

    def SelectFormation(self, formation):
        probescanning.customFormations.SelectFormation(formation[0])
        self.UpdateFormationButton()

    def UpdateButton(self):
        if self.selectedFormationID is not None and sm.GetService('scanSvc').CanLaunchFormation(self.selectedFormationID):
            self.Enable()
        else:
            self.Disable()


class Scanner(Window):
    __notifyevents__ = ['OnSessionChanged',
     'OnProbeAdded',
     'OnProbeRemoved',
     'OnSystemScanBegun',
     'OnSystemScanDone',
     'OnNewScannerFilterSet',
     'OnProbeStateUpdated',
     'OnProbeRangeUpdated',
     'OnScannerDisconnected',
     'OnRefreshScanResults',
     'OnReconnectToProbesAvailable',
     'OnModuleOnlineChange',
     'OnProbePositionsUpdated',
     'OnBallparkSetState',
     'OnDogmaItemChange']
    default_windowID = 'scanner'
    default_width = 510
    default_height = 450
    default_minSize = (335, 340)
    default_captionLabelPath = 'UI/Inflight/Scanner/ProbeScanner'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.scanSvc = sm.GetService('scanSvc')
        self.__disallowanalysisgroups = [groupSurveyProbe]
        self.lastScaleUpdate = None
        self.lastMoveUpdate = None
        self.sr.probeSpheresByID = {}
        self.centerProbeControl = None
        self.sr.rangeIndicators = {}
        self.sr.resultObjectsByID = {}
        self.sr.probeIntersectionsByPair = {}
        self.sr.distanceRings = None
        self.rememberToTurnOffTracking = False
        self.lastProbeScaleInfo = None
        self.centroidLines = None
        self.lastProbeIDs = None
        self.sr.systemParent = None
        activeFilter = settings.user.ui.Get('activeProbeScannerFilter', None)
        currentFilters = settings.user.ui.Get('probeScannerFilters', {})
        self.currentFilter = currentFilters.get(activeFilter, [])
        self.activeScanGroupInFilter = set()
        self.sr.keyUpCookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_KEYUP, self.OnGlobalKey)
        self.sr.keyDownCookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_KEYDOWN, self.OnGlobalKey)
        self.scope = 'inflight'
        self.SetTopparentHeight(0)
        self.SetWndIcon(None)
        self.HideMainIcon()
        systemsParent = Container(name='system', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0), clipChildren=1)
        self.sr.systemsParent = systemsParent
        probesClipper = Container(parent=systemsParent, align=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, height=100)
        probesClipper.padLeft = defaultPadding
        probesClipper.padRight = defaultPadding
        self.sr.probesClipper = probesClipper
        self.sr.scroll = Scroll(name='scroll', parent=probesClipper, align=uiconst.TOALL)
        divPar = Container(name='divider', align=uiconst.TOBOTTOM, height=defaultPadding, parent=probesClipper, idx=0)
        divider = Divider(name='divider', align=uiconst.TOALL, pos=(0, 0, 0, 0), parent=divPar, state=uiconst.UI_NORMAL, idx=0)
        divider.Startup(probesClipper, 'height', 'y', 57, 800)
        divider.OnSizeChanged = self._OnProbesSizeChanged
        divider.OnSizeChangeStarting = self._OnProbesSizeChangeStarting
        divider.OnSizeChanging = self._OnProbesSizeChanging
        Line(parent=divider, align=uiconst.CENTER, width=6, height=1)
        self.sr.divider = divider
        topParent = Container(name='systemSettings', parent=systemsParent, align=uiconst.TOTOP, height=40)
        topParent.padTop = 6
        topParent.padLeft = 6
        topParent.padRight = 6
        self.sr.systemTopParent = topParent
        btn = GetBigButton(32, topParent)
        btn.Click = self.Analyze
        btn.hint = localization.GetByLabel('UI/Inflight/Scanner/Analyze')
        btn.sr.icon.LoadIcon('77_57')
        self.sr.analyzeBtn = btn
        btn = GetBigButton(32, topParent, left=44)
        btn.Click = self.RecoverActiveProbes
        btn.hint = localization.GetByLabel('UI/Inflight/Scanner/RecoverActiveProbes')
        btn.sr.icon.LoadIcon('77_58')
        self.sr.recoverBtn = btn
        btn = GetBigButton(32, topParent, left=80)
        btn.Click = self.ReconnectToLostProbes
        btn.hint = localization.GetByLabel('UI/Inflight/Scanner/ReconnectActiveProbes')
        btn.sr.icon.LoadIcon('77_59')
        self.sr.reconnectBtn = btn
        btn = GetBigButton(32, topParent, left=116)
        btn.Click = self.DestroyActiveProbes
        btn.hint = localization.GetByLabel('UI/Inflight/Scanner/DestroyActiveProbes')
        btn.sr.icon.LoadIcon('77_60')
        self.sr.destroyBtn = btn
        self.formationButtonsByID = {}
        btn = GetBigButton(32, topParent, left=152)
        btn.OnClick = lambda *args: self.LaunchFormation(formations.SPREAD_FORMATION, 32)
        btn.hint = localization.GetByLabel('UI/Inflight/Scanner/LaunchSpreadFormation')
        btn.sr.icon.LoadIcon('ui_112_64_3')
        self.formationButtonsByID[formations.SPREAD_FORMATION] = btn
        btn = GetBigButton(32, topParent, left=188)
        btn.OnClick = lambda *args: self.LaunchFormation(formations.PINPOINT_FORMATION, 4)
        btn.hint = localization.GetByLabel('UI/Inflight/Scanner/LaunchPinpointFormation')
        btn.sr.icon.LoadIcon('ui_112_64_4')
        self.formationButtonsByID[formations.PINPOINT_FORMATION] = btn
        self.customFormationButton = FormationButton(parent=topParent, left=224)
        btn = GetBigButton(32, topParent)
        btn.SetAlign(align=uiconst.TOPRIGHT)
        btn.OnClick = self.OpenMap
        btn.hint = localization.GetByLabel('UI/Common/Map')
        btn.sr.icon.SetTexturePath('res:/ui/Texture/WindowIcons/map.png')
        self.filterLine = Container(parent=systemsParent, align=uiconst.TOBOTTOM, name='filterLine', height=18)
        resultClipper = Container(parent=systemsParent, align=uiconst.TOALL, pos=(0, 0, 0, 0), state=uiconst.UI_PICKCHILDREN)
        resultClipper.padLeft = defaultPadding
        resultClipper.padRight = defaultPadding
        resultClipper.padBottom = 6
        resultClipper.padTop = 6
        self.sr.resultClipper = resultClipper
        filterContainer = Container(parent=resultClipper, align=uiconst.TOTOP, height=18)
        filterContainer.padTop = 2
        filterContainer.padBottom = 4
        filterCombo = Combo(label='', parent=filterContainer, options=[], name='probeScanningFilter', select=None, callback=self.OnFilterComboChange, align=uiconst.TOLEFT, width=180)
        self.showAnomalies = settings.user.ui.Get('scannerShowAnomalies', True)
        Checkbox(parent=filterContainer, text=localization.GetByLabel('UI/Inflight/Scanner/ShowAnomalies'), checked=self.showAnomalies, callback=self.OnShowAnomaliesCheckbox, align=uiconst.TOLEFT, width=170, padding=(10, 0, 0, 0))
        if self.showAnomalies:
            self.scanSvc.ShowAnomalies()
        else:
            self.scanSvc.StopShowingAnomalies()
        filterCombo.left = 23
        self.sr.filterCombo = filterCombo
        presetMenu = MenuIcon()
        presetMenu.GetMenu = self.GetFilterMenu
        presetMenu.left = 2
        presetMenu.top = 0
        presetMenu.hint = ''
        filterContainer.children.append(presetMenu)
        self.sortContainer = Container(parent=resultClipper, name='sortcontainer', align=uiconst.TOTOP, height=18)
        columnWidthDefaults = map(lambda x: x * uicore.fontSizeFactor, (50, 50, 65, 45, 43, 55))
        self.columnWidths = settings.user.ui.Get('columnWidths', columnWidthDefaults)
        self.GetSortControl(self.sortContainer)
        self.sortContainer.padTop = 2
        self.sortContainer.padBottom = 4
        self.sr.resultscroll = Scroll(name='resultscroll', parent=resultClipper)
        self.sr.resultscroll.OnSelectionChange = self.OnSelectionChange
        scanAnimatorParent = Container(parent=resultClipper, name='scanAnimatorParent', align=uiconst.TOALL)
        self.scanAnimator = Container(parent=scanAnimatorParent, name='scanAnimator', align=uiconst.TOLEFT_PROP, right=0)
        GradientSprite(parent=self.scanAnimator, align=uiconst.TORIGHT, pos=(0, 0, 256, 256), rgbData=[(0, (0.3, 0.5, 0.9)), (1, (0.3, 0.8, 0.7))], alphaData=[(0, 0),
         (0.95, 0.3),
         (0.99, 0.5),
         (1, 0)], alphaInterp=GradientConst.INTERP_LINEAR, colorInterp=GradientConst.INTERP_LINEAR)
        systemMapSvc = sm.GetService('systemmap')
        systemMapSvc.LoadProbesAndScanResult()
        systemMapSvc.LoadSolarsystemBrackets(True)
        self.LoadProbeList()
        if self.destroyed:
            return
        self.UpdateProbeSpheres()
        self.LoadFilterOptions()
        show = localization.GetByLabel('UI/Inflight/Scanner/Show')
        showIgnored = EveLabelMedium(parent=self.filterLine, text=show, color=(0.8, 0.8, 0.0), align=uiconst.TORIGHT, state=uiconst.UI_NORMAL, padding=(0, 0, 10, 0))
        showIgnored.OnClick = self.ClearIgnoredResults
        showIgnored.OnMouseEnter = (self.HighlightLabelOn, showIgnored, (1, 1, 0))
        showIgnored.OnMouseExit = (self.HighlightLabelOff, showIgnored, (1, 1, 0))
        ignored = localization.GetByLabel('UI/Inflight/Scanner/Ignored', noIgnored=0)
        self.ignoredLabel = EveLabelMediumBold(parent=self.filterLine, text=ignored, align=uiconst.TORIGHT, color=(0.8, 0.8, 0.8), state=uiconst.UI_NORMAL, padding=(0, 0, 10, 0))
        EveLabelMediumBold(parent=self.filterLine, text='/', align=uiconst.TORIGHT, color=(0.8, 0.8, 0.8), state=uiconst.UI_DISABLED, padding=(10, 0, 10, 0))
        showFiltered = EveLabelMedium(parent=self.filterLine, text=show, color=(0.8, 0.8, 0.0), align=uiconst.TORIGHT, state=uiconst.UI_NORMAL, padding=(0, 0, 0, 0))
        showFiltered.OnClick = self.ClearFilteredResults
        showFiltered.OnMouseEnter = (self.HighlightLabelOn, showFiltered, (1, 1, 0))
        showFiltered.OnMouseExit = (self.HighlightLabelOff, showFiltered, (1, 1, 0))
        filtered = localization.GetByLabel('UI/Inflight/Scanner/Filtered', noFiltered=0)
        self.filteredLabel = EveLabelMediumBold(parent=self.filterLine, text=filtered, align=uiconst.TORIGHT, color=(0.8, 0.8, 0.8), state=uiconst.UI_NORMAL, padding=(0, 0, 10, 0))
        self.filterLine.height = max(18, self.ignoredLabel.textheight, self.filteredLabel.textheight)
        uthread.new(self.ApplyProbesPortion)
        ballpark = sm.GetService('michelle').GetBallpark()
        if ballpark is not None:
            uthread.new(self.InitialResultLoad)
        self.Refresh()
        self.ApplyProbesPortion()

    def OnShowAnomaliesCheckbox(self, checkbox):
        self.showAnomalies = checkbox.GetValue()
        if self.showAnomalies:
            self.scanSvc.ShowAnomalies()
        else:
            self.scanSvc.StopShowingAnomalies()
        settings.user.ui.Set('scannerShowAnomalies', self.showAnomalies)
        self.LoadResultList()

    def InitialResultLoad(self):
        blue.pyos.synchro.Yield()
        self.LoadResultList()

    def UpdateAnalyzeButtonState(self):
        if self.scanSvc.HasAvailableProbes():
            self.sr.analyzeBtn.Enable()
        else:
            self.sr.analyzeBtn.Disable()

    def HighlightLabelOn(self, label, color = (1, 1, 1)):
        label.color = (color[0],
         color[1],
         color[2],
         1.0)

    def HighlightLabelOff(self, label, color = (1, 1, 1)):
        label.color = (color[0],
         color[1],
         color[2],
         0.8)

    def ShowSortingTriangle(self, triangle, ascending):
        triangle.state = uiconst.UI_NORMAL
        if ascending:
            MapIcon(triangle, 'ui_1_16_16')
        else:
            MapIcon(triangle, 'ui_1_16_15')

    def SortBy(self, header):
        if len(self.sr.resultscroll.GetNodes()) == 0:
            return
        if self.sortingByKey == header.key:
            header.ascending = not header.ascending
        else:
            header.parent.clipChildren = True
            if self.sortingBy:
                self.sortingBy.parent.clipChildren = False
            self.sortingBy = header
            self.sortingTriangles[self.sortingByKey].state = uiconst.UI_HIDDEN
            self.sortingByKey = header.key
        self.sortingByAscending = header.ascending
        self.ShowSortingTriangle(header.triangle, self.sortingByAscending)
        settings.user.ui.Set('scannerSortingKey', self.sortingByKey)
        settings.user.ui.Set('scannerSortingAsc', self.sortingByAscending)
        self.LoadResultList()

    def ClearIgnoredResults(self):
        self.scanSvc.ClearIgnoredResults()

    def ClearFilteredResults(self):
        self.sr.filterCombo.SelectItemByValue(0)
        self.scanSvc.SetActiveFilter(0)
        self.LoadResultList()

    def StartScaleColumn(self, sender, *args):
        if uicore.uilib.rightbtn:
            return
        l, t, w, h = sender.parent.GetAbsolute()
        sl, st, sw, sh = sender.GetAbsolute()
        self._startScalePosition = uicore.uilib.x
        self._startScalePositionDiff = sl - uicore.uilib.x
        if sender.width <= 1:
            self._scaleColumnInitialWidth = sender.width * w
        else:
            self._scaleColumnInitialWidth = sender.width
        self.scalingColumn = True
        uthread.new(self.ScalingColumn, sender)

    def AdjustColumnWidth(self, column, parentWidth, diff):
        if diff == 0:
            return 0
        else:
            width = self._scaleColumnInitialWidth + diff
            if width > 10:
                column.width = width
                return diff
            return 0

    def ScalingColumn(self, sender, *args):
        l, t, w, h = sender.parent.GetAbsolute()
        while self.scalingColumn:
            blue.pyos.synchro.Sleep(10)
            if getattr(self, '_startScalePosition', None):
                diff = uicore.uilib.x - self._startScalePosition
                self.AdjustColumnWidth(sender, w, diff)

    def EndScaleColumn(self, sender, *args):
        self.scalingColumn = False
        self.sr.scaleEntries = None
        self._startScalePosition = 0
        colWidths = self.GetColumnWidths()
        settings.user.ui.Set('columnWidths', colWidths)
        self.LoadResultList()

    def SortHeader(self, parent, label, key, ascending, align = uiconst.TOLEFT, triangleVisible = uiconst.UI_HIDDEN, resize = True):
        if resize:
            resizer = Container(parent=parent, name='resizer', width=5, state=uiconst.UI_NORMAL, align=uiconst.TORIGHT)
            Line(parent=resizer, align=uiconst.TORIGHT, idx=0, color=(1.0, 1.0, 1.0, 0.45))
            resizer.cursor = 18
            resizer.OnMouseDown = (self.StartScaleColumn, parent)
            resizer.OnMouseUp = (self.EndScaleColumn, parent)
        if resize:
            arrowBox = Container(parent=parent, name='arrow', state=uiconst.UI_NORMAL, width=7, align=uiconst.TORIGHT)
            headerContainer = Container(parent=parent, name='header' + label, state=uiconst.UI_NORMAL, align=uiconst.TOALL, clipChildren=False)
            header = EveLabelMedium(parent=headerContainer, text=label, align=align, color=(0.8, 0.8, 0.8), state=uiconst.UI_NORMAL, padding=(5, 0, 0, 0))
        else:
            header = EveLabelMedium(parent=parent, text=label, align=align, color=(0.8, 0.8, 0.8), state=uiconst.UI_NORMAL, padding=(5, 0, 0, 0))
            arrowBox = Container(parent=parent, name='arrow', state=uiconst.UI_NORMAL, width=7, align=uiconst.TOLEFT)
        if ascending:
            header.triangle = Icon(parent=arrowBox, state=triangleVisible, align=uiconst.TORIGHT, left=-7, name='directionIcon', icon='ui_1_16_16')
        else:
            header.triangle = Icon(parent=arrowBox, state=triangleVisible, align=uiconst.TORIGHT, left=-7, name='directionIcon', icon='ui_1_16_15')
        header.OnClick = (self.SortBy, header)
        header.triangle.OnClick = (self.SortBy, header)
        arrowBox.OnClick = (self.SortBy, header)
        header.key = key
        header.ascending = ascending
        header.OnMouseEnter = (self.HighlightLabelOn, header)
        header.OnMouseExit = (self.HighlightLabelOff, header)
        self.sortingTriangles[header.key] = header.triangle
        return header

    def GetColumnWidths(self):
        return (self.headerDistance.width,
         self.headerID.width,
         self.headerScanGroup.width,
         self.headerGroupName.width,
         self.headerTypeName.width,
         self.headerSignal.width)

    def GetSortControl(self, sortContainerParent):
        self.headerSignal = Container(parent=sortContainerParent, name='signalbox', width=55, padding=(0, 0, 0, 0), align=uiconst.TORIGHT, clipChildren=True)
        sortContainer = Container(parent=sortContainerParent, name='columns', align=uiconst.TOALL, clipChildren=True)
        self.headerDistance = Container(parent=sortContainer, name='distancebox', padding=(0, 0, 0, 0), width=self.columnWidths[0], align=uiconst.TOLEFT, clipChildren=True)
        self.headerID = Container(parent=sortContainer, name='idHeader', padding=(0, 0, 0, 0), align=uiconst.TOLEFT, width=self.columnWidths[1], clipChildren=True)
        self.headerScanGroup = Container(parent=sortContainer, name='scanGroupHeader', padding=(0, 0, 0, 0), align=uiconst.TOLEFT, width=self.columnWidths[2], clipChildren=True)
        self.headerGroupName = Container(parent=sortContainer, name='groupNameHeader', padding=(0, 0, 0, 0), align=uiconst.TOLEFT, width=self.columnWidths[3], clipChildren=True)
        self.headerTypeName = Container(parent=sortContainer, name='typeNameHeader', padding=(0, 0, 0, 0), align=uiconst.TOLEFT, width=100, clipChildren=True)
        self.columns = [self.headerDistance,
         self.headerID,
         self.headerScanGroup,
         self.headerGroupName,
         self.headerTypeName,
         self.headerSignal]
        self.sortingTriangles = {}
        self.sortBySignal = self.SortHeader(self.headerSignal, localization.GetByLabel('UI/Inflight/Scanner/SignalStrength'), 'certainty', False, resize=False)
        self.sortByDistance = self.SortHeader(self.headerDistance, localization.GetByLabel('UI/Common/Distance'), 'distance', True)
        self.sortByID = self.SortHeader(self.headerID, localization.GetByLabel('UI/Common/ID'), 'id', True)
        self.sortByScanGroup = self.SortHeader(self.headerScanGroup, localization.GetByLabel('UI/Inflight/Scanner/ScanGroup'), 'scanGroupName', True)
        self.sortByGroupName = self.SortHeader(self.headerGroupName, localization.GetByLabel('UI/Inventory/ItemGroup'), 'groupName', True)
        self.sortByTypeName = self.SortHeader(self.headerTypeName, localization.GetByLabel('UI/Common/Type'), 'typeName', True, resize=False)
        self.sortingBy = None
        self.sortingByKey = settings.user.ui.Get('scannerSortingKey', self.sortBySignal.key)
        self.sortingByAscending = settings.user.ui.Get('scannerSortingAsc', self.sortBySignal.ascending)
        self.ShowSortingTriangle(self.sortingTriangles[self.sortingByKey], self.sortingByAscending)

    def CopyToClipboard(self):
        pass

    def _OnClose(self, *args):
        self.Cleanup()
        systemMap = sm.GetService('systemmap')
        systemMap.LoadProbesAndScanResult_Delayed()
        uthread.new(systemMap.LoadSolarsystemBrackets, True)

    @property
    def probeTracker(self):
        return self.scanSvc.GetProbeTracker()

    def UpdateProbeControlDisplay(self):
        displayAll = uicore.uilib.Key(uiconst.VK_SHIFT) or uicore.uilib.Key(uiconst.VK_MENU)
        try:
            self.centerProbeControl.cursor.display = not displayAll and self.scanSvc.HasAvailableProbes()
        except AttributeError:
            pass

        for probeID, probeControl in self.sr.probeSpheresByID.iteritems():
            probeControl.cursor.display = displayAll and self.probeTracker.GetProbeState(probeID) == probeStateIdle

    def OnGlobalKey(self, wnd, eventID, (vkey, flag)):
        self.UpdateProbeControlDisplay()
        return 1

    def SetScanDronesState(self, value):
        for probe in self.sr.probeSpheresByID.values():
            probe.SetScanDronesState(value)

    def OnSystemScanBegun(self):
        self.Refresh()
        self.SetScanDronesState(1)
        scanSvc = sm.GetService('scanSvc')
        currentScan = scanSvc.GetCurrentScan()
        self.scanAnimator.state = uiconst.UI_NORMAL
        animations.FadeTo(self.sr.resultscroll, duration=0.5, startVal=1.0, endVal=0.5)
        animations.FadeIn(self.scanAnimator, duration=0.5)
        animations.MorphScalar(self.scanAnimator, 'width', 0, 1, duration=currentScan.duration / 1000 + 0.5, callback=self.FadeOutScanAnimator)

    def FadeOutScanAnimator(self):
        animations.FadeTo(self.sr.resultscroll, duration=0.5, startVal=0.5, endVal=1.0)
        animations.FadeOut(self.scanAnimator, duration=0.5, callback=self.HideScanAnimator)

    def HideScanAnimator(self):
        self.scanAnimator.state = uiconst.UI_HIDDEN
        self.scanAnimator.width = 0

    def OnSystemScanDone(self):
        self.SetScanDronesState(0)
        self.Refresh()

    def OnSessionChanged(self, isRemote, session, change):
        if 'solarsystemid' in change and not eve.session.stationid:
            self.LoadProbeList()
            self.LoadResultList()

    def OnNewScannerFilterSet(self, *args):
        self.LoadFilterOptionsAndResults()

    def OnProbeStateUpdated(self, probeID, state):
        self.sr.loadProbeList = AutoTimer(200, self.LoadProbeList)
        self.sr.updateProbeSpheresTimer = AutoTimer(200, self.UpdateProbeSpheres)

    def OnProbeRangeUpdated(self, probeID, scanRange):
        probe = self.GetProbeSphere(probeID)
        if probe:
            probe.SetRange(scanRange)

    def OnScannerDisconnected(self):
        """
        Refresh all probe related stuff
        """
        self.LoadProbeList()
        self.LoadResultList()
        self.UpdateProbeSpheres()
        self.CheckButtonStates()

    def OnProbeRemoved(self, probeID):
        uthread.new(self._OnProbeRemove, probeID)

    def _OnProbeRemove(self, probeID):
        rm = []
        cnt = 0
        for entry in self.sr.scroll.GetNodes():
            if entry.Get('probe', None) is None:
                continue
            if entry.probe.probeID == probeID:
                rm.append(entry)
            cnt += 1

        if rm:
            self.sr.scroll.RemoveEntries(rm)
        if cnt <= 1:
            uthread.new(self.LoadProbeList)
        self.CheckButtonStates()
        self.UpdateProbeSpheres()

    def OnProbeAdded(self, probe):
        uthread.new(self._OnProbeAdded, probe)

    def _OnProbeAdded(self, probe):
        self.UpdateProbeSpheres()
        self.LoadProbeList()
        sm.GetService('systemmap').LoadProbesAndScanResult()

    def UpdateProbeState(self, probeID, probeState):
        probe = self.GetProbeSphere(probeID)
        if probe:
            if not uicore.uilib.Key(uiconst.VK_SHIFT):
                probe.cursor.display = False
            else:
                probe.cursor.display = probeState == probeStateIdle

    def Cleanup(self):
        """
        Cleans up added spheres, brackets and scanresults
        """
        self.sr.probeSpheresByID = {}
        self.centerProbeControl = None
        bracketWnd = uicore.layer.systemMapBrackets
        for each in bracketWnd.children[:]:
            if each.name in ('__probeSphereBracket', '__pointResultBracket'):
                each.trackTransform = None
                each.Close()

        self.CleanupResultShapes()
        scene = sm.GetService('sceneManager').GetRegisteredScene('systemmap')
        if scene:
            for intersection in self.sr.probeIntersectionsByPair.values():
                if intersection.lineSet in scene.objects:
                    scene.objects.remove(intersection.lineSet)

            if self.sr.distanceRings and self.sr.distanceRings.lineSet in scene.objects:
                scene.objects.remove(self.sr.distanceRings.lineSet)
        self.sr.probeIntersectionsByPair = {}
        self.sr.distanceRings = None
        parent = self.GetSystemParent(create=0)
        systemMapSvc = sm.GetService('systemmap')
        currentSystem = systemMapSvc.GetCurrentSolarSystem()
        if currentSystem:
            if self.centroidLines and self.centroidLines in currentSystem.children:
                currentSystem.children.remove(self.centroidLines)
                self.centroidLines = None
            if parent and parent in currentSystem.children[:]:
                currentSystem.children.remove(parent)
        self.sr.systemParent = None
        systemMapSvc.HighlightItemsWithinProbeRange()

    def OpenMap(self, *args):
        sm.GetService('viewState').ToggleSecondaryView('systemmap')

    def LaunchFormation(self, formationID, size):
        sm.GetService('scanSvc').MoveProbesToFormation(formationID)

    def BreakFormation(self, *args):
        self.probeTracker.BreakFormation()

    def GetFilterMenu(self, *args):
        filterName = self.sr.filterCombo.GetKey()
        filterData = self.sr.filterCombo.GetValue()
        m = [(MenuLabel('UI/Inflight/Scanner/CreateNewFilter'), AddFilter)]
        if filterName and filterData:
            m.append((MenuLabel('UI/Inflight/Scanner/EditCurrentFilter'), self.EditCurrentFilter))
            m.append((MenuLabel('UI/Inflight/Scanner/DeleteCurrentFilter'), self.DeleteCurrentFilter))
        scanSvc = sm.GetService('scanSvc')
        resultsIgnored = self.scanSvc.GetIgnoredResultsDesc()
        if len(resultsIgnored) > 0:
            m.append(None)
            m.append((MenuLabel('UI/Inflight/Scanner/ClearAllIgnoredResults'), scanSvc.ClearIgnoredResults))
            ids = sorted(resultsIgnored)
            submenu = []
            for id, desc in ids:
                if desc:
                    idDesc = (localization.GetByLabel('UI/Inflight/Scanner/ResultIdAndDesc', id=id, desc=desc), scanSvc.ShowIgnoredResult, (id,))
                else:
                    idDesc = (id, scanSvc.ShowIgnoredResult, (id,))
                submenu.append(idDesc)

            m.append((MenuLabel('UI/Inflight/Scanner/ClearIgnoredResult'), submenu))
        return m

    def LoadFilterOptions(self):
        filterOps = self.scanSvc.GetFilterOptions()
        activeFilter = self.scanSvc.GetActiveFilterID()
        self.sr.filterCombo.LoadOptions(filterOps)
        self.sr.filterCombo.SelectItemByValue(activeFilter)

    def LoadFilterOptionsAndResults(self):
        self.LoadFilterOptions()
        self.LoadResultList()

    def CopyToClipboard(self, *args):
        pass

    def EditCurrentFilter(self, *args):
        activeFilter = self.scanSvc.GetActiveFilterID()
        editor = ScannerFilterEditor.Open()
        editor.LoadData(activeFilter)

    def DeleteCurrentFilter(self, *args):
        self.scanSvc.DeleteCurrentFilter()
        self.LoadFilterOptionsAndResults()

    def OnFilterComboChange(self, combo, key, value, *args):
        self.scanSvc.SetActiveFilter(value)
        self.LoadResultList()

    def ApplyProbesPortion(self):
        if not GetAttrs(self, 'sr', 'probesClipper') or getattr(self, '_ignorePortion', False) or not IsVisible(self.sr.probesClipper):
            return
        portion = settings.user.ui.Get('scannerProbesPortion', 0.5)
        minResultSpace = 18
        sl, st, sw, sh = self.sr.systemsParent.GetAbsolute()
        self.sr.resultClipper.GetAbsolute()
        spread = sh - self.sr.systemTopParent.height
        height = int(spread * portion)
        self.sr.probesClipper.height = min(height, spread - minResultSpace)

    def OnResizeUpdate(self, *args):
        uthread.new(self.ApplyProbesPortion)

    def _OnProbesSizeChanged(self, *args):
        sl, st, sw, sh = self.sr.systemsParent.GetAbsolute()
        probesPart = self.sr.probesClipper.height
        self.sr.resultClipper.GetAbsolute()
        portion = probesPart / float(sh - self.sr.systemTopParent.height)
        settings.user.ui.Set('scannerProbesPortion', portion)
        self._ignorePortion = False

    def _OnProbesSizeChangeStarting(self, *args):
        self._ignorePortion = True
        l, t, w, h = self.sr.probesClipper.GetAbsolute()
        minResultSpace = 18
        maxValue = uicore.desktop.height - t - minResultSpace
        self.sr.divider.SetMinMax(maxValue=maxValue)
        self._maxProbesClipperHeight = maxValue

    def _OnProbesSizeChanging(self, *args):
        if self.sr.probesClipper.height < self._maxProbesClipperHeight:
            if self.sr.stack:
                l, t, w, h = self.sr.stack.GetAbsolute()
            else:
                l, t, w, h = self.GetAbsolute()
            minResultSpace = 18
            if t + h - uicore.uilib.y < minResultSpace:
                if self.sr.stack:
                    self.sr.stack.height = uicore.uilib.y + minResultSpace - t
                else:
                    self.height = uicore.uilib.y + minResultSpace - t

    def CenterMapOnResult(self, pos):
        uicore.layer.systemmap.FocusOnPoint(pos)

    def LoadResultList(self):
        if self.destroyed:
            return
        scanSvc = sm.GetService('scanSvc')
        currentScan = scanSvc.GetCurrentScan()
        scanningProbes = scanSvc.GetScanningProbes()
        bp = sm.GetService('michelle').GetBallpark(doWait=True)
        if bp is None:
            return
        if not bp.ego:
            return
        ego = bp.balls[bp.ego]
        myPos = (ego.x, ego.y, ego.z)
        results, ignored, filtered, filteredAnomalies = self.scanSvc.GetResults()
        self.CleanupResultShapes()
        resultList = []
        if currentScan and blue.os.TimeDiffInMs(currentScan.startTime, blue.os.GetSimTime()) < currentScan.duration:
            return
        if scanningProbes and session.shipid not in scanningProbes:
            return
        if results:
            for result in results:
                scanGroupName = self.scanSvc.GetScanGroupName(result)
                groupName = self.scanSvc.GetGroupName(result)
                typeName = self.scanSvc.GetTypeName(result)
                distance = result.GetDistance(myPos)
                texts = [result.id,
                 scanGroupName,
                 groupName,
                 typeName,
                 localization.GetByLabel('UI/Inflight/Scanner/SignalStrengthPercentage', signalStrength=min(1.0, result.certainty) * 100),
                 FmtDist(distance)]
                sortData = KeyVal(id=result.id, scanGroupName=scanGroupName, groupName=groupName, typeName=typeName, certainty=min(1.0, result.certainty) * 100, distance=distance)
                data = KeyVal()
                data.texts = texts
                data.sortData = sortData
                data.columnID = 'probeResultGroupColumn'
                data.scanGroupName = scanGroupName
                data.groupName = groupName
                data.typeName = typeName
                data.result = result
                data.GetMenu = self.ResultMenu
                data.GetColumnWidths = self.GetColumnWidths
                data.distance = distance
                data.newResult = True
                data.CenterMapOnResult = self.CenterMapOnResult
                resultList.append(listentry.Get('ScanResult', data=data))

        resultList = sorted(resultList, key=lambda x: getattr(x.sortData, self.sortingByKey), reverse=not self.sortingByAscending)
        if not resultList:
            data = KeyVal()
            data.label = localization.GetByLabel('UI/Inflight/Scanner/NoScanResult')
            data.hideLines = 1
            resultList.append(listentry.Get('Generic', data=data))
        resultList.append(listentry.Get('Line', data=KeyVal(height=1)))
        self.sr.resultscroll.Load(contentList=resultList)
        self.sr.resultscroll.ShowHint('')
        self.ShowFilteredAndIgnored(filtered, ignored, filteredAnomalies)
        self.HighlightGoodResults()

    def ClearScanResult(self, *args):
        data = KeyVal()
        data.label = localization.GetByLabel('UI/Inflight/Scanner/NoScanResult')
        data.hideLines = 1
        self.sr.resultscroll.Load(contentList=[listentry.Get('Generic', data=data)])
        self.sr.resultscroll.ShowHint('')

    def GetProbeEntry(self, probe, selectedIDs = None):
        selectedIDs = selectedIDs or []
        data = KeyVal()
        data.texts, data.sortData = self.GetProbeLabelAndSortData(probe)
        data.columnID = 'probeGroupColumn'
        data.probe = probe
        data.probeID = probe.probeID
        data.isSelected = probe.probeID in selectedIDs
        data.GetMenu = self.GetProbeMenu
        data.scanRangeSteps = sm.GetService('scanSvc').GetScanRangeStepsByTypeID(probe.typeID)
        data.OnMouseEnter = self.OnProbeMouseEnter
        data.OnMouseExit = self.OnProbeMouseExit
        iconPar = Container(name='iconParent', parent=None, align=uiconst.TOPLEFT, width=36, height=16, state=uiconst.UI_PICKCHILDREN)
        icon1 = Icon(parent=iconPar, icon='ui_38_16_181', pos=(0, 0, 16, 16), align=uiconst.RELATIVE)
        icon1.hint = localization.GetByLabel('UI/Inflight/Scanner/RecoverProbe')
        icon1.probeID = probe.probeID
        icon1.OnClick = (self.RecoverProbeClick, icon1)
        icon2 = Icon(parent=iconPar, icon='ui_38_16_182', pos=(20, 0, 16, 16), align=uiconst.RELATIVE)
        icon2.hint = localization.GetByLabel('UI/Inflight/Scanner/DestroyProbe')
        icon2.probeID = probe.probeID
        icon2.OnClick = (self.DestroyProbeClick, icon2)
        data.overlay = iconPar
        entry = listentry.Get('ScanProbeEntry', data=data)
        return entry

    def OnProbeMouseEnter(self, entry):
        probeID = entry.sr.node.probeID
        try:
            self.sr.probeSpheresByID[probeID].HighlightProbe()
        except KeyError:
            pass

    def OnProbeMouseExit(self, entry):
        probeID = entry.sr.node.probeID
        try:
            self.sr.probeSpheresByID[probeID].StopHighlightProbe()
        except KeyError:
            pass

    def LoadProbeList(self):
        selectedIDs = self.GetSelectedProbes(asIds=1)
        scans = sm.GetService('scanSvc')
        scrolllist = []
        for probeID, probe in scans.GetProbeData().items():
            if cfg.invtypes.Get(probe.typeID).groupID in self.__disallowanalysisgroups:
                continue
            entry = self.GetProbeEntry(probe, selectedIDs)
            scrolllist.append(entry)

        scrolllist = listentry.SortNodeList(scrolllist, 'probeGroupColumn')
        if len(scrolllist) == 0:
            data = KeyVal()
            data.label = localization.GetByLabel('UI/Inflight/Scanner/NoProbesDeployed')
            scrolllist.append(listentry.Get('Generic', data=data))
        scrolllist.append(listentry.Get('Line', data=KeyVal(height=1)))
        self.sr.scroll.Load(contentList=scrolllist)
        self.sr.scroll.ShowHint('')
        self.UpdateProbeList()
        self.sr.updateProbes = AutoTimer(1000, self.UpdateProbeList)
        self.CheckButtonStates()
        self.sr.loadProbeList = None

    def GetProbeLabelAndSortData(self, probe, entry = None):
        if probe.expiry is None:
            expiryText = localization.GetByLabel('UI/Generic/None')
        else:
            expiry = max(0L, long(probe.expiry) - blue.os.GetSimTime())
            if expiry <= 0:
                expiryText = localization.GetByLabel('UI/Inflight/Scanner/Expired')
            else:
                expiryText = FmtDate(expiry, 'ss')
        scanSvc = sm.GetService('scanSvc')
        isActive = scanSvc.IsProbeActive(probe.probeID)
        probeStateSortText = FmtProbeState(probe.state)
        probeStateDisplayText = FmtProbeState(probe.state, colorize=True)
        if entry:
            sortData = entry.sortData[:]
            texts = entry.texts[:]
            sortData[4] = isActive
            texts[4].SetChecked(isActive, report=0)
            sortData[1] = probe.scanRange
            texts[1] = FmtDist(probe.scanRange)
            sortData[2] = probe.expiry
            texts[2] = expiryText
            sortData[3] = probeStateSortText
            texts[3] = probeStateDisplayText
        else:
            label = scanSvc.GetProbeLabel(probe.probeID)
            sortData = [probe.probeID,
             probe.scanRange,
             probe.expiry,
             probeStateSortText,
             isActive]
            checkBox = Checkbox(text='', parent=None, configName='probeactive', retval=probe.probeID, checked=isActive, callback=self.OnProbeCheckboxChange, align=uiconst.CENTER)
            checkBox.hint = localization.GetByLabel('UI/Inflight/Scanner/MakeActive')
            texts = [label,
             FmtDist(probe.scanRange),
             expiryText,
             probeStateDisplayText,
             checkBox]
        return (texts, sortData)

    def OnProbeCheckboxChange(self, checkbox, *args):
        selected = self.sr.scroll.GetSelected()
        probeIDs = [ each.probe.probeID for each in selected if getattr(each, 'probe') ]
        probeID = checkbox.data['value']
        if probeID not in probeIDs:
            probeIDs = [probeID]
        for probeID in probeIDs:
            sm.GetService('scanSvc').SetProbeActiveState(probeID, checkbox.checked)

        self.UpdateProbeList()
        self.CheckButtonStates()

    def UpdateProbeList(self):
        """ 
        Update function for the probe listing, called with one sec interval to 
        check if a probe has expired or been moved from the ballpark
        """
        if self is None or self.destroyed:
            self.sr.updateProbes = None
            return
        bracketsByProbeID = {}
        for each in uicore.layer.systemMapBrackets.children[:]:
            probe = getattr(each, 'probe', None)
            if probe is None:
                continue
            bracketsByProbeID[probe.probeID] = each

        probeEntries = []
        for entry in self.sr.scroll.GetNodes():
            if entry.Get('probe', None) is None:
                continue
            probe = entry.probe
            newTexts, newSortData = self.GetProbeLabelAndSortData(probe, entry)
            if newTexts != entry.texts or newSortData != entry.sortData:
                entry.needReload = 1
            else:
                entry.needReload = 0
            entry.sortData = newSortData
            entry.texts = newTexts
            probeEntries.append(entry)
            bracket = bracketsByProbeID.get(probe.probeID, None)
            if bracket:
                bracket.displayName = localization.GetByLabel('UI/Inflight/Scanner/ProbeBracket', probeLabel=newTexts[0], probeStatus=newTexts[3], probeRange=newTexts[1])
                bracket.ShowLabel()

        self.sr.scroll.state = uiconst.UI_DISABLED
        self.UpdateColumnSort(probeEntries, 'probeGroupColumn')
        self.sr.scroll.state = uiconst.UI_NORMAL

    def UpdateColumnSort(self, entries, columnID):
        if not entries:
            return
        startIdx = entries[0].idx
        endIdx = entries[-1].idx
        entries = listentry.SortNodeList(entries, columnID)
        self.sr.scroll.sr.nodes = self.sr.scroll.sr.nodes[:startIdx] + entries + self.sr.scroll.sr.nodes[endIdx + 1:]
        self.sr.scroll.UpdatePosition('UpdateColumnSort_Scanner')
        for entry in self.sr.scroll.GetNodes()[startIdx:]:
            if entry.Get('needReload', 0) and entry.panel:
                entry.panel.Load(entry)

    def ValidateProbesState(self, probeIDs, isEntryButton = False):
        """
        Validates if all probes in probeIDs are in idle state
        """
        scanSvc = sm.GetService('scanSvc')
        probeData = scanSvc.GetProbeData()
        for probeID in probeIDs:
            if probeID in probeData:
                probe = probeData[probeID]
                if isEntryButton:
                    if probe.state not in (probeStateIdle, probeStateInactive):
                        return False
                elif probe.state != probeStateIdle:
                    return False

        return True

    def CheckButtonStates(self):
        probes = sm.GetService('scanSvc').GetActiveProbes()
        scanningProbes = sm.GetService('scanSvc').GetScanningProbes()
        allIdle = self.ValidateProbesState(probes)
        if probes and allIdle:
            self.sr.destroyBtn.Enable()
            self.sr.recoverBtn.Enable()
        else:
            self.DisableButton(self.sr.destroyBtn)
            self.DisableButton(self.sr.recoverBtn)
        canClaim = sm.GetService('scanSvc').CanClaimProbes()
        if canClaim:
            self.sr.reconnectBtn.Enable()
        else:
            self.DisableButton(self.sr.reconnectBtn)
        if scanningProbes:
            self.DisableButton(self.sr.analyzeBtn)
        else:
            self.sr.analyzeBtn.Enable()
        self.CheckFormationButtons()

    def CheckFormationButtons(self):
        for formationID, btn in self.formationButtonsByID.iteritems():
            if self.scanSvc.CanLaunchFormation(formationID):
                btn.Enable()
            else:
                self.DisableButton(btn)

        self.customFormationButton.UpdateButton()

    def DisableButton(self, btn):
        btn.Disable()
        btn.opacity = 0.25

    def OnModuleOnlineChange(self, item, oldValue, newValue):
        if item.groupID == groupScanProbeLauncher:
            self.CheckButtonStates()

    def OnDogmaItemChange(self, item, change):
        if item.groupID == groupScannerProbe and IsShipFittingFlag(item.flagID):
            self.CheckFormationButtons()

    def OnProbePositionsUpdated(self):
        sm.GetService('scanSvc').LogInfo('OnProbePositionsUpdated...')
        self.UpdateProbeSpheres()

    def OnBallparkSetState(self):
        self.LoadFilterOptionsAndResults()

    def GetShipScannerEntry(self):
        scanRange = 5
        label = '%s<t>%s<t>%s' % (localization.GetByLabel('UI/Inflight/Scanner/OnBoardScanner'), FmtDist(scanRange * AU), '')
        data = KeyVal()
        data.label = label
        data.probe = None
        data.probeID = eve.session.shipid
        data.isSelected = False
        data.GetMenu = self.GetProbeMenu
        return listentry.Get('Generic', data=data)

    def GetProbeMenu(self, entry, *args):
        probeIDs = self.GetSelectedProbes(asIds=1)
        return sm.GetService('scanSvc').GetProbeMenu(entry.sr.node.probeID, probeIDs)

    @UserErrorIfScanning
    def DestroyActiveProbes(self, *args):
        scanSvc = sm.GetService('scanSvc')
        probes = scanSvc.GetActiveProbes()
        allIdle = self.ValidateProbesState(probes)
        if probes and allIdle and eve.Message('DestroyProbes', {}, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            for _probeID in probes[:]:
                if scanSvc.GetProbeState(_probeID) != probeStateIdle:
                    self.ClearScanResult()
                scanSvc.DestroyProbe(_probeID)

    @UserErrorIfScanning
    def DestroyProbeClick(self, icon):
        probeID = getattr(icon, 'probeID', None)
        probes = [probeID]
        allIdle = self.ValidateProbesState(probes, True)
        if probeID and allIdle and eve.Message('DestroySelectedProbes', {}, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            sm.GetService('scanSvc').DestroyProbe(probeID)

    @UserErrorIfScanning
    def ReconnectToLostProbes(self, *args):
        self.sr.reconnectBtn.opacity = 0.25
        sm.GetService('scanSvc').ReconnectToLostProbes()
        self.LoadProbeList()

    @UserErrorIfScanning
    def RecoverActiveProbes(self, *args):
        scanSvc = sm.GetService('scanSvc')
        probes = scanSvc.GetProbeData()
        recall = [ pID for pID, p in probes.iteritems() if p.state == probeStateIdle ]
        scanSvc.RecoverProbes(recall)

    @UserErrorIfScanning
    def RecoverProbeClick(self, icon):
        probeID = getattr(icon, 'probeID', None)
        if not probeID:
            return
        sm.GetService('scanSvc').RecoverProbes([probeID])

    def GetSelectedProbes(self, asIds = 0):
        selected = self.sr.scroll.GetSelected()
        returnVal = []
        for each in selected:
            if each.Get('probe', None) is not None:
                if asIds:
                    returnVal.append(each.probe.probeID)
                else:
                    returnVal.append(each)

        return returnVal

    def UpdateProbeSpheres(self, *args):
        uthread.Lock('ScannerWnd::UpdateProbeSpheres')
        try:
            self.isUpdatingProbeSpheres = True
            scanSvc = sm.GetService('scanSvc')
            bp = sm.GetService('michelle').GetBallpark()
            if not bp or eve.session.shipid not in bp.balls or not sm.GetService('viewState').IsViewActive('systemmap'):
                self.Cleanup()
                return
            parent = self.GetSystemParent()
            probeData = scanSvc.GetProbeData()
            probeIDs = self.sr.probeSpheresByID.keys()[:]
            for probeID in probeIDs:
                if probeID not in probeData or probeData[probeID].state == probeStateInactive:
                    probeControl = self.sr.probeSpheresByID[probeID]
                    for bracket in uicore.layer.systemMapBrackets.children[:]:
                        if getattr(bracket, 'probeID', None) == probeID:
                            bracket.trackTransform = None
                            bracket.Close()

                    if probeControl.locator in parent.children:
                        parent.children.remove(probeControl.locator)
                    del self.sr.probeSpheresByID[probeID]

            if self.centerProbeControl is None:
                self.centerProbeControl = BaseProbeControl(FORMATION_CONTROL_ID, parent)
            shift = uicore.uilib.Key(uiconst.VK_SHIFT)
            if not shift:
                self.centerProbeControl.SetPosition(self.probeTracker.GetCenterOfActiveProbes())
            for probeID, probe in probeData.items():
                if probe.state == probeStateInactive:
                    continue
                if probeID not in self.sr.probeSpheresByID:
                    probeControl = ProbeControl(probeID, probe, parent, self)
                    self.sr.probeSpheresByID[probeID] = probeControl
                else:
                    probeControl = self.sr.probeSpheresByID[probeID]
                probeControl.SetRange(probe.scanRange)
                probeControl.SetPosition(probe.destination)
                self.UpdateProbeState(probeID, probe.state)

            self.UpdateProbeControlDisplay()
            self.HighlightProbeIntersections()
            sm.GetService('systemmap').HighlightItemsWithinProbeRange()
        finally:
            uthread.UnLock('ScannerWnd::UpdateProbeSpheres')
            self.sr.updateProbeSpheresTimer = None
            self.UpdateAnalyzeButtonState()

    def HighlightProbeIntersections(self):
        """
        Find out which probes are intersecting and draw highlight circles where they
        intersect. Updates the distance reference rings to maintain sync
        """
        scanSvc = sm.GetService('scanSvc')
        if self.sr.distanceRings:
            movingProbeID = self.sr.distanceRings.probeID
        else:
            movingProbeID = None
        probeIDs = scanSvc.GetActiveProbes()
        probeIDs.sort()
        possiblePairs = [ pair for pair in itertools.combinations(probeIDs, 2) ]
        activePairs = []
        for id1, id2 in possiblePairs:
            pair = (id1, id2)
            probe1 = self.GetProbeSphere(id1)
            probe2 = self.GetProbeSphere(id2)
            if not probe1 or not probe2:
                self.RemoveIntersection((id1, id2))
                continue
            pos1 = probe1.GetPosition()
            radius1 = probe1.GetRange()
            pos2 = probe2.GetPosition()
            radius2 = probe2.GetRange()
            if IsIntersecting(pos1, radius1, pos2, radius2) and not self.probeTracker.IsInFormation():
                if pair not in self.sr.probeIntersectionsByPair:
                    self.CreateIntersectionHighlight(pair)
                activePairs = self.SetIntersectionHighlight(pair, (pos1,
                 pos2,
                 radius1,
                 radius2), movingProbeID)
            else:
                self.RemoveIntersection(pair)

        for pair in self.sr.probeIntersectionsByPair.keys():
            if pair not in possiblePairs:
                self.RemoveIntersection(pair)

        self.UpdateDistanceRings()
        self.sr.deactivatingIntersections = False
        self.sr.fadeActiveIntersectionsTimer = AutoTimer(500, self.FadeActiveIntersections, activePairs)
        self.sr.deactivateIntersectionsTimer = AutoTimer(3000, self.DeactivateIntersections)

    def SetIntersectionHighlight(self, pair, config, movingProbeID):
        activePairs = []
        intersection = self.sr.probeIntersectionsByPair[pair]
        if config != intersection.lastConfig:
            intersection.lastConfig = config
            self.SetIntersectionColor(intersection, INTERSECTION_ACTIVE)
            pos1, pos2, _, _ = config
            distance = geo2.Vec3Length(geo2.Vec3Subtract(pos1, pos2))
            self.UpdateIntersectionHighlight(pair, distance)
            activePairs.append(pair)
        elif movingProbeID in pair:
            self.SetIntersectionColor(intersection, INTERSECTION_ACTIVE)
            activePairs.append(pair)
        else:
            self.SetIntersectionColor(intersection, INTERSECTION_FADED)
        return activePairs

    def RemoveIntersection(self, pair):
        scene = sm.GetService('sceneManager').GetRegisteredScene('systemmap')
        if not scene:
            return
        if pair in self.sr.probeIntersectionsByPair:
            intersection = self.sr.probeIntersectionsByPair[pair]
            if intersection.lineSet in scene.objects:
                scene.objects.remove(intersection.lineSet)
            del self.sr.probeIntersectionsByPair[pair]

    def UpdateIntersectionHighlight(self, pair, distance):
        intersection = self.sr.probeIntersectionsByPair[pair]
        data = self.ComputeHighlightCircle(distance, *intersection.lastConfig)
        if data:
            point, rotation, radius = data
            lineSet = intersection.lineSet
            lineSet.translationCurve.value = point
            lineSet.rotationCurve.value = rotation
            lineSet.scaling = (radius, radius, radius)
        else:
            self.RemoveIntersection(pair)

    def ComputeHighlightCircle(self, distance, pos1, pos2, rad1, rad2):
        if not distance:
            return None
        rad1_sq = rad1 ** 2
        rad2_sq = rad2 ** 2
        dist_sq = distance ** 2
        distToPoint = (rad1_sq - rad2_sq + dist_sq) / (2 * distance)
        radius_sq = rad1_sq - distToPoint ** 2
        if radius_sq < 0.0:
            return None
        radius = math.sqrt(radius_sq)
        normal = geo2.Vec3Normalize(pos2 - pos1)
        normal = geo2.Vector(*normal)
        point = pos1 + normal * distToPoint
        rotation = geo2.QuaternionRotationArc(AXIS_Y, normal)
        return (point * SYSTEMMAP_SCALE, rotation, radius * SYSTEMMAP_SCALE)

    def CreateIntersectionHighlight(self, pair):
        """
        create a line set for a intersection circle.
        The circle is located, rotated using curves.
        """
        scene = sm.GetService('sceneManager').GetRegisteredScene('systemmap')
        if not scene:
            return
        lineSet = self.CreateLineSet()
        scene.objects.append(lineSet)
        self.DrawCircle(lineSet, 1.0, INTERSECTION_COLOR)
        lineSet.SubmitChanges()
        lineSet.translationCurve = trinity.TriVectorCurve()
        lineSet.rotationCurve = trinity.TriRotationCurve()
        intersection = KeyVal(lastConfig=None, lineSet=lineSet, colorState=INTERSECTION_ACTIVE)
        self.sr.probeIntersectionsByPair[pair] = intersection

    def DrawCircle(self, lineSet, size, color):
        for idx in xrange(CIRCLE_NUM_POINTS):
            p1 = CIRCLE_POINTS[idx]
            p2 = CIRCLE_POINTS[(idx + 1) % CIRCLE_NUM_POINTS]
            lineSet.AddLine((p1[0] * size, p1[1] * size, p1[2] * size), color, (p2[0] * size, p2[1] * size, p2[2] * size), color)

    def FadeActiveIntersections(self, activePairs):
        if self.sr.distanceRings and self.sr.distanceRings.probeID:
            return
        start = blue.os.GetWallclockTime()
        ndt = 0.0
        while ndt != 1.0:
            ndt = max(0.0, min(blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime()) / 500.0, 1.0))
            colorRatio = Lerp(INTERSECTION_ACTIVE, INTERSECTION_FADED, ndt)
            for pair in activePairs:
                if pair in self.sr.probeIntersectionsByPair:
                    intersection = self.sr.probeIntersectionsByPair[pair]
                    self.SetIntersectionColor(intersection, colorRatio)

            blue.pyos.synchro.SleepWallclock(50)
            if self.destroyed:
                return

        self.sr.fadeActiveIntersectionsTimer = None

    def DeactivateIntersections(self):
        """
        dim all the intersections
        """
        self.sr.deactivatingIntersections = True
        start = blue.os.GetWallclockTime()
        ndt = 0.0
        while self.sr.deactivatingIntersections and ndt != 1.0:
            ndt = max(0.0, min(blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime()) / 2000.0, 1.0))
            colorRatio = Lerp(INTERSECTION_FADED, INTERSECTION_INACTIVE, ndt)
            for intersection in self.sr.probeIntersectionsByPair.itervalues():
                self.SetIntersectionColor(intersection, colorRatio)

            blue.pyos.synchro.SleepWallclock(100)
            if self.destroyed:
                return

        self.sr.deactivateIntersectionsTimer = None

    def SetIntersectionColor(self, intersection, colorState = 1.0):
        """
        dim the intersection highlight for specific pair.
        inactive: if True the intersection is made darker than if move else
        """
        if intersection.colorState == colorState:
            return
        intersection.colorState = colorState
        color = (INTERSECTION_COLOR[0] * colorState,
         INTERSECTION_COLOR[1] * colorState,
         INTERSECTION_COLOR[2] * colorState,
         1.0)
        lineSet = intersection.lineSet
        for i in xrange(CIRCLE_NUM_POINTS):
            intersection.lineSet.ChangeLineColor(i, color, color)

        lineSet.SubmitChanges()

    def ShowDistanceRings(self, probeControl, axis):
        scene = sm.GetService('sceneManager').GetRegisteredScene('systemmap')
        if scene:
            if not self.sr.distanceRings:
                lineSet = trinity.EveCurveLineSet()
                lineSet.additive = True
                tex2D = trinity.TriTexture2DParameter()
                tex2D.name = 'TexMap'
                tex2D.resourcePath = 'res:/dx9/texture/UI/lineSolid.dds'
                lineSet.lineEffect.resources.append(tex2D)
                baseColor = RANGE_INDICATOR_CIRCLE_COLOR
                for i, r in enumerate(DISTANCE_RING_RANGES):
                    div = 1.0 + i * 0.5
                    color = (baseColor[0] / div,
                     baseColor[1] / div,
                     baseColor[2] / div,
                     1.0)
                    unitcircle = ((r, 0, 0),
                     (0, 0, r),
                     (-r, 0, 0),
                     (0, 0, -r))
                    for i in xrange(4):
                        a, b = unitcircle[i - 1], unitcircle[i]
                        lineID = lineSet.AddSpheredLineCrt(a, color, b, color, (0, 0, 0), DISTRING_LINE_WIDTH)
                        lineSet.ChangeLineSegmentation(lineID, 10 * r)

                lineSet.AddStraightLine((MAX_DIST_RING_RANGE, 0.0, 0.0), RANGE_INDICATOR_CROSS_COLOR, (-MAX_DIST_RING_RANGE, 0.0, 0.0), RANGE_INDICATOR_CROSS_COLOR, DISTRING_LINE_WIDTH)
                lineSet.AddStraightLine((0.0, 0.0, MAX_DIST_RING_RANGE), RANGE_INDICATOR_CROSS_COLOR, (0.0, 0.0, -MAX_DIST_RING_RANGE), RANGE_INDICATOR_CROSS_COLOR, DISTRING_LINE_WIDTH)
                lineSet.SubmitChanges()
                self.sr.distanceRings = KeyVal(__doc__='distanceRings', lineSet=lineSet)
            if self.sr.distanceRings.lineSet not in probeControl.locator.children:
                probeControl.locator.children.append(self.sr.distanceRings.lineSet)
            self.sr.distanceRings.axis = axis
            self.sr.distanceRings.probeID = probeControl.uniqueID
            self.UpdateDistanceRings()

    def UpdateDistanceRings(self):
        """
        Update distance reference rings.
        Relocate the ring center to the center of the control used.
        rotate according to the control axis manipulated
        """
        if self.sr.distanceRings and self.sr.distanceRings.probeID not in (None, FORMATION_CONTROL_ID):
            probeControl = self.GetProbeSphere(self.sr.distanceRings.probeID)
            if probeControl:
                lineSet = self.sr.distanceRings.lineSet
                axis = self.sr.distanceRings.axis
                scale = probeControl.GetRange() / MAX_DIST_RING_RANGE
                lineSet.scaling = (scale, scale, scale)
                if axis == 'xy':
                    lineSet.rotation = (SQRT_05,
                     0.0,
                     0.0,
                     SQRT_05)
                elif axis == 'yz':
                    lineSet.rotation = (SQRT_05,
                     SQRT_05,
                     0.0,
                     0.0)
                elif axis == 'xz':
                    lineSet.rotation = (0.0, 0.0, 0.0, 0.0)
                else:
                    self.HideDistanceRings()

    def HideDistanceRings(self):
        scene = sm.GetService('sceneManager').GetRegisteredScene('systemmap')
        if self.sr.distanceRings and scene:
            parent = self.GetSystemParent()
            for tr in parent.children:
                if self.sr.distanceRings.lineSet in tr.children:
                    tr.children.remove(self.sr.distanceRings.lineSet)

            self.sr.distanceRings.axis = None
            self.sr.distanceRings.probeID = None

    def StartScaleMode(self, point):
        self.probeTracker.SetAsScaling(point)

    def StopScaleMode(self):
        if self.lastProbeScaleInfo is None:
            return
        self.probeTracker.UnsetAsScaling()
        probeID = self.lastProbeScaleInfo
        self.lastProbeScaleInfo = None
        probe = self.probeTracker.GetProbe(probeID)
        currentSize = probe.scanRange
        desiredSize = self.sr.probeSpheresByID[probeID].GetRange()
        rangeStep, desiredSize = self.probeTracker.GetRangeStepForType(probe.typeID, desiredSize)
        if not uicore.uilib.Key(uiconst.VK_SHIFT):
            scale = desiredSize / currentSize
            self.probeTracker.ScaleAllProbes(scale)
        else:
            self.probeTracker.SetProbeRangeStep(probeID, rangeStep)
        self.probeTracker.PersistProbeFormation()
        self.UpdateProbeSpheres()

    def ScaleProbe(self, probeControl, pos, force = 0):
        pVector = trinity.TriVector(*probeControl.locator.translation)
        cVector = trinity.TriVector(*(pos * (1.0 / SYSTEMMAP_SCALE)))
        s = max(probeControl.scanRanges[0], (pVector - cVector).Length())
        probeControl.SetRange(s)
        closest = probeControl.scanRanges[-1]
        for scanRange in probeControl.scanRanges:
            if not closest or abs(scanRange - s) <= abs(closest - s):
                closest = scanRange

        if probeControl or force:
            shift = uicore.uilib.Key(uiconst.VK_SHIFT)
            if not shift:
                probeIDs = [ probeID for probeID in self.probeTracker.GetProbeData() ]
                probeInfo = self.scanSvc.GetScaledProbes(pos, probeIDs)
            else:
                probeInfo = [(probeControl.uniqueID, probeControl.GetPosition(), probeControl.GetRange())]
            for probeID, probePos, scanRange in probeInfo:
                _probeControl = self.sr.probeSpheresByID[probeID]
                _probeControl.SetRange(scanRange)
                _probeControl.SetPosition(probePos)

            self.lastProbeScaleInfo = probeControl.uniqueID
        self.HighlightProbeIntersections()
        self.lastScaleUpdate = (probeControl.probeID, pos)
        probeControl.bracket.displayName = localization.GetByLabel('UI/Inflight/Scanner/ProbeRange', curDist=FmtDist(s), maxDist=FmtDist(closest))
        sm.GetService('systemmap').HighlightItemsWithinProbeRange()
        probeControl.ShowScanRanges()

    def RegisterProbeRange(self, probeControl):
        self.lastScaleUpdate = None
        sm.GetService('systemmap').HighlightItemsWithinProbeRange()
        self.HighlightProbeIntersections()
        self.scanSvc.PurgeBackupData()
        probeControl.HideScanRanges()

    def UpdateProbeRangeUI(self, probeID, range, rangeStep):
        probe = self.GetProbeSphere(probeID)
        if probe:
            probe.SetRange(range)

    def GetControl(self, uniqueID):
        if uniqueID == FORMATION_CONTROL_ID:
            return self.centerProbeControl
        else:
            return self.GetProbeSphere(uniqueID)

    def GetProbeSphere(self, probeID):
        return self.sr.probeSpheresByID.get(int(probeID), None)

    def GetProbeSpheres(self):
        return self.sr.probeSpheresByID

    def HiliteCursor(self, pickObject = None):
        for probeID, probeControl in self.sr.probeSpheresByID.iteritems():
            probeControl.ResetCursorHighlight()

        if self.centerProbeControl is not None:
            self.centerProbeControl.ResetCursorHighlight()
        if pickObject:
            cursorName, side, probeID = pickObject.name.split('_')
            hiliteAxis = cursorName[6:]
            if probeID == FORMATION_CONTROL_ID:
                self.centerProbeControl.HighlightAxis(hiliteAxis)
                self.scanSvc.ProbeControlSelect()
            else:
                probeID = int(probeID)
                if probeID in self.sr.probeSpheresByID:
                    probeControl = self.sr.probeSpheresByID[probeID]
                    probeControl.HighlightAxis(hiliteAxis)
                    self.scanSvc.ProbeControlSelect()
        else:
            self.scanSvc.ProbeControlDeselected()

    def ShowCentroidLines(self):
        """
        Draw lines from the centroid to each active probe
        """
        if self.centroidLines is None:
            systemMap = sm.GetService('systemmap')
            if systemMap.currentSolarsystem is None:
                return
            self.centroidLines = trinity.EveCurveLineSet()
            tex2D = trinity.TriTexture2DParameter()
            tex2D.name = 'TexMap'
            tex2D.resourcePath = 'res:/dx9/texture/UI/lineSolid.dds'
            self.centroidLines.lineEffect.resources.append(tex2D)
            systemMap.currentSolarsystem.children.append(self.centroidLines)
        self.centroidLines.display = True
        scanSvc = sm.GetService('scanSvc')
        probes = scanSvc.GetProbeData()
        probeIDs = [ probeID for probeID, probe in probes.iteritems() if probe.state == probeStateIdle ]
        if probeIDs:
            probeIDs.sort()
            update = self.lastProbeIDs == probeIDs
            if not update:
                self.lastProbeIDs = probeIDs
                self.centroidLines.ClearLines()
            centroid = geo2.Vector(0, 0, 0)
            probePositions = []
            for index, probeID in enumerate(probeIDs):
                probeControl = self.GetProbeSphere(probeID)
                if probeControl:
                    p = probeControl.GetPosition()
                    centroid += p
                    probePositions.append((p.x, p.y, p.z))

            centroid /= len(probeIDs)
            c = (centroid.x, centroid.y, centroid.z)
            for index, position in enumerate(probePositions):
                if update:
                    self.centroidLines.ChangeLinePositionCrt(index, c, position)
                else:
                    self.centroidLines.AddStraightLine(c, CENTROID_LINE_COLOR, position, CENTROID_LINE_COLOR, CENTROID_LINE_WIDTH)
                self.centroidLines.ChangeLineAnimation(index, CENTROID_LINE_COLOR, -0.25, 10.0)

            self.centroidLines.SubmitChanges()
        self.centroidTimer = AutoTimer(500, self.RemoveCentroidLines)

    def RemoveCentroidLines(self):
        if self.centroidLines is not None:
            self.centroidLines.display = False
        self.centroidTimer = None

    def RegisterProbeMove(self, *args):
        self.lastMoveUpdate = None
        scanSvc = sm.GetService('scanSvc')
        probes = scanSvc.GetProbeData()
        for probeID, probe in probes.iteritems():
            if probe.state != probeStateIdle:
                continue
            probeControl = self.GetProbeSphere(probeID)
            if probeControl:
                cachedPos = probes[probeID].destination
                currentPos = probeControl.locator.translation
                if geo2.Vec3DistanceD(cachedPos, currentPos):
                    scanSvc.SetProbeDestination(probeID, currentPos)

        self.probeTracker.PersistProbeFormation()
        self.HideDistanceRings()
        self.scanSvc.PurgeBackupData()
        sm.GetService('systemmap').HighlightItemsWithinProbeRange()

    def MoveProbe(self, probeControl, translation):
        """
        Move Probe to new location without storing the position
        """
        if probeControl.uniqueID == FORMATION_CONTROL_ID:
            probeInfo = self.probeTracker.ShiftAllProbes(translation)
        else:
            probeInfo = self.probeTracker.ShiftProbe(probeControl.uniqueID, translation)
            self.HighlightProbeIntersections()
        for probeID, pos in probeInfo:
            try:
                _probeControl = self.sr.probeSpheresByID[probeID]
            except KeyError:
                self.scanSvc.LogError("Trying to shift a probe that doesn't exist", probeID)
                continue

            _probeControl.SetPosition(pos)

        self.centerProbeControl.SetPosition(self.probeTracker.GetCenterOfActiveProbes())
        self.lastMoveUpdate = (probeControl.uniqueID, translation)
        sm.GetService('systemmap').HighlightItemsWithinProbeRange()

    def CancelProbeMoveOrScaling(self, *args):
        self.scanSvc.RestoreProbesFromBackup()
        self.centerProbeControl.SetPosition(self.probeTracker.GetCenterOfActiveProbes())
        self.UpdateProbeSpheres()
        for probeControl in self.sr.probeSpheresByID.itervalues():
            probeControl.HideScanRanges()

        sm.GetService('systemmap').HighlightItemsWithinProbeRange()

    @UserErrorIfScanning
    def Analyze(self, *args):
        self.sr.analyzeBtn.Disable()
        self.sr.analyzeBtn.opacity = 0.25
        scanSvc = sm.GetService('scanSvc')
        try:
            scanSvc.RequestScans()
        except UserError as e:
            self.CheckButtonStates()
            raise e

        self.LoadResultList()

    def ResultMenu(self, panel, *args):
        result = panel.sr.node.result
        scanSvc = sm.GetService('scanSvc')
        menu = []
        siteData = SiteDataFromScanResult(result)
        menu.extend(scanSvc.GetScanResultMenuWithoutIgnore(siteData))
        nodes = self.sr.resultscroll.GetSelected()
        idList = []
        nonAnomalyIdList = []
        for node in nodes:
            if hasattr(node.result, 'id'):
                idList.append(node.result.id)
                if node.result.scanGroupID != probeScanGroupAnomalies:
                    nonAnomalyIdList.append(node.result.id)

        menu.append((MenuLabel('UI/Inflight/Scanner/IngoreResult'), scanSvc.IgnoreResult, idList))
        menu.append((MenuLabel('UI/Inflight/Scanner/IgnoreOtherResults'), scanSvc.IgnoreOtherResults, idList))
        if len(nonAnomalyIdList) > 0:
            menu.append((MenuLabel('UI/Inflight/Scanner/ClearResult'), scanSvc.ClearResults, nonAnomalyIdList))
        return menu

    def OnSelectionChange(self, entries):
        self.DisplaySelectedResults()

    def DisplaySelectedResults(self):
        if 'scanresult' not in GetVisibleSolarsystemBrackets():
            self.HideAllResults()
        else:
            nodes = self.sr.resultscroll.GetSelected()
            excludeSet = set()
            for entry in nodes:
                if entry.result:
                    self.DisplayResult(entry.result)
                    if entry.result in self.sr.resultObjectsByID:
                        excludeSet.add(entry.result)

            resultSet = set(self.sr.resultObjectsByID.keys())
            resultsToHide = resultSet - excludeSet
            for resultID in resultsToHide:
                self.HideResult(resultID)

    def HideAllResults(self):
        for resultID in self.sr.resultObjectsByID.keys():
            self.HideResult(resultID)

    def DisplayResult(self, result):
        if result in self.sr.resultObjectsByID:
            for obj in self.sr.resultObjectsByID[result]:
                if obj.__bluetype__ in ('trinity.EveTransform', 'trinity.EveRootTransform'):
                    obj.display = 1
                elif obj.__bluetype__ == 'trinity.EveLineSet':
                    scene = sm.GetService('sceneManager').GetRegisteredScene('systemmap')
                    if scene:
                        if obj not in scene.objects:
                            scene.objects.append(obj)
                elif isinstance(obj, Bracket):
                    obj.state = uiconst.UI_PICKCHILDREN
                    if 'scanresult' in GetHintsOnSolarsystemBrackets():
                        obj.ShowBubble(obj.hint)
                    else:
                        obj.ShowBubble(None)

        elif isinstance(result.data, float):
            self.CreateSphereResult(result)
        elif isinstance(result.data, tuple):
            self.CreatePointResult(result, result.data)
        elif isinstance(result.data, list):
            for translation in result.data:
                self.CreatePointResult(result, translation)

        else:
            self.CreateCircleResult(result)

    def HideResult(self, resultID):
        if resultID in self.sr.resultObjectsByID:
            for obj in self.sr.resultObjectsByID[resultID]:
                if obj.__bluetype__ in ('trinity.EveTransform', 'trinity.EveRootTransform'):
                    obj.display = 0
                elif obj.__bluetype__ == 'trinity.EveLineSet':
                    scene = sm.GetService('sceneManager').GetRegisteredScene('systemmap')
                    if scene:
                        if obj in scene.objects:
                            scene.objects.remove(obj)
                elif isinstance(obj, Bracket):
                    obj.state = uiconst.UI_HIDDEN

    def RegisterMapObject(self, result, ob):
        if result not in self.sr.resultObjectsByID:
            self.sr.resultObjectsByID[result] = []
        self.sr.resultObjectsByID[result].append(ob)

    def CreateSphereResult(self, result):
        sphereSize = result.data
        sphere = trinity.Load('res:/dx9/model/UI/Resultbubble.red')
        sphere.name = 'Result sphere'
        sphere.children[0].scaling = (2.0, 2.0, 2.0)
        sphere.scaling = (sphereSize, sphereSize, sphereSize)
        locator = trinity.EveTransform()
        locator.name = 'scanResult_%s' % result.id
        locator.translation = result.pos
        locator.children.append(sphere)
        parent = self.GetSystemParent()
        parent.children.append(locator)
        self.RegisterMapObject(result, locator)

    def CreateCircleResult(self, result):
        numPoints = 256
        lineSet = self.CreateLineSet()
        lineSet.scaling = (SYSTEMMAP_SCALE, SYSTEMMAP_SCALE, SYSTEMMAP_SCALE)
        parentPos = geo2.Vector(*result.data.point)
        dirVec = geo2.Vector(*result.data.normal)
        radius = result.data.radius
        if radius == 0:
            return
        fwdVec = geo2.Vector(0.0, 1.0, 0.0)
        dirVec = geo2.Vec3Normalize(dirVec)
        fwdVec = geo2.Vec3Normalize(fwdVec)
        stepSize = pi * 2.0 / numPoints
        rotation = geo2.QuaternionRotationArc(fwdVec, dirVec)
        matrix = geo2.MatrixAffineTransformation(1.0, geo2.Vector(0.0, 0.0, 0.0), rotation, parentPos)
        coordinates = []
        for step in xrange(numPoints):
            angle = step * stepSize
            x = cos(angle) * radius
            z = sin(angle) * radius
            pos = geo2.Vector(x, 0.0, z)
            pos = geo2.Vec3TransformCoord(pos, matrix)
            coordinates.append(pos)

        for start in xrange(numPoints):
            end = (start + 1) % numPoints
            lineSet.AddLine(coordinates[start], CIRCLE_COLOR, coordinates[end], CIRCLE_COLOR)

        lineSet.SubmitChanges()
        scene = sm.GetService('sceneManager').GetRegisteredScene('systemmap')
        if scene:
            scene.objects.append(lineSet)
        self.RegisterMapObject(result, lineSet)

    def CreatePointResult(self, result, translation):
        pointLocator = trinity.EveTransform()
        pointLocator.name = 'scanResult_' + result.id
        pointLocator.translation = translation
        pointLocator.display = 1
        if result.certainty >= probeResultPerfect:
            resultBracket = WarpableResultBracket()
        else:
            resultBracket = SimpleBracket()
        resultBracket.width = resultBracket.height = 16
        resultBracket.name = '__pointResultBracket'
        resultBracket.trackTransform = pointLocator
        resultBracket.resultID = result.id
        resultBracket.result = result
        resultBracket.invisible = False
        resultBracket.align = uiconst.ABSOLUTE
        resultBracket.state = uiconst.UI_NORMAL
        resultBracket.fadeColor = False
        resultBracket.displayName = self.scanSvc.GetDisplayName(result)
        resultBracket.groupID = None
        resultBracket.OnDblClick = (sm.GetService('systemmap').OnBracketDoubleClick, resultBracket)
        hint = self.scanSvc.GetScanGroupName(result)
        if result.typeID is not None:
            hint += ': %s' % self.scanSvc.GetTypeName(result)
        elif result.groupID is not None:
            hint += ': %s' % self.scanSvc.GetGroupName(result)
        resultBracket.hint = hint
        if 'scanresult' in GetHintsOnSolarsystemBrackets():
            resultBracket.ShowBubble(hint)
            resultBracket.showLabel = 0
        if result.certainty >= probeResultInformative:
            typeID = result.Get('typeID', None)
            groupID = result.groupID
            categoryID = None
        elif result.certainty >= probeResultGood:
            typeID = None
            groupID = result.Get('groupID', None)
            categoryID = cfg.invgroups.Get(result.groupID).categoryID
        else:
            typeID = None
            groupID = None
            categoryID = None
        iconNo, color = self.GetIconBasedOnQuality(categoryID, groupID, typeID, result.certainty)
        resultBracket.Startup(('result', result.id), groupID, categoryID, iconNo)
        resultBracket.sr.icon.color = color
        uicore.layer.systemMapBrackets.children.insert(0, resultBracket)
        parent = self.GetSystemParent()
        parent.children.append(pointLocator)
        self.RegisterMapObject(result, resultBracket)

    def GetIconBasedOnQuality(self, categoryID, groupID, typeID, certainty):
        if groupID in (groupCosmicAnomaly, groupCosmicSignature):
            props = POINT_ICON_DUNGEON
        elif categoryID == categoryShip and groupID is None:
            props = sm.GetService('bracket').GetMappedBracketProps(categoryShip, groupFrigate, None, default=POINT_ICON_PROPS)
        else:
            props = sm.GetService('bracket').GetMappedBracketProps(categoryID, groupID, typeID, default=POINT_ICON_PROPS)
        iconNo = props[0]
        if certainty >= probeResultPerfect:
            color = POINT_COLOR_GREEN
        elif certainty >= probeResultGood:
            color = POINT_COLOR_YELLOW
        else:
            color = POINT_COLOR_RED
        return (iconNo, color)

    def GetSystemParent(self, create = 1):
        """
        gets a solarsystem parent node where all results are added
        the node stays at the same place as the sun. This is done to
        make up for the fact that the world coordinates are relatice to space ship
        """
        if not create:
            return self.sr.systemParent
        if self.sr.systemParent is None:
            systemParent = trinity.EveTransform()
            systemParent.name = 'systemParent_%d' % session.solarsystemid2
            self.sr.systemParent = systemParent
        if sm.GetService('viewState').IsViewActive('systemmap'):
            currentSystem = sm.GetService('systemmap').GetCurrentSolarSystem()
            if self.sr.systemParent not in currentSystem.children:
                currentSystem.children.append(self.sr.systemParent)
        return self.sr.systemParent

    def CleanupResultShapes(self):
        """
        clean all cached result shapes and kill the systemParent while at it
        """
        bracketWnd = uicore.layer.systemMapBrackets
        for bracket in bracketWnd.children[:]:
            if bracket.name == '__pointResultBracket':
                bracket.trackTransform = None
                bracket.Close()

        parent = self.GetSystemParent(0)
        if parent:
            for model in parent.children[:]:
                if model.name.startswith('scanResult_'):
                    parent.children.remove(model)

        scene = sm.GetService('sceneManager').GetRegisteredScene('systemmap')
        if scene:
            for result in itertools.chain(*self.sr.resultObjectsByID.itervalues()):
                if result in scene.objects:
                    scene.objects.remove(result)

        self.sr.resultObjectsByID = {}

    def HighlightGoodResults(self):
        """
        Display all non range results returned
        """
        for entry in self.sr.resultscroll.GetNodes():
            if entry.Get('result', None) is not None:
                self.DisplayResult(entry.result)

    def Refresh(self):
        """
        Refresh is delayed 200 ms and the timer trigger reset if reset is 
        called with in that time.  This should prevent excessive refresh spamming
        when getting a bunch of events causing refresh at the same time.
        """
        self.sr.doRefresh = AutoTimer(200, self.DoRefresh)

    def DoRefresh(self):
        """
        refresh system map objects not owned my the map itself.
        called when system map in initialized.
        """
        sm.GetService('scanSvc').LogInfo('Scanner Refresh')
        sm.GetService('systemmap').LoadProbesAndScanResult_Delayed()
        self.UpdateProbeSpheres()
        self.CheckButtonStates()
        self.LoadProbeList()
        self.LoadFilterOptionsAndResults()
        self.sr.doRefresh = None

    def CreateLineSet(self):
        lineSet = trinity.EveLineSet()
        lineSet.effect = trinity.Tr2Effect()
        lineSet.effect.effectFilePath = LINESET_EFFECT
        lineSet.renderTransparent = False
        return lineSet

    def OnRefreshScanResults(self):
        self.Refresh()

    def ShowFilteredAndIgnored(self, filtered, ignored, filteredAnomalies):
        self.filteredLabel.text = localization.GetByLabel('UI/Inflight/Scanner/Filtered', noFiltered=filtered)
        self.ignoredLabel.text = localization.GetByLabel('UI/Inflight/Scanner/Ignored', noIgnored=ignored)

    def OnReconnectToProbesAvailable(self):
        self.CheckButtonStates()
