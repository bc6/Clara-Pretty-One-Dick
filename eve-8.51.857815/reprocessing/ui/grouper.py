#Embedded file name: reprocessing/ui\grouper.py


class Grouper(object):

    def __init__(self, groupingFunc, getGroupName):
        self.groupingFunc = groupingFunc
        self.getGroupName = getGroupName

    def GetGroupIDs(self, items):
        return {self.GetGroupID(i) for i in items}

    def GetGroupID(self, item):
        return self.groupingFunc(item.typeID)

    def GetGroupName(self, groupID):
        return self.getGroupName(groupID)


def GetCategoryGrouper():
    return Grouper(lambda typeID: cfg.invtypes.Get(typeID).categoryID, lambda categoryID: cfg.invcategories.Get(categoryID).categoryName)


def GetGroupGrouper():
    return Grouper(lambda typeID: cfg.invtypes.Get(typeID).groupID, lambda groupID: cfg.invgroups.Get(groupID).groupName)
