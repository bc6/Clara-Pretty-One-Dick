#Embedded file name: eve/client/script/ui/station/captainsquarters\screenControls.py
import math
import blue
import carbonui.const as uiconst
import uiprimitives
import uicontrols
import uicls
import uthread
import util
import random
TIME_BASE = 0.3

class ScreenWedgeBracketTop(uiprimitives.Transform):
    """
    A top aligned bracket with wedges and entry animations
    """
    __guid__ = 'uicls.ScreenWedgeBracketTop'
    default_name = 'ScreenWedgeBracketTop'
    default_hasCorners = True
    default_wedgeWidth = 100
    default_wedgeTopStart = -10
    default_wedgePosRatio = 0.5
    default_align = uiconst.TOTOP
    default_height = 25
    default_rotation = 0.0

    def ApplyAttributes(self, attributes):
        global TIME_BASE
        uiprimitives.Transform.ApplyAttributes(self, attributes)
        TIME_BASE = 0.3
        self.hasCorners = attributes.get('hasCorners', self.default_hasCorners)
        wedgeWidth = attributes.get('wedgeWidth', self.default_wedgeWidth)
        wedgeTopStart = attributes.get('wedgeTopStart', self.default_wedgeTopStart)
        self.wedgePosRatio = attributes.get('wedgePosRatio', self.default_wedgePosRatio)
        self.borderLeft = uicontrols.Frame(parent=self, name='borderLeft', texturePath='res:/UI/Texture/classes/CQMainScreen/borderLeft.png', cornerSize=16, align=uiconst.TOPLEFT, pos=(0, 1, 200, 48), padLeft=2, color=util.Color.WHITE)
        self.wedge = uicontrols.Frame(parent=self, name='wedge', texturePath='res:/UI/Texture/classes/CQMainScreen/wedge.png', cornerSize=13, align=uiconst.TOPLEFT, pos=(300,
         wedgeTopStart,
         wedgeWidth,
         27), padding=(-5, 0, -5, 0), color=util.Color.WHITE)
        self.borderRight = uicontrols.Frame(parent=self, name='borderLeft', texturePath='res:/UI/Texture/classes/CQMainScreen/borderRight.png', cornerSize=16, align=uiconst.TOPRIGHT, pos=(0, 1, 200, 48), padRight=2, color=util.Color.WHITE)
        if self.hasCorners:
            self.cornerLeft = uiprimitives.Sprite(parent=self, name='cornerLeft', texturePath='res:/UI/Texture/classes/CQMainScreen/cornerLeft.png', pos=(0, 0, 22, 22))
            self.cornerRight = uiprimitives.Sprite(parent=self, name='cornerRight', texturePath='res:/UI/Texture/classes/CQMainScreen/cornerRight.png', pos=(0, 0, 22, 22), align=uiconst.TOPRIGHT)

    def _OnResize(self):
        if not hasattr(self, 'wedge'):
            return
        self.UpdatePosition()

    def UpdatePosition(self):
        w, h = self.GetAbsoluteSize()
        self.wedge.left = (w - self.wedge.width) * self.wedgePosRatio
        self.borderLeft.width = self.wedge.left
        self.borderRight.width = w - self.wedge.left - self.wedge.width

    def AnimAppear(self):
        if self.hasCorners:
            uicore.animations.FadeIn(self.cornerLeft, duration=TIME_BASE / 3, loops=3)
            uicore.animations.FadeIn(self.cornerRight, duration=TIME_BASE / 3, loops=3, sleep=True)
        uicore.animations.FadeIn(self.borderLeft, duration=TIME_BASE)
        uicore.animations.FadeIn(self.borderRight, duration=TIME_BASE)
        uicore.animations.FadeIn(self.wedge, duration=TIME_BASE / 3, loops=3, sleep=True)
        uicore.animations.MorphScalar(self.wedge, 'top', self.wedge.top, 0, duration=TIME_BASE, curveType=uiconst.ANIM_LINEAR, sleep=True)

    def AnimDisappear(self):
        uicore.animations.FadeOut(self)


