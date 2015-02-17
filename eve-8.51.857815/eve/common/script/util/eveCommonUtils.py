#Embedded file name: eve/common/script/util\eveCommonUtils.py
"""
    This file contains declarations and common helper functions used in the UI
    and ESP; most of these are formatting and parsing functions.
    
    This file contains eve-specific functionality to compliment commonutils.py in core

"""
import math
from inventorycommon.util import IsShipFittingFlag
import util
import types
import xml.parsers.expat
from dogma.const import attributeAsteroidRadiusUnitSize, attributeAsteroidRadiusGrowthFactor
from eve.common.lib.appConst import maxAsteroidRadius
import localization
import re
ASTEROID_EXP_SCALE = 4e-05

def CombatLog_CopyText(mail, *args):
    kwargs = {'system': mail.solarSystemID,
     'target': mail.victimShipTypeID,
     'damage': mail.victimDamageTaken}
    if boot.role == 'client':
        kwargs['security'] = sm.GetService('map').GetSecurityStatus(mail.solarSystemID)
    else:
        kwargs['security'] = cfg.mapSystemCache[mail.solarSystemID].pseudoSecurity
    if mail.moonID is not None:
        kwargs['moon'] = cfg.evelocations.Get(mail.moonID).name
    else:
        kwargs['moon'] = localization.GetByLabel('UI/Common/Unknown')
    if mail.victimAllianceID is not None:
        kwargs['alliance'] = cfg.eveowners.Get(mail.victimAllianceID).name
    else:
        kwargs['alliance'] = localization.GetByLabel('UI/Common/Unknown')
    if mail.victimFactionID is not None:
        kwargs['faction'] = cfg.eveowners.Get(mail.victimFactionID).name
    else:
        kwargs['faction'] = localization.GetByLabel('UI/Common/Unknown')
    if mail.victimCharacterID is not None:
        if mail.victimCorporationID is None:
            return
        kwargs['victim'] = mail.victimCharacterID
        kwargs['corporation'] = cfg.eveowners.Get(mail.victimCorporationID).name
        headerLabel = 'UI/Util/CommonUtils/KillMailHeaderWithShip'
    elif mail.victimCorporationID is not None:
        kwargs['corporation'] = cfg.eveowners.Get(mail.victimCorporationID).name
        headerLabel = 'UI/Util/CommonUtils/KillMailHeaderWithStructure'
    else:
        return
    header = localization.GetByLabel(headerLabel, **kwargs)
    attackers, items = GetAttackersAndItemsFromKillMail(mail)
    attackerList = []
    for row in attackers:
        attacker = row[1]
        data = {'damage': attacker.damageDone}
        attackerLabel = None
        if attacker.characterID is not None:
            data['attacker'] = cfg.eveowners.Get(attacker.characterID).name
            data['security'] = attacker.secStatusText
            data['corporation'] = cfg.eveowners.Get(attacker.corporationID).name
            if attacker.allianceID is not None:
                data['alliance'] = cfg.eveowners.Get(attacker.allianceID).name
            else:
                data['alliance'] = localization.GetByLabel('UI/Common/None')
            if attacker.factionID is not None:
                data['faction'] = cfg.eveowners.Get(attacker.factionID).name
            else:
                data['faction'] = localization.GetByLabel('UI/Common/None')
            if attacker.shipTypeID is not None:
                data['ship'] = cfg.invtypes.Get(attacker.shipTypeID).name
            else:
                data['ship'] = localization.GetByLabel('UI/Common/Unknown')
            if attacker.weaponTypeID is not None:
                data['weapon'] = cfg.invtypes.Get(attacker.weaponTypeID).name
            else:
                data['weapon'] = localization.GetByLabel('UI/Common/Unknown')
            if attacker.finalBlow:
                attackerLabel = 'UI/Util/CommonUtils/KillMailPlayerAttackerWithFinalBlow'
            else:
                attackerLabel = 'UI/Util/CommonUtils/KillMailPlayerAttacker'
        elif attacker.corporationID is not None:
            if attacker.shipTypeID is not None:
                data['attacker'] = cfg.invtypes.Get(attacker.shipTypeID).name
            else:
                data['attacker'] = localization.GetByLabel('UI/Common/Unknown')
            data['owner'] = cfg.eveowners.Get(attacker.corporationID).name
            if attacker.finalBlow:
                attackerLabel = 'UI/Util/CommonUtils/KillMailMPCAttackerWithFinalBlow'
            else:
                attackerLabel = 'UI/Util/CommonUtils/KillMailNPCAttacker'
        if attackerLabel is not None:
            attackerList.append(localization.GetByLabel(attackerLabel, **data))

    droppedItemList = []
    destroyedItemList = []
    textDropped = textDestroyed = ''
    for item in items:
        qty = None
        if item.qtyDropped > 0:
            qty = item.qtyDropped
            wasDropped = True
        else:
            qty = item.qtyDestroyed
            wasDropped = False
        if item.flag == const.flagCargo:
            itemLocation = localization.GetByLabel('UI/Util/CommonUtils/KillMailItemLocation', itemLocation=localization.GetByLabel('UI/Generic/Cargo'))
        elif item.flag == const.flagDroneBay:
            itemLocation = localization.GetByLabel('UI/Util/CommonUtils/KillMailItemLocation', itemLocation=localization.GetByLabel('UI/Common/DroneBay'))
        elif item.flag == const.flagImplant:
            itemLocation = localization.GetByLabel('UI/Util/CommonUtils/KillMailItemLocation', itemLocation=localization.GetByLabel('UI/Common/Implant'))
        elif IsShipFittingFlag(item.flag):
            itemLocation = ''
        else:
            itemLocation = localization.GetByLabel('UI/Util/CommonUtils/KillMailItemLocation', itemLocation=localization.GetByLabel('UI/Common/Other'))
        itemText = GetItemText(item, qty, itemLocation)
        if wasDropped:
            droppedItemList.append(itemText)
        else:
            destroyedItemList.append(itemText)
        if len(item.contents) > 0:
            for subitem in item.contents:
                itemLocation = localization.GetByLabel('UI/Util/CommonUtils/KillMailItemLocation', itemLocation=localization.GetByLabel('UI/Util/CommonUtils/InContainer'))
                if subitem.qtyDropped > 0:
                    qty = subitem.qtyDropped
                else:
                    qty = subitem.qtyDestroyed
                itemText = '<t>' + GetItemText(subitem, qty, itemLocation)
                if wasDropped:
                    droppedItemList.append(itemText)
                else:
                    destroyedItemList.append(itemText)

    if len(droppedItemList) > 0:
        textDropped = localization.GetByLabel('UI/Util/CommonUtils/KillMailDroppedItems', droppedItems=''.join(droppedItemList))
    if len(destroyedItemList) > 0:
        textDestroyed = localization.GetByLabel('UI/Util/CommonUtils/KillMailDestroyedItems', destroyedItems=''.join(destroyedItemList))
    killmail = localization.GetByLabel('UI/Util/CommonUtils/KillMail', timestamp=util.FmtDate(mail.killTime, fmt='ll'), header=header, attackers=''.join(attackerList), droppedItems=textDropped, destroyedItems=textDestroyed)
    return killmail.replace('\n', '')


