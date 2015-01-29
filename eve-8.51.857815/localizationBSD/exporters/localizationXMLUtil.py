#Embedded file name: localizationBSD/exporters\localizationXMLUtil.py
"""
I/O functions that provide interface to generate XML file(s) from Localization database 
and import XML files into Localization database 
"""
import xml.etree.ElementTree
import log
import types
from carbon.backend.script.bsdWrappers.bsdUtil import MakeRowDicts
from localization.const import LOCALE_SHORT_ENGLISH
from localization.logger import LogInfo, LogWarn
from .. import const as localizationBSDConst, util
from ..wrappers.messageText import MessageText
from . import LocalizationExporterError
ADDED = 'Added text'
UPDATED = 'Updated text'
UNCHANGED = 'Unchanged text'
SKIPPED = 'Skipped messageID'
NO_DATAID = 'Missing dataID, skipped message (Import via FSD)'
EMPTY_TAG = 'Empty tags'
_MESSAGE_INCLUDED = 1
_MESSAGE_EXCLUDED = 2
_MESSAGE_DO_NOT_TRANSLATE = 3
_STATUS_CALC_TRANSLATE = 'Translate'
_STATUS_CALC_TRANSLATED = 'Translated'
FILTER_EXPORT_ALL = 'All messages'
FILTER_EXPORT_UNTRANSLATED = 'Untranslated messages'
FILTER_EXPORT_DEFECTS = 'Defects'
FILTER_EXPORT_SPECIAL = 'Special project'
TARGET_FIELD_ENGLISH = 1
TARGET_FIELD_TRANSLATION = 2
XML_EXTENSION = '.xml'
EXPORT_XML_TEXT_ROOT = 'CCP_textData'
EXPORT_XML_META_ROOT = 'CCP_metaData'
EXPORT_XML_TRANSLATIONS = 'translations'
EXPORT_XML_METADATA = 'metadata'
EXPORT_XML_MESSAGE = 'message'
EXPORT_XML_DESCRIPTION = 'description'
EXPORT_XML_TEXT = 'text'
EXPORT_XML_MESSAGEID = 'messageID'
EXPORT_XML_DATAID = 'dataID'
EXPORT_XML_SOURCE_DATAID = 'sourceDataID'
EXPORT_XML_PATH = 'path'
EXPORT_XML_STATUS = 'status'
EXPORT_XML_TRANSLATE = 'Translate'
importEnglishText = False
compareTranslationWithEnglish = False

def ExportToXMLFileFromDatabase(fileNamePattern, projectID, exportFilterSetting = FILTER_EXPORT_UNTRANSLATED, exportTargetField = TARGET_FIELD_ENGLISH, exportByReleaseID = None, changelistList = None):
    """
    The method queries the DB for the data and creates XML files for exporting text data and meta data to translation houses.
    The files are "bilingual" and contain one target language per file. 
    parameters:
        fileNamePattern           - disk path including file name. But doesnt include extension. The default extension is ".xml"
        projectID                 - id of the project to export
        exportFilterSetting       - parameter to filter the content from DB before writing it to the export file
                                    The parameter accepts FILTER_EXPORT_* consts.
                              
                                    for example:
                              
                                    filter that specifies that all translation records must be exported
                                    exportFilterSetting=FILTER_EXPORT_ALL            
                              
                                    filter that specifies that only records that need to be translated/retranslated must be exported
                                    exportFilterSetting=FILTER_EXPORT_UNTRANSLATED
        exportTargetField         - parameter to not include translations in the xml file, instead English(primary language) is placed in every text field
        exportByReleaseID         - release ID of the text rows to select. Note: only selecting the text rows for specified releaseID (only).
        changelistList            - A list of BSD changelists to filter by.
        changed                   - filter for messages only containing changed flag
        
    returns:
        List of files generated
        
    sample of the output file
        <CCP_textData>
            <message messageID='13' dataID='1001' path='UI/Profile/Message'>
                <en-us>            
                    <text>Test item</text>
                    <metadata>
                        <article>a</article>
                        <plural>Test items</plural>                                         
                    </metadata>
                </en-us>
                <description>This is just a sample message on a Profile page</description>
                
                <translations>
                    <ru>
                        <text status='Translate'>Test item</text>
                        <metadata>
                           <gender status='Translate'></gender>
                           <genitivePlural status='Translate'></genitivePlural>
                           <genitiveSingular status='Translate'></genitiveSingular>
                        </metadata>
                    </ru>
                    <ja>
                        <text status='Translate'>Test item</text>
                        <metadata>
                           <counter status='Translated'></counter>
                        </metadata>
                    </ja>
                </translations>
            </message>
        </CCP_textData>
    """
    if not fileNamePattern:
        return
    exportFilterDictionary = {'exportFilterSetting': exportFilterSetting,
     'exportTargetField': exportTargetField}
    dbData = _GetExportDataFromDatabase(projectID, exportByReleaseID, changelistList)
    textsElements = _ExportXMLElementsFromDataRows(dbData, exportFilterDictionary)
    generatedFileNames = []
    for textsElement in textsElements:
        languageID = textsElement.get('exportedLanguage')
        fileName = fileNamePattern + '_' + languageID + XML_EXTENSION
        textsElementTree = xml.etree.ElementTree.ElementTree(textsElement)
        try:
            textsElementTree.write(fileName, encoding='utf-8', xml_declaration=True)
            generatedFileNames.append(fileName)
        except TypeError as anError:
            newMessage = "Is there perhaps an attribute on XML Element with None value? ElementTree doesn't like that."
            raise TypeError(anError.args, newMessage)

    return generatedFileNames