class ScreenWedgeBracketBottom(ScreenWedgeBracketTop):
    """
    A bottom aligned bracket with wedges and entry animations
    """
    __guid__ = 'uicls.ScreenWedgeBracketBottom'
    default_name = 'ScreenWedgeBracketBottom'
    default_align = uiconst.TOBOTTOM
    default_rotation = math.pi


class ScreenSimpleBracketTop(uicontrols.Frame):
    """
    A top aligned bracket with an entry animation
    """
    __guid__ = 'uicls.ScreenSimpleBracketTop'
    default_name = 'ScreenSimpleBracketTop'
    default_texturePath = 'res:/UI/Texture/classes/CQMainScreen/simpleBracketTop.png'
    default_cornerSize = 21
    default_align = uiconst.TOTOP
    default_height = 21
    default_color = util.Color.WHITE

    def AnimAppear(self):
        uicore.animations.FadeIn(self, duration=TIME_BASE)

    def AnimDisappear(self):
        uicore.animations.FadeOut(self, duration=TIME_BASE)


class ScreenSimpleBracketBottom(ScreenSimpleBracketTop):
    """
    A bottom aligned bracket with an entry animation
    """
    __guid__ = 'uicls.ScreenSimpleBracketBottom'
    default_name = 'ScreenSimpleBracketTop'
    default_texturePath = 'res:/UI/Texture/classes/CQMainScreen/simpleBracketBottom.png'
    default_align = uiconst.TOBOTTOM


class ScreenFrameBase(uiprimitives.Container):
    __guid__ = 'uicls._ScreenFrameBase'

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.bracketLayer = uiprimitives.Container(name='bracketCont', parent=self)
        self.mainCont = uiprimitives.Container(name='mainCont', parent=self)
        self.topBracket = None
        self.bottomBracket = None
        uthread.new(self.AnimAppear)

    def AnimAppear(self):
        w, h = self.GetAbsoluteSize()
        uicore.animations.MorphScalar(self.topBracket, 'padTop', h / 2, 0, duration=TIME_BASE)
        uicore.animations.MorphScalar(self.bottomBracket, 'padBottom', h / 2, 0, duration=TIME_BASE, sleep=True)
        for obj in self.bracketLayer.children:
            uthread.new(obj.AnimAppear)
            blue.pyos.synchro.SleepWallclock(200)

        blue.pyos.synchro.SleepWallclock(2000)
        for c in self.mainCont.children:
            if hasattr(c, 'AnimAppear'):
                uthread.new(c.AnimAppear)


class ScreenFrame1(ScreenFrameBase):
    """
    Wedge brackets top and bottom 
    """
    __guid__ = 'uicls.ScreenFrame1'
    default_name = 'ScreenFrame1'

    def ApplyAttributes(self, attributes):
        uicls._ScreenFrameBase.ApplyAttributes(self, attributes)
        self.bottomBracket = uicls.ScreenWedgeBracketBottom(parent=self.bracketLayer, wedgePosRatio=0.3, rotation=math.pi, align=uiconst.TOBOTTOM)
        self.topBracket = uicls.ScreenWedgeBracketTop(parent=self.bracketLayer, wedgePosRatio=0.3, rotation=0)


class ScreenFrame2(ScreenFrameBase):
    """
    Wedge bracket top, simple bracket bottom
    """
    __guid__ = 'uicls.ScreenFrame2'
    default_name = 'ScreenFrame2'

    def ApplyAttributes(self, attributes):
        ScreenFrameBase.ApplyAttributes(self, attributes)
        self.topBracket = uicls.ScreenWedgeBracketTop(parent=self.bracketLayer, wedgePosRatio=0.3, wedgeWidth=200, hasCorners=False)
        self.bottomBracket = uicls.ScreenSimpleBracketBottom(parent=self.bracketLayer)


