#Embedded file name: eve/client/script/util\eveDebug.py
"""
Stuff that is meant to be used during development, not in checked-in code.
hooks for code that resides in the core folder
"""

def GetCharacterName(o = None):
    if o is not None:
        return cfg.eveowners.Get(o.charID).name
    elif eve.session.charid:
        return cfg.eveowners.Get(eve.session.charid).name
    else:
        return 'no name'


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('dbg', locals())
