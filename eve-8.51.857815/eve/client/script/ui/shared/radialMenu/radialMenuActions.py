#Embedded file name: eve/client/script/ui/shared/radialMenu\radialMenuActions.py
"""
    this file contains the buttons in the radial menu
"""
from eve.client.script.ui.control.eveWindowUnderlay import SpriteUnderlay
from eve.client.script.ui.control.glowSprite import GlowSprite
import uiprimitives
import uicontrols
import carbonui.const as uiconst
import uicls
import localization
from carbonui.primitives.transform import Transform
import types
import mathUtil
import telemetry
import uix

class RadialMenuActionBase(uiprimitives.Transform):
    """
        this is the base for the buttons in the radial menu
    """
    __guid__ = 'uicls.RadialMenuActionBase'
    default_left = 0
    default_top = 0
    default_align = uiconst.CENTERTOP
    default_state = uiconst.UI_NORMAL
    moveOverSliceBasePath = 'res:/UI/Texture/classes/RadialMenu/mouseOver_%s.png'
    selelectedBasePath = 'res:/UI/Texture/classes/RadialMenu/selected_%s.png'
    emptySliceBasePath = 'res:/UI/Texture/classes/RadialMenu/emptySlice_%s.png'
    sliceBasePath = 'res:/UI/Texture/classes/RadialMenu/slice_%s.png'
    default_width = 100
    default_height = 70
    default_fullWidth = default_width
    default_fullHeight = default_height

    def ApplyAttributes(self, attributes):
        uiprimitives.Transform.ApplyAttributes(self, attributes)
        self.degree = attributes.get('degree', 0)
        self.func = None
        self.funcArgs = None
        self.itemID = attributes.itemID
        self.isDisabled = False
        self.degreeWidth = attributes.degreeWidth
        self.labelPath = ''
        self.labelText = ''
        self.isEmpty = attributes.get('isEmpty', False)
        self.commandName = None
        self.isHilighted = False
        self.fullWidth = attributes.sizeInfo.buttonWidth
        self.fullHeight = attributes.sizeInfo.buttonHeight
        iconPar = uiprimitives.Transform(parent=self, name='iconPar', pos=(0, 3, 32, 32), state=uiconst.UI_DISABLED, align=uiconst.CENTER)
        iconPar.rotation = mathUtil.DegToRad(self.degree)
        self.icon = GlowSprite(parent=iconPar, name='icon', pos=(0, 0, 32, 32), state=uiconst.UI_DISABLED, align=uiconst.CENTER)
        selectionSlice = SpriteUnderlay(parent=self, name='selectionSlice', state=uiconst.UI_DISABLED, texturePath=self.selelectedBasePath % self.degreeWidth, align=uiconst.TOALL, opacity=0.9)
        selectionSlice.display = False
        self.selectionSlice = selectionSlice
        if self.isEmpty:
            sliceTexturePath = self.emptySliceBasePath % self.degreeWidth
        else:
            sliceTexturePath = self.sliceBasePath % self.degreeWidth
        self.hilite = SpriteUnderlay(parent=self, name='hilite', state=uiconst.UI_DISABLED, texturePath=self.selelectedBasePath % self.degreeWidth, align=uiconst.TOALL, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW, opacity=0.0)
        self.availableSlice = SpriteUnderlay(parent=self, name='availableSlice', state=uiconst.UI_DISABLED, texturePath=sliceTexturePath, align=uiconst.TOALL, opacity=attributes.get('buttonBackgroundOpacity', 0.8))
        self.unavailableSlice = SpriteUnderlay(parent=self, name='unavailableSlice', state=uiconst.UI_DISABLED, texturePath=sliceTexturePath, align=uiconst.TOALL, colorType=uiconst.COLORTYPE_UIBASE, opacity=0.85)
        self.unavailableSlice.display = False
        self.sliceInUse = self.availableSlice

    def SetButtonInfo(self, labelPath, labelArgs, buttonInfo = None, isEnabled = True, iconTexturePath = None):
        self.labelPath = labelPath
        if isEnabled:
            self.labelText = localization.GetByLabel(labelPath, **labelArgs)
        else:
            self.labelText = ''
        self.name = 'actionButton_%s' % labelPath.split('/')[-1]
        if isEnabled:
            self.SetEnabled()
        else:
            self.SetDisabled()
        if iconTexturePath is not None:
            self.SetIcon(iconTexturePath)
        if buttonInfo is None:
            return
        buttonFunc = buttonInfo.func
        buttonFuncArgs = buttonInfo.funcArgs
        if not isinstance(buttonFunc, (types.MethodType, types.LambdaType)):
            return
        self.func = buttonFunc
        self.funcArgs = buttonFuncArgs
        self.commandName = getattr(buttonInfo, 'commandName', None)

    @telemetry.ZONE_METHOD
    def ShowButtonHilite(self):
        if self.isHilighted:
            return
        uicore.animations.FadeTo(self.hilite, self.hilite.opacity, 0.15, duration=uiconst.TIME_ENTRY)
        self.isHilighted = True
        sm.GetService('audio').SendUIEvent('ui_radial_mouseover_play')
        self.icon.OnMouseEnter()

    @telemetry.ZONE_METHOD
    def HideButtonHilite(self):
        if not self.isHilighted:
            return
        uicore.animations.FadeTo(self.hilite, self.hilite.opacity, 0.0, duration=uiconst.TIME_EXIT)
        self.isHilighted = False
        self.sliceInUse.Show()
        if self.isDisabled:
            self.icon.opacity = 0.4
        else:
            self.icon.opacity = 1.0
        self.icon.OnMouseExit()

    def ShowSelectionSlice(self):
        self.availableSlice.display = False
        self.unavailableSlice.display = False
        self.selectionSlice.display = True

    def SetIcon(self, texturePath):
        self.icon.SetTexturePath(texturePath)

    def SetDisabled(self):
        if self.sliceInUse != self.unavailableSlice:
            self.sliceInUse = self.unavailableSlice
            self.availableSlice.display = False
            self.unavailableSlice.display = True
        self.isDisabled = True
        self.icon.opacity = 0.4

    def SetEnabled(self):
        if self.sliceInUse != self.availableSlice:
            self.sliceInUse = self.availableSlice
            self.unavailableSlice.display = False
            self.availableSlice.display = True
        self.isDisabled = False
        self.icon.opacity = 1.0

    def AnimateSize(self, sizeRatio = 0.5, duration = 0.5, grow = True):
        if grow:
            startHeight = sizeRatio * self.fullHeight
            startWidth = sizeRatio * self.fullWidth
            endHeight = self.fullHeight
            endWidth = self.fullWidth
        else:
            startHeight = self.height
            startWidth = self.width
            endHeight = sizeRatio * self.fullHeight
            endWidth = sizeRatio * self.fullWidth
        uicore.animations.MorphScalar(self, 'height', startVal=startHeight, endVal=endHeight, duration=duration)
        uicore.animations.MorphScalar(self, 'width', startVal=startWidth, endVal=endWidth, duration=duration)

    def SelectButtonSlice(self, duration = 0.5):
        self.ShowSelectionSlice()
        animationDuration = uix.GetTiDiAdjustedAnimationTime(duration, minTiDiValue=0.1, minValue=0.02)
        curvePoints = ([0.0, 0], [0.5, -10], [1, -10])
        uicore.animations.MorphScalar(self, 'top', duration=animationDuration, curveType=curvePoints, sleep=False)
        curvePoints = ([0.0, self.selectionSlice.opacity],
         [0.5, self.selectionSlice.opacity],
         [0.6, 1.5],
         [0.7, 0.5],
         [0.8, 1.5],
         [1, 0])
        uicore.animations.MorphScalar(self, 'opacity', duration=animationDuration, curveType=curvePoints, sleep=True)


