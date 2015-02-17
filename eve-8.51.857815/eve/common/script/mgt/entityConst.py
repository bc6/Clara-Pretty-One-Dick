#Embedded file name: eve/common/script/mgt\entityConst.py
"""
Common module to provide the consts for entities 
These states will be recorded in the DB to persist the 
state of the object. 

These cosntants could have been left on the server, but 
they are used by the posConst.py file and need to be in 
common for the common code there. 
"""
import localization
import eve.common.lib.appConst as const
STATE_OFFLINING = -7
STATE_ANCHORING = -6
STATE_ONLINING = -5
STATE_ANCHORED = -4
STATE_UNANCHORING = -3
STATE_UNANCHORED = -2
STATE_INCAPACITATED = -1
STATE_IDLE = 0
STATE_COMBAT = 1
STATE_MINING = 2
STATE_APPROACHING = 3
STATE_DEPARTING = 4
STATE_DEPARTING_2 = 5
STATE_PURSUIT = 6
STATE_FLEEING = 7
STATE_REINFORCED = 8
STATE_OPERATING = 9
STATE_ENGAGE = 10
STATE_VULNERABLE = 11
STATE_SHIELD_REINFORCE = 12
STATE_ARMOR_REINFORCE = 13
STATE_INVULNERABLE = 14
STATE_WARPAWAYANDDIE = 15
STATE_WARPAWAYANDCOMEBACK = 16
STATE_WARPTOPOSITION = 17
STATE_SALVAGING = 18
ENTITY_STATE_NAMES = {STATE_OFFLINING: 'State_OFFLINING',
 STATE_ANCHORING: 'STATE_ANCHORING',
 STATE_ONLINING: 'STATE_ONLINING',
 STATE_ANCHORED: 'STATE_ANCHORED',
 STATE_UNANCHORING: 'STATE_UNANCHORING',
 STATE_UNANCHORED: 'STATE_UNANCHORED',
 STATE_INCAPACITATED: 'STATE_INCAPACITATED',
 STATE_IDLE: 'STATE_IDLE',
 STATE_COMBAT: 'STATE_COMBAT',
 STATE_MINING: 'STATE_MINING',
 STATE_APPROACHING: 'STATE_APPROACHING',
 STATE_DEPARTING: 'STATE_DEPARTING',
 STATE_DEPARTING_2: 'STATE_DEPARTING_2',
 STATE_PURSUIT: 'STATE_PURSUIT',
 STATE_FLEEING: 'STATE_FLEEING',
 STATE_REINFORCED: 'STATE_REINFORCED',
 STATE_OPERATING: 'STATE_OPERATING',
 STATE_ENGAGE: 'STATE_ENGAGE',
 STATE_VULNERABLE: 'STATE_VULNERABLE',
 STATE_SHIELD_REINFORCE: 'STATE_SHIELD_REINFORCE',
 STATE_ARMOR_REINFORCE: 'STATE_ARMOR_REINFORCE',
 STATE_INVULNERABLE: 'STATE_INVULNERABLE',
 STATE_WARPAWAYANDDIE: 'STATE_WARPAWAYANDDIE',
 STATE_WARPAWAYANDCOMEBACK: 'STATE_WARPAWAYANDCOMEBACK',
 STATE_WARPTOPOSITION: 'STATE_WARPTOPOSITION',
 STATE_SALVAGING: 'STATE_SALVAGING'}
INCAPACITATION_DISTANCE = 250000
COMMAND_DISTANCE = INCAPACITATION_DISTANCE
POS_STRUCTURE_STATE = {const.pwnStructureStateAnchored: localization.GetByLabel('UI/Entities/States/Anchored'),
 const.pwnStructureStateAnchoring: localization.GetByLabel('UI/Entities/States/Anchoring'),
 const.pwnStructureStateIncapacitated: localization.GetByLabel('UI/Entities/States/Incapacitated'),
 const.pwnStructureStateInvulnerable: localization.GetByLabel('UI/Entities/States/Invulnerable'),
 const.pwnStructureStateOnline: localization.GetByLabel('UI/Entities/States/Online'),
 const.pwnStructureStateOnlining: localization.GetByLabel('UI/Entities/States/Onlining'),
 const.pwnStructureStateOperating: localization.GetByLabel('UI/Entities/States/Operating'),
 const.pwnStructureStateReinforced: localization.GetByLabel('UI/Entities/States/Reinforced'),
 const.pwnStructureStateUnanchored: localization.GetByLabel('UI/Entities/States/Unanchored'),
 const.pwnStructureStateUnanchoring: localization.GetByLabel('UI/Entities/States/Unanchoring'),
 const.pwnStructureStateVulnerable: localization.GetByLabel('UI/Entities/States/Vulnerable'),
 const.pwnStructureStateAnchor: localization.GetByLabel('UI/Inflight/MoonMining/Structures/Anchor'),
 const.pwnStructureStateUnanchor: localization.GetByLabel('UI/Inflight/MoonMining/Structures/Unanchor'),
 const.pwnStructureStateOffline: localization.GetByLabel('UI/Inflight/MoonMining/Structures/Offline'),
 const.pwnStructureStateOnlineActive: localization.GetByLabel('UI/Inflight/MoonMining/States/OnlineActive'),
 const.pwnStructureStateOnlineStartingUp: localization.GetByLabel('UI/Inflight/MoonMining/States/OnlineStartingUp')}
exports = {'entities.ENTITY_STATE_NAMES': ENTITY_STATE_NAMES}
