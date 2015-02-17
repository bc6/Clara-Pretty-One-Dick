#Embedded file name: eve/client/script/ui/view\dockPanelView.py
from viewstate import View

class DockPanelView(View):
    """
    Dumb view to turn off primary and secondary views and to notify dock panels if
    a this view is taken down
    """
    __guid__ = 'viewstate.DockPanelView'
    __layerClass__ = None

    def LoadView(self, **kwargs):
        """
        Called when the view is loaded
        """
        import trinity
        sm.GetService('sceneManager').RegisterScene(trinity.EveSpaceScene(), 'dockpanelview')
        sm.GetService('sceneManager').SetRegisteredScenes('dockpanelview')

    def UnloadView(self):
        uicore.dockablePanelManager.OnViewStateClosed()
        sm.GetService('sceneManager').SetRegisteredScenes('default')
        sm.GetService('sceneManager').UnregisterScene('dockpanelview')

    def CheckShouldReopen(self, newKwargs, cachedKwargs):
        """We never want to reload anything.  Another layer of paint is just fine."""
        return True
