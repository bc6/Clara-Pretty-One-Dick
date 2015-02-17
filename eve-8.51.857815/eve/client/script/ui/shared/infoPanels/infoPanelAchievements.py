#Embedded file name: eve/client/script/ui/shared/infoPanels\infoPanelAchievements.py
from achievements.common.achievementGroups import AllAchievementGroups
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.fill import Fill
from carbonui.primitives.frame import Frame
from carbonui.primitives.sprite import Sprite
from carbonui.util.color import Color
from eve.client.script.ui.control.eveLabel import EveLabelSmall, EveLabelMediumBold, EveLabelMedium
from eve.client.script.ui.shared.infoPanels import infoPanelConst
from eve.client.script.ui.shared.infoPanels.InfoPanelBase import InfoPanelBase
import carbonui.const as uiconst
from eve.client.script.ui.shared.infoPanels.infoPanelConst import PANEL_ACHIEVEMENTS
from localization import GetByLabel
OVERLAYROOT = 'res:/UI/Texture/Classes/Tutorial/OverlayAssets/'
COLOR_COMPLETED_BG = Color.HextoRGBA('0x3aa0cc')
COLOR_INCOMPLETE_BG = Color.HextoRGBA('0x787878')
COLOR_COMPLETED = Color.HextoRGBA('0x75d5ff')
COLOR_INCOMPLETED_TEXT = Color.HextoRGBA('0xffffff')
COLOR_NOT_STARTED_TEXT = Color.HextoRGBA('0xa0a0a0')

