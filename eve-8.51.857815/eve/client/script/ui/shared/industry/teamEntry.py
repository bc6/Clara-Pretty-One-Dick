#Embedded file name: eve/client/script/ui/shared/industry\teamEntry.py
"""
Code for the team entry in industry
"""
from operator import itemgetter
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.shared.industry.installationActivityIcon import InstallationActivityIcon
from localization import GetByLabel
from carbon.common.script.sys.service import ROLE_QA
from carbon.common.script.util.format import StrFromColor, FmtDate
from eve.client.script.ui.control.baseListEntry import BaseListEntryCustomColumns
from eve.client.script.ui.control.buttons import Button, ButtonIcon
from eve.client.script.ui.control.eveLabel import EveLabelSmall, EveLabelMediumBold, EveLabelMedium
from eve.client.script.ui.control.eveScroll import Scroll
from eve.client.script.ui.shared.industry.industryUIConst import TEAM_TYPE_ICONS_SMALL
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from eve.client.script.ui.control.utilMenu import UtilMenu
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.util.searchUtil import QuickSearch
from eve.common.script.util.eveFormat import FmtSystemSecStatus, FmtISK
import blue
import sys
import carbonui.const as uiconst
import uthread
import util
import uiutil
import listentry
from workers import SPE_LABELS
from workers.specializationGroups import SPECIALIZATION_GROUPS
from workers.util import GetHighestBid, GetBidsBySolarSystem, GetMyBidsBySolarSystem, GetGroupNamesFromSpeciality, GetDistanceCost
from carbon.common.script.util.format import FmtAmt

