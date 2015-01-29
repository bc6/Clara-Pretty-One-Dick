#Embedded file name: eve/client/script/ui/shared/planet/pinContainers\ExtractorContainer.py
"""
This file contains the pin container classes; the ones that appear when a pin on the
surface of a planet is clicked. All containers derive from the BasePinContainer class.
"""
import util
import uicls
import blue
import localization
from .BasePinContainer import BasePinContainer, CaptionAndSubtext
from dogma.attributes.format import GetFormatAndValue
from .obsoletePinContainer import ObsoletePinContainer
import eve.common.script.planet.entities.basePin as basePin
from .. import planetCommon as planetCommonUI

class ExtractorContainer(ObsoletePinContainer):
    __guid__ = 'planet.ui.ExtractorContainer'
    default_name = 'ExtractorContainer'

    def ApplyAttributes(self, attributes):
        BasePinContainer.ApplyAttributes(self, attributes)

    def _GetInfoCont(self):
        p = self.infoContPad
        infoCont = self._DrawAlignTopCont(95, 'infoCont', padding=(p,
         p,
         p,
         p))
        self.currDepositTxt = CaptionAndSubtext(parent=infoCont, caption=localization.GetByLabel('UI/PI/Common/Extracting'), top=0)
        self.depositsLeftTxt = CaptionAndSubtext(parent=infoCont, caption=localization.GetByLabel('UI/PI/Common/TotalAmountLeft'), top=40)
        self.timeToDeplTxt = CaptionAndSubtext(parent=infoCont, caption=localization.GetByLabel('UI/PI/Common/TimeToDepletion'), top=70)
        left = self.infoContRightColAt
        self.currCycleGauge = uicls.Gauge(parent=infoCont, value=0.0, color=planetCommonUI.PLANET_COLOR_CYCLE, label=localization.GetByLabel('UI/PI/Common/CurrentCycle'), cyclic=True)
        self.currCycleGauge.left = left
        self.amountPerCycleTxt = CaptionAndSubtext(parent=infoCont, caption=localization.GetByLabel('UI/PI/Common/OutputPerCycle'), top=40, left=left)
        self.amountPerHourTxt = CaptionAndSubtext(parent=infoCont, caption=localization.GetByLabel('UI/PI/Common/OutputPerHour'), top=70, left=left)
        return infoCont

    def _UpdateInfoCont(self):
        """
        Called every 100 ms to update the info container
        """
        if self.pin.depositType is not None and self.pin.depositQtyPerCycle > 0:
            timeToDepletion = self.pin.GetTimeToDepletion()
            totalTimeLeft = timeToDepletion
            self.timeToDeplTxt.SetCaption(localization.GetByLabel('UI/PI/Common/TimeToDepletion'))
            if totalTimeLeft < const.DAY:
                totalTimeLeft = util.FmtTime(float(totalTimeLeft))
            else:
                totalTimeLeft = util.FmtTimeInterval(long(totalTimeLeft), breakAt='hour')
            deposName = cfg.invtypes.Get(self.pin.depositType).name
            if self.pin.activityState < basePin.STATE_IDLE:
                currCycle = 0
                currCycleProportion = 0.0
                cycleTime = 0
            else:
                currCycle = blue.os.GetWallclockTime() - self.pin.lastRunTime
                currCycleProportion = currCycle / float(self.pin.GetCycleTime())
                cycleTime = self.pin.GetCycleTime()
        else:
            currCycle = 0
            totalTimeLeft = util.FmtTime(0)
            currCycleProportion = 0.0
            cycleTime = 0
            deposName = localization.GetByLabel('UI/PI/Common/NothingExtracted')
        self.currDepositTxt.SetIcon(self.pin.depositType)
        self.currDepositTxt.SetSubtext(deposName)
        self.depositsLeftTxt.SetSubtext(localization.GetByLabel('UI/PI/Common/UnitsAmount', amount=self.pin.depositQtyRemaining))
        if self.pin.IsInEditMode():
            self.currCycleGauge.SetSubText(localization.GetByLabel('UI/PI/Common/InactiveEditMode'))
            self.timeToDeplTxt.SetSubtext(localization.GetByLabel('UI/PI/Common/InactiveEditMode'))
        else:
            self.currCycleGauge.SetValueInstantly(currCycleProportion)
            self.timeToDeplTxt.SetSubtext(totalTimeLeft)
            self.currCycleGauge.SetSubText(localization.GetByLabel('UI/PI/Common/CycleTimeElapsed', currTime=long(currCycle), totalTime=long(cycleTime)))
        self.amountPerCycleTxt.SetSubtext(localization.GetByLabel('UI/PI/Common/UnitsAmount', amount=self.pin.depositQtyPerCycle))
        attr = cfg.dgmattribs.GetIfExists(const.attributeLogisticalCapacity)
        self.amountPerHourTxt.SetSubtext(GetFormatAndValue(attr, self.pin.GetOutputVolumePerHour()))
