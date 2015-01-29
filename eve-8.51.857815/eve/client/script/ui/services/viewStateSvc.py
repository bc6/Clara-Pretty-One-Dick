#Embedded file name: eve/client/script/ui/services\viewStateSvc.py
"""
The view manager is tasked with controlling the transitions between fullscreen views
"""
from service import Service
import uicls
import carbonui.const as uiconst
import blue
import uthread
import localization
import memorySnapshot
import log

class ViewStateError(Exception):
    """
    A generic error wrapper for view state related errors
    """
    __guid__ = 'viewstate.ViewStateError'


class View(object):
    """
    The base class for a view. It consists of a UI root container and a scene.
    The view is registered for notify event by the view manager and will receive them while active or visible
    """
    __guid__ = 'viewstate.View'
    __notifyevents__ = []
    __dependencies__ = []
    __layerClass__ = uicls.LayerCore
    __progressMessageLabel__ = None
    __subLayers__ = None
    __overlays__ = set()
    __suppressedOverlays__ = set()
    __exclusiveOverlay__ = set()

    def __init__(self):
        self.name = None
        self.layer = None
        self.scene = None
        self._dynamicViewType = None

    def GetDynamicViewType(self):
        """
            Override in views that are able to exist as primary or secondary views.
        """
        if self._dynamicViewType is None:
            raise RuntimeError('View %s was activated without being set to Primary or Secondary' % self.name)
        return self._dynamicViewType

    def SetDynamicViewType(self, viewType):
        self._dynamicViewType = viewType

    def LoadView(self, **kwargs):
        """Called when the view is loaded"""
        self.LogInfo('LoadView called on view', self.name, 'kwargs', kwargs)

    def UnloadView(self):
        """Used for cleaning up after the view has served its purpose"""
        self.LogInfo('UnloadView called on view', self.name)

    def ShowView(self, **kwargs):
        """
        Only called on a Primary views. Called after LoadView has been called.
        This allows the primary view to stay loaded while still responding to view switch from secondary back to primary view.
        """
        self.LogInfo('ShowView called on view', self.name, 'with', kwargs)

    def HideView(self):
        """
        Only called on a Primary views after LoadView has been called when a secondary view is activated.
        This allows the primary view to stay loaded while still responding to view switch from primary back to secondary view.
        """
        self.LogInfo('HideView called on view', self.name)

    def ZoomBy(self, amount):
        if self.layer:
            self.layer.ZoomBy(amount)

    def IsActive(self):
        sm.GetService('viewState').IsViewActive(self.name)

    def GetProgressText(self, **kwargs):
        """Override this if you has complicated needs with respect to progress text"""
        if self.__progressMessageLabel__:
            return localization.GetByLabel(self.__progressMessageLabel__)

    def CanEnter(self, **kwargs):
        """
        Indicate if it is safe to enter the view.
        argumenst:
        - kwargs: named input arguments to the view activation
        """
        return True

    def CanExit(self):
        """
        Indicate if it is safe to exit the view. If we are in the middle of something bad stuff can happen.
        """
        return True

    def CheckShouldReopen(self, newKwargs, cachedKwargs):
        """
        This method gets to evaluate the opening arguments and decide if we want to reopen or recreate the view.
        Only evaluated for primary views
        Override if naive dict equality does not cut it.
        
        Returns True to reopen and false to recreate.
        """
        return newKwargs == cachedKwargs

    def __repr__(self):
        return '%s(name=%s)' % (self.__class__.__name__, self.name)

    def LogInfo(self, *args, **kwargs):
        sm.GetService('viewState').LogInfo(self, *args, **kwargs)

    def LogWarn(self, *args, **kwargs):
        sm.GetService('viewState').LogWarn(self, *args, **kwargs)

    def LogError(self, *args, **kwargs):
        sm.GetService('viewState').LogError(self, *args, **kwargs)


