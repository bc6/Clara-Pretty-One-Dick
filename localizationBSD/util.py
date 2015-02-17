#Embedded file name: localizationBSD\util.py
import blue
import types
import eveLocalization
import telemetry
import random
import localization.logger as locLogger
from localization.parser import _Tokenize

def GetDummyData():
    """
        Pulls dummy data for localization either from the database or bulk data
    """
    try:
        db2 = sm.GetService('DB2')
    except:
        db2 = None

    if db2 is None:
        raise RuntimeError("Can't select dummy data for checking localization strings without a database connection!")
    charRows = db2.SQL('SELECT TOP 5 characterID from character.characters ORDER BY NEWID()')
    locRow = db2.SQL('SELECT TOP 1 solarSystemID from map.solarSystemsDx ORDER BY NEWID()')
    typeRow = db2.SQL('SELECT TOP 1 typeID from inventory.types ORDER BY NEWID()')
    msgRow = db2.SQL('SELECT TOP 1 messageID from zlocalization.messages ORDER BY NEWID()')
    return {eveLocalization.VARIABLE_TYPE.CHARACTER: charRows[0].characterID,
     eveLocalization.VARIABLE_TYPE.NPCORGANIZATION: const.factionCaldariState,
     eveLocalization.VARIABLE_TYPE.ITEM: typeRow[0].typeID,
     eveLocalization.VARIABLE_TYPE.LOCATION: locRow[0].solarSystemID,
     eveLocalization.VARIABLE_TYPE.CHARACTERLIST: [ x.characterID for x in charRows ],
     eveLocalization.VARIABLE_TYPE.MESSAGE: msgRow[0].messageID,
     eveLocalization.VARIABLE_TYPE.DATETIME: blue.os.GetWallclockTime(),
     eveLocalization.VARIABLE_TYPE.FORMATTEDTIME: blue.os.GetWallclockTime(),
     eveLocalization.VARIABLE_TYPE.TIMEINTERVAL: long(random.random() * 60) * const.SEC,
     eveLocalization.VARIABLE_TYPE.NUMERIC: 99.9,
     eveLocalization.VARIABLE_TYPE.GENERIC: 'This is a test message.'}


@telemetry.ZONE_FUNCTION
def ValidateString(sourceText, languageID, dummyData = None):
    """
    Validates a string for tokenizer and parser errors.  Returns a list of error messages, if any are found for the given string.
    """
    if dummyData is None:
        dummyData = GetDummyData()
    errors = []
    oldMethod = locLogger.LogError

    def ValidationLogError(*args):
        oldMethod(*args)
        errors.append(args)

    locLogger.LogError = ValidationLogError
    openCount = sourceText.count('{')
    closeCount = sourceText.count('}')
    if openCount != closeCount:
        return ["Mismatching brackets in string '" + unicode(sourceText) + "'"]
    try:
        tags = _Tokenize(sourceText)
    except Exception as e:
        return ["Exception occurred when attempting to tokenize string '" + unicode(sourceText) + "': " + repr(e)]

    kwargs = {}
    for tag in tags.values():
        if tag['variableName'] and tag['variableType'] in dummyData:
            kwargs[tag['variableName']] = dummyData[tag['variableType']]
        if 'linkinfo' in tag['kwargs']:
            kwargs[tag['kwargs']['linkinfo']] = ('showinfo', 1)
        if 'quantity' in tag['kwargs']:
            kwargs[tag['kwargs']['quantity']] = 3

    result = sourceText
    try:
        result = eveLocalization.Parse(sourceText, languageID, tags, **kwargs)
    except Exception as e:
        errors = ["Exception occurred when attempting to validate string '" + unicode(sourceText) + "': " + repr(e) + repr(kwargs)]

    locLogger.LogError = oldMethod
    if errors:
        return errors
    return result


def ValidateAll(languageID, projectID = None):
    """
    Validates all strings in the database for a particular language, and returns a dictionary of {messageID: [list of errors]}.
    """
    db2 = sm.GetService('DB2')
    if projectID is None:
        sql = "\n            SELECT messageID, text\n              FROM zlocalization.messageTexts T\n                INNER JOIN zlocalization.languages L ON L.numericLanguageID = T.numericLanguageID\n             WHERE L.languageID='%s'\n        " % languageID
    else:
        sql = "\n            SELECT T.messageID, T.text\n              FROM zlocalization.messages M\n                INNER JOIN zlocalization.projectsToGroups PG ON M.groupID = PG.groupID\n                INNER JOIN zlocalization.messageTexts T ON M.messageID = T.messageID\n                  INNER JOIN zlocalization.languages L ON L.numericLanguageID = T.numericLanguageID\n             WHERE PG.projectID = %d AND L.languageID='%s'\n        " % (projectID, languageID)
    rs = db2.SQL(sql)
    dummyData = GetDummyData()
    errorDict = {}
    for row in rs:
        blue.pyos.BeNice()
        if row.text:
            errors = ValidateString(row.text, languageID, dummyData)
            if isinstance(errors, types.ListType):
                errorDict[row.messageID] = errors

    return errorDict


def GetNumericLanguageIDFromLanguageID(languageID):
    if not hasattr(GetNumericLanguageIDFromLanguageID, 'langs'):
        GetNumericLanguageIDFromLanguageID.langs = sm.GetService('cache').GetRowset(const.cacheLocalizationLanguages).Index('languageID')
    if languageID in GetNumericLanguageIDFromLanguageID.langs:
        return GetNumericLanguageIDFromLanguageID.langs[languageID].numericLanguageID
    raise ValueError('Unkown languageID %s' % languageID)


def GetGroupLink(groupID, text = None):
    """
        Returns a link to the localization browser for a particular group
    """
    if text is None:
        text = str(groupID)
    return '<a href="/localization/localizationbrowser.py#/f:%d/">%s</a>' % (groupID, text)


def GetMessageLink(messageID, text = None):
    """
        Returns a link to the localization browser for a particular message
    """
    if text is None:
        text = str(messageID)
    return '<a href="/localization/localizationbrowser.py#/m:%d/">%s</a>' % (messageID, text)
