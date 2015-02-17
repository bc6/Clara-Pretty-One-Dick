#Embedded file name: eve/client/script/ui/inflight\stanceButtons.py
import util
from carbonui.primitives.container import Container
from eve.client.script.ui.inflight import shipstance

class StanceButtons(Container):

    def ApplyAttributes(self, attributes):
        self._heightOffset = 32
        Container.ApplyAttributes(self, attributes)
        self.buttonSize = attributes.buttonSize
        self.AddButtons()

    def AddButtons(self):
        shipID = util.GetActiveShip()
        typeID = sm.GetService('invCache').GetInventoryFromId(shipID).GetItem().typeID
        self.shipstances = []
        for idx, kwargs in enumerate(shipstance.get_ship_stance_buttons_args(typeID, shipID)):
            self.shipstances.append(shipstance.ShipStanceButton(parent=self, shipID=shipID, typeID=typeID, left=(10 * (idx % 2)), top=(40 * idx), width=self.buttonSize, height=self.buttonSize, **kwargs))

    def HasStances(self):
        return bool(self.shipstances)
