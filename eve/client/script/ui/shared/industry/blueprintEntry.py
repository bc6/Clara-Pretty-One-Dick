#Embedded file name: eve/client/script/ui/shared/industry\blueprintEntry.py
from carbonui.const import TOALL, UI_DISABLED
from carbonui.control.menuLabel import MenuLabel
from carbonui.primitives.container import Container
from carbonui.primitives.gradientSprite import GradientSprite
from carbonui.util.color import Color
from eve.client.script.ui.control.baseListEntry import BaseListEntryCustomColumns
from eve.client.script.ui.control.eveIcon import Icon
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.shared.industry import industryUIConst
from eve.client.script.ui.shared.industry.views.containersMETE import ContainerTE, ContainerME
import sys
import industry
import localization
import carbonui.const as uiconst
from eve.client.script.ui.shared.industry.industryUIConst import VIEWMODE_ICONLIST, ACTIVITY_ICONS_SMALL, ACTIVITY_NAMES
from carbonui.primitives.sprite import Sprite
import eve.client.script.ui.util.uix as uix
from industry.const import ACTIVITIES
from eve.client.script.ui.control.buttons import ButtonIcon

class BlueprintEntry(BaseListEntryCustomColumns):
    default_name = 'BlueprintEntry'

    def ApplyAttributes(self, attributes):
        BaseListEntryCustomColumns.ApplyAttributes(self, attributes)
        self.bpData = self.node.bpData
        self.item = self.node.item
        self.activityCallback = self.node.activityCallback
        self.activityButtons = []
        self.viewMode = self.node.viewMode
        self.AddColumnBlueprintLabel()
        self.AddColumnMaterialEfficiency()
        self.AddColumnTimeEfficiency()
        self.AddColumnRunsRemaining()
        self.columnActivities = self.AddColumnActivities()
        if self.node.showFacility:
            self.AddColumnJumps()
            self.AddColumnText(self.bpData.GetFacilityName())
        if self.node.showLocation:
            self.AddColumnText(self.bpData.GetLocationName())
        self.AddColumnText(self.bpData.GetGroupName())
        self.OnJobStateChanged()

    def OnJobStateChanged(self, status = None):
        if status:
            isInstalled = industry.STATUS_UNSUBMITTED < status < industry.STATUS_COMPLETED
            if status in (industry.STATUS_INSTALLED, industry.STATUS_DELIVERED):
                self.AnimFlash(Color.WHITE)
        else:
            isInstalled = self.bpData.IsInstalled()
        opacity = 0.15 if isInstalled else 1.0
        for col in self.columns:
            col.opacity = opacity

        if isInstalled:
            self.columnActivities.Disable()
        else:
            self.columnActivities.Enable()

    def AnimFlash(self, color):
        """
        Animate sliding arrows from left to right to indicate state change
        """
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

    @staticmethod
    def GetDynamicHeight(node, width):
        if node.viewMode == VIEWMODE_ICONLIST:
            return 36
        else:
            return 22

    def AddColumnRunsRemaining(self):
        runsRemaining = self.bpData.runsRemaining
        if runsRemaining != -1:
            self.AddColumnText('%s' % runsRemaining)
        else:
            col = self.AddColumnContainer()
            Sprite(name='infinityIcon', parent=col, align=uiconst.CENTERLEFT, pos=(6, 0, 11, 6), texturePath='res:/UI/Texture/Classes/Industry/infinity.png', opacity=Label.default_color[3])

    def AddColumnJumps(self):
        jumps = self.node.jumps
        if jumps != sys.maxint:
            self.AddColumnText(jumps)
        else:
            col = self.AddColumnContainer()
            Sprite(name='infinityIcon', parent=col, align=uiconst.CENTERLEFT, pos=(6, 0, 11, 6), texturePath='res:/UI/Texture/Classes/Industry/infinity.png', opacity=Label.default_color[3])

    def AddColumnBlueprintLabel(self):
        col = self.AddColumnContainer()
        texturePath, hint = uix.GetTechLevelIconPathAndHint(self.bpData.blueprintTypeID)
        if texturePath:
            techIconSize = 16 if self.viewMode == VIEWMODE_ICONLIST else 12
            Sprite(name='techIcon', parent=col, texturePath=texturePath, hint=hint, width=techIconSize, height=techIconSize)
        if self.viewMode == VIEWMODE_ICONLIST:
            iconSize = 32
            Icon(parent=col, typeID=self.bpData.blueprintTypeID, isCopy=not self.bpData.original, ignoreSize=True, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, width=iconSize, height=iconSize, left=2)
        else:
            iconSize = 0
        Label(parent=col, text=self.bpData.GetLabel(), align=uiconst.CENTERLEFT, left=iconSize + 4, idx=0)

    def _AddColumnMETE(self, cls, value):
        col = self.AddColumnContainer()
        opacity = 0.5 if not value else 1.0
        isCompact = self.viewMode != VIEWMODE_ICONLIST
        gauge = cls(parent=col, align=TOALL, state=UI_DISABLED, padding=(3, 2, 3, 6), opacity=opacity, showBG=False, isCompact=isCompact)
        gauge.SetValue(value)

    def AddColumnMaterialEfficiency(self):
        value = self.bpData.materialEfficiency
        cls = ContainerME
        self._AddColumnMETE(cls, value)

    def AddColumnTimeEfficiency(self):
        value = self.bpData.timeEfficiency
        cls = ContainerTE
        self._AddColumnMETE(cls, value)

    def AddColumnActivities(self):
        col = self.AddColumnContainer()
        ICONSIZE = 20 if self.viewMode == VIEWMODE_ICONLIST else 14
        for i, activityID in enumerate(ACTIVITIES):
            isEnabled = activityID in self.bpData.activities
            hint = ACTIVITY_NAMES.get(activityID) if isEnabled else 'UI/Industry/ActivityNotAvailable'
            btn = ActivityButtonIcon(parent=col, align=uiconst.CENTERLEFT, pos=(6 + i * (ICONSIZE + 4),
             0,
             ICONSIZE + 4,
             ICONSIZE + 4), texturePath=ACTIVITY_ICONS_SMALL[activityID], iconSize=ICONSIZE, func=self.OnActivityBtn, args=(activityID, self.bpData), hint=localization.GetByLabel(hint), isHoverBGUsed=True, colorSelected=industryUIConst.GetActivityColor(activityID))
            self.activityButtons.append(btn)
            if not isEnabled:
                btn.Disable(opacity=0.05)

        return col

    def OnActivityBtn(self, activityID, bpData):
        self.activityCallback(self.bpData, activityID)

    def GetMenu(self):
        m = sm.GetService('menu').GetMenuFormItemIDTypeID(self.bpData.blueprintID, self.bpData.blueprintTypeID, ignoreMarketDetails=False, invItem=self.item)
        label = MenuLabel('UI/Industry/Facility')
        m.append((label, sm.GetService('menu').CelestialMenu(itemID=self.bpData.facilityID)))
        return m

    @staticmethod
    def GetDefaultColumnWidth():
        return {localization.GetByLabel('UI/Industry/Blueprint'): 230,
         localization.GetByLabel('UI/Industry/MaterialEfficiency'): 80,
         localization.GetByLabel('UI/Industry/TimeEfficiency'): 80,
         localization.GetByLabel('UI/Industry/Facility'): 200}

    @staticmethod
    def GetFixedColumns(viewMode):
        if viewMode == VIEWMODE_ICONLIST:
            return {localization.GetByLabel('UI/Industry/Activities'): 132}
        else:
            return {localization.GetByLabel('UI/Industry/Activities'): 104}

    @staticmethod
    def GetHeaders(showFacility = True, showLocation = True):
        ret = [localization.GetByLabel('UI/Industry/Blueprint'),
         localization.GetByLabel('UI/Industry/MaterialEfficiency'),
         localization.GetByLabel('UI/Industry/TimeEfficiency'),
         localization.GetByLabel('UI/Industry/RunsRemaining'),
         localization.GetByLabel('UI/Industry/Activities')]
        if showFacility:
            ret.extend((localization.GetByLabel('UI/Common/Jumps'), localization.GetByLabel('UI/Industry/Facility')))
        if showLocation:
            ret.append(localization.GetByLabel('UI/Industry/InventoryLocation'))
        ret.append(localization.GetByLabel('UI/Common/Group'))
        return ret

    @staticmethod
    def GetColumnSortValues(bpData, jumps = None, showFacility = True, showLocation = True):
        activitySum = ''
        for activityID in ACTIVITIES:
            activitySum += '1' if activityID in bpData.activities else '0'

        ret = [cfg.invtypes.Get(bpData.blueprintTypeID).name,
         bpData.materialEfficiency,
         bpData.timeEfficiency,
         bpData.runsRemaining,
         activitySum]
        if showFacility:
            ret.extend((jumps, bpData.GetFacilityName()))
        if showLocation:
            ret.append(bpData.GetLocationName())
        ret.append(bpData.GetGroupName())
        return ret

    def OnActivitySelected(self, itemID, activityID):
        for btn in self.activityButtons:
            if self.bpData.blueprintID == itemID and btn.activityID == activityID:
                btn.SetSelected()
            else:
                btn.SetDeselected()

    def GetDragData(self):
        ret = []
        nodes = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        for node in nodes:
            ret.append(node.bpData.GetDragData())

        return ret

    def OnDblClick(self, *args):
        sm.ScatterEvent('OnBlueprintEntryDblClicked')


class ActivityButtonIcon(ButtonIcon):

    def ApplyAttributes(self, attributes):
        ButtonIcon.ApplyAttributes(self, attributes)
        self.activityID, self.bpData = attributes.args

    def OnDblClick(self, *args):
        if uicore.uilib.Key(uiconst.VK_SHIFT):
            job = sm.GetService('industrySvc').CreateJob(self.bpData, self.activityID, self.bpData.facilityID)
            sm.GetService('industrySvc').InstallJob(job)
