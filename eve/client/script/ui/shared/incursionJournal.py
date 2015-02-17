#Embedded file name: eve/client/script/ui/shared\incursionJournal.py
import carbonui.const as uiconst
from eve.client.script.ui.control.themeColored import LineThemeColored
import uicontrols
import uicls
import uiprimitives
import uiutil
from mapcommon import STARMODE_INCURSION, STARMODE_FRIENDS_CORP
import uix
import util
import talecommon as taleCommon
import localization
MIDDLECONTAINER_WIDTH = 200
MARGIN = 8

class IncursionTab:
    GlobalReport, Encounters, LPLog = range(3)


class GlobalIncursionReportEntry(uicontrols.SE_BaseClassCore):
    __guid__ = 'listentry.GlobalIncursionReportEntry'
    MARGIN = 8
    TEXT_OFFSET = 84
    BUTTON_OFFSET = 295

    def ApplyAttributes(self, attributes):
        uicontrols.SE_BaseClassCore.ApplyAttributes(self, attributes)
        self.iconsize = iconsize = 44
        LineThemeColored(parent=self, align=uiconst.TOBOTTOM)
        self.factionParent = uiprimitives.Container(name='factionParent', parent=self, align=uiconst.TOLEFT, pos=(0, 0, 64, 64), padding=MARGIN)
        middleCont = uiprimitives.Container(parent=self, name='middleContainer', width=MIDDLECONTAINER_WIDTH, align=uiconst.TOLEFT, padTop=MARGIN, clipChildren=True)
        self.constellationLabel = BigReportLabel(name='constellationName', parent=middleCont, fontsize=20, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        self.statusText = SmallReportLabel(parent=middleCont, align=uiconst.TOTOP, uppercase=True)
        SmallReportLabel(name='systemInfluence', parent=middleCont, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Incursion/Common/HUDInfluenceTitle'))
        self.statusBar = uicls.SystemInfluenceBar(parent=middleCont, pos=(0, 0, 200, 10), align=uiconst.TOTOP, padding=(0, 4, 0, 4))
        self.stagingText = SmallReportLabel(parent=middleCont, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        self.bossIcon = uicls.IncursionBossIcon(parent=middleCont, left=3, top=3, align=uiconst.TOPRIGHT, idx=0)
        btn = uix.GetBigButton(iconsize, self, left=self.BUTTON_OFFSET, top=MARGIN, align=uiconst.BOTTOMLEFT)
        btn.hint = localization.GetByLabel('UI/Incursion/Journal/ShowActiveCorpMembersInMap')
        btn.sr.icon.LoadIcon('res:/ui/Texture/WindowIcons/corpmap.png', ignoreSize=True)
        self.corpMapButton = btn
        btn = uix.GetBigButton(iconsize, self, left=self.BUTTON_OFFSET + 50, top=MARGIN, align=uiconst.BOTTOMLEFT)
        btn.hint = localization.GetByLabel('UI/Incursion/Journal/ShowOnStarMap')
        btn.sr.icon.LoadIcon('res:/ui/Texture/WindowIcons/map.png', ignoreSize=True)
        self.mapButton = btn
        btn = uix.GetBigButton(iconsize, self, left=self.BUTTON_OFFSET + 100, top=MARGIN, align=uiconst.BOTTOMLEFT)
        btn.hint = localization.GetByLabel('UI/Incursion/Journal/StagingAsAutopilotDestination')
        btn.sr.icon.LoadIcon('res:/ui/Texture/WindowIcons/ships.png', ignoreSize=True)
        self.autopilotButton = btn
        btn = uix.GetBigButton(iconsize, self, left=self.BUTTON_OFFSET, top=MARGIN)
        btn.hint = localization.GetByLabel('UI/Incursion/Journal/ViewLoyaltyPointLog')
        btn.sr.icon.LoadIcon('res:/ui/Texture/WindowIcons/lpstore.png', ignoreSize=True)
        self.lpButton = btn
        self.loyaltyPoints = ReportNumber(name='loyaltyPoints', parent=self, pos=(self.BUTTON_OFFSET + 50,
         MARGIN,
         105,
         iconsize), number=0, hint=localization.GetByLabel('UI/Incursion/Journal/LoyaltyPointsWin'), padding=(4, 4, 4, 4))

    def Load(self, data):
        iconsize = 48
        self.factionParent.Flush()
        if data.factionID:
            owner = cfg.eveowners.Get(data.factionID)
            uiutil.GetLogoIcon(parent=self.factionParent, align=uiconst.RELATIVE, size=64, itemID=data.factionID, ignoreSize=True, hint=localization.GetByLabel('UI/Incursion/Journal/FactionStagingRuler', faction=owner.ownerName))
        else:
            uicontrols.Icon(parent=self.factionParent, size=64, icon='ui_94_64_16', ignoreSize=True, hint=localization.GetByLabel('UI/Incursion/Journal/StagingSystemUnclaimed'), align=uiconst.RELATIVE)
        rowHeader = localization.GetByLabel('UI/Incursion/Journal/ReportRowHeader', constellation=data.constellationID, constellationInfo=('showinfo', const.typeConstellation, data.constellationID))
        self.constellationLabel.SetText(rowHeader)
        incursionStateMessages = [localization.GetByLabel('UI/Incursion/Journal/Withdrawing'), localization.GetByLabel('UI/Incursion/Journal/Mobilizing'), localization.GetByLabel('UI/Incursion/Journal/Established')]
        self.statusText.SetText(incursionStateMessages[data.state])
        if data.jumps is not None:
            distanceAwayText = localization.GetByLabel('UI/Incursion/Journal/ReportRowNumJumps', jumps=data.jumps)
        else:
            distanceAwayText = localization.GetByLabel('UI/Incursion/Journal/ReportRowSystemUnreachable')
        bodyText = localization.GetByLabel('UI/Incursion/Journal/ReportRowBody', color='<color=' + sm.GetService('map').GetSystemColorString(data.stagingSolarSystemID) + '>', security=data.security, securityColor=sm.GetService('map').GetSystemColorString(data.stagingSolarSystemID), system=data.stagingSolarSystemID, systemInfo=('showinfo', const.typeSolarSystem, data.stagingSolarSystemID), distanceAway=distanceAwayText)
        self.stagingText.SetText(bodyText)
        self.statusBar.SetInfluence(taleCommon.CalculateDecayedInfluence(data.influenceData), None, animate=False)
        self.bossIcon.SetBossSpawned(data.hasBoss)
        self.corpMapButton.OnClick = lambda : sm.GetService('viewState').ActivateView('starmap', interestID=data.constellationID, starColorMode=STARMODE_FRIENDS_CORP)
        self.mapButton.OnClick = lambda : sm.GetService('viewState').ActivateView('starmap', interestID=data.constellationID, starColorMode=STARMODE_INCURSION)
        self.autopilotButton.OnClick = lambda : sm.GetService('starmap').SetWaypoint(data.stagingSolarSystemID, clearOtherWaypoints=True)
        self.lpButton.OnClick = lambda : sm.GetService('journal').ShowIncursionTab(flag=IncursionTab.LPLog, taleID=data.taleID, constellationID=data.constellationID)
        self.loyaltyPoints.number.SetText(localization.GetByLabel('UI/Incursion/Journal/NumberLoyaltyPointsAcronym', points=util.FmtAmt(data.loyaltyPoints)))

    def GetDynamicHeight(node, width):
        rowHeader = localization.GetByLabel('UI/Incursion/Journal/ReportRowHeader', constellation=node.constellationID, constellationInfo=('showinfo', const.typeConstellation, node.constellationID))
        headerWidth, headerHeight = BigReportLabel.MeasureTextSize(rowHeader, fontsize=20, width=MIDDLECONTAINER_WIDTH)
        incursionStateMessages = [localization.GetByLabel('UI/Incursion/Journal/Withdrawing'), localization.GetByLabel('UI/Incursion/Journal/Mobilizing'), localization.GetByLabel('UI/Incursion/Journal/Established')]
        statusWidth, statusHeight = SmallReportLabel.MeasureTextSize(incursionStateMessages[node.state], width=MIDDLECONTAINER_WIDTH)
        influenceWidth, influenceHeight = SmallReportLabel.MeasureTextSize(localization.GetByLabel('UI/Incursion/Common/HUDInfluenceTitle'), width=MIDDLECONTAINER_WIDTH)
        statusBar = 18
        if node.jumps is not None:
            distanceAwayText = localization.GetByLabel('UI/Incursion/Journal/ReportRowNumJumps', jumps=node.jumps)
        else:
            distanceAwayText = localization.GetByLabel('UI/Incursion/Journal/ReportRowSystemUnreachable')
        bodyText = localization.GetByLabel('UI/Incursion/Journal/ReportRowBody', color='<color=' + sm.GetService('map').GetSystemColorString(node.stagingSolarSystemID) + '>', security=node.security, securityColor=sm.GetService('map').GetSystemColorString(node.stagingSolarSystemID), system=node.stagingSolarSystemID, systemInfo=('showinfo', const.typeSolarSystem, node.stagingSolarSystemID), distanceAway=distanceAwayText)
        bodyWidth, bodyHeight = SmallReportLabel.MeasureTextSize(bodyText, width=MIDDLECONTAINER_WIDTH)
        return max(114, headerHeight + statusHeight + influenceHeight + statusBar + bodyHeight + MARGIN * 2)


class ReportNumber(uiprimitives.Container):
    __guid__ = 'incursion.ReportNumber'
    default_align = uiconst.RELATIVE
    default_clipChildren = True

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        number = attributes.Get('number', 0)
        self.number = BigReportLabel(name='bignumber', parent=self, align=uiconst.CENTERRIGHT, text=str(number), fontsize=18, hint=attributes.Get('hint', None))


class SmallReportLabel(uicontrols.Label):
    default_align = uiconst.RELATIVE
    default_fontsize = 13


class BigReportLabel(uicontrols.Label):
    __guid__ = 'incursion.ReportLabel'
    default_fontsize = 20
    default_letterspace = 0
    default_align = uiconst.RELATIVE
    default_maxLines = None


exports = {'incursion.IncursionTab': IncursionTab}
