#Embedded file name: carbon/client/script/environment\audioService.py
"""
This file contains the client audio service through which all sounds are governed.
In order to play any audio in EVE that is not directly governed by WWise/Effects/3D
your services should call into this service.
This service also handles audio parameter configuration.
"""
import service
import blue
import audio2
import trinity
import weakref
import funcDeco
import log
import sys
import eveaudio
from eveaudio.shiphealthnotification import ShipHealthNotifier
import eveaudio.audiomanager as audiomanager
from eveaudio.gameworldaudio import GameworldAudioMixin
from eveaudio.audiomanager import AudioManager
import carbonui.const as uiconst
customSoundLevelsSettings = {'custom_master': 'custom_master',
 'custom_turrets': 'custom_turrets',
 'custom_jumpgates': 'custom_jumpgates',
 'custom_wormholes': 'custom_wormholes',
 'custom_jumpactivation': 'custom_jumpactivation',
 'custom_crimewatch': 'custom_crimewatch',
 'custom_explosions': 'custom_explosions',
 'custom_boosters': 'custom_boosters',
 'custom_stationext': 'custom_stationext',
 'custom_stationint': 'custom_stationint',
 'custom_modules': 'custom_modules',
 'custom_warping': 'custom_warping',
 'custom_mapisis': 'custom_mapisis',
 'custom_locking': 'custom_locking',
 'custom_shipsounds': 'custom_shipsounds',
 'custom_shipdamage': 'custom_shipdamage',
 'custom_store': 'custom_store',
 'custom_planets': 'custom_planets',
 'custom_uiclick': 'custom_uiclick',
 'custom_radialmenu': 'custom_radialmenu',
 'custom_impact': 'custom_impact',
 'custom_uiinteraction': 'custom_uiinteraction',
 'custom_aura': 'custom_aura',
 'custom_hacking': 'custom_hacking',
 'custom_shieldlow': 'custom_shieldlow',
 'custom_armorlow': 'custom_armorlow',
 'custom_hulllow': 'custom_hulllow',
 'custom_atmosphere': 'custom_atmosphere',
 'custom_dungeonmusic': 'custom_dungeonmusic',
 'custom_normalmusic': 'custom_normalmusic',
 'custom_warpeffect': 'custom_warpeffect'}
dampeningSettings = {'inactiveSounds_master': 'custom_damp_master',
 'inactiveSounds_music': 'custom_damp_music',
 'inactiveSounds_turrets': 'custom_damp_turrets',
 'inactiveSounds_shield': 'custom_damp_shield',
 'inactiveSounds_armor': 'custom_damp_armor',
 'inactiveSounds_hull': 'custom_damp_hull',
 'inactiveSounds_shipsound': 'custom_damp_shipsound',
 'inactiveSounds_jumpgates': 'custom_damp_jumpgates',
 'inactiveSounds_wormholes': 'custom_damp_wormholes',
 'inactiveSounds_jumping': 'custom_damp_jumping',
 'inactiveSounds_aura': 'custom_damp_aura',
 'inactiveSounds_modules': 'custom_damp_modules',
 'inactiveSounds_explosions': 'custom_damp_explosions',
 'inactiveSounds_warping': 'custom_damp_warping',
 'inactiveSounds_locking': 'custom_damp_locking',
 'inactiveSounds_planets': 'custom_damp_planets',
 'inactiveSounds_impacts': 'custom_damp_impacts',
 'inactiveSounds_deployables': 'custom_damp_deployables',
 'inactiveSounds_boosters': 'custom_damp_boosters',
 'inactiveSounds_pocos': 'custom_damp_pocos',
 'inactiveSounds_stationint': 'custom_damp_stationint',
 'inactiveSounds_stationext': 'custom_damp_stationext',
 'inactiveSounds_atmosphere': 'custom_damp_atmosphere'}
industryLevels = {i:u'set_industry_level_%s_state' % (i,) for i in xrange(6)}
researchLevels = {i:u'set_research_level_%s_state' % (i,) for i in xrange(6)}

