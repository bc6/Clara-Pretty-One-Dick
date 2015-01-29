#Embedded file name: eve/client/script/ui/station/medical\medical.py
import blue
import carbonui.const as uiconst
import dogma.const
import functools
import localization
import math
import uthread
from carbonui.uianimations import animations
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.line import Line
from carbonui.primitives.sprite import Sprite
from carbonui.util.color import Color
from contextlib import contextmanager
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.eveIcon import ItemIcon
from eve.client.script.ui.control.eveLabel import EveLabelLargeBold, EveLabelMedium, EveLabelMediumBold, WndCaptionLabel
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.control.eveWindowUnderlay import SpriteUnderlay
from eve.client.script.ui.station.medical.cloneStation import CloneStationWindow
from eve.client.script.ui.shared.shipTree.infoBubble import SkillEntry
from inventorycommon import types
from itertoolsext import Bundle
BACKGROUND_GRAY_COLOR = (0.2,
 0.2,
 0.2,
 0.3)
BLUE_COLOR = (0.0,
 0.54,
 0.8,
 1.0)
GRAY_COLOR = Color.GRAY6
GREEN_COLOR = (0.0,
 1.0,
 0.0,
 0.8)
LINE_COLOR = (1,
 1,
 1,
 0.2)
RED_COLOR = (1.0,
 0.275,
 0.0,
 1.0)
WHITE_COLOR = Color.GRAY9
JUMP_CLONE_SKILLS = [24242, 33407]

