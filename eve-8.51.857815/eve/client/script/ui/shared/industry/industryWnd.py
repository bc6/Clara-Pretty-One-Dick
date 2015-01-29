#Embedded file name: eve/client/script/ui/shared/industry\industryWnd.py
from math import pi
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from eve.client.script.ui.control.buttons import ButtonIcon
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.control.historyBuffer import HistoryBuffer
from eve.client.script.ui.shared.industry.views.baseView import BaseView
import industry
from industry.const import ACTIVITIES
from localization import GetByLabel
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from eve.client.script.ui.shared.industry.jobsStrip import JobsStrip
from eve.client.script.ui.control.tabGroup import TabGroup
from eve.client.script.ui.shared.industry.browserBlueprints import BrowserBlueprints
from eve.client.script.ui.shared.industry.browserJobs import BrowserJobs
from eve.client.script.ui.shared.industry.browserFacilities import BrowserFacilities
from eve.common.script.util import industryCommon
import localization
import telemetry
import uthread
import blue
FIXED_HEIGHT = 512
VIEW_HEIGHT = 418
TOP_HEIGHT = 465
TAB_BLUEPRINTS = 0
TAB_FACILITIES = 1
TAB_JOBS = 2

class Industry(Window):
    __guid__ = 'form.Industry'
    __notifyevents__ = ['OnIndustryLeftOrRightKey',
     'OnIndustryDropData',
     'OnIndustryRemoveBlueprint',
     'OnIndustryJob',
     'OnBlueprintReload',
     'OnFacilityReload',
     'OnBlueprintEntryDblClicked']
    default_captionLabelPath = 'UI/Industry/Industry'
    default_descriptionLabelPath = 'UI/Industry/IndustryTooltip'
    default_caption = localization.GetByLabel('UI/Industry/Industry')
    default_windowID = 'industryWnd'
    default_iconNum = 'res:/UI/Texture/WindowIcons/Industry.png'
    default_height = 800
    default_topParentHeight = 0
    default_isStackable = False
    default_minSize = (1004, 650)

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        blueprintID = attributes.Get('blueprintID', None)
        blueprintTypeID = attributes.Get('blueprintTypeID', None)
        bpData = attributes.Get('bpData', None)
        self.history = HistoryBuffer()
        self.jobData = None
        self.pendingBlueprint = None
        self.loadBlueprintThread = None
        self.topCont = Container(name='topCont', parent=self.sr.main, align=uiconst.TOTOP, height=TOP_HEIGHT, clipChildren=True)
        self.currView = BaseView(parent=self.topCont, align=uiconst.TOTOP, height=VIEW_HEIGHT)
        self.jobsStrip = JobsStrip(parent=self.topCont, align=uiconst.TOTOP, padding=(5, -1, 7, 2), callback=self.OnBlueprintsSelected)
        self.bottomCont = Container(name='bottomCont', parent=self.sr.main, controller=self, height=0.4, padding=(4, 0, 4, 0), callback=self.OnBlueprintsSelected)
        cont = ContainerAutoSize(name='historyArrowCont', parent=self.sr.main, align=uiconst.TOPRIGHT, height=16, left=3, top=1)
        self.expandViewBtn = ButtonIcon(name='expandViewBtn', parent=cont, align=uiconst.TORIGHT, width=16, iconSize=7, texturePath='res:/UI/Texture/classes/Neocom/arrowDown.png', func=self.OnExpandViewBtn)
        self.goForwardBtn = ButtonIcon(name='goForwardBtn', parent=cont, align=uiconst.TORIGHT, width=16, iconSize=16, padRight=5, texturePath='res:/UI/Texture/icons/38_16_224.png', func=self.OnForward, hint=localization.GetByLabel('UI/Control/EveWindow/Next'))
        self.goBackBtn = ButtonIcon(name='goBackBtn', parent=cont, align=uiconst.TORIGHT, width=16, iconSize=16, texturePath='res:/UI/Texture/icons/38_16_223.png', func=self.OnBack, hint=localization.GetByLabel('UI/Control/EveWindow/Previous'))
        self.browserCont = Container(name='browserCont', parent=self.bottomCont, padding=(0, 2, 0, 2))
        self.browserBlueprints = BrowserBlueprints(parent=self.browserCont, callback=self.OnBlueprintsSelected)
        self.browserFacilities = BrowserFacilities(parent=self.browserCont, callback=self.OnFacilitySelected)
        self.browserJobs = BrowserJobs(parent=self.browserCont, callback=self.OnJobSelected)
        tabs = ((localization.GetByLabel('UI/Industry/Blueprints'),
          self.browserBlueprints,
          None,
          'blueprints',
          None,
          GetByLabel('UI/Industry/TabBlueprints')), (localization.GetByLabel('UI/Industry/Facilities'),
          self.browserFacilities,
          None,
          'facilities',
          None,
          GetByLabel('UI/Industry/TabFacilities')), (localization.GetByLabel('UI/Industry/Jobs'),
          self.browserJobs,
          None,
          'jobs',
          None,
          GetByLabel('UI/Industry/TabJobs')))
        self.tabs = TabGroup(parent=self.browserCont, tabs=tabs, height=26, labelPadding=12, idx=0, padLeft=0, groupID='IndustryWindowBrowsers', autoselecttab=not self.IsBrowserCollapsed())
        self.expandBottomBtn = ButtonIcon(name='expandBottomBtn', parent=self.bottomCont, align=uiconst.TOPRIGHT, pos=(2, -3, 16, 16), iconSize=7, texturePath='res:/UI/Texture/classes/Neocom/arrowDown.png', func=self.OnExpandBottomBtn)
        if blueprintID or blueprintTypeID:
            self.ShowBlueprint(blueprintID, blueprintTypeID, bpData=bpData)
        if self.IsViewCollapsed():
            self.CollapseView(animate=False)
        else:
            self.expandViewBtn.SetRotation(-pi)
        if self.IsBrowserCollapsed():
            self.CollapseBrowser(animate=False)
        else:
            self.expandBottomBtn.SetRotation(-pi)
        sm.GetService('audio').SendUIEvent('ind_windowOpened')

    def Close(self, *args, **kwargs):
        Window.Close(self, *args, **kwargs)
        if self.jobData:
            sm.GetService('industrySvc').DisconnectJob(self.jobData)

    @telemetry.ZONE_METHOD
    def OnNewJobData(self, branchHistory = True):
        if self.jobData:
            settings.user.ui.Set('IndustryCurrentActivityID', self.jobData.activityID)
        self.jobsStrip.OnNewJobData(self.jobData)
        self.currView.OnNewJobData(self.jobData)
        self.browserBlueprints.OnNewJobData(self.jobData)
        if branchHistory and self.jobData:
            self.history.Append((self.jobData.blueprintID, self.jobData.blueprint.blueprintTypeID, self.jobData.activityID))
            self.UpdateHistoryButtons()

    @telemetry.ZONE_METHOD
    def OnBlueprintsSelected(self, bpData, activityID = None, branchHistory = True):
        self.pendingBlueprint = (bpData, activityID, branchHistory)
        if not self.loadBlueprintThread:
            self.loadBlueprintThread = uthread.new(self._OnBlueprintSelected)

    def _OnBlueprintSelected(self):
        try:
            while self.pendingBlueprint:
                while uicore.uilib.Key(uiconst.VK_UP) or uicore.uilib.Key(uiconst.VK_DOWN):
                    blue.synchro.Yield()

                bpData, activityID, branchHistory = self.pendingBlueprint
                self.pendingBlueprint = None
                if activityID is None:
                    activityID = self._GetDefaultActivityID(bpData)
                if self.jobData and self.jobData.blueprint.IsSameBlueprint(bpData):
                    if activityID == self.jobData.activityID:
                        break
                self.jobData = None
                if bpData.jobID is not None:
                    jobData = sm.GetService('industrySvc').GetJobByID(bpData.jobID)
                    if jobData.status < industry.STATUS_COMPLETED:
                        self.jobData = sm.GetService('industrySvc').JobDataWithBlueprint(jobData)
                if not self.jobData:
                    self.jobData = self.CreateJob(bpData, activityID)
                if not self.pendingBlueprint:
                    self.browserBlueprints.OnActivitySelected(self.jobData.blueprintID, activityID)
                    self.OnNewJobData(branchHistory)
                blue.synchro.SleepWallclock(500)

        finally:
            self.loadBlueprintThread = None

    @telemetry.ZONE_METHOD
    def OnFacilitySelected(self, facilityData):
        if self.jobData:
            self.jobData.facility = facilityData

    @telemetry.ZONE_METHOD
    def OnJobSelected(self, jobData):
        if jobData.status > industry.STATUS_COMPLETED:
            jobData = sm.GetService('industrySvc').RecreateJob(jobData)
        else:
            jobData = sm.GetService('industrySvc').JobDataWithBlueprint(jobData)
        if not jobData:
            return
        self.jobData = jobData
        self.OnNewJobData(jobData)
        self.UpdateBlueprintBrowserActivitySelected()

    @telemetry.ZONE_METHOD
    def UpdateBlueprintBrowserActivitySelected(self):
        if self.jobData:
            self.browserBlueprints.OnActivitySelected(self.jobData.blueprintID, self.jobData.activityID)

    def OnBlueprintEntryDblClicked(self):
        if self.IsViewCollapsed():
            self.ExpandView()

    def _GetDefaultActivityID(self, bpData):
        currActivityID = settings.user.ui.Get('IndustryCurrentActivityID', None)
        if currActivityID in bpData.activities:
            return currActivityID
        for activityID in industry.ACTIVITIES:
            if activityID in bpData.activities:
                return activityID

    @telemetry.ZONE_METHOD
    def CreateJob(self, bpData, activityID):
        return sm.GetService('industrySvc').CreateJob(bpData, activityID, bpData.facilityID)

    def ShowBlueprint(self, blueprintID = None, blueprintTypeID = None, activityID = None, branchHistory = True, bpData = None):
        if not bpData:
            if blueprintID:
                bpData = sm.GetService('blueprintSvc').GetBlueprintItem(blueprintID)
            else:
                bpData = sm.GetService('blueprintSvc').GetBlueprintTypeCopy(blueprintTypeID)
        self.OnBlueprintsSelected(bpData, activityID=activityID, branchHistory=branchHistory)

    def ShowJob(self, jobID):
        if jobID:
            self.OnJobSelected(sm.GetService('industrySvc').GetJobByID(jobID))

    @classmethod
    def OpenOrShowBlueprint(cls, blueprintID = None, blueprintTypeID = None, bpData = None):
        wnd = cls.GetIfOpen()
        if wnd:
            wnd.Maximize()
            wnd.ShowBlueprint(blueprintID, blueprintTypeID, bpData=bpData)
            if wnd.IsViewCollapsed():
                wnd.ExpandView()
            uicore.registry.SetFocus(wnd)
        else:
            wnd = cls.Open(blueprintID=blueprintID, blueprintTypeID=blueprintTypeID, bpData=bpData)
            wnd.Maximize()

    def OnExpandBottomBtn(self, *args):
        if self.IsBrowserCollapsed():
            self.ExpandBrowser()
        else:
            self.CollapseBrowser()

    def OnExpandViewBtn(self, *args):
        if self.IsViewCollapsed():
            self.ExpandView()
        else:
            self.CollapseView()

    def ExpandView(self, animate = True):
        settings.user.ui.Set('industryWndIsViewCollapsed', False)
        sm.ScatterEvent('OnIndustryViewExpandCollapse')
        self.expandViewBtn.SetRotation(-pi)
        self.expandViewBtn.Disable()
        self.topCont.Show()
        if animate:
            uicore.animations.MorphScalar(self.topCont, 'height', self.topCont.height, TOP_HEIGHT, duration=0.3)
            uicore.animations.FadeIn(self.topCont, duration=0.3, sleep=True)
        else:
            self.topCont.height = TOP_HEIGHT
            self.topCont.opacity = 1.0
        self.expandBottomBtn.Show()
        self.expandViewBtn.Enable()

    def CollapseView(self, animate = True):
        settings.user.ui.Set('industryWndIsViewCollapsed', True)
        sm.ScatterEvent('OnIndustryViewExpandCollapse')
        self.expandViewBtn.Disable()
        self.expandViewBtn.SetRotation(0)
        self.expandBottomBtn.Hide()
        if animate:
            uicore.animations.MorphScalar(self.topCont, 'height', self.topCont.height, 0, duration=0.3)
            uicore.animations.FadeOut(self.topCont, duration=0.3, sleep=True)
        else:
            self.topCont.height = 0
            self.topCont.opacity = 0.0
        self.topCont.Hide()
        self.expandViewBtn.Enable()

    def IsViewCollapsed(self):
        return settings.user.ui.Get('industryWndIsViewCollapsed', False)

    def ExpandBrowser(self, animate = True):
        if self.tabs.GetSelectedIdx() is None:
            self.tabs.AutoSelect()
        settings.user.ui.Set('industryWndIsBrowserCollapsed', False)
        self.expandBottomBtn.SetRotation(-pi)
        self.expandBottomBtn.Disable()
        height = settings.user.ui.Get('industryWndExpandedHeight', self.default_height)
        self.browserCont.Show()
        if animate:
            uicore.animations.MorphScalar(self, 'height', self.height, height, duration=0.3)
            uicore.animations.FadeIn(self.browserCont, duration=0.3, sleep=True)
        else:
            self.height = height
            self.browserCont.opacity = 1.0
        self.UnlockHeight()
        self.expandViewBtn.Show()
        self.expandBottomBtn.Enable()

    def CollapseBrowser(self, animate = True):
        if not self.IsBrowserCollapsed():
            settings.user.ui.Set('industryWndExpandedHeight', self.height)
        settings.user.ui.Set('industryWndIsBrowserCollapsed', True)
        self.expandBottomBtn.Disable()
        self.expandBottomBtn.SetRotation(0)
        self.expandViewBtn.Hide()
        if animate:
            uicore.animations.MorphScalar(self, 'height', self.height, FIXED_HEIGHT, duration=0.3)
            uicore.animations.FadeOut(self.browserCont, duration=0.3, sleep=True)
        else:
            self.height = FIXED_HEIGHT
            self.browserCont.opacity = 0.0
        self.LockHeight(FIXED_HEIGHT)
        self.browserCont.Hide()
        self.expandBottomBtn.Enable()

    def IsBrowserCollapsed(self):
        return settings.user.ui.Get('industryWndIsBrowserCollapsed', False)

    def OnBack(self):
        historyID = self.history.GoBack()
        if historyID:
            if uicore.uilib.mouseOver != self.goBackBtn:
                self.goBackBtn.Blink()
            self.ShowBlueprint(branchHistory=False, *historyID)
            self.UpdateHistoryButtons()

    def OnForward(self):
        historyID = self.history.GoForward()
        if historyID:
            if uicore.uilib.mouseOver != self.goForwardBtn:
                self.goForwardBtn.Blink()
            self.ShowBlueprint(branchHistory=False, *historyID)
            self.UpdateHistoryButtons()

    def UpdateHistoryButtons(self):
        if self.history.IsBackEnabled():
            self.goBackBtn.Enable()
        else:
            self.goBackBtn.Disable()
        if self.history.IsForwardEnabled():
            self.goForwardBtn.Enable()
        else:
            self.goForwardBtn.Disable()

    def OnMouseWheel(self, *args):
        sm.ScatterEvent('OnIndustryWndMouseWheel')

    def OnClick(self, *args):
        sm.ScatterEvent('OnIndustryWndClick')

    def CloseByUser(self, *args):
        sm.GetService('audio').SendUIEvent('ind_windowClosed')
        Window.CloseByUser(self, *args)

    def _GetCurrentActivities(self):
        """
        Returns available activities for current blueprint correctly sorted
        """
        currActivities = self.jobData.blueprint.activities.keys()
        currActivities = sorted(currActivities, key=lambda x: ACTIVITIES.index(x))
        return currActivities

    def SelectPreviousActivity(self):
        if not self.jobData or self.jobData.IsInstalled():
            return
        currActivities = self._GetCurrentActivities()
        idx = currActivities.index(self.jobData.activityID)
        if idx == 0:
            return
        activityID = currActivities[idx - 1]
        self._SelectActivity(activityID)

    def SelectNextActivity(self):
        if not self.jobData or self.jobData.IsInstalled():
            return
        currActivities = self._GetCurrentActivities()
        idx = currActivities.index(self.jobData.activityID)
        if idx == len(currActivities) - 1:
            return
        activityID = currActivities[idx + 1]
        self._SelectActivity(activityID)

    def _SelectActivity(self, activityID):
        self.browserBlueprints.OnActivitySelected(self.jobData.blueprintID, activityID)
        self.OnBlueprintsSelected(self.jobData.blueprint, activityID)

    def OnIndustryLeftOrRightKey(self, key):
        if key == uiconst.VK_LEFT:
            self.SelectPreviousActivity()
        elif key == uiconst.VK_RIGHT:
            self.SelectNextActivity()

    def OnDropData(self, dragSource, dragData):
        if not dragData:
            return
        typeID = itemID = None
        data = dragData[0]
        bpData = getattr(data, 'bpData', None)
        if getattr(data, 'item', None):
            itemID = getattr(data.item, 'itemID', None)
            typeID = data.item.typeID
        else:
            typeID = getattr(data, 'typeID', None)
            itemID = getattr(data, 'itemID', None)
        if itemID or typeID:
            categoryID = cfg.invtypes.Get(typeID).categoryID
            if industryCommon.IsBlueprintCategory(categoryID):
                Industry.OpenOrShowBlueprint(itemID, typeID, bpData)
            else:
                if not bpData:
                    bpData = sm.GetService('blueprintSvc').GetBlueprintByProduct(typeID)
                if bpData:
                    Industry.OpenOrShowBlueprint(bpData=bpData)

    def OnIndustryDropData(self, dragSource, dragData):
        self.OnDropData(dragSource, dragData)

    def OnIndustryRemoveBlueprint(self):
        """
        Active blueprint removed by user
        """
        self.jobData = None
        self.OnNewJobData()

    def OnIndustryJob(self, jobID, ownerID, blueprintID, installerID, status, successfulRuns):
        """
        Notification if a job is modified in anyway.
        """
        if self.destroyed:
            return
        if self.jobData and self.jobData.jobID == jobID:
            if status == industry.STATUS_CANCELLED:
                self.jobData = None
            else:
                self.jobData.status = status
                self.jobData.successfulRuns = successfulRuns
            self.OnNewJobData()
        elif self.jobData and self.jobData.blueprintID == blueprintID:
            self.jobData = sm.GetService('industrySvc').GetJobByID(jobID)
            self.OnNewJobData()
        if status in (industry.STATUS_INSTALLED, industry.STATUS_READY):
            if self.tabs.GetSelectedIdx() != TAB_JOBS:
                self.tabs.BlinkPanelByName(localization.GetByLabel('UI/Industry/Jobs'))
        if status == industry.STATUS_INSTALLED:
            if self.tabs.GetSelectedIdx() == TAB_BLUEPRINTS:
                self.browserBlueprints.SetFocus()

    def OnBlueprintReload(self, ownerID):
        """
        If a blueprint changes relating to our current job, just reload.
        """
        if self.jobData and self.jobData.ownerID == ownerID:
            self.Reload()

    def OnFacilityReload(self, facilityID):
        """
        If a facility changes relating to our current job, just reload.
        """
        if self.jobData and self.jobData.facilityID == facilityID:
            self.Reload(force=True)

    def Reload(self, force = False):
        """
        Whatever the industry window is currently displaying at the top, reload all the data and redraw.
        """
        try:
            jobData = self.jobData
            if jobData:
                if force:
                    self.jobData = None
                if jobData.jobID:
                    self.ShowJob(jobData.jobID)
                else:
                    self.ShowBlueprint(blueprintID=jobData.blueprint.blueprintID, blueprintTypeID=jobData.blueprint.blueprintTypeID, activityID=jobData.activityID, bpData=jobData.blueprint)
        except UserError:
            self.OnIndustryRemoveBlueprint()
