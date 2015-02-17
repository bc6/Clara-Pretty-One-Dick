#Embedded file name: overviewPresets\overviewPresetUtil.py
"""
    This file contains some utility functions for the overview presets, for storing them and sharing with others
"""
import hashlib
import yaml
MAX_SHARED_PRESETS = 15
MAX_TAB_NUM = 5

def GetDeterministicListFromDict(inputDict):
    outputList = [ (x, y) for x, y in inputDict.iteritems() ]
    outputList.sort()
    return outputList


def GetDictFromList(inputList):
    return {x:y for x, y in inputList}


def ReplaceInnerListsWithDicts(parentDict):
    for tabIdx, tabValue in parentDict.iteritems():
        newTabValue = GetDictFromList(tabValue)
        parentDict[tabIdx] = newTabValue

    return parentDict


def GetOrderedListFromDict(inputDict, orderedKeys):
    dictCopy = inputDict.copy()
    outputList = []
    for eachKey in orderedKeys:
        dictValue = dictCopy.pop(eachKey, None)
        if dictValue:
            outputList.append(dictValue)

    outputList += dictCopy.values()
    return outputList


def GetHashvalueFromDict(inputDict):
    inputList = GetDeterministicListFromDict(inputDict)
    hashvalue = GetHashvalueForList(inputList)
    return hashvalue


def GetYamlStringFromDict(inputDict):
    inputList = GetDeterministicListFromDict(inputDict)
    yamlString = GetYamlStringFromList(inputList)
    return yamlString


def GetYamlStringFromList(inputList):
    yamlString = yaml.safe_dump(inputList)
    return yamlString


def GetHashvalueForList(inputList):
    yamlString = GetYamlStringFromList(inputList)
    return GetHashValueFromString(yamlString)


def GetHashValueFromString(yamlString):
    hashvalue = hashlib.sha1(yamlString).hexdigest()
    return hashvalue


def EncodeKeyInDict(inputDict):
    outputDict = {}
    for key, value in inputDict.iteritems():
        newKey = '%s_%s' % (key[0], key[1])
        outputDict[newKey] = value

    return outputDict


def DecodeKeyInDict(inputDict):
    """ assumes first element in key is string, other int """
    outputDict = {}
    for key, value in inputDict.iteritems():
        parts = key.split('_')
        newKey = (parts[0], int(parts[1]))
        outputDict[newKey] = value

    return outputDict


def IsPresetTheSame(preset1, preset2):

    def CheckPreset(pA, pB):
        for pAKey, pAValue in pA.iteritems():
            pBValue = pB.get(pAKey, -1)
            if pBValue == -1 and not pAValue:
                continue
            if pBValue != pAValue:
                return False

        return True

    allP1InP2 = CheckPreset(preset1, preset2)
    allP2InP1 = CheckPreset(preset2, preset1)
    return allP1InP2 and allP2InP1


def ReorderList(parentDict, namesToReorder):
    for reorderName in namesToReorder:
        listToReorder = parentDict.get(reorderName, None)
        if listToReorder is None:
            continue
        listToReorder.sort()
