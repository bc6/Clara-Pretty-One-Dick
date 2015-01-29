#Embedded file name: carbon/client/script/environment\AudioUtil.py
"""
    Some helper stuff for svc.audio and svc.vivox
    TODO: Move more stuff here from audioService
"""

def CheckAudioFileForEnglish(audioPath):
    if settings.user.ui.Get('forceEnglishVoice', False):
        audioPath = audioPath[:-3] + 'EN.' + audioPath[-3:]
    return audioPath


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('audioUtil', locals())
