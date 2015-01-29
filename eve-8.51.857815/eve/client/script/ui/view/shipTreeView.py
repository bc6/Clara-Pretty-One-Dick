#Embedded file name: eve/client/script/ui/view\shipTreeView.py
from viewstate import View
from eve.client.script.ui.shared.shipTree.shipTreeLayer import ShipTreeLayer
import trinity

class ShipTreeView(View):
    __guid__ = 'viewstate.ShipTreeView'
    __notifyevents__ = []
    __dependencies__ = []
    __suppressedOverlays__ = {'shipui', 'target'}
    __layerClass__ = ShipTreeLayer

    def GetLayerClass(self):
        return ShipTreeLayer

    def __init__(self):
        View.__init__(self)

    def LoadView(self, **kwargs):
        sm.GetService('sceneManager').RegisterScene(trinity.EveSpaceScene(), 'shipTree')
        sm.GetService('sceneManager').SetRegisteredScenes('shipTree')
        sm.GetService('shipTreeUI').OnShipTreeOpened()

    def UnloadView(self):
        sm.GetService('shipTreeUI').OnShipTreeClosed()
        sm.GetService('sceneManager').UnregisterScene('shipTree')
        sm.GetService('sceneManager').SetRegisteredScenes('default')

    def ZoomBy(self, dz):
        uicore.layer.shiptree.OnZoom(dz)
