#Embedded file name: carbon/client/script/animation\animationController.py
import log
INVALID_TRACK_ID = -1

class AnimationController(object):
    """
    Provides the interface to an active animation network attached to this entity.
    """
    __guid__ = 'animation.AnimationController'

    def __init__(self, animationNetwork):
        self.animationNetwork = animationNetwork
        self.entityRef = None
        self.controlParameterIDs = self.animationNetwork.GetAllControlParameters()
        self.controlParameterValues = {}
        self.requestIDs = self.animationNetwork.GetAllRequestIDs()
        self.eventTrackIDs = self.animationNetwork.GetAllEventTrackIDs()
        self.eventTrackNames = {}
        self.targetController = None
        self.behaviors = []
        self._MapEventTrackNames()
        self._MapControlParameterValues()
        self.Run()

    def Run(self):
        """
        Stub function to extend any functionality after init is called.
        """
        pass

    def Reset(self):
        """
        Stub function to extend any functionality
        """
        pass

    def Stop(self, stream):
        """
        Stub function to tear down this controller.
        """
        pass

    def _MapEventTrackNames(self):
        """
        Populate the eventTrackNames dict with the inverse of the eventTrackIDs dict.
        """
        for name, id in self.eventTrackIDs.iteritems():
            self.eventTrackNames[id] = name

    def _MapControlParameterValues(self):
        """
        Populate the controlParameterValues dict with the values of each parameter.
        """
        for name, id in self.controlParameterIDs.iteritems():
            self.controlParameterValues[id] = self.animationNetwork.GetControlParameterValueByID(id)

    def GetEventTrackID(self, trackName):
        """
        Looks up the trackID for this event track name if we haven't cached it already.
        """
        return self.eventTrackIDs.get(trackName)

    def GetEventTrackName(self, trackID):
        """
        Looks up the cached trackName for this event track.
        Requires that it was already stored in the cache.
        """
        trackName = self.eventTrackNames.get(trackID, 'Unknown')
        return trackName

    def GetEventTrackIDs(self):
        """
        Returns a dict of all the event track IDs that have been cached. 
        """
        return self.eventTrackIDs

    def SetControlParameter(self, name, args):
        """
        Set a control parameter to a desired value.  Will only propagate it down to C if it is a new value.
        """
        cpID = None
        name = 'ControlParameters|' + name
        if name not in self.controlParameterIDs:
            log.LogError('Attempting to set a value to an invalid control parameter %s!' % name)
            return
        cpID = self.controlParameterIDs[name]
        if self.controlParameterValues[cpID] != args and self.animationNetwork is not None:
            self.controlParameterValues[cpID] = args
            self.animationNetwork.SetControlParameterByID(cpID, args)

    def GetControlParameter(self, name, forceLookup = False):
        """
        Retrieve a control parameter value from the cache.  If it is not in the cache, grab it first.
        """
        name = 'ControlParameters|' + name
        cpID = self.controlParameterIDs.get(name)
        value = self.controlParameterValues.get(cpID)
        if value is not None:
            return value
        self.controlParameterValues[id] = self.animationNetwork.GetControlParameterValueByID(cpID)
        log.LogError('Attempted to get a control parameter value %s, but it does not exist!' % name)

    def GetAllControlParameterValues(self, force = False):
        """
        Returns the dict of controlParameterIDs to their values.
        'Force' will query C for the values rather than relying on the stored values in Python.
        """
        if force is True:
            self._MapControlParameterValues()
        return self.controlParameterValues

    def GetAllControlParameterValuesByName(self, force = False):
        """
        Returns the dict of controlParameter names to their values.
        'Force' will query C for the values rather than relying on the stored values in Python.
        """
        if force is True:
            self._MapControlParameterValues()
        nameDict = {}
        for name, id in self.controlParameterIDs.iteritems():
            nameDict[name.split('|')[1]] = self.controlParameterValues[id]

        return nameDict

    def BroadcastRequest(self, name):
        """
        Inform the animation network of a significant event that would require an immediate transition to occur.
        """
        if self.animationNetwork is not None:
            bcID = self.requestIDs.get(name, None)
            if bcID:
                self.animationNetwork.BroadcastRequestByID(bcID)
            else:
                log.LogError('Attempted to broadcast the %s request, but it does not exist!' % name)

    def SetTargetController(self, animationController):
        """
        Associate this animation controller with a target controller to handle actions that require multiple networks.
        """
        self.targetController = animationController

    def GetTargetController(self):
        """
        Return our target controller, if we have one.
        """
        return self.targetController

    def _UpdateHook(self):
        """
        Stub function for child classes to place additional update calls.
        """
        pass

    def _UpdateTargetHook(self):
        """
        Stub function for child classes to update parameters involving the target's data.
        """
        pass

    def _UpdateNoTargetHook(self):
        """
        Stub function for child classes to update parameters exclusively when there is no target selected.
        """
        pass

    def Update(self):
        """
        Update any specific animation parameters whenever the entity is updated.
        """
        if self.animationNetwork is not None:
            self._UpdateHook()
            if self.targetController is not None:
                self._UpdateTargetHook()
            else:
                self._UpdateNoTargetHook()
            for priority, behavior in self.behaviors:
                behavior.Update(self)

    def AddBehavior(self, behavior, priority = 100):
        """
            Add a controller plugin
            These are processed according to their given priority.
        """
        self.behaviors.append((priority, behavior))
        self.behaviors.sort()
        behavior.OnAdd(self)

    def RemoveBehavior(self, behavior):
        """
            Remove a controller behavior
        """
        toRemove = None
        for priority, myBehavior in self.behaviors:
            if myBehavior == behavior:
                toRemove = (priority, myBehavior)
                break

        if toRemove is not None:
            self.behaviors.remove(toRemove)

    def ResetBehaviors(self):
        """
            Calls Reset on all behaviors on this controller
        """
        for priority, behavior in self.behaviors:
            behavior.Reset()

    def SetEntityRef(self, ent):
        self.entityRef = ent
        self._UpdateEntityInfo()

    def _UpdateEntityInfo(self):
        """
        Stub to store a few values that are used on every update.
        """
        pass