class MedicalWindow(Window):
    __guid__ = 'form.MedicalWindow'
    __notifyevents__ = ['OnCloneJumpUpdate',
     'OnGodmaSkillTrained',
     'OnHomeStationChanged',
     'OnSessionChanged']
    default_width = 480
    default_height = 100
    default_windowID = 'cloneBay'
    default_iconNum = 'res:/ui/Texture/WindowIcons/cloneBay.png'
    default_clipChildren = True
    default_isPinable = False
    default_captionLabelPath = 'Tooltips/StationServices/CloneBay'
    default_descriptionLabelPath = 'Tooltips/StationServices/CloneBay_description'
    PADDING = 12
    HALF_PADDING = PADDING / 2
    BUTTON_HEIGHT = 30
    BUTTON_WIDTH = 140
    TOP_PARENT_HEIGHT = 66

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.homeStationID = GetHomeStation()
        self.jumpCloneID = GetJumpClone()
        self.Layout()
        uthread.new(self.Reload)

    def Layout(self):
        self.HideHeader()
        self.MakeUnResizeable()
        self.SetWndIcon(self.iconNum, mainTop=2, mainLeft=6)
        self.SetTopparentHeight(self.TOP_PARENT_HEIGHT)
        station = cfg.stations.Get(session.stationid2)
        WndCaptionLabel(parent=self.sr.topParent, align=uiconst.RELATIVE, text=localization.GetByLabel('UI/Medical/Medical'), subcaption=station.stationName)
        self.container = ContainerAutoSize(parent=self.GetMainArea(), align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, padding=(self.PADDING,
         self.PADDING,
         self.PADDING,
         self.PADDING), callback=self.OnContainerResized, opacity=0.0)
        EveLabelLargeBold(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Medical/MedicalClone'))
        EveLabelMedium(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Medical/MedicalCloneDescription'), color=GRAY_COLOR, padding=(0,
         0,
         0,
         self.HALF_PADDING))
        self.homeStation = CreateSectionContainer(self.container)
        EveLabelLargeBold(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Medical/ActiveClone'), padding=(0,
         self.PADDING,
         0,
         0))
        EveLabelMedium(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Medical/DestroyActiveCloneDescription'), color=GRAY_COLOR, padding=(0,
         0,
         0,
         self.HALF_PADDING))
        EveLabelMediumBold(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Medical/DestroyActiveCloneWarning'), color=RED_COLOR, padding=(0,
         0,
         0,
         self.HALF_PADDING))
        self.activeClone = CreateSectionContainer(self.container)
        EveLabelLargeBold(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Medical/JumpClone'), padding=(0,
         self.PADDING,
         0,
         0))
        EveLabelMedium(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Medical/JumpCloneDescription'), color=GRAY_COLOR, padding=(0,
         0,
         0,
         self.HALF_PADDING))
        self.jumpClone = CreateSectionContainer(self.container)
        animations.FadeIn(self.container, duration=0.5)

    def Reload(self):
        if self.destroyed:
            return
        homeStationID = GetHomeStation()
        animate = homeStationID != self.homeStationID
        self.homeStationID = homeStationID
        uthread.new(self.ReloadHomeStation, animate=animate)
        uthread.new(self.ReloadSelfDestruct, animate=animate)
        jumpCloneID = GetJumpClone()
        animate = jumpCloneID != self.jumpCloneID
        self.jumpCloneID = jumpCloneID
        uthread.new(self.ReloadJumpClone, animate=animate)

    def ReloadHomeStation(self, animate = False):
        if animate:
            HideContainerContent(self.homeStation)
        stationNameLabel = PrepareStationLink(self.homeStationID)
        opacity = 0.0 if animate else 1.0
        with FlushAndLockAutoSize(self.homeStation):
            SectionEntry(parent=self.homeStation, align=uiconst.TOTOP, iconPath='res:/UI/Texture/WindowIcons/medical.png', title=localization.GetByLabel('UI/Medical/Clone/HomeStation'), titleColor=GREEN_COLOR, text=stationNameLabel, actionText=localization.GetByLabel('UI/Medical/ChangeStation'), actionCallback=lambda _: OpenHomeStationDialog(), opacity=opacity)
            if animate:
                RevealContainerContent(self.homeStation)

    def ReloadSelfDestruct(self, animate = False):
        if animate:
            HideContainerContent(self.activeClone)
        stationNameLabel = PrepareStationLink(self.homeStationID)
        opacity = 0.0 if animate else 1.0
        with FlushAndLockAutoSize(self.activeClone):
            errors = ValidateSelfDestruct()
            SectionEntry(parent=self.activeClone, align=uiconst.TOTOP, iconPath='res:/UI/Texture/WindowIcons/terminate.png', title=localization.GetByLabel('UI/Medical/SelfDestructHeader'), titleColor=GRAY_COLOR, text=stationNameLabel, actionText=localization.GetByLabel('UI/Medical/SelfDestruct'), actionCallback=lambda _: ActivateClone(), actionErrors=errors, opacity=opacity)
            if animate:
                RevealContainerContent(self.activeClone)

    def ReloadJumpClone(self, animate = False):
        if animate:
            HideContainerContent(self.jumpClone)
        if self.jumpCloneID:
            iconColor = WHITE_COLOR
            header = localization.GetByLabel('UI/Medical/JumpCloneInstalled')
            headerColor = BLUE_COLOR
            buttonText = localization.GetByLabel('UI/Medical/DestroyJumpClone')
            buttonFunc = lambda _: DestroyJumpClone()
            actionErrors = []
            clone = GetJumpCloneDetails()
            if clone.implants:
                subtext = localization.GetByLabel('UI/Medical/JumpCloneImplants', implantCount=len(clone.implants))
                subtextColor = WHITE_COLOR
                loadSubtextTooltip = functools.partial(LoadJumpCloneImplantTooltip, implants=clone.implants)
            else:
                subtext = localization.GetByLabel('UI/Medical/NoImplantsInstalled')
                subtextColor = GRAY_COLOR
                loadSubtextTooltip = None
            if clone.name:
                subtext = '%s - %s' % (clone.name, subtext)
        else:
            iconColor = GRAY_COLOR
            header = localization.GetByLabel('UI/Medical/NoJumpCloneInstalled')
            headerColor = GRAY_COLOR
            buttonText = localization.GetByLabel('UI/Medical/InstallJumpClone')
            buttonFunc = lambda _: InstallJumpClone()
            actionErrors = ValidateInstallJumpClone()
            cloneCount, cloneLimit = GetJumpCloneCountAndLimit()
            remaining = cloneLimit - cloneCount
            if cloneLimit == 0:
                subtext = localization.GetByLabel('UI/Medical/JumpCloneSkillReqNotMet')
                subtextColor = RED_COLOR
            elif remaining == 0:
                subtext = localization.GetByLabel('UI/Medical/JumpCloneSkillCapacityReached')
                subtextColor = RED_COLOR
            else:
                subtext = localization.GetByLabel('UI/Medical/JumpCloneRemainingCapacity', count=int(remaining))
                subtextColor = WHITE_COLOR
            loadSubtextTooltip = LoadJumpCloneCapacityTooltip
        opacity = 0.0 if animate else 1.0
        with FlushAndLockAutoSize(self.jumpClone):
            SectionEntry(parent=self.jumpClone, align=uiconst.TOTOP, iconPath='res:/UI/Texture/WindowIcons/jumpclones.png', iconColor=iconColor, title=header, titleColor=headerColor, text=subtext, textTooltipCallback=loadSubtextTooltip, textColor=subtextColor, actionText=buttonText, actionCallback=buttonFunc, actionErrors=actionErrors, opacity=opacity)
            if animate:
                RevealContainerContent(self.jumpClone)

    def OnCloneJumpUpdate(self):
        uthread.new(self.Reload)

    def OnContainerResized(self):
        """
        Callback for the parent auto resized container, we set the overall
        window height to fit the contents of the resizeable container here.
        This allows localized text to wrap around and push out the height of
        this window.
        """
        self.width = self.default_width
        totalHeight = self.container.height + self.TOP_PARENT_HEIGHT + self.PADDING * 2
        self.height = totalHeight

    def OnGodmaSkillTrained(self, skillItemID):
        skill = sm.GetService('godma').GetItem(skillItemID)
        if not skill:
            return
        if skill.typeID in JUMP_CLONE_SKILLS:
            uthread.new(self.Reload)

    def OnHomeStationChanged(self, stationID):
        uthread.new(self.Reload)

    def OnSessionChanged(self, isRemote, sess, change):
        if 'stationid2' in change:
            self.Close()


