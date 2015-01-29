#Embedded file name: localizationBSD/exporters\localizationExporter.py
from ..wrappers.messageGroup import MessageGroup

class LocalizationMessage:
    """
    Data structure containing text and label data.
    """

    def __init__(self):
        self.labelPath = None
        self.labelRow = None
        self._textRows = {}

    def GetTextRow(self, languageID):
        if languageID in self._textRows:
            return self._textRows[languageID]

    def GetAllTextDict(self):
        """
        return all texts in a dictionary, keyed by languageID
        """
        return self._textRows


class LocalizationExporterBase(object):
    """
    Generic API to export resource files from Projects defined on the content database.
    Exporters used by localizationExportManager must inherit this class.
    """
    EXPORT_DESCRIPTION = 'Undefined'

    @classmethod
    def ExportWithProjectSettings(cls, projectID, **kwargs):
        """
        Execute this export method for specified project, with project settings provided.
        It is up to each exporter to select what data to export, but currently all exporters select submitted only data.
        NOTE: implementations must catch all extra settings with **kwargs
        """
        raise NotImplementedError

    @classmethod
    def GetResourceNamesWithProjectSettings(cls, projectID, **kwargs):
        """
        Method creates and returns list of filenames of resource files that user will need to check out in perforce,
        before calling an Export method
        NOTE: implementations must catch all extra settings with **kwargs
        """
        raise NotImplementedError

    @classmethod
    def _GetLocalizationMessageDataForExport(cls, projectID, getSubmittedOnly, bsdBranchID = None):
        """
        Non public helper method, meant to be used by inherited exporters when needed. The method returns
        Two indexes to DB Row objects that were retrieved with procedure call that retrieves simple exporter data.
        That data contains: texts, labels, languages information and project information. All that's needed for exporter
        that doesnt need to export more complex grammar logic, involving metadata.
        NOTE: protected method
        parameters:
            projectID        - required ID of the specific project to export
            getSubmittedOnly - flag that indicates whether or not to retrieve submitted only bsd data
        returns:
            folderPathToLabelsIndex    - dictionary indexing all labels by their folder path: { FolderPath : [labelDBRow, labelDBRow, ]}
            languageMessageToTextIndex - dictionary indexing all texts by messageID and languageID: { (messageID, languageID): TextRow  }
            languageCodesResultSet     - db rowset with language data
            projectResultSet           - db rowset for the selected project
        """
        dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
        exportResultSet = dbzlocalization.GetTableDataForMessageExport(1 if getSubmittedOnly else 0, projectID, bsdBranchID)
        messageResultSet = exportResultSet[0]
        labelsResultSet = exportResultSet[1]
        languageCodesResultSet = exportResultSet[2]
        projectResultSet = exportResultSet[3]
        maxDataID = exportResultSet[4][0].maxDataID
        workingDirectory = None
        if projectResultSet and len(projectResultSet):
            workingDirectory = projectResultSet[0].workingDirectory
        messagesDict = {}
        for aLabel in labelsResultSet:
            if aLabel.messageID in messagesDict:
                messageObj = messagesDict[aLabel.messageID]
            else:
                messageObj = messagesDict[aLabel.messageID] = LocalizationMessage()
            messageObj.labelRow = aLabel
            messageObj.labelPath = MessageGroup.TurnIntoRelativePath(aLabel.FullPath + '/' + aLabel.label, workingDirectory)

        langsByNumeric = languageCodesResultSet.Index('numericLanguageID')
        for textRow in messageResultSet:
            if textRow.messageID in messagesDict:
                messageObj = messagesDict[textRow.messageID]
            else:
                messageObj = messagesDict[textRow.messageID] = LocalizationMessage()
            languageID = langsByNumeric[textRow.numericLanguageID].languageID
            messageObj._textRows[languageID] = textRow

        folderPathToMessagesIndex = {}
        for aLabelRow in labelsResultSet:
            fullPath = MessageGroup.TurnIntoRelativePath(aLabelRow.FullPath, workingDirectory)
            if fullPath not in folderPathToMessagesIndex:
                folderPathToMessagesIndex[fullPath] = []
            folderPathToMessagesIndex[fullPath].append(messagesDict[aLabelRow.messageID])

        return (folderPathToMessagesIndex,
         messagesDict,
         languageCodesResultSet,
         projectResultSet,
         maxDataID)