class ScreenFrame3(ScreenFrameBase):
    """
    Wedge brackets bottom, simple bracket top 
    """
    __guid__ = 'uicls.ScreenFrame3'
    default_name = 'ScreenFrame3'

    def ApplyAttributes(self, attributes):
        ScreenFrameBase.ApplyAttributes(self, attributes)
        self.topBracket = uicls.ScreenSimpleBracketTop(parent=self.bracketLayer)
        self.bottomBracket = uicls.ScreenWedgeBracketBottom(parent=self.bracketLayer, wedgePosRatio=0.3, wedgeWidth=200, hasCorners=False)


class ScreenFrame4(ScreenFrameBase):
    """
    Simple brackets top and bottom
    """
    __guid__ = 'uicls.ScreenFrame4'
    default_name = 'ScreenFrame4'

    def ApplyAttributes(self, attributes):
        ScreenFrameBase.ApplyAttributes(self, attributes)
        self.topBracket = uicls.ScreenSimpleBracketTop(parent=self.bracketLayer)
        self.bottomBracket = uicls.ScreenSimpleBracketBottom(parent=self.bracketLayer)


class ScreenFrame5(ScreenFrame1):
    """
    Wedge brackets top and bottom and blinking squares fluff at bottom 
    """
    __guid__ = 'uicls.ScreenFrame5'
    default_name = 'ScreenFrame5'

    def ApplyAttributes(self, attributes):
        ScreenFrame1.ApplyAttributes(self, attributes)
        ScreenBlinkingSquares(parent=self.bracketLayer, padLeft=50, padBottom=-5, padRight=15)


class ScreenHeading1(uiprimitives.Container):
    """
    Heading with square slot on left for text or icon, text on the right and gradient
    background.
    
    Use self.leftCont and self.mainCont for adding content
    """
    __guid__ = 'uicls.ScreenHeading1'
    default_name = 'ScreenHeading1'
    default_align = uiconst.TOTOP
    default_fillColor = (0.180392157, 0.219607843, 0.239215686, 1.0)
    default_gradientColor = (0.152941176, 0.168627451, 0.17254902, 1.0)
    default_leftContWidth = 60
    default_height = 60

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        fillColor = attributes.get('fillColor', self.default_fillColor)
        gradientColor = attributes.get('gradientColor', self.default_gradientColor)
        leftContWidth = attributes.get('leftContWidth', self.default_leftContWidth)
        appear = attributes.get('appear', False)
        self.leftCont = uiprimitives.Container(name='leftCont', parent=self, align=uiconst.TOLEFT, width=leftContWidth)
        uiprimitives.Fill(name='leftBg', bgParent=self.leftCont, color=fillColor)
        self.mainCont = uiprimitives.Container(name='mainCont', parent=self, padLeft=0, padRight=0)
        gradient = uiprimitives.Sprite(name='rightGradient', bgParent=self.mainCont, color=gradientColor, texturePath='res:/UI/Texture/classes/CQMainScreen/gradientHoriz.png')
        if appear:
            uthread.new(self.AnimAppear)
        else:
            self.opacity = 0.0

    def AnimAppear(self):
        TIME_BASE = 0.2
        w, h = self.GetAbsoluteSize()
        self.opacity = 1.0
        uicore.animations.MorphScalar(self.leftCont, 'displayWidth', 0, self.leftCont.width, duration=TIME_BASE)
        uicore.animations.FadeIn(self.leftCont, duration=TIME_BASE / 3, loops=3, sleep=True)
        uicore.animations.MorphScalar(self.mainCont, 'displayWidth', 0, w - self.leftCont.width, duration=TIME_BASE)
        uicore.animations.FadeIn(self.mainCont, duration=TIME_BASE / 3, loops=3, sleep=True)


