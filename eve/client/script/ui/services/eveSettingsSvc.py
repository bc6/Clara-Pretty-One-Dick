#Embedded file name: eve/client/script/ui/services\eveSettingsSvc.py
"""
Contains an EVE agnostic service for managing saving and loading of settings.
"""
import uicontrols
import log
import svc
import uicls

class EveSettingsSvc(svc.settings):
    __guid__ = 'svc.eveSettings'
    __replaceservice__ = 'settings'

    def LoadSettings(self):
        svc.settings.LoadSettings(self)
        settings.user.CreateGroup('audio')
        settings.user.CreateGroup('overview')
        settings.user.CreateGroup('notifications')
        settings.char.CreateGroup('generic')
        settings.char.CreateGroup('autorepeat')
        settings.char.CreateGroup('autoreload')
        settings.char.CreateGroup('inbox')
        settings.char.CreateGroup('notepad')
        settings.char.CreateGroup('notifications')
        try:
            self.FixListgroupSettings()
        except Exception:
            settings.char.ui.Set('listgroups', {})
            log.LogError('Something happened when fixing listgroups settings and they had to be deleted')

        uicontrols.Window.ValidateSettings()
        return settings

    def FixListgroupSettings(self):
        """"
            we have to change the settings for the listgroups because the list of items of subgroups/entries
            of a group cannot be called 'items' anymore (conflicts with the items() of dictionaries)
            This code should be removed when we think everyone has updated settings
        """
        if not session.charid:
            return
        if settings.char.ui.Get('listgroupSettingsUpdated', 0):
            return
        for key, value in settings.char.ui.Get('listgroups', {}).iteritems():
            for key2, value2 in value.iteritems():
                items = value2.pop('items', None)
                if items is not None:
                    value2['groupItems'] = items

        settings.char.ui.Set('listgroupSettingsUpdated', 1)