class RadialMenuAction(RadialMenuActionBase):
    """
        this is the regular button in the radial menu
    """
    __guid__ = 'uicls.RadialMenuAction'

    def OnButtonClick(self):
        if self.func:
            if self.funcArgs and isinstance(self.funcArgs[0], tuple) and isinstance(self.funcArgs[0][0], (types.MethodType, types.LambdaType)):
                self.func(*self.funcArgs[0])
            else:
                self.func(*self.funcArgs)
            return True
        return False


class RadialMenuRangeAction(RadialMenuActionBase):
    """
        this is the regular button in the radial menu
    """
    __guid__ = 'uicls.RadialMenuRangeAction'

    def ApplyAttributes(self, attributes):
        uicls.RadialMenuActionBase.ApplyAttributes(self, attributes)
        self.rangeList = attributes.rangeList
        self.defaultRange = attributes.defaultRange
        self.percOfAllRange = None
        self.currentRange = self.defaultRange
        self.minRangeDistance = attributes.sizeInfo.actionDistance
        self.actionButtonTopPadding = attributes.get('actionButtonTopPadding', 0)
        self.usePreciseRanges = attributes.get('usePreciseRanges', True)
        self.maxRangeDistance = 300
        self.lastLength = None
        self.rangeArrow = uiprimitives.Sprite(parent=self, name='rangeArrow', pos=(0,
         self.actionButtonTopPadding + 1,
         18,
         12), state=uiconst.UI_DISABLED, align=uiconst.CENTERTOP, texturePath='res:/UI/Texture/classes/RadialMenu/rangeArrow.png', idx=0)

    def SetEnabled(self):
        uicls.RadialMenuActionBase.SetEnabled(self)
        self.rangeArrow.opacity = 1.0

    def SetDisabled(self):
        uicls.RadialMenuActionBase.SetDisabled(self)
        self.rangeArrow.opacity = 0.4

    def MoveMouse(self, length, currentDegree):
        if self.isDisabled:
            self.currentRange = None
            self.percOfAllRange = None
            return (self.currentRange, self.percOfAllRange)
        if length < self.minRangeDistance - self.actionButtonTopPadding:
            self.currentRange = self.defaultRange
            self.percOfAllRange = None
            return (self.currentRange, self.percOfAllRange)
        numRangeOptions = len(self.rangeList)
        lengthInEachStep = float((self.maxRangeDistance - self.minRangeDistance) / numRangeOptions)
        lengthInRangeMeasurer = length - self.minRangeDistance
        lengthInRangeMeasurer = self.FindLengthToUse(lengthInRangeMeasurer, currentDegree)
        for i, eachRange in enumerate(self.rangeList):
            lengthForThisStep = i * lengthInEachStep
            if lengthInRangeMeasurer > lengthForThisStep:
                continue
            if i == 0:
                self.currentRange = eachRange
                self.percOfAllRange = 0
                return (self.currentRange, self.percOfAllRange)
            lengthForPreviousStep = lengthInEachStep * (i - 1)
            previousStepDistance = self.rangeList[i - 1]
            lengthInThisStep = lengthInRangeMeasurer - lengthForPreviousStep
            percOfStep = float(lengthInThisStep) / lengthInEachStep
            if self.usePreciseRanges:
                currentRange = percOfStep * (eachRange - previousStepDistance) + previousStepDistance
            else:
                currentRange = previousStepDistance
            percOfEachStep = 1.0 / (numRangeOptions - 1)
            percOfAllRange = (i - 1 + percOfStep) * percOfEachStep
            self.currentRange = currentRange
            self.percOfAllRange = percOfAllRange
            return (currentRange, self.percOfAllRange)
        else:
            self.currentRange = self.rangeList[-1]
            return (self.currentRange, 1)

    def FindLengthToUse(self, length, currentDegree):
        if self.lastLength is None:
            self.lastLength = length
        halfDegreeWidth = self.degreeWidth / 2.0
        if not self.degree - halfDegreeWidth < currentDegree < self.degree + halfDegreeWidth:
            dx, dy = uicore.uilib.dx, uicore.uilib.dy
            if 90 < self.degree < 270:
                length = self.lastLength + dy
            else:
                length = self.lastLength - dy
        length = max(0, length)
        self.lastLength = length
        return length

    def OnButtonClick(self):
        if self.func and self.currentRange is not None:
            self.func(self.funcArgs, self.currentRange, self.percOfAllRange)


