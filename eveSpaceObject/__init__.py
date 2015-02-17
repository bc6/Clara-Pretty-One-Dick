#Embedded file name: eveSpaceObject\__init__.py
import inventorycommon.const as const
gfxRaceAmarr = 'amarr'
gfxRaceCaldari = 'caldari'
gfxRaceGallente = 'gallente'
gfxRaceMinmatar = 'minmatar'
gfxRaceJove = 'jove'
gfxRaceAngel = 'angel'
gfxRaceSleeper = 'sleeper'
gfxRaceORE = 'ore'
gfxRaceConcord = 'concord'
gfxRaceRogue = 'rogue'
gfxRaceSansha = 'sansha'
gfxRaceSOCT = 'soct'
gfxRaceTalocan = 'talocan'
gfxRaceGeneric = 'generic'
gfxRaceSoE = 'soe'
droneTurretGfxID_fighterbomber = {gfxRaceAmarr: 11515,
 gfxRaceGallente: 11517,
 gfxRaceCaldari: 11516,
 gfxRaceMinmatar: 11518,
 gfxRaceSansha: 20339}
droneTurretGfxID_mining = 11521
droneTurretGfxID_combat = {gfxRaceAmarr: 11504,
 gfxRaceGallente: 11506,
 gfxRaceCaldari: 11505,
 gfxRaceMinmatar: 11508}
droneTurretGfxID_salvager = 20925
droneTurretGfxID_generic = 11507
gfxDroneGroupFighterBomber = 1
gfxDroneGroupCombat = 2
gfxDroneGroupUtility = 3
gfxDroneGroupMining = 4
gfxDroneGroupNpc = 5
gfxDroneGroupSalvager = 6
droneGroupFromTypeGroup = {const.groupFighterBomber: gfxDroneGroupFighterBomber,
 const.groupMiningDrone: gfxDroneGroupMining,
 const.groupSalvageDrone: gfxDroneGroupSalvager,
 const.groupCombatDrone: gfxDroneGroupCombat,
 const.groupFighterDrone: gfxDroneGroupCombat,
 const.groupElectronicWarfareDrone: gfxDroneGroupCombat,
 const.groupStasisWebifyingDrone: gfxDroneGroupCombat,
 const.groupUnanchoringDrone: gfxDroneGroupCombat,
 const.groupRepairDrone: gfxDroneGroupCombat,
 const.groupWarpScramblingDrone: gfxDroneGroupCombat,
 const.groupCapDrainDrone: gfxDroneGroupCombat,
 const.groupLogisticDrone: gfxDroneGroupCombat,
 const.groupLCODrone: gfxDroneGroupNpc,
 const.groupRogueDrone: gfxDroneGroupNpc,
 const.groupAsteroidRogueDroneBattleCruiser: gfxDroneGroupNpc,
 const.groupAsteroidRogueDroneBattleship: gfxDroneGroupNpc,
 const.groupAsteroidRogueDroneCruiser: gfxDroneGroupNpc,
 const.groupAsteroidRogueDroneDestroyer: gfxDroneGroupNpc,
 const.groupAsteroidRogueDroneFrigate: gfxDroneGroupNpc,
 const.groupAsteroidRogueDroneHauler: gfxDroneGroupNpc,
 const.groupAsteroidRogueDroneSwarm: gfxDroneGroupNpc,
 const.groupAsteroidRogueDroneOfficer: gfxDroneGroupNpc,
 const.groupDeadspaceRogueDroneBattleCruiser: gfxDroneGroupNpc,
 const.groupDeadspaceRogueDroneBattleship: gfxDroneGroupNpc,
 const.groupDeadspaceRogueDroneCruiser: gfxDroneGroupNpc,
 const.groupDeadspaceRogueDroneDestroyer: gfxDroneGroupNpc,
 const.groupDeadspaceRogueDroneFrigate: gfxDroneGroupNpc,
 const.groupDeadspaceRogueDroneSwarm: gfxDroneGroupNpc,
 const.groupAsteroidRogueDroneCommanderFrigate: gfxDroneGroupNpc,
 const.groupAsteroidRogueDroneCommanderDestroyer: gfxDroneGroupNpc,
 const.groupAsteroidRogueDroneCommanderCruiser: gfxDroneGroupNpc,
 const.groupAsteroidRogueDroneCommanderBattleCruiser: gfxDroneGroupNpc,
 const.groupMissionFighterDrone: gfxDroneGroupNpc}
droneTurretGfxID = {gfxDroneGroupFighterBomber: (droneTurretGfxID_fighterbomber, droneTurretGfxID_generic),
 gfxDroneGroupCombat: (droneTurretGfxID_combat, droneTurretGfxID_generic),
 gfxDroneGroupUtility: (None, None),
 gfxDroneGroupMining: (None, droneTurretGfxID_mining),
 gfxDroneGroupNpc: (droneTurretGfxID_combat, droneTurretGfxID_generic),
 gfxDroneGroupSalvager: (None, droneTurretGfxID_salvager)}
EXPLOSION_BASE_PATH = 'res:/fisfx/deathexplosion/death'

def GetDeathExplosionInfo(model, radius, raceName):
    """
    This method builds an explosion path using the raceID. If raceName is not
    defined we use rogue drone explosions as a fallback.
    Takes an optional base path as an argument.
    """
    if raceName is None:
        raceName = gfxRaceRogue
    radius = getattr(model, 'boundingSphereRadius', radius)
    if radius < 20.0:
        size = '_d_'
        delay = 0
        scale = radius / 20.0
    elif radius < 100.0:
        size = '_s_'
        delay = 100
        scale = radius / 100.0
    elif radius < 400.0:
        size = '_m_'
        delay = 250
        scale = radius / 400.0
    elif radius < 1500.0:
        size = '_l_'
        delay = 500
        scale = radius / 700.0
    elif radius < 6000.0:
        size = '_h_'
        delay = 1000
        scale = radius / 6000.0
    else:
        size = '_t_'
        delay = 2000
        scale = 1.0
    path = EXPLOSION_BASE_PATH + size + raceName + '.red'
    info = (delay, scale)
    return (path, info)
