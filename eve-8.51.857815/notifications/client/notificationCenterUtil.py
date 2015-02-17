#Embedded file name: notifications/client\notificationCenterUtil.py
from notifications.client.notificationSettings.notificationSettingConst import ExpandAlignmentConst

class ExpandEvaluator:

    def __init__(self, screenHeight, screenWidth, preferredHeight, minHistoryHeight, maxHistoryHeight, expandWidth):
        self.screenHeight = screenHeight
        self.screenWidth = screenWidth
        self.preferredHeight = preferredHeight
        self.customX = screenWidth
        self.customY = screenHeight
        self.actualX = 0
        self.actualY = 0
        self.minHistoryHeight = minHistoryHeight
        self.maxHistoryHeight = maxHistoryHeight
        self._updateActualXY()
        self.expandWidth = expandWidth

    def _updateActualXY(self):
        self.actualX = self.screenWidth - self.customX
        self.actualY = self.screenHeight - self.customY

    def SetScreenSize(self, width, height):
        self.screenWidth = width
        self.screenHeight = height
        self._updateActualXY()

    def SetWidgetInversePosition(self, x, y):
        self.customX = x
        self.customY = y
        self._updateActualXY()

    def SetWidgetPositon(self, x, y):
        self.SetWidgetInversePosition(self.screenWidth - x, self.screenHeight - y)

    def GetAdjustedHeightValue(self):
        endTopValue = self.screenHeight - self.preferredHeight - self.customY
        if endTopValue < 0:
            return self.preferredHeight + endTopValue
        return self.preferredHeight

    def CanExpandUp(self):
        return self.GetAdjustedHeightValue() >= self.minHistoryHeight

    def CanExpandDown(self):
        return self.GetAdjustedHeightForDownExpand() >= self.minHistoryHeight

    def CanExpandLeft(self):
        return self.actualX - self.expandWidth > 0

    def CanExpandRight(self):
        return self.actualX + self.expandWidth < self.screenWidth

    def GetAdjustedHeightForDownExpand(self):
        if self.preferredHeight + self.actualY > self.screenHeight:
            heightOvershoot = self.preferredHeight + self.actualY - self.screenHeight
            return self.preferredHeight - heightOvershoot
        return self.preferredHeight


from notifications.client.notificationSettings.notificationSettingConst import ExpandAlignmentConst

class AlignmentTransitioner:

    def __init__(self, verticalAlignment, horizontalAlignment, wantedVertical, wantedHorizontal, expandEvaluator):
        self.wantedVerticalAlignment = wantedVertical
        self.wantedHorizontalAlignment = wantedHorizontal
        self.neededVerticalAlignment = None
        self.neededHorizontalAlignment = None
        self.SetAlignments(verticalAlignment=verticalAlignment, horizontalAlignment=horizontalAlignment)
        self.expandEvaluator = expandEvaluator

    def SetAlignments(self, verticalAlignment, horizontalAlignment):
        self.verticalAlignment = verticalAlignment
        self.horizontalAlignment = horizontalAlignment
        self._CalculateNeeded()

    def _CalculateNeeded(self):
        if self.verticalAlignment != self.wantedVerticalAlignment:
            self.neededVerticalAlignment = self.verticalAlignment
        else:
            self.neededVerticalAlignment = None
        if self.horizontalAlignment != self.wantedHorizontalAlignment:
            self.neededHorizontalAlignment = self.horizontalAlignment
        else:
            self.neededHorizontalAlignment = None

    def CheckVerticalAlignBackNeeded(self):
        expand = self.expandEvaluator
        adjustedAlignment = self.verticalAlignment
        reAlignNeeded = False
        if self.wantedVerticalAlignment != self.verticalAlignment:
            if self.verticalAlignment is ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_UP and expand.CanExpandDown():
                adjustedAlignment = ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_DOWN
            elif self.verticalAlignment is ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_DOWN and expand.CanExpandUp():
                adjustedAlignment = ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_UP
        return adjustedAlignment

    def CheckHorizontalAlignBackNeeded(self):
        expand = self.expandEvaluator
        adjustedAlignment = self.horizontalAlignment
        if self.wantedHorizontalAlignment != self.horizontalAlignment:
            if self.horizontalAlignment is ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_LEFT and expand.CanExpandRight():
                adjustedAlignment = ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_RIGHT
            elif self.horizontalAlignment is ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_RIGHT and expand.CanExpandLeft():
                adjustedAlignment = ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_LEFT
        return adjustedAlignment

    def GetActualVerticalAlignment(self):
        useThisAlignment = None
        expand = self.expandEvaluator
        if self.wantedVerticalAlignment is ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_UP:
            if expand.CanExpandUp():
                useThisAlignment = ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_UP
            else:
                useThisAlignment = ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_DOWN
        elif expand.CanExpandDown():
            useThisAlignment = ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_DOWN
        else:
            useThisAlignment = ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_UP
        return useThisAlignment

    def GetActualHorizontalAlignment(self):
        expand = self.expandEvaluator
        if self.wantedHorizontalAlignment is ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_RIGHT:
            if expand.CanExpandRight():
                useThisAlignment = ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_RIGHT
            else:
                useThisAlignment = ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_LEFT
        elif expand.CanExpandLeft():
            useThisAlignment = ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_LEFT
        else:
            useThisAlignment = ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_RIGHT
        return useThisAlignment

    def CheckChangeBackNeeded(self):
        adjustedVerticalAlignment = self.CheckVerticalAlignBackNeeded()
        adjustedHorizontalAlignment = self.CheckHorizontalAlignBackNeeded()
        return adjustedVerticalAlignment is not self.verticalAlignment or adjustedHorizontalAlignment is not self.horizontalAlignment

    def isDown(self):
        return self.verticalAlignment is ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_DOWN
