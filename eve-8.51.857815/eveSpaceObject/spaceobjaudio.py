#Embedded file name: eveSpaceObject\spaceobjaudio.py
"""
Audio stuff for space objects.
Eventually this should be removed as the abstraction between
audio and graphics increases.
This is a step in that direction.
"""
import logging
import audio2
import trinity
from inventorycommon import const
import eveaudio
import shipmode.data as stancedata
L = logging.getLogger(__name__)
__all__ = ['BOOSTER_AUDIO_LOCATOR_NAME',
 'SetupAudioEntity',
 'SendEvent',
 'PlayAmbientAudio',
 'GetBoosterEmitterAndEvent']
BOOSTER_AUDIO_LOCATOR_NAME = 'locator_audio_booster'
ship_stance_events = {stancedata.shipStanceDefense: {stancedata.shipStanceSpeed: 'confessor_animation1_2_play',
                                stancedata.shipStanceSniper: 'confessor_animation1_3_play'},
 stancedata.shipStanceSpeed: {stancedata.shipStanceDefense: 'confessor_animation2_1_play',
                              stancedata.shipStanceSniper: 'confessor_animation2_3_play'},
 stancedata.shipStanceSniper: {stancedata.shipStanceDefense: 'confessor_animation3_1_play',
                               stancedata.shipStanceSpeed: 'confessor_animation3_2_play'}}

def SetupAudioEntity(model):
    """
    Creates a generalized audio emitter that objects can use to play random
    audio events on a space object.
    
    :return: AudEmitter
    :raises: AttributeError if model does not support observers.
    """
    triObserver = trinity.TriObserverLocal()
    result = audio2.AudEmitter('spaceObject_%s_general' % id(model))
    triObserver.observer = result
    model.observers.append(triObserver)
    return result


def SendEvent(audEntity, eventName):
    """Helper for calling SendEvent on an AudEmitter.
    
    Will trip off 'wise:/' from eventName,
    cast it to unicode,
    and log info.
    """
    if eventName.startswith('wise:/'):
        eventName = eventName[6:]
    L.debug('playing audio event %s on emitter %s', eventName, id(audEntity))
    audEntity.SendEvent(unicode(eventName))


def PlayAmbientAudio(audEntity, soundUrl = None):
    """
    Plays a soundUrl on `audioEntity`.
    """
    if soundUrl is not None:
        SendEvent(audEntity, soundUrl)


def GetSoundUrl(slimItem = None, defaultSoundUrl = None):
    """
    Takes in a slimitem and a defaultSoundUrl and decides if to use the sound url found in the
    inventory type database for a given typeID.
    :param slimItem: the slimitem of the spaceobject
    :param defaultSoundUrl: a default sound to be used if no typeID sound is found.
    :return: the sound url
    """
    soundUrl = None
    if slimItem:
        soundUrl = eveaudio.GetSoundUrlForType(slimItem)
    if soundUrl is None:
        soundUrl = defaultSoundUrl
    return soundUrl


def GetBoosterSizeStr(groupID):
    """
    This grouping is take from the bracket manager grouping
    ship groups to parts of wwise audio event string
    """
    boosterMappings = {const.groupCapDrainDrone: 'd',
     const.groupCombatDrone: 'd',
     const.groupElectronicWarfareDrone: 'd',
     const.groupFighterBomber: 'd',
     const.groupFighterDrone: 'd',
     const.groupLogisticDrone: 'd',
     const.groupMiningDrone: 'd',
     const.groupProximityDrone: 'd',
     const.groupRepairDrone: 'd',
     const.groupSalvageDrone: 'd',
     const.groupStasisWebifyingDrone: 'd',
     const.groupUnanchoringDrone: 'd',
     const.groupWarpScramblingDrone: 'd',
     const.groupCapsule: 'f',
     const.groupRookieship: 'f',
     const.groupFrigate: 'f',
     const.groupShuttle: 'f',
     const.groupAssaultShip: 'f',
     const.groupCovertOps: 'f',
     const.groupInterceptor: 'f',
     const.groupStealthBomber: 'f',
     const.groupElectronicAttackShips: 'f',
     const.groupPrototypeExplorationShip: 'f',
     const.groupExpeditionFrigate: 'f',
     const.groupDestroyer: 'c',
     const.groupCruiser: 'c',
     const.groupStrategicCruiser: 'c',
     const.groupAttackBattlecruiser: 'c',
     const.groupBattlecruiser: 'c',
     const.groupInterdictor: 'c',
     const.groupHeavyAssaultShip: 'c',
     const.groupLogistics: 'c',
     const.groupForceReconShip: 'c',
     const.groupCombatReconShip: 'c',
     const.groupCommandShip: 'c',
     const.groupHeavyInterdictors: 'c',
     const.groupMiningBarge: 'c',
     const.groupExhumer: 'c',
     const.groupTacticalDestroyer: 'c',
     const.groupIndustrial: 'bs',
     const.groupIndustrialCommandShip: 'bs',
     const.groupTransportShip: 'bs',
     const.groupBlockadeRunner: 'bs',
     const.groupBattleship: 'bs',
     const.groupEliteBattleship: 'bs',
     const.groupMarauders: 'bs',
     const.groupBlackOps: 'bs',
     const.groupFreighter: 'dr',
     const.groupJumpFreighter: 'dr',
     const.groupDreadnought: 'dr',
     const.groupCarrier: 'dr',
     const.groupSupercarrier: 'dr',
     const.groupCapitalIndustrialShip: 'dr',
     const.groupTitan: 't'}
    return boosterMappings.get(groupID, 'f')


