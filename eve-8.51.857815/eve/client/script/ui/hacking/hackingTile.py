#Embedded file name: eve/client/script/ui/hacking\hackingTile.py
from math import pi
import carbonui.const as uiconst
import uiprimitives
import uicontrols
import util
import localization
import random
from eve.client.script.ui.hacking.hackingStatContainer import StatContainer
import hackingcommon.hackingConstants as hackingConst
import hackingUIConst
import uthread
import blue
import inventorycommon.types

class Tile(uiprimitives.Container):
    __guid__ = 'hackingui.Tile'
    __notifyevents__ = ['OnSelectedUtilityElementChanged',
     'OnHackingUEDurationReduced',
     'OnDefenseSoftwareUnveiled',
     'OnCoreUnveiled',
     'OnHoneyPotHealed',
     'OnCoreContentsRevealed']
    default_width = hackingUIConst.TILE_SIZE
    default_height = hackingUIConst.TILE_SIZE
    pickRadius = hackingUIConst.TILE_SIZE
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.tileData = attributes.tileData
        self.bgColor = util.Color.WHITE
        self.iconColor = util.Color.WHITE
        self.emptySegmentTexturePath = None
        self.bgScale = (1.0, 1.0)
        self.mouseHoverSprite = uiprimitives.Sprite(name='mouseHoverSprite', parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/hacking/tileHover.png', opacity=0.0)
        self.coherenceCont = None
        self.strengthCont = None
        self.distanceIndicatorCont = None
        self.iconSprite = uiprimitives.Sprite(name='iconSprite', parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, width=hackingUIConst.TILE_ICON_SIZE, height=hackingUIConst.TILE_ICON_SIZE)
        self.tileBgTransform = uiprimitives.Transform(name='tileBgTransform', parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, width=hackingUIConst.TILE_ICON_SIZE, height=hackingUIConst.TILE_ICON_SIZE, scalingCenter=(0.5, 0.5), scale=self.bgScale)
        self.tileBgSprite = uiprimitives.Sprite(name='tileSprite', bgParent=self.tileBgTransform)
        self.utilElementMarkerSprite = None
        self.healingGivenSprite = None
        self.healingReceivedSprite = None
        self.UpdateTileState(hackingConst.EVENT_TILE_CREATED)

    def UpdateTileState(self, eventID = None, tileData = None):
        """ Update tile appearance according to state """
        tileType = self.tileData.type
        tileSubType = self.tileData.subtype
        self.tileBgSprite.SetTexturePath(self.GetTileBackgroundTexturePath())
        self.bgColor = self.GetTileBackgroundColor()
        uicore.animations.SpColorMorphTo(self.tileBgSprite, self.tileBgSprite.GetRGBA(), self.bgColor)
        self.iconSprite.SetTexturePath(self.GetIconTexturePath())
        self.iconColor = hackingUIConst.COLOR_TILE_ICON_BY_TYPE.get(tileType, util.Color.WHITE)
        uicore.animations.SpColorMorphTo(self.iconSprite, self.iconSprite.GetRGBA(), self.iconColor)
        if self.HasLargeIcon():
            uicore.animations.FadeOut(self.mouseHoverSprite, duration=0.1)
        if (self.HasLargeIcon() or tileType == hackingConst.TYPE_DATACACHE) and self.tileData.blocked:
            uicore.animations.FadeTo(self, self.opacity, 0.3, duration=0.3)
        else:
            uicore.animations.FadeIn(self, duration=0.3)
        if self.IsAttackable(tileType):
            self.ShowCoherence()
            self.ShowStrength()
        else:
            self.HideCoherence()
            self.HideStrength()
        if self.tileData.distanceIndicator > 0:
            uthread.new(self.ShowDistanceIndicator)
        if uicore.uilib.mouseOver == self:
            self.OnMouseEnter()
        if tileType == hackingConst.TYPE_SEGMENT:
            self.bgScale = (0.7, 0.7)
        else:
            self.bgScale = (1.0, 1.0)
        uicore.animations.Tr2DScaleTo(self.tileBgTransform, self.tileBgTransform.scale, self.bgScale, duration=0.6)
        if eventID == hackingConst.EVENT_TILE_FLIPPED and not self.IsAttackable(tileType):
            rotation = pi * (0.05 + 0.2 * random.random()) * random.choice((-1, 1))
            uicore.animations.Tr2DRotateTo(self.tileBgSprite, rotation, 0.0, duration=0.3)
            uicore.animations.FadeTo(self.tileBgSprite, 0.0, 1.0, duration=0.3)
        elif eventID == hackingConst.EVENT_ATTACK:
            if self.tileData.coherence > 0:
                uicore.animations.BlinkIn(self.iconSprite, duration=0.1, loops=3)
                uicore.animations.Tr2DScaleTo(self.tileBgTransform, self.bgScale, (0.9, 0.9), duration=0.15, curveType=uiconst.ANIM_WAVE)
            else:
                uicore.animations.BlinkIn(self.iconSprite, duration=0.1, loops=3)
        elif eventID == hackingConst.EVENT_OBJECT_KILLED:
            uicore.animations.BlinkIn(self.iconSprite, duration=0.1, loops=3)
        elif eventID == hackingConst.EVENT_TILE_REACHABLE and not self.tileData.blocked and tileType == hackingConst.TYPE_NONE:
            uicore.animations.BlinkIn(self, duration=0.1, loops=3)
        elif eventID == hackingConst.EVENT_TILE_CREATED and self.tileData.type == hackingConst.TYPE_SEGMENT:
            uthread.new(self.AnimBlinkFirstSegment)

    def AnimBlinkFirstSegment(self):
        uicore.animations.BlinkIn(self.mouseHoverSprite, timeOffset=0.6, loops=2, duration=0.15)
        blue.synchro.SleepSim(1200)
        uicore.animations.FadeOut(self.mouseHoverSprite, duration=0.6)

    def GetTileBackgroundTexturePath(self):
        tileType = self.tileData.type
        if tileType == hackingConst.TYPE_NONE:
            if not self.tileData.IsFlippable() or self.tileData.blocked:
                return 'res:/UI/Texture/classes/hacking/tileBlocked.png'
            else:
                return 'res:/UI/Texture/classes/hacking/tileUnflipped.png'
        else:
            if tileType in (hackingConst.TYPE_DATACACHE, hackingConst.TYPE_SEGMENT, hackingConst.TYPE_UTILITYELEMENTTILE):
                return self.GetEmptySegmentTexturePath()
            return 'res:/UI/Texture/classes/hacking/tileIconFrame.png'

    def GetTileBackgroundColor(self):
        tileType = self.tileData.type
        if tileType == hackingConst.TYPE_CORE:
            return hackingUIConst.COLOR_BY_SUBTYPE[self.tileData.subtype]
        elif self.tileData.blocked and tileType == hackingConst.TYPE_NONE:
            return hackingUIConst.COLOR_DEFENSE
        elif not self.tileData.IsFlippable():
            return hackingUIConst.COlOR_UNREACHABLE
        else:
            return hackingUIConst.COLOR_TILE_BG_BY_TYPE.get(tileType, util.Color.WHITE)

    def GetIconTexturePath(self):
        tileType = self.tileData.type
        if tileType == hackingConst.TYPE_DATACACHE:
            return 'res:/UI/Texture/classes/hacking/tileDataCache.png'
        elif tileType in (hackingConst.TYPE_DEFENSESOFTWARE, hackingConst.TYPE_CORE, hackingConst.TYPE_UTILITYELEMENTTILE):
            return hackingUIConst.ICONPATH_BY_SUBTYPE[self.tileData.subtype]
        else:
            return None

    def GetEmptySegmentTexturePath(self):
        if not self.emptySegmentTexturePath:
            self.emptySegmentTexturePath = random.choice(hackingUIConst.ICONPATHS_INFECTED)
        return self.emptySegmentTexturePath

    def ConstructMarkerSprite(self):
        if self.utilElementMarkerSprite is None:
            self.utilElementMarkerSprite = uiprimitives.Sprite(name='utilElementMarkerSprite', bgParent=self, texturePath='res:/UI/Texture/classes/hacking/utilTileMouseDown.png', opacity=0.0, padding=-20)

    def ShowCoherence(self):
        self.ConstructCoherenceCont()
        self.coherenceCont.Show()
        self.coherenceCont.SetValue(self.tileData.coherence)

    def ConstructCoherenceCont(self):
        if self.coherenceCont is None:
            self.coherenceCont = StatContainer(name='coherenceCont', statType=hackingUIConst.STAT_COHERENCE, parent=self, align=uiconst.CENTERTOP, top=-3)

    def HideCoherence(self):
        if self.coherenceCont:
            self.coherenceCont.Hide()

    def ShowStrength(self):
        self.ConstructStrengthCont()
        self.strengthCont.Show()
        self.strengthCont.SetValue(self.tileData.strength)

    def ConstructStrengthCont(self):
        if self.strengthCont is None:
            self.strengthCont = StatContainer(name='strengthCont', statType=hackingUIConst.STAT_STRENGTH, parent=self, align=uiconst.CENTERBOTTOM, top=-3)

    def HideStrength(self):
        if self.strengthCont:
            self.strengthCont.Hide()

    def ShowDistanceIndicator(self):
        if self.distanceIndicatorCont is None:
            self.distanceIndicatorCont = uicontrols.Label(name='distanceIndicatorCont', parent=self, align=uiconst.CENTER, fontsize=10, text=self.tileData.distanceIndicator, idx=0)
        uicore.animations.BlinkIn(self.distanceIndicatorCont, duration=0.1, loops=3)
        blue.synchro.SleepSim(1200)
        uicore.animations.FadeOut(self.distanceIndicatorCont, duration=0.6)
        self.tileData.distanceIndicator = 0

    def OnSelectedUtilityElementChanged(self, selected):
        if self.IsAttackable(self.tileData.type) and selected is not None:
            self.ConstructMarkerSprite()
            uicore.animations.FadeTo(self.utilElementMarkerSprite, 0.2, 1.0, duration=1.2, curveType=uiconst.ANIM_WAVE, loops=uiconst.ANIM_REPEAT)
        elif self.utilElementMarkerSprite:
            uicore.animations.FadeOut(self.utilElementMarkerSprite, duration=0.2, callback=self.utilElementMarkerSprite.Close)
            self.utilElementMarkerSprite = None

    def OnHackingUEDurationReduced(self, index, coord):
        if coord == self.tileData.coord:
            self.ConstructMarkerSprite()
            uicore.animations.FadeTo(self.utilElementMarkerSprite, 0.8, 0.0, duration=0.6)

    def GetTileHint(self):
        if self.tileData.blocked:
            ret = localization.GetByLabel('UI/Hacking/BlockedNode')
        elif self.tileData.subtype in hackingUIConst.DS_HINTS_BY_SUBTYPE:
            ret = localization.GetByLabel(hackingUIConst.DS_HINTS_BY_SUBTYPE[self.tileData.subtype])
        else:
            ret = localization.GetByLabel(hackingUIConst.HINTS_BY_TILE_TYPE[self.tileData.type])
        return ret

    def OnMouseEnter(self, *args):
        if self.tileData.blocked or not self.tileData.IsFlippable():
            return
        sm.GetService('audio').SendUIEvent('minigame_node' + str(len(self.tileData.neighbourTiles)))
        sm.GetService('hackingUI').SetTileHint(self.GetTileHint())
        color = util.Color(*self.bgColor).SetBrightness(1.0).GetRGBA()
        uicore.animations.SpColorMorphTo(self.tileBgSprite, self.tileBgSprite.GetRGBA(), color, duration=0.3)
        if self.HasLargeIcon():
            uicore.animations.SpColorMorphTo(self.iconSprite, self.iconSprite.GetRGBA(), util.Color.WHITE, duration=0.3)
        else:
            uicore.animations.FadeIn(self.mouseHoverSprite, duration=0.3)
        if self.IsAttackable(self.tileData.type):
            uicore.animations.Tr2DScaleTo(self.tileBgTransform, (1.0, 1.0), (1.05, 1.05), duration=0.8, curveType=uiconst.ANIM_WAVE)

    def OnMouseExit(self, *args):
        sm.GetService('hackingUI').SetTileHint(None)
        uicore.animations.SpColorMorphTo(self.tileBgSprite, self.tileBgSprite.GetRGBA(), self.bgColor, duration=0.3)
        uicore.animations.SpColorMorphTo(self.iconSprite, self.iconSprite.GetRGBA(), util.Color.WHITE, duration=0.3)
        if self.HasLargeIcon():
            uicore.animations.SpColorMorphTo(self.iconSprite, self.iconSprite.GetRGBA(), self.iconColor, duration=0.3)
        else:
            uicore.animations.FadeOut(self.mouseHoverSprite, duration=0.3)

    def OnMouseMove(self, *args):
        """ Pass value (ranging from 0 at edge to 99 at center) to audio engine for analog hover audio effect """
        l, t = self.GetAbsolutePosition()
        x = 2.0 * (uicore.uilib.x - l) / float(hackingUIConst.TILE_SIZE) - 1.0
        y = 2.0 * (uicore.uilib.y - t) / float(hackingUIConst.TILE_SIZE) - 1.0
        z = (x ** 2 + y ** 2) ** 0.5
        val = 99 * (1.0 - min(1.0, z))
        sm.GetService('audio').SetGlobalRTPC('minigame_mouseover', val)

    def OnMouseDown(self, *args):
        uthread.new(sm.GetService('hackingUI').OnTileClicked, self.tileData.coord)

    def IsAttackable(self, type):
        return type in (hackingConst.TYPE_CORE, hackingConst.TYPE_DEFENSESOFTWARE)

    def HasLargeIcon(self):
        return self.tileData.type in (hackingConst.TYPE_CORE, hackingConst.TYPE_DEFENSESOFTWARE, hackingConst.TYPE_UTILITYELEMENTTILE)

    def OnCoreUnveiled(self, coord):
        if coord == self.tileData.coord:
            uicore.animations.BlinkIn(self.iconSprite, loops=3, duration=0.2)

    def OnDefenseSoftwareUnveiled(self, coord):
        if coord == self.tileData.coord:
            uicore.animations.FadeTo(self.iconSprite, 0.0, 1.0, duration=0.3, timeOffset=0.2)

    def OnHoneyPotHealed(self, sourceCoord, healedCoord, amount):
        if sourceCoord == self.tileData.coord:
            self.ConstructHealingGivenSprite()
            duration = 0.5
            curve = ((0.0, 0),
             (0.2, 100),
             (0.8, 100),
             (1.0, 0))
            uicore.animations.MorphScalar(self.healingGivenSprite, 'width', duration=duration, curveType=curve)
            uicore.animations.MorphScalar(self.healingGivenSprite, 'height', duration=duration, curveType=curve)
            curve = ((0.0, 0.0),
             (0.2, 1.0),
             (0.8, 1.0),
             (1.0, 0.0))
            uicore.animations.FadeTo(self.healingGivenSprite, 0.0, 1.0, duration=duration, curveType=curve)
        elif healedCoord == self.tileData.coord:
            self.ConstructHealingReceivedSprite()
            duration = 0.2
            timeOffset = 0.1
            loops = 2
            uicore.animations.MorphScalar(self.healingReceivedSprite, 'width', 128, 0, duration=duration, timeOffset=timeOffset, loops=loops)
            uicore.animations.MorphScalar(self.healingReceivedSprite, 'height', 128, 0, duration=duration, timeOffset=timeOffset, loops=loops)
            uicore.animations.FadeTo(self.healingReceivedSprite, 0.0, 1.0, duration=duration, curveType=uiconst.ANIM_WAVE, timeOffset=timeOffset, loops=loops)

    def OnCoreContentsRevealed(self, coord, contentsList):
        if coord == self.tileData.coord:
            text = 'Contents:'
            for entry in contentsList:
                text = text + '<br>' + str(entry[1]) + 'x ' + inventorycommon.types.GetName(entry[0])

            self.hint = text

    def ConstructHealingGivenSprite(self):
        if self.healingGivenSprite is None:
            self.healingGivenSprite = uiprimitives.Sprite(name='healingGivenSprite', parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, color=hackingUIConst.COLOR_UNEXPLORED, texturePath='res:/UI/Texture/classes/hacking/healRing1.png', opacity=0.0)

    def ConstructHealingReceivedSprite(self):
        if self.healingReceivedSprite is None:
            self.healingReceivedSprite = uiprimitives.Sprite(name='healingReceivedSprite', parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, color=hackingUIConst.COLOR_UNEXPLORED, texturePath='res:/UI/Texture/classes/hacking/healRing2.png', opacity=0.0)
