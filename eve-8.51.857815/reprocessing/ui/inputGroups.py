#Embedded file name: reprocessing/ui\inputGroups.py


class InputGroups(object):

    def __init__(self, inputContainer, grouper):
        self.inputContainer = inputContainer
        self.grouper = grouper
        self.groups = {}

    def _GetGroupIDsFromItems(self, items):
        newGroupIDs = self.grouper.GetGroupIDs(items)
        return newGroupIDs

    def _GetGroupsToCreate(self, newGroupIDs):
        return newGroupIDs - self.groups

    def UpdateGroups(self, items):
        groupsToCreate = set()
        newGroupIDs = set()
        for item in items:
            newGroup = self.grouper.GetGroupID(item)
            if newGroup not in self.groups:
                groupsToCreate.add(newGroup)
                self.groups[newGroup] = set()
            self.groups[newGroup].add(item.itemID)
            newGroupIDs.add(newGroup)

        if groupsToCreate:
            self.inputContainer.AddGroups(self.GetGroupParameters(groupsToCreate))
        return newGroupIDs

    def SetEfficiency(self, group, efficiency, typeIDs):
        self.inputContainer.SetEfficiency(group, efficiency, typeIDs)

    def SetTaxAndStationEfficiency(self, group, efficiency, tax):
        self.inputContainer.SetTaxAndStationEfficiency(group, efficiency, tax)

    def GetGroupParameters(self, groups):
        return [ (groupID, self.grouper.GetGroupName(groupID)) for groupID in groups ]

    def RemoveItem(self, item):
        group = self.grouper.GetGroupID(item)
        itemIDsInGroup = self.groups[group]
        itemIDsInGroup.remove(item.itemID)
        if not itemIDsInGroup:
            self.inputContainer.RemoveGroup(group)
            del self.groups[group]
        if not self.groups:
            self.inputContainer.container.overlayCont.display = True

    def ClearAllGroups(self):
        self.groups.clear()

    def HasItem(self, item):
        group = self.grouper.GetGroupID(item)
        if group in self.groups:
            return item.itemID in self.groups[group]
        return False
