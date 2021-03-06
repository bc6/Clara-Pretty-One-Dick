#Embedded file name: eve/client/script/ui/shared/planet\surveyUI.py
"""
The survey window that enables players to control their extractor control units (ECUs)
"""
import math
import carbonui.const as uiconst
import uiprimitives
import uicontrols
import util
import uicls
import blue
import uthread
import geo2
from PlanetResources import builder
import localization
import eve.common.script.util.planetCommon as planetCommon
from eve.common.script.util.planetCommon import SurfacePoint
from pinContainers.BasePinContainer import CaptionLabel, IconButton, SubTextLabel
from . import planetCommon as planetCommonUI

class SurveyWindow(uicontrols.Window):
    __guid__ = 'form.PlanetSurvey'
    __notifyevents__ = ['OnPlanetViewChanged', 'OnEditModeChanged', 'OnEditModeBuiltOrDestroyed']
    default_fixedWidth = 700
    default_fixedHeight = 256
    default_windowID = 'PlanetSurvey'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.ecuPinID = attributes.get('ecuPinID')
        self.barGraphUpdating = False
        self.planetUISvc = sm.GetService('planetUI')
        self.planet = self.planetUISvc.planet
        self.pin = self.planet.GetPin(self.ecuPinID)
        self.extractionHeadValues = {}
        self.resourceTypeIDs = self.planet.remoteHandler.GetPlanetResourceInfo().keys()
        self.currResourceTypeID = self.pin.programType
        self.outputVals = []
        self.programCycleTime = None
        self.dragThread = None
        self.flashStateColorThread = None
        self.currCycleTime = None
        self.sh = None
        if self.currResourceTypeID is not None:
            inRange, self.sh = self.planetUISvc.planet.GetResourceData(self.currResourceTypeID)
        self.revertToResource = self.planetUISvc.selectedResourceTypeID
        self.currentResource = None
        self.editsEnabled = self.pin.GetExtractionType() is None or self.pin.GetTimeToExpiry() <= 0
        if self.editsEnabled:
            self.planetUISvc.myPinManager.UnlockHeads(self.pin.id)
        self.barTimeIndicatorThread = None
        self.overlapValues = {}
        self.stateColor = None
        self.pinData = None
        if self.pin.IsInEditMode():
            self.pinData = self.pin.Serialize()
        self.SetTopparentHeight(10)
        self.MakeUnResizeable()
        captionTxt = localization.GetByLabel('UI/PI/Common/SurveyingProgram', pinName=planetCommon.GetGenericPinName(self.pin.typeID, self.pin.id))
        self.SetCaption(captionTxt)
        self.bottomCont = uiprimitives.Container(name='bottomCont', parent=self.sr.main, align=uiconst.TOBOTTOM, height=30)
        self.leftCont = uiprimitives.Container(name='leftCont', parent=self.sr.main, align=uiconst.TOLEFT, width=130, padding=(6, 0, 3, 0))
        self.rightCont = uiprimitives.Container(name='rightCont', parent=self.sr.main, align=uiconst.TORIGHT, width=145, padding=(10, 5, 5, 5))
        self.centerCont = uiprimitives.Container(name='centerCont', parent=self.sr.main, align=uiconst.TOALL, padTop=3)
        self._ConstructLeftContainer()
        self._ConstructCenterContainer()
        self._ConstructRightContainer()
        self._ConstructBottomContainer()

    def _ConstructLeftContainer(self):
        textCont = uiprimitives.Container(parent=self.leftCont, height=15, align=uiconst.TOTOP)
        CaptionLabel(parent=textCont, text=localization.GetByLabel('UI/PI/Common/ExtractorHeadUnits'), align=uiconst.TOTOP)
        self.headButtons = []
        headEntryCont = uiprimitives.Container(parent=self.leftCont, name='headEntryCont', align=uiconst.TOTOP, height=200)
        headEntryContLeft = uiprimitives.Container(parent=headEntryCont, name='headEntryContLeft', align=uiconst.TOLEFT, width=self.leftCont.width / 2)
        headEntryContRight = uiprimitives.Container(parent=headEntryCont, name='headEntryContRight', align=uiconst.TOLEFT, width=self.leftCont.width / 2)
        for i in xrange(planetCommon.ECU_MAX_HEADS):
            value = self.GetResourceLayerValueForHead(i)
            if self.editsEnabled:
                state = uiconst.UI_NORMAL
            else:
                state = uiconst.UI_DISABLED
            if i < 5:
                parent = headEntryContLeft
            else:
                parent = headEntryContRight
            btn = ExtractionHeadEntry(parent=parent, headID=i, ecuID=self.pin.id, align=uiconst.TOTOP, height=20, state=state, value=value, pin=self.pin)
            btn.OnClick = (self.OnHeadBtnClicked, i)
            self.headButtons.append(btn)

        self.currentRadius = max(min(self.pin.headRadius, planetCommon.RADIUS_DRILLAREAMAX), planetCommon.RADIUS_DRILLAREAMIN)
        sliderCont = uiprimitives.Container(parent=self.leftCont, name='sliderCont', align=uiconst.TOBOTTOM, height=16)
        CaptionLabel(parent=self.leftCont, text=localization.GetByLabel('UI/PI/Common/ExtractionAreaSize'), align=uiconst.TOBOTTOM, padBottom=2)
        BTNSIZE = 20
        BTNFONTSIZE = 8
        sliderValue = math.sqrt((self.currentRadius - planetCommon.RADIUS_DRILLAREAMIN) / planetCommon.RADIUS_DRILLAREADIFF)
        self.areaSlider = AreaSlider(parent=sliderCont, name='areaSlider', align=uiconst.TOPLEFT, minValue=0.0, maxValue=1.0, startVal=sliderValue, hint=localization.GetByLabel('UI/PI/Common/ExtractionAreaSize'), endsliderfunc=self.OnAreaSliderReleased, pos=(BTNSIZE - 4,
         0,
         95,
         13))
        subtrBtn = uicontrols.Button(parent=sliderCont, name='subtractBtn', align=uiconst.TOPLEFT, label=localization.GetByLabel('UI/PI/Common/SurveyMinusSign'), func=self.DecreaseDrillAreaSize, alwaysLite=True, fixedwidth=BTNSIZE, fontsize=BTNFONTSIZE, left=-4, top=-3)
        subtrBtn.sr.label.left += 1
        addBtn = uicontrols.Button(parent=sliderCont, name='addBtn', align=uiconst.TOPRIGHT, label=localization.GetByLabel('UI/PI/Common/SurveyPlusSign'), func=self.IncreaseDrillAreaSize, alwaysLite=True, fixedwidth=BTNSIZE, fontsize=BTNFONTSIZE, top=-3)
        addBtn.sr.label.left += 1
        self.areaSlider.OnSetValue = self.OnAreaSliderMoved
        if not self.editsEnabled:
            self.areaSlider.Disable()
            subtrBtn.Disable()
            addBtn.Disable()

    def DecreaseDrillAreaSize(self, *args):
        newSliderValue = self._GetNextSliderValue(increase=False)
        self.areaSlider.SetValue(newSliderValue, updateHandle=True)
        self.SetExtractorRadius()

    def IncreaseDrillAreaSize(self, *args):
        newSliderValue = self._GetNextSliderValue(increase=True)
        self.areaSlider.SetValue(newSliderValue, updateHandle=True)
        self.SetExtractorRadius()

    def _GetNextSliderValue(self, increase = True):
        """
        Due to the complexity of how number of cycles and cycle time is changed as a (stepped)
        function of radius, we just try to increase the slider value slightly in a loop until
        we have reached next/previous step.
        
        To be safe, we never do more than maxCount iterations
        """
        oldNumCycles = None
        sliderVal = self.areaSlider.value
        maxCount = 1000
        count = 0
        while count < maxCount:
            count += 1
            cycleTime, numCycles = self._GetCycleTimeAndNumCyclesFromSliderVal(sliderVal)
            if not oldNumCycles:
                oldNumCycles = numCycles
            if oldNumCycles != numCycles:
                break
            if increase:
                sliderVal += 0.001
            else:
                sliderVal -= 0.001

        return sliderVal

    def _GetCycleTimeAndNumCyclesFromSliderVal(self, sliderVal):
        radius = self._GetRadiusFromSliderVal(sliderVal)
        programLength = planetCommon.GetProgramLengthFromHeadRadius(radius)
        cycleTime = planetCommon.GetCycleTimeFromProgramLength(programLength)
        numCycles = int(programLength / cycleTime)
        return (cycleTime, numCycles)

    def _GetRadiusFromSliderVal(self, sliderVal):
        return sliderVal ** 2 * planetCommon.RADIUS_DRILLAREADIFF + planetCommon.RADIUS_DRILLAREAMIN

    def OnAreaSliderReleased(self, slider):
        self.SetExtractorRadius()

    def SetExtractorRadius(self):
        radius = self.areaSlider.value ** 2 * planetCommon.RADIUS_DRILLAREADIFF + planetCommon.RADIUS_DRILLAREAMIN
        self.planetUISvc.myPinManager.SetExtractionHeadRadius(self.pin.id, radius)
        self.currentRadius = radius
        self.UpdateProgram()

    def OnAreaSliderMoved(self, slider):
        AreaSlider.OnSetValue(slider, slider)
        cycleTime, numCycles = self._GetCycleTimeAndNumCyclesFromSliderVal(slider.value)
        cycleTime = int(cycleTime * const.HOUR)
        self.barGraph.SetXLabels((localization.GetByLabel('UI/PI/Common/SurveyProgramStart'), util.FmtDate(cycleTime * numCycles)))

    def _ConstructCenterContainer(self):
        self.barGraph = uicls.BarGraph(parent=self.centerCont, align=uiconst.TOPLEFT, width=self.default_fixedWidth - self.leftCont.width - self.rightCont.width - 25, height=190, barUpdateDelayMs=1, barHintFunc=self.GetBarHint)
        uthread.new(self.UpdateProgram)

    def GetBarHint(self, numBar, value, maxValue):
        accOutput = sum(self.outputVals[:numBar])
        accTime = self.currCycleTime * numBar
        accPerHour = const.HOUR * accOutput / accTime
        return localization.GetByLabel('UI/PI/Common/SurveyBarHint', numBar=numBar, value=value, accOutput=accOutput, accTime=accTime, accPerHour=accPerHour)

    def UpdateProgram(self, replaceHeadID = None, point = None):
        if self.currentResource is None:
            return
        heads = self.pin.heads[:]
        if self.editsEnabled:
            if replaceHeadID is not None:
                for each in self.pin.heads:
                    if each[0] == replaceHeadID:
                        heads.remove(each)
                        heads.append((replaceHeadID, point.phi, point.theta))
                        break

            colony = self.GetColony()
            maxValue, cycleTime, numCycles, self.overlapValues = colony.CreateProgram(self.currentResource, self.pin.id, self.currResourceTypeID, points=heads, headRadius=self.currentRadius)
            self.UpdateOverlapValues()
            self.planetUISvc.myPinManager.SetEcuOverlapValues(self.pin.id, self.overlapValues)
        else:
            maxValue, cycleTime, numCycles = self.pin.GetProgramParameters()
        self.currCycleTime = cycleTime
        xLabels = (localization.GetByLabel('UI/PI/Common/SurveyProgramStart'), util.FmtDate(cycleTime * numCycles))
        self.UpdateBarGraph(maxValue, cycleTime, numCycles, xLabels)

    def UpdateOverlapValues(self):
        for id, headButton in enumerate(self.headButtons):
            headButton.SetOverlapValue(self.overlapValues.get(id, None))

    def UpdateBarGraph(self, maxValue, cycleTime, numCycles, xLabels):
        self.outputVals = self.pin.GetProgramOutputPrediction(maxValue, cycleTime, numCycles)
        totalOutput = sum(self.outputVals)
        perHourOutput = float(totalOutput) * const.HOUR / (numCycles * cycleTime)
        currOutput = self.pin.GetProducts().values()
        if currOutput:
            currOutput = currOutput[0]
        else:
            currOutput = 0
        self.outputPerHourTxt.SetText(localization.GetByLabel('UI/PI/Common/SurveyPerHourOutput', perHourOutput=perHourOutput))
        self.outputTotalTxt.SetText(localization.GetByLabel('UI/PI/Common/SurveyTotalOutput', totalOutput=totalOutput))
        self.barGraph.SetValues(self.outputVals)
        self.barGraph.SetXLabels(xLabels)
        self.UpdateBarTimeIndicator()
        self.programCycleTime = cycleTime

    def UpdateBarTimeIndicator(self):
        """
        Show or hide the bargraph time indicator, depending on the ecu pin state
        """
        if self.pin.IsActive() and not self.pin.IsInEditMode():
            if self.barTimeIndicatorThread is None:
                self.barTimeIndicatorThread = uthread.new(self._UpdateBarTimeIndicator)
        else:
            self.barGraph.HideTimeIndicator()
            if self.barTimeIndicatorThread is not None:
                self.barTimeIndicatorThread.kill()
                self.barTimeIndicatorThread = None

    def _UpdateBarTimeIndicator(self):
        """
        Update the bargraph time indicator position every 10 seconds
        """
        while self and not self.destroyed:
            indicatorValue = float(blue.os.GetWallclockTime() - self.pin.installTime) / (self.pin.expiryTime - self.pin.installTime)
            if indicatorValue > 0.0 and indicatorValue < 1.0:
                self.barGraph.ShowTimeIndicator(indicatorValue)
            blue.pyos.synchro.SleepWallclock(10000)

    def OnHeadEntryMouseEnter(self, headID):
        if not uicore.uilib.leftbtn:
            self.headButtons[headID].ShowFill()

    def OnHeadEntryMouseExit(self, headID):
        self.headButtons[headID].HideFill()

    def _ConstructRightContainer(self):
        self.resourceIconButtons = {}
        numIcons = len(self.resourceTypeIDs)
        ICONSIZE = 25
        PAD = 4
        stateParent = uiprimitives.Container(parent=self.rightCont, align=uiconst.TOTOP, height=20, padBottom=6)
        self._SetStateInfo()
        self.stateTxt = uicontrols.EveLabelSmall(parent=stateParent, text='<center>' + self.stateInfoText, align=uiconst.TOALL, top=4, color=util.Color.WHITE, state=uiconst.UI_NORMAL)
        uicontrols.Frame(parent=stateParent, color=util.Color.GetGrayRGBA(1.0, 0.2))
        self.stateColorFill = uiprimitives.Fill(parent=stateParent, color=self.stateColor)
        if self.editsEnabled:
            state = uiconst.UI_PICKCHILDREN
        else:
            state = uiconst.UI_DISABLED
        iconCont = uiprimitives.Container(parent=self.rightCont, align=uiconst.TOTOP, pos=(0,
         0,
         numIcons * (ICONSIZE + PAD),
         ICONSIZE), state=state, padding=(0,
         PAD,
         0,
         PAD))
        resourceTypes = [ (cfg.invtypes.Get(typeID).typeName, typeID) for typeID in self.resourceTypeIDs ]
        resourceTypes.sort()
        for i, (typeName, typeID) in enumerate(resourceTypes):
            ib = IconButton(parent=iconCont, pos=(i * (ICONSIZE + PAD),
             0,
             ICONSIZE,
             ICONSIZE), size=ICONSIZE, typeID=typeID, ignoreSize=True)
            self.resourceIconButtons[typeID] = ib
            ib.OnClick = (self.OnResourceBtnClicked, typeID)
            ib.OnMouseEnter = (self.OnResourceBtnMouseEnter, ib, typeID)
            ib.OnMouseExit = (self.OnResourceBtnMouseExit, ib)

        self.selectedResourceTxt = SubTextLabel(parent=self.rightCont, text='', align=uiconst.TOTOP)
        self.SetCurrentResourceText(self.currResourceTypeID)
        self.currCycleGauge = uicls.Gauge(parent=self.rightCont, align=uiconst.TOTOP, value=0.0, color=planetCommonUI.PLANET_COLOR_CYCLE, label=localization.GetByLabel('UI/PI/Common/CurrentCycle'), padTop=18)
        uthread.new(self._UpdateCurrCycleGauge)
        outputTxtCont = uiprimitives.Container(parent=self.rightCont, align=uiconst.TOBOTTOM, height=40)
        CaptionLabel(parent=outputTxtCont, text=localization.GetByLabel('UI/PI/Common/Output'), align=uiconst.TOTOP)
        tabs = [-6, 60]
        self.outputPerHourTxt = SubTextLabel(parent=outputTxtCont, text=localization.GetByLabel('UI/Common/None'), align=uiconst.TOTOP, tabs=tabs)
        self.outputTotalTxt = SubTextLabel(parent=outputTxtCont, align=uiconst.TOTOP, tabs=tabs)

    def _UpdateCurrCycleGauge(self):
        while not self.destroyed:
            txt, cycleProportion = planetCommonUI.GetPinCycleInfo(self.pin, self.programCycleTime)
            self.currCycleGauge.SetValueInstantly(cycleProportion)
            self.currCycleGauge.SetSubText(txt)
            blue.pyos.synchro.SleepWallclock(1000)

    def _SetStateInfo(self):
        if self.pin.IsInEditMode():
            self.stateColor = util.Color.WHITE
            self.stateInfoText = localization.GetByLabel('UI/PI/Common/EditsPending')
            flash = True
        elif self.pin.IsActive():
            self.stateColor = util.Color('GREEN').SetAlpha(0.4).GetRGBA()
            self.stateInfoText = localization.GetByLabel('UI/PI/Common/SurveyProgramRunning')
            flash = False
        else:
            self.stateColor = util.Color.WHITE
            self.stateInfoText = localization.GetByLabel('UI/Common/Idle')
            flash = True
        self.FlashStateColor(flash)

    def FlashStateColor(self, flash):
        if self.flashStateColorThread is not None:
            self.flashStateColorThread.kill()
        if flash:
            self.flashStateColorThread = uthread.new(self._FlashStateColor)

    def _FlashStateColor(self):
        CYCLETIME = 3.0
        t = 0.0
        while not self.destroyed:
            if self.stateColor:
                t += 1.0 / blue.os.fps % CYCLETIME
                x = math.sin(2 * math.pi * t / CYCLETIME) * 0.2 + 0.3
                color = util.Color(*self.stateColor).SetAlpha(x)
                self.stateColorFill.color.SetRGB(*color.GetRGBA())
            blue.pyos.synchro.Yield()

    def _ConstructBottomContainer(self):
        if self.editsEnabled:
            btnName = localization.GetByLabel('UI/PI/Common/SurveyInstallProgram')
            btns = [(btnName, self._ApplyProgram, None)]
        else:
            btnName = localization.GetByLabel('UI/PI/Common/SurveyStopProgram')
            btns = [(btnName, self._StopProgram, None)]
        btns.append((localization.GetByLabel('UI/Common/Close'), self._Cancel, None))
        btnGroup = uicontrols.ButtonGroup(btns=btns, parent=self.bottomCont, line=False)
        self.submitButton = btnGroup.GetBtnByLabel(btnName)
        self.SetCurrentResource(self.currResourceTypeID)
        self._SetSubmitButtonState()

    def _SetSubmitButtonState(self):
        nextEditTime = self.pin.GetNextEditTime()
        if nextEditTime is not None and nextEditTime > blue.os.GetWallclockTime() and not self.pin.IsInEditMode():
            self.submitButton.Disable()
            uthread.new(self._UnlockStopButtonThread).context = '_SetSubmitButtonState'
        elif self.currentResource is None:
            self.submitButton.Disable()
            self.submitButton.SetHint('')
        else:
            self.submitButton.Enable()
            self.submitButton.SetHint('')

    def _UnlockStopButtonThread(self):
        nextEditTime = self.pin.GetNextEditTime()
        while nextEditTime > blue.os.GetWallclockTime():
            self.submitButton.SetHint(localization.GetByLabel('UI/PI/Common/SurveyEditsAvailableIn', time=nextEditTime - blue.os.GetWallclockTime()))
            blue.pyos.synchro.SleepWallclock(200)
            if not self or self.destroyed:
                return

        self._SetSubmitButtonState()

    def OnHeadBtnClicked(self, headID):
        head = self.pin.FindHead(headID)
        if not head:
            self.PlaceProbeAtDefaultPosition(headID)
        else:
            self.planetUISvc.myPinManager.RemoveExtractionHead(self.pin.id, headID)
            if headID in self.extractionHeadValues:
                self.extractionHeadValues.pop(headID)
            self.headButtons[headID].SetValue(None)
        self.UpdateProgram()

    def OnBeginDragExtractionHead(self, headID, surfacePoint):
        sm.GetService('audio').SendUIEvent('wise:/msg_pi_extractor_play')
        sm.GetService('audio').SendUIEvent('wise:/msg_pi_extractor_distorted_play')
        if self.currResourceTypeID is not None:
            self.dragThread = uthread.new(self._WhileExtractionHeadDraggedThread, headID, surfacePoint)
        else:
            self.headButtons[headID].SetValue(0.0)
        self.headButtons[headID].HideFill()

    def OnEndDragExtractionHead(self):
        sm.GetService('audio').SendUIEvent('wise:/msg_pi_extractor_stop')
        sm.GetService('audio').SendUIEvent('wise:/msg_pi_extractor_distorted_stop')
        if self.dragThread is not None:
            self.dragThread.kill()
            self.dragThread = None

    def OnExtractionHeadMoved(self, headID, surfacePoint):
        self.UpdateHeadPosition(headID, surfacePoint)

    def _WhileExtractionHeadDraggedThread(self, headID, surfacePoint):
        while not self.destroyed:
            if self.currentResource is not None:
                self.UpdateProgram(replaceHeadID=headID, point=surfacePoint)
            blue.pyos.synchro.SleepWallclock(200)

    def UpdateHeadPosition(self, headID, surfacePoint):
        heads = self.pin.heads
        headRadius = self.pin.headRadius
        if self.currentResource is not None:
            value = self.GetResourceLayerValueForHead(headID, surfacePoint)
            overlapValue = self.overlapValues.get(headID, None)
            self.headButtons[headID].SetValue(value=value, overlapValue=overlapValue)
            if value is not None:
                sm.GetService('audio').SetGlobalRTPC('pitch_extractor_quality', 100 * value / 250)
            if overlapValue is not None:
                sm.GetService('audio').SetGlobalRTPC('volume_extractor_interference', 10 * overlapValue)
        else:
            self.headButtons[headID].SetValue(value=0.0)

    def UpdateHeadButtonValues(self):
        for headButton in self.headButtons:
            value = self.GetResourceLayerValueForHead(headButton.headID)
            self.extractionHeadValues[headButton.headID] = value
            headButton.SetValue(value)

    def GetResourceLayerValueForHead(self, headID, surfacePoint = None):
        if self.currResourceTypeID:
            head = self.pin.FindHead(headID)
            if head:
                headID, phi, theta = head
                if surfacePoint:
                    theta = 2.0 * math.pi - surfacePoint.theta
                    phi = surfacePoint.phi
                else:
                    theta = 2.0 * math.pi - theta
                    phi = phi
                return max(0.0, builder.GetValueAt(self.sh, theta, phi))
        else:
            if self.pin.FindHead(headID) is not None:
                return 0.0
            return

    def PlaceProbeAtDefaultPosition(self, headID):
        OFFSET = 0.08
        VEC_X = (-1, 0, 0)
        rotAngle = float(headID) / planetCommon.ECU_MAX_HEADS * 2 * math.pi
        ecuVector = self.planetUISvc.myPinManager.pinsByID[self.pin.id].surfacePoint.GetAsXYZTuple()
        normal = geo2.Vec3Cross(ecuVector, VEC_X)
        normal = geo2.Vector(*normal) * OFFSET
        posVec = geo2.Vec3Subtract(ecuVector, normal)
        posVec = geo2.Vec3Normalize(posVec)
        rotMat = geo2.MatrixRotationAxis(ecuVector, rotAngle)
        posVec = geo2.Multiply(rotMat, posVec)
        surfacePoint = SurfacePoint(*posVec)
        self.planetUISvc.myPinManager.PlaceExtractionHead(self.pin.id, headID, surfacePoint, self.currentRadius)
        self.UpdateHeadPosition(headID, surfacePoint)

    def _ApplyProgram(self, *args):
        if self.currResourceTypeID is not None:
            self.planet.InstallProgram(self.pin.id, self.currResourceTypeID, self.currentRadius)
        self.planetUISvc.myPinManager.ReRenderPin(self.pin)
        self.Close()

    def _Cancel(self, *args):
        self.planetUISvc.CancelInstallProgram(self.pin.id, self.pinData)
        self.Close()

    def _StopProgram(self, *args):
        self.editsEnabled = True
        self.pin.inEditMode = True
        self.leftCont.Flush()
        self.rightCont.Flush()
        self.bottomCont.Flush()
        self.planetUISvc.myPinManager.UnlockHeads(self.pin.id)
        self.planetUISvc.GetCurrentPlanet().InstallProgram(self.pin.id, None, self.currentRadius)
        self._ConstructLeftContainer()
        self._ConstructRightContainer()
        self._ConstructBottomContainer()

    def OnResourceBtnClicked(self, typeID, *args):
        self.SetCurrentResource(typeID)

    def OnResourceBtnMouseEnter(self, btn, typeID, *args):
        self.SetCurrentResourceText(typeID)
        IconButton.OnMouseEnter(btn)

    def OnResourceBtnMouseExit(self, btn, *args):
        self.SetCurrentResourceText(self.currResourceTypeID)
        IconButton.OnMouseExit(btn)

    def SetCurrentResource(self, typeID = None):
        self.currResourceTypeID = typeID
        self.currentResource = None if typeID is None else self.planet.GetResourceHarmonic(typeID)
        for ibTypeID, ib in self.resourceIconButtons.iteritems():
            ib.SetSelected(False)
            if not self.editsEnabled and ibTypeID != typeID:
                ib.Disable()

        if typeID:
            self.resourceIconButtons[typeID].SetSelected(True)
        self._SetSubmitButtonState()
        if typeID is None:
            self.sh = None
        else:
            inRange, self.sh = self.planetUISvc.planet.GetResourceData(self.currResourceTypeID)
        self.SetCurrentResourceText(typeID)
        self.UpdateHeadButtonValues()
        self.UpdateProgram()
        self.planetUISvc.ShowResource(typeID)

    def SetCurrentResourceText(self, typeID):
        if typeID:
            text = cfg.invtypes.Get(typeID).name
        else:
            text = localization.GetByLabel('UI/PI/Common/NoResourceSelected')
        self.selectedResourceTxt.text = text

    def OnPlanetViewChanged(self, newPlanet, oldPlanet):
        """
        Close the window when exiting planet view or switching planets
        """
        self.Close()

    def OnEditModeBuiltOrDestroyed(self):
        """
        Close the window if the pin was deleted 
        """
        if not self or self.destroyed:
            return
        if self.planet.GetPin(self.pin.id) is None:
            self.Close()

    def OnEditModeChanged(self, isEdit):
        if not self or self.destroyed:
            return
        if not isEdit:
            self.Close()

    def CloseByUser(self, *args):
        self.planetUISvc.CancelInstallProgram(self.pin.id, self.pinData)
        uicontrols.Window.CloseByUser(self, *args)

    def _OnClose(self, *args):
        if hasattr(self, 'revertToResource'):
            self.planetUISvc.ShowResource(self.revertToResource)
        self.planetUISvc.ExitSurveyMode()
        self.planetUISvc.eventManager.SetStateNormal()

    def GetColony(self):
        return self.planetUISvc.GetCurrentPlanet().GetColony(session.charid)


