#Embedded file name: localization/propertyHandlers\characterListPropertyHandler.py
from .. import const as locconst
from basePropertyHandler import BasePropertyHandler
import log

class CharacterListPropertyHandler(BasePropertyHandler):
    """
    The character list property handler class that defines the methods 
    to retrieve some character-specific property data from list of characters. 
    """
    PROPERTIES = {locconst.CODE_UNIVERSAL: ('quantity', 'genders')}
    GENDER_NORMALIZATION_MAPPING = {1: locconst.GENDER_MALE,
     0: locconst.GENDER_FEMALE}

    def _GetQuantity(self, wrappedCharacters, languageID, *args, **kwargs):
        """
        Retrieve the number of characters in this list 
        """
        return len(wrappedCharacters)

    def _GetGenders(self, wrappedCharacters, languageID, *args, **kwargs):
        """
        Retrieve genders of these PCs or NPCs.
        return
            enum of the values in the following set: locconst.GENDERS_*
        """
        totalCharacters = len(wrappedCharacters)
        numberOfMales = 0
        numberOfFemales = 0
        for wrappedCharacter in wrappedCharacters:
            try:
                eveGender = cfg.eveowners.Get(wrappedCharacter).gender
            except KeyError:
                log.LogException()
                eveGender = 0

            characterGender = self.GENDER_NORMALIZATION_MAPPING[eveGender]
            if characterGender == locconst.GENDER_FEMALE:
                numberOfFemales += 1
            else:
                numberOfMales += 1
                break

        resultType = locconst.GENDERS_UNDEFINED
        if totalCharacters == 1:
            resultType = locconst.GENDERS_EXACTLY_ONE_FEMALE if numberOfFemales == 1 else locconst.GENDERS_EXACTLY_ONE_MALE
        elif totalCharacters > 1:
            resultType = locconst.GENDERS_AT_LEAST_ONE_MALE if numberOfMales >= 1 else locconst.GENDERS_ALL_FEMALE
        return resultType