class InfoPanelAchievements(InfoPanelBase):
    __guid__ = 'uicls.InfoPanelAchievements'
    default_name = 'InfoPanelAchievements'
    default_iconTexturePath = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesPanelIcon.png'
    default_state = uiconst.UI_PICKCHILDREN
    default_height = 120
    label = 'UI/Achievements/OpportunitiesHint'
    hasSettings = False
    panelTypeID = PANEL_ACHIEVEMENTS
    __notifyevents__ = ['OnAchievementGroupSelectionChanged', 'OnAchievementsReady', 'OnAchievementChanged']

    def ApplyAttributes(self, attributes):
        InfoPanelBase.ApplyAttributes(self, attributes)
        self.headerTextCont = Container(name='headerTextCont', parent=self.headerCont, align=uiconst.TOALL)
        self.titleLabel = self.headerCls(name='title', text=GetByLabel('UI/Achievements/InfoPanelHeader'), parent=self.headerTextCont, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED)

    @staticmethod
    def IsAvailable():
        """ Is this info panel currently available for viewing """
        return settings.user.ui.Get('opportunities_showTemp', False)

    def GetAllGroups(self):
        allGroups = AllAchievementGroups().GetGroups()
        return allGroups

    def GetGroupFromGroupID(self, groupID):
        allGroups = AllAchievementGroups().GetGroups()
        return allGroups.get(groupID, None)

    def ConstructCompact(self):
        self.mainCont.Flush()

    def ConstructNormal(self):
        self.mainCont.Flush()
        completedText = self.GetCompletedText()
        subTextCont = Container(parent=self.mainCont, name='subTextCont', align=uiconst.TOTOP, height=20)
        self.backSprite = Sprite(name='arrow', parent=subTextCont, pos=(0, 0, 14, 14), texturePath='res:/UI/Texture/Classes/InfoPanels/opportunitiesReturnArrow.png', state=uiconst.UI_NORMAL, align=uiconst.CENTERLEFT)
        self.backSprite.OnClick = self.OnBackClicked
        self.backSprite.display = False
        self.subTextLabel = EveLabelMediumBold(parent=subTextCont, align=uiconst.CENTERLEFT, text=completedText, state=uiconst.UI_DISABLED)
        self.subTextLabel.OnClick = self.OnBackClicked
        self.achievementContent = ContainerAutoSize(parent=self.mainCont, name='achievementContent', height=30, align=uiconst.TOTOP, padBottom=4)
        groupID = settings.user.ui.Get('opportunities_infoPanel_group', None)
        self.LoadContent(groupID)

    def GetCompletedText(self):
        allGroups = self.GetAllGroups()
        completedGroups = 0
        for eachGroupInfo in allGroups.itervalues():
            totalNum = len(eachGroupInfo.achievements)
            completed = len([ x for x in eachGroupInfo.achievements if x.completed ])
            if completed == totalNum:
                completedGroups += 1

        completedText = GetByLabel('UI/Achievements/InfoPanelCompletedText', completedNum=completedGroups, totalNum=len(allGroups))
        return completedText

    def LoadContent(self, groupID = None):
        self.achievementContent.Flush()
        self.ChangeSubTextCont(bool(groupID))
        if groupID:
            self.LoadOneDetailedGroup(groupID)
        else:
            self.LoadGroups()

    def LoadOneDetailedGroup(self, groupID):
        settings.user.ui.Set('opportunities_infoPanel_group', groupID)
        selectedGroup = self.GetGroupFromGroupID(groupID)
        if not selectedGroup:
            return self.LoadGroups()
        self.AddGroupEntry(selectedGroup, isExpanded=True)

    def LoadGroups(self):
        settings.user.ui.Set('opportunities_infoPanel_group', None)
        allGroups = self.GetAllGroups()
        for eachGroupID, eachGroup in allGroups.iteritems():
            self.AddGroupEntry(eachGroup, isExpanded=False)

    def AddGroupEntry(self, groupInfo, isExpanded):
        entry = AchievementGroup(parent=self.achievementContent, align=uiconst.TOTOP, groupInfo=groupInfo, isExpanded=isExpanded, clickCallback=self.OnGroupClicked)
        return entry

    def OnGroupClicked(self, groupInfo, isExpanded):
        if isExpanded:
            self.GoBack()
        else:
            self.ExpandGroup(groupInfo)

    def OnBackClicked(self, *args):
        self.GoBack()

    def GoBack(self):
        self.ChangeSubTextCont(groupIsExpanded=False)
        self.LoadContent()

    def ExpandGroup(self, groupInfo):
        self.LoadContent(groupInfo.groupID)
        self.ChangeSubTextCont(groupIsExpanded=True)

    def ChangeSubTextCont(self, groupIsExpanded):
        if groupIsExpanded:
            self.backSprite.display = True
            self.subTextLabel.left = 20
            self.subTextLabel.text = GetByLabel('UI/Achievements/InfoPanelShowAllCategories')
            self.subTextLabel.state = uiconst.UI_NORMAL
        else:
            self.backSprite.display = False
            self.subTextLabel.left = 0
            self.subTextLabel.text = self.GetCompletedText()
            self.subTextLabel.state = uiconst.UI_DISABLED

    def OnInfoHeaderClicked(self, container, *args):
        return self.OnHeaderClicked(self.infoContent, container.isOpen)

    def OnAchievementHeaderClicked(self, container, *args):
        return self.OnHeaderClicked(self.achievementContent, container.isOpen)

    def OnHeaderClicked(self, subContainer, isOpen):
        if isOpen:
            subContainer.display = True
        else:
            subContainer.display = False

    def OnAchievementGroupSelectionChanged(self):
        self.Refresh()

    def OnAchievementsReady(self, *args):
        self.Refresh()

    def OnAchievementChanged(self):
        self.Refresh()

    def Refresh(self):
        if self.mode != infoPanelConst.MODE_NORMAL:
            self.ConstructCompact()
        else:
            self.ConstructNormal()


