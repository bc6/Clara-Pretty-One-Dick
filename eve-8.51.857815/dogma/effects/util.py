#Embedded file name: dogma/effects\util.py
from dogma.effects import modifiers
from dogma.effects.modifiereffect import ModifierEffect

def _GetItemModifier(effectDict):
    return modifiers.ItemModifier(effectDict['operator'], effectDict['domain'], effectDict['modifiedAttributeID'], effectDict['modifyingAttributeID'])


def _GetLocationRequiredSkillModifier(effectDict):
    return modifiers.LocationRequiredSkillModifier(effectDict['operator'], effectDict['domain'], effectDict['modifiedAttributeID'], effectDict['modifyingAttributeID'], effectDict['skillTypeID'])


def _GetOwnerRequiredSkillModifier(effectDict):
    return modifiers.OwnerRequiredSkillModifier(effectDict['operator'], effectDict['domain'], effectDict['modifiedAttributeID'], effectDict['modifyingAttributeID'], effectDict['skillTypeID'])


def _GetLocationModifier(effectDict):
    return modifiers.LocationModifier(effectDict['operator'], effectDict['domain'], effectDict['modifiedAttributeID'], effectDict['modifyingAttributeID'])


def _GetLocationGroupModifier(effectDict):
    return modifiers.LocationGroupModifier(effectDict['operator'], effectDict['domain'], effectDict['modifiedAttributeID'], effectDict['modifyingAttributeID'], effectDict['groupID'])


def _GetGangItemModifier(effectDict):
    return modifiers.GangItemModifier(effectDict['operator'], 'shipID', effectDict['modifiedAttributeID'], effectDict['modifyingAttributeID'])


def _GetGangRequiredSkillModifier(effectDict):
    return modifiers.GangRequiredSkillModifier(effectDict['operator'], 'shipID', effectDict['modifiedAttributeID'], effectDict['modifyingAttributeID'], effectDict['skillTypeID'])


modifierGetterByType = {'ItemModifier': _GetItemModifier,
 'LocationRequiredSkillModifier': _GetLocationRequiredSkillModifier,
 'OwnerRequiredSkillModifier': _GetOwnerRequiredSkillModifier,
 'LocationModifier': _GetLocationModifier,
 'LocationGroupModifier': _GetLocationGroupModifier,
 'GangItemModifier': _GetGangItemModifier,
 'GangRequiredSkillModifier': _GetGangRequiredSkillModifier}

def CreateEffect(modifierInfo):
    """
    :type modifierInfo: list of dict
    """
    mods = []
    for effectDict in modifierInfo:
        modifierType = effectDict['func']
        mods.append(modifierGetterByType[modifierType](effectDict))

    return ModifierEffect(mods)