def GetPublicCrestUrl(*args):
    public_crest_url = sm.GetService('machoNet').GetGlobalConfig().get('publicCrestUrl')
    if public_crest_url is None:
        public_crest_url = ''
    args_as_url = '/'.join((str(x) for x in args))
    full_crest_url = '%s%s/' % (public_crest_url, args_as_url)
    return full_crest_url


def GetAttackersAndItemsFromKillMail(mail):
    attackers = []
    items = []
    rx = re.compile('=(\\d+(?:\\.\\d+)?)')
    tempBlob = rx.sub('="\\1"', mail.killBlob)
    pstate = util.Object()
    pstate.Set('state', 0)
    pstate.Set('lastitem', None)

    def _xmlTagStart(tag, attrs):
        state = pstate.Get('state', 0)
        if state == 99:
            return
        if tag == 'doc':
            return
        if tag == 'attackers':
            if state != 0:
                pstate.Set('state', 99)
                return
            pstate.Set('state', 1)
        elif tag == 'a':
            if state != 1:
                pstate.Set('state', 99)
                return
            pstate.Set('state', 2)
            attacker = util.KeyVal()
            attacker.characterID = attrs.get('c', None)
            attacker.corporationID = attrs.get('r', None)
            attacker.allianceID = attrs.get('a', None)
            attacker.factionID = attrs.get('f', None)
            attacker.shipTypeID = attrs.get('s', None)
            attacker.weaponTypeID = attrs.get('w', None)
            attacker.damageDone = int(float(attrs.get('d', 0)))
            attacker.secStatusText = attrs.get('t', '0.0')
            attacker.finalBlow = False
            attackers.append((attacker.damageDone, attacker))
        elif tag == 'items':
            if state != 0 and state != 3:
                pstate.Set('state', 99)
                return
            pstate.Set('state', 4)
        elif tag == 'i':
            if state != 4 and state != 5:
                pstate.Set('state', 99)
                return
            item = util.KeyVal()
            item.typeID = attrs.get('t', None)
            item.flag = int(float(attrs.get('f', 0)))
            item.singleton = int(float(attrs.get('s', 0)))
            item.qtyDropped = int(float(attrs.get('d', 0)))
            item.qtyDestroyed = int(float(attrs.get('x', 0)))
            item.contents = []
            if state == 4:
                pstate.Set('state', 5)
                if item.qtyDropped > 0 and item.qtyDestroyed > 0:
                    item2 = util.KeyVal()
                    item2.typeID = item.typeID
                    item2.flag = item.flag
                    item2.singleton = item.singleton
                    item2.qtyDropped = item.qtyDropped
                    item2.qtyDestroyed = 0
                    item2.contents = []
                    item.qtyDropped = 0
                    items.append(item)
                    items.append(item2)
                else:
                    items.append(item)
                    pstate.Set('lastitem', item)
            else:
                pstate.Set('state', 6)
                litem = pstate.Get('lastitem', None)
                if litem is not None:
                    litem.contents.append(item)
                    pstate.Set('lastitem', litem)
                else:
                    pstate.Set('state', 99)
        else:
            pstate.Set('state', 99)

    def _xmlTagEnd(tag):
        state = pstate.Get('state', 0)
        if state == 99:
            return
        if tag == 'doc':
            return
        if tag == 'attackers':
            if state != 1:
                pstate.Set('state', 99)
                return
            pstate.Set('state', 3)
        elif tag == 'a':
            if state != 2:
                pstate.Set('state', 99)
                return
            pstate.Set('state', 1)
        elif tag == 'items':
            if state != 4:
                pstate.Set('state', 99)
                return
            pstate.Set('state', 7)
        elif tag == 'i':
            if state != 5 and state != 6:
                pstate.Set('state', 99)
                return
            if state == 5:
                pstate.Set('state', 4)
            else:
                pstate.Set('state', 5)
        else:
            pstate.Set('state', 99)

    parser = xml.parsers.expat.ParserCreate()
    parser.StartElementHandler = _xmlTagStart
    parser.EndElementHandler = _xmlTagEnd
    parser.buffer_text = True
    parser.returns_unicode = False
    parser.Parse('<doc>' + tempBlob + '</doc>', 1)
    pstate.Set('state', 0)
    pstate.Set('lastitem', None)
    finalBlow = util.KeyVal()
    finalBlow.characterID = mail.finalCharacterID
    finalBlow.corporationID = mail.finalCorporationID
    finalBlow.allianceID = mail.finalAllianceID
    finalBlow.factionID = mail.finalFactionID
    finalBlow.shipTypeID = mail.finalShipTypeID
    finalBlow.weaponTypeID = mail.finalWeaponTypeID
    finalBlow.damageDone = mail.finalDamageDone
    if mail.finalSecurityStatus is None:
        finalBlow.secStatusText = '0.0'
    else:
        finalBlow.secStatusText = util.FmtSystemSecStatus(mail.finalSecurityStatus)
    finalBlow.finalBlow = True
    attackers.append((finalBlow.damageDone, finalBlow))
    attackers.sort(reverse=True)
    return (attackers, items)