class RadialMenuActioSecondLevel(RadialMenuActionBase):
    """
        this is the button parent in the radial menu
    """
    __guid__ = 'uicls.RadialMenuActioSecondLevel'

    def ApplyAttributes(self, attributes):
        uicls.RadialMenuActionBase.ApplyAttributes(self, attributes)
        self.icon.SetTexturePath(attributes.texturePath)
        self.hasExtraOptions = attributes.hasExtraOptions
        self.levelType = attributes.levelType

    def MoveMouse(self, length, currentDegree):
        return True


class ActionParent(Transform):
    default_align = uiconst.CENTER
    default_name = 'radialmenuActionParent'

    def ApplyAttributes(self, attributes):
        Transform.ApplyAttributes(self, attributes)
        degree = attributes.degree
        radians = mathUtil.DegToRad(degree)
        self.rotation = -radians
        self.actionDistance = attributes.sizeInfo.actionDistance
        self.degree = degree

    def SetButtonInfo(self, menuOptions, buttonInfo, isEnabled, iconTexturePath):
        activeOption = menuOptions.activeOption
        labelArgs = getattr(menuOptions, 'labelArgs', {})
        self.actionButton.SetButtonInfo(activeOption, labelArgs, buttonInfo, isEnabled=isEnabled, iconTexturePath=iconTexturePath)

    def SetDisabledIcon(self, texturePath):
        self.actionButton.SetIcon(texturePath=texturePath)
        self.actionButton.SetDisabled()

    def SetIconOffset(self, iconOffset):
        self.actionButton.icon.parent.top = iconOffset


