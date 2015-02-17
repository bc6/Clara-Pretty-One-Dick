#Embedded file name: dogma/attributes\utils.py
"""
    Utility functions for dogma attributes.
"""
import dogma.attributes

def GetAttributeValuesByCategoryNames(dbdogma, attributeList):
    """
        Gets attributes by attributeCategory from the DB.
        :param dbdogma: dogma schema object from DB2
        :param attributeList: dict of key:attributeID and item:value
        :return attributesByCategories: dict with key:categoryName and item:dict with key:attributeID and item:value.
    """
    categories = dbdogma.AttributeCategories_Select().Index('categoryID')
    attributesByCategories = {}
    for attributeID, value in attributeList.iteritems():
        attribute = dogma.attributes.GetAttribute(attributeID)
        categoryName = categories[attribute.categoryID].categoryName
        if categoryName not in attributesByCategories:
            attributesByCategories[categoryName] = []
        attributesByCategories[categoryName].append((attributeID, attribute.attributeName, value))

    for category, attributes in attributesByCategories.iteritems():
        attributesByCategories[category] = sorted(attributes, key=lambda x: x[1])

    return attributesByCategories


def GetDisplayNamesForAttributeList(attributeList):
    """
        Gets display names for a list (or dict) of attributes.
            If no display name exists it gets the default name.
        :param attributeList: list or dict containing attributes
        :return attributeNames: list of names
    """
    attributeNames = []
    for attribute in attributeList:
        name = dogma.attributes.GetDisplayName(attribute)
        attributeNames.append(name)

    return attributeNames