class ScreenHeading2(uiprimitives.Container):
    """
    Heading with dynamic dynamic bargraph on right side
    """
    __guid__ = 'uicls.ScreenHeading2'
    default_name = 'ScreenHeading2'
    default_height = 60
    default_width = 600
    default_align = uiconst.TOPLEFT
    default_text = ''
    default_opacity = 0.0
    default_hasBargraph = True

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        text = attributes.get('text', self.default_text)
        appear = attributes.get('appear', False)
        self.hasBargraph = attributes.get('hasBargraph', self.default_hasBargraph)
        rightCont = uiprimitives.Container(name='rightCont', parent=self, align=uiconst.TORIGHT, width=446, padBottom=5)
        uiprimitives.Sprite(name='rightGraphics', parent=rightCont, align=uiconst.TOBOTTOM, texturePath='res:/UI/Texture/classes/CQMainScreen/heading2.png', height=14)
        uiprimitives.Fill(name='thickLine', parent=self, align=uiconst.TOBOTTOM, height=6, padBottom=9, color=util.Color.WHITE)
        self.label = uicontrols.Label(parent=self, text=text, top=10, fontsize=30, color=util.Color.WHITE)
        self.movingFill = uiprimitives.Fill(name='movingFill', parent=self, align=uiconst.BOTTOMRIGHT, pos=(0, 0, 100, 3), color=util.Color.WHITE)
        if self.hasBargraph:
            barGraphCont = uiprimitives.Container(name='bargraphCont', parent=self, align=uiconst.TOPRIGHT, pos=(10, 8, 332, 31))
            self.barGraph = uiprimitives.Sprite(name='barGraph', parent=barGraphCont, texturePath='res:/UI/Texture/classes/CQMainScreen/barGraph.png', align=uiconst.CENTER, width=barGraphCont.width, height=31)
            self.barGraph.color.a = 0.6
        if appear:
            uthread.new(self.AnimAppear)

    def AnimAppear(self):
        TIME_BASE = 0.2
        uicore.animations.FadeIn(self, duration=TIME_BASE / 3, loops=3)
        uicore.animations.MorphScalar(self.movingFill, 'left', 0, 244, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_WAVE, duration=2.0)
        if self.hasBargraph:
            uicore.animations.MorphScalar(self.barGraph, 'height', 0, 45, curveType=uiconst.ANIM_RANDOM, duration=1.0)


class ScreenHeading3(uiprimitives.Container):
    """
    Simple heading with gray fill background
    """
    __guid__ = 'uicls.ScreenHeading3'
    default_name = 'ScreenHeading3'
    default_height = 60
    default_width = 600
    default_align = uiconst.TOPLEFT
    default_text = ''
    default_opacity = 0.0

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        text = attributes.get('text', self.default_text)
        appear = attributes.get('appear', False)
        self.label = uicontrols.EveLabelMedium(parent=self, align=uiconst.CENTER, fontsize=self.height - 25, text=text)
        uiprimitives.Fill(bgParent=self, color=(0.5, 0.5, 0.5, 1.0))
        if appear:
            uthread.new(self.AnimAppear)

    def AnimAppear(self):
        uicore.animations.BlinkIn(self, sleep=True)
        uicore.animations.BlinkIn(self.label, sleep=True)
        uicore.animations.MorphScalar(self.label, 'opacity', startVal=1.0, endVal=0.5, curveType=uiconst.ANIM_WAVE, loops=uiconst.ANIM_REPEAT)


