#Embedded file name: eve/client/script/ui/services\eveDevice.py
"""
Contains class definition for eve specific device service.
"""
import uicontrols
import blue
import trinity
from carbonui.services.device import DeviceMgr
import localization
import uthread
import evegraphics.settings as gfxsettings
NVIDIA_VENDORID = 4318

class EveDeviceMgr(DeviceMgr):
    __guid__ = 'svc.eveDevice'
    __replaceservice__ = 'device'

    def AppRun(self):
        if not settings.public.generic.Get('resourceUnloading', 1):
            trinity.SetEveSpaceObjectResourceUnloadingEnabled(0)
        self.defaultPresentationInterval = trinity.PRESENT_INTERVAL.ONE
        gfx = gfxsettings.GraphicsSettings.GetGlobal()
        gfx.InitializeSettingsGroup(gfxsettings.SETTINGS_GROUP_DEVICE, settings.public.device)
        if gfxsettings.Get(gfxsettings.GFX_INTERIOR_SHADER_QUALITY) != 0:
            trinity.AddGlobalSituationFlags(['OPT_INTERIOR_SM_HIGH'])
        else:
            trinity.RemoveGlobalSituationFlags(['OPT_INTERIOR_SM_HIGH'])
        blue.classes.maxPendingDeletes = 20000
        blue.classes.maxTimeForPendingDeletes = 4.0
        blue.classes.pendingDeletesEnabled = True
        self.deviceCreated = False
        if blue.win32.IsTransgaming():
            self.cider = sm.GetService('cider')
            self.ciderFullscreenLast = False
            self.ciderFullscreenBackup = False

    def Initialize(self):
        DeviceMgr.Initialize(self)
        aaQuality = gfxsettings.Get(gfxsettings.GFX_ANTI_ALIASING)
        if aaQuality > 0 and self.GetMSAATypeFromQuality(aaQuality) == 0:
            gfxsettings.Set(gfxsettings.GFX_ANTI_ALIASING, 0, pending=False)
        shaderQuality = gfxsettings.Get(gfxsettings.GFX_SHADER_QUALITY)
        if shaderQuality == 3 and gfxsettings.MAX_SHADER_MODEL < gfxsettings.SHADER_MODEL_HIGH:
            gfxsettings.Set(gfxsettings.GFX_SHADER_QUALITY, gfxsettings.SHADER_MODEL_MEDIUM, pending=False)

    def CreateDevice(self):
        DeviceMgr.CreateDevice(self)
        if blue.win32.IsTransgaming():
            tgToggleEventHandler = blue.BlueEventToPython()
            tgToggleEventHandler.handler = self.ToggleWindowedTransGaming
            trinity.app.tgToggleEventListener = tgToggleEventHandler

    def GetMSAATypeFromQuality(self, quality):
        if quality == 0:
            return 0
        if not hasattr(self, 'msaaTypes'):
            set = self.GetSettings()
            formats = [(set.BackBufferFormat, True), (set.AutoDepthStencilFormat, False), (trinity.PIXEL_FORMAT.R16G16B16A16_FLOAT, True)]
            self.GetMultiSampleQualityOptions(set, formats)
        if quality >= len(self.msaaTypes):
            quality = len(self.msaaTypes) - 1
        return self.msaaTypes[quality]

    def GetShaderModel(self, val):
        if val == 3:
            if not trinity.renderJobUtils.DeviceSupportsIntZ():
                return 'SM_3_0_HI'
            else:
                return 'SM_3_0_DEPTH'
        elif val == 2:
            return 'SM_3_0_HI'
        return 'SM_3_0_LO'

    def GetWindowModes(self):
        self.LogInfo('GetWindowModes')
        adapter = self.CurrentAdapter()
        if adapter.format not in self.validFormats:
            return [(localization.GetByLabel('/Carbon/UI/Service/Device/FullScreen'), 0)]
        elif blue.win32.IsTransgaming():
            return [(localization.GetByLabel('/Carbon/UI/Service/Device/WindowMode'), 1), (localization.GetByLabel('/Carbon/UI/Service/Device/FullScreen'), 0)]
        else:
            return [(localization.GetByLabel('/Carbon/UI/Service/Device/WindowMode'), 1), (localization.GetByLabel('/Carbon/UI/Service/Device/FullScreen'), 0), (localization.GetByLabel('/Carbon/UI/Service/Device/FixedWindowMode'), 2)]

    def GetAppShaderModel(self):
        shaderQuality = gfxsettings.Get(gfxsettings.GFX_SHADER_QUALITY)
        return self.GetShaderModel(shaderQuality)

    def GetAppSettings(self):
        appSettings = {}
        lodQuality = gfxsettings.Get(gfxsettings.GFX_LOD_QUALITY)
        if lodQuality == 1:
            appSettings = {'eveSpaceSceneVisibilityThreshold': 15.0,
             'eveSpaceSceneLowDetailThreshold': 140.0,
             'eveSpaceSceneMediumDetailThreshold': 480.0}
        elif lodQuality == 2:
            appSettings = {'eveSpaceSceneVisibilityThreshold': 6,
             'eveSpaceSceneLowDetailThreshold': 70,
             'eveSpaceSceneMediumDetailThreshold': 240}
        elif lodQuality == 3:
            appSettings = {'eveSpaceSceneVisibilityThreshold': 3.0,
             'eveSpaceSceneLowDetailThreshold': 35.0,
             'eveSpaceSceneMediumDetailThreshold': 120.0}
        return appSettings

    def GetAppMipLevelSkipExclusionDirectories(self):
        return ['res:/Texture/IntroScene', 'res:/UI/Texture']

    def IsWindowed(self, settings = None):
        if settings is None:
            settings = self.GetSettings()
        if blue.win32.IsTransgaming():
            return not self.cider.GetFullscreen()
        return settings.Windowed

    def SetToSafeMode(self):
        gfxsettings.Set(gfxsettings.GFX_TEXTURE_QUALITY, 2, pending=False)
        gfxsettings.Set(gfxsettings.GFX_SHADER_QUALITY, 1, pending=False)
        gfxsettings.Set(gfxsettings.GFX_HDR_ENABLED, False, pending=False)
        gfxsettings.Set(gfxsettings.GFX_POST_PROCESSING_QUALITY, 0, pending=False)
        gfxsettings.Set(gfxsettings.GFX_SHADOW_QUALITY, 0, pending=False)
        gfxsettings.Set(gfxsettings.MISC_RESOURCE_CACHE_ENABLED, 0, pending=False)

    def SetDeviceCiderStartup(self, *args, **kwds):
        devSettings = args[0]
        settingsCopy = devSettings.copy()
        devSettings.BackBufferWidth, devSettings.BackBufferHeight = self.GetPreferedResolution(False)
        self.cider.SetFullscreen(True)
        DeviceMgr.SetDevice(self, devSettings, **kwds)
        self.cider.SetFullscreen(False)
        self.ciderFullscreenLast = False
        DeviceMgr.SetDevice(self, settingsCopy, **kwds)

    def SetDeviceCiderFullscreen(self, *args, **kwds):
        DeviceMgr.SetDevice(self, *args, **kwds)
        self.cider.SetFullscreen(True)

    def SetDeviceCiderWindowed(self, *args, **kwds):
        self.cider.SetFullscreen(False)
        DeviceMgr.SetDevice(self, *args, **kwds)

    def SetDevice(self, *args, **kwds):
        if blue.win32.IsTransgaming():
            ciderFullscreen = self.cider.GetFullscreen()
            self.ciderFullscreenLast = self.cider.GetFullscreen(apiCheck=True)
            if not self.deviceCreated and not ciderFullscreen:
                self.SetDeviceCiderStartup(*args, **kwds)
            elif ciderFullscreen:
                self.SetDeviceCiderFullscreen(*args, **kwds)
            else:
                self.SetDeviceCiderWindowed(*args, **kwds)
            self.deviceCreated = True
        else:
            DeviceMgr.SetDevice(self, *args, **kwds)

    def BackupSettings(self):
        DeviceMgr.BackupSettings(self)
        if blue.win32.IsTransgaming():
            self.ciderFullscreenBackup = self.ciderFullscreenLast

    def DiscardChanges(self, *args):
        if self.settingsBackup:
            if blue.win32.IsTransgaming():
                self.cider.SetFullscreen(self.ciderFullscreenBackup, setAPI=False)
            self.SetDevice(self.settingsBackup)

    def ToggleWindowedTransGaming(self, *args):
        self.LogInfo('ToggleWindowedTransGaming')
        windowed = not self.cider.GetFullscreen(apiCheck=True)
        self.cider.SetFullscreen(not windowed)
        if windowed:
            wr = trinity.app.GetWindowRect()
            self.preFullScreenPosition = (wr.left, wr.top)
        devSettings = self.GetSettings()
        devSettings.BackBufferWidth, devSettings.BackBufferHeight = self.GetPreferedResolution(windowed)
        uthread.new(self.SetDevice, devSettings, hideTitle=True)

    def GetMultiSampleQualityOptions(self, deviceSettings = None, formats = None):
        self.LogInfo('GetMultiSampleQualityOptions')
        if deviceSettings is None:
            deviceSettings = self.GetSettings()
        if formats is None:
            formats = [(deviceSettings.BackBufferFormat, True), (deviceSettings.AutoDepthStencilFormat, False)]
        vID, dID = self.GetVendorIDAndDeviceID()
        self.msaaOptions = [(localization.GetByLabel('/Carbon/UI/Common/Disabled'), 0)]
        self.msaaTypes = [0]

        def Supported(msType):
            supported = True
            for format in formats:
                if format[1]:
                    qualityLevels = trinity.adapters.GetRenderTargetMsaaSupport(deviceSettings.Adapter, format[0], deviceSettings.Windowed, msType)
                else:
                    qualityLevels = trinity.adapters.GetDepthStencilMsaaSupport(deviceSettings.Adapter, format[0], deviceSettings.Windowed, msType)
                supported = supported and qualityLevels

            return supported

        if Supported(2):
            self.msaaOptions.append((localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/LowQuality'), 1))
            self.msaaTypes.append(2)
        if Supported(4):
            self.msaaOptions.append((localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/MediumQuality'), 2))
            self.msaaTypes.append(4)
        if Supported(8):
            self.msaaOptions.append((localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/HighQuality'), 3))
            self.msaaTypes.append(8)
        elif Supported(6):
            self.msaaOptions.append((localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/HighQuality'), 3))
            self.msaaTypes.append(6)
        return self.msaaOptions

    def EnforceDeviceSettings(self, devSettings):
        """ 
        Enforce best backbuffer and depth stencil formats
        """
        devSettings.BackBufferFormat = self.GetBackbufferFormats()[0]
        devSettings.AutoDepthStencilFormat = self.GetStencilFormats()[0]
        devSettings.MultiSampleType = 0
        devSettings.MultiSampleQuality = 0
        return devSettings

    def GetAdapterResolutionsAndRefreshRates(self, set = None):
        options, resoptions = DeviceMgr.GetAdapterResolutionsAndRefreshRates(self, set)
        if set.Windowed:
            maxWidth = trinity.app.GetVirtualScreenWidth()
            maxHeight = trinity.app.GetVirtualScreenHeight()
            maxLabel = localization.GetByLabel('/Carbon/UI/Service/Device/ScreenSize', width=maxWidth, height=maxHeight)
            maxOp = (maxLabel, (maxWidth, maxHeight))
            if maxOp not in options:
                options.append(maxOp)
        elif blue.win32.IsTransgaming() and self.IsWindowed(set):
            width = trinity.app.GetVirtualScreenWidth()
            height = trinity.app.GetVirtualScreenHeight() - 44
            if height < trinity.app.minimumHeight:
                height = trinity.app.minimumHeight
            label = localization.GetByLabel('/Carbon/UI/Service/Device/ScreenSize', width=width, height=height)
            op = (label, (width, height))
            if op not in options:
                options.append(op)
            width = width / 2
            if width < trinity.app.minimumWidth:
                width = trinity.app.minimumWidth
            label = localization.GetByLabel('/Carbon/UI/Service/Device/ScreenSize', width=width, height=height)
            op = (label, (width, height))
            if op not in options:
                options.append(op)
        return (options, resoptions)

    def GetAppFeatureState(self, featureName, featureDefaultState):
        """
        Returns a boolean allowing applications to enable and disable various features
        This can be dependent on performance settings.
        """
        interiorGraphicsQuality = gfxsettings.Get(gfxsettings.GFX_INTERIOR_GRAPHICS_QUALITY)
        postProcessingQuality = gfxsettings.Get(gfxsettings.GFX_POST_PROCESSING_QUALITY)
        shaderQuality = gfxsettings.Get(gfxsettings.GFX_SHADER_QUALITY)
        shadowQuality = gfxsettings.Get(gfxsettings.GFX_SHADOW_QUALITY)
        interiorShaderQuality = gfxsettings.Get(gfxsettings.GFX_INTERIOR_SHADER_QUALITY)
        if featureName == 'Interior.ParticlesEnabled':
            return interiorGraphicsQuality == 2
        elif featureName == 'Interior.LensflaresEnabled':
            return interiorGraphicsQuality >= 1
        elif featureName == 'Interior.lowSpecMaterialsEnabled':
            return interiorGraphicsQuality == 0
        elif featureName == 'Interior.ssaoEnbaled':
            identifier = self.cachedAdapterIdentifiers[0]
            if identifier is not None:
                vendorID = identifier.vendorID
                if vendorID != 4318:
                    return False
            return postProcessingQuality != 0 and shaderQuality > 1
        elif featureName == 'Interior.dynamicShadows':
            return shadowQuality > 1
        elif featureName == 'Interior.lightPerformanceLevel':
            return interiorGraphicsQuality
        elif featureName == 'Interior.clothSimulation':
            identifier = self.cachedAdapterIdentifiers[0]
            if identifier is None:
                return featureDefaultState
            vendorID = identifier.vendorID
            return vendorID == NVIDIA_VENDORID and gfxsettings.Get(gfxsettings.GFX_CHAR_CLOTH_SIMULATION) and interiorGraphicsQuality == 2 and not blue.win32.IsTransgaming()
        elif featureName == 'CharacterCreation.clothSimulation':
            return gfxsettings.Get(gfxsettings.GFX_CHAR_CLOTH_SIMULATION)
        elif featureName == 'Interior.useSHLighting':
            return interiorShaderQuality > 0
        else:
            return featureDefaultState

    def GetUIScalingOptions(self, height = None):
        if height:
            desktopHeight = height
        else:
            desktopHeight = uicore.desktop.height
        options = [(localization.GetByLabel('UI/Common/Formatting/Percentage', percentage=90), 0.9), (localization.GetByLabel('UI/Common/Formatting/Percentage', percentage=100), 1.0)]
        if desktopHeight >= 900:
            options.append((localization.GetByLabel('UI/Common/Formatting/Percentage', percentage=110), 1.1))
        if desktopHeight >= 960:
            options.append((localization.GetByLabel('UI/Common/Formatting/Percentage', percentage=125), 1.25))
        if desktopHeight >= 1200:
            options.append((localization.GetByLabel('UI/Common/Formatting/Percentage', percentage=150), 1.5))
        return options

    def GetChange(self, scaleValue):
        oldHeight = int(trinity.device.height / uicore.desktop.dpiScaling)
        oldWidth = int(trinity.device.width / uicore.desktop.dpiScaling)
        newHeight = int(trinity.device.height / scaleValue)
        newWidth = int(trinity.device.width / scaleValue)
        changeDict = {}
        changeDict['ScalingWidth'] = (oldWidth, newWidth)
        changeDict['ScalingHeight'] = (oldHeight, newHeight)
        return changeDict

    def CapUIScaleValue(self, checkValue):
        desktopHeight = trinity.device.height
        minScale = 0.9
        if desktopHeight < 900:
            maxScale = 1.0
        elif desktopHeight < 960:
            maxScale = 1.1
        elif desktopHeight < 1200:
            maxScale = 1.25
        else:
            maxScale = 1.5
        return max(minScale, min(maxScale, checkValue))

    def SetupUIScaling(self):
        if not uicore.desktop:
            return
        windowed = self.IsWindowed()
        self.SetUIScaleValue(self.GetUIScaleValue(windowed), windowed)

    def SetUIScaleValue(self, scaleValue, windowed):
        self.LogInfo('SetUIScaleValue', scaleValue, 'windowed', windowed)
        capValue = self.CapUIScaleValue(scaleValue)
        if windowed:
            gfxsettings.Set(gfxsettings.GFX_UI_SCALE_WINDOWED, capValue, pending=False)
        else:
            gfxsettings.Set(gfxsettings.GFX_UI_SCALE_FULLSCREEN, capValue, pending=False)
        if capValue != uicore.desktop.dpiScaling:
            PreUIScaleChange_DesktopLayout = uicontrols.Window.GetDesktopWindowLayout()
            oldValue = uicore.desktop.dpiScaling
            uicore.desktop.dpiScaling = capValue
            uicore.desktop.UpdateSize()
            self.LogInfo('SetUIScaleValue capValue', capValue)
            sm.ScatterEvent('OnUIScalingChange', (oldValue, capValue))
            uicontrols.Window.LoadDesktopWindowLayout(PreUIScaleChange_DesktopLayout)
        else:
            self.LogInfo('SetUIScaleValue No Change')

    def GetUIScaleValue(self, windowed):
        if windowed:
            scaleValue = gfxsettings.Get(gfxsettings.GFX_UI_SCALE_WINDOWED)
        else:
            scaleValue = gfxsettings.Get(gfxsettings.GFX_UI_SCALE_FULLSCREEN)
        return scaleValue

    def ApplyTrinityUserSettings(self):
        effectsEnabled = gfxsettings.Get(gfxsettings.UI_EFFECTS_ENABLED)
        trailsEnabled = effectsEnabled and gfxsettings.Get(gfxsettings.UI_TRAILS_ENABLED)
        trinity.settings.SetValue('eveSpaceObjectTrailsEnabled', trailsEnabled)
        gpuParticlesEnabled = effectsEnabled and gfxsettings.Get(gfxsettings.UI_GPU_PARTICLES_ENABLED)
        trinity.settings.SetValue('gpuParticlesEnabled', gpuParticlesEnabled)
