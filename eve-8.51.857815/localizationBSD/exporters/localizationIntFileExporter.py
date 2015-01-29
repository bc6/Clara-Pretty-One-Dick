#Embedded file name: localizationBSD/exporters\localizationIntFileExporter.py
import localizationExporter
from . import LocalizationExporterError
import cStringIO
import zipfile
import codecs
import os
LANGUAGE_MAP_TO_UNREAL_FOLDER = {'en-us': 'INT',
 'de': 'DEU',
 'es': 'ESN',
 'fr': 'FRA',
 'it': 'ITA',
 'ja': 'JPN',
 'ru': 'RUS',
 'zh': 'CHN'}

class LocalizationIntFileExporter(localizationExporter.LocalizationExporterBase):
    """
    Exporter that creates *.int resource files with text data from zlocalization tables. The data doesnt include metadata and
    metadata related content.
    """
    EXPORT_DESCRIPTION = 'Exports language data into .int files, that are then used by Unreal/Dust client to load language strings that are displayed by Unreal code.\nWhere:\nexportLocation    - location of Localization folder under which the subfolders for each language are created\nexportFileName    - name of the language resource file located under a language subfolder.'
    FOLDER_SEPARATOR = '/'
    GROUP_SEPARATOR = '_'
    FILE_ENCODING = 'utf-16-le'
    FILE_BOM = codecs.BOM_UTF16_LE
    FILE_WRITE_MODE = 'wb'
    FILE_NEXTLINE = '\r\n'
    ENGLISH_FOLDER = 'INT'

    @classmethod
    def ExportWithProjectSettings(cls, projectID, exportLocation, exportFileName, getSubmittedOnly = True, **kwargs):
        """
        Execute this export method for specified project, with project settings provided.
        Method queries the DB and writes language data into .int file in the specified folder
        NOTE: inherited from LocalizationExporterBase
        parameters:
            projectID         - ID of specific project to select data for. This identifies what content will be exported.
            exportLocation    - location of 'Localization' folder under which the subfolders for each language are created, 
                                containing *.int resource file(s)
                                  exp: "root:/dust/ue3/DustGame/Localization/"
            exportFileName    - name of the language resource file located under a language subfolder.
                                  exp: "DustGame"
            getSubmittedOnly  - flag to indicate if need to write submitted only BSD entries.
                                If True is passed, only submitted BSD entries are written into
                                pickles. Otherwise, latest submitted and unsubmitted BSD 
                                entries are written into pickles.
        returns:
            list of new file paths
        """
        if not exportLocation or not exportFileName:
            raise LocalizationExporterError('Filepath strings are incomplete. exportLocation, exportFileName: %s, %s.' % (exportLocation, exportFileName))
        exportedFilenames = []
        exportData = cls._GetLocalizationMessageDataForExport(projectID, getSubmittedOnly)
        folderPathToLabelsIndex = exportData[0]
        languageCodesResultSet = exportData[2]
        openFiles = {}
        try:
            indexToFilePaths = cls._GetResourceNamesWithProjectSettings(languageCodesResultSet, exportLocation, exportFileName)
            for aLanguageRow in languageCodesResultSet:
                filePath = indexToFilePaths[aLanguageRow.languageID]
                if not os.path.exists(os.path.dirname(filePath)):
                    os.makedirs(os.path.dirname(filePath))
                file = open(filePath, cls.FILE_WRITE_MODE)
                file.write(cls.FILE_BOM)
                openFiles[aLanguageRow.languageID] = file
                exportedFilenames.append(filePath)

            for folderPath, messageRows in folderPathToLabelsIndex.iteritems():
                groupString = cls._PrepareGroupName(folderPath)
                for languageString, file in openFiles.iteritems():
                    groupIsWritten = False
                    for aMessage in messageRows:
                        textRow = aMessage.GetTextRow(languageString)
                        if textRow is not None and textRow.text is not None:
                            if not groupIsWritten:
                                cls._WriteGroupString(file, groupString)
                                groupIsWritten = True
                            cls._WriteLabelString(file, aMessage.labelRow.label, textRow.text)

        finally:
            for languageString, file in openFiles.iteritems():
                file.close()

        return exportedFilenames

    @classmethod
    def ExportWithProjectSettingsToZipFileObject(cls, projectID, fileObject, exportFileName, getSubmittedOnly = True, bsdBranchID = None):
        exportData = cls._GetLocalizationMessageDataForExport(projectID, getSubmittedOnly, bsdBranchID=bsdBranchID)
        folderPathToLabelsIndex = exportData[0]
        languageCodesResultSet = exportData[2]
        openFiles = {}
        exportedFilenames = []
        indexToFilePaths = cls._GetResourceNamesWithProjectSettings(languageCodesResultSet, None, exportFileName)
        for aLanguageRow in languageCodesResultSet:
            filePath = indexToFilePaths[aLanguageRow.languageID]
            file = cStringIO.StringIO()
            file.write(cls.FILE_BOM)
            openFiles[aLanguageRow.languageID] = (filePath, file)
            exportedFilenames.append(filePath)

        for folderPath, messageRows in folderPathToLabelsIndex.iteritems():
            groupString = cls._PrepareGroupName(folderPath)
            for languageString, fileInfo in openFiles.iteritems():
                path, file = fileInfo
                groupIsWritten = False
                for aMessage in messageRows:
                    textRow = aMessage.GetTextRow(languageString)
                    if textRow is not None and textRow.text is not None:
                        if not groupIsWritten:
                            cls._WriteGroupString(file, groupString)
                            groupIsWritten = True
                        cls._WriteLabelString(file, aMessage.labelRow.label, textRow.text)

        zipDataFile = zipfile.ZipFile(fileObject, 'w')
        for languageString, fileInfo in openFiles.iteritems():
            path, file = fileInfo
            zipDataFile.writestr(path, file.getvalue())
            file.close()

        zipDataFile.close()
        return (zipDataFile, exportedFilenames)

    @classmethod
    def _PrepareGroupName(cls, groupString):
        return groupString.replace('/', cls.GROUP_SEPARATOR)

    @classmethod
    def _WriteGroupString(cls, file, groupName):
        cls._WriteEncoded(file, u''.join((cls.FILE_NEXTLINE,
         u'[',
         groupName,
         ']',
         cls.FILE_NEXTLINE)))

    @classmethod
    def _WriteLabelString(cls, file, label, textString):
        textString = textString.replace('"', '\\"')
        cls._WriteEncoded(file, u''.join((label,
         '="',
         textString,
         '"',
         cls.FILE_NEXTLINE)))

    @classmethod
    def _WriteEncoded(cls, file, textString):
        file.write(textString.encode(cls.FILE_ENCODING))

    @classmethod
    def GetResourceNamesWithProjectSettings(cls, projectID, exportLocation, exportFileName, getSubmittedOnly = True, **kwargs):
        """
        Queries DB for enabled languages and returns list of files that ExportWithProjectSettings
        is expected to generate.
        NOTE: inherited from LocalizationExporterBase
        parameters:
            projectID         - ID of specific project to select data for. This identifies what content will be exported.
            exportLocation    - location of 'Localization' folder under which the subfolders for each language are created, 
                                containing *.int resource file(s)
                                  exp: "root:/dust/ue3/DustGame/Localization/"
            exportFileName    - name of the *.int file located under a language subfolder.
                                  exp: "DustGame"
            getSubmittedOnly  - flag to indicate if need to write submitted only BSD entries.
                                If True is passed, only submitted BSD entries are written into
                                pickles. Otherwise, latest submitted and unsubmitted BSD 
                                entries are written into pickles.
        returns:
            list of new file paths
        """
        listOfFilePaths = []
        dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
        languageCodesResultSet = dbzlocalization.Languages_SelectByProject(1 if getSubmittedOnly else 0, projectID)
        indexToFilePaths = cls._GetResourceNamesWithProjectSettings(languageCodesResultSet, exportLocation, exportFileName)
        for language, paths in indexToFilePaths.iteritems():
            filePath = paths
            listOfFilePaths.append(filePath)

        return listOfFilePaths

    @classmethod
    def _GetResourceNamesWithProjectSettings(cls, languageCodesResultSet, exportLocation, exportFileName):
        """
        Queries DB for enabled languages and returns list of files that ExportWithProjectSettings
        is expected to generate.
        """
        indexOfPaths = {}
        for aLanguageRow in languageCodesResultSet:
            try:
                languageFolderName = LANGUAGE_MAP_TO_UNREAL_FOLDER[aLanguageRow.languageID]
            except KeyError:
                raise LocalizationExporterError('Unknown language code %s for Unreal export. Please update the LANGUAGE_MAP_TO_UNREAL_FOLDER mapping.' % aLanguageRow.languageID)

            if exportLocation is not None:
                folderPath = os.path.join(exportLocation, languageFolderName)
            else:
                folderPath = languageFolderName
            indexOfPaths[aLanguageRow.languageID] = os.path.join(os.path.abspath(folderPath), exportFileName + u'.' + languageFolderName)

        return indexOfPaths
