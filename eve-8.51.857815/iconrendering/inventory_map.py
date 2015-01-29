#Embedded file name: iconrendering\inventory_map.py
"""
Contains methods for getting groups and categories from the DB
"""
import pyodbc
import industry
cache = {}

def memoize(function):
    """
    Yet another memoize decorator.
    The cache is on the module level.
    """

    def wrapper(*args):
        key = (function.__name__,) + args
        if key in cache:
            return cache[key]
        else:
            ret = function(*args)
            cache[key] = ret
            return ret

    return wrapper


class InventoryMapper(object):

    def __init__(self, branchID = 1):
        self.branchID = branchID
        self.typeData = {}
        self.dogmaAttributeValues = None
        self.InitializeData()

    def InitializeData(self):
        """Initializes the typeID, groupID, categoryID and raceID in a dict for
        fast lookup."""
        catQuery = 'select groupID = M.keyID, D.categoryID\n                      from zstatic.mappings M\n                       inner join inventory.groupsTx D on D.dataID = M.dataID\n                      where M.branchID = ? AND M.tableID = 600002'
        categories = self._ConnectAndExecute(catQuery, self.branchID).fetchall()
        categoryByGroup = {}
        for pair in categories:
            categoryByGroup[pair[0]] = pair[1]

        groupQuery = 'select typeID = M.keyID, D.groupID, D.raceID\n                        from zstatic.mappings M\n                        inner join inventory.typesTx D on D.dataID = M.dataID\n                        where M.branchID = ? AND M.tableID = 600004'
        groups = self._ConnectAndExecute(groupQuery, self.branchID).fetchall()
        for typeID, groupID, raceID in groups:
            self.typeData[typeID] = (groupID, categoryByGroup[groupID], raceID)

        self.blueprints = industry.BlueprintStorage()

    def _ConnectAndExecute(self, execstr, params = None):
        connection = pyodbc.connect('DRIVER={SQL Server};SERVER=sqldev1is;DATABASE=ebs_ADAM;Trusted_Connection=yes')
        if params:
            result = connection.execute(execstr, params)
        else:
            result = connection.execute(execstr)
        return result

    def _ConstructQuery(self, selectStr, fromStr, whereStr = None):
        """Constructs a query string.
        """
        selectStr = 'SELECT %s' % selectStr
        fromStr = 'FROM zstatic.mappings M INNER JOIN %s D ON D.dataID = M.dataID' % fromStr
        if whereStr:
            whereStr = 'WHERE %s and M.branchID = %d' % (whereStr, self.branchID)
        else:
            whereStr = 'WHERE M.branchID = %d' % self.branchID
        return '%s %s %s ' % (selectStr, fromStr, whereStr)

    @memoize
    def GetDogmaAttributeForTypeID(self, attributeID, typeID):
        """
        Returns a dogma attribute for a typeID.
        """
        key = (attributeID, typeID)
        if self.dogmaAttributeValues is not None:
            return self.dogmaAttributeValues.get(key, None)
        query = self._ConstructQuery('D.valueFloat, D.valueInt, D.attributeID, D.typeID', 'dogma.typeAttributesTx')
        self.dogmaAttributeValues = {}
        for floatVal, intVal, attribID, tID in self._ConnectAndExecute(query).fetchall():
            if attribID is None:
                continue
            if tID is None:
                continue
            k = (int(attribID), int(tID))
            if floatVal is not None:
                self.dogmaAttributeValues[k] = float(floatVal)
            else:
                self.dogmaAttributeValues[k] = int(intVal)

        return self.dogmaAttributeValues.get(key, None)

    def GetAllTypesData(self):
        for typeID, (groupID, categoryID, raceID) in self.typeData.iteritems():
            yield (typeID,
             groupID,
             categoryID,
             raceID)

    def GetTypesData(self, listOfTypes):

        def GetTypesForList():
            for typeID in listOfTypes:
                groupID, categoryID, raceID = self.typeData.get(typeID)
                yield (typeID,
                 groupID,
                 categoryID,
                 raceID)

        return GetTypesForList()

    def GetTypeData(self, typeID):
        return self.typeData.get(typeID, None)

    @memoize
    def GetBlueprintProductType(self, typeID):
        try:
            return self.blueprints[typeID].productTypeID
        except KeyError:
            return None

    @memoize
    def GetBlueprintThatMakesType(self, typeID):
        try:
            return self.blueprints.index('productTypeID', typeID).blueprintTypeID
        except KeyError:
            return None

    def GetGroupAndCategoryByType(self, typeID):
        entry = self.typeData.get(typeID, None)
        if entry:
            return (entry[0], entry[1])
