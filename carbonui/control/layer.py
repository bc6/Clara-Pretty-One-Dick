#Embedded file name: carbonui/control\layer.py
import carbonui.const as uiconst
from carbonui.primitives.container import Container

class LayerManager(object):
    __guid__ = 'uicls.LayerManager'

    def __getattr__(self, k):
        return self.GetLayer(k)

    def GetLayer(self, name):
        for layer in uicore.desktop.children:
            if hasattr(layer, 'GetLayer'):
                found = layer.GetLayer(name.lower())
                if found:
                    return found

    Get = GetLayer


class LayerCore(Container):
    __guid__ = 'uicls.LayerCore'
    isTopLevelWindow = False

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.isopen = 0
        self.isopening = 0
        self.decoClass = None
        self.form = self
        self.uiwindow = self

    def ReloadUIObject(self):
        newInstance = self.CloseView()
        if newInstance:
            newInstance.OpenView()
            return newInstance
        else:
            self.display = True
            return self

    def GetLayer(self, name):
        if name.lower() == self.name[2:].lower():
            return self
        if name.lower() == self.name.lower():
            return self
        for layer in self.children:
            if hasattr(layer, 'GetLayer'):
                found = layer.GetLayer(name)
                if found:
                    return found

    def OpenView(self):
        self.display = True
        if self.isopen or self.decoClass is None:
            return
        if self.isopening:
            return
        self.isopening = True
        if getattr(self, '__notifyevents__', None):
            sm.RegisterNotify(self)
        try:
            self.OnOpenView()
            self.isopen = True
        finally:
            self.isopening = False

    def OnOpenView(self, *args):
        """ overwriteable"""
        pass

    def OnCloseView(self, *args):
        """ overwriteable"""
        pass

    def CloseView(self, recreate = True, *args):
        if not self.isopen:
            return
        for l in self.children[:]:
            if hasattr(l, 'CloseView'):
                l.CloseView(recreate=True)
            elif recreate:
                l.Close()

        wasopen = self.isopen
        self.isopen = 0
        if wasopen:
            self.OnCloseView()
        if self.isTopLevelWindow:
            uicore.registry.CheckMoveActiveState(self)
        if getattr(self, '__notifyevents__', None):
            sm.UnregisterNotify(self)
        uicore.uilib.ReleaseCapture()
        if recreate:
            parent = None
            name = None
            if self.parent:
                parent = self.parent
                name = self.name
                idx = parent.children.index(self)
            self.Close()
            if parent is not None:
                decoClass, subLayers = uicore.layerData.get(name, (None, None))
                newInstance = parent.AddLayer(name, decoClass, subLayers, idx=idx)
                return newInstance
        else:
            self.display = False

    def AddLayer(self, name, decoClass = None, subLayers = None, idx = -1):
        if decoClass:
            layer = decoClass(parent=self, name=name, idx=idx, align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        else:
            layer = LayerCore(parent=self, name=name, idx=idx, align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        layer.decoClass = decoClass or LayerCore
        uicore.layerData[name] = (decoClass or LayerCore, subLayers)
        if name.startswith('l_'):
            name = name[2:]
        setattr(uicore.layer, name.lower(), layer)
        if subLayers is not None:
            for _layerName, _decoClass, _subLayers in subLayers:
                subLayer = layer.AddLayer(_layerName, _decoClass, _subLayers)
                if _layerName.startswith('l_'):
                    _layerName = _layerName[2:]
                setattr(layer, _layerName, subLayer)

        return layer

    def IsClosed(self):
        return not self.isopen and not self.isopening

    def ZoomBy(self, amount):
        """ overwriteable"""
        pass
