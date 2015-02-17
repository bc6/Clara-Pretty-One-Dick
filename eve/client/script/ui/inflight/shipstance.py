#Embedded file name: eve/client/script/ui/inflight\shipstance.py
import blue
import util
from carbonui import const as uiconst
from eve.client.script.ui.inflight.hudbuttons import LeftSideButton
from eve.client.script.ui.inflight.shipModuleButton.ramps import ShipModuleReactivationTimer
import inventorycommon.const as invconst
import shipmode

def get_ship_stance_buttons_args(type_id, shipID):
    btns = []
    try:
        ship_modes = shipmode.get_ship_modes_data(type_id)
    except KeyError:
        return btns

    for ship_mode in ship_modes:
        btns.append({'stanceID': ship_mode.get_key(),
         'iconNum': ship_mode.get_icon_num(),
         'stanceName': ship_mode.get_name(),
         'stanceDescription': ship_mode.get_description(),
         'stance': get_ship_stance(shipID, type_id)})

    return btns


def get_ship_stance(ship_id, type_id):
    inv = shipmode.InventoryClient(sm.GetService('invCache'), ship_id, invconst.flagHiddenModifers)
    return shipmode.get_current_ship_stance(type_id, inv.list_items())


def set_stance(stance_id, ship_id):
    sm.RemoteSvc('shipStanceMgr').SetShipStance(ship_id, stance_id)


class ShipStanceButton(LeftSideButton):

    def ApplyAttributes(self, attributes):
        LeftSideButton.ApplyAttributes(self, attributes)
        self.shipID = attributes.shipID
        if attributes.stanceID is not None:
            self.SetAsStance(attributes.typeID, attributes.stanceID, attributes.stance)
        self.activationDelay = ShipModuleReactivationTimer(parent=self, idx=-1, height=self.height, width=self.width, state=uiconst.UI_DISABLED)
        self.activationDelay.display = False
        sm.RegisterForNotifyEvent(self, 'OnStanceActive')

    def SetAsStance(self, typeID, stanceID, currentStanceID):
        self.stanceID = stanceID
        stanceData = shipmode.get_stance_data(typeID, stanceID)
        self.stanceName = stanceData.get_name()
        self.stanceDescription = stanceData.get_description()
        self.currentStanceID = currentStanceID
        self.commandName = stanceData.get_command_name()
        self.LoadIcon(stanceData.get_icon_num())
        self._UpdateStanceState(self.currentStanceID)

    def LoadTooltipPanel(self, tooltipPanel, *args):
        tooltipPanel.LoadGeneric1ColumnTemplate()
        tooltipPanel.cellSpacing = 6
        tooltipPanel.AddCommandTooltip(uicore.cmd.commandMap.GetCommandByName(self.commandName))
        tooltipPanel.AddLabelLarge(text=self.stanceName)
        tooltipPanel.AddLabelMedium(text=self.stanceDescription, color=(0.6, 0.6, 0.6, 1))

    def OnClick(self, *args):
        set_stance(self.stanceID, self.shipID)

    def OnStanceActive(self, shipID, stanceID):
        if self.shipID != shipID:
            return
        self._UpdateStanceState(stanceID)
        if stanceID != self.stanceID:
            try:
                ship = sm.GetService('godma').GetItem(self.shipID)
                switchTime = ship.stanceSwitchTime * const.MSEC
            except Exception:
                switchTime = 0.0

            self.icon.opacity = 0.5
            if switchTime:
                self.activationDelay.display = True
                try:
                    self.activationDelay.AnimateTimer(blue.os.GetSimTime(), switchTime)
                finally:
                    self.activationDelay.display = False
                    self.icon.opacity = 1.0

    def _UpdateStanceState(self, stanceID):
        if stanceID == self.stanceID:
            self.busy.state = uiconst.UI_DISABLED
        else:
            self.busy.state = uiconst.UI_HIDDEN
