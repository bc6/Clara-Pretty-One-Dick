#Embedded file name: eve/client/script/ui/station/fitting\base_fitting.py
import math
import sys
from eve.client.script.ui.control.eveWindowUnderlay import RaisedUnderlay, WindowUnderlay
from eve.client.script.ui.inflight.shipstance import get_ship_stance
from eve.client.script.ui.station.fitting.stanceSlot import StanceSlots
from eveSpaceObject import shipanimation
from inventorycommon.util import IsModularShip, IsShipFittingFlag
import inventorycommon.const as invconst
import shipmode
import uiprimitives
import uicontrols
import uix
import uiutil
import mathUtil
import uthread
import blue
import util
from carbonui.primitives.container import Container
from carbonui.primitives.flowcontainer import FlowContainer
from carbonui.primitives.layoutGrid import LayoutGrid
import carbon.client.script.util.lg as lg
import log
import base
import trinity
import carbonui.const as uiconst
import uicls
import turretSet
import localization
import evegraphics.utils as gfxutils
from uthread2.callthrottlers import CallCombiner
from dogma.attributes.format import GetFormatAndValue
from eve.client.script.environment.t3shipSvc import NotEnoughSubSystems
from collections import defaultdict
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.scenecontainer import SceneContainer, SceneContainerBaseNavigation
from eve.client.script.ui.shared.fittingMgmtWindow import ViewFitting
from eve.client.script.ui.shared.export import ImportLegacyFittingsWindow
from eve.client.script.ui.shared.fittingMgmtWindow import FittingMgmt
from eve.client.script.ui.station.fitting.fittingTooltipUtils import SetFittingTooltipInfo
from eve.client.script.ui.station.fitting.slot import FittingSlot
from eve.client.script.ui.control.expandablemenu import ExpandableMenuContainer
from eve.client.script.ui.station.fitting.minihangar import CargoCargoSlots, CargoDroneSlots
from eve.client.script.ui.control.damageGaugeContainers import DamageGaugeContainerFitting
from eve.client.script.ui.tooltips.tooltipUtil import SetTooltipHeaderAndDescription
CONSTMAXSHIELDFRI = 350
CONSTMAXSHIELDCRU = 1500
CONSTMAXSHIELDBAT = 5000
CONSTMAXARMORFRI = 350
CONSTMAXARMORCRU = 1500
CONSTMAXARMORBAT = 5000
CONSTMAXSTRUCTUREFRI = 350
CONSTMAXSTRUCTURECRU = 1500
CONSTMAXSTRUCTUREBAT = 5000
PASSIVESHIELDRECHARGE = 0
SHIELDBOOSTRATEACTIVE = 1
ARMORREPAIRRATEACTIVE = 2
HULLREPAIRRATEACTIVE = 3
FONTCOLOR_HILITE = '<color=0xffffff00>'
FONTCOLOR_DEFAULT = '<color=0xc0ffffff>'
FONTCOLOR_HILITE2 = 4294967040L
FONTCOLOR_DEFAULT2 = 3238002687L
CALIBRATION_GAUGE_ZERO = 223.0
CALIBRATION_GAUGE_RANGE = 30.0
CALIBRATION_GAUGE_COLOR = (0.29296875, 0.328125, 0.33984375, 1.0)
CPU_GAUGE_ZERO = 45.0
CPU_GAUGE_RANGE = -45.0
CPU_GAUGE_COLOR = (0.203125, 0.3828125, 0.37890625, 1.0)
POWERGRID_GAUGE_ZERO = 45.0
POWERGRID_GAUGE_RANGE = 45.0
POWERGRID_GAUGE_COLOR = (0.40625, 0.078125, 0.03125, 1.0)
GAUGE_THICKNESS = 11
MAXDEFENCELABELWIDTH = 62
MAXDEFENCELABELHEIGHT = 32

class FittingWindow(uicontrols.Window):
    __guid__ = 'form.FittingWindow'
    __notifyevents__ = ['OnSetDevice', 'ProcessActiveShipChanged']
    default_width = 920
    default_height = 560
    default_windowID = 'fitting'
    default_captionLabelPath = 'Tooltips/StationServices/ShipFitting'
    default_descriptionLabelPath = 'Tooltips/StationServices/ShipFitting_description'
    default_iconNum = 'res:/ui/Texture/WindowIcons/fitting.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        self.HideHeaderFill()
        self.shipID = attributes.shipID
        self.ConstructLayout()

    def ConstructLayout(self):
        uix.Flush(self.sr.main)
        if eve.session.stationid:
            self.scope = 'station'
        else:
            self.scope = 'inflight'
        self.sr.fitting = Fitting(top=-8, parent=self.sr.main, shipID=self.shipID)
        self.sr.fitting.sr.wnd = self
        self.sr.fitting.Startup()
        self.clipChildren = 0
        self.sr.main.clipChildren = 0
        self.sr.maincontainer.clipChildren = 0

    def OnSetDevice(self):
        if self.shipID:
            uthread.new(self.ConstructLayout)

    def InitializeStatesAndPosition(self, *args, **kw):
        current = self.GetRegisteredPositionAndSize()
        default = self.GetDefaultSizeAndPosition()
        fixedWidth, fixedHeight = self._fixedWidth, self._fixedHeight
        uicontrols.Window.InitializeStatesAndPosition(self, *args, **kw)
        if fixedWidth is not None:
            self.width = fixedWidth
            self._fixedWidth = fixedWidth
        if fixedHeight is not None:
            self.height = fixedHeight
            self._fixedHeight = fixedHeight
        if list(default) == list(current)[:4]:
            settings.user.ui.Set('defaultFittingPosition', 1)
            dw = uicore.desktop.width
            dh = uicore.desktop.height
            self.left = (dw - self.width) / 2
            self.top = (dh - self.height) / 2
        self.MakeUnpinable()
        self.Unlock()
        uthread.new(uicore.registry.SetFocus, self)
        self._collapseable = 0

    def _OnClose(self, *args):
        settings.user.ui.Set('defaultFittingPosition', 0)

    def MouseDown(self, *args):
        uthread.new(uicore.registry.SetFocus, self)
        uiutil.SetOrder(self, 0)

    def HiliteFitting(self, item):
        uthread.new(self.sr.fitting.HiliteSlots, item)

    def ProcessActiveShipChanged(self, shipID, oldShipID):
        self.shipID = shipID

    def OnStartMinimize_(self, *args):
        self.sr.fitting.sr.sceneContainer.Hide()

    def OnEndMinimize_(self, *args):
        self.sr.fitting.sr.sceneContainer.Show()

    def OnMouseMove(self, *args):
        self.DisplayGaugeTooltips()

    def DisplayGaugeTooltips(self):
        """
            displaying cpu, powergrid and calibration tooltips
        """
        if not self.sr.fitting:
            return
        l, t, w, h = self.sr.fitting.GetAbsolute()
        cX = w / 2 + l
        cY = h / 2 + t
        x = uicore.uilib.x - cX
        y = uicore.uilib.y - cY
        length2 = pow(x, 2) + pow(y, 2)
        if length2 < pow(w / 2 - 20, 2):
            if y != 0:
                rad = math.atan(float(x) / float(y))
                degrees = 180 * rad / math.pi
            else:
                degrees = 90
            if x > 0:
                status = self.sr.fitting.GetStatusCpuPowerCalibr()
                if degrees > 0 and degrees < 45:
                    self.hint = localization.GetByLabel('UI/Fitting/FittingWindow/PowerGridState', state=status[1])
                elif degrees > 45 and degrees < 90:
                    self.hint = localization.GetByLabel('UI/Fitting/FittingWindow/CpuState', state=status[0])
                else:
                    self.hint = ''
            elif degrees > 47 and degrees < 77:
                status = self.sr.fitting.GetStatusCpuPowerCalibr()
                self.hint = localization.GetByLabel('UI/Fitting/FittingWindow/CalibrationState', state=status[2])
            else:
                self.hint = ''
        else:
            self.hint = ''

    def GetTooltipPosition(self):
        return (uicore.uilib.x - 5,
         uicore.uilib.y - 5,
         10,
         10)