def ExportXMLFromDatabase(projectID, exportFilterSetting = FILTER_EXPORT_UNTRANSLATED, exportTargetField = TARGET_FIELD_ENGLISH, exportByReleaseID = None):
    """
    The method queries the DB for the data and creates list of XML trees containing XML data for exporting to translation houses.
    The strings contain "bilingual" XMLs - one target language per XML tree.
    parameters:
        projectID                 - id of the project to export
        exportFilterSetting       - parameter to filter the content from DB before writing it to the export file
                                    The parameter accepts FILTER_EXPORT_* consts.
                              
                                    for example:
                              
                                    filter that specifies that all translation records must be exported
                                    exportFilterSetting=FILTER_EXPORT_ALL            
                              
                                    filter that specifies that only records that need to be translated/retranslated must be exported
                                    exportFilterSetting=FILTER_EXPORT_UNTRANSLATED
        exportTargetField         - parameter to not include translations in the xml file, instead English(primary language) is placed in every text field
        exportByReleaseID         - release ID of the text rows to select. Note: only selecting the text rows for specified releaseID (only).
        
    returns:
        list of large XML strings of the format defined in ExportXMLFileFromDatabase.
    """
    exportFilterDictionary = {'exportFilterSetting': exportFilterSetting,
     'exportTargetField': exportTargetField}
    return _ExportXMLFromDataRows(_GetExportDataFromDatabase(projectID, exportByReleaseID), exportFilterDictionary)


def ImportFromXMLFileIntoDatabase(fileName, importBatchSize = 1000):
    """
    Imports translated text data and metadata from the XML string and updates the Database.
    parameters:
       fileName        - name of the XML file formatted as defined in ExportToXMLFileFromDatabase
                         method
       importBatchSize - number of items/messages per update when performing writes/updates on DB
                         must be low enough not to blow up string object, currently used by Transactions
                         NOTE/TODO: this is not really ideal, but to be able to do batch updates requires a bit of
                         investigation into bsd procs and quite possibly the addition of procs/functions
                         that would take objects containing updates and perform those updates in a single
                         procedure on DB.
    returns:
        tuple of dictionaries specifying how many records were updated/added/unchanged or
        skipped, in an error case. First dictionary lists updates to text entries; second -
        to meta data entries. Third and forth contain (selected) details.
    exceptions:
        will throw various exceptions if XML is not correctly formatted
    prereq:
        Import must not run within a bsd Transaction.
    """
    if not fileName:
        return
    textDataTree = xml.etree.ElementTree.ElementTree()
    textDataTree.parse(fileName)
    return _ImportXMLIntoDatabase(textRootElement=textDataTree, importBatchSize=importBatchSize)


def ValidateXMLFile(fileName):
    """
    Validates text content of an XML file and makes sure syntax is correct. For use by outsourcers when they do
    not have the ability to actually import into BSD.
    parameters:
       fileName        - name of the XML file formatted as defined in ExportToXMLFileFromDatabase
                         method
    returns:
        A dictionary which contains an entry of {msgID: errorList} for each message that has an error.
    exceptions:
        will throw various exceptions if XML is not correctly formatted
    """
    if not fileName:
        return
    textDataTree = xml.etree.ElementTree.ElementTree()
    textDataTree.parse(fileName)
    return _ValidateXMLInput(textRootElement=textDataTree)


