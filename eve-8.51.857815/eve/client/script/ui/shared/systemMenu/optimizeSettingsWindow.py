#Embedded file name: eve/client/script/ui/shared/systemMenu\optimizeSettingsWindow.py
import carbonui.const as uiconst
import evegraphics.settings as gfxsettings
import localization
import uicontrols
import uicls

class OptimizeSettingsWindow(uicontrols.Window):
    __guid__ = 'form.OptimizeSettingsWindow'
    default_windowID = 'optimizesettings'
    default_iconNum = 'res:/ui/Texture/WindowIcons/settings.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetWndIcon(self.iconNum, mainTop=-10)
        self.SetCaption(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/OptimizeSettings/Header'))
        self.SetMinSize([360, 240])
        self.MakeUnResizeable()
        self.sr.windowCaption = uicontrols.CaptionLabel(text=localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/OptimizeSettings/Header'), parent=self.sr.topParent, align=uiconst.RELATIVE, left=70, top=15, state=uiconst.UI_DISABLED, fontsize=18)
        self.SetScope('all')
        main = self.sr.main
        optimizeSettingsOptions = [(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/OptimizeSettings/OptimizeSettingsSelect'), None),
         (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/OptimizeSettings/OptimizeSettingsMemory'), 1),
         (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/OptimizeSettings/OptimizeSettingsPerformance'), 2),
         (localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/OptimizeSettings/OptimizeSettingsQuality'), 3)]
        combo = self.combo = uicontrols.Combo(label='', parent=main, options=optimizeSettingsOptions, name='', select=None, callback=self.OnComboChange, labelleft=0, align=uiconst.TOTOP)
        combo.SetHint(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/OptimizeSettings/OptimizeSettingsSelect'))
        combo.padding = (6, 0, 6, 0)
        self.messageArea = uicls.EditPlainText(parent=main, readonly=1, hideBackground=1, padding=6)
        self.messageArea.HideBackground()
        self.messageArea.RemoveActiveFrame()
        uicontrols.Frame(parent=self.messageArea, color=(0.4, 0.4, 0.4, 0.5))
        self.messageArea.SetValue(localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/OptimizeSettings/OptimizeSettingsSelectInfo'))
        btns = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Common/Buttons/Apply'),
          self.Apply,
          (),
          66], [localization.GetByLabel('UI/Common/Buttons/Cancel'),
          self.CloseByUser,
          (),
          66]], parent=main, idx=0)
        return self

    def OnComboChange(self, *args):
        idx = args[2]
        info = {1: localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/OptimizeSettings/OptimizeSettingsMemoryInfo'),
         2: localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/OptimizeSettings/OptimizeSettingsPerformanceInfo'),
         3: localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/OptimizeSettings/OptimizeSettingsQualityInfo')}.get(idx, localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/OptimizeSettings/OptimizeSettingsSelectInfo'))
        self.messageArea.SetValue(info)

    def Apply(self):
        if self.combo.selectedValue is None:
            return
        value = self.combo.selectedValue
        if value == 3:
            gfxsettings.Set(gfxsettings.GFX_TEXTURE_QUALITY, 0)
            gfxsettings.Set(gfxsettings.GFX_SHADER_QUALITY, gfxsettings.MAX_SHADER_MODEL)
            gfxsettings.Set(gfxsettings.GFX_SHADOW_QUALITY, 2)
            gfxsettings.Set(gfxsettings.GFX_HDR_ENABLED, 1)
            gfxsettings.Set(gfxsettings.GFX_POST_PROCESSING_QUALITY, 2)
            gfxsettings.Set(gfxsettings.MISC_RESOURCE_CACHE_ENABLED, 0)
            gfxsettings.Set(gfxsettings.GFX_LOD_QUALITY, 3)
            gfxsettings.Set(gfxsettings.GFX_CHAR_FAST_CHARACTER_CREATION, 0)
            gfxsettings.Set(gfxsettings.GFX_CHAR_CLOTH_SIMULATION, 1)
            gfxsettings.Set(gfxsettings.GFX_CHAR_TEXTURE_QUALITY, 0)
            gfxsettings.Set(gfxsettings.GFX_ANTI_ALIASING, 2)
            if eve.session.userid:
                gfxsettings.Set(gfxsettings.UI_DRONE_MODELS_ENABLED, 1)
                gfxsettings.Set(gfxsettings.UI_EFFECTS_ENABLED, 1)
                gfxsettings.Set(gfxsettings.UI_MISSILES_ENABLED, 1)
                gfxsettings.Set(gfxsettings.UI_EXPLOSION_EFFECTS_ENABLED, 1)
                gfxsettings.Set(gfxsettings.UI_TURRETS_ENABLED, 1)
                gfxsettings.Set(gfxsettings.UI_TRAILS_ENABLED, 1)
                gfxsettings.Set(gfxsettings.UI_GPU_PARTICLES_ENABLED, 1)
        elif value == 2:
            gfxsettings.Set(gfxsettings.GFX_TEXTURE_QUALITY, 1)
            gfxsettings.Set(gfxsettings.GFX_SHADER_QUALITY, 1)
            gfxsettings.Set(gfxsettings.GFX_SHADOW_QUALITY, 0)
            gfxsettings.Set(gfxsettings.GFX_HDR_ENABLED, 0)
            gfxsettings.Set(gfxsettings.GFX_POST_PROCESSING_QUALITY, 0)
            gfxsettings.Set(gfxsettings.MISC_RESOURCE_CACHE_ENABLED, 0)
            gfxsettings.Set(gfxsettings.GFX_LOD_QUALITY, 1)
            gfxsettings.Set(gfxsettings.GFX_CHAR_FAST_CHARACTER_CREATION, 1)
            gfxsettings.Set(gfxsettings.GFX_CHAR_CLOTH_SIMULATION, 0)
            gfxsettings.Set(gfxsettings.GFX_CHAR_TEXTURE_QUALITY, 1)
            gfxsettings.Set(gfxsettings.GFX_ANTI_ALIASING, 0)
            if eve.session.userid:
                gfxsettings.Set(gfxsettings.UI_DRONE_MODELS_ENABLED, 0)
                gfxsettings.Set(gfxsettings.UI_EFFECTS_ENABLED, 0)
                gfxsettings.Set(gfxsettings.UI_MISSILES_ENABLED, 0)
                gfxsettings.Set(gfxsettings.UI_EXPLOSION_EFFECTS_ENABLED, 0)
                gfxsettings.Set(gfxsettings.UI_TURRETS_ENABLED, 0)
                gfxsettings.Set(gfxsettings.UI_TRAILS_ENABLED, 0)
                gfxsettings.Set(gfxsettings.UI_GPU_PARTICLES_ENABLED, 0)
        elif value == 1:
            gfxsettings.Set(gfxsettings.GFX_TEXTURE_QUALITY, 2)
            gfxsettings.Set(gfxsettings.GFX_SHADER_QUALITY, 1)
            gfxsettings.Set(gfxsettings.GFX_SHADOW_QUALITY, 0)
            gfxsettings.Set(gfxsettings.GFX_HDR_ENABLED, 0)
            gfxsettings.Set(gfxsettings.GFX_POST_PROCESSING_QUALITY, 0)
            gfxsettings.Set(gfxsettings.MISC_RESOURCE_CACHE_ENABLED, 0)
            gfxsettings.Set(gfxsettings.GFX_LOD_QUALITY, 2)
            gfxsettings.Set(gfxsettings.GFX_CHAR_FAST_CHARACTER_CREATION, 1)
            gfxsettings.Set(gfxsettings.GFX_CHAR_CLOTH_SIMULATION, 0)
            gfxsettings.Set(gfxsettings.GFX_CHAR_TEXTURE_QUALITY, 2)
            gfxsettings.Set(gfxsettings.GFX_ANTI_ALIASING, 0)
            if eve.session.userid:
                gfxsettings.Set(gfxsettings.UI_DRONE_MODELS_ENABLED, 0)
                gfxsettings.Set(gfxsettings.UI_EFFECTS_ENABLED, 1)
                gfxsettings.Set(gfxsettings.UI_MISSILES_ENABLED, 1)
                gfxsettings.Set(gfxsettings.UI_EXPLOSION_EFFECTS_ENABLED, 1)
                gfxsettings.Set(gfxsettings.UI_TURRETS_ENABLED, 1)
                gfxsettings.Set(gfxsettings.UI_TRAILS_ENABLED, 0)
                gfxsettings.Set(gfxsettings.UI_GPU_PARTICLES_ENABLED, 0)
        self.CloseByUser()