class ExtractionHeadEntry(uiprimitives.Container):
    __guid__ = 'uicls.ExtractionHeadEntry'
    default_name = 'ExtractionHeadEntry'
    default_height = 20
    default_state = uiconst.UI_NORMAL
    default_padBottom = 9

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.headID = attributes.headID
        self.ecuID = attributes.ecuID
        self.value = attributes.get('value', None)
        self.pin = attributes.pin
        self.overlapValue = None
        self.fill = uiprimitives.Fill(parent=self, align=uiconst.TOTOP, height=self.default_height, color=util.Color(*util.Color.WHITE).SetAlpha(0.1).GetRGBA(), state=uiconst.UI_HIDDEN, idx=0)
        self.icon = uicontrols.Icon(parent=self, icon='ui_77_32_38', size=self.default_height, ignoreSize=True, state=uiconst.UI_DISABLED, left=-2)
        self.label = SubTextLabel(parent=self, text='', left=self.default_height, top=4)
        self.SetValue(self.value)

    def SetValue(self, value = None, overlapValue = None):
        self.value = value
        self.overlapValue = overlapValue
        if value is None:
            txt = localization.GetByLabel('UI/PI/Common/SurveyDashSign')
            self.opacity = 0.5
        else:
            if overlapValue:
                txt = localization.GetByLabel('UI/PI/Common/SurveyHeadValueDisturbed', value=value, percentage=100 * overlapValue)
            else:
                txt = localization.GetByLabel('UI/PI/Common/SurveyHeadValue', value=value)
            self.opacity = 1.0
        self.label.text = txt

    def GetHint(self, *args):
        if self.value is None:
            return localization.GetByLabel('UI/PI/Common/SurveyInstallHeadHint', power=self.pin.GetExtractorHeadPowerUsage(), cpu=self.pin.GetExtractorHeadCpuUsage())
        if self.overlapValue:
            disturbanceText = localization.GetByLabel('UI/PI/Common/SurveyExtractorHeadDisturbanceHint', percentage=100 * self.overlapValue)
        else:
            disturbanceText = ''
        hint = localization.GetByLabel('UI/PI/Common/SurveyExtractorHeadHint', headID=self.headID + 1, value=self.value, disturbanceText=disturbanceText)
        return hint

    def SetOverlapValue(self, overlapValue):
        self.SetValue(self.value, overlapValue)

    def OnMouseEnter(self, *args):
        if not self or self.destroyed:
            return
        self.ShowFill()
        if self.value is None:
            self.label.text = localization.GetByLabel('UI/PI/Common/SurveyInstall')
            self.opacity = 1.0
        sm.GetService('planetUI').myPinManager.OnExtractionHeadMouseEnter(self.ecuID, self.headID)

    def OnMouseExit(self, *args):
        if not self or self.destroyed:
            return
        self.HideFill()
        if self.value is None:
            self.label.text = localization.GetByLabel('UI/PI/Common/SurveyDashSign')
            self.opacity = 0.5
        sm.GetService('planetUI').myPinManager.OnExtractionHeadMouseExit(self.ecuID, self.headID)

    def ShowFill(self):
        if self.overlapValue:
            self.fill.height = 28
        else:
            self.fill.height = self.default_height
        self.fill.state = uiconst.UI_DISABLED

    def HideFill(self):
        self.fill.state = uiconst.UI_HIDDEN