def ImportXMLIntoDatabase(translatedTextXML, importBatchSize = 1000):
    """
    Imports translated text data and metadata from the XML string and updates the Database.
    parameters:
       translatedTextXML  - XML strings. Must be of the format defined
                            in ExportToXMLFileFromDatabase
       importBatchSize    - number of items/messages per update when performing writes/updates on DB
                            must be low enough not to blow up string object, currently used by Transactions
                            NOTE/TODO: this is not really ideal, but to be able to do batch updates requires a bit of
                            investigation into bsd procs and quite possibly the addition of procs/functions
                            that would take objects containing updates and perform those updates in a single
                            procedure on DB.
    returns:
        tuple of dictionaries specifying how many records were updated/added/unchanged or
        skipped, in an error case. First dictionary lists updates to text entries; second -
        to meta data entries. Third and forth contain (selected) details.
    exceptions:
        will throw various exceptions if XML is not correctly formatted
    prereq:
        Import must not run within a bsd Transaction.
    """
    if not translatedTextXML:
        log.LogError('Import function received an empty xml string. Cannot do anything with it.')
        return None
    textRootElement = xml.etree.ElementTree.fromstringlist(translatedTextXML.encode('utf-8'))
    return _ImportXMLIntoDatabase(textRootElement=textRootElement, importBatchSize=importBatchSize)


def _GetExportDataFromDatabase(projectID, exportByReleaseID = None, changelistList = None):
    """
    Worker method to retrieve data to be exported.
    returns:
        tuple/list of row sets containing all the info needed for the export
        currently, the list is the return of stored procedure
    """
    dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
    return dbzlocalization.GetXMLExportData(projectID, exportByReleaseID, changelistList)


def _ExportXMLFromDataRows(dataRows, exportFilterDictionary):
    """
    Worker method that accepts the DB data in params and creates two xml strings containing 
    XML data for exporting to translation houses.
    parameters:
        dataRows    - tuple/list of row sets containing all the info needed for the export
    returns:
        large XML string of the format defined in ExportXMLFileFromDatabase.
    
    NOTE: this function is being unit tested, so it cant be deleted
    """
    textsElements = _ExportXMLElementsFromDataRows(dataRows, exportFilterDictionary)
    XMLList = []
    for textsElement in textsElements:
        try:
            textsXMLString = xml.etree.ElementTree.tostring(textsElement, encoding='utf-8').decode('utf-8')
            XMLList.append(textsXMLString)
        except TypeError as anError:
            newMessage = "Is there perhaps an attribute on XML Element with None value or non-string type value? ElementTree doesn't like that."
            raise TypeError(anError.args, newMessage)

    return XMLList


