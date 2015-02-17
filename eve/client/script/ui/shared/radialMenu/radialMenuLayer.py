#Embedded file name: eve/client/script/ui/shared/radialMenu\radialMenuLayer.py
"""
    This file contains the code that makes the first and second button layers of the radial menu
"""
from carbonui.primitives.transform import Transform
import carbonui.const as uiconst
from carbonui.primitives.sprite import Sprite
import telemetry
from carbon.common.script.util import mathUtil
from eve.client.script.ui.control.themeColored import SpriteThemeColored
from eve.client.script.ui.shared.radialMenu.radialMenuActions import ActionButtonParent, RangeActionButtonParent, SecondLevelButtonParent
from eve.client.script.ui.util import uix
from eve.client.script.ui.shared.radialMenu.radialMenuUtils import RangeRadialMenuAction, SecondLevelRadialMenuAction, SimpleRadialMenuAction, FindOptionsDegree
from utillib import KeyVal

class RadialMenuLayer(Transform):
    default_align = uiconst.CENTER
    default_state = uiconst.UI_DISABLED

    def ApplyAttributes(self, attributes):
        Transform.ApplyAttributes(self, attributes)
        self.display = attributes.Get('display', True)
        self.isExpanded = False
        self.buttonDict = {}
        self.sizeInfo = attributes.sizeInfo
        self.buttonWidth = attributes.sizeInfo.buttonWidth
        self.actionDistance = attributes.sizeInfo.actionDistance
        self.actionButtonTopPadding = attributes.sizeInfo.buttonPaddingTop
        self.buttonBackgroundOpacity = attributes.Get('buttonBackgroundOpacity', 0.8)
        self.usePreciseRanges = attributes.Get('usePreciseRanges', True)

    def AnimateFromCenter(self, curveSet, animationDuration, sizeRatio, opacityRatio, grow, skipBnts):
        for eachButtonCont in self.buttonDict.values():
            if eachButtonCont in skipBnts:
                continue
            normalSize = eachButtonCont.actionDistance * 2
            if grow:
                startSize = sizeRatio * normalSize
                endSize = normalSize
                startOpacity = opacityRatio
                endOpacity = 1.0
            else:
                startSize = eachButtonCont.height
                endSize = sizeRatio * normalSize
                startOpacity = eachButtonCont.opacity
                endOpacity = opacityRatio
            eachButtonCont.actionButton.AnimateSize(sizeRatio=sizeRatio, duration=animationDuration, grow=grow)
            curveSet = uicore.animations.MorphScalar(eachButtonCont, 'height', startVal=startSize, endVal=endSize, duration=animationDuration, curveSet=curveSet)
            curveSet = uicore.animations.MorphScalar(eachButtonCont, 'width', startVal=startSize, endVal=endSize, duration=animationDuration, curveSet=curveSet)
            curveSet = uicore.animations.MorphScalar(eachButtonCont, 'opacity', startVal=startOpacity, endVal=endOpacity, duration=animationDuration, curveSet=curveSet)

        return curveSet

    @telemetry.ZONE_METHOD
    def FindMyButton(self, degree, stepSize):
        """
            finds the button container in the btnContList which matches
            the degree at which you have the mouse currently
        """
        halfStepSize = stepSize / 2.0
        if not self.buttonDict:
            return None
        if degree > 360 - halfStepSize:
            degree = 0
        for eachButtonCont in self.buttonDict.itervalues():
            if eachButtonCont.degree - halfStepSize <= degree < eachButtonCont.degree + halfStepSize:
                if eachButtonCont.actionButton.isDisabled:
                    return None
                return eachButtonCont

    def HiliteOneButtonAndGetLabel(self, btnCont):
        """
            Highlighting a specific button (or none, btn can be None) and hiding the hightlight
            for all other buttons
        """
        label = None
        for eachButtonCont in self.buttonDict.itervalues():
            if btnCont and eachButtonCont == btnCont:
                eachButtonCont.actionButton.ShowButtonHilite()
                label = btnCont.actionButton.labelText
            else:
                eachButtonCont.actionButton.HideButtonHilite()

        return label

    def Reset(self):
        self.Flush()
        self.buttonDict = {}

    def LoadButtons(self, itemID, stepSize, alternate, animate, doReset, optionsInfo, startingDegree, iconPathFunc):
        myWantedMenuOptions = optionsInfo.allWantedMenuOptions
        activeSingleOptionsDict = optionsInfo.activeSingleOptions
        inactiveSingleOptionsSet = optionsInfo.inactiveSingleOptions
        activeRangeOptions = optionsInfo.activeRangeOptions
        if doReset:
            self.Reset()
        for counter, menuOptions in enumerate(myWantedMenuOptions):
            degree = FindOptionsDegree(counter, stepSize, startingDegree=startingDegree, alternate=alternate)
            activeOption = menuOptions.activeOption
            iconTexturePath = iconPathFunc(activeOption, menuOptions)
            if isinstance(menuOptions, SimpleRadialMenuAction):
                isEmpty = activeOption is None
                actionCont = self.AddActionButton(counter=counter, degree=degree, itemID=itemID, degreeWidth=stepSize, isEmpty=isEmpty)
                if activeOption in activeSingleOptionsDict:
                    actionCont.SetButtonInfo(menuOptions, activeSingleOptionsDict[activeOption], isEnabled=True, iconTexturePath=iconTexturePath)
                elif activeOption is not None and activeOption in inactiveSingleOptionsSet:
                    actionCont.SetButtonInfo(menuOptions, None, isEnabled=False, iconTexturePath=iconTexturePath)
                else:
                    actionCont.SetDisabledIcon(texturePath=iconTexturePath)
            if isinstance(menuOptions, RangeRadialMenuAction):
                actionCont = self.AddRangeButton(counter=counter, degree=degree, itemID=itemID, degreeWidth=stepSize, rangeList=menuOptions.rangeList, defaultRange=menuOptions.defaultRange)
                if activeOption in activeRangeOptions:
                    actionCont.SetButtonInfo(menuOptions, KeyVal(func=menuOptions.callback, funcArgs=menuOptions.funcArgs), isEnabled=True, iconTexturePath=iconTexturePath)
                else:
                    actionCont.SetButtonInfo(menuOptions, KeyVal(func=None, funcArgs=None, texturePath=None), isEnabled=False, iconTexturePath=iconTexturePath)
            if isinstance(menuOptions, SecondLevelRadialMenuAction):
                actionCont = self.AddSecondLevelButton(counter=counter, degree=degree, itemID=itemID, degreeWidth=stepSize, hasExtraOptions=menuOptions.hasExtraOptions, levelType=menuOptions.levelType, texturePath=menuOptions.texturePath)
                if not menuOptions.hasExtraOptions:
                    actionCont.SetDisabledIcon(texturePath=iconTexturePath)
            iconOffset = getattr(menuOptions, 'iconOffset', None)
            if iconOffset is not None:
                actionCont.SetIconOffset(iconOffset)
            if animate:
                self.AnimateButtonsIn(startingDegree)

    def AnimateButtonsIn(self, startingDegree):
        curveSet = None
        for eachButton in self.buttonDict.itervalues():
            degreeToUse = eachButton.degree
            if eachButton.degree > 180 + startingDegree:
                degreeToUse = degreeToUse - 360
            radians = mathUtil.DegToRad(degreeToUse)
            startRad = mathUtil.DegToRad(startingDegree)
            animationDuration = uix.GetTiDiAdjustedAnimationTime(normalDuation=0.25, minTiDiValue=0.1, minValue=0.02)
            curveSet = uicore.animations.MorphScalar(eachButton, 'rotation', startVal=-startRad, endVal=-radians, duration=animationDuration, curveSet=curveSet)

    def AddActionButton(self, counter, degree, isEmpty = False, *args, **kw):
        actionCont = self.buttonDict.get(counter, None)
        if actionCont is None or actionCont.destroyed:
            actionCont = ActionButtonParent(parent=self, pos=(0,
             0,
             self.buttonWidth,
             self.actionDistance * 2), buttonBackgroundOpacity=self.buttonBackgroundOpacity, degree=degree, sizeInfo=self.sizeInfo, isEmpty=isEmpty, actionKeywords=kw)
            self.buttonDict[counter] = actionCont
        return actionCont

    def AddRangeButton(self, counter, degree, *args, **kw):
        actionCont = self.buttonDict.get(counter, None)
        if actionCont is None or actionCont.destroyed:
            actionCont = RangeActionButtonParent(parent=self, pos=(0,
             0,
             self.buttonWidth,
             self.actionDistance * 2), buttonBackgroundOpacity=self.buttonBackgroundOpacity, usePreciseRanges=self.usePreciseRanges, degree=degree, sizeInfo=self.sizeInfo, actionKeywords=kw)
            self.buttonDict[counter] = actionCont
        return actionCont

    def AddSecondLevelButton(self, counter, degree, *args, **kw):
        actionCont = self.buttonDict.get(counter, None)
        if actionCont is None or actionCont.destroyed:
            actionCont = SecondLevelButtonParent(parent=self, pos=(0,
             0,
             self.buttonWidth,
             self.actionDistance * 2), buttonBackgroundOpacity=self.buttonBackgroundOpacity, degree=degree, sizeInfo=self.sizeInfo, actionKeywords=kw)
            self.buttonDict[counter] = actionCont
        return actionCont


