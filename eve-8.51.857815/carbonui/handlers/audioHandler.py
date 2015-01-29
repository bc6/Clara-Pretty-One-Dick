#Embedded file name: carbonui/handlers\audioHandler.py
__author__ = 'fridrik'

class AudioHandler(object):
    """
    Dumb audio handler to eat up carbonui audio requests if its not running under game client
    """

    def StopSoundLoop(self, *args, **kwds):
        print 'Unhandled audio.StopSoundLoop', args, kwds

    def GetAudioBus(self, *args, **kwds):
        print 'Unhandled audio.GetAudioBus', args, kwds
        return (None, None)

    def Activate(self, *args, **kwds):
        print 'Unhandled audio.Activate', args, kwds

    def Deactivate(self, *args, **kwds):
        print 'Unhandled audio.Deactivate', args, kwds
