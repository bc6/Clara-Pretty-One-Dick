#Embedded file name: dogma/authoring\expressions.py
from operator import itemgetter
import yaml
from dogma.authoring import DOMAINS, NAME_BY_OPERATOR_ID
from dogma.effects import EXPRESSIONS
import inventorycommon.types
import inventorycommon.groups
import inventorycommon.const as invconst
ALL_ELEMENTS = ['func',
 'domain',
 'operator',
 'skillTypeID',
 'groupID',
 'modifyingAttributeID',
 'modifiedAttributeID']

class BaseModifier(object):
    __modifier_name__ = ''
    __elements__ = None

    def __init__(self, **defaultArgs):
        self.defaultArgs = defaultArgs

    def GetInfoForForm(self):
        attributes = self._GetAttributeOptions()
        return [ (elementName, options, selected) for elementName, options, selected in (('func', [ (k, k) for k in EXPRESSIONS ], self.defaultArgs.get('func', '')),
         ('domain', [ (k, k) for k in DOMAINS ], self.defaultArgs.get('domain', 'shipID')),
         ('operator', [ (k, v) for k, v in NAME_BY_OPERATOR_ID.iteritems() ], self.defaultArgs.get('operator')),
         ('skillTypeID', self._GetSkillTypeOptions(), self.defaultArgs.get('skillTypeID')),
         ('groupID', self._GetGroupOptions(), self.defaultArgs.get('groupID')),
         ('modifyingAttributeID', attributes, self.defaultArgs.get('modifyingAttributeID')),
         ('modifiedAttributeID', attributes, self.defaultArgs.get('modifiedAttributeID'))) if self._IsElementValid(elementName) ]

    def GetInfoForSelect(self):
        """
        Gets all the info for the select boxes in the form of list
        """
        ret = []
        for elementName, options, defaultValue in self.GetInfoForForm():
            ret.append((elementName, options, defaultValue))

        return ret

    def _GetFunc(self):
        return self.__modifier_name__

    def _GetAttributeOptions(self):
        return self._Sort([ (attributeID, attrib.attributeName) for attributeID, attrib in cfg.dgmattribs.data.iteritems() ])

    def _GetSkillTypeOptions(self):
        return self._Sort([ (typeID, inventorycommon.types.GetName(typeID)) for typeID in cfg.invtypes.data.iterkeys() if inventorycommon.types.GetCategoryID(typeID) == invconst.categorySkill ])

    def _GetGroupOptions(self):
        return self._Sort([ (groupID, inventorycommon.groups.GetName(groupID)) for groupID in cfg.invgroups.data.iterkeys() ])

    def _IsElementValid(self, elementName):
        if self.__elements__ is None:
            return True
        return elementName in self.__elements__

    def RemoveRedundantElements(self, formItems):
        ret = {}
        for elementName, value in formItems.iteritems():
            if elementName in self.__elements__:
                ret[elementName] = value

        return ret

    def _Sort(self, keyValuePairs):
        return sorted(keyValuePairs, key=itemgetter(1))


class ItemModifier(BaseModifier):
    __modifier_name__ = 'ItemModifier'
    __elements__ = ['func',
     'domain',
     'operator',
     'modifyingAttributeID',
     'modifiedAttributeID']


def _GetRequiredSkillElements():
    return ['func',
     'domain',
     'operator',
     'skillTypeID',
     'modifyingAttributeID',
     'modifiedAttributeID']


class LocationRequiredSkillModifier(BaseModifier):
    __modifier_name__ = 'LocationRequiredSkillModifier'
    __elements__ = _GetRequiredSkillElements()


class OwnerRequiredSkillModifier(BaseModifier):
    __modifier_name__ = 'OwnerRequiredSkillModifier'
    __elements__ = _GetRequiredSkillElements()


class GangRequiredSkillModifier(BaseModifier):
    __modifier_name__ = 'GangRequiredSkillModifier'
    __elements__ = ['func',
     'operator',
     'skillTypeID',
     'modifyingAttributeID',
     'modifiedAttributeID']


class LocationGroupModifier(BaseModifier):
    __modifier_name__ = 'LocationGroupModifier'
    __elements__ = ['func',
     'domain',
     'operator',
     'groupID',
     'modifyingAttributeID',
     'modifiedAttributeID']


class GangGroupModifier(BaseModifier):
    __modifier_name__ = 'GangGroupModifier'
    __elements__ = ['func',
     'operator',
     'groupID',
     'modifyingAttributeID',
     'modifiedAttributeID']


class GangItemModifier(BaseModifier):
    __modifier_name__ = 'GangItemModifier'
    __elements__ = ['func',
     'operator',
     'modifyingAttributeID',
     'modifiedAttributeID']


def _GetExpression(expressionType):
    classType = {c.__modifier_name__:c for c in (ItemModifier,
     LocationRequiredSkillModifier,
     OwnerRequiredSkillModifier,
     GangRequiredSkillModifier,
     LocationGroupModifier,
     GangGroupModifier,
     GangItemModifier)}
    expression = classType[expressionType]()
    return expression


def GetInfoForForm(expressionType, **defaultArgs):
    return _GetExpression(expressionType).GetInfoForForm(**defaultArgs)


def GetFields(expressionType, **defaultArgs):
    expression = _GetExpression(expressionType, **defaultArgs)
    return [ (element, element in expression.__elements__) for element in ALL_ELEMENTS ]


def RemoveRedundantElements(formItems):
    expression = _GetExpression(formItems['func'])
    return expression.RemoveRedundantElements(formItems)


def UpdateExpression(expressionYaml, newExpression, idx):
    if expressionYaml:
        expressions = LoadExpressions(expressionYaml)
        if idx is None:
            expressions.append(newExpression)
        else:
            expressions[idx] = newExpression
    else:
        expressions = [newExpression]
    return expressions


def LoadExpressions(expressionYaml):
    return yaml.safe_load(expressionYaml)


def DumpExpression(expressions):
    return yaml.safe_dump(expressions, default_flow_style=False)
