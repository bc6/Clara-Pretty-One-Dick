#Embedded file name: eve/client/script/ui/inflight\radialMenuShipUI.py
from eve.client.script.ui.control.tooltips import ShortcutHint
import uicontrols
import carbonui.const as uiconst
import uicls
import blue
from eve.client.script.ui.shared.radialMenu.radialMenu import RadialMenu
from eve.client.script.ui.shared.radialMenu.radialMenu import ThreePartContainer
from eve.client.script.ui.shared.radialMenu.radialMenuUtils import RadialMenuSizeInfo
RM1_SizeInfo = RadialMenuSizeInfo(width=118, height=118, shadowSize=104, rangeSize=50, sliceCount=4, buttonWidth=84, buttonHeight=49, buttonPaddingTop=5, buttonPaddingBottom=5, actionDistance=59)

class RadialMenuShipUI(RadialMenu):
    __guid__ = 'uicls.RadialMenuShipUI'
    default_left = 0
    default_top = 0
    default_align = uiconst.TOPLEFT
    default_width = RM1_SizeInfo.width
    default_height = RM1_SizeInfo.height
    sizeInfo = RM1_SizeInfo
    default_showActionText = True
    shadowTexture = 'res:/UI/Texture/classes/RadialMenu/menuShadow3.png'
    buttonBackgroundOpacity = 0.9

    def SetSpecificValues(self, attributes):
        self.anchorObject = attributes.anchorObject
        self.displayName = attributes.displayName
        self.upCounter = 0

    def SetPosition(self):
        left, top, width, height = self.anchorObject.GetAbsolute()
        self.originalX = self.currentCenterX = left + width / 2
        self.originalY = self.currentCenterY = top + height / 2
        self.left = self.originalX - self.width / 2
        self.top = self.originalY - self.height / 2

    def LoadMyActions(self, doReset = False, animate = False, *args):
        optionsInfo = self.GetMyActions()
        if optionsInfo is None:
            return
        self.LoadButtons(self.firstLayerCont, optionsInfo, doReset=doReset)
        if animate:
            self.AnimateMenuFromCenter(duration=0.1)

    def GetMyActions(self, *args):
        pass

    def AdjustTextShadow(self, *args):
        if not self.optionLabel.display:
            if getattr(self, 'labelShadow', None):
                self.labelShadow.display = False
            return
        shorcutPadding = self.GetPaddingBecauseOfShortcut()
        centerWidth = self.optionLabel.textwidth + shorcutPadding
        self.optionLabel.left = -shorcutPadding / 2
        height = self.optionLabel.textheight + 4
        top = -18
        self.labelShadow.display = True
        self.labelShadow.SetCenterSizeAndTop(centerWidth, height, top=top)

    def GetPaddingBecauseOfShortcut(self):
        if not self.shortcutHint.textLabel.text:
            return 0
        return self.shortcutHint.width + 5

    def AddOptionText(self):
        self.labelShadow = ThreePartContainer(parent=self, name='labelShadow', pos=(0, 0, 200, 30), align=uiconst.CENTERTOP, state=uiconst.UI_DISABLED, idx=0, leftTexturePath='res:/UI/Texture/classes/RadialMenu/textShadowLeft.png', rightTexturePath='res:/UI/Texture/classes/RadialMenu/textShadowRight.png', centerTexturePath='res:/UI/Texture/classes/RadialMenu/textShadowCenter.png', sideSize=24, color=(0, 0, 0, 0.6))
        self.labelShadow.display = False
        self.shortcutHint = ShortcutHint(parent=self.labelShadow, text='', bgColor=(0.15, 0.15, 0.15, 1.0), textColor=(0.5, 0.5, 0.5, 1.0), align=uiconst.CENTERRIGHT, left=24, idx=0)
        self.optionLabel = uicontrols.EveLabelLarge(parent=self.labelShadow, state=uiconst.UI_DISABLED, align=uiconst.CENTER, top=0, idx=0, bold=True)
        self.optionLabel.display = False
        self.AdjustTextShadow()

    def GetIconTexturePath(self, activeOption, menuOptions = None):
        """
            since it's simple cases, I just include the iconPath in the keyvals
        """
        return menuOptions.iconPath

    def OnMouseUp(self, button, *args):
        """
            on releasing the mouse we either select the option that has been highlighted
            or close the menu if non is highlighted
        """
        uicore.uilib.UnclipCursor()
        self.cursorClipped = False
        self.upCounter += 1
        radialMenuBtn = self.GetRadialMenuButton()
        if button != radialMenuBtn:
            self.Close()
        if self.selectedBtn:
            self.ClickButton(self.selectedBtn)
        elif self.upCounter > 1:
            self.Close()

    def OnMouseUpBlocker(self, button, *args):
        uicls.RadialMenu.OnMouseUp(self, button, *args)

    def IsRadialMenuButtonActive(self, *args):
        if self.upCounter:
            return False
        menuButton = self.GetRadialMenuButton()
        actionmenuBtnState = uicore.uilib.GetMouseButtonState(menuButton)
        return actionmenuBtnState

    def GetRadialMenuButton(self, *args):
        return uiconst.MOUSELEFT

    def HiliteOneButton(self, btnCont, buttonLayer):
        RadialMenu.HiliteOneButton(self, btnCont, buttonLayer)
        self.SetShortcut(btnCont)
        self.AdjustTextShadow()

    def SetShortcut(self, btnCont):
        shortcutStr = self.GetShortcutString(btnCont)
        if not shortcutStr:
            return self.ClearShortcutHint()
        self.shortcutHint.display = True
        self.shortcutHint.textLabel.text = shortcutStr
        self.shortcutHint.AdjustSize()

    def GetShortcutString(self, btnCont):
        if not btnCont or not btnCont.actionButton:
            return
        commandName = getattr(btnCont.actionButton, 'commandName', None)
        if not commandName:
            return
        command = uicore.cmd.commandMap.GetCommandByName(commandName)
        if not command:
            return
        shortcutStr = command.GetShortcutAsString()
        return shortcutStr

    def ClearShortcutHint(self):
        self.shortcutHint.textLabel.text = ''
        self.shortcutHint.display = False
