#Embedded file name: spacecomponents/client/components\microJumpDriver.py
from carbonui.control.menuLabel import MenuLabel
from carbon.common.script.util.format import FmtDist
from carbon.common.lib.const import SEC, MSEC
from dogma.attributes.format import GetFormattedAttributeAndValue
from dogma.const import attributeDuration, attributeMass
from dogma.const import attributeSignatureRadiusBonusPercent
from eve.common.lib.appConst import microJumpDriveDistance
from spacecomponents.client.display import EntryData
from spacecomponents.client.display import DogmaEntryData
from spacecomponents.client.display import RANGE_ICON
from spacecomponents.client.display import GetDogmaAttributeAndValue
from spacecomponents.client.messages import MSG_ON_SLIM_ITEM_UPDATED
from spacecomponents.common.componentConst import MICRO_JUMP_DRIVER_CLASS
from spacecomponents.common.components.component import Component
import logging
logger = logging.getLogger(__name__)
REMOTE_CALL_START_MICRO_JUMP_DRIVE = 'StartMicroJumpDriveForShip'

class MicroJumpDriver(Component):

    def __init__(self, itemID, typeID, attributes, componentRegistry):
        Component.__init__(self, itemID, typeID, attributes, componentRegistry)
        self.SubscribeToMessage(MSG_ON_SLIM_ITEM_UPDATED, self.OnSlimItemUpdated)
        self.lastEndTime = None
        self.spoolUpDurationMillisec = self.attributes.spoolUpDurationMillisec

    def OnSlimItemUpdated(self, slimItem):
        if slimItem.component_microJumpDriver is not None:
            startTime = slimItem.component_microJumpDriver
            logger.debug('MicroJumpDriver.OnSlimItemUpdates: %s', startTime)
            endTime = startTime + self.spoolUpDurationMillisec * MSEC
            if self.lastEndTime is None:
                self.lastEndTime = endTime
                self.UThreadNew(self._StartVisualEffectThread)
            elif endTime > self.lastEndTime:
                self.lastEndTime = endTime

    def _StartVisualEffectThread(self):
        self.TriggerEffect('trigger')
        try:
            while self.lastEndTime > self.GetSimTime():
                timeDiff = self.TimeDiffInMs(self.GetSimTime(), self.lastEndTime)
                logger.debug('visual effect thread entering sleep for %d ms', timeDiff)
                self.SleepSim(long(timeDiff))

            logger.debug('visual effect thread exiting')
        finally:
            self.lastEndTime = None
            self.TriggerEffect('active')

    def TriggerEffect(self, effectName):
        logger.debug('TriggerEffect %s', effectName)
        ball = sm.GetService('michelle').GetBall(self.itemID)
        if ball is not None:
            ball.TriggerAnimation(effectName)

    @staticmethod
    def GetAttributeInfo(godmaService, typeID, attributes, instance, localization):
        maxMassData = GetFormattedAttributeAndValue(attributeMass, attributes.maxShipMass)
        maxMassData.displayName = localization.GetByLabel('UI/Inflight/SpaceComponents/MicroJumpDriver/MaxShipMass')
        durationData = GetFormattedAttributeAndValue(attributeDuration, attributes.spoolUpDurationMillisec)
        attributeEntries = [EntryData('Header', localization.GetByLabel('UI/Inflight/SpaceComponents/MicroJumpDriver/InfoAttributesHeader')),
         EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/MicroJumpDriver/InteractionRange'), FmtDist(attributes.interactionRange), iconID=RANGE_ICON),
         EntryData('LabelTextSides', localization.GetByLabel('UI/Inflight/SpaceComponents/MicroJumpDriver/JumpDistance'), FmtDist(microJumpDriveDistance), iconID=RANGE_ICON),
         DogmaEntryData('LabelTextSides', durationData),
         DogmaEntryData('LabelTextSides', GetDogmaAttributeAndValue(godmaService, typeID, attributeSignatureRadiusBonusPercent)),
         DogmaEntryData('LabelTextSides', maxMassData)]
        return attributeEntries

    @staticmethod
    def GetSuppressedDogmaAttributeIDs():
        return [attributeDuration, attributeSignatureRadiusBonusPercent]


def ActivateMicroJumpDrive(michelleService, itemID):
    remoteBallpark = michelleService.GetRemotePark()
    remoteBallpark.CallComponentFromClient(itemID, MICRO_JUMP_DRIVER_CLASS, REMOTE_CALL_START_MICRO_JUMP_DRIVE)
    logger.info('Activating micro jump drive')


def GetMenu(michelleService, shipID, itemID):
    ballpark = michelleService.GetBallpark()
    component = ballpark.componentRegistry.GetComponentForItem(itemID, MICRO_JUMP_DRIVER_CLASS)
    menu = []
    if ballpark.DistanceBetween(shipID, itemID) <= component.attributes.interactionRange:
        menu.append([MenuLabel('UI/Inflight/SpaceComponents/MicroJumpDriver/ActivateMicroJumpDrive'), ActivateMicroJumpDrive, [michelleService, itemID]])
    return menu
