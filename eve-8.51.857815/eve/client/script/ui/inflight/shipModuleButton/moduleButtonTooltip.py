#Embedded file name: eve/client/script/ui/inflight/shipModuleButton\moduleButtonTooltip.py
"""
The UI code for the ship module hints
"""
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from carbon.common.script.util.timerstuff import AutoTimer
from eve.client.script.ui.control.tooltips import TooltipPanel, ShortcutHint
from eve.client.script.ui.crimewatch.crimewatchConst import Colors as CrimeWatchColors
import math
from carbon.common.script.util.format import FmtDist
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.inflight.shipModuleButton.attributeValueRowContainer import AttributeValueRowContainer
from eve.client.script.ui.tooltips.tooltipsWrappers import TooltipBaseWrapper
from eve.client.script.ui.util.uix import GetTechLevelIcon
from eve.common.script.sys.eveCfg import GetActiveShip
import localization
RESISTANCE_BONUS_ATTRIBUTES = [const.attributeEmDamageResistanceBonus,
 const.attributeExplosiveDamageResistanceBonus,
 const.attributeKineticDamageResistanceBonus,
 const.attributeThermalDamageResistanceBonus]

class TooltipModuleWrapper(TooltipBaseWrapper):

    def CreateTooltip(self, parent, owner, idx):
        self.tooltipPanel = ModuleButtonTooltip(parent=parent, owner=owner, idx=idx)
        return self.tooltipPanel