class Transition(object):
    """
    A transition defines graphical behavior while switching between any two views.
    Graphical effects for masking the switch belong here
    """
    __guid__ = 'viewstate.Transition'

    def __init__(self, allowReopen = True, fallbackView = None):
        self.allowReopen = allowReopen
        self.fallbackView = fallbackView
        self.transitionReason = None
        self.animatedOut = set()

    def StartTransition(self, fromView, toView):
        """Called when the view is activated"""
        sm.GetService('viewState').LogInfo('Transition starting for', fromView, 'to', toView)

    def EndTransition(self, fromView, toView):
        """Used for cleaning up after the view"""
        sm.GetService('viewState').LogInfo('Transition ending for', fromView, 'to', toView)
        self.transitionReason = None

    def IsActive(self):
        """Query if a transition is currently in progress"""
        return self.active

    def SetTransitionReason(self, reason, allowOverwrite = False):
        if reason is None or self.transitionReason is not None and not allowOverwrite:
            return
        self.transitionReason = reason

    def AnimateUIIn(self, duration = 2):
        uthread.new(self._AnimateUIIn, duration)

    def _AnimateUIIn(self, duration = 2):
        """
            display the layers if they have been animated by us, and then fade them in
        """
        curveSet = None
        for layer, doSleep in ((uicore.layer.main, False), (uicore.layer.viewstate, True)):
            if layer in self.animatedOut:
                layer.display = True
                self.animatedOut.remove(layer)
            uicore.animations.FadeIn(layer, curveSet=curveSet, duration=duration, sleep=doSleep)

        self.animatedOut = set()

    def AnimateUIOut(self, duration = 0.5):
        uthread.new(self._AnimateUIOut, duration)

    def _AnimateUIOut(self, duration = 0.5):
        curveSet = None
        myCallback = lambda : self.FadeOutEndCallback(uicore.layer.main)
        uicore.animations.FadeOut(uicore.layer.main, duration=duration, curveSet=curveSet, callback=myCallback)
        myCallback = lambda : self.FadeOutEndCallback(uicore.layer.viewstate)
        uicore.animations.FadeOut(uicore.layer.viewstate, duration=duration, sleep=True, curveSet=curveSet, callback=myCallback)

    def FadeOutEndCallback(self, layer, *args):
        """
            set the display of the layers to False so they are not active while hidden
            also record that we did something to this layer, so when animating in we are not chaning display
            of something we are not responsible for hiding (someone else might have been doing it)
        """
        if layer.display:
            self.animatedOut.add(layer)
            layer.display = False


class ViewType:
    """
    Enum the different types of view templates available.
    Also defines the precedence of different types.
    """
    __guid__ = 'viewstate.ViewType'
    Primary = 0
    Secondary = 1
    Dynamic = 2


class ViewInfo(object):
    """
    Meta data about a view.  This is used internally by the viewState service for accounting
    purposes. Stores info like name, type and statistics. Also caches the opening arguments last
    used to open the view to use when re-entering primary views.
    """
    __guid__ = 'viewstate.ViewInfo'

    def __init__(self, name, view, viewType = ViewType.Primary):
        self.name = name
        self.view = view
        self.viewType = viewType
        self.viewCount = 0
        self.viewTime = 0
        self.entryArguments = None

    def GetViewType(self):
        if self.viewType == ViewType.Dynamic:
            return self.view.GetDynamicViewType()
        else:
            return self.viewType

    def __repr__(self):
        return 'ViewInfo(view=%s type=%d)' % (self.view, self.viewType)


