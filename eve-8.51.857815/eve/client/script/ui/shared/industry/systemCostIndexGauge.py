#Embedded file name: eve/client/script/ui/shared/industry\systemCostIndexGauge.py
from carbonui.util.color import Color
from eve.client.script.ui.control.eveLabel import Label, EveLabelSmallBold
from eve.client.script.ui.control.gauge import Gauge
from eve.client.script.ui.shared.industry import industryUIConst
import localization
import carbonui.const as uiconst

class SystemCostIndexGauge(Gauge):
    """
    A specialized gauge used to visualize System cost index
    """
    default_color = Color(*industryUIConst.COLOR_SYSTEMCOSTINDEX).SetBrightness(0.5).GetRGBA()
    default_backgroundColor = Color(*industryUIConst.COLOR_SYSTEMCOSTINDEX).SetAlpha(0.1).GetRGBA()

    def ApplyAttributes(self, attributes):
        Gauge.ApplyAttributes(self, attributes)
        facilityData = attributes.facilityData
        activityID = attributes.activityID
        self.valueLabel = EveLabelSmallBold(parent=self, align=uiconst.CENTER, idx=0, top=1)
        for i in xrange(11):
            self.ShowMarker(i / 10.0, color=(0.5,
             0.5,
             0.7,
             i / 60.0))

        systemCostIndexes = facilityData.GetCostIndexByActivityID()
        value = systemCostIndexes.get(activityID, 0.0)
        maxValue = sm.GetService('facilitySvc').GetMaxActivityModifier(activityID)
        Gauge.SetValue(self, value / maxValue)
        self.valueLabel.text = '%.2f%%' % (value * 100.0)

    def GetHint(self):
        return '<b>%s</b><br>%s' % (localization.GetByLabel('UI/Industry/SystemCostIndex'), localization.GetByLabel('UI/Industry/SystemCostIndexHint'))
