#Embedded file name: eve/common/lib\appConst.py
"""
This is the file where all EVE constants are kept.
Copyright now and forever CCP.
Matthias Gudmundsson.

This file needs to be organized. Add comments with your constants.
"""
from carbon.common.lib.const import *
from eve.common.lib.infoEventConst import *
from inventorycommon.const import *
from dogma.const import *
from crimewatch.const import *
from eveexceptions.const import *
from probescanning.const import *
from characterskills.const import *
from eve.common.script.util.notificationconst import *
from evefleet.const import *
FEMALE = 0
MALE = 1
TYPEID_NONE = -1
USL_SERVER_PORT = 26004
NUM_BATTLES_PER_NODE = 256
intervalDustUser = 20
minDustUserType = 100
minDustUser = 1000000000
minDustCharacter = 2100000000
maxDustCharacter = 2130000000
userTypeDustPlayer = 101
userTypeDustCCP = 102
userTypeDustBattleServer = 103
userConnectTypeDustClient = 101
objectiveStateCeasefire = 0
objectiveStateMobilizing = 1
objectiveStateWar = 2
objectiveStateRebuilding = 3
OFFLINE_CHARID = -1
OFFLINE_USERID = -1
DUST_AUR_CURRENCY = 'AUR'
DUST_ISK_CURRENCY = 'ISK'
ACCOUNTING_DUST_ISK = 10000
ACCOUNTING_DUST_AUR = 11000
corporationStartupCost = 1599800
colorValues = [{'color': '0x202020',
  'blending': 'solid',
  'id': 671},
 {'color': '0xa5d4ff',
  'blending': 'multiply',
  'id': 673},
 {'color': '0xffffff',
  'blending': 'multiply',
  'id': 674},
 {'color': '0x789fff',
  'blending': 'multiply',
  'id': 676},
 {'color': '0xffd659',
  'blending': 'multiply',
  'id': 677},
 {'color': '0x939b9b',
  'blending': 'multiply',
  'id': 678},
 {'color': '0xff7800',
  'blending': 'multiply',
  'id': 679},
 {'color': '0x960000',
  'blending': 'multiply',
  'id': 680},
 {'color': '0x000000',
  'blending': 'solid',
  'alpha': 50,
  'id': 682},
 {'color': '0x3e4040',
  'blending': 'solid',
  'alpha': 40,
  'id': 683},
 {'color': '0xe8e8e8',
  'blending': 'solid',
  'id': 684},
 {'color': '0xffb23e',
  'blending': 'solid',
  'id': 685}]
ACCOUNT_TYPES_TO_CURRENCY_TYPE = {ACCOUNTING_DUST_ISK: DUST_ISK_CURRENCY}
VALID_VGS_CURRENCIES = set([DUST_AUR_CURRENCY])
DUST_VGS_STORE_NAME = 'DUST 514 Virtual Goods Store'
ACCOUNTING_DUST_MODIFYISK = 10001
ACCOUNTING_DUST_PRIMARYMARKETPURCHASE = 10002
ACCOUNTING_DUST_NEW_CHARACTER_MONEY = 10004
ACCOUNTING_DUST_CORP_WITHDRAWAL = 10005
ACCOUNTING_DUST_CORP_DEPOSIT = 10006
ACCOUNTING_DUST_BATTLEREWARD_WIN = 10009
ACCOUNTING_DUST_BATTLEREWARD_LOSS = 10010
ACCOUNTING_DUST_ISK_RESET_FOR_CHARACTER_WIPE = 10011
ACCOUNTING_DUST_CONTRACT_DEPOSIT = 10012
ACCOUNTING_DUST_CONTRACT_DEPOSIT_REFUND = 10013
ACCOUNTING_DUST_CONTRACT_COLLATERAL = 10014
ACCOUNTING_DUST_CONTRACT_COLLATERAL_REFUND = 10015
ACCOUNTING_DUST_CONTRACT_REWARD = 10016
refCloneTransport = 10017
refCloneTransportRefund = 10018
refDistrictInfrastructure = 10019
refCloneSales = 10020
refClonePurchase = 10021
refBattleRewardBiomass = 10022
ACCOUNTING_DUST_MODIFYRMC = 11001
BATTLEKICKSTATUS_SERVERSHUTDOWN = 0
BATTLEKICKSTATUS_NORMALKICK = 1
DATA_SORT_ORDER_ASC = 0
DATA_SORT_ORDER_DESC = 1
MARKET_GROUPID_UNCATEGORIZED = -1
MARKET_GROUPNAME_UNCATEGORIZED = 'Uncategorized Items'
FAKE_ITEM_ID = None
CHARACTER_POSITION_RESPAWN = -1
CHARACTER_POSITION_RUN = 0
CHARACTER_POSITION_DRIVEN = 1
CHARACTER_POSITION_FLOWN = 2
INVOKE_ASYNCHRONOUS = 0
INVOKE_SYNCHRONOUS = 1
GTYPE_TEAM = 0
GTYPE_COMMANDER = 1
GTYPE_DOODLE = 2
GTYPE_SKIRMISH = 3
GTYPE_UNKNOWN = 4
DEFAULT_SPAWN_POINT = -1
battleLightingMoodDay = 0
battleLightingMoodDull = 1
battleLightingMoodDark = 2
BATTLE_LIGHTING_MOOD = {battleLightingMoodDay: 'MOOD_DAY',
 battleLightingMoodDull: 'MOOD_DULL',
 battleLightingMoodDark: 'MOOD_DARK'}
battleTypeBattleSeries = 0
battleTypeCorporationBattle = 1
SKILL_MULTIPLIER_PASSIVE_BOOSTER = 0
SKILL_MULTIPLIER_ACTIVE_BOOSTER = 1
VOICE_ACTIVATION_BOOSTER = 2
FACTION_BOOSTER_AMARR = 3
FACTION_BOOSTER_CALDARI = 4
FACTION_BOOSTER_GALLENTE = 5
FACTION_BOOSTER_MINMATAR = 6
STACKABLE_BOOSTERS_STACK_LIMIT_DEFAULT = 3
STACKABLE_BOOSTERS = [SKILL_MULTIPLIER_PASSIVE_BOOSTER,
 SKILL_MULTIPLIER_ACTIVE_BOOSTER,
 FACTION_BOOSTER_AMARR,
 FACTION_BOOSTER_CALDARI,
 FACTION_BOOSTER_GALLENTE,
 FACTION_BOOSTER_MINMATAR]
EDITOR_MULTIPLIER_KIND_NAME = {SKILL_MULTIPLIER_PASSIVE_BOOSTER: 'Passive',
 SKILL_MULTIPLIER_ACTIVE_BOOSTER: 'Active',
 VOICE_ACTIVATION_BOOSTER: 'Voice',
 FACTION_BOOSTER_AMARR: 'Faction Amarr',
 FACTION_BOOSTER_CALDARI: 'Faction Caldari',
 FACTION_BOOSTER_GALLENTE: 'Faction Gallente',
 FACTION_BOOSTER_MINMATAR: 'Faction Minmatar'}
MULTIPLIER_CATMA_CLASS_NAME = {SKILL_MULTIPLIER_PASSIVE_BOOSTER: 'PassiveSkillGainBooster',
 SKILL_MULTIPLIER_ACTIVE_BOOSTER: 'ActiveSkillGainBooster',
 FACTION_BOOSTER_AMARR: 'FactionBoosterAmarr',
 FACTION_BOOSTER_CALDARI: 'FactionBoosterCaldari',
 FACTION_BOOSTER_GALLENTE: 'FactionBoosterGallente',
 FACTION_BOOSTER_MINMATAR: 'FactionBoosterMinmatar'}
MULTIPLIER_REASON_CHARACTER_SKILL_GAIN = 0
MULTIPLIER_REASON_BOOSTER = 1
EDITOR_MULTIPLIER_REASON_NAME = {MULTIPLIER_REASON_CHARACTER_SKILL_GAIN: 'Passive Skill Gain Activated',
 MULTIPLIER_REASON_BOOSTER: 'Booster'}
MAX_DUST_SKILL_LEVEL = 5
DUST_SKILL_COST_TABLE = [6220,
 18650,
 43530,
 87060,
 155460]
MAX_PLAYERLIST_IN_CORP_CHAT = 20
BATTLE_REGION_US = 10007
BATTLE_REGION_EU = 10008
BATTLE_REGION_ASIA = 10009
BATTLE_REGION_ALL = 10010
SEARCH_CHARS_NPCS_CORPS = 0
SEARCH_CHARS_NPCS = 1
SEARCH_CORPS = 2
SEARCH_PLAYER_CHARS = 3
SEARCH_DUST_PLAYER_CHARS = 4
SEARCH_EVE_PLAYER_CHARS = 5
SEARCH_PLAYER_CHARS_CORPS = 6
SKILL_CORPORATION_MANAGEMENT = 352887
SKILL_EMIPRE_CONTROL = 352890
SKILL_MEGACORP_MANAGEMENT = 352888
RDV_DENIED_REQUESTNOTFINISH = 'requestNotFinish'
DUST_CHARACTER_PASSIVE_SKILL_GAIN_MULTIPLIER = 1.0
DUST_CHARACTER_ACTIVE_SKILL_BOOSTER_DEFAULT_MULTIPLIER = 0.5
BASE_MULTIPLIERS = {SKILL_MULTIPLIER_ACTIVE_BOOSTER: 1.0,
 SKILL_MULTIPLIER_PASSIVE_BOOSTER: 0.0}
userTypeBattleServer = 103
intervalEveUser = 10
uniqueCharacterIdentifier = 'charid'
ACT_IDX_START = 0
ACT_IDX_DURATION = 1
ACT_IDX_ENV = 2
ACT_IDX_REPEAT = 3
AU = 149597870700.0
LIGHTYEAR = 9460000000000000.0
ALSCActionNone = 0
ALSCActionAdd = 6
ALSCActionAssemble = 1
ALSCActionConfigure = 10
ALSCActionEnterPassword = 9
ALSCActionLock = 7
ALSCActionRepackage = 2
ALSCActionSetName = 3
ALSCActionSetPassword = 5
ALSCActionUnlock = 8
ALSCPasswordNeededToOpen = 1
ALSCPasswordNeededToLock = 2
ALSCPasswordNeededToUnlock = 4
ALSCPasswordNeededToViewAuditLog = 8
ALSCLockAddedItems = 16
CTPC_CHAT = 8
CTPC_MAIL = 9
CTPG_CASH = 6
CTPG_SHARES = 7
CTV_ADD = 1
CTV_COMMS = 5
CTV_GIVE = 4
CTV_REMOVE = 2
CTV_SET = 3
SCCPasswordTypeConfig = 2
SCCPasswordTypeGeneral = 1
agentTypeBasicAgent = 2
agentTypeEventMissionAgent = 8
agentTypeGenericStorylineMissionAgent = 6
agentTypeNonAgent = 1
agentTypeResearchAgent = 4
agentTypeStorylineMissionAgent = 7
agentTypeTutorialAgent = 3
agentTypeFactionalWarfareAgent = 9
agentTypeEpicArcAgent = 10
agentTypeAura = 11
agentTypeCareerAgent = 12
auraAgentIDs = [3019499,
 3019493,
 3019495,
 3019490,
 3019497,
 3019496,
 3019486,
 3019498,
 3019492,
 3019500,
 3019489,
 3019494]
agentRangeSameSystem = 1
agentRangeSameOrNeighboringSystemSameConstellation = 2
agentRangeSameOrNeighboringSystem = 3
agentRangeNeighboringSystemSameConstellation = 4
agentRangeNeighboringSystem = 5
agentRangeSameConstellation = 6
agentRangeSameOrNeighboringConstellationSameRegion = 7
agentRangeSameOrNeighboringConstellation = 8
agentRangeNeighboringConstellationSameRegion = 9
agentRangeNeighboringConstellation = 10
agentRangeNearestEnemyCombatZone = 11
agentRangeNearestCareerHub = 12
agentIskMultiplierLevel1 = 1
agentIskMultiplierLevel2 = 2
agentIskMultiplierLevel3 = 4
agentIskMultiplierLevel4 = 8
agentIskMultiplierLevel5 = 16
agentIskMultipliers = (agentIskMultiplierLevel1,
 agentIskMultiplierLevel2,
 agentIskMultiplierLevel3,
 agentIskMultiplierLevel4,
 agentIskMultiplierLevel5)
agentLpMultiplierLevel1 = 20
agentLpMultiplierLevel2 = 60
agentLpMultiplierLevel3 = 180
agentLpMultiplierLevel4 = 540
agentLpMultiplierLevel5 = 4860
agentLpMultipliers = (agentLpMultiplierLevel1,
 agentLpMultiplierLevel2,
 agentLpMultiplierLevel3,
 agentLpMultiplierLevel4,
 agentLpMultiplierLevel5)
agentIskRandomLowValue = 11000
agentIskRandomHighValue = 16500
agentDivisionBusiness = 25
agentDivisionExploration = 26
agentDivisionIndustry = 27
agentDivisionMilitary = 28
agentDivisionAdvMilitary = 29
agentDivisionsCareer = [agentDivisionBusiness,
 agentDivisionExploration,
 agentDivisionIndustry,
 agentDivisionMilitary,
 agentDivisionAdvMilitary]
agentDialogueButtonViewMission = 1
agentDialogueButtonRequestMission = 2
agentDialogueButtonAccept = 3
agentDialogueButtonAcceptChoice = 4
agentDialogueButtonAcceptRemotely = 5
agentDialogueButtonComplete = 6
agentDialogueButtonCompleteRemotely = 7
agentDialogueButtonContinue = 8
agentDialogueButtonDecline = 9
agentDialogueButtonDefer = 10
agentDialogueButtonQuit = 11
agentDialogueButtonStartResearch = 12
agentDialogueButtonCancelResearch = 13
agentDialogueButtonBuyDatacores = 14
agentDialogueButtonLocateCharacter = 15
agentDialogueButtonLocateAccept = 16
agentDialogueButtonLocateReject = 17
agentDialogueButtonYes = 18
agentDialogueButtonNo = 19
allianceApplicationAccepted = 2
allianceApplicationEffective = 3
allianceApplicationNew = 1
allianceApplicationRejected = 4
allianceCreationCost = 1000000000
allianceMembershipCost = 2000000
allianceRelationshipCompetitor = 3
allianceRelationshipEnemy = 4
allianceRelationshipFriend = 2
allianceRelationshipNAP = 1
bloodline11Type = 1383
bloodline5Type = 1373
bloodline4Type = 1380
bloodline2Type = 1375
bloodline1Type = 1376
bloodline7Type = 1377
bloodline8Type = 1378
bloodline12Type = 1384
bloodline13Type = 1385
bloodline10Type = 1382
bloodline6Type = 1374
bloodline3Type = 1379
bloodline9Type = 1381
bloodline14Type = 1386
bloodlineAchura = 11
bloodlineAmarr = 5
bloodlineBrutor = 4
bloodlineCivire = 2
bloodlineDeteis = 1
bloodlineGallente = 7
bloodlineIntaki = 8
bloodlineJinMei = 12
bloodlineKhanid = 13
bloodlineModifier = 10
bloodlineNiKunni = 6
bloodlineSebiestor = 3
bloodlineStatic = 9
bloodlineVherokior = 14
raceCaldari = 1
raceMinmatar = 2
raceAmarr = 4
raceGallente = 8
raceJove = 16
raceAngel = 32
raceSleepers = 64
raceORE = 128
races = {raceCaldari: 'Caldari',
 raceMinmatar: 'Minmatar',
 raceAmarr: 'Amarr',
 raceGallente: 'Gallente',
 raceJove: 'Jove',
 raceAngel: 'Angel',
 raceSleepers: 'Sleepers',
 raceORE: 'ORE'}
