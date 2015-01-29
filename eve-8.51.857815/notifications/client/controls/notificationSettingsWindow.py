#Embedded file name: notifications/client/controls\notificationSettingsWindow.py
from eve.client.script.ui.control.eveWindow import Window
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
import carbonui.const as uiconst
import localization
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from carbonui.primitives.line import Line
from notifications.client.notificationSettings.notificationSettingHandler import NotificationSettingHandler
from notifications.client.notificationSettings.notificationSettingConst import ExpandAlignmentConst
from eve.client.script.ui.control.eveWindowUnderlay import RaisedUnderlay, BumpedUnderlay

class NotificationSettingsWindow(Window):
    default_windowID = 'NotificationSettings'
    default_captionLabelPath = 'Notifications/NotificationSettings/NotificationSettingsWindowCaption'
    default_width = 660
    default_height = 400
    default_topParentHeight = 0
    default_minSize = (default_width, default_height)

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        developerMode = sm.GetService('notificationUIService').IsDeveloperMode()
        self.mainContainer = NotificationSettingsMainContainer(name='mainContainer', align=uiconst.TOALL, parent=self.GetMainArea(), parentwidth=self.default_width, developerMode=developerMode)


from eve.client.script.ui.control.checkbox import Checkbox
from eve.client.script.ui.control.buttons import Button
from carbonui.control.slider import Slider
from eve.client.script.ui.control.listgroup import ListGroup
from eve.client.script.ui.control.eveLabel import EveLabelMediumBold
from notifications.client.controls.notificationSettingList import NotificationSettingList

class NotificationSettingGroupDeco(ListGroup):
    pass


