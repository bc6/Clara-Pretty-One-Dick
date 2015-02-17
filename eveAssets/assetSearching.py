#Embedded file name: eveAssets\assetSearching.py
from collections import defaultdict
from carbon.common.script.sys.crowset import CRowset
from carbon.common.script.util.logUtil import LogNotice
import blue

def GetSearchResults(nameHelper, conditions, itemRowset, searchtype):
    stations = defaultdict(list)
    itemsByContainerID = defaultdict(set)
    allContainersByItemIDs = {}
    failedTypeCheck = set()
    containerGroups = set([const.groupSecureCargoContainer,
     const.groupAuditLogSecureContainer,
     const.groupFreightContainer,
     const.groupCargoContainer])
    containerFlags = (const.flagNone, const.flagLocked, const.flagUnlocked)
    LogNotice('Asset search - find containers')
    for item in itemRowset:
        if item.groupID in containerGroups:
            allContainersByItemIDs[item.itemID] = item

    def AddStationIDToFakeRow(locationID, row):
        containerItem = allContainersByItemIDs.get(locationID)
        if containerItem:
            stationID = containerItem.locationID
        elif item.flagID == const.flagHangar:
            stationID = locationID
        else:
            return
        setattr(row, 'stationID', stationID)

    LogNotice('Asset Search - start search')
    for item in itemRowset:
        try:
            invType = cfg.invtypes.Get(item.typeID)
        except KeyError:
            continue

        if item.stacksize == 0:
            continue
        if searchtype:
            if invType.typeID in failedTypeCheck:
                continue
            elif not MatchesTypeChecks(nameHelper, invType, searchtype):
                failedTypeCheck.add(invType.typeID)
                continue
            AddStationIDToFakeRow(item.locationID, item)
        else:
            AddStationIDToFakeRow(item.locationID, item)
            if not MatchesSearchCriteria(item, conditions):
                continue
        if item.flagID in containerFlags:
            itemsByContainerID[item.locationID].add(item)
        else:
            stations[item.locationID].append(item)

    LogNotice('Asset Search - Searching done')
    return (allContainersByItemIDs, itemsByContainerID, stations)


def MatchesTypeChecks(nameHelper, invType, searchtype):
    if nameHelper.GetTypeName(invType.typeID).find(searchtype) > -1:
        return True
    elif nameHelper.GetGroupName(invType.groupID).find(searchtype) > -1:
        return True
    elif nameHelper.GetCategoryName(invType.categoryID).find(searchtype) > -1:
        return True
    else:
        return False


def MatchesSearchCriteria(item, conditions):
    if not all((condition(item) for condition in conditions)):
        return False
    return True


def GetFakeRowset(nameHelper, allitems):
    rowDescriptor = blue.DBRowDescriptor((('itemID', const.DBTYPE_I8),
     ('typeID', const.DBTYPE_I4),
     ('ownerID', const.DBTYPE_I4),
     ('groupID', const.DBTYPE_I4),
     ('categoryID', const.DBTYPE_I4),
     ('quantity', const.DBTYPE_I4),
     ('singleton', const.DBTYPE_I4),
     ('stacksize', const.DBTYPE_I4),
     ('locationID', const.DBTYPE_I8),
     ('flagID', const.DBTYPE_I2),
     ('stationID', const.DBTYPE_I4)))
    itemRowset = CRowset(rowDescriptor, [])
    for eachItem in allitems:
        try:
            itemRowset.InsertNew(GetListForFakeItemRow(nameHelper, eachItem))
        except KeyError:
            pass

    return itemRowset


def GetListForFakeItemRow(nameHelper, item):
    line = [item.itemID,
     item.typeID,
     session.charid,
     nameHelper.GetGroupIDFromTypeID(item.typeID),
     nameHelper.GetCategoryIDFromTypeID(item.typeID),
     item.quantity,
     -item.quantity if item.quantity < 0 else 0,
     1 if item.quantity < 0 else item.quantity,
     item.locationID,
     item.flagID,
     None]
    return line