def _ExportXMLElementsFromDataRows(dataForXMLResultSet, exportFilterDictionary):
    """
    The method queries the DB for the data and creates xml elements containing XML data 
    for exporting to translation houses.
    parameters:
        dataForXMLResultSet    - tuple/list of row sets containing all the info needed
                                 for the export. Note: can't be None.
        exportFilterDictionary - dictionary with export settings, containing
                                     {"exportFilterSetting": <INT>, "exportTargetField": <INT>}
    returns:
        XML Element
    """
    textDataElements = []
    groupPathsResultSet = dataForXMLResultSet[0]
    messageDataResultSet = dataForXMLResultSet[1]
    allPropertiesResultSet = dataForXMLResultSet[2]
    allMetaDataResultSet = dataForXMLResultSet[3]
    requestedLanguagesResultSet = dataForXMLResultSet[4]
    textsResultSet = dataForXMLResultSet[5]
    languageCodesDict = MakeRowDicts(requestedLanguagesResultSet, requestedLanguagesResultSet.columns, localizationBSDConst.COLUMN_LANGUAGE_KEY)
    groupIdToPath = {}
    messageAndPropertyToMetaDataIndex = {}
    messageToTextIndex = {}
    typeAndLanguageToPropertiesIndex = {}
    wordPropertyIDToPropertyName = {}
    for aGroupEntry in groupPathsResultSet:
        groupIdToPath[aGroupEntry.groupID] = aGroupEntry.FullPath

    for aTextEntry in textsResultSet:
        msgID = aTextEntry.messageID
        langID = languageCodesDict[aTextEntry.numericLanguageID][localizationBSDConst.COLUMN_LANGUAGE_ID]
        messageToTextIndex[msgID, langID] = aTextEntry

    for aProperty in allPropertiesResultSet:
        wordPropertyIDToPropertyName[aProperty.wordPropertyID] = aProperty.propertyName
        aPropertyList = typeAndLanguageToPropertiesIndex.get((aProperty.wordTypeID, aProperty.languageID), None)
        if aPropertyList is None:
            aPropertyList = typeAndLanguageToPropertiesIndex[aProperty.wordTypeID, aProperty.languageID] = []
        aPropertyList.append(aProperty)

    for allMetaData in allMetaDataResultSet:
        languageCodeString = languageCodesDict[allMetaData.numericLanguageID][localizationBSDConst.COLUMN_LANGUAGE_ID]
        propertyName = wordPropertyIDToPropertyName[allMetaData.wordPropertyID]
        messageAndPropertyToMetaDataIndex[allMetaData.messageID, languageCodeString, propertyName] = allMetaData

    for languageSet in requestedLanguagesResultSet:
        messagesExported = 0
        metaDataExported = 0
        if languageSet.languageID != LOCALE_SHORT_ENGLISH:
            rootAttributes = {'exportType': exportFilterDictionary['exportFilterSetting'],
             'exportedLanguage': languageSet.languageID}
            textDataElement = xml.etree.ElementTree.Element(tag=EXPORT_XML_TEXT_ROOT, attrib=rootAttributes)
            for messageRow in messageDataResultSet:
                englishTextRow = messageToTextIndex.get((messageRow.messageID, LOCALE_SHORT_ENGLISH))
                if not englishTextRow:
                    continue
                textRow = messageToTextIndex.get((messageRow.messageID, languageSet.languageID))
                if not _CheckIfIncludingTextBasedOnStatus(englishTextRow, textRow, exportFilterDictionary):
                    continue
                rowPath = '/'.join([groupIdToPath.get(messageRow.groupID, 'Unknown group %d' % messageRow.groupID), messageRow.label or ''])
                attributes = {EXPORT_XML_MESSAGEID: str(messageRow.messageID),
                 EXPORT_XML_DATAID: str(messageRow.dataID),
                 EXPORT_XML_PATH: rowPath}
                messageElement = xml.etree.ElementTree.Element(EXPORT_XML_MESSAGE, attrib=attributes)
                textDataElement.append(messageElement)
                messagesExported += 1
                englishTextElement = _MakeXMLLanguageTextElements(messageElement, messageRow, LOCALE_SHORT_ENGLISH, messageToTextIndex, exportFilterDictionary)
                descriptionElement = xml.etree.ElementTree.Element(EXPORT_XML_DESCRIPTION)
                descriptionElement.text = messageRow.context
                messageElement.append(descriptionElement)
                englishMetaElement = _MakeXMLLanguageMetaDataElements(englishTextElement, messageRow, LOCALE_SHORT_ENGLISH, typeAndLanguageToPropertiesIndex, messageAndPropertyToMetaDataIndex, exportFilterDictionary)
                if englishMetaElement is not None:
                    metaDataExported += 1
                translationsElement = xml.etree.ElementTree.Element(tag=EXPORT_XML_TRANSLATIONS)
                messageElement.append(translationsElement)
                languageTextElement = _MakeXMLLanguageTextElements(translationsElement, messageRow, languageSet.languageID, messageToTextIndex, exportFilterDictionary)
                if languageTextElement is not None and messageRow.wordTypeID is not None:
                    languageMetaElement = _MakeXMLLanguageMetaDataElements(languageTextElement, messageRow, languageSet.languageID, typeAndLanguageToPropertiesIndex, messageAndPropertyToMetaDataIndex, exportFilterDictionary)
                    if languageMetaElement is not None:
                        metaDataExported += 1

            textDataElement.set('numberOfMessages', str(messagesExported))
            if messagesExported > 0:
                textDataElements.append(textDataElement)
        LogInfo("Export method exported '%i' message(s) and '%i' metaData entries for language '%s' (including english metadata) " % (messagesExported, metaDataExported, languageSet.languageID))

    return textDataElements


