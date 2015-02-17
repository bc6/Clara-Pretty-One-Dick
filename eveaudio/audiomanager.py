#Embedded file name: eveaudio\audiomanager.py
import audio2
import blue
import remotefilecache
import uthread2
from eveaudio import LANGUAGE_ID_TO_BANK
import logging
L = logging.getLogger(__name__)

class AudioManager(object):
    """Wraps an `audio2.AudManager` so the state of banks can be better managed.
    
    Banks are added to the list of active banks and loaded to memory if the manager is enabled
    using the 'SwapBanks' function. If the manager is disabled, then 'SwapBanks' will
    just add the name of the bank to the list of active banks that will be loaded
    into memory the next time manager is enabled.
    
    :type audio2Manager: audio2.AudManager
    :param banksToKeepActive: Banks to keep active when other banks are swapped.
    """

    def __init__(self, audio2Manager, banksToKeepActive):
        """
        Takes in an audio2 AudManager and a list of banks that should be loaded
        
        :type audio2Manager: audio2.AudManager
        :param audio2Manager: An instance of audio2.AudManager
        :type banksToKeepActive: list()
        :param banksToKeepActive: A list of banks that should be loaded at all times.
        """
        self.manager = audio2Manager
        self.defaultBanks = banksToKeepActive
        uthread2.StartTasklet(self.LoadDefaultBanks)

    def LoadDefaultBanks(self):
        prefetch = set()
        for bank in self.defaultBanks:
            filename = 'res:/Audio/' + bank
            if blue.paths.exists(filename) and not blue.paths.FileExistsLocally(filename):
                prefetch.add(filename)

        remotefilecache.prefetch_files(prefetch)
        map(self.manager.LoadBank, self.defaultBanks)

    def LoadedBanks(self):
        """Returns the names of all banks loaded into memory."""
        return self.manager.GetLoadedSoundBanks()

    def Disable(self):
        """
        Disables the audio manager, and unloads all sound banks from memory.
        """
        self.manager.SetEnabled(False)

    def Enable(self):
        """
        Enables the audio manager and loads all banks to memory.
        
        Even though the manager has been disabled and all banks unloaded from memory,
        all banks that have been swapped during the disabled time will load correctly
        to memory as the manager maintains an active list of banks that should be
        loaded.
        """
        self.manager.SetEnabled(True)

    def SwapBanks(self, banks):
        """
        Takes in a list of banks, compares them to the list that has already been loaded,
        unloads banks that are no longer needed and loads the banks that are needed.
        It never unloads the common banks that are defined in the constructor
        
        :type banks: list()
        :param banks: A list of banks what should be loaded at this time, should not include common banks.
        """
        loadedBanks = self.LoadedBanks()
        self._UnloadUnusedBanks(banks, loadedBanks)
        self._LoadNeededBanks(banks, loadedBanks)

    def _UnloadUnusedBanks(self, banks, loadedBanks):
        """
        Compairs the loaded banks, and banks to be loaded, excluding the common banks, and unloads all
        uneccesary banks.
        
        :type banks: list()
        :param banks: A list of banks to be loaded
        :type loadedBanks: list()
        :param loadedBanks: A list of banks that are currenty loaded
        """
        defaultsExcluded = set(loadedBanks).difference(self.defaultBanks)
        banksToUnload = defaultsExcluded.difference(banks)
        for each in banksToUnload:
            L.debug('Unloading %s' % each)
            self.manager.UnloadBank(each)
            uthread2.Yield()

    def _LoadNeededBanks(self, banks, loadedBanks):
        """
        Compairs the banks that are already loaded and loads only the banks that aren't already in the
        loaded banks list.
        
        :type banks: list()
        :param banks: a list of banks to be loaded
        :type loadedBanks: list()
        :param loadedBanks: A list of banks currently loaded
        :return:
        """
        banksToLoad = set(banks).difference(loadedBanks)
        for each in banksToLoad:
            L.debug('Loading %s' % each)
            self.manager.LoadBank(each)
            uthread2.Yield()


def InitializeAudioManager(languageID):
    manager = audio2.GetManager()
    io = audio2.AudLowLevelIO(u'res:/Audio/', LANGUAGE_ID_TO_BANK.get(languageID, u''))
    initConf = audio2.AudConfig()
    initConf.lowLevelIO = io
    initConf.numRefillsInVoice = 8
    initConf.asyncFileOpen = True
    manager.config = initConf
    return manager
