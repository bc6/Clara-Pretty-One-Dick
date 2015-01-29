#Embedded file name: eve/client/script/ui/inflight/scannerFiles\directionalScanner.py
"""
The UI code for the directional scanner
"""
from carbon.common.script.util.format import FmtDist
from carbon.common.script.util.mathUtil import DegToRad
import carbonui.const as uiconst
from carbonui.primitives.layoutGrid import LayoutGrid
from carbonui.util.various_unsorted import SortListOfTuples
from eve.client.script.ui.control.eveCombo import Combo
from eve.client.script.ui.util.uix import GetSlimItemName
import uthread
import blue
import service
from carbonui.control.slider import Slider
from carbonui.primitives.container import Container
from eve.client.script.ui.control import entries as listentry
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.checkbox import Checkbox
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from eve.client.script.ui.control.eveWindow import Window
import geo2
from eve.client.script.ui.inflight.scannerFiles.pieCircle import PieCircle
from localization import GetByLabel
from eve.client.script.ui.shared.maps.browserwindow import MapBrowserWnd
from utillib import KeyVal

def ConvertKmToAu(kmValue):
    auValue = kmValue * 1000 / const.AU
    return auValue


def ConvertAuToKm(auValue):
    kmValue = int(auValue * const.AU / 1000)
    return kmValue


