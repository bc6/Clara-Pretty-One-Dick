#Embedded file name: eve/client/script/ui/control\glowSprite.py
from carbonui.primitives.container import Container
import carbonui.const as uiconst
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveWindowUnderlay import SpriteUnderlay
import trinity

class GlowSprite(Container):
    default_name = 'GlowSprite'
    default_texturePath = ''
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOPLEFT
    default_glowExpand = 0
    default_color = None
    default_rotation = 0.0
    default_iconOpacity = 0.9
    default_gradientStrength = 1.0
    default_color = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.texturePath = attributes.Get('texturePath', self.default_texturePath)
        self.color = attributes.Get('color', None)
        self.rotation = attributes.Get('rotation', self.default_rotation)
        self.iconOpacity = attributes.Get('iconOpacity', self.default_iconOpacity)
        self.gradientStrength = attributes.get('gradientStrength', self.default_gradientStrength)
        self.color = attributes.get('color', self.default_color)
        self._glowAmount = 0.0
        self.spriteEffect = None
        self.glowExpand = None
        self.icon = SpriteUnderlay(bgParent=self, name='icon', state=uiconst.UI_DISABLED, align=uiconst.TOALL, blendMode=trinity.TR2_SBM_ADD, opacity=self.iconOpacity, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW, color=self.color, texturePath=self.texturePath, rotation=self.rotation)
        self.glowIcon = None
        self.bgGradient = None

    def ConstructGlow(self):
        if not self.glowIcon:
            self.OnSizeUpdate()
            self.glowIcon = SpriteUnderlay(name='glowIcon', bgParent=self, state=uiconst.UI_DISABLED, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW, spriteEffect=self.spriteEffect, padding=-self.glowExpand, blendMode=trinity.TR2_SBM_ADDX2, opacity=0.0, texturePath=self.texturePath, rotation=self.rotation, color=self.color)
            self.bgGradient = SpriteUnderlay(name='bgGradient', bgParent=self, texturePath='res:/UI/Texture/shared/circularGradient.png', opacity=0.0, padding=-self.glowExpand, color=self.color)

    def UpdateSpriteEffect(self, size):
        """
        Use BLUR effect for small icons and GLOW for larger
        """
        if size > 20:
            self.spriteEffect = trinity.TR2_SFX_GLOW
        else:
            self.spriteEffect = trinity.TR2_SFX_BLUR

    def OnSizeUpdate(self):
        w, h = self.GetAbsoluteSize()
        size = max(w, h)
        self.UpdateSpriteEffect(size)
        self.UpdateGlowExpand(size)

    def _OnResize(self, *args):
        self.OnSizeUpdate()

    def UpdateGlowExpand(self, size):
        """
        Make glow expand more for larger icons
        """
        g = size / 20
        g = max(1, min(g, 3))
        self.glowExpand = g
        if self.glowIcon:
            self.glowIcon.padding = (-g,
             -g,
             -g,
             -g)
            self.bgGradient.padding = (-g,
             -g,
             -g,
             -g)

    def SetTexturePath(self, texturePath):
        self.texturePath = texturePath
        self.icon.SetTexturePath(texturePath)
        if self.glowIcon:
            self.glowIcon.SetTexturePath(texturePath)

    def LoadTexture(self, texturePath):
        self.SetTexturePath(texturePath)

    def LoadIcon(self, iconNo, ignoreSize = False):
        texturePath, _ = Icon.ConvertIconNoToResPath(iconNo)
        self.SetTexturePath(texturePath)

    def LoadIconByTypeID(self, typeID, itemID, *args, **kw):
        """ Hack needed since loading texturePaths by typeID/itemID is locked within the Icon class """
        icon = Icon(typeID=typeID, itemID=itemID)
        self.SetTexturePath(icon.texturePath)

    def SetRGBA(self, *color):
        self.color = color
        if self.glowIcon:
            self.glowIcon.SetFixedColor(color)
            self.bgGradient.SetFixedColor(color)

    def SetRGB(self, *args):
        self.SetRGBA(*args)

    def GetRGBA(self):
        return self.icon.GetRGBA()

    def OnMouseEnter(self, *args):
        uicore.animations.MorphScalar(self, 'glowAmount', self.glowAmount, 1.0, duration=uiconst.TIME_ENTRY)

    def OnMouseExit(self, *args):
        uicore.animations.MorphScalar(self, 'glowAmount', self.glowAmount, 0.0, duration=uiconst.TIME_EXIT)

    def OnMouseDown(self, *args):
        uicore.animations.MorphScalar(self, 'glowAmount', self.glowAmount, 1.5, duration=0.1)

    def OnMouseUp(self, *args):
        uicore.animations.MorphScalar(self, 'glowAmount', self.glowAmount, 1.0, duration=0.3)

    @property
    def glowAmount(self):
        return self._glowAmount

    @glowAmount.setter
    def glowAmount(self, value):
        self.ConstructGlow()
        self._glowAmount = value
        self.icon.opacity = self.iconOpacity + value * 0.5
        self.glowIcon.opacity = value * 0.2
        self.bgGradient.opacity = value * 0.3 * self.gradientStrength
        self.glowIcon.display = value > 0.0001

    def SetRotation(self, value):
        self.rotation = value
        self.icon.rotation = value
        if self.glowIcon:
            self.glowIcon.rotation = value
