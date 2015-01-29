#Embedded file name: eve/client/script/ui/shared/planet\resourceController.py
"""
There is the sidebar bellow the location text overlay that replaces the autopilot route info.
The resouce controller allows the user to switch between resources to have them displayed on planet surface
"""
import carbonui.const as uiconst
import uiprimitives
import uicontrols
import uiutil
import uthread
import blue
from service import ROLE_GML
import localization
MAX_DISPLAY_QUALTY = const.planetResourceMaxValue * 255 * 0.5

class ResourceController(uicontrols.ContainerAutoSize):
    """
    This is the side bar controller that controls what resource is selected
    and gives a crude indication of resource state on the planet
    """
    __guid__ = 'planet.ui.ResourceController'
    __notifyevents__ = []
    default_name = 'ResourceController'
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_HIDDEN

    def ApplyAttributes(self, attributes):
        uicontrols.ContainerAutoSize.ApplyAttributes(self, attributes)
        self.CreateLayout()
        sm.RegisterNotify(self)

    def CreateLayout(self):
        legend = ResourceLegend(parent=self)
        planetUI = sm.GetService('planetUI')
        self.resourceList = ResourceList(parent=self)
        planetObject = sm.GetService('planetSvc').GetPlanet(planetUI.planetID)
        resourceInfo = planetObject.remoteHandler.GetPlanetResourceInfo()
        sortedList = []
        for typeID, quality in resourceInfo.iteritems():
            name = cfg.invtypes.Get(typeID).name
            sortedList.append((name, (typeID, quality)))

        sortedList = uiutil.SortListOfTuples(sortedList)
        for typeID, quality in sortedList:
            qualityRemapped = quality / MAX_DISPLAY_QUALTY
            self.resourceList.AddItem(typeID, quality=max(0, min(1.0, qualityRemapped)))

    def StopLoadingResources(self, resourceTypeID):
        self.resourceList.StopLoading(resourceTypeID)

    def StartLoadingResources(self):
        self.resourceList.StartLoading()

    def ResourceSelected(self, resourceTypeID):
        for item in self.resourceList.children:
            if item.typeID == resourceTypeID:
                self.resourceList.SelectItem(item)

    def EnterSurveyMode(self):
        self.resourceList.SetOpacity(0.5)
        self.resourceList.state = uiconst.UI_DISABLED

    def ExitSurveyMode(self):
        self.resourceList.SetOpacity(1)
        self.resourceList.state = uiconst.UI_PICKCHILDREN


