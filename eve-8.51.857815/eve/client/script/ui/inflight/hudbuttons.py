#Embedded file name: eve/client/script/ui/inflight\hudbuttons.py
from carbonui import const as uiconst
import localization
import trinity
import uicontrols
import uiprimitives

class LeftSideButton(uiprimitives.Container):
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.RELATIVE

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.btnName = attributes.btnName
        self.func = attributes.func
        self.funcArgs = None
        self.cmdName = attributes.cmdName
        self.orgTop = None
        self.pickRadius = self.width / 2
        self.icon = uicontrols.Icon(parent=self, name='icon', pos=(0, 0, 32, 32), align=uiconst.CENTER, state=uiconst.UI_DISABLED, icon=attributes.iconNum)
        self.transform = uiprimitives.Transform(parent=self, name='icon', pos=(0, 0, 32, 32), align=uiconst.CENTER, state=uiconst.UI_DISABLED)
        self.hilite = uiprimitives.Sprite(parent=self, name='hilite', align=uiconst.TOALL, state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/classes/ShipUI/utilBtnBaseAndShadow.png', color=(0.63, 0.63, 0.63, 1.0), blendMode=trinity.TR2_SBM_ADD)
        slot = uiprimitives.Sprite(parent=self, name='slot', align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/utilBtnBaseAndShadow.png')
        self.busy = uiprimitives.Sprite(parent=self, name='busy', align=uiconst.TOALL, state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/classes/ShipUI/utilBtnGlow.png', color=(0.27, 0.72, 1.0, 0.53))
        self.blinkBG = uiprimitives.Sprite(parent=self, name='blinkBG', align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/utilBtnGlow.png', opacity=0.0, blendMode=trinity.TR2_SBM_ADD)

    def LoadTooltipPanel(self, tooltipPanel, *args):
        tooltipPanel.LoadGeneric2ColumnTemplate()
        if self.name == 'inFlightScannerBtn':
            tooltipPanel.AddLabelShortcut(localization.GetByLabel('Tooltips/Hud/Scanners'), '')
            tooltipPanel.AddLabelMedium(text=localization.GetByLabel('Tooltips/Hud/Scanners_description'), wrapWidth=200, colSpan=tooltipPanel.columns, color=(0.6, 0.6, 0.6, 1))
        elif self.name == 'inFlightCameraControlsBtn':
            tooltipPanel.AddLabelMedium(text=localization.GetByLabel('Tooltips/Hud/CameraControls'), colSpan=tooltipPanel.columns)
            tooltipPanel.AddLabelMedium(text=localization.GetByLabel('Tooltips/Hud/CameraControls_description'), wrapWidth=200, colSpan=tooltipPanel.columns, color=(0.6, 0.6, 0.6, 1))
        elif self.cmdName:
            cmd = uicore.cmd.commandMap.GetCommandByName(self.cmdName)
            tooltipPanel.AddCommandTooltip(cmd)

    def LoadIcon(self, iconPath):
        self.icon.LoadIcon(iconPath)

    def OnClick(self, *args):
        if self.func:
            if self.funcArgs is not None:
                self.func(*self.funcArgs)
            else:
                self.func()
        sm.GetService('ui').StopBlink(self.icon)

    def OnMouseDown(self, btn, *args):
        if getattr(self, 'orgTop', None) is None:
            self.orgTop = self.top
        self.top = self.orgTop + 2

    def OnMouseUp(self, *args):
        if getattr(self, 'orgTop', None) is not None:
            self.top = self.orgTop

    def OnMouseEnter(self, *args):
        self.hilite.state = uiconst.UI_DISABLED

    def OnMouseExit(self, *args):
        self.hilite.state = uiconst.UI_HIDDEN
        if getattr(self, 'orgTop', None) is not None:
            self.top = self.orgTop

    def GetHint(self):
        ret = self.btnName
        if self.cmdName:
            shortcut = uicore.cmd.GetShortcutStringByFuncName(self.cmdName)
            if shortcut:
                ret += ' [%s]' % shortcut
        return ret

    def Blink(self, loops = 3):
        uicore.animations.FadeTo(self.blinkBG, 0.0, 0.9, duration=0.15, loops=loops, callback=self._BlinkFadeOut)

    def _BlinkFadeOut(self):
        uicore.animations.FadeOut(self.blinkBG, duration=0.6)
