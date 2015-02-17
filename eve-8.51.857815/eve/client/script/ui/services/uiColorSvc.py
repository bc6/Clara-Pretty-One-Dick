#Embedded file name: eve/client/script/ui/services\uiColorSvc.py
import carbon.common.script.sys.service as service
from carbonui.util.color import Color
from eve.client.script.ui.shared import colorThemes
import carbonui.const as uiconst
from eveexceptions.exceptionEater import ExceptionEater
from localization import GetByLabel
import weakref

class UIColor(service.Service):
    __guid__ = 'svc.uiColor'
    __servicename__ = 'uiColor'
    __displayname__ = 'UI Color Service'
    __exportedcalls__ = {'LoadUIColors': []}
    __startupdependencies__ = ['settings']
    __notifyevents__ = ['OnSessionChanged', 'ProcessActiveShipChanged', 'OnWindowBlurSettingChanged']

    def Run(self, memStream = None):
        self.colorUpdateRegistry = weakref.WeakSet()
        self.LoadUIColors()

    def OnSessionChanged(self, isRemote, sess, change):
        if 'charid' in change:
            self.TriggerUpdate()
        self.SelectThemeFromShip()

    def Register(self, obj):
        self.colorUpdateRegistry.add(obj)

    def OnWindowBlurSettingChanged(self):
        self.TriggerUpdate()

    def ProcessActiveShipChanged(self, *args):
        self.SelectThemeFromShip()

    def SelectThemeFromShip(self):
        if settings.char.windows.Get('shiptheme', False):
            with ExceptionEater('SelectThemeFromShip'):
                typeID = sm.GetService('fleet').GetMyShipTypeID()
                if typeID:
                    themeID = colorThemes.FACTIONS.get(cfg.fsdTypeOverrides.Get(typeID).factionID, None)
                    if themeID:
                        self.SetThemeID(themeID)

    def GetSelectedThemeID(self):
        defaultID = colorThemes.RACES.get(session.raceID, colorThemes.DEFAULT_COLORTHEMEID)
        return settings.char.windows.Get('wndColorThemeID', defaultID)

    def SetThemeID(self, themeID):
        if themeID is None:
            raise RuntimeError('colorID is None')
        settings.char.windows.Set('wndColorThemeID', themeID)
        settings.char.windows.Set('baseColorTemp', None)
        settings.char.windows.Set('hiliteColorTemp', None)
        self.TriggerUpdate()

    def _GetBaseColor(self):
        if self._colorBase:
            return self._colorBase
        color = settings.char.windows.Get('baseColorTemp', None)
        if color:
            return color
        self._colorBase, _ = self.GetColor(self.GetSelectedThemeID())
        return self._colorBase

    def SetBaseColor(self, color):
        """ Only used by internal tools """
        settings.char.windows.Set('baseColorTemp', color)
        self.TriggerUpdate()

    def _GetHilightColor(self):
        if self._colorHilite:
            return self._colorHilite
        color = settings.char.windows.Get('hiliteColorTemp', None)
        if color:
            return color
        _, self._colorHilite = self.GetColor(self.GetSelectedThemeID())
        return self._colorHilite

    def _GetHilightGlowColor(self):
        if self._colorHiliteGlow:
            return self._colorHiliteGlow
        color = Color(*self._GetHilightColor()).SetBrightness(1.0)
        if color.GetSaturation() > 0.2:
            color.SetSaturation(0.2)
        self._colorHiliteGlow = color.GetRGBA()
        return self._colorHiliteGlow

    def SetHilightColor(self, color):
        """ Only used by internal tools """
        settings.char.windows.Set('hiliteColorTemp', color)
        self.TriggerUpdate()

    def _GetBaseContrastColor(self):
        if self._colorBaseContrast:
            return self._colorBaseContrast
        color = self.GetUIColor(colorType=uiconst.COLORTYPE_UIBASE)
        color = Color(*color)
        b = color.GetBrightness()
        if b < 0.12:
            b += 0.1
            s = color.GetSaturation()
            color.SetSaturation(s * 0.75)
        else:
            b *= 0.8
        self._colorBaseContrast = color.SetBrightness(b).GetRGBA()
        return self._colorBaseContrast

    def _GetHeaderColor(self):
        return self._GetHilightColor()

    def GetUIColor(self, colorType):
        if colorType == uiconst.COLORTYPE_UIBASE:
            return self._GetBaseColor()
        if colorType == uiconst.COLORTYPE_UIHILIGHT:
            return self._GetHilightColor()
        if colorType == uiconst.COLORTYPE_UIHILIGHTGLOW:
            return self._GetHilightGlowColor()
        if colorType == uiconst.COLORTYPE_UIBASECONTRAST:
            return self._GetBaseContrastColor()
        if colorType == uiconst.COLORTYPE_UIHEADER:
            return self._GetHeaderColor()

    def _ResetColorCache(self):
        self._colorBase = None
        self._colorBaseContrast = None
        self._colorHilite = None
        self._colorHiliteGlow = None
        self._colorHeader = None

    def TriggerUpdate(self):
        self._ResetColorCache()
        for obj in self.colorUpdateRegistry:
            obj.UpdateColor()

        sm.ScatterEvent('OnUIColorsChanged')

    def LoadUIColors(self, reset = False):
        reset = reset or eve.session.userid is None
        if reset:
            settings.char.windows.Set('wndColorThemeID', colorThemes.DEFAULT_COLORTHEMEID)
        self.TriggerUpdate()

    def FindColor(self, themeID):
        for themeID2, baseColor, hiliteColor in colorThemes.THEMES:
            if themeID == themeID2:
                return (baseColor + (1.0,), hiliteColor + (1.0,))

        return self.FindColor(colorThemes.DEFAULT_COLORTHEMEID)

    def GetColor(self, themeID):
        try:
            return self.FindColor(themeID)
        except:
            self.LoadUIColors(reset=True)
            raise

    def GetThemeBaseColor(self, themeID):
        baseColor, _ = self.GetColor(themeID)
        return baseColor

    def GetThemeHiliteColor(self, themeID):
        _, hiliteColor = self.GetColor(themeID)
        return hiliteColor

    def GetThemeName(self, themeID):
        return GetByLabel(themeID)

    def SetTransparency(self, value):
        settings.user.ui.Set('windowTransparency', value)
        self.TriggerUpdate()

    def GetTransparency(self):
        settings.user.ui.Get('windowTransparency', 1.0)
