#Embedded file name: eve/client/script/ui/shared/industry\activitySelectionButtons.py
from carbonui.primitives.container import Container
from carbonui.util.color import Color
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.control.buttons import ToggleButtonGroup, ToggleButtonGroupButton
from eve.client.script.ui.shared.industry.views.errorFrame import ErrorFrame
import localization
import carbonui.const as uiconst
from industry.const import ACTIVITIES

class ActivitySelectionButtons(Container):
    default_name = 'ActivityTabs'
    default_height = 32

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.callback = attributes.callback
        self.jobData = None
        self.btnGroup = None
        self.ReconstructButtons()

    def ReconstructButtons(self):
        if self.btnGroup:
            self.btnGroup.Close()
        self.btnGroup = ToggleButtonGroup(name='myToggleBtnGroup', parent=self, align=uiconst.TOALL, callback=self.OnActivitySelected, height=0)
        for activityID in ACTIVITIES:
            isDisabled = self.jobData is None or activityID not in self.jobData.blueprint.activities
            color = industryUIConst.GetActivityColor(activityID)
            color = Color(*color).SetBrightness(0.5).GetRGBA()
            btn = self.btnGroup.AddButton(activityID, iconPath=industryUIConst.ACTIVITY_ICONS_LARGE[activityID], iconSize=26, colorSelected=color, isDisabled=isDisabled, btnClass=ActivityToggleButtonGroupButton, activityID=activityID)

    def OnNewJobData(self, jobData):
        oldJobData = self.jobData
        self.jobData = jobData
        if jobData:
            jobData.on_updated.connect(self.OnJobDataUpdated)
        blueprint = oldJobData.blueprint if oldJobData else None
        if jobData and jobData.blueprint.IsSameBlueprint(blueprint):
            self.UpdateSelectedBtn()
            return
        self.ReconstructButtons()
        self.UpdateState()

    def OnJobDataUpdated(self, jobData):
        self.UpdateState()

    def UpdateState(self):
        if self.jobData and self.jobData.IsInstalled():
            self.btnGroup.Disable()
            self.btnGroup.opacity = 0.5
        else:
            self.btnGroup.Enable()
            self.btnGroup.opacity = 1.0
        if not self.jobData:
            return
        self.UpdateSelectedBtn(self.jobData.activityID)
        for btn in self.btnGroup.buttons:
            activityID = btn.btnID
            if self.jobData.facility and activityID not in self.jobData.facility.activities:
                btn.ShowErrorFrame()
            else:
                btn.HideErrorFrame()

    def UpdateSelectedBtn(self, activityID = None):
        if self.btnGroup:
            self.btnGroup.SetSelectedByID(self.jobData.activityID, animate=False)

    def OnActivitySelected(self, activityID):
        self.callback(self.jobData.blueprint, activityID)


class ActivityToggleButtonGroupButton(ToggleButtonGroupButton):
    default_iconOpacity = 0.75

    def ApplyAttributes(self, attributes):
        ToggleButtonGroupButton.ApplyAttributes(self, attributes)
        self.activityID = attributes.activityID
        color = Color(*self.colorSelected).SetBrightness(0.75).GetRGBA()
        self.errorFrame = ErrorFrame(bgParent=self, state=uiconst.UI_HIDDEN, color=color, padding=1, idx=0)

    def ShowErrorFrame(self):
        if not self.isDisabled:
            self.errorFrame.Show()

    def HideErrorFrame(self):
        self.errorFrame.Hide()

    def GetHint(self, *args):
        hint = '<b>%s</b><br>%s' % (localization.GetByLabel(industryUIConst.ACTIVITY_NAMES[self.activityID]), localization.GetByLabel(industryUIConst.ACTIVITY_HINTS[self.activityID]))
        if self.errorFrame.display:
            colorHex = Color.RGBtoHex(*industryUIConst.COLOR_NOTREADY)
            hint += '<br><b><color=%s>%s</color></b>' % (colorHex, localization.GetByLabel('UI/Industry/ActivityNotSupported'))
        return hint
