#Embedded file name: eve/client/script/ui/shared/shipTree\shipTreeConst.py
import eve.common.lib.appConst as const
from carbonui.util.color import Color
import localization
TREE_SCALE = 350.0
ZOOMED_IN = 1.0
ZOOMED_OUT = 0.5
NODETYPE_ROOT = 1
NODETYPE_GROUP = 2
NODETYPE_CONNECTOR = 3
NODETYPE_OTHERFACTIONGROUP = 4
PAD_SIDE = 400
PAD_TOP = 200
FACTIONS = (const.factionAmarrEmpire,
 const.factionCaldariState,
 const.factionGallenteFederation,
 const.factionMinmatarRepublic,
 const.factionORE,
 const.factionGuristasPirates,
 const.factionSanshasNation,
 const.factionTheBloodRaiderCovenant,
 const.factionAngelCartel,
 const.factionSerpentis,
 const.factionSistersOfEVE,
 const.factionMordusLegion)
ICON_BY_FACTIONID = {const.factionAmarrEmpire: 'res:/UI/Texture/Classes/ShipTree/factions/amarr.png',
 const.factionCaldariState: 'res:/UI/Texture/Classes/ShipTree/factions/caldari.png',
 const.factionGallenteFederation: 'res:/UI/Texture/Classes/ShipTree/factions/gallente.png',
 const.factionMinmatarRepublic: 'res:/UI/Texture/Classes/ShipTree/factions/minmatar.png',
 const.factionORE: 'res:/UI/Texture/Classes/ShipTree/factions/ORE.png',
 const.factionGuristasPirates: 'res:/UI/Texture/Classes/ShipTree/factions/guristas.png',
 const.factionSanshasNation: 'res:/UI/Texture/Classes/ShipTree/factions/sansha.png',
 const.factionTheBloodRaiderCovenant: 'res:/UI/Texture/Classes/ShipTree/factions/bloodRaiders.png',
 const.factionAngelCartel: 'res:/UI/Texture/Classes/ShipTree/factions/angel.png',
 const.factionSerpentis: 'res:/UI/Texture/Classes/ShipTree/factions/serpentis.png',
 const.factionSistersOfEVE: 'res:/UI/Texture/Classes/ShipTree/factions/soe.png',
 const.factionMordusLegion: 'res:/UI/Texture/Classes/ShipTree/factions/mordus.png'}
HOMESYSTEM_BY_FACTIONID = {const.factionAmarrEmpire: ('res:/dx9/scene/Universe/a03_cube.red', (0, 0, 1000)),
 const.factionCaldariState: ('res:/dx9/scene/Universe/c02_cube.red', (0, 0, 1000)),
 const.factionGallenteFederation: ('res:/dx9/scene/Universe/g03_cube.red', (-629, 223, 742)),
 const.factionMinmatarRepublic: ('res:/dx9/scene/Universe/m02_cube.red', (0, 0, 1000)),
 const.factionORE: ('res:/dx9/scene/Universe/g08_cube.red', (477, -628, -613)),
 const.factionGuristasPirates: ('res:/dx9/scene/Universe/c08_cube.red', (936, 197, -289)),
 const.factionSanshasNation: ('res:/dx9/scene/Universe/a16_cube.red', (-929, 338, -149)),
 const.factionTheBloodRaiderCovenant: ('res:/dx9/scene/Universe/a04_cube.red', (0, 0, 1000)),
 const.factionAngelCartel: ('res:/dx9/scene/Universe/m06_cube.red', (-302, 548, 779)),
 const.factionSerpentis: ('res:/dx9/scene/Universe/g10_cube.red', (0, 0, 1000)),
 const.factionSistersOfEVE: ('res:/dx9/scene/Universe/m02_cube.red', (0, 0, 1000)),
 const.factionMordusLegion: ('res:/dx9/scene/Universe/c02_cube.red', (0, 0, 1000))}

def GetFactionSceneResPathAndEyePos(factionID):
    return HOMESYSTEM_BY_FACTIONID.get(factionID)


AUDIOEVENT_BY_FACTION = {const.factionAmarrEmpire: 'isis_faction_amarr',
 const.factionCaldariState: 'isis_faction_caldari',
 const.factionGallenteFederation: 'isis_faction_gallente',
 const.factionMinmatarRepublic: 'isis_faction_minmatar',
 const.factionORE: 'isis_faction_ore',
 const.factionGuristasPirates: 'isis_faction_guristas',
 const.factionSanshasNation: 'isis_faction_sansha',
 const.factionTheBloodRaiderCovenant: 'isis_faction_bloodraider',
 const.factionAngelCartel: 'isis_faction_angel',
 const.factionSerpentis: 'isis_faction_serpentis',
 const.factionSistersOfEVE: 'isis_faction_sistersofeve',
 const.factionMordusLegion: 'isis_faction_mordu'}

def GetAudioEventIDForFaction(factionID):
    return AUDIOEVENT_BY_FACTION.get(factionID)


