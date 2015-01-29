#Embedded file name: eve/client/script/ui/shared/planet/pinContainers\obsoletePinContainer.py
import util
import localization
from .BasePinContainer import BasePinContainer
from .. import planetCommon

class ObsoletePinContainer(BasePinContainer):
    """
    A base pin container class for pin containers to inherit from. The pin containers
    are the ones shown when pins are clicked.
    """
    __guid__ = 'planet.ui.ObsoletePinContainer'

    def _GetActionButtons(self):
        typeObj = cfg.invtypes.Get(self.pin.typeID)
        btns = [util.KeyVal(id=planetCommon.PANEL_DECOMMISSION, panelCallback=self.PanelDecommissionPin, hint=localization.GetByLabel('UI/PI/Common/ObsoletePinReimbursementHint', pinName=typeObj.typeName, iskAmount=util.FmtISK(typeObj.basePrice)))]
        return btns
