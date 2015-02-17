#Embedded file name: carbon/client/script/graphics\uiDesktopComponent.py
import service
import trinity
import blue
import uthread
import log
import sys
import uiprimitives
import collections
import weakref

class UIDesktopComponent(object):
    """
    A client-side CEF component for linking objects that have dynamic UIDesktop textures
    to the UI, and allowing them to be interactive using picking.
    """
    __guid__ = 'component.UIDesktopComponent'

    def __init__(self):
        self.uiDesktopName = ''
        self.uiDesktop = None
        self.renderTarget = None
        self.width = 1280
        self.height = 720
        self.liveUpdates = False
        self.updateFunction = None
        self.renderJob = None
        self.active = True
        self.autoMipMap = False
        self.entityID = None
        self.format = trinity.TRIFORMAT.TRIFMT_X8R8G8B8
        if blue.win32.IsTransgaming():
            self.format = trinity.TRIFORMAT.TRIFMT_A8R8G8B8


class UIDesktopComponentManager(service.Service):
    __guid__ = 'svc.UIDesktopComponentManager'
    __componentTypes__ = ['UIDesktopComponent']
    __notifyevents__ = []

    def __init__(self):
        service.Service.__init__(self)
        trinity.device.RegisterResource(self)
        self.uiDesktops = []
        self.updateThreadsByID = weakref.WeakValueDictionary()

    def Run(self, *etc):
        service.Service.Run(self, *etc)

    def ReportState(self, component, entity):
        report = collections.OrderedDict()
        report['uiDesktopName'] = component.uiDesktopName
        report['uiDesktop'] = str(component.uiDesktop)
        report['renderTarget'] = component.renderTarget is not None
        report['width'] = component.width
        report['height'] = component.height
        report['live'] = component.liveUpdates
        report['renderJob'] = str(component.renderJob)
        report['updateFunction'] = component.updateFunction is not None
        report['active'] = component.active
        return report

    def OnInvalidate(self, *args):
        """
        Handle D3D device invalidation, for example, locked machines.
        """
        pass

    def OnCreate(self, device):
        """
        Recreate the device resources after they have been invalidated
        """
        for desktop in self.uiDesktops:
            self.CreateUIDesktopRendertarget(desktop)
            if desktop.liveUpdates == False:
                uthread.new(self.UpdateAndRenderUIDesktop, desktop)

    def UpdateUIDesktop_t(self, component):
        """
        Call a function that has been registered for a component that does the UI layout for it.
        This isn't very UI-like, since that generally uses classes.
        """
        while component.active:
            self.UpdateUIDesktop(component)

    def UpdateUIDesktop(self, component):
        """
        Call a function that has been registered for a component that does the UI layout for it.
        This isn't very UI-like, since that generally uses classes.
        """
        if component.updateFunction is not None:
            try:
                component.updateFunction(component.width, component.height, component.uiDesktop, component.entityID)
            except Exception:
                log.LogException()
                sys.exc_clear()

    def RenderUIDesktop(self, component):
        """
        For a component that's not meant to render every frame, we don't need to
        update it either. This provides us a way to make sure we render a single frame
        to the render target after we create it.
        """
        if component.renderJob is not None:
            component.renderJob.ScheduleOnce()

    def UpdateAndRenderUIDesktop(self, component):
        """
        Intended to be called on a tasklet, since updates might need to wait for resources
        to be loaded.
        """
        self.UpdateUIDesktop(component)
        self.RenderUIDesktop(component)

    def CreateUIDesktopRendertarget(self, component):
        """
        Create a standard ARGB render target that the screen can use.
        """
        if component.renderTarget is not None:
            rt = trinity.Tr2RenderTarget(component.width, component.height, 0 if component.autoMipMap else 1, component.format)
            component.renderTarget.SetFromRenderTarget(rt)
            if hasattr(component.renderTarget, 'name'):
                component.renderTarget.name = component.uiDesktopName
            if component.uiDesktop is not None:
                component.uiDesktop.SetRenderTarget(rt)

    def CreateComponent(self, name, state):
        """
        Create a UIDesktop component and return it. This performs a little bit of namespace magic
        which looks upa UIDesktop within the 'screens' namespace. A registration mechanic would be better.
        We cannot define an absolute list in the core code, to cover both Eve and Wod.
        """
        component = UIDesktopComponent()
        if 'uiDesktopName' in state:
            component.uiDesktopName = str(state['uiDesktopName'])
            component.renderTarget = blue.resMan.GetResource('dynamic:/%s' % component.uiDesktopName)
            if component.renderTarget is None:
                log.LogError('Failed to acquire a render target texture for %s' % component.uiDesktopName)
            try:
                import screens
                component.width, component.height, component.format, component.liveUpdates, component.autoMipMap, component.updateFunction = getattr(screens, component.uiDesktopName)
            except (AttributeError, ImportError):
                log.LogException()

            if not component.liveUpdates:
                component.active = False
                component.renderJob = trinity.CreateRenderJob()
        else:
            log.LogError('No uiDesktopName set')
        self.uiDesktops.append(component)
        return component

    def PrepareComponent(self, sceneID, entityID, component):
        """
        Prepare the component, this is the first step where you can access other
        components, but happens before the SetupComponent step.
        """
        component.entityID = entityID
        try:
            self.CreateUIDesktopRendertarget(component)
        except trinity.D3DError:
            sys.exc_clear()

        if component.renderTarget is not None:
            rt = component.renderTarget.wrappedRenderTarget
        else:
            rt = None
        if component.liveUpdates:
            component.uiDesktop = uicore.uilib.CreateRootObject(component.uiDesktopName, width=component.width, height=component.height, renderTarget=rt, renderJob=component.renderJob)
        else:
            component.uiDesktop = uiprimitives.UIRoot(name=component.uiDesktopName, width=component.width, height=component.height, renderTarget=rt, renderJob=component.renderJob)

    def SetupComponent(self, entity, component):
        interiorPlaceable = entity.GetComponent('interiorPlaceable')
        desktopComponent = entity.GetComponent('UIDesktopComponent')
        if interiorPlaceable is not None and desktopComponent.uiDesktop is not None:
            desktopComponent.uiDesktop.sceneObject = interiorPlaceable.renderObject
        if not component.liveUpdates:
            updateThread = uthread.new(self.UpdateAndRenderUIDesktop, component)
            updateThread.context = 'svc.UIDesktopComponentManager.UpdateAndRenderUIDesktop'
            self.updateThreadsByID[entity.entityID] = updateThread
            return
        if component.uiDesktop is None:
            return
        desktopComponent.uiDesktop.positionComponent = entity.GetComponent('position')
        updateThread = uthread.new(self.UpdateUIDesktop_t, component)
        self.updateThreadsByID[entity.entityID] = updateThread

    def UnRegisterComponent(self, entity, component):
        if component.uiDesktop:
            component.uiDesktop.sceneObject = None
            component.uiDesktop.Close()
            component.renderTarget = None
            component.active = False
            if component.liveUpdates:
                try:
                    uicore.uilib.RemoveRootObject(component.uiDesktop)
                except KeyError:
                    log.LogWarn('UIDesktop root object for was already removed somehow:', component.uiDesktopName)

        if entity.entityID in self.updateThreadsByID:
            self.updateThreadsByID.pop(entity.entityID).kill()
        self.uiDesktops.remove(component)
