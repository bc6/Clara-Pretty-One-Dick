#Embedded file name: localization/propertyHandlers\npcOrganizationPropertyHandler.py
import const
import eveLocalization
from basePropertyHandler import BasePropertyHandler
import log
from .. import GetMetaData
from .. import const as locconst
from ..logger import LogWarn

class NpcOrganizationPropertyHandler(BasePropertyHandler):
    """
    The base items property handler class that defines the methods 
    to retrieve item-specific property data.
    """
    PROPERTIES = {locconst.CODE_UNIVERSAL: ('name', 'rawName', 'nameWithArticle'),
     locconst.LOCALE_SHORT_ENGLISH: ('nameWithArticle',),
     locconst.LOCALE_SHORT_RUSSIAN: ('gender',),
     locconst.LOCALE_SHORT_GERMAN: ('gender',),
     locconst.LOCALE_SHORT_FRENCH: ('nameWithArticle', 'genitiveName')}

    def _GetName(self, npcOrganizationID, languageID, *args, **kwargs):
        """
        Method to retrieve name property (singular form)
        """
        if const.minFaction <= npcOrganizationID <= const.maxFaction or const.minNPCCorporation <= npcOrganizationID <= const.maxNPCCorporation:
            try:
                return cfg.eveowners.Get(npcOrganizationID).name
            except KeyError:
                log.LogException()
                return '[no npcOrganization: %d]' % npcOrganizationID

    def _GetRawName(self, npcOrganizationID, languageID, *args, **kwargs):
        """
            Returns the localized name without respect to bilingual functionlity settings
        """
        if const.minFaction <= npcOrganizationID <= const.maxFaction or const.minNPCCorporation <= npcOrganizationID <= const.maxNPCCorporation:
            try:
                return cfg.eveowners.Get(npcOrganizationID).GetRawName(languageID)
            except KeyError:
                log.LogException()
                return '[no npcOrganization: %d]' % npcOrganizationID

    if boot.role != 'client':
        _GetName = _GetRawName

    def _GetArticleEN_US(self, npcOrganizationID, *args, **kwargs):
        """
        Retrieve article for the NPC organization name. If the "article" is not filled in for this 
        npcOrganizationID, then return empty string. However if the "article" property is not defined for
        this set of messages, then will be logging error and returning that no such property/metadata exists.
        returns:
            string       - if article was found
            ""           - if metadata article wasnt filled in or found
            error string - if property "article" is invalid
        """
        try:
            messageID = cfg.eveowners.Get(npcOrganizationID).ownerNameID
        except KeyError:
            log.LogException()
            return '[no npcOrganization: %d]' % npcOrganizationID

        try:
            return GetMetaData(messageID, 'article', languageID=locconst.LOCALE_SHORT_ENGLISH)
        except:
            LogWarn("npcOrganizationID %s does not have the requested metadata 'article' in language '%s. Returning empty string by default." % (itemID, locconst.LOCALE_SHORT_ENGLISH))
            return ''

    def _GetNameWithArticle(self, npcOrganizationID, languageID, *args, **kwargs):
        return self._GetName(npcOrganizationID, languageID, args, kwargs)

    def _GetNameWithArticleEN_US(self, npcOrganizationID, *args, **kwargs):
        """
        Returns the faction name prefixed by the definite article, if the name doesn't already start with an article.
        """
        englishName = self._GetName(npcOrganizationID, locconst.LOCALE_SHORT_ENGLISH) or 'None'
        if 'The ' in englishName:
            return englishName
        else:
            return self._PrepareLocalizationSafeString(' '.join(('the', englishName)))

    def _GetGenderDE(self, npcOrganizationID, *args, **kwargs):
        return locconst.GENDER_MALE

    def _GetGenderRU(self, npcOrganizationID, *args, **kwargs):
        return locconst.GENDER_MALE

    def _GetNameWithArticleFR(self, npcOrganizationID, *args, **kwargs):
        ret = self._GetName(npcOrganizationID, locconst.LOCALE_SHORT_FRENCH)
        messageID = cfg.eveowners.Get(npcOrganizationID).ownerNameID
        try:
            article = GetMetaData(messageID, 'article', locconst.LOCALE_SHORT_FRENCH)
        except KeyError:
            log.LogException()
            return ret

        if article:
            if article.endswith("'"):
                ret = article + ret
            else:
                ret = ' '.join((article, ret))
        return ret

    def _GetGenitiveNameFR(self, npcOrganizationID, *args, **kwargs):
        ret = self._GetName(npcOrganizationID, locconst.LOCALE_SHORT_FRENCH)
        messageID = cfg.eveowners.Get(npcOrganizationID).ownerNameID
        try:
            article = GetMetaData(messageID, 'genitiveArticle', locconst.LOCALE_SHORT_FRENCH)
        except KeyError:
            log.LogException()
            return ret

        if article:
            if article.endswith("'"):
                ret = article + ret
            else:
                ret = ' '.join((article, ret))
        return ret

    def GetShowInfoData(self, ownerID, *args, **kwargs):
        """
            Get the show info data, for npc organizations it is the
            Type of the organization and the ownerID
        """
        try:
            item = cfg.eveowners.Get(ownerID)
        except KeyError:
            log.LogException()
            return [0, 0]

        return [item.typeID, ownerID]


eveLocalization.RegisterPropertyHandler(eveLocalization.VARIABLE_TYPE.NPCORGANIZATION, NpcOrganizationPropertyHandler())
