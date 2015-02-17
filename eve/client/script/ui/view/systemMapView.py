#Embedded file name: eve/client/script/ui/view\systemMapView.py
from viewstate import View
import uicls

class SystemMapView(View):
    __guid__ = 'viewstate.SystemMapView'
    __notifyevents__ = ['OnStateChange']
    __dependencies__ = ['map', 'station', 'bracket']
    __layerClass__ = uicls.SystemMapLayer
    __subLayers__ = (('l_systemMapBrackets', None, None),)

    def __init__(self):
        View.__init__(self)

    def LoadView(self):
        """
        Currently we are pretty much just relaying to the system map service.
        What we want to do is to dismantle it and mode data to mapSvc
        
        """
        mapSvc = sm.GetService('map')
        mapSvc.MinimizeWindows()
        mapSvc.OpenMapsPalette()
        settings.user.ui.Set('activeMap', 'systemmap')
        systemMapSvc = sm.GetService('systemmap')
        systemMapSvc.InitMap()
        sm.ScatterEvent('OnMapModeChangeDone', 'systemmap')

    def UnloadView(self):
        """Used for cleaning up after the view has served its purpose"""
        if 'systemmap' in sm.GetActiveServices():
            sm.GetService('systemmap').CleanUp()
        if sm.GetService('viewState').isOpeningView != 'starmap':
            self.map.ResetMinimizedWindows()
            self.map.CloseMapsPalette()
        sm.GetService('map').CloseMapsPalette()
        sm.GetService('sceneManager').SetRegisteredScenes('default')
        activeScene = sm.GetService('sceneManager').GetActiveScene()
        if activeScene:
            activeScene.display = 1
