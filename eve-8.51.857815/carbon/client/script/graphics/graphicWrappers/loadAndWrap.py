#Embedded file name: carbon/client/script/graphics/graphicWrappers\loadAndWrap.py
import trinity
import log
import weakref
loadedObjects = weakref.WeakKeyDictionary()

def LoadAndWrap(resPath, urgent = False, convertSceneType = True):
    """
    Will load up an object and wrap it if a wrapper exists
    In the case of no wrapper it will return None
    """
    resPath = str(resPath)
    if urgent:
        triObject = trinity.LoadUrgent(resPath)
    else:
        triObject = trinity.Load(resPath)
    if triObject:
        return Wrap(triObject, resPath, convertSceneType=convertSceneType)
    log.LogError('Unable to load', resPath)


def Wrap(triObject, resPath = None, convertSceneType = True):
    """
    Will wrap a trinity object
    """
    import graphicWrappers
    resPath = str(resPath)
    wrapper = getattr(graphicWrappers, triObject.__typename__, None)
    if hasattr(wrapper, 'ConvertToInterior'):
        triObject = wrapper.ConvertToInterior(triObject, resPath)
        wrapper = getattr(graphicWrappers, triObject.__typename__, None)
    if wrapper:
        obj = wrapper.Wrap(triObject, resPath)
        if getattr(prefs, 'http', False):
            loadedObjects[obj] = True
        return obj


def GetLoadedObjects():
    return loadedObjects


exports = {'graphicWrappers.LoadAndWrap': LoadAndWrap,
 'graphicWrappers.Wrap': Wrap,
 'graphicWrappers.GetLoadedObjects': GetLoadedObjects}