raceByBloodline = {bloodlineDeteis: raceCaldari,
 bloodlineCivire: raceCaldari,
 bloodlineSebiestor: raceMinmatar,
 bloodlineBrutor: raceMinmatar,
 bloodlineAmarr: raceAmarr,
 bloodlineNiKunni: raceAmarr,
 bloodlineGallente: raceGallente,
 bloodlineIntaki: raceGallente,
 bloodlineAchura: raceCaldari,
 bloodlineJinMei: raceGallente,
 bloodlineKhanid: raceAmarr,
 bloodlineVherokior: raceMinmatar}
cacheEosNpcToNpcStandings = 109998
cacheAutAffiliates = 109997
cacheAutCdkeyTypes = 109996
cacheEveWarnings = 109995
cacheTutCategories = 200006
cacheTutCriterias = 200003
cacheTutTutorials = 200001
cacheTutActions = 200009
cacheDungeonArchetypes = 300001
cacheDungeonDungeons = 300005
cacheDungeonEntityGroupTypes = 300004
cacheDungeonEventMessageTypes = 300017
cacheDungeonEventTypes = 300015
cacheDungeonSpawnpoints = 300012
cacheDungeonTriggerTypes = 300013
cacheInvCategories = 600001
cacheInvContrabandTypes = 600008
cacheInvGroups = 600002
cacheInvTypes = 600004
cacheInvTypeMaterials = 600005
cacheInvTypeReactions = 600010
cacheInvWreckUsage = 600009
cacheInvMetaGroups = 600006
cacheInvMetaTypes = 600007
cacheDogmaAttributes = 800004
cacheDogmaEffects = 800005
cacheDogmaExpressionCategories = 800001
cacheDogmaExpressions = 800003
cacheDogmaOperands = 800002
cacheDogmaTypeAttributes = 800006
cacheDogmaTypeEffects = 800007
cacheDogmaUnits = 800009
cacheEveMessages = 1000001
cacheMapRegions = 1409999
cacheMapConstellations = 1409998
cacheMapSolarSystems = 1409997
cacheMapSolarSystemLoadRatios = 1409996
cacheLocationWormholeClasses = 1409994
cacheMapPlanets = 1409993
cacheMapSolarSystemJumpIDs = 1409992
cacheMapTypeBalls = 1400001
cacheMapWormholeClasses = 1400003
cacheMapCelestialDescriptions = 1400008
cacheMapNebulas = 1400016
cacheMapLocationWormholeClasses = 1400002
cacheMapPlanetsTable = 1400020
cacheMapMoonsTable = 1400021
cacheMapStargateTable = 1400022
cacheMapStarsTable = 1400023
cacheMapBeltsTable = 1400024
cacheMapCelestialStatistics = 1400025
cacheNpcCommandLocations = 1600009
cacheNpcCommands = 1600005
cacheNpcDirectorCommandParameters = 1600007
cacheNpcDirectorCommands = 1600006
cacheNpcLootTableFrequencies = 1600004
cacheNpcCommandParameters = 1600008
cacheNpcTypeGroupingClassSettings = 1600016
cacheNpcTypeGroupingClasses = 1600015
cacheNpcTypeGroupingTypes = 1600017
cacheNpcTypeGroupings = 1600014
cacheNpcTypeLoots = 1600001
cacheRamSkillInfo = 1809999
cacheRamActivities = 1800003
cacheRamAssemblyLineTypes = 1800006
cacheRamAssemblyLineTypesCategory = 1800004
cacheRamAssemblyLineTypesGroup = 1800005
cacheRamCompletedStatuses = 1800007
cacheRamInstallationTypes = 1800002
cacheRamTypeRequirements = 1800001
cacheShipInsurancePrices = 2000007
cacheShipTypes = 2000001
cacheStaOperations = 2209999
cacheStaServices = 2209998
cacheStaOperationServices = 2209997
cacheStaSIDAssemblyLineQuantity = 2209996
cacheStaSIDAssemblyLineType = 2209995
cacheStaSIDAssemblyLineTypeQuantity = 2209994
cacheStaSIDOfficeSlots = 2209993
cacheOutpostReprocessingEfficiency_Get = 2209992
cacheStaStationImprovementTypes = 2209990
cacheStaStationUpgradeTypes = 2209989
cacheStaStations = 2209988
cacheStaStationsStatic = 2209987
cacheMktAveragePriceHistorySelect = 2409996
cacheMktOrderStates = 2409999
cacheMktNpcMarketData = 2400001
cacheCrpRoles = 2809999
cacheCrpActivities = 2809998
cacheCrpNpcDivisions = 2809997
cacheCrpCorporations = 2809996
cacheCrpNpcMembers = 2809994
cacheCrpPlayerCorporationIDs = 2809993
cacheCrpTickerNamesStatic = 2809992
cacheNpcSupplyDemand = 2800001
cacheCrpRegistryGroups = 2800002
cacheCrpRegistryTypes = 2800003
cacheCrpNpcCorporations = 2800006
cacheAgentAgents = 3009999
cacheAgentCorporationActivities = 3009998
cacheAgentCorporations = 3009997
cacheAgentEpicMissionMessages = 3009996
cacheAgentEpicMissionsBranching = 3009995
cacheAgentEpicMissionsNonEnd = 3009994
cacheAgtContentAgentInteractionMissions = 3009992
cacheAgtContentFlowControl = 3009991
cacheAgtContentTalkToAgentMissions = 3009990
cacheAgtPrices = 3009989
cacheAgtContentTemplates = 3000001
cacheAgentMissionsKill = 3000006
cacheAgtStorylineMissions = 3000008
cacheAgtContentCourierMissions = 3000003
cacheAgtContentExchangeOffers = 3000005
cacheAgentEpicArcConnections = 3000013
cacheAgentEpicArcMissions = 3000015
cacheAgentEpicArcs = 3000012
cacheAgtContentMissionExtraStandings = 3000020
cacheAgtContentMissionTutorials = 3000018
cacheAgtContentMissionLocationFilters = 3000021
cacheAgtOfferDetails = 3000004
cacheAgtOfferTableContents = 3000010
cacheChrSchools = 3209997
cacheChrRaces = 3200001
cacheChrBloodlines = 3200002
cacheChrAncestries = 3200003
cacheChrCareers = 3200004
cacheChrSpecialities = 3200005
cacheChrBloodlineNames = 3200010
cacheChrAttributes = 3200014
cacheChrFactions = 3200015
cacheChrDefaultOverviews = 3200011
cacheChrDefaultOverviewGroups = 3200012
cacheChrNpcCharacters = 3200016
cacheFacWarCombatZoneSystems = 4500006
cacheFacWarCombatZones = 4500005
cacheRedeemWhitelist = 6300001
cacheActBillTypes = 6400004
cachePetCategories = 8109999
cachePetQueues = 8109998
cachePetCategoriesVisible = 8109997
cachePetGMQueueOrder = 8109996
cachePetOsTypes = 8109995
cacheCertificates = 5100001
cacheCertificateRelationships = 5100004
cachePlanetBlacklist = 7309999
cachePlanetSchematics = 7300004
cachePlanetSchematicsTypeMap = 7300005
cachePlanetSchematicsPinMap = 7300003
cacheMapDistrictCelestials = 100309999
cacheMapDistricts = 100300014
cacheMapBattlefields = 100300015
cacheMapLevels = 100300020
cacheMapOutposts = 100300022
cacheMapLandmarks = 100300023
cacheEspCorporations = 1
cacheEspAlliances = 2
cacheEspSolarSystems = 3
cacheSolarSystemObjects = 4
cacheCargoContainers = 5
cachePriceHistory = 6
cacheTutorialVersions = 7
cacheSolarSystemOffices = 8
tableTutorialTutorials = 200001
tableDungeonDungeons = 300005
tableAgentMissions = 3000002
corpLogoChangeCost = 100
corpRoleDiplomat = 17179869184L
corpRoleAccountCanTake1 = 134217728
corpRoleAccountCanTake2 = 268435456
corpRoleAccountCanTake3 = 536870912
corpRoleAccountCanTake4 = 1073741824
corpRoleAccountCanTake5 = 2147483648L
corpRoleAccountCanTake6 = 4294967296L
corpRoleAccountCanTake7 = 8589934592L
corpRoleAccountant = 256
corpRoleAuditor = 4096
corpRoleCanRentFactorySlot = 1125899906842624L
corpRoleCanRentOffice = 562949953421312L
corpRoleCanRentResearchSlot = 2251799813685248L
corpRoleChatManager = 36028797018963968L
corpRoleContainerCanTake1 = 4398046511104L
corpRoleContainerCanTake2 = 8796093022208L
corpRoleContainerCanTake3 = 17592186044416L
corpRoleContainerCanTake4 = 35184372088832L
corpRoleContainerCanTake5 = 70368744177664L
corpRoleContainerCanTake6 = 140737488355328L
corpRoleContainerCanTake7 = 281474976710656L
corpRoleContractManager = 72057594037927936L
corpRoleStarbaseCaretaker = 288230376151711744L
corpRoleDirector = 1
corpRoleEquipmentConfig = 2199023255552L
corpRoleFactoryManager = 1024
corpRoleFittingManager = 576460752303423488L
corpRoleHangarCanQuery1 = 1048576
corpRoleHangarCanQuery2 = 2097152
corpRoleHangarCanQuery3 = 4194304
corpRoleHangarCanQuery4 = 8388608
corpRoleHangarCanQuery5 = 16777216
corpRoleHangarCanQuery6 = 33554432
corpRoleHangarCanQuery7 = 67108864
corpRoleHangarCanTake1 = 8192
corpRoleHangarCanTake2 = 16384
corpRoleHangarCanTake3 = 32768
corpRoleHangarCanTake4 = 65536
corpRoleHangarCanTake5 = 131072
corpRoleHangarCanTake6 = 262144
corpRoleHangarCanTake7 = 524288
corpRoleJuniorAccountant = 4503599627370496L
corpRoleLocationTypeBase = 2
corpRoleLocationTypeHQ = 1
corpRoleLocationTypeOther = 3
corpRolePersonnelManager = 128
corpRoleSecurityOfficer = 512
corpRoleStarbaseConfig = 9007199254740992L
corpRoleStationManager = 2048
corpRoleTrader = 18014398509481984L
corpRoleInfrastructureTacticalOfficer = 144115188075855872L
corpRoleTerrestrialCombatOfficer = 1152921504606846976L
corpRoleTerrestrialLogisticsOfficer = 2305843009213693952L
corpHangarTakeRolesByFlag = {flagHangar: corpRoleHangarCanTake1,
 flagCorpSAG2: corpRoleHangarCanTake2,
 flagCorpSAG3: corpRoleHangarCanTake3,
 flagCorpSAG4: corpRoleHangarCanTake4,
 flagCorpSAG5: corpRoleHangarCanTake5,
 flagCorpSAG6: corpRoleHangarCanTake6,
 flagCorpSAG7: corpRoleHangarCanTake7}
corpHangarQueryRolesByFlag = {flagHangar: corpRoleHangarCanQuery1,
 flagCorpSAG2: corpRoleHangarCanQuery2,
 flagCorpSAG3: corpRoleHangarCanQuery3,
 flagCorpSAG4: corpRoleHangarCanQuery4,
 flagCorpSAG5: corpRoleHangarCanQuery5,
 flagCorpSAG6: corpRoleHangarCanQuery6,
 flagCorpSAG7: corpRoleHangarCanQuery7}
corpContainerTakeRolesByFlag = {flagHangar: corpRoleContainerCanTake1,
 flagCorpSAG2: corpRoleContainerCanTake2,
 flagCorpSAG3: corpRoleContainerCanTake3,
 flagCorpSAG4: corpRoleContainerCanTake4,
 flagCorpSAG5: corpRoleContainerCanTake5,
 flagCorpSAG6: corpRoleContainerCanTake6,
 flagCorpSAG7: corpRoleContainerCanTake7}
corpStationMgrGraceMinutes = 60
corpactivityEducation = 18
corpactivityEntertainment = 8
corpactivityMilitary = 5
corpactivitySecurity = 16
corpactivityTrading = 12
corpactivityWarehouse = 10
corpDivisionDistribution = 22
corpDivisionMining = 23
corpDivisionSecurity = 24
corporationStartupCost = 1599800
corporationAdvertisementFlatFee = 500000
corporationAdvertisementDailyRate = 250000
corporationMaxCorpRecruiters = 6
corporationMaxRecruitmentAds = 3
corporationMaxRecruitmentAdDuration = 28
corporationMinRecruitmentAdDuration = 3
corporationRecMaxTitleLength = 40
corporationRecMaxMessageLength = 1000
dunArchetypeCOSMOSFlags = 1
dunArchetypeAgentMissionDungeon = 20
dunArchtypeTaleDungeon = 21
dunArchetypeHiddenMiniProfessions = 29
dunArchetypeFacwarDefensive = 32
dunArchetypeFacwarOffensive = 35
dunArchetypeFacwarDungeons = (dunArchetypeFacwarDefensive, dunArchetypeFacwarOffensive)
dunArchetypeWormhole = 38
dunArchetypeZTest = 19
dunEventMessageEnvironment = 3
dunEventMessageImminentDanger = 1
dunEventMessageMissionInstruction = 7
dunEventMessageMissionObjective = 6
dunEventMessageMood = 4
dunEventMessageNPC = 2
dunEventMessageStory = 5
dunEventMessageWarning = 8
dunExpirationDelay = 48
dungeonGateUnlockPeriod = 66
dungeonKeylockUnlocked = 0
dungeonKeylockPrivate = 1
dungeonKeylockPublic = 2
dungeonKeylockTrigger = 3
dunTriggerArchaeologyFailure = 16
dunTriggerArchaeologySuccess = 15
dunTriggerArmorConditionLevel = 5
dunTriggerAttacked = 1
dunTriggerCounterEQ = 34
dunTriggerCounterGE = 36
dunTriggerCounterGT = 35
dunTriggerCounterLE = 38
dunTriggerCounterLT = 37
dunTriggerEffectActivated = 27
dunTriggerExploding = 3
dunTriggerFWShipEnteredProximity = 21
dunTriggerFWShipLeftProximity = 30
dunTriggerHackingFailure = 12
dunTriggerHackingSuccess = 11
dunTriggerItemInCargo = 33
dunTriggerItemPlacedInMissionContainer = 23
dunTriggerItemRemovedFromSpawnContainer = 32
dunTriggerMined = 7
dunTriggerPlayerKilled = 26
dunTriggerRoomCapturedAlliance = 19
dunTriggerRoomCapturedFacWar = 20
dunTriggerRoomCapturedCorp = 18
dunTriggerRoomEntered = 8
dunTriggerRoomMined = 10
dunTriggerRoomMinedOut = 9
dunTriggerRoomWipedOut = 31
dunTriggerSalvagingFailure = 14
dunTriggerSalvagingSuccess = 13
dunTriggerShieldConditionLevel = 4
dunTriggerShipEnteredProximity = 2
dunTriggerShipLeftProximity = 29
dunTriggerShipsEnteredRoom = 17
dunTriggerShipsLeftRoom = 28
dunTriggerStructureConditionLevel = 6
dunTriggerTimerComplete = 41
dunTriggerEventActivateGate = 1
dunTriggerEventAdjustSystemInfluence = 39
dunTriggerEventAgentMessage = 23
dunTriggerEventAgentTalkTo = 22
dunTriggerEventCounterAdd = 32
dunTriggerEventCounterDivide = 35
dunTriggerEventCounterMultiply = 34
dunTriggerEventCounterSet = 36
dunTriggerEventCounterSubtract = 33
dunTriggerEventDropLoot = 24
dunTriggerEventDungeonCompletion = 11
dunTriggerEventEffectBeaconActivate = 13
dunTriggerEventEffectBeaconDeactivate = 14
dunTriggerEventEntityDespawn = 18
dunTriggerEventEntityExplode = 19
dunTriggerEventGrantGroupReward = 37
dunTriggerEventGrantGroupRewardLimitedRestrictions = 45
dunTriggerEventGrantDelayedGroupReward = 38
dunTriggerFacWarLoyaltyPointsGranted = 48
dunTriggerFacWarVictoryPointsGranted = 20
dunTriggerEventMessage = 10
dunTriggerEventMissionCompletion = 9
dunTriggerEventMissionFailure = 31
dunTriggerEventObjectDespawn = 15
dunTriggerEventObjectExplode = 16
dunTriggerEventOpenTutorial = 46
dunTriggerEventRangedNPCDamageEM = 26
dunTriggerEventRangedNPCDamageExplosive = 27
dunTriggerEventRangedNPCDamageKinetic = 28
dunTriggerEventRangedNPCDamageThermal = 29
dunTriggerEventRangedNPCHealing = 4
dunTriggerEventRangedPlayerDamageEM = 5
dunTriggerEventRangedPlayerDamageExplosive = 6
dunTriggerEventRangedPlayerDamageKinetic = 7
dunTriggerEventRangedPlayerDamageThermal = 8
dunTriggerEventRangedPlayerHealing = 25
dunTriggerEventSpawnGuardObject = 3
dunTriggerEventSpawnGuards = 2
dunTriggerEventSpawnItemInCargo = 30
dunTriggerEventSpawnShip = 47
dunTriggerEventSupressAllRespawn = 42
dunTriggerEventTimerCancel = 52
dunTriggerEventTimerStart = 49
dunTriggerEventWarpShipAwayAndComeBack = 41
dunTriggerEventWarpShipAwayDespawn = 40
DUNGEON_EVENT_TYPE_AFFECTS_ENTITY = [dunTriggerEventEntityExplode,
 dunTriggerEventEntityDespawn,
 dunTriggerEventSpawnGuards,
 dunTriggerEventWarpShipAwayDespawn,
 dunTriggerEventWarpShipAwayAndComeBack]
