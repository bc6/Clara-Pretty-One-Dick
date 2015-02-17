#Embedded file name: localization/propertyHandlers\characterPropertyHandler.py
import eveLocalization
from basePropertyHandler import BasePropertyHandler
from .. import const as locconst
import log

class CharacterPropertyHandler(BasePropertyHandler):
    """
    The character property handler class that defines the methods 
    to retrieve character-specific property data. 
    """
    PROPERTIES = {locconst.CODE_UNIVERSAL: ('name', 'rawName', 'gender'),
     locconst.LOCALE_SHORT_ENGLISH: ('nameWithPossessive',),
     locconst.LOCALE_SHORT_FRENCH: ('nameWithPossessive',),
     locconst.LOCALE_SHORT_GERMAN: ('genitiveName',),
     locconst.LOCALE_SHORT_RUSSIAN: ('genitiveName',)}
    GENDER_NORMALIZATION_MAPPING = {1: locconst.GENDER_MALE,
     0: locconst.GENDER_FEMALE}

    def _GetName(self, charID, languageID, *args, **kwargs):
        """
        Retrieve name of this PC or NPC.
        """
        try:
            return cfg.eveowners.Get(charID).ownerName
        except KeyError:
            log.LogException()
            return '[no character: %d]' % charID

    def _GetRawName(self, charID, languageID, *args, **kwargs):
        """
            Returns the localized name without respect to bilingual functionlity settings
        """
        try:
            return cfg.eveowners.Get(charID).GetRawName(languageID)
        except KeyError:
            log.LogException()
            return '[no character: %d]' % charID

    if boot.role != 'client':
        _GetName = _GetRawName

    def _GetGender(self, charID, languageID, *args, **kwargs):
        """
        Retrieve the gender of this PC or NPC.
        """
        try:
            return self.GENDER_NORMALIZATION_MAPPING[cfg.eveowners.Get(charID).gender]
        except KeyError:
            log.LogException()
            return self.GENDER_NORMALIZATION_MAPPING[0]

    def _GetNameWithPossessiveEN_US(self, charID, *args, **kwargs):
        """
        Method to retrieve possessive name in English
        """
        characterName = self._GetName(charID, languageID=locconst.LOCALE_SHORT_ENGLISH)
        return self._PrepareLocalizationSafeString(characterName + "'s")

    def _GetNameWithPossessiveFR(self, charID, *args, **kwargs):
        """
        Method to retrieve possessive name in English
        """
        characterName = self._GetName(charID, languageID=locconst.LOCALE_SHORT_FRENCH)
        if characterName and characterName[0].lower() in u'aeiouy':
            poss = u"d'"
        else:
            poss = u'de '
        return self._PrepareLocalizationSafeString(poss + characterName)

    def _GetGenitiveNameDE(self, charID, *args, **kwargs):
        """
        Method to retrieve genitive name in German
        """
        characterName = self._GetName(charID, languageID=locconst.LOCALE_SHORT_GERMAN)
        if characterName[-1:] not in 'sxz':
            characterName = characterName + 's'
        return self._PrepareLocalizationSafeString(characterName)

    def _GetGenitiveNameRU(self, charID, *args, **kwargs):
        """
        Method to retrieve genitive name in Russian
        """
        characterName = self._GetName(charID, languageID=locconst.LOCALE_SHORT_RUSSIAN)
        nameWithPossessive = self._PrepareLocalizationSafeString(characterName + '[possessive]')
        return nameWithPossessive

    def Linkify(self, charID, linkText):
        """
            Return the data for the character show info link. 
            For a character it is the type of the character and the charID
        """
        try:
            charInfo = cfg.eveowners.Get(charID)
        except KeyError:
            log.LogException()
            return '[no character: %d]' % charID

        if charInfo.typeID:
            return '<a href=showinfo:%d//%d>%s</a>' % (charInfo.typeID, charID, linkText)
        else:
            return linkText


eveLocalization.RegisterPropertyHandler(eveLocalization.VARIABLE_TYPE.CHARACTER, CharacterPropertyHandler())
