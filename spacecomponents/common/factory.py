#Embedded file name: spacecomponents/common\factory.py
from componentstaticdata import ComponentStaticData

def CreateComponentStaticData(resPath):
    componentStaticData = ComponentStaticData(resPath)
    return componentStaticData
