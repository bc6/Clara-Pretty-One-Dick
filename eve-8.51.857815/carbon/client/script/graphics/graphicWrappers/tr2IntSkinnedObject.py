#Embedded file name: carbon/client/script/graphics/graphicWrappers\tr2IntSkinnedObject.py
import util
from eve.client.script.graphics.graphicWrappers.eveExtSkinnedObject import WodExtSkinnedObject

class Tr2IntSkinnedObject(util.BlueClassNotifyWrap('trinity.Tr2IntSkinnedObject'), WodExtSkinnedObject):
    __guid__ = 'graphicWrappers.Tr2IntSkinnedObject'

    @staticmethod
    def Wrap(triObject, resPath):
        Tr2IntSkinnedObject(triObject)
        triObject.InitTransformMatrixMixinWrapper()
        triObject.AddNotify('transform', triObject._TransformChange)
        return triObject
