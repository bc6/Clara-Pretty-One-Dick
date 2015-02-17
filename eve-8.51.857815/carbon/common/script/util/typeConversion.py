#Embedded file name: carbon/common/script/util\typeConversion.py
"""
Utility to cast a variable to a type described by a string
"""
conversionTable = {'int': int,
 'float': float,
 'str': str,
 'unicode': unicode}

class ConvertVariableException(Exception):
    pass


def CastValue(type, value):
    if type in conversionTable:
        return conversionTable[type](value)
    raise ConvertVariableException, 'Unknown conversion type -%s-' % type


exports = {'util.CastValue': CastValue}
