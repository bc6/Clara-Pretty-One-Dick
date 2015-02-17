#Embedded file name: eve/client/script/ui/shared\systemmenu.py
from carbonui.primitives.fill import Fill
from carbonui.util.color import Color
from eve.client.script.ui.control.eveCombo import Combo
from eve.client.script.ui.control.eveWindowUnderlay import WindowUnderlay, BumpedUnderlay
import sys
from eve.client.script.ui.control.themeColored import LineThemeColored
import uicontrols
import blue
import form
import listentry
import log
import service
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.container import Container
from eve.client.script.ui.shared.systemMenu.sliderEntry import SliderEntry
import trinity
import uiprimitives
import uix
import uiutil
import mathUtil
import uthread
import util
import carbonui.const as uiconst
import uicls
import cameras
import appUtils
import telemetry
import evegraphics.settings as gfxsettings
import trinity.evePostProcess as evePostProcess
from eve.client.script.ui.shared.systemMenu.optimizeSettingsWindow import OptimizeSettingsWindow
from eve.client.script.ui.shared.systemMenu.generalSettings import GenericSystemMenu
from notifications.client.notificationSettings.notificationSettingConst import ExperimentalConst
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_DELAY_GENERIC, TOOLTIP_SETTINGS_GENERIC, TOOLTIP_SETTINGS_BRACKET, TOOLTIP_DELAY_BRACKET, TOOLTIP_DELAY_MIN, TOOLTIP_DELAY_MAX
import localization
import localization.settings
CACHESIZES = [0,
 32,
 128,
 256,
 512]
LEFTPADDING = 120
SLIDERWIDTH = 120

