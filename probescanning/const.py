#Embedded file name: probescanning\const.py
import inventorycommon.const
import dogma.const
MAX_PROBES = 8
probeStateInactive = 0
probeStateIdle = 1
probeStateMoving = 2
probeStateWarping = 3
probeStateScanning = 4
probeStateReturning = 5
probeResultPerfect = 1.0
probeResultInformative = 0.75
probeResultGood = 0.25
probeResultUnusable = 0.001
scanProbeNumberOfRangeSteps = 8
scanProbeBaseNumberOfProbes = 4
AU = 149597870700.0
MAX_PROBE_DIST_FROM_SUN_SQUARED = (AU * 250) ** 2
probeScanGroupScrap = 1
probeScanGroupSignatures = 4
probeScanGroupShips = 8
probeScanGroupStructures = 16
probeScanGroupDronesAndProbes = 32
probeScanGroupCelestials = 64
probeScanGroupAnomalies = 128
probeScanGroups = {}
probeScanGroups[probeScanGroupScrap] = set([inventorycommon.const.groupAuditLogSecureContainer,
 inventorycommon.const.groupBiomass,
 inventorycommon.const.groupCargoContainer,
 inventorycommon.const.groupFreightContainer,
 inventorycommon.const.groupSecureCargoContainer,
 inventorycommon.const.groupWreck])
probeScanGroups[probeScanGroupSignatures] = set([inventorycommon.const.groupCosmicSignature])
probeScanGroups[probeScanGroupAnomalies] = set([inventorycommon.const.groupCosmicAnomaly])
probeScanGroups[probeScanGroupShips] = set([inventorycommon.const.groupAssaultShip,
 inventorycommon.const.groupAttackBattlecruiser,
 inventorycommon.const.groupBattlecruiser,
 inventorycommon.const.groupBattleship,
 inventorycommon.const.groupBlackOps,
 inventorycommon.const.groupBlockadeRunner,
 inventorycommon.const.groupCapitalIndustrialShip,
 inventorycommon.const.groupCapsule,
 inventorycommon.const.groupCarrier,
 inventorycommon.const.groupCombatReconShip,
 inventorycommon.const.groupCommandShip,
 inventorycommon.const.groupCovertOps,
 inventorycommon.const.groupCruiser,
 inventorycommon.const.groupDestroyer,
 inventorycommon.const.groupDreadnought,
 inventorycommon.const.groupElectronicAttackShips,
 inventorycommon.const.groupEliteBattleship,
 inventorycommon.const.groupExhumer,
 inventorycommon.const.groupExpeditionFrigate,
 inventorycommon.const.groupForceReconShip,
 inventorycommon.const.groupFreighter,
 inventorycommon.const.groupFrigate,
 inventorycommon.const.groupHeavyAssaultShip,
 inventorycommon.const.groupHeavyInterdictors,
 inventorycommon.const.groupIndustrial,
 inventorycommon.const.groupIndustrialCommandShip,
 inventorycommon.const.groupInterceptor,
 inventorycommon.const.groupInterdictor,
 inventorycommon.const.groupJumpFreighter,
 inventorycommon.const.groupLogistics,
 inventorycommon.const.groupMarauders,
 inventorycommon.const.groupMiningBarge,
 inventorycommon.const.groupSupercarrier,
 inventorycommon.const.groupPrototypeExplorationShip,
 inventorycommon.const.groupRookieship,
 inventorycommon.const.groupShuttle,
 inventorycommon.const.groupStealthBomber,
 inventorycommon.const.groupTacticalDestroyer,
 inventorycommon.const.groupTitan,
 inventorycommon.const.groupTransportShip,
 inventorycommon.const.groupStrategicCruiser])