class SectionEntry(ContainerAutoSize):
    default_alignMode = uiconst.TOTOP
    default_iconColor = WHITE_COLOR
    default_titleColor = WHITE_COLOR
    default_textColor = GRAY_COLOR
    BUTTON_FONT_SIZE = 13
    BUTTON_HEIGHT = 30
    BUTTON_WIDTH = 140
    ICON_SIZE = 32
    PADDING = 5

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        iconPath = attributes.iconPath
        iconColor = attributes.get('iconColor', self.default_iconColor)
        title = attributes['title']
        titleColor = attributes.get('titleColor', self.default_titleColor)
        text = attributes['text']
        textColor = attributes.get('textColor', self.default_textColor)
        textTooltipCallback = attributes.get('textTooltipCallback', None)
        actionCallback = attributes.get('actionCallback', None)
        actionText = attributes['actionText']
        self.actionErrors = attributes.get('actionErrors', [])
        Sprite(parent=self, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, texturePath=iconPath, color=iconColor, left=self.PADDING, height=self.ICON_SIZE, width=self.ICON_SIZE)
        EveLabelMediumBold(parent=self, align=uiconst.TOTOP, text=title, padding=(self.ICON_SIZE + 2 * self.PADDING,
         self.PADDING,
         self.BUTTON_WIDTH + 2 * self.PADDING,
         0), color=titleColor)
        textLabel = EveLabelMediumBold(parent=self, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, text=text, padding=(self.ICON_SIZE + 2 * self.PADDING,
         0,
         self.BUTTON_WIDTH + 2 * self.PADDING,
         self.PADDING), color=textColor)
        if textTooltipCallback:
            textLabel.state = uiconst.UI_NORMAL
            textLabel.LoadTooltipPanel = textTooltipCallback
        button = Button(parent=self, label=actionText, align=uiconst.CENTERRIGHT, fontsize=self.BUTTON_FONT_SIZE, fixedwidth=self.BUTTON_WIDTH, fixedheight=self.BUTTON_HEIGHT, left=self.PADDING, func=actionCallback)
        if self.actionErrors:
            button.Disable()
            button.LoadTooltipPanel = self.LoadActionErrorTooltip
        self.SetSizeAutomatically()

    def LoadActionErrorTooltip(self, tooltipPanel, parent):
        if not self.actionErrors:
            return
        tooltipPanel.LoadGeneric1ColumnTemplate()
        tooltipPanel.margin = (8, 8, 8, 8)
        tooltipPanel.cellSpacing = (0, 4)
        for error in self.actionErrors:
            label = tooltipPanel.AddLabelMedium(text=error, wrapWidth=300, padding=(8, 4, 8, 4))
            Sprite(bgParent=label.parent, texturePath='res:/UI/Texture/Classes/Industry/Output/hatchPattern.png', tileX=True, tileY=True, color=RED_COLOR, opacity=0.3)


def CreateSectionContainer(parent):
    Line(parent=parent, align=uiconst.TOTOP, color=LINE_COLOR)
    container = ContainerAutoSize(parent=parent, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, bgColor=BACKGROUND_GRAY_COLOR)
    Line(parent=parent, align=uiconst.TOTOP, color=LINE_COLOR)
    SpriteUnderlay(bgParent=container, name='blinkSprite', texturePath='res:/UI/Texture/classes/Neocom/buttonBlink.png', state=uiconst.UI_HIDDEN, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW)
    return container


def OpenHomeStationDialog():
    CloneStationWindow.Open()


def ActivateClone():
    if ConfirmActivateClone():
        if not session.stationid2:
            raise UserError('MustBeDocked')
        sm.GetService('corp').GetCorpStationManager().ActivateClone()


def ConfirmActivateClone():
    messageData = {'station': GetHomeStation()}
    implants = GetDestructibleImplants()
    if len(implants):
        message = 'AskStationSelfDestructImplants'
        implants = [ '<t>- %s<br>' % cfg.FormatConvert(const.UE_TYPEIDANDQUANTITY, implant.typeID, implant.stacksize) for implant in implants ]
        messageData['items'] = ''.join(implants)
    else:
        message = 'AskStationSelfDestruct'
    return eve.Message(message, messageData, uiconst.YESNO) == uiconst.ID_YES