DUNGEON_EVENT_TYPE_AFFECTS_OBJECT = [dunTriggerEventSpawnGuardObject,
 dunTriggerEventEffectBeaconActivate,
 dunTriggerEventEffectBeaconDeactivate,
 dunTriggerEventObjectExplode,
 dunTriggerEventObjectDespawn,
 dunTriggerEventActivateGate]
DUNGEON_ORIGIN_UNDEFINED = None
DUNGEON_ORIGIN_STATIC = 1
DUNGEON_ORIGIN_AGENT = 2
DUNGEON_ORIGIN_PLAYTEST = 3
DUNGEON_ORIGIN_EDIT = 4
DUNGEON_ORIGIN_DISTRIBUTION = 5
DUNGEON_ORIGIN_PATH = 6
DUNGEON_ORIGIN_TUTORIAL = 7
dungeonSpawnBelts = 0
dungeonSpawnGate = 1
dungeonSpawnNear = 2
dungeonSpawnDeep = 3
dungeonSpawnReinforcments = 4
dungeonSpawnStations = 5
dungeonSpawnFaction = 6
dungeonSpawnConcord = 7
locationAbstract = 0
locationSystem = 1
locationBank = 2
locationTemp = 5
locationTrading = 7
locationGraveyard = 8
locationUniverse = 9
locationHiddenSpace = 9000001
locationJunkyard = 10
locationCorporation = 13
locationTradeSessionJunkyard = 1008
locationCharacterGraveyard = 1501
locationCorporationGraveyard = 1502
locationRAMInstalledItems = 2003
locationAlliance = 3007
locationMinJunkyardID = 1000
locationMaxJunkyardID = 1999
minFaction = 500000
maxFaction = 599999
minNPCCorporation = 1000000
maxNPCCorporation = 1999999
minAgent = 3000000
maxAgent = 3999999
minRegion = 10000000
maxRegion = 19999999
minConstellation = 20000000
maxConstellation = 29999999
minSolarSystem = 30000000
maxSolarSystem = 39999999
minValidLocation = 30000000
minValidShipLocation = 30000000
minUniverseCelestial = 40000000
maxUniverseCelestial = 49999999
minStargate = 50000000
maxStargate = 59999999
minStation = 60000000
maxNPCStation = 60999999
maxStation = 69999999
minValidCharLocation = 60000000
minUniverseAsteroid = 70000000
maxUniverseAsteroid = 79999999
minPlayerItem = 100000000
maxNonCapitalModuleSize = 3500
minDistrict = 82000000
maxDistrict = 84999999
minEveMarketGroup = 0
maxEveMarketGroup = 350000
minDustMarketGroup = 350001
maxDustMarketGroup = 999999
factionNoFaction = 0
factionAmarrEmpire = 500003
factionAmmatar = 500007
factionAngelCartel = 500011
factionCONCORDAssembly = 500006
factionCaldariState = 500001
factionGallenteFederation = 500004
factionGuristasPirates = 500010
factionInterBus = 500013
factionJoveEmpire = 500005
factionKhanidKingdom = 500008
factionMinmatarRepublic = 500002
factionMordusLegion = 500018
factionORE = 500014
factionOuterRingExcavations = 500014
factionSanshasNation = 500019
factionSerpentis = 500020
factionSistersOfEVE = 500016
factionSocietyOfConsciousThought = 500017
factionTheBloodRaiderCovenant = 500012
factionTheServantSistersofEVE = 500016
factionTheSyndicate = 500009
factionThukkerTribe = 500015
factionUnknown = 500021
factionMordusLegionCommand = 500018
factionTheInterBus = 500013
factionAmmatarMandate = 500007
factionTheSociety = 500017
refSkipLog = -1
refUndefined = 0
refPlayerTrading = 1
refMarketTransaction = 2
refGMCashTransfer = 3
refATMWithdraw = 4
refATMDeposit = 5
refBackwardCompatible = 6
refMissionReward = 7
refCloneActivation = 8
refInheritance = 9
refPlayerDonation = 10
refCorporationPayment = 11
refDockingFee = 12
refOfficeRentalFee = 13
refFactorySlotRentalFee = 14
refRepairBill = 15
refBounty = 16
refBountyPrize = 17
refInsurance = 19
refMissionExpiration = 20
refMissionCompletion = 21
refShares = 22
refCourierMissionEscrow = 23
refMissionCost = 24
refAgentMiscellaneous = 25
refPaymentToLPStore = 26
refAgentLocationServices = 27
refAgentDonation = 28
refAgentSecurityServices = 29
refAgentMissionCollateralPaid = 30
refAgentMissionCollateralRefunded = 31
refAgentMissionReward = 33
refAgentMissionTimeBonusReward = 34
refCSPA = 35
refCSPAOfflineRefund = 36
refCorporationAccountWithdrawal = 37
refCorporationDividendPayment = 38
refCorporationRegistrationFee = 39
refCorporationLogoChangeCost = 40
refReleaseOfImpoundedProperty = 41
refMarketEscrow = 42
refMarketFinePaid = 44
refBrokerfee = 46
refAllianceRegistrationFee = 48
refWarFee = 49
refAllianceMaintainanceFee = 50
refContrabandFine = 51
refCloneTransfer = 52
refAccelerationGateFee = 53
refTransactionTax = 54
refJumpCloneInstallationFee = 55
refManufacturing = 56
refResearchingTechnology = 57
refResearchingTimeProductivity = 58
refResearchingMaterialProductivity = 59
refCopying = 60
refDuplicating = 61
refReverseEngineering = 62
refContractAuctionBid = 63
refContractAuctionBidRefund = 64
refContractCollateral = 65
refContractRewardRefund = 66
refContractAuctionSold = 67
refContractReward = 68
refContractCollateralRefund = 69
refContractCollateralPayout = 70
refContractPrice = 71
refContractBrokersFee = 72
refContractSalesTax = 73
refContractDeposit = 74
refContractDepositSalesTax = 75
refSecureEVETimeCodeExchange = 76
refContractAuctionBidCorp = 77
refContractCollateralCorp = 78
refContractPriceCorp = 79
refContractBrokersFeeCorp = 80
refContractDepositCorp = 81
refContractDepositRefund = 82
refContractRewardAdded = 83
refContractRewardAddedCorp = 84
refBountyPrizes = 85
refCorporationAdvertisementFee = 86
refMedalCreation = 87
refMedalIssuing = 88
refAttributeRespecification = 90
refSovereignityRegistrarFee = 91
refSovereignityUpkeepAdjustment = 95
refPlanetaryImportTax = 96
refPlanetaryExportTax = 97
refPlanetaryConstruction = 98
refRewardManager = 99
refBountySurcharge = 101
refContractReversal = 102
refStorePurchase = 106
refStoreRefund = 107
refPlexConversion = 108
refAurumGiveAway = 109
refAurumTokenConversion = 111
refDatacoreFee = 112
refWarSurrenderFee = 113
refWarAllyContract = 114
refBountyReimbursement = 115
refKillRightBuy = 116
refSecurityTagProcessingFee = 117
refIndustryTeamEscrow = 118
refIndustryTeamEscrowReimbursement = 119
refIndustryFacilityTax = 120
refMaxEve = 10000
refCorporationTaxNpcBounties = 92
refCorporationTaxAgentRewards = 93
refCorporationTaxAgentBonusRewards = 94
refCorporationTaxRewards = 103
derivedTransactionParentMapping = {refCorporationTaxNpcBounties: refBountyPrize,
 refCorporationTaxAgentRewards: refAgentMissionReward,
 refCorporationTaxAgentBonusRewards: refAgentMissionTimeBonusReward,
 refCorporationTaxRewards: refRewardManager}
recDescription = 'DESC'
recDescNpcBountyList = 'NBL'
recDescNpcBountyListTruncated = 'NBLT'
recStoreItems = 'STOREITEMS'
recDescOwners = 'OWNERIDS'
recDescOwnersTrunc = 'OWNERST'
minCorporationTaxAmount = 100000.0
stationServiceBountyMissions = 1
stationServiceAssassinationMissions = 2
stationServiceCourierMission = 4
stationServiceInterbus = 8
stationServiceReprocessingPlant = 16
stationServiceRefinery = 32
stationServiceMarket = 64
stationServiceBlackMarket = 128
stationServiceStockExchange = 256
stationServiceCloning = 512
stationServiceSurgery = 1024
stationServiceDNATherapy = 2048
stationServiceRepairFacilities = 4096
stationServiceFactory = 8192
stationServiceLaboratory = 16384
stationServiceGambling = 32768
stationServiceFitting = 65536
stationServiceNews = 262144
stationServiceStorage = 524288
stationServiceInsurance = 1048576
stationServiceDocking = 2097152
stationServiceOfficeRental = 4194304
stationServiceJumpCloneFacility = 8388608
stationServiceLoyaltyPointStore = 16777216
stationServiceNavyOffices = 33554432
stationServiceSecurityOffice = 67108864
stationServiceCombatSimulator = 134217728
stationServiceUnavailableMessages = {stationServiceCloning: 'StaServiceNoneOperationalCloning',
 stationServiceSurgery: 'StaServiceNoneOperationalCloning',
 stationServiceDNATherapy: 'StaServiceNoneOperationalCloning',
 stationServiceJumpCloneFacility: 'StaServiceNoneOperationalCloning',
 stationServiceFitting: 'StaServiceNoneOperationalFitting',
 stationServiceRepairFacilities: 'StaServiceNoneOperationalRepair',
 stationServiceReprocessingPlant: 'StaServiceNoneOperationalReprocessing'}
billTypeMarketFine = 1
billTypeRentalBill = 2
billTypeBrokerBill = 3
billTypeWarBill = 4
billTypeAllianceMaintainanceBill = 5
billTypeSovereignityMarker = 6
billUnpaid = 0
billPaid = 1
billCancelled = 2
billHidden = 3
chrattrIntelligence = 1
chrattrCharisma = 2
chrattrPerception = 3
chrattrMemory = 4
chrattrWillpower = 5
completedStatusAborted = 2
completedStatusUnanchored = 4
completedStatusDestroyed = 5
ramActivityCopying = 5
ramActivityDuplicating = 6
ramActivityInvention = 8
ramActivityManufacturing = 1
ramActivityNone = 0
ramActivityResearchingMaterialProductivity = 4
ramActivityResearchingTimeProductivity = 3
ramJobStatusPending = 1
ramJobStatusInProgress = 2
ramJobStatusReady = 3
ramJobStatusDelivered = 4
ramMaxCopyRuns = 20
ramMaxProductionTimeInDays = 30
ramRestrictNone = 0
ramRestrictBySecurity = 1
ramRestrictByStanding = 2
ramRestrictByCorp = 4
ramRestrictByAlliance = 8
activityCopying = 5
activityDuplicating = 6
activityInvention = 8
activityManufacturing = 1
activityNone = 0
activityResearchingMaterialProductivity = 4
activityResearchingTechnology = 2
activityResearchingTimeProductivity = 3
conAvailMyAlliance = 3
conAvailMyCorp = 2
conAvailMyself = 1
conAvailPublic = 0
conStatusOutstanding = 0
conStatusInProgress = 1
conStatusFinishedIssuer = 2
conStatusFinishedContractor = 3
conStatusFinished = 4
conStatusCancelled = 5
conStatusRejected = 6
conStatusFailed = 7
conStatusDeleted = 8
conStatusReversed = 9
conTypeNothing = 0
conTypeItemExchange = 1
conTypeAuction = 2
conTypeCourier = 3
conTypeLoan = 4
facwarLPPayoutAdjustment = 10000
facwarCorporationJoining = 0
facwarCorporationActive = 1
facwarCorporationLeaving = 2
facwarStandingPerVictoryPoint = 0.0015
facwarWarningStandingCharacter = 0
facwarWarningStandingCorporation = 1
facwarMinStandingsToJoin = -0.0001
facwarSolarSystemUpgradeThresholds = [40000,
 60000,
 90000,
 140000,
 200000]
facwarSolarSystemMaxLPPool = 300000
facwarLPGainBonus = [0.5,
 1.0,
 1.75,
 2.5,
 3.25]
facwarIHubInteractDist = 2500.0
facwarBaseVictoryPointsThreshold = 3000
facwarCaptureBleedLPs = 0.1
facwarDefensivePlexingLPMultiplier = 0.75
facwarMinLPDonation = 10
facwarMaxVictoryPointsOverThreshold = 100
facwarMaxLPUnknownGroup = 25000
facwarMaxLPPayout = {groupAssaultShip: 10000,
 groupAttackBattlecruiser: 15000,
 groupBattlecruiser: 15000,
 groupBattleship: 50000,
 groupBlackOps: 150000,
 groupBlockadeRunner: 150000,
 groupCapitalIndustrialShip: 150000,
 groupCapsule: 50000,
 groupCarrier: 150000,
 groupCombatReconShip: 50000,
 groupCommandShip: 50000,
 groupCovertOps: 10000,
 groupCruiser: 10000,
 groupDestroyer: 3000,
 groupDreadnought: 150000,
 groupElectronicAttackShips: 10000,
 groupExhumer: 50000,
 groupExpeditionFrigate: 10000,
 groupForceReconShip: 50000,
 groupFreighter: 150000,
 groupFrigate: 2000,
 groupHeavyAssaultShip: 50000,
 groupHeavyInterdictors: 50000,
 groupIndustrial: 50000,
 groupIndustrialCommandShip: 150000,
 groupInterceptor: 10000,
 groupInterdictor: 10000,
 groupJumpFreighter: 150000,
 groupLogistics: 50000,
 groupMarauders: 150000,
 groupMiningBarge: 10000,
 groupPrototypeExplorationShip: 10000,
 groupRookieship: 2000,
 groupShuttle: 2000,
 groupStealthBomber: 10000,
 groupStrategicCruiser: 100000,
 groupSupercarrier: 150000,
 groupTitan: 150000,
 groupTransportShip: 150000,
 groupTacticalDestroyer: 10000}
