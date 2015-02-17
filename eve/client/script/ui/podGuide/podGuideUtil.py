#Embedded file name: eve/client/script/ui/podGuide\podGuideUtil.py
"""
    Utility functions for the podguide/manual
"""
from collections import OrderedDict, defaultdict
import fsdSchemas.binaryLoader as fsdBinaryLoader

def GetTerms():
    groupDict = defaultdict(set)
    fsdData = GetFSDInfoForTerms()
    for eachTermID, eachTerm in fsdData.iteritems():
        groupDict[eachTerm.groupID].add(eachTerm)

    return groupDict


def GetTermByID(termID):
    allTerms = GetFSDInfoForTerms()
    return allTerms.Get(termID)


def GetTermShortText(termID):
    term = GetTermByID(termID)
    return term.shortTextID


def GetFSDInfoForTerms():
    data = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/podGuide.static')
    return data


def GetFSDInfoForGroups():
    data = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/podGuideGroups.static')
    return data


def GetGroupNames(groupKey):
    groupsInfo = GetFSDInfoForGroups()
    groupNameID = groupsInfo.Get(groupKey).groupName
    return groupNameID


def GetCategories():
    groupsByCategory = defaultdict(set)
    allGroupsInfo = GetFSDInfoForGroups()
    for groupID, groupInfo in allGroupsInfo.iteritems():
        if groupInfo.groupType == 'group':
            groupsByCategory[groupInfo.belongsToGroup].add(groupInfo)

    categoryInfo = defaultdict(dict)
    for groupID, groupInfo in allGroupsInfo.iteritems():
        if groupInfo.groupType == 'category':
            categoryInfo[groupID]['categoryInfo'] = groupInfo
            categoryInfo[groupID]['subgroups'] = groupsByCategory.get(groupID, [])

    return categoryInfo


def OpenPodGuide(termID = None):
    from eve.client.script.ui.podGuide.podGuideUI import PodGuideWindow
    wnd = PodGuideWindow.GetIfOpen()
    if wnd:
        wnd.LoadPanelByID(termID=termID)
    else:
        PodGuideWindow.Open(termID=termID)
