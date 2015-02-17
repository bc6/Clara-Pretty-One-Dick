#Embedded file name: localizationBSD/wrappers\messageText.py
from . import AuthoringValidationError
from .. import const as localizationBSDConst
from ..util import GetNumericLanguageIDFromLanguageID
from localization.const import LOCALE_SHORT_ENGLISH
import bsdWrappers

class MessageText(bsdWrappers.BaseWrapper):
    """
    A wrapper object for message strings, where a message can have multiple strings (one per supported language).  
    """
    __primaryTable__ = bsdWrappers.RegisterTable(localizationBSDConst.MESSAGE_TEXTS_TABLE)

    @classmethod
    def Create(cls, messageID, languageID = LOCALE_SHORT_ENGLISH, text = '', sourceDataID = None):
        primaryTable = bsdWrappers.GetTable(MessageText.__primaryTable__)
        dbLocaleID = GetNumericLanguageIDFromLanguageID(languageID)
        if dbLocaleID is None:
            raise RuntimeError('LanguageID %s could not be mapped to a locale ID.' % languageID)
        import message
        if not message.Message.Get(messageID):
            raise RuntimeError('Message ID %d does not exist! Message text not created for language %s' % (messageID, languageID))
        statusID = None
        if languageID != LOCALE_SHORT_ENGLISH:
            englishText = MessageText.GetMessageTextByMessageID(messageID, LOCALE_SHORT_ENGLISH)
            if englishText:
                if sourceDataID is None:
                    sourceDataID = englishText.dataID
                if MessageText._ValidateChangeToReview(None, sourceDataID, englishText.dataID):
                    statusID = localizationBSDConst.TEXT_STATUS_REVIEW
        return bsdWrappers.BaseWrapper._Create(cls, messageID, dbLocaleID, text=text, sourceDataID=sourceDataID, statusID=statusID)

    def SetTextAndSourceDataID(self, text, sourceDataID):
        """
        Set text and sourceDataID field the same time, while setting appropriate flag, like: Review. 
        """
        bsdWrappers.BaseWrapper.__setattr__(self, 'sourceDataID', sourceDataID)
        bsdWrappers.BaseWrapper.__setattr__(self, 'text', text)
        bsdWrappers.BaseWrapper.__setattr__(self, 'changed', False)
        englishText = MessageText.GetMessageTextByMessageID(self.messageID, LOCALE_SHORT_ENGLISH)
        if englishText:
            self._TrySettingToReview()

    def MarkTranslationAsCurrent(self):
        """
        Set this translation as translated vs current sourceDataID, by associating this translation to current English row (current in memory!).
        """
        if self.numericLanguageID != GetNumericLanguageIDFromLanguageID(LOCALE_SHORT_ENGLISH):
            englishText = MessageText.GetMessageTextByMessageID(self.messageID, LOCALE_SHORT_ENGLISH)
            if englishText:
                self.sourceDataID = englishText.dataID
        else:
            raise AuthoringValidationError("Cannot call SetAsTranslated() method on '%s' text entry with messageID '%s'. The method must be called on translations." % (LOCALE_SHORT_ENGLISH, self.messageID))

    def __setattr__(self, key, value):
        """
        Overwritting setattr in order to catch all edits to the row from external code.
        NOTE: other code in this object needs to be aware of this setattr when changing value of object variables. In other words, local code most likely shouldnt call this setattr.
        """
        if key == localizationBSDConst.COLUMN_TEXT and value != self.text:
            if self.numericLanguageID != GetNumericLanguageIDFromLanguageID(LOCALE_SHORT_ENGLISH):
                englishText = MessageText.GetMessageTextByMessageID(self.messageID, LOCALE_SHORT_ENGLISH)
                if englishText:
                    sourceDataID = englishText.dataID
                    bsdWrappers.BaseWrapper.__setattr__(self, 'sourceDataID', sourceDataID)
                    self._TrySettingToReview()
        bsdWrappers.BaseWrapper.__setattr__(self, key, value)

    def _TrySettingToReview(self):
        """
        Perform required validation and if passed, set the status of this text row to Review.
        """
        englishText = MessageText.GetMessageTextByMessageID(self.messageID, LOCALE_SHORT_ENGLISH)
        if englishText:
            if MessageText._ValidateChangeToReview(self.statusID, self.sourceDataID, englishText.dataID):
                self.statusID = localizationBSDConst.TEXT_STATUS_REVIEW

    @staticmethod
    def _ValidateChangeToReview(currentStatusID, currentSourceID, englishDataID):
        """
        Validate if ok to change to Review status. Can only change to Review if the current status is not explicitly specified or set to 'Defect'.
        """
        if englishDataID == currentSourceID and (currentStatusID is None or currentStatusID != localizationBSDConst.TEXT_STATUS_DEFECT):
            return True
        return False

    @classmethod
    def Get(cls, messageID, languageID = LOCALE_SHORT_ENGLISH, _getDeleted = False):
        dbLocaleID = GetNumericLanguageIDFromLanguageID(languageID)
        return bsdWrappers._TryGetObjByKey(cls, messageID, dbLocaleID, _getDeleted=_getDeleted)

    @staticmethod
    def GetMessageTextsByMessageID(messageID):
        """
        Returns text strings for all languages associated with this messageID.
        parameters:
            messageID - requested message ID
        """
        primaryTable = bsdWrappers.GetTable(MessageText.__primaryTable__)
        return primaryTable.GetRows(_wrapperClass=MessageText, messageID=messageID, _getDeleted=False)

    @staticmethod
    def GetMessageTextByMessageID(messageID, languageID):
        """
        Returns text strings for language associated with this messageID.
        parameters:
            messageID - requested message ID
        """
        primaryTable = bsdWrappers.GetTable(MessageText.__primaryTable__)
        dbLocaleID = GetNumericLanguageIDFromLanguageID(languageID)
        return primaryTable.GetRowByKey(_wrapperClass=MessageText, keyId1=messageID, keyId2=dbLocaleID, _getDeleted=False)
