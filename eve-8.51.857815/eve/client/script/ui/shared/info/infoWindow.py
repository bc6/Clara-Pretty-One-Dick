#Embedded file name: eve/client/script/ui/shared/info\infoWindow.py
import sys
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.shared.industry.views.containersMETE import ContainerTE, ContainerME
from eve.client.script.ui.shared.info.panels.panelUsedWith import PanelUsedWith
from eve.client.script.ui.shared.stateFlag import FlagIconWithState
import uiprimitives
import types
import state
from eve.client.script.ui.control.eveScroll import Scroll
from inventorycommon.const import groupCapsule
import uicls
import maputils
import carbonui.const as uiconst
import uicontrols
import uthread
import uiutil
import blue
import log
import util
import uix
import localization
from eve.client.script.ui.control.eveWindow import Window
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbon.common.script.sys.service import ROLE_GML
import listentry
from eve.client.script.ui.inflight.shipModuleButton.attributeValueRowContainer import AttributeValueRowContainer
from .infoConst import *
from .panels.panelCertificateSkills import PanelCertificateSkills
from .panels.panelMastery import PanelMastery
from .panels.panelRequiredFor import PanelRequiredFor
from .panels.panelNotes import PanelNotes
from .panels.panelIndustry import PanelIndustry
from .panels.panelItemIndustry import PanelItemIndustry
from eve.client.script.ui.shared.info.panels.panelTraits import PanelTraits
from eve.client.script.ui.control.historyBuffer import HistoryBuffer
from eve.client.script.ui.shared.info.panels.panelRequirements import PanelRequirements
from eve.client.script.ui.shared.info.panels.panelFitting import PanelFitting
from eve.client.script.ui.shared.monetization.trialPopup import ORIGIN_SHOWINFO
MINWIDTH = 325
MINHEIGHTREGULAR = 280
MINHEIGHTMEDAL = 480

