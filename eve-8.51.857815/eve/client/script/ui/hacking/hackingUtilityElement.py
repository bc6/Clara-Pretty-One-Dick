#Embedded file name: eve/client/script/ui/hacking\hackingUtilityElement.py
import uiprimitives
import uicontrols
import uicls
import carbonui.const as uiconst
import util
import localization
import hackingcommon.hackingConstants as hackingConst
import hackingUIConst
import uthread
from service import ROLE_PROGRAMMER

class UtilityElement(uiprimitives.Container):
    __guid__ = 'hackingui.UtilityElement'
    __notifyevents__ = ['OnSelectedUtilityElementChanged', 'OnHackingUEInventoryChanged', 'OnHackingUEDurationReduced']
    SIZE = 50
    default_width = SIZE
    pickRadius = SIZE
    default_align = uiconst.TOLEFT
    default_state = uiconst.UI_NORMAL
    default_padLeft = 5
    default_opacity = 0.0

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.data = attributes.utilityElementData
        self.index = attributes.index
        self.color = None
        self.inUseThread = None
        self.mouseDownSprite = uiprimitives.Sprite(name='mouseDownSprite', bgParent=self, texturePath='res:/UI/Texture/classes/hacking/utilTileMouseDown.png', opacity=0.0, padding=-15)
        self.mouseHoverSprite = uiprimitives.Sprite(name='mouseHoverSprite', bgParent=self, texturePath='res:/UI/Texture/classes/hacking/utilTileMouseHover.png', opacity=0.0, padding=-15)
        uiprimitives.Sprite(name='baseSprite', bgParent=self, texturePath='res:/UI/Texture/classes/hacking/utilTileBase.png', padding=-15)
        self.iconSprite = uiprimitives.Sprite(parent=self, align=uiconst.CENTER, pos=(0, 0, 64, 64), state=uiconst.UI_DISABLED)
        self.durationLabel = uicontrols.Label(name='durationLabel', parent=self, align=uiconst.CENTERTOP, top=-10, bold=True)
        uicore.animations.FadeTo(self, self.opacity, 0.5, duration=0.6)
        self.UpdateUtilityElementState()

    def UpdateUtilityElementState(self):
        oldSubtype = self.data.subtype if self.data else None
        texturePath = hackingUIConst.ICONPATH_BY_SUBTYPE.get(self.data.subtype, None)
        self.iconSprite.SetTexturePath(texturePath)
        if self.data.subtype != hackingConst.SUBTYPE_NONE:
            uicore.animations.FadeTo(self, self.opacity, 1.0, duration=0.6)
            if self.data.isInUse:
                self.color = hackingUIConst.COLOR_UTILITYELEMENTICON
                if not self.inUseThread:
                    self.inUseThread = uthread.new(self.AnimInUseThread)
            elif self.data.isSelected:
                self.color = hackingUIConst.COLOR_UTILITYELEMENTICON
            else:
                self.color = util.Color.WHITE
        else:
            self.color = hackingUIConst.COLOR_UEEMPTY_SLOT
            if oldSubtype != hackingConst.SUBTYPE_NONE:
                uicore.animations.FadeTo(self, 1.0, 0.5, duration=0.15, loops=2)
                uicore.animations.FadeTo(self.mouseDownSprite, 0.5, 0.0, duration=0.15, loops=2)
        if self.data.durationRemaining:
            self.durationLabel.text = str(self.data.durationRemaining)
        else:
            self.durationLabel.text = ''
        uicore.animations.SpColorMorphTo(self.iconSprite, self.iconSprite.GetRGB(), self.color, duration=0.1)

    def AnimInUseThread(self):
        while not self.destroyed and self.data.isInUse:
            uicore.animations.FadeTo(self.iconSprite, 1.0, 0.1, duration=1.0, curveType=uiconst.ANIM_WAVE, sleep=True)

        self.inUseThread = None
        self.opacity = 1.0

    def OnMouseEnter(self, *args):
        if self.data.subtype == hackingConst.SUBTYPE_NONE or self.data.isInUse:
            return
        color = util.Color(*self.color).SetBrightness(1.0).GetRGBA()
        uicore.animations.SpColorMorphTo(self.iconSprite, self.iconSprite.GetRGBA(), color, duration=0.3)
        uicore.animations.FadeIn(self.mouseHoverSprite, duration=0.3)

    def OnMouseExit(self, *args):
        uicore.animations.SpColorMorphTo(self.iconSprite, self.iconSprite.GetRGBA(), self.color, duration=0.3)
        uicore.animations.FadeOut(self.mouseHoverSprite, duration=0.3)

    def OnMouseDown(self, *args):
        if self.data.subtype == hackingConst.SUBTYPE_NONE or self.data.isInUse:
            return
        uicore.animations.FadeIn(self.mouseDownSprite, duration=0.1)

    def OnMouseUp(self, *args):
        uicore.animations.FadeOut(self.mouseDownSprite, duration=0.2)

    def OnClick(self, *args):
        if self.data.subtype == hackingConst.SUBTYPE_NONE or self.data.isInUse:
            return
        sm.GetService('hackingUI').OnUtilityElementClicked(self.index, self.data)

    def OnSelectedUtilityElementChanged(self, eventData):
        self.UpdateUtilityElementState()

    def OnHackingUEInventoryChanged(self):
        self.UpdateUtilityElementState()

    def OnHackingUEDurationReduced(self, index, coord = None):
        if index == self.data.index:
            uicore.animations.FadeTo(self.mouseDownSprite, 0.8, 0.0, duration=0.6)

    def GetHint(self):
        if self.data.subtype != hackingConst.SUBTYPE_NONE:
            ret = localization.GetByLabel(hackingUIConst.UE_HINTS_BY_SUBTYPE[self.data.subtype], amount=self.data.info, turns=self.data.totalDuration)
        else:
            ret = localization.GetByLabel('UI/Hacking/EmptyUtilitySlot')
        if bool(session.role & ROLE_PROGRAMMER):
            ret += repr(self.data).replace('<', '').replace('>', '')
        return ret