def GetItemText(item, qty, itemLocation):
    if item.singleton == const.singletonBlueprintCopy and cfg.invtypes.Get(item.typeID).Group().categoryID == const.categoryBlueprint:
        if qty > 1:
            return localization.GetByLabel('UI/Util/CommonUtils/KillMailLostStackBPC', item=item.typeID, quantity=qty, itemLocation=itemLocation)
        else:
            return localization.GetByLabel('UI/Util/CommonUtils/KillMailLostItemBPC', item=item.typeID, itemLocation=itemLocation)
    else:
        if qty > 1:
            return localization.GetByLabel('UI/Util/CommonUtils/KillMAilLostStack', item=item.typeID, quantity=qty, itemLocation=itemLocation)
        return localization.GetByLabel('UI/Util/CommonUtils/KillMailLostItem', item=item.typeID, itemLocation=itemLocation)


def SecurityClassFromLevel(level):
    """
        Returns the security class of a system when given its sec level
        use:  secClass = util.SecurityClassFromLevel(lvl)
        pre:  -1.0 <= lvl <= 1.0
        post: iff lvl <= 0.0: secClass is securityClassZeroSec 
              iff 0.0 < lvl < 0.45: secClass is securityClassLowSec
              iff 0.45 <= lvl: secClass is securityClassHighSec
    """
    if level <= 0.0:
        return const.securityClassZeroSec
    elif level < 0.45:
        return const.securityClassLowSec
    else:
        return const.securityClassHighSec


