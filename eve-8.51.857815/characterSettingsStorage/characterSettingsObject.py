#Embedded file name: characterSettingsStorage\characterSettingsObject.py
"""
This file contains a class that allows you to easily keep track of character settings that are stored on the server.
It will load settings from a yamls string, and can return you the yaml string to store on the server.
This class has 2 dictionaries, lists and singleValues.
The values in the lists dictionaries are lists, but the values in the singleValues dictionary are, well, singleValues
such as 5 or True.
The lists in the list dictionary are always sorted from lowest to highest so list can be easily compared.

This class can be easily extended to have "dictionaries" dictionary too, but yaml can't handle defaultdict or sets.

Exmpla of data in this class:

    allSettings: {
        "lists": {"settingKey1": [1,2], "anotherSettingKey": [3,4]}
        "singleValues": {"isOn": True, "bestNumber": 5}
    }
"""
import yaml

class CharacterSettingsObject:

    def __init__(self, yamlString):
        self.allSettings = self.UploadSettingsFromYamlString(yamlString)
        self.EnsureSettingsAreValid()
        self.SortValueLists(self.allSettings['lists'])

    def EnsureSettingsAreValid(self):
        for settingType in ('lists', 'singleValues'):
            if settingType not in self.allSettings:
                self.allSettings[settingType] = {}

    def UploadSettingsFromYamlString(self, yamlString):
        if yamlString:
            self.allSettings = yaml.load(yamlString, Loader=yaml.CLoader)
            self.EnsureSettingsAreValid()
            self.SortValueLists(self.GetSettingLists())
        else:
            self.allSettings = {'lists': {},
             'singleValues': {}}
        self.EnsureSettingsAreValid()
        return self.allSettings

    def GetYamlStringForServer(self):
        yamlString = yaml.safe_dump(self.allSettings)
        return yamlString

    def IsSaveNeeded(self, newSettingDict):
        settingLists = self.GetSettingLists()
        self.SortValueLists(newSettingDict.get('lists', {}))
        for settingKey, settingValue in newSettingDict.get('lists', {}).iteritems():
            if settingLists.get(settingKey, []) != settingValue:
                return True

        singleValues = self.GetSettingSingleValues()
        for settingKey, settingValue in newSettingDict.get('singleValues', {}).iteritems():
            if singleValues.get(settingKey, None) != settingValue:
                return True

        return False

    def UpdateSettings(self, newSettingsDict):
        self.UpdateListSettings(newSettingsDict.get('lists'))
        self.UpdateSingleValueSettings(newSettingsDict.get('singleValues'))

    def GetSettingLists(self):
        return self.allSettings.get('lists', {})

    def GetListForSettingKey(self, settingsKey):
        values = self.GetSettingLists().get(settingsKey, [])
        return values

    def IsValueStoredInList(self, settingKey, checkValue):
        values = self.GetListForSettingKey(settingKey)
        return checkValue in values

    def UpdateListSettings(self, newListSettingDict):
        settingLists = self.GetSettingLists()
        for settingName, settingValue in newListSettingDict.iteritems():
            settingLists[settingName] = settingValue

        self.SortValueLists(settingLists)

    def UpdateSettingListWithNewValues(self, settingName, values):
        self.GetSettingLists()[settingName] = values[:]

    def CreateListSettingIfNeeded(self, settingKey):
        settingLists = self.GetSettingLists()
        if settingKey not in settingLists:
            settingLists[settingKey] = []

    def AddValueToListSetting(self, settingName, newValue):
        self.CreateListSettingIfNeeded(settingName)
        settingLists = self.GetSettingLists()
        if newValue not in settingLists.get(settingName, []):
            settingLists[settingName].append(newValue)
            self.SortValueLists(settingLists)

    def RemoveValueFromListSetting(self, settingName, value):
        settingLists = self.GetSettingLists()
        if value in settingLists.get(settingName, []):
            settingLists[settingName].remove(value)

    def SortValueLists(self, settingLists):
        for valueList in settingLists.itervalues():
            valueList.sort()

        return settingLists

    def GetSettingSingleValues(self):
        return self.allSettings.get('singleValues', {})

    def GetSingleValue(self, settingKey, defaultValue):
        return self.GetSettingSingleValues().get(settingKey, defaultValue)

    def SetSingleValue(self, settingKey, newValue):
        singleValues = self.GetSettingSingleValues()
        singleValues[settingKey] = newValue

    def UpdateSingleValueSettings(self, newSingleValueSettingDict):
        singleValues = self.GetSettingSingleValues()
        for settingName, settingValue in newSingleValueSettingDict.iteritems():
            singleValues[settingName] = settingValue
