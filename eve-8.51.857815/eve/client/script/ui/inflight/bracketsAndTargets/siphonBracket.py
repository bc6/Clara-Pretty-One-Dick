#Embedded file name: eve/client/script/ui/inflight/bracketsAndTargets\siphonBracket.py
""" Custom brackettype for SiphoningSilos, showing the remaining capacity of silo as a bar."""
from eve.client.script.ui.inflight.bracketsAndTargets.inSpaceBracket import InSpaceBracket
import util
import localization
import moniker
from uiprimitives import Container, Fill
from uicontrols import Frame
import carbonui.const as uiconst

class SiphonSiloBracket(InSpaceBracket):
    """ Custom brackettype for SiphoningSilos, showing the remaining capacity of silo as a bar."""

    def ApplyAttributes(self, attributes):
        InSpaceBracket.ApplyAttributes(self, attributes)
        self.width = 32
        self.height = 40
        container = Container(parent=self, align=uiconst.BOTTOMLEFT, height=8, width=32)
        inner = Container(parent=container, padding=(2, 2, 2, 2))
        self.frame = Frame(parent=container)
        container.fill = Fill(parent=inner, align=uiconst.TOLEFT_PROP, width=0, padding=(0, 0, 0, 0))
        self.capacityBar = container

    def Startup(self, slimItem, ball = None, transform = None):
        InSpaceBracket.Startup(self, slimItem, ball=ball, transform=transform)

    def SetHint(self, hint):
        self.capacityBar.hint = hint
        self.hint = hint

    def SetCapacityBarPercentage(self, capacityusage):
        usage = min(float(capacityusage.used) / float(capacityusage.capacity), 1.0)
        self.capacityBar.fill.width = usage
        if usage > 0.98:
            self.capacityBar.fill.color = util.Color.YELLOW
        else:
            self.capacityBar.fill.color = util.Color.GRAY
        self.SetHint(localization.GetByLabel('UI/Inventory/ContainerQuantityAndCapacity', quantity=capacityusage.used, capacity=capacityusage.capacity))

    def GetSiphonCapacityUsage(self):
        ballpark = moniker.GetBallPark(session.solarsystemid)
        capacity = ballpark.GetCapacityOfSiphon(self.slimItem.itemID)
        return capacity

    def Select(self, status):
        InSpaceBracket.Select(self, status)
        if status:
            self.SetCapacityBarPercentage(self.GetSiphonCapacityUsage())
            self.capacityBar.state = uiconst.UI_NORMAL
        else:
            self.capacityBar.state = uiconst.UI_HIDDEN
            self.SetHint('')
