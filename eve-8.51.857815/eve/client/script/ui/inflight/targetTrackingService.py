#Embedded file name: eve/client/script/ui/inflight\targetTrackingService.py
import service
import carbonui.const as uiconst
from eve.client.script.ui.inflight.bracketsAndTargets.trackingLocator import TrackingLocator
import state
import uthread

class TargetTrackingService(service.Service):
    __guid__ = 'svc.targetTrackingService'
    __servicename__ = 'targetTrackingService'
    __displayname__ = 'Target Tracking Service'
    __notifyevents__ = ['OnSetDevice', 'OnLookAt', 'OnStateChange']
    __dependencies__ = ['camera']
    __startupdependencies__ = ['camera']

    def Run(self, *args):
        self.targetTracker = sm.GetService('camera').targetTracker
        self.trackingLocator = None
        self.isCentered = settings.char.ui.Get('track_is_centered', False)
        self.isActiveTracking = settings.char.ui.Get('track_selected_item', False)
        self.customOnScreenPoint = settings.char.ui.Get('tracking_cam_location', (uicore.desktop.width / 4, uicore.desktop.height / 4))
        self.isPaused = False
        self.selectedItemForTracking = None
        self.MakeTrackLocatorBoundaries()
        self.SetCenteredTrackingState(self.isCentered)
        self.SetActiveTrackingState(on=self.isActiveTracking, persist=False)
        self.waitSelectThread = None

    def OnStateChange(self, itemID, flag, beingSelected, *args):
        if flag == state.selected:
            if beingSelected:
                self.SetSelectedItem(itemID)
            if not beingSelected and self.selectedItemForTracking == itemID:
                self.selectedItemForTracking = None
                self.deselectThread = uthread.new(self.RunDeselectIfNonSelect)

    def RunDeselectIfNonSelect(self):
        if self.selectedItemForTracking is None:
            self.SetSelectedItem(None)
            self.deselectThread = None

    def MakeTrackLocatorBoundaries(self):
        width = uicore.desktop.width
        height = uicore.desktop.height
        self.trackerBoundaries = (0.1 * width,
         0.1 * height,
         0.9 * width,
         0.9 * height)

    def ConformTrackPointToBoundaries(self):
        p = self.customOnScreenPoint
        x, y = p
        left, top, right, bottom = self.trackerBoundaries
        x = max(left, x)
        x = min(x, right)
        y = max(top, y)
        y = min(y, bottom)
        self.customOnScreenPoint = (x, y)

    def OnSetDevice(self):
        self.MakeTrackLocatorBoundaries()
        self.ConformTrackPointToBoundaries()
        if self.isActiveTracking:
            self.SetCenteredTrackingState(self.isCentered)

    def IsTargetKeyBeingPressed(self):
        lockSC = uicore.cmd.GetShortcutByFuncName('CmdLockTargetItem')
        if lockSC and uicore.uilib.Key(lockSC[0]):
            return True
        else:
            return False

    def SetSelectedItem(self, itemID):
        self.SetSelectedItems([itemID])

    def SetSelectedItems(self, itemIds):
        if self.IsTargetKeyBeingPressed() or len(itemIds) <= 0:
            return
        self.selectedItemForTracking = itemIds[0]
        if self.isActiveTracking:
            self._TrackSelectedItem()
        elif self.isActiveTracking is None:
            self.SetActiveTrackingState(on=True, persist=False)
        self.NotifyTrackingState()

    def GetActiveTrackingState(self):
        return self.isActiveTracking

    def GetCenteredState(self):
        return self.isCentered

    def MouseTrackInterrupt(self):
        if not self.isPaused and self.isActiveTracking:
            self._PauseActiveTracking()

    def _PauseActiveTracking(self):
        self.isPaused = True
        self.SetActiveTrackingState(None, persist=False)

    def ToggleActiveTracking(self):
        self.SetActiveTrackingState(self.isActiveTracking is False, persist=True)

    def ToggleCenteredTracking(self):
        self.SetCenteredTrackingState(not self.isCentered)

    def SetCenteredTrackingState(self, center):
        self.isCentered = center
        self.DestroyLocatorIfExisting()
        if center:
            self.SetTrackingToCenter()
        else:
            self.SetTrackingToCustom()
        settings.char.ui.Set('track_is_centered', center)
        sm.ScatterEvent('OnCenterTrackingChange', self.isCentered)

    def SetTrackingToCustom(self):
        self.targetTracker.SetTrackingPoint(self.customOnScreenPoint[0], self.customOnScreenPoint[1])

    def SetTrackingToCenter(self):
        centerX, centerY = self.GetCenterPosition()
        self.targetTracker.SetTrackingPoint(centerX, centerY)

    def _TrackSelectedItem(self):
        self.isPaused = False
        self.targetTracker.TrackItem(self.selectedItemForTracking)

    def _StopTrackingItem(self):
        self.targetTracker.TrackItem(None)

    def OnLookAt(self, itemID):
        if self.isActiveTracking:
            self.targetTracker.TrackItem(None)
            self.targetTracker.TrackItem(self.selectedItemForTracking)

    def NotifyTrackingState(self):
        isReallyTracking = self.isActiveTracking
        if isReallyTracking and self.selectedItemForTracking is None:
            isReallyTracking = None
        sm.ScatterEvent('OnActiveTrackingChange', isReallyTracking)

    def EnableTrackingCamera(self):
        self.SetActiveTrackingState(on=True, persist=True)

    def DisableTrackingCamera(self):
        self.SetActiveTrackingState(on=False, persist=True)

    def SetActiveTrackingState(self, on, persist = False):
        self.isActiveTracking = on
        if on:
            self._TrackSelectedItem()
            self.ShowOnScreenPositionPicker(interactive=not self.isCentered)
        else:
            self._StopTrackingItem()
        if on is not None and persist:
            previouslyOn = settings.char.ui.Get('track_selected_item', False)
            if on and previouslyOn is False:
                sm.GetService('infoGatheringSvc').LogInfoEvent(eventTypeID=const.infoEvenTrackingCameraEnabled, itemID=session.charid, int_1=1, int_2=1 if self.isCentered else 0)
            settings.char.ui.Set('track_selected_item', on)
        self.NotifyTrackingState()

    def SetCustomTrackingPoint(self, x, y, persist = True):
        self.customOnScreenPoint = (x, y)
        if persist:
            settings.char.ui.Set('tracking_cam_location', (x, y))
        if not self.isCentered and self.isActiveTracking:
            self.targetTracker.SetTrackingPoint(x, y)

    def ShowOnScreenPositionPicker(self, interactive = True):
        if sm.GetService('viewState').GetCurrentView().name != 'inflight':
            return
        stayTime = 2.0
        sm.ScatterEvent('OnPickScreenPosition', stayTime)
        self.CreateLocatorIfNotExisting(interactive)

    def GetCenterPosition(self):
        camera = sm.GetService('camera').GetSpaceCamera()
        middle = uicore.desktop.width / 2
        return (uicore.ScaleDpi(middle * (1 - camera.centerOffset)), uicore.ScaleDpi(uicore.desktop.height / 2))

    def CreateLocatorIfNotExisting(self, interactive):
        if not self.trackingLocator or self.trackingLocator.destroyed:
            pos = None
            callback = None
            if interactive:
                callback = self.SetCustomTrackingPoint
                pos = self.customOnScreenPoint
            else:
                pos = self.GetCenterPosition()
            self.trackingLocator = TrackingLocator(align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL, parent=uicore.layer.abovemain, idx=0, desiredPosition=pos, interactive=interactive, positionCallback=callback, boundary=self.trackerBoundaries)

    def DestroyLocatorIfExisting(self):
        if self.trackingLocator and not self.trackingLocator.destroyed:
            self.trackingLocator.Close()
