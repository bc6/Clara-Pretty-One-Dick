#Embedded file name: eve/client/script/ui/shared/info\infoConst.py
import const
TYPE_CHARACTER = 1
TYPE_CORPORATION = 2
TYPE_ALLIANCE = 3
TYPE_FACTION = 4
TYPE_BOOKMARK = 5
TYPE_SHIP = 6
TYPE_MODULE = 7
TYPE_CHARGE = 8
TYPE_BLUEPRINT = 9
TYPE_REACTION = 10
TYPE_DRONE = 11
TYPE_SECURITYTAG = 12
TYPE_PLANETCOMMODITY = 13
TYPE_APPAREL = 14
TYPE_GENERICITEM = 15
TYPE_STARGATE = 30
TYPE_CONTROLTOWER = 31
TYPE_CONSTRUCTIONPLATFORM = 32
TYPE_STATION = 33
TYPE_STRUCTURE = 34
TYPE_PLANETPIN = 35
TYPE_CUSTOMSOFFICE = 38
TYPE_STRUCTUREUPGRADE = 39
TYPE_PLANET = 40
TYPE_WORMHOLE = 41
TYPE_CONTAINER = 50
TYPE_SECURECONTAINER = 51
TYPE_CELESTIAL = 52
TYPE_ENTITY = 53
TYPE_LANDMARK = 54
TYPE_ASTEROID = 55
TYPE_DEPLOYABLE = 56
TYPE_RANK = 60
TYPE_MEDAL = 61
TYPE_RIBBON = 62
TYPE_CERTIFICATE = 63
TYPE_SCHEMATIC = 64
TYPE_SKILL = 65
TYPE_UNKNOWN = 100
infoTypeByTypeID = {const.typeBookmark: TYPE_BOOKMARK,
 const.typeRank: TYPE_RANK,
 const.typeMedal: TYPE_MEDAL,
 const.typeRibbon: TYPE_RIBBON,
 const.typeCertificate: TYPE_CERTIFICATE,
 const.typeSchematic: TYPE_SCHEMATIC}
infoTypeByGroupID = {const.groupCharacter: TYPE_CHARACTER,
 const.groupCorporation: TYPE_CORPORATION,
 const.groupAlliance: TYPE_ALLIANCE,
 const.groupFaction: TYPE_FACTION,
 const.groupSecurityTags: TYPE_SECURITYTAG,
 const.groupStargate: TYPE_STARGATE,
 const.groupControlTower: TYPE_CONTROLTOWER,
 const.groupStationUpgradePlatform: TYPE_CONSTRUCTIONPLATFORM,
 const.groupStationImprovementPlatform: TYPE_CONSTRUCTIONPLATFORM,
 const.groupConstructionPlatform: TYPE_CONSTRUCTIONPLATFORM,
 const.groupPlanetaryCustomsOffices: TYPE_CUSTOMSOFFICE,
 const.groupPlanet: TYPE_PLANET,
 const.groupWormhole: TYPE_WORMHOLE,
 const.groupMobileWarpDisruptor: TYPE_STRUCTURE,
 const.groupLargeCollidableStructure: TYPE_CELESTIAL,
 const.groupDeadspaceOverseersStructure: TYPE_CELESTIAL,
 const.groupHarvestableCloud: TYPE_ASTEROID,
 const.groupSecureCargoContainer: TYPE_SECURECONTAINER,
 const.groupAuditLogSecureContainer: TYPE_SECURECONTAINER,
 const.groupLandmark: TYPE_LANDMARK,
 const.groupStation: TYPE_STATION,
 const.groupCargoContainer: TYPE_CONTAINER,
 const.groupFreightContainer: TYPE_CONTAINER,
 const.groupOrbitalConstructionPlatforms: TYPE_STRUCTURE}
