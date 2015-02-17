#Embedded file name: eve/client/script/ui/shared/mapView\dockPanelSubFrame.py
from carbonui.primitives.base import Base
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.frame import Frame
from carbonui.primitives.sprite import Sprite
from carbonui.util.color import GetColor
from eve.client.script.ui.control.themeColored import FrameThemeColored
from eve.client.script.ui.shared.radialMenu.radialMenu import ThreePartContainer
import carbonui.const as uiconst
import trinity
import uthread
BASECOLOR = (118 / 255.0, 163 / 255.0, 255 / 255.0)
OUTER_FRAME = GetColor(BASECOLOR, alpha=0.6, saturation=0.7)
FRAME_GLOW_ACTIVE = (1.0, 1.0, 1.0, 1.0)
INNER_FRAME_ACTIVE = GetColor(BASECOLOR, alpha=0.6)

class DockablePanelContentFrame(Container):
    default_align = uiconst.TOALL
    default_state = uiconst.UI_NORMAL
    default_width = 0
    default_height = 0
    outerFrameWidth = 2
    innerFrameWidth = 1
    distanceFromOuterToInnerFrame_side = 4
    distanceFromOuterToInnerFrame_bottom = 4
    distanceFromInnerFrameToContent_sides = 6
    distanceFromInnerFrameToContent_bottom = 6

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        innerContainerPadding = self.outerFrameWidth + self.distanceFromOuterToInnerFrame_side
        innerContainer = Container(parent=self, name='innerContainer', padding=innerContainerPadding, bgColor=(0, 0, 0, 0.5))
        frameCornerSize = 2 + self.innerFrameWidth
        glowFrameTexturePath = 'res:/UI/Texture/classes/CharacterSelection/glowDotFrame.png'
        self.normalGlowFrame = Frame(parent=innerContainer, name='glowFrame', color=FRAME_GLOW_ACTIVE, frameConst=(glowFrameTexturePath,
         5,
         -2,
         0), padding=0)
        self.normalFrame = FrameThemeColored(parent=innerContainer, name='normalFrame', padding=0, frameConst=('ui_1_16_161',
         frameCornerSize,
         -2,
         0))
        self.normalFrame.opacity = 0.0
        self.selectionFrameGlow = Frame(parent=self, name='selectionFrame', color=FRAME_GLOW_ACTIVE, texturePath='res:/UI/Texture/classes/CharacterSelection/selectFrame.png', cornerSize=22)
        self.selectionFrameGlow.opacity = 0
        frameCornerSize = 2 + self.outerFrameWidth
        self.selectionFrame = Frame(parent=self, name='selectionFrame', color=OUTER_FRAME, frameConst=('ui_1_16_161',
         frameCornerSize,
         -2,
         0))
        self.selectionFrame.opacity = 0
        contentPadding = self.distanceFromInnerFrameToContent_sides + self.innerFrameWidth
        contentParent = Container(parent=innerContainer, name='contentParent', padding=contentPadding, align=uiconst.TOALL)
        self.contentTopPush = Container(name='contentTopPush', parent=contentParent, align=uiconst.TOTOP_PROP, height=0.55)
        self.contentBottomPush = Container(name='contentBottomPush', parent=contentParent, align=uiconst.TOBOTTOM_PROP, height=0.55)
        self.content = Container(parent=contentParent, name='content', align=uiconst.TOALL, pos=(0, 0, 0, 0), clipChildren=True, state=uiconst.UI_PICKCHILDREN, opacity=0.0)
        self.dotFrameTopPush = Container(name='dotFrameTopPush', parent=innerContainer, align=uiconst.TOTOP_PROP, height=0.5)
        self.dotFrameBottomPush = Container(name='dotFrameBottomPush', parent=innerContainer, align=uiconst.TOBOTTOM_PROP, height=0.5)
        self.dotFrame = FrameThemeColored(parent=innerContainer, name='dotFrame', color=FRAME_GLOW_ACTIVE, texturePath='res:/UI/Texture/classes/MapView/dotFrame.png', cornerSize=21, offset=-1)
        self.dotFrame.opacity = 0.0

    def AnimateContentIn(self, animationOffset = 0.0):
        """
            Animates the content in
        """
        minBlinkValue = 0.2
        blinkDuration = 0.1
        lineAnimationOffset = animationOffset
        lineAnimationDuration = 0.4
        lineFadeOutOffset = lineAnimationOffset + lineAnimationDuration
        lineFadeOutDuration = 0.2
        for each in (self.dotFrameTopPush, self.dotFrameBottomPush):
            uicore.animations.MorphScalar(each, 'height', startVal=each.height, endVal=0.0, duration=lineAnimationDuration, timeOffset=lineAnimationOffset)

        uicore.animations.MorphScalar(self.dotFrame, 'opacity', startVal=0.8, endVal=0, duration=lineFadeOutDuration, timeOffset=lineFadeOutOffset)
        normalFrameFadeOffset = lineFadeOutDuration + lineFadeOutOffset - 0.2
        normalFrameFadeDuration = 0.4
        uicore.animations.MorphScalar(self.normalFrame, 'opacity', startVal=0, endVal=INNER_FRAME_ACTIVE[3], duration=normalFrameFadeDuration, timeOffset=normalFrameFadeOffset)
        portraitOffset = normalFrameFadeOffset + normalFrameFadeDuration - 0.2
        portraitDuration = 0.2
        for each in (self.contentTopPush, self.contentBottomPush):
            uicore.animations.MorphScalar(each, 'height', startVal=each.height, endVal=0.0, duration=portraitDuration, timeOffset=portraitOffset)

        uicore.animations.BlinkIn(self.content, startVal=1.0, endVal=minBlinkValue, duration=blinkDuration, curveType=uiconst.ANIM_BOUNCE, timeOffset=portraitOffset + portraitDuration)

    def PlaySelectedAnimation(self):
        print 'PlaySelectedAnimation'
        uicore.animations.BlinkIn(self.selectionFrame, startVal=OUTER_FRAME[3], endVal=0.0, duration=0.1, loops=2, curveType=uiconst.ANIM_BOUNCE, timeOffset=0.2)


class ContainerLockedRatio(Container):
    lockDesktopRatio = None

    @apply
    def displayRect():
        doc = ''
        fget = Base.displayRect.fget

        def fset(self, value):
            displayX, displayY, displayWidth, displayHeight = value
            self._displayHeight = int(round(displayY + displayHeight)) - self._displayY
            if self.lockDesktopRatio:
                self._displayWidth = min(uicore.desktop.width * self.self.lockDesktopRatio, int(round(displayX + displayWidth)) - self._displayX)
            if self.parent:
                self._displayX = (self.parent.displayWidth - self._displayWidth) / 2
                self._displayY = int(round(displayY))
            ro = self.renderObject
            if ro:
                ro.displayX = self._displayX
                ro.displayY = self._displayY
                ro.displayWidth = self._displayWidth
                ro.displayHeight = self._displayHeight
            if self._backgroundlist and len(self.background):
                self.UpdateBackgrounds()

        return property(**locals())
