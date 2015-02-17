#Embedded file name: carbon/client/script/zaction\genericProcs.py
import service
import GameWorld
import uthread
from carbon.common.script.zaction.zactionCommon import ProcTypeDef, ProcPropertyTypeDef

class GenericClientProcSvc(service.Service):
    __guid__ = 'svc.genericProcClient'
    __machoresolve__ = 'location'

    def Run(self, *args):
        service.Service.Run(self, *args)
        GameWorld.RegisterPythonActionProc('SetClientPrefInt', self._SetClientPrefInt, ('Name', 'Value'))
        GameWorld.RegisterPythonActionProc('ClientPrefEqualsInt', self._ClientPrefEqualsInt, ('Name', 'Value'))
        GameWorld.RegisterPythonActionProc('SetClientPrefBool', self._SetClientPrefBool, ('Name', 'Value'))
        GameWorld.RegisterPythonActionProc('ClientPrefEqualsBool', self._ClientPrefEqualsBool, ('Name', 'Value'))
        GameWorld.RegisterPythonActionProc('SetCharacterPrefBool', self._SetCharacterPrefBool, ('Name', 'Value'))
        GameWorld.RegisterPythonActionProc('CharacterPrefEqualsBool', self._CharacterPrefEqualsBool, ('Name', 'Value'))

    def _SetClientPrefInt(self, Name, Value):
        uthread.worker('_SetClientPrefInt', self._SetClientPrefIntTasklet, Name, Value)
        return True

    def _SetClientPrefIntTasklet(self, Name, Value):
        prefs.SetValue(Name, Value)

    def _ClientPrefEqualsInt(self, Name, Value):
        prefVal = prefs.GetValue(Name, None)
        if prefVal is None:
            return False
        return prefVal == Value

    def _SetClientPrefBool(self, Name, Value):
        uthread.worker('_SetClientPrefBool', self._SetClientPrefBoolTasklet, Name, Value)
        return True

    def _SetClientPrefBoolTasklet(self, Name, Value):
        prefs.SetValue(Name, Value)

    def _ClientPrefEqualsBool(self, Name, Value):
        prefVal = prefs.GetValue(Name, None)
        if prefVal is None:
            return False
        return prefVal == Value

    def _SetCharacterPrefBool(self, Name, Value):
        uthread.worker('_SetCharacterPrefBool', self._SetCharacterPrefBoolTasklet, Name, Value)
        return True

    def _SetCharacterPrefBoolTasklet(self, Name, Value):
        settings.char.zaction.Set(Name, Value)

    def _CharacterPrefEqualsBool(self, Name, Value):
        prefVal = settings.char.zaction.Get(Name, None)
        if prefVal is None:
            return False
        return prefVal == Value


SetClientPrefInt = ProcTypeDef(isMaster=True, procCategory='Client Preferences', properties=[ProcPropertyTypeDef('Name', 'S', userDataType=None, isPrivate=True, displayName='Pref Name'), ProcPropertyTypeDef('Value', 'I', userDataType=None, isPrivate=True, displayName='Value')], description='Sets a client preference (integer value).')
ClientPrefEqualsInt = ProcTypeDef(isMaster=True, procCategory='Client Preferences', isConditional=True, properties=[ProcPropertyTypeDef('Name', 'S', userDataType=None, isPrivate=True, displayName='Pref Name'), ProcPropertyTypeDef('Value', 'I', userDataType=None, isPrivate=True, displayName='Value')], description='Tests a client pref against a value (integer).')
SetClientPrefBool = ProcTypeDef(isMaster=True, procCategory='Client Preferences', properties=[ProcPropertyTypeDef('Name', 'S', userDataType=None, isPrivate=True, displayName='Pref Name'), ProcPropertyTypeDef('Value', 'B', userDataType=None, isPrivate=True, displayName='Value')], description='Sets a client preference (boolean value).')
ClientPrefEqualsBool = ProcTypeDef(isMaster=True, procCategory='Client Preferences', isConditional=True, properties=[ProcPropertyTypeDef('Name', 'S', userDataType=None, isPrivate=True, displayName='Pref Name'), ProcPropertyTypeDef('Value', 'B', userDataType=None, isPrivate=True, displayName='Value')], description='Tests a client pref against a value (boolean).')
SetCharacterPrefBool = ProcTypeDef(isMaster=True, procCategory='Client Preferences', properties=[ProcPropertyTypeDef('Name', 'S', userDataType=None, isPrivate=True, displayName='Pref Name'), ProcPropertyTypeDef('Value', 'B', userDataType=None, isPrivate=True, displayName='Value')], description='Sets a character preference (boolean value).')
CharacterPrefEqualsBool = ProcTypeDef(isMaster=True, procCategory='Client Preferences', isConditional=True, properties=[ProcPropertyTypeDef('Name', 'S', userDataType=None, isPrivate=True, displayName='Pref Name'), ProcPropertyTypeDef('Value', 'B', userDataType=None, isPrivate=True, displayName='Value')], description='Tests a character pref against a value (boolean).')
exports = {'actionProcTypes.SetClientPrefInt': SetClientPrefInt,
 'actionProcTypes.ClientPrefEqualsInt': ClientPrefEqualsInt,
 'actionProcTypes.SetClientPrefBool': SetClientPrefBool,
 'actionProcTypes.ClientPrefEqualsBool': ClientPrefEqualsBool,
 'actionProcTypes.SetCharacterPrefBool': SetCharacterPrefBool,
 'actionProcTypes.CharacterPrefEqualsBool': CharacterPrefEqualsBool}
