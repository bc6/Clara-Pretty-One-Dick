#Embedded file name: inventorycommon\types.py


def _GetType(typeID):
    return cfg.invtypes.Get(typeID)


def GetGroupID(typeID):
    return _GetType(typeID).groupID


def GetCategoryID(typeID):
    return _GetType(typeID).categoryID


def GetVolume(typeID):
    return _GetType(typeID).volume


def GetIconID(typeID):
    return _GetType(typeID).iconID


def GetName(typeID):
    return _GetType(typeID).name


def GetCapacity(typeID):
    return _GetType(typeID).capacity


def GetBasePrice(typeID):
    return _GetType(typeID).basePrice


def GetPortionSize(typeID):
    return _GetType(typeID).portionSize


def GetAveragePrice(typeID):
    return _GetType(typeID).averagePrice


def GetMarketGroupID(typeID):
    return _GetType(typeID).marketGroupID


def GetTypeName(typeID):
    return _GetType(typeID).typeName


def GetDescription(typeID):
    return _GetType(typeID).description