def _MakeXMLLanguageTextElements(parentElement, messageRow, languageCodeString, messageToTextIndex, exportFilterDictionary):
    """
    Worker function to make a language tag element and a text tag element
    parameters:
        parentElement                       - parent element to attach to (normally a language tag)
        messageRow                          - result row for this message
        languageCodeString                  - locale code string for this language        
        messageToTextIndex                  - cache for easy look up
    returns:
        language element, or None if it was determined that text entry shouldn't be exported
    """
    englishTextEntry = messageToTextIndex.get((messageRow.messageID, LOCALE_SHORT_ENGLISH), None)
    languageTextEntry = messageToTextIndex.get((messageRow.messageID, languageCodeString), None)
    if englishTextEntry is None:
        errMsg = 'Didnt find the English text row when creating translation text tag, '
        errMsg += "therefore won't be able to properly export this message. messageID (%s)"
        log.LogError(errMsg % englishTextEntry.messageID)
        return
    if languageCodeString == LOCALE_SHORT_ENGLISH:
        textFlags = _PrepareMainFlags(englishTextEntry, messageRow.messageID)
    else:
        textFlags = _PrepareTranslationFlags(englishTextEntry, languageTextEntry, messageRow.messageID, languageCodeString)
    textEntry = None
    if exportFilterDictionary['exportTargetField'] == TARGET_FIELD_ENGLISH:
        textEntry = englishTextEntry
    elif exportFilterDictionary['exportTargetField'] == TARGET_FIELD_TRANSLATION:
        if languageCodeString != LOCALE_SHORT_ENGLISH and languageTextEntry is None:
            textEntry = englishTextEntry
        else:
            textEntry = languageTextEntry
    languageTextElement = xml.etree.ElementTree.Element(languageCodeString)
    parentElement.append(languageTextElement)
    languageTextEntryElement = xml.etree.ElementTree.Element(EXPORT_XML_TEXT)
    languageTextElement.append(languageTextEntryElement)
    if textEntry is not None:
        languageTextEntryElement.text = textEntry.text
        if len(textFlags):
            for attrKey, attrVal in textFlags.iteritems():
                languageTextEntryElement.set(attrKey, attrVal)

    return languageTextElement


def _CheckIfIncludingTextBasedOnStatus(englishTextRow, languageTextRow, exportFilterDictionary):
    """
    Method to check if message text entry, given its status and export settings should be included in the xml export.
    """
    englishStatus = englishTextRow.statusID
    textStatus = languageTextRow.statusID if languageTextRow else None
    if localizationBSDConst.TEXT_STATUS_DO_NOT_TRANSLATE in (englishStatus, textStatus):
        return False
    elif exportFilterDictionary['exportFilterSetting'] == FILTER_EXPORT_ALL:
        return True
    elif exportFilterDictionary['exportFilterSetting'] == FILTER_EXPORT_DEFECTS:
        if textStatus == localizationBSDConst.TEXT_STATUS_DEFECT:
            return True
        return False
    elif exportFilterDictionary['exportFilterSetting'] == FILTER_EXPORT_SPECIAL:
        if textStatus == localizationBSDConst.TEXT_STATUS_SPECIAL:
            return True
        return False
    elif exportFilterDictionary['exportFilterSetting'] == FILTER_EXPORT_UNTRANSLATED:
        return not _LanguageTextUpToDate(englishTextRow, languageTextRow)
    else:
        return LocalizationExporterError('XML Exporter cant export with the unrecognized filter setting: %s.' % exportFilterDictionary['exportFilterSetting'])


def _LanguageTextUpToDate(englishEntry, languageEntry):
    """
    Returns true if a language text is up to date with its corresponding English entry.
    """
    return languageEntry and languageEntry.sourceDataID == englishEntry.dataID


def _PrepareMainFlags(englishEntry, messageID):
    """
    Function that generates dictionary of flags to be added on the english text attribute
    """
    if englishEntry is None:
        log.LogError('Didnt find the English text row for English tag. messageID (%s)' % messageID)
        return {}
    return {EXPORT_XML_DATAID: str(englishEntry.dataID)}


def _GetMessageTextStatusNameByID(statusID):
    """
    Retrieve status name for text status specified.
    NOTE: this function goes directly to the DB on the first call for the data and will cache the resulting db rows.
    returns:
        status string name if found, None otherwise
    """
    if not getattr(_GetMessageTextStatusNameByID, '_messageTextStatuses', None):
        dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
        resultSet = dbzlocalization.MessageTextStatuses_Select()
        _GetMessageTextStatusNameByID._messageTextStatuses = {r.statusID:r.statusName for r in resultSet}
    if statusID in _GetMessageTextStatusNameByID._messageTextStatuses:
        return _GetMessageTextStatusNameByID._messageTextStatuses[statusID]
    else:
        return 'unknown (%s)' % statusID