facwarMaxLPPayoutFactionOverwrites = {groupBattleship: 150000,
 groupCruiser: 50000,
 groupFrigate: 10000,
 groupIndustrial: 150000}
facwarStatTypeKill = 0
facwarStatTypeLoss = 1
battleSquadPlayers = 6
battleSquadSlots = 6
battleSquadVisibilityPublic = 'public'
battleSquadVisibilityPrivate = 'private'
battleSquadVisibilityCorporation = 'corporation'
battleSquadVisibilityAlliance = 'alliance'
battleSquadVisibility = [battleSquadVisibilityPublic,
 battleSquadVisibilityPrivate,
 battleSquadVisibilityCorporation,
 battleSquadVisibilityAlliance]
battleServerStatusCreated = 1
battleServerStatusRequested = 2
battleServerStatusStarting = 3
battleServerStatusRunning = 4
battleServerStatusStopping = 5
battleServerStatusStopped = 6
battleServerStatusFailed = 7
battleServerStatuses = {battleServerStatusCreated: 'created',
 battleServerStatusRequested: 'requested',
 battleServerStatusStarting: 'starting',
 battleServerStatusRunning: 'running',
 battleServerStatusStopping: 'stopping',
 battleServerStatusStopped: 'stopped',
 battleServerStatusFailed: 'failed'}
battleServerStatusNames = {v:k for k, v in battleServerStatuses.iteritems()}
battleStatusCreated = 1
battleStatusStarting = 2
battleStatusRunning = 3
battleStatusDelayed = 4
battleStatusCompleted = 0
battleStatuses = {battleStatusCreated: 'created',
 battleStatusStarting: 'starting',
 battleStatusRunning: 'running',
 battleStatusCompleted: 'completed',
 battleStatusDelayed: 'delayed'}
battleStatusNames = {v:k for k, v in battleStatuses.iteritems()}
battleTeamAttacker = 'A'
battleTeamDefender = 'D'
battleTeams = {battleTeamAttacker: 'attacker',
 battleTeamDefender: 'defender'}
battleMemberLeftPlayerLeft = 10
battleMemberLeftPlayerKicked = 11
battleMemberLeftPlayerDisconnect = 12
battleMemberLeftServerDefault = 20
battleMemberLeftServerComplete = 21
battleMemberLeftServerError = 22
battleMemberLeftServerTimeout = 23
battleMemberLeftServerKicked = 24
battleMemberLeftServerIdle = 25
battleMemberLeftServerFriendlyFire = 26
battleMemberLeftGMKick = 30
battleMemberLeftReasons = {battleMemberLeftPlayerLeft: 'player-left',
 battleMemberLeftPlayerKicked: 'player-kicked',
 battleMemberLeftPlayerDisconnect: 'player-disconnect',
 battleMemberLeftServerDefault: 'server-default',
 battleMemberLeftServerComplete: 'server-complete',
 battleMemberLeftServerError: 'server-error',
 battleMemberLeftServerTimeout: 'server-timeout',
 battleMemberLeftServerKicked: 'server-kicked',
 battleMemberLeftServerIdle: 'server-idle',
 battleMemberLeftServerFriendlyFire: 'server-friendlyfire',
 battleMemberLeftGMKick: 'gm-kick'}
battleMemberLeftReasonNames = {v:k for k, v in battleMemberLeftReasons.iteritems()}
battlePaymentNone = 1
battlePaymentConsumption = 2
battlePaymentBiomass = 3
battlePaymentStandings = 4
battlePaymentTypes = {battlePaymentNone: 'none',
 battlePaymentConsumption: 'consumption',
 battlePaymentBiomass: 'biomass',
 battlePaymentStandings: 'standings'}
battleSalvageNone = 1
battleSalvageFabricated = 2
battleSalvageDropped = 3
battleSalvageTypes = {battleSalvageNone: 'none',
 battleSalvageFabricated: 'fabricated',
 battleSalvageDropped: 'dropped'}
battleOrbitalStatusConnected = 1
battleOrbitalStatusDisonnected = 2
battleOrbitalStatuses = {battleOrbitalStatusConnected: 'connected',
 battleOrbitalStatusDisonnected: 'disconnected'}
battleOrbitalSupportStatusRequested = 1
battleOrbitalSupportStatusPending = 2
battleOrbitalSupportStatusApproved = 3
battleOrbitalSupportStatusCompleted = 4
battleOrbitalSupportStatuses = {battleOrbitalSupportStatusRequested: 'requested',
 battleOrbitalSupportStatusPending: 'pending',
 battleOrbitalSupportStatusApproved: 'approved',
 battleOrbitalSupportStatusCompleted: 'completed'}
districtStatusOffline = 0
districtStatusOnline = 1
districtStatusPending = 2
districtStatusLocked = 3
districtStatusStalled = 4
districtStatusStalledPending = 5
districtStatuses = {districtStatusOffline: 'offline',
 districtStatusOnline: 'online',
 districtStatusPending: 'pending',
 districtStatusLocked: 'locked',
 districtStatusStalled: 'stalled',
 districtStatusStalledPending: 'stalled-pending'}
districtStatusUpdate = {districtStatusPending: districtStatusLocked,
 districtStatusLocked: districtStatusOnline,
 districtStatusStalled: districtStatusOnline,
 districtStatusStalledPending: districtStatusLocked}
districtWarpinRange = 1.4
districtConflictActionCapture = 1
districtConflictActionAssault = 2
districtConflictActions = {districtConflictActionCapture: 'capture',
 districtConflictActionAssault: 'assault'}
districtConflictStatusResolved = 50
districtConflictStatusCompleted = 100
districtConflictStatusCreated = 1
districtConflictStatusStarted = 2
districtConflictStatusAttackedPending = 51
districtConflictStatusDefendedPending = 53
districtConflictStatusRevertedPending = 54
districtConflictStatusAttacked = 101
districtConflictStatusDefended = 103
districtConflictStatusReverted = 104
districtConflictStatuses = {districtConflictStatusCreated: 'created',
 districtConflictStatusStarted: 'started',
 districtConflictStatusAttackedPending: 'attacked-pending',
 districtConflictStatusDefendedPending: 'defended-pending',
 districtConflictStatusRevertedPending: 'reverted-pending',
 districtConflictStatusAttacked: 'attacked',
 districtConflictStatusDefended: 'defended',
 districtConflictStatusReverted: 'reverted'}
districtConflictStatusCompletion = {districtConflictStatusAttackedPending: districtConflictStatusAttacked,
 districtConflictStatusDefendedPending: districtConflictStatusDefended,
 districtConflictStatusRevertedPending: districtConflictStatusReverted}
districtContractTypeAttack = 1
districtContractTypeDefense = 2
districtContractTypes = {districtContractTypeAttack: 'attack',
 districtContractTypeDefense: 'defense'}
districtContractStatusOffered = 1
districtContractStatusCreated = 2
districtContractStatusAssigned = 3
districtContractStatusCompleted = 100
districtContractStatusSuccess = 101
districtContractStatusFailed = 102
districtContractStatusCancelled = 103
districtContractStatusReverted = 104
districtContractStatuses = (districtContractStatusOffered,
 districtContractStatusCreated,
 districtContractStatusAssigned,
 districtContractStatusSuccess,
 districtContractStatusFailed,
 districtContractStatusCancelled,
 districtContractStatusReverted)
districtInfrastructureCargoHub = 364205
districtInfrastructureProductionFacility = 364207
districtInfrastructureResearchLab = 364206
districtInfrastructure = (districtInfrastructureCargoHub, districtInfrastructureProductionFacility, districtInfrastructureResearchLab)
districtBonusManufacturingTime = 1
districtBonusPlanetaryInteraction = 2
districtBonusFuelUsage = 3
districtBonuses = {districtBonusManufacturingTime: (districtInfrastructureCargoHub, -0.1, 0.6),
 districtBonusPlanetaryInteraction: (districtInfrastructureProductionFacility, -0.025, 0.9),
 districtBonusFuelUsage: (districtInfrastructureResearchLab, -0.05, 0.8)}
districtInfrastructureComponents = {districtInfrastructureCargoHub: 356003,
 districtInfrastructureProductionFacility: 356078,
 districtInfrastructureResearchLab: 364084}
districtConflictLevels = (356100, 364085, 364154)
districtConflictModes = (365347, 365340, 365345)
militiaCorporationMinmatar = 1000182
militiaCorporationAmarr = 1000179
militiaCorporationCaldari = 1000180
militiaCorporationGallente = 1000181
battleMilitiaCorporationMinmatar = 1000263
battleMilitiaCorporationAmarr = 1000198
battleMilitiaCorporationCaldari = 1000261
battleMilitiaCorporationGallente = 1000262
battleMilitiaMappings = {militiaCorporationMinmatar: battleMilitiaCorporationMinmatar,
 militiaCorporationAmarr: battleMilitiaCorporationAmarr,
 militiaCorporationCaldari: battleMilitiaCorporationCaldari,
 militiaCorporationGallente: battleMilitiaCorporationGallente}
battleMilitiaMappingsReversed = {v:k for k, v in battleMilitiaMappings.items()}
battleMilitiaFactionsByCorporation = {battleMilitiaCorporationMinmatar: factionMinmatarRepublic,
 battleMilitiaCorporationAmarr: factionAmarrEmpire,
 battleMilitiaCorporationCaldari: factionCaldariState,
 battleMilitiaCorporationGallente: factionGallenteFederation}
battleMilitiaCorporationsByFaction = {v:k for k, v in battleMilitiaFactionsByCorporation.items()}
battleMilitiaCorporations = battleMilitiaCorporationsByFaction.values()
battleMilitiaFactions = battleMilitiaFactionsByCorporation.values()
battleMilitiaOpponents = {battleMilitiaCorporationMinmatar: battleMilitiaCorporationAmarr,
 battleMilitiaCorporationAmarr: battleMilitiaCorporationMinmatar,
 battleMilitiaCorporationCaldari: battleMilitiaCorporationGallente,
 battleMilitiaCorporationGallente: battleMilitiaCorporationCaldari}
battleMilitiaAllies = {battleMilitiaCorporationMinmatar: battleMilitiaCorporationGallente,
 battleMilitiaCorporationAmarr: battleMilitiaCorporationCaldari,
 battleMilitiaCorporationCaldari: battleMilitiaCorporationAmarr,
 battleMilitiaCorporationGallente: battleMilitiaCorporationMinmatar}
battleMilitiaBoosters = {battleMilitiaCorporationAmarr: FACTION_BOOSTER_AMARR,
 battleMilitiaCorporationCaldari: FACTION_BOOSTER_CALDARI,
 battleMilitiaCorporationGallente: FACTION_BOOSTER_GALLENTE,
 battleMilitiaCorporationMinmatar: FACTION_BOOSTER_MINMATAR}
orbitalStrikeAmmo = {typeTacticalEMPAmmoS: 356506,
 typeTacticalHybridAmmoS: 356508,
 typeTacticalLaserAmmoS: 356507}
battleQueueLocations = {40188512: [1000134, 1000205],
 40189225: [1000162, 1000207],
 40190566: [1000253, 1000228],
 40225549: [1000134, 1000229],
 40226285: [1000162, 1000084],
 40107847: [1000259, 1000091],
 40321416: [1000251, 1000089],
 40245947: [1000134, 1000206],
 40005528: [1000257, 1000074],
 40260663: [1000161, 1000087],
 40011654: [1000127, 1000037],
 40175320: [1000262, 1000261],
 40173897: [1000127, 1000043],
 40090823: [1000128, 1000197],
 40176889: [1000127, 1000015],
 40174909: [1000181, 1000180],
 40341608: [1000240, 1000238],
 40012849: [1000127, 1000043],
 40089274: [1000239, 1000026],
 40009244: [1000262, 1000233],
 40193119: [1000135, 1000099],
 40335701: [1000232, 1000181],
 40337263: [1000234, 1000247],
 40335591: [1000213, 1000262],
 40336371: [1000135, 1000056],
 40317959: [1000208, 1000102],
 40316346: [1000157, 1000100],
 40168027: [1000162, 1000098],
 40171389: [1000214, 1000109],
 40241240: [1000135, 1000122],
 40152534: [1000124, 1000163],
 40151769: [1000135, 1000054],
 40131025: [1000231, 1000182],
 40219544: [1000227, 1000256],
 40131120: [1000138, 1000057],
 40159764: [1000229, 1000054],
 40164208: [1000135, 1000108],
 40130917: [1000230, 1000259],
 40219307: [1000226, 1000255],
 40214314: [1000138, 1000220]}
battleQueueOptionSkirmish = 1
battleQueueOptionAmbush = 2
battleQueueOptionDomination = 3
battleQueueOptionAmarr = 4
battleQueueOptionMinmatar = 5
battleQueueOptionCaldari = 6
battleQueueOptionGallente = 7
battleQueueOptions = {battleQueueOptionSkirmish: {'name': '/EVE-Universe/Battles/modeSkrimishName',
                             'description': '/EVE-Universe/Battles/modeSkrimishDescription'},
 battleQueueOptionAmbush: {'name': '/EVE-Universe/Battles/modeAmbushName',
                           'description': '/EVE-Universe/Battles/modeAmbushDescription'},
 battleQueueOptionDomination: {'name': '/EVE-Universe/Battles/modeDominationName',
                               'description': '/EVE-Universe/Battles/modeDominationDescription'},
 battleQueueOptionAmarr: {'name': '/EVE-Universe/Battles/raceAmarrName',
                          'description': '/EVE-Universe/Battles/raceAmarrDescription',
                          'icon': 'Alliance/500003_32.png'},
 battleQueueOptionMinmatar: {'name': '/EVE-Universe/Battles/raceMinmatarName',
                             'description': '/EVE-Universe/Battles/raceMinmatarDescription',
                             'icon': 'Alliance/500002_32.png'},
 battleQueueOptionCaldari: {'name': '/EVE-Universe/Battles/raceCaldariName',
                            'description': '/EVE-Universe/Battles/raceCaldariDescription',
                            'icon': 'Alliance/500001_32.png'},
 battleQueueOptionGallente: {'name': '/EVE-Universe/Battles/raceGallenteName',
                             'description': '/EVE-Universe/Battles/raceGallenteDescription',
                             'icon': 'Alliance/500004_32.png'}}
battleRegionUS = 'us'
battleRegionEU = 'eu'
battleRegionAS = 'as'
battleRegionOC = 'oc'
battleRegionLabels = {battleRegionUS: '/EVE-Universe/Battles/Regions/US',
 battleRegionEU: '/EVE-Universe/Battles/Regions/EU',
 battleRegionAS: '/EVE-Universe/Battles/Regions/AS',
 battleRegionOC: '/EVE-Universe/Battles/Regions/OC'}
battleRegions = battleRegionLabels.keys()
battleQueueMiltiaOptions = {battleQueueOptionMinmatar: battleMilitiaCorporationMinmatar,
 battleQueueOptionAmarr: battleMilitiaCorporationAmarr,
 battleQueueOptionCaldari: battleMilitiaCorporationCaldari,
 battleQueueOptionGallente: battleMilitiaCorporationGallente}