class ScreenBlinkingSquares(uiprimitives.Container):
    """
    A fluff component that has three blinking squares bottom-right
    """
    __guid__ = 'uicls.ScreenBlinkingSquares'
    default_name = 'ScreenBlinkingSquares'
    default_height = 10
    default_align = uiconst.TOBOTTOM
    default_opacity = 0.0
    default_padBottom = 10
    default_padLeft = 10
    default_padRight = 10

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        left1 = uiprimitives.Fill(name='left1', parent=self, align=uiconst.TOLEFT, width=8, padBottom=5, color=util.Color.WHITE)
        left2 = uiprimitives.Fill(name='left2', parent=self, align=uiconst.TOLEFT, width=30, padLeft=3, color=util.Color.WHITE)
        left3 = uiprimitives.Fill(name='left3', parent=self, align=uiconst.TOLEFT, width=8, padLeft=3, color=util.Color.WHITE)
        self.label = uicontrols.EveLabelSmall(parent=self, align=uiconst.TOLEFT, width=100, padLeft=5)
        self.right1 = uiprimitives.Fill(name='right1', parent=self, align=uiconst.TORIGHT, width=50, color=util.Color.WHITE)
        self.right2 = uiprimitives.Fill(name='right2', parent=self, align=uiconst.TORIGHT, width=50, color=util.Color.WHITE, padRight=3)
        self.right3 = uiprimitives.Fill(name='right3', parent=self, align=uiconst.TORIGHT, width=50, color=util.Color.WHITE, padRight=3)

    def AnimAppear(self):
        TIME_BASE = 0.2
        uicore.animations.FadeIn(self, duration=TIME_BASE / 3, loops=3)
        uthread.new(self.UpdateBitCounter)
        uthread.new(self.UpdateText)

    def UpdateText(self):
        """ Update top secret hex ASCII message """
        x1 = 10000
        x2 = 30000
        msgList = ['59 4F 55 20',
         '48 41 56 45',
         '20 57 41 59',
         '20 54 4F 4F',
         '20 4D 55 43',
         '48 20 54 49',
         '4D 45 20 4F',
         '4E 20 59 4F',
         '55 52 20 48',
         '41 4E 44 53']
        while not self.destroyed:
            for msg in msgList:
                self.label.text = '<b>%s' % msg
                uicore.animations.FadeIn(self.label, duration=TIME_BASE / 3, loops=3)
                blue.pyos.synchro.SleepWallclock(random.randint(1000, 2000))
                if self.label.destroyed:
                    return

    def UpdateBitCounter(self):
        """
        A 3 bit binary clock
        """
        count = 0
        while not self.destroyed:
            val = max(0.2, count & 1)
            uicore.animations.FadeTo(self.right1, self.right1.opacity, val)
            val = max(0.2, count >> 1 & 1)
            uicore.animations.FadeTo(self.right2, self.right2.opacity, val)
            val = max(0.2, count >> 2 & 1)
            uicore.animations.FadeTo(self.right3, self.right3.opacity, val)
            count += 1
            if count == 8:
                count = 0
            blue.pyos.synchro.SleepWallclock(1000)


