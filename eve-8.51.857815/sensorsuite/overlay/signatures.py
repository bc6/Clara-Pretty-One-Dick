#Embedded file name: sensorsuite/overlay\signatures.py
import math
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.transform import Transform
from carbonui.uianimations import animations
from inventorycommon.const import groupCosmicSignature
import localization
from probescanning.const import probeScanGroupSignatures
from sensorsuite.overlay.anomalies import BaseScannableSiteData, AnomalyHandler
from sensorsuite.overlay.brackets import SensorSuiteBracket, INNER_ICON_COLOR
from sensorsuite.overlay.siteconst import SITE_COLOR_SIGNATURE
from sensorsuite.overlay.sitetype import SIGNATURE
import carbonui.const as uiconst

class SignatureSiteData(BaseScannableSiteData):
    """
    This is a data construct holding data we know about sites in a system for the sensor overlay
    """
    siteType = SIGNATURE
    baseColor = SITE_COLOR_SIGNATURE
    hoverSoundEvent = 'ui_scanner_state_signature'
    scanGroupID = probeScanGroupSignatures
    groupID = groupCosmicSignature

    def __init__(self, siteID, position, targetID, difficulty, deviation, signalStrength, dungeonNameID = None):
        BaseScannableSiteData.__init__(self, siteID, position, targetID, difficulty, dungeonNameID, None, None)
        self.deviation = deviation
        self.signalStrength = signalStrength

    def IsAccurate(self):
        """is the data accurate"""
        return self.signalStrength >= 1.0

    def GetBracketClass(self):
        return SignatureBracket


class SignatureBracket(SensorSuiteBracket):
    outerColor = SITE_COLOR_SIGNATURE.GetRGBA()
    innerColor = INNER_ICON_COLOR.GetRGBA()
    innerIconResPath = 'res:/UI/Texture/classes/SensorSuite/diamond2.png'
    outerTexturesAccurate = ('res:/UI/Texture/classes/SensorSuite/bracket_sig_accurate_1.png', 'res:/UI/Texture/classes/SensorSuite/bracket_sig_accurate_2.png', 'res:/UI/Texture/classes/SensorSuite/bracket_sig_accurate_3.png', 'res:/UI/Texture/classes/SensorSuite/bracket_sig_accurate_4.png')
    outerTexturesInaccurate = ('res:/UI/Texture/classes/SensorSuite/bracket_sig_inaccurate_1.png', 'res:/UI/Texture/classes/SensorSuite/bracket_sig_inaccurate_2.png', 'res:/UI/Texture/classes/SensorSuite/bracket_sig_inaccurate_3.png', 'res:/UI/Texture/classes/SensorSuite/bracket_sig_inaccurate_4.png')

    def _GetOuterTextures(self):
        if self.data.IsAccurate():
            return self.outerTexturesAccurate
        else:
            return self.outerTexturesInaccurate

    outerTextures = property(_GetOuterTextures)

    def ApplyAttributes(self, attributes):
        SensorSuiteBracket.ApplyAttributes(self, attributes)
        if not self.isScrollEntry:
            self.spinnerOpacity = 0.15
            self.CreateSpinningCircles()

    def SetOuterBracketTextures(self):
        for i, outerSprite in enumerate(self.outerSprites):
            outerSprite.SetTexturePath(self.outerTextures[i])

    def GetMenu(self):
        return self.data.GetMenu()

    def UpdateScanData(self):
        self.SetOuterBracketTextures()
        if self.data.dungeonNameID is not None:
            self.UpdateSiteName(localization.GetByMessageID(self.data.dungeonNameID))

    def DoEntryAnimation(self, curveSet = None, enable = False):
        self.AnimateSpinningCircleEnter(curveSet, timeOffset=0.3)
        SensorSuiteBracket.DoEntryAnimation(self, curveSet=curveSet, enable=enable)

    def CreateSpinningCircles(self):
        self.wheelTransformInner = Transform(parent=self, align=uiconst.CENTER, width=175, height=175, state=uiconst.UI_DISABLED)
        self.wheelTransformOuter = Transform(parent=self, align=uiconst.CENTER, width=175, height=175, state=uiconst.UI_DISABLED)
        self.wheelSpriteInner = Sprite(parent=self.wheelTransformInner, align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/SensorSuite/CircleDots_Inner.png', opacity=self.spinnerOpacity)
        self.wheelSpriteOuter = Sprite(parent=self.wheelTransformOuter, align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/SensorSuite/CircleDots_Outer.png', opacity=self.spinnerOpacity)

    def AnimateSpinningCircleEnter(self, curveSet, timeOffset):
        animations.FadeTo(self.wheelSpriteOuter, startVal=0.0, endVal=self.spinnerOpacity, duration=0.5, timeOffset=timeOffset)
        animations.FadeTo(self.wheelSpriteInner, startVal=0.0, endVal=self.spinnerOpacity, duration=0.5, timeOffset=timeOffset)
        animations.Tr2DRotateTo(self.wheelSpriteInner, startAngle=2 * math.pi, endAngle=0.0, loops=uiconst.ANIM_REPEAT, duration=60.0, curveType=uiconst.ANIM_LINEAR, curveSet=curveSet)
        animations.Tr2DRotateTo(self.wheelSpriteOuter, startAngle=0.0, endAngle=2 * math.pi, loops=uiconst.ANIM_REPEAT, duration=40.0, curveType=uiconst.ANIM_LINEAR, curveSet=curveSet)

    def GetBracketLabelText(self):
        return self.data.targetID


class SignatureHandler(AnomalyHandler):
    siteType = SIGNATURE
    filterIconPath = 'res:/UI/Texture/classes/SensorSuite/diamond2.png'
    filterLabel = 'UI/Inflight/Scanner/SignatureSiteFilterLabel'
    color = SITE_COLOR_SIGNATURE

    def GetSiteData(self, siteID, position, targetID, difficulty, deviation):
        return SignatureSiteData(siteID, position, targetID, difficulty, deviation, 0)