battleQueueAcademy = 1
battleQueueMercenary = 2
battleQueueFaction = 3
battleQueues = {battleQueueAcademy: {'name': 'academy',
                      'locations': battleQueueLocations,
                      'modes': [{'modeID': 365739,
                                 'weight': 1.0}],
                      'options': []},
 battleQueueMercenary: {'name': 'mercenary',
                        'locations': battleQueueLocations,
                        'modes': [{'modeID': 365345,
                                   'weight': 3.0,
                                   'option': battleQueueOptionSkirmish},
                                  {'modeID': 365347,
                                   'weight': 1.0,
                                   'option': battleQueueOptionSkirmish},
                                  {'modeID': 365340,
                                   'weight': 5.0,
                                   'option': battleQueueOptionSkirmish},
                                  {'modeID': 353889,
                                   'weight': 1.0,
                                   'option': battleQueueOptionAmbush},
                                  {'modeID': 364136,
                                   'weight': 1.0,
                                   'option': battleQueueOptionAmbush},
                                  {'modeID': 365195,
                                   'weight': 1.0,
                                   'option': battleQueueOptionDomination}],
                        'options': [battleQueueOptionSkirmish, battleQueueOptionAmbush, battleQueueOptionDomination]},
 battleQueueFaction: {'name': 'faction',
                      'modes': [{'modeID': 365345,
                                 'weight': 3.0}, {'modeID': 365347,
                                 'weight': 1.0}, {'modeID': 365340,
                                 'weight': 5.0}],
                      'options': battleQueueMiltiaOptions.keys()}}
battleTheatreAcademy = 1
battleTheatreMercenary = 2
battleTheatreFaction = 3
battleTheatreCorporation = 4
battleTheatrePublic = 5
battleTheatres = [{'theatreID': battleTheatreAcademy,
  'key': 'academy',
  'name': '/EVE-Universe/Battles/academyTheaterName',
  'description': '/EVE-Universe/Battles/academyTheaterDescription',
  'help': '/EVE-Universe/Battles/academyTheaterHelp',
  'icon': 'theatre_academy.png',
  'queueID': battleQueueAcademy,
  'regions': [10000032,
              10000001,
              10000002,
              10000068,
              10000037,
              10000033,
              10000065,
              10000028,
              10000042,
              10000043,
              10000048,
              10000049,
              10000020,
              10000052,
              10000036,
              10000016,
              10000064,
              10000030]},
 {'theatreID': battleTheatreMercenary,
  'key': 'mercenary',
  'name': '/EVE-Universe/Battles/instantTheaterName',
  'description': '/EVE-Universe/Battles/instantTheaterDescription',
  'help': '/EVE-Universe/Battles/instantTheaterHelp',
  'icon': 'theatre_mercenary.png',
  'queueID': battleQueueMercenary,
  'regions': [10000032,
              10000001,
              10000002,
              10000068,
              10000037,
              10000033,
              10000065,
              10000028,
              10000042,
              10000043,
              10000048,
              10000049,
              10000020,
              10000052,
              10000036,
              10000016,
              10000064,
              10000030]},
 {'theatreID': battleTheatreFaction,
  'key': 'faction',
  'name': '/EVE-Universe/Battles/factionalTheaterName',
  'description': '/EVE-Universe/Battles/factionalTheaterDescription',
  'help': '/EVE-Universe/Battles/factionalTheaterHelp',
  'icon': 'theatre_faction.png',
  'queueID': battleQueueFaction,
  'regions': [10000064,
              10000033,
              10000036,
              10000069,
              10000038,
              10000042,
              10000048,
              10000068,
              10000030]},
 {'theatreID': battleTheatreCorporation,
  'key': 'corporation',
  'name': '/EVE-Universe/Battles/corporationTheaterName',
  'description': '/EVE-Universe/Battles/corporationTheaterDescription',
  'help': '/EVE-Universe/Battles/corporationTheaterHelp',
  'icon': 'theatre_corporation.png',
  'regions': [10000028]},
 {'theatreID': battleTheatrePublic,
  'key': 'public',
  'name': '/EVE-Universe/Battles/otherTheaterName',
  'description': '/EVE-Universe/Battles/otherTheaterDescription',
  'help': '/EVE-Universe/Battles/otherTheaterHelp',
  'icon': 'theatre_other.png',
  'regions': [10000064]}]
blockAmarrCaldari = 1
blockGallenteMinmatar = 2
blockSmugglingCartel = 3
blockTerrorist = 4
cargoContainerLifetime = 120
containerCharacter = 10011
containerCorpMarket = 10012
containerGlobal = 10002
containerHangar = 10004
containerOffices = 10009
containerRecycler = 10008
containerSolarSystem = 10003
containerStationCharacters = 10010
containerWallet = 10001
costCloneContract = 100000
costJumpClone = 100000
crpApplicationAppliedByCharacter = 0
crpApplicationRenegotiatedByCharacter = 1
crpApplicationAcceptedByCharacter = 2
crpApplicationRejectedByCharacter = 3
crpApplicationRejectedByCorporation = 4
crpApplicationRenegotiatedByCorporation = 5
crpApplicationAcceptedByCorporation = 6
crpApplicationWithdrawnByCharacter = 7
crpApplicationInvitedByCorporation = 8
crpApplicationMaxSize = 1000
crpApplicationEndStatuses = [crpApplicationRejectedByCorporation,
 crpApplicationWithdrawnByCharacter,
 crpApplicationAcceptedByCharacter,
 crpApplicationRejectedByCharacter]
crpApplicationOpenStatuses = [crpApplicationAppliedByCharacter, crpApplicationRenegotiatedByCharacter, crpApplicationRenegotiatedByCorporation]
crpApplicationActiveStatuses = [crpApplicationAcceptedByCorporation, crpApplicationAppliedByCharacter, crpApplicationInvitedByCorporation]
deftypeHouseWarmingGift = 34
deftypeCorpseMale = 25
deftypeCorpseFemale = 29148
directorConcordSecurityLevelMax = 1000
directorConcordSecurityLevelMin = 450
directorConvoySecurityLevelMin = 450
directorPirateGateSecurityLevelMax = 349
directorPirateGateSecurityLevelMin = -1000
directorPirateSecurityLevelMax = 849
directorPirateSecurityLevelMin = -1000
entityApproaching = 3
entityCombat = 1
entityDeparting = 4
entityDeparting2 = 5
entityEngage = 10
entityFleeing = 7
entityIdle = 0
entityMining = 2
entityOperating = 9
entityPursuit = 6
entitySalvaging = 18
graphicIDBrokenPod = 20391
graphicCorpLogoLibNoShape = 415
graphicCorpLogoLibShapes = {415: 'res:/UI/Texture/corpLogoLibs/415.png',
 416: 'res:/UI/Texture/corpLogoLibs/416.png',
 417: 'res:/UI/Texture/corpLogoLibs/417.png',
 418: 'res:/UI/Texture/corpLogoLibs/418.png',
 419: 'res:/UI/Texture/corpLogoLibs/419.png',
 420: 'res:/UI/Texture/corpLogoLibs/420.png',
 421: 'res:/UI/Texture/corpLogoLibs/421.png',
 422: 'res:/UI/Texture/corpLogoLibs/422.png',
 423: 'res:/UI/Texture/corpLogoLibs/423.png',
 424: 'res:/UI/Texture/corpLogoLibs/424.png',
 425: 'res:/UI/Texture/corpLogoLibs/425.png',
 426: 'res:/UI/Texture/corpLogoLibs/426.png',
 427: 'res:/UI/Texture/corpLogoLibs/427.png',
 428: 'res:/UI/Texture/corpLogoLibs/428.png',
 429: 'res:/UI/Texture/corpLogoLibs/429.png',
 430: 'res:/UI/Texture/corpLogoLibs/430.png',
 431: 'res:/UI/Texture/corpLogoLibs/431.png',
 432: 'res:/UI/Texture/corpLogoLibs/432.png',
 433: 'res:/UI/Texture/corpLogoLibs/433.png',
 434: 'res:/UI/Texture/corpLogoLibs/434.png',
 435: 'res:/UI/Texture/corpLogoLibs/435.png',
 436: 'res:/UI/Texture/corpLogoLibs/436.png',
 437: 'res:/UI/Texture/corpLogoLibs/437.png',
 438: 'res:/UI/Texture/corpLogoLibs/438.png',
 439: 'res:/UI/Texture/corpLogoLibs/439.png',
 440: 'res:/UI/Texture/corpLogoLibs/440.png',
 441: 'res:/UI/Texture/corpLogoLibs/441.png',
 442: 'res:/UI/Texture/corpLogoLibs/442.png',
 443: 'res:/UI/Texture/corpLogoLibs/443.png',
 444: 'res:/UI/Texture/corpLogoLibs/444.png',
 445: 'res:/UI/Texture/corpLogoLibs/445.png',
 446: 'res:/UI/Texture/corpLogoLibs/446.png',
 447: 'res:/UI/Texture/corpLogoLibs/447.png',
 448: 'res:/UI/Texture/corpLogoLibs/448.png',
 449: 'res:/UI/Texture/corpLogoLibs/449.png',
 450: 'res:/UI/Texture/corpLogoLibs/450.png',
 451: 'res:/UI/Texture/corpLogoLibs/451.png',
 452: 'res:/UI/Texture/corpLogoLibs/452.png',
 453: 'res:/UI/Texture/corpLogoLibs/453.png',
 454: 'res:/UI/Texture/corpLogoLibs/454.png',
 455: 'res:/UI/Texture/corpLogoLibs/455.png',
 456: 'res:/UI/Texture/corpLogoLibs/456.png',
 457: 'res:/UI/Texture/corpLogoLibs/457.png',
 458: 'res:/UI/Texture/corpLogoLibs/458.png',
 459: 'res:/UI/Texture/corpLogoLibs/459.png',
 460: 'res:/UI/Texture/corpLogoLibs/460.png',
 461: 'res:/UI/Texture/corpLogoLibs/461.png',
 462: 'res:/UI/Texture/corpLogoLibs/462.png',
 463: 'res:/UI/Texture/corpLogoLibs/463.png',
 464: 'res:/UI/Texture/corpLogoLibs/464.png',
 465: 'res:/UI/Texture/corpLogoLibs/465.png',
 466: 'res:/UI/Texture/corpLogoLibs/466.png',
 467: 'res:/UI/Texture/corpLogoLibs/467.png',
 468: 'res:/UI/Texture/corpLogoLibs/468.png',
 469: 'res:/UI/Texture/corpLogoLibs/469.png',
 470: 'res:/UI/Texture/corpLogoLibs/470.png',
 471: 'res:/UI/Texture/corpLogoLibs/471.png',
 472: 'res:/UI/Texture/corpLogoLibs/472.png',
 473: 'res:/UI/Texture/corpLogoLibs/473.png',
 474: 'res:/UI/Texture/corpLogoLibs/474.png',
 475: 'res:/UI/Texture/corpLogoLibs/475.png',
 476: 'res:/UI/Texture/corpLogoLibs/476.png',
 477: 'res:/UI/Texture/corpLogoLibs/477.png',
 478: 'res:/UI/Texture/corpLogoLibs/478.png',
 479: 'res:/UI/Texture/corpLogoLibs/479.png',
 480: 'res:/UI/Texture/corpLogoLibs/480.png',
 481: 'res:/UI/Texture/corpLogoLibs/481.png',
 482: 'res:/UI/Texture/corpLogoLibs/482.png',
 483: 'res:/UI/Texture/corpLogoLibs/483.png',
 484: 'res:/UI/Texture/corpLogoLibs/484.png',
 485: 'res:/UI/Texture/corpLogoLibs/485.png',
 486: 'res:/UI/Texture/corpLogoLibs/486.png',
 487: 'res:/UI/Texture/corpLogoLibs/487.png',
 488: 'res:/UI/Texture/corpLogoLibs/488.png',
 489: 'res:/UI/Texture/corpLogoLibs/489.png',
 490: 'res:/UI/Texture/corpLogoLibs/490.png',
 491: 'res:/UI/Texture/corpLogoLibs/491.png',
 492: 'res:/UI/Texture/corpLogoLibs/492.png',
 493: 'res:/UI/Texture/corpLogoLibs/493.png',
 494: 'res:/UI/Texture/corpLogoLibs/494.png',
 495: 'res:/UI/Texture/corpLogoLibs/495.png',
 496: 'res:/UI/Texture/corpLogoLibs/496.png',
 497: 'res:/UI/Texture/corpLogoLibs/497.png',
 498: 'res:/UI/Texture/corpLogoLibs/498.png',
 499: 'res:/UI/Texture/corpLogoLibs/499.png',
 500: 'res:/UI/Texture/corpLogoLibs/500.png',
 501: 'res:/UI/Texture/corpLogoLibs/501.png',
 502: 'res:/UI/Texture/corpLogoLibs/502.png',
 503: 'res:/UI/Texture/corpLogoLibs/503.png',
 504: 'res:/UI/Texture/corpLogoLibs/504.png',
 505: 'res:/UI/Texture/corpLogoLibs/505.png',
 506: 'res:/UI/Texture/corpLogoLibs/506.png',
 507: 'res:/UI/Texture/corpLogoLibs/507.png',
 508: 'res:/UI/Texture/corpLogoLibs/508.png',
 509: 'res:/UI/Texture/corpLogoLibs/509.png',
 510: 'res:/UI/Texture/corpLogoLibs/510.png',
 511: 'res:/UI/Texture/corpLogoLibs/511.png',
 512: 'res:/UI/Texture/corpLogoLibs/512.png',
 513: 'res:/UI/Texture/corpLogoLibs/513.png',
 514: 'res:/UI/Texture/corpLogoLibs/514.png',
 515: 'res:/UI/Texture/corpLogoLibs/515.png',
 516: 'res:/UI/Texture/corpLogoLibs/516.png',
 517: 'res:/UI/Texture/corpLogoLibs/517.png',
 518: 'res:/UI/Texture/corpLogoLibs/518.png',
 519: 'res:/UI/Texture/corpLogoLibs/519.png',
 520: 'res:/UI/Texture/corpLogoLibs/520.png',
 521: 'res:/UI/Texture/corpLogoLibs/521.png',
 522: 'res:/UI/Texture/corpLogoLibs/522.png',
 523: 'res:/UI/Texture/corpLogoLibs/523.png',
 524: 'res:/UI/Texture/corpLogoLibs/524.png',
 525: 'res:/UI/Texture/corpLogoLibs/525.png',
 526: 'res:/UI/Texture/corpLogoLibs/526.png',
 527: 'res:/UI/Texture/corpLogoLibs/527.png',
 528: 'res:/UI/Texture/corpLogoLibs/528.png',
 529: 'res:/UI/Texture/corpLogoLibs/529.png',
 530: 'res:/UI/Texture/corpLogoLibs/530.png',
 531: 'res:/UI/Texture/corpLogoLibs/531.png',
 532: 'res:/UI/Texture/corpLogoLibs/532.png',
 533: 'res:/UI/Texture/corpLogoLibs/533.png',
 534: 'res:/UI/Texture/corpLogoLibs/534.png',
 535: 'res:/UI/Texture/corpLogoLibs/535.png',
 536: 'res:/UI/Texture/corpLogoLibs/536.png',
 537: 'res:/UI/Texture/corpLogoLibs/537.png',
 538: 'res:/UI/Texture/corpLogoLibs/538.png',
 539: 'res:/UI/Texture/corpLogoLibs/539.png',
 540: 'res:/UI/Texture/corpLogoLibs/540.png',
 541: 'res:/UI/Texture/corpLogoLibs/541.png',
 542: 'res:/UI/Texture/corpLogoLibs/542.png',
 543: 'res:/UI/Texture/corpLogoLibs/543.png',
 544: 'res:/UI/Texture/corpLogoLibs/544.png',
 545: 'res:/UI/Texture/corpLogoLibs/545.png',
 546: 'res:/UI/Texture/corpLogoLibs/546.png',
 547: 'res:/UI/Texture/corpLogoLibs/547.png',
 548: 'res:/UI/Texture/corpLogoLibs/548.png',
 549: 'res:/UI/Texture/corpLogoLibs/549.png',
 550: 'res:/UI/Texture/corpLogoLibs/550.png',
 551: 'res:/UI/Texture/corpLogoLibs/551.png',
 552: 'res:/UI/Texture/corpLogoLibs/552.png',
 553: 'res:/UI/Texture/corpLogoLibs/553.png',
 554: 'res:/UI/Texture/corpLogoLibs/554.png',
 555: 'res:/UI/Texture/corpLogoLibs/555.png',
 556: 'res:/UI/Texture/corpLogoLibs/556.png',
 557: 'res:/UI/Texture/corpLogoLibs/557.png',
 558: 'res:/UI/Texture/corpLogoLibs/558.png',
 559: 'res:/UI/Texture/corpLogoLibs/559.png',
 560: 'res:/UI/Texture/corpLogoLibs/560.png',
 561: 'res:/UI/Texture/corpLogoLibs/561.png',
 562: 'res:/UI/Texture/corpLogoLibs/562.png',
 563: 'res:/UI/Texture/corpLogoLibs/563.png',
 564: 'res:/UI/Texture/corpLogoLibs/564.png',
 565: 'res:/UI/Texture/corpLogoLibs/565.png',
 566: 'res:/UI/Texture/corpLogoLibs/566.png',
 567: 'res:/UI/Texture/corpLogoLibs/567.png',
 568: 'res:/UI/Texture/corpLogoLibs/568.png',
 569: 'res:/UI/Texture/corpLogoLibs/569.png',
 570: 'res:/UI/Texture/corpLogoLibs/570.png',
 571: 'res:/UI/Texture/corpLogoLibs/571.png',
 572: 'res:/UI/Texture/corpLogoLibs/572.png',
 573: 'res:/UI/Texture/corpLogoLibs/573.png',
 574: 'res:/UI/Texture/corpLogoLibs/574.png',
 575: 'res:/UI/Texture/corpLogoLibs/575.png',
 576: 'res:/UI/Texture/corpLogoLibs/576.png',
 577: 'res:/UI/Texture/corpLogoLibs/577.png'}
