#Embedded file name: achievements/client\achievementWindow.py
from achievements.common.achievementConst import AchievementEventConst
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.checkbox import Checkbox
from eve.client.script.ui.control.eveWindow import Window
from carbonui.primitives.container import Container
import carbonui.const as uiconst
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.line import Line
from eve.client.script.ui.control.eveLabel import EveLabelMedium
from eve.client.script.ui.control.tabGroup import TabGroup
import listentry
import service

class AchievementEntry(Container):
    default_height = 20
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.achievement = attributes.Get('achievement', None)
        if self.achievement.isEnabled:
            alpha = 0.75
        else:
            alpha = 0.25
        if self.achievement.completed:
            textColor = (0.0, 1.0, 0.0, 1.0)
        else:
            textColor = (1.0,
             1.0,
             1.0,
             alpha)
        if self.achievement.isClientAchievement:
            clientText = ' (client)'
        else:
            clientText = ''
        self.label = EveLabelMedium(name='myLabel', parent=self, align=uiconst.CENTERLEFT, text='%s - %s%s' % (self.achievement.achievementID, self.achievement.name, clientText), left=4, color=textColor)
        self.hint = self.achievement.description
        self.UpdateState()

    def UpdateState(self):
        if self.achievement.completed:
            self.label.SetTextColor((0.0, 1.0, 0.0, 1.0))


class AchievementMainContainer(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.uiEntries = {}
        self._ConstructLayout()

    def AddElement(self, achievement):
        self.uiEntries[achievement.achievementID] = AchievementEntry(align=uiconst.TOTOP, parent=self.scrollContainer, achievement=achievement)

    def FlushData(self):
        self.scrollContainer.Flush()
        self.uiEntries = {}

    def _ConstructLayout(self):
        Button(parent=self, align=uiconst.TOTOP, func=self.ResetAll, label='Reset Achievement state', padBottom=4)
        self.scrollContainer = ScrollContainer(name='achievementScrollContainer', align=uiconst.TOALL, parent=self)

    def ResetAll(self, *args, **kwargs):
        sm.GetService('achievementSvc').ResetAllForCharacter()

    def UpdateAchievements(self, achievement):
        if achievement.achievementID in self.uiEntries:
            ui = self.uiEntries[achievement.achievementID]
            ui.UpdateState()


class ConditionsContainer(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.uiEntries = {}
        self._ConstructLayout()

    def _ConstructLayout(self):
        button = Button(parent=self, label='Refresh Conditions', func=self.FetchData, align=uiconst.TOTOP, padBottom=4)
        self.scrollContainer = ScrollContainer(name='achievementScrollContainer', align=uiconst.TOALL, parent=self)

    def FlushData(self):
        self.uiEntries = {}
        self.scrollContainer.Flush()

    def AddElement(self, conditionText, conditionCount):
        self.uiEntries[conditionText] = ConditionsEntry(align=uiconst.TOTOP, parent=self.scrollContainer, conditionText=conditionText, conditionCount=conditionCount)

    def UpdateStats(self, characterStats):
        for uiEntry in self.uiEntries.itervalues():
            uiEntry.SetConditionText(uiEntry.conditionText, '-')

        for condText, condCount in characterStats.iteritems():
            uiEntry = self.uiEntries.get(condText, None)
            if not uiEntry:
                continue
            uiEntry.SetConditionText(condText, condCount)

    def FetchData(self, *args):
        userStats = sm.GetService('achievementSvc').GetDebugStatsFromCharacter(force=True)
        self.UpdateStats(userStats)


class ConditionsEntry(Container):
    default_height = 20
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.conditionText = attributes.Get('conditionText')
        self.conditionCount = attributes.Get('conditionCount')
        self.label = EveLabelMedium(name='myLabel', parent=self, align=uiconst.CENTERLEFT, left=4, tabs=[200, 300], maxline=1)
        self.SetConditionText(self.conditionText, self.conditionCount)
        Line(parent=self, align=uiconst.TOBOTTOM, opacity=0.1)

    def SetConditionText(self, conditionText, conditionCount):
        text = '%s<t>%s' % (conditionText, conditionCount)
        self.label.text = text


class AchievementWindow(Window):
    default_caption = 'Window of Opportunity'
    default_windowID = 'windowOfOpportunity'
    default_width = 300
    default_height = 300
    default_topParentHeight = 0
    __notifyevents__ = ['OnAchievementsDataInitialized', 'OnAchievementChanged']

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        achievementSvc = sm.GetService('achievementSvc')
        isCharacterListening = sm.RemoteSvc('achievementTrackerMgr').IsCharacterIsListening(session.charid)
        if isCharacterListening:
            text = 'This character is listening for broadcasted opportunity changes'
        else:
            text = 'This character is <color=red><b>NOT</b></color> listening for broadcasted opportunity changes'
        EveLabelMedium(parent=self.sr.main, name='listeningLabel', text=text, align=uiconst.TOTOP, padding=(10, 4, 10, 4))
        maintabs = TabGroup(name='tabparent', align=uiconst.TOTOP, height=18, parent=self.sr.main)
        self.mainContainer = AchievementMainContainer(align=uiconst.TOALL, parent=self.sr.main, padding=const.defaultPadding)
        self.conditionsCont = ConditionsContainer(align=uiconst.TOALL, parent=self.sr.main, padding=const.defaultPadding)
        tabs = [['Achievements',
          None,
          self,
          'achievements',
          self.mainContainer], ['Conditions',
          None,
          self,
          'conditions',
          self.conditionsCont]]
        maintabs.Startup(tabs, groupID='achievements', autoselecttab=True)
        self.initData()

    def initData(self):
        achievementSvc = sm.GetService('achievementSvc')
        statsForCharacter = achievementSvc.GetDebugStatsFromCharacter()
        clientStats = achievementSvc.clientStatsTracker.statistics
        statsForCharacter.update(clientStats)
        self.FillConditions(statsForCharacter)
        self.FillAchievements(achievementSvc.GetFullAchievementList())

    def FillAchievements(self, allAchievements):
        self.mainContainer.FlushData()
        for achievement in allAchievements:
            self.mainContainer.AddElement(achievement)

    def FillConditions(self, statsForCharacter):
        toAdd = [ value for key, value in AchievementEventConst.__dict__.iteritems() if key.isupper() ]
        toAdd.sort()
        self.conditionsCont.FlushData()
        for each in toAdd:
            self.conditionsCont.AddElement(each, '-')

        self.conditionsCont.UpdateStats(statsForCharacter)

    def OnAchievementChanged(self, achievement, *args, **kwds):
        self.mainContainer.UpdateAchievements(achievement)

    def OnAchievementsDataInitialized(self):
        self.initData()