class InfoWindow(Window):
    __guid__ = 'form.infowindow'
    __notifyevents__ = ['OnBountyPlaced']
    default_width = 256
    default_height = 340
    default_left = 56
    default_top = '__center__'
    default_name = 'infoWindow'
    default_iconNum = 'res:/ui/Texture/WindowIcons/info.png'
    default_scope = 'station_inflight'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        typeID = attributes.get('typeID', None)
        itemID = attributes.get('itemID', None)
        rec = attributes.get('rec', None)
        parentID = attributes.get('parentID', None)
        abstractinfo = attributes.get('abstractinfo', None)
        selectTabType = attributes.get('selectTabType', None)
        self.SetWndIcon(self.default_iconNum, hidden=True)
        self.typeID = None
        self.itemID = None
        self.isLoading = False
        self.pendingLoadData = None
        self.isBrowsing = False
        self.maintabs = None
        self.toparea = Container(name='toparea', parent=self.sr.topParent, align=uiconst.TOALL, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding), clipChildren=0, state=uiconst.UI_PICKCHILDREN)
        self.mainiconparent = Container(name='mainiconparent', parent=self.toparea, align=uiconst.TOLEFT, state=uiconst.UI_NORMAL, padRight=6)
        self.techicon = Sprite(name='techIcon', parent=self.mainiconparent, align=uiconst.RELATIVE, left=0, width=16, height=16, idx=0)
        self.mainicon = Container(name='mainicon', parent=self.mainiconparent, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
        self.topRightContent = ContainerAutoSize(name='topRightContent', align=uiconst.TOTOP, parent=self.toparea, callback=self.OnTopRightContResized)
        self.captioncontainer = ContainerAutoSize(name='captioncontainer', parent=self.topRightContent, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
        self.subinfolinkcontainer = Container(name='subinfolinkcontainer', parent=self.topRightContent, align=uiconst.TOTOP, padTop=6)
        self.therestcontainer = ContainerAutoSize(name='therestcontainer', parent=self.topRightContent, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, padTop=6)
        self.history = self.history = HistoryBuffer()
        self.goForwardBtn = uicontrols.ButtonIcon(name='goForwardBtn', parent=self.toparea, align=uiconst.TOPRIGHT, pos=(-2, -5, 16, 16), iconSize=16, texturePath='res:/UI/Texture/icons/38_16_224.png', func=self.OnForward, hint=localization.GetByLabel('UI/Control/EveWindow/Next'))
        self.goBackBtn = uicontrols.ButtonIcon(name='goBackBtn', parent=self.toparea, align=uiconst.TOPRIGHT, pos=(12, -5, 16, 16), iconSize=16, texturePath='res:/UI/Texture/icons/38_16_223.png', func=self.OnBack, hint=localization.GetByLabel('UI/Control/EveWindow/Previous'))
        self.mainContentCont = Container(name='mainContentCont', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        uthread.new(self.ReconstructInfoWindow, typeID, itemID, rec=rec, parentID=parentID, abstractinfo=abstractinfo, selectTabType=selectTabType)

    def ReconstructSubContainer(self):
        self.mainContentCont.Flush()
        self.scroll = Scroll(name='scroll', parent=self.mainContentCont, state=uiconst.UI_HIDDEN, padding=const.defaultPadding)
        self.scroll.ignoreTabTrimming = True
        self.descedit = uicls.EditPlainText(name='descedit', parent=self.mainContentCont, state=uiconst.UI_HIDDEN, padding=const.defaultPadding, readonly=1, linkStyle=uiconst.LINKSTYLE_SUBTLE)

    def GetMainIconDragData(self, *args):
        if not self.typeID:
            return []
        if self.IsType(TYPE_MEDAL):
            return []
        fakeNode = uiutil.Bunch()
        fakeNode.typeID = self.typeID
        if self.IsType(TYPE_CHARACTER, TYPE_CORPORATION, TYPE_ALLIANCE, TYPE_FACTION):
            fakeNode.__guid__ = 'listentry.User'
            fakeNode.itemID = self.itemID
            fakeNode.IsCharacter = self.IsType(TYPE_CHARACTER)
            fakeNode.IsCorporation = self.IsType(TYPE_CORPORATION)
            fakeNode.IsFaction = self.IsType(TYPE_FACTION)
            fakeNode.IsAlliance = self.IsType(TYPE_ALLIANCE)
            if not (fakeNode.IsCharacter or fakeNode.IsCorporation or fakeNode.IsFaction or fakeNode.IsAlliance):
                return []
            fakeNode.charID = self.itemID
            fakeNode.info = uiutil.Bunch(typeID=self.typeID, name=cfg.eveowners.Get(self.itemID).name)
            return [fakeNode]
        if self.IsType(TYPE_CELESTIAL, TYPE_STATION) and self.itemID:
            fakeNode.__guid__ = 'xtriui.ListSurroundingsBtn'
            fakeNode.itemID = self.itemID
            fakeNode.label = self.captionText or localization.GetByLabel('UI/Common/Unknown')
            return [fakeNode]
        if self.IsType(TYPE_CERTIFICATE):
            fakeNode.__guid__ = 'listentry.CertEntry'
            fakeNode.typeID = self.typeID
            fakeNode.certID = self.abstractinfo.certificateID
            fakeNode.level = self.abstractinfo.level
            className, grade, _ = sm.GetService('certificates').GetCertificateLabel(self.abstractinfo.certificateID)
            label = localization.GetByLabel('UI/InfoWindow/CertificateNameWithGrade', certificateName=className, certificateGrade=grade)
            fakeNode.label = label
            return [fakeNode]
        invtype = cfg.invtypes.Get(self.typeID)
        if invtype.published:
            fakeNode.__guid__ = 'listentry.GenericMarketItem'
        else:
            fakeNode.__guid__ = 'uicls.GenericDraggableForTypeID'
        label = invtype.name
        fakeNode.label = label or 'Unknown'
        return [fakeNode]

    def ShowError(self, args):
        self.sr.topParent.Hide()
        errorPar = Container(parent=self.sr.main, name='errorPar', align=uiconst.TOALL, left=12, top=6, width=12, height=6, state=uiconst.UI_DISABLED)
        msg = cfg.GetMessage(*args)
        title = uicontrols.CaptionLabel(text=msg.title, parent=errorPar, align=uiconst.TOTOP)
        title.name = 'errorTitle'
        Container(parent=errorPar, name='separator', align=uiconst.TOTOP, height=6)
        uicontrols.EveLabelMedium(text=msg.text, name='errorDetails', parent=errorPar, align=uiconst.TOTOP)

    def HideError(self):
        if not self.IsCollapsed():
            self.sr.topParent.state = uiconst.UI_PICKCHILDREN
        errorPar = uiutil.FindChild(self.sr.main, 'errorPar')
        if errorPar is not None:
            errorPar.Close()

    def OnTopRightContResized(self, *args):
        height = self.topRightContent.height
        self.sr.topParent.height = max(height, self.mainiconparent.width, self.mainiconparent.height)
        self.sr.topParent.height += 2 * const.defaultPadding

    def UpdateWindowMinSize(self, width):
        height = MINHEIGHTREGULAR
        if self.IsType(TYPE_MEDAL):
            height = MINHEIGHTMEDAL
        self.SetMinSize([width, height])

    def ConstructSubtabs(self, tabgroup, subtabs, tabname):
        subtabgroup = []
        sublisttype = None
        for sublisttype, _, _ in subtabs:
            subitems = self.data[sublisttype]['items']
            subtabname = self.data[sublisttype]['name']
            if len(subitems):
                subtabgroup.append([subtabname,
                 self.scroll,
                 self,
                 (sublisttype, None)])

        if subtabgroup:
            _subtabs = uicontrols.TabGroup(name='%s_subtabs' % tabname.lower(), parent=self.mainContentCont, idx=0, tabs=subtabgroup, groupID='infowindow_%s' % sublisttype, autoselecttab=0)
            tabgroup.append([tabname,
             self.scroll,
             self,
             ('selectSubtab', None, _subtabs),
             _subtabs])

    def ConstructCustomTab(self, tabgroup, tabType, tabName):
        name = localization.GetByLabel(tabName)
        panel = self.GetPanelByTabType(tabType)
        if panel:
            tabgroup.append([name,
             panel,
             self,
             (tabType, panel.Load)])
        else:
            func = self.GetDynamicTabLoadMethod(tabType)
            if func:
                tabgroup.append([name,
                 self.scroll,
                 self,
                 (tabType, func)])

    def GetPanelByTabType(self, tabType):
        if tabType == TAB_NOTES:
            return PanelNotes(parent=self.mainContentCont, itemID=self.itemID)
        if tabType == TAB_MASTERY:
            return PanelMastery(parent=self.mainContentCont, typeID=self.typeID)
        if tabType == TAB_CERTSKILLS:
            return PanelCertificateSkills(parent=self.mainContentCont, typeID=self.typeID, certificateID=self.abstractinfo.certificateID)
        if tabType == TAB_REQUIREDFOR:
            return PanelRequiredFor(parent=self.mainContentCont, typeID=self.typeID)
        if tabType == TAB_INDUSTRY:
            return PanelIndustry(parent=self.mainContentCont, bpData=self.GetBlueprintData())
        if tabType == TAB_ITEMINDUSTRY:
            return PanelItemIndustry(parent=self.mainContentCont, typeID=self.typeID)
        if tabType == TAB_TRAITS:
            if PanelTraits.TraitsVisible(self.typeID):
                return PanelTraits(parent=self.mainContentCont, typeID=self.typeID)
        elif tabType == TAB_REQUIREMENTS:
            if PanelRequirements.RequirementsVisible(self.typeID):
                return PanelRequirements(parent=self.mainContentCont, typeID=self.typeID)
        else:
            if tabType == TAB_FITTING:
                return PanelFitting(parent=self.mainContentCont, item=self.rec, itemID=self.itemID, typeID=self.typeID)
            if tabType == TAB_USEDWITH:
                return PanelUsedWith(parent=self.mainContentCont, typeID=self.typeID)

    def ConstructMainTabs(self, widthRequirements, tabNumber, selectTabType = None):
        """ Load tabs and their content from self.data, using self.scroll """
        tabgroup = []
        for listtype, subtabs, tabName in INFO_TABS:
            items = self.data[listtype]['items']
            tabname = self.data[listtype]['name']
            text = self.data[listtype].get('text', None)
            if text:
                tabgroup.append([tabname,
                 self.descedit,
                 self,
                 ('readOnlyText', None, text)])
            elif len(items):
                tabgroup.append([tabname,
                 self.scroll,
                 self,
                 (listtype, None)])
            elif listtype in self.dynamicTabs:
                self.ConstructCustomTab(tabgroup, listtype, tabName)
            if subtabs:
                self.ConstructSubtabs(tabgroup, subtabs, tabname)
            if selectTabType is not None and listtype == selectTabType:
                tabNumber = len(tabgroup) - 1

        if len(tabgroup):
            autoSelectTab = tabNumber is None and selectTabType is None
            self.maintabs = uicontrols.TabGroup(name='maintabs', parent=self.mainContentCont, idx=0, tabs=tabgroup, groupID='infowindow_%s' % self.infoType, autoselecttab=autoSelectTab)
            if not autoSelectTab:
                self.maintabs.SelectByIdx(tabNumber)
            widthRequirements.append(self.maintabs.totalTabWidth + 16)

    def UpdateHistoryButtons(self):
        if self.history.IsBackEnabled():
            self.goBackBtn.Enable()
        else:
            self.goBackBtn.Disable()
        if self.history.IsForwardEnabled():
            self.goForwardBtn.Enable()
        else:
            self.goForwardBtn.Disable()

    def OnBack(self):
        self.UpdateHistoryData()
        infoWndID = self.history.GoBack()
        if infoWndID:
            if uicore.uilib.mouseOver != self.goBackBtn:
                self.goBackBtn.Blink()
            self.ReconstructInfoWindow(branchHistory=False, *infoWndID)

    def OnForward(self):
        self.UpdateHistoryData()
        infoWndData = self.history.GoForward()
        if infoWndData:
            if uicore.uilib.mouseOver != self.goForwardBtn:
                self.goForwardBtn.Blink()
            self.ReconstructInfoWindow(branchHistory=False, *infoWndData)

    def ConstructBottomButtons(self, widthRequirements):
        """ Construct bottom button strip that appears beneath all tabs """
        if self.data['buttons'] and session.charid:
            btns = uicontrols.ButtonGroup(btns=self.data['buttons'], parent=self.mainContentCont, idx=0, unisize=0, line=False)
            totalBtnWidth = 0
            for btn in btns.children[0].children:
                totalBtnWidth += btn.width

            widthRequirements.append(totalBtnWidth)

    def ReconstructInfoWindow(self, typeID, itemID = None, rec = None, parentID = None, abstractinfo = None, tabNumber = None, branchHistory = True, selectTabType = None):
        if self.isLoading:
            self.pendingLoadData = (typeID,
             itemID,
             rec,
             parentID,
             abstractinfo,
             tabNumber,
             branchHistory,
             selectTabType)
            return
        self._ReconstructInfoWindow(typeID, itemID, rec, parentID, abstractinfo, tabNumber, branchHistory, selectTabType)
        if self.pendingLoadData:
            pendingData = self.pendingLoadData
            self.pendingLoadData = None
            self.ReconstructInfoWindow(*pendingData)

    def _ReconstructInfoWindow(self, typeID, itemID = None, rec = None, parentID = None, abstractinfo = None, tabNumber = None, branchHistory = True, selectTabType = None):
        """ 
        Takes care of updating window data, reconstructing header and main content as well 
        as updating some window states such as minimum width
        """
        try:
            self.ShowLoad()
            self.isLoading = True
            self.HideError()
            if self.top == uicore.desktop.height:
                self.Maximize()
            else:
                self.SetState(uiconst.UI_NORMAL)
            if branchHistory and not self.history.IsEmpty():
                self.UpdateHistoryData()
            self.typeID = typeID
            self.itemID = itemID
            self.rec = rec
            self.parentID = parentID
            self.abstractinfo = abstractinfo
            typeObj = cfg.invtypes.Get(typeID)
            self.groupID = typeObj.groupID
            self.categoryID = typeObj.categoryID
            self.infoType = self.GetInfoWindowType()
            self.corpinfo = None
            self.allianceinfo = None
            self.factioninfo = None
            self.warfactioninfo = None
            self.stationinfo = None
            self.plasticinfo = None
            self.corpID = None
            self.allianceID = None
            self.captionText = None
            self.subCaptionText = None
            self.ResetWindowData()
            self.variationCompareBtn = None
            self.maintabs = None
            self.captioncontainer.Flush()
            self.subinfolinkcontainer.Flush()
            self.therestcontainer.Flush()
            self.subinfolinkcontainer.height = 0
            self.subinfolinkcontainer.padTop = 6
            self.mainiconparent.GetDragData = self.GetMainIconDragData
            self.mainiconparent.isDragObject = True
            self.ReconstructSubContainer()
            self.UpdateCaption()
            self.UpdateHeaderActionMenu()
            self.UpdateWindowIcon(typeID, itemID)
            self.UpdateDescriptionCaptionAndSubCaption()
            self.ConstructWindowHeader()
            sm.GetService('info').UpdateWindowData(self, typeID, itemID, parentID=parentID)
            self.CheckConstructOwnerButtonIcon(itemID)
            if branchHistory:
                self.history.Append(self.GetHistoryData())
            self.UpdateHistoryButtons()
            widthRequirements = [MINWIDTH]
            self.ConstructMainTabs(widthRequirements, tabNumber, selectTabType)
            self.ConstructBottomButtons(widthRequirements)
            width = max(widthRequirements)
            self.UpdateWindowMinSize(width)
            self.toparea.state = uiconst.UI_PICKCHILDREN
        except BadArgs as e:
            self.ShowError(e.args)
            sys.exc_clear()
        finally:
            self.HideLoad()
            self.ShowHeaderButtons(1)
            self.isLoading = False

        uicore.registry.SetFocus(self)

    def UpdateHistoryData(self):
        self.history.UpdateCurrent(self.GetHistoryData())

    def GetHistoryData(self):
        return (self.typeID,
         self.itemID,
         self.rec,
         self.parentID,
         self.abstractinfo,
         self.GetSelectedTabIdx())

    def GetSelectedTabIdx(self):
        if self.maintabs:
            return self.maintabs.GetSelectedIdx()
        else:
            return 0

    def GetOwnerIDToShow(self, itemID):
        """ Returns an owner id for the item being viewed, and None if there isn't any """
        if self.IsOwned():
            if session.solarsystemid is not None:
                slimitem = sm.GetService('michelle').GetBallpark().GetInvItem(itemID)
                if slimitem is not None:
                    return slimitem.ownerID

    def CheckConstructOwnerButtonIcon(self, itemID):
        """ Add owner button for stations, containers, sentries and such if necessary """
        ownerID = self.GetOwnerIDToShow(itemID)
        if ownerID:
            ownerOb = cfg.eveowners.Get(ownerID)
            if ownerOb.groupID == const.groupCharacter:
                btn = Icon(parent=self.subinfolinkcontainer, pos=(0, 0, 42, 42), iconMargin=2, hint=localization.GetByLabel('UI/InfoWindow/ClickForPilotInfo'))
                btn.OnClick = (self.ReconstructInfoWindow, ownerOb.typeID, ownerID)
                btn.LoadIconByTypeID(ownerOb.typeID, itemID=ownerID, ignoreSize=True)
                self.subinfolinkcontainer.height = 42
            elif ownerOb.groupID == const.groupCorporation:
                self.GetCorpLogo(ownerID, parent=self.subinfolinkcontainer)
                self.subinfolinkcontainer.height = 64

    def ConstructHeaderCaptionAndSubCaption(self):
        if self.captionText:
            uicontrols.EveLabelMedium(name='caption', text=self.captionText, parent=self.captioncontainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
            self.captioncontainer.height = 30
            if self.subCaptionText:
                alpha = 0
                if self.IsType(TYPE_SKILL):
                    labelType = uicontrols.EveLabelSmall
                    alpha = 0.6
                else:
                    labelType = uicontrols.EveLabelMedium
                lbl = labelType(name='subCaption', text=self.subCaptionText, parent=self.captioncontainer, align=uiconst.TOTOP, tabs=[84], state=uiconst.UI_DISABLED)
                if alpha != 0:
                    lbl.SetAlpha(alpha)

    def ConstructWindowHeader(self):
        """
            Construct all header UI that should live under self.captioncontainer, self.subinfolinkcontainer or self.therestcontainer
        """
        self.ConstructHeaderCaptionAndSubCaption()
        if self.IsType(TYPE_CHARACTER) and self.itemID:
            self.ConstructHeaderCharacter()
        elif self.IsType(TYPE_SHIP) or self.typeID and sm.GetService('godma').GetType(self.typeID).agentID:
            self.ConstructHeaderShip()
        elif self.IsType(TYPE_MEDAL, TYPE_RIBBON) and self.abstractinfo is not None:
            self.ConstructHeaderMedalOrRibbon()
        elif self.IsType(TYPE_CORPORATION):
            self.ConstructHeaderCorporation()
        elif self.IsType(TYPE_ALLIANCE):
            self.ConstructHeaderAlliance()
        elif self.IsType(TYPE_FACTION):
            self.ConstructHeaderFaction()
        elif self.IsType(TYPE_SKILL) and session.charid:
            self.ConstructHeaderSkill()
        elif self.IsType(TYPE_BLUEPRINT):
            self.ConstructHeaderBlueprint()

    def ConstructHeaderCharacter(self):
        corpid = None
        corpAge = None
        allianceid = None
        charinfo = None
        corpCharInfo = None
        security = None
        if not util.IsNPC(self.itemID):
            if util.IsDustCharacter(self.itemID):
                corpCharInfo = sm.GetService('corp').GetInfoWindowDataForChar(self.itemID, 1)
            else:
                parallelCalls = []
                parallelCalls.append((sm.RemoteSvc('charMgr').GetPublicInfo3, (self.itemID,)))
                parallelCalls.append((sm.GetService('corp').GetInfoWindowDataForChar, (self.itemID, 1)))
                parallelCalls.append((sm.GetService('crimewatchSvc').GetCharacterSecurityStatus, (self.itemID,)))
                charinfo, corpCharInfo, security = uthread.parallel(parallelCalls)
        if charinfo is not None:
            charinfo = charinfo[0]
            self.data[TAB_BIO]['text'] = charinfo.description
            corpAge = blue.os.GetWallclockTime() - charinfo.startDateTime
            if getattr(charinfo, 'medal1GraphicID', None):
                uicontrols.Icon(icon='res:/ui/Texture/WindowIcons/corporationdecorations.png', parent=self.mainicon, left=70, top=80, size=64, align=uiconst.RELATIVE, idx=0)
        if corpCharInfo:
            corpid = corpCharInfo.corpID
            allianceid = corpCharInfo.allianceID
            self.corpID = corpid
            self.allianceID = allianceid
            title = ''
            titleList = []
            if corpCharInfo.title:
                title = corpCharInfo.title
                titleList.append(title)
            for ix in xrange(1, 17):
                titleText = getattr(corpCharInfo, 'title%s' % ix, None)
                if titleText:
                    titleList.append(titleText)

            if len(titleList) > 0:
                title = localization.formatters.FormatGenericList(titleList)
                text = uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/InfoWindow/CorpTitle', title=title), parent=self.captioncontainer, align=uiconst.TOTOP)
                if text.height > 405:
                    text.height = 405
        uiprimitives.Line(parent=self.captioncontainer, align=uiconst.TOTOP, padTop=4)
        if not util.IsNPC(self.itemID) and not util.IsDustCharacter(self.itemID):
            uiprimitives.Line(parent=self.therestcontainer, align=uiconst.TOTOP)
            secText = localization.GetByLabel('UI/InfoWindow/SecurityStatusOfCharacter', secStatus=security)
            uicontrols.EveLabelSmall(text=secText, parent=self.therestcontainer, align=uiconst.TOTOP, padTop=4)
            standing = sm.GetService('standing').GetStanding(eve.session.corpid, self.itemID)
            if standing is not None:
                standingText = localization.GetByLabel('UI/InfoWindow/CorpStandingOfCharacter', corpStanding=standing)
                uicontrols.EveLabelSmall(text=standingText, parent=self.therestcontainer, align=uiconst.TOTOP)
            wanted = False
            bountyOwnerIDs = (self.itemID, corpid, allianceid)
            bountyAmount = self.GetBountyAmount(*bountyOwnerIDs)
            if bountyAmount > 0:
                wanted = True
            bountyAmounts = self.GetBountyAmounts(*bountyOwnerIDs)
            charBounty = 0
            corpBounty = 0
            allianceBounty = 0
            if len(bountyAmounts):
                for ownerID, value in bountyAmounts.iteritems():
                    if util.IsCharacter(ownerID):
                        charBounty = value
                    elif util.IsCorporation(ownerID):
                        corpBounty = value
                    elif util.IsAlliance(ownerID):
                        allianceBounty = value

            bountyHint = localization.GetByLabel('UI/Station/BountyOffice/BountyHint', charBounty=util.FmtISK(charBounty, 0), corpBounty=util.FmtISK(corpBounty, 0), allianceBounty=util.FmtISK(allianceBounty, 0))
            self.Wanted(bountyAmount, True, wanted, ownerIDs=bountyOwnerIDs, hint=bountyHint)
        if util.IsNPC(self.itemID) and not util.IsDustCharacter(self.itemID):
            agentInfo = sm.GetService('agents').GetAgentByID(self.itemID)
            if agentInfo:
                corpid = agentInfo.corporationID
            else:
                corpid = sm.RemoteSvc('corpmgr').GetCorporationIDForCharacter(self.itemID)
        if corpid:
            corpLogo = self.GetCorpLogo(corpid, parent=self.subinfolinkcontainer)
            corpLogo.padRight = 4
            self.subinfolinkcontainer.height = 64
            if not util.IsNPC(self.itemID) and corpid:
                tickerName = cfg.corptickernames.Get(corpid).tickerName
                uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/InfoWindow/MemberOfCorp', corpName=cfg.eveowners.Get(corpid).name, tickerName=tickerName), parent=self.subinfolinkcontainer, align=uiconst.TOTOP, top=0, left=0)
                if corpAge is not None:
                    uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/InfoWindow/MemberFor', timePeriod=util.FmtTimeInterval(corpAge, 'day')), parent=self.subinfolinkcontainer, align=uiconst.TOBOTTOM, left=4)
                uthread.new(self.ShowRelationshipIcon, self.itemID, corpid, allianceid)
            if charinfo is not None:
                militiaFactionID = charinfo.militiaFactionID
                if not util.IsNPC(self.itemID) and (allianceid or militiaFactionID):
                    subinfoCont = Container(name='subinfo', parent=self.therestcontainer, align=uiconst.TOTOP, height=16, idx=0)
                    uiprimitives.Line(parent=subinfoCont, align=uiconst.TOTOP, padBottom=1)
                    text = ''
                    if allianceid:
                        text = cfg.eveowners.Get(allianceid).name
                        if militiaFactionID:
                            text += ' | '
                    subinfoText = uicontrols.EveLabelSmall(text=text, parent=subinfoCont, align=uiconst.TOLEFT, top=4)
                    subinfoCont.height = subinfoText.textheight + 2 * subinfoText.top
                    if militiaFactionID:
                        fwiconCont = Container(name='subinfo', parent=subinfoCont, align=uiconst.TOLEFT, width=20)
                        fwicon = Sprite(name='fwIcon', parent=fwiconCont, align=uiconst.TOPLEFT, texturePath='res:/UI/Texture/Icons/FW_Icon_Small.png', pos=(-2, 0, 20, 20))
                        fwicon.OnClick = sm.GetService('cmd').OpenMilitia
                        factionText = localization.GetByLabel('UI/FactionWarfare/MilitiaAndFaction', factionName=cfg.eveowners.Get(militiaFactionID).name)
                        factionLabel = uicontrols.EveLabelSmall(text=factionText, parent=subinfoCont, align=uiconst.TOLEFT, top=4)
                        subinfoCont.height = max(subinfoText.textheight + 2 * subinfoText.top, factionLabel.textheight + 2 * subinfoText.top)

    def ConstructHeaderShip(self):
        self.subinfolinkcontainer.height = 42
        shipOwnerID = None
        if self.itemID:
            if self.itemID == session.shipid:
                shipOwnerID = session.charid
            elif session.stationid and util.GetActiveShip() == self.itemID:
                shipOwnerID = session.charid
            elif self.typeID and sm.GetService('godma').GetType(self.typeID).agentID:
                shipOwnerID = sm.GetService('godma').GetType(self.typeID).agentID
            elif eve.session.solarsystemid is not None:
                shipOwnerID = sm.GetService('michelle').GetCharIDFromShipID(self.itemID)
            if shipOwnerID:
                btn = Icon(parent=self.subinfolinkcontainer, width=42, height=42, hint=localization.GetByLabel('UI/InfoWindow/ClickForPilotInfo'), align=uiconst.CENTERLEFT)
                btn.OnClick = (self.ReconstructInfoWindow, cfg.eveowners.Get(shipOwnerID).typeID, shipOwnerID)
                btn.LoadIconByTypeID(cfg.eveowners.Get(shipOwnerID).typeID, itemID=shipOwnerID, ignoreSize=True)
        left = 54 if shipOwnerID else 0
        if self.groupID == groupCapsule:
            return
        skills = sm.GetService('skills').GetRequiredSkills(self.typeID).items()
        texturePath, hint = sm.GetService('skills').GetRequiredSkillsLevelTexturePathAndHint(skills, typeID=self.typeID)
        skillSprite = Sprite(name='skillSprite', parent=self.subinfolinkcontainer, align=uiconst.CENTERLEFT, pos=(left,
         0,
         33,
         33), texturePath=texturePath, hint=hint)
        isTrialRestricted = sm.GetService('skills').IsTrialRestricted(self.typeID)
        if isTrialRestricted:
            skillSprite.OnClick = lambda *args: uicore.cmd.OpenSubscriptionPage(origin=ORIGIN_SHOWINFO, reason=':'.join(['ship', str(self.typeID)]))
        else:
            skillSprite.OnClick = lambda *args: self.maintabs.ShowPanelByName(localization.GetByLabel('UI/InfoWindow/TabNames/Requirements'))
        masterySprite = Sprite(name='masterySprite', parent=self.subinfolinkcontainer, align=uiconst.CENTERLEFT, pos=(left + 36,
         0,
         45,
         45))
        masterySprite.OnClick = lambda *args: self.maintabs.ShowPanelByName(localization.GetByLabel('UI/InfoWindow/TabNames/Mastery'))
        shipMasteryLevel = sm.GetService('certificates').GetCurrCharMasteryLevel(self.typeID)
        texturePath = sm.GetService('certificates').GetMasteryIconForLevel(shipMasteryLevel)
        if shipMasteryLevel == 0:
            hint = localization.GetByLabel('UI/InfoWindow/MasteryNone')
        else:
            hint = localization.GetByLabel('UI/InfoWindow/MasteryLevel', masteryLevel=shipMasteryLevel)
        masterySprite.SetTexturePath(texturePath)
        masterySprite.hint = hint
        if self.itemID:
            insuranceCont = Container(parent=self.therestcontainer, align=uiconst.TOTOP, height=32)
            insuranceLabel = uicontrols.EveLabelMedium(text='', parent=insuranceCont, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
            timeLabel = uicontrols.EveLabelMedium(text='', parent=insuranceCont, align=uiconst.TOTOP)
            bp = sm.GetService('michelle').GetBallpark()
            isMine = False
            if bp is not None:
                slimItem = bp.GetInvItem(self.itemID)
                if slimItem is not None:
                    if slimItem.ownerID in (session.corpid, session.charid):
                        isMine = True
                elif not session.solarsystemid:
                    isMine = True
            if isMine or bp is None:
                contract = sm.RemoteSvc('insuranceSvc').GetContractForShip(self.itemID)
                price = sm.GetService('insurance').GetInsurancePrice(self.typeID)
                if self.groupID in (const.groupTitan, const.groupSupercarrier) or price <= 0:
                    insuranceLabel.text = ''
                elif contract and contract.ownerID in (session.corpid, session.charid):
                    insuranceName = sm.GetService('info').GetInsuranceName(contract.fraction)
                    insuranceLabel.text = insuranceName
                    payout = price * contract.fraction
                    insuranceLabel.hint = util.FmtISK(payout)
                    timeDiff = contract.endDate - blue.os.GetWallclockTime()
                    days = timeDiff / const.DAY
                    text = localization.GetByLabel('UI/Insurance/TimeLeft', time=timeDiff)
                    if days < 5:
                        timeLabel.color = util.Color.RED
                    timeLabel.text = text
                else:
                    insuranceLabel.text = localization.GetByLabel('UI/Insurance/ShipUninsured')
                    insuranceLabel.color = util.Color.RED

    def ConstructHeaderMedalOrRibbon(self):
        info = sm.GetService('medals').GetMedalDetails(self.itemID).info[0]
        corpid = info.ownerID
        if corpid:
            corpLogo = self.GetCorpLogo(corpid, parent=self.subinfolinkcontainer)
            corpLogo.padRight = 4
            self.subinfolinkcontainer.height = 64
            if corpid and not util.IsNPC(corpid):
                tickerName = cfg.corptickernames.Get(corpid).tickerName
                uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/InfoWindow/MedalIssuedBy', corpName=cfg.eveowners.Get(corpid).name, tickerName=tickerName), parent=self.subinfolinkcontainer, align=uiconst.TOTOP, top=0, left=0)
            uiprimitives.Line(parent=self.captioncontainer, align=uiconst.TOTOP)
        uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/InfoWindow/NumberOfTimesAwarded', numTimes=info.numberOfRecipients), parent=self.therestcontainer, align=uiconst.TOTOP)

    def ConstructHeaderCorporation(self):
        parallelCalls = []
        if self.corpinfo is None:
            parallelCalls.append((sm.RemoteSvc('corpmgr').GetPublicInfo, (self.itemID,)))
        else:
            parallelCalls.append((lambda : None, ()))
        parallelCalls.append((sm.GetService('faction').GetFaction, (self.itemID,)))
        if self.warfactioninfo is None:
            parallelCalls.append((sm.GetService('facwar').GetCorporationWarFactionID, (self.itemID,)))
        else:
            parallelCalls.append((lambda : None, ()))
        corpinfo, factionID, warFaction = uthread.parallel(parallelCalls)
        self.corpinfo = self.corpinfo or corpinfo
        allianceid = self.corpinfo.allianceID
        uthread.new(self.ShowRelationshipIcon, None, self.itemID, allianceid)
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/InfoWindow/HeadquartersLocation', location=self.corpinfo.stationID), parent=self.captioncontainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)
        uiprimitives.Line(parent=self.captioncontainer, align=uiconst.TOTOP, padTop=4)
        memberDisp = None
        if factionID or warFaction:
            faction = cfg.eveowners.Get(factionID) if factionID else cfg.eveowners.Get(warFaction)
            uiutil.GetLogoIcon(itemID=faction.ownerID, parent=self.subinfolinkcontainer, align=uiconst.TOLEFT, state=uiconst.UI_NORMAL, hint=localization.GetByLabel('UI/InfoWindow/ClickForFactionInfo'), OnClick=(self.ReconstructInfoWindow, faction.typeID, faction.ownerID), size=64, ignoreSize=True)
            self.subinfolinkcontainer.height = 64
            memberDisp = cfg.eveowners.Get(faction.ownerID).name
        if allianceid:
            alliance = cfg.eveowners.Get(allianceid)
            uiutil.GetLogoIcon(itemID=allianceid, align=uiconst.TOLEFT, parent=self.subinfolinkcontainer, OnClick=(self.ReconstructInfoWindow, alliance.typeID, allianceid), hint=localization.GetByLabel('UI/InfoWindow/ClickForAllianceInfo'), state=uiconst.UI_NORMAL, size=64, ignoreSize=True)
            self.subinfolinkcontainer.height = 64
            memberDisp = cfg.eveowners.Get(allianceid).name
        if memberDisp is not None:
            uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/InfoWindow/MemberOfAlliance', allianceName=memberDisp), parent=self.subinfolinkcontainer, align=uiconst.TOTOP, top=4, padLeft=4)
        if warFaction is not None:
            facWarInfoCont = Container(name='facwarinfo', parent=self.subinfolinkcontainer, align=uiconst.TOTOP, height=28)
            fwicon = Sprite(name='fwIcon', parent=facWarInfoCont, align=uiconst.CENTERLEFT, texturePath='res:/UI/Texture/Icons/FW_Icon_Large.png', pos=(2, 0, 32, 32), hint=localization.GetByLabel('UI/Commands/OpenFactionalWarfare'))
            fwicon.OnClick = sm.GetService('cmd').OpenMilitia
            uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/FactionWarfare/MilitiaAndFaction', factionName=cfg.eveowners.Get(warFaction).name), parent=facWarInfoCont, align=uiconst.CENTERLEFT, left=38)
        if not util.IsNPC(self.itemID):
            wanted = False
            if not self.corpinfo.deleted:
                bountyOwnerIDs = (self.itemID, allianceid)
                bountyAmount = self.GetBountyAmount(*bountyOwnerIDs)
                if bountyAmount > 0:
                    wanted = True
                bountyAmounts = self.GetBountyAmounts(*bountyOwnerIDs)
                corpBounty = 0
                allianceBounty = 0
                if len(bountyAmounts):
                    for ownerID, value in bountyAmounts.iteritems():
                        if util.IsCorporation(ownerID):
                            corpBounty = value
                        elif util.IsAlliance(ownerID):
                            allianceBounty = value

                bountyHint = localization.GetByLabel('UI/Station/BountyOffice/BountyHintCorp', corpBounty=util.FmtISK(corpBounty, 0), allianceBounty=util.FmtISK(allianceBounty, 0))
                self.Wanted(bountyAmount, False, wanted, ownerIDs=bountyOwnerIDs, hint=bountyHint)

    def ConstructHeaderAlliance(self):
        warFactionID = sm.GetService('facwar').GetAllianceWarFactionID(self.itemID)
        if warFactionID is not None:
            fwicon = Sprite(name='fwIcon', parent=self.subinfolinkcontainer, align=uiconst.CENTERLEFT, texturePath='res:/UI/Texture/Icons/FW_Icon_Large.png', pos=(2, 0, 32, 32), hint=localization.GetByLabel('UI/Commands/OpenFactionalWarfare'))
            fwicon.OnClick = sm.GetService('cmd').OpenMilitia
            uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/FactionWarfare/MilitiaAndFaction', factionName=cfg.eveowners.Get(warFactionID).name), parent=self.subinfolinkcontainer, align=uiconst.CENTERLEFT, left=38)
            self.subinfolinkcontainer.height = 32
        if self.allianceinfo is None:
            self.allianceinfo = sm.GetService('alliance').GetAlliance(self.itemID)
        uthread.new(self.ShowRelationshipIcon, None, None, self.itemID)
        if not self.allianceinfo.deleted:
            bountyOwnerIDs = (self.itemID,)
            bountyAmount = self.GetBountyAmount(*bountyOwnerIDs)
            wanted = bountyAmount > 0
            self.Wanted(bountyAmount, False, wanted, ownerIDs=bountyOwnerIDs)

    def ConstructHeaderFaction(self):
        if self.factioninfo is None:
            self.factioninfo = cfg.factions.GetIfExists(self.itemID)
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/InfoWindow/HeadquartersLocation', location=self.factioninfo.solarSystemID), parent=self.captioncontainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED)

    def ConstructHeaderSkill(self):
        hasSkill = sm.GetService('skills').HasSkill(self.typeID)
        if hasSkill:
            skillParent = Container(parent=self.therestcontainer, align=uiconst.TOTOP, height=10, top=4)
            uicls.SkillLevels(parent=skillParent, align=uiconst.TOLEFT, typeID=self.typeID, groupID=self.groupID)
        else:
            labelText = localization.GetByLabel('UI/SkillQueue/Skills/SkillNotInjected')
            lbl = uicontrols.EveLabelSmall(text=labelText, parent=self.therestcontainer, align=uiconst.TOTOP)
            lbl.SetAlpha(0.4)

    def ConstructHeaderBlueprint(self):
        self.subinfolinkcontainer.padTop = 0
        bpData = self.GetBlueprintData()
        bpInfoCont = Container(name='copyInfoCont', parent=self.therestcontainer, align=uiconst.TOTOP, height=32)
        if not bpData.IsAncientRelic():
            if bpData.original:
                text = localization.GetByLabel('UI/Industry/OriginalInfiniteRuns')
            elif not bpData.runsRemaining or bpData.runsRemaining <= 0:
                text = localization.GetByLabel('UI/Industry/Copy')
            else:
                text = localization.GetByLabel('UI/Industry/CopyRunsRemaining', runsRemaining=bpData.runsRemaining)
            Label(parent=self.captioncontainer, align=uiconst.TOTOP, text=text)
        if bpData.IsAncientRelic():
            return
        self.containerME = ContainerME(parent=bpInfoCont, align=uiconst.TOPLEFT, pos=(0, 0, 71, 30))
        self.containerME.SetValue(bpData.materialEfficiency)
        self.containerTE = ContainerTE(parent=bpInfoCont, align=uiconst.TOPLEFT, pos=(80, 0, 71, 30))
        self.containerTE.SetValue(bpData.timeEfficiency)

    def GetInfoWindowType(self):
        if self.typeID in infoTypeByTypeID:
            return infoTypeByTypeID[self.typeID]
        if self.groupID in infoTypeByGroupID:
            return infoTypeByGroupID[self.groupID]
        if self.categoryID in infoTypeByCategoryID:
            return infoTypeByCategoryID[self.categoryID]
        return TYPE_UNKNOWN

    def IsType(self, *args):
        """
        Check if this window is of a certain info window type as defined by constants in infoConst.py        
        Accepts either a list or a single info type id
        """
        return self.infoType in args

    def IsOwned(self):
        return self.groupID in ownedGroups or self.categoryID in ownedCategories

    def IsUpgradeable(self):
        try:
            godmaType = sm.GetService('godma').GetType(self.typeID)
            return godmaType.constructionType != 0
        except AttributeError:
            return False

    def UpdateCaption(self):
        invtype = cfg.invtypes.Get(self.typeID)
        if self.IsType(TYPE_SHIP, TYPE_BOOKMARK, TYPE_CERTIFICATE):
            caption = localization.GetByLabel('UI/InfoWindow/InfoWindowCaption', infoObject=invtype.name)
        elif self.IsType(TYPE_LANDMARK):
            caption = localization.GetByLabel('UI/InfoWindow/LandmarkInformationCaption')
        elif self.IsType(TYPE_SCHEMATIC):
            caption = localization.GetByLabel('UI/InfoWindow/InfoWindowCaption', infoObject=localization.GetByLabel('UI/PI/Common/Schematics'))
        elif self.IsType(TYPE_SKILL):
            caption = localization.GetByLabel('UI/InfoWindow/InfoWindowCaption', infoObject=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SkillTabs/Skill'))
        else:
            caption = localization.GetByLabel('UI/InfoWindow/InfoWindowCaption', infoObject=invtype.Group().name)
        self.SetCaption(caption)

    def GetBlueprintData(self):
        if self.abstractinfo and self.abstractinfo.Get('bpData', None):
            return self.abstractinfo.bpData
        return sm.GetService('blueprintSvc').GetBlueprint(self.itemID, self.typeID)

    def UpdateWindowIcon(self, typeID, itemID):
        iWidth = iHeight = 64
        rendersize = 128
        self.mainicon.Flush()
        self.techicon.Hide()
        self.mainiconparent.cursor = None
        self.mainiconparent.OnClick = None
        if self.IsType(TYPE_SHIP, TYPE_STATION, TYPE_STARGATE, TYPE_DRONE, TYPE_ENTITY, TYPE_CELESTIAL, TYPE_RANK):
            iWidth = iHeight = 128
            if self.groupID not in (const.groupRegion, const.groupConstellation, const.groupSolarSystem):
                rendersize = 256
        hasAbstractIcon = False
        if self.abstractinfo is not None:
            import xtriui
            if self.IsType(TYPE_RANK):
                rank = xtriui.Rank(name='rankicon', align=uiconst.TOPLEFT, left=3, top=2, width=iWidth, height=iHeight, parent=self.mainicon)
                rank.Startup(self.abstractinfo.warFactionID, self.abstractinfo.currentRank)
                hasAbstractIcon = True
            if self.IsType(TYPE_MEDAL, TYPE_RIBBON):
                rendersize = 256
                iWidth, iHeight = (128, 256)
                medal = xtriui.MedalRibbon(name='medalicon', align=uiconst.TOPLEFT, left=3, top=2, width=iWidth, height=iHeight, parent=self.mainicon)
                medal.Startup(self.abstractinfo, rendersize)
                hasAbstractIcon = True
            if self.IsType(TYPE_CERTIFICATE):
                texturePath = 'res:/UI/Texture/icons/79_64_%s.png' % (self.abstractinfo.level + 1)
                sprite = Sprite(parent=self.mainicon, texturePath=texturePath, align=uiconst.TOALL)
                self.mainiconparent.hint = cfg.invtypes.Get(const.typeCertificate).description
                hasAbstractIcon = True
            if self.IsType(TYPE_SCHEMATIC):
                sprite = uicontrols.Icon(parent=self.mainicon, icon='ui_27_64_3', align=uiconst.TOALL)
                hasAbstractIcon = True
        if self.IsType(TYPE_CHARACTER):
            sprite = Sprite(parent=self.mainicon, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
            sm.GetService('photo').GetPortrait(itemID, 256, sprite, allowServerTrip=True)
            iWidth = iHeight = 128
            if not util.IsDustCharacter(itemID):
                self.mainiconparent.cursor = uiconst.UICURSOR_MAGNIFIER
                self.mainiconparent.OnClick = (self.OpenPortraitWnd, itemID)
        elif self.IsType(TYPE_CORPORATION, TYPE_FACTION, TYPE_ALLIANCE):
            if self.IsType(TYPE_CORPORATION):
                try:
                    cfg.eveowners.Get(itemID)
                except:
                    log.LogWarn('Tried to show info on bad corpID:', itemID)
                    raise BadArgs('InfoNoCorpWithID')

            uiutil.GetLogoIcon(itemID=itemID, parent=self.mainicon, name='corplogo', acceptNone=False, align=uiconst.TOALL)
            self.mainiconparent.cursor = uiconst.UICURSOR_MAGNIFIER
            self.mainiconparent.OnClick = (self.OpenEntityWnd, itemID)
        elif self.IsType(TYPE_LANDMARK):
            landmark = sm.GetService('map').GetLandmark(itemID * -1)
            if hasattr(landmark, 'iconID'):
                sprite = Sprite(parent=self.mainicon, align=uiconst.TOALL)
                sprite.texture.resPath = util.IconFile(landmark.iconID)
                sprite.rectLeft = 64
                sprite.rectWidth = 128
                iWidth = iHeight = 128
        elif self.IsType(TYPE_BLUEPRINT) and (itemID and itemID < const.minFakeItem or self.abstractinfo is not None):
            uix.GetTechLevelIcon(self.techicon, 0, typeID)
            bpData = self.GetBlueprintData()
            icon = Icon(parent=self.mainicon, align=uiconst.TOALL, size=rendersize, typeID=typeID, itemID=itemID, ignoreSize=True, isCopy=not bpData.original)
        elif not hasAbstractIcon:
            uix.GetTechLevelIcon(self.techicon, 0, typeID)
            icon = uicontrols.Icon(parent=self.mainicon, align=uiconst.TOALL, size=rendersize, typeID=typeID, itemID=itemID, ignoreSize=True)
            if util.IsPreviewable(typeID):
                icon.typeID = typeID
                self.mainiconparent.cursor = uiconst.UICURSOR_MAGNIFIER
                self.mainiconparent.OnClick = (self.OnPreviewClick, icon)
        self.mainiconparent.width = self.mainicon.width = iWidth
        self.mainiconparent.height = self.mainicon.height = iHeight

    def GetNeocomGroupLabel(self):
        return localization.GetByLabel('UI/InfoWindow/Information')

    def UpdateHeaderActionMenu(self):
        actionMenu = self.GetActionMenu(self.itemID, self.typeID, self.rec)
        infoicon = self.sr.headerIcon
        if actionMenu:
            self.SetHeaderIcon()
            infoicon = self.sr.headerIcon
            infoicon.state = uiconst.UI_NORMAL
            infoicon.expandOnLeft = 1
            infoicon.GetMenu = lambda *args: self.GetIconActionMenu(self.itemID, self.typeID, self.rec)
            infoicon.hint = localization.GetByLabel('UI/InfoWindow/ActionMenuHint')
            self.presetMenu = infoicon
            infoicon.state = uiconst.UI_NORMAL
            if self.sr.tab:
                self.sr.tab.SetIcon(self.headerIconNo, 14, self.headerIconHint, menufunc=infoicon.GetMenu)
        elif infoicon:
            infoicon.Hide()

    def UpdateDescriptionCaptionAndSubCaption(self):
        capt = None
        invtype = cfg.invtypes.Get(self.typeID)
        if self.itemID in cfg.evelocations.data:
            capt = cfg.evelocations.Get(self.itemID).name
        if not capt:
            capt = invtype.name
        desc = invtype.description
        subCapt = ''
        if self.IsType(TYPE_LANDMARK):
            landmark = sm.GetService('map').GetLandmark(self.itemID * -1)
            capt = maputils.GetNameFromMapCache(landmark.landmarkNameID, 'landmark')
            desc = maputils.GetNameFromMapCache(landmark.descriptionID, 'landmark')
            subCapt = ''
        elif self.IsType(TYPE_RANK) and self.abstractinfo is not None:
            capt = localization.GetByLabel('UI/FactionWarfare/Rank')
            rankLabel, rankDescription = sm.GetService('facwar').GetRankLabel(self.abstractinfo.warFactionID, self.abstractinfo.currentRank)
            desc = rankDescription
            subCapt = rankLabel
        elif self.IsType(TYPE_MEDAL, TYPE_RIBBON) and self.abstractinfo is not None:
            info = sm.GetService('medals').GetMedalDetails(self.itemID).info[0]
            desc = info.description
            subCapt = info.title
        elif self.IsType(TYPE_CERTIFICATE) and self.abstractinfo is not None:
            capt, _, desc = sm.GetService('certificates').GetCertificateLabel(self.abstractinfo.certificateID)
            subCapt = ''
        elif self.IsType(TYPE_SCHEMATIC) and self.abstractinfo is not None:
            subCapt = self.abstractinfo.schematicName
            desc = ''
        elif self.IsType(TYPE_SKILL):
            subCapt = '&gt; %s' % cfg.invtypes.Get(self.typeID).Group().name
        elif self.IsType(TYPE_BOOKMARK) and self.itemID is not None:
            capt = localization.GetByLabel('UI/Browser/Bookmark')
            voucherinfo = sm.GetService('voucherCache').GetVoucher(self.itemID)
            if voucherinfo:
                subCapt, desc = sm.GetService('addressbook').UnzipMemo(voucherinfo.GetDescription())
                desc = voucherinfo.GetDescription()
        elif self.IsType(TYPE_CHARACTER) and self.itemID is not None:
            capt = cfg.eveowners.Get(self.itemID).name
            desc = cfg.eveowners.Get(self.itemID).description
            if desc == capt:
                bloodline = sm.GetService('info').GetBloodlineByTypeID(cfg.eveowners.Get(self.itemID).typeID)
                desc = localization.GetByMessageID(bloodline.descriptionID)
        elif self.IsType(TYPE_CORPORATION) and self.itemID is not None:
            if self.corpinfo is None:
                self.corpinfo = sm.RemoteSvc('corpmgr').GetPublicInfo(self.itemID)
            if self.corpinfo.corporationID < 1100000:
                desc = cfg.npccorporations.Get(self.corpinfo.corporationID).description
            else:
                desc = self.corpinfo.description
            if uiutil.CheckCorpID(self.itemID):
                capt = ''
            else:
                capt = cfg.eveowners.Get(self.itemID).name
                if self.corpinfo.deleted:
                    capt = localization.GetByLabel('UI/InfoWindow/ClosedCorpOrAllianceCaption', corpOrAllianceName=cfg.eveowners.Get(self.itemID).name)
        elif self.IsType(TYPE_ALLIANCE) and self.itemID is not None:
            if self.allianceinfo is None:
                self.allianceinfo = sm.GetService('alliance').GetAlliance(self.itemID)
            capt = cfg.eveowners.Get(self.itemID).name
            desc = self.allianceinfo.description
            if self.allianceinfo.deleted:
                capt = localization.GetByLabel('UI/InfoWindow/ClosedCorpOrAllianceCaption', corpOrAllianceName=cfg.eveowners.Get(self.itemID).name)
        elif self.IsType(TYPE_STATION):
            if self.itemID is not None:
                if self.stationinfo is None:
                    self.stationinfo = sm.GetService('map').GetStation(self.itemID)
                capt = self.stationinfo.stationName
                if self.itemID < 61000000 and self.stationinfo.stationTypeID not in (12294, 12295, 12242):
                    desc = localization.GetByMessageID(self.stationinfo.descriptionID)
                else:
                    desc = self.stationinfo.description
            else:
                desc = cfg.invtypes.Get(self.typeID).description or cfg.invtypes.Get(self.typeID).name
        elif self.IsType(TYPE_WORMHOLE):
            slimItem = sm.StartService('michelle').GetItem(self.itemID)
            if slimItem:
                wormholeClasses = {0: 'UI/Wormholes/Classes/UnknownSpaceDescription',
                 1: 'UI/Wormholes/Classes/UnknownSpaceDescription',
                 2: 'UI/Wormholes/Classes/UnknownSpaceDescription',
                 3: 'UI/Wormholes/Classes/UnknownSpaceDescription',
                 4: 'UI/Wormholes/Classes/DangerousUnknownSpaceDescription',
                 5: 'UI/Wormholes/Classes/DangerousUnknownSpaceDescription',
                 6: 'UI/Wormholes/Classes/DeadlyUnknownSpaceDescription',
                 7: 'UI/Wormholes/Classes/HighSecuritySpaceDescription',
                 8: 'UI/Wormholes/Classes/LowSecuritySpaceDescription',
                 9: 'UI/Wormholes/Classes/NullSecuritySpaceDescription',
                 12: 'UI/Wormholes/Classes/TheraDescription',
                 13: 'UI/Wormholes/Classes/UnknownSpaceDescription'}
                wormholeClassLabelName = wormholeClasses.get(slimItem.otherSolarSystemClass)
                wClass = localization.GetByLabel(wormholeClassLabelName)
                if slimItem.wormholeAge >= 2:
                    wAge = localization.GetByLabel('UI/InfoWindow/WormholeAgeReachingTheEnd')
                elif slimItem.wormholeAge >= 1:
                    wAge = localization.GetByLabel('UI/InfoWindow/WormholeAgeStartedDecaying')
                elif slimItem.wormholeAge >= 0:
                    wAge = localization.GetByLabel('UI/InfoWindow/WormholeAgeNew')
                else:
                    wAge = ''
                if slimItem.wormholeSize < 0.5:
                    remaining = localization.GetByLabel('UI/InfoWindow/WormholeSizeStabilityCriticallyDisrupted')
                elif slimItem.wormholeSize < 1:
                    remaining = localization.GetByLabel('UI/InfoWindow/WormholeSizeStabilityReduced')
                else:
                    remaining = localization.GetByLabel('UI/InfoWindow/WormholeSizeNotDisrupted')
                if slimItem.maxShipJumpMass == const.WH_SLIM_MAX_SHIP_MASS_SMALL:
                    maxSize = localization.GetByLabel('UI/InfoWindow/WormholeMaxShipMassSmall')
                elif slimItem.maxShipJumpMass == const.WH_SLIM_MAX_SHIP_MASS_MEDIUM:
                    maxSize = localization.GetByLabel('UI/InfoWindow/WormholeMaxShipMassMedium')
                elif slimItem.maxShipJumpMass == const.WH_SLIM_MAX_SHIP_MASS_LARGE:
                    maxSize = localization.GetByLabel('UI/InfoWindow/WormholeMaxShipMassLarge')
                elif slimItem.maxShipJumpMass == const.WH_SLIM_MAX_SHIP_MASS_VERYLARGE:
                    maxSize = localization.GetByLabel('UI/InfoWindow/WormholeMaxShipMassVeryLarge')
                else:
                    maxSize = ''
                desc = invtype.description + '<br>'
                desc = localization.GetByLabel('UI/InfoWindow/WormholeDescription', wormholeName=desc, wormholeClass=wClass, wormholeAge=wAge, remaining=remaining, maxSize=maxSize)
                capt = invtype.name
        elif self.IsType(TYPE_CELESTIAL, TYPE_STARGATE):
            desc = ''
            if invtype.groupID in (const.groupSolarSystem, const.groupConstellation, const.groupRegion):
                locationTrace = self.GetLocationTrace(self.itemID, [])
                subCapt = invtype.name + '<br><br>' + locationTrace
                mapdesc = cfg.mapcelestialdescriptions.GetIfExists(self.itemID)
                if mapdesc:
                    desc = mapdesc.description
            if not desc:
                desc = invtype.description or invtype.name
            desc = desc + '<br>'
            capt = invtype.name
            if invtype.groupID == const.groupBeacon:
                beacon = sm.GetService('michelle').GetItem(self.itemID)
                if beacon and hasattr(beacon, 'dunDescriptionID') and beacon.dunDescriptionID:
                    desc = localization.GetByMessageID(beacon.dunDescriptionID)
            locationname = None
            if self.itemID is not None:
                try:
                    if self.itemID < const.minPlayerItem or self.rec is not None and self.rec.singleton:
                        locationname = cfg.evelocations.Get(self.itemID).name
                    else:
                        locationname = invtype.name
                except KeyError:
                    locationname = invtype.name
                    sys.exc_clear()

            if locationname and locationname[0] != '@':
                capt = locationname
        elif self.IsType(TYPE_ASTEROID):
            capt = invtype.name
        elif self.IsType(TYPE_FACTION):
            capt = ''
            if self.factioninfo is None:
                self.factioninfo = cfg.factions.GetIfExists(self.itemID)
            desc = localization.GetByMessageID(self.factioninfo.descriptionID)
        elif self.IsType(TYPE_CUSTOMSOFFICE):
            capt = cfg.invtypes.Get(self.typeID).name
            bp = sm.GetService('michelle').GetBallpark()
            slimItem = None
            if bp is not None:
                slimItem = bp.GetInvItem(self.itemID)
            if slimItem:
                capt = uix.GetSlimItemName(slimItem)
        if desc:
            self.data[TAB_DESCRIPTION]['text'] = desc
        self.captionText = capt or ''
        self.subCaptionText = subCapt or ''

    def GetLocationTrace(self, itemID, trace, recursive = 0):
        parentID = sm.GetService('map').GetParent(itemID)
        if parentID != const.locationUniverse:
            parentItem = sm.GetService('map').GetItem(parentID)
            if parentItem:
                label = localization.GetByLabel('UI/InfoWindow/LocationTrace', locationType=parentItem.typeID, locationName=parentItem.itemName)
                trace += self.GetLocationTrace(parentID, [label], 1)
        if recursive:
            return trace
        else:
            trace.reverse()
            item = sm.GetService('map').GetItem(itemID)
            if item and self.groupID == const.groupSolarSystem and item.security is not None:
                sec = sm.GetService('map').GetSecurityStatus(itemID)
                label = localization.GetByLabel('UI/InfoWindow/SecurityLevelInLocationTrace', secLevel=util.FmtSystemSecStatus(sec))
                trace += [label]
            return '<br>'.join(trace)

    def OnPreviewClick(self, obj, *args):
        sm.GetService('preview').PreviewType(obj.typeID, itemID=getattr(obj, 'itemID', None))

    def OpenPortraitWnd(self, charID, *args):
        PortraitWindow.CloseIfOpen()
        PortraitWindow.Open(charID=charID)

    def OpenEntityWnd(self, entityID, *args):
        EntityWindow.CloseIfOpen()
        EntityWindow.Open(entityID=entityID)

    def GetIconActionMenu(self, itemID, typeID, rec):
        return self.GetActionMenu(itemID, typeID, rec)

    def GetActionMenu(self, itemID, typeID, invItem):
        if typeID == const.typeCertificate:
            return None
        m = sm.GetService('menu').GetMenuFormItemIDTypeID(itemID, typeID, filterFunc=[localization.GetByLabel('UI/Commands/ShowInfo')], invItem=invItem, ignoreMarketDetails=0)
        if self.IsType(TYPE_CHARACTER, TYPE_CORPORATION):
            if not util.IsNPC(itemID) and not util.IsDustCharacter(itemID):
                m.append((uiutil.MenuLabel('UI/InfoWindow/ShowContracts'), self.ShowContracts, (itemID,)))
        if self.IsType(TYPE_CHARACTER) and not util.IsNPC(itemID) and not int(sm.GetService('machoNet').GetGlobalConfig().get('hideReportBot', 0)):
            m.append((uiutil.MenuLabel('UI/InfoWindow/ReportBot'), self.ReportBot, (itemID,)))
        return m

    def ReportBot(self, itemID, *args):
        if eve.Message('ConfirmReportBot', {'name': cfg.eveowners.Get(itemID).name}, uiconst.YESNO) != uiconst.ID_YES:
            return
        if itemID == session.charid:
            raise UserError('ReportBotCannotReportYourself')
        sm.RemoteSvc('userSvc').ReportBot(itemID)
        eve.Message('BotReported', {'name': cfg.eveowners.Get(itemID).name})

    def ShowContracts(self, itemID, *args):
        sm.GetService('contracts').Show(lookup=cfg.eveowners.Get(itemID).name)

    def ShowRelationshipIcon(self, itemID, corpid, allianceid):
        ret = sm.GetService('addressbook').GetRelationship(itemID, corpid, allianceid)
        relationships = [ret.persToCorp,
         ret.persToPers,
         ret.persToAlliance,
         ret.corpToPers,
         ret.corpToCorp,
         ret.corpToAlliance,
         ret.allianceToPers,
         ret.allianceToCorp,
         ret.allianceToAlliance]
        relationship = 0.0
        for r in relationships:
            if r != 0.0 and r > relationship or relationship == 0.0:
                relationship = r

        flag = None
        iconNum = 0
        if relationship > const.contactGoodStanding:
            flag = state.flagStandingHigh
            iconNum = 3
        elif relationship > const.contactNeutralStanding and relationship <= const.contactGoodStanding:
            flag = state.flagStandingGood
            iconNum = 3
        elif relationship < const.contactNeutralStanding and relationship >= const.contactBadStanding:
            flag = state.flagStandingBad
            iconNum = 4
        elif relationship < const.contactBadStanding:
            flag = state.flagStandingHorrible
            iconNum = 4
        if not flag:
            return
        if itemID:
            pos = (4, 4, 14, 14)
            iconPos = (0, 0, 15, 15)
        else:
            pos = (4, 4, 12, 12)
            iconPos = (0, 0, 13, 13)
        icon = FlagIconWithState(parent=self.mainicon, pos=pos, state=uiconst.UI_DISABLED, align=uiconst.BOTTOMLEFT)
        flagInfo = sm.GetService('state').GetStatePropsColorAndBlink(flag)
        icon.ModifyIcon(flagInfo=flagInfo, showHint=False)
        icon.ChangeIconPos(*iconPos)
        uicore.animations.FadeTo(icon.flagBackground, startVal=0.0, endVal=0.6, duration=0.3, loops=1)

    def GetCorpLogo(self, corpID, parent = None):
        logo = uiutil.GetLogoIcon(itemID=corpID, parent=parent, state=uiconst.UI_NORMAL, hint=localization.GetByLabel('UI/InfoWindow/ClickForCorpInfo'), align=uiconst.TOLEFT, pos=(0, 0, 64, 64), ignoreSize=True)
        parent.height = 64
        if not util.IsNPC(corpID):
            try:
                uicontrols.Frame(parent=logo, color=(1.0, 1.0, 1.0, 0.1))
            except:
                pass

        logo.OnClick = (self.ReconstructInfoWindow, const.typeCorporation, corpID)
        return logo

    def Wanted(self, bounty, isChar, showSprite, isNPC = False, ownerIDs = None, hint = None):
        if not isNPC:
            self.bountyOwnerIDs = (self.itemID,) if ownerIDs is None else ownerIDs
            uicls.PlaceBountyUtilMenu(parent=self.therestcontainer, ownerID=self.itemID, bountyOwnerIDs=self.bountyOwnerIDs)
        if showSprite:
            if isChar or isNPC:
                width = 128
                height = 34
                top = 2
            else:
                width = 64
                height = 17
                top = 1
            Sprite(name='wanted', parent=self.mainicon, idx=0, texturePath='res:/UI/Texture/wanted.png', width=width, height=height, align=uiconst.CENTERBOTTOM, hint=localization.GetByLabel('UI/InfoWindow/BountyHint', amount=util.FmtISK(bounty, False)), top=top)
        self.bountyLabelInfo = uicontrols.EveLabelSmall(text='', parent=self.therestcontainer, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        self.bountyLabelInfo.text = localization.GetByLabel('UI/Common/BountyAmount', bountyAmount=util.FmtISK(bounty, False))
        if hint is not None:
            self.bountyLabelInfo.hint = hint

    def OnBountyPlaced(self, ownerID):
        if ownerID == self.itemID:
            bounty = self.GetBountyAmount(*self.bountyOwnerIDs)
            self.bountyLabelInfo.text = localization.GetByLabel('UI/Common/BountyAmount', bountyAmount=util.FmtISK(bounty, False))

    def GetBountyAmount(self, *ownerIDs):
        bountyAmount = sm.GetService('bountySvc').GetBounty(*ownerIDs)
        return bountyAmount

    def GetBountyAmounts(self, *ownerIDs):
        bountyAmounts = sm.GetService('bountySvc').GetBounties(*ownerIDs)
        return bountyAmounts

    def ResetWindowData(self, tabs = None):
        self.data = {}
        self.dynamicTabs = []
        self.data['buttons'] = []
        self._ParseTabs(INFO_TABS)

    def GetDynamicTabLoadMethod(self, tabID):
        """
            DEPRICATED. Please look into using GetPanelByTabType instead
        """
        if tabID == TAB_ALLIANCEHISTORY:
            return self.LoadAllianceHistory
        if tabID == TAB_EMPLOYMENTHISTORY:
            return self.LoadEmploymentHistory
        if tabID == TAB_DECORATIONS:
            return self.LoadDecorations
        if tabID == TAB_WARHISTORY:
            return self.LoadWarHistory
        if tabID == TAB_SCHEMATICS:
            return self.LoadProcessPinSchematics
        if tabID == TAB_PLANETCONTROL:
            return self.LoadPlanetControlInfo
        if tabID == TAB_FUELREQ:
            return self.LoadFuelRequirements
        if tabID == TAB_UPGRADEMATERIALREQ:
            return self.LoadUpgradeMaterialRequirements
        if tabID == TAB_MATERIALREQ:
            return self.LoadMaterialRequirements
        if tabID == TAB_REACTION:
            return self.LoadReaction
        if tabID == TAB_STANDINGS:
            return self.LoadStandings
        if tabID == TAB_MEMBERS:
            return self.LoadAllianceMembers
        if tabID == TAB_PRODUCTIONINFO:
            return self.LoadCommodityProductionInfo

    def _ParseTabs(self, tabs):
        for listtype, subtabs, tabName in tabs:
            self.data[listtype] = {'name': localization.GetByLabel(tabName),
             'items': [],
             'subtabs': subtabs,
             'inited': 0,
             'headers': []}
            if subtabs:
                self._ParseTabs(subtabs)

    def Close(self, *args, **kwargs):
        try:
            sm.GetService('info').UnregisterWindow(self)
        finally:
            uicontrols.Window.Close(self, *args, **kwargs)

    def SetActive(self, *args):
        uicontrols.Window.SetActive(self, *args)
        sm.GetService('info').OnActivateWnd(self)

    def Load(self, passedargs, *args):
        """ Load method for main tabs """
        if type(passedargs) == types.TupleType:
            if len(passedargs) == 2:
                listtype, func = passedargs
                if func:
                    func()
                elif listtype in self.data:
                    self.scroll.Load(contentList=self.data[listtype]['items'], headers=self.data[listtype]['headers'])
            elif len(passedargs) == 3:
                listtype, func, string = passedargs
                if listtype == 'readOnlyText':
                    self.descedit.window = self
                    self.descedit.SetValue(string, scrolltotop=1)
                elif listtype == 'selectSubtab':
                    listtype, string, subtabgroup = passedargs
                    subtabgroup.AutoSelect()
            self._LogIGS(listtype)
        else:
            self.scroll.Clear()
        if self.variationCompareBtn is not None:
            if listtype == TAB_VARIATIONS:
                self.variationCompareBtn.state = uiconst.UI_PICKCHILDREN
            else:
                self.variationCompareBtn.Hide()

    def _LogIGS(self, tabID):
        with util.ExceptionEater('infosvc _LogIGS'):
            if tabID == 'readOnlyText':
                tabID = 0
            if isinstance(tabID, int):
                sm.GetService('infoGatheringSvc').LogInfoEvent(eventTypeID=const.infoEventInfoWindowTabs, itemID=session.charid, int_1=self.infoType, int_2=tabID, int_3=1)

    def LoadEmploymentHistory(self):
        self.LoadGeneric(TAB_EMPLOYMENTHISTORY, sm.GetService('info').GetEmploymentHistorySubContent)

    def LoadAllianceHistory(self):
        self.LoadGeneric(TAB_ALLIANCEHISTORY, sm.GetService('info').GetAllianceHistorySubContent)

    def LoadWarHistory(self):
        self.LoadGeneric(TAB_WARHISTORY, sm.GetService('info').GetWarHistorySubContent, noContentHint=localization.GetByLabel('UI/Common/NothingFound'))

    def LoadAllianceMembers(self):
        self.LoadGeneric(TAB_MEMBERS, sm.GetService('info').GetAllianceMembersSubContent)

    def LoadStandings(self):
        self.LoadGeneric(TAB_STANDINGS, sm.GetService('info').GetStandingsHistorySubContent)

    def LoadUpgradeMaterialRequirements(self):
        if not self.data[TAB_UPGRADEMATERIALREQ]['inited']:
            t = sm.GetService('godma').GetType(self.typeID)
            upgradeToType = cfg.invtypes.Get(t.constructionType)
            materialList = cfg.invtypematerials.get(t.constructionType)
            menuFunc = lambda itemID = t.constructionType: sm.GetService('menu').GetMenuFormItemIDTypeID(None, itemID, ignoreMarketDetails=0)
            upgradesIntoEntry = listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
             'label': localization.GetByLabel('UI/InfoWindow/UpgradesInto'),
             'text': upgradeToType.name,
             'typeID': upgradeToType.typeID,
             'GetMenu': menuFunc})
            self.data[TAB_UPGRADEMATERIALREQ]['items'].append(upgradesIntoEntry)
            self.data[TAB_UPGRADEMATERIALREQ]['items'].append(listentry.Get('Divider'))
            commands = []
            for _, resourceTypeID, quantity in materialList:
                resourceType = cfg.invtypes.Get(resourceTypeID)
                menuFunc = lambda itemID = resourceType.typeID: sm.GetService('menu').GetMenuFormItemIDTypeID(None, itemID, ignoreMarketDetails=0)
                text = localization.formatters.FormatNumeric(quantity, useGrouping=True, decimalPlaces=0)
                le = listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
                 'label': resourceType.typeName,
                 'text': text,
                 'iconID': resourceType.iconID,
                 'typeID': resourceType.typeID,
                 'GetMenu': menuFunc})
                commands.append((resourceTypeID, quantity))
                self.data[TAB_UPGRADEMATERIALREQ]['items'].append(le)

            if eve.session.role & ROLE_GML == ROLE_GML:
                self.data[TAB_UPGRADEMATERIALREQ]['items'].append(listentry.Get('Divider'))
                self.data[TAB_UPGRADEMATERIALREQ]['items'].append(listentry.Get('Button', {'label': 'GML: Create in cargo',
                 'caption': 'Create',
                 'OnClick': sm.GetService('info').DoCreateMaterials,
                 'args': (commands, '', 1)}))
            self.data[TAB_UPGRADEMATERIALREQ]['inited'] = 1
        self.scroll.Load(fixedEntryHeight=27, contentList=self.data[TAB_UPGRADEMATERIALREQ]['items'])

    def LoadGeneric(self, label, getSubContent, noContentHint = ''):
        if not self.data[label]['inited']:
            self.data[label]['items'].extend(getSubContent(self.itemID))
            self.data[label]['inited'] = True
        self.scroll.Load(fixedEntryHeight=27, contentList=self.data[label]['items'], noContentHint=noContentHint)

    def LoadGenericType(self, label, getSubContent):
        if not self.data[label]['inited']:
            self.data[label]['items'].extend(getSubContent(self.typeID))
            self.data[label]['inited'] = True
        self.scroll.Load(fixedEntryHeight=27, contentList=self.data[label]['items'])

    def LoadFuelRequirements(self):
        if not self.data[TAB_FUELREQ]['inited']:
            purposeDict = [(1, localization.GetByLabel('UI/InfoWindow/ControlTowerOnline')),
             (2, localization.GetByLabel('UI/InfoWindow/ControlTowerPower')),
             (3, localization.GetByLabel('UI/InfoWindow/ControlTowerCPU')),
             (4, localization.GetByLabel('UI/InfoWindow/ControlTowerReinforced'))]
            cycle = sm.GetService('godma').GetType(self.typeID).posControlTowerPeriod
            rs = sm.RemoteSvc('posMgr').GetControlTowerFuelRequirements()
            controlTowerResourcesByTypePurpose = {}
            for entry in rs:
                if not controlTowerResourcesByTypePurpose.has_key(entry.controlTowerTypeID):
                    controlTowerResourcesByTypePurpose[entry.controlTowerTypeID] = {entry.purpose: [entry]}
                elif not controlTowerResourcesByTypePurpose[entry.controlTowerTypeID].has_key(entry.purpose):
                    controlTowerResourcesByTypePurpose[entry.controlTowerTypeID][entry.purpose] = [entry]
                else:
                    controlTowerResourcesByTypePurpose[entry.controlTowerTypeID][entry.purpose].append(entry)

            commands = []
            for purposeID, caption in purposeDict:
                self.data[TAB_FUELREQ]['items'].append(listentry.Get('Header', {'label': caption}))
                if self.typeID in controlTowerResourcesByTypePurpose:
                    if purposeID in controlTowerResourcesByTypePurpose[self.typeID]:
                        for row in controlTowerResourcesByTypePurpose[self.typeID][purposeID]:
                            extraList = []
                            if row.factionID is not None:
                                label = localization.GetByLabel('UI/InfoWindow/FactionSpace', factionName=cfg.eveowners.Get(row.factionID).name)
                                extraList.append(label)
                            if row.minSecurityLevel is not None:
                                label = localization.GetByLabel('UI/InfoWindow/SecurityLevel', secLevel=row.minSecurityLevel)
                                extraList.append(label)
                            if len(extraList):
                                t = localization.formatters.FormatGenericList(extraList)
                                extraText = localization.GetByLabel('UI/InfoWindow/IfExtraText', extraText=t)
                            else:
                                extraText = ''
                            if cycle / 3600000L == 1:
                                text = localization.GetByLabel('UI/InfoWindow/FuelRequirementPerHour', qty=row.quantity, extraText=extraText)
                            else:
                                numHours = cycle / 3600000L
                                text = localization.GetByLabel('UI/InfoWindow/FuelRequirement', qty=row.quantity, numHours=numHours, extraText=extraText)
                            resourceType = cfg.invtypes.Get(row.resourceTypeID)
                            menuFunc = lambda itemID = resourceType.typeID: sm.StartService('menu').GetMenuFormItemIDTypeID(None, itemID, ignoreMarketDetails=0, filterFunc=['UI/Commands/ShowInfo'])
                            le = listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
                             'label': resourceType.typeName,
                             'text': text,
                             'iconID': resourceType.iconID,
                             'typeID': resourceType.typeID,
                             'GetMenu': menuFunc})
                            commands.append((row.resourceTypeID, row.quantity))
                            self.data[TAB_FUELREQ]['items'].append(le)

            if eve.session.role & ROLE_GML == ROLE_GML:
                self.data[TAB_FUELREQ]['items'].append(listentry.Get('Divider'))
                self.data[TAB_FUELREQ]['items'].append(listentry.Get('Button', {'label': 'GML: Create in cargo',
                 'caption': 'Create',
                 'OnClick': sm.GetService('info').DoCreateMaterials,
                 'args': (commands, '', 10)}))
            self.data[TAB_FUELREQ]['inited'] = 1
        self.scroll.Load(fixedEntryHeight=27, contentList=self.data[TAB_FUELREQ]['items'])

    def LoadMaterialRequirements(self):
        if not self.data[TAB_MATERIALREQ]['inited']:
            stationTypeID = sm.GetService('godma').GetType(self.typeID).stationTypeID
            ingredients = cfg.invtypematerials.get(stationTypeID)
            commands = []
            for _, materialTypeID, quantity in ingredients:
                commands.append((materialTypeID, quantity))
                text = localization.GetByLabel('UI/Common/NumUnits', numItems=quantity)
                materialType = cfg.invtypes.Get(materialTypeID)
                le = listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
                 'label': materialType.name,
                 'text': text,
                 'iconID': materialType.iconID,
                 'typeID': materialType.typeID})
                self.data[TAB_MATERIALREQ]['items'].append(le)

            self.data[TAB_MATERIALREQ]['inited'] = 1
            if eve.session.role & ROLE_GML == ROLE_GML:
                self.data[TAB_MATERIALREQ]['items'].append(listentry.Get('Divider'))
                self.data[TAB_MATERIALREQ]['items'].append(listentry.Get('Button', {'label': 'GML: Create in cargo',
                 'caption': 'Create',
                 'OnClick': sm.GetService('info').DoCreateMaterials,
                 'args': (commands, '', 1)}))
        self.scroll.Load(fixedEntryHeight=27, contentList=self.data[TAB_MATERIALREQ]['items'])

    def LoadReaction(self):
        if not self.data[TAB_REACTION]['inited']:
            res = [ (row.typeID, row.quantity) for row in cfg.invtypereactions[self.typeID] if row.input == 1 ]
            prod = [ (row.typeID, row.quantity) for row in cfg.invtypereactions[self.typeID] if row.input == 0 ]
            godma = sm.GetService('godma')
            commands = []
            for label, what in [(localization.GetByLabel('UI/InfoWindow/Resources'), res), (localization.GetByLabel('UI/InfoWindow/Products'), prod)]:
                self.data[TAB_REACTION]['items'].append(listentry.Get('Header', {'label': label}))
                for typeID, quantity in what:
                    invtype = cfg.invtypes.Get(typeID)
                    amount = godma.GetType(typeID).moonMiningAmount
                    text = localization.GetByLabel('UI/Common/NumUnits', numItems=quantity * amount)
                    menuFunc = lambda typeID = typeID: sm.GetService('menu').GetMenuFormItemIDTypeID(None, typeID, ignoreMarketDetails=0, filterFunc=['UI/Commands/ShowInfo'])
                    commands.append((typeID, quantity * amount))
                    le = listentry.Get(decoClass=listentry.LabelTextSides, data={'line': 1,
                     'label': invtype.name,
                     'text': text,
                     'typeID': typeID,
                     'iconID': invtype.iconID,
                     'GetMenu': menuFunc})
                    self.data[TAB_REACTION]['items'].append(le)

            if eve.session.role & ROLE_GML == ROLE_GML:
                self.data[TAB_REACTION]['items'].append(listentry.Get('Divider'))
                self.data[TAB_REACTION]['items'].append(listentry.Get('Button', {'label': 'GML: Create in cargo',
                 'caption': 'Create',
                 'OnClick': sm.GetService('info').DoCreateMaterials,
                 'args': (commands, '', 10)}))
            self.data[TAB_REACTION]['inited'] = 1
        self.scroll.Load(contentList=self.data[TAB_REACTION]['items'])

    def LoadDecorations(self):
        self.scroll.Load(contentList=[], noContentHint=localization.GetByLabel('UI/Common/NoPublicDecorations'))

    def LoadProcessPinSchematics(self):
        if not self.data[TAB_SCHEMATICS]['inited']:
            schematicItems = []
            for schematicRow in cfg.schematicsByPin.get(self.typeID, []):
                schematic = cfg.schematics.Get(schematicRow.schematicID)
                abstractinfo = util.KeyVal(schematicName=schematic.schematicName, schematicID=schematic.schematicID, cycleTime=schematic.cycleTime)
                le = listentry.Get('Item', {'itemID': None,
                 'typeID': const.typeSchematic,
                 'label': schematic.schematicName,
                 'getIcon': 0,
                 'abstractinfo': abstractinfo})
                schematicItems.append(le)

            self.data[TAB_SCHEMATICS]['items'] = schematicItems
            self.data[TAB_SCHEMATICS]['inited'] = 1
        self.scroll.Load(contentList=self.data[TAB_SCHEMATICS]['items'])

    def LoadCommodityProductionInfo(self):
        if not self.data[TAB_PRODUCTIONINFO]['inited']:
            schematicItems = []
            producingStructureLines = []
            producingSchematicLines = []
            consumingSchematicLines = []
            for typeRow in cfg.schematicsByType.get(self.typeID, []):
                if typeRow.schematicID not in cfg.schematics:
                    self.LogWarn('CONTENT ERROR - Schematic ID', typeRow.schematicID, 'is in type map but not in main schematics list')
                    continue
                schematic = cfg.schematics.Get(typeRow.schematicID)
                abstractinfo = util.KeyVal(schematicName=schematic.schematicName, schematicID=schematic.schematicID, typeID=typeRow.typeID, isInput=typeRow.isInput, quantity=typeRow.quantity, cycleTime=schematic.cycleTime)
                le = listentry.Get('Item', {'itemID': None,
                 'typeID': const.typeSchematic,
                 'label': schematic.schematicName,
                 'getIcon': 0,
                 'abstractinfo': abstractinfo})
                if typeRow.isInput:
                    consumingSchematicLines.append(le)
                else:
                    producingSchematicLines.append(le)

            godma = sm.GetService('godma')
            for pinType in cfg.typesByGroups.get(const.groupExtractorPins, []):
                pinType = cfg.invtypes.Get(pinType.typeID)
                pinProducedType = godma.GetTypeAttribute(pinType.typeID, const.attributeHarvesterType)
                if pinProducedType and pinProducedType == self.typeID:
                    producingStructureLines.append(listentry.Get('Item', {'itemID': None,
                     'typeID': pinType.typeID,
                     'label': pinType.typeName,
                     'getIcon': 0}))

            if len(producingSchematicLines) > 0:
                schematicItems.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/SchematicsProducedBy')}))
                schematicItems.extend(producingSchematicLines)
            if len(producingStructureLines) > 0:
                schematicItems.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/StructuresProducedBy')}))
                schematicItems.extend(producingStructureLines)
            if len(consumingSchematicLines) > 0:
                schematicItems.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/InfoWindow/SchematicsConsuming')}))
                schematicItems.extend(consumingSchematicLines)
            self.data[TAB_PRODUCTIONINFO]['items'] = schematicItems
            self.data[TAB_PRODUCTIONINFO]['inited'] = 1
        self.scroll.Load(contentList=self.data[TAB_PRODUCTIONINFO]['items'])

    def LoadPlanetControlInfo(self):
        controlLabel = TAB_PLANETCONTROL
        if not self.data[controlLabel]['inited']:
            planetID = self.itemID
            lines = []
            bp = sm.GetService('michelle').GetBallpark()
            planetItem = bp.GetInvItem(planetID) if bp is not None else None
            controller = planetItem.ownerID if planetItem is not None else None
            if controller is not None:
                lines.append(listentry.Get('OwnerWithIconEntry', {'label': localization.GetByLabel('UI/InfoWindow/Sovereign'),
                 'line': 1,
                 'ownerID': controller}))
            requirementsText = localization.GetByLabel('UI/InfoWindow/PlanetControlRequirementHint')
            lines.append(listentry.Get('Generic', {'label': requirementsText,
             'maxLines': None}))
            self.data[controlLabel]['items'] = lines
            self.data[controlLabel]['inited'] = 1
        self.scroll.Load(contentList=self.data[controlLabel]['items'], noContentHint=localization.GetByLabel('UI/InfoWindow/PlanetNotContested'))


