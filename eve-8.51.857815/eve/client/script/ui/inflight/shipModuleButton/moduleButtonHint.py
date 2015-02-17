#Embedded file name: eve/client/script/ui/inflight/shipModuleButton\moduleButtonHint.py
"""
The UI code for the ship module hints
"""
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from eve.client.script.ui.crimewatch.crimewatchConst import Colors as CrimeWatchColors
import math
import blue
from carbonui.primitives.fill import Fill
from carbonui.primitives.frame import Frame
from localization import GetByLabel
from localization.formatters import FormatNumeric
from uthread import worker
from carbon.common.script.util.format import FmtDist
from carbon.common.script.util.mathUtil import Lerp
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveLabel import EveLabelMedium
from eve.client.script.ui.util.uix import GetTechLevelIcon
from eve.common.script.sys.eveCfg import GetActiveShip
MAXMODULEHINTWIDTH = 300

class ModuleButtonHint(ContainerAutoSize):
    __guid__ = 'uicls.ModuleButtonHint'
    default_state = uiconst.UI_DISABLED
    infoFunctionNames = {const.groupMiningLaser: 'AddMiningLaserInfo',
     const.groupStripMiner: 'AddMiningLaserInfo',
     const.groupFrequencyMiningLaser: 'AddMiningLaserInfo',
     const.groupEnergyVampire: 'AddEnergyVampireInfo',
     const.groupEnergyDestabilizer: 'AddEnergyDestabilizerInfo',
     const.groupArmorRepairUnit: 'AddArmorRepairersInfo',
     const.groupHullRepairUnit: 'AddHullRepairersInfo',
     const.groupShieldBooster: 'AddShieldBoosterInfo',
     const.groupTrackingComputer: 'AddTrackingComputerInfo',
     const.groupTrackingLink: 'AddTrackingComputerInfo',
     const.groupSmartBomb: 'AddSmartBombInfo',
     const.groupAfterBurner: 'AddPropulsionModuleInfo',
     const.groupStatisWeb: 'AddStasisWebInfo',
     const.groupWarpScrambler: 'AddWarpScramblerInfo',
     const.groupCapacitorBooster: 'AddCapacitorBoosterInfo',
     const.groupEnergyTransferArray: 'AddEnergyTransferArrayInfo',
     const.groupShieldTransporter: 'AddShieldTransporterInfo',
     const.groupArmorRepairProjector: 'AddArmorRepairProjectorInfo',
     const.groupRemoteHullRepairer: 'AddRemoteHullRepairInfo',
     const.groupArmorHardener: 'AddArmorHardenerInfo',
     const.groupArmorCoating: 'AddArmorHardenerInfo',
     const.groupShieldHardener: 'AddArmorHardenerInfo',
     const.groupShieldAmplifier: 'AddArmorHardenerInfo',
     const.groupArmorPlatingEnergized: 'AddArmorHardenerInfo',
     const.groupElectronicCounterMeasureBurst: 'AddECMInfo',
     const.groupElectronicCounterMeasures: 'AddECMInfo',
     const.groupElectronicCounterCounterMeasures: 'AddECCMInfo',
     const.groupProjectedElectronicCounterCounterMeasures: 'AddECCMInfo',
     const.groupRemoteSensorDamper: 'AddSensorDamperInfo',
     const.groupRemoteSensorBooster: 'AddSensorDamperInfo',
     const.groupSensorBooster: 'AddSensorDamperInfo',
     const.groupTargetBreaker: 'AddTargetBreakerInfo',
     const.groupTargetPainter: 'AddTargetPainterInfo',
     const.groupTrackingDisruptor: 'AddTrackingDisruptorInfo',
     const.groupCloakingDevice: 'AddCloakingDeviceInfo',
     const.groupTractorBeam: 'AddTractorBeamInfo',
     const.groupDamageControl: 'AddDamageControlInfo',
     const.groupArmorResistanceShiftHardener: 'AddArmorResistanceShiftHardenerInfo',
     const.groupSuperWeapon: 'AddSuperWeaponInfo',
     const.groupGangCoordinator: 'AddGangCoordinatorInfo'}

    def ApplyAttributes(self, attributes):
        self.stateManager = sm.StartService('godma').GetStateManager()
        self.dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        ContainerAutoSize.ApplyAttributes(self, attributes)
        self.moduleTypeID = attributes.moduleTypeID
        self.chargeTypeID = attributes.chargeTypeID
        self.clipChildren = 1
        self.smallContainerHeight = 30
        self.bigContainerHeight = 36
        self.iconeSize = 26
        self.fromWhere = ''
        self.typeCont = ModuleButtonHintContainerTypeWithShortcut(parent=self, name='typeCont', height=self.smallContainerHeight)
        self.chargeCont = ModuleButtonHintContainerType(parent=self, name='chargeCont', height=self.smallContainerHeight)
        self.rangeCont = ModuleButtonHintContainerBase(parent=self, name='rangeCont', height=self.bigContainerHeight, texturePath='res:/UI/Texture/Icons/22_32_15.png')

    def UpdateAllInfo(self, moduleItemID, chargeItemID, positionTuple = None, fromWhere = 'shipModuleButton', *args):
        self.fromWhere = fromWhere
        moduleInfoItem = self.dogmaLocation.GetDogmaItem(moduleItemID)
        if chargeItemID is None:
            chargeInfoItem = None
        else:
            chargeInfoItem = self.dogmaLocation.GetDogmaItem(chargeItemID)
        typeName = cfg.invtypes.Get(moduleInfoItem.typeID).name
        moduleDamageAmount = None
        if fromWhere == 'fitting':
            damage = self.dogmaLocation.GetAccurateAttributeValue(moduleItemID, const.attributeDamage)
        else:
            damage = uicore.layer.shipui.GetModuleGroupDamage(moduleItemID)
        if damage:
            moduleDamageAmount = int(math.ceil(damage / self.dogmaLocation.GetAttributeValue(moduleItemID, const.attributeHp) * 100))
        else:
            moduleDamageAmount = 0.0
        chargesType, chargesQty = self.GetChargeTypeAndQty(moduleInfoItem, chargeInfoItem)
        if self.moduleTypeID != moduleInfoItem.typeID or self.chargeTypeID != chargesType:
            for child in self.children[:]:
                if getattr(child, 'isExtraInfoContainer', False):
                    child.Close()

            self.moduleTypeID = moduleInfoItem.typeID
            self.typeCont.SetTypeIcon(typeID=moduleInfoItem.typeID)
        maxTextWidth = 0
        myShip = GetActiveShip()
        if fromWhere == 'fitting':
            numSlaves = 0
        else:
            numSlaves = self.GetNumberOfSlaves(moduleInfoItem.itemID, myShip)
        self.typeCont.SetTypeTextAndDamage(typeName, moduleDamageAmount, numSlaves, bold=True)
        self.typeCont.SetContainerHeight()
        moduleShortcut = self.GetModuleShortCut(moduleInfoItem)
        if moduleShortcut:
            self.typeCont.SetShortcutText(moduleShortcut)
            self.typeCont.shortcutCont.display = True
        else:
            self.HideContainer(self.typeCont.shortcutCont)
            self.typeCont.shortcutPadding = 0
        self.UpdateChargesCont(chargeInfoItem, chargesQty)
        maxRange, falloffDist, bombRadius = sm.GetService('tactical').FindMaxRange(moduleInfoItem, chargeInfoItem)
        self.UpdateRangeCont(moduleInfoItem.typeID, maxRange, falloffDist)
        self.AddGroupOrCategorySpecificInfo(moduleInfoItem.itemID, moduleInfoItem.typeID, chargeInfoItem, chargesQty, numSlaves)
        maxTextWidth = self.FindMaxWidths()
        self.width = min(maxTextWidth + 10, MAXMODULEHINTWIDTH)
        self.typeCont.AddFading(self.width)
        self.chargeCont.AddFading(self.width)

    def SetSafetyWarning(self, safetyLevel):
        safetyCont = getattr(self, 'safetyCont', None)
        if safetyCont is None:
            self.safetyCont = ModuleButtonHintContainerSafetyLevel(parent=self, name='safetyCont', height=self.smallContainerHeight, texturePath='res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal.png')
            safetyCont = self.safetyCont
        else:
            safetyCont.SetOrder(-1)
        safetyCont.SetSafetyLevelWarning(safetyLevel)
        safetyCont.display = True

    def RemoveSafetyWarning(self):
        if getattr(self, 'safetyCont', None) is not None:
            self.safetyCont.display = False

    def GetNumberOfSlaves(self, itemID, shipID):
        slaves = self.dogmaLocation.GetSlaveModules(itemID, shipID)
        if slaves:
            numSlaves = len(slaves) + 1
        else:
            numSlaves = 0
        return numSlaves

    def GetCrystalDamage(self, chargeInfoItem):
        crystalDamageAmount = None
        if chargeInfoItem is not None:
            dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
            crystalDamageAmount = dogmaLocation.GetAccurateAttributeValue(chargeInfoItem.itemID, const.attributeDamage)
        return crystalDamageAmount

    def GetModuleShortCut(self, moduleInfoItem):
        moduleShortcut = None
        masterModuleID = self.dogmaLocation.GetMasterModuleID(GetActiveShip(), moduleInfoItem.itemID)
        if masterModuleID is not None:
            masterModuleInfoItem = self.dogmaLocation.GetDogmaItem(masterModuleID)
            flagID = masterModuleInfoItem.flagID
        else:
            flagID = moduleInfoItem.flagID
        slotOrder = uicore.layer.shipui.GetSlotOrder()
        if flagID not in slotOrder:
            return
        pos = slotOrder.index(flagID)
        if pos is not None:
            row = pos / 8
            hiMedLo = ('High', 'Medium', 'Low')[row]
            loc = pos % 8
            slotno = loc + 1
            shortcut = uicore.cmd.GetShortcutStringByFuncName('CmdActivate%sPowerSlot%i' % (hiMedLo, slotno))
            if shortcut:
                moduleShortcut = shortcut
        return moduleShortcut

    def GetChargeTypeAndQty(self, moduleInfoItem, chargeInfoItem):
        chargesQty = None
        chargesType = None
        if self.IsChargeCompatible(moduleInfoItem):
            if chargeInfoItem and chargeInfoItem.typeID:
                chargesQty = self.dogmaLocation.GetQuantity(chargeInfoItem.itemID)
                chargesType = chargeInfoItem.typeID
            else:
                chargesQty = 0
        return (chargesType, chargesQty)

    def IsChargeCompatible(self, moduleInfoItem, *args):
        return moduleInfoItem.groupID in cfg.__chargecompatiblegroups__

    def FindMaxWidths(self, *args):
        maxTextWidth = 0
        for child in self.children:
            maxWidthFunc = getattr(child, 'GetContainerWidth', None)
            if maxWidthFunc is None:
                continue
            maxTextWidth = max(child.GetContainerWidth(), maxTextWidth)

        return maxTextWidth

    def UpdateRangeCont(self, typeID, optimalRange, falloff):
        if optimalRange > 0:
            self.rangeCont.display = True
            rangeText = self.GetOptimalRangeText(typeID, optimalRange, falloff)
            self.rangeCont.textLabel.text = rangeText
            self.rangeCont.SetContainerHeight()
        else:
            self.HideContainer(self.rangeCont)

    def GetOptimalRangeText(self, typeID, optimalRange, falloff, *args):
        rangeText = ''
        if optimalRange > 0:
            formattedOptimalRAnge = FmtDist(optimalRange)
            if sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, const.effectLauncherFitted):
                rangeText = GetByLabel('UI/Inflight/ModuleRacks/MaxRange', maxRange=formattedOptimalRAnge)
            elif sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, const.effectTurretFitted):
                if falloff > 1:
                    rangeText = GetByLabel('UI/Inflight/ModuleRacks/OptimalRangeAndFalloff', optimalRange=formattedOptimalRAnge, falloffPlusOptimal=FmtDist(falloff + optimalRange))
                else:
                    rangeText = GetByLabel('UI/Inflight/ModuleRacks/OptimalRange', optimalRange=formattedOptimalRAnge)
            elif cfg.invtypes.Get(typeID).Group().groupID == const.groupSmartBomb:
                rangeText = GetByLabel('UI/Inflight/ModuleRacks/AreaOfEffect', range=formattedOptimalRAnge)
            elif falloff > 1:
                rangeText = GetByLabel('UI/Inflight/ModuleRacks/RangeWithFalloff', optimalRange=formattedOptimalRAnge, falloffPlusOptimal=FmtDist(falloff + optimalRange))
            else:
                rangeText = GetByLabel('UI/Inflight/ModuleRacks/Range', optimalRange=formattedOptimalRAnge)
        return rangeText

    def UpdateChargesCont(self, chargeInfoItem, chargesQty):
        if chargeInfoItem and chargesQty:
            self.chargeCont.display = True
            chargesTypeID = chargeInfoItem.typeID
            if self.chargeTypeID != chargesTypeID:
                self.chargeTypeID = chargesTypeID
                self.chargeCont.SetTypeIcon(typeID=chargesTypeID)
                GetTechLevelIcon(self.chargeCont.techIcon, typeID=chargesTypeID)
            chargeText = self.GetChargeText(chargeInfoItem, chargesQty)
            self.chargeCont.textLabel.text = chargeText
            self.chargeCont.SetContainerHeight()
        else:
            self.chargeTypeID = None
            self.HideContainer(self.chargeCont)

    def GetChargeText(self, chargeInfoItem, chargesQty, *args):
        chargeText = ''
        if chargeInfoItem.groupID in cfg.GetCrystalGroups():
            crystalDamageAmount = self.GetCrystalDamage(chargeInfoItem)
            chargeText = '<b>%s</b>' % cfg.invtypes.Get(chargeInfoItem.typeID).name
            if crystalDamageAmount > 0.0:
                damagedText = GetByLabel('UI/Inflight/ModuleRacks/AmmoDamaged', color='<color=red>', damage=crystalDamageAmount)
                chargeText += '<br>' + damagedText
        else:
            chargeText = GetByLabel('UI/Inflight/ModuleRacks/AmmoNameWithQty', qty=chargesQty, ammoTypeID=chargeInfoItem.typeID)
        return chargeText

    def HideContainer(self, container):
        container.display = False
        container.textLabel.text = ''

    def AddSpecificInfoContainer(self, text, configName, iconID = None, texturePath = None, *args):
        myContainer = getattr(self, configName, None)
        if myContainer is None or myContainer.destroyed:
            myContainer = ModuleButtonHintContainerBase(parent=self, name=configName, align=uiconst.TOTOP, height=self.bigContainerHeight, texturePath=texturePath, iconID=iconID, isExtraInfoContainer=True)
            setattr(self, configName, myContainer)
        myContainer.textLabel.text = text
        myContainer.SetContainerHeight()

    def AddGroupOrCategorySpecificInfo(self, itemID, typeID, chargeInfoItem, chargesQty, numSlaves, *args):
        """
            if needed, this function can be changed so it does if/elif checks on the groups 
            rather than use a dictionary to find the info functions
        """
        group = cfg.invtypes.Get(typeID).Group()
        if chargesQty is None:
            for contName in ('damageTypeContMany', 'damagaTypeContOne', 'dpsCont'):
                cont = getattr(self, contName, None)
                if cont is not None and not cont.destroyed:
                    cont.Close()

        else:
            self.AddDpsAndDamgeTypeInfo(itemID, typeID, group.groupID, chargeInfoItem, numSlaves)
        myInfoFunctionName = self.infoFunctionNames.get(group.groupID, None)
        if myInfoFunctionName is not None:
            myInfoFunction = getattr(self, myInfoFunctionName)
            myInfoFunction(itemID, chargeInfoItem)

    def GetAttributeValue(self, itemID, attributeID, *args):
        return self.dogmaLocation.GetAccurateAttributeValue(itemID, attributeID)

    def GetDuration(self, itemID, *args):
        duration = self.GetAttributeValue(itemID, const.attributeDuration)
        durationInSec = duration / 1000.0
        if durationInSec % 1.0 == 0:
            decimalPlaces = 0
        else:
            decimalPlaces = 1
        unit = cfg.dgmunits.Get(const.unitMilliseconds).displayName
        durationFormatted = FormatNumeric(durationInSec, decimalPlaces=decimalPlaces)
        formattedDuration = GetByLabel('UI/InfoWindow/ValueAndUnit', value=durationFormatted, unit=unit)
        return formattedDuration

    def GetAmountPerTimeInfo(self, itemID, attributeID, configName, labelPath, *args):
        """
            This function adds a container where the info is "X amount per Y seconds".
            This function assumes the string the labelPath points to only has 2 keywords, amount and duration
            A lot of the modules are showing this info, using the attribute icon, but if some other icon
            is needed, or some special casing is needed, it's easy enough to build those containers
            (see AddMiningLaserInfo and AddSmartBombInfo)
        """
        duration = self.GetDuration(itemID)
        amount = self.GetAttributeValue(itemID, attributeID)
        text = GetByLabel(labelPath, duration=duration, amount=amount)
        self.AddSpecificInfoContainer(text, configName, iconID=cfg.dgmattribs.Get(attributeID).iconID)

    def AddDpsAndDamgeTypeInfo(self, itemID, typeID, groupID, charge, numSlaves, *args):
        isBomb = groupID == const.groupMissileLauncherBomb
        isLauncher = sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, const.effectLauncherFitted)
        isTurret = sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, const.effectTurretFitted)
        if not isLauncher and not isTurret and not isBomb:
            return
        GAV = self.dogmaLocation.GetAccurateAttributeValue
        texturePath = None
        iconID = None
        totalDpsDamage = 0
        if (isLauncher or isBomb) and charge:
            chargeKey = charge.itemID
            totalDpsDamage = self.dogmaLocation.GetLauncherDps(chargeKey, itemID, session.charid, GAV)
            damageMultiplier = GAV(session.charid, const.attributeMissileDamageMultiplier)
            if isLauncher:
                texturePath = 'res:/UI/Texture/Icons/81_64_16.png'
            else:
                iconID = cfg.invtypes.Get(typeID).iconID
        elif isTurret:
            if charge:
                chargeKey = charge.itemID
            else:
                chargeKey = None
            totalDpsDamage = self.dogmaLocation.GetTurretDps(chargeKey, itemID, GAV)
            damageMultiplier = GAV(itemID, const.attributeDamageMultiplier)
            texturePath = 'res:/UI/Texture/Icons/26_64_1.png'
        if totalDpsDamage == 0:
            return
        if numSlaves:
            totalDpsDamage = numSlaves * totalDpsDamage
            damageMultiplier = numSlaves * damageMultiplier
        text = GetByLabel('UI/Inflight/ModuleRacks/DamagePerSecond', dps=totalDpsDamage)
        self.AddSpecificInfoContainer(text, 'dpsCont', iconID=iconID, texturePath=texturePath)
        damageTypeAttributes = [(const.attributeEmDamage, None),
         (const.attributeExplosiveDamage, None),
         (const.attributeKineticDamage, None),
         (const.attributeThermalDamage, None)]
        textDict = {'noPassiveValue': 'UI/Inflight/ModuleRacks/Tooltips/DamageHitpoints',
         'manyHeaderWithoutPassive': 'UI/Inflight/ModuleRacks/Tooltips/DamageTypesHeader',
         'oneDamageTypeWithoutPassive': 'UI/Inflight/ModuleRacks/Tooltips/OneDamageTypeText'}
        if charge:
            dmgCausingItemID = charge.itemID
        else:
            dmgCausingItemID = itemID
            if numSlaves:
                damageMultiplier = numSlaves
            else:
                damageMultiplier = 1
        self.GetDamageTypeInfo(dmgCausingItemID, damageTypeAttributes, textDict, multiplier=damageMultiplier)

    def AddMiningLaserInfo(self, itemID, chargeInfoItem, *args):
        duration = self.GetDuration(itemID)
        amount = self.GetAttributeValue(itemID, const.attributeMiningAmount)
        if chargeInfoItem is not None:
            specializationMultiplier = self.GetAttributeValue(chargeInfoItem.itemID, const.attributeSpecialisationAsteroidYieldMultiplier)
            amount = specializationMultiplier * amount
        text = GetByLabel('UI/Inflight/ModuleRacks/Tooltips/MiningAmountPerTime', duration=duration, amount=amount)
        self.AddSpecificInfoContainer(text, 'miningAmountCont', texturePath='res:/ui/texture/icons/23_64_5.png')

    def AddEnergyVampireInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributePowerTransferAmount, configName='leachedAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/EnergyVampireAmountPerTime')

    def AddEnergyDestabilizerInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeEnergyDestabilizationAmount, configName='destablizedAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/EnergDestabilizedPerTime')

    def AddArmorRepairersInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeArmorDamageAmount, configName='armorRepairAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/ArmorRepairedPerTime')

    def AddHullRepairersInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeStructureDamageAmount, configName='hullRepairAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/HullRepairedPerTime')

    def AddShieldBoosterInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeShieldBonus, configName='shieldBoosterAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/ShieldBonusPerTime')

    def AddTrackingComputerInfo(self, itemID, *args):
        falloff = self.GetAttributeValue(itemID, const.attributeFalloffBonus)
        text = GetByLabel('UI/Inflight/ModuleRacks/Tooltips/TrackingComputerFalloffBonus', falloffBonus=falloff)
        self.AddSpecificInfoContainer(text, 'trackingComputerFalloffCont', iconID=cfg.dgmattribs.Get(const.attributeFalloffBonus).iconID)
        optimalBonus = self.GetAttributeValue(itemID, const.attributeMaxRangeBonus)
        text = GetByLabel('UI/Inflight/ModuleRacks/Tooltips/TrackingComputerRangeBonus', optimalRangeBonus=optimalBonus)
        self.AddSpecificInfoContainer(text, 'trackingComputerOptimalRangeCont', iconID=cfg.dgmattribs.Get(const.attributeMaxRangeBonus).iconID)
        tracking = self.GetAttributeValue(itemID, const.attributeTrackingSpeedBonus)
        text = GetByLabel('UI/Inflight/ModuleRacks/Tooltips/TrackingComputerTrackingBonus', trackingSpeedBonus=tracking)
        self.AddSpecificInfoContainer(text, 'trackingComputerTrackingSpeedCont', iconID=cfg.dgmattribs.Get(const.attributeTrackingSpeedBonus).iconID)

    def AddSmartBombInfo(self, itemID, *args):
        attrID = None
        damage = 0
        for attributeID in (const.attributeEmDamage,
         const.attributeKineticDamage,
         const.attributeThermalDamage,
         const.attributeExplosiveDamage):
            damage = self.GetAttributeValue(itemID, attributeID)
            if damage > 0:
                attrID = attributeID
                break

        attributeInfo = cfg.dgmattribs.Get(attrID)
        damageType = attributeInfo.displayName
        iconID = attributeInfo.iconID
        text = GetByLabel('UI/Inflight/ModuleRacks/Tooltips/SmartBombDamage', amount=damage, damageType=damageType)
        self.AddSpecificInfoContainer(text, 'smortBombAmountCont', iconID=iconID)

    def AddPropulsionModuleInfo(self, itemID, *args):
        myShip = GetActiveShip()
        myMaxVelocity = self.dogmaLocation.GetAttributeValue(myShip, const.attributeMaxVelocity)
        speedFactor = self.GetAttributeValue(itemID, const.attributeSpeedFactor)
        speedBoostFactor = self.GetAttributeValue(itemID, const.attributeSpeedBoostFactor)
        mass = self.dogmaLocation.GetAttributeValue(myShip, const.attributeMass)
        massAddition = self.dogmaLocation.GetAttributeValue(itemID, const.attributeMassAddition)
        maxVelocityWithBonus = myMaxVelocity * (1 + speedBoostFactor * speedFactor * 0.01 / (massAddition + mass))
        text = GetByLabel('UI/Inflight/ModuleRacks/Tooltips/MaxVelocityWithAndWithoutPropulsion', maxVelocity=myMaxVelocity, maxVelocityWithBonus=maxVelocityWithBonus)
        self.AddSpecificInfoContainer(text, 'propulsionModuleAmountCont', iconID=cfg.dgmattribs.Get(const.attributeMaxVelocity).iconID)

    def AddStasisWebInfo(self, itemID, *args):
        amount = self.GetAttributeValue(itemID, const.attributeSpeedFactor)
        text = GetByLabel('UI/Inflight/ModuleRacks/Tooltips/VelocityReductionFromWeb', percentage=abs(amount))
        self.AddSpecificInfoContainer(text, 'stasisWebAmountCont', iconID=cfg.dgmattribs.Get(const.attributeMaxVelocity).iconID)

    def AddCapacitorBoosterInfo(self, itemID, chargeInfoItem, *args):
        """
            cannot use GetAmountPerTimeInfo() for cap boosters because the amount info comes from the charge, not the module
        """
        duration = self.GetDuration(itemID)
        if chargeInfoItem is None:
            return
        amount = self.GetAttributeValue(chargeInfoItem.itemID, const.attributeCapacitorBonus)
        text = GetByLabel('UI/Inflight/ModuleRacks/Tooltips/CapacitorBoostPerTime', boostAmount=amount, duration=duration)
        self.AddSpecificInfoContainer(text, 'capacitorBoosterAmountCont', iconID=cfg.dgmattribs.Get(const.attributeCapacitorBonus).iconID)

    def AddEnergyTransferArrayInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributePowerTransferAmount, configName='energyTransferArrayAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/EnergyTransferredPerTime')

    def AddShieldTransporterInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeShieldBonus, configName='shieldTransporterAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/ShieldTransportedPerTime')

    def AddArmorRepairProjectorInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeArmorDamageAmount, configName='armorRepairProjectorAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/ArmorTransferredPerTime')

    def AddRemoteHullRepairInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeStructureDamageAmount, configName='remoteHullRepairAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/HullRemoteRepairedPerTime')

    def AddWarpScramblerInfo(self, itemID, *args):
        strength = self.GetAttributeValue(itemID, const.attributeWarpScrambleStrength)
        text = GetByLabel('UI/Inflight/ModuleRacks/Tooltips/WarpScramblerStrength', strength=strength)
        self.AddSpecificInfoContainer(text, 'warpScramblerAmountCont', iconID=cfg.dgmattribs.Get(const.attributeWarpScrambleStrength).iconID)

    def AddArmorHardenerInfo(self, itemID, *args):
        damageTypeAttributes = [(const.attributeEmDamageResistanceBonus, None),
         (const.attributeExplosiveDamageResistanceBonus, None),
         (const.attributeKineticDamageResistanceBonus, None),
         (const.attributeThermalDamageResistanceBonus, None)]
        textDict = {'noPassiveValue': 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues',
         'manyHeaderWithoutPassive': 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusesHeader',
         'oneDamageTypeWithoutPassive': 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText'}
        self.GetDamageTypeInfo(itemID, damageTypeAttributes, textDict)

    def AddECMInfo(self, itemID, *args):
        damageTypeAttributes = [const.attributeScanGravimetricStrengthBonus,
         const.attributeScanLadarStrengthBonus,
         const.attributeScanMagnetometricStrengthBonus,
         const.attributeScanRadarStrengthBonus]
        rows = []
        for attrID in damageTypeAttributes:
            strength = self.GetAttributeValue(itemID, attrID)
            if strength is not None and strength != 0:
                attributeName = cfg.dgmattribs.Get(attrID).displayName
                rows.append(GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ECMStrengthBonus', strength=strength, attributeName=attributeName))

        text = '<br>'.join(rows)
        self.AddSpecificInfoContainer(text, 'ecmInfoCont', iconID=None)

    def AddECCMInfo(self, itemID, *args):
        damageTypeAttributes = [const.attributeScanGravimetricStrengthPercent,
         const.attributeScanLadarStrengthPercent,
         const.attributeScanMagnetometricStrengthPercent,
         const.attributeScanRadarStrengthPercent]
        rows = []
        for attrID in damageTypeAttributes:
            strength = self.GetAttributeValue(itemID, attrID)
            if strength is not None and strength != 0:
                attributeName = cfg.dgmattribs.Get(attrID).displayName
                rows.append(GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=strength, activeName=attributeName))

        text = '<br>'.join(rows)
        self.AddSpecificInfoContainer(text, 'eccmInfoCont', iconID=cfg.invgroups.Get(const.groupElectronicCounterCounterMeasures).iconID)

    def AddSensorDamperInfo(self, itemID, *args):
        bonus = self.GetAttributeValue(itemID, const.attributeScanResolutionBonus)
        if bonus != 0:
            attributeName = cfg.dgmattribs.Get(const.attributeScanResolutionBonus).displayName
            self.AddSpecificInfoContainer(GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=bonus, activeName=attributeName), 'trackingDisruptorTrackingSpeedBonusCont', iconID=cfg.dgmattribs.Get(const.attributeScanResolutionBonus).iconID)
        bonus = self.GetAttributeValue(itemID, const.attributeMaxTargetRangeBonus)
        if bonus != 0:
            attributeName = cfg.dgmattribs.Get(const.attributeMaxTargetRangeBonus).displayName
            self.AddSpecificInfoContainer(GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=bonus, activeName=attributeName), 'trackingDisruptorMaxRangeBonusCont', iconID=cfg.dgmattribs.Get(const.attributeMaxTargetRangeBonus).iconID)

    def AddTargetBreakerInfo(self, itemID, *args):
        strength = self.GetAttributeValue(itemID, const.attributeScanResolutionMultiplier)
        strength = self.ConvertInversedModifierPercent(strength)
        attributeName = cfg.dgmattribs.Get(const.attributeScanResolutionBonus).displayName
        self.AddSpecificInfoContainer(GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=strength, activeName=attributeName), 'targetBreakerInfoCont', iconID=cfg.dgmattribs.Get(const.attributeScanResolutionBonus).iconID)

    def AddTargetPainterInfo(self, itemID, *args):
        sigRadiusBonus = self.GetAttributeValue(itemID, const.attributeSignatureRadiusBonus)
        attributeName = cfg.dgmattribs.Get(const.attributeSignatureRadiusBonus).displayName
        self.AddSpecificInfoContainer(GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=sigRadiusBonus, activeName=attributeName), 'targetPainterSigRadiusCont', iconID=cfg.dgmattribs.Get(const.attributeSignatureRadiusBonus).iconID)

    def AddTrackingDisruptorInfo(self, itemID, *args):
        falloffBonus = self.GetAttributeValue(itemID, const.attributeFalloffBonus)
        attributeName = cfg.dgmattribs.Get(const.attributeFalloffBonus).displayName
        self.AddSpecificInfoContainer(GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=falloffBonus, activeName=attributeName), 'trackingDisruptorFalloffBonusCont', iconID=cfg.dgmattribs.Get(const.attributeFalloffBonus).iconID)
        trackingSpeedBonus = self.GetAttributeValue(itemID, const.attributeTrackingSpeedBonus)
        if trackingSpeedBonus != 0:
            attributeName = cfg.dgmattribs.Get(const.attributeTrackingSpeedBonus).displayName
            self.AddSpecificInfoContainer(GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=trackingSpeedBonus, activeName=attributeName), 'trackingDisruptorTrackingSpeedBonusCont', iconID=cfg.dgmattribs.Get(const.attributeTrackingSpeedBonus).iconID)
        maxRangeBonus = self.GetAttributeValue(itemID, const.attributeMaxRangeBonus)
        if maxRangeBonus != 0:
            attributeName = cfg.dgmattribs.Get(const.attributeMaxRangeBonus).displayName
            self.AddSpecificInfoContainer(GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=maxRangeBonus, activeName=attributeName), 'trackingDisruptorMaxRangeBonusCont', iconID=cfg.dgmattribs.Get(const.attributeMaxRangeBonus).iconID)

    def AddCloakingDeviceInfo(self, itemID, *args):
        bonus = self.GetAttributeValue(itemID, const.attributeMaxVelocityBonus)
        bonus = self.ConvertInversedModifierPercent(bonus)
        attributeName = cfg.dgmattribs.Get(const.attributeMaxVelocityBonus).displayName
        self.AddSpecificInfoContainer(GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=bonus, activeName=attributeName), 'trackingDisruptorFalloffBonusCont', iconID=cfg.dgmattribs.Get(const.attributeMaxVelocityBonus).iconID)

    def AddTractorBeamInfo(self, itemID, *args):
        maxTractorVel = self.GetAttributeValue(itemID, const.attributeMaxTractorVelocity)
        attributeName = cfg.dgmattribs.Get(const.attributeMaxTractorVelocity).displayName
        self.AddSpecificInfoContainer(GetByLabel('UI/Inflight/ModuleRacks/Tooltips/TractorBeamTractorVelocity', maxTractorVel=maxTractorVel, attributeName=attributeName), 'trackingDisruptorFalloffBonusCont', iconID=cfg.dgmattribs.Get(const.attributeMaxTractorVelocity).iconID)

    def AddDamageControlInfo(self, itemID, *args):
        damageTypeAttributes = [const.attributeShieldEmDamageResonance,
         const.attributeShieldExplosiveDamageResonance,
         const.attributeShieldKineticDamageResonance,
         const.attributeShieldThermalDamageResonance]
        self.AddDamageControlInfoRow(itemID, damageTypeAttributes, 'UI/Inflight/ModuleRacks/Tooltips/ShieldDamageResistanceHeader', 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues', 'Shield')
        damageTypeAttributes = [const.attributeArmorEmDamageResonance,
         const.attributeArmorExplosiveDamageResonance,
         const.attributeArmorKineticDamageResonance,
         const.attributeArmorThermalDamageResonance]
        self.AddDamageControlInfoRow(itemID, damageTypeAttributes, 'UI/Inflight/ModuleRacks/Tooltips/ArmorDamageResistanceHeader', 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues', 'Armor')
        damageTypeAttributes = [const.attributeHullEmDamageResonance,
         const.attributeHullExplosiveDamageResonance,
         const.attributeHullKineticDamageResonance,
         const.attributeHullThermalDamageResonance]
        self.AddDamageControlInfoRow(itemID, damageTypeAttributes, 'UI/Inflight/ModuleRacks/Tooltips/HullDamageResistanceHeader', 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues', 'Hull')

    def AddDamageControlInfoRow(self, itemID, damageTypeAttributes, headerText, rowText, containerName, *args):
        headerText = GetByLabel(headerText)
        allDamageTypeInfo = []
        for damageTypeAttr in damageTypeAttributes:
            attributeValue = self.GetAttributeValue(itemID, damageTypeAttr)
            attributeValue = self.ConvertInverseAbsolutePercent(attributeValue)
            allDamageTypeInfo.append((damageTypeAttr, GetByLabel(rowText, activeValue=attributeValue)))

        containerName = 'damageControlContainer' + containerName
        damageTypeContMany = getattr(self, containerName, None)
        if damageTypeContMany is None or damageTypeContMany.destroyed:
            damageTypeContMany = ModuleButtonHintContainerIcons(parent=self, name=containerName, align=uiconst.TOTOP, isExtraInfoContainer=True, headerText=headerText)
            setattr(self, containerName, damageTypeContMany)
        damageTypeContMany.SetDamageTypeInfo(allDamageTypeInfo)
        damageTypeContMany.SetContainerHeight()

    def AddArmorResistanceShiftHardenerInfo(self, itemID, *args):
        damageTypeAttributes = [const.attributeArmorEmDamageResonance,
         const.attributeArmorExplosiveDamageResonance,
         const.attributeArmorKineticDamageResonance,
         const.attributeArmorThermalDamageResonance]
        self.AddDamageControlInfoRow(itemID, damageTypeAttributes, 'UI/Inflight/ModuleRacks/Tooltips/ArmorDamageResistanceHeader', 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues', 'Armor')

    def AddSuperWeaponInfo(self, itemID, *args):
        damageTypeAttributes = [const.attributeEmDamage,
         const.attributeExplosiveDamage,
         const.attributeKineticDamage,
         const.attributeThermalDamage]
        for damageType in damageTypeAttributes:
            damage = self.GetAttributeValue(itemID, damageType)
            if damage == 0:
                continue
            attributeName = cfg.dgmattribs.Get(damageType).displayName
            text = GetByLabel('UI/Inflight/ModuleRacks/Tooltips/SuperWeaponDamage', activeValue=damage, activeName=attributeName)
            self.AddSpecificInfoContainer(text, 'superWeaponInfoCont' + attributeName, iconID=cfg.dgmattribs.Get(damageType).iconID)

    def AddGangCoordinatorInfo(self, itemID, *args):
        commandBonus = self.GetAttributeValue(itemID, const.attributeCommandbonus)
        if commandBonus != 0:
            displayName = cfg.dgmattribs.Get(const.attributeCommandbonus).displayName
            text = GetByLabel('UI/Inflight/ModuleRacks/Tooltips/GangCoordinatorCommandBonus', commandBonus=commandBonus, attributeName=displayName)
            self.AddSpecificInfoContainer(text, 'gangCoordInfoContCommand', iconID=cfg.dgmattribs.Get(const.attributeCommandbonus).iconID)
        maxGangModulesAttr = cfg.dgmattribs.Get(const.attributeMaxGangModules)
        if maxGangModulesAttr.attributeName in self.stateManager.GetAttributes(itemID):
            maxGangModules = self.GetAttributeValue(itemID, const.attributeMaxGangModules)
            displayName = maxGangModulesAttr.displayName
            text = GetByLabel('UI/Inflight/ModuleRacks/Tooltips/GangCoordinatorMaxCommandRelays', maxGangModules=maxGangModules, attributeName=displayName)
            self.AddSpecificInfoContainer(text, 'gangCoordInfoContMaxGangModules', iconID=cfg.dgmattribs.Get(const.attributeMaxGangModules).iconID)

    def ConvertInverseAbsolutePercent(self, value):
        return (1.0 - value) * 100.0

    def ConvertInversedModifierPercent(self, value):
        return -(1.0 - value) * 100.0

    def GetDamageTypeInfo(self, itemID, damageTypeAttributes, textDict, multiplier = None, *args):
        if multiplier is None:
            multiplier = 1
        allDamageTypeInfo, effectiveDamageTypes, withPassiveValues = self.GetDamageTypeAttributeInfo(itemID, damageTypeAttributes, textDict, multiplier)
        damageTypeContMany = getattr(self, 'damageTypeContMany', None)
        damagaTypeContOne = getattr(self, 'damagaTypeContOne', None)
        if len(effectiveDamageTypes) > 1:
            if damagaTypeContOne is not None and not damagaTypeContOne.destroyed:
                damagaTypeContOne.Close()
            headerText = self.GetDamageText('manyHeader', textDict, hasPassive=withPassiveValues)
            if damageTypeContMany is None or damageTypeContMany.destroyed:
                damageTypeContMany = ModuleButtonHintContainerIcons(parent=self, name='damageTypeContMany', align=uiconst.TOTOP, isExtraInfoContainer=True, headerText=headerText)
                self.damageTypeContMany = damageTypeContMany
            damageTypeContMany.SetDamageTypeInfo(allDamageTypeInfo)
            damageTypeContMany.SetContainerHeight()
        elif len(effectiveDamageTypes) == 1:
            if damageTypeContMany is not None:
                damageTypeContMany.Close()
            activeAttributeID, activeValue, passiveAttributeID, passiveValue = effectiveDamageTypes[0]
            text = self.GetDamageText('oneDamageType', textDict, activeAttributeID, activeValue, passiveAttributeID, passiveValue, multiplier=multiplier, hasPassive=withPassiveValues)
            self.AddSpecificInfoContainer(text, 'damagaTypeContOne', iconID=cfg.dgmattribs.Get(activeAttributeID).iconID)

    def GetDamageTypeAttributeInfo(self, itemID, damageTypeAttributes, textDict, multiplier, *args):
        effectiveDamageTypes = []
        allDamageTypeInfo = []
        withPassiveValues = False
        for activeAttributeID, passiveAttributeID in damageTypeAttributes:
            activeValue = self.GetAttributeValue(itemID, activeAttributeID)
            if passiveAttributeID:
                passiveValue = self.GetAttributeValue(itemID, passiveAttributeID)
                withPassiveValues = True
            else:
                passiveValue = 0
            text = self.GetDamageText('value', textDict, activeAttributeID, activeValue, passiveAttributeID, passiveValue, multiplier=multiplier)
            if text:
                effectiveDamageTypes.append((activeAttributeID,
                 activeValue,
                 passiveAttributeID,
                 passiveValue))
            allDamageTypeInfo.append((activeAttributeID, text))

        return (allDamageTypeInfo, effectiveDamageTypes, withPassiveValues)

    def GetDamageText(self, textTypeToGet, textDict, activeAttributeID = None, activeValue = None, passiveAttributeID = None, passiveValue = None, hasPassive = True, multiplier = 1, *args):
        if textTypeToGet == 'value':
            if activeValue == 0 and passiveValue == 0:
                return ''
            elif passiveValue == 0:
                return GetByLabel(textDict['noPassiveValue'], activeValue=multiplier * activeValue)
            else:
                return GetByLabel(textDict['activeAndPassiveValues'], activeValue=multiplier * activeValue, passiveValue=multiplier * passiveValue)
        elif textTypeToGet == 'manyHeader':
            if hasPassive:
                return GetByLabel(textDict['manyHeaderWithPassive'])
            else:
                return GetByLabel(textDict['manyHeaderWithoutPassive'])
        elif textTypeToGet == 'oneDamageType':
            if hasPassive:
                return GetByLabel(textDict['oneDamageTypeWithPassive'], activeName=cfg.dgmattribs.Get(activeAttributeID).displayName, passiveName=cfg.dgmattribs.Get(passiveAttributeID).displayName, activeValue=multiplier * activeValue, passiveValue=passiveValue)
            else:
                return GetByLabel(textDict['oneDamageTypeWithoutPassive'], activeName=cfg.dgmattribs.Get(activeAttributeID).displayName, activeValue=multiplier * activeValue)
        return ''

    def FadeOpacity(self, toOpacity):
        if toOpacity == getattr(self, '_settingOpacity', None):
            return
        self._newOpacity = toOpacity
        self._settingOpacity = toOpacity
        worker('ModuleButtonHint::FadeOpacity', self.FadeOpacityThread, toOpacity)

    def FadeOpacityThread(self, toOpacity):
        self._newOpacity = None
        ndt = 0.0
        start = blue.os.GetWallclockTime()
        startOpacity = self.opacity
        while ndt != 1.0:
            ndt = min(float(blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime())) / float(250.0), 1.0)
            self.opacity = min(1.0, max(0.0, Lerp(startOpacity, toOpacity, ndt)))
            if toOpacity == 1.0:
                self.Show()
            blue.pyos.synchro.Yield()
            if self._newOpacity:
                return

        if toOpacity == 0.0:
            self.Hide()


class ModuleButtonHintContainerBase(Container):
    __guid__ = 'uicls.ModuleButtonHintContainerBase'
    default_state = uiconst.UI_DISABLED
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        self.iconSize = 26
        Container.ApplyAttributes(self, attributes)
        self.moduleTypeID = attributes.typeID
        self.iconCont = Container(parent=self, name='iconCont', align=uiconst.TOLEFT, width=self.iconSize, padLeft=const.defaultPadding)
        self.textCont = Container(parent=self, name='textCont', align=uiconst.TOALL)
        self.icon = Icon(parent=self.iconCont, name='icon', align=uiconst.CENTER, size=self.iconSize, ignoreSize=True)
        self.textLabel = EveLabelMedium(text='', parent=self.textCont, name='textLabel', align=uiconst.CENTERLEFT, left=8)
        self.isExtraInfoContainer = attributes.get('isExtraInfoContainer', False)
        if attributes.iconID:
            self.LoadIconByIconID(attributes.iconID)
        elif attributes.texturePath:
            self.SetIconPath(attributes.texturePath)
        self.smallContainerHeight = attributes.get('smallContainerHeight', 30)
        self.bigContainerHeight = attributes.get('bigContainerHeight', 36)

    def SetIconPath(self, texturePath):
        self.icon.LoadTexture(texturePath)

    def LoadIconByIconID(self, iconID):
        self.icon.LoadIcon(iconID, ignoreSize=True)

    def SetContainerHeight(self, *args):
        textHeight = self.textLabel.textheight
        if textHeight < self.smallContainerHeight - 2:
            self.height = self.smallContainerHeight
        elif textHeight < self.bigContainerHeight - 2:
            self.height = self.bigContainerHeight
        else:
            self.height = textHeight + 2

    def GetContainerWidth(self, *args):
        if self.display == True:
            myWidth = self.textLabel.textwidth + self.textLabel.left + self.iconCont.width + self.iconCont.left
            return myWidth
        return 0


class ModuleButtonHintContainerSafetyLevel(ModuleButtonHintContainerBase):
    __guid__ = 'uicls.ModuleButtonHintContainerSafetyLevel'

    def ApplyAttributes(self, attributes):
        attributes.texturePath = 'res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal.png'
        ModuleButtonHintContainerBase.ApplyAttributes(self, attributes)
        self.icon.width = self.icon.height = 16

    def SetSafetyLevelWarning(self, safetyLevel):
        if safetyLevel == const.shipSafetyLevelNone:
            self.icon.color.SetRGBA(*CrimeWatchColors.Criminal.GetRGBA())
            self.textLabel.text = GetByLabel('UI/Crimewatch/SafetyLevel/ModuleRestrictionTooltip', color=CrimeWatchColors.Criminal.GetHex())
        else:
            self.icon.color.SetRGBA(*CrimeWatchColors.Suspect.GetRGBA())
            self.textLabel.text = GetByLabel('UI/Crimewatch/SafetyLevel/ModuleRestrictionTooltip', color=CrimeWatchColors.Suspect.GetHex())


class ModuleButtonHintContainerType(ModuleButtonHintContainerBase):
    __guid__ = 'uicls.ModuleButtonHintContainerType'

    def ApplyAttributes(self, attributes):
        ModuleButtonHintContainerBase.ApplyAttributes(self, attributes)
        self.techIcon = Icon(parent=self.iconCont, width=16, height=16, align=uiconst.TOPLEFT, idx=0, top=4)

    def SetTypeIcon(self, typeID = None, iconSize = 26):
        self.icon.LoadIconByTypeID(typeID, size=self.iconSize, ignoreSize=True)
        GetTechLevelIcon(self.techIcon, typeID=typeID)

    def SetTypeTextAndDamage(self, typeName, damage, numSlaves, bold = True):
        if numSlaves:
            typeText = GetByLabel('UI/Inflight/ModuleRacks/TypeNameWithNumInGroup', numInGroup=numSlaves, typeName=typeName)
        else:
            typeText = typeName
        if bold:
            typeText = '<b>%s</b>' % typeText
        self.textLabel.text = typeText
        if damage > 0:
            damagedText = GetByLabel('UI/Inflight/ModuleRacks/ModuleDamaged', color='<color=red>', percentageNum=damage)
            self.textLabel.text += '<br>' + damagedText
            if getattr(self, 'shortcutText', None) is not None:
                self.shortcutText.text += '<br>'

    def AddFading(self, parentWidth, *args):
        availableTextWidth = parentWidth - self.icon.width - self.textLabel.left
        self.textLabel.SetRightAlphaFade(fadeEnd=availableTextWidth, maxFadeWidth=20)


class ModuleButtonHintContainerTypeWithShortcut(ModuleButtonHintContainerType):
    __guid__ = 'uicls.ModuleButtonHintContainerTypeWithShortcut'

    def ApplyAttributes(self, attributes):
        ModuleButtonHintContainerType.ApplyAttributes(self, attributes)
        self.shortcutCont = Container(parent=self, name='shortcutCont', align=uiconst.TORIGHT, width=32, state=uiconst.UI_HIDDEN)
        self.shortcutText = EveLabelMedium(text='', parent=self.shortcutCont, name='shortcutText', align=uiconst.CENTERRIGHT, left=8)
        self.shortcutCont.textLabel = self.shortcutText
        self.shortcutPadding = 0

    def SetShortcutText(self, moduleShortcut):
        self.shortcutPadding = 0
        if moduleShortcut:
            self.shortcutText.text = GetByLabel('UI/Inflight/ModuleRacks/HintShortcut', shotcutString=moduleShortcut)
            self.shortcutCont.display = True
            self.shortcutCont.width = self.shortcutText.textwidth + 14
            shortcutPadding = self.shortcutCont.width + 10
        else:
            self.shortcutText.text = ''
            self.shortcutCont.display = False
        self.shortcutPadding = shortcutPadding

    def GetContainerWidth(self, *args):
        myWidth = ModuleButtonHintContainerType.GetContainerWidth(self)
        myWidth += self.shortcutPadding
        return myWidth

    def AddFading(self, parentWidth, *args):
        availableTextWidth = parentWidth - self.icon.width - self.textLabel.left - self.shortcutPadding
        self.textLabel.SetRightAlphaFade(fadeEnd=availableTextWidth, maxFadeWidth=20)


class ModuleButtonHintContainerIcons(Container):
    __guid__ = 'uicls.ModuleButtonHintContainerIcons'
    default_state = uiconst.UI_DISABLED

    def ApplyAttributes(self, attributes):
        self.iconSize = 26
        Container.ApplyAttributes(self, attributes)
        self.moduleTypeID = attributes.typeID
        self.textLabel = EveLabelMedium(text='', parent=self, name='textLabel', align=uiconst.TOTOP, padTop=const.defaultPadding, padLeft=self.iconSize + 3 * const.defaultPadding, maxLines=1)
        self.allIconCont = Container(parent=self, name='allIconCont', align=uiconst.TOTOP, height=30)
        self.isExtraInfoContainer = attributes.get('isExtraInfoContainer', False)
        self.textLabel.text = attributes.headerText

    def SetDamageTypeInfo(self, damageTypeInfo):
        for each in damageTypeInfo:
            attributeID, text = each
            self.SetText(attributeID, text)

    def SetText(self, attributeID, text):
        if text == '':
            cont = self.FindDamageTypeContainer(attributeID)
            if cont:
                cont.display = False
            return
        damageTypeContainer = self.GetDamageTypeContainer(attributeID)
        damageTypeContainer.textLabel.text = text
        damageTypeContainer.width = max(64, damageTypeContainer.textLabel.textwidth + self.iconSize + 10)
        damageTypeContainer.display = True

    def FindDamageTypeContainer(self, attributeID, *args):
        myContainerName = 'damageTypeCont_%s' % attributeID
        return getattr(self, myContainerName, None)

    def GetDamageTypeContainer(self, attributeID, *args):
        myContainer = self.FindDamageTypeContainer(attributeID)
        if not myContainer or myContainer.destroyed:
            myContainerName = 'damageTypeCont_%s' % attributeID
            myContainer = Container(parent=self.allIconCont, name=myContainerName, align=uiconst.TOLEFT, width=64)
            setattr(self, myContainerName, myContainer)
            attributeInfo = cfg.dgmattribs.Get(attributeID)
            iconID = attributeInfo.iconID
            icon = Icon(parent=myContainer, name='icon', align=uiconst.CENTERLEFT, size=self.iconSize, ignoreSize=True)
            icon.LoadIcon(iconID, ignoreSize=True)
            myContainer.icon = icon
            textLabel = EveLabelMedium(text='', parent=myContainer, name='textLabel', align=uiconst.CENTERLEFT, left=self.iconSize)
            myContainer.textLabel = textLabel
        return myContainer

    def SetContainerHeight(self, *args):
        self.height = self.textLabel.textheight + self.allIconCont.height + self.allIconCont.padTop + 2 * const.defaultPadding

    def GetContainerWidth(self, *args):
        textWidth = self.textLabel.textwidth + self.textLabel.padLeft
        visibleIconsWidths = [ child.width for child in self.allIconCont.children if child.display == True ]
        myWidth = max(textWidth, sum(visibleIconsWidths))
        return myWidth
