#Embedded file name: eveaudio\dynamicmusicsystem.py
import eveaudio
import eve.common.lib.appConst as const

class DynamicMusicSystem(object):

    def __init__(self, sendEvent):
        self.sendEvent = sendEvent
        self.loginMusicPaused = False
        self.musicPlaying = False
        self._musicEnabled = True
        self.musicLocation = None
        self.lastLocationPlayed = None

    def UpdateDynamicMusic(self, uicore, solarsystemid2, securityStatus):
        """
        Takes the state and location and feeds those information into the music engine.
        
        :param uicore:
        :param solarsystemid2: the solarsystemid2 of the current system user is in.
        """
        if not self._musicEnabled:
            return
        self.musicLocation = GetMusicLocation(uicore, solarsystemid2)
        if self.musicLocation is eveaudio.MUSIC_LOCATION_CHARACTER_CREATION:
            self.SetCharacterCreationMusicState(uicore)
        elif self.musicLocation is eveaudio.MUSIC_LOCATION_SPACE:
            self.SetSpaceMusicState(solarsystemid2, securityStatus)
        if self.musicLocation is None or self.lastLocationPlayed == self.musicLocation:
            return
        self.PlayLocationMusic(self.musicLocation)

    def PlayLocationMusic(self, location):
        """
        This takes care of playing a music track under the music_eve_dynamic
        music system. It will turn off the music that is currently playing
        or pause it if it's the login music. It will update the state flags as
        needed.
        
        :param location: should be MUSIC_LOCATION_LOGIN,
                                    MUSIC_LOCATION_CHARACTER_CREATION or
                                    MUSIC_LOCATION_SPACE
        """
        if self.lastLocationPlayed is not None:
            self.StopLocationMusic(self.lastLocationPlayed)
        if location == eveaudio.MUSIC_LOCATION_LOGIN and self.loginMusicPaused:
            self.ResumeLocationMusic(location)
            return
        if not self.musicPlaying:
            self.musicPlaying = True
            self.lastLocationPlayed = location
            self.sendEvent(location + '_play')
        if location == eveaudio.MUSIC_LOCATION_SPACE and self.loginMusicPaused:
            self.sendEvent(eveaudio.MUSIC_LOCATION_LOGIN + '_stop')
            self.loginMusicPaused = False

    def StopLocationMusic(self, location):
        """
        This take care of actually stopping a track and set the state flags
        accordingly. It checks for the login music location to pause the music
        instead of stopping it.
        
        :param location: should be MUSIC_LOCATION_LOGIN,
                                    MUSIC_LOCATION_CHARACTER_CREATION or
                                    MUSIC_LOCATION_SPACE
        """
        if location == eveaudio.MUSIC_LOCATION_LOGIN and self.musicLocation != eveaudio.MUSIC_LOCATION_SPACE:
            self.PauseLocationMusic(location)
            return
        self.sendEvent(location + '_stop')
        self.lastLocationPlayed = None
        self.musicPlaying = False

    def PauseLocationMusic(self, location):
        """
        This pauses music, only used for the login music when going from
        login to character creation and back.
        """
        self.sendEvent(location + '_pause')
        self.musicPlaying = False
        self.lastLocationPlayed = None
        if location == eveaudio.MUSIC_LOCATION_LOGIN:
            self.loginMusicPaused = True

    def ResumeLocationMusic(self, location):
        self.sendEvent(location + '_resume')
        self.musicPlaying = True
        self.lastLocationPlayed = location
        if location == eveaudio.MUSIC_LOCATION_LOGIN:
            self.loginMusicPaused = False

    def EnableMusic(self):
        self._musicEnabled = True

    def DisableMusic(self):
        if self.lastLocationPlayed:
            self.StopLocationMusic(self.lastLocationPlayed)
        self.lastLocationPlayed = None
        self.loginMusicPaused = False
        self.musicPlaying = False
        self._musicEnabled = False

    def IsMusicEnabled(self):
        return self._musicEnabled

    def SetCharacterCreationMusicState(self, uicore, ccConstRaceStep = 1):
        """
        This function takes care of checking the state of the character
        creation to have the correct state playing.
        """
        raceID = uicore.layer.charactercreation.raceID
        stepID = uicore.layer.charactercreation.stepID
        if not raceID:
            self.sendEvent(eveaudio.MUSIC_STATE_FULL)
            self.sendEvent(eveaudio.MUSIC_STATE_RACE_NORACE)
        elif stepID == ccConstRaceStep:
            raceState = eveaudio.RACIALMUSICDICT.get(raceID)
            self.sendEvent(raceState)
            self.sendEvent(eveaudio.MUSIC_STATE_FULL)
        else:
            raceState = eveaudio.RACIALMUSICDICT.get(raceID)
            self.sendEvent(raceState)
            self.sendEvent(eveaudio.MUSIC_STATE_AMBIENT)

    def SetSpaceMusicState(self, solarsystemid2, securityStatus):
        """
        This sets the space music state if it is not empty.
        """
        musicState = GetSpaceMusicState(solarsystemid2, securityStatus)
        if musicState:
            self.sendEvent(musicState)

    def SetDynamicMusicSwitchPopularity(self, pilotsInChannel, securityStatus):
        """
        This sets the Dynamic music switch for High security systems in eve.
        Only valid in space.
        
        :param pilotsInChannel: number of pilots in the chat channel (in solarsystem)
        """
        state = GetDynamicMusicSwitchPopularity(pilotsInChannel, securityStatus)
        if state is not None:
            self.sendEvent(state)


def GetDynamicMusicSwitchPopularity(pilotsInChannel, securityStatus):
    """
    Handles changes of solarsystem in highsec. Plays different kind of music depending on whether
    it's popular or not.
    
    :param pilotsInChannel: number of pilots in the chat channel (number of pilots in space)
    """
    if securityStatus != const.securityClassHighSec:
        return
    elif pilotsInChannel > eveaudio.PILOTS_IN_SPACE_TO_CHANGE_MUSIC:
        return eveaudio.MUSIC_STATE_EMPIRE_POPULATED
    else:
        return eveaudio.MUSIC_STATE_EMPIRE


def GetSpaceMusicState(solarsystemid2, securityStatus):
    """
    This checks the state of the space music and returns it.
    """
    if securityStatus == const.securityClassZeroSec:
        if solarsystemid2 > eveaudio.WORMHOLE_SYSTEM_ID_STARTS:
            return eveaudio.MUSIC_STATE_NULLSEC_WORMHOLE
        else:
            return eveaudio.MUSIC_STATE_NULLSEC
    else:
        if securityStatus == const.securityClassLowSec:
            return eveaudio.MUSIC_STATE_LOWSEC
        if securityStatus == const.securityClassHighSec:
            return eveaudio.MUSIC_STATE_EMPIRE


def GetMusicLocation(uicore, solarsystemid2):
    """
    Finds the possible music locations in the, login, character creation
    and space, and returns the location.
    """
    if getattr(uicore.layer.login, 'isopen', None) or getattr(uicore.layer.charsel, 'isopen', None) or getattr(uicore.layer.charsel, 'isopening', None):
        return eveaudio.MUSIC_LOCATION_LOGIN
    if getattr(uicore.layer.charactercreation, 'isopen', None) or getattr(uicore.layer.charactercreation, 'isopening', None):
        return eveaudio.MUSIC_LOCATION_CHARACTER_CREATION
    if solarsystemid2:
        return eveaudio.MUSIC_LOCATION_SPACE