def _PrepareTranslationFlags(englishEntry, targetLanguageEntry, messageID, languageCodeString):
    """
    Function to put together appropriate flags/attributes for the text/translation row in the exported XML file.
    """
    textFlags = {}
    if targetLanguageEntry is None:
        textFlags[EXPORT_XML_STATUS] = _STATUS_CALC_TRANSLATE
    else:
        if targetLanguageEntry.statusID is None:
            stat = _STATUS_CALC_TRANSLATED if _LanguageTextUpToDate(englishEntry, targetLanguageEntry) else _STATUS_CALC_TRANSLATE
        else:
            stat = _GetMessageTextStatusNameByID(targetLanguageEntry.statusID)
        textFlags[EXPORT_XML_STATUS] = stat
        textFlags[EXPORT_XML_DATAID] = str(targetLanguageEntry.dataID)
    return textFlags


def _MakeXMLLanguageMetaDataElements(parentElement, messageRow, languageCodeString, typeAndLanguageToPropertiesIndex, messageAndPropertyToMetaDataIndex, exportFilterDictionary):
    """
    Worker function to put together metadata tag, followed by property tags.
    Metadata tag is not added if there are no properties for this language
    parameters:
        parentElement                        - parent element to attach to (normally a language tag)
        messageRow                           - message entry for this message
        languageCodeString                   - locale code string for this language
        typeAndLanguageToPropertiesIndex     - reference to cache containing all properties
        messageAndPropertyToMetaDataIndex    - reference to cache containing property values
    returns:
        metadata element, or None if metadata wasnt created 
    """
    languageMetaElement = None
    properties = typeAndLanguageToPropertiesIndex.get((messageRow.wordTypeID, languageCodeString))
    if properties:
        languageMetaElement = xml.etree.ElementTree.Element(EXPORT_XML_METADATA)
        parentElement.append(languageMetaElement)
        for aProperty in properties:
            languageProperty = xml.etree.ElementTree.Element(aProperty.propertyName)
            languageMetaElement.append(languageProperty)
            if languageCodeString == LOCALE_SHORT_ENGLISH or exportFilterDictionary['exportTargetField'] == TARGET_FIELD_TRANSLATION:
                languageMetaDataRow = messageAndPropertyToMetaDataIndex.get((messageRow.messageID, languageCodeString, aProperty.propertyName), None)
                if languageMetaDataRow is not None:
                    languageProperty.text = languageMetaDataRow.metaDataValue

    return languageMetaElement


def _ValidateXMLInput(textRootElement):
    errors = {}
    dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
    getSubmittedOnly = 1
    allPropertiesResultSet = dbzlocalization.WordTypes_GetAllProperties(getSubmittedOnly, None)
    updatesResults = _GetUpdatesListForImportIntoDatabase(textRootElement, allPropertiesResultSet, sm.GetService('bsdTable').GetTable(localizationBSDConst.MESSAGES_TABLE), importEnglishText)
    listOfTextImports = updatesResults[0]
    vData = util.GetDummyData()
    for anEntry in listOfTextImports:
        messageID, translatedText, languageID, _ = anEntry
        res = util.ValidateString(unicode(translatedText), languageID, dummyData=vData)
        if isinstance(res, types.ListType):
            errors[messageID] = res

    return errors