class ActionButtonParent(ActionParent):

    def ApplyAttributes(self, attributes):
        ActionParent.ApplyAttributes(self, attributes)
        actionButton = RadialMenuAction(parent=self, name='actionButton', sizeInfo=attributes.sizeInfo, degree=attributes.degree, isEmpty=attributes.isEmpty, buttonBackgroundOpacity=attributes.buttonBackgroundOpacity, **attributes.actionKeywords)
        self.actionButton = actionButton


class RangeActionButtonParent(ActionParent):

    def ApplyAttributes(self, attributes):
        ActionParent.ApplyAttributes(self, attributes)
        actionButton = RadialMenuRangeAction(parent=self, name='rangeButton', sizeInfo=attributes.sizeInfo, degree=attributes.degree, actionButtonTopPadding=attributes.sizeInfo.buttonPaddingTop, usePreciseRanges=attributes.usePreciseRanges, buttonBackgroundOpacity=attributes.buttonBackgroundOpacity, **attributes.actionKeywords)
        self.actionButton = actionButton


class SecondLevelButtonParent(ActionParent):
    default_name = 'secondLevelButtonParent'

    def ApplyAttributes(self, attributes):
        ActionParent.ApplyAttributes(self, attributes)
        self.levelType = attributes.actionKeywords['levelType']
        actionButton = RadialMenuActioSecondLevel(parent=self, name='secondLevelButton', sizeInfo=attributes.sizeInfo, degree=attributes.degree, buttonBackgroundOpacity=attributes.buttonBackgroundOpacity, **attributes.actionKeywords)
        self.actionButton = actionButton
