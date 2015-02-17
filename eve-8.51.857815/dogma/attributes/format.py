#Embedded file name: dogma/attributes\format.py
import math
from eve.common.script.util.eveFormat import FmtDist2
from inventorycommon import types, groups
from carbon.common.lib.const import SEC, HOUR
from localization import GetByLabel
import localization
from carbon.common.script.util import format
from dogma import const as dogmaConst, attributes, units
from itertoolsext import Bundle
SIZE_DICT = {1: 'UI/InfoWindow/SmallSize',
 2: 'UI/InfoWindow/MediumSize',
 3: 'UI/InfoWindow/LargeSize',
 4: 'UI/InfoWindow/XLargeSize'}
GENDER_DICT = {1: 'UI/Common/Gender/Male',
 2: 'UI/Common/Gender/Unisex',
 3: 'UI/Common/Gender/Female'}

def FormatUnit(unitID, fmt = 'd'):
    if unitID in (dogmaConst.unitTime, dogmaConst.unitLength):
        return ''
    if units.HasUnit(unitID) and fmt == 'd':
        return units.GetDisplayName(unitID)
    return ''


def FormatValue(value, unitID = None):
    if value is None:
        return
    if unitID == dogmaConst.unitTime:
        return format.FmtDate(long(value * SEC), 'll')
    if unitID == dogmaConst.unitMilliseconds:
        return '%.2f' % (value / 1000.0)
    if unitID == dogmaConst.unitLength:
        return FmtDist2(value)
    if unitID == dogmaConst.unitHour:
        return format.FmtDate(long(value * HOUR), 'll')
    if unitID == dogmaConst.unitMoney:
        return format.FmtAmt(value)
    if unitID in (dogmaConst.unitInverseAbsolutePercent, dogmaConst.unitInversedModifierPercent):
        value = float(round(1.0 - value, 6)) * 100
    if unitID == dogmaConst.unitModifierPercent:
        value = abs(value * 100 - 100) * (-1 if value < 1.0 else 1)
    if unitID == dogmaConst.unitAbsolutePercent:
        value *= 100
    if type(value) is str:
        value = eval(value)
    if unitID == dogmaConst.unitMass:
        return localization.formatters.FormatNumeric(value, decimalPlaces=0, useGrouping=True)
    if type(value) is not str and value - int(value) == 0:
        return format.FmtAmt(value)
    if unitID == dogmaConst.unitAttributePoints:
        return round(value, 1)
    if unitID == dogmaConst.unitMaxVelocity:
        return localization.formatters.FormatNumeric(value, decimalPlaces=2, useGrouping=True)
    if unitID in (dogmaConst.unitHitpoints,
     dogmaConst.unitVolume,
     dogmaConst.unitInverseAbsolutePercent,
     dogmaConst.unitInversedModifierPercent):
        if value < 1:
            significantDigits = 2 if unitID == dogmaConst.unitHitpoints else 3
            decimalPlaces = int(-math.ceil(math.log10(value)) + significantDigits)
        else:
            decimalPlaces = 2
        return localization.formatters.FormatNumeric(value, decimalPlaces=decimalPlaces, useGrouping=True)
    return value


def GetFormatAndValue(attributeType, value):
    attrUnit = FormatUnit(attributeType.unitID)
    if attributeType.unitID == dogmaConst.unitGroupID:
        value = groups.GetName(value)
    elif attributeType.unitID == dogmaConst.unitTypeID:
        value = types.GetName(value)
    elif attributeType.unitID == dogmaConst.unitSizeclass:
        value = GetByLabel(SIZE_DICT.get(int(value)))
    elif attributeType.unitID == dogmaConst.unitAttributeID:
        value = attributes.GetDisplayName(value)
    elif attributeType.attributeID == dogmaConst.attributeVolume:
        value = value
    elif attributeType.unitID == dogmaConst.unitLevel:
        value = GetByLabel('UI/InfoWindow/TechLevelX', numLevel=format.FmtAmt(value))
    elif attributeType.unitID == dogmaConst.unitBoolean:
        if int(value) == 1:
            value = GetByLabel('UI/Common/True')
        else:
            value = GetByLabel('UI/Common/False')
    elif attributeType.unitID == dogmaConst.unitSlot:
        value = GetByLabel('UI/InfoWindow/SlotX', slotNum=format.FmtAmt(value))
    elif attributeType.unitID == dogmaConst.unitBonus:
        if value >= 0:
            value = '%s%s' % (attrUnit, value)
    elif attributeType.unitID == dogmaConst.unitGender:
        value = GetByLabel(GENDER_DICT.get(int(value)))
    else:
        value = GetByLabel('UI/InfoWindow/ValueAndUnit', value=FormatValue(value, attributeType.unitID), unit=attrUnit)
    return value


def GetFormattedAttributeAndValue(attributeID, value):
    attribute = attributes.GetAttribute(attributeID)
    if not attribute.published or not value:
        return
    iconID = attribute.iconID
    infoTypeID = None
    if not iconID:
        if attribute.unitID == dogmaConst.unitTypeID:
            iconID = types.GetIconID(value)
            infoTypeID = value
        if attribute.unitID == dogmaConst.unitGroupID:
            iconID = groups.GetIconID(value)
        if attribute.unitID == dogmaConst.unitAttributeID:
            iconID = attributes.GetIconID(value)
    value = GetFormatAndValue(attribute, value)
    return Bundle(displayName=attribute.displayName, value=value, iconID=iconID, infoTypeID=infoTypeID)