class AudioService(service.Service, GameworldAudioMixin):
    __guid__ = 'svc.audio'
    __exportedcalls__ = {'Activate': [],
     'Deactivate': [],
     'GetMasterVolume': [],
     'SetMasterVolume': [],
     'GetUIVolume': [],
     'SetUIVolume': [],
     'GetWorldVolume': [],
     'SetWorldVolume': [],
     'SetMusicVolume': [],
     'GetVoiceVolume': [],
     'SetVoiceVolume': [],
     'MuteSounds': [],
     'UnmuteSounds': [],
     'IsActivated': [],
     'AudioMessage': [],
     'SendUIEvent': [],
     'StartSoundLoop': [],
     'StopSoundLoop': [],
     'GetTurretSuppression': [],
     'SetTurretSuppression': []}
    __startupdependencies__ = ['settings', 'sceneManager']
    __notifyevents__ = ['OnChannelsJoined',
     'OnDamageStateChange',
     'OnCapacitorChange',
     'OnSessionChanged',
     'OnBallparkSetState',
     'OnDogmaItemChange']
    __componentTypes__ = ['audioEmitter']

    def __init__(self):
        service.Service.__init__(self)
        GameworldAudioMixin.__init__(self)
        self.soundLoops = {}
        self.lastLookedAt = None
        self.shipHealthNotifier = ShipHealthNotifier(self.SendWiseEvent)
        self.firstStartup = True
        self.lastSystemID = None

    def Run(self, ms = None):
        """
            Service run method. Acquires the audio2 player objects,
            initializes some internal stuff, and hooks up the
            Windows session change handler.
            
            Also hooks up the Jukebox player object so that we
            receive track-change events from Wise.
            
            ARGUMENTS:
                ms      Legacy. No idea what this does.
        """
        self.active = False
        self.manager = AudioManager(audiomanager.InitializeAudioManager(session.languageID), eveaudio.EVE_COMMON_BANKS)
        self.banksLoaded = False
        enabled = self.AppGetSetting('audioEnabled', 1)
        self.uiPlayer = self.jukeboxPlayer = None
        self.busChannels = {}
        for i in xrange(8):
            self.busChannels[i] = None

        trinity.SetDirectSoundPtr(audio2.GetDirectSoundPtr())
        if self.AppGetSetting('forceEnglishVoice', False):
            io = audio2.AudLowLevelIO(u'res:/Audio/')
            self.manager.manager.config.lowLevelIO = io
        if enabled:
            self.Activate()

    def Stop(self, stream):
        """
            Service halt method. Cleans up the audio2 player objects
            and unhooks the Windows session-change handler.
            
            ARGUMENTS:
                stream      Legacy. No idea what this does.
        """
        self.uiPlayer = None
        self.jukeboxPlayer = None
        if blue.win32 and trinity.device:
            try:
                blue.win32.WTSUnRegisterSessionNotification(trinity.device.GetWindow())
            except:
                sys.exc_clear()

        if uicore.uilib:
            uicore.uilib.SessionChangeHandler = None

    def SetGlobalRTPC(self, rtpcName, value):
        """
            Use this method to set the value of a global RTPC in WWise
            from the application-level audio service.
            
            ARGUMENTS:
                rtpcName        A string containing the RTPC's name.
                value           The value to set the RTPC to.
        """
        if not self.IsActivated():
            return
        audio2.SetGlobalRTPC(unicode(rtpcName), value)

    def Activate(self):
        """
            This method is used by external services to activate the audio
            system. This sets up the user's saved audio preferences and
            attaches an audio2 listener to the camera.
        
            Scatters the OnAudioActivated event.
        """
        self.manager.Enable()
        if self.uiPlayer is None:
            self.uiPlayer = audio2.GetUIPlayer()
        self.active = True
        self.SetMasterVolume(self.GetMasterVolume())
        self.SetUIVolume(self.GetUIVolume())
        self.SetWorldVolume(self.GetWorldVolume())
        self.SetVoiceVolume(self.GetVoiceVolume())
        self._SetAmpVolume(self.GetMusicVolume())
        self.SetTurretSuppression(self.GetTurretSuppression())
        self.SetVoiceCountLimitation(self.GetVoiceCountLimitation())
        if not self.firstStartup:
            sm.GetService('dynamicMusic').dynamicMusicSystem.EnableMusic()
            sm.GetService('dynamicMusic').UpdateDynamicMusic()
        self.firstStartup = False
        try:
            self.SetListener(audio2.GetListener(0))
        except Exception:
            pass

        sm.ScatterEvent('OnAudioActivated')

    def Deactivate(self):
        """
            This method is used by external services to shut down the
            audio system. This SHOULD tell Wise to unload itself or
            otherwise go into standby mode, but that functionality
            does not exist in Audio2 yet.
            
            At the moment, this just mutes Audio2.
            
            Scatters the OnAudioDeactivated event.
        """
        self.manager.Disable()
        sm.GetService('dynamicMusic').dynamicMusicSystem.DisableMusic()
        self.active = False
        sm.ScatterEvent('OnAudioDeactivated')

    def GetAudioBus(self, is3D = False):
        """
            This method opens an audio bus and starts the bussing plugin for piping sounds into WWise.
            
            ARGUMENTS:
                is3D    (defaults to false) A bool that signifies if the sound played will be localized or 2D
        
            RETURNS:
                An audio emitter object that must be retained for the lifetime of the audio bus
                A channel number for the output to be bussed into.
        """
        for outputChannel, emitterWeakRef in self.busChannels.iteritems():
            if emitterWeakRef is None:
                emitter = audio2.AudEmitter('Bus Channel: ' + str(outputChannel))
                if is3D:
                    emitter.SendEvent(unicode('Play_3d_audio_stream_' + str(outputChannel)))
                else:
                    emitter.SendEvent(unicode('Play_2d_audio_stream_' + str(outputChannel)))
                self.busChannels[outputChannel] = weakref.ref(emitter, self.AudioBusDeathCallback)
                return (emitter, outputChannel)

        self.LogError('Bus voice starvation!')
        return (None, -1)

    @funcDeco.CallInNewThread(context='^AudioService::AudioBusDeathCallback')
    def AudioBusDeathCallback(self, audioEmitter):
        """
            This method is called when the audio bus weakref is garbage collected.
            It waits 2 seconds for the sound to fully fade out before freeing the bus to be used.
            It should never be called directly, instead it is called by the weakref callback.
        
            ARGUMENTS:
                audioEmitter    the weakref of the audio bus audio emitter
        """
        blue.synchro.SleepWallclock(2000)
        for outputChannel, emitterWeakRef in self.busChannels.iteritems():
            if emitterWeakRef == audioEmitter:
                self.busChannels[outputChannel] = None

    def SetMasterVolume(self, vol = 1.0, persist = True):
        """
            This method sets the volume of the master bus in Wise,
            overriding all other volume settings.
            
            If Persist is set, it will save the value off to the settings hive.
            
            ARGUMENTS:
                vol     (optional) A floating-point value, 0.0 <= vol <= 1.0
                        This is the proportion of maximum volume to be set.
                        Defaults to 1.0
                        
                persist (optional) A boolean value. If set, the value of vol
                        will be saved to the settings hive.
                        Defaults to True.
        """
        if vol < 0.0 or vol > 1.0:
            raise RuntimeError('Erroneous value received for volume')
        self.SetGlobalRTPC(unicode('volume_master'), vol)
        if persist:
            self.AppSetSetting('masterVolume', vol)

    def GetMasterVolume(self):
        """
            Returns the master volume value from the settings hive.
        
            RETURNS:
                The value for the master volume bus in the settings hive.
        """
        return self.AppGetSetting('masterVolume', 0.4)

    def SetUIVolume(self, vol = 1.0, persist = True):
        """
            This method sets the volume of the UI bus in Wise,
            controlling non-spatialized UI sounds.
            
            If Persist is set, it will save the value off to the settings hive.
            
            ARGUMENTS:
                vol     (optional) A floating-point value, 0.0 <= vol <= 1.0
                        This is the proportion of maximum volume to be set.
                        Defaults to 1.0
                        
                persist (optional) A boolean value. If set, the value of vol
                        will be saved to the settings hive.
                        Defaults to True.
        """
        if vol < 0.0 or vol > 1.0:
            raise RuntimeError('Erroneous value received for volume')
        self.SetGlobalRTPC(unicode('volume_ui'), vol)
        if persist:
            self.AppSetSetting('uiGain', vol)

    def GetUIVolume(self):
        """
            Returns the UI volume value from the settings hive.
        
            RETURNS:
                The value for the UI volume bus in the settings hive.
        """
        return self.AppGetSetting('uiGain', 0.4)

    def SetWorldVolume(self, vol = 1.0, persist = True):
        """
            This method sets the volume of the World bus in Wise,
            controlling spatialized (non-UI) sounds.
            
            If Persist is set, it will save the value off to the settings hive.
            
            ARGUMENTS:
                vol     (optional) A floating-point value, 0.0 <= vol <= 1.0
                        This is the proportion of maximum volume to be set.
                        Defaults to 1.0
                        
                persist (optional) A boolean value. If set, the value of vol
                        will be saved to the settings hive.
                        Defaults to True.
        """
        if vol < 0.0 or vol > 1.0:
            raise RuntimeError('Erroneous value received for volume')
        self.SetGlobalRTPC(unicode('volume_world'), vol)
        if persist:
            self.AppSetSetting('worldVolume', vol)

    def SetCustomValue(self, vol, settingName, persist = True):
        rtpcConfigName = customSoundLevelsSettings.get(settingName)
        if not rtpcConfigName:
            return
        self.SetSoundVolumeBetween0and1(volume=vol, configNameRTPC=rtpcConfigName, configNameAppSetting=settingName, persist=persist)

    def SetSoundVolumeBetween0and1(self, volume, configNameRTPC, configNameAppSetting, persist):
        if volume is None:
            volume = settings.user.audio.Get(configNameAppSetting, 0.5)
        if volume < 0.0 or volume > 1.0:
            raise RuntimeError('Erroneous value received for volume, configName=', configNameAppSetting)
        self.SetGlobalRTPC(unicode(configNameRTPC), volume)
        if persist:
            settings.user.audio.Set(configNameAppSetting, volume)

    def EnableAdvancedSettings(self):
        for eachSettingName in customSoundLevelsSettings.iterkeys():
            self.SetCustomValue(vol=None, settingName=eachSettingName, persist=False)

    def DisableAdvancedSettings(self):
        for eachSettingName in customSoundLevelsSettings.iterkeys():
            self.SetCustomValue(vol=0.5, settingName=eachSettingName, persist=False)

    def LoadUpSavedAdvancedSettings(self):
        for eachSettingName in customSoundLevelsSettings.iterkeys():
            volume = settings.user.audio.Get(eachSettingName, 0.5)
            self.SetCustomValue(vol=volume, settingName=eachSettingName, persist=False)

    def SetDampeningValue(self, settingName, setOn = True):
        audioEvent = dampeningSettings.get(settingName)
        if not audioEvent:
            return
        if setOn:
            audioEvent += '_on'
        else:
            audioEvent += '_off'
        self.SendUIEvent(audioEvent)

    def SetDampeningValueSetting(self, settingName, setOn = True):
        settings.user.audio.Set(settingName, setOn)

    def DisableDampeningValues(self):
        for eachSettingName in dampeningSettings.iterkeys():
            self.SetDampeningValue(settingName=eachSettingName, setOn=False)

    def LoadUpSavedDampeningValues(self):
        for eachSettingName in dampeningSettings.iterkeys():
            setOn = settings.user.audio.Get(eachSettingName, False)
            self.SetDampeningValue(settingName=eachSettingName, setOn=setOn)

    def GetWorldVolume(self):
        """
            Returns the UI volume value from the settings hive.
            
            RETURNS:
                The value for the UI volume bus in the settings hive.
        """
        return self.AppGetSetting('worldVolume', 0.4)

    def SetMusicVolume(self, volume = 1.0, persist = True):
        """
            Sets the volume RTPC for music. This is a direct, low-level method.
            Actual music control should be done via the jukebox service.
            
            ARGUMENTS:
                volume          A float in the range 0 <= f <= 1.
        """
        volume = min(1.0, max(0.0, volume))
        self.SetGlobalRTPC(unicode('volume_music'), volume)
        if persist:
            self.AppSetSetting('eveampGain', volume)

    def SetVoiceVolume(self, vol = 1.0, persist = True):
        """
            This method sets the volume of the UI Voice bus in Wise,
            as well as the EVE Voice volume.
            controlling voice-type sounds originating from the UI.
            This is used for some eve.Message messages and for
            tutorial messages.
        
            If Persist is set, it will save the value off to the settings hive.
        
            ARGUMENTS:
                vol     (optional) A floating-point value, 0.0 <= vol <= 1.0
                        This is the proportion of maximum volume to be set.
                        Defaults to 1.0
        
                persist (optional) A boolean value. If set, the value of vol
                        will be saved to the settings hive.
                        Defaults to True.
        """
        if vol < 0.0 or vol > 1.0:
            raise RuntimeError('Erroneous value received for volume')
        if not self.IsActivated():
            return
        self.SetGlobalRTPC('volume_voice', vol)
        if persist:
            self.AppSetSetting('evevoiceGain', vol)

    def GetVoiceVolume(self):
        """
            Returns the UI & EVE Voice volume value from the settings hive.
        
            RETURNS:
                The value for the UI volume bus in the settings hive.
        """
        return self.AppGetSetting('evevoiceGain', 0.9)

    def _SetAmpVolume(self, volume = 0.25, persist = True):
        """
            Sets the volume of the jukebox.
            ARGUMENTS:
                volume      A floating-point number in the range
                                0 <= f <= 1
                            0.0 is silence, 1.0 is full volume.
                persist     If set to true, then this volume change
                            will be placed in the user's settings hive
                            and persist across client restarts.
        """
        if volume < 0.0 or volume > 1.0:
            raise RuntimeError('Erroneous value received for volume')
        if not self.IsActivated():
            return
        self.SetGlobalRTPC('volume_music', volume)
        if persist:
            self.AppSetSetting('eveampGain', volume)

    def UserSetAmpVolume(self, volume = 0.25, persist = True):
        self._SetAmpVolume(volume, persist)
        sm.GetService('dynamicMusic').MusicVolumeChangedByUser(volume)

    def GetMusicVolume(self):
        """
            Retrieves the volume of the jukebox's music from the settings
            hive.
        
            RETURNS:
                A floating-point number in the range 0 <= f <= 1
                indicating the volume of the jukebox's music.
                Defaults to 0.4 if not set.
        """
        return self.AppGetSetting('eveampGain', 0.25)

    def IsActivated(self):
        """
            Indicates whether the audio service is currently active.
            Note that most methods will trap and silently return if
            the audio service is inactive, so you really don't need
            to use this unless you're the options menu!
            
            RETURNS:
                A boolean value. True if the audio service is active,
                false otherwise.
        """
        return self.active

    def SendEntityEventBySoundID(self, entity, soundID):
        """
        Given an entity and a sound resource ID, tries to look up the audioEmitter component on
        the entity and the event name of the sound through cfg.sounds. If both exist, it calls
        SendEvent on the audio component's emitter object which will play the sound.
        """
        if not entity:
            self.LogError('Trying to play an audio on an entity but got None sent in instead of entity instance')
            return
        if not self.IsActivated():
            self.LogInfo('Audio inactive - skipping sound id', soundID)
            return
        audioEmitterComponent = entity.GetComponent('audioEmitter')
        soundEventName = cfg.sounds.GetIfExists(soundID)
        if audioEmitterComponent and soundEventName:
            if soundEventName.startswith('wise:/'):
                soundEventName = soundEventName[6:]
            audioEmitterComponent.emitter.SendEvent(unicode(soundEventName))
        elif not audioEmitterComponent:
            self.LogError('Trying to play audio', soundID, 'on entity', entity.entityID, 'that does not have an audioEmitter component')
        else:
            self.LogError('Could not find audio resource with ID', soundID)

    def SendEntityEvent(self, entity, event):
        """
        Given an entity and a sound event name, tries to look up the audioEmitter component on
        the entity. If the entity has an audio component it will call SendEvent on the audio 
        component's emitter object which will play the the sound.
        """
        if not entity:
            self.LogError('Trying to play an audio on an entity but got None sent in instead of entity instance')
            return
        if not self.IsActivated():
            self.LogInfo('Audio inactive - skipping sound event', event)
            return
        if event.startswith('wise:/'):
            event = event[6:]
        audioEmitterComponent = entity.GetComponent('audioEmitter')
        if audioEmitterComponent:
            audioEmitterComponent.emitter.SendEvent(unicode(event))
        else:
            self.LogError('Trying to play audio on entity', entity.entityID, 'that does not have an audioEmitter component')

    def SendUIEvent(self, event):
        """
            Helper method that dispatches an event to Wise via the UI 
            source. Event names may be bare or may have 'wise:/'
            preprended to them.
        
            ARGUMENTS:
                event           A string with the event name to send.
        """
        if not self.IsActivated():
            self.LogInfo('Audio inactive - skipping UI event', event)
            return
        if event.startswith('wise:/'):
            event = event[6:]
        self.LogInfo('Sending UI event to WWise:', event)
        self.uiPlayer.SendEvent(unicode(event))

    def SendUIEventByTypeID(self, typeID):
        """ Play the UI sound associated with typeID """
        soundID = cfg.invtypes.Get(typeID).soundID
        if not soundID:
            log.LogException('No soundID assigned to typeID: %s' % typeID)
            return
        soundFile = cfg.sounds.Get(soundID).soundFile
        if not soundFile:
            log.LogException('No soundFile assigned to soundID: %s' % soundID)
            return
        self.SendUIEvent('ui_' + soundFile.replace('wise:/', ''))

    def SetListener(self, listener):
        """
            Application hook. The core service passes down an audio listener,
            which should be attached to the game's camera.
            
            This method must be overridden, or you won't hear any spatialized
            audio!
        
            ARGUMENTS:
                listener            An audio2.EventListener object.
        """
        sm.GetService('sceneManager').GetRegisteredCamera(None, defaultOnActiveCamera=True).audio2Listener = listener
        sm.GetService('cameraClient').SetAudioListener(listener)

    def AppGetSetting(self, setting, default):
        try:
            return settings.public.audio.Get(setting, default)
        except (AttributeError, NameError):
            return default

    def AppSetSetting(self, setting, value):
        try:
            settings.public.audio.Set(setting, value)
        except (AttributeError, NameError):
            pass

    def AudioMessage(self, msg):
        """
            This method plays a sound in Wise that sources from an
            EVE Message.
        
            This method largely remains so that the many places
            using eve.Message do not need to refactor their code to
            be compatible with the new system.
        
            Stacktraces if old sounds are played, so that QA can report
            the old sound as a defect with good logs.
        
            ARGUMENTS:
                msg         The wise message to play. Must start with 'wise:/'
        """
        if not self.IsActivated():
            return
        if msg.audio:
            audiomsg = msg.audio
        else:
            return
        if audiomsg.startswith('wise:/'):
            audiomsg = audiomsg[6:]
            self.SendUIEvent(audiomsg)
        else:
            raise RuntimeError('OLD UI SOUND BEING PLAYED: %s' % msg)

    def StartSoundLoop(self, rootLoopMsg):
        """
            Starts a ref-counted looping message in Wise.
            If the sound is not playing, a reference count is created
            and the given root message is expanded into a standard
            Wise Play event, which is sent to Wise.
        
            If the sound is already playing, we increment the refcount.
        
            Wise handles the actual looping of sounds.
        
            ARGUMENTS:
                rootLoopMsg     The ROOT of a wise message. This is the central
                                part, as messages are formatted prefix_root_suffix.
                                e.g. msg_Beep_play, the root message is Beep.
        
                                Wise must have a play and stop event based on
                                this root message, in the format:
                                    msg_(ROOT)_play & msg_(ROOT)_stop
        """
        if not self.IsActivated():
            return
        try:
            if rootLoopMsg not in self.soundLoops:
                self.LogInfo('StartSoundLoop starting loop with root %s' % rootLoopMsg)
                self.soundLoops[rootLoopMsg] = 1
                self.SendUIEvent('wise:/msg_%s_play' % rootLoopMsg)
            else:
                self.soundLoops[rootLoopMsg] += 1
                self.LogInfo('StartSoundLoop incrementing %s loop to %d' % (rootLoopMsg, self.soundLoops[rootLoopMsg]))
        except:
            self.LogWarn('StartSoundLoop failed - halting loop with root', rootLoopMsg)
            self.SendUIEvent('wise:/msg_%s_stop' % rootLoopMsg)
            sys.exc_clear()

    def StopSoundLoop(self, rootLoopMsg, eventMsg = None):
        """
            Performs refcounted halting of sound loops started with
            StartSoundLoop. If the refcount hits zero, the sound loop's
            stop message is sent to halt the loop. Otherwise,
            the refcount is simply decremented.
        
            For the formatting/definition and content requirements of
            sound loops, see the documentation for StartSoundLoop.
        
            ARGUMENTS:
                rootLoopMsg     The root of a loop wise message. For
                                formatting details, see StartSoundLoop.
                                This is reformatted into msg_(ROOT)_stop
                                before being sent to Wise.
        
                eventMsg        (optional) A one-time event message that
                                is always sent to Wise, regardless of
                                whether the loop stops or not.
        """
        if rootLoopMsg not in self.soundLoops:
            self.LogInfo('StopSoundLoop told to halt', rootLoopMsg, 'but that message is not playing!')
            return
        try:
            self.soundLoops[rootLoopMsg] -= 1
            if self.soundLoops[rootLoopMsg] <= 0:
                self.LogInfo('StopSoundLoop halting message with root', rootLoopMsg)
                del self.soundLoops[rootLoopMsg]
                self.SendUIEvent('wise:/msg_%s_stop' % rootLoopMsg)
            else:
                self.LogInfo('StopSoundLoop decremented count of loop with root %s to %d' % (rootLoopMsg, self.soundLoops[rootLoopMsg]))
        except:
            self.LogWarn('StopSoundLoop failed due to an exception - forcibly halting', rootLoopMsg)
            self.SendUIEvent('wise:/msg_%s_stop' % rootLoopMsg)
            sys.exc_clear()

        if eventMsg is not None:
            self.SendUIEvent(eventMsg)

    def GetTurretSuppression(self):
        """
            Retrieves the turret-sound-suppression flag from the
            settings hive.
        
            RETURNS:
                A integer value. If nonzero, turret sounds should be suppressed.
        """
        return self.AppGetSetting('suppressTurret', 0)

    def SetTurretSuppression(self, suppress, persist = True):
        """
            Sets the turret-sound-suppression RTPC in WWise.
        
            ARGUMENTS:
                suppress    A boolean indicating whether or not to
                            suppress turret sounds. True = Suppress.
                persist     (Optional) If set to true, persists
                            the value sent to the RTPC into the
                            settings hive. Defaults to true.
        """
        if not self.IsActivated():
            return
        if suppress:
            self.SetGlobalRTPC('turret_muffler', 0.0)
            suppress = 1
        else:
            self.SetGlobalRTPC('turret_muffler', 1.0)
            suppress = 0
        if persist:
            self.AppSetSetting('suppressTurret', suppress)

    def GetVoiceCountLimitation(self):
        """
            Retrieves the voice-limitation flag from the settings hive
        
            :returns: A integer value. If nonzero, voice count should be limited.
        """
        return self.AppGetSetting('limitVoiceCount', 0)

    def SetVoiceCountLimitation(self, limit, persist = True):
        """
            Sets the voice count limitation RTPC in WWise
        
            :param limit:       A boolean indicating whether or not to
                                limit voice count. True = limit.
            :param persist:     (Optional) If set to true, persists
                                the value sent to the RTPC into the
                                settings hive. Defaults to true.
        """
        if not self.IsActivated():
            return
        if limit:
            self.SetGlobalRTPC('voice_count_limit', 1.0)
            limit = 1
        else:
            self.SetGlobalRTPC('voice_count_limit', 0.0)
            limit = 0
        if persist:
            self.AppSetSetting('limitVoiceCount', limit)

    def MuteSounds(self):
        self.SetMasterVolume(0.0, False)

    def UnmuteSounds(self):
        self.SetMasterVolume(self.GetMasterVolume(), False)

    def SendWiseEvent(self, event):
        """
        A wrapper around the SendUIEvent since the name of the function can be misleading, we are only using the
        UI emitter to send wwise command data not dirctly connected to the UI sound or UI sound behavoir.
        Blue should provide a generic event
        """
        if event:
            self.SendUIEvent(event)

    def OnChannelsJoined(self, channelIDs):
        """
            Is an notify event that happens each time you join a chat channel so we can evalutate the population
            at your current location to feed that state into the sound engine.
        
        :param channelIDs: A list of channel IDs
        """
        if not session.stationid2:
            return
        if (('solarsystemid2', session.solarsystemid2),) in channelIDs:
            pilotsInChannel = eveaudio.GetPilotsInSystem()
            self.SetHangarPopulationSwitch(pilotsInChannel)

    def SetHangarPopulationSwitch(self, pilotsInChannel):
        """
            Sets the population switch as used in the hangar atmosphere sounds.
        :param pilotsInChannel: number of pilots in the channel (in the solarsystem)
        """
        self.SendUIEvent(eveaudio.GetHangarPopulationSwitch(pilotsInChannel))

    def SwapBanks(self, banks):
        """
        Forwards SwapBanks to the audiomanger
        
        :param banks: A list of banks that should be loaded in favout of the previously loaded optional banks.
        see further in eveaudio.audiomanager.SwapBanks()
        """
        self.manager.SwapBanks(banks)

    def OnDamageStateChange(self, *args, **kwargs):
        return self.shipHealthNotifier.OnDamageStateChange(*args, **kwargs)

    def OnCapacitorChange(self, *args, **kwargs):
        return self.shipHealthNotifier.OnCapacitorChange(*args, **kwargs)

    def OnSessionChanged(self, isRemote, session, change):
        if session.stationid2:
            self.SwapBanks(eveaudio.EVE_INCARNA_BANKS)
            eveaudio.SetTheraSystemHangarSwitch(session.solarsystemid2, self.uiPlayer)
        elif session.solarsystemid2:
            self.SwapBanks(eveaudio.EVE_SPACE_BANKS)
        if 'userid' in change and session.userid:
            uicore.event.RegisterForTriuiEvents(uiconst.UI_ACTIVE, self.CheckAppFocus)
            if settings.user.audio.Get('soundLevel_advancedSettings', False):
                self.LoadUpSavedAdvancedSettings()
            if settings.user.audio.Get('inactiveSounds_advancedSettings', False) and not uicore.registry.GetFocus():
                self.LoadUpSavedDampeningValues()
        self.lastSystemID = eveaudio.PlaySystemSpecificEntrySound(self.lastSystemID, session.solarsystemid2, self.uiPlayer)

    def CheckAppFocus(self, wnd, msgID, vkey):
        if not settings.user.audio.Get('inactiveSounds_advancedSettings', False):
            return 1
        focused = vkey[0]
        if focused in (1, 2):
            self.DisableDampeningValues()
        else:
            self.LoadUpSavedDampeningValues()
        return 1

    def OnBallparkSetState(self):
        self.SetResearchAndIndustryLevel()

    def SetResearchAndIndustryLevel(self):
        ballpark = sm.GetService('michelle').GetBallpark()
        if ballpark is None:
            return
        industryLevel = ballpark.industryLevel
        researchLevel = ballpark.researchLevel
        if industryLevel in industryLevels.keys():
            self.SendUIEvent(industryLevels.get(industryLevel))
        if researchLevel in researchLevels.keys():
            self.SendUIEvent(researchLevels.get(researchLevel))

    def OnDogmaItemChange(self, *args, **kwargs):
        if session.solarsystemid:
            shipid = session.shipid
            ship = sm.StartService('godma').GetItem(shipid)
            if shipid and ship:
                cargoHoldState = ship.GetCapacity()
                return self.shipHealthNotifier.OnCargoHoldChange(shipid, cargoHoldState, *args, **kwargs)