class AreaSlider(uicls.Slider):
    __guid__ = 'uicls.AreaSlider'
    default_barPadding = 0
    default_barHeight = 13

    def ApplyAttributes(self, attributes):
        uicls.Slider.ApplyAttributes(self, attributes)
        bgCont = uiprimitives.Container(parent=self, name='bgCont', align=uiconst.TOALL, padLeft=2, idx=0)
        self.sliderFill = uiprimitives.Fill(parent=bgCont, align=uiconst.TOLEFT, pos=(0, 0, 0, 0), color=util.Color.GetGrayRGBA(1.0, 0.5))

    def Prepare_Handle_(self):
        self.handle = uiprimitives.Line(name='handle', parent=self, align=uiconst.BOTTOMLEFT, state=uiconst.UI_NORMAL, pos=(0,
         -1,
         4,
         self.height + 2), color=util.Color.WHITE, idx=0)
        self.handle.OnMouseDown = self.OnHandleMouseDown
        self.handle.OnMouseUp = self.OnHandleMouseUp
        self.handle.OnMouseMove = self.OnHandleMouseMove

    def Prepare_Label_(self):
        pass

    def OnSetValue(self, *args):
        self.sliderFill.width = self.handle.left

    def Disable(self, *args):
        uicls.Slider.Disable(self, args)
        self.handle.state = uiconst.UI_HIDDEN

    def Enable(self, *args):
        uicls.Slider.Enable(self, args)
        self.handle.state = uiconst.UI_NORMAL