class ResourceLegend(uiprimitives.Container):
    """
    This is the side bar controller that controls what resource is selected
    and gives a crude indication of resource state on the planet
    """
    __guid__ = 'planet.ui.ResourceLegend'
    default_name = 'ResourceLegend'
    default_align = uiconst.TOTOP
    default_height = 30
    default_state = uiconst.UI_PICKCHILDREN
    LINE_COLOR = (1, 1, 1, 0.5)
    RAMP_HEIGHT = 8
    HEIGHT = 4
    ADJUSTER_WIDTH = 16
    MIN_COLOR_RANGE = 26
    LEGENDWIDTH = 240

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.leftSpacerMaxWidth = self.ADJUSTER_WIDTH + self.LEGENDWIDTH - self.MIN_COLOR_RANGE
        self.CreateLayout()

    def CreateLayout(self):
        scale = uiprimitives.Container(name='scale', parent=self, align=uiconst.TOTOP, pos=(0,
         0,
         0,
         self.HEIGHT), padding=(4, 2, 4, -4))
        uiprimitives.Line(name='scaleBase', parent=scale, align=uiconst.TOTOP, color=self.LINE_COLOR)
        uiprimitives.Line(name='leftTick', parent=scale, align=uiconst.TOLEFT, color=self.LINE_COLOR)
        uiprimitives.Line(name='rightTick', parent=scale, align=uiconst.TORIGHT, color=self.LINE_COLOR)
        uiprimitives.Line(name='centerTick', parent=scale, align=uiconst.RELATIVE, color=self.LINE_COLOR, pos=(self.LEGENDWIDTH / 2,
         1,
         1,
         self.HEIGHT))
        for x in (0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9):
            left = int(self.LEGENDWIDTH * x)
            uiprimitives.Line(name='miniorTick_%f' % x, parent=scale, align=uiconst.RELATIVE, color=self.LINE_COLOR, pos=(left,
             1,
             1,
             self.HEIGHT / 2))

        self.legendContainer = uiprimitives.Container(parent=self, name='colorFilterContainer', align=uiconst.TOTOP, statestate=uiconst.UI_PICKCHILDREN, pos=(0,
         8,
         self.LEGENDWIDTH + 2 * self.ADJUSTER_WIDTH,
         self.ADJUSTER_WIDTH))
        self.leftSpacer = uiprimitives.Container(parent=self.legendContainer, name='leftSpacer', align=uiconst.TOLEFT, pos=(0,
         0,
         self.ADJUSTER_WIDTH,
         self.ADJUSTER_WIDTH), state=uiconst.UI_PICKCHILDREN)
        self.centerSpacer = uiprimitives.Container(parent=self.legendContainer, name='centerSpacer', align=uiconst.TOLEFT, pos=(0,
         0,
         self.LEGENDWIDTH,
         self.ADJUSTER_WIDTH), state=uiconst.UI_PICKCHILDREN)
        self.rightSpacer = uiprimitives.Container(parent=self.legendContainer, name='rightSpacer', align=uiconst.TOLEFT, pos=(0,
         0,
         self.ADJUSTER_WIDTH,
         self.ADJUSTER_WIDTH), state=uiconst.UI_PICKCHILDREN)
        adjusterMin = uicontrols.Icon(iname='leftAdjuster', icon='ui_73_16_185', parent=self.leftSpacer, align=uiconst.TORIGHT, pos=(0,
         0,
         self.ADJUSTER_WIDTH - 2,
         self.ADJUSTER_WIDTH), state=uiconst.UI_NORMAL, hint=localization.GetByLabel('UI/PI/Common/ResourcesMinimumVisibleHint'), color=(1, 1, 1, 0.5))
        adjusterMax = uicontrols.Icon(name='rightAdjuster', icon='ui_73_16_186', parent=self.rightSpacer, align=uiconst.TOLEFT, pos=(0,
         0,
         self.ADJUSTER_WIDTH - 2,
         self.ADJUSTER_WIDTH), state=uiconst.UI_NORMAL, hint=localization.GetByLabel('UI/PI/Common/ResourcesMaximumVisibleHint'), color=(1, 1, 1, 0.5))
        adjusterMin.OnMouseDown = (self.OnAdjustMouseDown, adjusterMin)
        adjusterMin.OnMouseUp = (self.OnAdjustMouseUp, adjusterMin)
        adjusterMin.OnMouseMove = (self.OnAdjustMouseMove, adjusterMin)
        adjusterMin.OnMouseEnter = (self.OnAdjusterMouseEnter, adjusterMin)
        adjusterMin.OnMouseExit = (self.OnAdjusterMouseExit, adjusterMin)
        adjusterMax.OnMouseDown = (self.OnAdjustMouseDown, adjusterMax)
        adjusterMax.OnMouseUp = (self.OnAdjustMouseUp, adjusterMax)
        adjusterMax.OnMouseMove = (self.OnAdjustMouseMove, adjusterMax)
        adjusterMax.OnMouseEnter = (self.OnAdjusterMouseEnter, adjusterMax)
        adjusterMax.OnMouseExit = (self.OnAdjusterMouseExit, adjusterMax)
        colorRamp = uiprimitives.Sprite(name='ColorRamp', parent=self.centerSpacer, texturePath='res:/dx9/model/worldobject/planet/resource_colorramp.dds', color=(1, 1, 1, 0.75), padding=(0, 4, 0, 4), state=uiconst.UI_NORMAL, align=uiconst.TOALL)
        colorRamp.OnMouseDown = (self.OnAdjustMouseDown, colorRamp)
        colorRamp.OnMouseUp = (self.OnAdjustMouseUp, colorRamp)
        colorRamp.OnMouseMove = (self.OnMoveRange, colorRamp)
        low, hi = settings.char.ui.Get('planet_resource_display_range', (0.0, 1.0))
        scalar = self.LEGENDWIDTH - 1
        self.leftSpacer.width = int(low * scalar) + self.ADJUSTER_WIDTH
        self.centerSpacer.width = int((hi - low) * scalar)

    def OnAdjusterMouseEnter(self, adjuster, *args):
        adjuster.color.SetRGB(1, 1, 1, 0.75)

    def OnAdjusterMouseExit(self, adjuster, *args):
        adjuster.color.SetRGB(1, 1, 1, 0.5)

    def OnAdjustMouseDown(self, adjuster, button):
        if button == 0:
            adjuster.dragging = True

    def OnAdjustMouseUp(self, adjuster, button):
        if button == 0:
            adjuster.dragging = False

    def OnAdjustMouseMove(self, adjuster, *args):
        """dragging the adjuster"""
        if getattr(adjuster, 'dragging', False) and uicore.uilib.leftbtn:
            if adjuster.name.startswith('right'):
                self.centerSpacer.width += uicore.uilib.dx
                if self.centerSpacer.width + self.leftSpacer.width - self.ADJUSTER_WIDTH > self.LEGENDWIDTH:
                    self.centerSpacer.width = self.LEGENDWIDTH - (self.leftSpacer.width - self.ADJUSTER_WIDTH)
                elif self.centerSpacer.width < self.MIN_COLOR_RANGE:
                    self.centerSpacer.width = self.MIN_COLOR_RANGE
            else:
                width = self.leftSpacer.width
                dx = uicore.uilib.dx
                if self.centerSpacer.width - uicore.uilib.dx < self.MIN_COLOR_RANGE:
                    dx = self.centerSpacer.width - self.MIN_COLOR_RANGE
                width += dx
                if width < self.ADJUSTER_WIDTH:
                    width = self.ADJUSTER_WIDTH
                elif width > self.leftSpacerMaxWidth:
                    width = self.leftSpacerMaxWidth
                dx = width - self.leftSpacer.width
                self.leftSpacer.width = width
                self.centerSpacer.width -= dx
            self.UpdateColorRamp()

    def OnMoveRange(self, adjuster, *args):
        """dragging the range"""
        if getattr(adjuster, 'dragging', False):
            self.leftSpacer.width += uicore.uilib.dx
            if self.centerSpacer.width + self.leftSpacer.width - self.ADJUSTER_WIDTH > self.LEGENDWIDTH:
                self.leftSpacer.width = self.LEGENDWIDTH - (self.centerSpacer.width - self.ADJUSTER_WIDTH)
            elif self.leftSpacer.width < self.ADJUSTER_WIDTH:
                self.leftSpacer.width = self.ADJUSTER_WIDTH
            self.UpdateColorRamp()

    def UpdateColorRamp(self):
        low = self.leftSpacer.width - self.ADJUSTER_WIDTH
        hi = low + self.centerSpacer.width
        sm.GetService('planetUI').SetResourceDisplayRange(low / float(self.LEGENDWIDTH - 1), hi / float(self.LEGENDWIDTH - 1))


