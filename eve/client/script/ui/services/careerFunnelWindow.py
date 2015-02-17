#Embedded file name: eve/client/script/ui/services\careerFunnelWindow.py
from carbonui import const as uiconst
from eve.client.script.ui.control import entries as listentry
from eve.client.script.ui.services.careerAgentEntry import CareerAgentEntry
from eve.common.lib import appConst as const
import localization
import uicontrols

class CareerFunnelWindow(uicontrols.Window):
    __guid__ = 'form.CareerFunnelWindow'
    default_windowID = 'careerFunnel'
    default_iconNum = 'res:/ui/Texture/WindowIcons/agent.png'
    notifiers = None

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.currWidth = 600
        self.inited = False
        self.contentItemList = []
        self.SetTopparentHeight(0)
        self.MakeUnstackable()
        self.width = self.currWidth
        self.left = 0
        leftpush, rightpush = uicore.layer.sidePanels.GetSideOffset()
        self.left += leftpush
        self.top = 0
        self.SetCaption(localization.GetByLabel('UI/Tutorial/CareerFunnel'))
        self.height = 500
        self.SetMinSize([self.currWidth, self.height])
        self.headerText = uicontrols.EveCaptionMedium(text=localization.GetByLabel('UI/Tutorial/CareerFunnelHeader'), parent=self.sr.main, align=uiconst.TOTOP, padding=const.defaultPadding * 2, state=uiconst.UI_DISABLED)
        self.textObject = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Tutorial/CareerFunnelIntro'), parent=self.sr.main, padLeft=const.defaultPadding * 2, padRight=const.defaultPadding * 2, padBottom=const.defaultPadding, state=uiconst.UI_DISABLED, align=uiconst.TOTOP)
        self.sr.contentList = uicontrols.Scroll(parent=self.sr.main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        noContentHint = localization.GetByLabel('UI/Generic/Unknown')
        if not len(self.contentItemList):
            careerAgents = self.GetAgents()
            agentNodes = None
            pathfinder = sm.GetService('clientPathfinderService')
            for career in careerAgents:
                agentToUse = None
                jumps = 999
                for agentID in careerAgents[career]['agent']:
                    agent = careerAgents[career]['agent'][agentID]
                    station = careerAgents[career]['station'][agentID]
                    jumpsToAgent = pathfinder.GetJumpCountFromCurrent(station.solarSystemID)
                    if jumpsToAgent < jumps:
                        agentToUse = agentID
                        jumps = jumpsToAgent

                if agentToUse:
                    data = {'agent': careerAgents[career]['agent'][agentToUse],
                     'career': career,
                     'agentStation': careerAgents[career]['station'][agentToUse]}
                    self.contentItemList.append(listentry.GetFromClass(CareerAgentEntry, data))
                else:
                    noContentHint = localization.GetByLabel('UI/Generic/NoRouteCanBeFound')

        self.sr.contentList.Startup()
        self.sr.contentList.ShowHint()
        self.sr.contentList.Load(None, self.contentItemList, headers=None, noContentHint=noContentHint)
        height = self.headerText.textheight + self.headerText.padTop + self.headerText.padBottom
        height += self.textObject.textheight + self.textObject.padTop + self.textObject.padBottom
        height += 440
        self.height = height
        self.inited = True

    def GetAgents(self):
        return sm.GetService('tutorial').GetCareerFunnelAgents()

    def RefreshEntries(self):
        for content in self.contentItemList:
            if content.panel is not None:
                content.panel.Load(content)

        self.sr.contentList.Load(None, self.contentItemList, headers=None, noContentHint=localization.GetByLabel('UI/Generic/Unknown'))

    def CloseByUser(self, *args):
        if eve.Message('CareerFunnelClose', {}, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            uicontrols.WindowCore.CloseByUser(self)