class BadArgs(RuntimeError):

    def __init__(self, msgID, kwargs = None):
        RuntimeError.__init__(self, msgID, kwargs or {})


class PortraitWindow(uicontrols.Window):
    __guid__ = 'form.PortraitWindow'
    default_windowID = 'PortraitWindow'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        charID = attributes.charID
        self.charID = charID
        self.photoSize = 512
        self.width = self.photoSize + 2 * const.defaultPadding
        self.height = self.width + 46
        self.SetMinSize([self.width, self.height])
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        caption = localization.GetByLabel('UI/Preview/ViewFullBody')
        btns = [[caption,
          self.SwitchToFullBody,
          (),
          81,
          1,
          1,
          0]]
        btnGroup = uicontrols.ButtonGroup(btns=btns, parent=self.sr.main, idx=0)
        self.switchBtn = btnGroup.GetBtnByLabel(caption)
        self.picParent = Container(name='picpar', parent=self.sr.main, align=uiconst.TOALL, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.pic = Sprite(parent=self.picParent, align=uiconst.TOALL)
        self.pic.GetMenu = self.PicMenu
        self.Load(charID)
        from eve.client.script.ui.shared.preview import PreviewCharacterWnd
        previewWnd = PreviewCharacterWnd.GetIfOpen()
        if previewWnd:
            previewWnd.CloseByUser()

    def Load(self, charID):
        caption = localization.GetByLabel('UI/InfoWindow/PortraitCaption', character=charID)
        self.SetCaption(caption)
        sm.GetService('photo').GetPortrait(charID, self.photoSize, self.pic)

    def PicMenu(self, *args):
        m = []
        if not util.IsDustCharacter(self.charID):
            m.append((uiutil.MenuLabel('UI/Commands/CapturePortrait'), sm.StartService('photo').SavePortraits, [self.charID]))
        m.append((uiutil.MenuLabel('/Carbon/UI/Common/Close'), self.CloseByUser))
        return m

    def SwitchToFullBody(self):
        try:
            self.switchBtn.Disable()
            wnd = sm.GetService('preview').PreviewCharacter(self.charID)
        finally:
            self.switchBtn.Enable()

        if wnd:
            self.CloseByUser()


class EntityWindow(uicontrols.Window):
    __guid__ = 'form.EntityWindow'
    default_windowID = 'EntityWindow'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        entityID = attributes.entityID
        self.entityID = entityID
        self.photoSize = 128
        self.width = self.photoSize + 2 * const.defaultPadding
        self.height = self.width + 20
        self.SetMinSize([self.width, self.height])
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        self.picParent = Container(name='picpar', parent=self.sr.main, align=uiconst.TOALL, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.Load()

    def Load(self):
        self.SetCaption(cfg.eveowners.Get(self.entityID).name)
        uiutil.GetLogoIcon(self.entityID, parent=self.picParent, acceptNone=False, align=uiconst.TOPRIGHT, height=128, width=128, state=uiconst.UI_NORMAL)


class AttributeRowEntry(listentry.Generic):
    """
        Entry that groups attribute icons and their values into one row
    """

    def Startup(self, *args):
        listentry.Generic.Startup(self, *args)
        self.sr.label.display = False
        self.rowLabel = uicontrols.EveLabelMedium(parent=self, text='', align=uiconst.TOTOP, padLeft=8, padTop=3)
        self.spriteCont = Container(parent=self, name='spriteCont', align=uiconst.TOLEFT, width=32)
        self.sprite = Sprite(parent=self.spriteCont, name='rowSprite', pos=(0, 0, 32, 32), align=uiconst.CENTER)
        self.damageContainer = AttributeValueRowContainer(parent=self, padding=(2, 2, 0, 2), align=uiconst.TOALL, height=0, doWidthAdjustments=True, loadOnStartup=False)

    def Load(self, node):
        node.selectable = False
        labelText = localization.GetByLabel(node.labelPath) if node.labelPath else ''
        self.rowLabel.text = labelText
        self.damageContainer.Load(node.attributeValues, mouseExitFunc=self.OnMouseExit, onClickFunc=node.OnClickAttr)
        if node.texturePath:
            self.sprite.LoadTexture(node.texturePath)
        else:
            self.spriteCont.display = False

    def GetHeight(self, *args):
        node, width = args
        node.height = 50
        return node.height

    def OnMouseExit(self, *args):
        if uiutil.IsUnder(uicore.uilib.mouseOver, self):
            return
        listentry.Generic.OnMouseExit(self, *args)

    def GetMenu(self):
        return [(uiutil.MenuLabel('UI/Common/Copy'), self.CopyText)]

    def CopyText(self):
        text = self.GetCopyData(self.sr.node)
        blue.pyos.SetClipboardData(text)

    @classmethod
    def GetCopyData(cls, node):
        attributeTextList = []
        for attributeID, value in node.attributeValues:
            attributeInfo = cfg.dgmattribs.Get(attributeID)
            text = '%s\t%s' % (attributeInfo.displayName, value)
            attributeTextList.append(text)

        return '\n'.join(attributeTextList)