class ModuleButtonTooltip(TooltipPanel):
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
        TooltipPanel.ApplyAttributes(self, attributes)
        self.stateManager = sm.StartService('godma').GetStateManager()
        self.dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        self.columns = 4
        self.margin = (4, 4, 4, 4)
        self.cellPadding = 0
        self.cellSpacing = 0
        self.labelPadding = (4, 2, 4, 2)
        self.SetBackgroundAlpha(0.75)

    def LoadTooltip(self):
        if not self.owner:
            return
        self.ownerGuid = self.owner.__guid__
        if self.ownerGuid == 'xtriui.ModuleButton':
            self.moduleItemID = self.owner.sr.moduleInfo.itemID
        else:
            self.moduleItemID = self.owner.id
        if not self.moduleItemID:
            return
        self.moduleInfoItem = self.dogmaLocation.GetDogmaItem(self.moduleItemID)
        self.moduleGroup = cfg.invtypes.Get(self.moduleInfoItem.typeID).Group()
        self.numSlaves = self.GetNumberOfSlaves(self.moduleInfoItem, self.ownerGuid)
        if self.stateManager.GetDefaultEffect(self.moduleInfoItem.typeID):
            self.moduleShortcut = self.GetModuleShortcut(self.moduleInfoItem)
        else:
            self.moduleShortcut = None
        self.typeName = cfg.invtypes.Get(self.moduleInfoItem.typeID).name
        self.onHUDModuleButton = self.ownerGuid == 'xtriui.ModuleButton'
        self.UpdateToolTips()
        self._toolTooltipUpdateTimer = AutoTimer(1000, self.UpdateToolTips)

    def UpdateToolTips(self):
        if self.destroyed or self.beingDestroyed or self.owner is None:
            self._toolTooltipUpdateTimer = None
            return
        self.Flush()
        if self.owner.charge:
            chargeItemID = self.owner.charge.itemID
        else:
            chargeItemID = None
        if chargeItemID is None:
            chargeInfoItem = None
        else:
            chargeInfoItem = self.dogmaLocation.GetDogmaItem(chargeItemID)
        moduleDamageAmount = self.GetModuleDamage(self.ownerGuid, self.moduleItemID)
        chargesType, chargesQty = self.GetChargeTypeAndQty(self.moduleInfoItem, chargeInfoItem)
        if self.numSlaves:
            typeText = localization.GetByLabel('UI/Inflight/ModuleRacks/TypeNameWithNumInGroup', numInGroup=self.numSlaves, typeName=self.typeName)
        else:
            typeText = self.typeName
        typeText = '<b>%s</b>' % typeText
        self.AddTypeAndIcon(label=typeText, typeID=self.moduleInfoItem.typeID, moduleShortcut=self.moduleShortcut, moduleDamageAmount=moduleDamageAmount)
        self.UpdateChargesCont(chargeInfoItem, chargesQty)
        maxRange, falloffDist, bombRadius = sm.GetService('tactical').FindMaxRange(self.moduleInfoItem, chargeInfoItem)
        if maxRange > 0:
            self.AddRangeInfo(self.moduleInfoItem.typeID, optimalRange=maxRange, falloff=falloffDist)
        if chargesQty is not None:
            self.AddDpsAndDamgeTypeInfo(self.moduleItemID, self.moduleInfoItem.typeID, self.moduleGroup.groupID, chargeInfoItem, self.numSlaves)
        myInfoFunctionName = self.infoFunctionNames.get(self.moduleGroup.groupID, None)
        if myInfoFunctionName is not None:
            myInfoFunction = getattr(self, myInfoFunctionName)
            myInfoFunction(self.moduleItemID, chargeInfoItem)
        if self.onHUDModuleButton:
            safetyLevel = self.owner.GetSafetyWarning()
            if safetyLevel is not None:
                self.AddSafetyLevelWarning(safetyLevel)

    def UpdateChargesCont(self, chargeInfoItem, chargesQty):
        if chargeInfoItem and chargesQty:
            chargeText = self.GetChargeText(chargeInfoItem, chargesQty)
            self.AddTypeAndIcon(label=chargeText, typeID=chargeInfoItem.typeID)

    def GetChargeText(self, chargeInfoItem, chargesQty):
        if chargeInfoItem.groupID in cfg.GetCrystalGroups():
            crystalDamageAmount = self.GetCrystalDamage(chargeInfoItem)
            chargeText = '<b>%s</b>' % cfg.invtypes.Get(chargeInfoItem.typeID).name
            if crystalDamageAmount > 0.0:
                damagedText = localization.GetByLabel('UI/Inflight/ModuleRacks/AmmoDamaged', color='<color=red>', damage=crystalDamageAmount)
                chargeText += '<br>' + damagedText
        else:
            chargeText = localization.GetByLabel('UI/Inflight/ModuleRacks/AmmoNameWithQty', qty=chargesQty, ammoTypeID=chargeInfoItem.typeID)
        return chargeText

    def GetModuleDamage(self, ownerGuid, moduleItemID):
        if ownerGuid == 'xtriui.FittingSlot':
            damage = self.dogmaLocation.GetAccurateAttributeValue(moduleItemID, const.attributeDamage)
        else:
            damage = uicore.layer.shipui.GetModuleGroupDamage(moduleItemID)
        if damage:
            moduleDamageAmount = int(math.ceil(damage / self.dogmaLocation.GetAttributeValue(moduleItemID, const.attributeHp) * 100))
        else:
            moduleDamageAmount = 0.0
        return moduleDamageAmount

    def GetCrystalDamage(self, chargeInfoItem):
        crystalDamageAmount = None
        if chargeInfoItem is not None:
            dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
            crystalDamageAmount = dogmaLocation.GetAccurateAttributeValue(chargeInfoItem.itemID, const.attributeDamage)
        return crystalDamageAmount

    def GetNumberOfSlaves(self, moduleInfoItem, ownerGuid):
        myShip = GetActiveShip()
        if ownerGuid == 'xtriui.FittingSlot':
            return 0
        else:
            slaves = self.dogmaLocation.GetSlaveModules(moduleInfoItem.itemID, myShip)
            if slaves:
                numSlaves = len(slaves) + 1
            else:
                numSlaves = 0
            return numSlaves

    def GetModuleShortcut(self, moduleInfoItem):
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

    def IsChargeCompatible(self, moduleInfoItem):
        return moduleInfoItem.groupID in cfg.__chargecompatiblegroups__

    def GetEffectiveAttributeValue(self, itemID, attributeID):
        """
            Gets the attribute value to display in the hints.
            If the value needs to be inversed, it is done here.
        """
        attributeValue = sm.GetService('clientDogmaIM').GetDogmaLocation().GetAccurateAttributeValue(itemID, attributeID)
        attributeTypeInfo = cfg.dgmattribs.Get(attributeID)
        unitID = attributeTypeInfo.unitID
        if unitID in (const.unitInverseAbsolutePercent, const.unitInversedModifierPercent):
            attributeValue = (1.0 - attributeValue) * 100.0
        elif unitID == const.unitModifierPercent:
            attributeValue = -(1.0 - attributeValue) * 100.0
        return attributeValue

    def GetDuration(self, itemID):
        duration = self.GetEffectiveAttributeValue(itemID, const.attributeDuration)
        durationInSec = duration / 1000.0
        if durationInSec % 1.0 == 0:
            decimalPlaces = 0
        else:
            decimalPlaces = 1
        unit = cfg.dgmunits.Get(const.unitMilliseconds).displayName
        durationFormatted = localization.formatters.FormatNumeric(durationInSec, decimalPlaces=decimalPlaces)
        formattedDuration = localization.GetByLabel('UI/InfoWindow/ValueAndUnit', value=durationFormatted, unit=unit)
        return formattedDuration

    def AddSafetyLevelWarning(self, safetyLevel):
        if safetyLevel == const.shipSafetyLevelNone:
            iconColor = CrimeWatchColors.Criminal.GetRGBA()
            text = localization.GetByLabel('UI/Crimewatch/SafetyLevel/ModuleRestrictionTooltip', color=CrimeWatchColors.Criminal.GetHex())
        else:
            iconColor = CrimeWatchColors.Suspect.GetRGBA()
            text = localization.GetByLabel('UI/Crimewatch/SafetyLevel/ModuleRestrictionTooltip', color=CrimeWatchColors.Suspect.GetHex())
        texturePath = 'res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal.png'
        icon, label = self.AddRowWithIconAndText(text, texturePath, iconSize=16)
        icon.color.SetRGBA(*iconColor)

    def AddTypeAndIcon(self, label, typeID, moduleShortcut = None, moduleDamageAmount = 0, iconSize = 26, minRowSize = 30):
        self.FillRow()
        self.AddSpacer(height=minRowSize, width=0)
        iconCont = Container(pos=(0,
         0,
         iconSize,
         iconSize), align=uiconst.CENTER)
        iconObj = Icon(parent=iconCont, pos=(0,
         0,
         iconSize,
         iconSize), align=uiconst.TOPLEFT, ignoreSize=True)
        iconObj.LoadIconByTypeID(typeID, size=iconSize, ignoreSize=True)
        techIcon = Icon(parent=iconCont, width=16, height=16, align=uiconst.TOPLEFT, idx=0, top=0)
        GetTechLevelIcon(techIcon, typeID=typeID)
        self.AddCell(iconCont, cellPadding=2)
        if moduleShortcut:
            nameColSpan = self.columns - 3
        else:
            nameColSpan = self.columns - 2
        if moduleDamageAmount > 0:
            damagedText = localization.GetByLabel('UI/Inflight/ModuleRacks/ModuleDamaged', color='<color=red>', percentageNum=moduleDamageAmount)
            label += '<br>' + damagedText
        labelObj = self.AddLabelMedium(text=label, align=uiconst.CENTERLEFT, cellPadding=self.labelPadding, colSpan=nameColSpan)
        if moduleShortcut:
            shortcutObj = ShortcutHint(text=moduleShortcut)
            shortcutObj.width += 10
            shortcutObj.padLeft = 10
            self.AddCell(shortcutObj)
        return (iconObj, labelObj)

    def AddAttributeRow(self, texturePath, attributeValues, minRowSize = 30, spacerWidth = 100):
        self.AddCell()
        self.AddCell()
        self.AddSpacer(colSpan=self.columns - 2, width=spacerWidth, height=0)
        self.FillRow()
        self.AddSpacer(width=0, height=minRowSize)
        self.AddIconCell(texturePath)
        container = AttributeValueRowContainer(attributeValues=attributeValues)
        self.AddCell(container, colSpan=self.columns - 2)
        self.FillRow()

    def AddRangeInfo(self, typeID, optimalRange, falloff):
        text, formattedOptimalRange = self.GetOptimalRangeText(typeID, optimalRange, falloff)
        if not text:
            return
        texturePath = 'res:/UI/Texture/Icons/22_32_15.png'
        self.AddRowWithIconAndText(text, texturePath)

    def GetOptimalRangeText(self, typeID, optimalRange, falloff):
        if optimalRange <= 0:
            return ('', '')
        formattedOptimalRAnge = FmtDist(optimalRange)
        if sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, const.effectLauncherFitted):
            rangeText = localization.GetByLabel('UI/Inflight/ModuleRacks/MaxRange', maxRange=formattedOptimalRAnge)
        elif sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, const.effectTurretFitted):
            if falloff > 1:
                rangeText = localization.GetByLabel('UI/Inflight/ModuleRacks/OptimalRangeAndFalloff', optimalRange=formattedOptimalRAnge, falloffPlusOptimal=FmtDist(falloff + optimalRange))
            else:
                rangeText = localization.GetByLabel('UI/Inflight/ModuleRacks/OptimalRange', optimalRange=formattedOptimalRAnge)
        elif cfg.invtypes.Get(typeID).Group().groupID == const.groupSmartBomb:
            rangeText = localization.GetByLabel('UI/Inflight/ModuleRacks/AreaOfEffect', range=formattedOptimalRAnge)
        elif falloff > 1:
            rangeText = localization.GetByLabel('UI/Inflight/ModuleRacks/RangeWithFalloff', optimalRange=formattedOptimalRAnge, falloffPlusOptimal=FmtDist(falloff + optimalRange))
        else:
            rangeText = localization.GetByLabel('UI/Inflight/ModuleRacks/Range', optimalRange=formattedOptimalRAnge)
        return (rangeText, formattedOptimalRAnge)

    def GetAmountPerTimeInfo(self, itemID, attributeID, labelPath):
        """
            This function adds a container where the info is "X amount per Y seconds".
            This function assumes the string the labelPath points to only has 2 keywords, amount and duration
            A lot of the modules are showing this info, using the attribute icon, but if some other icon
            is needed, or some special casing is needed, it's easy enough to build those containers
            (see AddMiningLaserInfo and AddSmartBombInfo)
        """
        duration = self.GetDuration(itemID)
        amount = self.GetEffectiveAttributeValue(itemID, attributeID)
        text = localization.GetByLabel(labelPath, duration=duration, amount=amount)
        return (text, duration, amount)

    def AddRowWithIconAndText(self, text, texturePath = None, iconID = None, iconSize = 24, minRowSize = 30):
        """
            adds a row in the tool tip that has a icon, followed by some text
        """
        self.FillRow()
        self.AddSpacer(height=minRowSize, width=0)
        icon = self.AddIconCell(texturePath or iconID, iconSize=iconSize)
        label = self.AddLabelMedium(text=text, colSpan=self.columns - 2, align=uiconst.CENTERLEFT, cellPadding=self.labelPadding)
        self.FillRow()
        return (icon, label)

    def AddRowWithIconAndTextAndValue(self, text, valueText, texturePath, iconSize = 24, minRowSize = 30):
        """
            adds a row in the tool tip that has a icon, followed by some text, and then the value
        """
        self.FillRow()
        self.AddSpacer(height=minRowSize, width=0)
        self.AddIconCell(texturePath, iconSize=iconSize)
        self.AddLabelMedium(text=text, colSpan=1, align=uiconst.CENTERLEFT, cellPadding=self.labelPadding)
        self.AddLabelMedium(text=valueText, align=uiconst.CENTERRIGHT)
        self.FillRow()

    def AddRowWithIconAndContainer(self, texturePath, container, iconSize = 24, minRowSize = 30):
        """
            adds a row that has icon, then any container that is sent in
        """
        self.FillRow()
        self.AddSpacer(height=minRowSize, width=0)
        self.AddIconCell(texturePath, iconSize=iconSize)
        self.AddCell(container, colSpan=self.columns - 1)

    def AddIconCell(self, texturePath = None, iconID = None, iconSize = 24):
        """
            adds a cell with a sprite
        """
        icon = Icon(pos=(0,
         0,
         iconSize,
         iconSize), align=uiconst.CENTER, ignoreSize=True, state=uiconst.UI_DISABLED, icon=texturePath or iconID)
        self.AddCell(icon)
        return icon

    def AddRowForInfoWithOneOrMoreAttributes(self, attributeValues, oneAttributeText, manyAttributesText, headerText, texturePath = ''):
        """
            Adds info for a set of attributes (for example damage/resistance type).
            If there i only 1 attributeValue sent in, a line will be added that spells it out
            If there is more than 1 attributeValue, a header is added followed by a row with icons and short value text
            for that attribute.
        """
        if len(attributeValues) == 1:
            self.AddRowForSingleAttribute(attributeValues=attributeValues, labelPath=oneAttributeText)
        elif attributeValues:
            self.AddRowAndHeaderForManyAttributes(attributeValues, manyAttributesText, headerText, texturePath)

    def AddRowForSingleAttribute(self, attributeValues, labelPath):
        """
            adds a row with an icon for the single attribute and text the spells out the value of the attribute and
            its name.
            The labelPath needs to have the tokesn 'activeName' and 'activeValue' for this to work as expected
        """
        attributeID, value = attributeValues[0]
        attributeName = cfg.dgmattribs.Get(attributeID).displayName
        text = localization.GetByLabel(labelPath, activeName=attributeName, activeValue=value)
        iconID = cfg.dgmattribs.Get(attributeID).iconID
        self.AddRowWithIconAndText(text=text, iconID=iconID)

    def AddRowAndHeaderForManyAttributes(self, attributeValues, manyAttributesText, headerText, texturePath = ''):
        """
            adds a header followed by a row with icons and short value text for each of the attributes (>1)
        """
        text = localization.GetByLabel(headerText)
        icon, label = self.AddRowWithIconAndText(text=text, texturePath='', minRowSize=24)
        label.SetAlign(uiconst.BOTTOMLEFT)
        formattedAttributeValues = self.GetFormattedAttributeValues(attributeValues=attributeValues, valueText=manyAttributesText)
        self.AddAttributeRow(texturePath, formattedAttributeValues, minRowSize=0, spacerWidth=65 * len(formattedAttributeValues))

    def GetFormattedAttributeValues(self, attributeValues, valueText):
        """
            takes in a list of tuples with attributeIDs and values.
            returns a list of tuples with attributeIDs and the values formatted
        """
        attributeValuesText = []
        for attributeID, attributeValue in attributeValues:
            attributeValueText = localization.GetByLabel(valueText, activeValue=attributeValue)
            attributeValuesText.append((attributeID, attributeValueText))

        return attributeValuesText

    def AddDpsAndDamgeTypeInfo(self, itemID, typeID, groupID, charge, numSlaves):
        totalDpsDamage, texturePath, iconID, damageMultiplier = self.GetDpsDamageTypeInfo(itemID, typeID, groupID, charge, numSlaves)
        if not totalDpsDamage:
            return
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/DamagePerSecond', dps=totalDpsDamage)
        self.AddRowWithIconAndText(text=text, texturePath=texturePath, iconID=iconID)
        self.AddDamageTypes(itemID, charge, damageMultiplier)

    def GetDpsDamageTypeInfo(self, itemID, typeID, groupID, charge, numSlaves):
        isBomb = groupID == const.groupMissileLauncherBomb
        isLauncher = sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, const.effectLauncherFitted)
        isTurret = sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, const.effectTurretFitted)
        if not isLauncher and not isTurret and not isBomb:
            return (None, None, None, None)
        GAV = self.dogmaLocation.GetAccurateAttributeValue
        texturePath = None
        iconID = None
        totalDpsDamage = 0
        damageMultiplier = 1
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
            return (totalDpsDamage,
             texturePath,
             iconID,
             damageMultiplier)
        if numSlaves:
            totalDpsDamage = numSlaves * totalDpsDamage
            damageMultiplier = numSlaves * damageMultiplier
        return (totalDpsDamage,
         texturePath,
         iconID,
         damageMultiplier)

    def AddDamageTypes(self, itemID, charge, multiplier):
        """
            adding the info on the damage types this module does
        """
        if charge:
            dmgCausingItemID = charge.itemID
        else:
            dmgCausingItemID = itemID
        damageAttributeValues = self.GetAttributesValues(dmgCausingItemID, multiplier, const.damageTypeAttributes, includeZeros=False)
        if not damageAttributeValues:
            return
        self.AddRowForInfoWithOneOrMoreAttributes(attributeValues=damageAttributeValues, oneAttributeText='UI/Inflight/ModuleRacks/Tooltips/OneDamageTypeText', manyAttributesText='UI/Inflight/ModuleRacks/Tooltips/DamageHitpoints', headerText='UI/Inflight/ModuleRacks/Tooltips/DamageTypesHeader')

    def GetAttributesValues(self, itemID, multiplier, attributeList, includeZeros = True):
        """
            finds the attribute values of the attributesIDs that are sent in.
            Returns a list of tuples of attributeIDs and their values
        """
        attributeValues = []
        for eachAttributeID in attributeList:
            attributeValue = self.GetEffectiveAttributeValue(itemID, eachAttributeID)
            if not attributeValue and not includeZeros:
                continue
            attributeValue = attributeValue * multiplier
            attributeValues.append((eachAttributeID, attributeValue))

        return attributeValues

    def AddAttributePerTimeInfo(self, itemID, attributeID, labelPath):
        """
            adds a row (with icon) that spells out how much the module does be time unit.
        """
        text, duration, amount = self.GetAmountPerTimeInfo(itemID=itemID, attributeID=attributeID, labelPath=labelPath)
        iconID = cfg.dgmattribs.Get(attributeID).iconID
        self.AddRowWithIconAndText(text=text, iconID=iconID)

    def AddAttributeInfo(self, itemID, attributeID, labelPath, labelKeyword):
        """
            adds a row (with icon) that spells out what the module does.
            the 'labelKeyword' is a keyword for the the attributeValue when creating the text
        """
        value = self.GetEffectiveAttributeValue(itemID, attributeID)
        tokenDict = {labelKeyword: value}
        text = localization.GetByLabel(labelPath, **tokenDict)
        iconID = cfg.dgmattribs.Get(attributeID).iconID
        self.AddRowWithIconAndText(text=text, iconID=iconID)

    def AddAttributeInfoWithAttributeName(self, itemID, attributeID, labelPath):
        """
            adds a row (with icon) that uses the attribute name and the attribute value in the text.
            The labelPath needs to have the tokens 'activeName' and 'activeValue' for this to work as expected
        """
        activeValue = self.GetEffectiveAttributeValue(itemID, attributeID)
        attributeName = cfg.dgmattribs.Get(attributeID).displayName
        text = localization.GetByLabel(labelPath, activeValue=activeValue, activeName=attributeName)
        iconID = cfg.dgmattribs.Get(attributeID).iconID
        self.AddRowWithIconAndText(text=text, iconID=iconID)

    def AddMiningLaserInfo(self, itemID, chargeInfoItem, *args):
        duration = self.GetDuration(itemID)
        amount = self.GetEffectiveAttributeValue(itemID, const.attributeMiningAmount)
        if chargeInfoItem is not None:
            specializationMultiplier = self.GetEffectiveAttributeValue(chargeInfoItem.itemID, const.attributeSpecialisationAsteroidYieldMultiplier)
            amount = specializationMultiplier * amount
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/MiningAmountPerTime', duration=duration, amount=amount)
        self.AddRowWithIconAndText(text=text, texturePath='res:/ui/texture/icons/23_64_5.png')

    def AddEnergyVampireInfo(self, itemID, chargeInfoItem):
        self.AddAttributePerTimeInfo(itemID=itemID, attributeID=const.attributePowerTransferAmount, labelPath='UI/Inflight/ModuleRacks/Tooltips/EnergyVampireAmountPerTime')

    def AddEnergyDestabilizerInfo(self, itemID, chargeInfoItem):
        self.AddAttributePerTimeInfo(itemID=itemID, attributeID=const.attributeEnergyDestabilizationAmount, labelPath='UI/Inflight/ModuleRacks/Tooltips/EnergDestabilizedPerTime')

    def AddArmorRepairersInfo(self, itemID, chargeInfoItem):
        self.AddAttributePerTimeInfo(itemID=itemID, attributeID=const.attributeArmorDamageAmount, labelPath='UI/Inflight/ModuleRacks/Tooltips/ArmorRepairedPerTime')

    def AddHullRepairersInfo(self, itemID, chargeInfoItem):
        self.AddAttributePerTimeInfo(itemID=itemID, attributeID=const.attributeStructureDamageAmount, labelPath='UI/Inflight/ModuleRacks/Tooltips/HullRepairedPerTime')

    def AddShieldBoosterInfo(self, itemID, chargeInfoItem):
        self.AddAttributePerTimeInfo(itemID=itemID, attributeID=const.attributeShieldBonus, labelPath='UI/Inflight/ModuleRacks/Tooltips/ShieldBonusPerTime')

    def AddTrackingComputerInfo(self, itemID, chargeInfoItem):
        self.AddAttributeInfo(itemID=itemID, attributeID=const.attributeFalloffBonus, labelPath='UI/Inflight/ModuleRacks/Tooltips/TrackingComputerFalloffBonus', labelKeyword='falloffBonus')
        self.AddAttributeInfo(itemID=itemID, attributeID=const.attributeMaxRangeBonus, labelPath='UI/Inflight/ModuleRacks/Tooltips/TrackingComputerRangeBonus', labelKeyword='optimalRangeBonus')
        self.AddAttributeInfo(itemID=itemID, attributeID=const.attributeTrackingSpeedBonus, labelPath='UI/Inflight/ModuleRacks/Tooltips/TrackingComputerTrackingBonus', labelKeyword='trackingSpeedBonus')

    def AddSmartBombInfo(self, itemID, chargeInfoItem):
        attrID = None
        damage = 0
        for attributeID in const.damageTypeAttributes:
            damage = self.GetEffectiveAttributeValue(itemID, attributeID)
            if damage > 0:
                attrID = attributeID
                break

        attributeInfo = cfg.dgmattribs.Get(attrID)
        damageType = attributeInfo.displayName
        iconID = attributeInfo.iconID
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/SmartBombDamage', amount=damage, damageType=damageType)
        self.AddRowWithIconAndText(text=text, iconID=iconID)

    def AddPropulsionModuleInfo(self, itemID, chargeInfoItem):
        myShip = GetActiveShip()
        myMaxVelocity = self.dogmaLocation.GetAttributeValue(myShip, const.attributeMaxVelocity)
        speedFactor = self.GetEffectiveAttributeValue(itemID, const.attributeSpeedFactor)
        speedBoostFactor = self.GetEffectiveAttributeValue(itemID, const.attributeSpeedBoostFactor)
        mass = self.dogmaLocation.GetAttributeValue(myShip, const.attributeMass)
        massAddition = self.dogmaLocation.GetAttributeValue(itemID, const.attributeMassAddition)
        maxVelocityWithBonus = myMaxVelocity * (1 + speedBoostFactor * speedFactor * 0.01 / (massAddition + mass))
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/MaxVelocityWithAndWithoutPropulsion', maxVelocity=myMaxVelocity, maxVelocityWithBonus=maxVelocityWithBonus)
        iconID = cfg.dgmattribs.Get(const.attributeMaxVelocity).iconID
        self.AddRowWithIconAndText(text=text, iconID=iconID)

    def AddStasisWebInfo(self, itemID, chargeInfoItem):
        attributeID = const.attributeSpeedFactor
        amount = self.GetEffectiveAttributeValue(itemID, attributeID)
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/VelocityReductionFromWeb', percentage=abs(amount))
        iconID = cfg.dgmattribs.Get(attributeID).iconID
        self.AddRowWithIconAndText(text=text, iconID=iconID)

    def AddWarpScramblerInfo(self, itemID, chargeInfoItem):
        self.AddAttributeInfo(itemID=itemID, attributeID=const.attributeWarpScrambleStrength, labelPath='UI/Inflight/ModuleRacks/Tooltips/WarpScramblerStrength', labelKeyword='strength')

    def AddCapacitorBoosterInfo(self, itemID, chargeInfoItem):
        """
            cannot use GetAmountPerTimeInfo() for cap boosters because the amount info comes from the charge, not the module
        """
        attributeID = const.attributeCapacitorBonus
        duration = self.GetDuration(itemID)
        if chargeInfoItem is None:
            return
        amount = self.GetEffectiveAttributeValue(chargeInfoItem.itemID, attributeID)
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/CapacitorBoostPerTime', boostAmount=amount, duration=duration)
        iconID = cfg.dgmattribs.Get(attributeID).iconID
        self.AddRowWithIconAndText(text=text, iconID=iconID)

    def AddEnergyTransferArrayInfo(self, itemID, chargeInfoItem):
        self.AddAttributePerTimeInfo(itemID=itemID, attributeID=const.attributePowerTransferAmount, labelPath='UI/Inflight/ModuleRacks/Tooltips/EnergyTransferredPerTime')

    def AddShieldTransporterInfo(self, itemID, chargeInfoItem):
        self.AddAttributePerTimeInfo(itemID=itemID, attributeID=const.attributeShieldBonus, labelPath='UI/Inflight/ModuleRacks/Tooltips/ShieldTransportedPerTime')

    def AddArmorRepairProjectorInfo(self, itemID, chargeInfoItem):
        self.AddAttributePerTimeInfo(itemID=itemID, attributeID=const.attributeArmorDamageAmount, labelPath='UI/Inflight/ModuleRacks/Tooltips/ArmorTransferredPerTime')

    def AddRemoteHullRepairInfo(self, itemID, chargeInfoItem):
        self.AddAttributePerTimeInfo(itemID=itemID, attributeID=const.attributeStructureDamageAmount, labelPath='UI/Inflight/ModuleRacks/Tooltips/HullRemoteRepairedPerTime')

    def AddArmorHardenerInfo(self, itemID, chargeInfoItem):
        damageAttributeValues = self.GetAttributesValues(itemID, 1, RESISTANCE_BONUS_ATTRIBUTES, includeZeros=False)
        self.AddRowForInfoWithOneOrMoreAttributes(attributeValues=damageAttributeValues, oneAttributeText='UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', manyAttributesText='UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues', headerText='UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusesHeader')

    def AddECMInfo(self, itemID, chargeInfoItem):
        bonusAttributes = [const.attributeScanGravimetricStrengthBonus,
         const.attributeScanLadarStrengthBonus,
         const.attributeScanMagnetometricStrengthBonus,
         const.attributeScanRadarStrengthBonus]
        rows = []
        for attrID in bonusAttributes:
            strength = self.GetEffectiveAttributeValue(itemID, attrID)
            if strength is not None and strength != 0:
                attributeName = cfg.dgmattribs.Get(attrID).displayName
                rows.append(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ECMStrengthBonus', strength=strength, attributeName=attributeName))

        text = '<br>'.join(rows)
        self.AddRowWithIconAndText(text=text, texturePath='res:/UI/Texture/Icons/4_64_12.png')

    def AddECCMInfo(self, itemID, chargeInfoItem):
        damageTypeAttributes = [const.attributeScanGravimetricStrengthPercent,
         const.attributeScanLadarStrengthPercent,
         const.attributeScanMagnetometricStrengthPercent,
         const.attributeScanRadarStrengthPercent]
        rows = []
        for attrID in damageTypeAttributes:
            strength = self.GetEffectiveAttributeValue(itemID, attrID)
            if strength is not None and strength != 0:
                attributeName = cfg.dgmattribs.Get(attrID).displayName
                rows.append(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=strength, activeName=attributeName))

        text = '<br>'.join(rows)
        self.AddRowWithIconAndText(text=text, texturePath='res:/UI/Texture/Icons/4_64_12.png')

    def AddSensorDamperInfo(self, itemID, chargeInfoItem):
        bonus = self.GetEffectiveAttributeValue(itemID, const.attributeScanResolutionBonus)
        if bonus != 0:
            self.AddAttributeInfoWithAttributeName(itemID=itemID, attributeID=const.attributeScanResolutionBonus, labelPath='UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText')
        bonus = self.GetEffectiveAttributeValue(itemID, const.attributeMaxTargetRangeBonus)
        if bonus != 0:
            self.AddAttributeInfoWithAttributeName(itemID=itemID, attributeID=const.attributeMaxTargetRangeBonus, labelPath='UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText')

    def AddTargetBreakerInfo(self, itemID, chargeInfoItem):
        self.AddAttributeInfoWithAttributeName(itemID=itemID, attributeID=const.attributeScanResolutionMultiplier, labelPath='UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText')

    def AddTargetPainterInfo(self, itemID, chargeInfoItem):
        self.AddAttributeInfoWithAttributeName(itemID=itemID, attributeID=const.attributeSignatureRadiusBonus, labelPath='UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText')

    def AddTrackingDisruptorInfo(self, itemID, chargeInfoItem):
        self.AddAttributeInfoWithAttributeName(itemID=itemID, attributeID=const.attributeFalloffBonus, labelPath='UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText')

    def AddCloakingDeviceInfo(self, itemID, chargeInfoItem):
        self.AddAttributeInfoWithAttributeName(itemID=itemID, attributeID=const.attributeMaxVelocityBonus, labelPath='UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText')

    def AddTractorBeamInfo(self, itemID, chargeInfoItem):
        attributeID = const.attributeMaxTractorVelocity
        maxTractorVel = self.GetEffectiveAttributeValue(itemID, attributeID)
        attributeName = cfg.dgmattribs.Get(attributeID).displayName
        text = (localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/TractorBeamTractorVelocity', maxTractorVel=maxTractorVel, attributeName=attributeName),)
        iconID = cfg.dgmattribs.Get(attributeID).iconID
        self.AddRowWithIconAndText(text=text, iconID=iconID)

    def AddDamageControlInfo(self, itemID, chargeInfoItem):
        shieldDamageTypeAttributes = [const.attributeShieldEmDamageResonance,
         const.attributeShieldExplosiveDamageResonance,
         const.attributeShieldKineticDamageResonance,
         const.attributeShieldThermalDamageResonance]
        armorDamageTypeAttributes = [const.attributeArmorEmDamageResonance,
         const.attributeArmorExplosiveDamageResonance,
         const.attributeArmorKineticDamageResonance,
         const.attributeArmorThermalDamageResonance]
        hullDamageTypeAttributes = [const.attributeHullEmDamageResonance,
         const.attributeHullExplosiveDamageResonance,
         const.attributeHullKineticDamageResonance,
         const.attributeHullThermalDamageResonance]
        for damageTypeAttributes, texturePath, headerText in ((shieldDamageTypeAttributes, 'res:/UI/Texture/Icons/1_64_13.png', 'UI/Inflight/ModuleRacks/Tooltips/ShieldDamageResistanceHeader'), (armorDamageTypeAttributes, 'res:/UI/Texture/Icons/1_64_9.png', 'UI/Inflight/ModuleRacks/Tooltips/ArmorDamageResistanceHeader'), (hullDamageTypeAttributes, 'res:/UI/Texture/Icons/2_64_12.png', 'UI/Inflight/ModuleRacks/Tooltips/HullDamageResistanceHeader')):
            attributeValues = self.GetAttributesValues(itemID, 1, damageTypeAttributes, includeZeros=True)
            self.AddRowAndHeaderForManyAttributes(attributeValues=attributeValues, manyAttributesText='UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues', headerText=headerText, texturePath=texturePath)

    def AddArmorResistanceShiftHardenerInfo(self, itemID, chargeInfoItem):
        damageTypeAttributes = [const.attributeArmorEmDamageResonance,
         const.attributeArmorExplosiveDamageResonance,
         const.attributeArmorKineticDamageResonance,
         const.attributeArmorThermalDamageResonance]
        attributeValues = self.GetAttributesValues(itemID, 1, damageTypeAttributes, includeZeros=True)
        self.AddRowAndHeaderForManyAttributes(attributeValues=attributeValues, manyAttributesText='UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues', headerText='UI/Inflight/ModuleRacks/Tooltips/ArmorDamageResistanceHeader', texturePath='')

    def AddSuperWeaponInfo(self, itemID, chargeInfoItem):
        for attributeID in const.damageTypeAttributes:
            damage = self.GetEffectiveAttributeValue(itemID, attributeID)
            if damage == 0:
                continue
            self.AddAttributeInfoWithAttributeName(itemID=itemID, attributeID=attributeID, labelPath='UI/Inflight/ModuleRacks/Tooltips/SuperWeaponDamage')

    def AddGangCoordinatorInfo(self, itemID, chargeInfoItem):
        commandBonus = self.GetEffectiveAttributeValue(itemID, const.attributeCommandbonus)
        if commandBonus != 0:
            displayName = cfg.dgmattribs.Get(const.attributeCommandbonus).displayName
            text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/GangCoordinatorCommandBonus', commandBonus=commandBonus, attributeName=displayName)
            self.AddRowWithIconAndText(text=text, texturePath='')
        maxGangModulesAttr = cfg.dgmattribs.Get(const.attributeMaxGangModules)
        if maxGangModulesAttr.attributeName in self.stateManager.GetAttributes(itemID):
            maxGangModules = self.GetEffectiveAttributeValue(itemID, const.attributeMaxGangModules)
            displayName = maxGangModulesAttr.displayName
            text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/GangCoordinatorMaxCommandRelays', maxGangModules=maxGangModules, attributeName=displayName)
            self.AddRowWithIconAndText(text=text, texturePath='')