def GetHomeStation():
    return sm.RemoteSvc('charMgr').GetHomeStation()


def GetDestructibleImplants():
    godma = sm.GetService('godma')
    implants = godma.GetItem(session.charid).implants
    destructible = []
    for implant in implants:
        if IsDestructible(implant.typeID):
            destructible.append(implant)

    return destructible


def IsDestructible(typeID):
    godma = sm.GetService('godma')
    return godma.GetTypeAttribute2(typeID, const.attributeNonDestructible) == 0.0


def InstallJumpClone():
    sm.GetService('clonejump').InstallCloneInStation()


def DestroyJumpClone():
    cloneID = GetJumpClone()
    if cloneID:
        sm.GetService('clonejump').DestroyInstalledClone(cloneID)


def GetJumpClone():
    clonejump = sm.GetService('clonejump')
    cloneID, _ = clonejump.GetCloneAtLocation(session.stationid2)
    return cloneID


def GetJumpCloneDetails():
    clonejump = sm.GetService('clonejump')
    cloneID, cloneName = clonejump.GetCloneAtLocation(session.stationid2)
    implants = clonejump.GetImplantsForClone(cloneID)
    clone = Bundle(id=cloneID, name=cloneName, implants=implants)
    return clone


def GetJumpCloneCountAndLimit():
    cloneCount = len(sm.GetService('clonejump').GetClones())
    dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
    cloneLimit = int(dogmaLocation.GetAttributeValue(session.charid, dogma.const.attributeMaxJumpClones))
    return (cloneCount, cloneLimit)


def PrepareStationLink(stationID):
    station = cfg.stations.Get(stationID)
    return '<url=showinfo:%d//%d>%s</url>' % (station.stationTypeID, station.stationID, station.stationName)


def ValidateSelfDestruct():
    errors = []
    if session.stationid2 == GetHomeStation():
        errors.append(localization.GetByLabel('UI/Medical/ErrorAlreadyAtHomeStation'))
    return errors


def ValidateInstallJumpClone():
    return sm.GetService('clonejump').ValidateInstallJumpClone()


def LoadJumpCloneCapacityTooltip(tooltipPanel, parent):
    tooltipPanel.state = uiconst.UI_NORMAL
    tooltipPanel.LoadGeneric2ColumnTemplate()
    tooltipPanel.margin = (8, 8, 8, 8)
    count, limit = GetJumpCloneCountAndLimit()
    text = localization.GetByLabel('UI/Medical/JumpCloneUsageAndCapacity', count=int(count), limit=int(limit))
    tooltipPanel.AddCell(EveLabelMedium(text=text), colSpan=2, cellPadding=(0, 0, 0, 2))
    for typeID in JUMP_CLONE_SKILLS:
        tooltipPanel.AddRow(rowClass=SkillEntry, typeID=typeID, level=0, showLevel=False)


def LoadJumpCloneImplantTooltip(tooltipPanel, parent, implants = None):
    tooltipPanel.state = uiconst.UI_NORMAL
    tooltipPanel.LoadGeneric1ColumnTemplate()
    tooltipPanel.margin = (8, 8, 8, 8)
    for implant in implants:
        tooltipPanel.AddCell(ItemEntry(typeID=implant.typeID), cellPadding=(4, 2, 4, 2))


class ItemEntry(ContainerAutoSize):
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        ContainerAutoSize.ApplyAttributes(self, attributes)
        self.typeID = attributes.typeID
        ItemIcon(parent=self, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, pos=(0, 0, 32, 32), typeID=self.typeID)
        EveLabelMediumBold(parent=self, align=uiconst.CENTERLEFT, text=types.GetName(self.typeID), left=36)

    def GetMenu(self):
        return sm.GetService('menu').GetMenuFormItemIDTypeID(None, self.typeID, ignoreMarketDetails=False)

    def GetHint(self):
        return types.GetDescription(self.typeID)


def HideContainerContent(container):
    for child in container.children:
        animations.FadeOut(child, duration=0.3)

    blue.synchro.SleepWallclock(300)


def RevealContainerContent(container):
    _, height = container.GetAutoSize()
    if height != container.height:
        animations.MorphScalar(container, 'height', startVal=container.height, endVal=height, duration=0.5, curveType=uiconst.ANIM_OVERSHOT)
    for background in container.background:
        if background.name == 'blinkSprite':
            background.Show()
            animations.SpSwoopBlink(background, rotation=math.pi * 0.75, duration=0.5)

    for child in container.children:
        animations.FadeIn(child, endVal=child.opacity or 1.0, duration=0.4)

    blue.synchro.SleepWallclock(500)


@contextmanager
def FlushAndLockAutoSize(container):
    container.DisableAutoSize()
    container.Flush()
    try:
        yield
    finally:
        container.EnableAutoSize()
