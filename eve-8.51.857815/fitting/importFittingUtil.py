#Embedded file name: fitting\importFittingUtil.py
"""
    This file contains some utility functions for import EFT fittings
"""
import collections
import inventorycommon.const as invconst
import dogma.const as dogmaConst
SHIP_FIRST_CHARACTER = '['
SHIP_LAST_CHARACTER = ']'
OFFLINE_INDICATOR = '/offline'
CHARGE_SEPARATOR = ','
MULTIPLIER_SEPARATOR = ' x'
EMPTY_TEMPLATE_STRING = '[Empty %s slot]'
emptySlotDict = {EMPTY_TEMPLATE_STRING % 'Low': 'flagLoSlot',
 EMPTY_TEMPLATE_STRING % 'Med': 'flagMedSlot',
 EMPTY_TEMPLATE_STRING % 'High': 'flagHiSlot',
 EMPTY_TEMPLATE_STRING % 'Rig': 'flagRigSlot'}
slotDict = {dogmaConst.effectRigSlot: 'flagRigSlot',
 dogmaConst.effectHiPower: 'flagHiSlot',
 dogmaConst.effectMedPower: 'flagMedSlot',
 dogmaConst.effectLoPower: 'flagLoSlot'}
NUM_SLOTS = 8
validCategoryIDs = [invconst.categoryShip,
 invconst.categoryModule,
 invconst.categorySubSystem,
 invconst.categoryCharge,
 invconst.groupIceProduct,
 invconst.categoryDrone]