class DirectionalScanner(Window):
    __notifyevents__ = ['OnSessionChanged', 'OnOverviewPresetSaved']
    default_windowID = 'directionalScanner'
    default_width = 400
    default_height = 350
    default_minSize = (350, 175)
    default_captionLabelPath = 'UI/Inflight/Scanner/DirectionalScan'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.scanSvc = sm.GetService('scanSvc')
        self.busy = False
        self.scanresult = []
        self.scanangle = DegToRad(90)
        self.scope = 'inflight'
        self.SetTopparentHeight(0)
        self.SetWndIcon(None)
        self.HideMainIcon()
        directionBox = Container(name='direction', parent=self.sr.main, align=uiconst.TOALL, left=const.defaultPadding, width=const.defaultPadding, top=const.defaultPadding, height=const.defaultPadding)
        self.SetupDScanUI(directionBox)

    def SetupDScanUI(self, directionBox):
        directionSettingsBox = Container(name='direction', parent=directionBox, align=uiconst.TOTOP, height=70, clipChildren=True, padLeft=2)
        self.sr.dirscroll = Scroll(name='dirscroll', parent=directionBox)
        self.sr.dirscroll.sr.id = 'scanner_dirscroll'
        presetGrid = LayoutGrid(parent=directionSettingsBox, columns=2, state=uiconst.UI_PICKCHILDREN, align=uiconst.TOPLEFT, left=0, top=3)
        paddingBtwElements = 8
        checked = settings.user.ui.Get('scannerusesoverviewsettings', 0)
        self.sr.useoverview = Checkbox(text=GetByLabel('UI/Inflight/Scanner/UsePreset'), parent=presetGrid, configName='', retval=0, checked=checked, left=0, align=uiconst.TOPLEFT, callback=self.UseOverviewChanged, width=320, wrapLabel=False)
        presetSelected = settings.user.ui.Get('scanner_presetInUse', None)
        presetOptions = self.GetPresetOptions()
        self.presetsCombo = Combo(label='', parent=presetGrid, options=presetOptions, name='comboTabOverview', select=presetSelected, align=uiconst.TOPLEFT, width=120, left=10, callback=self.OnProfileInUseChanged)
        if not checked:
            self.presetsCombo.Disable()
            self.presetsCombo.opacity = 0.5
            self.sr.useoverview.sr.label.opacity = 0.5
        self.rangeCont = Container(parent=directionSettingsBox, name='rangeCont', align=uiconst.TOTOP, height=24, top=self.sr.useoverview.height)
        self.angleCont = Container(parent=directionSettingsBox, name='rangeCont', align=uiconst.TOTOP, height=24)
        textLeft = 2
        rangeText = GetByLabel('UI/Inflight/Scanner/Range')
        rangeLabel = EveLabelSmall(text=rangeText, parent=self.rangeCont, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, left=textLeft)
        angleText = GetByLabel('UI/Inflight/Scanner/Angle')
        angleLabel = EveLabelSmall(text=angleText, parent=self.angleCont, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, left=textLeft)
        innerLeft = max(rangeLabel.textwidth, angleLabel.textwidth) + paddingBtwElements + textLeft
        innerRangeCont = Container(parent=self.rangeCont, align=uiconst.TOALL, padLeft=innerLeft)
        innderAngleCont = Container(parent=self.angleCont, align=uiconst.TOALL, padLeft=innerLeft)
        maxAuRange = 14.3
        startingKmValue = settings.user.ui.Get('dir_scanrange', const.AU * maxAuRange)
        startingAuValue = ConvertKmToAu(startingKmValue)
        distanceSliderCont = Container(name='distanceSliderCont', parent=innerRangeCont, align=uiconst.CENTERLEFT, state=uiconst.UI_PICKCHILDREN, pos=(0, -1, 100, 18))
        smallestAU = ConvertKmToAu(1000000)
        self.distanceSlider = Slider(name='distanceSlider', parent=distanceSliderCont, sliderID='distanceSlider', minValue=0, maxValue=maxAuRange, endsliderfunc=self.EndSetDistanceSliderValue, onsetvaluefunc=self.OnSetDistanceSliderValue, increments=[smallestAU,
         1,
         5,
         10,
         maxAuRange], height=20, barHeight=10)
        self.distanceSlider.label.display = False
        self.distanceSlider.SetValue(startingAuValue, updateHandle=True, useIncrements=False)
        left = distanceSliderCont.width + paddingBtwElements
        maxAuRangeInKm = ConvertAuToKm(maxAuRange)
        self.dir_rangeinput = SinglelineEdit(name='dir_rangeinput', parent=innerRangeCont, ints=(0, maxAuRangeInKm), setvalue=startingKmValue, align=uiconst.CENTERLEFT, pos=(left,
         0,
         90,
         0), maxLength=len(str(maxAuRangeInKm)) + 1, OnReturn=self.DirectionSearch)
        self.dir_rangeinput.OnChar = self.OnKmChar
        self.dir_rangeinput.OnMouseWheel = self.OnMouseWheelKm
        self.dir_rangeinput.ChangeNumericValue = self.ChangeNumericValueKm
        kmText = GetByLabel('UI/Inflight/Scanner/UnitKMAndSeparator')
        left = self.dir_rangeinput.left + self.dir_rangeinput.width + paddingBtwElements / 2
        kmLabel = EveLabelSmall(text=kmText, parent=innerRangeCont, align=uiconst.CENTERLEFT, pos=(left,
         0,
         0,
         0), state=uiconst.UI_DISABLED)
        left = kmLabel.left + kmLabel.textwidth + paddingBtwElements
        self.dir_rangeinputAu = SinglelineEdit(name='dir_rangeinputAu', parent=innerRangeCont, setvalue=startingAuValue, floats=(0, maxAuRange, 1), align=uiconst.CENTERLEFT, pos=(left,
         0,
         45,
         0), maxLength=4, OnReturn=self.DirectionSearch)
        self.dir_rangeinputAu.OnChar = self.OnAuChar
        self.dir_rangeinputAu.OnMouseWheel = self.OnMouseWheelAu
        self.dir_rangeinputAu.ChangeNumericValue = self.ChangeNumericValueAu
        auText = GetByLabel('UI/Inflight/Scanner/UnitAU')
        left = self.dir_rangeinputAu.left + self.dir_rangeinputAu.width + paddingBtwElements / 2
        auLabel = EveLabelSmall(text=auText, parent=innerRangeCont, align=uiconst.CENTERLEFT, pos=(left,
         0,
         0,
         0), state=uiconst.UI_DISABLED)
        angleSliderCont = Container(name='sliderCont', parent=innderAngleCont, align=uiconst.CENTERLEFT, state=uiconst.UI_PICKCHILDREN, pos=(0, -1, 100, 18))
        self.angleSliderLabel = EveLabelSmall(text='', parent=innderAngleCont, align=uiconst.CENTERLEFT, pos=(0, 0, 0, 0), state=uiconst.UI_DISABLED)
        startingAngle = settings.user.ui.Get('scan_angleSlider', 360)
        startingAngle = max(0, min(startingAngle, 360))
        self.degreeCone = PieCircle(parent=innderAngleCont, left=0, align=uiconst.CENTERLEFT, setValue=startingAngle)
        self.degreeCone.opacity = 0.3
        self.scanangle = DegToRad(startingAngle)
        angleSlider = Slider(name='angleSlider', parent=angleSliderCont, sliderID='angleSlider', startVal=startingAngle, minValue=5, maxValue=360, increments=[5,
         15,
         30,
         60,
         90,
         180,
         360], isEvenIncrementsSlider=True, endsliderfunc=self.EndSetAngleSliderValue, height=20, barHeight=10, setlabelfunc=self.UpdateAngleSliderLabel)
        left = angleSliderCont.width + paddingBtwElements
        self.angleSliderLabel.left = left + 5
        self.degreeCone.left = left + 35
        buttonText = GetByLabel('UI/Inflight/Scanner/Scan')
        scanButton = Button(parent=innderAngleCont, label=buttonText, align=uiconst.CENTERLEFT, pos=(4, 0, 0, 0), func=self.DirectionSearch)
        scanButton.left = auLabel.left + auLabel.textwidth - scanButton.width

    def GetPresetOptions(self):
        p = sm.GetService('overviewPresetSvc').GetAllPresets().keys()
        options = []
        for name in p:
            defaultName = sm.GetService('overviewPresetSvc').GetDefaultOverviewName(name)
            if defaultName:
                options.append((' ' + defaultName.lower(), (defaultName, name)))
            else:
                displayName = sm.GetService('overviewPresetSvc').GetPresetDisplayName(name)
                options.append((displayName.lower(), (displayName, name)))

        options = SortListOfTuples(options)
        options.insert(0, (GetByLabel('UI/Inflight/Scanner/UseActiveOverviewSettings'), None))
        return options

    def OnOverviewPresetSaved(self):
        presetSelected = settings.user.ui.Get('scanner_presetInUse', None)
        presetOptions = self.GetPresetOptions()
        self.presetsCombo.LoadOptions(entries=presetOptions, select=presetSelected)

    def UpdateAngleSliderLabel(self, label, sliderID, displayName, value):
        self.angleSliderLabel.text = GetByLabel('UI/Inflight/Scanner/AngleDegrees', value=value)
        self.degreeCone.SetDegree(value)

    def OnKmChar(self, char, flag):
        returnValue = SinglelineEdit.OnChar(self.dir_rangeinput, char, flag)
        self.KmValueChanged()
        return returnValue

    def OnMouseWheelKm(self, *args):
        SinglelineEdit.MouseWheel(self.dir_rangeinput, *args)
        self.KmValueChanged()

    def ChangeNumericValueKm(self, *args):
        SinglelineEdit.ChangeNumericValue(self.dir_rangeinputAu, *args)
        self.AuValueChanged()

    def KmValueChanged(self):
        kmValue = self.dir_rangeinput.GetValue()
        auValue = ConvertKmToAu(kmValue)
        self.dir_rangeinputAu.SetValue(auValue)
        self.distanceSlider.SetValue(auValue, updateHandle=True, useIncrements=False)

    def OnAuChar(self, char, flag):
        returnValue = SinglelineEdit.OnChar(self.dir_rangeinputAu, char, flag)
        self.AuValueChanged()
        return returnValue

    def OnMouseWheelAu(self, *args):
        SinglelineEdit.MouseWheel(self.dir_rangeinputAu, *args)
        self.AuValueChanged()

    def ChangeNumericValueAu(self, *args):
        SinglelineEdit.ChangeNumericValue(self.dir_rangeinputAu, *args)
        self.AuValueChanged()

    def AuValueChanged(self):
        auValue = self.dir_rangeinputAu.GetValue()
        kmValue = ConvertAuToKm(auValue)
        self.dir_rangeinput.SetValue(kmValue)
        self.distanceSlider.SetValue(auValue, updateHandle=True, useIncrements=False)

    def UpdateDistanceFromSlider(self):
        auValue = self.distanceSlider.GetValue()
        kmValue = ConvertAuToKm(auValue)
        self.dir_rangeinput.SetValue(kmValue)
        self.dir_rangeinputAu.SetValue(auValue)

    def EndSetDistanceSliderValue(self, *args):
        self.UpdateDistanceFromSlider()
        uthread.new(self.DirectionSearch)

    def OnSetDistanceSliderValue(self, slider, *args):
        if not slider.dragging:
            return
        self.UpdateDistanceFromSlider()

    def EndSetAngleSliderValue(self, slider):
        angleValue = slider.GetValue()
        self.degreeCone.SetDegree(angleValue)
        self.SetMapAngle(DegToRad(angleValue))
        settings.user.ui.Set('scan_angleSlider', angleValue)
        uthread.new(self.DirectionSearch)

    def _OnClose(self, *args):
        self.SetMapAngle(0)

    def DirectionSearch(self, *args):
        if self.destroyed or self.busy:
            return
        self.busy = True
        self.ShowLoad()
        self.scanresult = []
        if self.sr.useoverview.checked:
            selectedValue = self.presetsCombo.GetValue()
            if selectedValue is None:
                selectedValue = sm.GetService('overviewPresetSvc').GetActiveOverviewPresetName()
            filters = sm.GetService('overviewPresetSvc').GetValidGroups(presetName=selectedValue)
        camera = sm.GetService('sceneManager').GetRegisteredCamera(None, defaultOnActiveCamera=True)
        if not camera:
            self.busy = False
            self.HideLoad()
            raise RuntimeError('No camera found?!')
        vec = geo2.QuaternionTransformVector(camera.rotationAroundParent, (0, 0, -1))
        vec = geo2.Vec3Normalize(vec)
        rnge = self.dir_rangeinput.GetValue()
        try:
            result = self.scanSvc.ConeScan(self.scanangle, rnge * 1000, vec[0], vec[1], vec[2])
        except (UserError, RuntimeError) as err:
            result = None
            self.busy = False
            self.HideLoad()
            raise err

        settings.user.ui.Set('dir_scanrange', rnge)
        if result:
            bp = sm.GetService('michelle').GetBallpark()
            if bp:
                for rec in result:
                    if self.sr.useoverview.checked:
                        if rec.groupID not in filters:
                            continue
                    if rec.id in bp.balls:
                        self.scanresult.append([None, bp.balls[rec.id], rec])
                    else:
                        self.scanresult.append([None, None, rec])

        self.ShowDirectionalSearchResult()
        self.busy = False
        self.HideLoad()

    def ShowDirectionalSearchResult(self, *args):
        self.listtype = 'location'
        scrolllist = []
        if self.scanresult and len(self.scanresult):
            myball = None
            ballpark = sm.GetService('michelle').GetBallpark()
            if ballpark:
                myball = ballpark.GetBall(eve.session.shipid)
            prime = []
            for result in self.scanresult:
                slimItem, ball, celestialRec = result
                if not slimItem and celestialRec:
                    prime.append(celestialRec.id)

            if prime:
                cfg.evelocations.Prime(prime)
            for slimItem, ball, celestialRec in self.scanresult:
                if self is None or self.destroyed:
                    return
                if slimItem:
                    typeinfo = cfg.invtypes.Get(slimItem.typeID)
                    entryname = GetSlimItemName(slimItem)
                    itemID = slimItem.itemID
                    typeID = slimItem.typeID
                    if not entryname:
                        entryname = typeinfo.Group().name
                elif celestialRec:
                    typeinfo = cfg.invtypes.Get(celestialRec.typeID)
                    if typeinfo.groupID == const.groupHarvestableCloud:
                        entryname = GetByLabel('UI/Inventory/SlimItemNames/SlimHarvestableCloud', typeinfo.name)
                    elif typeinfo.categoryID == const.categoryAsteroid:
                        entryname = GetByLabel('UI/Inventory/SlimItemNames/SlimAsteroid', typeinfo.name)
                    else:
                        entryname = cfg.evelocations.Get(celestialRec.id).name
                    if not entryname:
                        entryname = typeinfo.name
                    itemID = celestialRec.id
                    typeID = celestialRec.typeID
                else:
                    continue
                if ball is not None:
                    dist = ball.surfaceDist
                    diststr = FmtDist(dist, maxdemicals=1)
                else:
                    dist = 0
                    diststr = '-'
                groupID = cfg.invtypes.Get(typeID).groupID
                if not eve.session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
                    if groupID == const.groupCloud:
                        continue
                data = KeyVal()
                data.label = '%s<t>%s<t>%s' % (entryname, typeinfo.name, diststr)
                data.entryName = entryname
                data.typeName = typeinfo.name
                data.Set('sort_%s' % GetByLabel('UI/Common/Distance'), dist)
                data.columnID = 'directionalResultGroupColumn'
                data.result = result
                data.itemID = itemID
                data.typeID = typeID
                data.GetMenu = self.DirectionalResultMenu
                scrolllist.append(listentry.Get('DirectionalScanResults', data=data))
                blue.pyos.BeNice()

        if not len(scrolllist):
            data = KeyVal()
            data.label = GetByLabel('UI/Inflight/Scanner/DirectionalNoResult')
            data.hideLines = 1
            scrolllist.append(listentry.Get('Generic', data=data))
            headers = []
        else:
            headers = [GetByLabel('UI/Common/Name'), GetByLabel('UI/Common/Type'), GetByLabel('UI/Common/Distance')]
        self.sr.dirscroll.Load(contentList=scrolllist, headers=headers)

    def DirectionalResultMenu(self, entry, *args):
        if entry.sr.node.itemID:
            return sm.GetService('menu').CelestialMenu(entry.sr.node.itemID, typeID=entry.sr.node.typeID)
        return []

    def SetMapAngle(self, angle):
        if angle is not None:
            self.scanangle = angle
        wnd = MapBrowserWnd.GetIfOpen()
        if wnd:
            wnd.SetTempAngle(angle)

    def EndSetSliderValue(self, *args):
        uthread.new(self.DirectionSearch)

    def UseOverviewChanged(self, checked):
        if self.sr.useoverview.checked:
            self.presetsCombo.Enable()
            self.presetsCombo.opacity = 1
            self.sr.useoverview.sr.label.opacity = 1
        else:
            self.presetsCombo.Disable()
            self.presetsCombo.opacity = 0.5
            self.sr.useoverview.sr.label.opacity = 0.5
        settings.user.ui.Set('scannerusesoverviewsettings', self.sr.useoverview.checked)
        self.DirectionSearch()

    def OnProfileInUseChanged(self, *args):
        value = self.presetsCombo.GetValue()
        settings.user.ui.Set('scanner_presetInUse', value)
        self.DirectionSearch()


class DirectionalScanResults(listentry.Generic):
    """
        A class for the entries in the directional scanner.
        It gets its own class so it can be dragged/dropped correctly.
    """
    __guid__ = 'listentry.DirectionalScanResults'
    isDragObject = True

    def GetDragData(self, *args):
        return self.sr.node.scroll.GetSelectedNodes(self.sr.node)