dustCharacterPortraits = {FEMALE: {raceCaldari: 'res:/UI/Texture/DustPortraits/female_caldari.jpg',
          raceAmarr: 'res:/UI/Texture/DustPortraits/female_amarr.jpg',
          raceGallente: 'res:/UI/Texture/DustPortraits/female_gallente.jpg',
          raceMinmatar: 'res:/UI/Texture/DustPortraits/female_minmatar.jpg'},
 MALE: {raceCaldari: 'res:/UI/Texture/DustPortraits/male_caldari.jpg',
        raceAmarr: 'res:/UI/Texture/DustPortraits/male_amarr.jpg',
        raceGallente: 'res:/UI/Texture/DustPortraits/male_gallente.jpg',
        raceMinmatar: 'res:/UI/Texture/DustPortraits/male_minmatar.jpg'}}
dustCharacterPortraitsCDN = {FEMALE: {raceCaldari: {32: 'female_caldari_32.jpg',
                        64: 'female_caldari_64.jpg',
                        128: 'female_caldari_128.jpg',
                        256: 'female_caldari_256.jpg'},
          raceAmarr: {32: 'female_amarr_32.jpg',
                      64: 'female_amarr_64.jpg',
                      128: 'female_amarr_128.jpg',
                      256: 'female_amarr_256.jpg'},
          raceGallente: {32: 'female_gallente_32.jpg',
                         64: 'female_gallente_64.jpg',
                         128: 'female_gallente_128.jpg',
                         256: 'female_gallente_256.jpg'},
          raceMinmatar: {32: 'female_minmatar_32.jpg',
                         64: 'female_minmatar_64.jpg',
                         128: 'female_minmatar_128.jpg',
                         256: 'female_minmatar_256.jpg'}},
 MALE: {raceCaldari: {32: 'male_caldari_32.jpg',
                      64: 'male_caldari_64.jpg',
                      128: 'male_caldari_128.jpg',
                      256: 'male_caldari_256.jpg'},
        raceAmarr: {32: 'male_amarr_32.jpg',
                    64: 'male_amarr_64.jpg',
                    128: 'male_amarr_128.jpg',
                    256: 'male_amarr_256.jpg'},
        raceGallente: {32: 'male_gallente_32.jpg',
                       64: 'male_gallente_64.jpg',
                       128: 'male_gallente_128.jpg',
                       256: 'male_gallente_256.jpg'},
        raceMinmatar: {32: 'male_minmatar_32.jpg',
                       64: 'male_minmatar_64.jpg',
                       128: 'male_minmatar_128.jpg',
                       256: 'male_minmatar_256.jpg'}}}
CORPLOGO_BLEND = 1
CORPLOGO_SOLID = 2
CORPLOGO_GRADIENT = 3
graphicCorpLogoLibColors = {671: ((0.125, 0.125, 0.125, 1.0), CORPLOGO_SOLID),
 672: ((0.59, 0.5, 0.35, 1.0), CORPLOGO_GRADIENT),
 673: ((0.66, 0.83, 1.0, 1.0), CORPLOGO_BLEND),
 674: ((1.0, 1.0, 1.0, 1.0), CORPLOGO_BLEND),
 675: ((0.29, 0.29, 0.29, 1.0), CORPLOGO_GRADIENT),
 676: ((0.66, 1.04, 2.0, 1.0), CORPLOGO_BLEND),
 677: ((2.0, 1.4, 0.5, 1.0), CORPLOGO_BLEND),
 678: ((0.57, 0.6, 0.6, 1.0), CORPLOGO_BLEND),
 679: ((1.0, 0.47, 0.0, 1.0), CORPLOGO_BLEND),
 680: ((0.59, 0.0, 0.0, 1.0), CORPLOGO_BLEND),
 681: ((0.49, 0.5, 0.5, 1.0), CORPLOGO_GRADIENT),
 682: ((0.0, 0.0, 0.0, 0.5), CORPLOGO_SOLID),
 683: ((0.49, 0.5, 0.5, 0.41), CORPLOGO_SOLID),
 684: ((0.91, 0.91, 0.91, 1.0), CORPLOGO_SOLID),
 685: ((1.0, 0.7, 0.24, 1.0), CORPLOGO_SOLID)}
iconUnknown = 0
iconSkill = 33
iconModuleSensorDamper = 105
iconModuleECM = 109
iconModuleWarpScrambler = 111
iconModuleWarpScramblerMWD = 3433
iconModuleStasisWeb = 1284
iconDuration = 1392
iconModuleTrackingDisruptor = 1639
iconModuleTargetPainter = 2983
iconModuleDroneCommand = 2987
iconModuleNosferatu = 1029
iconModuleEnergyNeutralizer = 1283
iconWillpower = 3127
iconFemale = 3267
iconMale = 3268
invulnerabilityDocking = 3000
invulnerabilityJumping = 5000
invulnerabilityRestoring = 60000
invulnerabilityUndocking = 30000
invulnerabilityWarpingIn = 10000
invulnerabilityWarpingOut = 5000
jumpRadiusFactor = 130
jumpRadiusRandom = 15000
lifetimeOfDefaultContainer = 120
lifetimeOfDurableContainers = 43200
lockedContainerAccessTime = 180000
marketCommissionPercentage = 1
maxBoardingDistance = 6550
maxBuildDistance = 10000
maxCargoContainerTransferDistance = 2500
maxConfigureDistance = 5000
maxDockingDistance = 50000
maxDungeonPlacementDistance = 300
maxItemCountPerLocation = 1000
maxPetitionsPerDay = 2
maxSelfDestruct = 15000
maxStargateJumpingDistance = 2500
maxWormholeEnterDistance = 5000
maxWarpEndDistance = 100000
maxDroneAssist = 50
minAutoPilotWarpInDistance = 15000
minCloakingDistance = 2000
minDungeonPlacementDistance = 25
minJumpDriveDistance = 100000
minSpawnContainerDelay = 300000
minSpecialTutorialSpawnContainerDelay = 10000
minWarpDistance = 150000
minWarpEndDistance = 0
minCaptureBracketDistance = 200000
mktMinimumFee = 100
mktModificationDelay = 300
mktOrderCancelled = 3
mktOrderExpired = 2
mktTransactionTax = 1.5
npcCorpMax = 1999999
npcCorpMin = 1000000
npcDivisionAccounting = 1
npcDivisionAdministration = 2
npcDivisionAdvisory = 3
npcDivisionArchives = 4
npcDivisionAstrosurveying = 5
npcDivisionCommand = 6
npcDivisionDistribution = 7
npcDivisionFinancial = 8
npcDivisionIntelligence = 9
npcDivisionInternalSecurity = 10
npcDivisionLegal = 11
npcDivisionManufacturing = 12
npcDivisionMarketing = 13
npcDivisionMining = 14
npcDivisionPersonnel = 15
npcDivisionProduction = 16
npcDivisionPublicRelations = 17
npcDivisionRD = 18
npcDivisionSecurity = 19
npcDivisionStorage = 20
npcDivisionSurveillance = 21
onlineCapacitorChargeRatio = 95
onlineCapacitorRemainderRatio = 33
outlawSecurityStatus = -5
petitionMaxChatLogSize = 200000
petitionMaxCombatLogSize = 200000
posShieldStartLevel = 0.505
posMaxShieldPercentageForWatch = 0.95
posMinDamageDiffToPersist = 0.05
rangeConstellation = 4
rangeRegion = 32767
rangeSolarSystem = 0
rangeStation = -1
rentalPeriodOffice = 30
repairCostPercentage = 100
secLevelForBounty = -1
sentryTargetSwitchDelay = 40000
shipHidingCombatDelay = 120000
shipHidingDelay = 60000
shipHidingPvpCombatDelay = 900000
simulationTimeStep = 1000
skillEventCharCreation = 33
skillEventClonePenalty = 34
skillEventGMGive = 39
skillEventHaltedAccountLapsed = 260
skillEventTaskMaster = 35
skillEventTrainingCancelled = 38
skillEventTrainingComplete = 37
skillEventTrainingStarted = 36
skillEventQueueTrainingCompleted = 53
skillEventSkillInjected = 56
skillEventFreeSkillPointsUsed = 307
skillEventGMReverseFreeSkillPointsUsed = 309
solarsystemTimeout = 86400
sovereignityBillingPeriod = 14
sovereigntyDisruptorAnchorRange = 20000
sovereigntyDisruptorAnchorRangeMinBetween = 45000
starbaseSecurityLimit = 800
terminalExplosionDelay = 30
visibleSubSystems = 5
voteCEO = 0
voteGeneral = 4
voteItemLockdown = 5
voteItemUnlock = 6
voteKickMember = 3
voteShares = 2
voteWar = 1
warRelationshipAlliesAtWar = 5
warRelationshipAtWar = 3
warRelationshipAtWarCanFight = 4
warRelationshipUnknown = 0
warRelationshipYourAlliance = 2
warRelationshipYourCorp = 1
warpJitterRadius = 2500
warpSpeedToAUPerSecond = 0.001
solarSystemPolaris = 30000380
maxLoyaltyStoreBulkOffers = 100
approachRange = 50
leaderboardShipTypeAll = 0
leaderboardShipTypeTopFrigate = 1
leaderboardShipTypeTopDestroyer = 2
leaderboardShipTypeTopCruiser = 3
leaderboardShipTypeTopBattlecruiser = 4
leaderboardShipTypeTopBattleship = 5
leaderboardPeopleBuddies = 1
leaderboardPeopleCorpMembers = 2
leaderboardPeopleAllianceMembers = 3
leaderboardPeoplePlayersInSim = 4
securityClassZeroSec = 0
securityClassLowSec = 1
securityClassHighSec = 2
contestionStateNone = 0
contestionStateContested = 1
contestionStateVulnerable = 2
contestionStateCaptured = 3
aggressionTime = 15
certificateGradeBasic = 1
certificateGradeStandard = 2
certificateGradeImproved = 3
certificateGradeAdvanced = 4
certificateGradeElite = 5
medalMinNameLength = 3
medalMaxNameLength = 100
medalMaxDescriptionLength = 1000
medalMinDescriptionLength = 10
respecTimeInterval = 365 * DAY
respecMinimumAttributeValue = 17
respecMaximumAttributeValue = 27
respecTotalRespecPoints = 99
remoteHomeStationChangeInterval = 365 * DAY
shipNotWarping = 0
shipWarping = 1
shipAligning = 2
warpTypeNone = 0
warpTypeRegular = 1
warpTypeForced = 2
planetResourceScanDistance = 1000000000
planetResourceProximityDistant = 0
planetResourceProximityRegion = 1
planetResourceProximityConstellation = 2
planetResourceProximitySystem = 3
planetResourceProximityPlanet = 4
planetResourceProximityLimits = [(2, 6),
 (4, 10),
 (6, 15),
 (10, 20),
 (15, 30)]
planetResourceScanningRanges = [9.0,
 7.0,
 5.0,
 3.0,
 1.0]
planetResourceUpdateTime = 1 * HOUR
planetResourceMaxValue = 1.21
mapWormholeRegionMin = 11000000
mapWormholeRegionMax = 11999999
mapWormholeConstellationMin = 21000000
mapWormholeConstellationMax = 21999999
mapWormholeSystemMin = 31000000
mapWormholeSystemMax = 31999999
mapWorldSpaceMin = 81000000
mapWorldSpaceMax = 81999999
skillsWithHintPerMinute = 50
INVALID_WORMHOLE_CLASS_ID = 0
HIGH_SEC_WORMHOLE_CLASS_ID = 7
LOW_SEC_WORMHOLE_CLASS_ID = 8
ZERO_SEC_WORMHOLE_CLASS_ID = 9
WH_SLIM_MAX_SHIP_MASS_SMALL = 1
WH_SLIM_MAX_SHIP_MASS_MEDIUM = 2
WH_SLIM_MAX_SHIP_MASS_LARGE = 3
WH_SLIM_MAX_SHIP_MASS_VERYLARGE = 4
shipColor = {'MAIN': {raceAmarr: {0: (0.5, 0.5, 0.5, 1.0)},
          raceCaldari: {0: (0.36, 0.37, 0.37, 1.0),
                        1: (0.23, 0.24, 0.22, 1.0),
                        2: (0.33, 0.32, 0.3, 1.0),
                        3: (0.21, 0.25, 0.26, 1.0),
                        4: (0.21, 0.21, 0.21, 1.0)},
          raceGallente: {0: (0.5, 0.5, 0.5, 1.0)},
          raceMinmatar: {0: (0.5, 0.5, 0.5, 1.0)}},
 'MARKINGS': {raceAmarr: {0: (0.5, 0.5, 0.5, 1.0)},
              raceCaldari: {0: (0.63, 0.63, 0.63, 1.0),
                            1: (0.2, 0.09, 0.05, 1.0),
                            2: (0.1, 0.18, 0.23, 1.0),
                            3: (0.08, 0.08, 0.08, 1.0),
                            4: (0.2, 0.18, 0.12, 1.0)},
              raceGallente: {0: (0.5, 0.5, 0.5, 1.0)},
              raceMinmatar: {0: (0.5, 0.5, 0.5, 1.0)}},
 'LIGHTS': {raceAmarr: {0: (0.5, 0.5, 0.5, 1.0)},
            raceCaldari: {0: (0.56, 0.76, 0.92, 1.0),
                          1: (0.57, 0.57, 0.5, 1.0),
                          2: (0.76, 0.74, 0.51, 1.0),
                          3: (0.7, 0.85, 0.52, 1.0),
                          4: (0.99, 0.65, 0.43, 1.0)},
            raceGallente: {0: (0.5, 0.5, 0.5, 1.0)},
            raceMinmatar: {0: (0.5, 0.5, 0.5, 1.0)}}}
