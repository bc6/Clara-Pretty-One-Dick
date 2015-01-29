#Embedded file name: trinutils\trinparser.py
import blue
import trinity
import yamlext

def DictToTrinityParser(trinityrecipe, persistedAttributesOnly = True):
    """Return Trinity objects from a dictionary.
    
    :raise RuntimeError: Raised if ``persistedAttributesOnly`` is True
      but ``trinityrecipe`` specifies a non-persisted attribute."""
    dr = blue.DictReader()
    dr.persistedAttributesOnly = persistedAttributesOnly
    result = dr.CreateObject(trinityrecipe)
    blue.resMan.Wait()
    return result


def TrinityToDict(blueobj):
    """Return dictionary represetation of a Trinity object."""
    asStr = blue.resMan.SaveObjectToYamlString(blueobj)
    return yamlext.loads(asStr)
