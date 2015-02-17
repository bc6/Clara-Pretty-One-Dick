#Embedded file name: eve/client/script/ui/shared/systemMenu\betaOptions.py
from carbonui.util.bunch import Bunch
from eve.client.script.ui.control.checkbox import Checkbox
from eve.client.script.ui.util.uix import GetContainerHeader
import localization
import service
BETA_MAP_SETTING_KEY = 'experimental_map'

def ConstructOptInSection(column, columnWidth):
    optInOptions = GetOptInOptions()
    if not optInOptions:
        return
    GetContainerHeader(localization.GetByLabel('UI/SystemMenu/GeneralSettings/Experimental/Header'), column, xmargin=-5)
    for each in optInOptions:
        Checkbox(text=each.label, parent=column, configName=each.settingKey, checked=GetUserSetting(each.settingKey, False), prefstype=('user', 'ui'), callback=OnBetaSettingChanged)


def OnBetaSettingChanged(*args, **kwds):
    sm.GetService('neocom').UpdateNeocomButtons()


def IsGMRole():
    return session.role & (service.ROLE_GML | service.ROLE_WORLDMOD)


def IsMapEnabledInGlobalConfig():
    return IsBetaFeaturedEnabledInGlobalConfig(BETA_MAP_SETTING_KEY)


def IsBetaFeaturedEnabledInGlobalConfig(settingKey):
    globalConfig = sm.GetService('machoNet').GetGlobalConfig()
    return bool(int(globalConfig.get(settingKey, 0)))


def AppendNewMapOption(options):
    newMap = Bunch()
    newMap.settingKey = BETA_MAP_SETTING_KEY
    newMap.label = 'Try the New Map'
    options.append(newMap)


def GetOptInOptions():
    if not session.userid:
        return []
    options = []
    if IsGMRole() or IsMapEnabledInGlobalConfig():
        AppendNewMapOption(options)
    return options


def GetUserSetting(settingKey, defaultValue):
    return settings.user.ui.Get(settingKey, defaultValue)


def BetaFeatureEnabled(settingKey):
    if IsGMRole() or IsBetaFeaturedEnabledInGlobalConfig(settingKey):
        return GetUserSetting(settingKey, False)
    return False
