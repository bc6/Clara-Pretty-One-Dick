#Embedded file name: carbon/common/script/util\componentCommon.py
"""
This file contains common operations for taking intialisation values from entity components as strings 
and spitting them out in a format that can be used.
"""

def UnpackStringToTuple(string, conversionFunc = None):
    """
    Takes a string and evals it into elements then makes it a tuple. A conversion function can be specified
    to force data to the correct type.
    
    Security Note: Please never call this function with input from the UI!!! Code injection danger, DANGER!
    """
    elementList = eval(string)
    if conversionFunc is not None:
        elementList = [ conversionFunc(element) for element in elementList ]
    return tuple(elementList)


exports = {'util.UnpackStringToTuple': UnpackStringToTuple}