class ImportFittingUtil(object):

    def __init__(self, cfgInvtypes, dgmtypeeffectDict, clientDogmaStaticSvc):
        self.nameAndTypesDict = GetValidNamesAndTypesDict(cfgInvtypes)
        self.dgmtypeeffectDict = dgmtypeeffectDict
        self.clientDogmaStaticSvc = clientDogmaStaticSvc

    def GetLineInfo(self, line):
        parts = SplitAndStrip(line, CHARGE_SEPARATOR)
        typeName = parts[0]
        if len(parts) > 1:
            chargeName = parts[1].strip()
        else:
            chargeName = None
        parts = SplitAndStrip(typeName, MULTIPLIER_SEPARATOR)
        typeName = parts[0]
        if len(parts) > 1:
            numItems = int(parts[1])
        else:
            numItems = 1
        invType = self.nameAndTypesDict.get(typeName, None)
        chargeInvType = self.nameAndTypesDict.get(chargeName, None)
        isEmpty = True
        slotLocation = None
        if typeName in emptySlotDict:
            slotLocation = emptySlotDict[typeName]
        elif invType:
            slotLocation = self.GetSlot(invType.typeID)
            isEmpty = False
        info = {'typeName': typeName,
         'typeInvType': invType,
         'numItems': numItems,
         'chargeName': chargeName,
         'chargeInvType': chargeInvType,
         'slotLocation': slotLocation,
         'isEmpty': isEmpty}
        return info

    def GetAllItems(self, text):
        lines = GetItemLines(text)
        allItemsInfo = []
        for eachLine in lines:
            lineInfo = self.GetLineInfo(eachLine)
            allItemsInfo.append(lineInfo)

        return allItemsInfo

    def GetSlot(self, typeID):
        for effect in self.dgmtypeeffectDict.get(typeID, []):
            if effect.effectID in slotDict:
                return slotDict.get(effect.effectID)

        subsystemSlot = self.clientDogmaStaticSvc.GetTypeAttribute2(typeID, dogmaConst.attributeSubSystemSlot)
        if subsystemSlot:
            return int(subsystemSlot)

    def GetSlotNumbers(self, shipInvType):
        typeID = shipInvType.typeID
        slotDict = {'flagRigSlot': self.clientDogmaStaticSvc.GetTypeAttribute2(typeID, dogmaConst.attributeRigSlots)}
        if shipInvType.groupID == invconst.groupStrategicCruiser:
            slotDict['flagHiSlot'] = NUM_SLOTS
            slotDict['flagMedSlot'] = NUM_SLOTS
            slotDict['flagLoSlot'] = NUM_SLOTS
            for location in invconst.subSystemSlotFlags:
                slotDict[location] = 1

        else:
            slotDict['flagHiSlot'] = self.clientDogmaStaticSvc.GetTypeAttribute2(typeID, dogmaConst.attributeHiSlots)
            slotDict['flagMedSlot'] = self.clientDogmaStaticSvc.GetTypeAttribute2(typeID, dogmaConst.attributeMedSlots)
            slotDict['flagLoSlot'] = self.clientDogmaStaticSvc.GetTypeAttribute2(typeID, dogmaConst.attributeLowSlots)
        return slotDict

    def CreateFittingData(self, infoLines, shipInvType):
        fitData = []
        dronesByType = collections.defaultdict(int)
        cargoByType = collections.defaultdict(int)
        locationDict = collections.defaultdict(int)
        allowedSlotsDict = self.GetSlotNumbers(shipInvType)
        for eachLine in infoLines:
            slotLocation = eachLine['slotLocation']
            invType = eachLine['typeInvType']
            if slotLocation:
                if locationDict[slotLocation] >= allowedSlotsDict.get(slotLocation, 0):
                    continue
                slotIdx = locationDict[slotLocation]
                locationDict[slotLocation] += 1
                if eachLine['isEmpty'] or not invType:
                    continue
                typeID = invType.typeID
                if invType.categoryID == invconst.categorySubSystem:
                    slotLocationConst = slotLocation
                else:
                    slotLocationConst = getattr(invconst, '%s%s' % (slotLocation, slotIdx), None)
                fitData.append((typeID, slotLocationConst, 1))
                chargeInvType = eachLine['chargeInvType']
                if chargeInvType:
                    chargeAmount = invType.capacity / chargeInvType.volume
                    cargoByType[chargeInvType.typeID] += chargeAmount
            if not invType:
                continue
            if invType.categoryID in (invconst.categoryCharge, invconst.groupIceProduct):
                cargoByType[invType.typeID] += eachLine['numItems']
            if invType.categoryID == invconst.categoryDrone:
                dronesByType[invType.typeID] += eachLine['numItems']

        cargoAndDrones = [(cargoByType, invconst.flagCargo), (dronesByType, invconst.flagDroneBay)]
        for dictByType, locationFlag in cargoAndDrones:
            for typeID, amount in dictByType.iteritems():
                fitData.append((typeID, locationFlag, int(amount)))

        return fitData


def GetLines(text):
    textWithBr = text.replace('\n', '<br>').replace('\r\n', '<br>')
    textWithBr = textWithBr.replace(OFFLINE_INDICATOR, '')
    lines = SplitAndStrip(textWithBr, '<br>')
    return lines


def SplitAndStrip(text, splitOn):
    parts = text.split(splitOn)
    parts = [ x.strip() for x in parts if x.strip() ]
    return parts


def IsShipLine(text):
    return text.startswith(SHIP_FIRST_CHARACTER) and text[-1] == SHIP_LAST_CHARACTER and text not in emptySlotDict


def GetItemLines(text):
    lines = GetLines(text)
    lines = [ x for x in lines if not IsShipLine(x) ]
    return lines


def GetValidNamesAndTypesDict(invRecordSet):
    return {invtype._typeName:invtype for invtype in invRecordSet if invtype.categoryID in validCategoryIDs}


def FindShipAndFittingName(text):
    lines = GetLines(text)
    for eachLine in lines:
        if not eachLine:
            continue
        if IsShipLine(eachLine):
            shipInfo = eachLine[1:-1]
            parts = SplitAndStrip(shipInfo, CHARGE_SEPARATOR)
            commaIdx = shipInfo.find(CHARGE_SEPARATOR)
            return (parts[0], shipInfo[commaIdx + 1:].strip())
