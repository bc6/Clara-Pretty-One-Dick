#Embedded file name: spacecomponents/client/components\bountyEscrow.py
"""
A space object that collects bounties in escrow
"""
from utillib import KeyVal
import uthread2
import blue
from spacecomponents.client.display import EntryData, DogmaEntryData, RANGE_ICON
from spacecomponents.client.display import TIMER_ICON, CYCLE_TIME_ICON
from spacecomponents.client.messages import MSG_ON_ADDED_TO_SPACE, MSG_ON_SLIM_ITEM_UPDATED, MSG_ON_BOUNTYESCROW_TIMER_UPDATED
from spacecomponents.common.components.component import Component
from spacecomponents.common.componentConst import BOUNTYESCROW_CLASS
from spacecomponents.common.components.bountyEscrow import TagCalculator, GetPriceByTagTypeID
from carbonui.control.menuLabel import MenuLabel
from eve.client.script.ui.inflight.bountyEscrowWnd import BountyEscrowWnd
from carbon.common.script.util.format import FmtDist
import spacecomponents.common.components.bountyEscrow as bountyEscrow
import localization
import util

class BountyEscrow(Component):
    __notifyevents__ = ['OnBountyEscrowPlayerInRange']

    def __init__(self, itemID, typeID, attributes, componentRegistry):
        Component.__init__(self, itemID, typeID, attributes, componentRegistry)
        self.unlockTimestamp = None
        self.unlockSeconds = 0
        self.tagSpawnSeconds = attributes.tagSpawnDelay
        self.accessRange = attributes.accessRange
        self.unlockingShipID = None
        self.lockState = None
        self.tagCalculator = TagCalculator(GetPriceByTagTypeID(attributes.tagTypeIDs))
        self.SubscribeToMessage(MSG_ON_SLIM_ITEM_UPDATED, self.OnSlimItemUpdated)
        sm.RegisterNotify(self)

    @staticmethod
    def GetAttributeInfo(godmaService, typeID, attributes, instance, localization):
        attributeEntries = [EntryData('Header', localization.GetByLabel('UI/Inflight/SpaceComponents/BountyEscrow/InfoAttributesHeader')),
         EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/BountyEscrow/AccessRangeLabel'), FmtDist(attributes.accessRange), iconID=RANGE_ICON),
         EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/BountyEscrow/DurationLabel'), localization.GetByLabel('UI/Inflight/SpaceComponents/BountyEscrow/DurationValue', duration=long(attributes.unlockDelay * SEC)), iconID=TIMER_ICON),
         EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/BountyEscrow/TakePercentageLabel'), localization.GetByLabel('UI/Inflight/SpaceComponents/BountyEscrow/TakePercentageValue', takePercentage=long(attributes.takePercentage)), iconID=CYCLE_TIME_ICON),
         EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/BountyEscrow/LoyaltyPointsLabel'), localization.GetByLabel('UI/Inflight/SpaceComponents/BountyEscrow/LoyaltyPointsValue', lpBase=float(attributes.lpBase * 100.0)), iconID=CYCLE_TIME_ICON)]
        return attributeEntries

    def OnBountyEscrowPlayerInRange(self, charID):
        msg = localization.GetByLabel('UI/Inflight/SpaceComponents/BountyEscrow/CharacterInRangeOfESS', charid=charID)
        sm.GetService('LSC').LocalEchoAll(msg, const.ownerSystem)

    def OnSlimItemUpdated(self, slimItem):
        state = slimItem.unlockState
        if state is None:
            return
        if bountyEscrow.IsUnlocking(state):
            self.unlockTimestamp = bountyEscrow.GetUnlockingTimeStamp(state)
            self.unlockSeconds = bountyEscrow.GetUnlockingDuration(state)
            self.SendMessage(MSG_ON_BOUNTYESCROW_TIMER_UPDATED, self, slimItem)
        elif bountyEscrow.IsLocked(state):
            self.CloseDistributionWindow()
            self.unlockTimestamp = None
            self.lockState = None
            self.SendMessage(MSG_ON_BOUNTYESCROW_TIMER_UPDATED, self, slimItem)

    def ShowCollectionAnimation(self, shipID):
        sm.ScatterEvent('OnSpecialFX', self.itemID, None, None, shipID, None, 'effects.BeamCollecting', 0, 1, 0, self.unlockSeconds * 1000)
        self.unlockingShipID = shipID

    def StopShowingCollectionAnimation(self):
        if self.unlockingShipID is not None:
            sm.ScatterEvent('OnSpecialFX', self.itemID, None, None, self.unlockingShipID, None, 'effects.BeamCollecting', 0, 0, 0, 0)
            self.unlockingShipID = None

    def FormatContributions(self, contributions):
        formatted = []
        for charID, amount in contributions:
            formatted.append({'label': '%s %s' % (cfg.eveowners.Get(charID).name, str(round(amount, 2)))})

        return formatted

    def ShowDistributionWindow(self):
        sm.GetService('menu').GetCloseAndTryCommand(self.itemID, self.OpenDistributionWindow, [], interactionRange=self.attributes.accessRange)

    def OpenDistributionWindow(self):
        cons = [ KeyVal(charID=charID, amount=amount) for charID, amount in self.CallServerComponent('GetBountyContributors').items() ]
        consSorted = sorted(cons, key=lambda x: x.amount, reverse=True)
        amount = sum((x.amount for x in cons))
        BountyEscrowWnd.CloseIfOpen()
        BountyEscrowWnd(bountyEscrow=self, component=self, bountyAmount=amount, contributions=consSorted, ESSTypeID=self.typeID)

    def CloseDistributionWindow(self):
        BountyEscrowWnd.CloseIfOpen()

    def TakeAll(self, *args):
        self.CallServerComponent('GetIskAsTags')

    def DistributeEvenly(self, *args):
        self.CallServerComponent('DistributeIsk')

    def GetBountyAmount(self):
        return sm.GetService('michelle').GetRemotePark().GetBountyAmount(self.itemID)

    def CallServerComponent(self, methodName, *args, **kwargs):
        return sm.GetService('michelle').GetRemotePark().CallComponentFromClient(self.itemID, BOUNTYESCROW_CLASS, methodName, *args, **kwargs)

    def GetMenu(self):
        return [[MenuLabel('UI/Commands/AccessBountyEscrow'), self.ShowDistributionWindow]]

    def UnlockEscrow(self):
        shipBall = sm.GetService('michelle').GetBall(session.shipid)
        if shipBall.isCloaked:
            raise UserError('CantAccessWhileCloaked')
        sm.GetService('menu').GetCloseAndTryCommand(self.itemID, self.AccessBountyEscrow, [], interactionRange=self.attributes.accessRange)

    def AccessBountyEscrow(self):
        self.CallServerComponent('Unlock')


def GetSubLabel(slimItem):
    """
    Gets the current bountyBonus value and returns it as a string.
    """
    if slimItem.bountyEscrowBonus > 0.0:
        bountyEscrowBonus = str(int(slimItem.bountyEscrowBonus * 100))
        subLabel = bountyEscrowBonus + localization.GetByLabel('UI/Inflight/Brackets/BountyEscrowBonus')
        return subLabel


def GetBountyReductionForSolarSystem(ballpark, bountyAmount):
    """
    Takes in the ballpark and float: bounty.
    Returns float: paidBounty that will actually be paid and float: takenBounty.
    """
    componentRegistry = ballpark.componentRegistry
    bountyEscrows = componentRegistry.GetInstancesWithComponentClass(BOUNTYESCROW_CLASS)
    if bountyEscrows:
        bountyEscrow = bountyEscrows[0]
        paidBounty = bountyAmount * (1.0 - bountyEscrow.attributes.takePercentage / 100.0)
        slimItem = ballpark.slimItems[bountyEscrow.itemID]
        takenBounty = (bountyAmount - paidBounty) * (1.0 + slimItem.bountyEscrowBonus)
        return (paidBounty, takenBounty)
    return (None, None)
