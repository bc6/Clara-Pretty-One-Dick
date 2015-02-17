#Embedded file name: eve/client/script/ui/shared/industry\jobEntry.py
from carbonui.control.menuLabel import MenuLabel
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.gradientSprite import GradientSprite
from carbonui.primitives.sprite import Sprite
from carbon.common.script.sys.service import ROLE_PROGRAMMER
from carbon.common.script.util.format import StrFromColor
from eve.client.script.ui.control.baseListEntry import BaseListEntryCustomColumns
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveLabel import Label, EveLabelMedium
from eve.client.script.ui.control.gauge import Gauge
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.shared.industry.industryUIConst import VIEWMODE_ICONLIST
from eve.client.script.ui.shared.industry.installationActivityIcon import InstallationActivityIcon
from eve.common.script.util.eveFormat import FmtSystemSecStatus
import eve.client.script.ui.util.uix as uix
import industry
import localization
import carbonui.const as uiconst
import uthread
import blue
import sys

def IsPersonalJob(ownerID):
    return ownerID == session.charid


class JobEntry(BaseListEntryCustomColumns):
    default_name = 'JobEntry'

    def ApplyAttributes(self, attributes):
        BaseListEntryCustomColumns.ApplyAttributes(self, attributes)
        self.jobData = self.node.jobData
        self.item = self.node.item
        self.viewMode = self.node.viewMode
        self.AddColumnStatusIcon()
        self.AddColumnStatus()
        self.AddColumnText('x %s' % self.jobData.runs)
        self.AddColumnActivity()
        self.AddColumnBlueprintLabel()
        self.AddColumnJumps()
        self.AddColumnText(self.GetSecurityLabel())
        self.AddColumnInstallationName()
        if not IsPersonalJob(self.jobData.ownerID):
            self.AddColumnText(self.jobData.GetInstallerName())
        self.AddColumnText(self.jobData.GetStartDateLabel())
        self.AddColumnText(self.jobData.GetEndDateLabel())

    def AddColumnBlueprintLabel(self):
        col = self.AddColumnContainer()
        texturePath, hint = uix.GetTechLevelIconPathAndHint(self.jobData.blueprint.blueprintTypeID)
        if texturePath:
            techIconSize = 16 if self.viewMode == VIEWMODE_ICONLIST else 12
            Sprite(name='techIcon', parent=col, texturePath=texturePath, hint=hint, width=techIconSize, height=techIconSize)
        if self.viewMode == VIEWMODE_ICONLIST:
            iconSize = 32
            Icon(parent=col, typeID=self.jobData.blueprint.blueprintTypeID, isCopy=not self.jobData.blueprint.original, ignoreSize=True, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, width=iconSize, height=iconSize, left=2)
        else:
            iconSize = 0
        Label(parent=col, text=self.jobData.blueprint.GetLabel(), align=uiconst.CENTERLEFT, left=iconSize + 4, idx=0)

    def AddColumnStatusIcon(self):
        col = self.AddColumnContainer()
        self.statusIcon = Sprite(parent=col, align=uiconst.CENTER, width=16, height=16)
        self.UpdateStatusIcon()

    def UpdateStatusIcon(self):
        texturePath, color = industryUIConst.GetStatusIconAndColor(self.jobData.status)
        self.statusIcon.texturePath = texturePath
        self.statusIcon.SetRGBA(*color)

    def AddColumnStatus(self):
        col = self.AddColumnContainer()
        self.jobStateCont = JobStateContainer(parent=col, align=uiconst.TOALL, padding=2, jobData=self.jobData)

    def AddColumnActivity(self):
        col = self.AddColumnContainer()
        ICONSIZE = 20 if self.viewMode == VIEWMODE_ICONLIST else 16
        InstallationActivityIcon(parent=col, align=uiconst.CENTER, pos=(0,
         0,
         ICONSIZE,
         ICONSIZE), activityID=self.jobData.activityID, isEnabled=True)

    def AddColumnJumps(self):
        jumps = self.node.jumps
        if jumps != sys.maxint:
            self.AddColumnText(jumps)
        else:
            col = self.AddColumnContainer()
            Sprite(name='infinityIcon', parent=col, align=uiconst.CENTERLEFT, pos=(6, 0, 11, 6), texturePath='res:/UI/Texture/Classes/Industry/infinity.png', opacity=Label.default_color[3])

    def AddColumnInstallationName(self):
        self.AddColumnText(self.jobData.GetFacilityName())

    @staticmethod
    def GetDynamicHeight(node, width):
        if node.viewMode == VIEWMODE_ICONLIST:
            return 36
        else:
            return 20

    @staticmethod
    def GetDefaultColumnWidth():
        return {localization.GetByLabel('UI/Generic/Status'): 90,
         localization.GetByLabel('UI/Industry/Activity'): 32,
         localization.GetByLabel('UI/Industry/Blueprint'): 230,
         localization.GetByLabel('UI/Industry/Facility'): 230,
         localization.GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/Installer'): 120}

    def GetSecurityLabel(self):
        securityStatus = sm.GetService('map').GetSecurityStatus(self.jobData.solarSystemID)
        sec, col = FmtSystemSecStatus(securityStatus, 1)
        col.a = 1.0
        color = StrFromColor(col)
        return '<color=%s>%s</color>' % (color, sec)

    @staticmethod
    def GetColumnSortValues(jobData, jumps):
        if jobData.facilityID == session.stationid2 or jobData.solarSystemID == session.solarsystemid:
            jumps = -1
        if IsPersonalJob(jobData.ownerID):
            return (jobData.status,
             (-jobData.status, jobData.endDate),
             jobData.runs,
             jobData.activityID,
             cfg.invtypes.Get(jobData.blueprint.blueprintTypeID).name,
             jumps,
             sm.GetService('map').GetSecurityStatus(jobData.solarSystemID),
             jobData.GetFacilityName(),
             jobData.startDate,
             jobData.endDate)
        else:
            return (jobData.status,
             (jobData.status, jobData.endDate),
             jobData.runs,
             jobData.activityID,
             cfg.invtypes.Get(jobData.blueprint.blueprintTypeID).name,
             jumps,
             sm.GetService('map').GetSecurityStatus(jobData.solarSystemID),
             jobData.GetFacilityName(),
             jobData.GetInstallerName(),
             jobData.startDate,
             jobData.endDate)

    @staticmethod
    def GetHeaders(isPersonalJob = True):
        if isPersonalJob:
            return ('',
             localization.GetByLabel('UI/Generic/Status'),
             localization.GetByLabel('UI/Industry/JobRuns'),
             localization.GetByLabel('UI/Industry/Activity'),
             localization.GetByLabel('UI/Industry/Blueprint'),
             localization.GetByLabel('UI/Common/Jumps'),
             localization.GetByLabel('UI/Common/Security'),
             localization.GetByLabel('UI/Industry/Facility'),
             localization.GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/InstallDate'),
             localization.GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/EndDate'))
        else:
            return ('',
             localization.GetByLabel('UI/Generic/Status'),
             localization.GetByLabel('UI/Industry/JobRuns'),
             localization.GetByLabel('UI/Industry/Activity'),
             localization.GetByLabel('UI/Industry/Blueprint'),
             localization.GetByLabel('UI/Common/Jumps'),
             localization.GetByLabel('UI/Common/Security'),
             localization.GetByLabel('UI/Industry/Facility'),
             localization.GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/Installer'),
             localization.GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/InstallDate'),
             localization.GetByLabel('UI/ScienceAndIndustry/ScienceAndIndustryWindow/EndDate'))

    def GetMenu(self):
        m = sm.GetService('menu').GetMenuFormItemIDTypeID(self.jobData.blueprint.blueprintID, self.jobData.blueprint.blueprintTypeID, ignoreMarketDetails=False, invItem=self.jobData.blueprint.GetItem())
        label = MenuLabel('UI/Industry/Facility')
        m.append((label, sm.GetService('menu').CelestialMenu(itemID=self.jobData.facilityID)))
        if bool(session.role & ROLE_PROGRAMMER):
            m.append(None)
            m.append(('GM: Complete Job', sm.GetService('industrySvc').CompleteJob, (self.jobData.jobID,)))
            m.append(('GM: Cancel Job', sm.GetService('industrySvc').CancelJob, (self.jobData.jobID,)))
            m.append(None)
            m.append(('jobID: {}'.format(self.jobData.jobID), blue.pyos.SetClipboardData, (str(self.jobData.jobID),)))
        return m

    def UpdateValues(self, animate, num):
        self.jobStateCont.UpdateValue(animate, num)

    def OnStatusChanged(self, status, successfulRuns):
        self.jobData.status = status
        self.jobData.successfulRuns = successfulRuns
        self.jobStateCont.OnStatusChanged()
        if status > industry.STATUS_READY:
            if self.jobData.activityID == industry.MANUFACTURING:
                color = industryUIConst.COLOR_MANUFACTURING
            else:
                color = industryUIConst.COLOR_SCIENCE
            for col in self.columns:
                col.opacity = 0.3

            self.AnimFlash(color)
        self.UpdateStatusIcon()

    def AnimFlash(self, color):
        width = 500
        flashCont = Container(parent=self, idx=0, align=uiconst.TOPLEFT, width=width, height=self.height)
        flashGradient = GradientSprite(bgParent=flashCont, rgbData=[(0, color[:3])], alphaData=[(0, 0.0), (0.9, 0.4), (1.0, 0.0)])
        arrows = Sprite(parent=flashCont, align=uiconst.CENTERLEFT, texturePath='res:/UI/Texture/Classes/Industry/CenterBar/arrows.png', pos=(0,
         0,
         375,
         self.height), color=color, opacity=0.15, tileX=True)
        duration = self.width / 600.0
        uicore.animations.MorphScalar(flashCont, 'left', -width, self.width + width, duration=duration, curveType=uiconst.ANIM_LINEAR)
        uicore.animations.FadeTo(flashCont, 0.0, 1.0, duration=duration, callback=flashCont.Close, curveType=uiconst.ANIM_WAVE)


class JobStateContainer(Container):
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.jobData = attributes.jobData
        self.ConstructLayout()
        self.UpdateValue()

    def ConstructLayout(self):
        if not self.jobData:
            return
        if self.jobData.status == industry.STATUS_READY:
            self.deliverBtn = Button(name='deliverBtn', parent=self, align=uiconst.TOALL, label='<b>' + localization.GetByLabel('UI/Industry/Deliver'), func=self.OnDeliverBtn, padding=2)
            self.deliverBtn.width = self.deliverBtn.height = 0
            self.deliverBtn.Blink(time=3000)
            self.Enable()
        else:
            self.Disable()
            gaugeCont = ContainerAutoSize(name='gaugeCont', parent=self, align=uiconst.TOBOTTOM)
            mainCont = Container(name='mainCont', parent=self)
            self.deliverBtn = None
            self.valueLabel = EveLabelMedium(parent=mainCont, align=uiconst.CENTERLEFT, left=4)
        if self.jobData.status == industry.STATUS_INSTALLED:
            color = industryUIConst.COLOR_MANUFACTURING if self.jobData.activityID == industry.MANUFACTURING else industryUIConst.COLOR_SCIENCE
            self.gauge = Gauge(parent=gaugeCont, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, color=color, height=6, gaugeHeight=6, padTop=1, backgroundColor=(1.0, 1.0, 1.0, 0.05))

    def OnStatusChanged(self):
        self.Flush()
        self.ConstructLayout()
        if self.jobData.status == industry.STATUS_DELIVERED:
            uicore.animations.FadeTo(self.valueLabel, 0.0, 1.0)

    def UpdateValue(self, animate = False, num = 0):
        if not self.jobData or self.jobData.status in (industry.STATUS_READY, industry.STATUS_UNSUBMITTED):
            return
        if self.jobData.status == industry.STATUS_INSTALLED:
            progressRatio = self.jobData.GetJobProgressRatio()
            if progressRatio:
                self.gauge.SetValueInstantly(progressRatio)
                if animate and progressRatio != 1.0:
                    self.gauge.AnimFlash(1.0, duration=3.0, timeOffset=num * 0.1)
        self.valueLabel.text = self.jobData.GetJobStateLabel()

    def OnDeliverBtn(self, *args):
        sm.GetService('industrySvc').CompleteJob(self.jobData.jobID)
        sm.GetService('audio').SendUIEvent('ind_jobDelivered')

    def OnNewJobData(self, jobData):
        self.jobData = jobData
        self.OnStatusChanged()
        self.UpdateValue(animate=True)

    def StartUpdate(self):
        uthread.new(self._UpdateThread)

    def _UpdateThread(self):
        while not self.destroyed:
            self.UpdateValue()
            blue.synchro.SleepWallclock(500)