class BaseTeamEntry(BaseListEntryCustomColumns):
    default_name = 'BaseTeamEntry'

    def ApplyAttributes(self, attributes):
        BaseListEntryCustomColumns.ApplyAttributes(self, attributes)
        self.searchedSystem = None
        self.workerConts = []
        self.team = self.node.team
        self.teamName = self.node.teamName
        self.expiryTime = self.node.expiryTime
        self.teamCost = self.node.teamCost
        self.AddColumnTeam()
        self.AddColumnText(cfg.evelocations.Get(self.team.solarSystemID).name)
        self.AddColumnJumps()
        self.AddColumnText(self.GetSecurityLabel(self.team.solarSystemID))
        self.AddColumnActivity()
        self.AddColumnWorkers()
        self.AddColumnSalary()
        self.timeLeft = self.AddColumnText('')
        uthread.new(self.SetTimeLeft)

    def AddColumnActivity(self):
        col = self.AddColumnContainer()
        ICONSIZE = 20
        InstallationActivityIcon(parent=col, align=uiconst.CENTER, pos=(0,
         0,
         ICONSIZE,
         ICONSIZE), activityID=self.team.activity, isEnabled=True)

    def AddColumnJumps(self):
        jumps = self.GetJumpsTo()
        if jumps != sys.maxint:
            self.AddColumnText(jumps)
        else:
            col = self.AddColumnContainer()
            Sprite(name='infinityIcon', parent=col, align=uiconst.CENTERLEFT, pos=(6, 0, 11, 6), texturePath='res:/UI/Texture/Classes/Industry/infinity.png', opacity=Label.default_color[3])

    def AddColumnSalary(self):
        col = self.AddColumnContainer()
        col.state = uiconst.UI_NORMAL
        self.salaryLabel = EveLabelMedium(parent=col, text=GetByLabel('UI/Common/Formatting/Percentage', percentage=self.teamCost), align=uiconst.CENTERLEFT, left=6)
        col.hint = GetByLabel('UI/Industry/SalaryHint')
        col.OnMouseEnter = self.OnMouseEnter
        col.OnMouseExit = self.OnMouseExit

    def AddColumnTeam(self):
        col = self.AddColumnContainer()
        iconCont = Container(parent=col, width=32, height=32, align=uiconst.CENTERLEFT, left=6)
        Sprite(name='teamTypeSprite', parent=iconCont, texturePath=TEAM_TYPE_ICONS_SMALL[self.team.specialization.specializationID], align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        teamName = self.teamName
        EveLabelMedium(text=teamName, parent=col, align=uiconst.CENTERLEFT, left=40, lineSpacing=-0.1)

    def GetJumpsTo(self):
        return sm.GetService('clientPathfinderService').GetJumpCountFromCurrent(self.team.solarSystemID)

    def GetSecurityLabel(self, solarSystemID):
        sec, col = FmtSystemSecStatus(sm.GetService('map').GetSecurityStatus(solarSystemID), 1)
        col.a = 1.0
        color = StrFromColor(col)
        return '<color=%s>%s</color>' % (color, sec)

    def AddColumnWorkers(self):
        col = self.AddColumnContainer()
        row1 = Container(parent=col, height=18, align=uiconst.TOTOP)
        row2 = Container(parent=col, height=18, align=uiconst.TOTOP)
        workerList = self.ArrangeWorkers()
        for i, worker in enumerate(workerList):
            if i > 1:
                parCont = row2
                isTopRow = False
            else:
                parCont = row1
                isTopRow = True
            if i in (0, 2):
                alignMode = uiconst.TOLEFT_PROP
            else:
                alignMode = uiconst.TORIGHT_PROP
            workerCont = WorkerContainer(parent=parCont, jobData=self.node.jobData, worker=worker, align=alignMode, width=0.47, isTopRow=isTopRow)
            workerCont.OnMouseEnter = self.OnMouseEnter
            workerCont.OnMouseExit = self.OnMouseExit
            workerCont.OnClick = self.OnClick
            self.workerConts.append(workerCont)

    def ArrangeWorkers(self):
        workerList = []
        for worker in self.team.teamMembers:
            if self.node.jobData:
                groupID = cfg.invtypes.Get(self.node.jobData.product.typeID).groupID
                if groupID in SPECIALIZATION_GROUPS[worker.specializationID]:
                    workerList.insert(0, worker)
                    continue
            workerList.append(worker)

        return workerList

    def OnColumnResize(self, newCols):
        BaseListEntryCustomColumns.OnColumnResize(self, newCols)
        magicNumber = 80
        fadeWidth = newCols[5] / 2 - magicNumber
        for workerCont in self.workerConts:
            workerCont.FadeText(fadeWidth)

    def SetTimeLeft(self, *args):
        while self and not self.destroyed:
            timeNow = blue.os.GetWallclockTimeNow()
            timeUntil = self.expiryTime - timeNow
            if timeUntil > 0:
                self.timeLeft.text = FmtDate(timeUntil, 'ss')
            else:
                self.node.scroll.RemoveNodes([self.node])
            blue.pyos.synchro.SleepWallclock(1000)

    @staticmethod
    def GetDynamicHeight(node, width):
        return 38

    def GMExpireAuction(self, auctionID):
        sm.RemoteSvc('teamHandler').GMExpireAuction(auctionID)
        self.node.scroll.RemoveNodes([self.node])

    def GMRetireTeam(self, teamID):
        sm.RemoteSvc('teamHandler').GMRetireTeam(teamID)
        self.node.scroll.RemoveNodes([self.node])

    def ShowTeamID(self, *args):
        eve.Message('CustomInfo', {'info': 'teamID: %s' % self.team.teamID})

    def ShowBids(self):
        lines = []
        for solarSystemID, systemBids in self.GetBids().iteritems():
            lines.append('%s (%s), TOTAL: %s: ' % (cfg.evelocations.Get(solarSystemID).name, solarSystemID, sum((bid for bid in systemBids.itervalues()))))
            for characterID, bid in sorted(systemBids.iteritems(), itemgetter(1)):
                lines.append('-- %s (%s): %s' % (cfg.eveowners.Get(characterID).name, characterID, FmtISK(bid)))

        eve.Message('CustomInfo', {'info': '<br/>'.join(lines)})

    def GetMenu(self):
        menu = []
        menu += sm.GetService('menu').CelestialMenu(itemID=self.team.solarSystemID)
        if session.role & ROLE_QA == ROLE_QA:
            menu += self.GetQAMenu()
            menu += [['QA: Get teamID', self.ShowTeamID, []]]
        return menu

    def GetQAMenu(self):
        raise NotImplemented()


class TeamEntry(BaseTeamEntry):
    default_name = 'TeamEntry'

    @staticmethod
    def GetDefaultColumnWidth():
        return {GetByLabel('UI/Industry/Team'): 160,
         GetByLabel('UI/Common/LocationTypes/System'): 80,
         GetByLabel('UI/Common/Jumps'): 50,
         GetByLabel('UI/Common/Security'): 55,
         GetByLabel('UI/Industry/Activity'): 32,
         GetByLabel('UI/Industry/Bonuses'): 310,
         GetByLabel('UI/Industry/Salary'): 50,
         GetByLabel('UI/Industry/TeamRetires'): 110}

    @staticmethod
    def GetHeaders():
        return (GetByLabel('UI/Industry/Team'),
         GetByLabel('UI/Common/LocationTypes/System'),
         GetByLabel('UI/Common/Jumps'),
         GetByLabel('UI/Common/Security'),
         GetByLabel('UI/Industry/Activity'),
         GetByLabel('UI/Industry/Bonuses'),
         GetByLabel('UI/Industry/Salary'),
         GetByLabel('UI/Industry/TeamRetires'))

    @staticmethod
    def GetColumnSortValues(teamData, teamName, bonusSum, expiryTime, teamCost):
        return (teamName,
         cfg.evelocations.Get(teamData.team.solarSystemID).name,
         sm.GetService('clientPathfinderService').GetJumpCountFromCurrent(teamData.team.solarSystemID),
         sm.GetService('map').GetSecurityStatus(teamData.team.solarSystemID),
         teamData.team.activity,
         bonusSum,
         teamCost,
         expiryTime)

    def GetQAMenu(self):
        return [['QA: Retire Team', self.GMRetireTeam, [self.node.teamData.team.teamID]]]


class AuctionEntry(BaseTeamEntry):
    default_name = 'AuctionEntry'

    def ApplyAttributes(self, attributes):
        BaseTeamEntry.ApplyAttributes(self, attributes)
        self.auctionCost = self.node.auctionCost
        self.AddColumnAuction()
        self.pathFinder = sm.GetService('clientPathfinderService')
        self.teamHandlerClient = sm.GetService('industryTeamSvc')
        self.minAmount = 0

    def AddColumnAuction(self):
        col = self.AddColumnContainer()
        col.OnMouseEnter = self.OnMouseEnter
        col.OnMouseExit = self.OnMouseExit
        col.OnClick = self.OnClick
        col.state = uiconst.UI_NORMAL
        col.GetMenu = self.GetMenu
        col.LoadTooltipPanel = self.LoadAuctionHintPanel
        bidCont = Container(parent=col, align=uiconst.TORIGHT, width=50)
        costCont = Container(parent=col, align=uiconst.TOALL, clipChildren=True)
        costText = FmtISK(self.auctionCost, 0)
        self.costLabel = EveLabelMedium(text=costText, parent=costCont, align=uiconst.CENTERLEFT, left=6)
        self.bidUtilMenu = UtilMenu(menuAlign=uiconst.TOPRIGHT, align=uiconst.CENTERLEFT, parent=bidCont, GetUtilMenu=self.BidOnTeamMenu, texturePath='res:/UI/Texture/Icons/73_16_50.png', left=2, label=GetByLabel('UI/Industry/Bid'))
        bidCont.width = self.bidUtilMenu.width + 10
        self.bidUtilMenu.hint = GetByLabel('UI/Industry/BidBtnHint')

    def BidOnTeamMenu(self, menuParent):
        cont = menuParent.AddContainer(align=uiconst.TOTOP, padding=const.defaultPadding)
        cont.GetEntryWidth = lambda mc = cont: 300
        topCont = Container(parent=cont, height=20, align=uiconst.TOTOP)
        self.searchCont = Container(parent=topCont)
        self.resultCont = Container(parent=topCont)
        self.resultCont.display = False
        self.systemLabel = EveLabelMediumBold(parent=self.resultCont, left=2, top=4)
        self.searchEdit = SinglelineEdit(parent=self.searchCont, align=uiconst.TOALL, hinttext=GetByLabel('UI/Industry/SearchForSystem'), width=0, top=0)
        self.searchEdit.OnReturn = lambda *args: self.SearchForLocation(self.searchEdit, *args)
        self.searchEdit.OnTab = lambda *args: self.SearchForLocation(self.searchEdit, *args)
        self.searchEdit.displayHistory = False
        ButtonIcon(parent=self.resultCont, align=uiconst.CENTERRIGHT, width=16, iconSize=16, texturePath='res:/UI/Texture/Icons/73_16_210.png', hint=GetByLabel('UI/Inventory/Clear'), func=self.ClearSystemSearch)
        self.resultScroll = Scroll(parent=cont, id='ResultScroll', align=uiconst.TOTOP, height=70)
        self.resultScroll.display = False
        Container(parent=cont, height=8, align=uiconst.TOTOP)
        self.bidHint = EveLabelMedium(parent=cont, align=uiconst.TOTOP, padding=(2, 4, 2, 4))
        bottomCont = Container(parent=cont, height=20, align=uiconst.TOTOP, padBottom=4)
        self.bidButton = Button(parent=bottomCont, label=GetByLabel('UI/Industry/Bid'), align=uiconst.TORIGHT, func=self.BidOnTeam)
        self.bidButton.OnMouseHover = self.BidHint
        self.bidButton.Disable()
        self.bidAmountEdit = SinglelineEdit(parent=bottomCont, align=uiconst.TOALL, width=0, floats=[0, 100000000000L, 0], padRight=4, top=0, hinttext='Enter amount')
        self.bidAmountEdit.OnReturn = self.BidOnTeam

    def BidHint(self):
        if self.bidButton.disabled:
            if self.searchEdit.GetValue():
                self.bidButton.hint = GetByLabel('UI/Industry/BidBtnSearchHint')
        else:
            self.bidButton.hint = ''

    def BidOnTeam(self, *args):
        if not self.searchedSystem:
            return
        if self.IsUnreachable():
            self.bidAmountEdit.SetValue('')
            self.bidHint.text = GetByLabel('UI/Industry/UnreachableSystem')
            return
        amount = self.bidAmountEdit.GetValue()
        if not self.HasSolarSystemBidForAuctionID() and amount <= self.minAmount:
            self.bidAmountEdit.SetValue('')
            self.bidHint.text = GetByLabel('UI/Industry/TeamBidTooLow', minAmount=FmtAmt(self.minAmount, showFraction=0))
            return
        self.teamHandlerClient.BidOnTeam(self.team.teamID, self.searchedSystem, amount)
        self.costLabel.text = self.GetForcedAuctionCost()
        self.bidUtilMenu.CloseMenu()

    def SearchForLocation(self, edit, *args):
        searchText = edit.GetValue()
        if not searchText or searchText == '':
            return
        groupIDList = [const.searchResultSolarSystem, const.searchResultWormHoles]
        searchResult = QuickSearch(searchText.strip(), groupIDList)
        noOfResults = len(searchResult)
        if noOfResults == 1:
            self.ConfirmSystem(searchResult[0])
        elif noOfResults:
            self.resultScroll.display = True
            scrollList = self.GetScrollList(searchResult)
            self.resultScroll.LoadContent(contentList=scrollList)
        else:
            edit.SetHintText(GetByLabel('UI/Station/BountyOffice/NoOneFound'))

    def LoadAuctionHintPanel(self, tooltipPanel, *args):
        tooltipPanel.LoadGeneric3ColumnTemplate()
        tooltipPanel.AddLabelLarge(text=GetByLabel('UI/Industry/SystemBidList'), colSpan=tooltipPanel.columns, align=uiconst.CENTER)
        tooltipPanel.AddSpacer(colSpan=tooltipPanel.columns, width=0, height=2)
        topSystems = self.GetTopSystems()
        if topSystems:
            for i, (amount, solarSystemID) in enumerate(topSystems):
                if i > 2:
                    break
                systemName = self.FormatSystemName(solarSystemID)
                systemLabel = '%i %s' % (i + 1, systemName)
                tooltipPanel.AddLabelSmall(text=systemLabel, colSpan=1)
                tooltipPanel.AddSpacer(width=10, height=0)
                tooltipPanel.AddLabelSmall(text=FmtISK(amount, 0), colSpan=1, align=uiconst.TORIGHT)

        myBids = self.GetMyBids()
        if myBids:
            tooltipPanel.AddSpacer(colSpan=tooltipPanel.columns, width=0, height=6)
            tooltipPanel.AddLabelLarge(text=GetByLabel('UI/Industry/MyBidList'), colSpan=tooltipPanel.columns, align=uiconst.CENTER)
            tooltipPanel.AddSpacer(colSpan=tooltipPanel.columns, width=0, height=2)
            for solarSystemID, amount in myBids:
                systemName = self.FormatSystemName(solarSystemID)
                tooltipPanel.AddLabelSmall(text=systemName, colSpan=1)
                tooltipPanel.AddSpacer(width=10, height=0)
                tooltipPanel.AddLabelSmall(text=FmtISK(amount, 0), colSpan=1, align=uiconst.TORIGHT)

    def GetTopSystems(self):
        bids = self.GetBids()
        return bids.GetRankedBids()

    def GetMyBids(self):
        bids = self.GetBids()
        myBids = GetMyBidsBySolarSystem(session.charid, bids)
        if myBids:
            return sorted(myBids.iteritems(), key=itemgetter(1), reverse=True)

    def GetScrollList(self, results):
        scrollList = []
        for solarSystemID in results:
            data = util.KeyVal()
            data.label = self.FormatSystemName(solarSystemID)
            data.OnDblClick = self.DblClickEntry
            data.solarSystemID = solarSystemID
            entry = listentry.Get('Generic', data)
            scrollList.append(entry)

        return scrollList

    def FormatSystemName(self, solarSystemID):
        systemName = cfg.evelocations.Get(solarSystemID).name
        secStatus = self.GetSecurityLabel(solarSystemID)
        return '%s %s' % (systemName, secStatus)

    def DblClickEntry(self, entry, *args):
        solarSystemID = entry.sr.node.solarSystemID
        if solarSystemID:
            self.ConfirmSystem(solarSystemID)

    def ConfirmSystem(self, solarSystemID):
        self.resultScroll.display = False
        self.searchCont.display = False
        self.resultCont.display = True
        self.searchEdit.SetValue('')
        self.searchedSystem = solarSystemID
        self.systemLabel.text = self.FormatSystemName(solarSystemID)
        if self.IsUnreachable():
            self.bidHint.text = GetByLabel('UI/Industry/UnreachableSystem')
        elif not self.HasSolarSystemBidForAuctionID():
            self.minAmount = GetDistanceCost(self.pathFinder, self.team.solarSystemID, solarSystemID)
            self.bidHint.text = GetByLabel('UI/Industry/TeamMinBid', minAmount=FmtAmt(self.minAmount, showFraction=0))
        self.bidButton.Enable()
        uicore.registry.SetFocus(self.bidAmountEdit)

    def ClearSystemSearch(self, *args):
        self.searchedSystem = None
        self.resultCont.display = False
        self.systemLabel.text = ''
        self.bidHint.text = ''
        self.bidHint.height = 0
        self.searchCont.display = True
        self.bidButton.Disable()

    def GetForcedAuctionCost(self):
        return FmtISK(GetHighestBid(self.GetBids()), 0)

    def HasSolarSystemBidForAuctionID(self):
        return self.teamHandlerClient.HasSolarSystemBidForAuctionID(self.team.teamID, self.searchedSystem)

    def IsUnreachable(self):
        return bool(not util.IsWormholeSystem(self.searchedSystem) and self.pathFinder.GetJumpCount(self.team.solarSystemID, self.searchedSystem) > 1000)

    @staticmethod
    def GetDefaultColumnWidth():
        return {GetByLabel('UI/Industry/Team'): 160,
         GetByLabel('UI/Common/LocationTypes/System'): 80,
         GetByLabel('UI/Common/Jumps'): 50,
         GetByLabel('UI/Common/Security'): 55,
         GetByLabel('UI/Industry/Bonuses'): 310,
         GetByLabel('UI/Industry/Salary'): 50,
         GetByLabel('UI/Industry/AuctionEnds'): 110,
         GetByLabel('UI/Industry/Auction'): 110}

    @staticmethod
    def GetHeaders():
        return (GetByLabel('UI/Industry/Team'),
         GetByLabel('UI/Common/LocationTypes/System'),
         GetByLabel('UI/Common/Jumps'),
         GetByLabel('UI/Common/Security'),
         GetByLabel('UI/Industry/Activity'),
         GetByLabel('UI/Industry/Bonuses'),
         GetByLabel('UI/Industry/Salary'),
         GetByLabel('UI/Industry/AuctionEnds'),
         GetByLabel('UI/Industry/Auction'))

    @staticmethod
    def GetColumnSortValues(teamData, teamName, bonusSum, expiryTime, teamCost, auctionCost):
        return (teamName,
         cfg.evelocations.Get(teamData.team.solarSystemID).name,
         sm.GetService('clientPathfinderService').GetJumpCountFromCurrent(teamData.team.solarSystemID),
         sm.GetService('map').GetSecurityStatus(teamData.team.solarSystemID),
         teamData.team.activity,
         bonusSum,
         teamCost,
         expiryTime,
         auctionCost)

    def GetBids(self):
        return self.teamHandlerClient.GetBids(self.team.teamID)

    def GetQAMenu(self):
        return [['QA: Expire Auction', self.GMExpireAuction, [self.team.teamID]], ['QA: Print Bids', self.ShowBids, []], ['QA: Set Expiry time', self.SetExpiryTime]]

    def SetExpiryTime(self):
        ret = uiutil.NamePopup(caption='Set Expiry Time', label='Type in Expiry Time', setvalue=util.FmtDate(self.node.expiryTime))
        if ret is None:
            return
        newTime = util.ParseDateTime(ret)
        self.teamHandlerClient.GMSetAuctionExpiryTime(self.team.teamID, newTime)


class WorkerContainer(Container):
    default_name = 'WorkerContainer'

    def ShouldDim(self, worker, jobData):
        if not jobData:
            return False
        groupID = cfg.invtypes.Get(jobData.blueprint.productTypeID).groupID
        return groupID not in SPECIALIZATION_GROUPS[worker.specializationID]

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        worker = attributes.worker
        self.state = uiconst.UI_NORMAL
        rightCont = Container(name='bonusCont', parent=self, align=uiconst.TORIGHT, width=90)
        self.leftCont = Container(name='textCont', parent=self, align=uiconst.TOALL)
        self.opacity = 0.15 if self.ShouldDim(worker, attributes.jobData) else 1.0
        workerName = GetByLabel(SPE_LABELS[worker.specializationID])
        bonus, quality = worker.GetBonusType()
        if attributes.isTopRow:
            top = 4
        else:
            top = 2
        self.workerName = EveLabelSmall(parent=self.leftCont, text=workerName, left=6, top=top)
        EveLabelSmall(parent=rightCont, text=GetByLabel('UI/Common/Formatting/PercentageDecimal', percentage=quality), align=uiconst.TORIGHT_NOPUSH, top=top, left=4)
        bonusIcon = Icon(parent=rightCont, width=16, height=16, align=uiconst.TORIGHT, left=38, state=uiconst.UI_PICKCHILDREN, opacity=0.6)
        groupNames = GetGroupNamesFromSpeciality(worker.specializationID)
        self.hint = GetByLabel('UI/Industry/workerHint', groupNames=groupNames)
        if bonus == 'ME':
            bonusIcon.LoadIcon('res:/UI/Texture/Classes/Industry/iconME.png')
            bonusIcon.width = 17
        elif bonus == 'TE':
            bonusIcon.LoadIcon('res:/UI/Texture/Classes/Industry/iconTE.png')
            bonusIcon.width = 16

    def FadeText(self, fadeWidth):
        self.workerName.SetRightAlphaFade(fadeWidth, 25)
