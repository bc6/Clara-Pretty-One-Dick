#Embedded file name: inventorycommon\__init__.py
"""
utilities for working with static inventory data. Mostly contains constants
and utility functions
"""
from const import ixSingleton, flagHiddenModifers

def IsBecomingSingleton(change):
    if ixSingleton in change:
        old_singleton, new_singleton = change[ixSingleton]
        if not old_singleton and new_singleton:
            return True
    return False


def ItemIsVisible(item):
    return item.flagID != flagHiddenModifers