class SectionHeader(Container):
    default_height = 20

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.isOpen = True
        headerText = attributes.headerText
        self.toggleFunc = attributes.toggleFunc
        self.arrowSprite = Sprite(name='arrow', parent=self, pos=(0, 0, 16, 16), texturePath='res:/UI/Texture/Icons/38_16_229.png', state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
        self.tipsHeader = EveLabelMediumBold(name='tipsHeader', text=headerText, parent=self, left=16, align=uiconst.CENTERLEFT)

    def OnClick(self, *args):
        if self.isOpen:
            self.arrowSprite.SetTexturePath('res:/UI/Texture/Icons/38_16_228.png')
        else:
            self.arrowSprite.SetTexturePath('res:/UI/Texture/Icons/38_16_229.png')
        self.isOpen = not self.isOpen
        self.toggleFunc(self)


class ExtraInfoEntry(Container):
    default_padLeft = 30
    default_padRight = 30
    default_padTop = 6

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        info = attributes.info
        self.icon = Sprite(name='arrow', parent=self, pos=(0,
         0,
         info['size'],
         info['size']), texturePath=info['path'], state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT)
        self.text = EveLabelSmall(name='tipsHeader', text=info['text'], parent=self, left=info['size'] + 2, top=1, align=uiconst.TOPLEFT)
        iconColor = info.get('color', None)
        if iconColor:
            self.icon.SetRGB(*iconColor)

    def UpdateAlignment(self, *args, **kwds):
        retVal = Container.UpdateAlignment(self, *args, **kwds)
        if getattr(self, 'icon', None) and getattr(self, 'text', None):
            newHeight = max(self.icon.height + 2 * self.icon.top, self.text.textheight + 2 * self.text.padTop)
            self.height = newHeight
        return retVal


class AchievementEntry(Container):
    default_padLeft = 5
    default_padRight = 5
    default_padTop = 5
    default_padBottom = 2
    checkedTexturePath = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesCheck.png'
    uncheckedTexturePath = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesIncompleteBox.png'
    backgroundGradient = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesCriteriaRowBack.png'

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.bgSprite = Sprite(parent=self, texturePath=self.backgroundGradient, align=uiconst.TOALL)
        self.achievement = attributes.achievement
        self.checkbox = Sprite(parent=self, texturePath=self.uncheckedTexturePath, pos=(4, 4, 14, 14))
        self.achievementText = EveLabelMedium(name='achievementText', text=self.achievement.name, parent=self, padLeft=2 * self.checkbox.left + self.checkbox.width, align=uiconst.TOTOP, padTop=4)
        self.SetCompletedStates(self.achievement.completed)

    def SetCompletedStates(self, checked):
        if checked:
            texturePath = self.checkedTexturePath
            bgColor = COLOR_COMPLETED_BG
            textColor = COLOR_COMPLETED
        else:
            texturePath = self.uncheckedTexturePath
            bgColor = COLOR_INCOMPLETE_BG
            textColor = COLOR_NOT_STARTED_TEXT
        self.checkbox.SetTexturePath(texturePath)
        self.bgSprite.SetRGBA(*bgColor)
        self.achievementText.SetRGB(*textColor)

    def UpdateAlignment(self, *args, **kwds):
        retVal = Container.UpdateAlignment(self, *args, **kwds)
        if getattr(self, 'achievementText', None) and getattr(self, 'checkbox', None):
            newHeight = max(self.checkbox.height + 2 * self.checkbox.top, self.achievementText.textheight + 2 * self.achievementText.padTop)
            self.height = newHeight
        return retVal


class AchievementGroup(ContainerAutoSize):
    default_padTop = 3
    default_padBottom = 3
    headerHeight = 20
    default_alignMode = uiconst.TOTOP
    texturePath = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesIcon_Explore.png'
    progressBackground = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesFillBar.png'
    fillBox = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesFillBox.png'
    checkmarkPath = 'res:/UI/Texture/Classes/InfoPanels/opportunitiesCheck.png'

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        self.groupInfo = attributes.groupInfo
        self.isExpanded = attributes.isExpanded
        self.clickCallback = attributes.clickCallback
        iconColumn = Container(parent=self, name='iconColumn', align=uiconst.TOLEFT, width=20)
        self.icon = Sprite(name='groupIcon', parent=iconColumn, pos=(0, 0, 16, 16), texturePath=self.groupInfo.iconPath, state=uiconst.UI_DISABLED, align=uiconst.CENTERTOP)
        headerCont = Container(parent=self, name='headerCont', align=uiconst.TOTOP, state=uiconst.UI_NORMAL, height=self.headerHeight)
        headerCont.OnClick = (self.clickCallback, self.groupInfo, self.isExpanded)
        headerCont.OnMouseEnter = self.OnMouseEnterHeader
        headerCont.OnMouseExit = self.OnMouseExitHeader
        self.bodyCont = ContainerAutoSize(parent=self, name='bodyCont', align=uiconst.TOTOP)
        Fill(bgParent=self.bodyCont, color=(0.1, 0.1, 0.1, 0.2))
        self.groupText = EveLabelMediumBold(name='groupText', text=self.groupInfo.groupName, parent=headerCont, left=4, align=uiconst.CENTERLEFT)
        self.progressText = EveLabelMediumBold(name='progressText', text='', parent=headerCont, left=4, align=uiconst.CENTERRIGHT)
        self.fillBoxFrame = Frame(bgParent=headerCont, name='progress', texturePath=self.fillBox, cornerSize=2)
        progressCont = Container(parent=headerCont, name='progressCont', align=uiconst.TOALL)
        bgColor = [ x for x in COLOR_COMPLETED[:3] ] + [0.15]
        self.completedBg = Fill(bgParent=progressCont, color=tuple(bgColor))
        self.completedBg.display = False
        self.progressFrame = Frame(parent=progressCont, name='progressFrame', texturePath=self.progressBackground, cornerSize=2, width=0.0, align=uiconst.TOLEFT_PROP)
        self.checkmark = Sprite(name='checkmark', parent=headerCont, pos=(0, 0, 16, 16), texturePath=self.checkmarkPath, state=uiconst.UI_DISABLED, align=uiconst.CENTERRIGHT)
        self.SetProgress()
        if self.isExpanded:
            self.AddAchievementEntries()
            self.AddExtraInfo()
            self.AddPadding()

    def SetProgress(self):
        totalNum = len(self.groupInfo.achievements)
        completed = len([ x for x in self.groupInfo.achievements if x.completed ])
        percentage = float(completed) / totalNum
        self.progressFrame.width = percentage
        self.progressText.text = GetByLabel('UI/Achievements/InfoPanelGroupPercentage', percentCompleted=round(percentage * 100))
        if completed >= totalNum:
            self.SetCompletedProgress()
        elif completed < 1:
            self.SetNotStartedProgress()
        else:
            self.SetIncompleteProgress()

    def SetCompletedProgress(self):
        self.SetProgressStates(color=COLOR_COMPLETED, bgOn=True, showProgressFrame=False, showCheckMark=True, showProgressText=False)

    def SetIncompleteProgress(self):
        self.SetProgressStates(color=COLOR_INCOMPLETED_TEXT)

    def SetNotStartedProgress(self):
        self.SetProgressStates(color=COLOR_NOT_STARTED_TEXT, showProgressFrame=False)

    def SetProgressStates(self, color, bgOn = False, showProgressFrame = True, showCheckMark = False, showProgressText = True):
        self.completedBg.display = bgOn
        self.progressFrame.display = showProgressFrame
        self.checkmark.display = showCheckMark
        self.progressText.display = showProgressText
        self.progressText.SetRGB(*color)
        self.groupText.SetRGB(*color)
        self.icon.SetRGB(*color)

    def AddAchievementEntries(self):
        for eachAchievement in self.groupInfo.achievements:
            entry = AchievementEntry(parent=self.bodyCont, align=uiconst.TOTOP, achievement=eachAchievement)

    def AddExtraInfo(self):
        if not self.groupInfo.extraInfo:
            return
        extraInfo = self.groupInfo.extraInfo
        sectionHeader = SectionHeader(parent=self.bodyCont, headerText=GetByLabel('UI/Achievements/TipsAndInfoHeader'), toggleFunc=self.OnInfoHeaderClicked, state=uiconst.UI_NORMAL, align=uiconst.TOTOP)
        self.infoCont = ContainerAutoSize(parent=self.bodyCont, name='infoCont', align=uiconst.TOTOP)
        self.tipsText = EveLabelSmall(name='tipsText', text=self.groupInfo.groupHint, parent=self.infoCont, padLeft=16, align=uiconst.TOTOP)
        for each in extraInfo:
            ExtraInfoEntry(parent=self.infoCont, info=each, align=uiconst.TOTOP)

    def AddPadding(self):
        Container(parent=self.bodyCont, name='padding', align=uiconst.TOTOP, height=6)

    def OnInfoHeaderClicked(self, *args):
        self.infoCont.display = not self.infoCont.display

    def OnMouseEnterHeader(self, *args):
        self.ChangeAlphaOnUIElements(2.0)

    def OnMouseExitHeader(self, *args):
        self.ChangeAlphaOnUIElements(1.0)

    def ChangeAlphaOnUIElements(self, alpha):
        self.fillBoxFrame.SetAlpha(alpha)
        self.progressText.SetAlpha(alpha)
        self.groupText.SetAlpha(alpha)
