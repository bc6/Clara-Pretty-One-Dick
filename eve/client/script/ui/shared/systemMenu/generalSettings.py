#Embedded file name: eve/client/script/ui/shared/systemMenu\generalSettings.py
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.util.bunch import Bunch
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.control.eveWindowUnderlay import BumpedUnderlay, EntryUnderlay
from eve.client.script.ui.shared.colorThemes import THEMES
import eve.client.script.ui.shared.systemMenu.betaOptions as betaOptions
from eve.client.script.ui.tooltips.tooltipHandler import TOOLTIP_SETTINGS_GENERIC, TOOLTIP_DELAY_GENERIC, TOOLTIP_DELAY_MIN, TOOLTIP_DELAY_MAX, TOOLTIP_SETTINGS_BRACKET, TOOLTIP_DELAY_BRACKET
import localization
import carbonui.const as uiconst
import eve.common.lib.appConst as appConst
import uiprimitives
import uix
import uicontrols
import blue
import listentry
import uiutil
from notifications.client.notificationSettings.notificationSettingHandler import NotificationSettingHandler
SLIDERWIDTH = 120
LEFTPADDING = 120

class GenericSystemMenu(object):

    def __init__(self, mainParent, parseDataFunction, menuSizeColumnValidator):
        self.parent = mainParent
        self.ParseDataCallback = parseDataFunction
        self.ValidateMenuSize = menuSizeColumnValidator

    def GetMouseButtonOptions(self):
        actionbtnOps = [(localization.GetByLabel('UI/Common/Input/Mouse/LeftMouseButton'), uiconst.MOUSELEFT),
         (localization.GetByLabel('UI/Common/Input/Mouse/MiddleMouseButton'), uiconst.MOUSEMIDDLE),
         (localization.GetByLabel('UI/Common/Input/Mouse/RightMouseButton'), uiconst.MOUSERIGHT),
         (localization.GetByLabel('UI/Common/Input/Mouse/ExtraMouseButton1'), uiconst.MOUSEXBUTTON1),
         (localization.GetByLabel('UI/Common/Input/Mouse/ExtraMouseButton2'), uiconst.MOUSEXBUTTON2)]
        return actionbtnOps

    def GetSnapOptions(self):
        snapOps = [(localization.GetByLabel('UI/SystemMenu/GeneralSettings/Windows/DontSnap'), 0),
         (localization.formatters.FormatNumeric(3), 3),
         (localization.formatters.FormatNumeric(6), 6),
         (localization.formatters.FormatNumeric(12), 12),
         (localization.formatters.FormatNumeric(24), 24)]
        return snapOps

    def GetMenuFontSizeOptions(self):
        menufontsizeOps = [(localization.formatters.FormatNumeric(9), 9),
         (localization.formatters.FormatNumeric(10), 10),
         (localization.formatters.FormatNumeric(11), 11),
         (localization.formatters.FormatNumeric(12), 12),
         (localization.formatters.FormatNumeric(13), 13)]
        return menufontsizeOps

    def GetTooltipSection(self):
        return [('header', localization.GetByLabel('UI/SystemMenu/GeneralSettings/Tooltips/Header')), ('slider',
          (TOOLTIP_SETTINGS_GENERIC, ('user', 'ui'), TOOLTIP_DELAY_GENERIC),
          'UI/SystemMenu/GeneralSettings/Tooltips/GeneralTooltipsDelay',
          (TOOLTIP_DELAY_MIN, TOOLTIP_DELAY_MAX),
          SLIDERWIDTH,
          None,
          (localization.GetByLabel('UI/SystemMenu/GeneralSettings/Tooltips/NoTooltipsDelay'), localization.GetByLabel('UI/SystemMenu/GeneralSettings/Tooltips/LongTooltipsDelay'))), ('toppush', 4)]

    def CloseOrValidateColumn(self, column, doValidate = True):
        if len(column.children) == 1:
            column.Close()
        elif doValidate:
            self.ValidateMenuSize(column)

    def AddColumn(self, columnWidth, name = 'column'):
        column = uiprimitives.Container(name=name, align=uiconst.TOLEFT, width=columnWidth, padLeft=8, parent=self.parent)
        column.isTabOrderGroup = 1
        BumpedUnderlay(isInFocus=True, parent=column)
        return column

    def AppendToColumn(self, menuData, column, validateEntries = True):
        self.ParseDataCallback(entries=menuData, parent=column, validateEntries=validateEntries)

    def MakeColumn1(self, columnWidth):
        column = self.AddColumn(columnWidth, name='col1')
        menudata = self.ConstructColumn1MenuData()
        self.AppendToColumn(menudata, column)
        self.ConstructCrashesAndExperimentsUI(column, columnWidth=columnWidth)
        self.ConstructNotificationSection(column, columnWidth=columnWidth)
        betaOptions.ConstructOptInSection(column, columnWidth=columnWidth)
        self.CloseOrValidateColumn(column)

    def ConstructNotificationSection(self, column, columnWidth):
        uix.GetContainerHeader(localization.GetByLabel('UI/SystemMenu/GeneralSettings/Notifications/Header'), column, xmargin=-5)
        uiprimitives.Container(name='toppush', align=uiconst.TOTOP, height=2, parent=column)
        uicontrols.Checkbox(text=localization.GetByLabel('UI/SystemMenu/GeneralSettings/Notifications/NotificationsEnabled'), parent=column, checked=NotificationSettingHandler().GetNotificationWidgetEnabled(), callback=self.ToggleNotificationsEnabled)

    def ToggleNotificationsEnabled(self, *args):
        NotificationSettingHandler().ToggleNotificationWidgetEnabled()

    def MakeColumn2(self, columnWidth):
        column = self.AddColumn(columnWidth, name='col2')
        self.AppendToColumn(self.ConstructTutorialAndStationMenuData(), column)
        self.AppendToColumn(self.ConstructInflightMenuData(), column)
        self.IHaveNoIdea(column)
        self.ConstructAndAppendOptionalClientUpdate(column)
        self.AppendBottom(column)
        self.CloseOrValidateColumn(column, doValidate=False)

    def MakeColumn3(self, columnWidth):
        if session.charid:
            column = self.AddColumn(columnWidth, name='col3')
            uix.GetContainerHeader(localization.GetByLabel('UI/SystemMenu/GeneralSettings/ColorTheme'), column, xmargin=1)
            self.AppendToColumn([('slider',
              ('windowTransparency', ('user', 'ui'), 1.0),
              'UI/SystemMenu/GeneralSettings/Transparent',
              (0.0, 1.0),
              120),
             ('toppush', 6),
             ('checkbox', ('enableWindowBlur', ('char', 'windows'), 1), localization.GetByLabel('UI/SystemMenu/GeneralSettings/General/EnableWindowBlur')),
             ('checkbox', ('shiptheme', ('char', 'windows'), 0), localization.GetByLabel('UI/SystemMenu/GeneralSettings/General/ShipTheme')),
             ('toppush', 8)], column)
            myScrollCont = ScrollContainer(name='myScrollCont', parent=column, align=uiconst.TOALL)
            if settings.char.windows.Get('shiptheme', False):
                myScrollCont.state = uiconst.UI_DISABLED
                myScrollCont.opacity = 0.3
            for themeID, _, _ in THEMES:
                ColorSettingEntry(parent=myScrollCont, themeID=themeID)

    def AppendBottom(self, column):
        bottomPar = uiprimitives.Container(name='bottomPar', parent=None, align=uiconst.TOALL)
        bottomBtnPar = uiprimitives.Container(name='bottomBtnPar', parent=bottomPar, align=uiconst.CENTERTOP, height=26)
        column.children.append(bottomPar)

    def ConstructAndAppendOptionalClientUpdate(self, column):
        optionalUpgradeData = [('header', localization.GetByLabel('UI/SystemMenu/GeneralSettings/ClientUpdate/Header'))]
        if len(optionalUpgradeData) > 1:
            self.AppendToColumn(optionalUpgradeData, column, validateEntries=False)

    def IHaveNoIdea(self, column):
        if settings.user.ui.Get('damageMessages', 1) == 0:
            for each in ('damageMessagesNoDamage', 'damageMessagesMine', 'damageMessagesEnemy'):
                cb = uiutil.FindChild(column, each)
                if cb:
                    cb.state = uiconst.UI_HIDDEN

    def ConstructColumn1MenuData(self):
        menufontsizeOps = self.GetMenuFontSizeOptions()
        menusData = [('header', localization.GetByLabel('UI/SystemMenu/GeneralSettings/General/Header')),
         ('checkbox', ('showintro2', ('public', 'generic'), 1), localization.GetByLabel('UI/SystemMenu/GeneralSettings/General/ShowIntro')),
         ('toppush', 4),
         ('combo',
          ('cmenufontsize', ('user', 'ui'), 10),
          localization.GetByLabel('UI/SystemMenu/GeneralSettings/General/ContextMenuFontSize'),
          menufontsizeOps,
          LEFTPADDING),
         ('header', localization.GetByLabel('UI/SystemMenu/GeneralSettings/Windows/Header')),
         ('checkbox', ('stackwndsonshift', ('user', 'ui'), 0), localization.GetByLabel('UI/SystemMenu/GeneralSettings/Windows/OnlyStackWindowsIfShiftIsPressed')),
         ('checkbox', ('useexistinginfownd', ('user', 'ui'), 1), localization.GetByLabel('UI/SystemMenu/GeneralSettings/Windows/TryUseExistingInfoWin')),
         ('checkbox', ('lockwhenpinned', ('char', 'windows'), 0), localization.GetByLabel('UI/SystemMenu/GeneralSettings/Windows/LockWhenPinned')),
         ('toppush', 4)]
        if session.userid:
            menusData += self.GetTooltipSection()
            if session.charid:
                menusData.extend([('header', localization.GetByLabel('UI/Crimewatch/Duel/EscMenuSectionHeader')), ('checkbox', (appConst.autoRejectDuelSettingsKey, 'server_setting', 0), localization.GetByLabel('UI/Crimewatch/Duel/AutoRejectDuelInvites'))])
        return menusData

    def ConstructTutorialAndStationMenuData(self):
        stationData = None
        if sm.GetService('experimentClientSvc').IsTutorialEnabled():
            stationData = (('header', localization.GetByLabel('UI/SystemMenu/GeneralSettings/Help/Header')),
             ('checkbox', ('showTutorials', ('char', 'ui'), 1), localization.GetByLabel('UI/SystemMenu/GeneralSettings/Help/ShowTutorials')),
             ('header', localization.GetByLabel('UI/SystemMenu/GeneralSettings/Station/Header')),
             ('checkbox', ('stationservicebtns', ('user', 'ui'), 1), localization.GetByLabel('UI/SystemMenu/GeneralSettings/Station/SmallButtons')),
             ('checkbox', ('dockshipsanditems', ('char', 'windows'), 0), localization.GetByLabel('UI/SystemMenu/GeneralSettings/Station/MergeItemsAndShips')))
        else:
            stationData = (('header', localization.GetByLabel('UI/SystemMenu/GeneralSettings/Station/Header')), ('checkbox', ('stationservicebtns', ('user', 'ui'), 1), localization.GetByLabel('UI/SystemMenu/GeneralSettings/Station/SmallButtons')), ('checkbox', ('dockshipsanditems', ('char', 'windows'), 0), localization.GetByLabel('UI/SystemMenu/GeneralSettings/Station/MergeItemsAndShips')))
        return stationData

    def ConstructCrashesAndExperimentsUI(self, parent, columnWidth):
        column = parent
        uiprimitives.Container(name='toppush', align=uiconst.TOTOP, height=4, parent=column)
        uix.GetContainerHeader(localization.GetByLabel('UI/SystemMenu/GeneralSettings/Crashes/Header'), column, xmargin=-5)
        uiprimitives.Container(name='toppush', align=uiconst.TOTOP, height=2, parent=column)
        uicontrols.Checkbox(text=localization.GetByLabel('UI/SystemMenu/GeneralSettings/Crashes/UploadCrashDumpsToCCPEnabled'), parent=column, checked=blue.IsBreakpadEnabled(), callback=self.EnableDisableBreakpad)
        self._ConstructExperimental(column, columnWidth)

    def _ConstructExperimental(self, column, columnWidth):
        lst = []
        if lst:
            uiprimitives.Container(name='toppush', align=uiconst.TOTOP, height=4, parent=column)
            uix.GetContainerHeader(localization.GetByLabel('UI/SystemMenu/GeneralSettings/Experimental/Header'), column, xmargin=-5)
            uiprimitives.Container(name='toppush', align=uiconst.TOTOP, height=2, parent=column)
            scroll = uicontrols.Scroll(parent=column)
            scroll.name = 'experimentalFeatures'
            scroll.HideBackground()
            scroll.minimumHeight = 64
            scrollList = []
            for each in lst:
                scrollList.append(listentry.Get('Button', {'label': each['label'],
                 'caption': each['caption'],
                 'OnClick': each['OnClick'],
                 'args': (each['args'],),
                 'maxLines': None,
                 'entryWidth': columnWidth - 16}))

            scroll.Load(contentList=scrollList)

    def ConstructInflightMenuData(self):
        atOps = []
        actionbtnOps = self.GetMouseButtonOptions()
        for i in xrange(13):
            if i == 0:
                atOps.append((localization.GetByLabel('UI/SystemMenu/GeneralSettings/Inflight/ZeroTargets', targetCount=i), i))
            else:
                atOps.append((localization.GetByLabel('UI/SystemMenu/GeneralSettings/Inflight/Targets', targetCount=i), i))

        inflightData = [('header', localization.GetByLabel('UI/SystemMenu/GeneralSettings/Inflight/Header')),
         ('toppush', 4),
         ('combo',
          ('autoTargetBack', ('user', 'ui'), 0),
          localization.GetByLabel('UI/SystemMenu/GeneralSettings/Inflight/AutoTargetBack'),
          atOps,
          LEFTPADDING),
         ('combo',
          ('actionmenuBtn', ('user', 'ui'), 0),
          localization.GetByLabel('UI/SystemMenu/GeneralSettings/Inflight/ExpandActionMenu'),
          actionbtnOps,
          LEFTPADDING),
         ('slider',
          ('actionMenuExpandTime', ('user', 'ui'), 150.0),
          'UI/SystemMenu/GeneralSettings/Inflight/RadialMenuDelay',
          (0, 450),
          120,
          75),
         ('toppush', 10)]
        if session.userid:
            inflightData += [('slider',
              (TOOLTIP_SETTINGS_BRACKET, ('user', 'ui'), TOOLTIP_DELAY_BRACKET),
              'UI/SystemMenu/GeneralSettings/Inflight/BracketListDelay',
              (TOOLTIP_DELAY_MIN, TOOLTIP_DELAY_MAX),
              120,
              None,
              (localization.GetByLabel('UI/SystemMenu/GeneralSettings/Inflight/NoBracketListDelay'), localization.GetByLabel('UI/SystemMenu/GeneralSettings/Inflight/LongBracketListDelay'))),
             ('toppush', 2),
             ('checkbox', ('bracketmenu_docked', ('user', 'ui'), False), localization.GetByLabel('UI/SystemMenu/GeneralSettings/Inflight/CompactBracketListWhenSnapped')),
             ('checkbox', ('bracketmenu_floating', ('user', 'ui'), True), localization.GetByLabel('UI/SystemMenu/GeneralSettings/Inflight/CompactBracketListWhenNotSnapped'))]
        return inflightData

    def EnableDisableBreakpad(self, checkbox):
        try:
            blue.EnableBreakpad(checkbox.checked)
        except RuntimeError:
            pass
        finally:
            prefs.SetValue('breakpadUpload', 1 if checkbox.checked else 0)


