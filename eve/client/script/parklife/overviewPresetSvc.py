#Embedded file name: eve/client/script/parklife\overviewPresetSvc.py
from service import Service
import util
import form
import uiutil
import localization
import carbonui.const as uiconst
import yaml
import state
from overviewPresets.overviewPresetUtil import EncodeKeyInDict, DecodeKeyInDict, GetDeterministicListFromDict, IsPresetTheSame, GetDictFromList, ReplaceInnerListsWithDicts, ReorderList, GetOrderedListFromDict
import log
import blue
from overviewPresets.overviewPresetUtil import MAX_TAB_NUM
DEFAULT_PRESET_NAME = 'default'

class OverviewPresetSvc(Service):
    __guid__ = 'svc.overviewPresetSvc'
    __displayName__ = 'Overview Preset Service'
    __serviceName__ = 'This service handles overview presets'
    __update_on_reload__ = 1

    def Run(self, *args):
        Service.Run(self, *args)
        self.isLoaded = False
        self.configNamesAndDefaults = None
        self.cachedPresetsFromServer = {}
        self.LoadPresetsFromUserSettings()
        self.activeOverviewPreset = settings.user.overview.Get('activeOverviewPreset', DEFAULT_PRESET_NAME)
        self.activeBracketPreset = None
        self.AddDefaultPresetsToAllPresets()
        self.StorePresetsInSettings()

    def AddDefaultPresetsToAllPresets(self):
        for defaultOverviewName in self.GetDefaultOverviewNameList():
            groups = self.GetDefaultOverviewGroups(defaultOverviewName)
            groups.sort()
            self.allPresets[defaultOverviewName] = {'groups': groups}

    def LoadPresetsFromUserSettings(self):
        try:
            if settings.user.overview.Get('overviewPresets', None) is not None:
                oldPresets = settings.user.overview.Get('overviewPresets', {}).copy()
                settings.user.overview.Set('oldBackup_overviewPresets', oldPresets.copy())
                for presetKey, presetValue in oldPresets.iteritems():
                    presetValue.pop('ewarFilters', None)

                settings.user.overview.Delete('overviewPresets')
            else:
                oldPresets = {}
        except Exception as e:
            log.LogTraceback('Error when migrating overview presets, e = %s' % e)
            settings.user.overview.Delete('overviewPresets')
            oldPresets = {}

        self.allPresets = settings.user.overview.Get('overviewProfilePresets', oldPresets)
        self.unsavedPresets = settings.user.overview.Get('overviewProfilePresets_notSaved', {})
        self.ReorderPresets(self.allPresets)
        self.ReorderPresets(self.unsavedPresets)

    def ReorderPresets(self, presetDict):
        """
            reordering the lists in the dict in place
        """
        try:
            for presetKey, presetValue in presetDict.iteritems():
                ReorderList(presetValue, ('groups', 'filteredStates', 'alwaysShownStates'))

        except Exception as e:
            oldPresets = settings.user.overview.Get('oldBackup_overviewPresets', {})
            log.LogError('Error when reordering presets, e = ', e, oldPresets)
            presetDict.clear()

    def LoadDataIfNeeded(self):
        if not self.isLoaded:
            self.defaultOverviews = dict()
            if hasattr(cfg, 'overviewDefaults') and hasattr(cfg.overviewDefaults, 'data'):
                for key in cfg.overviewDefaults.data:
                    row = cfg.overviewDefaults.Get(key)
                    o = util.KeyVal()
                    o.row = row
                    o.groups = []
                    for groupRow in cfg.overviewDefaultGroups[row.overviewID]:
                        o.groups.append(groupRow.groupID)

                    self.defaultOverviews[row.overviewShortName] = o

            self.sortedDefaultOverviewNames = sorted(self.defaultOverviews.iterkeys(), key=lambda k: self.defaultOverviews[k].row.overviewName)
            self.isLoaded = True

    def GetDefaultOverviewNameList(self):
        """
        This returns a list of names of the default overview presets
        """
        self.LoadDataIfNeeded()
        return self.sortedDefaultOverviewNames

    def GetDefaultOverviewName(self, name):
        """
        Given a default overview preset name it will lookup the MLS string key and return it
        """
        self.LoadDataIfNeeded()
        if name in self.defaultOverviews:
            return self.defaultOverviews[name].row.overviewName

    def GetDefaultOverviewGroups(self, name):
        """
        Given a default overview preset name it will return a list of groupIDs in the preset
        """
        self.LoadDataIfNeeded()
        if name in self.defaultOverviews:
            return self.defaultOverviews[name].groups
        return []

    def GetAllPresets(self):
        if not self.allPresets:
            self.AddDefaultPresetsToAllPresets()
        return self.allPresets

    def GetPresetFromKey(self, key):
        if self.IsTempName(key):
            preset = self.unsavedPresets.get(key[1], None)
        else:
            self.GetAllPresets()
            preset = self.allPresets.get(key, None)
        if not preset:
            preset = self.allPresets.get(DEFAULT_PRESET_NAME, {})
        return preset

    def GetPresetGroupsFromKey(self, key):
        preset = self.GetPresetFromKey(key)
        if not preset:
            return []
        return preset.get('groups', [])

    def GetGroups(self, presetName = None):
        if not presetName:
            presetName = self.GetActiveOverviewPresetName()
        return self.GetPresetGroupsFromKey(presetName)

    def GetBracketGroups(self, presetName = None):
        if not presetName:
            presetName = self.GetActiveBracketPresetName()
        return self.GetPresetGroupsFromKey(presetName)

    def FindPresetForStates(self, isBracket = False, presetName = None):
        if not presetName:
            if isBracket:
                presetName = self.GetActiveBracketPresetName()
            else:
                presetName = self.GetActiveOverviewPresetName()
        preset = self.GetPresetFromKey(presetName)
        if preset is None:
            preset = self.GetPresetFromKey(DEFAULT_PRESET_NAME)
        return preset

    def GetFilteredStates(self, isBracket = False, presetName = None):
        preset = self.FindPresetForStates(isBracket, presetName)
        return preset.get('filteredStates', [])

    def GetAlwaysShownStates(self, isBracket = False, presetName = None):
        preset = self.FindPresetForStates(isBracket, presetName)
        return preset.get('alwaysShownStates', [])

    def GetValidGroups(self, isBracket = False, presetName = None):
        if isBracket:
            groups = set(self.GetBracketGroups(presetName=presetName))
        else:
            groups = set(self.GetGroups(presetName=presetName))
        availableGroups = sm.GetService('tactical').GetAvailableGroups(getIds=True)
        return groups.intersection(availableGroups)

    def GetFilteredStatesByPresetKey(self, key = ''):
        preset = self.GetPresetFromKey(key=key)
        if not preset:
            return []
        return preset.get('filteredStates', [])

    def GetAlwaysShownStatesByPresetKey(self, key = ''):
        preset = self.GetPresetFromKey(key=key)
        if not preset:
            return []
        return preset.get('alwaysShownStates', [])

    def GetPresetsMenu(self):
        p = self.allPresets.copy()
        for name in self.GetDefaultOverviewNameList():
            if name in p:
                del p[name]

        m = []
        dm = []
        for label in p:
            dm.append((label.lower(), (label, self.DeletePreset, (label,))))

        overview = form.OverView.GetIfOpen()
        m.append((localization.GetByLabel('UI/Overview/AddTab'), overview.AddTab))
        if dm:
            m.append(None)
            dm = uiutil.SortListOfTuples(dm)
            m.append((uiutil.MenuLabel('UI/Common/Delete'), dm))
        bracketMgr = sm.GetService('bracket')
        if not bracketMgr.ShowingAll():
            m.append((uiutil.MenuLabel('UI/Overview/ShowAllBrackets'), bracketMgr.ShowAll))
        else:
            m.append((uiutil.MenuLabel('UI/Tactical/StopSowingAllBrackets'), bracketMgr.StopShowingAll))
        if not bracketMgr.ShowingNone():
            m.append((uiutil.MenuLabel('UI/Tactical/HideAllBrackets'), bracketMgr.ShowNone))
        else:
            m.append((uiutil.MenuLabel('UI/Tactical/StopHidingAllBrackets'), bracketMgr.StopShowingNone))
        m += [None]
        m += [(uiutil.MenuLabel('UI/Commands/OpenOverviewSettings'), sm.GetService('tactical').OpenSettings)]
        return m

    def LoadPreset(self, label, updateTabSettings = True, notSavedPreset = False):
        defaultPresetNames = self.GetDefaultOverviewNameList()
        if not notSavedPreset:
            presets = self.GetAllPresets()
            if self.IsTempName(label):
                log.LogWarn("Loading temp name when I shouldn't be, label = ", label)
                label = label[1]
            if label not in presets and label not in defaultPresetNames:
                log.LogWarn("Trying to load a preset that doesn't exist, load default instead - label = ", label)
                label = DEFAULT_PRESET_NAME
        if updateTabSettings:
            overview = sm.GetService('tactical').GetPanelForUpdate(form.OverView.default_windowID)
            if overview is not None and hasattr(overview, 'GetSelectedTabKey'):
                tabKey = overview.GetSelectedTabKey()
                tabSettings = self.GetTabSettingsForOverview()
                if tabKey in tabSettings.keys():
                    tabSettings[tabKey][form.OverView.default_windowID] = label
                sm.ScatterEvent('OnOverviewTabChanged', tabSettings, None)
        self.activeOverviewPreset = label
        settings.user.overview.Set('activeOverviewPreset', label)
        sm.ScatterEvent('OnTacticalPresetChange', label, None)

    def LoadBracketPreset(self, label, showSpecials = None, bracketShowState = None, notSavedPreset = False):
        defaultPresetNames = self.GetDefaultOverviewNameList()
        if not notSavedPreset:
            if label not in self.allPresets and label not in defaultPresetNames and label is not None:
                return
        self.activeBracketPreset = label
        sm.GetService('bracket').SoftReload(showSpecials, bracketShowState)

    def GetActiveBracketPresetName(self):
        presetName = self.activeBracketPreset
        if not presetName or presetName not in self.allPresets or self.IsTempName(presetName) and presetName[1] not in self.unsavedPresets:
            presetName = None
            self.activeBracketPreset = presetName
        return presetName

    def GetActiveOverviewPresetName(self):
        presetName = self.activeOverviewPreset
        if not presetName or presetName not in self.allPresets and self.IsTempName(presetName) and presetName[1] not in self.unsavedPresets:
            presetName = DEFAULT_PRESET_NAME
            self.activeOverviewPreset = presetName
        return presetName

    def ResetActivePresets(self):
        self.activeOverviewPreset = DEFAULT_PRESET_NAME
        self.activeBracketPreset = None

    def ResetPresetsToDefault(self):
        self.allPresets = {}
        self.AddDefaultPresetsToAllPresets()

    def SavePreset(self, *args):
        activeOverviewName = self.GetActiveOverviewPresetName()
        if self.IsTempName(activeOverviewName):
            baseName = activeOverviewName[1]
        else:
            baseName = activeOverviewName
        displayName = self.GetPresetDisplayName(baseName)
        ret = uiutil.NamePopup(localization.GetByLabel('UI/Tactical/TypeInLabelForPreset'), localization.GetByLabel('UI/Overview/TypeInLabel'), setvalue=displayName, maxLength=20)
        if ret:
            presetName = ret.lower()
            if presetName == DEFAULT_PRESET_NAME:
                presetName = 'default2'
            if presetName in self.allPresets:
                if eve.Message('AlreadyHaveLabel', {}, uiconst.YESNO) != uiconst.ID_YES:
                    return self.SavePreset()
            newPreset = {'groups': self.GetGroups(presetName=activeOverviewName)[:],
             'filteredStates': self.GetFilteredStates(presetName=activeOverviewName)[:],
             'alwaysShownStates': self.GetAlwaysShownStates(presetName=activeOverviewName)[:]}
            self.allPresets[presetName] = newPreset
            self.StorePresetsInSettings()
            self.LoadPreset(presetName)
            sm.ScatterEvent('OnOverviewPresetSaved')

    def DeletePreset(self, dlabel):
        if dlabel in self.allPresets:
            del self.allPresets[dlabel]
        if dlabel == self.activeOverviewPreset:
            self.LoadPreset(DEFAULT_PRESET_NAME)
        sm.ScatterEvent('OnOverviewPresetSaved')

    def GetMotifiedSetting(self, value, add, current):
        if add:
            if type(value) == list:
                for each in value:
                    if each not in current:
                        current.append(each)

            elif value not in current:
                current.append(value)
        elif type(value) == list:
            for each in value:
                while each in current:
                    current.remove(each)

        else:
            while value in current:
                current.remove(value)

        current.sort()
        return current

    def ChangeSettings(self, changeList, presetName = None):
        if not presetName:
            presetName = self.GetActiveOverviewPresetName()
        activePreset = self.GetPresetFromKey(presetName).copy()
        changeCounter = 0
        for eachChange in changeList:
            what, value, add = eachChange
            current = None
            if what == 'filteredStates':
                current = self.GetFilteredStatesByPresetKey(presetName)[:]
            elif what == 'alwaysShownStates':
                current = self.GetAlwaysShownStatesByPresetKey(presetName)[:]
            elif what == 'groups':
                current = self.GetPresetGroupsFromKey(presetName)[:]
            if current is None:
                continue
            changeCounter += 1
            current = self.GetMotifiedSetting(value, add, current)
            activePreset[what] = current

        if changeCounter == 0:
            return
        if self.IsTempName(presetName):
            basePresetName = presetName[1]
            unsavedName = presetName
            basePreset = self.GetPresetFromKey(basePresetName)
        else:
            basePresetName = presetName
            unsavedName = ('notSaved', presetName)
        basePreset = self.GetPresetFromKey(basePresetName)
        if IsPresetTheSame(basePreset, activePreset):
            return self.RestoreSavedPreset(basePresetName, unsavedName)
        self.unsavedPresets[basePresetName] = activePreset
        self.StorePresetsInSettings()
        self.LoadPreset(unsavedName, notSavedPreset=True)

    def RestoreSavedPreset(self, basePresetName, unsavedName):
        self.ChangeTabSettingsToUseBasePreset(unsavedName, basePresetName)
        self.unsavedPresets.pop(basePresetName, None)
        self.StorePresetsInSettings()
        self.LoadPreset(basePresetName, notSavedPreset=True)

    def ChangeTabSettingsToUseBasePreset(self, tempPresetName, basePresetName):
        tabSettings = self.GetTabSettingsForOverview()
        for tabIdx, tSetting in tabSettings.iteritems():
            if tSetting.get('overview') == tempPresetName:
                tSetting['overview'] = basePresetName
            if tSetting.get('bracket') == tempPresetName:
                tSetting['bracket'] = basePresetName

        settings.user.overview.Set('tabsettings', tabSettings)

    def SetSettings(self, what, groupList):
        if what != 'groups':
            return
        currentPresetName = self.GetActiveOverviewPresetName()
        preset = self.GetPresetFromKey(currentPresetName).copy()
        preset['groups'] = groupList
        if self.IsTempName(currentPresetName):
            newTempPresetName = currentPresetName[1]
            unsavedName = currentPresetName
        else:
            newTempPresetName = currentPresetName
            unsavedName = ('notSaved', currentPresetName)
        self.unsavedPresets[newTempPresetName] = preset
        self.LoadPreset(unsavedName, notSavedPreset=True)
        self.StorePresetsInSettings()

    def IsTempName(self, presetName):
        if isinstance(presetName, (list, tuple)):
            return True
        return False

    def GetPresetDisplayName(self, presetName):
        if self.IsTempName(presetName):
            displayName = localization.GetByLabel('UI/Overview/PresetNotSaved', presetName=self.GetPresetDisplayName(presetName[1]))
            return displayName
        defaultLabel = self.GetDefaultOverviewName(presetName)
        if defaultLabel:
            return defaultLabel
        return presetName

    def StorePresetsInSettings(self):
        settings.user.overview.Set('overviewProfilePresets', self.allPresets)
        settings.user.overview.Set('overviewProfilePresets_notSaved', self.unsavedPresets)

    def GetStringForOverviewPreset(self, data):
        dataString = yaml.safe_dump(data)
        return dataString

    def GetOverviewDataForSave(self, presetsToUse = None):
        """
            This funtion gets the overview data from the client, and prepares it to be saved.
            Ordering of things is very important here, so when the data is hashed, we always get the same value
            for the same setup. Therefore we need to convert dicts to list, that can then be sorted.
            This function is very connectd to the LoadSettings function, that converts things back to dicts and loads
            the data
        """
        data = self.GetGeneralSettings()
        presetsInUseDict = self.GetPresetsInUse(presetsToUse=presetsToUse)
        presetsInUseList = presetsInUseDict.values()
        presetsInUseList.sort()
        data['presets'] = presetsInUseList
        data['tabSetup'] = self.GetTabSettingsForSaving()
        return data

    def GetGeneralSettings(self):
        """
            only the keys in GetAllowedKeysInOverview() are allowed in the dictionary.
            The server will not store the overview if it has keys that are not in that list.
            So add to the list if more settings are being added here.
        """
        data = {}
        settingsAndDefaults = self.GetSettingsNamesAndDefaults()
        userSettingsTuples = []
        for configName, defaultSetting in settingsAndDefaults.iteritems():
            myValue = bool(settings.user.overview.Get(configName, defaultSetting))
            if myValue == defaultSetting:
                continue
            userSettingsTuples.append((configName, myValue))

        userSettingsTuples.sort()
        data['userSettings'] = userSettingsTuples
        stateSvc = sm.GetService('state')
        flagOrder = stateSvc.GetStateOrder('Flag')
        backgroundOrder = stateSvc.GetStateOrder('Background')
        data['flagOrder'] = flagOrder
        data['backgroundOrder'] = backgroundOrder
        flagStates = stateSvc.GetStateStates('tag')[:]
        backgroundStates = stateSvc.GetStateStates('background')[:]
        flagStates.sort()
        backgroundStates.sort()
        data['flagStates'] = flagStates
        data['backgroundStates'] = backgroundStates
        columnOrder = sm.GetService('tactical').GetColumnOrder()
        overviewColumns = sm.GetService('tactical').GetColumns()[:]
        overviewColumns.sort()
        data['columnOrder'] = columnOrder
        data['overviewColumns'] = overviewColumns
        colorDict = sm.GetService('state').GetFixedColorSettings()
        newColorDict = self.GetColorsToSave(colorDict)
        colorDictAsList = GetDeterministicListFromDict(newColorDict)
        data['stateColorsNameList'] = colorDictAsList
        stateBlinks = sm.GetService('state').defaultBlinkStates.copy()
        stateBlinks.update(settings.user.overview.Get('stateBlinks', {}))
        stateBlinks = EncodeKeyInDict(stateBlinks)
        stateBlinksList = GetDeterministicListFromDict(stateBlinks)
        data['stateBlinks'] = stateBlinksList
        shipLabels = sm.GetService('state').GetShipLabels()
        shipLabelsList = []
        shipLabelOrder = []
        for eachConfig in shipLabels:
            configType = eachConfig['type']
            shipLabelOrder.append(configType)
            orderedConfig = GetDeterministicListFromDict(eachConfig)
            shipLabelsList.append((configType, orderedConfig))

        shipLabelsList.sort()
        data['shipLabels'] = shipLabelsList
        data['shipLabelOrder'] = shipLabelOrder
        return data

    def GetPresetsInUse(self, presetsToUse = None):
        allPresets = self.GetAllPresets()
        allTabSettings = self.GetTabSettingsForOverview()
        defaultPresetNames = self.GetDefaultOverviewNameList()
        return self.GetPresetsInUseFromTabSettings(allTabSettings, allPresets, defaultPresetNames, presetsToUse=presetsToUse)

    def GetPresetsInUseFromTabSettings(self, allTabSettings, allPresets, exludePresets = [], presetsToUse = None):
        presetsInUse = {}

        def ShouldAddPreset(presetName):
            if presetName not in allPresets:
                return False
            if presetName in presetsInUse:
                return False
            if presetName in exludePresets:
                return False
            return True

        def AddPreset(presetName):
            presetAsList = GetDeterministicListFromDict(allPresets[presetName])
            presetsInUse[presetName] = (presetName, presetAsList)

        if presetsToUse:
            for presetName in presetsToUse:
                if ShouldAddPreset(presetName):
                    AddPreset(presetName)

        else:
            for tabIdx, tabSettings in allTabSettings.iteritems():
                if tabIdx >= MAX_TAB_NUM:
                    break
                for setupGroupName in ('overview', 'bracket'):
                    presetName = tabSettings[setupGroupName]
                    if self.IsTempName(presetName):
                        presetName = presetName[1]
                    if ShouldAddPreset(presetName):
                        AddPreset(presetName)

        return presetsInUse

    def GetSettingsNamesAndDefaults(self):
        if self.configNamesAndDefaults is None:
            self.configNamesAndDefaults = {'applyOnlyToShips': True,
             'useSmallColorTags': False,
             'useSmallText': False,
             'hideCorpTicker': False,
             'overviewBroadcastsToTop': False,
             'showBiggestDamageDealers': True,
             'showModuleHairlines': True,
             'targetCrosshair': True,
             'showInTargetRange': True,
             'showCategoryInTargetRange_6': True,
             'showCategoryInTargetRange_11': True,
             'showCategoryInTargetRange_18': True}
        return self.configNamesAndDefaults

    def GetSettingValueOrDefaultFromName(self, settingName, fallbackDefaultValue):
        defaultValue = self.GetDefaultSettingValueFromName(settingName, fallbackDefaultValue)
        return settings.user.overview.Get(settingName, defaultValue)

    def GetDefaultSettingValueFromName(self, settingName, fallbackDefaultValue):
        defaultNameAndSettings = self.GetSettingsNamesAndDefaults()
        return defaultNameAndSettings.get(settingName, fallbackDefaultValue)

    def LoadSettings(self, presetKey, overviewName):
        """
            this function takes in a presetKey and uses that key to get the preset from the server (or if you have
            fetched it already, from the client).
            It then takes that preset and loads it in the players settings.
            The preset does not come from the server as a dict or with dicts, because it needs to be ordered to get always
            the same hash so it and its values needs to be converted back to dicts where approriate, using the utility
            function GetDictFromList.
            Dicts are represented with lists, and since we built it, we know how to unfold it
                [a,b] = > {a:b}
        
            dicts that are converted to list:
             - color dict (background and flags)
             - blink dict
             - ship labels dict
             - inner dictionaries within ship labels dict
             - tab preset dict
             - inner dictionaries with tab preset dict
        
        """
        if eve.Message('LoadOverviewProfile', {}, uiconst.YESNO, default=uiconst.ID_NO) != uiconst.ID_YES:
            return
        yamlString = self.cachedPresetsFromServer.get(presetKey, None)
        if yamlString is None:
            yamlString = sm.RemoteSvc('overviewPresetMgr').GetStoredPreset(presetKey)
        if yamlString is None:
            raise UserError('OverviewProfileLoadingError')
        self.StoreOldProfileDataInSettings()
        dataList = yaml.safe_load(yamlString)
        data = GetDictFromList(dataList)
        self.LoadSettingsFromDict(data, overviewName, presetKey, saveInHistory=True)

    def LoadSettingsFromDict(self, data, overviewName, presetKey = None, saveInHistory = False):
        self.LoadGeneralSettings(data)
        presetDict = GetDictFromList(data['presets'])
        tabPresets = ReplaceInnerListsWithDicts(presetDict)
        self.UpdateAllPresets(tabPresets)
        tabSetup = self.GetTabSetupToLoad(data)
        oldTabSetup = self.GetTabSettingsForOverview()
        self.SetTabSettingsForOverview(tabSetup)
        settings.user.ui.Set('overviewProfileName', overviewName)
        if presetKey and saveInHistory:
            self.SaveOverviewLinkInSettings(overviewName, presetKey)
        sm.ScatterEvent('OnOverviewTabChanged', tabSetup, oldTabSetup)
        sm.ScatterEvent('OnReloadingOverviewProfile')

    def StoreOldProfileDataInSettings(self):
        """
            creates a backup for your overview when you click a link to load up overview profile
        """
        oldProfileData = self.GetOverviewDataForSave()
        oldOverviewName = self.GetOverviewName()
        now = blue.os.GetWallclockTime()
        oldProfileInfo = {'data': oldProfileData,
         'name': oldOverviewName,
         'timestamp': now}
        settings.user.overview.Set('restoreData', oldProfileInfo)

    def SaveOverviewLinkInSettings(self, overviewName, presetKey):
        timestamp = blue.os.GetWallclockTime()
        presetHistoryKeys = settings.user.overview.Get('presetHistoryKeys', {})
        if presetKey in presetHistoryKeys:
            entry = presetHistoryKeys[presetKey]
            entry['overviewName'] = overviewName
            entry['timestamp'] = timestamp
        else:
            entry = {'overviewName': overviewName,
             'presetKey': presetKey,
             'timestamp': timestamp}
            presetHistoryKeys[presetKey] = entry
        settings.user.overview.Set('presetHistoryKeys', presetHistoryKeys)

    def LoadGeneralSettings(self, data):
        configNamesAndDefaultsCopy = self.GetSettingsNamesAndDefaults().copy()
        userSettings = data.get('userSettings', [])
        for configName, settingValue in userSettings:
            if configName not in configNamesAndDefaultsCopy:
                continue
            settings.user.overview.Set(configName, settingValue)
            configNamesAndDefaultsCopy.pop(configName)

        for configName, defaultValue in configNamesAndDefaultsCopy.iteritems():
            settings.user.overview.Set(configName, defaultValue)

        flagOrder = data.get('flagOrder', [])
        backgroundOrder = data.get('backgroundOrder', [])
        settings.user.overview.Set('flagOrder', flagOrder)
        settings.user.overview.Set('backgroundOrder', backgroundOrder)
        flagStates = data.get('flagStates', [])
        flagStates.sort()
        backgroundStates = data.get('backgroundStates', [])
        backgroundStates.sort()
        settings.user.overview.Set('flagStates', flagStates)
        settings.user.overview.Set('backgroundStates', backgroundStates)
        columnOrder = data.get('columnOrder', sm.GetService('tactical').GetAllColumns())
        overviewColumns = data.get('overviewColumns', sm.GetService('tactical').GetDefaultVisibleColumns())
        overviewColumns.sort()
        settings.user.overview.Set('overviewColumnOrder', columnOrder)
        settings.user.overview.Set('overviewColumns', overviewColumns)
        colorNameDictAsList = data.get('stateColorsNameList', [])
        colorNameDict = GetDictFromList(colorNameDictAsList)
        newColorDict = self.GetColorValuesFromName(colorNameDict)
        settings.user.overview.Set('stateColors', newColorDict)
        sm.GetService('state').InitColors(reset=True)
        stateBlinks = GetDictFromList(data.get('stateBlinks', []))
        stateBlinks = DecodeKeyInDict(stateBlinks)
        settings.user.overview.Set('stateBlinks', stateBlinks)
        shipLabels = GetDictFromList(data.get('shipLabels', []))
        shipLabels = ReplaceInnerListsWithDicts(shipLabels)
        sm.GetService('state').shipLabels = None
        shipLabelOrder = data.get('shipLabelOrder', [])
        orderedShipLabelsList = GetOrderedListFromDict(shipLabels, shipLabelOrder)
        settings.user.overview.Set('shipLabels', orderedShipLabelsList)

    def GetTabSetupToLoad(self, data):
        tabSetup = GetDictFromList(data.get('tabSetup', []))
        tabSetup = ReplaceInnerListsWithDicts(tabSetup)
        return tabSetup

    def UpdateAllPresets(self, profileUpdateDict):
        self.allPresets.update(profileUpdateDict)
        self.StorePresetsInSettings()

    def GetColorsToSave(self, colorDict):
        """need to change the key because yaml doesn't handle tuple keys well"""
        newColorDict = {}
        for key, colorValue in colorDict.iteritems():
            colorName = state.FindColorName(colorValue)
            if colorName:
                newColorDict[key] = colorName

        newColorDict = EncodeKeyInDict(newColorDict)
        return newColorDict

    def GetColorValuesFromName(self, colorDict):
        newColorDict = {}
        for key, colorName in colorDict.iteritems():
            colorInfo = state.STATE_COLORS.get(colorName, None)
            if colorInfo:
                newColorDict[key] = colorInfo[0]

        newColorDict = DecodeKeyInDict(newColorDict)
        return newColorDict

    def GetTabSettingsForSaving(self):
        tabSettings = self.GetTabSettingsForOverview()
        tabSettingsAsList = []
        for idx, tSettingValue in tabSettings.items():
            for setupGroupName in ('overview', 'bracket'):
                if self.IsTempName(tSettingValue.get(setupGroupName, None)):
                    tSettingValue[setupGroupName] = tSettingValue[setupGroupName][1]

            tSettingList = GetDeterministicListFromDict(tSettingValue)
            tabSettingsAsList.append((idx, tSettingList))

        tabSettingsAsList.sort()
        tabSettingsAsList = tabSettingsAsList[:MAX_TAB_NUM]
        return tabSettingsAsList

    def GetTabSettingsForOverview(self):
        return settings.user.overview.Get('tabsettings', {})

    def SetTabSettingsForOverview(self, newSettings):
        settings.user.overview.Set('tabsettings', newSettings)

    def GetOverviewName(self):
        currentText = settings.user.ui.Get('overviewProfileName', None)
        if not currentText:
            currentText = localization.GetByLabel('UI/Overview/DefaultOverviewName', charID=session.charid)
        return currentText

    def GetShareData(self, text, presetsToUse = None):
        data = self.GetOverviewDataForSave(presetsToUse=presetsToUse)
        overviewPreset = util.KeyVal(__guid__='fakeentry.OverviewProfile', data=data, label=text)
        return [overviewPreset]
