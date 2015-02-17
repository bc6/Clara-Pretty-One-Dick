#Embedded file name: localization\localizationBase.py
import __builtin__
import cPickle as pickle
import blue
import telemetry
import logmodule
import eveLocalization
import hashlib
import sys
from carbon.common.script.sys.service import ROLEMASK_ELEVATEDPLAYER
from carbon.common.script.util.commonutils import StripTags
from . import const as locconst, util, internalUtil
from .settings import qaSettings, bilingualSettings
from .parser import _Tokenize
from .logger import LogInfo, LogWarn, LogError, LogTraceback
from .uiutil import PrepareLocalizationSafeString
OFFSET_TEXT = 0
OFFSET_METADATA = 1
OFFSET_TOKENS = 2

class Localization(object):
    __guid__ = 'localization.Localization'
    PICKLE_EXT = '.pickle'
    CLIENT_PREFIX = 'res:/localization/localization_'
    FSD_CLIENT_PREFIX = 'res:/localizationFSD/localization_fsd_'
    FIELD_LABELS = 'labels'
    FIELD_LANGUAGES = 'languages'
    FIELD_MAPPING = 'mapping'
    FIELD_REGISTRATION = 'registration'
    FIELD_TYPES = 'types'
    FIELD_MAX_REVISION = 'maxRevision'
    FIELD_IMPORTANT = 'important'

    def __init__(self):
        self._InitializeInternalVariables()
        self._InitializeTextData()
        self._importantNameSetting = None
        self._languageTooltipSetting = None
        self._qaTooltipOverride = None
        self._highlightImportantSetting = None
        message = 'Cerberus localization module loaded on ' + boot.role
        LogInfo(message)
        print message

    def LoadLanguageData(self):
        import propertyHandlers
        if boot.role == 'client':
            internalUtil.ClearLanguageID()
        picklePrefixes = [(self.CLIENT_PREFIX, locconst.DATATYPE_BSD), (self.FSD_CLIENT_PREFIX, locconst.DATATYPE_FSD)]
        supportedLanguagesByPrefix = {}
        for prefix, dataType in picklePrefixes:
            supportedLanguagesByPrefix[prefix] = self._ReadLocalizationMainPickle(prefix + 'main' + self.PICKLE_EXT, dataType)
            if not supportedLanguagesByPrefix[prefix]:
                message = 'Cerberus localization module failed to load MAIN pickle on ' + boot.role + '.  See log server for details.'
                LogError(message)
                print message
                return

        self._ValidateAndRepairPrefs()
        for prefix, dataType in picklePrefixes:
            if not self._ReadLocalizationLanguagePickles(prefix, supportedLanguagesByPrefix[prefix], dataType):
                message = 'Cerberus localization module failed to load language pickles on ' + boot.role + '. See log server for details.'
                LogError(message)
                print message
                return

    def GetLanguages(self):
        return list(self.languagesDefined)

    @telemetry.ZONE_METHOD
    def LoadPrimaryLanguage(self, prefix, dataType):
        """
        Loads the primary language for the client (does nothing on proxy/server). The primary
        language defaults to "en-us", but can be passed in if necessary
        parameters:
            languageID    - language id
        return
            True if success, False otherwise
        """
        languageID = self._GetPrimaryLanguage()
        self._primaryLanguageID = languageID
        eveLocalization.SetPrimaryLanguage(languageID)
        if self._primaryLanguageID in self.languagesDefined:
            if not self._LoadLanguagePickle(prefix, self._primaryLanguageID, dataType):
                return False
        else:
            LogError("Language '", languageID, "' is not enabled. Text data was not loaded.")
            return False
        return True

    @telemetry.ZONE_METHOD
    def GetByMapping(self, resourceName, keyID, propertyName = None, languageID = None, **kwargs):
        """
        Retrieves and renders a string for the record in the registered resource. The resourceName
        string maps to the schema, table and column that it was originally imported from.
        If propertyName is specified then a metadata text is returned.
        parameters:
            resourceName    - name of the registered resource.
                              The name follows the format: <SCHEMA>.<TABLE>.<COLUMN>
                              For example "agent.missionView.messageText"
            keyID           - unique ID of the record in the table above, for which to get
                              the text entry
            propertyName    - name of the metadata property
            languageID      - character language code. Exp: 'en-us' for English
                              Note: if no languageID is passed a default one will be picked.
            **kwargs        - variable definitions for dynamic text
        returns:
            Text string or metadata string.
            A [no resource:%s, %s] string if no text was found.
        """
        try:
            tableRegID = self.tableRegistration[resourceName]
            messageID = self.messageMapping[tableRegID, keyID]
        except KeyError as e:
            LogTraceback("No mapping entry for '", resourceName, "' with keyID ", keyID, '.  Usually this is either because the source column was NULL for this row (NULL entries are not imported), or because the source column has been deleted on the content database, but not the database you are using.')
            return u'[no resource: %s, %s]' % (resourceName, keyID)

        if propertyName is None:
            return self.GetByMessageID(messageID, languageID, **kwargs)
        else:
            return self.GetMetaData(messageID, propertyName, languageID)

    def GetImportantByMessageID(self, messageID, **kwargs):
        """
            This wrapper calls GetByMessageID for important strings, and uses the important-name settings in localized
            clients to determine (a) which language the important message should be shown in and (b) whether the
            important message should have a tooltip. This should only be called from the client.
        """
        if boot.region == 'optic':
            if not (session and session.role & ROLEMASK_ELEVATEDPLAYER):
                return self.GetByMessageID(messageID, **kwargs)
        if boot.role == 'proxy':
            return self.GetByMessageID(messageID, **kwargs)
        playerLanguageID = internalUtil.GetLanguageID()
        if playerLanguageID != self._primaryLanguageID or self._QaTooltipOverride():
            if self.UsePrimaryLanguageText():
                textString = self.GetByMessageID(messageID, self._primaryLanguageID, **kwargs)
                hintLang = playerLanguageID
            else:
                textString = self.GetByMessageID(messageID, playerLanguageID, **kwargs)
                hintLang = self._primaryLanguageID
            if self.HighlightImportant():
                textString = '%s%s' % (textString, locconst.HIGHLIGHT_IMPORTANT_MARKER)
            if self.UseImportantTooltip() and not qaSettings.LocWrapSettingsActive():
                if self._QaTooltipOverride() and playerLanguageID == self._primaryLanguageID:
                    hintString = textString[:-1][::-1]
                else:
                    hintString = self.GetByMessageID(messageID, hintLang, **kwargs)
                hintString = hintString.replace('"', "'").replace('<', '[').replace('>', ']')
                textString = '<localized hint="%s">%s</localized>' % (hintString or '', textString)
        else:
            textString = self.GetByMessageID(messageID, **kwargs)
        return textString

    def GetImportantByLabel(self, labelNameAndPath, **kwargs):
        try:
            messageID = self.languageLabels[labelNameAndPath]
        except KeyError:
            LogTraceback("No label with name '", labelNameAndPath, "'.")
            return '[no label: %s]' % labelNameAndPath

        return self.GetImportantByMessageID(messageID, **kwargs)

    def FormatImportantString(self, locText, englishText):
        """
            Utility method to get the important message formatting on any random text. Since some data objects (like stations) are
            dependant on other cfg objects (like owners), then we have to use this method to get the proper important name formatting
            without nesting the important names and tooltips.
        """
        if boot.region == 'optic':
            if not (session and session.role & ROLEMASK_ELEVATEDPLAYER):
                return locText
        playerLanguageID = internalUtil.GetLanguageID()
        if playerLanguageID == self._primaryLanguageID and self._QaTooltipOverride():
            return '<localized hint="%s">%s*</localized>' % (englishText[::-1], englishText)
        if playerLanguageID != self._primaryLanguageID:
            if self.UsePrimaryLanguageText():
                textString = englishText
                hintText = locText
            else:
                textString = locText
                hintText = englishText
            if self.HighlightImportant():
                textString = '%s*' % textString
            if self.UseImportantTooltip() and not qaSettings.LocWrapSettingsActive():
                textString = '<localized hint="%s">%s</localized>' % (hintText, textString)
        else:
            textString = locText
        return textString

    def CleanImportantMarkup(self, textString):
        if self.UseImportantTooltip():
            textString = StripTags(textString, stripOnly=['localized'])
        if self.HighlightImportant() and len(textString) > 1 and textString[-1] == '*':
            textString = textString.replace(locconst.HIGHLIGHT_IMPORTANT_MARKER, '')
        return textString

    def GetByMessageID(self, messageID, languageID = None, **kwargs):
        """
        Retrieves and renders a label from the Language data.
        parameters:
            messageID    - unique & central ID of the label/string
            languageID   - character language code. Exp: 'en-us' for English
                           Note: if no languageID is passed a default one will be picked.
            **kwargs     - variable definitions for dynamic text
        returns:
            a [no message:%s] string if no text was found, None if the messageID was None, or the text if it was found.
        """
        if messageID is None:
            return ''
        languageID = util.StandardizedLanguageIDOrDefault(languageID)
        if session and 'player' not in kwargs:
            kwargs['player'] = session.charid
        try:
            textString = self._GetByMessageID(messageID, languageID, **kwargs)
            return PrepareLocalizationSafeString(textString, messageID=messageID)
        except KeyError:
            return u'[no messageID: %s]' % messageID
        except:
            logmodule.LogException()
            try:
                return self._GetRawByMessageID(messageID)
            except:
                return u'[no messageID: %s]' % messageID

    def GetByLabel(self, labelNameAndPath, languageID = None, **kwargs):
        """
        Retrieves and renders a label from the Language data.
        parameters:
            labelNameAndPath     - unique combination of the path and label name for the specific label/string.
                                   For example : "Category/Category/My Label"
            languageID           - character language code. Exp: 'en-us' for English
                                   Note: if no languageID is passed a default one will be picked.
            **kwargs             - variable definitions for dynamic text
        returns:
            a [no label:%s] string if no text was found. Returns text otherwise.
        """
        try:
            messageID = self.languageLabels[labelNameAndPath]
        except KeyError:
            LogTraceback("No label with name '", labelNameAndPath, "'.")
            return '[no label: %s]' % labelNameAndPath

        return self.GetByMessageID(messageID, languageID, **kwargs)

    def IsValidMessageID(self, messageID, languageID = None):
        """
        Checks if message is valid (exists) for the messageID and languageID specified.
        parameters:
            messageID    - unique & central ID of the label/string
            languageID   - character language code. Exp: 'en-us' for English
                           Note: if no languageID is passed a default one will be picked.
        returns:
            True, if message with said messageID was found. False, otherwise.
        """
        languageID = util.StandardizedLanguageIDOrDefault(languageID)
        return eveLocalization.IsValidMessageID(messageID, languageID)

    def IsValidLabel(self, labelNameAndPath, languageID = None):
        """
        Checks if label is valid (exists) for the languageID specified.
        parameters:
            labelNameAndPath     - unique combination of the path and label name for the specific label/string.
                                   For example : "Category/Category/MyLabel"
            languageID           - character language code. Exp: 'en-us' for English
                                   Note: if no languageID is passed a default one will be picked.
        returns:
            True, if label was found. False, otherwise.
        """
        try:
            messageID = self.languageLabels[labelNameAndPath]
            return self.IsValidMessageID(messageID, languageID)
        except KeyError:
            return False

    def IsValidMapping(self, resourceName, keyID):
        """
        Checks if message mapping is valid (exists) for the messageID specified.
        parameters:
            resourceName - name of the registered resource.
                           The name follows the format: <SCHEMA>.<TABLE>.<COLUMN>
                           For example "agent.missionView.messageText"
            keyID        - unique ID of the record in the table above, for which to get
                           the text entry
        returns:
            True, if mapping was found. False, otherwise.
        """
        if resourceName in self.tableRegistration:
            return (self.tableRegistration[resourceName], keyID) in self.messageMapping
        return False

    def IsValidTypeAndProperty(self, typeName, propertyName, languageID = None):
        """
        Checks if type and properties valid (exist) for the languageID specified.
        parameters:
            typeName     - name of the word type
            propertyName - name of the metadata property
            languageID   - character language code. Exp: 'en-us' for English
                           Note: if no languageID is passed a default one will be picked.
                           Also, if Pseudoloc ID was passed, English will be picked.
        returns True or False
        """
        IS_INVALID_TYPE = 0
        IS_INVALID_PROPERTY = 1
        IS_VALID_TYPE_AND_PROPERTY = 2
        result = None
        languageID = util.StandardizedLanguageIDOrDefault(languageID)
        foundType = self.languageTypesWithProperties.get(typeName, None)
        if foundType is not None:
            foundPropertyList = foundType.get(languageID, None)
            if foundPropertyList is not None:
                if propertyName in foundPropertyList:
                    result = IS_VALID_TYPE_AND_PROPERTY
                else:
                    result = IS_INVALID_PROPERTY
            else:
                result = IS_INVALID_PROPERTY
        else:
            result = IS_INVALID_TYPE
        if result == IS_INVALID_PROPERTY:
            LogError("'%s' is not a valid property for '%s' in language '%s'." % (propertyName, typeName, languageID))
        elif result == IS_INVALID_TYPE:
            LogError("'%s' is not a valid type; cannot retrieve properties for it." % typeName)
        elif result is None:
            LogError('IsValidTypeAndProperty wasnt able to determine if type and property were valid: %s, %s' % (typeName, propertyName))
        return result == IS_VALID_TYPE_AND_PROPERTY

    def GetMetaData(self, messageID, propertyName, languageID = None):
        """
        Retrieves a metadata for property for the specified message (messageID).
        parameters:
            messageID    - unique & central ID of the label/string
            propertyName - name of the metadata property
            languageID   - character language code. Exp: 'en-us' for English
                           Note: if no languageID is passed a default one will be picked.
        returns:
            a [no property:%s,%s] string if no text was found. Returns text otherwise.
        """
        languageID = util.StandardizedLanguageIDOrDefault(languageID)
        propertyString = self._GetMetaData(messageID, propertyName, languageID)
        if propertyString is not None:
            return PrepareLocalizationSafeString(propertyString, messageID=messageID)
        LogError('a non existent property was requested. messageID,propertyName,languageID : %s,%s,%s' % (messageID, propertyName, languageID))
        return '[no property:%s,%s]' % (messageID, propertyName)

    def GetPlaceholderLabel(self, englishText, **kwargs):
        """
        Method to temporary display all hardcoded strings. The method will log a warning reminding to remove
        the hardcoded string from the code when done.
        
        Placeholders are expected to be in English, so that markup tags that are language-sensitive will render
        properly if the client is not in English.
        
        parameters:
            englishText     - the english hardcoded string
            **kwargs        - variable definitions for dynamic text
        """
        tags = _Tokenize(englishText)
        parsedText = eveLocalization.Parse(englishText, locconst.LOCALE_SHORT_ENGLISH, tags, **kwargs)
        LogWarn('Placeholder label (%s) needs to be replaced.' % englishText)
        return '!_%s_!' % parsedText

    def _ValidateAndRepairPrefs(self):
        """
        Loads the language prefs for the client and then validates it.
        If it is incorrect we set it to something we think will work.
        """
        if boot.role == 'client':
            while not hasattr(__builtin__, 'prefs'):
                blue.synchro.Yield()

            prefsLanguage = prefs.GetValue('languageID', None)
            if not prefsLanguage or util.ConvertLanguageIDFromMLS(prefsLanguage) not in self.GetLanguages():
                prefs.languageID = 'EN' if boot.region != 'optic' else 'ZH'

    @telemetry.ZONE_METHOD
    def _ReadMainLocalizationData(self, unPickledObject, dataType):
        """
        Worker functions to read Main localization data from an object.
        parameters:
            unPickledObject    - data structure, usually read from a pickle file, containing
                                 main localization data. For example: labels, mappings, etc
                                 If you are passing one here yourself, you should ask yourself why.
        return
            Empty list [] there is any failure,
            otherwise a list of languages supported by this main pickle
        NOTE: this function is being unit tested
        """
        if unPickledObject and self.FIELD_LABELS in unPickledObject:
            labelsDict = unPickledObject[self.FIELD_LABELS]
            for aMessageID in labelsDict:
                dataRow = labelsDict[aMessageID]
                pathAndLabelKey = None
                if dataRow[locconst.PICKLE_LABELS_FULLPATH]:
                    aFullPath = dataRow[locconst.PICKLE_LABELS_FULLPATH]
                    pathAndLabelKey = '/'.join([aFullPath, dataRow[locconst.PICKLE_LABELS_LABEL]])
                else:
                    pathAndLabelKey = dataRow[locconst.PICKLE_LABELS_LABEL]
                self.languageLabels[pathAndLabelKey.encode('ascii')] = aMessageID

        else:
            LogError("didn't find 'labels' in the unpickled object.")
            return []
        langList = []
        if self.FIELD_LANGUAGES in unPickledObject:
            if isinstance(unPickledObject[self.FIELD_LANGUAGES], dict):
                langList = unPickledObject[self.FIELD_LANGUAGES].keys()
            else:
                langList = unPickledObject[self.FIELD_LANGUAGES]
            langList = filter(self._IsValidLanguage, langList)
            self.languagesDefined.update(langList)
        else:
            LogError("didn't find 'languages' in the unpickled object")
            return []
        if self.FIELD_TYPES in unPickledObject:
            self.languageTypesWithProperties.update(unPickledObject[self.FIELD_TYPES])
        else:
            LogError("didn't find 'types' in the unpickled object")
            return []
        if dataType == locconst.DATATYPE_BSD:
            if self.FIELD_REGISTRATION in unPickledObject and self.FIELD_MAPPING in unPickledObject:
                self.tableRegistration.update(unPickledObject[self.FIELD_REGISTRATION])
                self.messageMapping.update(unPickledObject[self.FIELD_MAPPING])
            else:
                LogError("didn't find 'mapping' or 'registration' in the unpickled object")
                return []
            if self.FIELD_IMPORTANT in unPickledObject:
                self.importantMessages.update(unPickledObject[self.FIELD_IMPORTANT])
            else:
                LogWarn("didn't find 'important' in the unpickled object")
            if self.FIELD_MAX_REVISION in unPickledObject:
                self.maxRevision = max(self.maxRevision, unPickledObject[self.FIELD_MAX_REVISION])
            else:
                LogError("didn't find 'maxRevision' in the unpickled object")
                return []
        return langList

    def _IsValidLanguage(self, languageID):
        if boot.role == 'client':
            if languageID == locconst.LOCALE_SHORT_CHINESE:
                return boot.region == 'optic'
            elif languageID == locconst.LOCALE_SHORT_ENGLISH:
                return True
            else:
                return boot.region != 'optic' and languageID not in ('it', 'es')
        return True

    @telemetry.ZONE_METHOD
    def _ReadLanguageLocalizationData(self, aLangCode, unPickledObject, dataType):
        """
        Worker functions to read Language specific text data from an object.
        parameters:
            aLangCode          - language id
            unPickledObject    - data structure, usually read from a pickle file, containing
                                 language specific data. For example: translated texts and
                                 metadata.
        return
            True if success, False, otherwise
        NOTE: this function is being unit tested
        """
        try:
            LogInfo('Loading all message data for language ', aLangCode)
            eveLocalization.LoadMessageData(*unPickledObject)
        except:
            logmodule.LogException()
            for x, y in unPickledObject[1].iteritems():
                if y[2] is not None and not isinstance(y[2], dict):
                    logmodule.LogError('%s: %s' % (x, repr(y)))

        return True

    @telemetry.ZONE_METHOD
    def UsePrimaryLanguageText(self):
        if self._importantNameSetting is None:
            if internalUtil.GetLanguageID() == self._primaryLanguageID:
                self._importantNameSetting = 0
            else:
                self._importantNameSetting = bilingualSettings.GetValue('localizationImportantNames')
        return self._importantNameSetting == bilingualSettings.IMPORTANT_NAME_ENGLISH

    def HighlightImportant(self):
        if self._highlightImportantSetting is None:
            if internalUtil.GetLanguageID() == self._primaryLanguageID:
                self._highlightImportantSetting = self._QaTooltipOverride()
            else:
                self._highlightImportantSetting = bilingualSettings.GetValue('localizationHighlightImportant')
        return self._highlightImportantSetting

    def UseImportantTooltip(self):
        if self._languageTooltipSetting is None:
            if internalUtil.GetLanguageID() == self._primaryLanguageID:
                self._languageTooltipSetting = self._QaTooltipOverride()
            else:
                self._languageTooltipSetting = bilingualSettings.GetValue('languageTooltip')
        return self._languageTooltipSetting

    def _QaTooltipOverride(self):
        if self._qaTooltipOverride is None:
            if internalUtil.GetLanguageID() == self._primaryLanguageID:
                self._qaTooltipOverride = qaSettings.GetValue('simulateTooltip')
            else:
                self._qaTooltipOverride
        return self._qaTooltipOverride

    def ClearImportantNameSetting(self):
        """
            Called when the user changes this setting in the escape menu
        """
        self._importantNameSetting = None
        self._highlightImportantSetting = None
        self._languageTooltipSetting = None
        self._qaTooltipOverride = None
        cfg.ReloadLocalizedNames()

    def _InitializeInternalVariables(self):
        """
        Function to clear internal variables. These dont get refreshed when pickles are reloaded.
        """
        self.hashDataDictionary = {}

    @telemetry.ZONE_METHOD
    def _InitializeTextData(self):
        """
        Worker function to initialize/clear internal text dictionaries. Notice these get refreshed when pickles are reloaded.
        """
        self.languagesDefined = set()
        self.languageLabels = {}
        self.importantMessages = {}
        self.languageTypesWithProperties = {}
        self.tableRegistration = {}
        self.messageMapping = {}
        self.maxRevision = None
        self._primaryLanguageID = None
        self._secondaryLanguageID = None

    @telemetry.ZONE_METHOD
    def UpdateTextCache(self, messagePerLanguage, metaDataPerLanguage, labelsDict):
        """
        Update the internal text and label dictionaries with the passed data.
        The cacheData consists of three dictionaries (as returned by localizationPickleExporter):
            messagePerLanguage, metaDataPerLanguage, labelsDict
        """
        for language in messagePerLanguage:
            LogInfo('Preparing to update internal text and label cache. The sizes of new data dictionaries are: ', len(messagePerLanguage.get(language, {})), ', ', len(metaDataPerLanguage.get(language, {})))
            if eveLocalization.HasLanguage(language):
                newData = {}
                for messageID, text in messagePerLanguage.get(language, {}).iteritems():
                    try:
                        metaData = None
                        ignore, metaData, ignore = eveLocalization.GetMessageDataByID(messageID, language)
                    except KeyError:
                        sys.exc_clear()

                    try:
                        newData[messageID] = (text, metaData, _Tokenize(text))
                    except:
                        logmodule.LogException()
                        continue

                try:
                    eveLocalization.LoadMessageData(language, newData)
                except:
                    logmodule.LogException()
                    continue

        for language in metaDataPerLanguage:
            if eveLocalization.HasLanguage(language):
                newData = {}
                for messageID, metaData in metaDataPerLanguage.get(language, {}).iteritems():
                    try:
                        text, ignore, tokens = eveLocalization.GetMessageDataByID(messageID, language)
                        newData[messageID] = (text, metaData, tokens)
                    except KeyError:
                        sys.exc_clear()

                try:
                    eveLocalization.LoadMessageData(language, newData)
                except:
                    logmodule.LogException()
                    continue

        LogInfo('Updating label cache. New data size is ', len(labelsDict))
        for label, messageID in labelsDict.iteritems():
            self.languageLabels[label.encode('ascii')] = messageID

    def GetMaxRevision(self):
        """
        Return revision number of set of pickle files. Currently this is the number recorded in the main pickle file.
        """
        return self.maxRevision

    def GetHashDataDictionary(self):
        """
        Return hash dictionary of pickle file hash numbers. The dictionary is keyed by pickle file identifier.
        for exp: {"main": <INT>, "en-us": <INT>}
        """
        return self.hashDataDictionary

    @telemetry.ZONE_METHOD
    def _ReadLocalizationMainPickle(self, pickleName, dataType):
        """
        Worker function that reads data from the main pickle in common/res and initializes internal data
        
        Returns the languages supported by the pickle file.
        """
        unPickledObject = self._LoadPickleData(pickleName, dataType)
        if unPickledObject is None:
            return []
        supportedLanguages = self._ReadMainLocalizationData(unPickledObject, dataType)
        if not supportedLanguages:
            LogError('Error reading main pickle file ', pickleName)
        del unPickledObject
        return supportedLanguages

    def _GetPrimaryLanguage(self):
        return locconst.LOCALE_SHORT_ENGLISH

    def IsPrimaryLanguage(self, languageID):
        languageID = util.StandardizedLanguageIDOrDefault(languageID)
        return languageID == self._GetPrimaryLanguage()

    @telemetry.ZONE_METHOD
    def _ReadLocalizationLanguagePickles(self, prefix, supportedLanguages, dataType):
        """
        Worker function that reads data from the language pickles in common/res and initializes internal data
        """
        primaryLanguage = self._GetPrimaryLanguage()
        if boot.role == 'client':
            prefsLanguage = util.StandardizedLanguageIDOrDefault(prefs.GetValue('languageID', None))
            if prefsLanguage != primaryLanguage and prefsLanguage in supportedLanguages:
                self._secondaryLanguageID = prefsLanguage
                if not (self.LoadPrimaryLanguage(prefix, dataType) and self._LoadLanguagePickle(prefix, prefsLanguage, dataType)):
                    return False
            else:
                return self.LoadPrimaryLanguage(prefix, dataType)
        elif boot.role == 'server' or boot.role == 'proxy':
            if not self.LoadPrimaryLanguage(prefix, dataType):
                return False
            for aLangCode in supportedLanguages:
                if aLangCode != self._primaryLanguageID and not self._LoadLanguagePickle(prefix, aLangCode, dataType):
                    return False

        return True

    @telemetry.ZONE_METHOD
    def _LoadLanguagePickle(self, prefix, languageID, dataType):
        """
        worker function to fully load a language from a pickle
        """
        unPickledObject = self._LoadPickleData(prefix + languageID + self.PICKLE_EXT, dataType)
        if unPickledObject == None:
            return False
        readStatus = self._ReadLanguageLocalizationData(languageID, unPickledObject, dataType)
        del unPickledObject
        return readStatus

    @telemetry.ZONE_METHOD
    def _LoadPickleData(self, pickleName, dataType):
        """
        Loads the specified pickle and returns the unpickled object
        """
        pickleFile = blue.ResFile()
        if not pickleFile.Open(pickleName):
            LogError('Could not load pickle file. ', pickleName, ' appears to be missing. The localization module will not be able to access labels or texts.')
            return None
        pickledData = pickleFile.Read()
        if not pickledData:
            pickleFile.Close()
            del pickleFile
            LogError('Could not read pickle data from file. ', pickleName, ' may be corrupt. The localization module will not be able to access labels or texts.')
            return None
        blue.statistics.EnterZone('pickle.loads')
        unPickledObject = pickle.loads(pickledData)
        blue.statistics.LeaveZone()

        @telemetry.ZONE_FUNCTION
        def md5ForFile(file, block_size = 1048576):
            md5 = hashlib.md5()
            while True:
                data = file.read(block_size)
                if not data:
                    break
                md5.update(data)

            return md5.digest()

        self.hashDataDictionary[pickleName] = md5ForFile(pickleFile)
        pickleFile.Close()
        del pickleFile
        del pickledData
        return unPickledObject

    def _GetRawByMessageID(self, messageID, languageID = None, **kwargs):
        """
        """
        languageID = util.StandardizedLanguageIDOrDefault(languageID)
        try:
            return eveLocalization.GetRawByMessageID(messageID, languageID)
        except:
            return '[no messageid: %s]' % messageID
