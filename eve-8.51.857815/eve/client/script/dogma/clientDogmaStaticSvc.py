#Embedded file name: eve/client/script/dogma\clientDogmaStaticSvc.py
"""
This is mostly to handle attributesByTypeAttribute. We already have the info in cfg
although it's cached in the form dgmtypeattribs[typeID] = rowset of attributes. I
simply overwrite the functionality on the client to have two dictinaries that immidate
a nested dictionary but is actually just fetching the info from cfg.dgmtypeattribs

Note because of that we can't loop over the dictionary as it will be empty.
"""
import svc
from collections import defaultdict

class AttributesByTypeLookupDict(defaultdict):

    def __init__(self, typeID, *args, **kwargs):
        defaultdict.__init__(self, *args, **kwargs)
        self.typeID = typeID

    def __missing__(self, attributeID):
        for attribute in cfg.dgmtypeattribs.get(self.typeID, []):
            if attribute.attributeID == attributeID:
                return attribute.value

        ret = None
        if attributeID == const.attributeMass:
            ret = cfg.invtypes.Get(self.typeID).mass
        elif attributeID == const.attributeCapacity:
            ret = cfg.invtypes.Get(self.typeID).capacity
        elif attributeID == const.attributeVolume:
            ret = cfg.invtypes.Get(self.typeID).volume
        if ret is None:
            raise KeyError(attributeID)
        else:
            self[attributeID] = ret
            return ret


class AttributesByTypeAttribute(defaultdict):

    def __missing__(self, typeID):
        if typeID not in cfg.dgmtypeattribs:
            raise KeyError(typeID)
        return AttributesByTypeLookupDict(typeID)


class ClientDogmaStaticSvc(svc.baseDogmaStaticSvc):
    __guid__ = 'svc.clientDogmaStaticSvc'

    def LoadTypeAttributes(self, *args, **kwargs):
        self.attributesByTypeAttribute = AttributesByTypeAttribute()

    def TypeHasAttribute(self, typeID, attributeID):
        try:
            for row in cfg.dgmtypeattribs[typeID]:
                if row.attributeID == attributeID:
                    return True

            return False
        except KeyError:
            return False
