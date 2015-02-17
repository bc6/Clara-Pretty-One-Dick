#Embedded file name: eve/client/script/ui/inflight\stanceButtons.py
from carbonui.primitives.container import Container
from eve.client.script.ui.inflight import shipstance

class StanceButtons(Container):

    def ApplyAttributes(self, attributes):
        self._heightOffset = 32
        Container.ApplyAttributes(self, attributes)
        self.buttonSize = attributes.buttonSize
        self.shipStanceButtons = []

    def HasStances(self):
        return bool(self.shipStanceButtons)

    def UpdateButtonsForShip(self, shipID, typeID):
        self._RemoveStanceButtons()
        self._AddStanceButtons(shipID, typeID)

    def _AddStanceButtons(self, shipID, typeID):
        for idx, kwargs in enumerate(shipstance.get_ship_stance_buttons_args(typeID, shipID)):
            self.shipStanceButtons.append(shipstance.ShipStanceButton(parent=self, shipID=shipID, typeID=typeID, left=(10 * (idx % 2)), top=(40 * idx), width=self.buttonSize, height=self.buttonSize, **kwargs))

    def _RemoveStanceButtons(self):
        for stanceButton in self.shipStanceButtons:
            stanceButton.Close()

        self.shipStanceButtons = []