def ComputeRadiusFromQuantity(categoryID, groupID, typeID, quantity, dogma):
    """
        Computes the radius of an object from the object quantity.  This reflects its visual size in game.
        This is necessary as some object types have a special relationship between quantity and scale.
    """
    if quantity < 0:
        quantity = 1
    if categoryID == const.categoryAsteroid:
        return AsteroidQuantityToRadius(typeID, quantity, dogma)
    if groupID == const.groupHarvestableCloud:
        return quantity * cfg.invtypes.Get(typeID).radius / 10.0
    return quantity * cfg.invtypes.Get(typeID).radius


def ComputeQuantityFromRadius(categoryID, groupID, typeID, radius, dogma):
    """
        Computes the quantity of an object from the object radius.  These calculations are the inverse of 
        ComputeRadiusFromQuantity. This function is necessary as some object types have a special relationship
        between quantity and scale.
    """
    if categoryID == const.categoryAsteroid:
        AsteroidRadiusToQuantity(typeID, radius, dogma)
    elif groupID == const.groupHarvestableCloud:
        quantity = radius * 10.0 / cfg.invtypes.Get(typeID).radius
        return quantity
    return radius / cfg.invtypes.Get(typeID).radius


def AsteroidQuantityToRadius(typeID, quantity, dogma):
    quantity = max(1, quantity)
    unitSize = dogma.GetTypeAttribute2(typeID, attributeAsteroidRadiusUnitSize)
    growthFactor = dogma.GetTypeAttribute2(typeID, attributeAsteroidRadiusGrowthFactor)
    radius = unitSize * math.exp(ASTEROID_EXP_SCALE * (quantity - 1) * growthFactor)
    maxRadius = int(prefs.GetValue('maxAsteroidRadius', maxAsteroidRadius))
    return min(maxRadius, radius)


def AsteroidRadiusToQuantity(typeID, radius, dogma):
    unitSize = dogma.GetTypeAttribute2(typeID, attributeAsteroidRadiusUnitSize)
    growthFactor = dogma.GetTypeAttribute2(typeID, attributeAsteroidRadiusGrowthFactor)
    quantity = 1 + math.log(radius / unitSize) * (1.0 / ASTEROID_EXP_SCALE / growthFactor)
    return quantity


def IsMemberlessLocal(channelID):
    """
        This utility function is used by the server and the client
        to know if channelID is a local channel in 'memberless' mode.
        Currently this is the case in wormhole systems only
    """
    if type(channelID) != types.IntType:
        if type(channelID[0]) == types.TupleType:
            channelID = channelID[0]
        if channelID[0] == 'solarsystemid2':
            if util.IsWormholeSystem(channelID[1]):
                return True
    return False


