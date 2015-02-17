#Embedded file name: eve/client/script/ui/shared\stateFlag.py
from carbonui import const as uiconst
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.sprite import Sprite
import inventorycommon.const as inventoryConst
from utillib import KeyVal

def GetStateFlagFromData(data):
    charID = getattr(data, 'charID', 0)
    if charID == session.charid:
        return
    fakeSlimItem = KeyVal()
    fakeSlimItem.ownerID = charID
    fakeSlimItem.charID = charID
    fakeSlimItem.corpID = data.Get('corpID', 0)
    fakeSlimItem.allianceID = data.Get('allianceID', 0)
    fakeSlimItem.warFactionID = data.Get('warFactionID', 0)
    if getattr(data, 'bounty', None):
        if data.bounty.bounty > 0.0:
            fakeSlimItem.bounty = data.bounty
    fakeSlimItem.groupID = data.Get('groupID', inventoryConst.groupCharacter)
    fakeSlimItem.categoryID = data.Get('categoryID', inventoryConst.categoryOwner)
    fakeSlimItem.securityStatus = data.Get('securityStatus', None)
    flag = sm.GetService('state').CheckStates(fakeSlimItem, 'flag')
    return flag


def AddAndSetFlagIconFromData(data, parentCont, **kwargs):
    flag = GetStateFlagFromData(data)
    return AddAndSetFlagIcon(parentCont=parentCont, flag=flag, **kwargs)


def AddAndSetFlagIcon(parentCont, *args, **kwargs):
    flag = kwargs.get('flag', 0)
    if not flag or flag == -1:
        return
    flagInfo = sm.GetService('state').GetStatePropsColorAndBlink(flag)
    stateFlagIcon = getattr(parentCont, 'stateFlagIcon', None)
    if stateFlagIcon and not stateFlagIcon.destroyed:
        stateFlagIcon.ModifyIcon(flagInfo=flagInfo)
    else:
        stateFlagIcon = FlagIconWithState(parent=parentCont, flagInfo=flagInfo, **kwargs)
        parentCont.stateFlagIcon = stateFlagIcon
    return stateFlagIcon


class FlagIcon(Container):
    default_align = uiconst.TOPRIGHT
    default_width = 9
    default_height = 9
    default_idx = 0
    iconTexturePathRoot = 'res:/UI/Texture/classes/FlagIcon/%s.png'

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.flagBackground = Fill(bgParent=self)
        self.flagBackground.opacity = 0
        self.flagIcon = Sprite(parent=self, pos=(0, 0, 9, 9), name='flagIcon', state=uiconst.UI_DISABLED, align=uiconst.CENTER)

    def SetIconTexturePath(self, iconIdx):
        self.flagIcon.texturePath = self.iconTexturePathRoot % iconIdx

    def SetBackgroundColor(self, color, opacity = 0.75):
        newColor = (color[0],
         color[1],
         color[2],
         opacity)
        self.flagBackground.SetRGB(*newColor)

    def ChangeIconVisibility(self, display):
        self.flagIcon.display = display

    def ChangeFlagPos(self, left, top, width, height):
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def ChangeIconPos(self, left, top, width, height):
        self.flagIcon.left = left
        self.flagIcon.top = top
        self.flagIcon.width = width
        self.flagIcon.height = height


class FlagIconWithState(FlagIcon):

    def ApplyAttributes(self, attributes):
        FlagIcon.ApplyAttributes(self, attributes)
        flagInfo = attributes.flagInfo
        showHint = attributes.get('showHint', True)
        if flagInfo is not None:
            self.ModifyIcon(flagInfo=flagInfo, showHint=showHint)

    def ModifyIcon(self, flagInfo, showHint = True):
        if not flagInfo:
            self.display = False
            return
        self.display = True
        flagProperties = flagInfo.flagProperties
        self.flagIcon.color.SetRGBA(*flagProperties.iconColor)
        col = flagInfo.flagColor
        blink = flagInfo.flagBlink
        if blink:
            uicore.animations.FadeTo(self, startVal=0.0, endVal=1.0, duration=0.5, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_WAVE)
        else:
            self.StopAnimations()
            self.opacity = 1.0
        self.SetBackgroundColor(col)
        self.SetIconTexturePath(flagProperties.iconIndex + 1)
        if showHint and flagProperties.text:
            self.hint = flagProperties.text
            self.state = uiconst.UI_NORMAL