class ViewStateSvc(Service):
    """
    Manages a set of view state and transitions between them.
    Views come in two flavors: Primary and Secondary
    Primary view:
      These are the important once. They usually represent game state and are usually dictated by the server.
      The classic way is to respond to session changes and change using ChangePrimaryView.
    Secondary view:
      These are for ingame tools.  Maps, inventory, character customization etc.  They are most often envoked
      by the players them selves via links, buttons and whatnot.
    Transisions:
      These define what view state can lead to what other view state.  Only the declared transisions are valid
      and others will result in errors.  There is allwas a transition class instance associated with the mapping.
      The instance implements any kind of effect ment to be exceuted WHILE the the state switch takes place.
    
    """
    __guid__ = 'svc.viewState'
    __servicename__ = 'view state manager'
    __displayname__ = 'View State Manager'
    __notifyevents__ = ['OnShowUI']
    __dependencies__ = ['loading']

    def Initialize(self, viewLayerParent):
        """
        Initialize the view state service and prepare for configuration
        arguments:
            viewLayerParent: this is the ui layer where all the view navigation layers will reside
                             in along with the overlay parent layer (ie. uicore.layer.viewstate)
        """
        self.viewLayerParent = viewLayerParent
        self.viewInfosByName = {}
        self.transitionsByNames = {}
        self.overlaysByName = {}
        self.overlayLayerParent = self.viewLayerParent.AddLayer('l_view_overlays', uicls.LayerCore)
        self.primaryInfo = None
        self.secondaryInfo = None
        self.activeViewInfo = None
        self.activeTransition = None
        self.isOpeningView = None
        self.lastViewOpenTime = blue.os.GetWallclockTime()
        self.logUsageHandler = None
        self.logStorage = []

    def LogUsage(self, viewName, time):
        """
        We start trying to log before we have logged in so we need to work around that
        """
        if self.logUsageHandler is None:
            if sm.GetService('machoNet').IsConnected() and session.charid is not None:
                self.logUsageHandler = sm.GetService('infoGatheringSvc').GetEventIGSHandle(const.infoEventViewStateUsage)
                for viewName, time in self.logStorage:
                    self.LogUsage(viewName, time)

                del self.logStorage
            else:
                self.logStorage.append((viewName, time))
        else:
            self.logUsageHandler(char_1=viewName, itemID=session.charid, int_1=1, float_1=float(time) / const.SEC)

    def ActivateView(self, name, **kwargs):
        """
        makes the selected view active
        
        """
        self.LogInfo('Activating view', name, 'with key words', kwargs)
        transitionFailed = False
        if self.isOpeningView is not None:
            self.LogInfo("Can't activate view", name, '. already busy opening view', self.isOpeningView)
            return
        self.isOpeningView = name
        error = None
        try:
            newInfo = self.GetViewInfo(name)
            oldInfo = self.secondaryInfo or self.primaryInfo
            if newInfo.viewType == ViewType.Dynamic:
                if self.primaryInfo is None:
                    newInfo.view.SetDynamicViewType(ViewType.Primary)
                else:
                    newInfo.view.SetDynamicViewType(ViewType.Secondary)
            transition = self.GetTransition(oldInfo, newInfo)
            if transition is None and oldInfo is not None and newInfo.name == oldInfo.name:
                self.LogInfo('No valid transition found for view', name, 'to view', name, '. Skipping since it is is already active')
            else:
                if oldInfo:
                    try:
                        if not oldInfo.view.CanExit():
                            oldInfo.view.LogInfo('Unable to exit view at present')
                            return
                    except:
                        log.LogException()

                try:
                    if not newInfo.view.CanEnter(**kwargs):
                        newInfo.view.LogInfo('Unable to enter view now. Arguments:', kwargs)
                        return
                except:
                    log.LogException()

                viewOpenTime = blue.os.GetWallclockTime()
                self.activeTransition = transition
                try:
                    self.activeTransition.StartTransition(oldInfo.view if oldInfo else None, newInfo.view)
                except:
                    log.LogException()

                progressText = newInfo.view.GetProgressText(**kwargs)
                if progressText:
                    sm.GetService('loading').ProgressWnd(progressText, '', 1, 2)
                reopen = False
                if newInfo.GetViewType() == ViewType.Secondary:
                    if self.secondaryInfo:
                        reopen = self.activeTransition.allowReopen and newInfo == self.secondaryInfo
                        if reopen:
                            try:
                                reopen = newInfo.view.CheckShouldReopen(kwargs, newInfo.entryArguments)
                            except:
                                log.LogException()
                                reopen = False

                        self._CloseView(self.secondaryInfo, unload=not reopen)
                    else:
                        self._CloseView(self.primaryInfo, unload=False)
                else:
                    if self.secondaryInfo:
                        self._CloseView(self.secondaryInfo)
                    if self.primaryInfo:
                        if self.activeTransition.allowReopen and newInfo == self.primaryInfo:
                            try:
                                self.primaryInfo.view.CheckShouldReopen(kwargs, newInfo.entryArguments)
                                reopen = True
                            except:
                                log.LogException()

                            self._CloseView(self.primaryInfo, unload=False)
                        else:
                            self._CloseView(self.primaryInfo)
                self.activeViewInfo = newInfo
                if newInfo.GetViewType() == ViewType.Primary:
                    self._OpenPrimaryView(newInfo, reopen=reopen, **kwargs)
                else:
                    self._OpenView(newInfo, reopen=reopen, **kwargs)
                self.UpdateOverlays()
                if progressText is not None:
                    sm.GetService('loading').ProgressWnd(progressText, '', 2, 2)
                try:
                    transitionFailed = self.activeTransition.EndTransition(oldInfo, newInfo)
                except:
                    log.LogException()

                timeInView = viewOpenTime - self.lastViewOpenTime
                if oldInfo:
                    oldInfo.viewTime += timeInView
                    self.LogUsage(oldInfo.name, timeInView)
                self.activeViewInfo.viewCount += 1
                self.lastViewOpenTime = viewOpenTime
                if newInfo.GetViewType() == ViewType.Primary:
                    sm.ScatterEvent('OnClientReady', newInfo.name)
                self.LogInfo('View', name, 'was activated')
                sm.ScatterEvent('OnViewStateChanged', oldInfo.name if oldInfo else None, newInfo.name)
        except UserError as e:
            self.LogInfo('UserError raised while making a transition. UserError', e)
            if newInfo.GetViewType() == ViewType.Secondary:
                error = e
            else:
                raise RuntimeError('UserError raised while transitioning from %s to %s UserError: %s' % (oldInfo, newInfo, e))
        finally:
            self.isOpeningView = None
            if transitionFailed:
                self.ActivateView(self.activeTransition.fallbackView, **kwargs)
            self.activeTransition = None
            sm.GetService('loading').HideAllLoad()

        if error:
            self.LogInfo('Trying to re-enter primary view', self.primaryInfo.name, 'using cached entry arguments', self.primaryInfo.entryArguments)
            uthread.new(self.ActivateView, self.primaryInfo.name, **self.primaryInfo.entryArguments).context = 'viewStateSvc::AttemptToRecoverFromUserError'
            raise error

    def StartDependantServices(self, viewInfo):
        """make sure all the dependent services have started before we fully activate the view"""
        for serviceName in viewInfo.view.__dependencies__:
            setattr(viewInfo.view, serviceName, sm.StartServiceAndWaitForRunningState(serviceName))
            self.LogInfo('Dependant service', serviceName, 'has started')

        self.LogInfo('All dependant services started for view', viewInfo.name)

    def _OpenPrimaryView(self, viewInfo, reopen = False, **kwargs):
        """
        takes care of primary view specific functionality that needs to happen when opening
        """
        blue.SetCrashKeyValues(u'ViewState', unicode(viewInfo.name))
        blue.statistics.SetTimelineSectionName(viewInfo.name)
        memorySnapshot.AutoMemorySnapshotIfEnabled(viewInfo.name)
        self._OpenView(viewInfo, reopen=reopen, **kwargs)

    def _OpenView(self, viewInfo, reopen = False, **kwargs):
        self.LogInfo('Re-open view' if reopen else 'Opening view', viewInfo, 'with kwargs', kwargs)
        self.StartDependantServices(viewInfo)
        showView = True
        if viewInfo.GetViewType() == ViewType.Primary:
            if self.activeViewInfo.GetViewType() == ViewType.Secondary:
                showView = False
            sm.ScatterEvent('OnPrimaryViewChanged', self.primaryInfo, viewInfo)
            self.primaryInfo = viewInfo
        else:
            self.secondaryInfo = viewInfo
        try:
            if showView:
                self.LogInfo('Opening layer', viewInfo.view.layer.name)
                viewInfo.view.layer.OpenView()
                viewInfo.view.layer.pickState = uiconst.TR2_SPS_ON
                viewInfo.view.layer.display = True
            else:
                self.LogInfo('Changing the primary layer while a secondary view', self.activeViewInfo.name, 'is active')
        except:
            log.LogException()

        try:
            if reopen:
                self.LogInfo('View', viewInfo.name, 'is being re-opened')
            else:
                self.LogInfo('View', viewInfo.name, 'is being loaded.')
                viewInfo.view.LoadView(**kwargs)
            if showView:
                self.LogInfo('Showing view', viewInfo.name)
                viewInfo.view.ShowView(**kwargs)
        except:
            log.LogException()

        sm.RegisterNotify(viewInfo.view)
        viewInfo.entryArguments = kwargs
        self.LogInfo('view', viewInfo, 'opened')

    def _CloseView(self, viewInfo, unload = True):
        sm.UnregisterNotify(viewInfo.view)
        try:
            viewInfo.view.layer.CloseView(recreate=False)
        except:
            log.LogException()

        viewInfo.view.layer.display = False
        try:
            viewInfo.view.HideView()
            if unload:
                viewInfo.view.UnloadView()
                self.LogInfo('Unloading view', viewInfo.name)
        except:
            log.LogException()

        if viewInfo.GetViewType() == ViewType.Primary:
            if unload:
                viewInfo.entryArguments = None
        else:
            self.secondaryInfo = None
        sm.ScatterEvent('OnViewClosed', viewInfo.name)

    def ChangePrimaryView(self, name, **kwargs):
        """
        change the primary view with out forcing the secondary view to change.
        NOTE: if this would make the current secondary invalid we should close it
        """
        self.LogInfo('ChangePrimaryView', name)
        while self.isOpeningView:
            blue.pyos.synchro.Yield()

        if self.secondaryInfo:
            if (self.secondaryInfo.name, name) not in self.transitionsByNames:
                raise ViewStateError('Changing primary view to %s from current active secondary view %s will leave the viewStateSvc in an undefined state' % (name, self.secondaryInfo.name))
            viewInfo = self.GetViewInfo(name)
            self._CloseView(self.primaryInfo)
            self._OpenView(viewInfo, **kwargs)
            self.UpdateOverlays()
        else:
            self.ActivateView(name, **kwargs)

    def GetTransition(self, oldInfo, newInfo):
        oldViewName = oldInfo.name if oldInfo else None
        transition = self.transitionsByNames.get((oldViewName, newInfo.name))
        if transition is None:
            transition = self.transitionsByNames.get((None, newInfo.name))
        if transition is None:
            raise ViewStateError('There is not a valid transition from %s to %s' % (oldViewName, newInfo.name))
        self.LogInfo('Found transition from', oldViewName, 'to', newInfo.name)
        return transition

    def GetTransitionByName(self, fromName, toName):
        if (fromName, toName) in self.transitionsByNames:
            return self.transitionsByNames[fromName, toName]

    def GetView(self, name):
        """return a named view"""
        return self.GetViewInfo(name).view

    def HasView(self, name):
        return name in self.viewInfosByName

    def GetViewInfo(self, name):
        """return a named view info"""
        try:
            return self.viewInfosByName[name]
        except KeyError:
            raise ViewStateError('There is no view registered by the name %s' % name)

    def GetCurrentViewInfo(self):
        """get the current view"""
        return self.activeViewInfo

    def GetCurrentView(self):
        """get the current view. None if no view is active."""
        return getattr(self.activeViewInfo, 'view', None)

    def IsViewActive(self, *names):
        return getattr(self.activeViewInfo, 'name', None) in names

    def GetActiveViewName(self):
        return getattr(self.activeViewInfo, 'name', None)

    def HasActiveTransition(self):
        """
        Queries whether there is a transition currently occuring
        
        NOTE: This should be temporary and used very sparingly as this is not a paradigm we want to follow.
        Refactoring is needed on the VSM and the use of transitions to avoid it though.
        """
        if self.activeTransition is not None:
            return True
        else:
            return False

    def AddView(self, name, view, viewType = ViewType.Primary):
        """
        add a new view
        """
        self.LogInfo('Adding view', name, view, viewType)
        view.name = name
        info = ViewInfo(name, view, viewType)
        view.layer = self.viewLayerParent.AddLayer('l_%s' % name, view.__layerClass__, view.__subLayers__)
        view.layer.state = uiconst.UI_HIDDEN
        self.viewInfosByName[name] = info

    def AddTransition(self, fromName, toName, transition = Transition()):
        """
        define a transition from one view to another.
        This will allow special effects to take place implemented by the view
        """
        self.LogInfo('Adding transition', fromName or '[All]', toName, transition)
        self.transitionsByNames[fromName, toName] = transition

    def AddTransitions(self, fromNames, toNames, transition = Transition()):
        """
        define many to many transitions that share a single transition implementation
        arguments:
          fromNames is a list of view names that appear in the from clause of a transition
          toNames is a list of new namse that appear in the to clause of a transition
          transition that is initiated for all the transitions generated
        """
        for fromName in fromNames:
            for toName in toNames:
                self.AddTransition(fromName, toName, transition)

    def GetPrimaryView(self):
        try:
            return self.primaryInfo.view
        except AttributeError:
            raise ViewStateError('There is no primary view set')

    def CloseSecondaryView(self, name = None):
        """
        Close a secondry view.  It is safe to call even if it is not active.
        If called with no arguments or None we will close whatever seconday view is open.
        You can call this if you just want to make sure no secondary view is open.
        """
        while self.isOpeningView:
            blue.pyos.synchro.Yield()

        if self.secondaryInfo is None:
            self.LogInfo("Can't close secondary view since none is active")
        elif name is None or self.activeViewInfo.name == name:
            self.LogInfo('closing secondary view', self.secondaryInfo.name)
            self.ActivateView(self.primaryInfo.name, **self.primaryInfo.entryArguments)
        else:
            self.LogInfo('The secondary view', name, 'was not closed as is not active')

    def ToggleSecondaryView(self, name):
        """Toggle the state of a secondary view"""
        self.LogInfo('Toggling view', name)
        while self.isOpeningView:
            blue.pyos.synchro.Yield()

        info = self.GetViewInfo(name)
        if info.GetViewType() != ViewType.Secondary:
            raise RuntimeError('You can only toggle secondary views (tools)')
        if self.IsViewActive(name):
            self.CloseSecondaryView(name)
        else:
            self.ActivateView(name)

    def IsCurrentViewPrimary(self):
        return self.activeViewInfo.GetViewType() == ViewType.Primary

    def IsCurrentViewSecondary(self):
        activeViewInfo = getattr(self, 'activeViewInfo', None)
        if activeViewInfo:
            return activeViewInfo.GetViewType() == ViewType.Secondary
        else:
            return False

    def AddOverlay(self, name, overlayClass, subLayers = None):
        if name not in self.overlaysByName:
            overlay = self.overlayLayerParent.AddLayer('l_%s' % name, overlayClass, subLayers)
            overlay.display = False
            self.overlaysByName[name] = overlay

    def UpdateOverlays(self):
        """
        compiles a list of all overlays to activate and then
        trims the list by removing all suppressed ovelays
        then walks all overlays and displays according to the compiled list
        """
        activeOverlays = self.primaryInfo.view.__overlays__.copy()
        if self.secondaryInfo:
            activeOverlays.update(self.secondaryInfo.view.__overlays__)
        activeOverlays.difference_update(self.primaryInfo.view.__suppressedOverlays__)
        if self.secondaryInfo:
            activeOverlays.difference_update(self.secondaryInfo.view.__suppressedOverlays__)
        self.LogInfo('Overlays to enable', activeOverlays)
        for name, overlay in self.overlaysByName.items():
            try:
                if name in activeOverlays or name in self.activeViewInfo.view.__exclusiveOverlay__:
                    overlay.OpenView()
                    overlay.display = True
                    sm.ScatterEvent('OnOverlayActivated', name)
                    self.LogInfo('Overlay', name, 'activated')
                else:
                    overlay.display = False
                    overlay.CloseView(recreate=False)
                    self.overlaysByName[name] = uicore.layer.Get(name)
                    sm.ScatterEvent('OnOverlayClosed', name)
                    self.LogInfo('Overlay', name, 'closed')
            except:
                log.LogException()

        if uicore.cmd.IsUIHidden():
            uicore.cmd.HideUI()

    def SetTransitionReason(self, fromName, toName, reason):
        self.LogInfo('Adding transition reason ', fromName or '[All]', toName, reason)
        self.transitionsByNames[fromName, toName].SetTransitionReason(reason)

    def GetActiveTransitionReason(self):
        if self.activeTransition is None:
            return
        return self.activeTransition.transitionReason

    def OnShowUI(self):
        self.UpdateOverlays()