class AutoTextScroll(uiprimitives.Container):
    """
    A single line of text that automatically scrolls the text from left to right
    """
    __guid__ = 'uicls.AutoTextScroll'
    default_name = 'AutoScrollHorizontal'
    default_scrollSpeed = 10
    default_clipChildren = True
    default_textList = None
    default_fontSize = 30
    default_fadeColor = util.Color.BLACK
    default_fadeWidth = 100
    default_color = util.Color.WHITE

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        textList = attributes.get('textList', self.default_textList)
        self.scrollSpeed = attributes.get('scrollSpeed', self.default_scrollSpeed)
        self.fontSize = attributes.get('fontSize', self.default_fontSize)
        fadeColor = attributes.get('fadeColor', self.default_fadeColor)
        fadeWidth = attributes.get('fadeWidth', self.default_fadeWidth)
        self.color = attributes.get('color', self.default_color)
        self.scrollThread = None
        if fadeColor:
            uiprimitives.Sprite(name='leftFade', parent=self, texturePath='res:/UI/Texture/classes/CQMainScreen/autoTextGradientLeft.png', color=fadeColor, align=uiconst.TOLEFT, width=fadeWidth, state=uiconst.UI_DISABLED)
            uiprimitives.Sprite(name='leftFade', parent=self, texturePath='res:/UI/Texture/classes/CQMainScreen/autoTextGradientRight.png', color=fadeColor, align=uiconst.TORIGHT, width=fadeWidth, state=uiconst.UI_DISABLED)
        self.textCont = uiprimitives.Container(name='textCont', parent=self, align=uiconst.CENTERLEFT, height=self.fontSize)
        if textList:
            self.SetTextList(textList)

    def SetTextList(self, textList, funcList = None, funcKeywordsList = None):
        self.textCont.Flush()
        if self.scrollThread:
            self.scrollThread.kill()
        if not textList:
            return
        x = 0
        for i, text in enumerate(textList):
            if i != 0:
                bullet = uiprimitives.Sprite(parent=self.textCont, align=uiconst.CENTERLEFT, texturePath='res:/UI/texture/classes/CQMainScreen/bullet.png', pos=(x,
                 0,
                 11,
                 11), color=self.color)
                bulletWidth = bullet.width + 10
            else:
                bulletWidth = 0
            if funcList:
                clickFunc = funcList[i]
            else:
                clickFunc = None
            if funcKeywordsList:
                funcKeywords = funcKeywordsList[i]
            else:
                funcKeywords = None
            labelCont = uicls._AutoTextLabelCont(parent=self.textCont, clickFunc=clickFunc, funcKeywords=funcKeywords, left=x + bulletWidth, align=uiconst.TOPLEFT)
            label = uicontrols.Label(parent=labelCont, text='<b>%s' % text, fontsize=self.fontSize, color=self.color)
            labelCont.width = label.width
            labelCont.height = label.height
            x += label.width + 10 + bulletWidth

        self.textCont.width = x
        self.textCont.height = label.height
        self.scrollThread = uthread.new(self.ScrollThread)

    def ScrollThread(self):
        w, h = self.GetAbsoluteSize()
        self.textCont.left = w
        while not self.destroyed:
            duration = self.textCont.width / float(self.scrollSpeed)
            uicore.animations.MorphScalar(self.textCont, 'left', startVal=w, endVal=-self.textCont.width, duration=duration, curveType=uiconst.ANIM_LINEAR, sleep=True)


class LabelCont(uiprimitives.Container):
    __guid__ = 'uicls._AutoTextLabelCont'
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.hoverFill = uiprimitives.Fill(parent=self, color=(1.0, 1.0, 1.0, 0.0), padLeft=-5, padRight=-5)
        self.clickFunc = attributes.get('clickFunc', None)
        self.funcKeywords = attributes.get('funcKeywords', None)

    def OnMouseEnter(self, *args):
        if self.clickFunc:
            uicore.animations.FadeIn(self.hoverFill, endVal=0.5, duration=0.3)

    def OnMouseExit(self, *args):
        if self.clickFunc:
            uicore.animations.FadeOut(self.hoverFill)

    def OnClick(self, *args):
        if self.clickFunc:
            if self.funcKeywords:
                self.clickFunc(**self.funcKeywords)
            else:
                self.clickFunc()


class TextBanner(uiprimitives.Container):
    __guid__ = 'uicls.TextBanner'
    default_height = 80
    default_align = uiconst.TOBOTTOM
    default_leftContWidth = 0
    default_scrollText = True
    default_fontSize = 30
    default_color = (0.15, 0.15, 0.15, 1.0)

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        text = attributes.get('text', '')
        textList = attributes.get('textList', None)
        if textList is None:
            textList = [text]
        fontSize = attributes.get('fontSize', self.default_fontSize)
        leftContWidth = attributes.get('leftContWidth', self.default_leftContWidth)
        color = attributes.get('color', self.default_color)
        self.leftCont = uiprimitives.Container(name='leftCont', parent=self, align=uiconst.TOLEFT, width=leftContWidth)
        autoText = uicls.AutoTextScroll(parent=self, align=uiconst.TOALL, scrollSpeed=70, fontSize=fontSize, textList=textList, fadeColor=color)
        uiprimitives.Sprite(bgParent=self, texturePath='res:/UI/Texture/Classes/CQMainScreen/autoTextGradientLeft.png', color=color)