probeScanGroups[probeScanGroupStructures] = set([inventorycommon.const.groupConstructionPlatform,
 inventorycommon.const.groupStationUpgradePlatform,
 inventorycommon.const.groupStationImprovementPlatform,
 inventorycommon.const.groupMobileWarpDisruptor,
 inventorycommon.const.groupAssemblyArray,
 inventorycommon.const.groupControlTower,
 inventorycommon.const.groupCorporateHangarArray,
 inventorycommon.const.groupElectronicWarfareBattery,
 inventorycommon.const.groupEnergyNeutralizingBattery,
 inventorycommon.const.groupForceFieldArray,
 inventorycommon.const.groupJumpPortalArray,
 inventorycommon.const.groupLogisticsArray,
 inventorycommon.const.groupMobileHybridSentry,
 inventorycommon.const.groupMobileLaboratory,
 inventorycommon.const.groupMobileLaserSentry,
 inventorycommon.const.groupMobileMissileSentry,
 inventorycommon.const.groupMobilePowerCore,
 inventorycommon.const.groupMobileProjectileSentry,
 inventorycommon.const.groupMobileReactor,
 inventorycommon.const.groupMobileShieldGenerator,
 inventorycommon.const.groupMobileStorage,
 inventorycommon.const.groupMoonMining,
 inventorycommon.const.groupReprocessingArray,
 inventorycommon.const.groupCompressionArray,
 inventorycommon.const.groupScannerArray,
 inventorycommon.const.groupSensorDampeningBattery,
 inventorycommon.const.groupShieldHardeningArray,
 inventorycommon.const.groupShipMaintenanceArray,
 inventorycommon.const.groupSilo,
 inventorycommon.const.groupStasisWebificationBattery,
 inventorycommon.const.groupStealthEmitterArray,
 inventorycommon.const.groupTrackingArray,
 inventorycommon.const.groupWarpScramblingBattery,
 inventorycommon.const.groupCynosuralSystemJammer,
 inventorycommon.const.groupCynosuralGeneratorArray,
 inventorycommon.const.groupInfrastructureHub,
 inventorycommon.const.groupSovereigntyClaimMarkers,
 inventorycommon.const.groupSovereigntyDisruptionStructures,
 inventorycommon.const.groupOrbitalConstructionPlatforms,
 inventorycommon.const.groupPlanetaryCustomsOffices,
 inventorycommon.const.groupSatellite,
 inventorycommon.const.groupPersonalHangar,
 inventorycommon.const.groupMobileHomes,
 inventorycommon.const.groupAutoLooter,
 inventorycommon.const.groupCynoInhibitor,
 inventorycommon.const.groupSiphonPseudoSilo,
 inventorycommon.const.groupMobileScanInhibitor,
 inventorycommon.const.groupMobileMicroJumpUnit,
 inventorycommon.const.groupEncounterSurveillanceSystem])
probeScanGroups[probeScanGroupDronesAndProbes] = set([inventorycommon.const.groupCapDrainDrone,
 inventorycommon.const.groupCombatDrone,
 inventorycommon.const.groupElectronicWarfareDrone,
 inventorycommon.const.groupFighterDrone,
 inventorycommon.const.groupFighterBomber,
 inventorycommon.const.groupLogisticDrone,
 inventorycommon.const.groupMiningDrone,
 inventorycommon.const.groupProximityDrone,
 inventorycommon.const.groupRepairDrone,
 inventorycommon.const.groupStasisWebifyingDrone,
 inventorycommon.const.groupUnanchoringDrone,
 inventorycommon.const.groupWarpScramblingDrone,
 inventorycommon.const.groupScannerProbe,
 inventorycommon.const.groupSurveyProbe,
 inventorycommon.const.groupSalvageDrone,
 inventorycommon.const.groupWarpDisruptionProbe])
probeScanGroups[probeScanGroupCelestials] = set([inventorycommon.const.groupAsteroidBelt,
 inventorycommon.const.groupForceField,
 inventorycommon.const.groupMoon,
 inventorycommon.const.groupPlanet,
 inventorycommon.const.groupStargate,
 inventorycommon.const.groupSun,
 inventorycommon.const.groupStation])
probeScanCosmicSignatureAttributes = {dogma.const.attributeScanGravimetricStrength,
 dogma.const.attributeScanLadarStrength,
 dogma.const.attributeScanMagnetometricStrength,
 dogma.const.attributeScanRadarStrength,
 dogma.const.attributeScanWormholeStrength,
 dogma.const.attributeScanAllStrength}
SCAN_STRENGTHS = [dogma.const.attributeScanGravimetricStrength,
 dogma.const.attributeScanLadarStrength,
 dogma.const.attributeScanMagnetometricStrength,
 dogma.const.attributeScanRadarStrength,
 dogma.const.attributeScanWormholeStrength]

def GetCosmicSignatureGroups():
    return {(inventorycommon.const.groupCosmicSignature, attributeID) for attributeID in probeScanCosmicSignatureAttributes}


def GetDroneGroups():
    return probeScanGroups[probeScanGroupDronesAndProbes]


def GetShipGroups():
    return probeScanGroups[probeScanGroupShips].copy()


def GetStructureGroups():
    return probeScanGroups[probeScanGroupStructures].copy()
