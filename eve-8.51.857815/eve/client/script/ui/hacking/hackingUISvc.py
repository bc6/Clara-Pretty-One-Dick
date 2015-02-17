#Embedded file name: eve/client/script/ui/hacking\hackingUISvc.py
import service
import hackingcommon.hackingConstants as hackingConst
import hackingUIConst
import hackingui as hackUI
import form
import random
import blue
import log
from contextlib import contextmanager

class HackingSvc(service.Service):
    """ 
    Provides data for the profession minigame UI
    """
    __guid__ = 'svc.hackingUI'
    __servicename__ = 'hackingUI'
    __displayname__ = 'Hacking UI'
    __notifyevents__ = ['OnHackingTurnComplete']
    __dependencies__ = []

    def Run(self, *args):
        self.game = None
        self.gameType = None
        self.selectedUtilElement = None
        self.virusID = None
        self.hackingMgr = sm.RemoteSvc('hackingMgr')
        self.tileDataByCoord = {}
        self.utilityElements = []
        self.virusStrength = None
        self.virusCoherence = None
        self.gameEnded = True
        self.difficulty = 1
        self.virusInitialCoherence = 200
        self.virusInitialStrength = 30
        self.virusSlots = 3

    def SetDifficulty(self, difficulty):
        """ TODO: Remove this temp method """
        self.difficulty = difficulty

    def SetVirusStats(self, coherence, strength, slots):
        """ TODO: Remove this temp method """
        self.virusInitialCoherence = coherence
        self.virusInitialStrength = strength
        self.virusSlots = slots

    def TriggerNewGame(self):
        """ TODO: Remove this temp method """
        import random
        self._ResetGameInfo()
        self.gameType = random.choice((hackingConst.GAMETYPE_HACKING, hackingConst.GAMETYPE_ARCHEOLOGY))
        self.hackingMgr.StartNewGameInstance(None, self.gameType, 22329, self.difficulty, self.virusInitialCoherence, self.virusInitialStrength, self.virusSlots)

    def QuitHackingAttempt(self):
        self.hackingMgr.QuitHackingAttempt()

    def OnHackingTurnComplete(self, events):
        """
        Callback from the server fired when a turn has been completed
        :param events: The events that occurred this turn
        """
        startEvents = [ event for event in events if event['eventID'] == hackingConst.EVENT_GAME_START ]
        if len(startEvents) > 0:
            self._OpenWindowOrReloadIfGameEnded()
        self._GameEventHandler(events)

    def _OpenWindowOrReloadIfGameEnded(self):
        if self.gameEnded:
            window = form.HackingWindow.GetIfOpen()
            if not window:
                self._ResetGameInfo()
                form.HackingWindow.Open()
            else:
                self._ResetGameInfo()
                form.HackingWindow.Reload(window)

    def _ResetGameInfo(self):
        random.seed()
        self.gameEnded = False
        self.tileDataByCoord = {}
        self.utilityElements = []

    def _GameEventHandler(self, events):
        for event in events:
            eventID = event['eventID']
            if eventID == hackingConst.EVENT_GAME_WON:
                sm.ScatterEvent('OnHackingWon')
                sm.GetService('audio').SendUIEvent('minigame_win')
                self.gameEnded = True
            elif eventID == hackingConst.EVENT_GAME_LOST:
                sm.ScatterEvent('OnHackingLost')
                sm.GetService('audio').SendUIEvent('minigame_loose')
                sm.GetService('audio').SendUIEvent('minigame_stop')
                self.gameEnded = True
            elif eventID == hackingConst.EVENT_GAME_START:
                self.ConstructTileDataNeighbours()
                sm.ScatterEvent('OnHackingStart', event['eventData'])
                if self.gameType == hackingConst.GAMETYPE_HACKING:
                    sm.GetService('audio').SendUIEvent('minigame_type_hack')
                elif self.gameType == hackingConst.GAMETYPE_ARCHEOLOGY:
                    sm.GetService('audio').SendUIEvent('minigame_type_arch')
            elif eventID == hackingConst.EVENT_GAME_STYLE:
                self.gameType = event['eventData']['style']
            elif eventID in (hackingConst.EVENT_TILE_FLIPPED,
             hackingConst.EVENT_TILE_BLOCKED,
             hackingConst.EVENT_DATACACHE_OPEN,
             hackingConst.EVENT_KERNALROT):
                eventData = event['eventData']
                if eventID == hackingConst.EVENT_TILE_FLIPPED:
                    type = eventData['type']
                    if type == hackingConst.TYPE_SEGMENT:
                        sm.GetService('audio').SendUIEvent('minigame_click_unexp_nothing')
                    elif type == hackingConst.TYPE_DEFENSESOFTWARE:
                        sm.GetService('audio').SendUIEvent('minigame_click_unexp_defence')
                        sm.ScatterEvent('OnDefenseSoftwareUnveiled', eventData['coord'])
                    elif type == hackingConst.TYPE_CORE:
                        sm.GetService('audio').SendUIEvent('minigame_click_unexp_goal')
                        sm.ScatterEvent('OnCoreUnveiled', eventData['coord'])
                    elif type == hackingConst.TYPE_DATACACHE:
                        sm.GetService('audio').SendUIEvent('minigame_click_unexp_treasure')
                    elif type == hackingConst.TYPE_UTILITYELEMENTTILE:
                        sm.GetService('audio').SendUIEvent('minigame_click_data_utility')
                elif eventID == hackingConst.EVENT_DATACACHE_OPEN:
                    type = eventData['type']
                    if type == hackingConst.TYPE_DEFENSESOFTWARE:
                        sm.ScatterEvent('OnDefenseSoftwareUnveiled', eventData['coord'])
                        sm.GetService('audio').SendUIEvent('minigame_click_data_defence')
                    else:
                        sm.GetService('audio').SendUIEvent('minigame_click_data_utility')
                self.HandleTileUpdatedEvent(eventID, eventData)
            elif eventID == hackingConst.EVENT_TILE_CREATED:
                eventData = event['eventData']
                tileData = hackUI.TileData(**eventData)
                if tileData.coord in self.tileDataByCoord:
                    if not self.gameEnded:
                        log.LogException('Hacking: Attempting to add tile to a coordinate that already contains a tile.')
                self.tileDataByCoord[tileData.coord] = tileData
                sm.ScatterEvent('OnHackingTileCreated', tileData, eventData)
            elif eventID == hackingConst.EVENT_ATTACK:
                self.HandleAttackEvent(event['eventData'], eventID)
                if event['eventData']['defenderResult']['coherence'] == 0:
                    sm.GetService('audio').SendUIEvent('minigame_kill')
                else:
                    sm.GetService('audio').SendUIEvent('minigame_use_utility_other')
            elif eventID == hackingConst.EVENT_VIRUS_CREATED:
                eventData = event['eventData']
                self.virusID = eventData['id']
                self.HandleVirusStatsChangedEvent(eventData, eventID)
                self.ConstructUtilityElements(eventData['inventory'])
            elif eventID == hackingConst.EVENT_UE_PICKEDUP:
                self.HandleUEPickedUpEvent(event['eventData'])
                sm.GetService('audio').SendUIEvent('minigame_inventory_add')
            elif eventID == hackingConst.EVENT_UE_REMOVED:
                eventData = event['eventData']
                if self.utilityElements[eventData['index']].subtype == hackingConst.SUBTYPE_UE_POLYMORPHICSHIELD:
                    sm.GetService('audio').SendUIEvent('minigame_shield_end')
                self.HandleUtilityElementsChanged(eventData['inventory']['inventory'])
                sm.GetService('audio').SendUIEvent('minigame_use_utility_you')
            elif event['eventID'] == hackingConst.EVENT_UE_INUSE:
                eventData = event['eventData']
                if self.utilityElements[eventData['index']].subtype == hackingConst.SUBTYPE_UE_POLYMORPHICSHIELD:
                    sm.GetService('audio').SendUIEvent('minigame_shield')
                self.utilityElements[eventData['index']].isInUse = bool(eventData['value'])
                sm.ScatterEvent('OnHackingUEInventoryChanged')
            elif eventID == hackingConst.EVENT_SELFREPAIR:
                sm.GetService('audio').SendUIEvent('minigame_use_utility_self')
                eventData = event['eventData']
                self.utilityElements[eventData['index']].durationRemaining = eventData['durationRemaining']
                sm.ScatterEvent('OnHackingUEInventoryChanged')
                self.HandleVirusStatsChangedEvent(eventData['target'], eventID)
            elif eventID == hackingConst.EVENT_OBJECT_KILLED:
                eventData = event['eventData']
                if eventData['type'] == hackingConst.TYPE_VIRUS:
                    self.HandleVirusStatsChangedEvent(eventData, eventID)
                else:
                    self.HandleTileUpdatedEvent(eventID, eventData)
            elif eventID == hackingConst.EVENT_POLYMORPHICSHIELDHIT:
                eventData = event['eventData']
                self.utilityElements[eventData['index']].durationRemaining = eventData['durationRemaining']
                sm.GetService('audio').SendUIEvent('minigame_use_utility_self')
                sm.ScatterEvent('OnHackingUEInventoryChanged')
                sm.ScatterEvent('OnHackingUEDurationReduced', eventData['index'], None)
            elif eventID == hackingConst.EVENT_SECONDARYVECTOR:
                sm.GetService('audio').SendUIEvent('minigame_use_utility_other')
                eventData = event['eventData']
                self.utilityElements[eventData['index']].durationRemaining = eventData['durationRemaining']
                self.HandleTileUpdatedEvent(eventID, eventData)
                sm.ScatterEvent('OnHackingUEInventoryChanged')
                sm.ScatterEvent('OnHackingUEDurationReduced', eventData['index'], eventData['coord'])
            elif eventID == hackingConst.EVENT_HONEYPOT_STRENGTH:
                sm.GetService('audio').SendUIEvent('minigame_defencepowerup')
                eventData = event['eventData']
                self.HandleVirusStatsChangedEvent(eventData['virus'], eventID)
            elif eventID == hackingConst.EVENT_HONEYPOT_HEALING:
                sm.GetService('audio').SendUIEvent('minigame_defencepowerup')
                eventData = event['eventData']
                sm.ScatterEvent('OnHoneyPotHealed', eventData['coord'], eventData['healedObject']['coord'], eventData['healingAmount'])
                self.HandleTileUpdatedEvent(eventID, eventData['healedObject'])
            elif eventID == hackingConst.EVENT_CORE_CONTENTS:
                eventData = event['eventData']
                sm.ScatterEvent('OnCoreContentsRevealed', eventData['coord'], eventData['contentsList'])
            elif eventID == hackingConst.EVENT_DISTANCEINDICATOR:
                eventData = event['eventData']
                self.HandleTileUpdatedEvent(eventID, eventData)
            if eventID in hackingUIConst.EVENTS_SLEEP and len(events) > 1:
                blue.synchro.SleepWallclock(hackingUIConst.EVENTS_SLEEP[eventID])
            else:
                blue.synchro.Yield()

    def ConstructUtilityElements(self, inventory):
        for i, element in enumerate(inventory):
            elementData = hackUI.UtilityElementData(index=i, **element)
            self.utilityElements.append(elementData)

        sm.ScatterEvent('OnHackingUEInventoryConstructed', self.utilityElements)

    def HandleTileUpdatedEvent(self, eventID, eventData):
        tileData = self.tileDataByCoord[eventData['coord']]
        tileData.Update(**eventData)
        sm.ScatterEvent('OnHackingTileChanged', eventID, tileData)

    def HandleUEPickedUpEvent(self, eventData):
        coord = eventData['coord']
        replacementObject = eventData['replacementObject']
        inventoryContents = eventData['inventory']
        self.HandleTileUpdatedEvent(hackingConst.EVENT_UE_PICKEDUP, replacementObject)
        self.HandleUtilityElementsChanged(inventoryContents)

    def HandleAttackEvent(self, eventData, eventID):
        attacker = eventData['attackerResult']
        defender = eventData['defenderResult']
        if attacker['type'] == hackingConst.TYPE_VIRUS:
            self.HandleVirusStatsChangedEvent(attacker, eventID)
        else:
            self.HandleTileUpdatedEvent(hackingConst.EVENT_ATTACK, attacker)
        if defender['type'] == hackingConst.TYPE_VIRUS:
            self.HandleVirusStatsChangedEvent(defender, eventID)
        else:
            self.HandleTileUpdatedEvent(hackingConst.EVENT_ATTACK, defender)

    def HandleVirusStatsChangedEvent(self, eventData, eventID):
        self.virusStrength = eventData['strength']
        self.virusCoherence = eventData['coherence']
        sm.ScatterEvent('OnHackingVirusChanged', eventData, eventID)

    def GetVirusStrengthAndCoherence(self):
        return (self.virusStrength, self.virusCoherence)

    def HandleUtilityElementsChanged(self, inventoryContents):
        for i, element in enumerate(inventoryContents):
            self.utilityElements[i].Update(**element)

        sm.ScatterEvent('OnHackingUEInventoryChanged')

    def OnTileClicked(self, tileCoord):
        """ A tile has been clicked by the player """
        if self.selectedUtilElement is not None:
            self.hackingMgr.UsedUtilityElement(self.selectedUtilElement, tileCoord)
            if self.tileDataByCoord[tileCoord].type not in (hackingConst.TYPE_CORE, hackingConst.TYPE_DEFENSESOFTWARE):
                sm.GetService('audio').SendUIEvent('minigame_error')
            self.SetSelectedUtilElement(None)
        else:
            if self.tileDataByCoord[tileCoord].blocked:
                sm.GetService('audio').SendUIEvent('minigame_error')
            self.hackingMgr.ClickedOnTile(tileCoord)

    def OnUtilityElementClicked(self, index, utilData):
        if index == self.selectedUtilElement:
            self.SetSelectedUtilElement(None)
        elif utilData.subtype in hackingConst.UE_SUBTYPES_APPLIED_TO_VIRUS:
            sm.GetService('audio').SendUIEvent('minigame_inventory_add')
            self.hackingMgr.UsedUtilityElementOnVirus(index)
        elif utilData.subtype in hackingConst.UE_SUBTYPES_APPLIED_TO_TARGET:
            sm.GetService('audio').SendUIEvent('minigame_inventory_add')
            self.SetSelectedUtilElement(index)

    def SetSelectedUtilElement(self, index = None):
        self.selectedUtilElement = index
        for i, uiData in enumerate(self.utilityElements):
            uiData.isSelected = i == self.selectedUtilElement

        sm.ScatterEvent('OnSelectedUtilityElementChanged', index)

    def ConstructTileDataNeighbours(self):
        """ Prime tile data instances with information about their neighbours """
        for tileData in self.tileDataByCoord.values():
            neighbourTileData = self.GetTileNeighbours(tileData)
            tileData.SetNeighbours(neighbourTileData)

    def GetTileNeighbours(self, tileData):
        """ Returns a list of neighboring tile coordinates if they exist"""
        ret = []
        if tileData.coord[1] % 2:
            offsets = hackingUIConst.NEIGHBOR_OFFSETS1
        else:
            offsets = hackingUIConst.NEIGHBOR_OFFSETS2
        for dx, dy in offsets:
            coord = (tileData.coord[0] + dx, tileData.coord[1] + dy)
            if coord in self.tileDataByCoord:
                ret.append(coord)

        return [ self.tileDataByCoord[coord] for coord in ret ]

    def SetTileHint(self, hint = None):
        wnd = form.HackingWindow.GetIfOpen()
        if wnd:
            wnd.SetTileHint(hint)