class ResourceList(uicontrols.ContainerAutoSize):
    """
    This is a movable "window" that controls the scan location on the planet surface along
    with the radius of the scanned area.
    There is a side ways histogram of the color bands attached.
    """
    __guid__ = 'planet.ui.ResourceList'
    default_name = 'ResourceList'
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_PICKCHILDREN

    def ApplyAttributes(self, attributes):
        uicontrols.ContainerAutoSize.ApplyAttributes(self, attributes)
        self.AddItem(None)

    def AddItem(self, typeID, quality = None):
        ResourceListItem(parent=self, typeID=typeID, quality=quality)

    def ClearItems(self):
        self.children.Clear()

    def SelectItem(self, selectedItem):
        for item in self.children:
            if item != selectedItem:
                item.Deselect()
            else:
                item.Select()

    def StopLoading(self, typeID):
        item = self.GetItemByType(typeID)
        item.StopLoading()

    def GetItemByType(self, typeID):
        for item in self.children:
            if item.typeID == typeID:
                return item

    def GetSelected(self):
        """Get the selected item"""
        for item in self.children:
            if item.selected:
                return item


class ResourceListItem(uiprimitives.Container):
    """
    A selectable resource list item with a magnitude indicator
    """
    __guid__ = 'planet.ui.ResourceListItem'
    ITEM_HEIGHT = 24
    SELECT_BLOCK_PADDING = 1
    LEVEL_COLOR = (0.85, 0.85, 0.85, 1)
    LEVEL_BG_COLOR = (0.85, 0.85, 0.85, 0.25)
    LEVEL_WIDTH = 112
    LEVEL_HEIGHT = 10
    LEVEL_LEFT = 150
    SELECT_FILL_COLOR = (1.0, 1.0, 1.0, 0.25)
    HOVER_FILL_COLOR = (1.0, 1.0, 1.0, 0.25)
    EMPTY_COLOR = (1, 1, 1, 0)
    ICON_SIZE = 24
    ICON_LEFT = 0
    default_name = 'ResourceListItem'
    default_left = 0
    default_top = 0
    default_width = 0
    default_height = ITEM_HEIGHT
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL
    default_typeID = None
    default_selected = False
    default_quality = None

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.typeID = attributes.get('typeID', self.default_typeID)
        self.quality = attributes.get('quality', self.default_quality)
        if self.typeID is None:
            self.selected = True
        else:
            self.selected = False
        self.CreateLayout()

    def CreateLayout(self):
        if self.typeID is None:
            text = localization.GetByLabel('UI/PI/Common/NoFilter')
            self.icon = None
            self.loadingIcon = None
        else:
            self.icon = uicontrols.Icon(parent=self, align=uiconst.RELATIVE, pos=(0,
             0,
             self.ICON_SIZE,
             self.ICON_SIZE), state=uiconst.UI_DISABLED, ignoreSize=True, typeID=self.typeID, size=self.ICON_SIZE)
            text = cfg.invtypes.Get(self.typeID).typeName
            self.loadingIcon = uiprimitives.Transform(parent=self, align=uiconst.RELATIVE, pos=(0,
             0,
             self.ICON_SIZE,
             self.ICON_SIZE), state=uiconst.UI_HIDDEN)
            load = uicontrols.Icon(icon='ui_77_32_13', parent=self.loadingIcon, IgnoreSize=True, pos=(0,
             0,
             self.ICON_SIZE,
             self.ICON_SIZE), align=uiconst.CENTER)
        self.container = uiprimitives.Container(parent=self, name='mainContainer', align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        self.resourceName = uicontrols.EveLabelMedium(text=text, parent=self, left=4 + (self.ICON_SIZE if self.typeID is not None else 0), top=6, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        if self.typeID is not None:
            self.levelBar = uiprimitives.Container(name='levelBar', parent=self, pos=(self.LEVEL_LEFT,
             7,
             self.LEVEL_WIDTH,
             self.LEVEL_HEIGHT), align=uiconst.RELATIVE, state=uiconst.UI_DISABLED)
            self.level = uiprimitives.Fill(parent=self.levelBar, pos=(0,
             0,
             int(self.LEVEL_WIDTH * (self.quality or 0.0)),
             0), align=uiconst.TOLEFT, color=self.LEVEL_COLOR)
            self.levelFill = uiprimitives.Fill(parent=self.levelBar, align=uiconst.TOALL, color=self.LEVEL_BG_COLOR)
            if self.quality is None:
                self.levelBar.state = uiconst.UI_HIDDEN
        self.selectBlock = uiprimitives.Fill(parent=self, name='selectBlock', state=uiconst.UI_DISABLED, align=uiconst.TOALL, padding=(0,
         self.SELECT_BLOCK_PADDING,
         0,
         self.SELECT_BLOCK_PADDING), color=self.SELECT_FILL_COLOR if self.selected else self.EMPTY_COLOR)

    def OnMouseEnter(self, *args):
        if not self.selected:
            self.selectBlock.color.SetRGB(*self.HOVER_FILL_COLOR)

    def OnMouseExit(self, *args):
        if not self.selected:
            self.selectBlock.color.SetRGB(*self.EMPTY_COLOR)

    def OnClick(self, *args):
        sm.GetService('audio').SendUIEvent('wise:/msg_pi_scanning_switch_play')
        selected = self.parent.GetSelected()
        if selected == self:
            return
        self.parent.SelectItem(self)
        sm.GetService('planetUI').ShowResource(self.typeID)

    def Select(self):
        self.selectBlock.color.SetRGB(*self.SELECT_FILL_COLOR)
        if self.loadingIcon:
            self.loadingIcon.state = uiconst.UI_DISABLED
            self.icon.state = uiconst.UI_HIDDEN
            uthread.new(self.loadingIcon.StartRotationCycle, 1.0, 4000.0)
        self.selected = True

    def Deselect(self):
        self.selectBlock.color.SetRGB(*self.EMPTY_COLOR)
        self.selected = False

    def StopLoading(self):
        """Loading animation start automatically but we have to stop it explicitly"""
        if self.loadingIcon:
            self.loadingIcon.StopRotationCycle()
            self.loadingIcon.state = uiconst.UI_HIDDEN
            self.icon.state = uiconst.UI_DISABLED

    def GetMenu(self):
        if self.typeID is None:
            return []
        ret = [(uiutil.MenuLabel('UI/Commands/ShowInfo'), sm.GetService('info').ShowInfo, [self.typeID])]
        if session.role & ROLE_GML == ROLE_GML:
            ret.append(('GM / WM Extras', self.GetGMMenu()))
        return ret

    def GetGMMenu(self):
        ret = []
        ret.append(('Copy typeID', self.CopyTypeID))
        ret.append(('Show resource details: current server version', sm.GetService('planetUI').GMShowResource, (self.typeID, 'current')))
        ret.append(('Show resource details: current player version', sm.GetService('planetUI').GMShowResource, (self.typeID, 'player')))
        ret.append(('Show resource details: base layer', sm.GetService('planetUI').GMShowResource, (self.typeID, 'base')))
        ret.append(('Show resource details: depletion layer', sm.GetService('planetUI').GMShowResource, (self.typeID, 'depletion')))
        ret.append(('Show resource details: Nugget layer', sm.GetService('planetUI').GMShowResource, (self.typeID, 'nuggets')))
        ret.append(None)
        ret.append(('Create nugget layer', sm.GetService('planetUI').GMCreateNuggetLayer, (self.typeID,)))
        return ret

    def CopyTypeID(self):
        blue.pyos.SetClipboardData(str(self.typeID))
