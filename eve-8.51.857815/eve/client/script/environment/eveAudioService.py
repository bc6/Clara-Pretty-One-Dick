#Embedded file name: eve/client/script/environment\eveAudioService.py
"""
This file contains the EVE-specific logic for unpacking messages and configuring the
client audio service through which all sounds are governed.
This service also handles audio parameter configuration business logic.
"""
import service
import eveaudio
from eveaudio.dynamicmusicsystem import DynamicMusicSystem

class DungeonCheckerService(service.Service):
    """Handles some crazy logic to determine if we're in a dungeon or not.
    
    When we enter a dungeon for the first time,
    our DungeonEntered/IncomingTransmission fire, 
    and we can safely say we are entering a dungeon.
    After that, the WarpFinished event fires.
    When we travel between rooms,
    the accelleration gate will set our state as inside of a dungeon.
    When we leave the dungeon, the WarpFinished event will fire again.
    """
    __guid__ = 'svc.dungeonChecker'
    __exportedcalls__ = {'AccelerationGateUpdate': [],
     'WarpFinishedUpdate': [],
     'IsInDungeon': []}
    __notifyevents__ = ['OnSessionChanged',
     'OnWarpFinished',
     'OnDistributionDungeonEntered',
     'OnEscalatingPathDungeonEntered',
     'OnIncomingTransmission']

    def __init__(self):
        service.Service.__init__(self)
        self.isInDungeon = False
        self.enteringDungeon = False

    def Run(self, *args):
        service.Service.Run(self, *args)
        sm.FavourMe(self.OnWarpFinished)

    def AccelerationGateUpdate(self):
        """Call when we go through an acceleration gate (go between dungeon rooms)."""
        self.isInDungeon = True
        self.enteringDungeon = True

    def WarpFinishedUpdate(self):
        """Call when a warp finishes. 
        Is called by OnWarpFinished, which includes acceleration gates, etc.
        """
        if self.enteringDungeon:
            self.isInDungeon = True
            self.enteringDungeon = False
        else:
            self.isInDungeon = False

    def IsInDungeon(self):
        return self.isInDungeon or self.enteringDungeon

    def OnSessionChanged(self, *args):
        self.isInDungeon = False
        self.enteringDungeon = False

    def OnWarpFinished(self, *args):
        self.WarpFinishedUpdate()

    def OnDistributionDungeonEntered(self, *args):
        self.enteringDungeon = True

    def OnEscalatingPathDungeonEntered(self, *args):
        self.enteringDungeon = True

    def OnIncomingTransmission(self, *args):
        self.enteringDungeon = True


class DynamicMusicService(service.Service):
    __guid__ = 'svc.dynamicMusic'
    __notifyevents__ = ['OnSessionChanged', 'OnChannelsJoined', 'OnWarpFinished']
    __dependencies__ = ['audio', 'dungeonChecker']

    def Run(self, *args):
        service.Service.Run(self, *args)
        self.dynamicMusicSystem = DynamicMusicSystem(self.audio.SendWiseEvent)

    def MusicVolumeChangedByUser(self, volume):
        if volume == 0.0 and self.dynamicMusicSystem.IsMusicEnabled():
            self.dynamicMusicSystem.DisableMusic()
        elif volume != 0.0 and not self.dynamicMusicSystem.IsMusicEnabled():
            self.dynamicMusicSystem.EnableMusic()
            self.UpdateDynamicMusic()

    def StopLocationMusic(self, location):
        """
        Forwards a stop location message to the dynamicMusicSystem
        :param location: a string representing the location, see eveaudio.dynamicmusicsystem.StopLocationMusic()
        """
        self.dynamicMusicSystem.StopLocationMusic(location)

    def PlayLocationMusic(self, location):
        """
        Forwards a play loaction message to the dynamicMusicSystem
        :param location: a string representing the location, see eveaudio.dynamicmusicsystem.PlayLocationMusic()
        :return:
        """
        self.dynamicMusicSystem.PlayLocationMusic(location)

    def OnSessionChanged(self, *args):
        """
            Is an notify event that happens every time an eve session changes.
            It's needed to take decisions about changes in music.
        :param args: all arguments, not needed in this function.
        """
        if session.solarsystemid2:
            self.UpdateDynamicMusic()

    def UpdateDynamicMusic(self):
        """
        Takes the state and location and feeds those information into the music engine.
        """
        self.dynamicMusicSystem.UpdateDynamicMusic(uicore, session.solarsystemid2, self._GetSecurityStatus())

    def OnWarpFinished(self, *args):
        """
        Takes care of updating the music system when warp is finished.
        :param args: unused arguments, not needed in this function
        """
        if not self.dungeonChecker.IsInDungeon():
            self.UpdateDynamicMusic()

    def OnChannelsJoined(self, channelIDs):
        """
            Is an notify event that happens each time you join a chat channel so we can evalutate the population
            at your current location to feed that state into the sound engine.
        
        :param channelIDs: A list of channel IDs
        """
        if self.dungeonChecker.isInDungeon:
            return
        if (('solarsystemid2', session.solarsystemid2),) in channelIDs:
            pilotsInChannel = eveaudio.GetPilotsInSystem()
            self._SetDynamicMusicSwitchPopularity(pilotsInChannel)
            self.UpdateDynamicMusic()

    def _SetDynamicMusicSwitchPopularity(self, pilotsInChannel = None):
        if not session.solarsystemid2:
            return
        if pilotsInChannel is None:
            pilotsInChannel = eveaudio.GetPilotsInSystem()
        self.dynamicMusicSystem.SetDynamicMusicSwitchPopularity(pilotsInChannel, self._GetSecurityStatus())

    def _GetSecurityStatus(self):
        securityStatus = 1.0
        if session.solarsystemid2:
            securityStatus = sm.GetService('map').GetSecurityClass(session.solarsystemid2)
        return securityStatus