class RadialMenuShadow(SpriteThemeColored):
    default_name = 'radialMenuShadow'
    default_state = uiconst.UI_DISABLED
    default_align = uiconst.CENTER
    default_colorType = uiconst.COLORTYPE_UIBASE

    def ApplyAttributes(self, attributes):
        SpriteThemeColored.ApplyAttributes(self, attributes)
        self.shadowSize = attributes.shadowSize

    def AnimateFromCenter(self, animationDuration, sizeRatio, opacityRatio, grow):
        if grow:
            shadowStartValue = sizeRatio * self.shadowSize
            shadowEndValue = self.shadowSize
            startOpacity = opacityRatio
            endOpacity = 1.3
        else:
            shadowStartValue = self.shadowSize
            shadowEndValue = sizeRatio * self.shadowSize
            startOpacity = self.opacity
            endOpacity = opacityRatio
        curveSet = None
        uicore.animations.MorphScalar(self, 'height', startVal=shadowStartValue, endVal=shadowEndValue, duration=animationDuration, curveSet=curveSet)
        uicore.animations.MorphScalar(self, 'width', startVal=shadowStartValue, endVal=shadowEndValue, duration=animationDuration, curveSet=curveSet)
        uicore.animations.MorphScalar(self, 'opacity', startVal=startOpacity, endVal=endOpacity, duration=animationDuration, curveSet=curveSet)
