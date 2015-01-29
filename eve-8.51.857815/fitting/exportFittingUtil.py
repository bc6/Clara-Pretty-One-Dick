#Embedded file name: fitting\exportFittingUtil.py
"""
    This file contains some utility functions for exporting fitting in EFT format
    It assume the following order, with the slot location separated by one linebreak
    low slots
    mid slots
    high slots
    rig slots
    subsystem slots
    drones
    items in cargo
"""
import inventorycommon.const as invconst
EXTRA_ITEM_TEMPLATE = '%s x%s'
EMPTY_TEMPLATE_STRING = '[Empty %s slot]'
SHIP_AND_FITTINGNAME_TEMPLATE = '[%s, %s]'
LINEBREAK = '\r\n'
NUM_SLOTS = 8
NUM_SUBSYSTEMS = 5
emptySlotDict = {invconst.flagLoSlot0: EMPTY_TEMPLATE_STRING % 'Low',
 invconst.flagMedSlot0: EMPTY_TEMPLATE_STRING % 'Med',
 invconst.flagHiSlot0: EMPTY_TEMPLATE_STRING % 'High',
 invconst.flagRigSlot0: EMPTY_TEMPLATE_STRING % 'Rig'}

def GetFittingEFTString(fitting, recordSet):
    fitData = fitting.fitData
    cargoItems = [ x for x in fitData if x[1] == invconst.flagCargo ]
    droneItems = [ x for x in fitData if x[1] == invconst.flagDroneBay ]
    fitDataFlagDict = {x[1]:x for x in fitData}
    slotTuples = [(NUM_SLOTS, invconst.flagLoSlot0),
     (NUM_SLOTS, invconst.flagMedSlot0),
     (NUM_SLOTS, invconst.flagHiSlot0),
     (NUM_SLOTS, invconst.flagRigSlot0),
     (NUM_SUBSYSTEMS, invconst.flagSubSystemSlot0)]
    shipName = recordSet.Get(fitting.shipTypeID)._typeName
    mysStringList = [SHIP_AND_FITTINGNAME_TEMPLATE % (shipName, fitting.name)]
    for numSlots, firstSlot in slotTuples:
        tempStringList = []
        emptyString = emptySlotDict.get(firstSlot, '')
        for i in xrange(numSlots):
            currentSlotIdx = firstSlot + i
            moduleInfo = fitDataFlagDict.get(currentSlotIdx, None)
            if moduleInfo:
                mysStringList += tempStringList
                tempStringList = []
                typeID = moduleInfo[0]
                mysStringList.append(recordSet.Get(typeID)._typeName)
            else:
                tempStringList.append(emptyString)

        mysStringList.append('')

    for location in (droneItems, cargoItems):
        for eachItem in location:
            typeID = eachItem[0]
            typeName = recordSet.Get(typeID)._typeName
            lineText = EXTRA_ITEM_TEMPLATE % (typeName, eachItem[2])
            mysStringList.append(lineText)

        mysStringList.append('')

    fittingString = LINEBREAK.join(mysStringList)
    return fittingString
