#Embedded file name: localizationBSD/exporters\localizationYamlFileExporter.py
import zipfile
import os
import yaml
import localizationExporter
from . import LocalizationExporterError

class LocalizationYamlFileExporter(localizationExporter.LocalizationExporterBase):
    """
    Exporter that creates *.staticdata files (YAML format) for using with the DUST vault.
    """
    EXPORT_DESCRIPTION = 'Exports language data into staticdata files that are used by the DUST vault generation process.'

    @classmethod
    def ExportWithProjectSettingsToZipFileObject(cls, projectID, fileObject, exportFileName, getSubmittedOnly = True, bsdBranchID = None):
        from fsdCommon.fsdYamlExtensions import FsdYamlDumper
        if not exportFileName:
            exportFileName = 'localization-'
        localizationFiles = cls._GetFileContents(projectID, getSubmittedOnly, bsdBranchID)
        exportedFileNames = []
        zipDataFile = zipfile.ZipFile(fileObject, 'w')
        for languageID, messageDict in localizationFiles.iteritems():
            filePath = exportFileName + languageID + '.staticdata'
            zipDataFile.writestr(filePath, yaml.dump(messageDict, allow_unicode=True, Dumper=FsdYamlDumper))
            exportedFileNames.append(filePath)

        zipDataFile.close()
        return (zipDataFile, exportedFileNames)

    @classmethod
    def ExportWithProjectSettings(cls, projectID, exportLocation, exportFileName, getSubmittedOnly = True, **kwargs):
        """
        Execute this export method for specified project, with project settings provided.
        Method queries the DB and writes language data into .staticdata file in the specified folder
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
        from fsdCommon.fsdYamlExtensions import FsdYamlDumper
        if not exportLocation or not exportFileName:
            raise LocalizationExporterError('Filepath strings are incomplete. exportLocation, exportFileName: %s, %s.' % (exportLocation, exportFileName))
        localizationFiles = cls._GetFileContents(projectID, getSubmittedOnly)
        exportedFileNames = []
        for languageID, messageDict in localizationFiles.iteritems():
            fileName = exportFileName + languageID + '.staticdata'
            filePath = os.path.abspath(os.path.join(exportLocation, fileName))
            with file(filePath, 'w') as f:
                f.write(yaml.dump(messageDict, allow_unicode=True, Dumper=FsdYamlDumper))
            exportedFileNames.append(filePath)

        return exportedFileNames

    @classmethod
    def _GetFileContents(cls, projectID, getSubmittedOnly, bsdBranchID = None):
        exportData = cls._GetLocalizationMessageDataForExport(projectID, getSubmittedOnly, bsdBranchID=bsdBranchID)
        messagesDict = exportData[1]
        localizationFiles = {}
        for msgID, msg in messagesDict.iteritems():
            msgTextDict = msg.GetAllTextDict()
            for languageID, msgTextRow in msgTextDict.iteritems():
                if languageID not in localizationFiles:
                    localizationFiles[languageID] = {}
                localizationFiles[languageID][msgID] = msgTextRow.text

        return localizationFiles
