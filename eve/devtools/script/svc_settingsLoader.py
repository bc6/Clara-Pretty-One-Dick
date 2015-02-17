#Embedded file name: eve/devtools/script\svc_settingsLoader.py
import uix
import carbonui.const as uiconst
import yaml
import os
import appUtils
from service import *

class SettingsLoaderSvc(Service):
    __guid__ = 'svc.settingsLoader'

    def Run(self, *args):
        self.exportActive = False

    def Load(self):
        ret = eve.Message('CustomWarning', {'header': 'Load Settings',
         'warning': 'Note that you have to restart after loading new settings'}, uiconst.OKCANCEL)
        if ret == uiconst.ID_CANCEL:
            return
        path = settings.public.ui.Get('LoadSettingsPath', None)
        selection = uix.GetFileDialog(path=path, fileExtensions=['yaml'], multiSelect=False, selectionType=uix.SEL_FILES)
        if selection is None or len(selection.files) < 1 or selection.files[0] == '':
            return
        fileName = selection.files[0]
        folder = '\\'.join(fileName.split('\\')[:-1])
        save = eve.Message('CustomQuestion', {'header': 'Save Current Settings?',
         'question': 'Do you want to save your current settings?'}, uiconst.YESNO)
        if save == uiconst.ID_YES:
            self.SaveCurrentSettings(folder)
        self.LoadSettings(fileName)
        settings.public.ui.Set('LoadSettingsPath', folder)
        appUtils.Reboot('Settings loaded')

    def Export(self):
        path = settings.public.ui.Get('LoadSettingsPath', None)
        selection = uix.GetFileDialog(path=path, multiSelect=False, selectionType=uix.SEL_FOLDERS)
        if selection is None or len(selection.folders) < 1 or selection.folders[0] == '':
            return
        folder = selection.folders[0]
        self.SaveCurrentSettings(folder)
        settings.public.ui.Set('LoadSettingsPath', folder)

    def SaveCurrentSettings(self, folder):
        allSettings = {}
        for settingsType in ('public', 'user', 'char'):
            allSettings[settingsType] = getattr(settings, settingsType).datastore

        data = yaml.dump(allSettings)
        charName = cfg.eveowners.Get(session.charid).name
        maxIndex = -1
        for file in os.listdir(folder):
            if file.startswith(charName) and file.endswith('.yaml'):
                indexChar = file[len(charName)]
                try:
                    index = int(indexChar)
                    maxIndex = max(maxIndex, index)
                except ValueError:
                    maxIndex = 0

        if maxIndex > -1:
            append = str(maxIndex + 1)
        else:
            append = ''
        backupFile = folder + '\\' + charName + append + '.yaml'
        with open(backupFile, 'w') as f:
            f.write(data)
        eve.Message('CustomInfo', {'info': 'Current settings saved as ' + backupFile})

    def LoadSettings(self, fileName):
        with open(fileName, 'r') as f:
            data = yaml.load(f)
            settings.public.datastore = data['public']
            settings.user.datastore = data['user']
            settings.char.datastore = data['char']
            settings.public.FlagDirty()
            settings.user.FlagDirty()
            settings.char.FlagDirty()
        sm.GetService('settings').SaveSettings()
