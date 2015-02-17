#Embedded file name: eve/client/script/ui/station/fw\warzoneControl.py
"""
FW warzone control module
"""
import uicls
import carbonui.const as uiconst
import localization
import uiprimitives
import uicontrols
import uthread
import facwarCommon
import blue
from math import pi, ceil
SIDE_WIDTH = 0.1

class FWWarzoneControl(uiprimitives.Container):
    __guid__ = 'uicls.FWWarzoneControl'
    default_height = 140
    TIERHINTS = ('UI/FactionWarfare/Tier1Hint', 'UI/FactionWarfare/Tier2Hint', 'UI/FactionWarfare/Tier3Hint', 'UI/FactionWarfare/Tier4Hint', 'UI/FactionWarfare/Tier5Hint')

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        leftCont = uiprimitives.Container(name='leftCont', parent=self, align=uiconst.TOLEFT_PROP, width=SIDE_WIDTH)
        self.friendIcon = uicls.LogoIcon(name='friendIcon', parent=leftCont, align=uiconst.CENTER, width=32, height=32, top=-20, ignoreSize=True)
        rightCont = uiprimitives.Container(name='leftCont', parent=self, align=uiconst.TORIGHT_PROP, width=SIDE_WIDTH)
        self.foeIcon = uicls.LogoIcon(name='foeIcon', parent=rightCont, align=uiconst.CENTER, width=32, height=32, top=20, ignoreSize=True)
        self.topCont = uiprimitives.Container(name='topCont', parent=self, align=uiconst.TOTOP_PROP, height=0.4)
        self.bottomCont = uiprimitives.Container(name='bottomCont', parent=self, align=uiconst.TOBOTTOM_PROP, height=0.4)
        self.centerCont = uiprimitives.Container(name='centerCont', parent=self, bgColor=facwarCommon.COLOR_CENTER_BG, padding=2)
        w, h = self.centerCont.GetAbsoluteSize()
        spWidth = 134 / 16.0 * h
        self.friendBar = uiprimitives.Container(parent=self.centerCont, align=uiconst.TOLEFT_PROP, state=uiconst.UI_NORMAL, bgColor=facwarCommon.COLOR_FRIEND_BAR, clipChildren=True)
        self.friendBarSprite = uiprimitives.Sprite(parent=self.friendBar, state=uiconst.UI_HIDDEN, texturePath='res:/ui/texture/classes/InfluenceBar/influenceBarPositive.png', color=facwarCommon.COLOR_FRIEND_LIGHT, align=uiconst.TOLEFT, width=spWidth)
        self.friendPointer = uiprimitives.Container(name='friendPointer', align=uiconst.TOPLEFT_PROP, parent=self, pos=(0.0, 0.5, 2, 0.2), idx=0)
        uiprimitives.Line(parent=self.friendPointer, align=uiconst.TOLEFT, weight=2, padBottom=2, color=facwarCommon.COLOR_FRIEND_LIGHT)
        self.friendPointerTxt = uicontrols.EveHeaderLarge(name='friendPointerTxt', parent=self.friendPointer, align=uiconst.CENTERTOP, top=-28)
        uiprimitives.Sprite(name='friendTriangle', parent=self.friendPointer, texturePath='res:/ui/texture/icons/105_32_15.png', color=facwarCommon.COLOR_FRIEND_LIGHT, align=uiconst.CENTERTOP, rotation=pi / 2, width=32, height=32, top=-19)
        self.foeBar = uiprimitives.Container(parent=self.centerCont, align=uiconst.TORIGHT_PROP, state=uiconst.UI_NORMAL, bgColor=facwarCommon.COLOR_FOE_BAR, clipChildren=True)
        self.foeBarSprite = uiprimitives.Sprite(parent=self.foeBar, state=uiconst.UI_HIDDEN, texturePath='res:/ui/texture/classes/InfluenceBar/influenceBarPositive.png', color=facwarCommon.COLOR_FOE_LIGHT, align=uiconst.TORIGHT, width=spWidth)
        self.foePointer = uiprimitives.Container(name='foePointer', align=uiconst.TOPLEFT_PROP, parent=self, pos=(0.0, 0.5, 2, 0.2), idx=0)
        uiprimitives.Line(parent=self.foePointer, align=uiconst.TORIGHT, weight=2, padTop=2, color=facwarCommon.COLOR_FOE_LIGHT)
        self.foePointerTxt = uicontrols.EveHeaderLarge(name='foePointerTxt', parent=self.foePointer, align=uiconst.CENTERBOTTOM, top=-28)
        uiprimitives.Sprite(name='foeTriangle', parent=self.foePointer, texturePath='res:/ui/texture/icons/105_32_15.png', color=facwarCommon.COLOR_FOE_LIGHT, align=uiconst.CENTERBOTTOM, rotation=-pi / 2, width=32, height=32, top=-19)
        uthread.new(self.FetchValues)
        uthread.new(self.AnimateBars)

    def FetchValues(self):
        """ Fetch values from server and update UI """
        fwSvc = sm.StartService('facwar')
        self.friendID = fwSvc.GetActiveFactionID()
        warzoneInfo = fwSvc.GetFacWarZoneInfo(self.friendID)
        self.foeID = warzoneInfo.enemyFactionID
        self.friendPoints = warzoneInfo.factionPoints
        self.foePoints = warzoneInfo.enemyFactionPoints
        self.totalPoints = warzoneInfo.maxWarZonePoints
        self.friendIsAdvancing = warzoneInfo.zonesAdvancing[self.friendID]
        self.foeIsAdvancing = warzoneInfo.zonesAdvancing[self.foeID]
        self.UpdateValues()

    def UpdateValues(self):
        """ Update UI according to lates values """
        friendProportion = self.friendPoints / self.totalPoints
        foeProportion = self.foePoints / self.totalPoints
        self.friendBar.width = friendProportion
        self.foeBar.width = foeProportion
        self.friendBar.hint = localization.GetByLabel('UI/FactionWarfare/WarzoneProgress', points=self.friendPoints, pointsTotal=int(self.totalPoints))
        self.foeBar.hint = localization.GetByLabel('UI/FactionWarfare/WarzoneProgress', points=self.foePoints, pointsTotal=int(self.totalPoints))
        self.friendPointer.left = SIDE_WIDTH + (1.0 - 2 * SIDE_WIDTH) * friendProportion
        self.foePointer.left = 1.0 - SIDE_WIDTH - (1.0 - 2 * SIDE_WIDTH) * foeProportion
        self.friendPointerTxt.text = '%s%%' % localization.formatters.FormatNumeric(100 * friendProportion, decimalPlaces=1)
        self.foePointerTxt.text = '%s%%' % localization.formatters.FormatNumeric(100 * foeProportion, decimalPlaces=1)
        self.ConstructFriendSquares(friendProportion)
        self.ConstructFoeSquares(foeProportion)
        iconID = self.friendIcon.GetFactionIconID(self.friendID, True)
        self.friendIcon.LoadIcon(iconID, True)
        iconID = self.foeIcon.GetFactionIconID(self.foeID, True)
        self.foeIcon.LoadIcon(iconID, True)

    def AnimateBars(self):
        duration = 7.0
        blue.synchro.Sleep(1000)
        while not self.destroyed:
            w, h = self.centerCont.GetAbsoluteSize()
            self.friendBarSprite.state = uiconst.UI_DISABLED
            if self.friendIsAdvancing:
                self.friendBarSprite.rotation = 0.0
                uicore.animations.MorphScalar(self.friendBarSprite, 'left', -w, w, curveType=uiconst.ANIM_LINEAR, duration=duration)
            else:
                self.friendBarSprite.rotation = pi
                uicore.animations.MorphScalar(self.friendBarSprite, 'left', w, -w, curveType=uiconst.ANIM_LINEAR, duration=duration)
            self.foeBarSprite.state = uiconst.UI_DISABLED
            if self.foeIsAdvancing:
                self.foeBarSprite.rotation = pi
                uicore.animations.MorphScalar(self.foeBarSprite, 'left', -w, w, curveType=uiconst.ANIM_LINEAR, duration=duration)
            else:
                self.foeBarSprite.rotation = 0.0
                uicore.animations.MorphScalar(self.foeBarSprite, 'left', w, -w, curveType=uiconst.ANIM_LINEAR, duration=duration)
            blue.synchro.SleepWallclock(duration * 1000)

    def ConstructFriendSquares(self, proportion):
        self.topCont.Flush()
        for i in xrange(5):
            cont = uiprimitives.Container(parent=self.topCont, align=uiconst.TOLEFT_PROP, state=uiconst.UI_NORMAL, width=0.2, padding=(0, 20, 0, 2), hint=localization.GetByLabel(self.TIERHINTS[i]))
            subCont = uiprimitives.Container(parent=cont, padding=(2, 0, 2, 0))
            uiprimitives.Sprite(bgParent=subCont, texturePath='res:/UI/Texture/Classes/FWWindow/TierBlock.png', opacity=0.5)
            uiprimitives.Fill(bgParent=subCont, color=facwarCommon.COLOR_FRIEND)
            if proportion * 5 < i:
                cont.opacity = 0.2
            uicontrols.EveHeaderLarge(parent=subCont, align=uiconst.CENTERTOP, top=-22, text=localization.GetByLabel('UI/FactionWarfare/TierNum', tierNum=i + 1), color=facwarCommon.COLOR_FRIEND_LIGHT)

    def ConstructFoeSquares(self, proportion):
        self.bottomCont.Flush()
        for i in xrange(int(ceil(proportion * 5))):
            cont = uiprimitives.Container(parent=self.bottomCont, align=uiconst.TORIGHT_PROP, state=uiconst.UI_NORMAL, width=0.2, padding=(0, 2, 0, 20), hint=localization.GetByLabel(self.TIERHINTS[i]))
            subCont = uiprimitives.Container(parent=cont, padding=(2, 0, 2, 0))
            uiprimitives.Sprite(bgParent=subCont, texturePath='res:/UI/Texture/Classes/FWWindow/TierBlock.png', opacity=0.5)
            uiprimitives.Fill(bgParent=subCont, color=facwarCommon.COLOR_FOE)
            uicontrols.EveHeaderLarge(parent=subCont, align=uiconst.CENTERBOTTOM, top=-22, text=localization.GetByLabel('UI/FactionWarfare/TierNum', tierNum=i + 1), color=facwarCommon.COLOR_FOE_LIGHT)
