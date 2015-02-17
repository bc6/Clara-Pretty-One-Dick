#Embedded file name: localization/propertyHandlers\locationPropertyHandler.py
import eveLocalization
import localization
from basePropertyHandler import BasePropertyHandler
import log
from .. import const as locconst
from ..logger import LogInfo, LogWarn
import eve.common.script.sys.eveCfg as evecfg

class LocationPropertyHandler(BasePropertyHandler):
    """
    The location property handler class that defines the methods 
    to retrieve location-specific property data. 
    """
    PROPERTIES = {locconst.CODE_UNIVERSAL: ('name', 'rawName')}

    def _GetName(self, locationID, languageID, *args, **kwargs):
        """
        Retrieve name of the location
        """
        try:
            return cfg.evelocations.Get(locationID).locationName
        except KeyError:
            log.LogException()
            return '[no location: %d]' % locationID

    def _GetRawName(self, locationID, languageID, *args, **kwargs):
        """
            Returns the localized name without respect to bilingual functionlity settings. Note that this does NOT work
            for celestials or stations on the server, since info for those is only packaged with the client.
        """
        try:
            return cfg.evelocations.Get(locationID).GetRawName(languageID)
        except KeyError:
            log.LogException()
            return '[no location: %d]' % locationID

    if boot.role != 'client':
        _GetName = _GetRawName

    def Linkify(self, locationID, linkText):
        """
            Return the show info data. A location is a little harder as it refers to 
            a bunch of potential things. So we use the ID ranges to determine
            what it is, These ranges are encapsulated in the util functions. 
            The stations need special handling if they are on the server or client. 
        
            The location link is the location type and locationID  
        """
        if evecfg.IsRegion(locationID):
            locationTypeID = const.typeRegion
        elif evecfg.IsConstellation(locationID):
            locationTypeID = const.typeConstellation
        elif evecfg.IsSolarSystem(locationID):
            locationTypeID = const.typeSolarSystem
        else:
            if evecfg.IsCelestial(locationID):
                warnText = "LOCALIZATION ERROR: 'linkify' argument used for a location of type celestial."
                warnText += " This is not supported. Please use the 'linkinfo' tag with arguments instead. locID:"
                LogWarn(warnText, locationID)
                return linkText
            if evecfg.IsStation(locationID):
                try:
                    locationTypeID = cfg.stations.Get(locationID).stationTypeID
                except KeyError:
                    return '[no station: %d]' % locationID

            else:
                LogInfo("LOCALIZATION LINK: The 'linkify' argument was used for a location whose type can not be identified.", locationID)
                return linkText
        return '<a href=showinfo:%d//%d>%s</a>' % (locationTypeID, locationID, linkText)


eveLocalization.RegisterPropertyHandler(eveLocalization.VARIABLE_TYPE.LOCATION, LocationPropertyHandler())
