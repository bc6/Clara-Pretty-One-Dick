#Embedded file name: dogma/authoring\__init__.py
from .attributeAuthoring import AttributeAuthoring as GetAttributeAuthoring
from dogma.authoring.data import DogmaData
import yaml
import dogma.const as dgmconst
import dogma.attributes
import inventorycommon.groups
import inventorycommon.types
NAME_BY_OPERATOR_ID = {dgmconst.dgmAssPostPercent: 'PostPercent',
 dgmconst.dgmAssModAdd: 'ModAdd',
 dgmconst.dgmAssModSub: 'ModSub',
 dgmconst.dgmAssPreMul: 'PreMul',
 dgmconst.dgmAssPostMul: 'PostMul',
 dgmconst.dgmAssPreDiv: 'PreDiv',
 dgmconst.dgmAssPostDiv: 'PostDiv',
 dgmconst.dgmAssPreAssignment: 'PreAssignment',
 dgmconst.dgmAssPostAssignment: 'PostAssignment'}
DOMAINS = ['shipID',
 'charID',
 'targetID',
 'otherID',
 None]

def GetReadableOperatorNames(operatorID):
    return NAME_BY_OPERATOR_ID[operatorID]


def GetFormatterForKey(key):
    return {'groupID': inventorycommon.groups.GetName,
     'skillTypeID': inventorycommon.types.GetName,
     'operator': GetReadableOperatorNames,
     'modifiedAttributeID': dogma.attributes.GetName,
     'modifyingAttributeID': dogma.attributes.GetName}.get(key, None)


def PrepareModifierInfo(modifierString):
    """
    Takes a modifier dict with extra information and transforms it to the raw data
    """
    modifierInfo = yaml.safe_load(modifierString)
    for modifierDict in modifierInfo:
        for key, value in modifierDict.iteritems():
            if GetFormatterForKey(key) is not None:
                modifierDict[key] = int(value.split(' ')[0])

    return yaml.dump(modifierInfo, default_flow_style=False)
