#Embedded file name: eve/client/script/ui/hacking\hackingLine.py
import uiprimitives
import uicls
import carbonui.const as uiconst
import random
import hackingcommon.hackingConstants as hackingConst
import hackingUIConst
import geo2

class Line(object):
    """ A line between two tiles in the hacking minigame """
    __guid__ = 'hackingui.Line'

    def __init__(self, parent, tileFrom, tileTo):
        self.tileFrom = tileFrom
        self.tileTo = tileTo
        self.parent = parent
        k = hackingUIConst.TILE_SIZE / 2.0
        self.p0 = (self.tileFrom.left + k, self.tileFrom.top + k)
        self.p1 = (self.tileTo.left + k, self.tileTo.top + k)
        self.offset = geo2.Vec2Subtract(self.p1, self.p0)
        self.offset = geo2.Vec2Normalize(self.offset)
        self.center = geo2.Vec2Lerp(self.p0, self.p1, 0.5)
        self.lineType = self.GetLineType()
        self.line = uicls.VectorLine(parent=parent, align=uiconst.TOPLEFT)
        self.bleedSprite = None
        self.UpdateState()

    def UpdateState(self):
        tileFromData = self.tileFrom.tileData
        tileToData = self.tileTo.tileData
        if not tileFromData.IsFlippable() and not tileToData.IsFlippable():
            colorFrom = colorTo = hackingUIConst.COLOR_BLOCKED
        elif hackingConst.TYPE_NONE in (tileFromData.type, tileToData.type):
            colorFrom = colorTo = hackingUIConst.COLOR_UNEXPLORED
        else:
            colorFrom = colorTo = hackingUIConst.COLOR_EXPLORED
            self.ShowBleed()
        widthFrom = widthTo = hackingUIConst.WIDTH_LINE
        if tileFromData.blocked or tileFromData.type == hackingConst.TYPE_DEFENSESOFTWARE:
            colorFrom = (0.0, 0.0, 0.0, 0.5)
            widthFrom = 5.0
            if not (tileToData.blocked or tileToData.type == hackingConst.TYPE_DEFENSESOFTWARE):
                widthTo = 0.0
        if tileToData.blocked or tileToData.type == hackingConst.TYPE_DEFENSESOFTWARE:
            colorFrom = (0.0, 0.0, 0.0, 0.5)
            widthTo = 5.0
            if not (tileFromData.blocked or tileFromData.type == hackingConst.TYPE_DEFENSESOFTWARE):
                widthFrom = 0.0
        uicore.animations.SpColorMorphTo(self.line, self.line.colorFrom, colorFrom, attrName='colorFrom')
        uicore.animations.SpColorMorphTo(self.line, self.line.colorTo, colorFrom, attrName='colorTo')
        uicore.animations.MorphScalar(self.line, 'widthFrom', self.line.widthFrom, widthFrom)
        uicore.animations.MorphScalar(self.line, 'widthTo', self.line.widthTo, widthTo)
        offset1 = self.GetLineOffsetAmount(self.tileFrom.tileData.type)
        p0 = geo2.Vec2Add(self.p0, geo2.Vec2Scale(self.offset, offset1))
        self.line.translationFrom = p0
        offset2 = self.GetLineOffsetAmount(self.tileTo.tileData.type)
        p1 = geo2.Vec2Subtract(self.p1, geo2.Vec2Scale(self.offset, offset2))
        self.line.translationTo = p1

    def ShowBleed(self):
        """ Show bleed effect (crooked background lines) """
        if not self.bleedSprite:
            texturePath = self.GetBleedTexturePath()
            width, height = hackingUIConst.LINEBLEED_SIZE_BY_LINETYPE[self.lineType]
            left, top = self.center
            left -= width / 2.0
            top -= height / 2.0
            if self.lineType == hackingUIConst.LINETYPE_DECLINE:
                top += height
                height *= -1
            self.bleedSprite = uiprimitives.Sprite(name='bleedSprite', parent=self.parent, state=uiconst.UI_DISABLED, texturePath=texturePath, align=uiconst.TOPLEFT, pos=(left,
             top,
             width,
             height), opacity=0.0)
            uicore.animations.FadeTo(self.bleedSprite, 0.0, 0.5, callback=self.AnimateLine, timeOffset=random.random() * 0.6, loops=3, duration=0.1)

    def AnimateLine(self):
        uicore.animations.FadeTo(self.bleedSprite, self.bleedSprite.opacity, 0.2, duration=5.0, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_WAVE)

    def GetBleedTexturePath(self):
        if self.lineType == hackingUIConst.LINETYPE_HORIZONTAL:
            return random.choice(hackingUIConst.LINEBLEED_TEXTUREPATHS_HORIZONTAL)
        else:
            return random.choice(hackingUIConst.LINEBLEED_TEXTUREPATHS_DIAGONAL)

    def GetLineType(self):
        y0 = self.tileFrom.top
        y1 = self.tileTo.top
        x0 = self.tileFrom.left
        x1 = self.tileTo.left
        if y0 == y1:
            return hackingUIConst.LINETYPE_HORIZONTAL
        if y0 > y1:
            if x0 > x1:
                return hackingUIConst.LINETYPE_INCLINE
            else:
                return hackingUIConst.LINETYPE_DECLINE
        else:
            if x0 < x1:
                return hackingUIConst.LINETYPE_INCLINE
            return hackingUIConst.LINETYPE_DECLINE

    def GetLineOffsetAmount(self, tileType):
        if tileType == hackingConst.TYPE_SEGMENT:
            return 10.0
        elif tileType in (hackingConst.TYPE_DATACACHE, hackingConst.TYPE_UTILITYELEMENTTILE):
            return 16.0
        elif tileType in (hackingConst.TYPE_DEFENSESOFTWARE, hackingConst.TYPE_CORE):
            return 21.0
        else:
            return 10.0

    def AnimExit(self, num):
        """ Game ended animation """
        uicore.animations.FadeTo(self.line, self.line.opacity, 0.0, timeOffset=0.2 + num * 0.01, duration=0.2)
        if self.bleedSprite:
            uicore.animations.FadeTo(self.bleedSprite, self.bleedSprite.opacity, 0.0, timeOffset=0.2 + num * 0.01, duration=1.0)
