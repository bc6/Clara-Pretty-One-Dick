#Embedded file name: eve/client/script/ui/services\characterSettingsSvc.py
import service

class CharacterSettingsSvc(service.Service):
    """
    Manipulates characer settings that are persisted in the DB.
    """
    __guid__ = 'svc.characterSettings'
    __update_on_reload__ = 1

    def Run(self, *args):
        self.settings = {}
        self.charMgr = session.ConnectToRemoteService('charMgr')
        self.settings = self.charMgr.GetCharacterSettings()

    def Get(self, settingKey):
        try:
            return self.settings[settingKey]
        except KeyError:
            return None

    def Save(self, settingKey, value):
        if value is None or value == '':
            self.Delete(settingKey)
        else:
            if len(value) > 102400:
                raise RuntimeError("We don't want to send too large character settings to the server", settingKey, len(value))
            self.charMgr.SaveCharacterSetting(settingKey, value)
            self.settings[settingKey] = value

    def Delete(self, settingKey):
        if settingKey in self.settings:
            self.charMgr.DeleteCharacterSetting(settingKey)
            del self.settings[settingKey]