class NotificationSettingsMainContainer(Container):
    default_clipChildren = True

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes=attributes)
        self.isDeveloperMode = attributes.get('developerMode', True)
        self.basePadLeft = 5
        self.dev_simpleHistoryDisplayEnabled = False
        self.dev_historySettingsEnabled = True
        self.dev_exportNotificationHistoryEnabled = False
        self.dev_clearNotificationHistoryEnabled = False
        self.dev_soundSettingsEnabled = True
        parentwidth = attributes.get('parentwidth')
        self.lastVerticalBarEnabledStatus = False
        self.entryCache = {}
        self.leftContainer = NotificationSettingList(name='LeftContainer', align=uiconst.TOLEFT, width=parentwidth / 2, padding=4, parent=self, developerMode=self.isDeveloperMode)
        self.rightContainer = Container(name='RightContainer', align=uiconst.TOALL, padding=(0, 4, 4, 4), parent=self)
        BumpedUnderlay(name='leftUnderlay', bgParent=self.leftContainer)
        BumpedUnderlay(name='rightUnderlay', bgParent=self.rightContainer)
        self.notificationSettingHandler = NotificationSettingHandler()
        self.notificationSettingData = self.notificationSettingHandler.LoadSettings()
        self._SetupRightSide()
        self.leftContainer.PopulateScroll()

    def _SetupRightSide(self):
        self._SetupPopupArea()
        if self.dev_historySettingsEnabled:
            self._SetupHistoryArea()
        self._SetupUIArea()

    def _SetupPopupArea(self):
        self.popupSettingsContainer = ContainerAutoSize(name='PopupSettings', align=uiconst.TOTOP, parent=self.rightContainer, padding=(self.basePadLeft,
         5,
         10,
         0))
        EveLabelMediumBold(name='PopupHeader', align=uiconst.TOTOP, parent=self.popupSettingsContainer, text=localization.GetByLabel('Notifications/NotificationSettings/PopupsHeader'))
        self._MakeSeperationLine(self.popupSettingsContainer)
        Checkbox(name='UsepopupNotifications', text=localization.GetByLabel('Notifications/NotificationSettings/UsePopupNotifications'), parent=self.popupSettingsContainer, align=uiconst.TOTOP, checked=self.notificationSettingHandler.GetPopupsEnabled(), callback=self.OnShowPopupNotificationToggle)
        if self.dev_soundSettingsEnabled:
            Checkbox(name='Play sound checkbox', text=localization.GetByLabel('Notifications/NotificationSettings/PlaySound'), parent=self.popupSettingsContainer, align=uiconst.TOTOP, checked=self.notificationSettingHandler.GetNotificationSoundEnabled(), callback=self.OnPlaySoundToggle)
        self.MakeSliderTextRow(label=localization.GetByLabel('Notifications/NotificationSettings/FadeDelay'), minValue=0, maxValue=10.0, startValue=self.notificationSettingHandler.GetFadeTime(), stepping=0.5, endSliderFunc=self.OnFadeDelaySet)
        self.MakeSliderTextRow(label=localization.GetByLabel('Notifications/NotificationSettings/StackSize'), minValue=1, maxValue=10, startValue=self.notificationSettingHandler.GetStackSize(), stepping=1, endSliderFunc=self.OnStackSizeSet)

    def OnFadeDelaySet(self, slider):
        self.notificationSettingHandler.SaveFadeTime(slider.GetValue())
        sm.ScatterEvent('OnNotificationFadeTimeChanged', slider.GetValue())

    def OnStackSizeSet(self, slider):
        self.notificationSettingHandler.SaveStackSize(slider.GetValue())
        sm.ScatterEvent('OnNotificationStackSizeChanged', slider.GetValue())

    def _MakeSeperationLine(self, parent):
        Line(name='topLine', parent=parent, align=uiconst.TOTOP, weight=1, padBottom=2, opacity=0.3)

    def OnShowPopupNotificationToggle(self, checkbox):
        self.notificationSettingHandler.TogglePopupsEnabled()

    def OnPlaySoundToggle(self, *args):
        self.notificationSettingHandler.ToggleSoundEnabled()

    def _SetupHistoryArea(self):
        self.historySettingsContainer = ContainerAutoSize(name='HistorySettings', align=uiconst.TOTOP, parent=self.rightContainer, alignMode=uiconst.TOTOP, padding=(self.basePadLeft,
         0,
         0,
         0))
        EveLabelMediumBold(name='History', align=uiconst.TOTOP, parent=self.historySettingsContainer, text=localization.GetByLabel('Notifications/NotificationSettings/HistoryHeader'))
        self._MakeSeperationLine(self.historySettingsContainer)
        Button(name='Restore Notification History Button', align=uiconst.TOTOP, label=localization.GetByLabel('Notifications/NotificationSettings/RestoreNotificationHistory'), func=self.OnExportHistoryClick, pos=(0, 0, 100, 20), parent=self.historySettingsContainer, padding=(5, 5, 50, 5))
        Button(name='clearNotificationHistoryBtn', align=uiconst.TOTOP, label=localization.GetByLabel('Notifications/NotificationSettings/ClearNotificationHistory'), func=self.OnClearHistoryClick, pos=(0, 0, 100, 20), parent=self.historySettingsContainer, padding=(5, 0, 50, 5))

    def _SetupUIArea(self):
        self.UISettingsContainer = ContainerAutoSize(name='HistorySettings', align=uiconst.TOTOP, parent=self.rightContainer, alignMode=uiconst.TOTOP, padLeft=self.basePadLeft)
        EveLabelMediumBold(name='UI', align=uiconst.TOTOP, parent=self.UISettingsContainer, text=localization.GetByLabel('Notifications/NotificationSettings/UISettingHeader'))
        self._MakeSeperationLine(self.UISettingsContainer)
        if self.dev_simpleHistoryDisplayEnabled:
            Checkbox(name='simple history view', text=localization.GetByLabel('Notifications/NotificationSettings/SimpleHistoryDisplay'), parent=self.UISettingsContainer, align=uiconst.TOTOP, checked=True)
        hComboRowContainer = Container(name='ComboBoxRow', parent=self.UISettingsContainer, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, height=40, padRight=10)
        from eve.client.script.ui.control.eveCombo import Combo
        Combo(name='H-ExpandCombo', parent=hComboRowContainer, labelleft=120, label=localization.GetByLabel('Notifications/NotificationSettings/DefaultHExpand'), hint=localization.GetByLabel('Notifications/NotificationSettings/DefaultHExpandToolTip'), options=self.GetHorizontalComboOptions(), align=uiconst.TOTOP, width=self.rightContainer.width, callback=self.OnHorizontalComboSelect, select=self.notificationSettingHandler.GetHorizontalExpandAlignment())
        Combo(name='V-ExpandCombo', parent=hComboRowContainer, labelleft=120, label=localization.GetByLabel('Notifications/NotificationSettings/DefaultVExpand'), hint=localization.GetByLabel('Notifications/NotificationSettings/DefaultVExpandToolTip'), align=uiconst.TOTOP, options=self.GetVerticalComboOptions(), width=self.rightContainer.width, callback=self.OnVerticalComboSelect, select=self.notificationSettingHandler.GetVerticalExpandAlignment())

    def OnVerticalComboSelect(self, box, key, value):
        self.notificationSettingHandler.SetVerticalExpandAlignment(value)

    def OnHorizontalComboSelect(self, box, key, value):
        self.notificationSettingHandler.SetHorizontalExpandAlignment(value)

    def GetHorizontalComboOptions(self):
        return ((localization.GetByLabel('Notifications/NotificationSettings/ExpandDirectionLeft'), ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_LEFT), (localization.GetByLabel('Notifications/NotificationSettings/ExpandDirectionRight'), ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_RIGHT))

    def GetVerticalComboOptions(self):
        return ((localization.GetByLabel('Notifications/NotificationSettings/ExpandDirectionUp'), ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_UP), (localization.GetByLabel('Notifications/NotificationSettings/ExpandDirectionDown'), ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_DOWN))

    def OnExportHistoryClick(self, *args):
        sm.GetService('notificationUIService').UnClearHistory()

    def OnClearHistoryClick(self, *args):
        sm.GetService('notificationUIService').ClearHistory()

    def MakeSliderTextRow(self, label, minValue, maxValue, startValue, stepping, setValueFunc = None, endSliderFunc = None):
        sliderWidth = 100
        sliderValueWidth = 30
        sliderLabelWidth = 120
        rowPadding = (5, 2, 10, 2)
        size = EveLabelSmall.MeasureTextSize(label, width=sliderLabelWidth)
        rowHeight = size[1]
        rowContainer = Container(name='TextRowContainer', parent=self.rightContainer, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, height=rowHeight, padding=rowPadding)
        EveLabelSmall(name='sliderlabel', align=uiconst.TOLEFT, parent=rowContainer, text=label, width=sliderLabelWidth)
        increments = []
        currentValue = minValue
        while currentValue <= maxValue:
            increments.append(currentValue)
            currentValue = currentValue + stepping

        valueLabel = EveLabelSmall(name='sliderValuelabel', left=sliderWidth, align=uiconst.CENTERRIGHT, text=str(startValue), width=sliderValueWidth)

        def UpdateLabel(slider):
            valueLabel.text = str(slider.GetValue())

        Slider(name='niceSlider', align=uiconst.CENTERRIGHT, parent=rowContainer, minValue=minValue, maxValue=maxValue, width=sliderWidth, showLabel=False, startVal=startValue, isEvenIncrementsSlider=True, increments=increments, onsetvaluefunc=UpdateLabel, endsliderfunc=endSliderFunc)
        rowContainer.children.append(valueLabel)
        return rowContainer
