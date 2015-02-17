#Embedded file name: crimewatch\const.py
import inventorycommon
securityLevelsPerTagType = {inventorycommon.const.typeSecurityTagCloneSoldierNegotiator: (-2.0, 0.0),
 inventorycommon.const.typeSecurityTagCloneSoldierTransporter: (-5.0, -2.0),
 inventorycommon.const.typeSecurityTagCloneSoldierRecruiter: (-8.0, -5.0),
 inventorycommon.const.typeSecurityTagCloneSoldierTrainer: (-10.0, -8.0)}
securityGainPerTag = 0.5
characterSecurityStatusMax = 10.0
characterSecurityStatusMin = -10.0
groupsSkipCriminalFlags = [inventorycommon.const.groupGangCoordinator, inventorycommon.const.groupSiegeModule]
targetGroupsWithNoSecurityPenalty = (inventorycommon.const.groupMobileHomes, inventorycommon.const.groupCynoInhibitor, inventorycommon.const.groupAutoLooter)
targetGroupsWithSuspectPenaltyInHighSec = (inventorycommon.const.groupMobileHomes,
 inventorycommon.const.groupCynoInhibitor,
 inventorycommon.const.groupAutoLooter,
 inventorycommon.const.groupMobileScanInhibitor,
 inventorycommon.const.groupMobileMicroJumpUnit)
targetGroupsWithNoPenalties = (inventorycommon.const.groupSiphonPseudoSilo,)