class SystemMenu(uicls.LayerCore):
    __guid__ = 'form.SystemMenu'
    __nonpersistvars__ = []
    __notifyevents__ = ['OnEchoChannel',
     'OnVoiceChatLoggedIn',
     'OnVoiceChatLoggedOut',
     'OnVoiceFontChanged',
     'OnEndChangeDevice',
     'OnUIScalingChange',
     'OnUIRefresh']
    isTopLevelWindow = True

    def OnUIScalingChange(self, change, *args):
        if uicore.layer.systemmenu.isopen:
            self.sr.abouteveinited = False
            if self.sr.messageArea:
                self.sr.messageArea.Close()

    def OnUIRefresh(self):
        self.CloseView()
        uicore.layer.systemmenu.OpenView()

    @telemetry.ZONE_METHOD
    def Reset(self):
        self.sr.genericinited = 0
        self.sr.displayandgraphicsinited = 0
        self.sr.chatInited = 0
        self.sr.audioInited = 0
        self.sr.resetsettingsinited = 0
        self.sr.shortcutsinited = 0
        self.sr.languageinited = 0
        self.sr.abouteveinited = 0
        self.sr.wnd = None
        self.closing = 0
        self.init_languageID = eve.session.languageID if session.userid else prefs.languageID
        self.init_loadstationenv = gfxsettings.Get(gfxsettings.MISC_LOAD_STATION_ENV)
        self.init_dockshipsanditems = settings.char.windows.Get('dockshipsanditems', 0)
        self.init_stationservicebtns = settings.user.ui.Get('stationservicebtns', 1)
        self.tempStuff = []
        self.voiceFontList = None
        if sm.GetService('vivox').Enabled():
            sm.GetService('vivox').StopAudioTest()

    @telemetry.ZONE_METHOD
    def OnCloseView(self):
        if self.hideUI and eve.session.userid:
            sm.GetService('cmd').ShowUI()
        if self.settings:
            self.ApplyDeviceChanges()
        if getattr(self, 'optimizeWnd', None) is not None:
            self.optimizeWnd.Close()
        vivox = sm.GetService('vivox')
        if vivox.Enabled():
            vivox.LeaveEchoChannel()
        self.ApplyGraphicsSettings()
        self.FadeBGOut()
        self.StationUpdateCheck()
        sm.GetService('settings').SaveSettings()
        if session.userid is not None:
            sm.GetService('sceneManager').CheckCameraOffsets()
            sm.GetService('cameraClient').ApplyUserSettings()
        if eve.session.charid:
            if sm.GetService('viewState').IsViewActive('starmap'):
                sm.GetService('starmap').UpdateRoute()
        sm.GetService('settings').LoadSettings()
        self.Reset()
        sm.UnregisterNotify(self)

    @telemetry.ZONE_METHOD
    def OnOpenView(self):
        self.Reset()
        self.sr.wnd = uiprimitives.Container(name='sysmenu', parent=self)
        self.sr.wnd.cacheContents = True
        self.settings = None
        self.hideUI = not bool(eve.hiddenUIState)
        self.Setup()
        sm.RegisterNotify(self)

    def GetBackground(self):
        self.bg = Fill(parent=self.sr.wnd, color=Color.BLACK, opacity=0.0)
        self.FadeBGIn()
        if self.hideUI and eve.session.userid:
            sm.GetService('cmd').CmdHideUI(1)

    def FadeBGIn(self):
        duration = 0.6
        ppJob = sm.GetService('sceneManager').fisRenderJob
        uicore.animations.MorphScalar(ppJob.sceneDesaturation, 'value', ppJob.sceneDesaturation.value, 0.0, duration=duration)
        uicore.animations.FadeTo(self.bg, self.bg.opacity, 0.6, duration=duration)

    def FadeBGOut(self):
        duration = 0.6
        ppJob = sm.GetService('sceneManager').fisRenderJob
        uicore.animations.MorphScalar(ppJob.sceneDesaturation, 'value', ppJob.sceneDesaturation.value, 1.0, duration=duration)
        uicore.animations.FadeTo(self.bg, self.bg.opacity, 0.0, duration=duration)

    def GetTabs(self):
        if eve.session.userid:
            return [('displayandgraphics', localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Header')),
             ('chat', localization.GetByLabel('UI/SystemMenu/AudioAndChat/ChatHeader')),
             ('audio', localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioHeader')),
             ('generic', localization.GetByLabel('UI/SystemMenu/GeneralSettings/Header')),
             ('shortcuts', localization.GetByLabel('UI/SystemMenu/Shortcuts/Header')),
             ('reset settings', localization.GetByLabel('UI/SystemMenu/ResetSettings/Header')),
             ('language', localization.GetByLabel('UI/SystemMenu/Language/Header')),
             ('about eve', localization.GetByLabel('UI/SystemMenu/AboutEve/Header'))]
        else:
            return [('displayandgraphics', localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Header')),
             ('audio', localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioHeader')),
             ('generic', localization.GetByLabel('UI/SystemMenu/GeneralSettings/Header')),
             ('reset settings', localization.GetByLabel('UI/SystemMenu/ResetSettings/Header')),
             ('about eve', localization.GetByLabel('UI/SystemMenu/AboutEve/Header'))]

    def Setup(self):
        width = 800
        push = sm.GetService('window').GetCameraLeftOffset(width, align=uiconst.CENTER, left=0)
        self.sr.wnd.state = uiconst.UI_HIDDEN
        sm.GetService('settings').LoadSettings()
        menuarea = uiprimitives.Container(name='menuarea', align=uiconst.CENTER, pos=(push,
         0,
         width,
         570), state=uiconst.UI_NORMAL, parent=self.sr.wnd)
        mainclosex = uicontrols.Icon(icon='ui_38_16_220', parent=menuarea, pos=(2, 1, 0, 0), align=uiconst.TOPRIGHT, idx=0, state=uiconst.UI_NORMAL)
        mainclosex.OnClick = self.CloseMenuClick
        self.sr.menuarea = menuarea
        self.colWidth = (menuarea.width - 32) / 3
        menusub = uiprimitives.Container(name='menusub', state=uiconst.UI_NORMAL, parent=menuarea, padTop=20)
        tabs = self.GetTabs()
        maintabgroups = []
        for tabId, label in tabs:
            maintabgroups.append([label,
             uiprimitives.Container(name=tabId + '_container', parent=menusub, padTop=8, padBottom=8),
             self,
             tabId])

        maintabs = uicontrols.TabGroup(parent=menusub, autoselecttab=True, tabs=maintabgroups, groupID='sysmenumaintabs', idx=0)
        self.sr.maintabs = maintabs
        btnPar = uiprimitives.Container(name='btnPar', parent=menusub, align=uiconst.TOBOTTOM, height=35, padTop=const.defaultPadding, idx=0)
        btn = uicontrols.Button(parent=btnPar, label=localization.GetByLabel('UI/SystemMenu/CloseWindow'), func=self.CloseMenuClick, align=uiconst.CENTER)
        btn = uicontrols.Button(parent=btnPar, label=localization.GetByLabel('UI/SystemMenu/QuitGame'), func=self.QuitBtnClick, left=10, align=uiconst.CENTERRIGHT)
        if eve.session.userid:
            if not sm.GetService('gameui').UsingSingleSignOn():
                btn = uicontrols.Button(parent=btnPar, label=localization.GetByLabel('UI/SystemMenu/LogOff'), func=self.Logoff, left=btn.width + btn.left + 2, align=uiconst.CENTERRIGHT)
            if session.solarsystemid is not None:
                btn = uicontrols.Button(parent=btnPar, label=localization.GetByLabel('UI/Inflight/SafeLogoff'), func=self.SafeLogoff, left=btn.width + btn.left + 2, align=uiconst.CENTERRIGHT)
            btn = uicontrols.Button(parent=btnPar, label=localization.GetByLabel('UI/SystemMenu/YourPetitions'), func=self.Petition, left=10, align=uiconst.CENTERLEFT)
        if eve.session.charid and boot.region != 'optic':
            btn = uicontrols.Button(parent=btnPar, label=localization.GetByLabel('UI/SystemMenu/ConvertETC'), func=self.ConvertETC, left=btn.width + btn.left + 2, align=uiconst.CENTERLEFT)
        if eve.session.userid:
            build = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/SystemMenu/VersionInfo', version=boot.keyval['version'].split('=', 1)[1], build=boot.build), parent=self.sr.wnd, left=6, top=6, state=uiconst.UI_NORMAL)
        WindowUnderlay(parent=menuarea)
        self.GetBackground()
        if self.sr.wnd:
            self.sr.wnd.state = uiconst.UI_NORMAL

    def CloseMenuClick(self, *args):
        uicore.cmd.OnEsc()

    def SafeLogoff(self, button, *args):
        if session.solarsystemid is None:
            button.Close()
        else:
            uicore.cmd.OnEsc()
            sm.GetService('menu').SafeLogoff()

    def Logoff(self, *args):
        uicore.cmd.CmdLogOff()

    def Load(self, key):
        func = getattr(self, key.capitalize().replace(' ', ''), None)
        if func:
            uthread.new(func)
        uthread.new(uicore.registry.SetFocus, self.sr.menuarea)

    def InitDeviceSettings(self):
        self.settings = sm.GetService('device').GetSettings()
        self.initsettings = self.settings.copy()
        windowed = sm.GetService('device').IsWindowed(self.initsettings)
        self.uiScaleValue = sm.GetService('device').GetUIScaleValue(windowed)

    def ProcessDeviceSettings(self, whatChanged = ''):
        left = 80
        where = self.sr.monitorsetup
        if not where:
            return
        set = self.settings
        deviceSvc = sm.GetService('device')
        deviceSet = deviceSvc.GetSettings()
        if where:
            uiutil.FlushList(where.children[1:])
        adapterOps = deviceSvc.GetAdaptersEnumerated()
        windowOps = deviceSvc.GetWindowModes()
        resolutionOps, refresh = deviceSvc.GetAdapterResolutionsAndRefreshRates(set)
        windowed = deviceSvc.IsWindowed(set)
        if bool(windowed) and gfxsettings.Get(gfxsettings.GFX_WINDOW_BORDER_FIXED):
            set.Windowed = 2
            windowed = 1
        elif not windowed:
            gfxsettings.Set(gfxsettings.GFX_WINDOW_BORDER_FIXED, False, pending=False)
        setBB = deviceSvc.GetPreferedResolution(deviceSvc.IsWindowed(set))
        triapp = trinity.app
        if triapp.isMaximized:
            setBB = (deviceSet.BackBufferWidth, deviceSet.BackBufferHeight)
        currentResLabel = localization.GetByLabel('/Carbon/UI/Service/Device/ScreenSize', width=setBB[0], height=setBB[1])
        currentRes = (currentResLabel, (setBB[0], setBB[1]))
        if windowed and currentRes not in resolutionOps:
            resolutionOps.append(currentRes)
        scalingOps = deviceSvc.GetUIScalingOptions(height=setBB[1])
        deviceData = [('header', localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/Header')),
         ('toppush', 4),
         ('combo',
          ('Windowed', None, deviceSvc.IsWindowed(self.settings)),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/WindowedOrFullscreen'),
          windowOps,
          left,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/WindowedOrFullscreenTooltip'),
          whatChanged == 'Windowed'),
         ('combo',
          ('BackBufferSize', None, (setBB[0], setBB[1])),
          [localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/AdapterResolution'), localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/WindowSize')][windowed],
          resolutionOps,
          left,
          [localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/AdapterResolutionTooltip'), localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/WindowSizeTooltip')][windowed],
          whatChanged == 'BackBufferSize',
          triapp.isMaximized),
         ('combo',
          ('UIScaling', None, self.uiScaleValue),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/UIScaling'),
          scalingOps,
          left,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/UIScalingTooltip'),
          whatChanged == 'UIScaling'),
         ('combo',
          ('Adapter', None, set.Adapter),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/DisplayAdapter'),
          adapterOps,
          left,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/DisplayAdapterTooltip'),
          whatChanged == 'Adapter')]
        if blue.win32.IsTransgaming():
            deviceData += [('checkbox',
              ('MacMTOpenGL', ('public', 'ui'), bool(sm.GetService('cider').GetMultiThreadedOpenGL())),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/UseMultithreadedOpenGL'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/UseMultithreadedOpenglToolTip'))]
        options = deviceSvc.GetPresentationIntervalOptions(set)
        if set.PresentationInterval not in [ val for label, val in options ]:
            set.PresentationInterval = options[1][1]
        deviceData.append(('combo',
         ('PresentationInterval', None, set.PresentationInterval),
         localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/PresentInterval'),
         options,
         left,
         localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/PresentIntervalTooltip')))
        if eve.session.userid:
            deviceData += [('header', localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/CameraSettings/InSpaceCameraSettings'))]
            self.cameraOffsetTextAdded = 0
            deviceData.append(('slider',
             ('cameraOffset', ('user', 'ui'), gfxsettings.GetDefault(gfxsettings.UI_CAMERA_OFFSET)),
             'UI/SystemMenu/DisplayAndGraphics/DisplaySetup/CameraCenter',
             (-100, 100),
             120,
             10))
            deviceData.append(('toppush', 10))
            deviceData.append(('checkbox',
             ('offsetUIwithCamera', ('user', 'ui'), gfxsettings.GetDefault(gfxsettings.UI_OFFSET_UI_WITH_CAMERA)),
             localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/OffsetUIWithCamera'),
             None,
             None,
             localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/OffsetUIWithCameraTooltip')))
            incarnaCameraSvc = sm.GetService('cameraClient')
            incarnaCamSett = incarnaCameraSvc.GetCameraSettings()
            self.incarnaCameraOffsetTextAdded = 0
            self.incarnaCameraMouseLookSpeedTextAdded = 0
            deviceData += [('header', localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/CameraSettings/InStationCameraSettings')),
             ('slider',
              ('incarnaCameraOffset', ('user', 'ui'), incarnaCamSett.charOffsetSetting),
              'UI/SystemMenu/DisplayAndGraphics/DisplaySetup/CameraCenter',
              (-1.0, 1.0),
              120,
              10),
             ('toppush', 8),
             ('slider',
              ('incarnaCameraMouseLookSpeedSlider', ('user', 'ui'), incarnaCamSett.mouseLookSpeed),
              'UI/SystemMenu/DisplayAndGraphics/DisplaySetup/IncarnaCamera/CameraLookSpeed',
              (-6, 6),
              120,
              10),
             ('toppush', 10),
             ('checkbox',
              ('incarnaCameraInvertY', ('user', 'ui'), incarnaCamSett.invertY),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/IncarnaCamera/InvertY'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/IncarnaCamera/InvertYTooltip'))]
        self.ParseData(deviceData, where)
        btnPar = uiprimitives.Container(name='btnpar', parent=where, align=uiconst.TOBOTTOM, height=32)
        btn = uicontrols.Button(parent=btnPar, label=localization.GetByLabel('UI/Common/Buttons/Apply'), func=self.ApplyDeviceChanges, align=uiconst.CENTERTOP)

    def ApplyDeviceChanges(self, *args):
        deviceSvc = sm.GetService('device')
        if self.settings is None:
            return
        s = self.settings.copy()
        fixedWindow = gfxsettings.Get(gfxsettings.GFX_WINDOW_BORDER_FIXED)
        deviceChanged = deviceSvc.CheckDeviceDifference(s, True)
        triapp = trinity.app
        if not deviceChanged and blue.win32.IsTransgaming():
            windowModeChanged = sm.GetService('cider').HasFullscreenModeChanged()
            deviceChanged = deviceChanged or windowModeChanged
        if deviceChanged:
            deviceSvc.SetDevice(s, userModified=True)
        elif triapp.fixedWindow != fixedWindow:
            triapp.AdjustWindowForChange(s.Windowed, fixedWindow)
            deviceSvc.UpdateWindowPosition(s)
        windowed = deviceSvc.IsWindowed(self.settings)
        currentUIScale = deviceSvc.GetUIScaleValue(windowed)
        scaleValue = getattr(self, 'uiScaleValue', currentUIScale)
        if scaleValue != currentUIScale:
            if eve.Message('ScaleUI', {}, uiconst.YESNO, default=uiconst.ID_YES) == uiconst.ID_YES:
                deviceSvc.SetUIScaleValue(scaleValue, windowed)

    def OnEndChangeDevice(self, *args):
        if self and not self.destroyed and self.isopen:
            self.settings = sm.GetService('device').GetSettings()
            self.ProcessDeviceSettings()
            self.ProcessGraphicsSettings()

    def ChangeWindowMode(self, windowed):
        deviceSvc = sm.GetService('device')
        self.uiScaleValue = deviceSvc.GetUIScaleValue(windowed)
        if windowed == 2:
            gfxsettings.Set(gfxsettings.GFX_WINDOW_BORDER_FIXED, True, pending=False)
        else:
            gfxsettings.Set(gfxsettings.GFX_WINDOW_BORDER_FIXED, False, pending=False)
        if blue.win32.IsTransgaming():
            settings.public.ui.Set('MacFullscreen', not windowed)
        else:
            self.settings.Windowed = windowed
        self.settings.BackBufferWidth, self.settings.BackBufferHeight = deviceSvc.GetPreferedResolution(windowed)

    def OnComboChange(self, combo, header, value, *args):
        if combo.name in ('Adapter', 'Windowed', 'BackBufferFormat', 'BackBufferSize', 'AutoDepthStencilFormat', 'PresentationInterval', 'incarnaCameraChase', 'UIScaling'):
            triapp = trinity.app
            if combo.name == 'BackBufferSize':
                setattr(self.settings, 'BackBufferWidth', value[0])
                setattr(self.settings, 'BackBufferHeight', value[1])
                windowed = sm.GetService('device').IsWindowed(self.settings)
                if windowed and not triapp.isMaximized:
                    gfxsettings.Set(gfxsettings.GFX_RESOLUTION_WINDOWED, value, pending=False)
                elif not windowed:
                    gfxsettings.Set(gfxsettings.GFX_RESOLUTION_FULLSCREEN, value, pending=False)
            elif combo.name == 'Windowed':
                self.ChangeWindowMode(value)
            elif combo.name == 'UIScaling':
                self.uiScaleValue = value
            else:
                setattr(self.settings, combo.name, value)
            self.ProcessDeviceSettings(whatChanged=combo.name)
        elif combo.name == 'autoTargetBack':
            settings.user.ui.Set('autoTargetBack', value)
        elif combo.name == 'talkBinding':
            settings.user.audio.Set('talkBinding', value)
            sm.GetService('vivox').EnableGlobalPushToTalkMode('talk', value)
        elif combo.name == 'talkMoveToTopBtn':
            settings.user.audio.Set('talkMoveToTopBtn', value)
        elif combo.name == 'talkAutoJoinFleet':
            settings.user.audio.Set('talkAutoJoinFleet', value)
        elif combo.name == 'TalkOutputDevice':
            settings.user.audio.Set('TalkOutputDevice', value)
            sm.GetService('vivox').SetPreferredAudioOutputDevice(value)
        elif combo.name == 'TalkInputDevice':
            settings.user.audio.Set('TalkInputDevice', value)
            sm.GetService('vivox').SetPreferredAudioInputDevice(value)
        elif combo.name == 'actionmenuBtn':
            settings.user.ui.Set('actionmenuBtn', value)
        elif combo.name == 'cmenufontsize':
            settings.user.ui.Set('cmenufontsize', value)
        elif combo.name == 'contentEdition':
            prefs.trinityVersion = value
            self.ProcessGraphicsSettings()
        elif combo.name == 'dblClickUser':
            settings.user.ui.Set('dblClickUser', value)
        elif gfxsettings.GetSettingFromSettingKey(combo.name) is not None:
            setting = gfxsettings.GetSettingFromSettingKey(combo.name)
            gfxsettings.Set(setting, value)
            self.ProcessGraphicsSettings()
        elif combo.name == 'pseudolocalizationPreset':
            self.SetPseudolocalizationSettingsByPreset(value)
            self.RefreshLanguage(allUI=False)
        elif combo.name == 'characterReplacementMethod':
            self.setCharacterReplacementMethod = value
            if value > 0:
                self.setSimulateTooltip = False
                self.RefreshLanguage(allUI=False)
        elif combo.name == 'localizationImportantNames':
            self.setImpNameSetting = value
            self.RefreshLanguage(allUI=False)

    def OnMicrophoneIntensityEvent(self, level):
        if not self or self.destroyed:
            return
        if not self.sr.chatInited:
            return
        if level:
            maxW = self.sr.inputmeter.parent.GetAbsolute()[2] - 4
            level = int(maxW * level)
            if level > 100:
                level = 100
            self.sr.inputmeter.width = int(maxW * (level / 100.0))
        else:
            self.sr.inputmeter.width = 0

    def JoinLeaveEchoChannel(self, *args):
        self.echoBtn.state = uiconst.UI_DISABLED
        sm.GetService('vivox').JoinEchoChannel()

    def OnVoiceFontChanged(self):
        self.__RebuildChatPanel()

    def OnEchoChannel(self, joined):
        self.__RebuildChatPanel()

    def OnVoiceChatLoggedIn(self):
        self.__RebuildChatPanel()

    def OnVoiceChatLoggedOut(self):
        self.__RebuildChatPanel()

    def __RebuildChatPanel(self):
        if self.sr.chatInited == 0:
            return
        for each in self.sr.chatPanels:
            each.Flush()

        self.sr.chatInited = 0
        self.Chat()

    def __RebuildAudioPanel(self):
        if self.sr.audioInited == 0:
            return
        for each in self.sr.audioPanels:
            each.Flush()

        self.sr.audioInited = 0
        self.Audio(flush=True)

    def ReloadCommands(self, key = None):
        if not key:
            key = self.sr.currentShortcutTabKey
        self.sr.currentShortcutTabKey = key
        scrolllist = []
        for c in uicore.cmd.commandMap.GetAllCommands():
            if c.category and c.category != key:
                continue
            data = util.KeyVal()
            data.cmdname = c.name
            data.context = uicore.cmd.GetCategoryContext(c.category)
            shortcutString = c.GetShortcutAsString() or localization.GetByLabel('UI/SystemMenu/Shortcuts/NoShortcut')
            data.label = c.GetDescription() + '<t>' + shortcutString
            data.locked = c.isLocked
            data.refreshcallback = self.ReloadCommands
            scrolllist.append(listentry.Get('CmdListEntry', data=data))

        self.sr.active_cmdscroll.Load(contentList=scrolllist, headers=[localization.GetByLabel('UI/SystemMenu/Shortcuts/Command'), localization.GetByLabel('UI/SystemMenu/Shortcuts/Shortcut')], scrollTo=self.sr.active_cmdscroll.GetScrollProportion())

    def RestoreShortcuts(self, *args):
        uicore.cmd.RestoreDefaults()
        self.ReloadCommands()

    def ClearCommand(self, cmdName):
        uicore.cmd.ClearMappedCmd(cmdName)
        self.ReloadCommands()

    def Abouteve(self):
        if self.sr.abouteveinited:
            return
        parent = uiutil.GetChild(self.sr.wnd, 'about eve_container')
        self.sr.messageArea = uicontrols.Edit(parent=parent, padLeft=8, padRight=8, readonly=1)
        self.sr.messageArea.AllowResizeUpdates(0)
        html = localization.GetByLabel('UI/SystemMenu/AboutEve/AboutEve', title=localization.GetByLabel('UI/SystemMenu/AboutEve/ReleaseTitle'), subtitle='', version=boot.keyval['version'].split('=', 1)[1], build=boot.build, currentYear=blue.os.GetTimeParts(blue.os.GetTime())[0], EVECredits=localization.GetByLabel('UI/SystemMenu/AboutEve/EVECredits'), NESCredits=localization.GetByLabel('UI/SystemMenu/AboutEve/NESCredits'), CCPCredits=localization.GetByLabel('UI/SystemMenu/AboutEve/CCPCredits'))
        self.sr.messageArea.LoadHTML(html)
        self.sr.abouteveinited = 1

    def ValidateData(self, entries):
        valid = []
        for rec in entries:
            if rec[0] not in ('checkbox', 'combo', 'slider', 'button'):
                valid.append(rec)
                continue
            if eve.session.charid:
                valid.append(rec)
            elif len(rec) > 1:
                if rec[1] is None:
                    valid.append(rec)
                    continue
                cfgName, prefsType, defaultValue = rec[1]
                if type(prefsType) is tuple:
                    if prefsType[0] == 'char':
                        if eve.session.charid:
                            valid.append(rec)
                    elif prefsType[0] == 'user':
                        if eve.session.userid:
                            valid.append(rec)
                    else:
                        valid.append(rec)
                else:
                    valid.append(rec)

        return valid

    def ParseData(self, entries, parent, validateEntries = 1):
        if validateEntries:
            validEntries = self.ValidateData(entries)
            if not validEntries:
                return
        for rec in entries:
            if validateEntries and rec[0] in ('checkbox', 'combo', 'slider', 'button') and rec not in validEntries:
                continue
            if rec[0] == 'topcontainer':
                c = uiprimitives.Container(name='container', align=uiconst.TOTOP, height=rec[1], parent=parent)
                if len(rec) > 2:
                    c.name = rec[2]
            elif rec[0] == 'toppush':
                uiprimitives.Container(name='toppush', align=uiconst.TOTOP, height=rec[1], parent=parent)
            elif rec[0] == 'leftpush':
                uiprimitives.Container(name='leftpush', align=uiconst.TOLEFT, width=rec[1], parent=parent)
            elif rec[0] == 'rightpush':
                uiprimitives.Container(name='rightpush', align=uiconst.TORIGHT, width=rec[1], parent=parent)
            elif rec[0] == 'button':
                btnpar = uiprimitives.Container(name='buttonpar', align=uiconst.TOTOP, height=24, parent=parent)
                args = None
                if len(rec) > 4:
                    args = rec[4]
                uicontrols.Button(parent=btnpar, label=rec[2], func=rec[3], args=args)
            elif rec[0] == 'header':
                if len(parent.children) > 1:
                    containerHeader = uix.GetContainerHeader(rec[1], parent, xmargin=-5)
                    containerHeader.padTop = 4
                    containerHeader.padBottom = 2
                else:
                    uix.GetContainerHeader(rec[1], parent, xmargin=1, bothlines=0)
                    uiprimitives.Container(name='leftpush', align=uiconst.TOLEFT, width=6, parent=parent)
                    uiprimitives.Container(name='rightpush', align=uiconst.TORIGHT, width=6, parent=parent)
                    uiprimitives.Container(name='toppush', align=uiconst.TOTOP, height=2, parent=parent)
            elif rec[0] == 'text':
                t = uicontrols.EveLabelMedium(name='sysheader', text=rec[1], parent=parent, align=uiconst.TOTOP, padTop=2, padBottom=2, state=uiconst.UI_NORMAL)
                if len(rec) > 2:
                    self.sr.Set(rec[2], t)
            elif rec[0] == 'line':
                LineThemeColored(parent=parent, align=uiconst.TOTOP, padLeft=-5, padRight=-5)
                uiprimitives.Container(name='toppush', align=uiconst.TOTOP, height=6, parent=parent)
            elif rec[0] == 'checkbox':
                cfgName, prefsType, defaultValue = rec[1]
                label = rec[2]
                checked = int(self.GetSettingsValue(cfgName, prefsType, defaultValue))
                value = None
                if len(rec) > 3 and rec[3] is not None:
                    value = rec[3]
                    checked = bool(checked == value)
                group = None
                if len(rec) > 4:
                    group = rec[4]
                hint = None
                if len(rec) > 5:
                    hint = rec[5]
                focus = None
                if len(rec) > 6:
                    focus = rec[6]
                if prefsType == 'server_setting':
                    prefsType = None
                cb = uicontrols.Checkbox(text=label, parent=parent, configName=cfgName, retval=value, checked=checked, groupname=group, callback=self.OnCheckBoxChange, prefstype=prefsType)
                if len(rec) > 7:
                    disabled = rec[7]
                    if disabled:
                        cb.Disable()
                        cb.opacity = 0.5
                if focus:
                    uicore.registry.SetFocus(cb)
                cb.sr.hint = hint
                cb.RefreshHeight()
                self.tempStuff.append(cb)
            elif rec[0] == 'combo':
                cfgName, prefsType, defaultValue = rec[1]
                if prefsType:
                    defaultValue = self.GetSettingsValue(cfgName, prefsType, defaultValue)
                label = rec[2]
                options = rec[3]
                if cfgName == 'UIScaling':
                    newValue = False
                    for optionLabel, value in options:
                        if defaultValue == value:
                            newValue = True

                    if not newValue:
                        defaultValue = options[-1][1]
                labelleft = 0
                if len(rec) > 4:
                    labelleft = rec[4]
                hint = None
                if len(rec) > 5:
                    hint = rec[5]
                focus = None
                if len(rec) > 6:
                    focus = rec[6]
                cont = uiprimitives.Container(name='comboCont', parent=parent, align=uiconst.TOTOP, height=18)
                combo = uicontrols.Combo(label=label, parent=cont, options=options, name=cfgName, select=defaultValue, callback=self.OnComboChange, labelleft=labelleft, align=uiconst.TOTOP)
                if focus:
                    uicore.registry.SetFocus(combo)
                combo.parent.hint = hint
                combo.SetHint(hint)
                combo.parent.state = uiconst.UI_NORMAL
                uiprimitives.Container(name='toppush', align=uiconst.TOTOP, height=6, parent=parent)
                if len(rec) > 7:
                    if rec[7]:
                        combo.Disable()
            elif rec[0] == 'slider':
                cfgName, prefsType, defaultValue = rec[1]
                label = rec[2]
                minVal, maxVal = rec[3]
                labelWidth = 0
                labelAlign = uiconst.RELATIVE
                step = None
                leftHint = None
                rightHint = None
                if len(rec) > 4:
                    lw = rec[4]
                    if lw is not None:
                        labelWidth = lw
                        labelAlign = uiconst.TOLEFT
                if len(rec) > 5:
                    step = rec[5]
                if len(rec) > 6 and isinstance(rec[6], tuple):
                    leftHint, rightHint = rec[6]
                slider = self.AddSlider(parent, rec[1], minVal, maxVal, label, height=10, labelAlign=labelAlign, labelWidth=labelWidth, startValue=defaultValue, step=step, leftHint=leftHint, rightHint=rightHint)
                if len(rec) > 6 and isinstance(rec[6], bool):
                    disabled = rec[6]
                    if disabled:
                        slider.Disable()
                        slider.opacity = 0.5
                        slider.label.Disable()
                        slider.label.opacity = 0.5

        if self.sr.maintabs and self.sr.menuarea and parent:
            self.ValidateMenuSize(parent)

    def ValidateMenuSize(self, column):
        colHeight = self.sr.maintabs.height + 100
        for child in column.children:
            if isinstance(child, uiprimitives.Container):
                colHeight += max(child.height, getattr(child, 'minimumHeight', 0))

        if colHeight > self.sr.menuarea.height:
            self.sr.menuarea.height = min(uicore.desktop.height, colHeight)

    def OnSetCameraSliderValue(self, value, *args):
        if not getattr(self, 'cameraOffsetTextAdded', 0):
            if getattr(self, 'cameraOffset', None) is None:
                self.cameraSlider = uiutil.FindChild(self, 'cameraOffset')
            self.AddCameraOffsetHint(self.cameraSlider)
            self.cameraOffsetTextAdded = 1
        gfxsettings.Set(gfxsettings.UI_CAMERA_OFFSET, value, pending=False)
        sm.ScatterEvent('OnGraphicSettingsChanged', [gfxsettings.UI_CAMERA_OFFSET])

    def OnSetIncarnaCameraSliderValue(self, value, *args):
        if not getattr(self, 'incarnaCameraOffsetTextAdded', 0):
            if getattr(self, 'incarnaCameraOffset', None) is None:
                self.incarnaCameraSlider = uiutil.FindChild(self, 'incarnaCameraOffset')
            self.AddCameraOffsetHint(self.incarnaCameraSlider)
            self.incarnaCameraOffsetTextAdded = 1
        gfxsettings.Set(gfxsettings.UI_INCARNA_CAMERA_OFFSET, value, pending=False)
        sm.ScatterEvent('OnGraphicSettingsChanged', [gfxsettings.UI_INCARNA_CAMERA_OFFSET])

    def OnSetIncarnaCameraMouseLookSpeedSliderValue(self, value, *args):
        if not getattr(self, 'incarnaCameraMouseLookSpeedTextAdded', 0):
            if getattr(self, 'incarnaCameraMouseLookSpeedSlider', None) is None:
                self.incarnaCameraMouseSpeedSlider = uiutil.FindChild(self, 'incarnaCameraMouseLookSpeedSlider')
            self.AddCameraMouseLookSpeedHint(self.incarnaCameraMouseSpeedSlider)
            self.incarnaCameraMouseLookSpeedTextAdded = 1
        valueToUse = cameras.MOUSE_LOOK_SPEED
        if value < 0:
            value = abs(value)
            value += 1.0
            valueToUse = valueToUse / value
        elif value > 0:
            value += 1.0
            valueToUse *= value
        gfxsettings.Set(gfxsettings.UI_INCARNA_CAMERA_MOUSE_LOOK_SPEED, valueToUse, pending=False)
        sm.ScatterEvent('OnGraphicSettingsChanged', [gfxsettings.UI_INCARNA_CAMERA_MOUSE_LOOK_SPEED])

    def OnRadialMenuSliderValue(self, value, *args):
        if not getattr(self, 'radialMenuSpeedTextAdded', 0):
            if getattr(self, 'actionMenuExpandTime', None) is None:
                self.actionMenuExpandTime = uiutil.FindChild(self, 'actionMenuExpandTime')
            p = self.actionMenuExpandTime.parent
            instantText = localization.GetByLabel('UI/SystemMenu/GeneralSettings/Inflight/NoRadialMenuDelay')
            uicontrols.EveLabelSmall(name='instant', text=instantText, parent=p, align=uiconst.TOPLEFT, top=10, color=(1.0, 1.0, 1.0, 0.75))
            slowText = localization.GetByLabel('UI/SystemMenu/GeneralSettings/Inflight/LongRadialMenuDelay')
            uicontrols.EveLabelSmall(name='slower', text=slowText, parent=p, align=uiconst.TOPRIGHT, top=10, color=(1.0, 1.0, 1.0, 0.75))
            self.radialMenuSpeedTextAdded = 1

    def AddCameraMouseLookSpeedHint(self, whichOne):
        p = whichOne.parent
        uicontrols.EveLabelSmall(name='slower', text=localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/IncarnaCamera/CameraSpeedSliderSlow'), parent=p, align=uiconst.TOPLEFT, top=10, color=(1.0, 1.0, 1.0, 0.75))
        uicontrols.EveLabelSmall(name='faster', text=localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/IncarnaCamera/CameraSpeedSliderFast'), parent=p, align=uiconst.TOPRIGHT, top=10, color=(1.0, 1.0, 1.0, 0.75))
        uiprimitives.Line(name='centerLine', parent=p, width=2, height=10, align=uiconst.CENTER)
        p.parent.hint = localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/IncarnaCamera/CameraSpeedSliderTooltip')
        p.state = p.parent.state = uiconst.UI_NORMAL

    def AddCameraOffsetHint(self, whichOne):
        p = whichOne.parent
        uicontrols.EveLabelSmall(name='left', text=localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/CameraCenterSliderLeft'), parent=p, align=uiconst.TOPLEFT, top=10, color=(1.0, 1.0, 1.0, 0.75))
        uicontrols.EveLabelSmall(name='right', text=localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/CameraCenterSliderRight'), parent=p, align=uiconst.TOPRIGHT, top=10, color=(1.0, 1.0, 1.0, 0.75))
        uiprimitives.Line(name='centerLine', parent=p, width=2, height=10, align=uiconst.CENTER)
        p.parent.hint = localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/CameraCenterSliderTooltip')
        p.state = p.parent.state = uiconst.UI_NORMAL

    def GetCameraMouseSpeedHintText(self, value):
        if value == 0:
            return localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/IncarnaCamera/CameraSpeedSliderDefaultValue')
        elif value < 0:
            value = abs(value) + 1.0
            return localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/IncarnaCamera/CameraSpeedSliderSlowerValue', value=value)
        else:
            value += 1.0
            return localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/IncarnaCamera/CameraSpeedSliderFasterValue', value=value)

    def GetCameraOffsetHintText(self, value, incarna = False):
        if incarna:
            value *= 100
        if value == 0:
            return localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/CameraCenterSliderCenteredValue')
        elif value < 0:
            return localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/CameraCenterSliderLeftValue', value=abs(int(value)))
        else:
            return localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/DisplaySetup/CameraCenterSliderRightValue', value=abs(int(value)))

    def GetSettingsValue(self, cfgName, prefsType, defaultValue):
        if not prefsType:
            return defaultValue
        elif prefsType == 'server_setting':
            value = sm.GetService('characterSettings').Get(cfgName)
            return value or defaultValue
        else:
            return util.GetAttrs(settings, *prefsType).Get(cfgName, defaultValue)

    def _RebuildGenericPanel(self):
        self.sr.genericinited = False
        parent = uiutil.GetChild(self.sr.wnd, 'generic_container')
        parent.Flush()
        self.Generic()

    def Generic(self):
        if self.sr.genericinited:
            return
        parent = uiutil.GetChild(self.sr.wnd, 'generic_container')
        parent.Flush()
        if settings.public.generic.Get('showintro2', None) is None:
            settings.public.generic.Set('showintro2', prefs.GetValue('showintro2', 1))
        menu = GenericSystemMenu(mainParent=parent, parseDataFunction=self.ParseData, menuSizeColumnValidator=self.ValidateMenuSize)
        menu.MakeColumn1(columnWidth=self.colWidth)
        menu.MakeColumn2(columnWidth=self.colWidth)
        menu.MakeColumn3(columnWidth=self.colWidth)
        self.sr.genericinited = 1

    def Audio(self, flush = False):
        if self.sr.audioInited:
            return
        parent = uiutil.GetChild(self.sr.wnd, 'audio_container')
        labelWidth = 125
        if self.sr.audioPanels is None or len(self.sr.audioPanels) == 0:
            self.sr.audioPanels = []
            col1 = uiprimitives.Container(name='col1', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
            col1.isTabOrderGroup = 1
            self.sr.audioPanels.append(col1)
        else:
            col1 = self.sr.audioPanels[0]
        BumpedUnderlay(isInFocus=True, parent=col1, idx=0)
        audioSvc = sm.GetService('audio')
        enabled = audioSvc.IsActivated()
        turretSuppressed = audioSvc.GetTurretSuppression()
        voiceCountLimited = audioSvc.GetVoiceCountLimitation()
        audioData = (('header', localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/Header')),
         ('checkbox', ('audioEnabled', ('public', 'audio'), enabled), localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/AudioEnabled')),
         ('header', localization.GetByLabel('UI/SystemMenu/AudioAndChat/VolumeLevel/Header')),
         ('slider',
          ('eveampGain', ('public', 'audio'), 0.25),
          'UI/SystemMenu/AudioAndChat/VolumeLevel/MusicLevel',
          (0.0, 1.0),
          labelWidth),
         ('slider',
          ('uiGain', ('public', 'audio'), 0.5),
          'UI/SystemMenu/AudioAndChat/VolumeLevel/UISoundLevel',
          (0.0, 1.0),
          labelWidth),
         ('slider',
          ('evevoiceGain', ('public', 'audio'), 0.7),
          'UI/SystemMenu/AudioAndChat/VolumeLevel/UIVoiceLevel',
          (0.0, 1.0),
          labelWidth),
         ('slider',
          ('worldVolume', ('public', 'audio'), 0.7),
          'UI/SystemMenu/AudioAndChat/VolumeLevel/WorldLevel',
          (0.0, 1.0),
          labelWidth),
         ('slider',
          ('masterVolume', ('public', 'audio'), 0.8),
          'UI/SystemMenu/AudioAndChat/VolumeLevel/MasterLevel',
          (0.0, 1.0),
          labelWidth),
         ('checkbox', ('suppressTurret', ('public', 'audio'), turretSuppressed), localization.GetByLabel('UI/SystemMenu/AudioAndChat/VolumeLevel/SuppressTurretSounds')),
         ('checkbox', ('limitVoiceCount', ('public', 'audio'), voiceCountLimited), localization.GetByLabel('UI/SystemMenu/AudioAndChat/VolumeLevel/LimitVoiceCount')),
         ('text', localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/Warning')))
        self.ParseData(audioData, col1)
        if not session.userid:
            self.sr.audioInited = True
            return
        if len(self.sr.audioPanels) < 2:
            col2 = uiprimitives.Container(name='column3', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
            col2.isTabOrderGroup = 1
            self.sr.audioPanels.append(col2)
        else:
            col2 = self.sr.audioPanels[1]
        if flush:
            col2.Flush()
        BumpedUnderlay(isInFocus=True, parent=col2, idx=0)
        advancedDisabled = not settings.user.audio.Get('soundLevel_advancedSettings', False)
        audioData2 = (('leftpush', 6),
         ('rightpush', 6),
         ('checkbox', ('soundLevel_advancedSettings', ('user', 'audio'), False), localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/AdvancedAudioSettings')),
         ('line',))
        self.ParseData(audioData2, col2)
        audioScroll2 = ScrollContainer(parent=col2, padding=(9, -5, -5, 1))
        audioSliderSetting = (('soundLevel_custom_turrets', 'UI/SystemMenu/AudioAndChat/AudioEngine/Turrets'),
         ('soundLevel_custom_impact', 'UI/SystemMenu/AudioAndChat/AudioEngine/Impact'),
         ('soundLevel_custom_jumpgates', 'UI/SystemMenu/AudioAndChat/AudioEngine/Jumpgates'),
         ('soundLevel_custom_wormholes', 'UI/SystemMenu/AudioAndChat/AudioEngine/Wormholes'),
         ('soundLevel_custom_jumpactivation', 'UI/SystemMenu/AudioAndChat/AudioEngine/JumpActivation'),
         ('soundLevel_custom_crimewatch', 'UI/SystemMenu/AudioAndChat/AudioEngine/Crimewatch'),
         ('soundLevel_custom_explosions', 'UI/SystemMenu/AudioAndChat/AudioEngine/Explosions'),
         ('soundLevel_custom_boosters', 'UI/SystemMenu/AudioAndChat/AudioEngine/Boosters'),
         ('soundLevel_custom_stationext', 'UI/SystemMenu/AudioAndChat/AudioEngine/StationsExterior'),
         ('soundLevel_custom_stationint', 'UI/SystemMenu/AudioAndChat/AudioEngine/StationsInterior'),
         ('soundLevel_custom_modules', 'UI/SystemMenu/AudioAndChat/AudioEngine/Modules'),
         ('soundLevel_custom_shipsounds', 'UI/SystemMenu/AudioAndChat/AudioEngine/ShipSounds'),
         ('soundLevel_custom_warping', 'UI/SystemMenu/AudioAndChat/AudioEngine/Warping'),
         ('soundLevel_custom_warpeffect', 'UI/SystemMenu/AudioAndChat/AudioEngine/WarpEffect'),
         ('soundLevel_custom_mapisis', 'UI/SystemMenu/AudioAndChat/AudioEngine/MapIsis'),
         ('soundLevel_custom_locking', 'UI/SystemMenu/AudioAndChat/AudioEngine/LockingSounds'),
         ('soundLevel_custom_store', 'UI/SystemMenu/AudioAndChat/AudioEngine/Store'),
         ('soundLevel_custom_planets', 'UI/SystemMenu/AudioAndChat/AudioEngine/Planets'),
         ('soundLevel_custom_uiclick', 'UI/SystemMenu/AudioAndChat/AudioEngine/Uiclick'),
         ('soundLevel_custom_radialmenu', 'UI/SystemMenu/AudioAndChat/AudioEngine/Radial'),
         ('soundLevel_custom_uiinteraction', 'UI/SystemMenu/AudioAndChat/AudioEngine/Uiinteraction'),
         ('soundLevel_custom_aura', 'UI/SystemMenu/AudioAndChat/AudioEngine/Aura'),
         ('soundLevel_custom_hacking', 'UI/SystemMenu/AudioAndChat/AudioEngine/Hacking'),
         ('soundLevel_custom_shieldlow', 'UI/SystemMenu/AudioAndChat/AudioEngine/shieldlow'),
         ('soundLevel_custom_armorlow', 'UI/SystemMenu/AudioAndChat/AudioEngine/armorlow'),
         ('soundLevel_custom_hulllow', 'UI/SystemMenu/AudioAndChat/AudioEngine/hulllow'),
         ('soundLevel_custom_shipdamage', 'UI/SystemMenu/AudioAndChat/AudioEngine/ShipDamage'),
         ('soundLevel_custom_cap', 'UI/SystemMenu/AudioAndChat/AudioEngine/cap'),
         ('soundLevel_custom_atmosphere', 'UI/SystemMenu/AudioAndChat/AudioEngine/Atmosphere'),
         ('soundLevel_custom_dungeonmusic', 'UI/SystemMenu/AudioAndChat/AudioEngine/DungeonMusic'),
         ('soundLevel_custom_normalmusic', 'UI/SystemMenu/AudioAndChat/AudioEngine/NormalMusic'))
        Container(parent=audioScroll2, align=uiconst.TOTOP, height=4)
        for settingKey, messageLabel in audioSliderSetting:
            SliderEntry(parent=audioScroll2, config=(settingKey, ('user', 'audio'), 0.5), minval=0.0, maxval=1.0, header=localization.GetByLabel(messageLabel), GetSliderValue=self.GetSliderValue, SetSliderLabel=self.SetSliderLabel, GetSliderHint=self.GetSliderHint, EndSetSliderValue=self.EndSliderValue, sliderWidth=80)

        Container(parent=audioScroll2, align=uiconst.TOTOP, height=4)
        if advancedDisabled:
            audioScroll2.state = uiconst.UI_DISABLED
            audioScroll2.opacity = 0.5
        if len(self.sr.audioPanels) < 3:
            col3 = uiprimitives.Container(name='col3', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
            col3.isTabOrderGroup = 1
            self.sr.audioPanels.append(col3)
        else:
            col3 = self.sr.audioPanels[2]
        if flush:
            col3.Flush()
        BumpedUnderlay(isInFocus=True, parent=col3)
        advancedDisabled = not settings.user.audio.Get('inactiveSounds_advancedSettings', False)
        audioData2 = (('leftpush', 6),
         ('rightpush', 6),
         ('checkbox', ('inactiveSounds_advancedSettings', ('user', 'audio'), False), localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientDampening')),
         ('line',),
         ('leftpush', 15),
         ('checkbox',
          ('inactiveSounds_master', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientMasterDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_music', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientMusicDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_turrets', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientTurretsDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_shield', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientShieldDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_armor', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientArmorDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_hull', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientHullDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_shipsound', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientShipsoundDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_jumpgates', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientJumpgateDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_wormholes', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientWormholeDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_jumping', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientJumpingDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_aura', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientAuraDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_modules', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientModulesDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_explosions', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientExplosionsDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_warping', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientWarpingDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_locking', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientLockingDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_planets', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientPlanetsDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_impacts', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientImpactsDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_deployables', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientDeployablesDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_boosters', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientBoostersDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_pocos', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientPocosDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_stationint', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientStationIntDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled),
         ('checkbox',
          ('inactiveSounds_stationext', ('user', 'audio'), False),
          localization.GetByLabel('UI/SystemMenu/AudioAndChat/AudioEngine/InactiveClientStationExtDampening'),
          None,
          None,
          None,
          None,
          advancedDisabled))
        self.ParseData(audioData2, col3)
        self.sr.audioInited = True

    def Chat(self):
        """ Creates the panels for audio, chat and voice chat settings.
        
            Voice Chat settings are only available when connected to Vivox.
            Reason: Those settings are stored on the Vivox side.
        """
        if self.sr.chatInited:
            return
        parent = uiutil.GetChild(self.sr.wnd, 'chat_container')
        if self.sr.chatPanels is None or len(self.sr.chatPanels) == 0:
            self.sr.chatPanels = []
            col1 = uiprimitives.Container(name='column', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
            col1.isTabOrderGroup = 1
            self.sr.chatPanels.append(col1)
        else:
            col1 = self.sr.chatPanels[0]
        BumpedUnderlay(isInFocus=True, parent=col1)
        labelWidth = 125
        voiceChatMenuAvailable = boot.region != 'optic'
        if sm.GetService('vivox').LoggedIn() and voiceChatMenuAvailable:
            keybindOptions = sm.GetService('vivox').GetAvailableKeyBindings()
            try:
                outputOps = [ (each[1], each[0]) for each in sm.GetService('vivox').GetAudioOutputDevices() ]
            except:
                log.LogException()
                sys.exc_clear()
                outputOps = []

            try:
                inputOps = [ (each[1], each[0]) for each in sm.GetService('vivox').GetAudioInputDevices() ]
            except:
                log.LogException()
                sys.exc_clear()
                inputOps = []

            joinedChannels = sm.GetService('vivox').GetJoinedChannels()
            voiceHeader = localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/Header')
            voiceServerInfo = sm.GetService('vivox').GetServerInfo()
            if voiceServerInfo:
                voiceHeader = localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/Header', server=voiceServerInfo)
            vivoxData = [('header', voiceHeader),
             ('checkbox',
              ('voiceenabled', ('user', 'audio'), 1),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/EveVoiceEnabled'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/EveVoiceEnabledTooltip')),
             ('checkbox',
              ('talkMutesGameSounds', ('user', 'audio'), 0),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/MuteWhenITalk'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/MuteWhenITalkTooltip')),
             ('checkbox',
              ('listenMutesGameSounds', ('user', 'audio'), 0),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/MuteWhenOthersTalk'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/MuteWhenOthersTalkTooltip')),
             ('header', localization.GetByLabel('UI/SystemMenu/AudioAndChat/ChannelSpecification/Header')),
             ('checkbox',
              ('talkMoveToTopBtn', ('user', 'audio'), 0),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/ChannelSpecification/MoveLastSpeakerToTop'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/ChannelSpecification/MoveLastSpeakerToTopTooltip')),
             ('checkbox',
              ('talkAutoJoinFleet', ('user', 'audio'), 1),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/ChannelSpecification/AutoJoinFleetVoice'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/ChannelSpecification/AutoJoinFleetVoiceTooltip')),
             ('checkbox',
              ('talkChannelPriority', ('user', 'audio'), 0),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/ChannelSpecification/ChannelPrioritize'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/ChannelSpecification/ChannelPrioritizeTooltip')),
             ('header', localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/Header')),
             ('toppush', 4),
             ('combo',
              ('talkBinding', ('user', 'audio'), 4),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/TalkKey'),
              keybindOptions,
              labelWidth),
             ('combo',
              ('TalkOutputDevice', ('user', 'audio'), 0),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/AudioOutputDevice'),
              outputOps,
              labelWidth),
             ('combo',
              ('TalkInputDevice', ('user', 'audio'), 0),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/AudioInputDevice'),
              inputOps,
              labelWidth),
             ('slider',
              ('TalkMicrophoneVolume', ('user', 'audio'), sm.GetService('vivox').defaultMicrophoneVolume),
              'UI/SystemMenu/AudioAndChat/GenericConfiguration/InputVolume',
              (0.0, 1.0),
              labelWidth),
             ('toppush', 4)]
            self.ParseData(vivoxData, col1)
            inputmeterpar = uiprimitives.Container(name='inputmeter', align=uiconst.TOTOP, height=12, parent=col1)
            if not sm.GetService('vivox').GetSpeakingChannel() == 'Echo':
                uix.GetContainerHeader(localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/TalkMeterInactive'), col1, 0)
            else:
                subpar = uiprimitives.Container(name='im_sub', align=uiconst.TORIGHT, width=col1.width - labelWidth - 11, parent=inputmeterpar)
                BumpedUnderlay(isInFocus=True, parent=subpar, width=-1)
                self.maxInputMeterWidth = subpar.width - 4
                self.sr.inputmeter = uiprimitives.Fill(parent=subpar, left=2, top=2, width=1, height=inputmeterpar.height - 4, align=uiconst.RELATIVE, color=(1.0, 1.0, 1.0, 0.25))
                uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/TalkMeter'), parent=inputmeterpar, top=2, state=uiconst.UI_NORMAL)
                sm.GetService('vivox').RegisterIntensityCallback(self)
                sm.GetService('vivox').StartAudioTest()
            if sm.GetService('vivox').GetSpeakingChannel() == 'Echo':
                echoBtnLabel = localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/StopEchoTest')
                echoTextString = localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/EchoTestInstructions')
            else:
                echoBtnLabel = localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/EchoTest')
                echoTextString = ''
            btnPar = uiprimitives.Container(name='push', align=uiconst.TOTOP, height=30, parent=col1)
            self.echoBtn = uicontrols.Button(parent=btnPar, label=echoBtnLabel, func=self.JoinLeaveEchoChannel, align=uiconst.CENTER)
            uiprimitives.Container(name='push', align=uiconst.TOTOP, height=8, parent=col1)
            self.echoText = uicontrols.EveLabelSmall(text=echoTextString, parent=col1, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        elif eve.session.userid and voiceChatMenuAvailable:
            vivoxData = (('header', localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/Header')),
             ('checkbox',
              ('voiceenabled', ('user', 'audio'), 1),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/EveVoiceEnabled'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/EveVoiceEnabledTooltip')),
             ('checkbox',
              ('talkMutesGameSounds', ('user', 'audio'), 0),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/MuteWhenITalk'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/MuteWhenITalkTooltip')),
             ('checkbox',
              ('listenMutesGameSounds', ('user', 'audio'), 0),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/MuteWhenOthersTalk'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/MuteWhenOthersTalkTooltip')),
             ('header', localization.GetByLabel('UI/SystemMenu/AudioAndChat/ChannelSpecification/Header')),
             ('text', localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/NotConnected')))
            self.ParseData(vivoxData, col1, 0)
        elif voiceChatMenuAvailable:
            vivoxData = (('header', localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceSettings/Header')),
             ('text', localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/NotLoggedIn')),
             ('header', localization.GetByLabel('UI/SystemMenu/AudioAndChat/ChannelSpecification/Header')),
             ('text', localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/NotConnected')))
            self.ParseData(vivoxData, col1, 0)
        self.sr.chatInited = 1
        if voiceChatMenuAvailable:
            if len(self.sr.chatPanels) < 2:
                col2 = uiprimitives.Container(name='column2', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
                col2.isTabOrderGroup = 1
                self.sr.chatPanels.append(col2)
            else:
                col2 = self.sr.chatPanels[1]
        else:
            col2 = col1
        BumpedUnderlay(isInFocus=True, parent=col2, idx=0)
        dblClickUserOps = [(localization.GetByLabel('UI/Commands/ShowInfo'), 0), (localization.GetByLabel('UI/Chat/StartConversation'), 1)]
        self.ParseData((('header', localization.GetByLabel('UI/SystemMenu/AudioAndChat/Chat/Header')),), col2, 0)
        if eve.session.userid:
            chatData = (('checkbox', ('logchat', ('user', 'ui'), 1), localization.GetByLabel('UI/SystemMenu/AudioAndChat/Chat/LogChatToFile')),
             ('checkbox', ('autoRejectInvitations', ('user', 'ui'), 0), localization.GetByLabel('UI/SystemMenu/AudioAndChat/Chat/AutoRejectInvitations')),
             ('toppush', 4),
             ('combo',
              ('dblClickUser', ('user', 'ui'), 0),
              localization.GetByLabel('UI/SystemMenu/AudioAndChat/Chat/OnDoubleClick'),
              dblClickUserOps,
              labelWidth),
             ('toppush', 4))
            if voiceChatMenuAvailable and sm.GetService('vivox').LoggedIn():
                chatData += (('header', localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceChatChannelSettings/Header')),
                 ('checkbox', ('chatJoinCorporationChannelOnLogin', ('user', 'ui'), 0), localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceChatChannelSettings/AutoJoinCorporation')),
                 ('checkbox', ('chatJoinAllianceChannelOnLogin', ('user', 'ui'), 0), localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceChatChannelSettings/AutoJoinAlliance')),
                 ('header', localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/Header')))
        else:
            chatData = (('text', localization.GetByLabel('UI/SystemMenu/AudioAndChat/GenericConfiguration/NotLoggedIn')),)
        self.ParseData(chatData, col2, 0)
        if eve.session.charid and voiceChatMenuAvailable and sm.GetService('vivox').LoggedIn():
            currentVoiceFont = settings.char.ui.Get('voiceFontName', localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/NoFontSelected'))
            currentVoiceFontText = uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/SelectedFont', selectedFont=currentVoiceFont), parent=col2, align=uiconst.TOTOP, top=4)
            btnPar = uiprimitives.Container(name='push', align=uiconst.TOTOP, height=30, parent=col2)
            self.voiceFontBtn = uicontrols.Button(parent=btnPar, label=localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/ChangeFont'), func=self.SelectVoiceFontDialog, args=(), align=uiconst.CENTER)
            uiprimitives.Container(name='push', align=uiconst.TOTOP, height=8, parent=col2)

    def SelectVoiceFontDialog(self):
        wnd = form.VoiceFontSelectionWindow.GetIfOpen()
        if wnd is None:
            wnd = form.VoiceFontSelectionWindow.Open()
            wnd.ShowModal()

    def Displayandgraphics(self):
        if self.sr.displayandgraphicsinited:
            return
        parent = uiutil.GetChild(self.sr.wnd, 'displayandgraphics_container')
        column = uiprimitives.Container(name='column', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
        column.isTabOrderGroup = 1
        BumpedUnderlay(isInFocus=True, parent=column, idx=0)
        self.sr.monitorsetup = column
        self.InitDeviceSettings()
        self.ProcessDeviceSettings()
        if eve.session.userid:
            column = uiprimitives.Container(name='column', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
            column.isTabOrderGroup = 1
            BumpedUnderlay(isInFocus=True, parent=column, idx=0)
            self.sr.graphicssetup = column
        column = uiprimitives.Container(name='column', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
        column.isTabOrderGroup = 1
        BumpedUnderlay(isInFocus=True, parent=column, idx=0)
        self.sr.graphicssetup2 = column
        self.ProcessGraphicsSettings()
        self.sr.displayandgraphicsinited = 1

    def ProcessGraphicsSettings(self, status = None):
        where = self.sr.Get('graphicssetup', None)
        where2 = self.sr.Get('graphicssetup2', None)
        deviceSvc = sm.GetService('device')
        if where:
            uiutil.FlushList(where.children[1:])
        if where2:
            uiutil.FlushList(where2.children[1:])
        message = None
        graphicsData = []
        graphicsData2 = [('header', localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/Header')), ('text', localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/Description'))]
        shaderQualityOptions = [(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/LowQuality'), 1), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/MediumQuality'), 2)]
        if gfxsettings.MAX_SHADER_MODEL == gfxsettings.SHADER_MODEL_HIGH:
            shaderQualityOptions.append((localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/HighQuality'), 3))
        try:
            shaderQualityMenu = [('combo',
              (gfxsettings.GetSettingKey(gfxsettings.GFX_SHADER_QUALITY), None, gfxsettings.GetPendingOrCurrent(gfxsettings.GFX_SHADER_QUALITY)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/ShaderQuality'),
              shaderQualityOptions,
              LEFTPADDING,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/ShaderQualityTooltip'))]
        except:
            log.LogException()

        textureQualityOptions = [(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/LowQuality'), 2), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/MediumQuality'), 1), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/HighQuality'), 0)]
        textureQualityMenu = [('combo',
          (gfxsettings.GetSettingKey(gfxsettings.GFX_TEXTURE_QUALITY), None, gfxsettings.GetPendingOrCurrent(gfxsettings.GFX_TEXTURE_QUALITY)),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/TextureQuality'),
          textureQualityOptions,
          LEFTPADDING,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/TextureQualityTooltip'))]
        lodQualityOptions = [(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/LowQuality'), 1), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/MediumQuality'), 2), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/HighQuality'), 3)]
        lodQualityMenu = [('combo',
          (gfxsettings.GetSettingKey(gfxsettings.GFX_LOD_QUALITY), None, gfxsettings.GetPendingOrCurrent(gfxsettings.GFX_LOD_QUALITY)),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/LODQuality'),
          lodQualityOptions,
          LEFTPADDING,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/LODQualityTooltip'))]
        shadowQualityOptions = [(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/Disabled'), 0), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/LowQuality'), 1), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/HighQuality'), 2)]
        shadowQualityMenu = [('combo',
          (gfxsettings.GetSettingKey(gfxsettings.GFX_SHADOW_QUALITY), None, gfxsettings.GetPendingOrCurrent(gfxsettings.GFX_SHADOW_QUALITY)),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/ShadowQuality'),
          shadowQualityOptions,
          LEFTPADDING,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/ShadowQualityTooltip'))]
        interiorQualityOptions = [(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/LowQuality'), 0), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/MediumQuality'), 1), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/HighQuality'), 2)]
        interiorQualityMenu = [('combo',
          (gfxsettings.GetSettingKey(gfxsettings.GFX_INTERIOR_GRAPHICS_QUALITY), None, gfxsettings.GetPendingOrCurrent(gfxsettings.GFX_INTERIOR_GRAPHICS_QUALITY)),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/InteriorQuality'),
          interiorQualityOptions,
          LEFTPADDING,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/InteriorQualityTooltip'))]
        interiorShaderQualityOptions = [(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/LowQuality'), 0), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/HighQuality'), 1)]
        interiorShaderQualityMenu = [('combo',
          (gfxsettings.GetSettingKey(gfxsettings.GFX_INTERIOR_SHADER_QUALITY), None, gfxsettings.GetPendingOrCurrent(gfxsettings.GFX_INTERIOR_SHADER_QUALITY)),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/InteriorShaderQuality'),
          interiorShaderQualityOptions,
          LEFTPADDING,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/InteriorShaderQualityTooltip'))]
        graphicsData2 += [('checkbox',
          (gfxsettings.GetSettingKey(gfxsettings.MISC_RESOURCE_CACHE_ENABLED), None, bool(gfxsettings.GetPendingOrCurrent(gfxsettings.MISC_RESOURCE_CACHE_ENABLED))),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/ResourceCache'),
          None,
          None,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/ResourceCacheTooltip'))]
        graphicsData2 += [('checkbox',
          (gfxsettings.GetSettingKey(gfxsettings.GFX_HDR_ENABLED), None, bool(gfxsettings.GetPendingOrCurrent(gfxsettings.GFX_HDR_ENABLED))),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/HDR'),
          None,
          None,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/HDRTooltip'))]
        graphicsData2 += [('checkbox',
          (gfxsettings.GetSettingKey(gfxsettings.MISC_LOAD_STATION_ENV), None, gfxsettings.GetPendingOrCurrent(gfxsettings.MISC_LOAD_STATION_ENV)),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/LoadStationEnvironment'),
          None,
          None,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/LoadStationEnvironmentTooltip'))]
        formats = [(self.settings.BackBufferFormat, True), (self.settings.AutoDepthStencilFormat, False), (trinity.PIXEL_FORMAT.R16G16B16A16_FLOAT, True)]
        options = deviceSvc.GetMultiSampleQualityOptions(self.settings, formats)
        graphicsData2.append(('combo',
         (gfxsettings.GetSettingKey(gfxsettings.GFX_ANTI_ALIASING), None, gfxsettings.GetPendingOrCurrent(gfxsettings.GFX_ANTI_ALIASING)),
         localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/AntiAliasing'),
         options,
         LEFTPADDING,
         localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/AntiAliasingTooltip')))
        postProcessingQualityOptions = [(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/NoneLabel'), 0), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/LowQuality'), 1), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/HighQuality'), 2)]
        graphicsData2 += [('combo',
          (gfxsettings.GetSettingKey(gfxsettings.GFX_POST_PROCESSING_QUALITY), None, gfxsettings.GetPendingOrCurrent(gfxsettings.GFX_POST_PROCESSING_QUALITY)),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/PostProcessing'),
          postProcessingQualityOptions,
          LEFTPADDING,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/PostProcessingTooltip'))]
        graphicsData2 += shaderQualityMenu
        graphicsData2 += textureQualityMenu
        graphicsData2 += lodQualityMenu
        graphicsData2 += shadowQualityMenu
        graphicsData2 += interiorQualityMenu
        graphicsData2 += interiorShaderQualityMenu
        if eve.session.userid:
            graphicsData += [('header', localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/Header')),
             ('checkbox',
              (gfxsettings.GetSettingKey(gfxsettings.UI_TURRETS_ENABLED), None, gfxsettings.GetPendingOrCurrent(gfxsettings.UI_TURRETS_ENABLED)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/TurretEffects'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/TurretEffectsTooltip')),
             ('checkbox',
              (gfxsettings.GetSettingKey(gfxsettings.UI_EFFECTS_ENABLED), None, gfxsettings.GetPendingOrCurrent(gfxsettings.UI_EFFECTS_ENABLED)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/Effects'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/EffectsTooltip')),
             ('checkbox',
              (gfxsettings.GetSettingKey(gfxsettings.UI_MISSILES_ENABLED), None, gfxsettings.GetPendingOrCurrent(gfxsettings.UI_MISSILES_ENABLED)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/MissileEffects'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/EffectsTooltip')),
             ('checkbox',
              (gfxsettings.GetSettingKey(gfxsettings.UI_CAMERA_SHAKE_ENABLED), None, gfxsettings.GetPendingOrCurrent(gfxsettings.UI_CAMERA_SHAKE_ENABLED)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/CameraShake'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/CameraShakeTooltip')),
             ('checkbox',
              (gfxsettings.GetSettingKey(gfxsettings.UI_EXPLOSION_EFFECTS_ENABLED), None, gfxsettings.GetPendingOrCurrent(gfxsettings.UI_EXPLOSION_EFFECTS_ENABLED)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/ShipExplosions'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/ShipExplosionsTooltip')),
             ('checkbox',
              (gfxsettings.GetSettingKey(gfxsettings.UI_DRONE_MODELS_ENABLED), None, gfxsettings.GetPendingOrCurrent(gfxsettings.UI_DRONE_MODELS_ENABLED)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/DroneModels'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/DroneModelsTooltip')),
             ('checkbox',
              (gfxsettings.GetSettingKey(gfxsettings.UI_TRAILS_ENABLED), None, gfxsettings.GetPendingOrCurrent(gfxsettings.UI_TRAILS_ENABLED)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/Trails'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/TrailsTooltip')),
             ('checkbox',
              (gfxsettings.GetSettingKey(gfxsettings.UI_GPU_PARTICLES_ENABLED), None, gfxsettings.GetPendingOrCurrent(gfxsettings.UI_GPU_PARTICLES_ENABLED)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/GPUParticles'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/GPUParticlesTooltip')),
             ('checkbox',
              (gfxsettings.GetSettingKey(gfxsettings.UI_ASTEROID_ATMOSPHERICS), None, gfxsettings.GetPendingOrCurrent(gfxsettings.UI_ASTEROID_ATMOSPHERICS)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/AsteroidEnvironments'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/AsteroidEnvironmentsTooltip')),
             ('checkbox',
              (gfxsettings.GetSettingKey(gfxsettings.UI_GODRAYS), None, gfxsettings.GetPendingOrCurrent(gfxsettings.UI_GODRAYS)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/Godrays'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Effects/GodraysTooltip')),
             ('header', localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Miscellaneous/Header')),
             ('checkbox',
              (gfxsettings.GetSettingKey(gfxsettings.UI_ADVANCED_CAMERA), None, gfxsettings.GetPendingOrCurrent(gfxsettings.UI_ADVANCED_CAMERA)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Miscellaneous/AdvancedCameraMenu'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Miscellaneous/AdvancedCameraMenuTooltip')),
             ('checkbox',
              (gfxsettings.GetSettingKey(gfxsettings.UI_NCC_GREEN_SCREEN), None, gfxsettings.GetPendingOrCurrent(gfxsettings.UI_NCC_GREEN_SCREEN)),
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Miscellaneous/EnableGreenscreen'),
              None,
              None,
              localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Miscellaneous/EnableGreenscreenMenuTooltip'))]
            if sm.GetService('lightFx').IsLightFxSupported():
                graphicsData += [('checkbox',
                  ('LightFxEnabled', ('user', 'ui'), 1),
                  localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Miscellaneous/LightLEDEffect'),
                  None,
                  None,
                  localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Miscellaneous/LightLEDEffectTooltip'))]
        graphicsData += (('header', localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/CharacterCreation/Header')),)
        currentFastCharacterCreationValue = gfxsettings.GetPendingOrCurrent(gfxsettings.GFX_CHAR_FAST_CHARACTER_CREATION)
        currentClothSimValue = gfxsettings.GetPendingOrCurrent(gfxsettings.GFX_CHAR_CLOTH_SIMULATION)
        graphicsData += [('checkbox',
          (gfxsettings.GetSettingKey(gfxsettings.GFX_CHAR_FAST_CHARACTER_CREATION), None, currentFastCharacterCreationValue),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/CharacterCreation/LowQualityCharacters'),
          None,
          None,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/CharacterCreation/LowQualityCharactersTooltip'),
          None,
          False)]
        graphicsData += [('checkbox',
          (gfxsettings.GetSettingKey(gfxsettings.GFX_CHAR_CLOTH_SIMULATION), None, currentClothSimValue),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/CharacterCreation/ClothHairSim'),
          None,
          None,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/CharacterCreation/ClothHairSimTooltip'),
          None,
          False)]
        charTextureQualityOptions = [(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/LowQuality'), 2), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/MediumQuality'), 1), (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/HighQuality'), 0)]
        graphicsData += [('combo',
          (gfxsettings.GetSettingKey(gfxsettings.GFX_CHAR_TEXTURE_QUALITY), None, gfxsettings.GetPendingOrCurrent(gfxsettings.GFX_CHAR_TEXTURE_QUALITY)),
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/CharacterCreation/TextureQuality'),
          charTextureQualityOptions,
          LEFTPADDING,
          localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/CharacterCreation/TextureQualityTooltip'))]
        if message is not None:
            graphicsData2 += [('text', message, 'dlMessage')]
        if where:
            self.ParseData(graphicsData, where, validateEntries=0)
        if where2:
            self.ParseData(graphicsData2, where2, validateEntries=0)
            optSettingsPar = uiprimitives.Container(name='optSettingsPar', parent=where2, align=uiconst.TOTOP, height=24)
            btn = uicontrols.Button(parent=optSettingsPar, label=localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/OptimizeSettings'), func=self.OpenOptimizeSettings, args=(), align=uiconst.CENTERTOP)
            bottomBtnPar = uiprimitives.Container(name='bottomBtnPar', parent=where2, align=uiconst.CENTERBOTTOM, height=32)
            bottomLeftCounter = 0
            btn = uicontrols.Button(parent=bottomBtnPar, label=localization.GetByLabel('UI/Common/Buttons/Apply'), func=self.ApplyGraphicsSettings, args=(), pos=(bottomLeftCounter,
             0,
             0,
             0))
            bottomLeftCounter += btn.width + 2
            btn = uicontrols.Button(parent=bottomBtnPar, label=localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/ResetGraphicSettings'), func=self.ResetGraphicsSettings, args=(), pos=(bottomLeftCounter,
             0,
             0,
             0))
            bottomLeftCounter += btn.width + 2
            bottomBtnPar.width = bottomLeftCounter

    def OpenOptimizeSettings(self):
        optimizeWnd = OptimizeSettingsWindow.GetIfOpen()
        if optimizeWnd is None:
            self.optimizeWnd = OptimizeSettingsWindow.Open()
            self.optimizeWnd.ShowModal()
            self.ApplyGraphicsSettings()
            sm.GetService('sceneManager').ApplyClothSimulationSettings()
        else:
            self.optimizeWnd = optimizeWnd

    def ResetGraphicsSettings(self):
        gfxsettings.SetDefault(gfxsettings.GFX_HDR_ENABLED)
        gfxsettings.SetDefault(gfxsettings.GFX_POST_PROCESSING_QUALITY)
        gfxsettings.SetDefault(gfxsettings.MISC_RESOURCE_CACHE_ENABLED)
        gfxsettings.SetDefault(gfxsettings.GFX_TEXTURE_QUALITY)
        gfxsettings.SetDefault(gfxsettings.GFX_SHADER_QUALITY)
        gfxsettings.SetDefault(gfxsettings.GFX_LOD_QUALITY)
        gfxsettings.SetDefault(gfxsettings.GFX_CHAR_FAST_CHARACTER_CREATION)
        gfxsettings.SetDefault(gfxsettings.GFX_CHAR_TEXTURE_QUALITY)
        gfxsettings.SetDefault(gfxsettings.GFX_INTERIOR_GRAPHICS_QUALITY)
        gfxsettings.SetDefault(gfxsettings.GFX_SHADOW_QUALITY)
        gfxsettings.SetDefault(gfxsettings.MISC_LOAD_STATION_ENV)
        if session.userid:
            gfxsettings.SetDefault(gfxsettings.UI_TURRETS_ENABLED)
            gfxsettings.SetDefault(gfxsettings.UI_EFFECTS_ENABLED)
            gfxsettings.SetDefault(gfxsettings.UI_MISSILES_ENABLED)
            gfxsettings.SetDefault(gfxsettings.UI_TRAILS_ENABLED)
            gfxsettings.SetDefault(gfxsettings.UI_ADVANCED_CAMERA)
            gfxsettings.SetDefault(gfxsettings.UI_NCC_GREEN_SCREEN)
            gfxsettings.SetDefault(gfxsettings.UI_CAMERA_OFFSET)
            gfxsettings.SetDefault(gfxsettings.UI_INCARNA_CAMERA_OFFSET)
            gfxsettings.SetDefault(gfxsettings.UI_INCARNA_CAMERA_INVERT_Y)
            gfxsettings.SetDefault(gfxsettings.UI_INCARNA_CAMERA_MOUSE_LOOK_SPEED)
            gfxsettings.SetDefault(gfxsettings.UI_ASTEROID_ATMOSPHERICS)
            gfxsettings.SetDefault(gfxsettings.UI_GODRAYS)
        self.ApplyGraphicsSettings()

    def ApplyGraphicsSettings(self):
        if not self.settings:
            return
        deviceSvc = sm.GetService('device')
        dev = trinity.device
        changes = gfxsettings.ApplyPendingChanges(gfxsettings.SETTINGS_GROUP_DEVICE)
        if session.userid:
            changes.extend(gfxsettings.ApplyPendingChanges(gfxsettings.SETTINGS_GROUP_UI))
        if gfxsettings.MISC_RESOURCE_CACHE_ENABLED in changes:
            deviceSvc.SetResourceCacheSize()
        if gfxsettings.GFX_LOD_QUALITY in changes:
            lodQuality = gfxsettings.Get(gfxsettings.GFX_LOD_QUALITY)
            if lodQuality == 1:
                trinity.settings.SetValue('eveSpaceSceneVisibilityThreshold', 15.0)
                trinity.settings.SetValue('eveSpaceSceneLowDetailThreshold', 140.0)
                trinity.settings.SetValue('eveSpaceSceneMediumDetailThreshold', 480.0)
            elif lodQuality == 2:
                trinity.settings.SetValue('eveSpaceSceneVisibilityThreshold', 6.0)
                trinity.settings.SetValue('eveSpaceSceneLowDetailThreshold', 70.0)
                trinity.settings.SetValue('eveSpaceSceneMediumDetailThreshold', 240.0)
            elif lodQuality == 3:
                trinity.settings.SetValue('eveSpaceSceneVisibilityThreshold', 3.0)
                trinity.settings.SetValue('eveSpaceSceneLowDetailThreshold', 35.0)
                trinity.settings.SetValue('eveSpaceSceneMediumDetailThreshold', 120.0)
        interiorShaderQuality = gfxsettings.Get(gfxsettings.GFX_INTERIOR_SHADER_QUALITY)
        if gfxsettings.GFX_INTERIOR_SHADER_QUALITY in changes:
            flag = trinity.HasGlobalSituationFlag('OPT_INTERIOR_SM_HIGH')
            if interiorShaderQuality == 0 and flag:
                trinity.RemoveGlobalSituationFlags(['OPT_INTERIOR_SM_HIGH'])
            elif not flag:
                trinity.AddGlobalSituationFlags(['OPT_INTERIOR_SM_HIGH'])
            trinity.RebindAllShaderMaterials()
        if gfxsettings.GFX_SHADER_QUALITY in changes:
            message = uicls.Message(className='Message', parent=uicore.layer.modal, name='msgDeviceReset')
            message.ShowMsg(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/ApplyingSettings'))
            blue.synchro.SleepWallclock(200)
            trinity.SetShaderModel(deviceSvc.GetShaderModel(gfxsettings.Get(gfxsettings.GFX_SHADER_QUALITY)))
            message.Close()
        if gfxsettings.GFX_TEXTURE_QUALITY in changes:
            dev.mipLevelSkipCount = gfxsettings.Get(gfxsettings.GFX_TEXTURE_QUALITY)
            dev.RefreshDeviceResources()
        if not self.closing:
            self.ProcessGraphicsSettings()
        if len(changes) > 0:
            sm.ScatterEvent('OnGraphicSettingsChanged', changes)

    def Shortcuts(self):
        if self.sr.shortcutsinited:
            return
        parent = uiutil.GetChild(self.sr.wnd, 'shortcuts_container')
        parent.Load = self.LoadShortcutTabs
        parent.Flush()
        tabs = []
        categories = [('window', localization.GetByLabel('UI/SystemMenu/Shortcuts/WindowTab')),
         ('combat', localization.GetByLabel('UI/SystemMenu/Shortcuts/CombatTab')),
         ('general', localization.GetByLabel('UI/SystemMenu/Shortcuts/GeneralTab')),
         ('navigation', localization.GetByLabel('UI/SystemMenu/Shortcuts/NavigationTab')),
         ('modules', localization.GetByLabel('UI/SystemMenu/Shortcuts/ModulesTab')),
         ('drones', localization.GetByLabel('UI/SystemMenu/Shortcuts/DronesTab')),
         ('charactercreator', localization.GetByLabel('UI/CharacterCreation')),
         ('movement', localization.GetByLabel('UI/SystemMenu/Shortcuts/CharacterMovementTab'))]
        for category, label in categories:
            if category in uicore.cmd.GetCommandCategoryNames():
                tabs.append([label,
                 None,
                 parent,
                 category])

        self.sr.shortcutTabs = uicontrols.TabGroup(name='tabs', parent=parent, padBottom=5, tabs=tabs, groupID='tabs', autoselecttab=1, idx=0)
        col2 = uiprimitives.Container(name='column2', parent=parent)
        col2.isTabOrderGroup = 1
        shortcutoptions = uiprimitives.Container(name='options', align=uiconst.TOBOTTOM, height=30, top=0, parent=col2, padding=(5, 0, 5, 0))
        btns = [(localization.GetByLabel('UI/SystemMenu/Shortcuts/EditShortcut'), self.OnEditShortcutBtnClicked, None), (localization.GetByLabel('UI/SystemMenu/Shortcuts/ClearShortcut'), self.OnClearShortcutBtnClicked, None)]
        btnGroup = uicontrols.ButtonGroup(btns=btns, parent=shortcutoptions, line=False, subalign=uiconst.BOTTOMLEFT)
        btn = uicontrols.Button(parent=shortcutoptions, label=localization.GetByLabel('UI/SystemMenu/Shortcuts/DefaultShortcuts'), func=self.RestoreShortcuts, top=0, align=uiconst.BOTTOMRIGHT)
        self.sr.active_cmdscroll = uicontrols.Scroll(name='availscroll', align=uiconst.TOALL, parent=col2, padLeft=8, multiSelect=False, id='active_cmdscroll')
        self.sr.shortcutsinited = 1

    def OnEditShortcutBtnClicked(self, *args):
        selected = self.sr.active_cmdscroll.GetSelected()
        if not selected:
            return
        p = selected[0].panel
        p.Edit()

    def OnClearShortcutBtnClicked(self, *args):
        selected = self.sr.active_cmdscroll.GetSelected()
        if not selected:
            return
        self.ClearCommand(selected[0].cmdname)

    def LoadShortcutTabs(self, key):
        self.ReloadCommands(key)

    def Resetsettings(self, reload = 0):
        if self.sr.resetsettingsinited:
            return
        parent = uiutil.GetChild(self.sr.wnd, 'reset settings_container')
        scrollTo = None
        suppressScrollTo = None
        defaultScrollTo = None
        if reload:
            scroll = uiutil.FindChild(parent, 'tutorialResetScroll')
            if scroll:
                scrollTo = scroll.GetScrollProportion()
            scroll = uiutil.FindChild(parent, 'suppressResetScroll')
            if scroll:
                suppressScrollTo = scroll.GetScrollProportion()
            scroll = uiutil.FindChild(parent, 'defaultResetScroll')
            if scroll:
                defaultScrollTo = scroll.GetScrollProportion()
        uix.Flush(parent)
        col1 = uiprimitives.Container(name='col1', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
        col1.isTabOrderGroup = 1
        BumpedUnderlay(isInFocus=True, parent=col1)
        uix.GetContainerHeader(localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/Header'), col1, 0)
        scroll = uicontrols.Scroll(parent=col1)
        scroll.name = 'suppressResetScroll'
        scroll.HideBackground()
        scrollList = []
        i = 0
        for each in settings.user.suppress.GetValues().keys():
            label = self.GetConfigName(each)
            entry = listentry.Get('Button', {'label': label,
             'caption': localization.GetByLabel('UI/SystemMenu/ResetSettings/Reset'),
             'OnClick': self.ConfigBtnClick,
             'args': (each,),
             'maxLines': None,
             'entryWidth': self.colWidth - 16})
            scrollList.append((label, entry))

        scrollList = uiutil.SortListOfTuples(scrollList)
        scroll.Load(contentList=scrollList, scrollTo=suppressScrollTo)
        col2 = uiprimitives.Container(name='column2', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
        col2.isTabOrderGroup = 1
        BumpedUnderlay(isInFocus=True, parent=col2)
        uix.GetContainerHeader(localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetToDefault/Header'), col2, (0, 1)[i >= 12])
        scroll = uicontrols.Scroll(parent=col2)
        scroll.name = 'defaultsResetScroll'
        scroll.HideBackground()
        scrollList = []
        lst = [{'label': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetToDefault/WindowPosition'),
          'caption': localization.GetByLabel('UI/SystemMenu/ResetSettings/Reset'),
          'OnClick': self.ResetBtnClick,
          'args': 'windows'},
         {'label': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetToDefault/WindowColors'),
          'caption': localization.GetByLabel('UI/SystemMenu/ResetSettings/Reset'),
          'OnClick': self.ResetBtnClick,
          'args': 'window color'},
         {'label': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetToDefault/ClearAllSettings'),
          'caption': localization.GetByLabel('UI/SystemMenu/ResetSettings/Clear'),
          'OnClick': self.ResetBtnClick,
          'args': 'clear settings'},
         {'label': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetToDefault/ClearAllCacheFiles'),
          'caption': localization.GetByLabel('UI/SystemMenu/ResetSettings/Clear'),
          'OnClick': self.ResetBtnClick,
          'args': 'clear cache'}]
        if session.charid:
            lst.append({'label': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetToDefault/ClearMailCache'),
             'caption': localization.GetByLabel('UI/SystemMenu/ResetSettings/Clear'),
             'OnClick': self.ResetBtnClick,
             'args': 'clear mail'})
            lst.append({'label': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetToDefault/NeocomButtons'),
             'caption': localization.GetByLabel('UI/SystemMenu/ResetSettings/Reset'),
             'OnClick': self.ResetBtnClick,
             'args': 'reset neocom'})
        if hasattr(sm.GetService('LSC'), 'spammerList'):
            lst.append({'label': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetToDefault/ClearISKSpammerList'),
             'caption': localization.GetByLabel('UI/SystemMenu/ResetSettings/Clear'),
             'OnClick': self.ResetBtnClick,
             'args': 'clear iskspammers'})
        for each in lst:
            scrollList.append(listentry.Get('Button', {'label': each['label'],
             'caption': each['caption'],
             'OnClick': each['OnClick'],
             'args': (each['args'],),
             'maxLines': None,
             'entryWidth': self.colWidth - 16}))

        scroll.Load(contentList=scrollList, scrollTo=suppressScrollTo)
        tutorials = sm.GetService('tutorial').GetTutorials()
        if tutorials:
            col3 = uiprimitives.Container(name='column3', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
            col3.isTabOrderGroup = 1
            BumpedUnderlay(isInFocus=True, parent=col3)
            uix.GetContainerHeader(localization.GetByLabel('UI/SystemMenu/ResetSettings/Tutorial/Header'), col3, 0)
            scroll = uicontrols.Scroll(parent=col3)
            scroll.name = 'tutorialResetScroll'
            scroll.HideBackground()
            all = sm.GetService('tutorial').GetValidTutorials()
            scrollList = []
            for tutorialID in all:
                if tutorialID not in tutorials:
                    continue
                seqStat = sm.GetService('tutorial').GetSequenceStatus(tutorialID)
                if seqStat:
                    label = localization.GetByMessageID(tutorials[tutorialID].tutorialNameID)
                    entry = listentry.Get('Button', {'label': label,
                     'caption': localization.GetByLabel('UI/SystemMenu/ResetSettings/Reset'),
                     'OnClick': self.TutorialResetBtnClick,
                     'args': (tutorialID,),
                     'maxLines': None,
                     'entryWidth': self.colWidth - 16})
                    scrollList.append((label, entry))

            scrollList = uiutil.SortListOfTuples(scrollList)
            scroll.Load(contentList=scrollList, scrollTo=scrollTo)
        self.sr.resetsettingsinited = 1

    def RefreshLanguage(self, allUI = True):
        """
        Function to call to refresh the Language tab when things change.
        """
        self.sr.languageinited = 0
        if allUI:
            sm.ChainEvent('ProcessUIRefresh')
            sm.ScatterEvent('OnUIRefresh')
        else:
            parent = uiutil.GetChild(self.sr.wnd, 'language_container')
            if parent:
                uix.Flush(parent)
                self.sr.languageinited = 0
                self.Language()

    def Language(self):
        """
        Language tab
        """
        if self.sr.languageinited:
            return
        parent = uiutil.GetChild(self.sr.wnd, 'language_container')
        self._ShowLanguageSelectionOptions(parent)
        column2 = self._ShowIMEAndVoiceOptions(parent)
        self._ShowPseudolocOptions(parent, column2)
        self.sr.languageinited = 1

    def _ShowLanguageSelectionOptions(self, parent):
        if boot.region == 'optic' and not eve.session.role & service.ROLEMASK_ELEVATEDPLAYER:
            return
        langs = localization.GetLanguages()
        serverOnlyLanguages = ['it', 'es']
        for badLanguage in serverOnlyLanguages:
            if badLanguage in langs:
                langs.remove(badLanguage)

        if blue.win32.IsTransgaming():
            langs.remove('ja')
        mlsToDisplayNameLabel = {'JA': localization.GetByLabel('UI/SystemMenu/Language/LanguageJapanese'),
         'DE': localization.GetByLabel('UI/SystemMenu/Language/LanguageGerman'),
         'EN': localization.GetByLabel('UI/SystemMenu/Language/LanguageEnglish'),
         'FR': localization.GetByLabel('UI/SystemMenu/Language/LanguageFrench'),
         'RU': localization.GetByLabel('UI/SystemMenu/Language/LanguageRussian'),
         'ZH': localization.GetByLabel('UI/SystemMenu/Language/LanguageChinese')}
        if len(langs) > 1:
            column1 = uiprimitives.Container(name='language_column_1', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
            column1.isTabOrderGroup = 1
            BumpedUnderlay(isInFocus=True, parent=column1)
            languageData = [('header', localization.GetByLabel('UI/SystemMenu/Language/Header'))]
            self.ParseData(languageData, column1)
            setLanguageID = getattr(self, 'setlanguageID', None)
            gameLanguageID = session.languageID if session.userid else prefs.languageID
            currentLang = setLanguageID or gameLanguageID
            for lang in langs:
                convertedID = localization.util.ConvertLanguageIDToMLS(lang)
                text = mlsToDisplayNameLabel[convertedID]
                checkbox = uicontrols.Checkbox(parent=column1, name='languageCheckbox_%s' % lang, text=text, retval=convertedID, groupname='languageSelection', checked=convertedID == currentLang, fontsize=12, configName='language', callback=self.OnCheckBoxChange)

            currentLanguageString = mlsToDisplayNameLabel[currentLang]
            impNameOptions = [(currentLanguageString, 0), (localization.GetByLabel('UI/SystemMenu/Language/EnglishReplacement'), localization.const.IMPORTANT_EN_OVERRIDE)]
            showTooltipOptions = setLanguageID and not localization.IsPrimaryLanguage(setLanguageID) or not setLanguageID and not localization.IsPrimaryLanguage(gameLanguageID)
            if showTooltipOptions:
                if not hasattr(self, 'setImpNameSetting'):
                    self.setImpNameSetting = localization.settings.bilingualSettings.GetValue('localizationImportantNames')
                if not hasattr(self, 'setLanguageTooltip'):
                    self.setLanguageTooltip = localization.settings.bilingualSettings.GetValue('languageTooltip')
                if not hasattr(self, 'setLocalizationHighlightImportant'):
                    self.setLocalizationHighlightImportant = localization.settings.bilingualSettings.GetValue('localizationHighlightImportant')
                if self.setImpNameSetting == localization.const.IMPORTANT_EN_OVERRIDE:
                    checkboxCaption = localization.GetByLabel('UI/SystemMenu/Language/ShowTooltipInLanguage', language=currentLanguageString)
                else:
                    english = mlsToDisplayNameLabel['EN']
                    checkboxCaption = localization.GetByLabel('UI/SystemMenu/Language/ShowTooltipInLanguage', language=english)
                highlightImportant = localization.GetByLabel('UI/SystemMenu/Language/HighlightImportantNames')
                impNameData = [('header', localization.GetByLabel('UI/SystemMenu/Language/ImportantNames')),
                 ('combo',
                  ('localizationImportantNames', None, self.setImpNameSetting),
                  localization.GetByLabel('UI/SystemMenu/Language/Display'),
                  impNameOptions,
                  LEFTPADDING,
                  localization.GetByLabel('UI/SystemMenu/Language/ImportantNamesExplanation')),
                 ('checkbox', ('languageTooltip', None, self.setLanguageTooltip), checkboxCaption),
                 ('checkbox', ('highlightImportant', None, self.setLocalizationHighlightImportant), highlightImportant)]
            else:
                impNameData = []
            impNameData.append(('button',
             None,
             localization.GetByLabel('UI/SystemMenu/Language/ApplyLanguageSettings'),
             self.ApplyLanguageSettings))
            self.ParseData(impNameData, column1)

    def _ShowIMEAndVoiceOptions(self, parent):
        column2 = uiprimitives.Container(name='language_column_2', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
        column2.isTabOrderGroup = 1
        BumpedUnderlay(isInFocus=True, parent=column2)
        if boot.region != 'optic' or eve.session.role & service.ROLEMASK_ELEVATEDPLAYER:
            columnData = [('header', localization.GetByLabel('UI/SystemMenu/Language/InputMethodEditor/Header')), ('checkbox', ('nativeIME', ('user', 'ui'), True), localization.GetByLabel('UI/SystemMenu/Language/InputMethodEditor/UseEveIME'))]
            self.ParseData(columnData, column2)
        columnData = [('header', localization.GetByLabel('UI/SystemMenu/Language/VoiceOptions/Header')), ('checkbox', ('forceEnglishVoice', ('public', 'audio'), False), localization.GetByLabel('UI/SystemMenu/Language/VoiceOptions/ForceEnglishVoice'))]
        self.ParseData(columnData, column2)
        return column2

    def _ShowPseudolocOptions(self, parent, column2):
        column3 = uiprimitives.Container(name='language_column_3', align=uiconst.TOLEFT, width=self.colWidth, padLeft=8, parent=parent)
        column3.isTabOrderGroup = 1
        BumpedUnderlay(isInFocus=True, parent=column3)
        if session and session.charid and session.role & service.ROLE_QA == service.ROLE_QA:
            self.DisplayLocalizationQAOptions(column2)
            self.DisplayPseudolocalizationSample(column3)

    def DisplayLocalizationQAOptions(self, column):
        qaSettings = localization.settings.qaSettings
        if not hasattr(self, 'setShowMessageID'):
            self.setShowMessageID = qaSettings.GetValue('showMessageID')
        if not hasattr(self, 'setEnableBoundaryMarkers'):
            self.setEnableBoundaryMarkers = qaSettings.GetValue('enableBoundaryMarkers')
        if not hasattr(self, 'setShowHardcodedStrings'):
            self.setShowHardcodedStrings = qaSettings.GetValue('showHardcodedStrings')
        if not hasattr(self, 'setSimulateTooltip'):
            self.setSimulateTooltip = qaSettings.GetValue('simulateTooltip')
        if not hasattr(self, 'setEnableTextExpansion'):
            self.setEnableTextExpansion = qaSettings.GetValue('textExpansionAmount') > 0
        if not hasattr(self, 'setCharacterReplacementMethod'):
            self.setCharacterReplacementMethod = qaSettings.GetValue('characterReplacementMethod')
        if not hasattr(self, 'setTextExpansionAmount'):
            self.setTextExpansionAmount = qaSettings.GetValue('textExpansionAmount')
        localizationQAOptions = [('header', 'Localization QA Options'),
         ('checkbox', ('simulateTooltip', None, self.setSimulateTooltip), 'Simulate Tooltip (cancels other options)'),
         ('checkbox', ('showMessageID', None, self.setShowMessageID), 'Show MessageID'),
         ('checkbox', ('enableBoundaryMarkers', None, self.setEnableBoundaryMarkers), 'Show Boundary Markers'),
         ('checkbox', ('showHardcodedStrings', None, self.setShowHardcodedStrings), 'Show Hardcoded Strings')]
        if localization.IsPrimaryLanguage(localization.util.GetLanguageID()):
            conversionMethodOptions = [('&lt; Select &gt;', -1),
             ('No Simulation', 0),
             ('Simulate German', 1),
             ('Simulate Russian', 2),
             ('Simulate Japanese', 3)]
            if not hasattr(self, 'chosenPseudolocPreset'):
                self.chosenPseudolocPreset = -1
            localizationQAOptions += [('combo',
              ('pseudolocalizationPreset', None, self.chosenPseudolocPreset),
              'Simulation Preset',
              conversionMethodOptions,
              LEFTPADDING,
              'Simulation presets auto-configure the pseudolocalization settings to test for common localization issues.')]
            replacementMethodOptions = [('No Replacement', localization.settings.qaSettings.NO_REPLACEMENT),
             ('Diacritic Replacement', localization.settings.qaSettings.DIACRITIC_REPLACEMENT),
             ('Cyrillic Replacement', localization.settings.qaSettings.CYRILLIC_REPLACEMENT),
             ('Full-Width Replacement', localization.settings.qaSettings.FULL_WIDTH_REPLACEMENT)]
            localizationQAOptions += [('header', 'Localization QA: Advanced Settings'), ('combo',
              ('characterReplacementMethod', None, self.setCharacterReplacementMethod),
              'Char. Replacement',
              replacementMethodOptions,
              LEFTPADDING,
              'The character replacement method allows you to test for specific character rendering issues.'), ('checkbox', ('enableTextExpansion', None, self.setEnableTextExpansion), 'Text Expansion Enabled')]
            if self.setEnableTextExpansion:
                localizationQAOptions += [('slider',
                  ('textExpansionAmount', None, self.setTextExpansionAmount),
                  'UI/SystemMenu/Language/LocalizationQAAdvanced/TextExpansion',
                  (0.0, 0.5),
                  SLIDERWIDTH)]
        localizationQAOptions.append(('button',
         None,
         'Apply QA Settings',
         self.ApplyQALanguageSettings))
        self.ParseData(localizationQAOptions, column)

    def DisplayPseudolocalizationSample(self, column):
        """
        For english only, will be adding a sample text, to be used by pseudoloc
        """
        if session.languageID == 'EN':
            pseudolocalizationSample = [('header', 'Localization QA: Sample Text')]
            self.ParseData(pseudolocalizationSample, column, validateEntries=0)
            self.pseudolocalizedSampleTextLabel = uicontrols.EveLabelMedium(name='pseudolocSample', text=localization.GetByLabel('UI/SystemMenu/SampleText'), parent=column, align=uiconst.TOTOP, padTop=2, padBottom=2, state=uiconst.UI_NORMAL)

    def SetPseudolocalizationSettingsByPreset(self, presetValue):
        """
        Setting pseudoloc settings based on preset passed. NOTE: this method won't be refreshing any screens.
        """
        self.chosenPseudolocPreset = presetValue
        if presetValue == 0:
            self.setCharacterReplacementMethod = localization.settings.qaSettings.NO_REPLACEMENT
            self.setEnableTextExpansion = 0
            self.setTextExpansionAmount = 0.0
        elif presetValue == 1:
            self.setCharacterReplacementMethod = localization.settings.qaSettings.DIACRITIC_REPLACEMENT
            self.setEnableTextExpansion = True
            self.setTextExpansionAmount = 0.15
            self.setSimulateTooltip = False
        elif presetValue == 2:
            self.setCharacterReplacementMethod = localization.settings.qaSettings.CYRILLIC_REPLACEMENT
            self.setEnableTextExpansion = True
            self.setTextExpansionAmount = 0.05
            self.setSimulateTooltip = False
        elif presetValue == 3:
            self.setCharacterReplacementMethod = localization.settings.qaSettings.FULL_WIDTH_REPLACEMENT
            self.setEnableTextExpansion = False
            self.setTextExpansionAmount = 0.0
            self.setSimulateTooltip = False

    def AddSlider(self, where, config, minval, maxval, header, hint = '', usePrefs = 0, width = 160, height = 14, labelAlign = None, labelWidth = 0, startValue = None, step = None, leftHint = None, rightHint = None):
        uiprimitives.Container(name='push', align=uiconst.TOTOP, height=[16, 4][labelAlign is not None], parent=where)
        _par = uiprimitives.Container(name=config[0] + '_slider', align=uiconst.TOTOP, height=height, state=uiconst.UI_PICKCHILDREN, parent=where)
        par = uiprimitives.Container(name=config[0] + '_slider_sub', parent=_par)
        slider = uicontrols.Slider(parent=par, width=height, height=height)
        if labelAlign is not None:
            labelParent = uiprimitives.Container(name='labelparent', parent=_par, align=labelAlign, width=labelWidth, idx=0)
            lbl = uicontrols.EveLabelSmall(text='', parent=labelParent, width=labelWidth, tabs=[labelWidth - 22], state=uiconst.UI_NORMAL)
            lbl._tabMargin = 0
        else:
            lbl = uicontrols.EveLabelSmall(text='', parent=par, width=200, top=-14, state=uiconst.UI_NORMAL)
        lbl.state = uiconst.UI_PICKCHILDREN
        lbl.name = 'label'
        slider.label = lbl
        slider.GetSliderValue = self.GetSliderValue
        slider.SetSliderLabel = self.SetSliderLabel
        slider.GetSliderHint = self.GetSliderHint
        slider.Startup(config[0], minval, maxval, config, header, usePrefs=usePrefs, startVal=startValue)
        slider.name = config[0]
        slider.hint = hint
        if step:
            slider.SetIncrements([ val for val in range(int(minval), int(maxval + 1), step) ], 0)
        if leftHint or rightHint:
            if leftHint:
                uicontrols.EveLabelSmall(name='leftHint', text=leftHint, parent=par, align=uiconst.TOPLEFT, top=10, color=(1.0, 1.0, 1.0, 0.75))
            if rightHint:
                uicontrols.EveLabelSmall(name='rightHint', text=rightHint, parent=par, align=uiconst.TOPRIGHT, top=10, color=(1.0, 1.0, 1.0, 0.75))
            _par.padBottom += 10
        slider.EndSetSliderValue = self.EndSliderValue
        return slider

    def FindColorFromName(self, findColor, colors):
        for colorName, color in colors:
            if colorName == findColor:
                return color

    def EndSliderValue(self, slider, *args):
        if slider.name == 'TalkMicrophoneVolume':
            value = slider.GetValue()
            settings.user.audio.Set('TalkMicrophoneVolume', value)
            sm.GetService('vivox').SetMicrophoneVolume(value)

    def SetSliderLabel(self, label, idname, dname, value):
        label.text = localization.GetByLabel(dname)

    def GetSliderHint(self, idname, dname, value):
        if idname.startswith('wnd_'):
            return localization.formatters.FormatNumeric(int(value * 255))
        elif idname == 'cameraOffset':
            return self.GetCameraOffsetHintText(value)
        elif idname == 'incarnaCameraOffset':
            return self.GetCameraOffsetHintText(value, incarna=True)
        elif idname == 'incarnaCameraMouseLookSpeedSlider':
            return self.GetCameraMouseSpeedHintText(value)
        elif idname in ('actionMenuExpandTime', TOOLTIP_SETTINGS_GENERIC, TOOLTIP_SETTINGS_BRACKET):
            return ''
        else:
            return localization.formatters.FormatNumeric(int(value * 100))

    def GetSliderValue(self, idname, value, *args):
        if idname.startswith('soundLevel_'):
            return self.GetSoundlevelSliderValue(idname, value)
        if idname == 'eveampGain':
            sm.GetService('audio').UserSetAmpVolume(value)
        elif idname == 'masterVolume':
            sm.GetService('audio').SetMasterVolume(value, persist=False)
        elif idname == 'uiGain':
            sm.GetService('audio').SetUIVolume(value, persist=False)
        elif idname == 'worldVolume':
            sm.GetService('audio').SetWorldVolume(value, persist=False)
        elif idname == 'evevoiceGain':
            sm.GetService('audio').SetVoiceVolume(value, persist=False)
        elif idname == 'cameraOffset':
            self.OnSetCameraSliderValue(value)
        elif idname == 'incarnaCameraOffset':
            self.OnSetIncarnaCameraSliderValue(value)
        elif idname == 'incarnaCameraMouseLookSpeedSlider':
            self.OnSetIncarnaCameraMouseLookSpeedSliderValue(value)
        else:
            if idname == 'actionMenuExpandTime':
                return self.OnRadialMenuSliderValue(value)
            if idname == 'textExpansionAmount':
                self.setTextExpansionAmount = value
                localization.settings.qaSettings.SetValue('textExpansionAmount', value)
            elif idname == 'windowTransparency':
                self.OnWindowTransparencySlider(value)

    def OnWindowTransparencySlider(self, value):
        sm.GetService('uiColor').SetTransparency(value)

    def GetSoundlevelSliderValue(self, idname, value):
        settingName = idname.replace('soundLevel_', '')
        if self.sr.audioInited:
            sm.GetService('audio').SetCustomValue(value, settingName, persist=True)

    def OnInactiveSoundsChange(self, configName, checkbox):
        if configName == 'inactiveSounds_advancedSettings':
            settings.user.audio.Set('inactiveSounds_advancedSettings', checkbox.checked)
            self.__RebuildAudioPanel()
            return
        sm.GetService('audio').SetDampeningValueSetting(configName, setOn=checkbox.checked)

    def OnCheckBoxChange(self, checkbox):
        if checkbox.data.get('prefstype', None) is None:
            if checkbox.data.get('config', None) == const.autoRejectDuelSettingsKey:
                sm.GetService('characterSettings').Save(const.autoRejectDuelSettingsKey, str(int(checkbox.checked)))
        if checkbox.data.has_key('config'):
            config = checkbox.data['config']
            if config.startswith('inactiveSounds_'):
                return self.OnInactiveSoundsChange(config, checkbox)
            if config == 'language':
                langID = checkbox.data['value']
                if boot.region == 'optic' and not eve.session.role & service.ROLEMASK_ELEVATEDPLAYER:
                    langID = 'ZH'
                self.setlanguageID = langID
                self.RefreshLanguage(allUI=False)
            elif config == 'offsetUIwithCamera':
                sm.ScatterEvent('OnUIoffsetChanged')
            elif config == 'languageTooltip':
                self.setLanguageTooltip = checkbox.checked
            elif config == 'highlightImportant':
                self.setLocalizationHighlightImportant = checkbox.checked
            elif config == 'audioEnabled':
                if checkbox.checked:
                    eve.Message('AudioEngineOnWarning')
                    sm.GetService('audio').Activate()
                else:
                    sm.GetService('audio').Deactivate()
            elif config == 'suppressTurret':
                sm.StartService('audio').SetTurretSuppression(checkbox.checked)
            elif config == 'damageMessages':
                idx = checkbox.parent.children.index(checkbox) + 1
                state = [uiconst.UI_HIDDEN, uiconst.UI_NORMAL][settings.user.ui.Get('damageMessages', 1)]
                for i in xrange(4):
                    checkbox.parent.children[idx + i].state = state

            elif config == 'voiceenabled':
                checkbox.Disable()
                if checkbox.checked:
                    if hasattr(self, 'voiceFontBtn'):
                        self.voiceFontBtn.Enable()
                    sm.GetService('vivox').Login()
                else:
                    if hasattr(self, 'voiceFontBtn'):
                        self.voiceFontBtn.Disable()
                    sm.GetService('vivox').LogOut()
            elif config == 'talkChannelPriority':
                if not checkbox.checked:
                    sm.GetService('vivox').StopChannelPriority()
            elif config == 'shiptheme':
                self._RebuildGenericPanel()
                sm.GetService('uiColor').SelectThemeFromShip()
            elif config == 'enableWindowBlur':
                self._RebuildGenericPanel()
                sm.ScatterEvent('OnWindowBlurSettingChanged')
            elif gfxsettings.GetSettingFromSettingKey(config) is not None:
                setting = gfxsettings.GetSettingFromSettingKey(config)
                gfxsettings.Set(setting, checkbox.checked)
                self.ProcessGraphicsSettings()
                if setting == gfxsettings.MISC_LOAD_STATION_ENV:
                    eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/GraphicContentSettings/NeedToEnterCQ')})
            elif config == 'enableTextExpansion':
                self.setEnableTextExpansion = checkbox.checked
                if not checkbox.checked:
                    self.setTextExpansionAmount = 0.0
                self.RefreshLanguage(False)
            elif config == 'showMessageID':
                self.setShowMessageID = checkbox.checked
                if checkbox.checked:
                    self.setSimulateTooltip = False
                self.RefreshLanguage(False)
            elif config == 'enableBoundaryMarkers':
                self.setEnableBoundaryMarkers = checkbox.checked
                if checkbox.checked:
                    self.setSimulateTooltip = False
                self.RefreshLanguage(False)
            elif config == 'showHardcodedStrings':
                self.setShowHardcodedStrings = checkbox.checked
                if checkbox.checked:
                    self.setSimulateTooltip = False
                self.RefreshLanguage(False)
            elif config == 'simulateTooltip':
                self.setSimulateTooltip = checkbox.checked
                if checkbox.checked:
                    self.SetPseudolocalizationSettingsByPreset(0)
                    self.setShowMessageID = False
                    self.setEnableBoundaryMarkers = False
                    self.setShowHardcodedStrings = False
                self.RefreshLanguage(False)
            elif config == 'soundLevel_advancedSettings':
                settings.user.audio.Set('soundLevel_advancedSettings', checkbox.checked)
                if checkbox.checked:
                    sm.GetService('audio').EnableAdvancedSettings()
                else:
                    sm.GetService('audio').DisableAdvancedSettings()
                self.__RebuildAudioPanel()
            elif config == 'limitVoiceCount':
                sm.StartService('audio').SetVoiceCountLimitation(checkbox.checked)

    def GetConfigName(self, suppression):
        configTranslation = {'AgtDelayMission': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/DelayMissionOfferDecision'),
         'AgtMissionOfferWarning': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AgentMissionOfferWarning'),
         'AgtMissionAcceptBigCargo': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AgentMissionAcceptsBigCargo'),
         'AgtDeclineMission': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AgentMissionDeclineWarning'),
         'AgtDeclineOnlyMission': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AgentDeclineOnlyMissionWarning'),
         'AgtDeclineImportantMission': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AgentDeclineImportantMissionWarning'),
         'AgtDeclineMissionSequence': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AgentDeclineMissionSequenceWarning'),
         'AgtQuitMission': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AgentQuitMissionWarning'),
         'AgtQuitImportantMission': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AgentQuitImportantMissionWarning'),
         'AgtQuitMissionSequence': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AgentQuitMissionSequenceWarning'),
         'AgtShare': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AgentShare'),
         'AgtNotShare': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AgentNotSharing'),
         'AskPartialCargoLoad': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/PartialCargoLoad'),
         'AskUndockInEnemySystem': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/UndockInEnemySystem'),
         'AidWithEnemiesEmpire2': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AidEnemiesInEmpireSpaceWarning'),
         'AidOutlawEmpire2': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AidOutlawInEmpireSpaceWarning'),
         'AidGlobalCriminalEmpire2': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AidCriminalInEmpireSpaceWarning'),
         'AttackInnocentEmpire2': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AttackInnocentPlayerInEmpireSpaceConfirmation'),
         'AttackInnocentEmpireAbort1': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AttackInnocentPlayerInEmpireSpaceConfirmation'),
         'AttackGoodNPC2': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AttackGoodPlayerConfirmation'),
         'AttackGoodNPCAbort1': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AttackGoodPlayerConfirmation'),
         'AttackAreaEmpire3': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AreaOfEffectModuleInEmpireSpaceConfirmation'),
         'AttackAreaEmpireAbort1': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AreaOfEffectModuleInEmpireSpaceConfirmation'),
         'AttackNonEmpire2': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AttackPlayerOwnedStuffConfirmation'),
         'AttackNonEmpireAbort1': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AttackPlayerOwnedStuffConfirmation'),
         'ConfirmOneWayItemMove': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/OneWayItemMoveConfirmation'),
         'ConfirmJumpToUnsafeSS': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/JumpToUnsafeSolarSystemConfirmation'),
         'ConfirmJettison': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/JettisonItemsConfirmation'),
         'AskQuitGame': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/QuitGameConfirmation'),
         'facAcceptEjectMaterialLoss': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/EjectBluePrintFromFactoryConformation'),
         'WarnDeleteFromAddressbook': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/DeleteFromAddressBookWarning'),
         'ConfirmDeleteFolder': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/DeleteFoldersConfirmation'),
         'AskCancelContinuation': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/ModifyCharacterConfirmation'),
         'ConfirmClearText': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/ClearTextConfirmation'),
         'ConfirmAbandonDrone': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/AbandonDroneConfirmation'),
         'QueueSaveChangesOnClose': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/TrainingQueueChanges'),
         'PI_Info': localization.GetByLabel('UI/SystemMenu/ResetSettings/ResetSuppressMessageSettings/PlanetaryInteractionInfo')}
        if configTranslation.has_key(suppression[9:]):
            txt = configTranslation[suppression[9:]]
        else:
            txt = cfg.GetRawMessageTitle(suppression[9:])
            if not txt:
                txt = suppression[9:]
            log.LogWarn('Missing system menu config translation', suppression[9:])
        return txt

    def ConfigBtnClick(self, suppress, *args):
        try:
            settings.user.suppress.Delete(suppress)
            self.sr.resetsettingsinited = 0
            self.Resetsettings(1)
        except:
            log.LogException()
            sys.exc_clear()

    def TutorialResetBtnClick(self, tutorialID, btn):
        sm.GetService('tutorial').SetSequenceStatus(tutorialID, tutorialID, None, 'reset')
        self.sr.resetsettingsinited = 0
        self.Resetsettings(1)

    def TutorialDoneResetBtnClick(self, btn, *args):
        sm.GetService('tutorial').SetSequenceDoneStatus(btn.tutorialID, None, None)
        btn.state = uiconst.UI_HIDDEN

    def ResetBtnClick(self, reset, *args):
        if reset == 'windows':
            self.sr.genericinited = False
        uicore.cmd.Reset(reset)

    def QuitBtnClick(self, *args):
        uicore.cmd.CmdQuitGame()

    def LogOutBtnClick(self, *args):
        uicore.cmd.CmdLogoutGame()

    def ConvertETC(self, *args):
        MAMMON_KEY_LENGTH = 25
        ETC_KEY_LENGTH = 16

        def IsIllegal(key):
            if key == '':
                return True
            if len(key) == MAMMON_KEY_LENGTH:
                eve.Message('ETCMammonCodeNotSupported', {'code': key})
                return True
            if len(key) != ETC_KEY_LENGTH:
                eve.Message('28DaysCodeInvalid', {'etc': key})
                return True
            return False

        if eve.session.stationid is None:
            raise UserError('28DaysConvertOnlyInStation')
        if eve.Message('28DaysConvertMessage', {}, uiconst.YESNO) != uiconst.ID_YES:
            return
        name = ''
        while name is not None and IsIllegal(name):
            name = uiutil.NamePopup(localization.GetByLabel('UI/SystemMenu/ConvertEveTimeCodeHeader'), localization.GetByLabel('UI/SystemMenu/ConvertEveTimeCodeTypeInCode'), name, maxLength=MAMMON_KEY_LENGTH)

        if not name:
            return
        sm.GetService('loading').ProgressWnd(localization.GetByLabel('UI/SystemMenu/ConvertEveTimeCodeHeader'), '.', 1, 2)
        try:
            sm.RemoteSvc('userSvc').ConvertETCToPilotLicence(name)
        finally:
            sm.GetService('loading').ProgressWnd(localization.GetByLabel('UI/SystemMenu/ConvertEveTimeCodeHeader'), '.', 2, 2)

    def Petition(self, *args):
        self.CloseMenu()
        sm.GetService('petition').Show()

    def CloseMenu(self, *args):
        try:
            if getattr(self, 'closing', False):
                return
            self.closing = 1
            if self.sr.wnd:
                self.sr.wnd.state = uiconst.UI_DISABLED
            if not getattr(self, 'inited', False):
                blue.pyos.synchro.Yield()
                uicore.layer.systemmenu.CloseView()
                if self and not self.destroyed:
                    self.closing = 0
                return
            if eve.session.stationid:
                self.FadeBGOut()
                blue.pyos.synchro.Yield()
            else:
                self.FadeBGOut()
                blue.pyos.synchro.Yield()
            if self.sr.wnd:
                self.sr.wnd.state = uiconst.UI_HIDDEN
        finally:
            uicore.layer.systemmenu.CloseView()

    def ApplyLanguageSettings(self, *args):
        doReboot = False
        setlanguageID = getattr(self, 'setlanguageID', None)
        if setlanguageID and setlanguageID != self.init_languageID:
            if boot.region == 'optic' and eve.session.role & service.ROLEMASK_ELEVATEDPLAYER:
                sm.GetService('gameui').SetLanguage(setlanguageID)
            else:
                ret = eve.Message('ChangeLanguageReboot', {}, uiconst.YESNO)
                if ret == uiconst.ID_YES:
                    doReboot = True
        if getattr(self, 'setImpNameSetting', None) is not None:
            localization.settings.bilingualSettings.SetValue('localizationImportantNames', self.setImpNameSetting)
        if getattr(self, 'setLanguageTooltip', None) is not None:
            localization.settings.bilingualSettings.SetValue('languageTooltip', self.setLanguageTooltip)
        if getattr(self, 'setLocalizationHighlightImportant', None) is not None:
            localization.settings.bilingualSettings.SetValue('localizationHighlightImportant', self.setLocalizationHighlightImportant)
        localization.settings.bilingualSettings.UpdateAndSaveSettings()
        if doReboot:
            sm.GetService('gameui').SetLanguage(setlanguageID)
            if prefs.GetValue('suppressLanguageChangeRestart', 0):
                eve.Message('CustomNotify', {'notify': 'Prefs override: Language changed without restart'})
            else:
                appUtils.Reboot('language change')
                return
        localization.ClearImportantNameSetting()
        self.RefreshLanguage()

    def ApplyQALanguageSettings(self, *args):

        def _setSetting(settingKey, controlID, defaultValue = False):
            localization.settings.qaSettings.SetValue(settingKey, getattr(self, controlID, defaultValue))

        _setSetting('showMessageID', 'setShowMessageID')
        _setSetting('enableBoundaryMarkers', 'setEnableBoundaryMarkers')
        _setSetting('showHardcodedStrings', 'setShowHardcodedStrings')
        _setSetting('simulateTooltip', 'setSimulateTooltip')
        _setSetting('characterReplacementMethod', 'setCharacterReplacementMethod', localization.settings.qaSettings.NO_REPLACEMENT)
        if not getattr(self, 'setEnableTextExpansion', False):
            localization.settings.qaSettings.SetValue('textExpansionAmount', 0)
        self.chosenPseudolocPreset = -1
        localization.settings.qaSettings.UpdateAndSaveSettings()
        localization.ClearImportantNameSetting()
        self.RefreshLanguage()

    def StationUpdateCheck(self):
        if eve.session.stationid:
            if self.init_dockshipsanditems != settings.char.windows.Get('dockshipsanditems', 0):
                sm.GetService('station').ReloadLobby()
            elif self.init_stationservicebtns != settings.user.ui.Get('stationservicebtns', 1):
                sm.GetService('station').ReloadLobby()


class VoiceFontSelectionWindow(uicontrols.Window):
    __guid__ = 'form.VoiceFontSelectionWindow'
    __notifyevents__ = ['OnVoiceFontsReceived']
    default_windowID = 'VoiceFontSelection'
    default_iconNum = 'res:/ui/Texture/WindowIcons/settings.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetWndIcon(self.iconNum, mainTop=-10)
        currentVoiceFont = settings.char.ui.Get('voiceFontName', localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/NoFontSelected'))
        self.SetCaption(localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/SelectedFont', selectedFont=currentVoiceFont))
        self.SetMinSize([240, 150])
        self.MakeUnResizeable()
        self.sr.windowCaption = uicontrols.EveCaptionSmall(text=localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/Header'), parent=self.sr.topParent, align=uiconst.RELATIVE, left=70, top=15, state=uiconst.UI_DISABLED)
        self.voiceFonts = None
        sm.RegisterNotify(self)
        uthread.new(self.Display)

    def OnVoiceFontsReceived(self, voiceFontList):
        self.voiceFonts = [(localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/NoFontSelected'), 0)]
        voiceFontMenuLabelDictionary = {'distorted_female1': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/DistoredFemale1'),
         'distorted_female2': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/DistoredFemale2'),
         'distorted_male1': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/DistoredMale1'),
         'distorted_male2': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/DistoredMale2'),
         'female1': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/Female1'),
         'female2': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/Female2'),
         'female3': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/Female3'),
         'female4': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/Female4'),
         'female5': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/Female5'),
         'female2male': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/FemaleToMale'),
         'male1': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/Male1'),
         'male2': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/Male2'),
         'male3': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/Male3'),
         'male4': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/Male4'),
         'male5': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/Male5'),
         'male2female': localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/MaleToFemale')}
        for voiceFont in voiceFontList:
            if voiceFont[1] in voiceFontMenuLabelDictionary:
                label = voiceFontMenuLabelDictionary[voiceFont[1]]
                self.voiceFonts.append((label, voiceFont[0]))

        self.Display()

    def Display(self):
        self.height = 150
        self.width = 240
        uiutil.FlushList(self.sr.main.children[0:])
        self.sr.main = uiutil.GetChild(self, 'main')
        mainContainer = uiprimitives.Container(name='mainContainer', parent=self.sr.main, align=uiconst.TOALL, padding=(3, 3, 3, 3))
        if self.voiceFonts is None:
            self.echoText = uicontrols.EveHeaderSmall(text=localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/ReceivingVoiceFonts'), parent=mainContainer, align=uiconst.TOTOP, padTop=2, state=uiconst.UI_NORMAL)
            sm.GetService('vivox').GetAvailableVoiceFonts()
        else:
            idx = sm.GetService('vivox').GetVoiceFont()
            self.combo = uicontrols.Combo(label=localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/VoiceFont'), parent=mainContainer, options=self.voiceFonts, name='voicefont', idx=idx, callback=self.OnComboChange, labelleft=100, align=uiconst.TOTOP, padTop=5)
            self.combo.SetHint(localization.GetByLabel('UI/SystemMenu/AudioAndChat/VoiceFont/VoiceFont'))
            self.combo.parent.state = uiconst.UI_NORMAL
        btns = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Common/Buttons/Apply'),
          self.Apply,
          (),
          66], [localization.GetByLabel('UI/Common/Buttons/Cancel'),
          self.CloseByUser,
          (),
          66]], parent=mainContainer, idx=0)

    def Apply(self, *args):
        """ saves settings and closes dialog """
        settings.char.ui.Set('voiceFontName', self.combo.GetKey())
        sm.GetService('vivox').SetVoiceFont(self.combo.selectedValue)
        sm.ScatterEvent('OnVoiceFontChanged')
        self.CloseByUser(args)

    def OnComboChange(self, *args):
        """ intentionally not doing anything here """
        pass