def _ImportXMLIntoDatabase(textRootElement, importBatchSize):
    """
    Imports translated text data and metadata from the XML string and updates the Database.
    parameters:
        textRootElement     - root element pointing to the XML structure 
    returns:
        tuple of two dictionaries specifying how many records were updated/added/unchanged or
        skipped, in an error case. First dictionary lists updates to text entries; second -
        to meta data entries
    exceptions:
        will throw various exceptions if XML is not correctly formatted
    prereq:
        Import must not run within a bsd Transaction.
    """
    import bsd
    dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
    updatedTextEntries = {ADDED: 0,
     UPDATED: 0,
     UNCHANGED: 0,
     SKIPPED: 0,
     EMPTY_TAG: 0}
    updatedTextEntriesDetail = {UPDATED: [],
     SKIPPED: [],
     EMPTY_TAG: []}
    updatedMetaDataEntries = {ADDED: 0,
     UPDATED: 0,
     UNCHANGED: 0,
     EMPTY_TAG: 0}
    updatedMetaDataEntriesDetail = {UPDATED: [],
     EMPTY_TAG: []}
    bsdTableService = sm.GetService('bsdTable')
    messageTextsTable = bsdTableService.GetTable(localizationBSDConst.MESSAGE_TEXTS_TABLE)
    metaDataTable = bsdTableService.GetTable(localizationBSDConst.WORD_METADATA_TABLE)
    messagesTable = bsdTableService.GetTable(localizationBSDConst.MESSAGES_TABLE)
    getSubmittedOnly = 1
    allPropertiesResultSet = dbzlocalization.WordTypes_GetAllProperties(getSubmittedOnly, None)
    updatesResults = _GetUpdatesListForImportIntoDatabase(textRootElement, allPropertiesResultSet, messagesTable, importEnglishText)
    listOfTextImports, listOfMetaDataImports, textEntriesStats, metaDataEntriesStats, textEntriesDetails, metaDataEntriesDetails = updatesResults
    updatedTextEntries.update(textEntriesStats)
    updatedMetaDataEntries.update(metaDataEntriesStats)
    updatedTextEntriesDetail.update(textEntriesDetails)
    updatedMetaDataEntriesDetail.update(metaDataEntriesDetails)
    batchList = listOfTextImports[0:importBatchSize]
    batchIteration = 0
    while batchList:
        with bsd.BsdTransaction():
            for anEntry in batchList:
                messageID, translatedText, languageID, sourceDataID = anEntry
                updateStatus = _ImportTextEntry(messageID, translatedText, languageID, sourceDataID, messageTextsTable, compareTranslationWithEnglish)
                updatedTextEntries[updateStatus] += 1
                if updateStatus == UPDATED:
                    updatedTextEntriesDetail[updateStatus].append((messageID, languageID))

        batchIteration += 1
        batchList = listOfTextImports[0 + batchIteration * importBatchSize:(1 + batchIteration) * importBatchSize]

    batchList = listOfMetaDataImports[0:importBatchSize]
    batchIteration = 0
    while batchList:
        with bsd.BsdTransaction():
            for anEntry in batchList:
                messageID, wordPropertyID, metaDataText = anEntry
                updateStatus = _ImportMetaDataEntry(messageID, wordPropertyID, metaDataText, metaDataTable)
                updatedMetaDataEntries[updateStatus] += 1
                if updateStatus == UPDATED:
                    updatedMetaDataEntriesDetail[updateStatus].append((messageID, wordPropertyID))

        batchIteration += 1
        batchList = listOfMetaDataImports[0 + batchIteration * importBatchSize:(1 + batchIteration) * importBatchSize]

    return (updatedTextEntries,
     updatedMetaDataEntries,
     updatedTextEntriesDetail,
     updatedMetaDataEntriesDetail)


def _GetUpdatesListForImportIntoDatabase(textRootElement, allPropertiesResultSet, messagesTable, importEnglishText = False):
    """
    Worker function to walk through the element hierarchy and create list of updates
    for text and metadata tables
    parameters:
        textRootElement           - root element pointing to the XML structure
        allPropertiesResultSet    - db rowset containing enabled properties
        messagesTable             - reference to bsdtable for messages
    returns:
        returns lists of data, to be processed by import function(s)
        listOfTextImports         - contains updates for:
                                    (messageID, translatedText, languageID)
        listOfMetaDataImports     - contains updates for:
                                    (messageID, wordPropertyID, metaDataText)
        update counters and update details
    exceptions:
        will throw various exceptions if XML is not correctly formatted
    
    NOTE: this function is being unit tested, so it cant be deleted
    """
    listOfTextImports = []
    listOfMetaDataImports = []
    updatedTextEntries = {SKIPPED: 0,
     EMPTY_TAG: 0,
     NO_DATAID: 0}
    updatedTextEntriesDetail = {SKIPPED: [],
     EMPTY_TAG: [],
     NO_DATAID: []}
    updatedMetaDataEntries = {EMPTY_TAG: 0}
    updatedMetaDataEntriesDetail = {EMPTY_TAG: []}
    propertyAndLanguageToPropertiesIndex = {}
    for aProperty in allPropertiesResultSet:
        propertyAndLanguageToPropertiesIndex[aProperty.propertyName, aProperty.languageID] = aProperty

    if textRootElement is not None:
        allMessageElements = textRootElement.findall(EXPORT_XML_MESSAGE)
        for aMessageElement in allMessageElements:
            messageID = int(aMessageElement.get(EXPORT_XML_MESSAGEID))
            dataID = aMessageElement.get(EXPORT_XML_DATAID)
            if dataID is None:
                LogWarn('No dataID for message %s, skipping this entry' % messageID)
                updatedTextEntries[NO_DATAID] += 1
                updatedTextEntriesDetail[NO_DATAID].append(messageID)
                continue
            dataID = int(dataID)
            messageRows = messagesTable.GetRowByKey(messageID)
            if not messageRows:
                log.LogError("Import didnt find a matching messageID in DB; skipping importing this entry : '%s'" % messageID)
                updatedTextEntries[SKIPPED] += 1
                updatedTextEntriesDetail[SKIPPED].append(messageID)
                continue
            englishElement = aMessageElement.find(LOCALE_SHORT_ENGLISH)
            englishTextElement = englishElement.find(EXPORT_XML_TEXT)
            translationElement = aMessageElement.find(EXPORT_XML_TRANSLATIONS)
            languageElements = list(translationElement)
            if importEnglishText:
                languageElements.append(englishElement)
            for aLanguageElement in languageElements:
                languageTextElement = aLanguageElement.find(EXPORT_XML_TEXT)
                languageID = aLanguageElement.tag
                translatedText = languageTextElement.text
                if translatedText:
                    sourceDataID = int(englishTextElement.get(EXPORT_XML_DATAID))
                    listOfTextImports.append((messageID,
                     translatedText,
                     languageID,
                     sourceDataID))
                else:
                    updatedTextEntries[EMPTY_TAG] += 1
                    updatedTextEntriesDetail[EMPTY_TAG].append((messageID, languageID))
                metaDataElement = aLanguageElement.find(EXPORT_XML_METADATA)
                if metaDataElement is not None:
                    languageMetaDataElements = list(metaDataElement)
                    for aPropertyElement in languageMetaDataElements:
                        propertyName = aPropertyElement.tag
                        metaDataText = aPropertyElement.text
                        if metaDataText:
                            try:
                                aPropertyEntry = propertyAndLanguageToPropertiesIndex[propertyName, languageID]
                                wordPropertyID = aPropertyEntry.wordPropertyID
                                listOfMetaDataImports.append((messageID, wordPropertyID, metaDataText))
                            except IndexError as e:
                                log.LogError("Import didnt find a matching property in DB; skipping importing this property (messageID,property) : '%s,%s'" % (messageID, propertyName))

                        else:
                            updatedMetaDataEntries[EMPTY_TAG] += 1
                            updatedMetaDataEntriesDetail[EMPTY_TAG].append((messageID, languageID))

    return (listOfTextImports,
     listOfMetaDataImports,
     updatedTextEntries,
     updatedMetaDataEntries,
     updatedTextEntriesDetail,
     updatedMetaDataEntriesDetail)