def Flatten(sequence):
    """
    Generator function that "flattens" one or more nested sequence types.  
    Every non-iterable element in the provided structures will be yielded individually.
    """
    if isinstance(sequence, basestring) or not hasattr(sequence, '__iter__'):
        yield sequence
        return
    for thingie in sequence:
        for dude in Flatten(thingie):
            yield dude


SERVEREWARTYPES = {const.effectWarpScramble: 'warpScrambler',
 const.effectDecreaseTargetSpeed: 'webify',
 const.effectWarpScrambleForEntity: 'warpScrambler',
 const.effectModifyTargetSpeed2: 'webify',
 const.effectConcordWarpScramble: 'warpScrambler',
 const.effectConcordModifyTargetSpeed: 'webify',
 const.effectWarpScrambleBlockMWDWithNPCEffect: 'warpScramblerMWD',
 const.effectWarpDisruptSphere: 'warpScrambler',
 const.effectLeech: 'ewEnergyVampire',
 const.effectEnergyDestabilizationNew: 'ewEnergyNeut',
 const.effectEntityCapacitorDrain: 'ewEnergyNeut',
 const.effectEnergyDestabilizationForStructure: 'ewEnergyNeut',
 const.effectWarpScrambleForStructure: 'warpScrambler',
 const.effectDecreaseTargetSpeedForStructures: 'webify',
 const.effectEssWarpScramble: 'warpScrambler',
 const.effectWarpScrambleTargetMWDBlockActivationForEntity: 'warpScramblerMWD'}
ALLEWARTYPES = {const.effectEwTargetPaint: 'ewTargetPaint',
 const.effectTargetMaxTargetRangeAndScanResolutionBonusHostile: 'ewRemoteSensorDamp',
 const.effectTargetGunneryMaxRangeAndTrackingSpeedBonusHostile: 'ewTrackingDisrupt',
 const.effectTargetGunneryMaxRangeAndTrackingSpeedAndFalloffBonusHostile: 'ewTrackingDisrupt',
 const.effectTurretWeaponRangeFalloffTrackingSpeedMultiplyTargetHostile: 'ewTrackingDisrupt',
 const.effectEntitySensorDampen: 'ewRemoteSensorDamp',
 const.effectSensorBoostTargetedHostile: 'ewRemoteSensorDamp',
 const.effectEntityTrackingDisrupt: 'ewTrackingDisrupt',
 const.effectEntityTargetPaint: 'ewTargetPaint'}
ALLEWARTYPES.update(SERVEREWARTYPES)

def GetEwarTypeByEffectID(effectID):
    """
        finds what kind of ewar this type is doing based on its effects
    """
    effect = cfg.dgmeffects.Get(effectID)
    if effect.electronicChance:
        return 'electronic'
    if effect.propulsionChance:
        return 'propulsion'
    ewarType = ALLEWARTYPES.get(effectID, None)
    return ewarType


def GetKillMailInfo(killmail):
    attackers, items = GetAttackersAndItemsFromKillMail(killmail)
    attackers = [ (damage, util.KeyVal(attacker)) for damage, attacker in attackers ]
    items = [ util.KeyVal(item) for item in items ]
    return (attackers, items)


def AUPerSecondToDestinyWarpSpeed(auPerSecond):
    """
    When issuing a WarpTo instruction to destiny, the warp speed is expected to be converted to mAU/s.
    """
    return int(auPerSecond / const.warpSpeedToAUPerSecond)


def IsDustEnabled():
    """
        Utility method to determine if DUST is enabled. Use this to hide functionality that is dependent on DUST interaction.
        For now, this only applies to Serenity.
    """
    return boot.region != 'optic'


exports = {'util.CombatLog_CopyText': CombatLog_CopyText,
 'util.SecurityClassFromLevel': SecurityClassFromLevel,
 'util.IsMemberlessLocal': IsMemberlessLocal,
 'util.Flatten': Flatten,
 'util.GetEwarTypeByEffectID': GetEwarTypeByEffectID,
 'util.SERVEREWARTYPES': SERVEREWARTYPES,
 'util.ALLEWARTYPES': ALLEWARTYPES,
 'util.GetKillMailInfo': GetKillMailInfo,
 'util.AUPerSecondToDestinyWarpSpeed': AUPerSecondToDestinyWarpSpeed,
 'util.IsDustEnabled': IsDustEnabled}
