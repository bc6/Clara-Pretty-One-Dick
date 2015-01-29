#Embedded file name: inventorycommon\groups.py


def _GetGroup(groupID):
    return cfg.invgroups.Get(groupID)


def GetCategoryID(groupID):
    return _GetGroup(groupID).categoryID


def GetIconID(groupID):
    return _GetGroup(groupID).iconID


def GetName(groupID):
    return _GetGroup(groupID).name
