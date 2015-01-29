#Embedded file name: eve/client/script/ui/services\skillQueueSvc.py
"""
This file contains the client-side skill queue service which provides
the UI with methods to manipulate the cached client-side skill queue
and mediates communication with the server.
Note that the queue is zero-based with the zero position being the
current skill in training.
"""
from carbonui.util.various_unsorted import GetAttrs
import service
import blue
import form
import characterskills.util
import sys
import uix
import carbonui.const as uiconst
import uiutil
import localization
import uicls

class SkillQueueService(service.Service):
    __exportedcalls__ = {}
    __guid__ = 'svc.skillqueue'
    __servicename__ = 'skillqueue'
    __displayname__ = 'Skill Queue Client Service'
    __dependencies__ = ['godma', 'skills', 'machoNet']
    __notifyevents__ = ['OnGodmaSkillTrained',
     'OnGodmaSkillStartTraining',
     'OnGodmaSkillTrainingStopped',
     'OnSkillQueueForciblyUpdated',
     'OnMultipleCharactersTrainingUpdated']

    def __init__(self):
        service.Service.__init__(self)
        self.skillQueue = []
        self.serverSkillQueue = []
        self.skillQueueCache = None
        self.cachedSkillQueue = None
        self.maxSkillqueueTimeLength = characterskills.util.GetSkillQueueTimeLength(session.userType)

    def Run(self, memStream = None):
        self.skillQueue, freeSkillPoints = self.godma.GetSkillHandler().GetSkillQueueAndFreePoints()
        self.skillQueueCache = None
        if freeSkillPoints is not None and freeSkillPoints > 0:
            sm.GetService('skills').SetFreeSkillPoints(freeSkillPoints)

    def BeginTransaction(self):
        """
            This method tells the skill queue that the UI is beginning a transaction.
            This forces the service to cache off the 'old' state of the queue so that
            the UI can manipulate the queue freely without interfering with the server.
            
            Note that this should be concluded with either a RollbackTransaction()
            or CommitTransaction()! If it's not, your changes will be overwritten
            and an 'OnSkillQueueRefreshed' event will be dispatched to notify open UIs
            that their view of the skill queue has been yanked out from under them.
            
            ARGUMENTS:
                None.
                
            RETURNS:
                None.
        """
        sendEvent = False
        if self.cachedSkillQueue is not None:
            sendEvent = True
            self.LogWarn('New skill queue transaction being opened - skill queue being overwritten!')
        self.skillQueueCache = None
        self.skillQueue, freeSkillPoints = self.godma.GetSkillHandler().GetSkillQueueAndFreePoints()
        if freeSkillPoints > 0:
            self.skills.SetFreeSkillPoints(freeSkillPoints)
        self.cachedSkillQueue = self.GetQueue()
        if sendEvent:
            sm.ScatterEvent('OnSkillQueueRefreshed')

    def RollbackTransaction(self):
        """
            This method tells the skill queue system that the UI is discarding its changes.
            The skill queue is then restored to using the cached copy of the queue itself.
            
            ARGUMENTS:
                None.
                
            RETURNS:
                None.
        """
        if self.cachedSkillQueue is None:
            self.LogError('Cannot rollback a skill queue transaction - no transaction was opened!')
            return
        self.skillQueue = self.cachedSkillQueue
        self.skillQueueCache = None
        self.cachedSkillQueue = None

    def CommitTransaction(self):
        """
            This method checks for differences between the cached queue and the real queue.
            If changes are detected, the queue is sent to the server to be saved.
            
            If changes are saved, then this method scatters the OnSkillQueueRefreshed
            method so that UIs can refresh themselves as needed.
            
            ARGUMENTS:
                None.
                
            RETURNS:
                None.
        """
        if self.cachedSkillQueue is None:
            self.LogError('Cannot commit a skill queue transaction - no transaction was opened!')
            return
        self.PrimeCache(True)
        cachedQueueCache = {}
        i = 0
        for queueSkillID, queueSkillLevel in self.cachedSkillQueue:
            if queueSkillID not in cachedQueueCache:
                cachedQueueCache[queueSkillID] = {}
            cachedQueueCache[queueSkillID][queueSkillLevel] = i
            i += 1

        hasChanges = False
        for skillTypeID, skillLevel in self.cachedSkillQueue:
            if skillTypeID not in self.skillQueueCache:
                hasChanges = True
                break
            elif skillLevel not in self.skillQueueCache[skillTypeID]:
                hasChanges = True
                break

        if not hasChanges:
            for skillTypeID, skillLevel in self.skillQueue:
                position = self.skillQueueCache[skillTypeID][skillLevel]
                if skillTypeID not in cachedQueueCache:
                    hasChanges = True
                elif skillLevel not in cachedQueueCache[skillTypeID]:
                    hasChanges = True
                elif position != cachedQueueCache[skillTypeID][skillLevel]:
                    hasChanges = True
                if hasChanges:
                    break

        scatterEvent = False
        try:
            if hasChanges:
                self.TrimQueue()
                skillHandler = sm.StartService('godma').GetSkillHandler()
                skillHandler.SaveSkillQueue(self.skillQueue)
                scatterEvent = True
            elif self.skillQueue is not None and len(self.skillQueue) and sm.StartService('skills').SkillInTraining() is None:
                skillHandler = sm.StartService('godma').GetSkillHandler()
                skillHandler.CharStartTrainingSkillByTypeID(self.skillQueue[0][0])
                scatterEvent = True
        except UserError as e:
            if e.msg == 'UserAlreadyHasSkillInTraining':
                scatterEvent = True
            raise
        finally:
            self.cachedSkillQueue = None
            if scatterEvent:
                sm.ScatterEvent('OnSkillQueueRefreshed')

    def CheckCanInsertSkillAtPosition(self, skillTypeID, skillLevel, position, check = 0, performLengthTest = True):
        """
            This method is used to check if a skill can be placed at a given position.
            This validates that multiple levels of the same skill are entered in-order
            
            ARGUMENTS:
                skillTypeID:    The type ID of the skill to add
                skillLevel:     The level of the skill to add
                position:       Where to add the skill in a zero-based array.
                                Must be valid (0 <= position <= queue length)
                check:          (optional) If this flag is set, this method will
                                return True/False indicating whether the skill can
                                be inserted, instead of throwing UserErrors.
                                All other exceptions, and exceptions from submethod calls,
                                will be thrown normally.
                performLengthTest: (optiona) If it is set, a queue length test will be performed.
                                    It's not needed when checking if the drop indicator should be displayed
                                
            RETURNS:
                True/False if Check is set. Otherwise, returns True and throws exceptions.
                
                Throws exceptions in case of errors in submethods or system errors.
        """
        if position is None or position < 0 or position > len(self.skillQueue):
            raise UserError('QueueInvalidPosition')
        self.PrimeCache()
        mySkills = self.GetGodmaSkillsSet()
        ret = True
        try:
            skillObj = mySkills.get(skillTypeID, None)
            if skillObj is None:
                raise UserError('QueueSkillNotUploaded')
            if skillObj.skillLevel >= skillLevel:
                raise UserError('QueueCannotTrainPreviouslyTrainedSkills')
            if skillObj.skillLevel >= 5:
                raise UserError('QueueCannotTrainPastMaximumLevel', {'typeName': (const.UE_TYPEID, skillTypeID)})
            if skillTypeID in self.skillQueueCache:
                for lvl, lvlPosition in self.skillQueueCache[skillTypeID].iteritems():
                    if lvl < skillLevel and lvlPosition >= position:
                        raise UserError('QueueCannotPlaceSkillLevelsOutOfOrder')
                    elif lvl > skillLevel and lvlPosition < position:
                        raise UserError('QueueCannotPlaceSkillLevelsOutOfOrder')

            if position > 0 and performLengthTest:
                if self.GetTrainingLengthOfQueue(position) > self.maxSkillqueueTimeLength:
                    raise UserError('QueueTooLong')
        except UserError as ue:
            if check and ue.msg in ('QueueTooLong', 'QueueCannotPlaceSkillLevelsOutOfOrder', 'QueueCannotTrainPreviouslyTrainedSkills', 'QueueSkillNotUploaded'):
                sys.exc_clear()
                ret = False
            else:
                raise

        return ret

    def AddSkillToQueue(self, skillTypeID, skillLevel, position = None):
        """
            This method is used to add a skill to the queue.
            ARGUMENTS:
                skillTypeID:    The type ID of the skill to add
                skillLevel:     The level of the skill to add
                position:       (optional) Where to add the skill in a zero-based array
                                If this argument is invalid (negative or None),
                                then the skill will be appended to the end of the queue.
                                
            RETURNS:
                An integer indicating the position of the added skill/level in the queue.
                Throws exceptions in case of errors.
        """
        if self.FindInQueue(skillTypeID, skillLevel) is not None:
            raise UserError('QueueSkillAlreadyPresent')
        skillQueueLength = len(self.skillQueue)
        if skillQueueLength >= characterskills.util.SKILLQUEUE_MAX_NUM_SKILLS:
            raise UserError('QueueTooManySkills', {'num': characterskills.util.SKILLQUEUE_MAX_NUM_SKILLS})
        newPos = position if position is not None and position >= 0 else skillQueueLength
        self.CheckCanInsertSkillAtPosition(skillTypeID, skillLevel, newPos)
        if newPos == skillQueueLength:
            self.skillQueue.append((skillTypeID, skillLevel))
            self.AddToCache(skillTypeID, skillLevel, newPos)
        else:
            if newPos > skillQueueLength:
                raise UserError('QueueInvalidPosition')
            self.skillQueueCache = None
            self.skillQueue.insert(newPos, (skillTypeID, skillLevel))
            self.TrimQueue()
        return newPos

    def RemoveSkillFromQueue(self, skillTypeID, skillLevel):
        """
            This method is used to remove a skill to the queue.
            ARGUMENTS:
                skillTypeID:    The type ID of the skill to add
                skillLevel:     The level of the skill to add
                                
            RETURNS:
                Nothing. Throws exceptions in case of errors.
        """
        self.PrimeCache()
        if skillTypeID in self.skillQueueCache:
            for cacheLevel in self.skillQueueCache[skillTypeID]:
                if cacheLevel > skillLevel:
                    raise UserError('QueueCannotRemoveSkillsWithHigherLevelsStillInQueue')

        self.InternalRemoveFromQueue(skillTypeID, skillLevel)

    def FindInQueue(self, skillTypeID, skillLevel):
        """
            This method is used to get the queue position of a skill
            ARGUMENTS:
                skillTypeID:    The type ID of the skill to find
                skillLevel:     The level of the skill to find
                                
            RETURNS:
                An integer indicating the position of the skill/level in the queue
                NoneType if the skill is not in the queue.
                Throws exceptions in case of other errors.
        """
        self.PrimeCache()
        if skillTypeID not in self.skillQueueCache:
            return None
        if skillLevel not in self.skillQueueCache[skillTypeID]:
            return None
        return self.skillQueueCache[skillTypeID][skillLevel]

    def MoveSkillToPosition(self, skillTypeID, skillLevel, position):
        """
            This method is used to update the queue position of a skill
            ARGUMENTS:
                skillTypeID:    The type ID of the skill to move
                skillLevel:     The level of the skill to move
                position:       The position to move this skill to
                                
            RETURNS:
                An integer indicating the position of the skill/level in the queue
                Throws exceptions in case of errors.
        """
        self.CheckCanInsertSkillAtPosition(skillTypeID, skillLevel, position)
        self.PrimeCache()
        currentPosition = self.skillQueueCache[skillTypeID][skillLevel]
        if currentPosition < position:
            position -= 1
        self.InternalRemoveFromQueue(skillTypeID, skillLevel)
        return self.AddSkillToQueue(skillTypeID, skillLevel, position)

    def GetQueue(self):
        """
            Retrieves a copy of the queue as a list of tuples, containing the skill
            type ID and level of each entry in the queue.
            ARGUMENTS:
                None.
                
            RETURNS:
                The queue, as a list of tuples, in order.
                [ (skill Type ID, level), ... ]
        """
        return self.skillQueue[:]

    def GetServerQueue(self):
        """
            Retrieves a copy of the queue as it is on the server as a list of tuples, 
            containing the skill type ID and level of each entry in the queue.
            If transaction has not been started (the skill queue window is closed)
            self.cachedSkillQueue is None and self.skillQueue is the same as the
            queue on the server.
            ARGUMENTS:
                None.
                
            RETURNS:
                The queue, as a list of tuples, in order.
                [ (skill Type ID, level), ... ]
        """
        if self.cachedSkillQueue is not None:
            return self.cachedSkillQueue[:]
        else:
            return self.GetQueue()

    def GetNumberOfSkillsInQueue(self):
        """
            Retrieves the length of the queue, in number of skills.
            ARGUMENTS:
                None.
                
            RETURNS:
                An integer indicating the length of the queue.
        """
        return len(self.skillQueue)

    def GetTrainingLengthOfQueue(self, position = None):
        """
            Retrieves the length of the queue, in Blue training time
            With an argument, only returns the length of skills up to,
            and including, a given position.
            ARGUMENTS:
                position:   (optional) A valid position in the queue.
                                (0 <= position <= queue length)
                                If this is None, the entire queue will be measured.
                                Note that position 0 will always return 0.
                None.
                
            RETURNS:
                A large integer indicating the amount of time it will take to
                finish training all the skills currently in the queue.
                This is in Blue Time.
        """
        if position is not None and position < 0:
            raise RuntimeError('Invalid queue position: ', position)
        trainingTime = 0
        currentAttributes = self.GetPlayerAttributeDict()
        booster = self.GetAttributeBooster()
        playerTheoreticalSkillPoints = {}
        godmaSkillSet = self.GetGodmaSkillsSet()
        currentIndex = 0
        finalIndex = position
        if finalIndex is None:
            finalIndex = len(self.skillQueue)
        for queueSkillTypeID, queueSkillLevel in self.skillQueue:
            if currentIndex >= finalIndex:
                break
            currentIndex += 1
            addedSP, addedTime, isAccelerated = self.GetAddedSpAndAddedTimeForSkill(queueSkillTypeID, queueSkillLevel, godmaSkillSet, playerTheoreticalSkillPoints, trainingTime, booster, currentAttributes)
            trainingTime += addedTime
            playerTheoreticalSkillPoints[queueSkillTypeID] += addedSP

        return trainingTime

    def GetTrainingEndTimeOfQueue(self):
        """
            Retrieves the timestamp when the queue will finish training, in Blue time
            ARGUMENTS:
                None.
                
            RETURNS:
                A large integer indicating the time when the current queue will
                finish training all of its skills. This is in Blue Time.
        """
        return blue.os.GetWallclockTime() + self.GetTrainingLengthOfQueue()

    def GetTrainingLengthOfSkill(self, skillTypeID, skillLevel, position = None):
        """
            Retrieves the Blue Time it will take to fully train a skill if that skill were
            inserted at a given position in the queue.
            ARGUMENTS:
                skillTypeID:
                skillLevel:
                position:       (optional) The hypothetical position in the queue of the skill.
                                If this is not set, and the skill is in the queue,
                                    the method will use the skill's position in the queue.
                                If this is not set and the skill is not in the queue,
                                    the method will presume that the skill is appended
                                    to the end of the queue.
                
            RETURNS:
                A tuple.
                The first is a large integer indicating the time it will take to 
                train the skill at the indicated position. This is in Blue Time.
                This includes the time required to train all skills before it
                in the queue.
                The second is a large integer indicating the time it will take
                just the skill in question.
        """
        if position is not None and (position < 0 or position > len(self.skillQueue)):
            raise RuntimeError('GetTrainingLengthOfSkill received an invalid position.')
        trainingTime = 0
        currentIndex = 0
        targetIndex = position
        if targetIndex is None:
            targetIndex = self.FindInQueue(skillTypeID, skillLevel)
            if targetIndex is None:
                targetIndex = len(self.skillQueue)
        playerTheoreticalSkillPoints = {}
        godmaSkillSet = self.GetGodmaSkillsSet()
        currentAttributes = self.GetPlayerAttributeDict()
        booster = self.GetAttributeBooster()
        for queueSkillTypeID, queueSkillLevel in self.skillQueue:
            if currentIndex >= targetIndex:
                break
            elif queueSkillTypeID == skillTypeID and queueSkillLevel == skillLevel and currentIndex < targetIndex:
                currentIndex += 1
                continue
            addedSP, addedTime, _ = self.GetAddedSpAndAddedTimeForSkill(queueSkillTypeID, queueSkillLevel, godmaSkillSet, playerTheoreticalSkillPoints, trainingTime, booster, currentAttributes)
            currentIndex += 1
            trainingTime += addedTime
            playerTheoreticalSkillPoints[queueSkillTypeID] += addedSP

        addedSP, addedTime, isAccelerated = self.GetAddedSpAndAddedTimeForSkill(skillTypeID, skillLevel, godmaSkillSet, playerTheoreticalSkillPoints, trainingTime, booster, currentAttributes)
        trainingTime += addedTime
        return (trainingTime, addedTime, isAccelerated)

    def GetTrainingParametersOfSkillInEnvironment(self, skillTypeID, skillLevel, existingSkillPoints = 0, playerAttributeDict = None):
        """
            Retrieves the Blue Time it will take to train a given skill, given a certain
            assumption of the number of skill points a player has at the start of training.
            An optional assumption can be injected about the number of skill points
            a player currently has in that skill.
            ARGUMENTS:
                skillTypeID:            The type ID of the skill in question
                skillLevel:             The level of the skill in question
                existingSkillPoints:    (optional) A number of skill points to subtract
                                        from the nominal # of skill points needed from
                                        leveling the skill. Use this to input the
                                        # of skill points a player currently has in a skill
                                        at the time training begins.
                                        If this is None, we will use the number of points
                                        the player currently has, if any.
                playerAttributeDict:    (optional) The player's current attribute dict, as
                                        obtained by the internal method GetPlayerAttributeDict().
                                        This can be passed in for caching purposes.
                                        
            RETURNS:
                A tuple.
                The first is a large integer indicating the amount of skill points
                that will be added.
                The second is a large integer indicating the time it will take to 
                train the skill using the indicated conditions. This is in Blue Time.
                This does NOT include the time required to train all skills before it,
                should the skill in question be in the queue.
        """
        skillTimeConstant = 0
        primaryAttributeID = 0
        secondaryAttributeID = 0
        playerCurrentSP = existingSkillPoints
        skillTimeConstant = self.godma.GetTypeAttribute(skillTypeID, const.attributeSkillTimeConstant)
        primaryAttributeID = self.godma.GetTypeAttribute(skillTypeID, const.attributePrimaryAttribute)
        secondaryAttributeID = self.godma.GetTypeAttribute(skillTypeID, const.attributeSecondaryAttribute)
        if existingSkillPoints is None:
            skillObj = self.GetGodmaSkillsSet().get(skillTypeID, None)
            if skillObj is not None:
                playerCurrentSP = skillObj.skillPoints
            else:
                playerCurrentSP = 0
        if skillTimeConstant is None:
            self.LogWarn('GetTrainingLengthOfSkillInEnvironment could not find skill type ID:', skillTypeID, 'via Godma')
            return 0
        skillPointsToTrain = characterskills.util.GetSPForLevelRaw(skillTimeConstant, skillLevel) - playerCurrentSP
        if skillPointsToTrain <= 0:
            return (0, 0)
        attrDict = playerAttributeDict
        if attrDict is None:
            attrDict = self.GetPlayerAttributeDict()
        playerPrimaryAttribute = attrDict[primaryAttributeID]
        playerSecondaryAttribute = attrDict[secondaryAttributeID]
        if playerPrimaryAttribute <= 0 or playerSecondaryAttribute <= 0:
            raise RuntimeError('GetTrainingLengthOfSkillInEnvironment found a zero attribute value on character', session.charid, 'for attributes [', primaryAttributeID, secondaryAttributeID, ']')
        trainingRate = characterskills.util.GetSkillPointsPerMinute(playerPrimaryAttribute, playerSecondaryAttribute)
        trainingTimeInMinutes = float(skillPointsToTrain) / float(trainingRate)
        return (skillPointsToTrain, trainingTimeInMinutes * const.MIN)

    def TrimQueue(self):
        """
            Runs through the queue and slices off any skills that would start beyond
            the time limit defined in the maxSkillqueueLength variable.
            
            Much of this is taken from GetTrainingLengthOfQueue().
            
            ARGUMENTS:
                None
                
            RETURNS:
                A list of (typeID, level) tuples representing the entries that were
                trimmed off of the queue.
        """
        trainingTime = 0
        currentAttributes = self.GetPlayerAttributeDict()
        booster = self.GetAttributeBooster()
        playerTheoreticalSkillPoints = {}
        godmaSkillSet = self.GetGodmaSkillsSet()
        cutoffIndex = 0
        for queueSkillTypeID, queueSkillLevel in self.skillQueue:
            cutoffIndex += 1
            addedSP, addedTime, isAccelerated = self.GetAddedSpAndAddedTimeForSkill(queueSkillTypeID, queueSkillLevel, godmaSkillSet, playerTheoreticalSkillPoints, trainingTime, booster, currentAttributes)
            trainingTime += addedTime
            playerTheoreticalSkillPoints[queueSkillTypeID] += addedSP
            if trainingTime > self.maxSkillqueueTimeLength:
                break

        if cutoffIndex < len(self.skillQueue):
            removedSkills = self.skillQueue[cutoffIndex:]
            self.skillQueue = self.skillQueue[:cutoffIndex]
            self.skillQueueCache = None
            sm.ScatterEvent('OnSkillQueueTrimmed', removedSkills)

    def GetAttributeBooster(self):
        myGodmaItem = sm.GetService('godma').GetItem(session.charid)
        boosters = myGodmaItem.boosters
        return characterskills.util.FindAttributeBooster(self.godma, boosters)

    def GetAttributesWithoutCurrentBooster(self, booster):
        currentAttributes = self.GetPlayerAttributeDict()
        for attributeID, value in currentAttributes.iteritems():
            newValue = characterskills.util.GetBoosterlessValue(self.godma, booster.typeID, attributeID, value)
            currentAttributes[attributeID] = newValue

        return currentAttributes

    def GetAddedSpAndAddedTimeForSkill(self, skillTypeID, skillLevel, godmaSkillSet, theoreticalSkillPointsDict, trainingTimeOffset, attributeBooster, currentAttributes = None):
        if currentAttributes is None:
            currentAttributes = self.GetPlayerAttributeDict()
        isAccelerated = False
        if attributeBooster:
            if characterskills.util.IsBoosterExpiredThen(long(trainingTimeOffset), attributeBooster.expiryTime):
                currentAttributes = self.GetAttributesWithoutCurrentBooster(attributeBooster)
            else:
                isAccelerated = True
        if skillTypeID not in theoreticalSkillPointsDict:
            skillObj = godmaSkillSet.get(skillTypeID, None)
            theoreticalSkillPointsDict[skillTypeID] = self.GetSkillPointsFromSkillObject(skillObj)
        addedSP, addedTime = self.GetTrainingParametersOfSkillInEnvironment(skillTypeID, skillLevel, theoreticalSkillPointsDict[skillTypeID], currentAttributes)
        return (addedSP, addedTime, isAccelerated)

    def GetAllTrainingLengths(self):
        """
            Runs through the queue and returns a dict, mapping skillType-Level pairs to
            a tuple of total/additional training times.
            
            ARGUMENTS:
                None.
                
            RETURNS:
                A dict of the form:
                    (skill Type ID, skill Level) => (total training time, time for this entry)
        """
        trainingTime = 0
        currentAttributes = self.GetPlayerAttributeDict()
        booster = self.GetAttributeBooster()
        resultsDict = {}
        playerTheoreticalSkillPoints = {}
        godmaSkillSet = self.GetGodmaSkillsSet()
        for queueSkillTypeID, queueSkillLevel in self.skillQueue:
            addedSP, addedTime, isAccelerated = self.GetAddedSpAndAddedTimeForSkill(queueSkillTypeID, queueSkillLevel, godmaSkillSet, playerTheoreticalSkillPoints, trainingTime, booster, currentAttributes)
            trainingTime += addedTime
            playerTheoreticalSkillPoints[queueSkillTypeID] += addedSP
            resultsDict[queueSkillTypeID, queueSkillLevel] = (trainingTime, addedTime, isAccelerated)

        return resultsDict

    def InternalRemoveFromQueue(self, skillTypeID, skillLevel):
        """
            INTERNAL USE METHOD FOR REMOVING SKILLS/LEVELS WITHOUT INTEGRITY CHECKING.
            Removes a skill from its place in the queue, invalidating the internal
            cache if needed.
            
            ARGUMENTS:
                skillTypeID:    The type ID of the skill to add
                skillLevel:     The level of the skill to add
                                
            RETURNS:
                Nothing. Throws exceptions in case of errors.
                
            INTERNAL USE ONLY.
        """
        skillPosition = self.FindInQueue(skillTypeID, skillLevel)
        if skillPosition is None:
            raise UserError('QueueSkillNotPresent')
        if skillPosition == len(self.skillQueue):
            del self.skillQueueCache[skillTypeID][skillLevel]
            self.skillQueue.pop()
        else:
            self.skillQueueCache = None
            self.skillQueue.pop(skillPosition)

    def ClearCache(self):
        """ INTERNAL USE METHOD FOR DEBUGGING.
            TODO: REMOVE THIS AFTER TESTING IS DONE.
        """
        self.skillQueueCache = None

    def AddToCache(self, skillTypeID, skillLevel, position):
        """
            INTERNAL USE METHOD.
            Adds a skill-level tuple to the skill cache,
            indicating that the given position is the position
            of the skill-level tuple in the queue.
            
            NO ERROR CHECKING. INTERNAL USE ONLY.
        """
        self.PrimeCache()
        if skillTypeID not in self.skillQueueCache:
            self.skillQueueCache[skillTypeID] = {}
        self.skillQueueCache[skillTypeID][skillLevel] = position

    def GetGodmaSkillsSet(self):
        """
            INTERNAL USE METHOD.
            Retrieves an IndexedRowset of skillTypeIDs: skill Godma objects
            from the skill service. Used for a lot of stuff internally,
            esp. knowing how many SPs the player has in a skill.
            
            INTERNAL USE ONLY.
        """
        return self.skills.GetMyGodmaItem().skills

    def GetPlayerAttributeDict(self):
        """
            INTERNAL USE ONLY.
            Stolen from infosvc. This gets the current character's attributes in a dict
            for easy use. Necessary in order to dynamically query the character's attributes
            by ID instead of by string key.
            INTERNAL USE ONLY.
        """
        attributeConsts = [const.attributePerception,
         const.attributeMemory,
         const.attributeWillpower,
         const.attributeIntelligence,
         const.attributeCharisma]
        charItem = self.godma.GetItem(session.charid)
        attrDict = {x.attributeID:x.value for x in charItem.displayAttributes if x.attributeID in attributeConsts}
        return attrDict

    def PrimeCache(self, force = False):
        """
            INTERNAL USE ONLY.
            Primes the internal skill queue position cache from the skill queue itself.
            Not particularly heavyweight on most cache setups. Still only an internal helper method.
        
            ARGUMENTS:
                force:          If set to true, the cache will be forcibly recalculated.
        
            RETURNS:
                None.
        
            INTERNAL USE ONLY.
        """
        if force:
            self.skillQueueCache = None
        if self.skillQueueCache is None:
            i = 0
            self.skillQueueCache = {}
            for queueSkillID, queueSkillLevel in self.skillQueue:
                self.AddToCache(queueSkillID, queueSkillLevel, i)
                i += 1

    def GetSkillPointsFromSkillObject(self, skillObject):
        """
            INTERNAL USE ONLY
            This retrieves the actual, current skill points for a given skill object.
            This includes adjusting the skill points for the current skill in training.
            
            ARGUMENTS:
                skillObject:        A skill object, retrieved from Godma.
                
            RETURNS:
                An integer representing the current skill points that the skill has
                'trained'.
        """
        if skillObject is None:
            return 0
        else:
            skillTrainingEnd, spHi, spm = skillObject.skillTrainingEnd, skillObject.spHi, skillObject.spm
            if skillTrainingEnd is not None and spHi is not None:
                secs = (skillTrainingEnd - blue.os.GetWallclockTime()) / const.SEC
                return min(spHi - secs / 60.0 * spm, spHi)
            return skillObject.skillPoints

    def OnGodmaSkillTrained(self, skillID):
        skill = sm.GetService('godma').GetItem(skillID)
        if not skill:
            return
        skillTypeID = skill.typeID
        level = skill.skillLevel
        if (skillTypeID, level) in self.skillQueue:
            try:
                self.InternalRemoveFromQueue(skillTypeID, level)
                sm.ScatterEvent('OnSkillFinished', skillID, skillTypeID, level)
            except UserError as ue:
                sys.exc_clear()

        if self.cachedSkillQueue and (skillTypeID, level) in self.cachedSkillQueue:
            self.cachedSkillQueue.remove((skillTypeID, level))

    def OnGodmaSkillStartTraining(self, skillID, ETA):
        skill = sm.GetService('godma').GetItem(skillID)
        level = skill.skillLevel + 1
        if (skill.typeID, level) not in self.skillQueue:
            self.AddSkillToQueue(skill.typeID, level, 0)
        else:
            self.MoveSkillToPosition(skill.typeID, level, 0)
        sm.ScatterEvent('OnSkillStarted', skill.typeID, level)

    def OnGodmaSkillTrainingStopped(self, skillID, silent):
        sm.ScatterEvent('OnSkillPaused', skillID)

    def OnSkillQueueTrimmed(self, removedSkills):
        eve.Message('skillQueueTrimmed', {'num': len(removedSkills)})

    def TrainSkillNow(self, skillID, toSkillLevel, *args):
        """
            Players don't have access to this function when they have the skill queue open.
            With that restriction we get around some issues on what happens when a skill
            is added to the top of the queue when the queue has been modified, etc.
        
            ARGUMENTS:
                skillID:        TypeID of the skill to be trained
                toSkillLevel:   The level to which the skill should be trained 
        
            RETURNS:
                None.
        
        """
        inTraining = sm.StartService('skills').SkillInTraining()
        if inTraining and eve.Message('ConfirmSkillTrainingNow', {'name': inTraining.type.typeName,
         'lvl': inTraining.skillLevel + 1}, uiconst.OKCANCEL) != uiconst.ID_OK:
            return
        self.BeginTransaction()
        commit = True
        try:
            if self.FindInQueue(skillID, toSkillLevel) is not None:
                self.MoveSkillToPosition(skillID, toSkillLevel, 0)
                eve.Message('SkillQueueStarted')
            else:
                self.AddSkillToQueue(skillID, toSkillLevel, 0)
                text = localization.GetByLabel('UI/SkillQueue/Skills/SkillNameAndLevel', skill=skillID, amount=toSkillLevel)
                if inTraining:
                    eve.Message('AddedToQueue', {'skillname': text})
                else:
                    eve.Message('AddedToQueueAndStarted', {'skillname': text})
        except (UserError, RuntimeError):
            commit = False
            raise
        finally:
            if commit:
                self.CommitTransaction()
            else:
                self.RollbackTransaction()

    def AddSkillToEnd(self, skillID, current, nextLevel = None):
        """
            Players don't have access to this function when they have the skill queue open.
            With that restriction we get around some issues on what happens when a skill
            is added to the end of the queue when the queue has been modified, etc.
        
            ARGUMENTS:
                skillID:    TypeID of the skill to be trained
                current:    The current skill level
        
            RETURNS:
                None.
        
        """
        queueLength = self.GetNumberOfSkillsInQueue()
        if queueLength >= characterskills.util.SKILLQUEUE_MAX_NUM_SKILLS:
            raise UserError('CustomNotify', {'notify': localization.GetByLabel('UI/SkillQueue/QueueIsFull')})
        totalTime = self.GetTrainingLengthOfQueue()
        if totalTime > self.maxSkillqueueTimeLength:
            raise UserError('CustomNotify', {'notify': localization.GetByLabel('UI/SkillQueue/QueueIsFull')})
        if nextLevel is None:
            queue = self.GetServerQueue()
            nextLevel = self.FindNextLevel(skillID, current, queue)
        self.AddSkillToQueue(skillID, nextLevel)
        try:
            sm.StartService('godma').GetSkillHandler().AddToEndOfSkillQueue(skillID, nextLevel)
            text = localization.GetByLabel('UI/SkillQueue/Skills/SkillNameAndLevel', skill=skillID, amount=nextLevel)
            if sm.StartService('skills').SkillInTraining():
                eve.Message('AddedToQueue', {'skillname': text})
            else:
                eve.Message('AddedToQueueAndStarted', {'skillname': text})
        except UserError:
            self.RemoveSkillFromQueue(skillID, nextLevel)
            raise

        sm.ScatterEvent('OnSkillStarted')

    def FindNextLevel(self, skillID, current, list = None):
        """
            This method is used to find next level of the specified skill
            that would be added to the skill queue.
            If no list is passed to this function, the skill queue as it is
            on the server will be used.
            
            ARGUMENTS:
                skillID     :   The type ID of the skill you need the next level for
                skillLevel  :   Your current level of that skill
                list        :   The skill queue (temporary SQ)
                                
            RETURNS:
                The level that would be planned next if this skill was added to the
                queue
        
        """
        if list is None:
            list = self.GetServerQueue()
        nextLevel = None
        for i in xrange(1, 7):
            if current >= i:
                continue
            inQueue = bool((skillID, i) in list)
            if inQueue is False:
                nextLevel = i
                break

        return nextLevel

    def OnSkillQueueForciblyUpdated(self):
        """
            A message from the server telling us that we need to re-fetch the queue
            from the server, as it has been remotely modified.
        """
        if self.skillQueueCache is not None:
            self.BeginTransaction()

    def OnMultipleCharactersTrainingUpdated(self):
        """
        Invlidates our local cache of multiple character training queues whenever they change.
        """
        sm.GetService('objectCaching').InvalidateCachedMethodCall('userSvc', 'GetMultiCharactersTrainingSlots')
        sm.ScatterEvent('OnMultipleCharactersTrainingRefreshed')

    def GetMultipleCharacterTraining(self, force = False):
        """
        Returns the ID and expiry date for multiple training queues for the current user.
        """
        if force:
            sm.GetService('objectCaching').InvalidateCachedMethodCall('userSvc', 'GetMultiCharactersTrainingSlots')
        return sm.RemoteSvc('userSvc').GetMultiCharactersTrainingSlots()

    def IsQueueWndOpen(self):
        return form.SkillQueue.IsOpen()

    def GetAddMenuForSkillEntries(self, skill):
        """
            This functions get the right click menu options for skill entries (SkillTreeEntry, and SkillEntry)
            ARGUMENTS:
                skill :   The skill you need the menu options for
                                
            RETURNS:
                A list of the right click menu options that are available for that skill
        """
        m = []
        if skill is None:
            return m
        skillLevel = skill.skillLevel
        if skillLevel is not None:
            sqWnd = form.SkillQueue.GetIfOpen()
            if skillLevel < 5:
                queue = self.GetQueue()
                nextLevel = self.FindNextLevel(skill.typeID, skill.skillLevel, queue)
                if skill.flagID == const.flagSkill:
                    trainingTime, totalTime, _ = self.GetTrainingLengthOfSkill(skill.typeID, skill.skillLevel + 1, 0)
                    takesText = ''
                    if trainingTime <= 0:
                        takesText = localization.GetByLabel('UI/SkillQueue/Skills/CompletionImminent')
                    else:
                        takesText = localization.GetByLabel('UI/SkillQueue/Skills/SkillTimeLeft', timeLeft=long(trainingTime))
                    if sqWnd:
                        if nextLevel < 6 and self.FindInQueue(skill.typeID, skill.skillLevel + 1) is None:
                            trainText = uiutil.MenuLabel('UI/SkillQueue/AddSkillMenu/AddToFrontOfQueueTime', {'takes': takesText})
                            m.append((trainText, sqWnd.AddSkillsThroughOtherEntry, (skill.typeID,
                              0,
                              queue,
                              nextLevel,
                              1)))
                    else:
                        trainText = uiutil.MenuLabel('UI/SkillQueue/AddSkillMenu/TrainNowWithTime', {'skillLevel': skill.skillLevel + 1,
                         'takes': takesText})
                        m.append((trainText, self.TrainSkillNow, (skill.typeID, skill.skillLevel + 1)))
                if nextLevel < 6:
                    if sqWnd:
                        label = uiutil.MenuLabel('UI/SkillQueue/AddSkillMenu/AddToEndOfQueue', {'nextLevel': nextLevel})
                        m.append((label, sqWnd.AddSkillsThroughOtherEntry, (skill.typeID,
                          -1,
                          queue,
                          nextLevel,
                          1)))
                    else:
                        label = uiutil.MenuLabel('UI/SkillQueue/AddSkillMenu/TrainAfterQueue', {'nextLevel': nextLevel})
                        m.append((label, self.AddSkillToEnd, (skill.typeID, skill.skillLevel, nextLevel)))
                if sm.GetService('skills').GetFreeSkillPoints() > 0:
                    diff = skill.spHi + 0.5 - skill.skillPoints
                    m.append((uiutil.MenuLabel('UI/SkillQueue/AddSkillMenu/ApplySkillPoints'), self.UseFreeSkillPoints, (skill.typeID, diff)))
            if skill.flagID == const.flagSkillInTraining:
                m.append((uiutil.MenuLabel('UI/SkillQueue/AddSkillMenu/AbortTraining'), sm.StartService('skills').AbortTrain, (skill,)))
        if m:
            m.append(None)
        return m

    def UseFreeSkillPoints(self, skillTypeID, diff):
        if sm.StartService('skills').SkillInTraining():
            eve.Message('CannotApplyFreePointsWhileQueueActive')
            return
        freeSkillPoints = sm.StartService('skills').GetFreeSkillPoints()
        text = localization.GetByLabel('UI/SkillQueue/AddSkillMenu/UseSkillPointsWindow', skill=skillTypeID, skillPoints=int(diff))
        caption = localization.GetByLabel('UI/SkillQueue/AddSkillMenu/ApplySkillPoints')
        ret = uix.QtyPopup(maxvalue=freeSkillPoints, caption=caption, label=text)
        if ret is None:
            return
        sp = int(ret.get('qty', ''))
        currentSkillPoints = sm.GetService('skills').GetSkillPoints()
        sm.StartService('skills').ApplyFreeSkillPoints(skillTypeID, sp)

    def IsMoveAllowed(self, draggedNode, checkedIdx):
        queue = self.GetQueue()
        if checkedIdx is None:
            checkedIdx = len(queue)
        if draggedNode.skillID:
            if draggedNode.panel and draggedNode.panel.__guid__ == 'listentry.SkillEntry':
                level = self.FindNextLevel(draggedNode.skillID, draggedNode.skill.skillLevel, queue)
            else:
                level = draggedNode.Get('trainToLevel', 1)
                if draggedNode.inQueue is None:
                    level += 1
            return self.CheckCanInsertSkillAtPosition(draggedNode.skillID, level, checkedIdx, check=1, performLengthTest=False)
        if draggedNode.__guid__ in ('xtriui.InvItem', 'listentry.InvItem'):
            category = GetAttrs(draggedNode, 'rec', 'categoryID')
            if category != const.categorySkill:
                return
            typeID = GetAttrs(draggedNode, 'rec', 'typeID')
            if typeID is None:
                return
            skill = sm.StartService('skills').GetMySkillsFromTypeID(typeID)
            if skill:
                return False
            meetsReq = sm.StartService('godma').CheckSkillRequirementsForType(typeID)
            if not meetsReq:
                return False
            return True
        if draggedNode.__guid__ == 'listentry.SkillTreeEntry':
            typeID = draggedNode.typeID
            if typeID is None:
                return
            mySkills = sm.StartService('skills').GetMyGodmaItem().skills
            skill = mySkills.get(typeID, None)
            if skill is None:
                return
            skill = sm.StartService('skills').GetMySkillsFromTypeID(typeID)
            level = self.FindNextLevel(typeID, skill.skillLevel, queue)
            return self.CheckCanInsertSkillAtPosition(typeID, level, checkedIdx, check=1, performLengthTest=False)