def GetBoosterAudioEventName(sizeStr, boosterSoundName):
    parts = [boosterSoundName, sizeStr, 'play']
    return '_'.join(parts)


def CreateEmitterForBooster(model, isAudioBoosterLocator = lambda n: n.name == BOOSTER_AUDIO_LOCATOR_NAME):
    locs = filter(isAudioBoosterLocator, model.locators)
    if not locs:
        return None
    if len(locs) > 1:
        L.error('Found %s locs, needed 1. Content should be validated against this!', len(locs))
    audLocator = locs[0]
    observer = trinity.TriObserverLocal()
    transform = audLocator.transform
    observer.front = (-transform[2][0], -transform[2][1], -transform[2][2])
    observer.position = (transform[3][0], transform[3][1], transform[3][2])
    emitter = audio2.AudEmitter('ship_%s_booster' % id(model))
    audparam = audio2.AudParameter()
    audparam.name = u'ship_speed'
    emitter.parameters.append(audparam)
    observer.observer = emitter
    model.observers.append(observer)
    model.audioSpeedParameter = audparam
    return emitter


def GetBoosterEmitterAndEvent(model, groupID, boosterSoundName):
    """Returns an AudEmitter created for a booster,
    and the name of the event to play.
    
    **NOTE**: Appends the emitter to the model.observers,
    and sets model.audioSpeedParameter
    
    The logic of how the emitter is set up and how the event name is
    calculated is handled in a bunch of helper functions and like most
    things written like this is too complicated (and inconsequential)
    to explain in a docstring.
    
    :return: (None, None) if model has booster locator.
    :return: (audio2.AudEmitter, str)
    """
    emitter = CreateEmitterForBooster(model)
    if emitter is None:
        return (None, None)
    boosterSize = GetBoosterSizeStr(groupID)
    boosterAudioEvent = GetBoosterAudioEventName(boosterSize, boosterSoundName)
    return (emitter, boosterAudioEvent)


def GetSharedAudioEmitter(eventName):
    """
        Gets an emitter for a given event name if it exists. If emitter does not exist a new
        emitter will be created by the audio2.AudManager.
    :param eventName:
    :return:
    """
    audMan = audio2.GetManager()
    if eventName.startswith('wise:/'):
        eventName = eventName[6:]
    emitter = audMan.GetEmitterForEventName(eventName)
    return emitter


def SetupSharedEmitterForAudioEvent(model, eventName):
    """
    Takes a model and an event and looks into the MultiEvent list of the AudManager to see if the multi emitter
    already exists.
    
    If it exists then it gets the emitter and attaches it to a TriObserverLocal and adds it to the
    observer list of the model.
    
    If there is no emitter found it will create a new emitter and attach that to the TriObserverLocal and add that
    to the observer list.
    :param model: A SpaceObject that has to have an observers list
    :param eventName: A string containing the name of the event that will be sent to the emitter upon creation.
    """
    triObserver = trinity.TriObserverLocal()
    emitter = GetSharedAudioEmitter(eventName)
    triObserver.observer = emitter
    model.observers.append(triObserver)


def PlayStateChangeAudio(stanceID, lastStanceID, audioEntity):
    audioEvent = ship_stance_events.get(lastStanceID).get(stanceID)
    if audioEvent is not None and audioEntity is not None:
        audioEntity.SendEvent(audioEvent)