infoTypeByCategoryID = {const.categoryShip: TYPE_SHIP,
 const.categoryModule: TYPE_MODULE,
 const.categorySubSystem: TYPE_MODULE,
 const.categoryCharge: TYPE_CHARGE,
 const.categoryBlueprint: TYPE_BLUEPRINT,
 const.categoryAncientRelic: TYPE_BLUEPRINT,
 const.categoryReaction: TYPE_REACTION,
 const.categoryDrone: TYPE_DRONE,
 const.categoryApparel: TYPE_APPAREL,
 const.categoryImplant: TYPE_GENERICITEM,
 const.categoryAccessories: TYPE_GENERICITEM,
 const.categoryStructure: TYPE_STRUCTURE,
 const.categorySovereigntyStructure: TYPE_STRUCTURE,
 const.categoryStructureUpgrade: TYPE_STRUCTUREUPGRADE,
 const.categoryEntity: TYPE_ENTITY,
 const.categoryPlanetaryInteraction: TYPE_PLANETPIN,
 const.categoryPlanetaryResources: TYPE_PLANETCOMMODITY,
 const.categoryPlanetaryCommodities: TYPE_PLANETCOMMODITY,
 const.categorySkill: TYPE_SKILL,
 const.categoryAsteroid: TYPE_ASTEROID,
 const.categoryCelestial: TYPE_CELESTIAL,
 const.categoryDeployable: TYPE_DEPLOYABLE}
ownedGroups = (const.groupWreck,
 const.groupSecureCargoContainer,
 const.groupAuditLogSecureContainer,
 const.groupCargoContainer,
 const.groupFreightContainer,
 const.groupSentryGun,
 const.groupDestructibleSentryGun,
 const.groupMobileSentryGun,
 const.groupDeadspaceOverseersSentry,
 const.groupPlanet)
ownedCategories = (const.categoryStructure,
 const.categorySovereigntyStructure,
 const.categoryOrbital,
 const.categoryDeployable)
