#Embedded file name: eve/client/script/ui/shared/industry\facilityEntry.py
from math import pi
from carbon.common.script.util.format import StrFromColor
from carbonui.primitives.gradientSprite import GradientSprite
from eve.client.script.ui.control.baseListEntry import BaseListEntryCustomColumns
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.shared.industry.industryUIConst import VIEWMODE_ICONLIST
from eve.client.script.ui.shared.industry.installationActivityIcon import InstallationActivityIcon
from eve.common.script.util.eveFormat import FmtSystemSecStatus
from carbonui.primitives.sprite import Sprite
from industry.const import ACTIVITIES
import sys
import localization
import carbonui.const as uiconst
from utillib import KeyVal

class FacilityEntry(BaseListEntryCustomColumns):
    default_name = 'FacilityEntry'

    def ApplyAttributes(self, attributes):
        BaseListEntryCustomColumns.ApplyAttributes(self, attributes)
        self.facilityData = self.node.facilityData
        self.item = self.node.item
        self.viewMode = self.node.viewMode
        self.AddColumnJumps()
        self.AddColumnText(self.GetSecurityLabel())
        self.AddColumnText(self.facilityData.GetName())
        self.AddColumnsActivities()
        self.AddColumnsTax()
        self.AddColumnText(self.facilityData.GetTypeName())
        self.AddColumnText(self.facilityData.GetOwnerName())

    def AddColumnJumps(self):
        jumps = self.node.jumps
        if jumps != sys.maxint:
            self.AddColumnText(jumps)
        else:
            col = self.AddColumnContainer()
            Sprite(name='infinityIcon', parent=col, align=uiconst.CENTERLEFT, pos=(6, 0, 11, 6), texturePath='res:/UI/Texture/Classes/Industry/infinity.png', opacity=Label.default_color[3])

    def AddColumnsActivities(self):
        """
        Add column for each activity
        """
        costIndexes = self.facilityData.GetCostIndexByActivityID()
        iconSize = 20 if self.viewMode == VIEWMODE_ICONLIST else 14
        for i, activityID in enumerate(ACTIVITIES):
            col = self.AddColumnContainer()
            isEnabled = activityID in self.facilityData.activities
            btn = InstallationActivityIcon(parent=col, align=uiconst.CENTER, pos=(0,
             -1,
             iconSize,
             iconSize), iconSize=iconSize, activityID=activityID, isEnabled=isEnabled, facilityData=self.facilityData)
            systemCostIndex = costIndexes.get(activityID, None)
            if systemCostIndex:
                maxIndex = sm.GetService('facilitySvc').GetMaxActivityModifier(activityID)
                value = systemCostIndex / maxIndex
                self.ConstructSystemCostGradient(col, value)

    def AddColumnsTax(self):
        """
        Add column for facility tax
        """
        if self.facilityData.tax is not None:
            self.AddColumnText('%s%%' % (self.facilityData.tax * 100))
        else:
            self.AddColumnText('-')

    def ConstructSystemCostGradient(self, col, systemCostIndex):
        GradientSprite(name='systemCostGradient', align=uiconst.TOLEFT_PROP, state=uiconst.UI_DISABLED, parent=col, width=systemCostIndex, padding=0, rgbData=((0.0, industryUIConst.COLOR_SYSTEMCOSTINDEX[:3]),), rotation=pi / 2, alphaData=((0.0, 1.0),
         (0.075, 1.0),
         (0.075001, 0.2),
         (0.8, 0.0)))

    @staticmethod
    def GetDynamicHeight(node, width):
        if node.viewMode == VIEWMODE_ICONLIST:
            return 28
        else:
            return 20

    @staticmethod
    def GetDefaultColumnWidth():
        return {localization.GetByLabel('UI/Industry/Facility'): 230,
         localization.GetByLabel('UI/Common/Owner'): 230}

    @staticmethod
    def GetFixedColumns(viewMode):
        ret = {}
        if viewMode == VIEWMODE_ICONLIST:
            iconSize = 36
            ret[localization.GetByLabel('UI/Industry/Activities')] = 154
        else:
            iconSize = 22
            ret[localization.GetByLabel('UI/Industry/Activities')] = 130
        ret.update({localization.GetByLabel('UI/Industry/ActivityManufacturing'): iconSize,
         localization.GetByLabel('UI/Industry/ActivityCopying'): iconSize,
         localization.GetByLabel('UI/Industry/ActivityMaterialEfficiencyResearch'): iconSize,
         localization.GetByLabel('UI/Industry/ActivityTimeEfficiencyResearch'): iconSize,
         localization.GetByLabel('UI/Industry/ActivityInvention'): iconSize})
        return ret

    def GetSecurityLabel(self):
        sec, col = FmtSystemSecStatus(sm.GetService('map').GetSecurityStatus(self.facilityData.solarSystemID), 1)
        col.a = 1.0
        color = StrFromColor(col)
        return '<color=%s>%s</color>' % (color, sec)

    @staticmethod
    def GetColumnSortValues(facilityData, jumps, activityID):
        if facilityData.facilityID == session.stationid2:
            jumps = -1
        costIndexes = facilityData.GetCostIndexByActivityID()
        return (jumps,
         sm.GetService('map').GetSecurityStatus(facilityData.solarSystemID),
         facilityData.GetName(),
         costIndexes.get(ACTIVITIES[0], None),
         costIndexes.get(ACTIVITIES[1], None),
         costIndexes.get(ACTIVITIES[2], None),
         costIndexes.get(ACTIVITIES[3], None),
         costIndexes.get(ACTIVITIES[4], None),
         facilityData.tax,
         facilityData.GetTypeName(),
         facilityData.GetOwnerName())

    @staticmethod
    def GetHeaders(showInstallation = True, showLocation = True):
        return (localization.GetByLabel('UI/Common/Jumps'),
         localization.GetByLabel('UI/Common/Security'),
         localization.GetByLabel('UI/Industry/Facility'),
         localization.GetByLabel(industryUIConst.ACTIVITY_NAMES[ACTIVITIES[0]]),
         localization.GetByLabel(industryUIConst.ACTIVITY_NAMES[ACTIVITIES[1]]),
         localization.GetByLabel(industryUIConst.ACTIVITY_NAMES[ACTIVITIES[2]]),
         localization.GetByLabel(industryUIConst.ACTIVITY_NAMES[ACTIVITIES[3]]),
         localization.GetByLabel(industryUIConst.ACTIVITY_NAMES[ACTIVITIES[4]]),
         localization.GetByLabel('UI/Industry/Tax'),
         localization.GetByLabel('UI/Industry/FacilityType'),
         localization.GetByLabel('UI/Common/Owner'))

    def GetMenu(self):
        return sm.GetService('menu').GetMenuFormItemIDTypeID(itemID=self.facilityData.facilityID, typeID=self.facilityData.typeID)

    def GetDragData(self):
        ret = KeyVal(__guid__='xtriui.ListSurroundingsBtn', typeID=self.facilityData.typeID, itemID=self.facilityData.facilityID, label=self.facilityData.GetName())
        return (ret,)
