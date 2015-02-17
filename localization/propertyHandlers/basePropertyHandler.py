#Embedded file name: localization/propertyHandlers\basePropertyHandler.py
from .. import const as locconst
from ..logger import LogError
from ..uiutil import PrepareLocalizationSafeString
import re
methodNameRE = re.compile('[A-Z][^A-Z]*|[^A-Z]+')

class Singleton(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance


class BasePropertyHandler(Singleton):
    """
    The base property handler provides a mechanism to programmatically retrieve properties from an arbitrary identifier type.
    Inherited class implementations are client/server specific; depending on your requirements, you may need to create subclasses in both places.
    Use the following path as a home for these files: (project name)/(client/server)/script/localization/
    
    Based on the available properties that you specify for an identifier, the property handler will call either:
    * A generic method based on the name of the property, for properties that are language-insensitive (like the gender of a character)
    * A language-specific method based on the name of the property and languageID, for properties that are language-sensitive (like plural forms of words).
    """
    PROPERTIES = {}

    def __init__(self):
        self._SetUpProperties()

    def GetProperty(self, propertyName, identifierID, languageID, *args, **kwargs):
        """
        Calls the programmatically-generated method that corresponds to the property name and languageID supplied by the caller.
        These methods must be defined for every property in self.properties.
        parameters:
            propertyName    - Name of the object property to retrieve (ie. "name", "quantity", etc.)
            identifierID    - Unique ID to look up the identifier object (ie. charid, entityid, etc.)
            languageID      - character language code. (ie. "en-us" for English)
        """
        if propertyName is None:
            method = self._GetDefault
            isUniversal = True
        else:
            isUniversal = False
            method = self._propertyMethods.get((languageID, propertyName), None)
            if method is None:
                method = self._propertyMethods.get((locconst.CODE_UNIVERSAL, propertyName), None)
                isUniversal = True
        if method is None:
            expectedUniversalMethodName = self._GeneratePropertyMethodName(propertyName, locconst.CODE_UNIVERSAL)
            expectedLangaugeSpecificMethodName = self._GeneratePropertyMethodName(propertyName, languageID)
            message = ''.join(("No method defined on '",
             str(self.__class__),
             "' to handle property '",
             propertyName,
             "'.  Tried methods'",
             expectedUniversalMethodName,
             "' and '",
             expectedLangaugeSpecificMethodName,
             "'."))
            raise AttributeError(message)
        try:
            if isUniversal:
                return method(identifierID, languageID, *args, **kwargs)
            return method(identifierID, *args, **kwargs)
        except TypeError:
            print '---- TYPE ERROR ----'
            print method
            print propertyName, identifierID, languageID
            print args
            print kwargs

    def _PrepareLocalizationSafeString(self, textString, messageID = None):
        return PrepareLocalizationSafeString(textString, messageID=messageID)

    def _SetUpProperties(self):
        """
        Worker function to set up property methods and property method dictionaries.
        The function expects to find property methods of the format:
            A "universal" property will simply be GetPropertyName (_GetGender, etc.)
            A language-specific property like "name.withPossessive" will generate (for, say, languageID "en-us") the method name "_GetNameWithPossessiveEN_US"
        Stub methods that thrown NotImplementedError exception will be generated if the property methods werent found.
        Precondition:
            self.PROPERTIES dictionary must be defined on child object.
                For example:
                PROPERTIES = {locconst.CODE_UNIVERSAL :    ("name", "quantity"), ... }
        """
        self._propertyMethods = {}
        for languageID in self.PROPERTIES:
            propertyNames = self.PROPERTIES[languageID]
            for propertyName in propertyNames:
                methodName = self._GeneratePropertyMethodName(propertyName, languageID)
                isUniversal = True if languageID == locconst.CODE_UNIVERSAL else False
                if not hasattr(self, methodName):
                    if isUniversal:
                        LogError("Class '", self.__class__.__name__, "' must implement the function '", methodName, "' to use the property '", propertyName, "'.")
                        setattr(self, methodName, BasePropertyHandler._NotImplementedUniversalPropertyFactory(methodName))
                    else:
                        LogError("Class '", self.__class__.__name__, "' must implement the function '", methodName, "' to use the property '", propertyName, "' in language '", languageID, "'.")
                        setattr(self, methodName, BasePropertyHandler._NotImplementedPropertyFactory(methodName))
                method = getattr(self, methodName)
                self._propertyMethods[languageID, propertyName] = method

    @staticmethod
    def _NotImplementedUniversalPropertyFactory(methodName):
        return lambda identifierID, languageID, *args, **kwargs: BasePropertyHandler._NotImplementedProperty(methodName)

    @staticmethod
    def _NotImplementedPropertyFactory(methodName):
        return lambda identifierID, *args, **kwargs: BasePropertyHandler._NotImplementedProperty(methodName)

    @staticmethod
    def _NotImplementedProperty(methodName):
        raise NotImplementedError, 'The property method (%s) is missing an implementation.' % methodName

    def _GeneratePropertyMethodName(self, propertyName, languageID):
        """                
        Dynamically generate the function name we should call to retrieve the value for this property/languageID pair
        A "universal" property will simply be GetPropertyName (_GetGender, etc.)
        A language-specific property like "name.withPossessive" will generate (for, say, languageID "en-us") the method name "_GetNameWithPossessiveEN_US"
        returns:
            generated method name for the property and language pair
        """
        methodName = '_Get' + ''.join([ part.title() for part in methodNameRE.findall(propertyName) ])
        if languageID != locconst.CODE_UNIVERSAL:
            methodName = methodName + languageID.replace('-', '_').upper()
        return methodName

    def _GetDefault(self, value, languageID, *args, **kwargs):
        """
        When no property is supplied, this function will return the underlying value used for the variable.
        For example, if someone requests {item:cargoItem} with no property specified (as opposed to {item:cargoItem.name}),
        by default we will return the value assigned to cargoItem; in this case, an itemID.  This method can be overridden
        in child classes to specify different return behavior. 
        """
        return value

    def Linkify(self, value, linkText):
        """
        If defined in a subclass, returns the provided text wrapped as a clickable link, in whatever default format is appropriate
        when only the value of the variable type is known and nothing else.
        
        For example, a default Linkify implementation for a charID may only be able to display an agent's basic information, while
        using the "linkinfo" kwarg in a markup tag could support more advanced functionality, like allowing you to fly to the destination
        of an agent in space.
        
        For your own implementation, use the following pattern for the return value:
        One parameter:       "<a href=showinfo:" + str(value) + ">" + linkText + "</a>"
        Multiple parameters: "<a href=showinfo:" + "//".join([str(each) for each in data]) + ">" + linkText + "</a>"         
        """
        raise NotImplementedError, 'This variable type cannot be converted into a link until a Linkify function is defined in its property handler.'
