#Embedded file name: localizationBSD/exporters\localizationScaleformFileExporter.py
import localizationExporter
from . import LocalizationExporterError
import log
import zipfile
import os

class LocalizationScaleformFileExporter(localizationExporter.LocalizationExporterBase):
    """
    Exporter that creates *.int resource files with text data from zlocalization tables. The data doesnt include metadata and
    metadata related content.
    """
    EXPORT_DESCRIPTION = '\nExports language data into a single fontconfig.txt file, which is then used by the PS Vita client / Scaleform to load language strings.\nWhere:\nexportLocation    - location of Localization folder under which the subfolders for each language are created\nexportFileName    - name of the language resource file located under a language subfolder.'
    FILE_NEXTLINE = u'\r\n'
    HEADER1 = FILE_NEXTLINE.join(['[FontConfig "%(languageName)s"]',
     'fontlib "fonts_en.swf"',
     'map "$TitleFont" = "Eve Sans Neue" Bold',
     'map "$NormalFont" = "Eve Sans Neue Regular" Normal',
     'map "$DebugFont" = "Consolas" Normal'])
    HEADER2 = FILE_NEXTLINE.join(['[FontConfig "%(languageName)s"]',
     'fontlib "fonts_ja.swf"',
     'map "$TitleFont" = "Arial Unicode MS" Normal',
     'map "$NormalFont" = "Arial Unicode MS" Normal',
     'map "$DebugFont" = "Consolas" Normal '])
    SCALEFORM_LANGUAGE_NAME_MAP = {'en-us': (HEADER1, {'languageName': 'English'}),
     'ru': (HEADER1, {'languageName': 'Russian'}),
     'de': (HEADER1, {'languageName': 'German'}),
     'zh': (HEADER1, {'languageName': 'Chinese'}),
     'es': (HEADER1, {'languageName': 'Spanish'}),
     'fr': (HEADER1, {'languageName': 'French'}),
     'it': (HEADER1, {'languageName': 'Italian'}),
     'ja': (HEADER2, {'languageName': 'Japanese'})}

    @classmethod
    def ExportWithProjectSettingsToZipFileObject(cls, projectID, fileObject, exportFileName, getSubmittedOnly = True, bsdBranchID = None):
        if not exportFileName:
            exportFileName = 'fontConfig.txt'
        fontConfig = cls._GetFileContents(projectID, getSubmittedOnly, bsdBranchID)
        zipDataFile = zipfile.ZipFile(fileObject, 'w')
        zipDataFile.writestr(exportFileName, fontConfig.encode('utf-8'))
        zipDataFile.close()
        return (zipDataFile, exportFileName)

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
        fontConfig = cls._GetFileContents(projectID, getSubmittedOnly)
        filePath = os.path.abspath(os.path.join(exportLocation, exportFileName))
        wFile = open(filePath, 'wb')
        wFile.write(fontConfig.encode('utf-8'))
        wFile.close()
        return [filePath]

    @classmethod
    def _GetFileContents(cls, projectID, getSubmittedOnly, bsdBranchID = None):
        exportData = cls._GetLocalizationMessageDataForExport(projectID, getSubmittedOnly, bsdBranchID=bsdBranchID)
        folderPathToLabelsIndex = exportData[0]
        languageCodesResultSet = exportData[2]
        fontConfig = u''
        for aLanguageRow in languageCodesResultSet:
            languageID = aLanguageRow.languageID
            if languageID not in cls.SCALEFORM_LANGUAGE_NAME_MAP:
                log.LogError('Language', languageID, 'is not valid for Scaleform export. Please add the language to the SCALEFORM_LANGUAGE_NAME_MAP dictionary.')
                continue
            header, headerParams = cls.SCALEFORM_LANGUAGE_NAME_MAP[languageID]
            fontConfig += header % headerParams
            fontConfig += cls.FILE_NEXTLINE
            fontConfig += cls.FILE_NEXTLINE
            for folderPath, messageRows in folderPathToLabelsIndex.iteritems():
                denormalizedFolderName = folderPath.replace('/', '_').strip()
                for aMessage in messageRows:
                    textRow = aMessage.GetTextRow(languageID)
                    if textRow is not None and textRow.text is not None:
                        if denormalizedFolderName:
                            msgID = '_'.join((denormalizedFolderName, aMessage.labelRow.label))
                        else:
                            msgID = aMessage.labelRow.label
                        trText = textRow.text
                        trText = trText.replace('"', "'")
                        fontConfig += u'tr  "%s" = "%s"' % (msgID, trText)
                        fontConfig += cls.FILE_NEXTLINE

        return fontConfig
