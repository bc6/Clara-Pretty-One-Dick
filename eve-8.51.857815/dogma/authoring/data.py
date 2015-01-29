#Embedded file name: dogma/authoring\data.py
from dogma import const as dgmconst

class DogmaData(object):
    """
        ESP support class object for getting information on dogma attributes and effects.
    """

    def __init__(self, DB2):
        self.DB2 = DB2

    def GetAttributeNames(self, attributes):
        names = []
        for attributeID in attributes:
            name = self.GetAttributeName(attributeID)
            names.append(name)

        return names

    def GetAttributeName(self, attributeID):
        row = self.DB2.SQL('SELECT attributeName\n                 FROM dogma.attributes\n                WHERE attributeID = %d' % attributeID)[0]
        return row.attributeName

    def GetEffectNames(self, effects):
        names = []
        for effectID in effects:
            row = self.GetEffect(effectID)
            name = row.displayName or row.effectName
            names.append(name)

        return names

    def GetEffect(self, effectID):
        return self.DB2.SQL('SELECT *\n                 FROM dogma.effects\n                WHERE effectID = %d' % effectID)[0]

    def GetAttributesByTypeID(self, typeID):
        attributeDict = {}
        attributeRows = self.DB2.SQL('SELECT attributeID, valueFloat, valueInt\n                 FROM dogma.typeAttributes\n                WHERE typeID = %d' % typeID)
        for row in attributeRows:
            if row.valueFloat is not None:
                attributeDict[row.attributeID] = row.valueFloat
            else:
                attributeDict[row.attributeID] = row.valueInt

        return attributeDict

    def GetEffectsByTypeID(self, typeID):
        effectRows = self.DB2.SQL('SELECT effectID\n                 FROM dogma.typeEffects\n                WHERE typeID = %d' % typeID)
        return effectRows

    def GetEffectIDsByTypeID(self, typeID):
        return [ e.effectID for e in self.GetEffectsByTypeID(typeID) ]

    def GetAttributeValueByTypeID(self, typeID, attributeID):
        valueFloat, valueInt = self.DB2.SQL('SELECT valueFloat, valueInt\n                 FROM dogma.typeAttributes\n                WHERE typeID = %d\n                  AND attributeID = %d' % (typeID, attributeID))[0]
        return valueFloat or valueInt

    def GetTypesByGroupID(self, groupID):
        rows = self.DB2.SQL('SELECT typeID\n                 FROM inventory.typesDx\n                WHERE groupID = %d' % groupID)
        return rows

    def GetAttributeCategoryID(self, attributeID):
        attributeCategory = self.DB2.SQL('SELECT attributeCategory\n                 FROM dogma.attributes\n                WHERE attributeID = %d' % attributeID)
        return attributeCategory

    def IsBasicAttribute(self, attributeID):
        """
            Some dogma attributes are listed as basic and need special treatment.
                These include mass, radius, raceID, volume, capacity.
                    Does not include basePrice, chanceOfDuplication or published.
        """
        return attributeID in dgmconst.basicAttributes

    def GetBasicAttributesByTypeID(self, typeID):
        row = self.DB2.SQL('SELECT\n                 groupID, mass, volume, capacity, portionSize, raceID,\n                 basePrice, chanceOfDuplicating, published\n                 FROM inventory.typesEx\n                WHERE typeID = %d' % typeID)[0]
        basicAttributes = {'groupID': row.groupID,
         'mass': row.mass,
         'volume': row.volume,
         'capacity': row.capacity,
         'portionSize': row.portionSize,
         'raceID': row.raceID,
         'basePrice': row.basePrice,
         'chanceOfDuplicating': row.chanceOfDuplicating,
         'published': row.published}
        return basicAttributes
