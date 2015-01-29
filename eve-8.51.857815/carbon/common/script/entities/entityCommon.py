#Embedded file name: carbon/common/script/entities\entityCommon.py
"""
This file contains all centralized utility functions for interfacing with the entity system.
"""
import cef
import log
import types
import utillib as util
from carbon.common.script.cef.baseComponentView import BaseComponentView

def GetComponentName(componentID):
    """
    Important Distinction:
      This gets the CODE name of the component, that is used as a real code variable name.
    It's QUITE urgent that those code names are never changed once defined,
      due to a bunch of weird things the components do, and how they're used.
    """
    componentView = BaseComponentView.GetComponentViewByID(componentID)
    if type(componentID) is str:
        return componentID
    if componentView is None:
        log.LogTraceback('UNKNOWN COMPONENT %s' % componentID)
        return 'UNKNOWN COMPONENT %s' % componentID
    return componentView.__COMPONENT_CODE_NAME__


def GetParentTypeString(parentType):
    if parentType == const.cef.PARENT_TYPEID:
        return 'Type'
    elif parentType == const.cef.PARENT_GROUPID:
        return 'Group'
    elif parentType == const.cef.PARENT_CATEGORYID:
        return 'Category'
    else:
        return 'UNKNOWN'


def GetIngredientInitialValue(initValueRow, tableName = const.cef.INGREDIENT_INITS_TABLE_FULL_NAME):
    """
        This method takes in a dbrow from the cache or a SQL statement,
        drawn from the zentity.ingredientInitialValues view.
        It returns a value representing the value of the row,
        which can be drawn from the valueInt, valueFloat or valueString
        columns depending on the pattern of NULLs.
    
        If all columns are NULL, then this method returns None.
    """
    if initValueRow.valueInt is not None:
        return initValueRow.valueInt
    elif initValueRow.valueFloat is not None:
        return initValueRow.valueFloat
    elif initValueRow.needsTranslation:
        return (initValueRow.valueString, tableName + '.valueString', initValueRow.dataID)
    else:
        return initValueRow.valueString


def GetDBInitValuesFromValue(value):
    """
        This method takes a value of some arbitrary type and returns a KeyVal
        representing the values that should be inserted into the database's
        zentity.ingredientInitialValues table in the valueInt, valueFloat and
        valueString columns.
    
        If the value is not explicitly an int or float, it will try to coerce
        the value via a string into those types. Failing that, it will make
        the value a string and store it as such.
    
        Empty/whitespace-only strings will be interpreted as NULLs in all
        columns.
    """
    if type(value) is types.IntType:
        return util.KeyVal(valueInt=value, valueFloat=None, valueString=None)
    if type(value) is types.FloatType:
        return util.KeyVal(valueInt=None, valueFloat=value, valueString=None)
    if type(value) is not types.StringType:
        try:
            value = str(value)
        except ValueError as e:
            return util.KeyVal(valueInt=None, valueFloat=None, valueString=None)

    try:
        valueInt = int(value)
    except ValueError as e:
        valueInt = None

    if valueInt is not None:
        valueFloat = None
    else:
        try:
            valueFloat = float(value)
        except ValueError as e:
            valueFloat = None

    if valueInt is not None or valueFloat is not None or value.strip() == '':
        value = None
    return util.KeyVal(valueInt=valueInt, valueFloat=valueFloat, valueString=value)


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('entityCommon', locals())
