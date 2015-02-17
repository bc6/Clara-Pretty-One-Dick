#Embedded file name: localizationBSD\search.py
from wrappers.project import Project
from wrappers.messageGroup import MessageGroup
from wrappers.message import Message
from wrappers.messageText import MessageText
SEARCH_BY_MESSAGEID = 0
SEARCH_BY_GROUPID = 1
SEARCH_BY_GROUPNAME = 2
SEARCH_BY_LABEL = 3
SEARCH_BY_DESCRIPTION = 4
SEARCH_BY_TEXT = 5
SEARCH_BY_STATUS = 6

def _SearchById(searchType, searchText):
    try:
        idList = map(int, searchText.split(','))
    except ValueError as e:
        raise RuntimeError('Error converting input to ID list: ' + e.message)

    if searchType == SEARCH_BY_MESSAGEID:
        idList = filter(Message.Get, idList)
    elif searchType == SEARCH_BY_GROUPID:
        idList = filter(MessageGroup.Get, idList)
    return list(set(idList))


def _SearchByStatus(statusID, projectID, rootGroupID, searchLanguageIDs = None):
    if isinstance(statusID, basestring):
        try:
            statusID = int(statusID)
        except ValueError as e:
            raise ValueError('Error converting search text to a valid statusID: %s' % (statusID, e.message))

    msgs = MessageText.GetWithFilter(statusID=statusID)
    if searchLanguageIDs:
        msgs = filter(lambda mt: mt.numericLanguageID in searchLanguageIDs, msgs)
    if max(rootGroupID, projectID) > 0:
        if rootGroupID > 0:
            if not MessageGroup.Get(rootGroupID):
                raise ValueError('Unknown root group ID %d' % rootGroupID)
            filterGroups = MessageGroup.GetVisibleGroupsByParentID(rootGroupID, projectID if projectID > 0 else None)
        elif projectID > 0:
            if not Project.Get(projectID):
                raise ValueError('Unknown project ID %d' % projectID)
            filterGroups = Project.Get(projectID).GetAllGroupIDs()
        msgs = filter(lambda mt: Message.Get(mt.messageID).groupID in filterGroups, msgs)
    return list(set([ x.messageID for x in msgs ]))


class _SearchWithDatabaseQuery(object):

    def __init__(self, exactPhraseOnly, caseSensitive, projectID = -1, rootGroupID = -1, languageIDList = None):
        self.exactPhraseOnly = exactPhraseOnly
        self.caseSensitive = caseSensitive
        self.projectID = projectID
        self.rootGroupID = rootGroupID
        if languageIDList:
            self.languageIDList = map(str, languageIDList)
        else:
            self.languageIDList = None

    def _StartSqlQuery(self, columnName, tableName):
        """
            Builds the beginning "SELECT" portion of the sql query, can support either selecting messageIDs from
            zlocalization.messages or groupIDs from zlocalization.messageGroups. Properly filters the initial
            select list based on rootGroupID and projectID, if applicable.
        """
        if self.rootGroupID > 0:
            SQL = "\n                ; WITH  GroupsRecursive (groupID, Ids) AS (\n                    SELECT G.groupID, CONVERT(VARCHAR(MAX), G.groupID) AS LabelIds\n                      FROM zlocalization.messageGroups G\n                     WHERE G.groupID = %d\n                    UNION ALL\n                    SELECT G1.groupID, Ids + '/' + CONVERT(VARCHAR(MAX), G1.groupID) As LabelIds\n                      FROM zlocalization.messageGroups G1 INNER JOIN GroupsRecursive G2 ON G1.parentID = G2.groupID\n                )\n                SELECT DISTINCT T.%s\n                  FROM %s T\n                 INNER JOIN GroupsRecursive RG ON T.groupID = RG.groupID\n            " % (self.rootGroupID, columnName, tableName)
        else:
            SQL = '\n                SELECT DISTINCT T.%s\n                  FROM %s T\n            ' % (columnName, tableName)
        if self.projectID > 0:
            SQL += '\n                INNER JOIN zlocalization.projectsToGroups PG ON T.groupID = PG.groupID AND PG.projectID=%d\n            ' % self.projectID
        return SQL

    def _GetWhereClause(self, columnName, searchText):
        whereTemplate = '%s'
        searchText = searchText.replace("'", "''")
        searchText = searchText.replace('%', '\\%')
        searchText = searchText.replace('_', '\\_')
        searchText = searchText.replace('[', '\\[')
        if not self.caseSensitive:
            searchText = '%s' % searchText.upper()
            whereTemplate = 'UPPER(%s)'
        if self.exactPhraseOnly:
            searchText = '%[.,?:<>" ()]' + searchText + '[.,?:<>" ()]%'
            whereTemplate = "' ' + %s + ' '" % whereTemplate
        else:
            searchText = '%' + searchText + '%'
        return "\n            WHERE %s LIKE N'%s' ESCAPE '\\'\n        " % (whereTemplate % columnName, searchText)

    def DoSearch(self, searchType, searchText):
        idColumn, table, textColumn = {SEARCH_BY_GROUPNAME: ('groupID', 'zlocalization.messageGroups', 'T.groupName'),
         SEARCH_BY_LABEL: ('messageID', 'zlocalization.messages', 'T.label'),
         SEARCH_BY_DESCRIPTION: ('messageID', 'zlocalization.messages', 'T.context'),
         SEARCH_BY_TEXT: ('messageID', 'zlocalization.messages', 'MT.text')}[searchType]
        SQL = self._StartSqlQuery(idColumn, table)
        if searchType == SEARCH_BY_TEXT:
            SQL += '\n                INNER JOIN zlocalization.messageTexts MT ON T.messageID = MT.messageID\n            '
            if self.languageIDList:
                SQL += ' AND MT.numericLanguageID IN (%s)\n                ' % ','.join(self.languageIDList)
        SQL += self._GetWhereClause(textColumn, searchText)
        retRows = sm.GetService('DB2').SQL(SQL)
        return [ getattr(x, idColumn) for x in retRows ]


def PerformSearch(searchType, searchText, searchLanguageIDs = None, projectID = -1, rootGroupID = -1, exactPhraseOnly = False, caseSensitive = False):
    """
        Performs a search by calling the correct search method from this file. Returns a list of messageID's followed
        by a list of groupID's.
    """
    msgs = []
    groups = []
    if searchType in (SEARCH_BY_MESSAGEID, SEARCH_BY_GROUPID):
        ret = _SearchById(searchType, searchText)
    elif searchType == SEARCH_BY_STATUS:
        ret = _SearchByStatus(searchText, projectID, rootGroupID, searchLanguageIDs)
    else:
        dbQueryRunner = _SearchWithDatabaseQuery(exactPhraseOnly, caseSensitive, projectID, rootGroupID, searchLanguageIDs)
        ret = dbQueryRunner.DoSearch(searchType, searchText)
    if searchType in (SEARCH_BY_GROUPID, SEARCH_BY_GROUPNAME):
        groups = ret
    else:
        msgs = ret
    return (msgs, groups)
