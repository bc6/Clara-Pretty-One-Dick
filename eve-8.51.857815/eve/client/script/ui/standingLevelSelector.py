#Embedded file name: eve/client/script/ui\standingLevelSelector.py
from eve.client.script.ui.shared.stateFlag import AddAndSetFlagIcon
import uiprimitives
import uicontrols
import uicls
import carbonui.const as uiconst
import localization
import state

class StandingLevelSelector(uiprimitives.Container):
    __guid__ = 'uicls.StandingLevelSelector'

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.level = attributes.get('level', None)
        self.iconPadding = attributes.get('iconPadding', 6)
        self.vertical = attributes.get('vertical', False)
        if attributes.get('callback', None):
            self.OnStandingLevelSelected = attributes.get('callback', None)
        self.ConstructLayout()

    def ConstructLayout(self):
        self.standingList = {const.contactHighStanding: localization.GetByLabel('UI/PeopleAndPlaces/ExcellentStanding'),
         const.contactGoodStanding: localization.GetByLabel('UI/PeopleAndPlaces/GoodStanding'),
         const.contactNeutralStanding: localization.GetByLabel('UI/PeopleAndPlaces/NeutralStanding'),
         const.contactBadStanding: localization.GetByLabel('UI/PeopleAndPlaces/BadStanding'),
         const.contactHorribleStanding: localization.GetByLabel('UI/PeopleAndPlaces/TerribleStanding')}
        levelList = self.standingList.keys()
        levelList.sort()
        shift = 20 + self.iconPadding
        for i, relationshipLevel in enumerate(levelList):
            leftPos = i * shift * float(not self.vertical)
            rightPos = i * shift * float(self.vertical)
            contName = 'level%d' % i
            level = uicls.StandingsContainer(name=contName, parent=self, align=uiconst.TOPLEFT, pos=(leftPos,
             rightPos,
             20,
             20), level=relationshipLevel, text=self.standingList.get(relationshipLevel), windowName='contactmanagement')
            setattr(self.sr, contName, level)
            level.OnClick = (self.LevelOnClick, relationshipLevel, level)
            if self.level == relationshipLevel:
                level.sr.selected.state = uiconst.UI_DISABLED
                uicore.registry.SetFocus(level)

    def LevelOnClick(self, level, container, *args):
        for i in xrange(0, 5):
            cont = self.sr.Get('level%d' % i)
            cont.sr.selected.state = uiconst.UI_HIDDEN

        container.sr.selected.state = uiconst.UI_DISABLED
        self.level = level
        if hasattr(self, 'OnStandingLevelSelected'):
            self.OnStandingLevelSelected(level)

    def GetValue(self):
        return self.level


class StandingsContainer(uiprimitives.Container):
    __guid__ = 'uicls.StandingsContainer'

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        text = attributes.get('text', '')
        self.text = text
        level = attributes.get('level', None)
        self.level = level
        windowName = attributes.get('windowName', '')
        self.windowName = windowName
        self.Prepare_(text, level)
        self.cursor = 1

    def Prepare_(self, text = '', contactLevel = None, *args):
        self.isTabStop = 1
        self.state = uiconst.UI_NORMAL
        flag = None
        if contactLevel == const.contactHighStanding:
            flag = state.flagStandingHigh
        elif contactLevel == const.contactGoodStanding:
            flag = state.flagStandingGood
        elif contactLevel == const.contactNeutralStanding:
            flag = state.flagStandingNeutral
        elif contactLevel == const.contactBadStanding:
            flag = state.flagStandingBad
        elif contactLevel == const.contactHorribleStanding:
            flag = state.flagStandingHorrible
        if flag:
            flagContainer = AddAndSetFlagIcon(self, flag=flag, state=uiconst.UI_DISABLED)
            flagContainer.ChangeFlagPos(0, 0, 20, 20)
            flagContainer.ChangeIconPos(0, 0, 15, 15)
            uicontrols.Frame(parent=flagContainer, color=(1.0, 1.0, 1.0, 0.2))
            self.sr.selected = uicontrols.Frame(parent=flagContainer, color=(1.0, 1.0, 1.0, 0.75), state=uiconst.UI_DISABLED, idx=0)
            self.sr.selected.display = False
            self.sr.hilite = uicontrols.Frame(parent=flagContainer, color=(1.0, 1.0, 1.0, 0.75), state=uiconst.UI_DISABLED, idx=0)
            self.sr.hilite.display = False

    def OnMouseEnter(self, *args):
        if self.sr.hilite:
            self.sr.hilite.display = True

    def OnMouseExit(self, *args):
        if self.sr.hilite:
            self.sr.hilite.display = False

    def OnSetFocus(self, *args):
        if self.sr.hilite:
            self.sr.hilite.display = True

    def OnKillFocus(self, *args):
        if self.sr.hilite:
            self.sr.hilite.display = False

    def OnChar(self, char, *args):
        if char in (uiconst.VK_SPACE, uiconst.VK_RETURN):
            self.parent.LevelOnClick(self.level, self)
