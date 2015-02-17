#Embedded file name: eveaudio\audioapp.py
"""Test application for using audio in stand-alone Python environment.

Putting this here for Snorri.
"""
import logging
import binbootstrapper
binbootstrapper.update_binaries(__file__, binbootstrapper.DLL_AUDIO, *binbootstrapper.DLLS_GRAPHICS)
from binbootstrapper.trinityapp import TrinityApp
import audio2
import blue

def main():
    app = TrinityApp.instance()
    manager = audio2.GetManager()
    uiplayer = audio2.GetUIPlayer()

    def init():
        aPath = blue.paths.ResolvePath(u'res:/Audio')
        print 'aPath:', aPath
        io = audio2.AudLowLevelIO(aPath, u'')
        initConf = audio2.AudConfig()
        initConf.lowLevelIO = io
        initConf.numRefillsInVoice = 8
        initConf.asyncFileOpen = True
        manager.config = initConf
        manager.SetEnabled(True)

    init()

    def loadbanks():
        manager.LoadBank(u'Init.bnk')
        manager.LoadBank(u'Interface.bnk')

    loadbanks()

    def maxVolume():
        audio2.SetGlobalRTPC(u'volume_master', 1.0)
        audio2.SetGlobalRTPC(u'volume_ui', 1.0)

    maxVolume()

    def onevent(*_):
        print 'SENDING'
        uiplayer.SendEvent(u'msg_CCPrevious_play')
        print 'SENT'

    app.mouse_moved.Connect(onevent)
    app.exec_()


if __name__ == '__main__':
    logging.basicConfig()
    print 'starting audio'
    main()
    print 'ran successfully'
