#Embedded file name: achievements/client\achievementWindow.py
from achievements.common.achievementConst import AchievementEventConst
from achievements.common.achievementGroups import AllAchievementGroups
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.checkbox import Checkbox
from eve.client.script.ui.control.eveScroll import Scroll
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
        textColor = (1.0, 0.5, 0.5)
        if self.achievement.completed:
            textColor = (0.0, 0.7, 0.0)
        self.label = EveLabelMedium(name='myLabel', parent=self, align=uiconst.CENTERLEFT, text='%s - %s' % (self.achievement.id, self.achievement.name), left=4, hint='bleggibleg', textColor=textColor)
        self.label.SetTextColor(textColor)
        self.hint = self.achievement.description
        Line(parent=self, align=uiconst.TOBOTTOM, opacity=0.1)

    def blingUnlocked(self):
        self.label.SetTextColor((0.0, 1.0, 0.0))


class AchievementMainContainer(Container):
    default_state = uiconst.UI_PICKCHILDREN

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.uiEntries = {}
        self._ConstructLayout()

    def AddElement(self, achievement):
        self.uiEntries[achievement.id] = AchievementEntry(align=uiconst.TOTOP, parent=self.scrollContainer, achievement=achievement)

    def RemoveElement(self, achievementId):
        uiEntry = self.uiEntries[achievementId]
        self.scrollContainer._RemoveChild(uiEntry)

    def _PopulateList(self, entries):
        for achievement in entries:
            self.AddElement(achievement)

    def _ConstructLayout(self):
        self.scrollContainer = ScrollContainer(name='achievementScrollContainer', align=uiconst.TOALL, parent=self)

    def AchievementUnlock(self, achievement):
        if self.uiEntries.has_key(achievement.id):
            ui = self.uiEntries[achievement.id]
            ui.blingUnlocked()


class ConditionsContainer(Container):
    default_state = uiconst.UI_PICKCHILDREN
    __notifyevents__ = ['OnAchievementsReset']

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.uiEntries = {}
        self._ConstructLayout()
        sm.RegisterNotify(self)

    def _ConstructLayout(self):
        buttonCont = Container(parent=self, align=uiconst.TOTOP, height=30)
        Button(parent=buttonCont, label='Fetch', func=self.FecthData)
        self.scrollContainer = ScrollContainer(name='achievementScrollContainer', align=uiconst.TOALL, parent=self)

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

    def RemoveElement(self, conditionText):
        uiEntry = self.uiEntries[conditionText]
        self.scrollContainer._RemoveChild(uiEntry)

    def _PopulateList(self, entries):
        for achievement in entries:
            self.AddElement(achievement)

    def FecthData(self, btn):
        userStats = sm.GetService('achievementSvc').GetDebugStatsFromCharacter(force=True)
        self.UpdateStats(userStats)

    def OnAchievementsReset(self):
        self.FecthData()


class GroupContainer(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        scroll = Scroll(parent=self)
        allGroups = AllAchievementGroups().GetGroups()
        scrollList = []
        for eachGroup in allGroups.itervalues():
            data = {'label': eachGroup.groupName,
             'group': 'achievementGroups',
             'groupID': eachGroup.groupID,
             'OnChange': self.OnAchievementGroupSelected,
             'retval': eachGroup.groupID}
            entry = listentry.Get('Checkbox', data=data)
            scrollList.append(entry)

        scroll.LoadContent(contentList=scrollList)

    def OnAchievementGroupSelected(self, cb, *args):
        settings.user.ui.Set('achievements_groupSelected', cb.data['retval'])
        sm.ScatterEvent('OnAchievementGroupSelectionChanged')


class ConditionsEntry(Container):
    default_height = 20
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.conditionText = attributes.Get('conditionText')
        self.conditionCount = attributes.Get('conditionCount')
        self.label = EveLabelMedium(name='myLabel', parent=self, align=uiconst.CENTERLEFT, text='', left=4, tabs=[200, 300], maxline=1)
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
    __notifyevents__ = ['OnClientAchievementUnlocked', 'OnAchievementsReset']

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        settingCont = Container(parent=self.sr.main, name='settingCont', align=uiconst.TOTOP, height=60)
        isCharacterListening = sm.RemoteSvc('achievementTrackerMgr').IsCharacterIsListening(session.charid)
        if isCharacterListening:
            text = 'This character is listening for broadcasted opportunity changes'
        else:
            text = 'This character is <color=red><b>NOT</b></color> listening for broadcasted opportunity changes'
        listendingLabel = EveLabelMedium(parent=settingCont, name='listendingLabel', text=text, align=uiconst.TOTOP, padLeft=10)
        showOpportunities = settings.user.ui.Get('opportunities_showTemp', False)
        cb = Checkbox(text='Show in info panel', parent=settingCont, configName='opportunities_showTemp', checked=showOpportunities, callback=self.CheckBoxChange, prefstype=('user', 'ui'), align=uiconst.TOTOP, padding=(9, 4, 0, 0))
        self.mainContainer = AchievementMainContainer(align=uiconst.TOALL, parent=self.sr.main)
        self.conditionsCont = ConditionsContainer(align=uiconst.TOALL, parent=self.sr.main)
        self.groupCont = GroupContainer(align=uiconst.TOALL, parent=self.sr.main)
        tabs = [['Achievements',
          None,
          self,
          'achievements',
          self.mainContainer], ['Conditions',
          None,
          self,
          'conditions',
          self.conditionsCont], ['AchievementGroup',
          None,
          self,
          'groups',
          self.groupCont]]
        maintabs = TabGroup(name='tabparent', align=uiconst.TOTOP, height=18, parent=self.sr.main, idx=1, tabs=tabs, groupID='achievements', autoselecttab=True)
        self.initData()

    def initData(self):
        svc = sm.GetService('achievementSvc')
        statsForCharacter = svc.GetDebugStatsFromCharacter()
        self.FillConditions(statsForCharacter)
        if svc.HasData():
            self.FillAchievements(svc.GetFullAchievementList())

    def FillAchievements(self, allAchievements):
        for achievement in allAchievements:
            self.mainContainer.AddElement(achievement)

    def FillConditions(self, statsForCharacter):
        toAdd = [ value for key, value in AchievementEventConst.__dict__.iteritems() if key.isupper() ]
        toAdd.sort()
        for each in toAdd:
            self.conditionsCont.AddElement(each, '-')

        self.conditionsCont.UpdateStats(statsForCharacter)

    def OnClientAchievementUnlocked(self, achievement):
        self.mainContainer.AchievementUnlock(achievement)

    def CheckBoxChange(self, cb):
        sm.GetService('infoPanel').Reload()


class AchievementWindowService(service.Service):
    __guid__ = 'svc.achievementUISvc'
    service = 'svc.achievementUISvc'
    __slashhook__ = True

    def cmd_achievement_show(self, p):
        AchievementWindow.ToggleOpenClose()