TAB_ATTIBUTES = 1
TAB_CORPMEMBERS = 2
TAB_NEIGHBORS = 3
TAB_CHILDREN = 4
TAB_FITTING = 5
TAB_CERTREQUIREMENTS = 6
TAB_REQUIREMENTS = 7
TAB_CERTRECOMMENDEDFOR = 10
TAB_VARIATIONS = 11
TAB_LEGALITY = 13
TAB_JUMPS = 14
TAB_MODULES = 15
TAB_ORBITALBODIES = 16
TAB_SYSTEMS = 17
TAB_LOCATION = 18
TAB_AGENTINFO = 19
TAB_AGENTS = 20
TAB_ROUTE = 21
TAB_INSURANCE = 22
TAB_SERVICES = 23
TAB_STANDINGS = 24
TAB_DECORATIONS = 25
TAB_MEDALS = 27
TAB_RANKS = 28
TAB_MEMBEROFCORPS = 29
TAB_MARKETACTIVITY = 30
TAB_DATA = 31
TAB_EMPLOYMENTHISTORY = 40
TAB_ALLIANCEHISTORY = 53
TAB_FUELREQ = 41
TAB_MATERIALREQ = 42
TAB_UPGRADEMATERIALREQ = 43
TAB_PLANETCONTROL = 44
TAB_REACTION = 45
TAB_NOTES = 46
TAB_DOGMA = 47
TAB_MEMBERS = 48
TAB_UNKNOWN = 49
TAB_HIERARCHY = 50
TAB_SCHEMATICS = 51
TAB_PRODUCTIONINFO = 52
TAB_WARHISTORY = 54
TAB_REQUIREDFOR = 55
TAB_MASTERY = 56
TAB_CERTSKILLS = 57
TAB_TRAITS = 58
TAB_DESCRIPTION = 59
TAB_BIO = 60
TAB_STATIONS = 61
TAB_INDUSTRY = 62
TAB_ITEMINDUSTRY = 63
TAB_USEDWITH = 64
INFO_TABS = ((TAB_TRAITS, [], 'UI/InfoWindow/TabNames/Traits'),
 (TAB_BIO, [], 'UI/InfoWindow/TabNames/Bio'),
 (TAB_INDUSTRY, [], 'UI/InfoWindow/TabNames/Industry'),
 (TAB_DESCRIPTION, [], 'UI/InfoWindow/TabNames/Description'),
 (TAB_ATTIBUTES, [], 'UI/InfoWindow/TabNames/Attributes'),
 (TAB_USEDWITH, [], 'UI/InfoWindow/TabNames/UsedWith'),
 (TAB_CORPMEMBERS, [], 'UI/InfoWindow/TabNames/CorpMembers'),
 (TAB_NEIGHBORS, [], 'UI/InfoWindow/TabNames/Neighbors'),
 (TAB_CHILDREN, [], 'UI/InfoWindow/TabNames/Children'),
 (TAB_FITTING, [], 'UI/InfoWindow/TabNames/Fitting'),
 (TAB_REQUIREMENTS, [], 'UI/InfoWindow/TabNames/Requirements'),
 (TAB_CERTSKILLS, [], 'UI/InfoWindow/TabNames/Levels'),
 (TAB_CERTRECOMMENDEDFOR, [], 'UI/InfoWindow/TabNames/RecommendedFor'),
 (TAB_MASTERY, [], 'UI/InfoWindow/TabNames/Mastery'),
 (TAB_VARIATIONS, [], 'UI/InfoWindow/TabNames/Variations'),
 (TAB_LEGALITY, [], 'UI/InfoWindow/TabNames/Legality'),
 (TAB_JUMPS, [], 'UI/InfoWindow/TabNames/Jumps'),
 (TAB_MODULES, [], 'UI/InfoWindow/TabNames/Modules'),
 (TAB_ORBITALBODIES, [], 'UI/InfoWindow/TabNames/OrbitalBodies'),
 (TAB_STATIONS, [], 'UI/Common/LocationTypes/Stations'),
 (TAB_SYSTEMS, [], 'UI/InfoWindow/TabNames/Systems'),
 (TAB_LOCATION, [], 'UI/InfoWindow/TabNames/Location'),
 (TAB_AGENTINFO, [], 'UI/InfoWindow/TabNames/AgentInfo'),
 (TAB_AGENTS, [], 'UI/InfoWindow/TabNames/Agents'),
 (TAB_ROUTE, [], 'UI/InfoWindow/TabNames/Route'),
 (TAB_INSURANCE, [], 'UI/InfoWindow/TabNames/Insurance'),
 (TAB_SERVICES, [], 'UI/InfoWindow/TabNames/Services'),
 (TAB_STANDINGS, [], 'UI/InfoWindow/TabNames/Standings'),
 (TAB_DECORATIONS, [(TAB_MEDALS, [], 'UI/InfoWindow/TabNames/Medals'), (TAB_RANKS, [], 'UI/InfoWindow/TabNames/Ranks')], 'UI/InfoWindow/TabNames/Decorations'),
 (TAB_MEMBEROFCORPS, [], 'UI/InfoWindow/TabNames/MemberCorps'),
 (TAB_MARKETACTIVITY, [], 'UI/InfoWindow/TabNames/MarketActivity'),
 (TAB_DATA, [], 'UI/InfoWindow/TabNames/Data'),
 (TAB_EMPLOYMENTHISTORY, [], 'UI/InfoWindow/TabNames/EmploymentHistory'),
 (TAB_ALLIANCEHISTORY, [], 'UI/InfoWindow/TabNames/AllianceHistory'),
 (TAB_WARHISTORY, [], 'UI/InfoWindow/TabNames/WarHistory'),
 (TAB_FUELREQ, [], 'UI/InfoWindow/TabNames/FuelRequirements'),
 (TAB_MATERIALREQ, [], 'UI/InfoWindow/TabNames/MaterialRequirements'),
 (TAB_UPGRADEMATERIALREQ, [], 'UI/InfoWindow/TabNames/UpgradeRequirements'),
 (TAB_PLANETCONTROL, [], 'UI/InfoWindow/TabNames/PlanetControl'),
 (TAB_REACTION, [], 'UI/InfoWindow/TabNames/Reaction'),
 (TAB_NOTES, [], 'UI/InfoWindow/TabNames/Notes'),
 (TAB_DOGMA, [], 'UI/InfoWindow/TabNames/Dogma'),
 (TAB_MEMBERS, [], 'UI/InfoWindow/TabNames/Members'),
 (TAB_UNKNOWN, [], 'UI/InfoWindow/TabNames/Unknown'),
 (TAB_HIERARCHY, [], 'UI/InfoWindow/TabNames/Hierarchy'),
 (TAB_SCHEMATICS, [], 'UI/InfoWindow/TabNames/Schematics'),
 (TAB_PRODUCTIONINFO, [], 'UI/InfoWindow/TabNames/ProductionInfo'),
 (TAB_REQUIREDFOR, [], 'UI/InfoWindow/TabNames/RequiredFor'),
 (TAB_ITEMINDUSTRY, [], 'UI/InfoWindow/TabNames/Industry'))
