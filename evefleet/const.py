#Embedded file name: evefleet\const.py
"""
This file contains declarations and common helper functions for the
Fleet system for use in both the client and the server
"""
fleetGroupingRange = 300
fleetJobCreator = 2
fleetJobNone = 0
fleetJobScout = 1
fleetLeaderRole = 1
fleetRoleLeader = 1
fleetRoleMember = 4
fleetRoleSquadCmdr = 3
fleetRoleWingCmdr = 2
fleetBoosterNone = 0
fleetBoosterFleet = 1
fleetBoosterWing = 2
fleetBoosterSquad = 3
rejectFleetInviteTimeout = 1
rejectFleetInviteAlreadyInFleet = 2
fleetRejectionReasons = {rejectFleetInviteTimeout: 'UI/Fleet/FleetServer/NoResponse',
 rejectFleetInviteAlreadyInFleet: 'UI/Fleet/FleetServer/AlreadyInFleet'}
FLEET_NONEID = -1
CHANNELSTATE_NONE = 0
CHANNELSTATE_LISTENING = 1
CHANNELSTATE_MAYSPEAK = 2
CHANNELSTATE_SPEAKING = 4
MIN_MEMBERS_IN_FLEET = 50
MAX_MEMBERS_IN_FLEET = 256
MAX_MEMBERS_IN_SQUAD = 10
MAX_SQUADS_IN_WING = 5
MAX_WINGS_IN_FLEET = 5
MIN_MEMBERS_CMDR_BONUSES = 2
MAX_NAME_LENGTH = 10
MAX_DAMAGE_SENDERS = 15
FLEET_STATUS_ACTIVE = 1
FLEET_STATUS_INACTIVE = 0
FLEET_STATUS_TOOFEWWINGS = -1
FLEET_STATUS_TOOMANYWINGS = -2
WING_STATUS_ACTIVE = 1
WING_STATUS_INACTIVE = 0
WING_STATUS_TOOFEWMEMBERS = -1
WING_STATUS_TOOMANYSQUADS = -2
SQUAD_STATUS_ACTIVE = 1
SQUAD_STATUS_INACTIVE = 0
SQUAD_STATUS_NOSQUADCOMMANDER = -1
SQUAD_STATUS_TOOMANYMEMBERS = -2
SQUAD_STATUS_TOOFEWMEMBERS = -3
BROADCAST_NONE = 0
BROADCAST_DOWN = 1
BROADCAST_UP = 2
BROADCAST_ALL = 3
BROADCAST_UNIVERSE = 0
BROADCAST_SYSTEM = 1
BROADCAST_BUBBLE = 2
INVITE_CLOSED = 0
INVITE_CORP = 1
INVITE_ALLIANCE = 2
INVITE_MILITIA = 4
INVITE_PUBLIC = 8
INVITE_ALL = 15
FLEETNAME_MAXLENGTH = 32
FLEETDESC_MAXLENGTH = 150
NODEID_MOD = 10000000
FLEETID_MOD = 10000
WINGID_MOD = 20000
SQUADID_MOD = 30000
ALL_BROADCASTS = ['EnemySpotted',
 'NeedBackup',
 'HoldPosition',
 'InPosition',
 'TravelTo',
 'JumpBeacon',
 'Location',
 'Target',
 'HealArmor',
 'HealShield',
 'HealCapacitor',
 'WarpTo',
 'AlignTo',
 'JumpTo']
RECONNECT_TIMEOUT = 2
