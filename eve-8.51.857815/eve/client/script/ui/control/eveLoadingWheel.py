#Embedded file name: eve/client/script/ui/control\eveLoadingWheel.py
from math import pi
import carbonui.const as uiconst
from carbonui.primitives.sprite import Sprite

class LoadingWheel(Sprite):
    __guid__ = 'uicls.LoadingWheel'
    default_name = 'loadingWheel'
    default_width = 64
    default_height = 64
    default_loopParams = (1, 1000.0)
    default_texturePath = 'res:/UI/Texture/loadingWheel.png'

    def ApplyAttributes(self, attributes):
        Sprite.ApplyAttributes(self, attributes)
        loopParams = attributes.get('loopParams', self.default_loopParams)
        if loopParams:
            direction, time = loopParams
            uicore.animations.MorphScalar(self, 'rotation', 0.0, -direction * 2 * pi, duration=time / 1000.0, curveType=uiconst.ANIM_LINEAR, loops=uiconst.ANIM_REPEAT)
