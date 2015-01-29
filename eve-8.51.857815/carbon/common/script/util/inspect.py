#Embedded file name: carbon/common/script/util\inspect.py
"""
This module contains helper functions to extend the Python inspect
module, and make some of its functionality easier to access and use.
"""
import types

def IsClassMethod(func):
    """
    Given an object, determine if that object is a class method.
    """
    if type(func) != types.MethodType:
        return False
    if type(func.im_self) is types.TypeType:
        return True
    return False


def IsStaticMethod(func):
    """
    There doesn't seem to be a good way to differentiate between
    a static method an a plain ol' function.  We'll just say that
    anything that fits the proper signature is a static method, and
    it's up to the calling code to determine if that function is
    actually a member of the class.
    """
    return type(func) == types.FunctionType


def IsNormalMethod(func):
    """
    Given an object, return true if it is a "normal" method (i.e.
    not static or class method).
    """
    if type(func) != types.MethodType:
        return False
    if type(func.im_self) is not types.TypeType:
        return True
    return False


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('util', locals())