COLOR_TEXT = (0.298, 0.549, 0.69, 1.0)
COLOR_TEXT_HILITE = (0.765, 0.914, 1.0, 1.0)
COLOR_MASTERED = (0.988, 0.82, 0.494, 1.0)
COLOR_HILIGHT = (0.753, 0.898, 0.98, 1.0)
COLOR_SHIPGROUP_UNLOCKED = (0.047, 0.063, 0.078, 1.0)
COLOR_SHIPGROUP_LOCKED = (0.0085, 0.0146, 0.02, 1.0)
COLOR_SHIPICON_LOCKED = (0.042, 0.073, 0.1, 0.1)
COLOR_SHIPICON_UNLOCKED = (0.042, 0.073, 0.1, 1.0)
COLOR_FRAME = (0.31, 0.369, 0.4, 0.6)
COLOR_BG = (0.0259, 0.0491, 0.075, 1.0)
COLOR_HOVER_LOCKED = (0.3, 0.3, 0.3, 0.0)
COLOR_HOVER_UNLOCKED = (0.31, 0.675, 1.0, 0.0)
COLOR_HOVER_MASTERED = (1.0, 0.467, 0.145, 0.0)
BG_BY_FACTIONID = {const.factionMinmatarRepublic: 'res:/UI/Texture/Classes/shipTree/factionBG/minmatar.png',
 const.factionAmarrEmpire: 'res:/UI/Texture/Classes/shipTree/factionBG/amarr.png',
 const.factionGallenteFederation: 'res:/UI/Texture/Classes/shipTree/factionBG/gallente.png',
 const.factionCaldariState: 'res:/UI/Texture/Classes/shipTree/factionBG/caldari.png',
 const.factionORE: 'res:/UI/Texture/Classes/shipTree/factionBG/ORE.png',
 const.factionGuristasPirates: 'res:/UI/Texture/Classes/shipTree/factionBG/guristas.png',
 const.factionSanshasNation: 'res:/UI/Texture/Classes/shipTree/factionBG/sanshasNation.png',
 const.factionTheBloodRaiderCovenant: 'res:/UI/Texture/Classes/shipTree/factionBG/bloodRaiders.png',
 const.factionAngelCartel: 'res:/UI/Texture/Classes/shipTree/factionBG/angelCartel.png',
 const.factionSerpentis: 'res:/UI/Texture/Classes/shipTree/factionBG/serpentis.png',
 const.factionSistersOfEVE: 'res:/UI/Texture/Classes/shipTree/factionBG/SOE.png',
 const.factionMordusLegion: 'res:/UI/Texture/Classes/shipTree/factionBG/mordus.png'}
groupRookie = 4
groupFrigate = 8
groupNavyFrigate = 9
groupInterceptor = 10
groupAssault = 11
groupCovertOps = 12
groupElectronicAttack = 13
groupDestroyer = 14
groupInterdictor = 15
groupCruiser = 16
groupNavyCruiser = 17
groupRecon = 18
groupHeavyAssault = 19
groupHeavyInterdictor = 20
groupLogistics = 21
groupStrategicCruiser = 22
groupBattlecruiser = 23
groupCommandship = 24
groupNavyBattlecruiser = 25
groupBattleship = 26
groupBlackOps = 27
groupMarauder = 28
groupDreadnought = 32
groupCarrier = 33
groupTitan = 34
groupShuttle = 35
groupIndustrial = 36
groupFreighter = 37
groupJumpFreighter = 38
groupTransport = 40
groupNavyBattleship = 47
groupTacticalDestroyer = 50
groupMiningFrigate = 41
groupMiningBarge = 42
groupExhumers = 43
groupOreIndustrial = 44
groupIndustrialCommand = 45
groupCapitalIndustrial = 46
groupExpeditionFrigate = 48
groupFilterResults = 100
MAIN_FACTIONS = (const.factionAmarrEmpire,
 const.factionGallenteFederation,
 const.factionCaldariState,
 const.factionMinmatarRepublic)
PARENT_FACTIONIDS_BY_FACTIONID = {const.factionGuristasPirates: (const.factionCaldariState, const.factionGallenteFederation),
 const.factionSanshasNation: (const.factionAmarrEmpire, const.factionCaldariState),
 const.factionTheBloodRaiderCovenant: (const.factionAmarrEmpire, const.factionMinmatarRepublic),
 const.factionAngelCartel: (const.factionGallenteFederation, const.factionMinmatarRepublic),
 const.factionSerpentis: (const.factionGallenteFederation, const.factionMinmatarRepublic),
 const.factionSistersOfEVE: (const.factionAmarrEmpire, const.factionGallenteFederation),
 const.factionMordusLegion: (const.factionCaldariState, const.factionGallenteFederation)}

def GetTagIconForType(typeID):
    techLevel = sm.GetService('godma').GetTypeAttribute(typeID, const.attributeTechLevel)
    if techLevel == 2:
        return 'res:/UI/Texture/classes/ShipTree/tech/tech2.png'
    if techLevel == 3:
        return 'res:/UI/Texture/classes/ShipTree/tech/tech3.png'
    metaGroupID = sm.GetService('godma').GetTypeAttribute(typeID, const.attributeMetaGroupID)
    if metaGroupID == const.metaGroupFaction:
        return 'res:/UI/Texture/classes/ShipTree/tech/navy.png'