agentMissionOffered = 'offered'
agentMissionOfferAccepted = 'offer_accepted'
agentMissionOfferDeclined = 'offer_declined'
agentMissionOfferExpired = 'offer_expired'
agentMissionOfferRemoved = 'offer_removed'
agentMissionAccepted = 'accepted'
agentMissionDeclined = 'declined'
agentMissionCompleted = 'completed'
agentTalkToMissionCompleted = 'talk_to_completed'
agentMissionQuit = 'quit'
agentMissionFailed = 'failed'
agentMissionResearchUpdatePPD = 'research_update_ppd'
agentMissionResearchStarted = 'research_started'
agentMissionProlonged = 'prolong'
agentMissionReset = 'reset'
agentMissionModified = 'modified'
agentMissionFailed = 'failed'
agentMissionStateAllocated = 0
agentMissionStateOffered = 1
agentMissionStateAccepted = 2
agentMissionStateFailed = 3
agentMissionDungeonStarted = 0
agentMissionDungeonCompleted = 1
agentMissionDungeonFailed = 2
rookieAgentList = [3018681,
 3018821,
 3018822,
 3018823,
 3018824,
 3018680,
 3018817,
 3018818,
 3018819,
 3018820,
 3018682,
 3018809,
 3018810,
 3018811,
 3018812,
 3018678,
 3018837,
 3018838,
 3018839,
 3018840,
 3018679,
 3018841,
 3018842,
 3018843,
 3018844,
 3018677,
 3018845,
 3018846,
 3018847,
 3018848,
 3018676,
 3018825,
 3018826,
 3018827,
 3018828,
 3018675,
 3018805,
 3018806,
 3018807,
 3018808,
 3018672,
 3018801,
 3018802,
 3018803,
 3018804,
 3018684,
 3018829,
 3018830,
 3018831,
 3018832,
 3018685,
 3018813,
 3018814,
 3018815,
 3018816,
 3018683,
 3018833,
 3018834,
 3018835,
 3018836]
epicArcNPEArcs = [64,
 67,
 68,
 69,
 70,
 71,
 72,
 73,
 74,
 75,
 76,
 77]
petitionPropertyAgentMissionReq = 2
petitionPropertyAgentMissionNoReq = 3
petitionPropertyAgents = 4
petitionPropertyShipID = 5
petitionPropertyStarbaseLocation = 6
petitionPropertyCharacter = 7
petitionPropertyUserCharacters = 8
petitionPropertyWebAddress = 9
petitionPropertyCorporations = 10
petitionPropertyChrAgent = 11
petitionPropertyOS = 12
petitionPropertyChrEpicArc = 13
tutorialPagesActionOpenCareerFunnel = 1
actionTypes = {1: 'Play_MLS_Audio',
 2: 'Neocom_Button_Blink',
 3: 'Open_MLS_Message',
 4: 'Poll_Criteria_Open_Tutorial',
 5: 'SpaceObject_UI_Pointer'}
neocomButtonScopeEverywhere = 1
neocomButtonScopeInflight = 2
neocomButtonScopeStation = 3
neocomButtonScopeStationOrWorldspace = 4
marketCategoryBluePrints = 2
marketCategoryShips = 4
marketCategoryShipEquipment = 9
marketCategoryAmmunitionAndCharges = 11
marketCategoryTradeGoods = 19
marketCategoryImplantesAndBoosters = 24
marketCategorySkills = 150
marketCategoryDrones = 157
marketCategoryManufactureAndResearch = 475
marketCategoryStarBaseStructures = 477
marketCategoryShipModifications = 955
maxCharFittings = 200
maxCorpFittings = 300
maxLengthFittingName = 50
maxLengthFittingDescription = 500
dungeonCompletionDestroyLCS = 0
dungeonCompletionDestroyGuards = 1
dungeonCompletionDestroyLCSandGuards = 2
defaultPadding = 4
sovereigntyClaimStructuresGroups = (groupSovereigntyClaimMarkers, groupSovereigntyDisruptionStructures)
sovereigntyStructuresGroups = (groupSovereigntyClaimMarkers,
 groupSovereigntyDisruptionStructures,
 groupSovereigntyStructures,
 groupInfrastructureHub)
mailingListBlocked = 0
mailingListAllowed = 1
mailingListMemberMuted = 0
mailingListMemberDefault = 1
mailingListMemberOperator = 2
mailingListMemberOwner = 3
ALLIANCE_SERVICE_MOD = 200
CHARNODE_MOD = 64
PLANETARYMGR_MOD = 128
BATTLEINSTANCEMANANGER_MOD = 128
BATTLEQUICKMATCHER_MOD = 64
mailTypeMail = 1
mailTypeNotifications = 2
mailStatusMaskRead = 1
mailStatusMaskReplied = 2
mailStatusMaskForwarded = 4
mailStatusMaskTrashed = 8
mailStatusMaskDraft = 16
mailStatusMaskAutomated = 32
mailLabelInbox = 1
mailLabelSent = 2
mailLabelCorporation = 4
mailLabelAlliance = 8
mailLabelsSystem = mailLabelInbox + mailLabelSent + mailLabelCorporation + mailLabelAlliance
mailMaxRecipients = 50
mailMaxGroups = 1
mailMaxSubjectSize = 150
mailMaxBodySize = 8000
mailMaxTaggedBodySize = 10000
mailMaxLabelSize = 40
mailMaxNumLabels = 25
mailMaxPerPage = 100
mailTrialAccountTimer = 1
mailMaxMessagePerMinute = 5
mailinglistMaxMembers = 3000
mailinglistMaxMembersUpdated = 1000
mailingListMaxNameSize = 60
notificationsMaxUpdated = 100
calendarMonday = 0
calendarTuesday = 1
calendarWednesday = 2
calendarThursday = 3
calendarFriday = 4
calendarSaturday = 5
calendarSunday = 6
calendarJanuary = 1
calendarFebruary = 2
calendarMarch = 3
calendarApril = 4
calendarMay = 5
calendarJune = 6
calendarJuly = 7
calendarAugust = 8
calendarSeptember = 9
calendarOctober = 10
calendarNovember = 11
calendarDecember = 12
calendarNumDaysInWeek = 7
calendarTagPersonal = 1
calendarTagCorp = 2
calendarTagAlliance = 4
calendarTagCCP = 8
calendarTagAutomated = 16
calendarViewRangeInMonths = 12
calendarMaxTitleSize = 40
calendarMaxDescrSize = 500
calendarMaxInvitees = 50
calendarMaxInviteeDisplayed = 100
calendarAutoEventPosFuel = 1
eventResponseUninvited = 0
eventResponseDeleted = 1
eventResponseDeclined = 2
eventResponseUndecided = 3
eventResponseAccepted = 4
eventResponseMaybe = 5
calendarStartYear = 2003
soundNotifications = {'shield': {'defaultThreshold': 0.25,
            'soundEventName': 'ui_notify_negative_05_play',
            'thresholdSettingsName': 'shieldThreshold',
            'localizationLabel': 'UI/Inflight/NotifySettingsWindow/ShieldAlertLevel',
            'defaultStatus': 1},
 'armour': {'defaultThreshold': 0.4,
            'soundEventName': 'ui_notify_negative_03_play',
            'localizationLabel': 'UI/Inflight/NotifySettingsWindow/ArmorAlertLevel',
            'defaultStatus': 1},
 'hull': {'defaultThreshold': 0.95,
          'soundEventName': 'ui_notify_negative_01_play',
          'localizationLabel': 'UI/Inflight/NotifySettingsWindow/HullAlertLevel',
          'defaultStatus': 1},
 'capacitor': {'defaultThreshold': 0.3,
               'soundEventName': 'ui_notify_negative_04_play',
               'localizationLabel': 'UI/Inflight/NotifySettingsWindow/CapacitorAlertLevel',
               'defaultStatus': 1},
 'cargoHold': {'defaultThreshold': 0.2,
               'soundEventName': 'ui_notify_positive_08_play',
               'localizationLabel': 'UI/Inflight/NotifySettingsWindow/CargoHoldAlertLevel',
               'defaultStatus': 0},
 'NameToIndices': {'shield': 0,
                   'armour': 1,
                   'hull': 2,
                   'capacitor': 3,
                   'cargoHold': 4}}
costReceiverTypeOwner = 0
costReceiverTypeMailingList = 1
costContactMax = 1000000
contactHighStanding = 10
contactGoodStanding = 5
contactNeutralStanding = 0
contactBadStanding = -5
contactHorribleStanding = -10
contactAll = 100
contactBlocked = 200
contactWatchlist = 300
contactNotifications = 400
developmentIndices = [attributeDevIndexMilitary,
 attributeDevIndexIndustrial,
 attributeDevIndexSovereignty,
 attributeDevIndexUpgrade]
sovAudioEventStopOnline = 0
sovAudioEventStopDestroyed = 1
sovAudioEventFlagVulnerable = 2
sovAudioEventFlagDestroyed = 3
sovAudioEventFlagClaimed = 4
sovAudioEventOutpostReinforced = 5
sovAudioEventOutpostCaptured = 6
sovAudioEventHubReinforced = 7
sovAudioEventHubDestroyed = 8
sovAudioEventOutpostAttacked = 9
sovAudioEventFiles = {sovAudioEventStopOnline: ('msg_stop_online_play', 'SovAudioMsg_StopOnline'),
 sovAudioEventStopDestroyed: ('msg_stop_destroyed_play', 'SovAudioMsg_StopDestroyed'),
 sovAudioEventFlagVulnerable: ('msg_flag_vulnerable_play', 'SovAudioMsg_FlagVulnerable'),
 sovAudioEventFlagDestroyed: ('msg_flag_destroyed_play', 'SovAudioMsg_FlagDestroyed'),
 sovAudioEventFlagClaimed: ('msg_flag_claimed_play', 'SovAudioMsg_FlagClaimed'),
 sovAudioEventOutpostReinforced: ('msg_outpost_reinforced_play', 'SovAudioMsg_OutpostReinforced'),
 sovAudioEventOutpostCaptured: ('msg_outpost_captureed_play', 'SovAudioMsg_OutpostCaptured'),
 sovAudioEventOutpostAttacked: ('msg_outpost_attacked_play', 'SovAudioMsg_OutpostUnderAttack'),
 sovAudioEventHubReinforced: ('msg_hub_reinforced_play', 'SovAudioMsg_HubReinforced'),
 sovAudioEventHubDestroyed: ('msg_hub_destroyed_play', 'SovAudioMsg_HubDestroyed')}
maxLong = 9223372036854775807L
maxContacts = 1024
maxAllianceContacts = 2600
maxContactsPerPage = 50
contactMaxLabelSize = 40
pwnStructureStateAnchored = 'anchored'
pwnStructureStateAnchoring = 'anchoring'
pwnStructureStateOnline = 'online'
pwnStructureStateOnlining = 'onlining'
pwnStructureStateUnanchored = 'unanchored'
pwnStructureStateUnanchoring = 'unanchoring'
pwnStructureStateVulnerable = 'vulnerable'
pwnStructureStateInvulnerable = 'invulnerable'
pwnStructureStateReinforced = 'reinforced'
pwnStructureStateOperating = 'operating'
pwnStructureStateIncapacitated = 'incapacitated'
pwnStructureStateAnchor = 'anchor'
pwnStructureStateUnanchor = 'unanchor'
pwnStructureStateOffline = 'offline'
pwnStructureStateOnlineActive = 'online - active'
pwnStructureStateOnlineStartingUp = 'online - starting up'
piLaunchOrbitDecayTime = DAY * 5
piCargoInOrbit = 0
piCargoDeployed = 1
piCargoClaimed = 2
piCargoDeleted = 3
piSECURITY_BANDS_LABELS = [(0, '[-1;-0.75]'),
 (1, ']-0.75;-0.45]'),
 (2, ']-0.45;-0.25]'),
 (3, ']-0.25;0.0['),
 (4, '[0.0;0.15['),
 (5, '[0.15;0.25['),
 (6, '[0.25;0.35['),
 (7, '[0.35;0.45['),
 (8, '[0.45;0.55['),
 (9, '[0.55;0.65['),
 (10, '[0.65;0.75['),
 (11, '[0.75;1.0]')]
singleCharsAllowedForShortcut = ['OEM_1',
 'OEM_102',
 'OEM_2',
 'OEM_3',
 'OEM_4',
 'OEM_5',
 'OEM_6',
 'OEM_7',
 'OEM_8',
 'OEM_CLEAR',
 'OEM_COMMA',
 'OEM_MINUS',
 'OEM_PERIOD',
 'OEM_PLUS',
 'F1',
 'F10',
 'F11',
 'F12',
 'F13',
 'F14',
 'F15',
 'F16',
 'F17',
 'F18',
 'F19',
 'F2',
 'F20',
 'F21',
 'F22',
 'F23',
 'F24',
 'F3',
 'F4',
 'F5',
 'F6',
 'F7',
 'F8',
 'F9']
repackableInStationCategories = (categoryStructure,
 categoryShip,
 categoryDrone,
 categoryModule,
 categorySubSystem,
 categorySovereigntyStructure,
 categoryDeployable)
repackableInStationGroups = (groupCargoContainer,
 groupSecureCargoContainer,
 groupAuditLogSecureContainer,
 groupFreightContainer,
 groupTool,
 groupMobileWarpDisruptor)
repackableInStructureCategories = (categoryDrone, categoryModule)
vcPrefixAlliance = 'allianceid'
vcPrefixFleet = 'fleetid'
vcPrefixCorp = 'corpid'
vcPrefixSquad = 'squadid'
vcPrefixWing = 'wingid'
vcPrefixInst = 'inst'
vcPrefixTeam = 'team'
incursionStateWithdrawing = 0
incursionStateMobilizing = 1
incursionStateEstablished = 2
rewardIneligibleReasonTrialAccount = 1
rewardIneligibleReasonInvalidGroup = 2
rewardIneligibleReasonShipCloaked = 3
rewardIneligibleReasonNotInFleet = 4
rewardIneligibleReasonNotBestFleet = 5
rewardIneligibleReasonNotTop5 = 6
rewardIneligibleReasonNotRightAmoutOfPlayers = 7
rewardIneligibleReasonTaleAlreadyEnded = 8
rewardIneligibleReasonNotInRange = 9
rewardIneligibleReasonNoISKLost = 10
rewardTypeLP = 1
rewardTypeISK = 2
rewardCriteriaAllSecurityBands = 0
rewardCriteriaHighSecurity = 1
rewardCriteriaLowSecurity = 2
rewardCriteriaNullSecurity = 3
rewardInvalidGroups = {groupCapsule,
 groupShuttle,
 groupRookieship,
 groupPrototypeExplorationShip}
rewardInvalidGroupsLimitedRestrictions = {groupCapsule, groupShuttle, groupPrototypeExplorationShip}
creditsISK = 0
creditsAURUM = 1
creditsDustMPLEX = 2
Plex2AurExchangeRatio = 3500
chinaPlex2AurExchangeRatio = 600
AurumToken2AurExchangeRatio = 1000
blacklistedTaleLocations = 1
defaultCustomsOfficeTaxRate = 0.05
configValues = {'MaxPush': 2.5,
 'VisibilityRangeAdd': 60.0,
 'VisibilityRangeRemove': 65.0}
dbMaxCountForIntList = 750
dbMaxCountForBigintList = 350
dbMaxQuantity = 2147483647
singletonBlueprintOriginal = 1
singletonBlueprintCopy = 2
metaGroupUnused = 0
metaGroupStoryline = 3
metaGroupFaction = 4
metaGroupOfficer = 5
metaGroupDeadspace = 6
metaGroupsUsed = [metaGroupStoryline,
 metaGroupFaction,
 metaGroupOfficer,
 metaGroupDeadspace]
