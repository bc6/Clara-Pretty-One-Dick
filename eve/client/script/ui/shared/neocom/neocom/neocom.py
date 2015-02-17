#Embedded file name: eve/client/script/ui/shared/neocom/neocom\neocom.py
"""
The actual neocom UI object that contains all other neocom objects. The data behind the 
buttons comes from the neocomSvc
"""
import carbonui.const as uiconst
from eve.client.script.ui.control.eveWindowUnderlay import BlurredSceneUnderlay
import uiprimitives
import uicontrols
import util
import uthread
import neocomButtons as neocom
import blue
import characterskills.util
import service
import uiutil
import trinity
import telemetry

class Neocom(uiprimitives.Container):
    __guid__ = 'neocom.Neocom'
    __notifyevents__ = ['OnHeadNodeChanged',
     'OnSkillStarted',
     'OnSkillQueueRefreshed',
     'OnSkillPaused',
     'OnEveMenuOpened',
     'OnEveMenuClosed',
     'OnCameraDragStart',
     'OnCameraDragEnd']
    default_name = 'Neocom'
    default_align = uiconst.TOLEFT
    default_state = uiconst.UI_NORMAL
    default_width = 40
    COLOR_CORNERFILL = (0, 0, 0, 0.5)
    NEOCOM_MINSIZE = 32
    NEOCOM_MAXSIZE = 64

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.updateClockThread = None
        self.autoHideActive = settings.char.ui.Get('neocomAutoHideActive', False)
        self.align = settings.char.ui.Get('neocomAlign', self.default_align)
        self.isHidden = False
        self.overflowButtons = []
        self.isResizingNeocom = False
        self.updateSkillThread = None
        self.width = settings.user.windows.Get('neocomWidth', self.default_width)
        self.resizeLineCont = uiprimitives.Container(parent=self, name='resizeLineCont', align=uiconst.TOALL)
        self.mainCont = uiprimitives.Container(parent=self, name='mainCont', align=uiconst.TOALL)
        self._ConstructBackground()
        self._ConstructBaseLayout()
        self._ConstructClock()
        self._ConstructCharCont()
        self.UpdateButtons()
        self.UpdateClock()
        if self.autoHideActive:
            self.HideNeocom()
        isElevated = eve.session.role & service.ROLEMASK_ELEVATEDPLAYER
        if isElevated and settings.public.ui.Get('Insider', True):
            try:
                insider = sm.GetService('insider')
                uthread.new(insider.Show, True, True)
            except ServiceNotFound:
                pass

    def _ConstructBackground(self):
        self.bgGradient = uicontrols.GradientSprite(bgParent=self, rgbData=((0, (1.0, 1.0, 1.0)),), alphaData=((0.0, 0.0), (1.0, 0.07)))
        self.blurredUnderlay = BlurredSceneUnderlay(bgParent=self, isPinned=True, isInFocus=True)
        if self.align == uiconst.TOLEFT:
            align = uiconst.TORIGHT
        else:
            align = uiconst.TOLEFT
        self.resizeLine = uiprimitives.Line(parent=self.resizeLineCont, color=(0, 0, 0, 0), align=align, weight=3, state=uiconst.UI_NORMAL)
        self.resizeLine.OnMouseDown = self.OnReisizeLineMouseDown
        self.resizeLine.OnMouseEnter = self.OnResizeLineMouseEnter
        self.SetResizeLineCursor()

    def OnCameraDragStart(self):
        self.blurredUnderlay.isCameraDragging = True
        self.blurredUnderlay.UpdateState()

    def OnCameraDragEnd(self):
        self.blurredUnderlay.isCameraDragging = False
        self.blurredUnderlay.UpdateState()

    def SetResizeLineCursor(self):
        if self.IsSizeLocked():
            self.resizeLine.cursor = None
        else:
            self.resizeLine.cursor = uiconst.UICURSOR_LEFT_RIGHT_DRAG

    def OnReisizeLineMouseDown(self, *args):
        if not self.IsSizeLocked():
            uthread.new(self.OnResizerDrag)

    def OnResizeLineMouseEnter(self, *args):
        if self.isHidden:
            self.UnhideNeocom()

    def OnResizerDrag(self, *args):
        while uicore.uilib.leftbtn and not self.destroyed:
            self.isResizingNeocom = True
            if self.align == uiconst.TOLEFT:
                width = uicore.uilib.x
            elif self.align == uiconst.TORIGHT:
                width = uicore.desktop.width - uicore.uilib.x
            if width != self.width:
                self.width = max(self.NEOCOM_MINSIZE, min(width, self.NEOCOM_MAXSIZE))
                self._ConstructCharCont()
                settings.user.windows.Set('neocomWidth', self.width)
                sm.ScatterEvent('OnNeocomResized')
            sm.GetService('window').UpdateIntersectionBackground()
            blue.synchro.SleepWallclock(100)

        self.isResizingNeocom = False

    def _ConstructBaseLayout(self):
        self.charCont = uicontrols.ContainerAutoSize(parent=self.mainCont, name='charCont', align=uiconst.TOTOP)
        self.clockCont = neocom.WrapperButton(parent=self.mainCont, name='clockCont', align=uiconst.TOBOTTOM, height=20, cmdName='OpenCalendar')
        self.fixedButtonCont = uicontrols.ContainerAutoSize(parent=self.mainCont, name='fixedButtonCont', align=uiconst.TOBOTTOM)
        uiprimitives.Fill(bgParent=self.fixedButtonCont, color=self.COLOR_CORNERFILL, blendMode=trinity.TR2_SBM_ADD)
        self.overflowBtn = neocom.OverflowButton(parent=self.mainCont, align=uiconst.TOBOTTOM, state=uiconst.UI_HIDDEN, height=20)
        self.buttonCont = uiprimitives.Container(parent=self.mainCont, name='buttonCont', align=uiconst.TOALL)
        self.dropIndicatorLine = uiprimitives.Line(parent=self.mainCont, name='dropIndicatorLine', align=uiconst.TOPLEFT, color=util.Color.GetGrayRGBA(0.7, 0.3), pos=(0, 0, 0, 1))

    def _ConstructCharCont(self):
        self.charCont.Flush()
        self.eveMenuBtn = neocom.ButtonEveMenu(parent=self.charCont, name='eveMenuBtn', align=uiconst.TOTOP, height=30, cmdName='OpenEveMenu', btnData=sm.GetService('neocom').eveMenuBtnData)
        self.charSheetBtn = neocom.WrapperButton(parent=self.charCont, name='charSheetBtn', align=uiconst.TOTOP, height=self.width, cmdName='OpenCharactersheet')
        self.skillTrainingCont = neocom.WrapperButton(parent=self.charCont, name='skillTrainingCont', align=uiconst.TOTOP, height=9, cmdName='OpenSkillQueueWindow')
        self.skillTrainingFill = uiprimitives.Sprite(parent=uiprimitives.Container(parent=self.skillTrainingCont, state=uiconst.UI_DISABLED), name='trainingProgressFill', align=uiconst.TOLEFT_PROP, texturePath='res:/UI/Texture/classes/Neocom/trainingGradient.png', padding=1)
        uicontrols.Frame(parent=self.skillTrainingCont, cornerSize=3, name='trainingProgressBG', align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/Neocom/trainingBG.png', color=(1.0, 1.0, 1.0, 1.0))
        if self.updateSkillThread:
            self.updateSkillThread.kill()
        self.updateSkillThread = uthread.new(self._UpdateSkillInfo)
        charPic = uiprimitives.Sprite(parent=self.charSheetBtn, name='charPic', ignoreSize=True, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        sm.GetService('photo').GetPortrait(eve.session.charid, 256, charPic)

    def _UpdateSkillInfo(self):
        """
        Update training progress every 5 seconds
        """
        while not self.destroyed:
            self._UpdateSkillBar()
            blue.pyos.synchro.Sleep(5000)

    def _UpdateSkillBar(self):
        skill = sm.StartService('skills').SkillInTraining()
        if not skill:
            trainingProgressRatio = 0.0
        else:
            currSkillPoints = sm.GetService('skillqueue').GetSkillPointsFromSkillObject(skill)
            skillPointsAtStartOfLevel = characterskills.util.GetSPForLevelRaw(skill.skillTimeConstant, skill.skillLevel)
            trainingProgressRatio = (currSkillPoints - skillPointsAtStartOfLevel) / float(skill.spHi - skillPointsAtStartOfLevel)
        if trainingProgressRatio == 0.0:
            self.skillTrainingFill.Hide()
        else:
            self.skillTrainingFill.Show()
            self.skillTrainingFill.width = trainingProgressRatio

    def OnSkillStarted(self, typeID = None, level = None):
        self._UpdateSkillBar()

    def OnSkillQueueRefreshed(self):
        self._UpdateSkillBar()

    def OnSkillPaused(self, typeID):
        self._UpdateSkillBar()

    @telemetry.ZONE_METHOD
    def UpdateButtons(self):
        self.fixedButtonCont.Flush()
        if session.stationid is not None:
            scopeSpecificButtonData = sm.GetService('neocom').GetScopeSpecificButtonData()
            if scopeSpecificButtonData is not None:
                for i, btnData in enumerate(scopeSpecificButtonData.children):
                    btnClass = neocom.GetBtnClassByBtnType(btnData)
                    btnUI = btnClass(parent=self.fixedButtonCont, name=btnData.id, btnData=btnData, align=uiconst.TOPLEFT, btnNum=i, width=self.width, isDraggable=False)
                    btnData.btnUI = btnUI

        self.buttonCont.Flush()
        isDraggable = not self.IsSizeLocked()
        for i, btnData in enumerate(sm.GetService('neocom').GetButtonData()):
            btnClass = neocom.GetBtnClassByBtnType(btnData)
            btnUI = btnClass(parent=self.buttonCont, name=btnData.id, btnData=btnData, align=uiconst.TOPLEFT, btnNum=i, width=self.width, isDraggable=isDraggable)
            btnData.btnUI = btnUI

        self.CheckOverflow()
        sm.GetService('neocom').OnNeocomButtonsRecreated()

    def CheckOverflow(self):
        self.overflowButtons = []
        w, h = self.buttonCont.GetAbsoluteSize()
        for btnUI in self.buttonCont.children:
            if btnUI.top + btnUI.height > h:
                btnUI.Hide()
                self.overflowButtons.append(btnUI.btnData)
            else:
                btnUI.Show()

        if self.overflowButtons:
            newState = uiconst.UI_NORMAL
        else:
            newState = uiconst.UI_HIDDEN
        if self.overflowBtn.state != newState:
            self.overflowBtn.state = newState
            self.CheckOverflow()

    def _ConstructClock(self):
        clockMain = uiprimitives.Container(parent=self.clockCont, align=uiconst.TOALL)
        uiprimitives.Fill(parent=self.clockCont, color=self.COLOR_CORNERFILL)
        self.clockLabel = uicontrols.Label(parent=clockMain, name='clockLabel', align=uiconst.CENTER, fontsize=11)

    def UpdateClock(self):
        if self.updateClockThread:
            self.updateClockThread.kill()
        self.updateClockThread = uthread.new(self._UpdateClock)

    def _UpdateClock(self):
        chinaOffset = 0
        if boot.region == 'optic':
            chinaOffset = 8 * const.HOUR
        while not self.destroyed:
            year, month, weekday, day, hour, minute, second, msec = blue.os.GetTimeParts(blue.os.GetTime() + chinaOffset)
            self.clockLabel.text = '<b>%2.2i:%2.2i' % (hour, minute)
            blue.synchro.SleepWallclock(5000)

    def GetMenu(self):
        return sm.GetService('neocom').GetMenu()

    def SetSizeLocked(self, isLocked):
        settings.char.ui.Set('neocomSizeLocked', isLocked)
        self.SetResizeLineCursor()
        for btn in self.buttonCont.children:
            btn.SetDraggable(not isLocked)

    def IsSizeLocked(self):
        return settings.char.ui.Get('neocomSizeLocked', False)

    def IsAutoHideActive(self):
        return settings.char.ui.Get('neocomAutoHideActive', False)

    def SetAutoHideOn(self):
        settings.char.ui.Set('neocomAutoHideActive', True)
        self.autoHideActive = True
        uthread.new(self.AutoHideThread)

    def SetAutoHideOff(self):
        settings.char.ui.Set('neocomAutoHideActive', False)
        self.autoHideActive = False
        self.UnhideNeocom()

    def SetAlignRight(self):
        settings.char.ui.Set('neocomAlign', uiconst.TORIGHT)
        self.align = uiconst.TORIGHT
        self.resizeLine.align = uiconst.TOLEFT
        self.overflowBtn.UpdateIconRotation()
        self.SetOrder(0)

    def SetAlignLeft(self):
        settings.char.ui.Set('neocomAlign', uiconst.TOLEFT)
        self.align = uiconst.TOLEFT
        self.resizeLine.align = uiconst.TORIGHT
        self.overflowBtn.UpdateIconRotation()
        self.SetOrder(0)

    def OnDropData(self, source, dropData):
        if not sm.GetService('neocom').IsValidDropData(dropData):
            return
        sm.GetService('neocom').OnBtnDataDropped(dropData[0])

    def OnDragEnter(self, panelEntry, dropData):
        if not sm.GetService('neocom').IsValidDropData(dropData):
            return
        sm.GetService('neocom').OnButtonDragEnter(sm.GetService('neocom').btnData, dropData[0])

    def OnDragExit(self, *args):
        self.HideDropIndicatorLine()

    def OnHeadNodeChanged(self, id):
        if id == 'neocom':
            self.UpdateButtons()
            self.HideDropIndicatorLine()

    def _OnSizeChange_NoBlock(self, width, height):
        uthread.new(self.UpdateButtons)

    def HideNeocom(self):
        endVal = 3 - self.width
        uicore.animations.MorphScalar(self, 'left', self.left, endVal, duration=0.7)
        self.isHidden = True

    def UnhideNeocom(self, sleep = False):
        if not self.isHidden:
            return
        uicore.animations.MorphScalar(self, 'left', self.left, 0, duration=0.2, sleep=sleep)
        self.isHidden = False
        if self.autoHideActive:
            uthread.new(self.AutoHideThread)

    def AutoHideThread(self):
        mouseNotOverTime = blue.os.GetTime()
        while not self.destroyed:
            blue.pyos.synchro.Sleep(50)
            if not self or self.destroyed:
                return
            if not self.IsAutoHideActive():
                return
            mo = uicore.uilib.mouseOver
            if mo == self or uiutil.IsUnder(mo, self):
                mouseNotOverTime = blue.os.GetTime()
                continue
            if sm.GetService('neocom').IsSomePanelOpen() or self.isResizingNeocom:
                mouseNotOverTime = blue.os.GetTime()
                continue
            if uicore.layer.menu.children:
                mouseNotOverTime = blue.os.GetTime()
                continue
            if sm.GetService('neocom').IsDraggingButtons():
                mouseNotOverTime = blue.os.GetTime()
                continue
            if blue.os.GetTime() - mouseNotOverTime > const.SEC:
                self.HideNeocom()
                return

    def ShowDropIndicatorLine(self, index):
        l, t = self.buttonCont.GetAbsolutePosition()
        self.dropIndicatorLine.state = uiconst.UI_DISABLED
        self.dropIndicatorLine.top = t + index * self.width
        self.dropIndicatorLine.width = self.width

    def HideDropIndicatorLine(self):
        self.dropIndicatorLine.state = uiconst.UI_HIDDEN

    def OnEveMenuOpened(self):
        for btn in self.buttonCont.children:
            uicore.animations.FadeTo(btn, btn.opacity, 0.5, duration=0.3)
            blue.synchro.SleepWallclock(20)

    def OnEveMenuClosed(self):
        for btn in self.buttonCont.children:
            uicore.animations.FadeTo(btn, btn.opacity, 1.0, duration=0.3)
