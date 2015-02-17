#Embedded file name: eve/client/script/ui/station/fitting\stanceSlot.py
from carbonui.primitives.container import Container
from eve.client.script.ui.inflight import shipstance

class StanceSlots(Container):

    def __init__(self, **kw):
        super(StanceSlots, self).__init__(**kw)

    def _GetAngles(self):
        return [ 258 - i * 10 for i in xrange(3) ]

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        typeID = sm.GetService('invCache').GetInventoryFromId(attributes.shipID).GetItem().typeID
        self.shipstances = []
        for angle in self._GetAngles():
            pos = attributes.angleToPos(angle)
            newPos = (pos[0],
             pos[1],
             32,
             32)
            self.shipstances.append(shipstance.ShipStanceButton(shipID=attributes.shipID, typeID=typeID, parent=self, pos=newPos))

    def ShowStances(self, shipID, typeID):
        for idx, kwargs in enumerate(shipstance.get_ship_stance_buttons_args(typeID, shipID)):
            stanceButton = self.shipstances[idx]
            stanceButton.SetAsStance(typeID, kwargs['stanceID'], kwargs['stance'])

    def GetStanceContainers(self):
        return self.shipstances