NCC_MAX_NORMAL_BACKGROUND_ID = 1000
GENDER_AS_ROOT_FOLDER = True
if GENDER_AS_ROOT_FOLDER:
    DEFAULT_FEMALE_PAPERDOLL_MODEL = 'res:/Graphics/Character/Female/Skeleton/masterSkeletonFemale.gr2'
    DEFAULT_MALE_PAPERDOLL_MODEL = 'res:/Graphics/Character/Male/Skeleton/masterSkeletonMale.gr2'
else:
    DEFAULT_FEMALE_PAPERDOLL_MODEL = 'res:/Graphics/Character/Skeletons/masterSkeletonFemale.gr2'
    DEFAULT_MALE_PAPERDOLL_MODEL = 'res:/Graphics/Character/Skeletons/masterSkeletonMale.gr2'
PAPERDOLL_LODS_IN_SEPARATE_FOLDER = True
PAPERDOLL_LOD_RED_FILES = True
FEMALE_MORPHEME_PATH = 'res:/morpheme/IncarnaPlayerNetwork/Female/IncarnaPlayerNetwork.mor'
MALE_MORPHEME_PATH = 'res:/morpheme/IncarnaPlayerNetwork/Male/IncarnaPlayerNetwork.mor'
MORPHEMEPATH = FEMALE_MORPHEME_PATH
AVATAR_MOVEMENT_SPEED_MAX = 1.9
AVATAR_STEP_HEIGHT = 0.2
BASE_INVENTORY_TYPES_TABLE = 'inventory.types'
CYNOJAM_JAMSHIPS = 1
CYNOJAM_JAMSHIPS_AND_JUMPBRIDGE = 2
INPUT_TYPE_LEFTCLICK = 1
INPUT_TYPE_RIGHTCLICK = 2
INPUT_TYPE_MIDDLECLICK = 3
INPUT_TYPE_EX1CLICK = 4
INPUT_TYPE_EX2CLICK = 5
INPUT_TYPE_DOUBLECLICK = 6
INPUT_TYPE_MOUSEMOVE = 7
INPUT_TYPE_MOUSEWHEEL = 8
INPUT_TYPE_MOUSEDOWN = 9
INPUT_TYPE_MOUSEUP = 10
MOVDIR_FORWARD = 0
MOVDIR_BACKWARD = 1
MOVDIR_LEFT = 2
MOVDIR_RIGHT = 3
INCARNA_CAMERA_FULL_CHASE = 10
INCARNA_CAMERA_CHASE_WHEN_MOVING = 11
INCARNA_CAMERA_NO_CHASE = 12
INCARNA_FLAT = 0
INCARNA_SLOPE_DOWN = 1
INCARNA_SLOPE_UP = 2
INCARNA_STEPS_DOWN = 3
INCARNA_STEPS_UP = 4
BAD_ASSET_PATH = 'res:/Graphics/Placeable/EditorOnly/BadAsset/'
BAD_ASSET_FILE = 'BadAsset.red'
BAD_ASSET_PATH_AND_FILE = BAD_ASSET_PATH + BAD_ASSET_FILE
BAD_ASSET_STATIC = 'res:/Tools/BadAsset/BadInteriorAsset.red'
BAD_ASSET_COLLISION = 'res:/Graphics/Placeable/EditorOnly/BadAsset/BadAsset.nxb'
completionTypeRookieArcCompletion = 1
ZACTION_DEFAULT_ACTION = 12
ZACTION_DEFAULT_ACTION = 12
CHAT_SYSTEM_CHANNEL = -1
WAR_NEGOTIATION_TYPE_ALLY_OFFER = 0
WAR_NEGOTIATION_TYPE_SURRENDER_OFFER = 2
warNegotiationNew = 0
warNegotiationAccepted = 1
warNegotiationDeclined = 2
GROUP_CAPSULES = 0
GROUP_FRIGATES = 1
GROUP_DESTROYERS = 2
GROUP_CRUISERS = 3
GROUP_BATTLESHIPS = 4
GROUP_BATTLECRUISERS = 5
GROUP_CAPITALSHIPS = 6
GROUP_INDUSTRIALS = 7
GROUP_POS = 8
OVERVIEW_NORMAL_COLOR = (1.0, 1.0, 1.0)
OVERVIEW_HOSTILE_COLOR = (1.0, 0.1, 0.1)
OVERVIEW_AUTO_PILOT_DESTINATION_COLOR = (1.0, 1.0, 0.0)
OVERVIEW_FORBIDDEN_CONTAINER_COLOR = (1.0, 1.0, 0.0)
OVERVIEW_ABANDONED_CONTAINER_COLOR = (0.2, 0.5, 1.0)
OVERVIEW_IGNORE_GROUPS = ()
MAX_FOLDERNAME_LENGTH = 40
maxCorpBookmarkCount = 500
maxCharBookmarkCount = 13000
BOOKMARKACTIONTHROTTLEKEY = 'BookmarkActionThrottleKey'
bookmarkThrottleMaxTimes = 20
bookmarkThrottleDuration = MIN
maxBookmarkCopies = 10
EXPLORATION_SITE_TYPES = {attributeScanGravimetricStrength: 'UI/Inflight/Scanner/OreSite',
 attributeScanLadarStrength: 'UI/Inflight/Scanner/GasSite',
 attributeScanMagnetometricStrength: 'UI/Inflight/Scanner/RelicSite',
 attributeScanRadarStrength: 'UI/Inflight/Scanner/DataSite',
 attributeScanWormholeStrength: 'UI/Inflight/Scanner/Wormhole',
 attributeScanAllStrength: 'UI/Inflight/Scanner/CombatSite'}
MAX_DRONE_RECONNECTS = 25
PLAYER_STATUS_ACTIVE = 0
PLAYER_STATUS_AFK = 1
searchByPartialTerms = 0
searchByExactTerms = 1
searchByExactPhrase = 2
searchByOnlyExactPhrase = 3
searchResultAgent = 1
searchResultCharacter = 2
searchResultCorporation = 3
searchResultAlliance = 4
searchResultFaction = 5
searchResultConstellation = 6
searchResultSolarSystem = 7
searchResultRegion = 8
searchResultStation = 9
searchResultInventoryType = 10
searchResultWormHoles = 11
searchResultAllOwners = [1,
 2,
 3,
 4,
 5]
searchResultAllLocations = [6,
 7,
 8,
 9]
searchMaxResults = 500
searchMinWildcardLength = 3
tianCityBannerUrl = 'http://eve.tiancity.com/homepage/endbanner/endbanner.html'
DEFAULT_SIGNATURE_RADIUS = 1000.0
warningISKBuying = 244
CHT_MAX_STRIPPED_INPUT = 253
CHT_MAX_INPUT = CHT_MAX_STRIPPED_INPUT * 2
mapHistoryStatJumps = 1
mapHistoryStatKills = 3
mapHistoryStatFacWarKills = 5
corpInvFlagByDivision = {0: flagHangar,
 1: flagCorpSAG2,
 2: flagCorpSAG3,
 3: flagCorpSAG4,
 4: flagCorpSAG5,
 5: flagCorpSAG6,
 6: flagCorpSAG7}
corpDivisionByInvFlag = {flagHangar: 0,
 flagCorpSAG2: 1,
 flagCorpSAG3: 2,
 flagCorpSAG4: 3,
 flagCorpSAG5: 4,
 flagCorpSAG6: 5,
 flagCorpSAG7: 6}
zmetricCounter_EVEOnline = 10
zmetricCounter_EVETrial = 11
zmetricCounter_EVECREST = 12
counterBattleMembers = 10010
counterBattleMembersRegionUS = 10007
counterBattleMembersRegionEU = 10008
counterBattleMembersRegionAS = 10009
counterBattleMembersRegionOC = 10011
counterBattles = 10020
counterBattlesRegionUS = 10021
counterBattlesRegionEU = 10022
counterBattlesRegionAS = 10023
counterBattlesRegionOC = 10024
counterMatchmaking = 10025
counterMatchmakingRegionUS = 10026
counterMatchmakingRegionEU = 10027
counterMatchmakingRegionAS = 10028
counterMatchmakingRegionOC = 10029
counterMatchmakingQueueAcademy = 10100
counterMatchmakingQueueMercenary = 10150
counterMatchmakingQueueFaction = 10200
counterMatchmakingQueueReserved1 = 10250
counterMatchmakingQueueReserved2 = 10300
counterMatchmakingQueueReserved3 = 10350
matchmakingCounterQueues = {counterMatchmakingQueueAcademy: 'Academy',
 counterMatchmakingQueueMercenary: 'Mercenary',
 counterMatchmakingQueueFaction: 'Faction'}
counterMatchmakingPerformanceAverage = 0
counterMatchmakingPerformanceDeviation = 1
counterMatchmakingPlayerJoin = 2
counterMatchmakingPlayerLeave = 3
counterMatchmakingSquadJoin = 4
counterMatchmakingPlayerExpired = 5
counterMatchmakingPlayerInvited = 6
counterMatchmakingBattleCreated = 7
counterMatchmakingBattleMuAverage = 8
counterMatchmakingBattleMuDeviation = 9
counterMatchmakingBattleSigmaAverage = 10
counterMatchmakingBattleSigmaDeviation = 11
counterMatchmakingQueueLengthAverage = 12
counterMatchmakingQueueLengthDeviation = 13
counterMatchmakingPlayerWaitingAverage = 14
counterMatchmakingPlayerWaitingDeviation = 15
counterMatchmakingPlayerOptionsAverage = 16
counterMatchmakingPlayerOptionsDeviation = 17
counterMatchmakingPlayerRegionAverage = 18
counterMatchmakingPlayerRegionDeviation = 19
counterMatchmakingPlayerLatencyAverage = 20
counterMatchmakingPlayerLatencyDeviation = 21
counterMatchmakingVectorDeviationMu = 22
counterMatchmakingVectorDeviationSigma = 23
counterMatchmakingVectorDeviationOption = 24
counterMatchmakingVectorDeviationRegion = 25
matchmakingCounters = [(counterMatchmakingPerformanceAverage, counterMatchmakingPerformanceDeviation, 'Queue - CPU'),
 (counterMatchmakingQueueLengthAverage, counterMatchmakingQueueLengthDeviation, 'Queue - Length'),
 (counterMatchmakingPlayerJoin, None, 'Player - Join'),
 (counterMatchmakingPlayerLeave, None, 'Player - Leave'),
 (counterMatchmakingSquadJoin, None, 'Player - Squad Join'),
 (counterMatchmakingPlayerExpired, None, 'Player - Expired'),
 (counterMatchmakingPlayerInvited, None, 'Player - Matched'),
 (counterMatchmakingPlayerWaitingAverage, counterMatchmakingPlayerWaitingDeviation, 'Player - Waiting Time (seconds)'),
 (counterMatchmakingPlayerOptionsAverage, counterMatchmakingPlayerOptionsDeviation, 'Player - Preferred Option (%)'),
 (counterMatchmakingPlayerRegionAverage, counterMatchmakingPlayerRegionDeviation, 'Player - Preferred Region (%)'),
 (counterMatchmakingPlayerLatencyAverage, counterMatchmakingPlayerLatencyDeviation, 'Player - Latency (ms)'),
 (counterMatchmakingBattleCreated, None, 'Battle - Created'),
 (counterMatchmakingBattleMuAverage, counterMatchmakingBattleMuDeviation, 'Battle - stdev(mu)'),
 (counterMatchmakingBattleSigmaAverage, counterMatchmakingBattleSigmaDeviation, 'Battle - stdev(sigma)')]
zmetricCounter_DUSTOnline = 10040
zmetricCounter_DUSTUser = 10041
zmetricCounter_DUSTBattle = 10042
battleRegionCounters = {battleRegionUS: (counterBattlesRegionUS, counterBattleMembersRegionUS),
 battleRegionEU: (counterBattlesRegionEU, counterBattleMembersRegionEU),
 battleRegionAS: (counterBattlesRegionAS, counterBattleMembersRegionAS),
 battleRegionOC: (counterBattlesRegionOC, counterBattleMembersRegionOC)}
weaponsTimerStateIdle = 100
weaponsTimerStateActive = 101
weaponsTimerStateTimer = 102
weaponsTimerStateInherited = 103
pvpTimerStateIdle = 200
pvpTimerStateActive = 201
pvpTimerStateTimer = 202
pvpTimerStateInherited = 203
criminalTimerStateIdle = 300
criminalTimerStateActiveCriminal = 301
criminalTimerStateActiveSuspect = 302
criminalTimerStateTimerCriminal = 303
criminalTimerStateTimerSuspect = 304
criminalTimerStateInheritedCriminal = 305
criminalTimerStateInheritedSuspect = 306
npcTimerStateIdle = 400
npcTimerStateActive = 401
npcTimerStateTimer = 402
npcTimerStateInherited = 403
weaponsTimerTimeout = 60 * SEC
pvpTimerTimeout = 15 * MIN
criminalTimerTimeout = 15 * MIN
npcTimerTimeout = 5 * MIN
boosterTimerTimeout = 30 * MIN
crimewatchEngagementTimeoutOngoing = -1
crimewatchEngagementDuration = 5 * MIN
shipSafetyLevelNone = 0
shipSafetyLevelPartial = 1
shipSafetyLevelFull = 2
illegalTargetNpcOwnedGroups = {groupStation, groupStargate}
crimewatchOutcomeNone = 0
crimewatchOutcomeSuspect = 1
crimewatchOutcomeCriminal = 2
crimewatchOutcomeEngagement = 3
duelOfferExpiryTimeout = 30 * SEC
autoRejectDuelSettingsKey = 'autoRejectDuelInvitations'
MIN_BOUNTY_AMOUNT_CHAR = 100000
MIN_BOUNTY_AMOUNT_CORP = 20000000
MIN_BOUNTY_AMOUNT_ALLIANCE = 100000000
MAX_BOUNTY_AMOUNT = 100000000000L
containerGroupIDs = {groupWreck,
 groupCargoContainer,
 groupSpawnContainer,
 groupSecureCargoContainer,
 groupAuditLogSecureContainer,
 groupFreightContainer,
 groupDeadspaceOverseersBelongings,
 groupMissionContainer}
WARS_PER_PAGE = 50
GAME_TIME_TYPE_PLEX = 0
GAME_TIME_TYPE_BUDDY = 1
GAME_TIME_TYPE_WINGMAN = 2
GAME_TIME_TYPE_GM = 3
GAME_TIME_TYPE_SIGNUP_BONUS_14 = 4
canFitShipGroups = [1298,
 1299,
 1300,
 1301,
 1872,
 1879,
 1880,
 1881]
canFitShipTypes = [1302,
 1303,
 1304,
 1305,
 1944]
entityMaxSignatureRadiusSmall = 85
entityMaxSignatureRadiusMedium = 240
stationOwnersWithSecurityService = (ownerCONCORD, ownerDED)
maxAsteroidRadius = 16255
defaultDockingView = 'hangar'
legalOffensiveTargetOwnerIDs = {ownerNone,
 ownerSystem,
 ownerUnknown,
 factionUnknown}
microJumpDriveDistance = 100000
DUST_INSTANT_BOOSTER_TYPEIDS = [367596, 367597, 367598]
DUST_AGENT_TYPEIDS = [367578]
DUST_REROLL_DAILY_QUEST_TYPEIDS = [367843]
CHAR_VIP_SETTING_TYPEID = 367618
VIP_LEVEL_MAX = 15
SELLING_TO_NPC_DISCOUNT = 367674