class ColorSettingEntry(Container):
    default_name = 'ColorSettingEntry'
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL
    default_height = 22
    __notifyevents__ = ['OnUIColorsChanged']

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.themeID = attributes.themeID
        uiColorSvc = sm.GetService('uiColor')
        baseColor = uiColorSvc.GetThemeBaseColor(self.themeID)
        hiliteColor = uiColorSvc.GetThemeHiliteColor(self.themeID)
        text = uiColorSvc.GetThemeName(self.themeID)
        Fill(parent=self, align=uiconst.TOLEFT, color=hiliteColor, width=20, padding=(2, 2, 0, 2))
        Fill(parent=self, align=uiconst.TOLEFT, color=baseColor, width=20, padding=(1, 2, 2, 2))
        Label(parent=self, align=uiconst.CENTERLEFT, left=45, text=text)
        self.underlay = EntryUnderlay(bgParent=self)
        self.UpdateSelected()

    def UpdateSelected(self):
        if self.themeID == sm.GetService('uiColor').GetSelectedThemeID():
            self.underlay.Select()
        else:
            self.underlay.Deselect()

    def OnMouseEnter(self, *args):
        self.underlay.OnMouseEnter()

    def OnMouseExit(self, *args):
        self.underlay.OnMouseExit()

    def OnMouseDown(self, *args):
        self.underlay.OnMouseDown()

    def OnMouseUp(self, *args):
        self.underlay.OnMouseUp()

    def OnClick(self, *args):
        sm.GetService('uiColor').SetThemeID(self.themeID)

    def OnUIColorsChanged(self):
        self.UpdateSelected()
