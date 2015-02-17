#Embedded file name: localizationBSD/exporters\localizationPickleExporter.py
import localizationExporter
from . import LocalizationExporterError
from ..wrappers.messageGroup import MessageGroup
from .. import const as localizationBSDConst
from localization.parser import _Tokenize
import cPickle as pickle
import os
import zipfile
import sys
from carbon.backend.script.bsdWrappers.bsdUtil import MakeRowDicts

class LocalizationPickleExporter(localizationExporter.LocalizationExporterBase):
    """
    Exporter that creates *.pickle resource files with dictionaries containing text data and metadata info from zlocalization tables.
    """
    EXPORT_DESCRIPTION = 'Exports language data into .pickle files, that are then used by Localization object to load language data client or server side.\n    Where:\n    exportLocation    - folder path to where the file(s) need to be created. This can include system paths\n    exportFileName    - first characters of every filename generated'
    PICKLE_PROTOCOL = 2
    PICKLE_MAIN = 'main'
    PICKLE_EXT = '.pickle'
    FIELD_LABELS = 'labels'
    FIELD_LANGUAGES = 'languages'
    FIELD_IMPORTANT = 'important'
    FIELD_MAPPING = 'mapping'
    FIELD_REGISTRATION = 'registration'
    FIELD_TYPES = 'types'
    FIELD_MAX_REVISION = 'maxRevision'

    @classmethod
    def ExportWithProjectSettings(cls, projectID, exportLocation, exportFileName, getSubmittedOnly = True, bsdBranchID = None, **kwargs):
        """
        Execute this export method for specified project, with project settings provided.
        Method queries the DB and writes language data into pickle files in the specified folder
        NOTE: inherited from LocalizationExporterBase
        parameters:
            projectID         - ID of specific project to select data for. This identifies what content will be exported.
            exportLocation    - folder path to where the file(s) need to be created. This can include system paths
                                  exp: "root:/common/res/localization/"
            exportFileName    - first characters of every filename generated
            getSubmittedOnly  - flag to indicate if need to write submitted only BSD entries.
                                If True is passed, only submitted BSD entries are written into
                                pickles. Otherwise, latest submitted and unsubmitted BSD 
                                entries are written into pickles.
            bsdBranchID       - Specify from which BSD branch you want to export. Defaults to None.
                                Uses whatever is the branch set for the database you are exporting from if set to None.
        returns:
            list of new pickle files
        """
        if not exportLocation or not exportFileName:
            raise LocalizationExporterError('Filepath strings are incomplete. exportLocation, exportFileName: %s, %s.' % (exportLocation, exportFileName))
        exportedFilenames = []
        pickleDataDict = cls._WriteLocalizationDataToDicts(getSubmittedOnly, projectID, bsdBranchID)
        for fileCode, dataToPickle in pickleDataDict.iteritems():
            filename = os.path.abspath(os.path.join(exportLocation, exportFileName + fileCode + cls.PICKLE_EXT))
            with open(filename, 'wb') as pickleFile:
                pickle.dump(dataToPickle, pickleFile, cls.PICKLE_PROTOCOL)
            pickleFile = None
            exportedFilenames.append(filename)

        return exportedFilenames

    @classmethod
    def ExportWithProjectSettingsToZipFileObject(cls, projectID, fileObject, exportFileName, getSubmittedOnly = True, bsdBranchID = None):
        """
        Generate pickle files and put them into file object / stream passed as parameter, while returning zip file object.
        parameters:
            projectID         - ID of specific project to select data for. This identifies what content will be exported.
            fileObject        - file-like object that zipfile will use to write data to
            exportFileName    - first characters of every filename generated
            getSubmittedOnly  - flag to indicate if need to write submitted only BSD entries.
                                If True is passed, only submitted BSD entries are written into
                                pickles. Otherwise, latest submitted and unsubmitted BSD 
                                entries are written into pickles.
            bsdBranchID       - Specify from which BSD branch you want to export. Defaults to None.
                                Uses whatever is the branch set for the database you are exporting from if set to None.
        returns:
            zip file object, list of new pickle files
        """
        exportedFilenames = []
        zipDataFile = zipfile.ZipFile(fileObject, 'w')
        pickleDataDict = cls._WriteLocalizationDataToDicts(getSubmittedOnly, projectID, bsdBranchID)
        for fileCode, dataToPickle in pickleDataDict.iteritems():
            fileName = exportFileName + fileCode + cls.PICKLE_EXT
            zipDataFile.writestr(fileName, pickle.dumps(dataToPickle, cls.PICKLE_PROTOCOL))
            exportedFilenames.append(fileName)

        zipDataFile.close()
        return (zipDataFile, exportedFilenames)

    @classmethod
    def GetResourceNamesWithProjectSettings(cls, projectID, exportLocation, exportFileName, getSubmittedOnly = True, bsdBranchID = None, **kwargs):
        """
        Queries DB for enabled languages and returns list of files that ExportWithProjectSettings
        is expected to generate.
        NOTE: inherited from LocalizationExporterBase
        parameters:
            projectID         - ID of specific project to select data for. This identifies what content will be exported.
            exportLocation    - folder path to where the file(s) need to be created. This can include system paths
                                  exp: "root:/common/res/localization/"
            exportFileName    - first characters of every filename generated
            getSubmittedOnly  - flag to indicate if need to write submitted only BSD entries.
                                If True is passed, only submitted BSD entries are written into
                                pickles. Otherwise, latest submitted and unsubmitted BSD 
                                entries are written into pickles.
        returns:
            list of new pickle files
        """
        filenameList = []
        fileName = exportFileName + cls.PICKLE_MAIN + cls.PICKLE_EXT
        mainPicklePath = os.path.abspath(os.path.join(exportLocation, fileName)) if exportLocation is not None else fileName
        filenameList.append(mainPicklePath)
        dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
        for row in dbzlocalization.Languages_SelectByProject(1 if getSubmittedOnly else 0, projectID, bsdBranchID):
            fileName = exportFileName + row.languageID + cls.PICKLE_EXT
            languagePicklePath = os.path.abspath(os.path.join(exportLocation, fileName)) if exportLocation is not None else fileName
            filenameList.append(languagePicklePath)

        return filenameList

    @classmethod
    def _WriteLocalizationDataToDicts(cls, getSubmittedOnly, projectID, bsdBranchID = None):
        pickleDataDict = {}
        dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
        languageIDToCode = {}
        messagePerLanguage = {}
        metaDataPerLanguage = {}
        tokensPerLanguage = {}
        tableDataResultSet = dbzlocalization.GetTableDataForPickling(1 if getSubmittedOnly else 0, projectID, bsdBranchID)
        messageResultSet = tableDataResultSet[0]
        wordMetaResultSet = tableDataResultSet[1]
        registrationResultSet = tableDataResultSet[2]
        mappingResultSet = tableDataResultSet[3]
        labelsResultSet = tableDataResultSet[4]
        typesWithPropertiesSet = tableDataResultSet[5]
        languageCodesResultSet = tableDataResultSet[6]
        projectResultSet = tableDataResultSet[7]
        maxDataID = tableDataResultSet[8][0].maxDataID if len(tableDataResultSet[8]) == 1 else None
        importanceResultSet = tableDataResultSet[9]
        labelsDict = MakeRowDicts(rowList=labelsResultSet, columnNames=[localizationBSDConst.COLUMN_MESSAGEID, localizationBSDConst.COLUMN_FULLPATH, localizationBSDConst.COLUMN_LABEL], tableUniqueKey=localizationBSDConst.COLUMN_MESSAGEID)
        languageCodesDict = MakeRowDicts(languageCodesResultSet, columnNames=languageCodesResultSet.columns, tableUniqueKey=localizationBSDConst.COLUMN_LANGUAGE_ID)
        workingDirectory = None
        if projectResultSet and len(projectResultSet):
            workingDirectory = projectResultSet[0].workingDirectory
        for languageCodeRow in languageCodesResultSet:
            languageCodeString = getattr(languageCodeRow, localizationBSDConst.COLUMN_LANGUAGE_ID)
            languagePrimaryKey = getattr(languageCodeRow, localizationBSDConst.COLUMN_LANGUAGE_KEY)
            languageIDToCode[languagePrimaryKey] = languageCodeString
            messagePerLanguage[languageCodeString] = {}
            metaDataPerLanguage[languageCodeString] = {}
            tokensPerLanguage[languageCodeString] = {}

        resultTuple = cls._PrepareDictionariesForWrite(registrationResultSet, mappingResultSet, typesWithPropertiesSet)
        registrationData, mappingData, typesWithPropertiesData, propertiesData = resultTuple
        for aRow, rowValue in labelsDict.iteritems():
            labelPath = rowValue[localizationBSDConst.COLUMN_FULLPATH]
            rowValue[localizationBSDConst.COLUMN_FULLPATH] = MessageGroup.TurnIntoRelativePath(labelPath, workingDirectory)

        importanceDict = {}
        for row in importanceResultSet:
            importanceDict[row['messageID']] = row['important']

        dataToPickle = {}
        dataToPickle[cls.FIELD_LABELS] = labelsDict
        dataToPickle[cls.FIELD_LANGUAGES] = languageCodesDict
        dataToPickle[cls.FIELD_IMPORTANT] = importanceDict
        dataToPickle[cls.FIELD_REGISTRATION] = registrationData
        dataToPickle[cls.FIELD_MAPPING] = mappingData
        dataToPickle[cls.FIELD_TYPES] = typesWithPropertiesData
        dataToPickle[cls.FIELD_MAX_REVISION] = maxDataID
        pickleDataDict[cls.PICKLE_MAIN] = dataToPickle
        for textEntry in messageResultSet:
            languagePrimaryKey = textEntry.numericLanguageID
            aMessageID = textEntry.messageID
            aLanguageCode = languageIDToCode[languagePrimaryKey]
            messagePerLanguage[aLanguageCode][aMessageID] = unicode(textEntry.text)
            if textEntry.text is not None:
                try:
                    tokens = _Tokenize(unicode(textEntry.text))
                except:
                    tokens = None
                    sys.exc_clear()

                if tokens is not None and len(tokens) > 0:
                    tokensPerLanguage[aLanguageCode][aMessageID] = tokens

        for metaEntry in wordMetaResultSet:
            wordPropertyID = metaEntry.wordPropertyID
            languageCodeString = propertiesData[wordPropertyID][localizationBSDConst.COLUMN_LANGUAGE_ID]
            aPropertyName = propertiesData[wordPropertyID][localizationBSDConst.COLUMN_PROPERTY_NAME]
            languageMetaEntry = metaDataPerLanguage[languageCodeString]
            aMessageID = metaEntry.messageID
            if aMessageID not in languageMetaEntry or languageMetaEntry[aMessageID] is None:
                languageMetaEntry[aMessageID] = {}
            languageMetaEntry[aMessageID][aPropertyName] = metaEntry.metaDataValue

        for aLanguageCode in messagePerLanguage:
            bakedData = {}
            for messageID in messagePerLanguage[aLanguageCode]:
                text = meta = tokens = None
                text = messagePerLanguage[aLanguageCode][messageID]
                if messageID in metaDataPerLanguage[aLanguageCode]:
                    meta = metaDataPerLanguage[aLanguageCode][messageID]
                if messageID in tokensPerLanguage[aLanguageCode]:
                    tokens = tokensPerLanguage[aLanguageCode][messageID]
                bakedData[messageID] = (text, meta, tokens)

            dataToPickle = (aLanguageCode, bakedData)
            pickleDataDict[aLanguageCode] = dataToPickle

        return pickleDataDict

    @classmethod
    def _PrepareDictionariesForWrite(cls, registrationResultSet, mappingResultSet, typesWithPropertiesSet):
        """
        helper to prepare registration, mapping, type-properties data
        """
        registrationData = {}
        for aRow in registrationResultSet:
            registrationData[getattr(aRow, localizationBSDConst.COLUMN_SCHEMA_REG_NAME) + '.' + getattr(aRow, localizationBSDConst.COLUMN_TABLE_REG_NAME) + '.' + getattr(aRow, localizationBSDConst.COLUMN_COLUMN_REG_NAME)] = getattr(aRow, localizationBSDConst.COLUMN_TABLE_REG_ID)

        mappingData = {}
        for aRow in mappingResultSet:
            mappingData[getattr(aRow, localizationBSDConst.COLUMN_TABLE_REG_ID), getattr(aRow, localizationBSDConst.COLUMN_KEY_ID)] = getattr(aRow, localizationBSDConst.COLUMN_MESSAGEID)

        typesWithPropertiesData = {}
        for aRow in typesWithPropertiesSet:
            languageToProperties = typesWithPropertiesData.get(getattr(aRow, localizationBSDConst.COLUMN_TYPE_NAME), None)
            if languageToProperties is None:
                languageToProperties = {}
                typesWithPropertiesData[getattr(aRow, localizationBSDConst.COLUMN_TYPE_NAME)] = languageToProperties
            propertyList = languageToProperties.get(getattr(aRow, localizationBSDConst.COLUMN_LANGUAGE_ID), None)
            if propertyList is None and getattr(aRow, localizationBSDConst.COLUMN_PROPERTY_NAME) is not None:
                propertyList = []
                languageToProperties[getattr(aRow, localizationBSDConst.COLUMN_LANGUAGE_ID)] = propertyList
            if propertyList is not None:
                propertyList.append(getattr(aRow, localizationBSDConst.COLUMN_PROPERTY_NAME))

        propertiesData = {}
        for aRow in typesWithPropertiesSet:
            propertyName = getattr(aRow, localizationBSDConst.COLUMN_PROPERTY_NAME)
            if propertyName is not None:
                propertyID = getattr(aRow, localizationBSDConst.COLUMN_PROPERTY_ID)
                languageCodeString = getattr(aRow, localizationBSDConst.COLUMN_LANGUAGE_ID)
                propertiesData[propertyID] = {localizationBSDConst.COLUMN_PROPERTY_NAME: propertyName,
                 localizationBSDConst.COLUMN_LANGUAGE_ID: languageCodeString}

        return (registrationData,
         mappingData,
         typesWithPropertiesData,
         propertiesData)

    @classmethod
    def ExportRowsSubsetForUpdatingPickleCache(cls, projectID, loadFromRevisionList):
        """
        Query the DB and return set of labels and text that corresponds to the revision IDs passed.
        This is here to provide LIVE update functionality.
        parameters:
            projectID            - ID of specific project to select data for. This identifies what content will be exported.
            loadFromRevisionList - list of revisions to load data for
        returns three dictionaries:
            messagePerLanguage, metaDataPerLanguage, languageLabels
        """
        dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
        if loadFromRevisionList is None or len(loadFromRevisionList) == 0:
            raise LocalizationExporterError("loadFromRevisionList parameter is required and can not be 'None' or empty list")
        loadFromRevisionListString = ','.join([ str(revisionID) for revisionID in loadFromRevisionList ])
        resultSet = dbzlocalization.GetTableDataSubsetOfPickleCache(projectID, loadFromRevisionListString)
        return cls._ExportRowsForUpdate(resultSet)

    @classmethod
    def _ExportRowsForUpdate(cls, listOfDBRows):
        """
        Convert the DB rows passed into dictionaries, similarly to what _Write does before the data is pickled.
        This worker method is expecting a specific set of rows.
        """
        projectRow = listOfDBRows[0][0] if len(listOfDBRows[0]) == 1 else None
        labelsResultSet = listOfDBRows[1]
        textsResultSet = listOfDBRows[2]
        metaDataResultSet = listOfDBRows[3]
        messagePerLanguage = {}
        metaDataPerLanguage = {}
        languageLabels = {}
        for textEntry in textsResultSet:
            if textEntry.languageID not in messagePerLanguage:
                messagePerLanguage[textEntry.languageID] = {}
            messagePerLanguage[textEntry.languageID][textEntry.messageID] = textEntry.text

        for metaEntry in metaDataResultSet:
            if metaEntry.languageID not in metaDataPerLanguage:
                metaDataPerLanguage[metaEntry.languageID] = {}
            languageMetaEntry = metaDataPerLanguage[metaEntry.languageID]
            if metaEntry.messageID not in languageMetaEntry:
                languageMetaEntry[metaEntry.messageID] = {}
            languageMetaEntry[metaEntry.messageID][metaEntry.propertyName] = metaEntry.metaDataValue

        workingDirectory = projectRow.workingDirectory if projectRow is not None else None
        for labelRow in labelsResultSet:
            labelPath = MessageGroup.TurnIntoRelativePath(labelRow.FullPath, workingDirectory)
            languageLabels[labelPath + '/' + labelRow.label] = labelRow.messageID

        return (messagePerLanguage, metaDataPerLanguage, languageLabels)

    @classmethod
    def ExportRowsForUpdatingPickleCache(cls, projectID, loadFromDataID):
        """
        Get and all (unsubmitted) data that pickle file should be updated with, to provide basic live update functionality.
        parameters:
            projectID          - ID of specific project to select data for. This identifies what content will be exported.
            loadFromDataID     - filtering parameter: oldest dataID of the record to select (not inclusive), when set will grab all submitted and unsubmitted revisions
        returns:
            
        """
        dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
        if loadFromDataID is None:
            raise LocalizationExporterError("loadFromDataID parameter is required and can not be 'None'")
        resultSet = dbzlocalization.GetTableDataForUpdatingPickleCache(projectID, loadFromDataID)
        return cls._ExportRowsForUpdate(resultSet)
