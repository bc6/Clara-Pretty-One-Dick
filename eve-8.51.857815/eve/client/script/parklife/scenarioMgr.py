#Embedded file name: eve/client/script/parklife\scenarioMgr.py
import service
import uthread
import trinity
import geo2
import blue
import decometaclass
import random
import sys
import uix
import dungeonHelper
import dungeonEditorTools
import log
import carbonui.const as uiconst
import telemetry
import math
SAVE_TIME = 30 * const.SEC
UNLOCK_TIME = 15 * const.SEC
UNLOCK_OBJECT_MODEL_TIMEOUT = 30.0 * const.SEC

class FakeBall(decometaclass.WrapBlueClass('destiny.ClientBall')):
    """
    FakeBall is a class to wrap client balls just so we have a __dict__ on destiny balls
    """
    pass


class ScenarioMgr(service.Service):
    __guid__ = 'svc.scenario'
    __exportedcalls__ = {'BindClientToLevelEditor': [service.ROLE_SERVICE],
     'ChoosePathStep': [service.ROLE_SERVICE]}
    __notifyevents__ = ['DoBallsAdded',
     'DoBallRemove',
     'OnReleaseBallpark',
     'OnDungeonEdit',
     'OnBSDRevisionChange',
     'DoBallsRemove']
    __dependencies__ = ['michelle']
    __startupdependencies__ = ['settings']

    def __init__(self):
        service.Service.__init__(self)
        self.selection = []
        self.selectionObjs = []
        self.ignoreAxis = None
        self.lookatID = None
        self.ed = None
        view = trinity.TriView()
        view.SetLookAtPosition((0, 2, -2), (0, 3, 0), (0, 1, 0))
        projection = trinity.TriProjection()
        projection.PerspectiveFov(1, trinity.device.viewport.GetAspectRatio(), 1, 3000)
        self.clientToolsScene = None
        self.clientToolsScene = scene = self.GetClientToolsScene()
        self.cursors = {'Translation': dungeonEditorTools.TranslationTool(view, projection, scene),
         'Rotation': dungeonEditorTools.RotationTool(view, projection, scene),
         'Scaling': dungeonEditorTools.ScalingTool(view, projection, scene)}
        self.currentCursor = None
        self.isActive = False
        self.isMoving = False
        self.isSaving = False
        self.isUnlocking = False
        self.dungeonOrigin = None
        self.playerLocation = None
        self.fakeBallTransforms = {}
        self.backupTranslations = {}
        self.backupRotations = {}
        self.unsavedChanges = {}
        self.unsavedTime = {}
        self.lockedObjects = {}
        self.lockedTime = {}
        self.lastChangeTimestamp = None
        self.lastUpdateRecievedTimestamp = None
        self.selectionCenter = (0.0, 0.0, 0.0)
        self.groupRotation = geo2.Vector(0, 0, 0, 1)
        self.addSelectedTaskletCount = 0
        self.currentHardGroup = None
        self.hardGroupRotations = {}
        self.rotatedSelectionGroups = {}
        self.editDungeonID = None
        self.editRoomID = None
        self.editRoomPos = None
        self.groupsWithNoModel = [const.groupCosmicAnomaly, const.groupCosmicSignature]

    def Run(self, memStream = None):
        service.Service.Run(self, memStream)
        self.ed = None

    def GetLevelEditor(self):
        """
        This gets a reference to the "level editor" on the server.
        """
        if self.ed is None and session.role & service.ROLE_CONTENT == service.ROLE_CONTENT:
            self.BindClientToLevelEditor()
        return self.ed

    def BindClientToLevelEditor(self):
        self.ed = sm.RemoteSvc('keeper').GetLevelEditor()
        self.ed.Bind()

    def EditRoom(self, dungeonID, roomID):
        ed = self.GetLevelEditor()
        if ed:
            ed.EditDungeon(dungeonID, roomID=roomID)
        else:
            print 'I have no ed instance'

    def PlayDungeon(self, dungeonID, roomID, godmode = 1):
        ed = self.GetLevelEditor()
        if ed:
            if roomID is not None:
                roomID = int(roomID)
            ed.PlayDungeon(dungeonID, roomID=roomID, godmode=godmode)
        else:
            print 'I have no ed instance'

    def ResetDungeon(self):
        ed = self.GetLevelEditor()
        if ed:
            for ballID in self.fakeBallTransforms.keys():
                self.RestoreObjectBall(ballID)

            ed.Reset()
            self.lastChangeTimestamp = None
            self.unsavedChanges = {}
            self.lockedObjects = {}
        else:
            print 'I have no ed instance'

    def GotoRoom(self, roomID):
        ed = self.GetLevelEditor()
        if roomID is not None and ed:
            ed.GotoRoom(int(roomID))

    def ChoosePathStep(self, defaultPathStepID, pathSteps, namesByDungeonID):
        deadEndLabel = 'Dead end'
        l = []
        for pathStep in pathSteps:
            l.append(('%s<t>%s<t>%s' % (pathStep.pathStepID, namesByDungeonID.get(pathStep.destDungeonID, deadEndLabel), ['No', 'Yes'][pathStep.pathStepID == defaultPathStepID]), pathStep.pathStepID))

        windowTitle = 'GMH EP Choice'
        listTitle = 'Select the next step in the escalating path. If you do not choose a step, or do not choose one within a reasonable amount of time, the random pick will be chosen for you.'
        choice = uix.ListWnd(l, 'generic', windowTitle, hint=listTitle, isModal=1, scrollHeaders=['ID', 'Dungeon', 'Default'], minw=180)
        if choice:
            choice = choice[1]
        return choice

    def Stop(self, stream):
        self.HideCursor()
        service.Service.Stop(self)

    def IsSelected(self, ballID):
        return ballID in self.selection

    def IsSelectedByObjID(self, objectID):
        if objectID in self.selectionObjs:
            return 1
        return 0

    def AreAllSelected(self, objectList):
        """
        Is this group of objects contained within my selection?
        """
        for slimItem in objectList:
            if slimItem.dunObjectID not in self.selectionObjs:
                return False

        return True

    def GetSelectedObjIDs(self):
        return self.selectionObjs[:]

    def WaitForObjectCreationByID(self, objectIDs):
        bp = sm.GetService('michelle').GetBallpark()
        attemptsLeft = 120
        pendingObjectIDs = set(objectIDs)
        objectItemIDs = []
        while len(pendingObjectIDs) and attemptsLeft:
            blue.pyos.synchro.SleepWallclock(500)
            arrivedObjectIDs = set()
            for itemID, slimItem in bp.slimItems.iteritems():
                if slimItem.dunObjectID in pendingObjectIDs:
                    arrivedObjectIDs.add(slimItem.dunObjectID)
                    objectItemIDs.append(slimItem.itemID)

            pendingObjectIDs -= arrivedObjectIDs
            attemptsLeft -= 1
            self.LogInfo('WaitForObjectCreationByID', attemptsLeft, len(pendingObjectIDs) * 100.0 / len(objectIDs), pendingObjectIDs)

        if attemptsLeft == 0:
            raise RuntimeError('Failed to identify the arrival of specified objects')

    def SetSelectionByID(self, objectIDs):
        self.SetActiveHardGroup(None)
        self.selection = []
        self.selectionObjs = []
        dunObjects = self.GetDunObjects()
        sleepTime = 0
        for objectID in objectIDs:
            objectWasAdded = False
            while not objectWasAdded and sleepTime < 5000:
                for slimItem in dunObjects:
                    if slimItem.dunObjectID == objectID:
                        self.AddSelected(slimItem.itemID)
                        objectWasAdded = True

                if not objectWasAdded:
                    sleepTime += 200
                    blue.synchro.SleepWallclock(200)
                    dunObjects = self.GetDunObjects()

            if not objectWasAdded:
                self.LogError('scenarioMgr could not add objectID', objectID, "to the selection--can't find it in the dungeon!")
                log.LogTraceback()

    def _SendSelectionEvent(self, objects = None):
        if objects is None:
            objects = self.selectionObjs
        objectID = objects and objects[0] or None
        sm.ScatterEvent('OnSelectObjectInGame', 'SelectDungeonObject', dungeonID=self.GetEditingDungeonID(), roomID=self.GetEditingRoomID(), objectID=objectID)

    def IncrementAddSelectedTaskletCount(self):
        """
        Increment the count of pending AddSelected tasklets.
        """
        self.addSelectedTaskletCount += 1

    def DecrementAddSelectedTaskletCount(self):
        """
        Increment the count of pending AddSelected tasklets.
        """
        self.addSelectedTaskletCount -= 1
        if self.addSelectedTaskletCount == 0:
            self.DoFullRefresh()
        elif self.addSelectedTaskletCount < 0:
            self.LogError('We have negative AddSelected tasklets--this is bad')

    def DoFullRefresh(self):
        """
        Refreshes all necessary listeners.
        """
        self.RefreshSelection()
        uthread.new(self.GetLevelEditor().ObjectSelection, self.selectionObjs)
        sm.ScatterEvent('OnDESelectionChanged')
        self._SendSelectionEvent()

    def AddSelected(self, ballID):
        """
        Add the given ball to the list of selected objects.
        """
        self.IncrementAddSelectedTaskletCount()
        uthread.new(self.AddSelected_thread, ballID).context = 'svc.scenario.AddSelected'

    def AddSelected_thread(self, ballID):
        """
        Simple wrapper method to help with reference counting.
        
        Note that the reference counting is done so we can do a
        refresh when all additions have been done.
        """
        try:
            self._AddSelected_thread(ballID)
        finally:
            self.DecrementAddSelectedTaskletCount()

    def _AddSelected_thread(self, ballID):
        if ballID in self.selection:
            return
        slimItem = sm.GetService('michelle').GetItem(ballID)
        for i in xrange(10):
            locked, byWho = dungeonHelper.IsObjectLocked(slimItem.dunObjectID)
            if locked != True or byWho != []:
                break
            blue.synchro.SleepWallclock(500)
        else:
            self.LogError('AddSelected_thread tried to add ball', ballID, 'for dungeon object', slimItem.dunObjectID, 'to selection, but it does not appear to exist.')
            return

        if locked:
            lockedBy = ', '.join((userName for userId, userName in byWho))
            eve.Message('AdminNotify', {'text': 'Unable to select object %d as its locked by %s' % (slimItem.dunObjectID, lockedBy)})
            sm.ScatterEvent('OnDESelectionChanged')
            return
        if not self.currentCursor:
            self.currentCursor = 'Translation'
        self.selection.append(ballID)
        if slimItem.dunObjectID not in self.selectionObjs:
            self.selectionObjs.append(slimItem.dunObjectID)
        self.groupRotation = geo2.Vector(0, 0, 0, 1)
        self.ReplaceObjectBall(ballID, slimItem)

    def ReplaceObjectBall(self, ballID, slimItem):
        """
        Replaces the ball of an object with a very small, fake ball that is used to
        safely move the object during editing.
        """
        if ballID in self.fakeBallTransforms:
            return
        targetBall = sm.GetService('michelle').GetBall(ballID)
        targetModel = getattr(targetBall, 'model', None)
        modelWaitEntryTime = blue.os.GetWallclockTime()
        if slimItem.groupID not in self.groupsWithNoModel:
            while not targetModel:
                blue.pyos.synchro.SleepWallclock(100)
                targetModel = getattr(targetBall, 'model', None)
                if blue.os.GetWallclockTime() > modelWaitEntryTime + const.SEC * 15.0:
                    self.LogError('ReplaceObjectBall gave up on waiting for the object model to load.')
                    return False

        bp = sm.GetService('michelle').GetBallpark()
        replacementBall = bp.AddBall(-ballID, 1.0, 0.0, 0, 0, 0, 0, 0, 0, targetBall.x, targetBall.y, targetBall.z, 0, 0, 0, 0, 1.0)
        replacementBall = FakeBall(replacementBall)
        replacementBall.__dict__['id'] = ballID
        tf = trinity.EveRootTransform()
        tf.translationCurve = replacementBall
        if targetModel and targetModel.rotationCurve and hasattr(targetModel.rotationCurve, 'value'):
            tf.rotationCurve = targetModel.rotationCurve
        elif hasattr(targetModel, 'rotation'):
            tf.rotationCurve = trinity.TriRotationCurve()
            tf.rotationCurve.value = targetModel.rotation
        self.fakeBallTransforms[ballID] = tf
        if targetModel:
            self.backupTranslations[ballID] = targetModel.translationCurve
            self.backupRotations[ballID] = targetModel.rotationCurve
            targetModel.translationCurve = tf.translationCurve
            targetModel.rotationCurve = tf.rotationCurve

    def RestoreObjectBall(self, ballID):
        targetBall = sm.GetService('michelle').GetBall(ballID)
        targetModel = getattr(targetBall, 'model', None)
        if targetModel:
            targetModel.translationCurve = self.backupTranslations[ballID]
            targetModel.rotationCurve = self.backupRotations[ballID]
        del self.fakeBallTransforms[ballID]

    def RemoveSelected(self, ballID, bpRemoval = None, silent = False):
        if ballID not in self.selection:
            return
        self.selection.remove(ballID)
        self.groupRotation = geo2.Vector(0, 0, 0, 1)
        self.RestoreObjectBall(ballID)
        if bpRemoval == None:
            slimItem = sm.GetService('michelle').GetItem(ballID)
            self.selectionObjs.remove(slimItem.dunObjectID)
        if not silent:
            self.RefreshSelection()
            sm.ScatterEvent('OnDESelectionChanged')
            self._SendSelectionEvent()

    def UnselectAll(self):
        while len(self.selection) > 1:
            self.RemoveSelected(self.selection[0], silent=True)

        if self.selection:
            self.RemoveSelected(self.selection[0])

    def StopMovingCursor(self):
        """ 
        Note that there is no StartMovingCursor analog anymore.
        """
        self.cursors[self.currentCursor].ReleaseAxis()
        self.StartSavingChanges()

    def StartSavingChanges(self):
        if not self.isSaving:
            self.isSaving = True
            uthread.new(self.SavingChanges_thread).context = 'svc.scenario::SavingChanges'

    def SavingChanges_thread(self):
        """
        This function now updates the database to reflect local changes after the user has stopped
        moving the editing cursor.  However, because database updates cause the editor to be
        unresponsive for a short time, we only begin the update process if the editing cursor
        has been inactive for a while.
        """
        try:
            while self.unsavedTime:
                sleepTill = min(self.unsavedTime.itervalues()) + SAVE_TIME
                sleepTill += const.SEC
                sleepTime = (sleepTill - blue.os.GetWallclockTime()) / const.MSEC
                if sleepTime > 0:
                    blue.synchro.SleepWallclock(sleepTime)
                while self.isMoving:
                    blue.synchro.Yield()

                if sleepTime < 0 and not self.isMoving:
                    self.unsavedTime = {}
                savingIDs = []
                threshhold = blue.os.GetWallclockTime() - SAVE_TIME
                for ballID, updateTime in self.unsavedTime.iteritems():
                    if threshhold > self.unsavedTime[ballID]:
                        savingIDs.append(ballID)

                if savingIDs or self.rotatedSelectionGroups:
                    self.SaveChanges(savingIDs)

        finally:
            self.isSaving = False

    def SaveAllChanges(self):
        self.SaveChanges(self.unsavedChanges.keys())

    def SaveChanges(self, savingIDs):
        for groupName, orientation in self.rotatedSelectionGroups.iteritems():
            sm.ScatterEvent('OnDungeonSelectionGroupRotation', self.currentHardGroup, *orientation)

        self.rotatedSelectionGroups = {}
        if savingIDs:
            michelle = sm.StartService('michelle')
            uthread.new(eve.Message, 'AdminNotify', {'text': 'LevelEd: Saving changes to database...'}).context = 'gameui.ServerMessage'
            for ballID in savingIDs[:]:
                slimItem = michelle.GetItem(ballID)
                if not slimItem:
                    savingIDs.remove(ballID)
                    continue
                if dungeonHelper.IsObjectLocked(slimItem.dunObjectID)[0]:
                    savingIDs.remove(ballID)
                    uthread.new(eve.Message, 'AdminNotify', {'text': 'Object %d is Locked' % slimItem.dunObjectID}).context = 'gameui.ServerMessage'
                    self.RestoreObjectBall(ballID)

            for ballID in savingIDs:
                self._LockBall(ballID, michelle)

            self.RefreshSelection()
            dungeonHelper.BatchStart()
            try:
                for ballID in savingIDs:
                    self._SaveBall(ballID, michelle)

            finally:
                dungeonHelper.BatchEnd()

    def _LockBall(self, ballID, michelle):
        slimItem = michelle.GetItem(ballID)
        if not slimItem:
            return
        objectID = slimItem.dunObjectID
        if objectID not in self.lockedObjects:
            self.lockedObjects[objectID] = int(bool(self.unsavedChanges[ballID] & dungeonEditorTools.CHANGE_TRANSLATION) or bool(self.unsavedChanges[ballID] & dungeonEditorTools.CHANGE_ROTATION) or bool(self.unsavedChanges[ballID] & dungeonEditorTools.CHANGE_SCALE))
            self.lockedTime[objectID] = blue.os.GetWallclockTime()
            self.UnlockObjectsOnTimeout()

    def _SaveBall(self, ballID, michelle):
        try:
            slimItem = michelle.GetItem(ballID)
            if not slimItem:
                return
            objectID = slimItem.dunObjectID
            if self.unsavedChanges[ballID] & dungeonEditorTools.CHANGE_TRANSLATION:
                dungeonHelper.SaveObjectPosition(objectID, slimItem.dunX, slimItem.dunY, slimItem.dunZ)
            if self.unsavedChanges[ballID] & dungeonEditorTools.CHANGE_SCALE:
                dungeonHelper.SaveObjectRadius(objectID, slimItem.dunRadius)
            targetBall = michelle.GetBall(slimItem.itemID)
            targetModel = getattr(targetBall, 'model', None)
            if not targetModel and not self.unsavedChanges[ballID] & dungeonEditorTools.CHANGE_TRANSLATION | dungeonEditorTools.CHANGE_SCALE:
                del self.lockedObjects[objectID]
            if targetModel and self.unsavedChanges[ballID] & dungeonEditorTools.CHANGE_ROTATION:
                quat = targetModel.rotationCurve.value
                yaw, pitch, roll = geo2.QuaternionRotationGetYawPitchRoll(quat)
                yaw = yaw / math.pi * 180.0
                pitch = pitch / math.pi * 180.0
                roll = roll / math.pi * 180.0
                dungeonHelper.SaveObjectRotation(objectID, yaw, pitch, roll)
        finally:
            del self.unsavedChanges[ballID]
            del self.unsavedTime[ballID]

    def DuplicateSelection(self, amount, x, y, z):
        slimItems = self.GetSelObjects()
        if len(slimItems) == 0:
            return
        newIDs = []
        for slimItem in slimItems:
            for n in range(1, amount + 1):
                objID = dungeonHelper.CopyObject(slimItem.dunObjectID, slimItem.dunRoomID, x * n, y * n, z * n)
                newIDs.append(objID)

        self.SetSelectionByID(newIDs)

    def SetSelectedQuantity(self, minQuantity, maxQuantity):
        slimItems = self.GetSelObjects()
        for slimItem in slimItems:
            obtype = cfg.invtypes.Get(slimItem.typeID)
            if slimItem.categoryID == const.categoryAsteroid or slimItem.groupID in (const.groupHarvestableCloud, const.groupCloud):
                quantity = minQuantity + (maxQuantity - minQuantity) * random.random()
                dungeonHelper.SetObjectQuantity(slimItem.dunObjectID, quantity)

    def SetSelectedRadius(self, minRadius, maxRadius):
        slimItems = self.GetSelObjects()
        for slimItem in slimItems:
            obtype = cfg.invtypes.Get(slimItem.typeID)
            if slimItem.categoryID == const.categoryAsteroid or slimItem.groupID in (const.groupHarvestableCloud, const.groupCloud):
                radius = minRadius + (maxRadius - minRadius) * random.random()
                dungeonHelper.SetObjectRadius(slimItem.dunObjectID, radius)

    def JitterSelection(self, x, y, z):
        slimItems = self.GetSelObjects()
        if len(slimItems) == 0:
            return
        commandArgs = []
        for slimItem in slimItems:
            ox = slimItem.dunX + x * random.random() * 2 - x
            oy = slimItem.dunY + y * random.random() * 2 - y
            oz = slimItem.dunZ + z * random.random() * 2 - z
            dungeonHelper.SetObjectPosition(slimItem.dunObjectID, ox, oy, oz)

    def JitterRotationSelection(self, yaw, pitch, roll):
        slimItems = self.GetSelObjects()
        if len(slimItems) == 0:
            return
        commandArgs = []
        for slimItem in slimItems:
            oYaw, oPitch, oRoll = dungeonHelper.GetObjectRotation(slimItem.dunObjectID)
            oYaw += yaw * random.random() * 2 - yaw
            oPitch += pitch * random.random() * 2 - pitch
            oRoll += roll * random.random() * 2 - roll
            dungeonHelper.SetObjectRotation(slimItem.dunObjectID, oYaw, oPitch, oRoll)

    def ArrangeSelection(self, x, y, z):
        slimItems = self.GetSelObjects()
        if len(slimItems) < 2:
            return
        minV = trinity.TriVector(slimItems[0].dunX, slimItems[0].dunY, slimItems[0].dunZ)
        maxV = minV.CopyTo()
        commandArgs = []
        centreAxis = trinity.TriVector()
        for slimItem in slimItems:
            centreAxis.x = centreAxis.x + slimItem.dunX
            centreAxis.y = centreAxis.y + slimItem.dunY
            centreAxis.z = centreAxis.z + slimItem.dunZ

        centreAxis.Scale(1.0 / len(slimItems))
        stepCount = float(len(slimItems))
        totalOffset = trinity.TriVector(x * stepCount, y * stepCount, z * stepCount)
        totalOffset.Scale(-0.5)
        counter = 0
        for slimItem in slimItems:
            offset = trinity.TriVector(x, y, z)
            offset.Scale(counter)
            pos = centreAxis + totalOffset + offset
            counter += 1
            dungeonHelper.SetObjectPosition(slimItem.dunObjectID, pos.x, pos.y, pos.z)

    def SetRotate(self, y, p, r):
        slimItems = self.GetSelObjects()
        if len(slimItems) == 0:
            return
        for slimItem in slimItems:
            dungeonHelper.SetObjectRotation(slimItem.dunObjectID, y, p, r)

    def RotateSelected(self, yaw, pitch, roll):
        slimItems = self.GetSelObjects()
        if len(slimItems) == 0:
            return
        yawRad = yaw / 180.0 * math.pi
        pitchRad = pitch / 180.0 * math.pi
        rollRad = roll / 180.0 * math.pi
        rotationToAdd = geo2.QuaternionRotationSetYawPitchRoll(yawRad, pitchRad, rollRad)
        posCtr = geo2.VectorD(0, 0, 0)
        for slimItem in slimItems:
            posCtr += geo2.VectorD(slimItem.dunX, slimItem.dunY, slimItem.dunZ)

        geo2.Scale(posCtr, 1.0 / len(slimItems))
        for slimItem in slimItems:
            rot = getattr(slimItem, 'dunRotation', None)
            slimItemRotation = geo2.QuaternionIdentity()
            if rot is not None:
                yaw, pitch, roll = rot
                slimItemRotation = geo2.QuaternionRotationSetYawPitchRoll(yaw / 180.0 * math.pi, pitch / 180.0 * math.pi, roll / 180.0 * math.pi)
            y, p, r = geo2.QuaternionRotationGetYawPitchRoll(slimItemRotation)
            slimItemRotation = geo2.QuaternionMultiply(rotationToAdd, slimItemRotation)
            y, p, r = geo2.QuaternionRotationGetYawPitchRoll(slimItemRotation)
            y = y / math.pi * 180.0
            p = p / math.pi * 180.0
            r = r / math.pi * 180.0
            translation = geo2.VectorD(slimItem.dunX, slimItem.dunY, slimItem.dunZ)
            translation -= posCtr
            geo2.QuaternionTransformVector(rotationToAdd, translation)
            translation += posCtr
            dungeonHelper.SetObjectPosition(slimItem.dunObjectID, translation.x, translation.y, translation.z)
            dungeonHelper.SetObjectRotation(slimItem.dunObjectID, y, p, r)

    def ClearSelection(self):
        self.selection = []
        self.SetActiveHardGroup(None)
        self.RefreshSelection()

    def RefreshSelection(self):
        self.LogInfo('ScenarioMgr: RefreshSelection')
        uthread.new(self.RefreshSelection_thread).context = 'svc.scenario.RefreshSelection'

    def RefreshSelection_thread(self):
        if getattr(self, 'refreshingSelection', None) != None:
            return
        self.refreshingSelection = 1
        if not self.isActive:
            self.ShowCursor()
        scene = sm.GetService('sceneManager').GetRegisteredScene('default')
        dungeonEditorObjects = [ obj for obj in scene.objects if obj.name == '_dungeon_editor_' ]
        for obj in dungeonEditorObjects:
            scene.objects.fremove(obj)

        bp = sm.GetService('michelle').GetBallpark()
        if bp is None:
            self.refreshingSelection = None
            return
        balls = []
        self.HideCursor()
        showAggrRadius = settings.user.ui.Get('showAggrRadius', 0)
        aggrSettingsAll = settings.user.ui.Get('aggrSettingsAll', 0)
        if showAggrRadius == 1 or aggrSettingsAll == 1:
            aggrSphere = blue.resMan.LoadObject('res:/model/global/gridSphere.red')
            aggrSphere.scaling = (1, 1, 1)
        for ballID in bp.balls:
            ball = bp.GetBall(ballID)
            if ball is None:
                continue
            slimItem = sm.GetService('michelle').GetItem(ballID)
            if slimItem and slimItem.dunObjectID in self.lockedObjects:
                if self.lockedObjects[slimItem.dunObjectID] > 0:
                    scale = 1.5
                    self.AddBoundingCube(ball, blue.resMan.LoadObject('res:/Model/UI/redGlassCube.red'), scale=scale)
                    balls.append(ball)
                else:
                    scale = 1.5
                    self.AddBoundingCube(ball, blue.resMan.LoadObject('res:/Model/UI/yellowGlassCube.red'), scale=scale)
                    balls.append(ball)

        for ballID in self.selection[:]:
            ball = bp.GetBall(ballID)
            if ball is None:
                self.selection.remove(ballID)
                continue
            scale = 1.5
            self.AddBoundingCube(ball, blue.resMan.LoadObject('res:/Model/UI/blueLineCube.red'), scale=scale)
            balls.append(ball)

        if aggrSettingsAll == 1 or showAggrRadius == 1:
            if aggrSettingsAll == 1:
                slimItems = self.GetDunObjects()
            else:
                slimItems = self.GetSelObjects()
            self.LogInfo('ScenarioMgr: showAggrRadius')
            for slimItem in slimItems:
                if hasattr(slimItem, 'dunGuardCommands'):
                    gc = slimItem.dunGuardCommands
                    if gc == None:
                        continue
                    aggressionRange = gc.aggressionRange
                    ball = bp.GetBall(slimItem.itemID)
                    aggrSphereInst = trinity.EveRootTransform()
                    aggrSphereInst.name = '_dungeon_editor_'
                    aggrSphereInst.children.append(aggrSphere.CloneTo())
                    aggrSphereInst.translationCurve = ball
                    aggrSphereInst.scaling = (aggressionRange * 2, aggressionRange * 2, aggressionRange * 2)
                    scene.objects.append(aggrSphereInst)

        if len(balls):
            self.ShowCursor()
        self.LogInfo('ScenarioMgr: RefreshSelection Done')
        self.refreshingSelection = None

    def AddBoundingCube(self, ball, model, scale = 1.0, rotation = geo2.Vector(0, 0, 0, 1)):
        scene = sm.GetService('sceneManager').GetRegisteredScene('default')
        transform = trinity.EveRootTransform()
        transform.name = '_dungeon_editor_'
        transform.children.append(model)
        if hasattr(ball, 'model') and ball.model is not None:
            transform.translationCurve = ball.model.translationCurve
        else:
            try:
                transform.translationCurve = self.fakeBallTransforms[ball.id].translationCurve
            except KeyError:
                self.LogError('AddBoundingCube failed because ball', ball.id, "didn't have a fake ball!")

        transform.rotationCurve = trinity.TriRotationCurve()
        transform.rotationCurve.value = (rotation.x,
         rotation.y,
         rotation.z,
         rotation.w)
        scaleFromBall = max(ball.radius, 150)
        scale = scale * scaleFromBall
        model.scaling = (scale, scale, scale)
        scene.objects.append(transform)

    def DoBallsAdded(self, *args, **kw):
        import stackless
        t = stackless.getcurrent()
        timer = t.PushTimer(blue.pyos.taskletTimer.GetCurrent() + '::scenarioMgr')
        try:
            return self.DoBallsAdded_(*args, **kw)
        finally:
            t.PopTimer(timer)

    def DoBallsAdded_(self, lst):
        for each in lst:
            self.DoBallAdd(*each)

    def DoBallAdd(self, ball, slimItem):
        if slimItem is None:
            bp = sm.GetService('michelle').GetBallpark()
            if bp is None:
                return
            slimItem = bp.GetInvItem(ball.id)
            if slimItem is None:
                return
        if slimItem.itemID is None or slimItem.itemID < 0:
            return
        slimItem = sm.GetService('michelle').GetItem(slimItem.itemID)
        toLookAt = None
        if slimItem.dunObjectID in self.selectionObjs:
            if getattr(self, 'lookingAt', [-1])[0] == slimItem.dunObjectID:
                toLookAt = ball.id
            self.AddSelected(ball.id)
        self.UnlockObject(slimItem.itemID, slimItem.dunObjectID, force=False)
        sm.ScatterEvent('OnDungeonObjectProperties', slimItem.dunObjectID)

    @telemetry.ZONE_METHOD
    def DoBallsRemove(self, pythonBalls, isRelease):
        for ball, slimItem, terminal in pythonBalls:
            self.DoBallRemove(ball, slimItem, terminal)

    def DoBallRemove(self, ball, slimItem, terminal):
        if ball is None:
            return
        self.LogInfo('DoBallRemove::scenarioMgr', ball.id)
        if ball.id in self.selection:
            self.RemoveSelected(slimItem.itemID, 1)

    def OnReleaseBallpark(self):
        pass

    def ShowCursor(self):
        self.LogInfo('ScenarioMgr: ShowCursor')
        if self.currentCursor:
            uthread.new(self._UpdateCursor).context = 'svc.scenario.ShowCursor'
        self.isActive = True

    def HideCursor(self):
        self.LogInfo('ScenarioMgr: HideCursor')
        if self.currentCursor:
            self.cursors[self.currentCursor].Hide()
        self.isActive = False

    def MoveCursor(self, tf, dx, dy, camera):
        if not self.isMoving:
            self.LogInfo('ScenarioMgr: MoveCursor')
            uthread.new(self.MoveCursor_thread).context = 'svc.scenario.MoveCursor'

    def MoveCursor_thread(self):
        self.isMoving = True
        lib = uicore.uilib
        while lib.leftbtn:
            if self.currentCursor:
                x, y, z = self.GetSelectionCenter()
                playerPos = self.GetPlayerClientBall()
                try:
                    rotation = self.GetSelectionRotation()
                    singleObjectRotation = self.currentCursor == 'Rotation' and len(self.selection) == 1
                    multipleObjectRotation = self.currentCursor == 'Rotation' and len(self.selection) > 1
                    if singleObjectRotation:
                        self.cursors[self.currentCursor].Rotate((rotation[0],
                         rotation[1],
                         rotation[2],
                         rotation[3]))
                    elif multipleObjectRotation:
                        self.cursors[self.currentCursor].Rotate((rotation[0],
                         rotation[1],
                         rotation[2],
                         -rotation[3]))
                    self.cursors[self.currentCursor].Translate(geo2.Vector(x - playerPos.x, y - playerPos.y, z - playerPos.z))
                    self.cursors[self.currentCursor].Transform(uicore.uilib.x, uicore.uilib.y)
                    if multipleObjectRotation:
                        rotation = self.cursors[self.currentCursor].GetRotation()
                        self.SetGroupSelectionRotation((rotation[0],
                         rotation[1],
                         rotation[2],
                         -rotation[3]))
                except:
                    self.LogError('Error when attempting to move the dungeon editor object manipulation tool.')
                    log.LogException()
                    sys.exc_clear()
                    self.isMoving = False
                    return

            self.lastChangeTimestamp = blue.os.GetWallclockTime()
            blue.synchro.Yield()

        self.isMoving = False
        self.StopMovingCursor()

    def UpdateUnsavedObjectChanges(self, ballID, changeType):
        if ballID not in self.unsavedChanges:
            self.unsavedChanges[ballID] = dungeonEditorTools.CHANGE_NONE
        self.unsavedChanges[ballID] = self.unsavedChanges[ballID] | changeType
        self.unsavedTime[ballID] = blue.os.GetWallclockTime()
        self.StartSavingChanges()
        slimItem = sm.StartService('michelle').GetItem(ballID)
        if slimItem and getattr(slimItem, 'dunObjectID', None) is not None:
            sm.ScatterEvent('OnDungeonObjectProperties', slimItem.dunObjectID)

    def DeleteSelected(self):
        selItems = self.GetSelObjects()
        self.UnselectAll()
        self.DeleteObjects(selItems)

    def DeleteObjects(self, objects):
        for slimItem in objects:
            try:
                dungeonHelper.DeleteObject(slimItem.dunObjectID)
            except:
                eve.Message('CannotDeleteObjectNPCAttached')
                sys.exc_clear()

        self.RefreshWhenDeletesAreFinished(objects)

    def RefreshWhenDeletesAreFinished(self, slimItemList):
        """
        Wait until all of the given objects have had their balls deleted, then
        trigger a refresh.
        """
        MAX_SLEEP_TIME = 10000
        ballStillHere = True
        sleepTime = 0
        while ballStillHere and sleepTime < MAX_SLEEP_TIME:
            ballStillHere = False
            for oldSlim in slimItemList:
                ball, newSlim = self.GetBallAndSlimItemFromObjectID(oldSlim.dunObjectID)
                if ball is not None:
                    ballStillHere = True
                    break

            if ballStillHere:
                sleepTime += 500
                blue.synchro.SleepWallclock(500)

        sm.ScatterEvent('OnDEObjectListChanged')

    def GetDunObjects(self):
        dunObjs = []
        bp = sm.StartService('michelle').GetBallpark()
        if not bp:
            return []
        for ballID in bp.balls:
            slimItem = sm.StartService('michelle').GetItem(ballID)
            if getattr(slimItem, 'dunObjectID', None) is not None:
                dunObjs.append(slimItem)

        return dunObjs

    def GetBallAndSlimItemFromObjectID(self, objectID):
        michelleSvc = sm.StartService('michelle')
        bp = michelleSvc.GetBallpark()
        if not bp:
            return (None, None)
        for ballID, ball in bp.balls.iteritems():
            slimItem = michelleSvc.GetItem(ballID)
            if getattr(slimItem, 'dunObjectID', None) == objectID:
                return (ball, slimItem)

        return (None, None)

    def GetLockedObjects(self):
        return self.lockedObjects

    def UnlockObject(self, ballID, dunObjectID, force = False):
        """
        This will forcibly unlock a locked object.  Objects are locked (positionally) because they are
        waiting for the server to update their position/rotation/scale.  They will unlock
        automatically when all expected updates have arrived.  Unlocking the object manually will
        allow the user to manipulate it again, but if a server update arrives for the object, it will
        be recreated and those changes will be lost.  Do this at your own risk.
        """
        if dunObjectID in self.lockedObjects and force:
            del self.lockedObjects[dunObjectID]
            del self.lockedTime[dunObjectID]
            self.RefreshSelection()
        else:
            uthread.new(self.UnlockObjectWhenInitialized, ballID, dunObjectID).context = 'svc.scenario.UnlockObject'

    def UnlockObjectWhenInitialized(self, ballID, dunObjectID):
        if dunObjectID not in self.lockedObjects:
            return
        michelleSvc = sm.StartService('michelle')
        targetBall = michelleSvc.GetBall(ballID)
        targetModel = getattr(targetBall, 'model', None)
        modelWaitEntryTime = blue.os.GetWallclockTime()
        slimItem = michelleSvc.GetItem(ballID)
        if slimItem.groupID not in self.groupsWithNoModel:
            while not targetModel:
                blue.pyos.synchro.SleepWallclock(1000)
                targetModel = getattr(targetBall, 'model', None)
                if blue.os.GetWallclockTime() > modelWaitEntryTime + UNLOCK_OBJECT_MODEL_TIMEOUT:
                    self.LogWarn('UnlockObjectWhenInitialized gave up after', UNLOCK_OBJECT_MODEL_TIMEOUT, 'sec on waiting for the object model to load.', ballID, dunObjectID)
                    return False

        self.lockedObjects[dunObjectID] -= 1
        pendingChanges = 0
        for count in self.lockedObjects.itervalues():
            if count > 0:
                pendingChanges += count

        if not pendingChanges:
            self.lockedObjects = {}
            self.lockedTime = {}
            uthread.new(eve.Message, 'AdminNotify', {'text': 'LevelEd: All changes have been confirmed.'}).context = 'gameui.ServerMessage'
        else:
            pendingObjects = len([ dunObjectID for dunObjectID in self.lockedObjects if self.lockedObjects[dunObjectID] > 0 ])
            if pendingChanges == 1:
                changeString = '%d unconfirmed change' % pendingChanges
            else:
                changeString = '%d unconfirmed changes' % pendingChanges
            if pendingObjects == 1:
                dict = {'text': 'LevelEd: %s pending in 1 object.' % changeString}
            else:
                dict = {'text': 'LevelEd: %s pending in %d objects.' % (changeString, len([ dunObjectID for dunObjectID in self.lockedObjects if self.lockedObjects[dunObjectID] > 0 ]))}
            uthread.new(eve.Message, 'AdminNotify', dict).context = 'gameui.ServerMessage'
        self.RefreshSelection()

    def UnlockObjectsOnTimeout(self):
        if not self.isUnlocking:
            self.isUnlocking = True
            uthread.new(self.UnlockObjectsOnTimeout_Thread).context = 'svc.scenario::UnlockObjectsOnTimeout'

    def UnlockObjectsOnTimeout_Thread(self):
        if self.currentCursor:
            self.cursors[self.currentCursor].ReleaseAxis()
        try:
            while self.lockedTime:
                sleepTill = min(self.lockedTime.itervalues()) + UNLOCK_TIME
                sleepTime = (sleepTill - blue.os.GetWallclockTime()) / const.MSEC
                if sleepTime > 0:
                    blue.synchro.SleepWallclock(sleepTime)
                threshhold = blue.os.GetWallclockTime() - UNLOCK_TIME
                unlockedAny = False
                for ballID, updateTime in self.lockedTime.items():
                    if threshhold > self.lockedTime[ballID]:
                        del self.lockedObjects[ballID]
                        del self.lockedTime[ballID]
                        unlockedAny = True

                if unlockedAny:
                    self.RefreshSelection()
                    uthread.new(eve.Message, 'AdminNotify', {'text': 'LevelEd: Timeout waiting for change confirmation; releasing locked objects.'}).context = 'gameui.ServerMessage'

        finally:
            self.isUnlocking = False

    def GetSelObjects(self):
        selObjs = []
        for each in self.GetDunObjects():
            if self.IsSelected(each.itemID):
                selObjs.append(each)

        return selObjs

    def GetSelectionCenter(self):
        x = 0
        y = 0
        z = 0
        count = 0
        for ballID in self.selection:
            if ballID in self.fakeBallTransforms:
                x += self.fakeBallTransforms[ballID].translationCurve.x
                y += self.fakeBallTransforms[ballID].translationCurve.y
                z += self.fakeBallTransforms[ballID].translationCurve.z
                count += 1

        if count:
            x /= count
            y /= count
            z /= count
        self.selectionCenter = (x, y, z)
        return self.selectionCenter

    def GetSelectionRotation(self):
        if self.currentCursor != 'Rotation' or not len(self.selection):
            return geo2.Vector(0, 0, 0, 1)
        if self.currentHardGroup in self.hardGroupRotations:
            return self.GetHardGroupRotation(self.currentHardGroup)
        if len(self.selection) > 1:
            return self.groupRotation
        ballID = self.selection[0]
        if ballID in self.fakeBallTransforms:
            targetBall = sm.GetService('michelle').GetBall(ballID)
            return geo2.QuaternionRotationSetYawPitchRoll(targetBall.yaw, targetBall.pitch, targetBall.roll)

    def SetGroupSelectionRotation(self, rotation):
        self.groupRotation = rotation
        if self.currentHardGroup in self.hardGroupRotations:
            self.hardGroupRotations[self.currentHardGroup] = rotation
            self.rotatedSelectionGroups[self.currentHardGroup] = rotation

    def SetCursor(self, cursorName):
        if cursorName in self.cursors:
            if self.currentCursor:
                self.cursors[self.currentCursor].Hide()
            self.currentCursor = cursorName
            self.cursors[self.currentCursor].Show()

    def _UpdateCursor(self):
        if self.currentCursor:
            self.cursors[self.currentCursor].Show()
        while self.currentCursor and self.cursors[self.currentCursor].IsShown():
            playerClientBall = self.GetPlayerClientBall()
            selectionCenter = geo2.VectorD(self.GetSelectionCenter())
            playerPosition = geo2.VectorD(playerClientBall.x, playerClientBall.y, playerClientBall.z)
            toolPosition = geo2.Vec3SubtractD(selectionCenter, playerPosition)
            self.cursors[self.currentCursor].Rotate(self.GetSelectionRotation())
            self.cursors[self.currentCursor].Translate(toolPosition)
            self.cursors[self.currentCursor].UpdatePrimitives()
            keyDown = uicore.uilib.Key
            if keyDown(uiconst.VK_MENU):
                if keyDown(uiconst.VK_W):
                    self.SetCursor('Translation')
                if keyDown(uiconst.VK_E):
                    self.SetCursor('Rotation')
                if keyDown(uiconst.VK_R):
                    self.SetCursor('Scaling')
            blue.synchro.Yield()

    def GetPlayerClientBall(self):
        bp = sm.StartService('michelle').GetBallpark()
        if not bp or not bp.ego:
            return
        return bp.balls[bp.ego]

    def GetDungeonOrigin(self):
        return self.dungeonOrigin.translation

    def SetDungeonOrigin(self):
        bp = sm.StartService('michelle').GetBallpark()
        if not bp or not bp.ego:
            return
        ego = bp.balls[bp.ego]
        self.dungeonOrigin = trinity.EveTransform()
        self.dungeonOrigin.translation = geo2.Vector(ego.x, ego.y, ego.z)
        self.dungeonOrigin.rotation = geo2.QuaternionRotationSetYawPitchRoll(ego.yaw, ego.pitch, ego.roll)

    def IsActive(self):
        return self.isActive

    def GetCursor(self):
        return self.cursors.get(self.currentCursor, None)

    def GetPickAxis(self):
        if self.currentCursor:
            return self.cursors[self.currentCursor].PickAxis(uicore.uilib.x, uicore.uilib.y)

    def AddHardGroup(self, groupName, orientation = None):
        """
        - If orientation is specified, it is expected to be a 4 tuple quaternion representing
          the orientation of the selection group.
        - If no orientation is specified, the default (0,0,0,1) will be used.
        """
        if orientation is None:
            orientation = geo2.Vector(0, 0, 0, 1)
        self.hardGroupRotations[groupName] = orientation

    def RemoveHardGroup(self, groupName):
        if groupName in self.hardGroupRotations:
            del self.hardGroupRotations[groupName]
            if groupName in self.rotatedSelectionGroups:
                del self.rotatedSelectionGroups[groupName]

    def RemoveAllHardGroups(self):
        self.hardGroupRotations = {}
        self.rotatedSelectionGroups = {}

    def RenameHardGroup(self, oldGroupName, newGroupName):
        if oldGroupName == newGroupName:
            return
        if oldGroupName in self.hardGroupRotations:
            self.hardGroupRotations[newGroupName] = self.hardGroupRotations[oldGroupName]
            del self.hardGroupRotations[oldGroupName]
            if self.currentHardGroup == oldGroupName:
                self.currentHardGroup = newGroupName

    def SetActiveHardGroup(self, groupName):
        self.currentHardGroup = groupName

    def GetActiveHardGroup(self):
        return self.currentHardGroup

    def GetHardGroupRotation(self, groupName):
        return self.hardGroupRotations.get(groupName, None)

    def OnDungeonEdit(self, dungeonID, roomID, roomPos):
        self.editDungeonID = dungeonID
        self.editRoomID = roomID
        self.editRoomPos = roomPos
        self.SetDungeonOrigin()
        self.lastChangeTimestamp = None
        self.unsavedChanges = {}
        self.lockedObjects = {}

    def GetEditingDungeonID(self):
        return self.editDungeonID

    def GetEditingRoomID(self):
        return self.editRoomID

    def GetEditingRoomPosition(self):
        return self.editRoomPos

    def OnBSDRevisionChange(self, action, schemaName, tableName, rowKeys, columnValues, reverting, _source = 'local'):
        remoteDungeonKeepr = sm.RemoteSvc('keeper')
        remoteDungeonKeepr.ClientBSDRevisionChange(action, schemaName, tableName, rowKeys, columnValues, reverting)

    def GetClientToolsScene(self):
        """
        This function attempts to get the client tools scene from the RenderJob.  If it
        doesn't exist yet, then a new primitive scene is created and added to the
        RenderJob.
        """
        if self.clientToolsScene is not None:
            return self.clientToolsScene
        rj = sm.GetService('sceneManager').fisRenderJob
        scene = rj.GetClientToolsScene()
        if scene is not None:
            self.clientToolsScene = scene
            return self.clientToolsScene
        self.clientToolsScene = trinity.Tr2PrimitiveScene()
        rj.SetClientToolsScene(self.clientToolsScene)
        return self.clientToolsScene