def _ImportMetaDataEntry(messageID, wordPropertyID, metaDataText, metaDataTable):
    """
    Worker function to update a given metadata entry.
    parameters:
        messageID        - id of the main message
        wordPropertyID        - ID of the property
        metaDataText     - text of the property
        metaDataTable         - table reference for DB access
    """
    updateStatus = UNCHANGED
    metaDataEntries = metaDataTable.GetRows(messageID=messageID, wordPropertyID=wordPropertyID)
    if metaDataEntries and len(metaDataEntries):
        if metaDataEntries[0].metaDataValue != metaDataText:
            metaDataEntries[0].metaDataValue = metaDataText
            updateStatus = UPDATED
        else:
            updateStatus = UNCHANGED
    else:
        metaDataTable.AddRow(metaDataValue=metaDataText, messageID=messageID, wordPropertyID=wordPropertyID)
        updateStatus = ADDED
    return updateStatus


def _ImportTextEntry(messageID, translatedText, languageID, sourceDataID, messageTextsTable, compareTranslationWithEnglish = False):
    """
    Worker function to import translated text
    parameters:
        messageID             - id of the main message
        translatedText        - text to import
        languageID            - language string id of the text
        messageTextsTable     - table reference for DB access
    """
    updateStatus = UNCHANGED
    englishText = MessageText.GetMessageTextByMessageID(messageID, LOCALE_SHORT_ENGLISH)
    if englishText is None:
        log.LogError("Import didnt find a matching english text in DB; skipping importing this entry. messageID : '%s'" % messageID)
        return updateStatus
    existingTranslation = MessageText.GetMessageTextByMessageID(messageID, languageID)
    isPassingEnglishTest = True
    if compareTranslationWithEnglish:
        isPassingEnglishTest = englishText.text != translatedText
    if existingTranslation:
        if existingTranslation.text != translatedText and isPassingEnglishTest:
            existingTranslation.SetTextAndSourceDataID(translatedText, sourceDataID)
            updateStatus = UPDATED
        elif existingTranslation.sourceDataID < sourceDataID:
            existingTranslation.sourceDataID = sourceDataID
            updateStatus = UPDATED
        else:
            updateStatus = UNCHANGED
    elif isPassingEnglishTest:
        MessageText.Create(messageID, languageID, text=translatedText, sourceDataID=sourceDataID)
        updateStatus = ADDED
    else:
        updateStatus = EMPTY_TAG
    return updateStatus
