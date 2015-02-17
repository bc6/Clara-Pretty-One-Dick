#Embedded file name: dogma/attributes\__init__.py


def GetAttribute(attributeID):
    return cfg.dgmattribs.Get(attributeID)


def GetDisplayName(attributeID):
    attribute = GetAttribute(attributeID)
    return attribute.displayName or attribute.attributeName


def GetIconID(attributeID):
    return GetAttribute(attributeID).iconID


def GetName(attributeID):
    return GetAttribute(attributeID).attributeName
