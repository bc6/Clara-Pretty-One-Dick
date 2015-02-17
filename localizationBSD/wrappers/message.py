#Embedded file name: localizationBSD/wrappers\message.py
from . import AuthoringValidationError
from .. import const as localizationBSDConst
from ..util import GetNumericLanguageIDFromLanguageID
import bsdWrappers
import bsd
import dbutil
import re
from localization.const import LOCALE_SHORT_ENGLISH
import utillib as util
import messageText as locMessageText
import wordMetaData as locWordMetaData
import wordType as locWordType

class Message(bsdWrappers.BaseWrapper):
    """
    A wrapper object for messages, where a message is composed of a label identifier, and one or more strings (one string per supported language).
    This class also handles operations on Metadata.  
    """
    __primaryTable__ = bsdWrappers.RegisterTable(localizationBSDConst.MESSAGES_TABLE)
    _messageTextTable = None
    _propertyTable = None
    _bsdSvc = None
    _APPEND_NEW = '(new)'

    def GetLabelPath(self, projectID = None):
        """
        Generate path to this label as it'll appear in export/pickle file(s).
        NOTE: This is primarily used in UI/Content Browser to show the user how the paths would look like.
              This function doesnt actually care whether this message was tagged with the projectID or not.
        parameters:
            projectID - optional parameter. When specified will use Project's working directory when rendering
                        final path string
        returns:
            a path string, of the form: u'/UI/Generic/Buttons/Cancel'
        """
        from messageGroup import MessageGroup
        labelPath = '' if self.label is None else self.label
        if self.groupID is not None:
            folderPath = MessageGroup.Get(self.groupID).GetFolderPath(projectID=projectID)
            if folderPath and labelPath:
                labelPath = '/'.join((folderPath, labelPath))
            elif folderPath:
                labelPath = folderPath
        return labelPath

    def GetOpenedBy(self):
        """
        Aggregates bsd state information across all components of a message (label, texts for each language, and metadata for each language),
        and returns it in human-readable form.
        """
        openedBy = [self._GetOpenedBy(self)]
        for messageText in locMessageText.MessageText.GetWithFilter(messageID=self.messageID):
            openedBy += [self._GetOpenedBy(messageText)]

        for metadata in locWordMetaData.WordMetaData.GetWithFilter(messageID=self.messageID):
            openedBy += [self._GetOpenedBy(metadata)]

        openedBy = '\n'.join([ text for text in openedBy if text ])
        return openedBy

    def _GetOpenedBy(self, bsdWrapper):
        """
        Get a nicely formatted message describing who is editing any rows that make up this wrapper.
        Because a message is composed of multiple wrappers, we create a fancier string including the wrapper name.
        """
        openedBy = ''
        openedByUserIDs = bsdWrapper.GetOpenedByUserIDs()
        bsdState = bsdWrapper.GetState()
        if bsdState & dbutil.BSDSTATE_OPENFORADD != 0:
            openedBy += bsdWrapper.__class__.__name__ + ' added by '
        elif bsdState & dbutil.BSDSTATE_OPENFORDELETE != 0:
            openedBy += bsdWrapper.__class__.__name__ + ' marked for delete by '
        elif bsdState & dbutil.BSDSTATE_OPENFOREDIT != 0:
            openedBy += bsdWrapper.__class__.__name__ + ' opened for edit by '
        elif openedByUserIDs:
            openedBy += bsdWrapper.__class__.__name__ + ' opened in unknown state by '
        if not openedBy:
            return openedBy
        openedBy += ', '.join((bsdWrapper.cache.Row(const.cacheStaticUsers, userID).userName for userID in openedByUserIDs))
        return openedBy

    def Copy(self, groupID, newLabel = None):
        """
        Copy the current message into groupID with the new Label. All metadata will be copied as well.
        parameters:
            groupID  - destination group. The message label needs to be unique in the destination group.
                       The group's wordType also needs to be the same as the message wordTypeID.
            newLabel - if set, the message's label will be changed to this new label
        pre-req:
            This method must not be ran within Transaction
        exceptions:
            Will throw various exceptions on unsuccessful Copy.
        returns:
            New row of the copied message
        """
        Message._ErrorIfInTransaction('Message Copy will not run within Transaction.')
        copyLabel = newLabel or self.label
        if not Message.CheckIfLabelUnique(copyLabel, groupID):
            raise AuthoringValidationError('Label (%s) is not unique.' % copyLabel)
        messageCopy = Message.Create(copyLabel, groupID, text=self.GetTextEntry(LOCALE_SHORT_ENGLISH).text, context=self.context)
        englishText = messageCopy.GetTextEntry(LOCALE_SHORT_ENGLISH)
        originalEnglishText = self.GetTextEntry(LOCALE_SHORT_ENGLISH)
        originalTexts = self.messageTextTable.GetRows(messageID=self.messageID, _getDeleted=False)
        for aText in originalTexts:
            if aText.numericLanguageID != localizationBSDConst.LOCALE_ID_ENGLISH:
                newSourceDataID = englishText.dataID if originalEnglishText.dataID == aText.sourceDataID else None
                self.messageTextTable.AddRow(messageCopy.messageID, aText.numericLanguageID, sourceDataID=newSourceDataID, text=aText.text, statusID=aText.statusID)

        locWordMetaData.WordMetaData._CopyAllMetaDataToNewMessage(sourceMessageID=self.messageID, destMessageID=messageCopy.messageID, destinationWordTypeID=messageCopy.wordTypeID)
        return messageCopy

    def ResetWordType(self):
        """
        Change the wordTypeID of this message to None. This operation will remove all metadata belonging to 
        this message.
        NOTE: This code is bsd transaction friendly.
        """
        if self.wordTypeID is not None:
            with bsd.BsdTransaction():
                self._DeleteMetaData()
                bsdWrappers.BaseWrapper.__setattr__(self, 'wordTypeID', None)

    def GetAllMetaDataEntries(self, languageID):
        """
        Return all metadata entries for this language
        returns:
            list of metadata row objects
        """
        metaDataForLanguage = []
        dbLanguageID = GetNumericLanguageIDFromLanguageID(languageID)
        propertyTable = self.__class__._propertyTable
        allMetaData = locWordMetaData.WordMetaData.GetWithFilter(messageID=self.messageID)
        for metaEntry in allMetaData:
            propertyRow = propertyTable.GetRowByKey(metaEntry.wordPropertyID)
            if propertyRow and propertyRow.numericLanguageID == dbLanguageID:
                metaDataForLanguage.append(metaEntry)

        return metaDataForLanguage

    def GetMetaDataEntry(self, wordPropertyID):
        """
        Return metadata for the specified property.
        returns:
            metadata row object if found, None if property or metadata isnt found
        """
        metaDataRows = locWordMetaData.WordMetaData.GetWithFilter(messageID=self.messageID, wordPropertyID=wordPropertyID)
        if metaDataRows and len(metaDataRows):
            return metaDataRows[0]
        else:
            return None

    def GetMetaDataEntryByName(self, propertyName, languageID):
        """
        Return metadata for the specified property / language.
        returns:
            metadata row object if found, None if property or metadata isnt found
        """
        propertyRows = self.__class__._propertyTable.GetRows(wordTypeID=self.wordTypeID, propertyName=propertyName, numericLanguageID=GetNumericLanguageIDFromLanguageID(languageID), _getDeleted=False)
        if propertyRows and len(propertyRows) != 1:
            return None
        else:
            metaDataRows = locWordMetaData.WordMetaData.GetWithFilter(messageID=self.messageID, wordPropertyID=propertyRows[0].wordPropertyID)
            if metaDataRows and len(metaDataRows):
                return metaDataRows[0]
            return None

    def AddMetaDataEntry(self, wordPropertyID, metaDataValue, transactionBundle = None):
        """
        Add new metadata entry to this message. Will throw an error if the metadata entry already exists.
        NOTE: This code is bsd transaction friendly.
        parameters:
            wordPropertyID    - unique identifier for the property
            metaDataValue     - metadata string
            transactionBundle - cache containing entries of messages to be added within transaction.
                                It is required for validations within transactions. See CreateMessageDataBundle()
        """
        if self.wordTypeID == None:
            raise AuthoringValidationError('Before adding metadata, the wordType needs to be set on this messageID (%s).' % str(self.messageID))
        with bsd.BsdTransaction():
            locWordMetaData.WordMetaData.TransactionAwareCreate(wordPropertyID, self.messageID, metaDataValue, transactionBundle=transactionBundle)

    def AddMetaDataEntryByName(self, propertyName, languageID, metaDataValue, transactionBundle = None):
        """
        Add new metadata entry to this message. Will throw an error if the metadata entry already exists.
        NOTE: This code is bsd transaction friendly.
        parameters:
            propertyName      - name of the property
            languageID        - id for the language. For example "en-us"
            metaDataValue     - metadata string
            transactionBundle - cache containing entries of messages to be added within transaction.
                                It is required for validations within transactions. See CreateMessageDataBundle()
        """
        if self.wordTypeID == None:
            raise AuthoringValidationError('Before adding metadata, the wordType needs to be set on this messageID (%s).' % str(self.messageID))
        typeRow = locWordType.WordType.Get(self.wordTypeID)
        if typeRow == None:
            raise AuthoringValidationError('WordTypeID (%s), of this message, does not exist.' % self.wordTypeID)
        typeName = typeRow.typeName
        with bsd.BsdTransaction():
            locWordMetaData.WordMetaData.TransactionAwareCreateFromPropertyName(typeName, propertyName, languageID, self.messageID, metaDataValue, transactionBundle)

    def GetTextEntry(self, languageID):
        """
        Returns text row for the language specified
        returns:
            text row or None if none found
        """
        return locMessageText.MessageText.Get(self.messageID, languageID)

    def AddTextEntry(self, languageID, text):
        """
        Add text entry for the language, if one doesnt exist
        NOTE: This code is bsd transaction friendly.
        """
        textRow = locMessageText.MessageText.Get(self.messageID, languageID)
        if textRow == None:
            locMessageText.MessageText.Create(self.messageID, languageID, text=text)
        else:
            raise AuthoringValidationError('Can not add duplicate text entry. messageID,languageID : (%s, %s)' % (str(self.messageID), languageID))

    def GetState(self):
        """
        Aggregates bsd state information across all components of a message (label, texts for each language, and metadata for each language)
        """
        bsdState = super(Message, self).GetState()
        for messageText in locMessageText.MessageText.GetWithFilter(messageID=self.messageID):
            bsdState |= messageText.GetState()

        for metadata in locWordMetaData.WordMetaData.GetWithFilter(messageID=self.messageID):
            bsdState |= metadata.GetState()

        return bsdState

    def GetWordCount(self, languageID = 'en-us', includeMetadata = True):
        """
        Does a naive word count of the message text in the given language (splitting on spaces).
        By default, includes the number of words in all metadata entries, where present.
        """
        textEntry = self.GetTextEntry(languageID)
        if not textEntry:
            return 0
        count = len([ part for part in re.findall('\\w*', textEntry.text or '') if part ])
        if includeMetadata:
            metadataEntries = self.GetAllMetaDataEntries(languageID)
            for metadata in metadataEntries:
                if metadata.metaDataValue:
                    count += len([ part for part in re.findall('\\w*', metadata.metaDataValue or '') if part ])

        return count

    def __init__(self, row):
        bsdWrappers.BaseWrapper.__init__(self, row)
        self.__class__.CheckAndSetCache()
        self.messageTextTable = self.__class__._messageTextTable

    def __setattr__(self, key, value):
        if key == localizationBSDConst.COLUMN_LABEL:
            if not Message.CheckIfLabelUnique(value, self.groupID):
                raise AuthoringValidationError('Label can not be set to non-unique name (%s).' % str(value))
        if key == localizationBSDConst.COLUMN_TYPE_ID:
            if self.wordTypeID is not None:
                raise AuthoringValidationError('Not allowed to edit wordTypeID on the message that may contain metadata. Use ResetWordType().')
            elif locWordType.WordType.Get(value) is None:
                raise AuthoringValidationError('WordTypeID (%s) does not exist.' % str(value))
        bsdWrappers.BaseWrapper.__setattr__(self, key, value)

    def _DeleteChildren(self):
        with bsd.BsdTransaction('Deleting message: %s' % self.label):
            self._DeleteText()
            self._DeleteMetaData()
        return True

    def _DeleteText(self):
        for messageText in locMessageText.MessageText.GetMessageTextsByMessageID(self.messageID):
            if not messageText.Delete():
                raise AuthoringValidationError('Message (%s) wrapper was unable to delete text entry.' % self.messageID)

    def _DeleteMetaData(self):
        for metaData in locWordMetaData.WordMetaData.GetWithFilter(messageID=self.messageID):
            if not metaData.Delete():
                raise AuthoringValidationError('Message (%s) wrapper was unable to metadata entry.' % self.messageID)

    @classmethod
    def Get(cls, messageID):
        return bsdWrappers._TryGetObjByKey(cls, messageID, _getDeleted=False)

    @classmethod
    def CheckAndSetCache(cls):
        """
        Reset cache on the class.
        """
        if cls._messageTextTable is None or cls._propertyTable is None:
            bsdTableSvc = sm.GetService('bsdTable')
            cls._messageTextTable = bsdTableSvc.GetTable(localizationBSDConst.MESSAGE_TEXTS_TABLE)
            cls._propertyTable = bsdTableSvc.GetTable(localizationBSDConst.WORD_PROPERTIES_TABLE)
            cls._bsdSvc = sm.GetService('BSD')

    @classmethod
    def Create(cls, label, groupID = None, text = '', context = None):
        """
        Creates a new message label, and a blank English string by default.
        parameters:
            label      - label of the message. Must be unique
            groupID    - destination group. Must match the wordType of this message
            text       - english text
            context    - description for this message entry
        pre-req:
            this MUST NOT be called within nested Transactions. This not what this method for.
        exceptions:
            throws various exceptions on failures
        returns:
            row of the message that we just added
        """
        cls._ErrorIfInTransaction('Message Create will not run within Transaction. Use TransactionAwareCreate.')
        with bsd.BsdTransaction('Creating new message: %s' % label) as bsdTransaction:
            cls._TransactionAwareCreate(label, groupID, LOCALE_SHORT_ENGLISH, text, context, wordTypeID=None, transactionBundle=None)
        resultList = bsdTransaction.GetTransactionResult()
        return cls.Get(resultList[0][1].messageID)

    @classmethod
    def TransactionAwareCreate(cls, label, groupID = None, text = '', context = None, transactionBundle = None):
        """
        This is the transaction-aware portion of the create code. It is split up from Create() on purpose; in order to 
        allow other Wrappers to include these operations as port of their transaction as well.
        Purpose: Creates a new message label, and a blank English string by default.
        parameters:
            label      - label of the message. Must be unique
            groupID    - destination group. Must match the wordType of this message
            text       - english text
            context    - description for this message entry
            wordTypeID - type of the message
            transactionBundle - cache containing entries of messages to be added within transaction.
                                It is required for validations within transactions. See CreateMessageDataBundle()
        pre-req:
            this IS meant to be called within nested Transactions.
        Returns:  reserved actionID dictionary for the message, that will be added when transaction is done.
                  The return is formated as:    
                      {"reservedMessageID": INTEGER}
                  Notice: when things in base fail, this may return None
        """
        cls._ErrorIfNotInTransaction('Message TransactionAwareCreate will not run within Transaction. Use Create.')
        with bsd.BsdTransaction('Creating new message: %s' % label):
            actionIDsResult = cls._TransactionAwareCreate(label, groupID, LOCALE_SHORT_ENGLISH, text, context, wordTypeID=None, transactionBundle=transactionBundle)
        return actionIDsResult

    @classmethod
    def _GetGroupRecord(cls, groupID, transactionBundle = None):
        """
        get the group entry, to resolve issue between actionIDs + bundles and live data
        """
        from messageGroup import MessageGroup
        if transactionBundle and type(groupID) != int:
            currentGroup = transactionBundle.get(localizationBSDConst.BUNDLE_GROUP, {}).get(groupID, None)
        else:
            currentGroup = MessageGroup.Get(groupID)
        return currentGroup

    @classmethod
    def _GetWordTypeID(cls, groupID, transactionBundle = None):
        """
        Resolving two required pieces of data for message creation.
        """
        wordTypeID = None
        if groupID is not None:
            parentGroup = cls._GetGroupRecord(groupID, transactionBundle=transactionBundle)
            if parentGroup:
                wordTypeID = parentGroup.wordTypeID
        return wordTypeID

    @classmethod
    def _ValidateCreationOfMessage(cls, label, groupID, wordTypeID, transactionBundle = None):
        """
        validate various things before allowing this entry to be created
        the function is expected to interrupt this execution if things are wrong
        """
        if not cls.CheckIfLabelUnique(label, groupID, transactionBundle=transactionBundle):
            raise AuthoringValidationError('Label (%s) in groupID (%s) is not unique.' % (label, str(groupID)))
        if groupID != None:
            parentGroup = cls._GetGroupRecord(groupID, transactionBundle=transactionBundle)
            if parentGroup:
                if wordTypeID != parentGroup.wordTypeID:
                    raise AuthoringValidationError('Group type doesnt match message type (%s,%s).' % (wordTypeID, parentGroup.wordTypeID))
            else:
                raise AuthoringValidationError("Parent group (%s) wasn't found." % str(groupID))
        if wordTypeID != None:
            typeRow = locWordType.WordType.Get(wordTypeID)
            if typeRow == None:
                raise AuthoringValidationError("Type (%s) wasn't found." % wordTypeID)
        return True

    @classmethod
    def _TransactionAwareCreate(cls, label, groupID, languageID, text, context, wordTypeID = None, transactionBundle = None):
        """
        Worker function for transaction-aware portion of the create code.
        parameters:
            label      - label of the message. Must be unique
            groupID    - destination group. Must match the wordType of this message
            languageID - id for text entry
            text       - text entry
            context    - description for this message entry
            wordTypeID - type of the message
            transactionBundle - cache containing entries of messages to be added within transaction.
                                It is required for validations within transactions. See CreateMessageDataBundle()
        Returns:  reserved actionID dictionary for the message, that will be added when transaction is done.
                  The return is formated as:    
                      {"reservedMessageID": INTEGER}
        pre-req:
            always meant to run in transaction
        """
        inheritedWordTypeID = Message._GetWordTypeID(groupID)
        if wordTypeID is None:
            wordTypeID = inheritedWordTypeID
        Message._ValidateCreationOfMessage(label, groupID, wordTypeID, transactionBundle=transactionBundle)
        dbLocaleID = GetNumericLanguageIDFromLanguageID(languageID)
        if dbLocaleID is None:
            raise AuthoringValidationError('Didnt find language (%s).' % languageID)
        reservedActionID = bsdWrappers.BaseWrapper._Create(cls, label=label, groupID=groupID, context=context, wordTypeID=wordTypeID)
        if transactionBundle:
            tupleActionID = (reservedActionID, 'messageID')
            transactionBundle[localizationBSDConst.BUNDLE_MESSAGE][tupleActionID] = util.KeyVal({'label': label,
             'groupID': groupID,
             'context': context,
             'wordTypeID': wordTypeID})
        messageTextTable = bsdWrappers.GetTable(locMessageText.MessageText.__primaryTable__)
        messageTextTable.AddRow((reservedActionID, 'messageID'), dbLocaleID, text=text)
        if type(reservedActionID) == int:
            return {'reservedMessageID': reservedActionID}
        raise AuthoringValidationError('Unexpected error. Possibly incorrect use of transactions. Expected actionID but instead got : %s ' % str(reservedActionID))

    @classmethod
    def _ErrorIfInTransaction(cls, errorMessage):
        cls.CheckAndSetCache()
        if cls._bsdSvc.TransactionOngoing():
            raise AuthoringValidationError(errorMessage)

    @classmethod
    def _ErrorIfNotInTransaction(cls, errorMessage):
        cls.CheckAndSetCache()
        if not cls._bsdSvc.TransactionOngoing():
            raise AuthoringValidationError(errorMessage)

    @staticmethod
    def CheckIfLabelUnique(originalLabel, groupID, transactionBundle = None, _appendWord = None):
        """
        Check against data in DB of label is unique
        parameters:
            groupID           - parent group
            transactionBundle - see CreateMessageDataBundle()
        return:
            True or False
        """
        isUnique, label = Message._CheckLabelUniqueness(originalLabel, groupID, transactionBundle=transactionBundle, returnUnique=False, _appendWord=_appendWord)
        return isUnique

    @staticmethod
    def GetUniqueLabel(originalLabel, groupID, transactionBundle = None, _appendWord = None):
        """
        Generate unique label against data in DB.
        parameters:
            groupID           - parent group
            transactionBundle - see CreateMessageDataBundle()
        return:
            unique label
        """
        isUnique, label = Message._CheckLabelUniqueness(originalLabel, groupID, transactionBundle=transactionBundle, returnUnique=True, _appendWord=_appendWord)
        return label

    @staticmethod
    def GetMessageByID(messageID):
        primaryTable = bsdWrappers.GetTable(Message.__primaryTable__)
        return primaryTable.GetRowByKey(_wrapperClass=Message, keyId1=messageID, _getDeleted=False)

    @staticmethod
    def GetMessagesByGroupID(groupID, projectID = None):
        """
        Returns all messages directly beneath the parent group. 
        If ProjectID is specified then return all messages under this group, tagged for this project.
        """
        return Message.GetWithFilter(groupID=groupID)

    @staticmethod
    def _CheckLabelUniqueness(originalLabel, groupID, transactionBundle = None, returnUnique = False, _appendWord = None):
        """
        Check or get unique label (if returnUnique is set to True)
        return:
            tuple: (if label is unique, unique label string)
        """
        isOriginalLabelUnique = True
        if originalLabel is None:
            return (isOriginalLabelUnique, None)
        primaryTable = bsdWrappers.GetTable(Message.__primaryTable__)
        newLabel = originalLabel
        while True:
            labels = primaryTable.GetRows(label=newLabel, groupID=groupID, _getDeleted=True)
            atLeastOneMatch = False
            if transactionBundle:
                for key, aLabel in transactionBundle[localizationBSDConst.BUNDLE_MESSAGE].iteritems():
                    if aLabel.label == newLabel and aLabel.groupID == groupID:
                        atLeastOneMatch = True
                        break

            if labels and len(labels) or atLeastOneMatch:
                isOriginalLabelUnique = False
                if returnUnique:
                    newLabel = newLabel + (Message._APPEND_NEW if not _appendWord else _appendWord)
                else:
                    break
            else:
                break

        if returnUnique:
            return (isOriginalLabelUnique, newLabel)
        else:
            return (isOriginalLabelUnique, None)
