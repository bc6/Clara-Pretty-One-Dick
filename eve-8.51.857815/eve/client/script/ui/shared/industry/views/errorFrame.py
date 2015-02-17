#Embedded file name: eve/client/script/ui/shared/industry/views\errorFrame.py
from carbonui import const as uiconst
from carbonui.primitives.sprite import Sprite

class ErrorFrame(Sprite):
    default_name = 'ErrorFrame'
    default_opacity = 0.0
    default_texturePath = 'res:/UI/Texture/Classes/Industry/Output/hatchPattern.png'
    default_tileX = True
    default_tileY = True
    default_color = (1.0, 0.275, 0.0, 1.0)

    def Show(self, *args):
        Sprite.Show(self, *args)
        uicore.animations.FadeTo(self, 0.3, 0.35, duration=3.0, curveType=uiconst.ANIM_WAVE, loops=uiconst.ANIM_REPEAT)

    def Hide(self, *args):
        Sprite.Hide(self, *args)
        uicore.animations.FadeOut(self, duration=0.3)
