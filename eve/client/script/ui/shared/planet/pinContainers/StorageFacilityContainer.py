#Embedded file name: eve/client/script/ui/shared/planet/pinContainers\StorageFacilityContainer.py
"""
This file contains the pin container classes; the ones that appear when a pin on the
surface of a planet is clicked. All containers derive from the BasePinContainer class.
"""
import carbonui.const as uiconst
import util
import uicls
import blue
import localization
import uiprimitives
import uicontrols
from .BasePinContainer import BasePinContainer, CaptionAndSubtext
from .. import planetCommon

class StorageFacilityContainer(BasePinContainer):
    __guid__ = 'planet.ui.StorageFacilityContainer'
    default_name = 'StorageFacilityContainer'

    def ApplyAttributes(self, attributes):
        BasePinContainer.ApplyAttributes(self, attributes)

    def _GetActionButtons(self):
        btns = [util.KeyVal(id=planetCommon.PANEL_STORAGE, panelCallback=self.PanelShowStorage)]
        btns.extend(BasePinContainer._GetActionButtons(self))
        return btns

    def _GetInfoCont(self):
        p = self.infoContPad
        infoCont = self._DrawAlignTopCont(70, 'infoCont', padding=(p,
         p,
         p,
         p))
        self.storageGauge = uicls.Gauge(parent=infoCont, value=0.0, color=planetCommon.PLANET_COLOR_STORAGE, label=localization.GetByLabel('UI/PI/Common/Storage'))
        self.cooldownTimer = CaptionAndSubtext(parent=infoCont, caption=localization.GetByLabel('UI/PI/Common/NextTransferAvailable'), top=40)
        left = self.infoContRightColAt
        self.itemsTxt = CaptionAndSubtext(parent=infoCont, caption=localization.GetByLabel('UI/PI/Common/StoredItems'), left=left, state=uiconst.UI_DISABLED)
        self.iconCont = uiprimitives.Container(parent=infoCont, pos=(left,
         12,
         120,
         60), align=uiconst.TOPLEFT, state=uiconst.UI_PICKCHILDREN)
        self._DrawStoredCommoditiesIcons()
        return infoCont

    def _DrawStoredCommoditiesIcons(self):
        self.iconCont.Flush()
        i = 0
        maxNumIcons = 8
        if self.pin.contents:
            for typeID, amount in self.pin.contents.iteritems():
                iconLeft, iconTop = self._GetIconPos(i)
                icon = uicontrols.Icon(parent=self.iconCont, pos=(iconLeft,
                 iconTop,
                 25,
                 25), hint=localization.GetByLabel('UI/PI/Common/ItemAmount', itemName=cfg.invtypes.Get(typeID).name, amount=int(amount)), typeID=typeID, size=32, ignoreSize=True)
                i += 1
                if i >= maxNumIcons:
                    break

            self.itemsTxt.SetSubtext('')
        else:
            self.itemsTxt.SetSubtext(localization.GetByLabel('UI/PI/Common/NothingStored'))

    def _UpdateInfoCont(self):
        """
        Called every 100 ms to update the info container
        """
        self.storageGauge.SetValue(float(self.pin.capacityUsed) / self.pin.GetCapacity())
        self.storageGauge.SetSubText(localization.GetByLabel('UI/PI/Common/StorageUsed', capacityUsed=self.pin.capacityUsed, capacityMax=self.pin.GetCapacity()))
        if self.pin.lastRunTime is None or self.pin.lastRunTime <= blue.os.GetWallclockTime():
            self.cooldownTimer.SetSubtext(localization.GetByLabel('UI/Common/Now'))
        else:
            self.cooldownTimer.SetSubtext(localization.GetByLabel('UI/PI/Common/TimeHourMinSec', time=self.pin.lastRunTime - blue.os.GetWallclockTime()))

    def _GetIconPos(self, iconNum):
        iconsInRow = 4
        iconSpace = 30
        left = iconSpace * (iconNum % iconsInRow)
        top = iconSpace * (iconNum / iconsInRow)
        return (left, top)

    def OnRefreshPins(self, pinIDs):
        if not self or self.destroyed:
            return
        BasePinContainer.OnRefreshPins(self, pinIDs)
        self._DrawStoredCommoditiesIcons()