class Fitting(uicls.FittingLayout):
    __notifyevents__ = ['ProcessActiveShipChanged',
     'OnStanceActive',
     'OnAttributes',
     'OnDogmaItemChange',
     'OnDogmaAttributeChanged',
     'OnItemNameChange',
     'OnCfgDataChanged',
     'OnStartSlotLinkingMode',
     'OnResetSlotLinkingMode',
     'OnAttributes',
     'OnAttribute',
     'OnUIScalingChange']
    __guid__ = 'form.Fitting'

    def ApplyAttributes(self, attributes):
        uicls.FittingLayout.ApplyAttributes(self, attributes)
        self._nohilitegroups = {const.groupRemoteSensorBooster: [const.attributeCpu, const.attributePower],
         const.groupRemoteSensorDamper: [const.attributeCpu, const.attributePower]}
        self.sr.colorPickerCookie = None
        self.Reset()
        self.CreateActiveShipModelThrottled = CallCombiner(self.CreateActiveShipModel, 1.0)
        shipID = attributes.shipID
        if shipID is None:
            self.shipID = session.shipid
        else:
            self.shipID = shipID
        self.dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        self.dogmaLocation.WaitForShip()
        self.updateStatsThread = None
        self.updateStatsArgs = (None, None)

    def GetShipAttribute(self, attributeID):
        if session.shipid == self.shipID:
            ship = sm.GetService('godma').GetItem(self.shipID)
            attributeName = self.dogmaLocation.dogmaStaticMgr.attributes[attributeID].attributeName
            return getattr(ship, attributeName)
        else:
            return self.dogmaLocation.GetAttributeValue(self.shipID, attributeID)

    def GetSensorStrengthAttribute(self):
        if session.shipid == self.shipID:
            return sm.GetService('godma').GetStateManager().GetSensorStrengthAttribute(self.shipID)
        else:
            return self.dogmaLocation.GetSensorStrengthAttribute(self.shipID)

    def Reset(self):
        self.slots = {}
        self.isDelayedAnim = False
        self.menuSlots = {}
        self.statusCpuPowerCalibr = [None, None, None]
        self.lastAddition = (0.0, 0.0, 0.0)
        self.initialized = False

    def _OnClose(self):
        uiprimitives.Container._OnClose(self)
        if self.sr.colorPickerCookie:
            uicore.event.UnregisterForTriuiEvents(self.sr.colorPickerCookie)
            self.sr.colorPickerCookie = None

    def OnDogmaItemChange(self, item, change):
        if self is None or self.destroyed or not hasattr(self, 'sr') or not self.initialized:
            return
        if const.ixStackSize not in change and const.ixFlag not in change and const.ixLocationID not in change:
            return
        oldLocationID = change.get(const.ixLocationID, None)
        if self.shipID not in (oldLocationID, item.locationID):
            return
        self.UpdateCapacitor()
        if item.groupID in const.turretModuleGroups:
            self.UpdateHardpoints()
        if (const.ixLocationID or const.ixFlag in change) and item.locationID == self.shipID and IsShipFittingFlag(item.flagID) and item.categoryID == const.categorySubSystem:
            self.ReloadShipModel(throttle=True)
            self.ReloadFitting(self.shipID)
        elif const.ixLocationID in change or const.ixFlag in change:
            self.ReloadFitting(self.shipID)

    def Startup(self):
        sm.RegisterNotify(self)
        self.state = uiconst.UI_PICKCHILDREN
        self.sr.slotParent = uiprimitives.Container(parent=self, name='slotParent', idx=0, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        uthread.new(self.Anim)

    def Anim(self):
        try:
            self._Anim()
        except:
            if self.destroyed:
                log.LogException(severity=log.LGWARN, toMsgWindow=0, toConsole=0)
                sys.exc_clear()
            else:
                raise

    def GetPositionForAngle(self, angle, centerX, centerY, rad, scaleFactor):
        cos = math.cos((angle - 90.0) * math.pi / 180.0)
        sin = math.sin((angle - 90.0) * math.pi / 180.0)
        width = int(round(44 * scaleFactor))
        height = int(round(54 * scaleFactor))
        left = int(round(rad * cos + centerX - width / 2.0))
        top = int(round(rad * sin + centerY - height / 2.0))
        return (left,
         top,
         width,
         height)

    def _Anim(self):
        toAnimate = []
        newslotParent = self.sr.slotParent
        uix.Flush(newslotParent)
        dw = uicore.desktop.width
        minWidth = 1400
        scaleFactor = min(1.0, max(0.75, dw / float(minWidth)))
        totalSidePanelsWidth = min(1200, max(960, dw - 120))
        self.sr.wnd.height = int(max(530, 560 * scaleFactor))
        self._scaleFactor = scaleFactor
        self._baseShapeSize = int(640 * scaleFactor)
        self._fullPanelWidth = 280
        self._centerOnlyWidth = self._baseShapeSize
        self._leftPanelWidth = 0
        self._rightPanelWidth = 0
        self.width = self._baseShapeSize
        self.height = self._baseShapeSize
        cX = cY = self._baseShapeSize / 2
        width = self._baseShapeSize
        settings.user.ui.Set('fittingPanelLeft', 0)
        if settings.user.ui.Get('fittingPanelRight', 1):
            width += self._fullPanelWidth
            self._rightPanelWidth = self._fullPanelWidth
            iconNo = 'ui_73_16_195'
            tooltipName = 'CollapseSidePane'
        else:
            iconNo = 'ui_73_16_196'
            tooltipName = 'ExpandSidePane'
        icon = uicontrols.Icon(icon=iconNo, parent=newslotParent, align=uiconst.CENTER, pos=(int(304 * scaleFactor),
         0,
         0,
         0))
        icon.OnClick = self.ToggleRight
        self.sr.toggleRightBtn = icon
        SetFittingTooltipInfo(self.sr.toggleRightBtn, tooltipName=tooltipName, includeDesc=False)
        self.sr.wnd.width = width
        self.UpdateCenterShapePosition()
        sceneContainerParent = uiprimitives.Container(parent=self, align=uiconst.CENTER, width=int(550 * scaleFactor), height=int(550 * scaleFactor))
        sc = SceneContainer(align=uiconst.TOALL, parent=sceneContainerParent, state=uiconst.UI_DISABLED)
        sc.PrepareCamera()
        sc.PrepareSpaceScene(scenePath='res:/dx9/scene/fitting/fitting.red')
        sc.SetStencilMap()
        self.sr.sceneContainer = sc
        nav = SceneContainerBaseNavigation(parent=sceneContainerParent, align=uiconst.TOALL, pos=(0, 0, 0, 0), idx=0, state=uiconst.UI_NORMAL, pickRadius=225 * scaleFactor)
        nav.Startup(sc)
        nav.OnDropData = self.OnDropData
        nav.GetMenu = self.GetShipMenu
        self.sr.sceneNavigation = nav
        rightside = uiprimitives.Container(name='rightside', parent=self.sr.wnd.sr.main, align=uiconst.TORIGHT, width=self._fullPanelWidth - 16, idx=0)
        rightside.padRight = 10
        rightside.padTop = 0
        rightside.padBottom = 10
        if not settings.user.ui.Get('fittingPanelRight', 1):
            rightside.opacity = 0.0
            rightside.state = uiconst.UI_DISABLED
        self.sr.rightPanel = rightside
        gapsize = 1.0
        numgaps = 4
        numslots = 32
        step = 360.0 / (numslots + numgaps * gapsize)
        rad = int(239 * scaleFactor)
        angle = 360.0 - 3.5 * step
        key = uix.FitKeys()
        i = 0
        for gidx in [0, 1, 2]:
            for sidx in xrange(8):
                if not self or self.destroyed:
                    return
                flag = getattr(const, 'flag%sSlot%s' % (key[gidx], sidx))
                cos = math.cos((angle - 90.0) * math.pi / 180.0)
                sin = math.sin((angle - 90.0) * math.pi / 180.0)
                width = int(round(44.0 * scaleFactor))
                height = int(round(54.0 * scaleFactor))
                left = int(round(rad * cos + cX - width / 2.0))
                top = int(round(rad * sin + cY - height / 2.0))
                nSlot = FittingSlot(name='slot_%s_%s' % (gidx, sidx), parent=newslotParent, pos=(left,
                 top,
                 width,
                 height), rotation=-mathUtil.DegToRad(angle), opacity=0.0)
                nSlot.scaleFactor = scaleFactor
                nSlot.radCosSin = (rad,
                 cos,
                 sin,
                 cX,
                 cY)
                angle += step
                if i + 1 in (8, 16):
                    angle += step * gapsize
                powerType = [const.effectHiPower, const.effectMedPower, const.effectLoPower][gidx]
                nSlot.gidx = gidx
                nSlot.Startup(flag, powerType, self.dogmaLocation, scaleFactor)
                toAnimate.append(nSlot)
                self.slots[flag] = nSlot
                i += 1

        gapsize = 0.333
        numgaps = 2
        numslots = 8
        step = 90.0 / (numslots + numgaps * gapsize)
        angle += step * (gapsize * 2.0)
        for i in xrange(5):
            if not self or self.destroyed:
                return
            i = 4 - i
            subsystemFlag = getattr(const, 'flagSubSystemSlot%s' % i, None)
            if not subsystemFlag:
                continue
            left, top, width, height = self.GetPositionForAngle(angle, cX, cY, rad, scaleFactor)
            cos = math.cos((angle - 90.0) * math.pi / 180.0)
            sin = math.sin((angle - 90.0) * math.pi / 180.0)
            nSlot = FittingSlot(name='subsystemSlot_%s' % i, parent=newslotParent, pos=(left,
             top,
             width,
             height), rotation=-mathUtil.DegToRad(angle), opacity=0.0)
            nSlot.scaleFactor = scaleFactor
            nSlot.radCosSin = (rad,
             cos,
             sin,
             cX,
             cY)
            nSlot.gidx = 3
            toAnimate.append(nSlot)
            nSlot.Startup(subsystemFlag, const.effectSubSystem, self.dogmaLocation, scaleFactor)
            angle += step
            self.slots[subsystemFlag] = nSlot

        angle += step * gapsize
        for i in xrange(3):
            rigFlag = getattr(const, 'flagRigSlot%s' % i, None)
            if not rigFlag:
                continue
            cos = math.cos((angle - 90.0) * math.pi / 180.0)
            sin = math.sin((angle - 90.0) * math.pi / 180.0)
            width = int(round(44.0 * scaleFactor))
            height = int(round(54.0 * scaleFactor))
            left = int(round(rad * cos + cX - width / 2.0))
            top = int(round(rad * sin + cY - height / 2.0))
            nSlot = FittingSlot(name='slot_%s_%s' % (gidx, sidx), parent=newslotParent, pos=(left,
             top,
             width,
             height), rotation=-mathUtil.DegToRad(angle), opacity=0.0)
            nSlot.scaleFactor = scaleFactor
            nSlot.radCosSin = (rad,
             cos,
             sin,
             cX,
             cY)
            nSlot.gidx = 4
            nSlot.Startup(rigFlag, const.effectRigSlot, self.dogmaLocation, scaleFactor)
            toAnimate.append(nSlot)
            angle += step
            self.slots[rigFlag] = nSlot

        self.stances = StanceSlots(parent=newslotParent, shipID=self.shipID, pos=(0, 0, 0, 0), angleToPos=lambda angle: self.GetPositionForAngle(angle, cX, cY, rad, scaleFactor))
        toAnimate.extend(self.stances.GetStanceContainers())
        powerGridAndCpuCont = LayoutGrid(parent=newslotParent, columns=1, state=uiconst.UI_PICKCHILDREN, align=uiconst.BOTTOMRIGHT, top=(self.height - self.sr.wnd.height) / 2 + 10, left=10)
        self.sr.cpu_statustextHeader = uicontrols.EveLabelMediumBold(text=localization.GetByLabel('UI/Fitting/FittingWindow/CPUStatusHeader'), name='cpu_statustextHeader', state=uiconst.UI_NORMAL, align=uiconst.TOPRIGHT)
        SetFittingTooltipInfo(targetObject=self.sr.cpu_statustextHeader, tooltipName='CPU')
        powerGridAndCpuCont.AddCell(self.sr.cpu_statustextHeader)
        self.sr.cpu_statustext = uicontrols.EveLabelMedium(text='', name='cpu_statustext', state=uiconst.UI_NORMAL, align=uiconst.TOPRIGHT)
        SetFittingTooltipInfo(targetObject=self.sr.cpu_statustext, tooltipName='CPU')
        powerGridAndCpuCont.AddCell(self.sr.cpu_statustext)
        powerGridAndCpuCont.AddCell(cellObject=Container(name='spacer', align=uiconst.TOTOP, height=10))
        self.sr.power_statustextHeader = uicontrols.EveLabelMediumBold(text=localization.GetByLabel('UI/Fitting/FittingWindow/PowergridHeader'), name='power_statustextHeader', state=uiconst.UI_NORMAL, align=uiconst.TOPRIGHT)
        SetFittingTooltipInfo(targetObject=self.sr.power_statustextHeader, tooltipName='PowerGrid')
        powerGridAndCpuCont.AddCell(self.sr.power_statustextHeader)
        self.sr.power_statustext = uicontrols.EveLabelMedium(text='', name='power_statustext', state=uiconst.UI_NORMAL, align=uiconst.TOPRIGHT)
        powerGridAndCpuCont.AddCell(self.sr.power_statustext)
        SetFittingTooltipInfo(targetObject=self.sr.power_statustext, tooltipName='PowerGrid')
        calibrationTop = (self.height - self.sr.wnd.height) / 2 + 50
        self.sr.calibrationstatustext = uicontrols.EveLabelMedium(text='', parent=newslotParent, name='calibrationstatustext', pos=(8,
         calibrationTop,
         0,
         0), idx=0, state=uiconst.UI_NORMAL)
        SetFittingTooltipInfo(targetObject=self.sr.calibrationstatustext, tooltipName='Calibration')
        self.sr.shipnamecont = uiprimitives.Container(name='shipname', parent=rightside, align=uiconst.TOTOP, height=12)
        self.sr.shipnamecont.padBottom = 6
        self.sr.shipnametext = uicontrols.EveLabelMedium(text='', parent=self.sr.shipnamecont, width=250, autoFitToText=True, state=uiconst.UI_NORMAL)
        SetTooltipHeaderAndDescription(targetObject=self.sr.shipnametext, headerText='', descriptionText=localization.GetByLabel('Tooltips/FittingWindow/ShipName_description'))
        self.sr.shipnametext.GetDragData = self.GetFittingDragData
        shipTypeID = self.GetShipDogmaItem().typeID
        self.sr.infolink = uicontrols.InfoIcon(typeID=shipTypeID, itemID=self.shipID, size=16, left=0, top=0, parent=self.sr.shipnamecont, idx=0)
        self.fittingSvcBtnGroup = FlowContainer(name='buttonParent', parent=rightside, align=uiconst.TOBOTTOM, padding=6, autoHeight=True, centerContent=True, contentSpacing=uiconst.BUTTONGROUPMARGIN)
        loadFittingBtn = Button(parent=self.fittingSvcBtnGroup, label=localization.GetByLabel('UI/Fitting/FittingWindow/Browse'), func=self.LoadFittingSetup, align=uiconst.NOALIGN)
        loadFittingBtn.hint = localization.GetByLabel('UI/Fitting/FittingWindow/BrowseTooltip')
        SetFittingTooltipInfo(targetObject=loadFittingBtn, tooltipName='BrowseSavedFittings', includeDesc=False)
        saveFittingBtn = Button(parent=self.fittingSvcBtnGroup, label=localization.GetByLabel('UI/Fitting/FittingWindow/Save'), func=self.SaveFittingSetup, align=uiconst.NOALIGN)
        saveFittingBtn.hint = localization.GetByLabel('UI/Fitting/FittingWindow/SaveTooltip')
        SetFittingTooltipInfo(targetObject=saveFittingBtn, tooltipName='SaveFitting', includeDesc=False)
        self.sr.stripBtn = Button(parent=self.fittingSvcBtnGroup, label=localization.GetByLabel('UI/Fitting/FittingWindow/StripFitting'), func=self.StripFitting, align=uiconst.NOALIGN)
        self.sr.stripBtn.hint = localization.GetByLabel('UI/Fitting/FittingWindow/StripFittingTooltip')
        SetFittingTooltipInfo(targetObject=self.sr.stripBtn, tooltipName='StripFitting', includeDesc=False)
        if not settings.user.ui.Get('fittingPanelRight', 1):
            self.fittingSvcBtnGroup.display = False
        self.sr.capacitorStatsParent = uiprimitives.Container(name='capacitorStatsParent')
        uicontrols.BumpedUnderlay(bgParent=self.sr.capacitorStatsParent)
        self.sr.capacitorHeaderStatsParent = uiprimitives.Container(name='capacitorHeaderStatsParent', parent=None, align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN, padRight=8, padTop=2)
        label = uicontrols.EveLabelMedium(parent=self.sr.capacitorHeaderStatsParent, state=uiconst.UI_NORMAL, align=uiconst.CENTERRIGHT, autoFadeSides=25)
        self.sr.capacitorHeaderStatsParent.sr.statusText = label
        self.sr.offenseStatsParent = uiprimitives.Container(name='offenseStatsParent')
        uicontrols.BumpedUnderlay(bgParent=self.sr.offenseStatsParent)
        self.sr.offenseHeaderStatsParent = uiprimitives.Container(name='offenseHeaderStatsParent', parent=None, align=uiconst.TORIGHT, state=uiconst.UI_PICKCHILDREN, width=200)
        label = uicontrols.EveLabelMedium(text='', parent=self.sr.offenseHeaderStatsParent, left=8, top=1, aidx=0, state=uiconst.UI_NORMAL, align=uiconst.CENTERRIGHT)
        label.hint = localization.GetByLabel('UI/Fitting/FittingWindow/ShipDpsTooltip')
        SetFittingTooltipInfo(targetObject=label, tooltipName='DamagePerSecond')
        self.sr.offenseHeaderStatsParent.sr.statusText = label
        self.sr.defenceStatsParent = uiprimitives.Container(name='defenceStatsParent')
        uicontrols.BumpedUnderlay(bgParent=self.sr.defenceStatsParent)
        self.sr.defenceHeaderStatsParent = uiprimitives.Container(name='defenceHeaderStatsParent', parent=None, align=uiconst.TORIGHT, state=uiconst.UI_PICKCHILDREN, width=200)
        label = uicontrols.EveLabelMedium(text='', parent=self.sr.defenceHeaderStatsParent, left=8, top=1, idx=0, state=uiconst.UI_NORMAL, align=uiconst.CENTERRIGHT)
        label.hint = localization.GetByLabel('UI/Fitting/FittingWindow/EffectiveHitpoints')
        SetFittingTooltipInfo(targetObject=label, tooltipName='EffectiveHitPoints')
        self.sr.defenceHeaderStatsParent.sr.statusText = label
        self.sr.targetingStatsParent = uiprimitives.Container(name='targetingStatsParent')
        uicontrols.BumpedUnderlay(bgParent=self.sr.targetingStatsParent)
        self.sr.targetingHeaderStatsParent = uiprimitives.Container(name='targetingHeaderStatsParent', parent=None, align=uiconst.TORIGHT, state=uiconst.UI_PICKCHILDREN, width=200)
        label = uicontrols.EveLabelMedium(text='', parent=self.sr.targetingHeaderStatsParent, left=8, top=1, aidx=0, state=uiconst.UI_NORMAL, align=uiconst.CENTERRIGHT)
        SetFittingTooltipInfo(targetObject=label, tooltipName='MaxTargetingRange')
        self.sr.targetingHeaderStatsParent.sr.statusText = label
        self.sr.navigationStatsParent = uiprimitives.Container(name='navigationStatsParent')
        uicontrols.BumpedUnderlay(bgParent=self.sr.navigationStatsParent)
        self.sr.navigationHeaderStatsParent = uiprimitives.Container(name='navigationHeaderStatsParent', parent=None, align=uiconst.TORIGHT, state=uiconst.UI_PICKCHILDREN, width=200)
        label = uicontrols.EveLabelMedium(text='', parent=self.sr.navigationHeaderStatsParent, left=8, top=1, aidx=0, state=uiconst.UI_NORMAL, align=uiconst.CENTERRIGHT)
        label.hint = localization.GetByLabel('UI/Fitting/FittingWindow/MaxVelocityHint')
        SetFittingTooltipInfo(targetObject=label, tooltipName='MaximumVelocity')
        self.sr.navigationHeaderStatsParent.sr.statusText = label
        em = ExpandableMenuContainer(parent=rightside, pos=(0, 0, 0, 0), clipChildren=True)
        em.multipleExpanded = True
        em.Load([(localization.GetByLabel('UI/Fitting/FittingWindow/Capacitor'),
          self.sr.capacitorStatsParent,
          self.LoadCapacitorStats,
          None,
          60,
          self.sr.capacitorHeaderStatsParent,
          False,
          True),
         (localization.GetByLabel('UI/Fitting/FittingWindow/Offense'),
          self.sr.offenseStatsParent,
          self.LoadOffenseStats,
          None,
          56,
          self.sr.offenseHeaderStatsParent,
          False,
          False),
         (localization.GetByLabel('UI/Fitting/FittingWindow/Defense'),
          self.sr.defenceStatsParent,
          self.LoadDefenceStats,
          None,
          150,
          self.sr.defenceHeaderStatsParent,
          False,
          False),
         (localization.GetByLabel('UI/Fitting/FittingWindow/Targeting'),
          self.sr.targetingStatsParent,
          self.LoadTargetingStats,
          None,
          84,
          self.sr.targetingHeaderStatsParent,
          False,
          False),
         (localization.GetByLabel('UI/Fitting/FittingWindow/Navigation'),
          self.sr.navigationStatsParent,
          self.LoadNavigationStats,
          None,
          84,
          self.sr.navigationHeaderStatsParent,
          False,
          False)], 'fittingRightside')
        angle = 306.0
        rad = int(310 * scaleFactor)
        attribute = cfg.dgmattribs.Get(const.attributeTurretSlotsLeft)
        cos = math.cos((180.0 - angle) * math.pi / 180.0)
        sin = math.sin((180.0 - angle) * math.pi / 180.0)
        left = int(round(rad * cos + cX - 16.0))
        top = int(round(rad * sin + cY - 16.0))
        turretHardpointName = attribute.displayName
        icon = uicontrols.Icon(name='turretSlotsLeft', icon='ui_26_64_1', parent=newslotParent, state=uiconst.UI_NORMAL, hint=attribute.displayName, pos=(left,
         top,
         32,
         32), ignoreSize=True)
        icon.LoadTooltipPanel = self.LoadTooltipPanelForTurret
        attribute = cfg.dgmattribs.Get(const.attributeLauncherSlotsLeft)
        cos = math.cos(angle * math.pi / 180.0)
        sin = math.sin(angle * math.pi / 180.0)
        left = int(round(rad * cos + cX - 16.0))
        top = int(round(rad * sin + cY - 16.0))
        launcherHardpointsName = attribute.displayName
        icon = uicontrols.Icon(name='missileLauncherSlotsLeft', icon='ui_81_64_16', parent=newslotParent, state=uiconst.UI_NORMAL, hint=attribute.displayName, pos=(left,
         top,
         32,
         32), ignoreSize=True)
        icon.LoadTooltipPanel = self.LoadTooltipPanelForLauncher
        step = 3.0 / scaleFactor
        rad = int(280 * scaleFactor)
        angle = 310.0 - step * 7.5
        self.sr.turretSlots = []
        self.sr.launcherSlots = []
        for i in xrange(8):
            cos = math.cos(angle * math.pi / 180.0)
            sin = math.sin(angle * math.pi / 180.0)
            left = int(round(rad * cos + cX) - 8)
            top = int(round(rad * sin + cY) - 8)
            icon = uiprimitives.Sprite(name='turret', texturePath='res:/UI/Texture/classes/Fitting/slotLeft.png', parent=newslotParent, pos=(left,
             top,
             16,
             16), hint=launcherHardpointsName)
            cos = math.cos((180.0 - angle) * math.pi / 180.0)
            sin = math.sin((180.0 - angle) * math.pi / 180.0)
            left = int(round(rad * cos + cX) - 8)
            top = int(round(rad * sin + cY) - 8)
            icon2 = uiprimitives.Sprite(name='launcher', texturePath='res:/UI/Texture/classes/Fitting/slotLeft.png', parent=newslotParent, pos=(left,
             top,
             16,
             16), hint=turretHardpointName)
            self.sr.launcherSlots.append(icon)
            self.sr.turretSlots.append(icon2)
            angle += step

        self.sr.turretSlots.reverse()
        self.sr.launcherSlots.reverse()
        cargoDroneCont = uiprimitives.Container(name='rightside', parent=newslotParent, align=uiconst.BOTTOMLEFT, width=110, height=64, left=const.defaultPadding)
        cargoDroneCont.top = (self.height - self.sr.wnd.height) / 2 + 6
        self.sr.cargoSlot = CargoCargoSlots(name='cargoSlot', parent=cargoDroneCont, align=uiconst.TOTOP, height=32, idx=-1)
        self.sr.cargoSlot.Startup(localization.GetByLabel('UI/Common/CargoHold'), 'ui_3_64_13', const.flagCargo, self.dogmaLocation)
        self.sr.cargoSlot.OnClick = uicore.cmd.OpenCargoHoldOfActiveShip
        self.sr.cargoSlot.state = uiconst.UI_NORMAL
        SetFittingTooltipInfo(self.sr.cargoSlot, 'CargoHold')
        self.sr.droneSlot = CargoDroneSlots(name='cargoSlot', parent=cargoDroneCont, align=uiconst.TOALL, pos=(0, 0, 0, 0), idx=-1)
        self.sr.droneSlot.Startup(localization.GetByLabel('UI/Common/DroneBay'), 'ui_11_64_16', const.flagDroneBay, self.dogmaLocation)
        self.sr.droneSlot.OnClick = uicore.cmd.OpenDroneBayOfActiveShip
        self.sr.droneSlot.state = uiconst.UI_NORMAL
        SetFittingTooltipInfo(self.sr.droneSlot, 'DroneBay')
        self.initialized = True
        uthread.new(self.ReloadFitting, session.shipid)
        uthread.new(self.ReloadShipModel)
        uthread.new(self.EntryAnimation, toAnimate)

    def ShowStanceButtons(self):
        self._HideSubSystemSlots()
        self.stances.display = True
        shipTypeID = self.GetShipDogmaItem().typeID
        self.stances.ShowStances(self.shipID, shipTypeID)

    def _HideSubSystemSlots(self):
        for flagID in xrange(invconst.flagSubSystemSlot0, invconst.flagSubSystemSlot5):
            self.slots[flagID].display = False

    def HideStanceButtons(self):
        self.stances.display = False

    def LoadTooltipPanelForTurret(self, tooltipPanel, *args):
        turretsFitted = self.GetHardpointsFitted(const.effectTurretFitted)
        turretSlotsLeft = self.GetShipAttribute(const.attributeTurretSlotsLeft)
        counterText = localization.GetByLabel('Tooltips/FittingWindow/TurretHardPointBubbles_description', hardpointsUsed=int(turretsFitted), hardpointsTotal=int(turretsFitted + turretSlotsLeft))
        return self.LoadTooltipPanelForTurretsAndLaunchers(tooltipPanel, const.attributeTurretSlotsLeft, counterText)

    def LoadTooltipPanelForLauncher(self, tooltipPanel, *args):
        turretsFitted = self.GetHardpointsFitted(const.effectLauncherFitted)
        turretSlotsLeft = self.GetShipAttribute(const.attributeLauncherSlotsLeft)
        counterText = localization.GetByLabel('Tooltips/FittingWindow/LauncherHardPointBubbles_description', hardpointsUsed=int(turretsFitted), hardpointsTotal=int(turretsFitted + turretSlotsLeft))
        return self.LoadTooltipPanelForTurretsAndLaunchers(tooltipPanel, const.attributeLauncherSlotsLeft, counterText)

    def LoadTooltipPanelForTurretsAndLaunchers(self, tooltipPanel, attributeID, counterText):
        attribute = cfg.dgmattribs.Get(attributeID)
        headerText = localization.GetByMessageID(attribute.tooltipTitleID)
        descriptionText = localization.GetByMessageID(attribute.tooltipDescriptionID)
        tooltipPanel.LoadGeneric2ColumnTemplate()
        tooltipPanel.AddLabelMedium(text=headerText, bold=True)
        tooltipPanel.AddLabelMedium(text=counterText, bold=True, align=uiconst.TOPRIGHT, cellPadding=(20, 0, 0, 0))
        tooltipPanel.AddLabelMedium(text=descriptionText, wrapWidth=200, colSpan=tooltipPanel.columns, color=(0.6, 0.6, 0.6, 1))

    def GetHardpointsFitted(self, effect):
        hardpointsFitted = 0
        ship = self.GetShipDogmaItem()
        for module in ship.GetFittedItems().itervalues():
            if self.dogmaLocation.dogmaStaticMgr.TypeHasEffect(module.typeID, effect):
                hardpointsFitted += 1

        return hardpointsFitted

    def GetFittingDragData(self, *args):
        fittingSvc = sm.StartService('fittingSvc')
        fitting = util.KeyVal()
        fitting.shipTypeID, fitting.fitData = fittingSvc.GetFittingDictForActiveShip()
        fitting.fittingID = None
        fitting.description = ''
        fitting.name = cfg.evelocations.Get(util.GetActiveShip()).locationName
        fitting.ownerID = 0
        entry = util.KeyVal()
        entry.fitting = fitting
        entry.label = fitting.name
        entry.displayText = fitting.name
        entry.__guid__ = 'listentry.FittingEntry'
        return [entry]

    def EntryAnimation(self, toAnimate):
        for obj in toAnimate:
            obj.opacity = 0.0

        for obj in toAnimate:
            sm.GetService('audio').SendUIEvent('wise:/msg_fittingSlotHi_play')
            endOpacity = 0.25 if obj.state == uiconst.UI_DISABLED else 1.0
            uicore.animations.FadeTo(obj, 0.0, endOpacity, duration=0.3)
            blue.synchro.SleepWallclock(5)

    def GetShipMenu(self, *args):
        if self.shipID is None:
            return []
        if session.stationid:
            hangarInv = sm.GetService('invCache').GetInventory(const.containerHangar)
            hangarItems = hangarInv.List()
            for each in hangarItems:
                if each.itemID == self.shipID:
                    return sm.GetService('menu').InvItemMenu(each)

        elif session.solarsystemid:
            return sm.GetService('menu').CelestialMenu(session.shipid)

    def SaveFittingSetup(self, *args):
        fittingSvc = sm.StartService('fittingSvc')
        fitting = util.KeyVal()
        fitting.shipTypeID, fitting.fitData = fittingSvc.GetFittingDictForActiveShip()
        fitting.fittingID = None
        fitting.description = ''
        fitting.name = cfg.evelocations.Get(util.GetActiveShip()).locationName
        fitting.ownerID = 0
        windowID = 'Save_ViewFitting_%s' % util.GetActiveShip()
        ViewFitting.Open(windowID=windowID, fitting=fitting, truncated=None)

    def LoadFittingSetup(self, *args):
        if sm.GetService('fittingSvc').HasLegacyClientFittings():
            wnd = ImportLegacyFittingsWindow.Open()
        else:
            wnd = FittingMgmt.Open()
        if wnd is not None and not wnd.destroyed:
            wnd.Maximize()

    def LoadNavigationStats(self, initialLoad = False):
        """
        Full reload of the navigation attribute panel
        """
        np = self.sr.navigationStatsParent
        uix.Flush(np)
        self.sr.navigationStatsParent.state = uiconst.UI_PICKCHILDREN
        toShow = ((const.attributeMass, const.attributeAgility), (const.attributeBaseWarpSpeed,))
        l, t, w, h = np.GetAbsolute()
        step = w / 2
        parentGrid = LayoutGrid(parent=np, columns=2, state=uiconst.UI_PICKCHILDREN, align=uiconst.TOTOP, padTop=-2)
        parentGrid.AddCell(cellObject=Container(name='spacer', align=uiconst.TOLEFT, width=step))
        parentGrid.AddCell(cellObject=Container(name='spacer', align=uiconst.TOLEFT, width=step))
        for attrGroup in toShow:
            for eachAttributeID in attrGroup:
                attribute = cfg.dgmattribs.Get(eachAttributeID)
                icon, label, cont = self.GetAttributeCont(attribute, parentGrid)
                self.sr.Set(('StatsLabel', attribute.attributeID), label)
                self.sr.Set(('StatsIcon', attribute.attributeID), icon)

        if not initialLoad:
            self.UpdateStats()

    def LoadTargetingStats(self, initialLoad = False):
        """
        Full reload of the targeting attribute panel
        """
        tp = self.sr.targetingStatsParent
        uix.Flush(tp)
        self.sr.targetingStatsParent.state = uiconst.UI_PICKCHILDREN
        sensorStrengthAttributeID, val = self.GetSensorStrengthAttribute()
        toShow = [('sensorStrength', const.attributeScanResolution), (const.attributeSignatureRadius, const.attributeMaxLockedTargets)]
        l, t, w, h = tp.GetAbsolute()
        step = w / 2
        parentGrid = LayoutGrid(parent=tp, columns=2, state=uiconst.UI_PICKCHILDREN, align=uiconst.TOTOP, padTop=-2)
        parentGrid.AddCell(cellObject=Container(name='spacer', align=uiconst.TOLEFT, width=step))
        parentGrid.AddCell(cellObject=Container(name='spacer', align=uiconst.TOLEFT, width=step))
        for attrGroup in toShow:
            for attributeID in attrGroup:
                if attributeID == 'sensorStrength':
                    each = sensorStrengthAttributeID
                else:
                    each = attributeID
                attribute = cfg.dgmattribs.Get(each)
                icon, label, cont = self.GetAttributeCont(attribute, parentGrid)
                tp.sr.Set(('StatsLabel', attributeID), label)
                tp.sr.Set(('StatsIcon', attributeID), icon)
                tp.sr.Set(('StatsCont', attributeID), cont)

        if not initialLoad:
            self.UpdateStats()

    def GetAttributeCont(self, attribute, parentGrid):
        iconSize = 32
        attributeCont = LayoutGrid(columns=3, state=uiconst.UI_NORMAL, align=uiconst.CENTERLEFT, padTop=1)
        parentGrid.AddCell(cellObject=attributeCont)
        attributeCont.AddCell()
        attributeCont.AddCell(cellObject=Container(name='widthSpacer', align=uiconst.TOLEFT, width=7 + iconSize))
        attributeCont.FillRow()
        attributeCont.AddCell(cellObject=Container(name='heightSpacer', align=uiconst.TOTOP, height=26))
        icon = uicontrols.Icon(graphicID=attribute.iconID, pos=(3,
         0,
         iconSize,
         iconSize), hint=attribute.displayName, name=attribute.displayName, ignoreSize=True, state=uiconst.UI_DISABLED)
        attributeCont.AddCell(cellObject=icon)
        label = uicontrols.EveLabelMedium(text='', left=0, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
        attributeCont.AddCell(cellObject=label)
        attributeCont.hint = attribute.displayName
        tooltipTitleID = attribute.tooltipTitleID
        if tooltipTitleID:
            tooltipTitle = localization.GetByMessageID(tooltipTitleID)
            tooltipDescr = localization.GetByMessageID(attribute.tooltipDescriptionID)
            SetTooltipHeaderAndDescription(targetObject=attributeCont, headerText=tooltipTitle, descriptionText=tooltipDescr)
        return (icon, label, attributeCont)

    def LoadOffenseStats(self, initialLoad = False):
        """
        Full reload of the offense attribute panel
        """
        op = self.sr.offenseStatsParent
        op.Flush()
        attributes = (('turretDps', 'res:/UI/Texture/Icons/26_64_1.png', 'UI/Fitting/FittingWindow/TurretDpsTooltip', 'DamagePerSecondTurrets'), ('droneDps', 'res:/UI/Texture/Icons/drones.png', 'UI/Fitting/FittingWindow/DroneDpsTooltip', 'DamagePerSecondDrones'), ('missileDps', 'res:/UI/Texture/Icons/81_64_16.png', 'UI/Fitting/FittingWindow/MissileDpsTooltip', 'DamagePerSecondMissiles'))
        iconSize = 26
        for i, (dps, texturePath, hintPath, tooltipName) in enumerate(attributes):
            hint = localization.GetByLabel(hintPath)
            c = uiprimitives.Container(parent=op, align=uiconst.TOLEFT_PROP, width=1.0 / len(attributes), height=20, state=uiconst.UI_NORMAL)
            icon = uiprimitives.Sprite(texturePath=texturePath, parent=c, align=uiconst.CENTERLEFT, pos=(5,
             0,
             iconSize,
             iconSize), state=uiconst.UI_DISABLED)
            SetFittingTooltipInfo(targetObject=c, tooltipName=tooltipName)
            c.hint = hint
            labelLeft = iconSize + 6
            label = uicontrols.EveLabelMedium(text='', parent=c, left=labelLeft, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
            op.sr.Set(('StatsLabel', dps), label)
            op.sr.Set(('StatsIcon', dps), icon)

        if not initialLoad:
            self.UpdateStats()
        self.UpdateOffenseStats()

    def UpdateOffenseStats(self):
        turretDps, missileDps = self.dogmaLocation.GetTurretAndMissileDps(self.shipID)
        label = self.sr.offenseStatsParent.sr.Get(('StatsLabel', 'turretDps'), None)
        if label:
            label.text = localization.GetByLabel('UI/Fitting/FittingWindow/DpsLabel', dps=turretDps)
        label = self.sr.offenseStatsParent.sr.Get(('StatsLabel', 'missileDps'), None)
        if label:
            label.text = localization.GetByLabel('UI/Fitting/FittingWindow/DpsLabel', dps=missileDps)
        droneDps, drones = self.dogmaLocation.GetOptimalDroneDamage(self.shipID)
        label = self.sr.offenseStatsParent.sr.Get(('StatsLabel', 'droneDps'), None)
        if label:
            label.text = localization.GetByLabel('UI/Fitting/FittingWindow/DpsLabel', dps=droneDps)
        totalDps = turretDps + missileDps + droneDps
        self.sr.offenseHeaderStatsParent.sr.statusText.text = localization.GetByLabel('UI/Fitting/FittingWindow/DpsLabel', dps=totalDps)

    def LoadDefenceStats(self, initialLoad = False):
        """
        Full reload of the defence attribute panel
        """
        col1Width = 90
        barColors = [(0.1, 0.37, 0.55, 1.0),
         (0.55, 0.1, 0.1, 1.0),
         (0.45, 0.45, 0.45, 1.0),
         (0.55, 0.37, 0.1, 1.0)]
        dsp = self.sr.defenceStatsParent
        uix.Flush(dsp)
        dsp.state = uiconst.UI_PICKCHILDREN
        tRow = uiprimitives.Container(name='topRow', parent=dsp, align=uiconst.TOTOP, height=32)
        self.sr.bestRepairPickerPanel = None
        bestPar = uiprimitives.Container(name='bestPar', parent=tRow, align=uiconst.TOPLEFT, height=32, width=col1Width, state=uiconst.UI_NORMAL, idx=0)
        bestPar.OnClick = self.ExpandBestRepair
        SetFittingTooltipInfo(targetObject=bestPar, tooltipName='ActiveDefenses')
        expandIcon = uicontrols.Icon(name='expandIcon', icon='ui_38_16_229', parent=bestPar, state=uiconst.UI_DISABLED, align=uiconst.BOTTOMRIGHT)
        numPar = uiprimitives.Container(name='numPar', parent=bestPar, width=11, height=11, top=17, left=4, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        numLabel = uicontrols.EveLabelMedium(text='', parent=numPar, atop=-1, state=uiconst.UI_DISABLED, align=uiconst.CENTER, shadowOffset=(0, 0))
        uiprimitives.Fill(parent=numPar, color=barColors[1])
        dsp.sr.Set('activeBestRepairNumLabel', numLabel)
        icon = uicontrols.Icon(parent=bestPar, state=uiconst.UI_DISABLED, width=32, height=32)
        statusLabel = uicontrols.Label(name='statusLabel', text='', parent=bestPar, left=icon.left + icon.width, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
        dsp.sr.Set('activeBestRepairLabel', statusLabel)
        dsp.sr.Set('activeBestRepairParent', bestPar)
        dsp.sr.Set('activeBestRepairIcon', icon)
        l, t, w, h = dsp.GetAbsolute()
        step = (w - col1Width) / 4
        resAttributeIDs = ((const.attributeEmDamageResonance, 'ResistanceHeaderEM'),
         (const.attributeThermalDamageResonance, 'ResistanceHeaderThermal'),
         (const.attributeKineticDamageResonance, 'ResistanceHeaderKinetic'),
         (const.attributeExplosiveDamageResonance, 'ResistanceHeaderExplosive'))
        left = col1Width
        for attributeID, tooltipName in resAttributeIDs:
            attribute = cfg.dgmattribs.Get(attributeID)
            icon = uicontrols.Icon(graphicID=attribute.iconID, parent=tRow, pos=(left + (step - 32) / 2 + 4,
             0,
             0,
             0), idx=0, hint=attribute.displayName)
            SetFittingTooltipInfo(icon, tooltipName=tooltipName, includeDesc=True)
            left += step

        for label, what, iconNo, labelhint, iconhint in ((localization.GetByLabel('UI/Common/Shield'),
          'shield',
          'ui_1_64_13',
          localization.GetByLabel('UI/Fitting/FittingWindow/ShieldHPAndRecharge'),
          ''), (localization.GetByLabel('UI/Common/Armor'),
          'armor',
          'ui_1_64_9',
          '',
          ''), (localization.GetByLabel('UI/Fitting/Structure'),
          'structure',
          'ui_2_64_12',
          '',
          '')):
            row = uiprimitives.Container(name='row_%s' % what, parent=dsp, align=uiconst.TOTOP, height=32)
            mainIcon = uicontrols.Icon(icon=iconNo, parent=row, pos=(0, 0, 32, 32), ignoreSize=True)
            mainIcon.hint = [label, iconhint][len(iconhint) > 0]
            statusLabel = uicontrols.Label(text='', parent=row, left=mainIcon.left + mainIcon.width, state=uiconst.UI_NORMAL, align=uiconst.CENTERLEFT, width=62)
            statusLabel.hint = [label, labelhint][len(labelhint) > 0]
            dsp.sr.Set('%sStatusText' % what, statusLabel)
            if what != 'effectiveHp':
                left = col1Width
                dmgContainer = uiprimitives.Container(parent=row, name='dmgContainer', left=col1Width)
                gaugeCont = DamageGaugeContainerFitting(parent=dmgContainer)
                dsp.sr.Set('%sDmgGaugeCont' % what, gaugeCont)

        dsp.children[0].padTop = 5
        if not initialLoad:
            self.UpdateStats()

    def LoadCapacitorStats(self, initialLoad = False):
        """
        Full reload of the capacitor attribute panel
        """
        uix.Flush(self.sr.capacitorStatsParent)
        left = 0
        self.sr.capacitorStatsParent.sr.powerCore = uiprimitives.Container(parent=self.sr.capacitorStatsParent, name='powercore', pos=(5, 5, 30, 30), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        csp = self.sr.capacitorStatsParent
        label = uicontrols.EveLabelMedium(text='', parent=csp, idx=0, state=uiconst.UI_NORMAL, top=5, left=45, align=uiconst.TOPLEFT)
        label.hint = localization.GetByLabel('UI/Fitting/FittingWindow/CapacityAndRechargeRate')
        self.sr.capacitorStatsParent.sr.statusText = label
        label = uicontrols.EveLabelMedium(text='', parent=csp, idx=0, state=uiconst.UI_NORMAL, top=22, left=45, align=uiconst.TOPLEFT)
        label.hint = localization.GetByLabel('UI/Fitting/FittingWindow/ExcessCapacitor')
        self.sr.capacitorStatsParent.sr.delta = label
        self.UpdateCapacitor(reload=1)
        if not initialLoad:
            self.UpdateStats()

    def UpdateStats(self, typeID = None, item = None):
        if typeID:
            typeOb = cfg.invtypes.Get(typeID)
            if not cfg.IsFittableCategory(typeOb.categoryID):
                return
        self.updateStatsArgs = (typeID, item)
        if self.updateStatsThread is not None:
            return
        self.updateStatsThread = uthread.pool('Fitting::UpdateStats', self._UpdateStats)

    def _UpdateStats(self):
        try:
            blue.pyos.synchro.SleepWallclock(100)
        finally:
            self.updateStatsThread = None

        typeID, item = self.updateStatsArgs
        if self is None or self.destroyed or not hasattr(self, 'sr') or not self.initialized:
            return
        if session.stationid2:
            if util.GetAttrs(self, 'sr', 'stripBtn'):
                self.sr.stripBtn.Enable()
        else:
            self.sr.stripBtn.Disable()
        xtraArmor = 0.0
        multiplyArmor = 1.0
        multiplyPower = 1.0
        xtraPower = 0.0
        xtraPowerload = 0.0
        multiplyCpu = 1.0
        xtraCpuLoad = 0.0
        xtraCpu = 0.0
        multiplyRecharge = 1.0
        xtraCapacitor = 0.0
        multiplyCapacitor = 1.0
        multiplyShieldRecharge = 1.0
        multiplyShieldCapacity = 1.0
        xtraShield = 0.0
        hpDrawback = 1.0
        multiplyStructure = 1.0
        xtraStructure = 0.0
        multiplyCargoCapacity = 1.0
        multiplySpeed = 1.0
        xtraSpeed = 0.0
        multiplyMaxTargetRange = 1.0
        maxLockedTargetsAdd = 0.0
        multiplyCalibration = 1.0
        xtraCalibrationLoad = 0.0
        xtraCalibrationOutput = 0.0
        xtraCargoSpace = 1.0
        xtraDroneSpace = 1.0
        multiplyResonance = {}
        multiplyResistance = {}
        sensorStrengthAttrs = [const.attributeScanRadarStrength,
         const.attributeScanMagnetometricStrength,
         const.attributeScanGravimetricStrength,
         const.attributeScanLadarStrength]
        sensorStrengthPercent = {}
        sensorStrengthPercentAttrs = [const.attributeScanRadarStrengthBonus,
         const.attributeScanMagnetometricStrengthBonus,
         const.attributeScanGravimetricStrengthBonus,
         const.attributeScanLadarStrengthBonus]
        sensorStrengthBonus = {}
        sensorStrengthBonusAttrs = [const.attributeScanRadarStrengthPercent,
         const.attributeScanMagnetometricStrengthPercent,
         const.attributeScanGravimetricStrengthPercent,
         const.attributeScanLadarStrengthPercent]
        ship = self.GetShipDogmaItem()
        turretsFitted = 0
        launchersFitted = 0
        modulesByGroupInShip = {}
        for module in ship.GetFittedItems().itervalues():
            if module.groupID not in modulesByGroupInShip:
                modulesByGroupInShip[module.groupID] = []
            modulesByGroupInShip[module.groupID].append(module)
            if self.dogmaLocation.dogmaStaticMgr.TypeHasEffect(module.typeID, const.effectLauncherFitted):
                launchersFitted += 1
            if self.dogmaLocation.dogmaStaticMgr.TypeHasEffect(module.typeID, const.effectTurretFitted):
                turretsFitted += 1

        typeAttributesByID = {}
        if typeID:
            for attribute in cfg.dgmtypeattribs.get(typeID, []):
                typeAttributesByID[attribute.attributeID] = attribute.value

            dgmAttr = sm.GetService('godma').GetType(typeID)
            asm = self.ArmorOrShieldMultiplier(typeID)
            asp = self.ArmorShieldStructureMultiplierPostPercent(typeID)
            mtr = self.MaxTargetRangeBonusMultiplier(typeID)
            doHilite = dgmAttr.groupID not in self._nohilitegroups
            allowedAttr = dgmAttr.displayAttributes
            for attribute in allowedAttr:
                if not doHilite and attribute.attributeID not in self._nohilitegroups[dgmAttr.groupID]:
                    continue
                if attribute.attributeID in sensorStrengthBonusAttrs:
                    sensorStrengthBonus[attribute.attributeID] = attribute
                elif attribute.attributeID in sensorStrengthPercentAttrs:
                    sensorStrengthPercent[attribute.attributeID] = attribute
                elif attribute.attributeID == const.attributeCapacityBonus:
                    xtraShield += attribute.value
                elif attribute.attributeID == const.attributeArmorHPBonusAdd:
                    xtraArmor += attribute.value
                elif attribute.attributeID == const.attributeStructureBonus:
                    xtraStructure += attribute.value
                elif attribute.attributeID == const.attributeCapacitorBonus:
                    xtraCapacitor += attribute.value
                elif attribute.attributeID == const.attributeCapacitorCapacityMultiplier:
                    multiplyCapacitor *= attribute.value
                elif attribute.attributeID == const.attributeCapacitorCapacityBonus:
                    multiplyCapacitor = 1 + attribute.value / 100
                elif attribute.attributeID == const.attributeCpuMultiplier:
                    multiplyCpu = attribute.value
                elif attribute.attributeID == const.attributeCpuOutput:
                    xtraCpu += attribute.value
                elif attribute.attributeID == const.attributePowerOutputMultiplier:
                    multiplyPower = attribute.value
                elif attribute.attributeID == const.attributePowerEngineeringOutputBonus:
                    multiplyPower = 1 + attribute.value / 100
                elif attribute.attributeID == const.attributeArmorHpBonus:
                    multiplyArmor += attribute.value / 100
                elif attribute.attributeID == const.attributeArmorHPMultiplier:
                    multiplyArmor = attribute.value
                elif attribute.attributeID == const.attributePowerIncrease:
                    xtraPower = attribute.value
                elif attribute.attributeID == const.attributePowerOutput:
                    xtraPower = attribute.value
                elif attribute.attributeID in (const.attributeCpuLoad, const.attributeCpu):
                    xtraCpuLoad += attribute.value
                elif attribute.attributeID in (const.attributePowerLoad, const.attributePower):
                    xtraPowerload += attribute.value
                elif attribute.attributeID == const.attributeUpgradeCost:
                    xtraCalibrationLoad = attribute.value
                elif attribute.attributeID == const.attributeCargoCapacityMultiplier:
                    xtraCargoSpace = attribute.value
                elif attribute.attributeID == const.attributeDroneCapacity:
                    xtraDroneSpace = attribute.value
                elif attribute.attributeID == const.attributeMaxVelocityBonus:
                    multiplySpeed = attribute.value
                elif asm is not None and attribute.attributeID == const.attributeEmDamageResonanceMultiplier:
                    multiplyResonance['%s_EmDamageResonance' % ['a', 's'][asm]] = attribute.value
                elif asm is not None and attribute.attributeID == const.attributeExplosiveDamageResonanceMultiplier:
                    multiplyResonance['%s_ExplosiveDamageResonance' % ['a', 's'][asm]] = attribute.value
                elif asm is not None and attribute.attributeID == const.attributeKineticDamageResonanceMultiplier:
                    multiplyResonance['%s_KineticDamageResonance' % ['a', 's'][asm]] = attribute.value
                elif asm is not None and attribute.attributeID == const.attributeThermalDamageResonanceMultiplier:
                    multiplyResonance['%s_ThermalDamageResonance' % ['a', 's'][asm]] = attribute.value
                elif asp and attribute.attributeID in (const.attributeEmDamageResistanceBonus,
                 const.attributeExplosiveDamageResistanceBonus,
                 const.attributeKineticDamageResistanceBonus,
                 const.attributeThermalDamageResistanceBonus):
                    groupName = {const.attributeEmDamageResistanceBonus: 'EmDamageResistance',
                     const.attributeExplosiveDamageResistanceBonus: 'ExplosiveDamageResistance',
                     const.attributeKineticDamageResistanceBonus: 'KineticDamageResistance',
                     const.attributeThermalDamageResistanceBonus: 'ThermalDamageResistance'}.get(attribute.attributeID, '')
                    if 'armor' in asp:
                        multiplyResistance['a_%s' % groupName] = attribute.value
                    if 'shield' in asp:
                        multiplyResistance['s_%s' % groupName] = attribute.value
                    if 'structure' in asp:
                        multiplyResistance['h_%s' % groupName] = attribute.value
                elif attribute.attributeID == const.attributeCapacitorRechargeRateMultiplier:
                    multiplyRecharge = multiplyRecharge * attribute.value
                elif attribute.attributeID == const.attributeCapRechargeBonus:
                    multiplyRecharge = 1 + attribute.value / 100
                elif attribute.attributeID == const.attributeShieldRechargeRateMultiplier:
                    multiplyShieldRecharge = attribute.value
                elif attribute.attributeID == const.attributeShieldCapacityMultiplier:
                    multiplyShieldCapacity *= attribute.value
                elif attribute.attributeID == const.attributeStructureHPMultiplier:
                    multiplyStructure = attribute.value
                elif attribute.attributeID == const.attributeCargoCapacityMultiplier:
                    multiplyCargoCapacity = attribute.value
                elif attribute.attributeID == const.attributeMaxTargetRangeMultiplier:
                    multiplyMaxTargetRange = attribute.value
                elif attribute.attributeID == const.attributeMaxLockedTargetsBonus:
                    maxLockedTargetsAdd += attribute.value
                elif mtr is not None and attribute.attributeID == const.attributeMaxTargetRangeBonus:
                    multiplyMaxTargetRange = abs(1.0 + attribute.value / 100.0)

        resAttrs = [const.attributeEmDamageResonance,
         const.attributeExplosiveDamageResonance,
         const.attributeKineticDamageResonance,
         const.attributeThermalDamageResonance]
        effectiveHp = 0.0
        effectiveHpColor = FONTCOLOR_DEFAULT2
        dsp = util.GetAttrs(self, 'sr', 'defenceStatsParent')
        if not dsp or dsp.destroyed:
            return
        resMap = {'structure': 'h',
         'armor': 'a',
         'shield': 's'}
        for what, label, attributeID, rechargeAttributeID, hpAddition, hpMultiplier in (('structure',
          dsp.sr.Get('structureStatusText', None),
          const.attributeHp,
          None,
          xtraStructure,
          multiplyStructure), ('armor',
          dsp.sr.Get('armorStatusText', None),
          const.attributeArmorHP,
          None,
          xtraArmor,
          multiplyArmor), ('shield',
          dsp.sr.Get('shieldStatusText', None),
          const.attributeShieldCapacity,
          1,
          xtraShield,
          multiplyShieldCapacity)):
            status = self.GetShipAttribute(attributeID)
            if not status:
                continue
            status = (status + hpAddition) * hpMultiplier
            dmgGaugeCont = dsp.sr.Get('%sDmgGaugeCont' % what, None)
            if label:
                color = self.GetColor(hpAddition, hpMultiplier)
                newText = color + localization.GetByLabel('UI/Fitting/FittingWindow/ColoredHp', hp=int(status)) + '</color>'
                if rechargeAttributeID is not None:
                    newText = localization.GetByLabel('UI/Fitting/FittingWindow/ColoredHitpointsAndRechargeTime', hp=int(status), rechargeTime=int(self.GetShipAttribute(const.attributeShieldRechargeRate) * multiplyShieldRecharge * 0.001), startColorTag1='<color=%s>' % hex(self.GetColor2(hpAddition, hpMultiplier)), startColorTag2='<color=%s>' % hex(self.GetMultiplyColor2(multiplyShieldRecharge)), endColorTag='</color>')
                    label.top = 2
                else:
                    newText = color + localization.GetByLabel('UI/Fitting/FittingWindow/ColoredHp', hp=int(status)) + '</color>'
                maxTextHeight = MAXDEFENCELABELHEIGHT
                maxTextWidth = MAXDEFENCELABELWIDTH
                textWidth, textHeight = label.MeasureTextSize(newText)
                fontsize = label.default_fontsize
                while textWidth > maxTextWidth or textHeight > maxTextHeight:
                    fontsize -= 1
                    textWidth, textHeight = label.MeasureTextSize(newText, fontsize=fontsize)

                label.fontsize = fontsize
                label.text = newText
            minResistance = 0.0
            for i, (dmgType, res) in enumerate([('em', 'EmDamageResonance'),
             ('explosive', 'ExplosiveDamageResonance'),
             ('kinetic', 'KineticDamageResonance'),
             ('thermal', 'ThermalDamageResonance')]):
                shipmod = '%s_%s' % (resMap[what], res)
                modmod = '%s_%s' % (resMap[what], res.replace('Resonance', 'Resistance'))
                multiplierShip = multiplyResonance.get(shipmod, 0.0)
                multiplierMod = multiplyResistance.get(modmod, 0.0)
                attribute = '%s%s' % ([what, ''][what == 'structure'], res)
                attribute = attribute[0].lower() + attribute[1:]
                attributeInfo = self.dogmaLocation.dogmaStaticMgr.attributesByName[attribute]
                attributeID = attributeInfo.attributeID
                value = self.GetShipAttribute(attributeID)
                if multiplierMod != 0.0:
                    effectiveHpColor = FONTCOLOR_HILITE2
                if value is not None:
                    value = value + value * multiplierMod / 100
                    if dsp.state != uiconst.UI_HIDDEN:
                        if dmgGaugeCont:
                            gaugeText = '<color=%s>' % hex(self.GetColor2(multiplierMod))
                            gaugeText += localization.GetByLabel('UI/Fitting/FittingWindow/ColoredResistanceLabel', number=100 - int(value * 100))
                            gaugeText += '</color>'
                            if attributeInfo.tooltipTitleID:
                                tooltipText = localization.GetByMessageID(attributeInfo.tooltipTitleID)
                            else:
                                tooltipText = cfg.dgmattribs.Get(attributeID).displayName
                            info = {'value': 1.0 - value,
                             'valueText': gaugeText,
                             'text': tooltipText,
                             'dmgType': dmgType}
                            dmgGaugeCont.UpdateGauge(info, animate=True)
                    minResistance = max(minResistance, value)

            if minResistance:
                effectiveHp += status / minResistance
            if hpMultiplier != 1.0 or hpAddition != 0.0:
                effectiveHpColor = FONTCOLOR_HILITE2

        coloredEffeciveHpLabel = '<color=%s>' % hex(effectiveHpColor)
        coloredEffeciveHpLabel += localization.GetByLabel('UI/Fitting/FittingWindow/ColoredEffectiveHp', color=hex(effectiveHpColor), effectiveHp=int(effectiveHp))
        coloredEffeciveHpLabel += '</color>'
        self.sr.defenceHeaderStatsParent.sr.statusText.text = coloredEffeciveHpLabel
        activeRepairLabel = dsp.sr.Get('activeBestRepairLabel', None)
        activeBestRepairParent = dsp.sr.Get('activeBestRepairParent', None)
        activeBestRepairNumLabel = dsp.sr.Get('activeBestRepairNumLabel', None)
        activeBestRepairIcon = dsp.sr.Get('activeBestRepairIcon', None)
        if activeRepairLabel:
            activeBestRepair = settings.user.ui.Get('activeBestRepair', PASSIVESHIELDRECHARGE)
            if activeBestRepair == PASSIVESHIELDRECHARGE:
                shieldCapacity = self.GetShipAttribute(const.attributeShieldCapacity)
                shieldRR = self.GetShipAttribute(const.attributeShieldRechargeRate)
                activeRepairText = '<color=%s>' % hex(self.GetMultiplyColor2(multiplyShieldRecharge))
                activeRepairText += localization.GetByLabel('UI/Fitting/FittingWindow/ColoredPassiveRepairRate', hpPerSec=int(2.5 * (shieldCapacity * multiplyShieldCapacity) / (shieldRR * multiplyShieldRecharge / 1000.0)))
                activeRepairText += '</color>'
                activeRepairLabel.text = activeRepairText
                activeBestRepairParent.hint = localization.GetByLabel('UI/Fitting/FittingWindow/PassiveShieldRecharge')
                activeBestRepairNumLabel.parent.state = uiconst.UI_HIDDEN
                activeBestRepairIcon.LoadIcon(cfg.dgmattribs.Get(const.attributeShieldCapacity).iconID, ignoreSize=True)
            else:
                dataSet = {ARMORREPAIRRATEACTIVE: (localization.GetByLabel('UI/Fitting/FittingWindow/ArmorRepairRate'),
                                         (const.groupArmorRepairUnit, const.groupFueledArmorRepairer),
                                         const.attributeArmorDamageAmount,
                                         'ui_1_64_11'),
                 HULLREPAIRRATEACTIVE: (localization.GetByLabel('UI/Fitting/FittingWindow/HullRepairRate'),
                                        (const.groupHullRepairUnit,),
                                        const.attributeStructureDamageAmount,
                                        'ui_1337_64_22'),
                 SHIELDBOOSTRATEACTIVE: (localization.GetByLabel('UI/Fitting/FittingWindow/ShieldBoostRate'),
                                         (const.groupShieldBooster, const.groupFueledShieldBooster),
                                         const.attributeShieldBonus,
                                         'ui_2_64_3')}
                hint, groupIDs, attributeID, iconNum = dataSet[activeBestRepair]
                activeBestRepairParent.hint = hint
                modules = []
                for groupID, modules2 in modulesByGroupInShip.iteritems():
                    if groupID in groupIDs:
                        modules.extend(modules2)

                color = FONTCOLOR_DEFAULT2
                if item and item.groupID in groupIDs:
                    modules += [item]
                    color = FONTCOLOR_HILITE2
                if modules:
                    data = self.CollectDogmaAttributes(modules, (const.attributeHp,
                     const.attributeShieldBonus,
                     const.attributeArmorDamageAmount,
                     const.attributeStructureDamageAmount,
                     const.attributeDuration))
                    durations = data.get(const.attributeDuration, None)
                    hps = data.get(attributeID, None)
                    if durations and hps:
                        commonCycleTime = None
                        for _ct in durations:
                            if commonCycleTime and _ct != commonCycleTime:
                                commonCycleTime = None
                                break
                            commonCycleTime = _ct

                        if commonCycleTime:
                            duration = commonCycleTime
                            activeRepairLabel.text = localization.GetByLabel('UI/Fitting/FittingWindow/ColoredHitpointsAndDuration', startColorTag='<color=%s>' % hex(color), endColorTag='</color>', hp=sum(hps), duration=duration / 1000.0)
                        else:
                            total = 0
                            for hp, ct in zip(hps, durations):
                                total += hp / (ct / 1000.0)

                            activeRepairText = '<color=%s>' % color
                            activeRepairText += localization.GetByLabel('UI/Fitting/FittingWindow/ColoredPassiveRepairRate', hpPerSec=total)
                            activeRepairText += '</color>'
                            activeRepairLabel.text = activeRepairText
                    activeBestRepairNumText = '<color=%s>' % color
                    activeBestRepairNumText += localization.GetByLabel('UI/Fitting/FittingWindow/ColoredBestRepairNumber', numberOfModules=len(modules))
                    activeBestRepairNumText += '</color>'
                    activeBestRepairNumLabel.bold = True
                    activeBestRepairNumLabel.text = activeBestRepairNumText
                    activeBestRepairNumLabel.parent.state = uiconst.UI_DISABLED
                else:
                    activeRepairLabel.text = localization.GetByLabel('UI/Fitting/FittingWindow/NoModule')
                    activeBestRepairNumLabel.text = localization.GetByLabel('UI/Fitting/FittingWindow/NoModuleNumber')
                    activeBestRepairNumLabel.parent.state = uiconst.UI_DISABLED
                activeBestRepairIcon.LoadIcon(iconNum, ignoreSize=True)
        turretAddition = 0
        launcherAddition = 0
        hiSlotAddition = 0
        medSlotAddition = 0
        lowSlotAddition = 0
        if self.shipID:
            godma = sm.StartService('godma')
            subSystemSlot = typeAttributesByID.get(const.attributeSubSystemSlot, None)
            if subSystemSlot is not None:
                slotOccupant = self.dogmaLocation.GetSubSystemInFlag(self.shipID, int(subSystemSlot))
                if slotOccupant is not None:
                    attributesByName = self.dogmaLocation.dogmaStaticMgr.attributesByName
                    GTA = lambda attributeID: self.dogmaLocation.dogmaStaticMgr.GetTypeAttribute2(slotOccupant.typeID, attributeID)
                    turretAddition = -GTA(attributesByName['turretHardPointModifier'].attributeID)
                    launcherAddition = -GTA(attributesByName['launcherHardPointModifier'].attributeID)
                    hiSlotAddition = -GTA(attributesByName['hiSlotModifier'].attributeID)
                    medSlotAddition = -GTA(attributesByName['medSlotModifier'].attributeID)
                    lowSlotAddition = -GTA(attributesByName['lowSlotModifier'].attributeID)
        turretAddition += typeAttributesByID.get(const.attributeTurretHardpointModifier, 0.0)
        turretSlotsLeft = self.GetShipAttribute(const.attributeTurretSlotsLeft)
        launcherAddition += typeAttributesByID.get(const.attributeLauncherHardPointModifier, 0.0)
        launcherSlotsLeft = self.GetShipAttribute(const.attributeLauncherSlotsLeft)
        for slotSet, slotsLeft, slotsFitted, slotsAddition, tooltipLoadFunc in [(self.sr.turretSlots,
          turretSlotsLeft,
          turretsFitted,
          turretAddition,
          self.LoadTooltipPanelForTurret), (self.sr.launcherSlots,
          launcherSlotsLeft,
          launchersFitted,
          launcherAddition,
          self.LoadTooltipPanelForLauncher)]:
            for i, slot in enumerate(slotSet):
                if i < slotsFitted:
                    slot.texturePath = 'res:/UI/Texture/classes/Fitting/slotTaken.png'
                else:
                    slot.texturePath = 'res:/UI/Texture/classes/Fitting/slotLeft.png'
                if i < slotsLeft + slotsFitted:
                    if i < slotsLeft + slotsFitted + slotsAddition:
                        slot.color.SetRGB(1.0, 1.0, 1.0, 0.7)
                    else:
                        slot.color.SetRGB(1.0, 0.0, 0.0, 0.7)
                    slot.state = uiconst.UI_NORMAL
                elif i < slotsLeft + slotsFitted + slotsAddition:
                    slot.color.SetRGB(1.0, 1.0, 0.0, 0.7)
                    slot.state = uiconst.UI_NORMAL
                else:
                    slot.state = uiconst.UI_HIDDEN
                slot.LoadTooltipPanel = tooltipLoadFunc

        hiSlotAddition += typeAttributesByID.get(const.attributeHiSlotModifier, 0.0)
        medSlotAddition += typeAttributesByID.get(const.attributeMedSlotModifier, 0.0)
        lowSlotAddition += typeAttributesByID.get(const.attributeLowSlotModifier, 0.0)
        self.ShowAddition(hiSlotAddition, medSlotAddition, lowSlotAddition)
        massLabel = self.sr.Get(('StatsLabel', const.attributeMass), None)
        if massLabel:
            massAddition = typeAttributesByID.get(const.attributeMassAddition, 0.0)
            mass = self.GetShipAttribute(const.attributeMass)
            value = int(mass + massAddition)
            color = self.GetXtraColor(massAddition)
            if value > 10000.0:
                value = value / 1000.0
                massLabel.text = color + localization.GetByLabel('UI/Fitting/FittingWindow/MassTonnes', mass=value)
            else:
                massLabel.text = color + localization.GetByLabel('UI/Fitting/FittingWindow/MassKg', mass=value)
        maxVelocityLabel = self.sr.navigationHeaderStatsParent.sr.statusText
        if maxVelocityLabel:
            xtraSpeed = typeAttributesByID.get(const.attributeSpeedBonus, 0.0) + typeAttributesByID.get(const.attributeMaxVelocity, 0.0)
            multiplyVelocity = typeAttributesByID.get(const.attributeVelocityModifier, None)
            if multiplyVelocity is not None:
                multiplyVelocity = 1 + multiplyVelocity / 100 * multiplySpeed
            else:
                multiplyVelocity = 1.0 * multiplySpeed
            maxVelocity = self.GetShipAttribute(const.attributeMaxVelocity)
            maxVelocityText = '<color=%s>' % hex(self.GetColor2(xtraSpeed, multiplyVelocity))
            maxVelocityText += localization.GetByLabel('UI/Fitting/FittingWindow/ColoredMaxVelocity', maxVelocity=(maxVelocity + xtraSpeed) * multiplyVelocity)
            maxVelocityText += '</color>'
            maxVelocityLabel.text = maxVelocityText
        agilityLabel = self.sr.Get(('StatsLabel', const.attributeAgility), None)
        if agilityLabel:
            agility = self.GetShipAttribute(const.attributeAgility)
            agilityLabel.text = localization.GetByLabel('UI/Fitting/FittingWindow/InertiaModifier', value=agility)
        baseWarpSpeedLabel = self.sr.Get(('StatsLabel', const.attributeBaseWarpSpeed), None)
        if baseWarpSpeedLabel:
            baseWarpSpeed = self.GetShipAttribute(const.attributeBaseWarpSpeed)
            warpSpeedMultiplier = self.GetShipAttribute(const.attributeWarpSpeedMultiplier)
            baseWarpSpeedLabel.text = localization.GetByLabel('UI/Fitting/FittingWindow/WarpSpeed', distText=util.FmtDist(baseWarpSpeed * warpSpeedMultiplier * const.AU, 2))
        maxTargetRange = self.GetShipAttribute(const.attributeMaxTargetRange)
        maxRange = maxTargetRange * multiplyMaxTargetRange / 1000.0
        headerText = self.GetMultiplyColor(multiplyMaxTargetRange)
        headerText += localization.GetByLabel('UI/Fitting/FittingWindow/TargetingHeader', startColorTag='', endColorTag='', maxRange=maxRange)
        headerHint = localization.GetByLabel('UI/Fitting/FittingWindow/TargetingHeaderHint')
        self.sr.targetingHeaderStatsParent.sr.statusText.text = headerText
        self.sr.targetingHeaderStatsParent.sr.statusText.hint = headerHint
        multiplyScanResolution = typeAttributesByID.get(const.attributeScanResolutionMultiplier, 1.0)
        if const.attributeScanResolutionBonus in typeAttributesByID:
            multiplyScanResolution *= 1 + typeAttributesByID[const.attributeScanResolutionBonus] / 100
        scanResolution = self.GetShipAttribute(const.attributeScanResolution)
        srt = self.GetMultiplyColor(multiplyScanResolution)
        srt += localization.GetByLabel('UI/Fitting/FittingWindow/ScanResolution', resolution=int(scanResolution * multiplyScanResolution))
        statsLabel = self.sr.targetingStatsParent.sr.Get(('StatsLabel', const.attributeScanResolution), None)
        if statsLabel:
            statsLabel.text = srt
        sensorStrengthAttributeID, maxSensorStrength = self.GetSensorStrengthAttribute()
        maxSensor = cfg.dgmattribs.Get(sensorStrengthAttributeID)
        attrIdx = sensorStrengthAttrs.index(maxSensor.attributeID)
        sensorBonusAttributeID = sensorStrengthBonusAttrs[attrIdx]
        sensorPercentAttributeID = sensorStrengthPercentAttrs[attrIdx]
        ssB = sensorStrengthBonus.get(sensorBonusAttributeID, None)
        ssP = sensorStrengthPercent.get(sensorPercentAttributeID, None)
        ssBValue = 1.0
        ssPValue = 1.0
        if ssB:
            ssBValue = 1.0 + ssB.value / 100.0
        if ssP:
            ssPValue = 1.0 + ssP.value / 100.0
        statsLabel = self.sr.targetingStatsParent.sr.Get(('StatsLabel', 'sensorStrength'), None)
        if statsLabel:
            statsText = self.GetColor(multi=(ssBValue + ssPValue) / 2.0)
            statsText += localization.GetByLabel('UI/Fitting/FittingWindow/SensorStrength', points=maxSensorStrength * ssBValue * ssPValue)
            statsLabel.text = statsText
            statsLabel.hint = maxSensor.displayName
        statsIcon = self.sr.targetingStatsParent.sr.Get(('StatsIcon', 'sensorStrength'), None)
        if statsIcon:
            statsIcon.hint = maxSensor.displayName
            statsIcon.LoadIcon(maxSensor.iconID, ignoreSize=True)
        statsCont = self.sr.targetingStatsParent.sr.Get(('StatsCont', 'sensorStrength'), None)
        if statsCont:
            sensorStrengthAttributeID, val = self.GetSensorStrengthAttribute()
            attribute = cfg.dgmattribs.Get(sensorStrengthAttributeID)
            tooltipTitleID = attribute.tooltipTitleID
            if tooltipTitleID:
                tooltipTitle = localization.GetByMessageID(tooltipTitleID)
                statsCont.tooltipPanelClassInfo.headerText = tooltipTitle
        signatureRadiusLabel = self.sr.targetingStatsParent.sr.Get(('StatsLabel', const.attributeSignatureRadius), None)
        if signatureRadiusLabel:
            signatureRadius = self.GetShipAttribute(const.attributeSignatureRadius)
            signatureRadiusAdd = typeAttributesByID.get(const.attributeSignatureRadiusAdd, 0.0)
            signatureRadiusText = self.GetXtraColor(signatureRadiusAdd)
            signatureRadiusText += localization.GetByLabel('UI/Fitting/FittingWindow/TargetingRange', range=signatureRadius + signatureRadiusAdd)
            signatureRadiusLabel.text = signatureRadiusText
        maxLockedTargetsLabel = self.sr.targetingStatsParent.sr.Get(('StatsLabel', const.attributeMaxLockedTargets), None)
        if maxLockedTargetsLabel:
            maxLockedTargets = self.GetShipAttribute(const.attributeMaxLockedTargets)
            maxLockedTargetsText = self.GetXtraColor(maxLockedTargetsAdd)
            maxLockedTargetsText += localization.GetByLabel('UI/Fitting/FittingWindow/MaxLockedTargets', maxTargets=int(maxLockedTargets + maxLockedTargetsAdd))
            maxLockedTargetsLabel.text = maxLockedTargetsText
        self.UpdateCapacitor(xtraCapacitor, multiplyRecharge, multiplyCapacitor, reload=1)
        self.UpdateCPUandPowerload(multiplyCpu, xtraCpuLoad, xtraCpu, xtraPower, multiplyPower, xtraPowerload)
        self.UpdateCalibration(multiplyCalibration, xtraCalibrationLoad, xtraCalibrationOutput)
        self.UpdateOffenseStats()
        self.UpdateCargoDroneInfo(xtraCargoSpace, xtraDroneSpace)

    def ShowAddition(self, h, m, l):
        if (h, m, l) == self.lastAddition:
            return
        self.lastAddition = (h, m, l)
        key = uix.FitKeys()
        for gidx, attributeID in enumerate((const.attributeHiSlots, const.attributeMedSlots, const.attributeLowSlots)):
            totalslots = self.GetShipAttribute(attributeID)
            add = [h, m, l][gidx]
            modslots = add + totalslots
            for sidx in xrange(8):
                flag = getattr(const, 'flag%sSlot%s' % (key[gidx], sidx))
                slot = self.slots[flag]
                if sidx < modslots:
                    if sidx >= totalslots:
                        slot.ColorUnderlay((1.0, 1.0, 0.0))
                        slot.Hilite(1)
                        slot.opacity = 1.0
                    else:
                        slot.ColorUnderlay()
                        if slot.state == uiconst.UI_DISABLED:
                            slot.opacity = 0.25
                        else:
                            slot.opacity = 1.0
                elif sidx >= totalslots:
                    slot.ColorUnderlay()
                    if slot.state == uiconst.UI_DISABLED:
                        slot.opacity = 0.25
                    else:
                        slot.opacity = 1.0
                else:
                    slot.ColorUnderlay((1.0, 0.0, 0.0))
                    slot.Hilite(1)
                    slot.opacity = 1.0

    def CollectDogmaAttributes(self, modules, attributes):
        ret = defaultdict(list)
        for module in modules:
            dogmaItem = self.dogmaLocation.dogmaItems.get(module.itemID, None)
            if dogmaItem and dogmaItem.locationID == self.shipID:
                for attributeID in attributes:
                    ret[attributeID].append(self.dogmaLocation.GetAccurateAttributeValue(dogmaItem.itemID, attributeID))

            else:
                for attributeID in attributes:
                    ret[attributeID].append(self.dogmaLocation.dogmaStaticMgr.GetTypeAttribute2(module.typeID, attributeID))

        return ret

    def UpdateCenterShapePosition(self):
        l, t, w, h = self.sr.wnd.GetAbsolute()
        lastLeft = getattr(self, '_lastLeftPanelWidth', None)
        self.sr.wnd.width = self._leftPanelWidth + self._baseShapeSize + self._rightPanelWidth
        if lastLeft is not None and lastLeft != self._leftPanelWidth:
            self.sr.wnd.left += lastLeft - self._leftPanelWidth
        self.left = self._leftPanelWidth
        self._lastLeftPanelWidth = self._leftPanelWidth
        self.sr.wnd._fixedWidth = self.sr.wnd.width
        self.sr.wnd._fixedHeight = self.sr.wnd.height

    def ToggleLeft(self, *args):
        current = settings.user.ui.Get('fittingPanelLeft', 1)
        settings.user.ui.Set('fittingPanelLeft', not current)
        uthread.new(self._ToggleSidePanel, 'left')

    def ToggleRight(self, *args):
        current = settings.user.ui.Get('fittingPanelRight', 1)
        settings.user.ui.Set('fittingPanelRight', not current)
        uthread.new(self._ToggleSidePanel, 'right')

    def _ToggleSidePanel(self, side):
        current = settings.user.ui.Get('fittingPanel%s' % side.capitalize(), 1)
        if current:
            endOpacity = 1.0
        else:
            endOpacity = 0.0
        panel = self.sr.Get('%sPanel' % side.lower(), None)
        btn = self.sr.Get('toggle%sBtn' % side.capitalize(), None)
        btn.state = uiconst.UI_DISABLED
        if side == 'left':
            begWidth = self._leftPanelWidth
            if current:
                self.sr.toggleLeftBtn.LoadIcon('ui_73_16_196')
            else:
                self.sr.toggleLeftBtn.LoadIcon('ui_73_16_195')
        else:
            begWidth = self._rightPanelWidth
            if current:
                self.sr.toggleRightBtn.LoadIcon('ui_73_16_195')
                self.sr.toggleRightBtn.tooltipPanelClassInfo.headerText = localization.GetByLabel('Tooltips/FittingWindow/CollapseSidePane')
            else:
                self.sr.toggleRightBtn.LoadIcon('ui_73_16_196')
                self.sr.toggleRightBtn.tooltipPanelClassInfo.headerText = localization.GetByLabel('Tooltips/FittingWindow/ExpandSidePane')
        if current:
            endWidth = self._fullPanelWidth
        else:
            endWidth = 0
        if panel:
            if endOpacity == 0.0:
                uicore.effect.MorphUI(panel, 'opacity', endOpacity, time=250.0, float=1, newthread=0)
                panel.state = uiconst.UI_DISABLED
                self.fittingSvcBtnGroup.display = False
            time = 250.0
            start = blue.os.GetWallclockTime()
            ndt = 0.0
            while ndt != 1.0:
                ndt = max(0.0, min(blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime()) / time, 1.0))
                if side == 'left':
                    self._leftPanelWidth = int(mathUtil.Lerp(begWidth, endWidth, ndt))
                else:
                    self._rightPanelWidth = int(mathUtil.Lerp(begWidth, endWidth, ndt))
                self.UpdateCenterShapePosition()
                blue.pyos.synchro.Yield()

            if endOpacity == 1.0:
                uicore.effect.MorphUI(panel, 'opacity', endOpacity, time=250.0, float=1)
                panel.state = uiconst.UI_PICKCHILDREN
                self.fittingSvcBtnGroup.display = True
        btn.state = uiconst.UI_NORMAL

    def RefreshChildren(self, parent):
        valid = [ each for each in parent.Find('trinity.Tr2Sprite2dContainer') if hasattr(each, '_OnResize') ]
        for each in valid:
            each._OnResize()

    def UpdateGauge(self, gauge, portion):
        l, t, w, h = gauge.parent.GetAbsolute()
        new = int(w * portion)
        uicore.effect.MorphUI(gauge, 'width', new, 100.0, ifWidthConstrain=0)

    def MaxTargetRangeBonusMultiplier(self, typeID):
        typeeffects = cfg.dgmtypeeffects.get(typeID, [])
        for effect in typeeffects:
            if effect.effectID in (const.effectShipMaxTargetRangeBonusOnline, const.effectmaxTargetRangeBonus):
                return 1

    def ArmorOrShieldMultiplier(self, typeID):
        typeeffects = cfg.dgmtypeeffects.get(typeID, [])
        for effect in typeeffects:
            if effect.effectID == const.effectShieldResonanceMultiplyOnline:
                return 1

    def ArmorShieldStructureMultiplierPostPercent(self, typeID):
        typeeffects = cfg.dgmtypeeffects.get(typeID, [])
        ret = []
        for effect in typeeffects:
            if effect.effectID == const.effectModifyArmorResonancePostPercent:
                ret.append('armor')
            elif effect.effectID == const.effectModifyShieldResonancePostPercent:
                ret.append('shield')
            elif effect.effectID == const.effectModifyHullResonancePostPercent:
                ret.append('structure')

        return ret

    def GetXtraColor(self, xtra):
        if xtra != 0.0:
            return FONTCOLOR_HILITE
        return FONTCOLOR_DEFAULT

    def GetMultiplyColor(self, multiply):
        if multiply != 1.0:
            return FONTCOLOR_HILITE
        return FONTCOLOR_DEFAULT

    def GetColor(self, xtra = 0.0, multi = 1.0):
        if multi != 1.0 or xtra != 0.0:
            return FONTCOLOR_HILITE
        return FONTCOLOR_DEFAULT

    def GetXtraColor2(self, xtra):
        if xtra != 0.0:
            return FONTCOLOR_HILITE2
        return FONTCOLOR_DEFAULT2

    def GetMultiplyColor2(self, multiply):
        if multiply != 1.0:
            return FONTCOLOR_HILITE2
        return FONTCOLOR_DEFAULT2

    def GetColor2(self, xtra = 0.0, multi = 1.0):
        if multi != 1.0 or xtra != 0.0:
            return FONTCOLOR_HILITE2
        return FONTCOLOR_DEFAULT2

    def UpdateCalibration(self, caliMultiply = 1.0, caliXtraLoad = 0.0, caliXtraCapacity = 0.0):
        if self.shipID is None:
            lg.Error('fitting', 'UpdateCalibration with no ship')
            return
        calibrationLoad = self.GetShipAttribute(const.attributeUpgradeLoad) + caliXtraLoad
        calibrationOutput = (self.GetShipAttribute(const.attributeUpgradeCapacity) + caliXtraCapacity) * caliMultiply
        portion = 0.0
        if calibrationLoad and calibrationOutput > 0:
            portion = max(0, min(1, calibrationLoad / calibrationOutput))
        self.sr.calibrationstatustext.text = localization.GetByLabel('UI/Fitting/FittingWindow/CalibrationStatusText', calibrationLoad=calibrationOutput - calibrationLoad, calibrationOutput=calibrationOutput, startColorTag1='<color=%s>' % hex(self.GetXtraColor2(caliXtraLoad)), startColorTag2='<color=%s>' % hex(self.GetMultiplyColor2(caliMultiply + caliXtraCapacity)), endColorTag='</color>')
        GAUGE_OUTERRAD = self.width * 0.89 / 2
        self.updateCalibrationStatusTimer = base.AutoTimer(10, self.UpdateStatusBar, 'calibration', self.sr.calibrationStatusPoly, radius=GAUGE_OUTERRAD - GAUGE_THICKNESS * self._scaleFactor, outerRadius=GAUGE_OUTERRAD, fromDeg=CALIBRATION_GAUGE_ZERO - CALIBRATION_GAUGE_RANGE * portion, toDeg=CALIBRATION_GAUGE_ZERO, innerColor=CALIBRATION_GAUGE_COLOR, outerColor=util.Color(*CALIBRATION_GAUGE_COLOR).SetAlpha(0.5).GetRGBA())
        if calibrationOutput > 0:
            status = 100.0 * float(calibrationLoad) / float(calibrationOutput)
            status = '%0.1f' % status
        else:
            status = ''
        self.statusCpuPowerCalibr[2] = status

    def UpdateCPUandPowerload(self, cpuMultiply = 1.0, xtraLoad = 0.0, xtraCpu = 0.0, xtraPower = 0.0, powerMultiply = 1.0, xtraPowerload = 0.0):
        if self.shipID is None:
            lg.Error('fitting', 'UpdateCPUAndPowerload with no ship')
            return
        if xtraCpu:
            skill = sm.GetService('skills').HasSkill(const.typeElectronics)
            if skill is not None:
                xtraCpu *= 1.0 + 0.05 * skill.skillLevel
        cpuLoad = self.GetShipAttribute(const.attributeCpuLoad) + xtraLoad
        cpuOutput = (self.GetShipAttribute(const.attributeCpuOutput) + xtraCpu) * cpuMultiply
        portion = 0.0
        if cpuLoad:
            if cpuOutput == 0:
                portion = 1
            else:
                portion = max(0, min(1, cpuLoad / cpuOutput))
        GAUGE_OUTERRAD = self.width * 0.89 / 2
        self.updateCpuStatusTimer = base.AutoTimer(10, self.UpdateStatusBar, 'cpu', self.sr.cpuStatusPoly, radius=GAUGE_OUTERRAD - GAUGE_THICKNESS * self._scaleFactor, outerRadius=GAUGE_OUTERRAD, fromDeg=CPU_GAUGE_ZERO + CPU_GAUGE_RANGE * portion, toDeg=CPU_GAUGE_ZERO, innerColor=CPU_GAUGE_COLOR, outerColor=util.Color(*CPU_GAUGE_COLOR).SetAlpha(0.5).GetRGBA())
        if cpuOutput > 0:
            status = 100.0 * float(cpuLoad) / float(cpuOutput)
            status = '%0.1f' % status
        else:
            status = ''
        self.statusCpuPowerCalibr[0] = status
        if xtraPower:
            skill = sm.GetService('skills').HasSkill(const.typeEngineering)
            if skill is not None:
                xtraPower *= 1.0 + 0.05 * skill.skillLevel
        powerLoad = self.GetShipAttribute(const.attributePowerLoad) + xtraPowerload
        output = (self.GetShipAttribute(const.attributePowerOutput) + xtraPower) * powerMultiply
        cpuText = localization.GetByLabel('UI/Fitting/FittingWindow/CpuStatusText', cpuLoad=cpuOutput - cpuLoad, cpuOutput=cpuOutput, startColorTag1='<color=%s>' % hex(self.GetXtraColor2(xtraLoad)), startColorTag2='<color=%s>' % hex(self.GetMultiplyColor2(cpuMultiply + xtraCpu)), endColorTag='</color>')
        powerText = localization.GetByLabel('UI/Fitting/FittingWindow/PowerStatusText', powerLoad=output - powerLoad, powerOutput=output, startColorTag3='<color=%s>' % hex(self.GetXtraColor2(xtraPowerload)), startColorTag4='<color=%s>' % hex(self.GetColor2(xtraPower, powerMultiply)), endColorTag='</color>')
        portion = 0.0
        if powerLoad:
            if output == 0.0:
                portion = 1.0
            else:
                portion = min(1.0, max(0.0, powerLoad / output))
        self.updatePowergridStatusTimer = base.AutoTimer(10, self.UpdateStatusBar, 'powergrid', self.sr.powergridStatusPoly, radius=GAUGE_OUTERRAD - GAUGE_THICKNESS * self._scaleFactor, outerRadius=GAUGE_OUTERRAD, toDeg=POWERGRID_GAUGE_ZERO, fromDeg=POWERGRID_GAUGE_ZERO + POWERGRID_GAUGE_RANGE * portion, innerColor=POWERGRID_GAUGE_COLOR, outerColor=util.Color(*POWERGRID_GAUGE_COLOR).SetAlpha(0.5).GetRGBA())
        if output > 0:
            status = 100.0 * float(powerLoad) / float(output)
            status = '%0.1f' % status
        else:
            status = ''
        self.statusCpuPowerCalibr[1] = status
        self.sr.cpu_statustext.text = cpuText
        self.sr.power_statustext.text = powerText

    def UpdateStatusBar(self, what, polyObject, radius, outerRadius, fromDeg, toDeg, innerColor, outerColor):
        if self.destroyed:
            return
        currentRotation = getattr(polyObject, 'currentFromDeg', toDeg)
        diff = abs(fromDeg - currentRotation)
        if diff < 0.0001:
            setattr(self, 'update%sStatusTimer' % what.capitalize(), None)
            currentRotation = fromDeg
        else:
            step = diff / 8.0
            if fromDeg > currentRotation:
                currentRotation += step
            else:
                currentRotation -= step
        polyObject.MakeArc(radius=radius * uicore.desktop.dpiScaling, outerRadius=outerRadius * uicore.desktop.dpiScaling, fromDeg=currentRotation, toDeg=toDeg, innerColor=innerColor, outerColor=outerColor)
        polyObject.currentFromDeg = currentRotation

    def GetStatusCpuPowerCalibr(self):
        return self.statusCpuPowerCalibr

    def UpdateCargoDroneInfo(self, xtraCargo, xtraDroneSpace):
        if not self or self.destroyed:
            return
        self.sr.cargoSlot.Update(xtraCargo)
        self.sr.droneSlot.Update(xtraDroneSpace)

    def UpdateCapacitor(self, xtraCapacitor = 0.0, rechargeMultiply = 1.0, multiplyCapacitor = 1.0, reload = 0):
        maxcap = (xtraCapacitor + self.GetShipAttribute(const.attributeCapacitorCapacity)) * multiplyCapacitor
        ccAttribute = cfg.dgmattribs.Get(const.attributeCapacitorCapacity)
        rrAttribute = cfg.dgmattribs.Get(const.attributeRechargeRate)
        rechargeRate = self.GetShipAttribute(const.attributeRechargeRate) * rechargeMultiply
        peakRechargeRate, totalCapNeed, loadBalance, TTL = self.dogmaLocation.CapacitorSimulator(self.shipID)
        if loadBalance > 0:
            sustainableText = '<color=0xff00ff00>'
            sustainableText += localization.GetByLabel('UI/Fitting/FittingWindow/Stable')
        else:
            sustainableText = '<color=0xffff0000>'
            sustainableText += localization.GetByLabel('UI/Fitting/FittingWindow/CapacitorNotStable', time=TTL)
        sustainableText += '</color>'
        self.sr.capacitorHeaderStatsParent.sr.statusText.text = sustainableText.replace('<br>', '')
        if self.sr.capacitorStatsParent.sr.Get('powerCore', None):
            if not reload and maxcap == getattr(self.sr.capacitorStatsParent, 'maxcap', None):
                return
            capText = localization.GetByLabel('UI/Fitting/FittingWindow/CapacitorCapAndRechargeTime', capacitorCapacity=GetFormatAndValue(ccAttribute, int(maxcap)), capacitorRechargeTime=GetFormatAndValue(rrAttribute, rechargeRate), startColorTag1='<color=%s>' % hex(self.GetColor2(xtraCapacitor, multiplyCapacitor)), startColorTag2='<color=%s>' % hex(self.GetMultiplyColor2(rechargeMultiply)), endColorTag='</color>')
            powerCore = self.sr.capacitorStatsParent.sr.powerCore
            powerCore.Flush()
            sustainabilityModified = False
            if xtraCapacitor > 0 or multiplyCapacitor != 1.0 or rechargeMultiply != 1.0:
                sustainabilityModified = True
            if loadBalance > 0:
                self.sr.capacitorHeaderStatsParent.sr.statusText.hint = localization.GetByLabel('UI/Fitting/FittingWindow/ModulesSustainable')
            else:
                self.sr.capacitorHeaderStatsParent.sr.statusText.hint = localization.GetByLabel('UI/Fitting/FittingWindow/ModulesNotSustainable')
            color = FONTCOLOR_DEFAULT
            if sustainabilityModified:
                color = FONTCOLOR_HILITE
            delta = color + localization.GetByLabel('UI/Fitting/FittingWindow/CapacitorDelta', delta=round((peakRechargeRate - totalCapNeed) * 1000, 2), percentage=round((peakRechargeRate - totalCapNeed) / peakRechargeRate * 100, 1))
            self.sr.capacitorStatsParent.sr.statusText.text = capText
            self.sr.capacitorStatsParent.sr.delta.text = delta
            numcol = min(10, int(maxcap / 50))
            rotstep = 360.0 / max(1, numcol)
            colWidth = max(12, min(16, numcol and int(192 / numcol)))
            colHeight = self.sr.capacitorStatsParent.sr.powerCore.height
            powerunits = []
            for i in range(numcol):
                powerColumn = uiprimitives.Transform(parent=powerCore, name='powerColumn', pos=(0,
                 0,
                 colWidth,
                 colHeight), align=uiconst.CENTER, state=uiconst.UI_DISABLED, rotation=mathUtil.DegToRad(i * -rotstep), idx=0)
                for ci in xrange(3):
                    newcell = uiprimitives.Sprite(parent=powerColumn, name='pmark', pos=(0,
                     ci * 4,
                     8 - ci * 2,
                     4), align=uiconst.CENTERTOP, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/capacitorCell.png', color=(0.94, 0.35, 0.19, 1.0), idx=0, blendMode=trinity.TR2_SBM_ADD)
                    powerunits.insert(0, newcell)

            self.sr.capacitorStatsParent.maxcap = maxcap
            self.capacitorDone = 1
            powerCore = self.sr.capacitorStatsParent.sr.powerCore
            bad = trinity.TriColor(70 / 256.0, 26 / 256.0, 13.0 / 256.0)
            good = trinity.TriColor(240 / 256.0, 90 / 256.0, 50.0 / 256.0)
            bad.Scale(1.0 - loadBalance)
            good.Scale(loadBalance)
            visible = max(0, min(len(powerunits), int(loadBalance * len(powerunits))))
            for ci, each in enumerate(powerunits):
                if ci >= visible:
                    each.SetRGB(0.25, 0.25, 0.25, 0.75)
                else:
                    each.SetRGB(bad.r + good.r, bad.g + good.g, bad.b + good.b, 1.0)

            if loadBalance == 0:
                self.sr.capacitorStatsParent.hint = localization.GetByLabel('UI/Fitting/FittingWindow/CapRunsOutBy', ttl=TTL)
            else:
                self.sr.capacitorStatsParent.hint = localization.GetByLabel('UI/Fitting/FittingWindow/CapSustainableBy', balance=loadBalance * 100)

    def DisableSlot(self, slot):
        slot.opacity = 0.25
        slot.state = uiconst.UI_DISABLED
        slot.sr.flagIcon.state = uiconst.UI_HIDDEN

    def StripFitting(self, *args):
        if eve.Message('AskStripShip', None, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            sm.GetService('invCache').GetInventoryFromId(self.shipID).StripFitting()
            uthread.new(self.ReloadFitting, self.shipID)

    def OnDropData(self, dragObj, nodes):
        for node in nodes:
            if node.Get('__guid__', None) in ('xtriui.InvItem', 'listentry.InvItem'):
                requiredSkills = sm.GetService('skills').GetRequiredSkills(node.rec.typeID)
                for skillID, level in requiredSkills.iteritems():
                    if getattr(sm.GetService('skills').HasSkill(skillID), 'skillLevel', 0) < level:
                        sm.GetService('tutorial').OpenTutorialSequence_Check(uix.skillfittingTutorial)
                        break

        recs = []
        for node in nodes:
            if getattr(node, 'rec', None):
                recs.append(node.rec)

        sm.GetService('menu').TryFit(recs)

    def OnActiveShipChange(self, shipid):
        uthread.new(self.ReloadFitting, shipid)

    def OnStartSlotLinkingMode(self, typeID, *args):
        """
            Gray out items that are not of the same type and therefore can't be linked
        """
        for flag, icon in self.slots.iteritems():
            if getattr(icon, 'module', None):
                if icon.module.typeID != typeID:
                    if hasattr(icon, 'color'):
                        icon.linkDragging = 1
                        icon.color.a = 0.1

    def OnResetSlotLinkingMode(self, *args):
        """
            set the items to the way they were before they were grayed out
        """
        for flag, icon in self.slots.iteritems():
            if getattr(icon, 'module', None):
                if getattr(icon, 'linkDragging', None):
                    icon.linkDragging = 0
                    if hasattr(icon, 'color'):
                        icon.color.a = 1.0

    def ReloadShipModel(self, throttle = False):
        if throttle:
            newModel = self.CreateActiveShipModelThrottled()
        else:
            newModel = self.CreateActiveShipModel()
        if newModel:
            if newModel.__bluetype__ == 'trinity.EveShip2' and not self.sr.sceneContainer.destroyed:
                newModel.FreezeHighDetailMesh()
                self.sr.sceneContainer.AddToScene(newModel)
                self.sr.sceneContainer.AnimEntry()
                camera = self.sr.sceneContainer.camera
                navigation = self.sr.sceneNavigation
                rad = newModel.GetBoundingSphereRadius()
                minZoom = rad + camera.frontClip
                alpha = camera.fieldOfView / 2.0
                maxZoom = rad * (1 / math.tan(alpha)) * 2
                zoom = minZoom / (maxZoom - minZoom)
                self.sr.sceneContainer.SetMinMaxZoom(minZoom, maxZoom)
                self.sr.sceneContainer.zoom = zoom
                shipTypeID = self.GetShipDogmaItem().typeID
                stanceID = get_ship_stance(self.shipID, shipTypeID)
                shipanimation.SetUpAnimation(newModel, stanceID, trinity)

    def GetShipDogmaItem(self):
        return self.dogmaLocation.dogmaItems[self.shipID]

    def CreateActiveShipModel(self):
        ship = self.GetShipDogmaItem()
        try:
            if IsModularShip(ship.typeID):
                try:
                    newModel = sm.GetService('t3ShipSvc').MakeModularShipFromShipItem(self.GetShipDogmaItem())
                except NotEnoughSubSystems:
                    log.LogInfo('CreateAndActiveShipModel - Not enough subsystems do display ship in fittingWindow')
                    return
                except:
                    log.LogException('failed bulding modular ship')
                    sys.exc_clear()
                    return

            else:
                modelDNA = gfxutils.BuildSOFDNAFromTypeID(ship.typeID)
                if modelDNA is not None:
                    spaceObjectFactory = sm.GetService('sofService').spaceObjectFactory
                    newModel = spaceObjectFactory.BuildFromDNA(modelDNA)
        except Exception as e:
            log.LogException(str(e))
            sys.exc_clear()

        if hasattr(newModel, 'ChainAnimationEx'):
            newModel.ChainAnimationEx('NormalLoop', 0, 0, 1.0)
        newModel.display = 1
        newModel.name = str(ship.itemID)
        self.UpdateHardpoints(newModel)
        return newModel

    def UpdateHardpoints(self, newModel = None):
        if newModel is None:
            newModel = self.GetSceneShip()
        if newModel is None:
            log.LogError('UpdateHardpoints - No model!')
            return
        turretSet.TurretSet.FitTurrets(self.shipID, newModel)

    def ReloadFitting(self, shipID):
        cfg.evelocations.Prime([self.shipID])
        try:
            self.GetFitting()
        except:
            if self.destroyed:
                log.LogException(severity=log.LGWARN, toMsgWindow=0, toConsole=0)
                sys.exc_clear()
            else:
                raise

        self.UpdateStats()

    def IsCharge(self, typeID):
        return cfg.invtypes.Get(typeID).Group().Category().id in (const.categoryCharge, const.groupFrequencyCrystal)

    def OnCfgDataChanged(self, cfgname, entry, *args):
        if cfgname == 'evelocations' and entry[0] == self.shipID:
            self.sr.shipnametext.text = entry[1]
            self.sr.shipnametext.tooltipPanelClassInfo.headerText = entry[1]

    def GetFitting(self):
        key = uix.FitKeys()
        shipName = cfg.evelocations.Get(self.shipID).name
        ship = self.dogmaLocation.dogmaItems[self.shipID]
        typeName = cfg.invtypes.Get(ship.typeID).typeName
        label = shipName
        self.sr.shipnametext.text = label
        self.sr.shipnametext.tooltipPanelClassInfo.headerText = label
        oneLineHeight = self.sr.shipnamecont.height
        lines = max(1, self.sr.shipnametext.height / max(1, self.sr.shipnamecont.height))
        margin = 3
        self.sr.shipnamecont.height = lines * oneLineHeight + margin * (lines - 1)
        self.sr.shipnametext.hint = typeName
        self.sr.infolink.left = self.sr.shipnametext.textwidth + 6
        if self.sr.infolink.left + 50 > self.sr.shipnamecont.width:
            self.sr.infolink.left = 0
            self.sr.infolink.SetAlign(uiconst.TOPRIGHT)
        self.sr.infolink.UpdateInfoLink(ship.typeID, ship.itemID)
        modulesByFlag = {}
        for module in ship.GetFittedItems().itervalues():
            modulesByFlag[module.flagID, self.IsCharge(module.typeID)] = module

        for gidx, attributeID in enumerate((const.attributeHiSlots, const.attributeMedSlots, const.attributeLowSlots)):
            totalslots = self.GetShipAttribute(attributeID)
            for sidx in xrange(8):
                flag = getattr(const, 'flag%sSlot%s' % (key[gidx], sidx))
                slot = self.slots[flag]
                slot.state = uiconst.UI_NORMAL
                module = modulesByFlag.get((flag, 0), None)
                if module:
                    slot.SetFitting(module, self.dogmaLocation)
                elif sidx >= totalslots:
                    slot.SetFitting(None, self.dogmaLocation)
                    self.DisableSlot(slot)
                    continue
                else:
                    slot.SetFitting(None, self.dogmaLocation)
                charge = modulesByFlag.get((flag, 1), None)
                if charge:
                    slot.SetFitting(charge, self.dogmaLocation)
                for charge in self.dogmaLocation.GetSublocations(self.shipID):
                    if charge.flagID == flag:
                        slot.SetFitting(charge, self.dogmaLocation)

        totalRigSlots = self.GetShipAttribute(const.attributeRigSlots)
        for i in xrange(3):
            rigFlag = getattr(const, 'flagRigSlot%s' % i, None)
            slot = self.GetSlot(rigFlag)
            if not slot:
                continue
            if i >= totalRigSlots:
                self.DisableSlot(slot)
            else:
                module = modulesByFlag.get((rigFlag, 0), None)
                slot.SetFitting(module, self.dogmaLocation)

        ship = self.GetShipDogmaItem()
        showSubsystems = IsModularShip(ship.typeID)
        for i in xrange(5):
            subsystemFlag = getattr(const, 'flagSubSystemSlot%s' % i, None)
            slot = self.GetSlot(subsystemFlag)
            if not slot:
                continue
            module = modulesByFlag.get((subsystemFlag, 0), None)
            slot.SetFitting(module)
            if not showSubsystems:
                self.DisableSlot(slot)

        shipTypeID = self.GetShipDogmaItem().typeID
        if shipmode.ship_has_stances(shipTypeID):
            self.ShowStanceButtons()
        else:
            self.HideStanceButtons()

    def GetSlot(self, flag):
        if self.slots.has_key(flag):
            return self.slots[flag]

    def HiliteSlots(self, item):
        if self.destroyed:
            return
        hiliteSlotFlag = None
        powerType = None
        typeID = None
        if item:
            typeID = item.typeID
            if typeID in cfg.dgmtypeattribs:
                for attribute in cfg.dgmtypeattribs[typeID]:
                    if attribute.attributeID == const.attributeSubSystemSlot:
                        hiliteSlotFlag = int(attribute.value)
                        break

            if hiliteSlotFlag is None:
                if typeID in cfg.dgmtypeeffects:
                    for effect in cfg.dgmtypeeffects[typeID]:
                        if effect.effectID in [const.effectHiPower,
                         const.effectMedPower,
                         const.effectLoPower,
                         const.effectSubSystem,
                         const.effectRigSlot]:
                            powerType = effect.effectID
                            break

            if self.IsCharge(typeID):
                pass
        for slot in self.slots.itervalues():
            if hiliteSlotFlag is None and powerType is None:
                if slot.id is None:
                    slot.Hilite(0)
            elif slot.state != uiconst.UI_DISABLED and slot.id is None:
                if powerType is not None and slot.powerType == powerType:
                    slot.Hilite(1)
                if hiliteSlotFlag is not None and slot.locationFlag == hiliteSlotFlag:
                    slot.Hilite(1)

        self.UpdateStats(typeID, item)

    def OnDogmaAttributeChanged(self, shipID, itemID, attributeID, value):
        if shipID == self.shipID:
            self.UpdateStats()
            if attributeID == const.attributeIsOnline:
                uthread.pool('Fitting::OnDogmaAttributeChanged', self.ProcessOnlineStateChange, itemID, value)
        if attributeID in (const.attributeIsOnline, const.attributeQuantity):
            try:
                dogmaItem = self.dogmaLocation.GetDogmaItem(itemID)
                flagID = dogmaItem.flagID
            except KeyError:
                if isinstance(itemID, tuple) and itemID[0] == self.shipID:
                    flagID = itemID[1]
                else:
                    return

            try:
                self.slots[flagID].OnDogmaAttributeChanged(shipID, itemID, attributeID, value)
            except KeyError:
                pass

    def ProcessOnlineStateChange(self, itemID, value):
        try:
            dogmaItem = self.dogmaLocation.GetDogmaItem(itemID)
        except KeyError:
            return

        slot = dogmaItem.flagID - const.flagHiSlot0 + 1
        if slot is not None:
            sceneShip = self.GetSceneShip()
            for turret in sceneShip.turretSets:
                if turret.slotNumber == slot:
                    if dogmaItem.IsOnline():
                        turret.EnterStateIdle()
                    else:
                        turret.EnterStateDeactive()

    def OnAttribute(self, attributeName, item, value, updateStats = 1):
        try:
            self.GetService('godma').GetItem(item.itemID)
        except AttributeError:
            sys.exc_clear()
            return

        if updateStats:
            self.UpdateStats()

    def OnAttributes(self, changeList):
        if self is None or self.destroyed or not hasattr(self, 'sr') or not self.initialized:
            return
        reanimate = False
        for attributeName, item, value in changeList:
            self.OnAttribute(attributeName, item, value, 0)
            if attributeName in ('hiSlots', 'medSlots', 'lowSlots'):
                reanimate = True

        self.UpdateStats()
        if reanimate:
            uthread.new(self.DelayedAnim)

    def DelayedAnim(self):
        if self.isDelayedAnim:
            return
        self.isDelayedAnim = True
        try:
            blue.pyos.synchro.SleepWallclock(500)
            uthread.new(self.GetFitting)
        finally:
            self.isDelayedAnim = False

    def ProcessActiveShipChanged(self, shipID, oldShipID):
        self.OnActiveShipChange(shipID)
        self.shipID = shipID
        self.ReloadShipModel()
        self.UpdateStats()
        self.LoadCapacitorStats()

    def OnStanceActive(self, shipID, stanceID):
        shipanimation.TriggerStanceAnimation(self.GetSceneShip(), stanceID)

    def OnUIScalingChange(self, *args):
        FittingWindow.CloseIfOpen()
        FittingWindow.Open()

    def RegisterForMouseUp(self):
        self.sr.colorPickerCookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEUP, self.OnGlobalMouseUp)

    def OnGlobalMouseUp(self, fromwhere, *etc):
        if self.sr.colorPickerPanel:
            if uicore.uilib.mouseOver == self.sr.colorPickerPanel or uiutil.IsUnder(fromwhere, self.sr.colorPickerPanel) or fromwhere == self.sr.colorPickers[self._expandedColorIdx]:
                log.LogInfo('Combo.OnGlobalClick Ignoring all clicks from comboDropDown')
                return 1
        if self.sr.colorPickerPanel and not self.sr.colorPickerPanel.destroyed:
            self.sr.colorPickerPanel.Close()
        self.sr.colorPickerPanel = None
        if self.sr.colorPickerCookie:
            uicore.event.UnregisterForTriuiEvents(self.sr.colorPickerCookie)
        self.sr.colorPickerCookie = None
        return 0

    def ExpandBestRepair(self, *args):
        if self.sr.bestRepairPickerPanel is not None:
            self.PickBestRepair(None)
            return
        self.sr.bestRepairPickerCookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEUP, self.OnGlobalMouseUp_BestRepair)
        bestRepairParent = self.sr.defenceStatsParent.sr.activeBestRepairParent
        l, t, w, h = bestRepairParent.GetAbsolute()
        wl, wt, ww, wh = self.sr.wnd.GetAbsolute()
        bestRepairPickerPanel = uiprimitives.Container(parent=self.sr.wnd, name='bestRepairPickerPanel', align=uiconst.TOPLEFT, width=150, height=100, left=l - wl, top=t - wt + h, state=uiconst.UI_NORMAL, idx=0, clipChildren=1)
        subpar = uiprimitives.Container(parent=bestRepairPickerPanel, name='subpar', align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN, pos=(0, 0, 0, 0))
        active = settings.user.ui.Get('activeBestRepair', PASSIVESHIELDRECHARGE)
        top = 0
        mw = 32
        for flag, hint, iconNo in ((ARMORREPAIRRATEACTIVE, localization.GetByLabel('UI/Fitting/FittingWindow/ArmorRepairRate'), 'ui_1_64_11'),
         (HULLREPAIRRATEACTIVE, localization.GetByLabel('UI/Fitting/FittingWindow/HullRepairRate'), 'ui_1337_64_22'),
         (PASSIVESHIELDRECHARGE, localization.GetByLabel('UI/Fitting/FittingWindow/PassiveShieldRecharge'), 'ui_22_32_7'),
         (SHIELDBOOSTRATEACTIVE, localization.GetByLabel('UI/Fitting/FittingWindow/ShieldBoostRate'), 'ui_2_64_3')):
            entry = uiprimitives.Container(name='entry', parent=subpar, align=uiconst.TOTOP, height=32, state=uiconst.UI_NORMAL)
            icon = uicontrols.Icon(icon=iconNo, parent=entry, state=uiconst.UI_DISABLED, pos=(0, 0, 32, 32), ignoreSize=True)
            label = uicontrols.Label(text=hint, parent=entry, left=icon.left + icon.width, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
            entry.OnClick = (self.PickBestRepair, entry)
            entry.OnMouseEnter = (self.OnMouseEnterBestRepair, entry)
            entry.bestRepairFlag = flag
            entry.sr.hilite = uiprimitives.Fill(parent=entry, state=uiconst.UI_HIDDEN)
            if active == flag:
                uiprimitives.Fill(parent=entry, color=(1.0, 1.0, 1.0, 0.125))
            top += 32
            mw = max(label.textwidth + label.left + 6, mw)

        bestRepairPickerPanel.width = mw
        bestRepairPickerPanel.height = 32
        bestRepairPickerPanel.opacity = 0.0
        WindowUnderlay(bgParent=bestRepairPickerPanel)
        self.sr.bestRepairPickerPanel = bestRepairPickerPanel
        uicore.effect.MorphUI(bestRepairPickerPanel, 'height', top, 250.0)
        uicore.effect.MorphUI(bestRepairPickerPanel, 'opacity', 1.0, 250.0, float=1)

    def OnGlobalMouseUp_BestRepair(self, fromwhere, *etc):
        if self.sr.bestRepairPickerPanel:
            if uicore.uilib.mouseOver == self.sr.bestRepairPickerPanel or uiutil.IsUnder(fromwhere, self.sr.bestRepairPickerPanel) or fromwhere == self.sr.defenceStatsParent.sr.activeBestRepairParent:
                log.LogInfo('Combo.OnGlobalClick Ignoring all clicks from comboDropDown')
                return 1
        if self.sr.bestRepairPickerPanel and not self.sr.bestRepairPickerPanel.destroyed:
            self.sr.bestRepairPickerPanel.Close()
        self.sr.bestRepairPickerPanel = None
        if self.sr.bestRepairPickerCookie:
            uicore.event.UnregisterForTriuiEvents(self.sr.bestRepairPickerCookie)
        self.sr.bestRepairPickerCookie = None
        return 0

    def PickBestRepair(self, entry):
        if entry:
            settings.user.ui.Set('activeBestRepair', entry.bestRepairFlag)
            self.UpdateStats()
        if self.sr.bestRepairPickerPanel and not self.sr.bestRepairPickerPanel.destroyed:
            self.sr.bestRepairPickerPanel.Close()
        self.sr.bestRepairPickerPanel = None
        if self.sr.bestRepairPickerCookie:
            uicore.event.UnregisterForTriuiEvents(self.sr.bestRepairPickerCookie)
        self.sr.bestRepairPickerCookie = None

    def OnMouseEnterBestRepair(self, entry):
        for each in entry.parent.children:
            if util.GetAttrs(each, 'sr', 'hilite'):
                each.sr.hilite.state = uiconst.UI_HIDDEN

        entry.sr.hilite.state = uiconst.UI_DISABLED

    def AddToSlotsWithMenu(self, slot):
        self.menuSlots[slot] = 1

    def ClearSlotsWithMenu(self):
        for slot in self.menuSlots.iterkeys():
            slot.HideUtilButtons()

        self.menuSlots = {}

    def GetSceneShip(self):
        for model in self.sr.sceneContainer.scene.objects:
            if getattr(model, 'name', None) == str(self.shipID):
                return model
