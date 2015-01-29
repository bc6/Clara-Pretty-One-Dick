#Embedded file name: eve/client/script/ui/hacking\hackingStatContainer.py
import uicontrols
import carbonui.const as uiconst
import uiprimitives
import uicls
import util
import hackingUIConst
import localization

class StatContainer(uiprimitives.Container):
    """ Displays a stat (strength or coherence) of a hacking game entity """
    __guid__ = 'hackingui.StatContainer'
    default_width = hackingUIConst.TILE_SIZE
    default_height = 12
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.statType = attributes.statType
        self.value = None
        self.diffQueue = []
        self.mainCont = uicontrols.ContainerAutoSize(parent=self, align=uiconst.CENTER)
        uiprimitives.Sprite(name='icon', parent=self.mainCont, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, texturePath=self.GetTexturePath(), pos=(0, 0, 10, 10), opacity=0.7)
        self.label = uicontrols.Label(name='label', parent=self.mainCont, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, color=util.Color.WHITE, fontsize=10, pos=(11, -1, 0, 0))
        self.diffLabel = None

    def SetValue(self, value):
        if value == self.value:
            return
        if self.value and value < self.value:
            uicore.animations.BlinkIn(self.label, loops=3)
        elif self.value and value > self.value:
            uicore.animations.FadeTo(self.label, 2.0, 1.0, duration=1.0)
        if self.value:
            self.AddDiffLabel(value)
        self.label.text = str(value)
        self.value = value

    def AddDiffLabel(self, value):
        diff = value - self.value
        if self.diffLabel:
            self.diffQueue.append(diff)
            return
        self._AddDiffLabel(diff)

    def _AddDiffLabel(self, diff):
        if diff > 0:
            text = '+%s' % diff
        else:
            text = '%s' % diff
        left = (self.width - self.mainCont.width) / 2 + 6
        self.diffLabel = uicontrols.Label(parent=self, align=self.GetDiffLabelAlign(), text=text, fontsize=10, left=left)
        duration = 1.0
        curveType = ((0.0, 0.0),
         (0.1, 1.0),
         (0.9, 1.0),
         (1.0, 0.0))
        uicore.animations.FadeTo(self.diffLabel, 0.0, 1.0, duration=duration, curveType=curveType)
        curveType = ((0.0, 5),
         (0.1, -13),
         (0.9, -13),
         (1.0, -25))
        uicore.animations.MorphScalar(self.diffLabel, 'top', 5, -15, duration=duration, curveType=curveType, callback=self.OnDiffLabelFadedOut)

    def OnDiffLabelFadedOut(self):
        self.diffLabel.Close()
        self.diffLabel = None
        if self.diffQueue:
            diff = self.diffQueue.pop(0)
            self._AddDiffLabel(diff)

    def GetHint(self):
        if self.hint:
            return self.hint
        if self.statType == hackingUIConst.STAT_STRENGTH:
            return localization.GetByLabel('UI/Hacking/Strength')
        if self.statType == hackingUIConst.STAT_COHERENCE:
            return localization.GetByLabel('UI/Hacking/Coherence')

    def GetTexturePath(self):
        if self.statType == hackingUIConst.STAT_STRENGTH:
            return 'res:/UI/Texture/classes/hacking/strength.png'
        if self.statType == hackingUIConst.STAT_COHERENCE:
            return 'res:/UI/Texture/classes/hacking/coherence.png'

    def GetDiffLabelAlign(self):
        if self.statType == hackingUIConst.STAT_STRENGTH:
            return uiconst.TOBOTTOM
        if self.statType == hackingUIConst.STAT_COHERENCE:
            return uiconst.TOTOP
