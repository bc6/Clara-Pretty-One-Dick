#Embedded file name: eve/client/script/ui/shared\eveCalendar.py
"""
    This file contains the UI for the calendar system
"""
import blue
from eve.client.script.ui.control.themeColored import FrameThemeColored, FillThemeColored, LineThemeColored
import uicontrols
import uiprimitives
from eve.client.script.ui.shared.neocom.characterSearchWindow import CharacterSearchWindow
from carbonui.control.calendarCore import Calendar as _Calendar
import uthread
import uix
import uiutil
import util
from eve.client.script.ui.control import entries as listentry
from eve.client.script.ui.control.divider import Divider
import carbonui.const as uiconst
import uicls
import calendar
import localization
import time
import eveLocalization
NUM_DAYROWS = 6

class CalendarWnd(uicontrols.Window):
    __guid__ = 'form.eveCalendarWnd'
    __notifyevents__ = []
    default_windowID = 'calendar'
    default_captionLabelPath = 'UI/Calendar/CalendarWindow/Caption'
    default_iconNum = 'res:/ui/Texture/WindowIcons/calendar.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        sm.GetService('neocom').BlinkOff('calendar')
        self.SetTopparentHeight(0)
        self.SetMinSize([580, 400])
        self.sr.leftSide = uiprimitives.Container(name='leftSide', parent=self.sr.main, align=uiconst.TOLEFT, pos=(0, 0, 150, 0), padding=(6,
         const.defaultPadding,
         0,
         const.defaultPadding))
        self.sr.xDivider = Divider(name='xDivider', parent=self.sr.main, align=uiconst.TOLEFT, pos=(0,
         0,
         const.defaultPadding,
         0), state=uiconst.UI_NORMAL)
        self.sr.xDivider.Startup(self.sr.leftSide, 'width', 'x', 75, 200)
        self.sr.xDivider.OnSizeChanging = self.OnLeftSideChanged
        self.sr.calendarForm = Calendar(pos=(0, 0, 0, 0), parent=self.sr.main, padding=(const.defaultPadding,
         1,
         2 * const.defaultPadding,
         const.defaultPadding))
        self.sr.leftSideTop = uiprimitives.Container(name='leftSideTop', parent=self.sr.leftSide, align=uiconst.TOTOP, pos=(0, 0, 0, 40))
        self.sr.cbCont = uiprimitives.Container(name='cbCont', parent=self.sr.leftSide, align=uiconst.TOBOTTOM, pos=(0, 0, 0, 125), clipChildren=True)
        self.sr.leftSideBottom = uiprimitives.Container(name='leftSideBottom', parent=self.sr.leftSide, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.sr.leftSideBottom.OnResize = self.OnResizeLeftSideBottom
        self.sr.updatedCont = uiprimitives.Container(name='updatedCont', parent=self.sr.leftSideBottom, align=uiconst.TOBOTTOM, pos=(0, 0, 0, 60))
        self.sr.yDivider = Divider(name='yDivider', parent=self.sr.leftSideBottom, align=uiconst.TOBOTTOM, pos=(0,
         0,
         0,
         const.defaultPadding), state=uiconst.UI_NORMAL)
        self.sr.yDivider.Startup(self.sr.updatedCont, 'height', 'y', 50, 205)
        self.sr.yDivider.OnSizeChanged = self.OnListsSizeChanged
        self.sr.todoCont = uiprimitives.Container(name='todoCont', parent=self.sr.leftSideBottom, align=uiconst.TOALL, padTop=4)
        hdrText = localization.GetByLabel('UI/Calendar/CalendarWindow/UpcomingEvents')
        uicontrols.EveLabelMedium(text=hdrText, parent=self.sr.todoCont, align=uiconst.TOTOP, bold=True, height=18)
        self.sr.toDoForm = uicls.EventList(pos=(0, 0, 0, 0), parent=self.sr.todoCont, name='toDoForm', listentryClass='CalendarListEntry', getEventsFunc=sm.GetService('calendar').GetMyNextEvents, header=hdrText, listType='upcomingEvents')
        hdrText = localization.GetByLabel('UI/Calendar/CalendarWindow/LatestUpdates')
        uicontrols.EveLabelMedium(text=hdrText, parent=self.sr.updatedCont, align=uiconst.TOTOP, bold=True, height=18)
        self.sr.changesForm = uicls.UpdateEventsList(pos=(0, 0, 0, 0), parent=self.sr.updatedCont, name='changesForm', listentryClass='CalendarUpdatedEntry', getEventsFunc=sm.GetService('calendar').GetMyChangedEvents, header=hdrText, listType='latestUpdates')
        self.AddCheckBoxes()
        uicontrols.Checkbox(text=localization.GetByLabel('UI/Calendar/CalendarWindow/DeclinedEvents'), parent=self.sr.cbCont, configName='showDeclined', retval=0, checked=settings.user.ui.Get('calendar_showDeclined', 1), groupname=None, align=uiconst.TOTOP, padLeft=6, callback=self.DisplayCheckboxesChecked)
        uicontrols.Checkbox(text=localization.GetByLabel('UI/Calendar/CalendarWindow/ShowTimestamp'), parent=self.sr.cbCont, configName='showTimestamp', retval=0, checked=settings.user.ui.Get('calendar_showTimestamp', 1), groupname=None, align=uiconst.TOTOP, padLeft=6, callback=self.DisplayCheckboxesChecked)
        self.sr.cbCont.height = sum([ each.height for each in self.sr.cbCont.children ])
        uicontrols.Button(parent=self.sr.leftSideTop, label=localization.GetByLabel('UI/Calendar/CalendarWindow/NewEvent'), func=self.CreateNewEvent, pos=(0, 7, 0, 0))
        self.sr.todayBtn = uicontrols.Button(parent=self.sr.leftSideTop, label=localization.GetByLabel('UI/Calendar/CalendarWindow/Today'), func=self.GetToday, pos=(0, 7, 0, 0), align=uiconst.TOPRIGHT)

    def AddCheckBoxes(self, *args):
        self.sr.cbCont.Flush()
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Calendar/CalendarWindow/Filters'), parent=self.sr.cbCont, align=uiconst.TOTOP, bold=True, height=18, padTop=3)
        checkboxInfo = [(localization.GetByLabel('UI/Calendar/CalendarWindow/GroupPersonal'),
          'personal',
          const.calendarTagPersonal,
          settings.user.ui.Get('calendarTagCheked_%s' % const.calendarTagPersonal, 1))]
        if session.corpid and not util.IsNPC(session.corpid):
            checkboxInfo.append((localization.GetByLabel('UI/Calendar/CalendarWindow/GroupCorp'),
             'corp',
             const.calendarTagCorp,
             settings.user.ui.Get('calendarTagCheked_%s' % const.calendarTagCorp, 1)))
        if session.allianceid:
            checkboxInfo.append((localization.GetByLabel('UI/Calendar/CalendarWindow/GroupAlliance'),
             'alliance',
             const.calendarTagAlliance,
             settings.user.ui.Get('calendarTagCheked_%s' % const.calendarTagAlliance, 1)))
        checkboxInfo.append((localization.GetByLabel('UI/Calendar/CalendarWindow/GroupCcp'),
         'ccp',
         const.calendarTagCCP,
         settings.user.ui.Get('calendarTagCheked_%s' % const.calendarTagCCP, 1)))
        checkboxInfo.append((localization.GetByLabel('UI/Calendar/CalendarWindow/GroupAutomated'),
         'automated',
         const.calendarTagAutomated,
         settings.user.ui.Get('calendarTagCheked_%s' % const.calendarTagAutomated, 1)))
        self.sr.checkboxes = []
        for label, config, tag, checked in checkboxInfo:
            cb = uicontrols.Checkbox(text=label, parent=self.sr.cbCont, configName=config, retval=tag, checked=checked, groupname=None, align=uiconst.TOTOP, padLeft=6, callback=self.CheckboxChecked)
            self.sr.checkboxes.append(cb)

    def CheckboxChecked(self, *args):
        showTags = 0
        for cb in self.sr.checkboxes:
            tag = cb.data.get('value', 0)
            if cb.checked == True:
                showTags += tag
            settings.user.ui.Set('calendarTagCheked_%s' % tag, cb.checked)

        sm.ScatterEvent('OnCalendarFilterChange')

    def DisplayCheckboxesChecked(self, cb):
        config = 'calendar_%s' % cb.name
        settings.user.ui.Set(config, cb.checked)
        sm.ScatterEvent('OnCalendarFilterChange')

    def CreateNewEvent(self, *args):
        day = self.sr.calendarForm.selectedDay
        if day and not sm.GetService('calendar').IsInPast(day.year, day.month, day.monthday, allowToday=1):
            year = day.year
            month = day.month
            monthday = day.monthday
        else:
            eve.Message('CalendarCannotPlanThePast2')
            now = blue.os.GetWallclockTime()
            year, month, wd, monthday, hour, min, sec, ms = util.GetTimeParts(now)
        if not sm.GetService('calendar').IsInPast(year, month, monthday, allowToday=1):
            sm.GetService('calendar').OpenNewEventWnd(year, month, monthday)

    def GetToday(self, *args):
        self.sr.calendarForm.ResetBrowse()
        self.sr.calendarForm.InsertData()

    def OnLeftSideChanged(self, *args):
        if self.sr.leftSide.width < 140:
            self.sr.todayBtn.state = uiconst.UI_HIDDEN
        else:
            self.sr.todayBtn.state = uiconst.UI_NORMAL

    def OnListsSizeChanged(self, *args):
        h = self.sr.updatedCont.height
        l, t, w, absHeight = self.sr.leftSideBottom.GetAbsolute()
        if h > absHeight:
            h = absHeight
            ratio = float(h) / absHeight
            settings.user.ui.Set('calendar_listRatio', ratio)
            self._OnResize()
            return
        ratio = float(h) / absHeight
        settings.user.ui.Set('calendar_listRatio', ratio)

    def OnResizeLeftSideBottom(self, *args):
        if self and not self.destroyed and util.GetAttrs(self, 'sr', 'updatedCont'):
            l, t, w, absHeight = self.sr.leftSideBottom.GetAbsolute()
            scrollHeight = absHeight - 64
            ratio = settings.user.ui.Get('calendar_listRatio', 0.5)
            h = int(ratio * absHeight)
            if h > scrollHeight:
                h = scrollHeight
            self.sr.updatedCont.height = max(64, h)
            self.sr.yDivider.max = scrollHeight
        uthread.new(self.UpdateIndicators)

    def UpdateIndicators(self, *args):
        blue.pyos.synchro.Yield()
        self.sr.changesForm.UpdateMoreIndicators()
        self.sr.toDoForm.UpdateMoreIndicators()

    def _OnResize(self, *args):
        uicontrols.Window._OnResize(self)
        self.sr.calendarForm._OnResize()
        self.sr.changesForm.OnResize()
        self.sr.toDoForm.OnResize()

    def OnExpanded(self, *args):
        uthread.new(self.OnExpanded_thread)

    def OnExpanded_thread(self, *args):
        blue.pyos.synchro.SleepWallclock(50)
        if self and not self.destroyed:
            self.UpdateIndicators()


class Calendar(_Calendar):
    """
        This class contains the calendar
    """
    __guid__ = 'form.eveCalendar'
    __notifyevents__ = ['OnReloadCalendar', 'OnReloadEvents', 'OnCalendarFilterChange']
    default_left = 0
    default_top = 0
    default_width = 256
    default_height = 256

    def InsertBrowseControls(self, *args):
        """
            Inserts the arrows to browse through the calendar months
            This will need to be changed in core
        """
        self.sr.backBtn = btn = uix.GetBigButton(24, self.sr.monthTextCont, 0, 0)
        btn.OnClick = (self.ChangeMonth, -1)
        btn.hint = localization.GetByLabel('UI/Calendar/Hints/Previous')
        btn.sr.icon.LoadIcon('ui_23_64_1')
        self.sr.fwdBtn = btn = uix.GetBigButton(24, self.sr.monthTextCont, 0, 0)
        btn.OnClick = (self.ChangeMonth, 1)
        btn.hint = localization.GetByLabel('UI/Calendar/Hints/Next')
        btn.sr.icon.LoadIcon('ui_23_64_2')
        btn.SetAlign(uiconst.TOPRIGHT)

    def AddMonthText(self, text = '', *args):
        if self.sr.Get('monthText', None) is None:
            self.sr.monthText = uicontrols.EveCaptionMedium(text=text, parent=self.sr.monthTextCont, state=uiconst.UI_NORMAL, align=uiconst.CENTERTOP)
        return self.sr.monthText

    def LoadEvents(self, *args):
        """
            This function loads the events to the corrects days.
            
            Currently it can only load one event per day, I will fix that when
            I have a better idea how the real data will be. Ideally I will be 
            able to fetch data for a given month, but until then I just filter out
            events from other months
        """
        yearInView, monthInView = self.yearMonthInView
        events = sm.GetService('calendar').GetEventsByMonthYear(monthInView, yearInView)
        showTag = sm.GetService('calendar').GetActiveTags()
        eventsByDates = {}
        for eventKV in events:
            if eventKV.isDeleted:
                continue
            year, month, wd, day, hour, minute, sec, ms = blue.os.GetTimeParts(eventKV.eventDateTime)
            ts = eventKV.eventDateTime - eveLocalization.GetTimeDelta() * const.SEC
            timeStr = localization.formatters.FormatDateTime(value=ts, dateFormat='none', timeFormat='short')
            eventKV.eventTimeStamp = timeStr
            if showTag is None or showTag & eventKV.flag != 0:
                eventsThisDay = eventsByDates.get(day, {})
                eventsThisDay[eventKV.eventID] = eventKV
                eventsByDates[day] = eventsThisDay

        for date, eventsThisDay in eventsByDates.iteritems():
            self.LoadEventsToADay(date, eventsThisDay)


class CalendarDay(uicontrols.CalendarDayCore):
    __guid__ = 'uicls.CalendarDay'
    default_left = 0
    default_top = 0
    default_width = 256
    default_height = 256
    default_name = 'CalendarDay'

    def AddMoreContFill(self, *args):
        icon = uicontrols.Icon(icon='ui_38_16_229', parent=self.sr.moreCont, pos=(0, -3, 16, 16), align=uiconst.CENTERTOP, idx=0, ignoreSize=True)
        icon.OnClick = self.OnMoreClick

    def AddFill(self, *args):
        self.sr.fill = FillThemeColored(parent=self, padding=1, colorType=uiconst.COLORTYPE_UIHILIGHT, opacity=0.5)

    def AddDayNumber(self, text = '', *args):
        """
            This function adds the text object that displays the day's number
            This needs to be changed in core
        """
        if self.sr.Get('dayNumberText', None) is None:
            self.sr.dayNumberText = uicontrols.EveLabelMedium(text=text, parent=self.sr.dayNumberCont, state=uiconst.UI_DISABLED, left=1, align=uiconst.TOPRIGHT)
        return self.sr.dayNumberText

    def OnMoreClick(self, *args):
        sm.GetService('calendar').OpenSingleDayWnd('day', self.year, self.month, self.monthday, self.events)


class CalendarHeader(uicontrols.CalendarHeaderCore):
    __guid__ = 'uicls.CalendarHeader'
    default_left = 0
    default_top = 0
    default_width = 256
    default_height = 256
    default_name = 'CalendarHeader'
    default_charID = None

    def AddDayNameText(self, text = '', *args):
        if self.sr.Get('dayNameText', None) is None:
            self.sr.dayNameText = uicontrols.EveLabelMedium(text=text, parent=self.sr.dayNameCont, state=uiconst.UI_NORMAL, align=uiconst.CENTERBOTTOM)
        return self.sr.dayNameText


class CalendarEventEntry(uicontrols.CalendarEventEntryCore):
    __guid__ = 'uicls.CalendarEventEntry'

    def AddLabel(self, text, *args):
        self.sr.label = uicontrols.EveLabelSmall(text=text, parent=self, left=14, top=0, state=uiconst.UI_DISABLED, color=None, align=uiconst.CENTERLEFT, maxLines=1)

    def GetMenu(self):
        return self.MenuFunction(self)

    def MenuFunction(self, entry, *args):
        return []


class CalendarNewEventWnd(uicontrols.Window):
    __guid__ = 'form.CalendarNewEventWnd'
    __notifyevents__ = ['OnRespondToEvent', 'OnRemoveCalendarEvent']
    default_iconNum = 'res:/ui/Texture/WindowIcons/calendar.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        year = attributes.year
        month = attributes.month
        monthday = attributes.monthday
        eventInfo = attributes.eventInfo
        edit = attributes.edit or False
        self.SetTopparentHeight(0)
        self.HideMainIcon()
        self.SetMinSize([380, 370])
        self.buttonGroup = None
        now = blue.os.GetWallclockTime()
        cyear, cmonth, cwd, cday, chour, cmin, csec, cms = util.GetTimeParts(now)
        if year is None or month is None:
            year = cyear
            month = cmonth
        if (year, month, monthday) == (cyear, cmonth, cday):
            year, month, monthday, hour = self.FindTimeToUse(year, month, monthday, chour)
        else:
            hour = 12
        self.year = year
        self.month = month
        self.monthday = monthday
        self.hour = hour
        self.min = 0
        self.configname = '%s_%s_%s' % (year, month, monthday)
        self.invitees = None
        self.oldInvitees = None
        self.inEditMode = False
        self.sr.infoCont = uiprimitives.Container(name='infoCont', parent=self.sr.main, align=uiconst.TOTOP, pos=(0, 0, 0, 100))
        self.sr.tabCont = uiprimitives.Container(name='tabCont', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.sr.eventDescrCont = uiprimitives.Container(name='invitedScroll', parent=self.sr.tabCont, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        self.sr.invitedCont = uiprimitives.Container(name='invitedScroll', parent=self.sr.tabCont, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        subtabs = [[localization.GetByLabel('UI/Calendar/EventWindow/TabDescription'),
          self.sr.eventDescrCont,
          self,
          'descr']]
        flag = util.GetAttrs(eventInfo, 'flag')
        if flag is None or flag == const.calendarTagPersonal:
            subtabs.append([localization.GetByLabel('UI/Calendar/EventWindow/TabInvitations'),
             self.sr.invitedCont,
             self,
             'invitations'])
        elif flag in [const.calendarTagCorp, const.calendarTagAlliance] and session.corpid and session.corprole & const.corpRoleChatManager == const.corpRoleChatManager:
            subtabs.append([localization.GetByLabel('UI/Calendar/EventWindow/TabInvitations'),
             self.sr.invitedCont,
             self,
             'invitations'])
        self.sr.tabs = uicontrols.TabGroup(name='tabs', parent=self.sr.tabCont, idx=0, tabs=subtabs, groupID='calenderEvent_tabs', autoselecttab=0)
        self.sr.tabs.ShowPanelByName(localization.GetByLabel('UI/Calendar/EventWindow/TabDescription'))
        invTab = self.sr.tabs.sr.Get('%s_tab' % localization.GetByLabel('UI/Calendar/EventWindow/TabInvitations'), None)
        if invTab is not None:
            invTab.OnTabDropData = self.OnDropData
        if eventInfo is not None:
            eventDetails = sm.GetService('calendar').GetEventDetails(eventInfo.eventID, eventInfo.ownerID)
            self.eventID = eventInfo.eventID
            self.title = eventInfo.eventTitle
            self.descr = eventDetails.eventText
            self.creatorID = eventDetails.creatorID
            self.duration = eventInfo.eventDuration
            self.importance = eventInfo.importance
            self.eventTag = eventInfo.flag
            self.cbChecked = self.eventTag
            self.eventInfo = eventInfo
            self.year, self.month, cwd, self.monthdayday, self.hour, self.min, sec, ms = blue.os.GetTimeParts(eventInfo.eventDateTime)
            if edit:
                self.SetupCreateControls(new=not edit)
            else:
                self.SetupReadOnlyElements()
        else:
            self.eventID = None
            self.title = ''
            self.descr = ''
            self.creatorID = None
            self.duration = 0
            self.importance = 0
            self.eventTag = const.calendarTagPersonal
            self.cbChecked = const.calendarTagPersonal
            self.eventInfo = None
            self.SetupCreateControls()

    def Load(self, key, *args):
        if key == 'invitations':
            self.LoadInviteeTabScroll()

    def LoadInviteeTabScroll(self, *args):
        if getattr(self, 'eventID', None) is None:
            tag = self.cbChecked
        else:
            tag = self.eventTag
        if tag == const.calendarTagCCP:
            return
        if self.inEditMode:
            if tag in (const.calendarTagCorp, const.calendarTagAutomated):
                self.LoadCorpAllianceInScroll(session.corpid)
                return
            if tag == const.calendarTagAlliance:
                self.LoadCorpAllianceInScroll(session.allianceid)
                return
        self.LoadInviteeScroll()

    def SetupCreateControls(self, new = 1, *args):
        """
            sets up the create/edit mode of the window
        """
        self.inEditMode = True
        left = 6
        top = 20
        thisDay = [self.year,
         self.month,
         self.monthday,
         self.hour,
         self.min]
        self.sr.infoCont.Flush()
        self.sr.infoCont.clipChildren = True
        if self.buttonGroup:
            self.buttonGroup.Close()
            self.buttonGroup = None
        btns = []
        if new:
            caption = localization.GetByLabel('UI/Calendar/EventWindow/CaptionNew')
            btns.append([localization.GetByLabel('UI/Calendar/EventWindow/Create'),
             self.CreateOrEditEvent,
             (1,),
             None])
        else:
            caption = localization.GetByLabel('UI/Calendar/EventWindow/CaptionEdit')
            btns.append([localization.GetByLabel('UI/Calendar/EventWindow/Save'),
             self.CreateOrEditEvent,
             (0,),
             None])
        btns.append([localization.GetByLabel('UI/Generic/Cancel'),
         self.CloseByUser,
         (),
         None])
        self.buttonGroup = uicontrols.ButtonGroup(btns=btns, parent=self.sr.main, idx=0)
        self.SetCaption(caption)
        label = uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Calendar/SingleDayWindow/Title'), parent=self.sr.infoCont, align=uiconst.TOTOP, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         0))
        self.sr.titleEdit = uicontrols.SinglelineEdit(name='titleEdit', parent=self.sr.infoCont, setvalue=self.title, maxLength=const.calendarMaxTitleSize, align=uiconst.TOTOP, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding))
        dateParent = uiprimitives.Container(parent=self.sr.infoCont, align=uiconst.TOTOP, padding=(const.defaultPadding,
         label.textheight,
         const.defaultPadding,
         const.defaultPadding), height=100)
        now = blue.os.GetWallclockTime()
        cyear, cmonth, cwd, cday, chour, cmin, csec, cms = util.GetTimeParts(now)
        yearRange = const.calendarViewRangeInMonths / 12 + 1
        self.sr.fromDate = uix.GetDatePicker(dateParent, setval=thisDay, idx=None, withTime=True, timeparts=4, startYear=cyear, yearRange=yearRange)
        durationOptions = [(localization.GetByLabel('UI/Calendar/EventWindow/DateNotSpecified'), None)]
        for i in xrange(1, 25):
            str = localization.GetByLabel('UI/Calendar/EventWindow/DateSpecified', hours=i)
            durationOptions += [(str, i * 60)]

        dLeft = self.sr.fromDate.left + self.sr.fromDate.width + 16
        self.sr.durationCombo = uicontrols.Combo(label=localization.GetByLabel('UI/Calendar/EventWindow/Duration'), parent=dateParent, options=durationOptions, name='duration', select=self.duration, left=dLeft, width=90, align=uiconst.TOPLEFT)
        dateParent.height = max(self.sr.fromDate.height, self.sr.durationCombo.height)
        self.sr.importantCB = uicontrols.Checkbox(text=localization.GetByLabel('UI/Calendar/EventWindow/Important'), parent=self.sr.infoCont, configName='personal', retval=1, checked=self.importance, align=uiconst.TOTOP, padLeft=const.defaultPadding)
        self.sr.radioBtns = []
        if new:
            checkboxes = [(localization.GetByLabel('UI/Calendar/EventWindow/GroupPersonal'),
              'personal',
              const.calendarTagPersonal,
              const.calendarTagPersonal == self.eventTag)]
            if session.corpid and session.corprole & const.corpRoleChatManager == const.corpRoleChatManager:
                checkboxes.append((localization.GetByLabel('UI/Calendar/EventWindow/GroupCorporation'),
                 'corp',
                 const.calendarTagCorp,
                 const.calendarTagCorp == self.eventTag))
            if session.allianceid and session.corprole & const.corpRoleChatManager == const.corpRoleChatManager:
                checkboxes.append((localization.GetByLabel('UI/Calendar/EventWindow/GroupAlliance'),
                 'alliance',
                 const.calendarTagAlliance,
                 const.calendarTagAlliance == self.eventTag))
            for label, config, tag, checked in checkboxes:
                cb = uicontrols.Checkbox(text=label, parent=self.sr.infoCont, configName=config, retval=tag, checked=checked, align=uiconst.TOTOP, groupname='eventTag', callback=self.TagCheckboxChecked)
                self.sr.radioBtns.append(cb)

        else:
            eventTypeH = localization.GetByLabel('UI/Calendar/EventWindow/EventType')
            eventType = sm.GetService('calendar').GetEventTypes().get(self.eventTag, '-')
            if eventType != '-':
                eventType = localization.GetByLabel(eventType)
            uicontrols.EveHeaderSmall(text=eventTypeH, parent=self.sr.infoCont, name='eventType', align=uiconst.TOTOP, padLeft=const.defaultPadding, state=uiconst.UI_NORMAL)
            uicontrols.EveLabelMedium(text=eventType, parent=self.sr.infoCont, align=uiconst.TOTOP, padLeft=const.defaultPadding, padBottom=const.defaultPadding, state=uiconst.UI_NORMAL)
        self.sr.infoCont.height = sum([ each.height + each.padTop + each.padBottom for each in self.sr.infoCont.children ])
        self.sr.eventDescrCont.Flush()
        self.sr.descrEdit = uicls.EditPlainText(setvalue=self.descr, parent=self.sr.eventDescrCont, align=uiconst.TOALL, padding=const.defaultPadding, maxLength=const.calendarMaxDescrSize)
        self.sr.invitedCont.Flush()
        self.sr.addIviteeeBtnCont = uiprimitives.Container(name='btnCont', parent=self.sr.invitedCont, align=uiconst.TOTOP, pos=(0, 0, 0, 26), state=uiconst.UI_HIDDEN)
        uicontrols.Button(parent=self.sr.addIviteeeBtnCont, label=localization.GetByLabel('UI/Calendar/EventWindow/AddInvitee'), func=self.OpenAddInvteeWnd, pos=(6, 6, 0, 0))
        if new or self.eventTag == const.calendarTagPersonal:
            self.sr.addIviteeeBtnCont.state = uiconst.UI_PICKCHILDREN
        self.AddQuickFilter(self.sr.addIviteeeBtnCont)
        self.sr.inviteScroll = uicontrols.Scroll(name='invitedScroll', parent=self.sr.invitedCont, padding=const.defaultPadding)
        content = self.sr.inviteScroll.sr.content
        content.OnDropData = self.OnDropData
        if self.sr.tabs.GetSelectedArgs() == 'invitations':
            self.LoadInviteeTabScroll()

    def TagCheckboxChecked(self, cb, *args):
        tag = cb.data.get('value', const.calendarTagPersonal)
        self.cbChecked = tag
        if tag == const.calendarTagPersonal:
            self.sr.addIviteeeBtnCont.state = uiconst.UI_PICKCHILDREN
            self.LoadInviteeScroll()
        else:
            self.sr.addIviteeeBtnCont.state = uiconst.UI_HIDDEN
            if tag in (const.calendarTagCorp, const.calendarTagAutomated):
                self.LoadCorpAllianceInScroll(session.corpid)
            elif tag == const.calendarTagAlliance:
                self.LoadCorpAllianceInScroll(session.allianceid)

    def LoadCorpAllianceInScroll(self, entityID, *args):
        if entityID is None:
            return
        owner = cfg.eveowners.GetIfExists(entityID)
        if owner is None:
            return
        typeinfo = cfg.invtypes.Get(owner.typeID)
        if typeinfo is not None:
            scrolllist = [listentry.Get('User', {'charID': entityID})]
            self.sr.inviteScroll.Load(contentList=scrolllist, headers=[], noContentHint='')

    def SetupReadOnlyElements(self, *args):
        """
            Sets up the read-only mode of the window
        """
        left = 8
        top = 6
        firstColumnItems = []
        secondColumnItems = []
        self.SetCaption(localization.GetByLabel('UI/Calendar/EventWindow/CaptionRead'))
        btns = []
        if not sm.GetService('calendar').IsInPastFromBlueTime(then=self.eventInfo.eventDateTime) and not self.eventInfo.isDeleted:
            if self.eventInfo.flag in [const.calendarTagCorp, const.calendarTagAlliance]:
                self.AddAcceptDeclineBtns(btns)
                if self.eventInfo.ownerID in [session.corpid, session.allianceid] and session.corprole & const.corpRoleChatManager == const.corpRoleChatManager:
                    self.InsertEditDeleteBtns(btns)
            elif self.eventInfo.flag == const.calendarTagPersonal:
                if self.eventInfo.ownerID != session.charid:
                    self.AddAcceptDeclineBtns(btns)
                else:
                    self.InsertEditDeleteBtns(btns)
        btns.append([localization.GetByLabel('UI/Generic/Close'),
         self.CloseByUser,
         (),
         None])
        if self.buttonGroup:
            self.buttonGroup.Close()
            self.buttonGroup = None
        self.buttonGroup = uicontrols.ButtonGroup(btns=btns, parent=self.sr.main, idx=0)
        title = self.title
        if self.importance > 0:
            title = '<color=red>!</color>%s' % title
        caption = uicontrols.EveCaptionMedium(text=title, parent=self.sr.infoCont, padding=(left,
         top,
         left,
         top), align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        top += caption.textheight
        startH = localization.GetByLabel('UI/Calendar/EventWindow/StartTime')
        label = uicontrols.EveLabelSmallBold(text=startH, parent=self.sr.infoCont, name='startTime', align=uiconst.TOPLEFT, top=top, left=left, idx=1, state=uiconst.UI_NORMAL)
        startTime = util.FmtDate(self.eventInfo.eventDateTime - eveLocalization.GetTimeDelta() * const.SEC, 'ls')
        dataLabel = uicontrols.EveLabelMedium(text=startTime, parent=self.sr.infoCont, left=left, top=top + label.textheight - 4, state=uiconst.UI_NORMAL)
        firstColumnItems.append(label)
        firstColumnItems.append(dataLabel)
        eventTypeH = localization.GetByLabel('UI/Calendar/EventWindow/EventType')
        label = uicontrols.EveLabelSmallBold(text=eventTypeH, parent=self.sr.infoCont, name='eventType', align=uiconst.TOPLEFT, top=top, state=uiconst.UI_NORMAL)
        eventType = sm.GetService('calendar').GetEventTypes().get(self.eventTag, '-')
        if eventType != '-':
            eventType = localization.GetByLabel(eventType)
        dataLabel2 = uicontrols.EveLabelMedium(text=eventType, parent=self.sr.infoCont, top=top + label.textheight - 4, width=200, state=uiconst.UI_NORMAL)
        secondColumnItems.append(label)
        secondColumnItems.append(dataLabel2)
        top = max(dataLabel.top + dataLabel.textheight, dataLabel2.top + dataLabel2.textheight)
        durationH = localization.GetByLabel('UI/Calendar/EventWindow/Duration')
        label = uicontrols.EveLabelSmallBold(text=durationH, parent=self.sr.infoCont, name='duration', align=uiconst.TOPLEFT, top=top, left=left, idx=1, state=uiconst.UI_NORMAL)
        if self.eventInfo.eventDuration is None:
            durationLabel = localization.GetByLabel('UI/Calendar/EventWindow/DateNotSpecified')
        else:
            hours = self.eventInfo.eventDuration / 60
            durationLabel = localization.GetByLabel('UI/Calendar/EventWindow/DateSpecified', hours=hours)
        dataLabel = uicontrols.EveLabelMedium(text=durationLabel, parent=self.sr.infoCont, left=left, top=top + label.textheight - 4, state=uiconst.UI_NORMAL)
        firstColumnItems.append(label)
        firstColumnItems.append(dataLabel)
        creatorH = localization.GetByLabel('UI/Calendar/EventWindow/Creator')
        creatorInfo = cfg.eveowners.Get(self.creatorID)
        if self.eventTag == const.calendarTagCCP:
            creatorNameText = localization.GetByLabel('UI/Calendar/CalendarWindow/GroupCcp')
        else:
            showInfoData = ('showinfo', creatorInfo.typeID, self.creatorID)
            creatorNameText = localization.GetByLabel('UI/Calendar/EventWindow/CreatorLink', charID=self.creatorID, showInfoData=showInfoData)
        label = uicontrols.EveLabelSmallBold(text=creatorH, parent=self.sr.infoCont, name='eventType', align=uiconst.TOPLEFT, top=top, state=uiconst.UI_NORMAL)
        dataLabel2 = uicontrols.EveLabelMedium(text=creatorNameText, parent=self.sr.infoCont, top=top + label.textheight - 4, state=uiconst.UI_NORMAL)
        secondColumnItems.append(label)
        secondColumnItems.append(dataLabel2)
        top = max(dataLabel.top + dataLabel.textheight, dataLabel2.top + dataLabel2.textheight)
        iconPath, myResponse = sm.GetService('calendar').GetMyResponseIconFromID(self.eventID, long=1, getDeleted=self.eventInfo.isDeleted)
        response = localization.GetByLabel(sm.GetService('calendar').GetResponseType().get(myResponse, 'UI/Generic/Unknown'))
        statusH = localization.GetByLabel('UI/Calendar/EventWindow/Status')
        label = uicontrols.EveLabelSmallBold(text=statusH, parent=self.sr.infoCont, name='status', align=uiconst.TOPLEFT, top=top, left=left, idx=1, state=uiconst.UI_NORMAL)
        self.sr.statusIconCont = uiprimitives.Container(name='statusIconCont', parent=self.sr.infoCont, align=uiconst.TOPLEFT, pos=(left,
         top + label.textheight - 4,
         16,
         16))
        self.sr.reponseText = uicontrols.EveLabelMedium(text=response, parent=self.sr.infoCont, left=left + 16, top=top + label.textheight - 4, state=uiconst.UI_NORMAL)
        if iconPath:
            uicontrols.Icon(icon=iconPath, parent=self.sr.statusIconCont, align=uiconst.CENTER, pos=(0, 0, 16, 16))
        firstColumnItems.append(label)
        firstColumnItems.append(self.sr.reponseText)
        updateH = localization.GetByLabel('UI/Calendar/EventWindow/LastUpdated')
        label = uicontrols.EveLabelSmallBold(text=updateH, parent=self.sr.infoCont, name='updated', align=uiconst.TOPLEFT, top=top, state=uiconst.UI_NORMAL)
        updateTime = util.FmtDate(self.eventInfo.dateModified, 'ls')
        dataLabel2 = uicontrols.EveLabelMedium(text=updateTime, parent=self.sr.infoCont, top=top + label.textheight - 4, width=200, state=uiconst.UI_NORMAL)
        secondColumnItems.append(label)
        secondColumnItems.append(dataLabel2)
        top = max(self.sr.reponseText.top + self.sr.reponseText.textheight, dataLabel2.top + dataLabel2.textheight)
        self.sr.infoCont.height = top
        firstColumnWidth = max([ each.textwidth for each in firstColumnItems ])
        for each in secondColumnItems:
            each.left = left + firstColumnWidth + 10

        descr = self.descr
        self.sr.descrEdit = uicls.EditPlainText(setvalue=descr, parent=self.sr.eventDescrCont, align=uiconst.TOALL, maxLength=1000, padding=const.defaultPadding, readonly=1)
        self.sr.invitedCont.Flush()
        self.sr.searchCont = uiprimitives.Container(name='searchCont', parent=self.sr.invitedCont, align=uiconst.TOTOP, pos=(0, 0, 0, 26))
        self.AddQuickFilter(self.sr.searchCont)
        if self.eventTag == const.calendarTagCCP:
            self.sr.searchCont.state = uiconst.UI_HIDDEN
        elif self.eventTag in [const.calendarTagCorp, const.calendarTagAlliance] and session.corpid and not session.corprole & const.corpRoleChatManager == const.corpRoleChatManager:
            self.sr.searchCont.state = uiconst.UI_HIDDEN
        self.sr.inviteScroll = uicontrols.Scroll(name='invitedScroll', parent=self.sr.invitedCont, padding=const.defaultPadding)

    def InsertEditDeleteBtns(self, btns, top = 6, *args):
        editDeleteCont = uiprimitives.Container(name='editCont', parent=self.sr.infoCont, align=uiconst.TORIGHT, pos=(0, 0, 30, 0))
        editBtn = uicontrols.Button(parent=editDeleteCont, label=localization.GetByLabel('UI/Calendar/EventWindow/Edit'), func=self.ChangeToEditMode, pos=(const.defaultPadding,
         top,
         0,
         0), align=uiconst.TOPRIGHT)
        deleteBtn = uicontrols.Button(parent=editDeleteCont, label=localization.GetByLabel('UI/Calendar/EventWindow/Delete'), func=self.Delete, pos=(const.defaultPadding,
         top + 24,
         0,
         0), align=uiconst.TOPRIGHT)
        editBtn.width = deleteBtn.width = max(editBtn.width, deleteBtn.width)
        editDeleteCont.width = 4 + editBtn.width

    def AddAcceptDeclineBtns(self, btns):
        iconPath, myResponse = sm.GetService('calendar').GetMyResponseIconFromID(self.eventID)
        if myResponse != const.eventResponseAccepted:
            btns.insert(0, [localization.GetByLabel('/Carbon/UI/Calendar/Accept'),
             self.RespondToEvent,
             (const.eventResponseAccepted,),
             None])
        if myResponse != const.eventResponseMaybe:
            btns.insert(1, [localization.GetByLabel('/Carbon/UI/Calendar/MaybeReply'),
             self.RespondToEvent,
             (const.eventResponseMaybe,),
             None])
        if myResponse != const.eventResponseDeclined:
            btns.insert(2, [localization.GetByLabel('/Carbon/UI/Calendar/Decline'),
             self.RespondToEvent,
             (const.eventResponseDeclined,),
             None])

    def AddQuickFilter(self, cont, *args):
        self.sr.searchBox = uicls.QuickFilterEdit(name='searchBox', parent=cont, setvalue='', maxLength=37, pos=(5, 6, 100, 0), align=uiconst.TOPRIGHT, isCharacterField=True)
        self.sr.searchBox.ReloadFunction = self.LoadInviteeScroll

    def OpenAddInvteeWnd(self, *args):
        """
            Gets a search window to search for invitees
        """
        actionBtn = [(localization.GetByLabel('UI/Calendar/FindInviteesWindow/Add'), self.AddInviteeToEvent, 1)]
        caption = localization.GetByLabel('UI/Calendar/FindInviteesWindow/Caption')
        CharacterSearchWindow.CloseIfOpen(windowID='searchWindow_calendar')
        extraIconHintFlag = ['ui_73_16_13', localization.GetByLabel('UI/Calendar/Hints/CharacterAdded'), False]
        wnd = CharacterSearchWindow.Open(windowID='searchWindow_calendar', actionBtns=actionBtn, caption=caption, input='', getMyCorp=False, getMyLists=False, getMyAlliance=False, showContactList=True, extraIconHintFlag=extraIconHintFlag, configname=self.configname)
        wnd.ExtraMenuFunction = self.InviteeMenuFunction
        wnd.IsAdded = self.CheckIfAdded

    def CheckIfAdded(self, contactID):
        if self.invitees is None:
            self.PopulateInviteeDicts(self.eventID)
        return contactID in self.invitees

    def AddInviteeToEvent(self, func, *args):
        if self.inEditMode is False:
            return
        if not self or self.destroyed:
            return
        sel = apply(func)
        selIDs = [ each.charID for each in sel ]
        self.AddInvitees(selIDs)

    def AddInvitees(self, charIDList):
        if self.inEditMode is False:
            return
        if self.invitees is None:
            self.PopulateInviteeDicts(self.eventID)
        for charID in charIDList:
            if charID == session.charid or charID is None:
                continue
            if len(self.invitees) >= const.calendarMaxInvitees:
                eve.Message('CustomInfo', {'info': localization.GetByLabel('UI/Calendar/FindInviteesWindow/TooMany', max=const.calendarMaxInvitees)})
                break
            if charID not in self.invitees:
                self.invitees[charID] = const.eventResponseUndecided
                sm.ScatterEvent('OnSearcedUserAdded', charID, self.configname)

        self.LoadInviteeScroll()

    def LoadInviteeScroll(self, *args):
        filter = self.sr.searchBox.GetValue()
        if len(filter) >= 2:
            return self.SearchInvitee()
        if self.invitees is None:
            self.PopulateInviteeDicts(self.eventID)
        responseDict = sm.GetService('calendar').GetResponsesToEventInStatusDict(self.eventID, self.invitees)
        scrolllist = []
        responseCategoryList = [const.eventResponseAccepted, const.eventResponseMaybe, const.eventResponseDeclined]
        if self.eventTag == const.calendarTagPersonal:
            responseCategoryList.insert(-1, const.eventResponseUndecided)
        for response in responseCategoryList:
            label = localization.GetByLabel(sm.GetService('calendar').GetResponseType().get(response, 'UI/Generic/Unknown'))
            data = {'GetSubContent': self.GetResponseSubContent,
             'label': label,
             'cleanLabel': label,
             'id': ('calendarInvitees', response),
             'state': 'locked',
             'BlockOpenWindow': 1,
             'showicon': sm.GetService('calendar').GetResponseIconNum(response),
             'showlen': 1,
             'groupName': 'labels',
             'groupItems': responseDict[response],
             'noItemText': localization.GetByLabel('UI/Calendar/EventWindow/NoCharacter'),
             'response': response,
             'DropData': self.DropUserOnGroup,
             'allowGuids': ['listentry.User', 'listentry.Sender', 'listentry.ChatUser']}
            scrolllist.append(listentry.Get('Group', data))

        self.sr.inviteScroll.Load(contentList=scrolllist, headers=[], noContentHint='')

    def GetResponseSubContent(self, data, *args):
        response = data.response
        scrolllist = []
        if len(data.groupItems) > const.calendarMaxInviteeDisplayed:
            if response == const.eventResponseDeclined:
                label = localization.GetByLabel('UI/Calendar/EventWindow/TooManyDeclined', max=const.calendarMaxInviteeDisplayed)
            else:
                label = localization.GetByLabel('UI/Calendar/EventWindow/TooManyAccepted', max=const.calendarMaxInviteeDisplayed)
            return [listentry.Get('Generic', {'label': label,
              'sublevel': 1})]
        cfg.eveowners.Prime(data.groupItems)
        for charID in data.groupItems:
            if response == const.eventResponseUninvited:
                continue
            charinfo = cfg.eveowners.Get(charID)
            entry = listentry.Get('User', {'charID': charID,
             'MenuFunction': self.InviteeMenuFunction})
            scrolllist.append((charinfo.name.lower(), entry))

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        return scrolllist

    def InviteeMenuFunction(self, nodes, *args):
        m = []
        if self.inEditMode is False:
            return m
        if self.invitees is None:
            self.PopulateInviteeDicts(self.eventID)
        charIDs = [ node.charID for node in nodes if node.charID in self.invitees ]
        if session.charid in charIDs:
            charIDs.remove(session.charid)
        numCharIDs = len(charIDs)
        if numCharIDs > 0:
            label = localization.GetByLabel('UI/Calendar/EventWindow/RemoveInvitee', num=numCharIDs)
            m = [(label, self.RemoveInviteeFromScroll, (charIDs,))]
        return m

    def RemoveInviteeFromScroll(self, charIDs):
        if self.inEditMode is False:
            return
        if self.invitees is None:
            self.PopulateInviteeDicts(self.eventID)
        for charID in charIDs:
            self.invitees.pop(charID, None)

        sm.ScatterEvent('OnSearcedUserRemoved', charIDs, self.configname)
        self.LoadInviteeScroll()

    def ChangeToEditMode(self, *args):
        self.FlushAll()
        if self.invitees is None:
            self.PopulateInviteeDicts(self.eventID)
        self.oldInvitees = self.invitees.copy()
        self.SetupCreateControls(new=0)

    def FlushAll(self, *args):
        uiutil.Flush(self.sr.infoCont)
        uiutil.Flush(self.sr.eventDescrCont)
        uiutil.Flush(self.sr.invitedCont)
        if self.buttonGroup:
            self.buttonGroup.Close()
            self.buttonGroup = None

    def FindTimeToUse(self, year, month, day, hour):
        firstDay, lastDay = calendar.monthrange(year, month)
        hour = hour + 1
        if hour > 23:
            hour = 0
            day = day + 1
        if day > lastDay:
            day = 1
            month += 1
        if month > const.calendarDecember:
            month = const.calendarJanuary
            year = year + 1
        return (year,
         month,
         day,
         hour)

    def CreateOrEditEvent(self, create = 1, *args):
        if getattr(self, 'editing', 0):
            return
        self.editing = 1
        try:
            eventTag = 0
            for btn in self.sr.radioBtns:
                if btn.checked:
                    eventTag = btn.data['value']

            if eventTag == 0:
                eventTag = self.eventTag
            descr = self.sr.descrEdit.GetValue()
            title = self.sr.titleEdit.GetValue()
            fromDate = self.sr.fromDate.GetValue()
            duration = self.sr.durationCombo.GetValue()
            important = self.sr.importantCB.checked
            cyear, cmonth, cwd, cday, chour, cmin, csec, cms = blue.os.GetTimeParts(fromDate + eveLocalization.GetTimeDelta() * const.SEC)
            if sm.GetService('calendar').IsInPast(cyear, cmonth, cday, chour, cmin):
                raise UserError('CalendarCannotPlanThePast')
            if create:
                if self.invitees is None:
                    self.PopulateInviteeDicts(self.eventID)
                newInviteeCharIDs = self.invitees.keys()
                sm.GetService('calendar').CreateNewEvent(fromDate, duration, title, descr, eventTag, important, invitees=newInviteeCharIDs)
            else:
                if self.invitees is None:
                    self.PopulateInviteeDicts(self.eventID)
                newInviteeCharIDs = [ charID for charID in self.invitees.keys() if charID not in self.oldInvitees.keys() ]
                removedInviteeCharIDs = [ charID for charID in self.oldInvitees.keys() if charID not in self.invitees.keys() ]
                wasEdited = sm.GetService('calendar').EditEvent(self.eventID, self.eventInfo.eventDateTime, fromDate, duration, title, descr, eventTag, important)
                if not wasEdited:
                    return
                if len(newInviteeCharIDs) + len(removedInviteeCharIDs) > 0:
                    sm.GetService('calendar').UpdateEventParticipants(self.eventID, newInviteeCharIDs, removedInviteeCharIDs)
        finally:
            self.editing = 0

        sm.ScatterEvent('OnReloadEvents')
        self.CloseByUser()

    def RespondToEvent(self, response, *args):
        sm.GetService('calendar').RespondToEvent(self.eventID, self.eventInfo, response)

    def Delete(self, *args):
        sm.GetService('calendar').DeleteEvent(self.eventID, self.eventInfo.ownerID)

    def Cancel(self, *args):
        self.CloseByUser()

    def OnDropData(self, dragObj, nodes, *args):
        toAdd = []
        for node in nodes:
            if node.__guid__ in ('listentry.User', 'listentry.Sender', 'listentry.ChatUser', 'listentry.SearchedUser') and node.IsCharacter and not util.IsNPC(node.itemID):
                toAdd.append(node.itemID)

        if len(toAdd) > 0:
            self.AddInvitees(toAdd)

    def DropUserOnGroup(self, groupID, nodes, *args):
        self.OnDropData(None, nodes)

    def _OnClose(self, *args):
        wnd = CharacterSearchWindow.GetIfOpen(windowID='searchWindow_calendar')
        if wnd and wnd.configname == self.configname:
            wnd.CloseByUser()

    def SearchInvitee(self, *args):
        if self.invitees is None:
            self.PopulateInviteeDicts(self.eventID)
        cfg.eveowners.Prime(self.invitees.keys())
        matched = uiutil.NiceFilter(self.sr.searchBox.QuickFilter, [ cfg.eveowners.Get(charID) for charID in self.invitees.keys() ])
        extraIcons = {}
        for each in [const.eventResponseAccepted, const.eventResponseDeclined, const.eventResponseUndecided]:
            icon = sm.GetService('calendar').GetLongResponseIconPath(each)
            label = sm.GetService('calendar').GetResponseType().get(each, '')
            if label != '':
                label = localization.GetByLabel(label)
            extraIcons[each] = [icon, label, True]

        scrolllist = []
        for owner in matched:
            charID = owner.ownerID
            contact = util.KeyVal(contactID=charID)
            response = self.invitees.get(charID, None)
            if response is None:
                continue
            extraIconHintFlag = extraIcons.get(response, None)
            extraInfo = util.KeyVal(extraIconHintFlag=extraIconHintFlag, wndConfigname=self.configname)
            entryTuple = sm.GetService('addressbook').GetContactEntry(None, contact, extraInfo=extraInfo, listentryType='SearchedUser')
            scrolllist.append(entryTuple)

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        self.sr.inviteScroll.Load(contentList=scrolllist, headers=[], noContentHint=localization.GetByLabel('UI/Calendar/FindInviteesWindow/NothingFound'))

    def PopulateInviteeDicts(self, eventID):
        if eventID is None:
            self.invitees = {}
        else:
            ownerID = util.GetAttrs(self, 'eventInfo', 'ownerID')
            self.invitees = sm.GetService('calendar').GetResponsesToEvent(eventID, ownerID)
        self.oldInvitees = self.invitees.copy()

    def OnRespondToEvent(self, *args):
        self.CloseByUser()

    def OnRemoveCalendarEvent(self, eventID, eventDateTime, isDeleted):
        if self.eventID == eventID:
            self.CloseByUser()


class CalendarSingleDayWnd(uicontrols.Window):
    __guid__ = 'form.CalendarSingleDayWnd'
    __notifyevents__ = ['OnReloadCalendar', 'OnCalendarFilterChange']
    default_iconNum = 'res:/ui/Texture/WindowIcons/calendar.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        header = attributes.header
        year = attributes.year
        month = attributes.month
        monthday = attributes.monthday
        events = attributes.events
        wndType = attributes.wndType
        isADay = attributes.isADay or False
        self.header = header
        self.date = (year, month, monthday)
        self.year = year
        self.month = month
        self.monthday = monthday
        self.wndType = wndType
        self.isADay = isADay
        sm.RegisterNotify(self)
        if isADay:
            dayDate = time.struct_time((year,
             month,
             monthday,
             0,
             0,
             0,
             0,
             1,
             0))
            caption = localization.formatters.FormatDateTime(value=dayDate, dateFormat='long', timeFormat='none')
        else:
            caption = header
        self.SetCaption(caption)
        uicontrols.WndCaptionLabel(text=caption, parent=self.sr.topParent, align=uiconst.RELATIVE)
        self.SetMinSize([315, 300])
        uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Generic/Close'),
          self.CloseByUser,
          (),
          None]], parent=self.sr.main, idx=0)
        self.sr.eventScroll = uicontrols.Scroll(name='eventScroll', parent=self.sr.main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.sr.eventScroll.sr.id = 'calendar_singedaywnd'
        self.sr.eventScroll.sr.maxDefaultColumns = {localization.GetByLabel('UI/Generic/Unknown'): 150}
        self.LoadDaysEvents(events)

    def LoadDaysEvents(self, events, *args):
        self.events = events
        scrolllist = []
        includeUpdatedColumn = self.wndType == 'latestUpdates'
        for eventID, event in events.iteritems():
            iconPath, myResponse = sm.GetService('calendar').GetMyResponseIconFromID(eventID, long=1, getDeleted=event.isDeleted)
            if not settings.user.ui.Get('calendar_showDeclined', 1) and myResponse == const.eventResponseDeclined:
                continue
            if event.isDeleted and self.isADay:
                continue
            if self.isADay:
                timeStamp = getattr(event, 'eventTimeStamp', '')
            else:
                timeStamp = util.FmtDate(event.eventDateTime - eveLocalization.GetTimeDelta() * const.SEC, 'ss')
            label = '%s<t>%s' % (timeStamp, event.eventTitle)
            if includeUpdatedColumn:
                modified = util.FmtDate(event.dateModified, 'ss')
                label += '<t>%s' % modified
                sortBy = event.dateModified
            else:
                sortBy = event.eventDateTime
            data = util.KeyVal()
            data.label = label
            data.cleanLabel = label
            data.eventInfo = event
            data.eventID = event.eventID
            data.GetMenu = self.EventMenu
            data.iconPath = iconPath
            data.response = myResponse
            data.OnDblClick = self.DblClickEventEntry
            entry = listentry.Get('CalendarSingleDayEntry', data=data)
            scrolllist.append((sortBy, entry))

        scrolllist = uiutil.SortListOfTuples(scrolllist, reverse=includeUpdatedColumn)
        headers = [localization.GetByLabel('UI/Calendar/SingleDayWindow/Time'), localization.GetByLabel('UI/Calendar/SingleDayWindow/Title')]
        if includeUpdatedColumn:
            headers.append(localization.GetByLabel('UI/Calendar/CalendarWindow/LatestUpdates'))
        self.sr.eventScroll.Load(contentList=scrolllist, headers=headers, noContentHint=localization.GetByLabel('UI/Calendar/SingleDayWindow/NoPlannedEvents'))

    def EventMenu(self, entry, *args):
        eventInfo = entry.sr.node.eventInfo
        m = sm.GetService('calendar').GetEventMenu(eventInfo, entry.sr.node.response)
        return m

    def DblClickEventEntry(self, entry, *args):
        eventInfo = entry.sr.node.eventInfo
        self.OpenEvent(eventInfo)

    def OpenEvent(self, eventInfo, *args):
        sm.GetService('calendar').OpenEventWnd(eventInfo)

    def OnReloadCalendar(self, *args):
        showTag = sm.GetService('calendar').GetActiveTags()
        if self.isADay:
            eventDict = {}
            events = sm.GetService('calendar').GetEventsByMonthYear(self.month, self.year)
            for eventKV in events:
                if not eventKV.isDeleted:
                    year, month, wd, day, hour, minute, sec, ms = blue.os.GetTimeParts(eventKV.eventDateTime)
                    if (year, month, day) == self.date and (showTag is None or showTag & eventKV.flag != 0):
                        eventDict[eventKV.eventID] = eventKV

            self.events = eventDict
            self.LoadDaysEvents(eventDict)
        elif self.wndType == 'upcomingEvents':
            events = sm.GetService('calendar').GetMyNextEvents()
            self.events = events
            self.LoadDaysEvents(events)
        elif self.wndType == 'latestUpdates':
            events = sm.GetService('calendar').GetMyChangedEvents()
            self.events = events
            self.LoadDaysEvents(events)

    def OnCalendarFilterChange(self, *args):
        self.OnReloadCalendar()


class CalendarSingleDayEntry(listentry.Generic):
    __guid__ = 'listentry.CalendarSingleDayEntry'

    def Startup(self, *args):
        self.sr.statusIconCont = uiprimitives.Container(name='statusIconCont', parent=self, align=uiconst.TOPLEFT, pos=(0, 0, 16, 16))
        self.sr.flagIconCont = uiprimitives.Container(name='statusIconCont', parent=self, align=uiconst.TOPRIGHT, pos=(0, 0, 14, 14))
        FrameThemeColored(parent=self.sr.flagIconCont)
        listentry.Generic.Startup(self, args)

    def Load(self, node):
        listentry.Generic.Load(self, node)
        self.sr.label.left = 16
        self.LoadStatusIcon(node)
        sm.GetService('calendar').LoadTagIconInContainer(node.eventInfo.flag, self.sr.flagIconCont)
        if node.eventInfo.importance > 0:
            self.UpdateLabel(node)
        node.Set('sort_%s' % localization.GetByLabel('UI/Calendar/SingleDayWindow/Time'), node.eventInfo.eventDateTime)
        self.hint = sm.GetService('calendar').GetEventHint(node.eventInfo, node.response)
        self.sr.label.Update()

    def LoadStatusIcon(self, data):
        uiutil.Flush(self.sr.statusIconCont)
        icon = uicontrols.Icon(icon=data.iconPath, parent=self.sr.statusIconCont, align=uiconst.CENTERLEFT, pos=(0, 0, 16, 16))
        icon.hint = localization.GetByLabel(sm.GetService('calendar').GetResponseType().get(data.response, 'UI/Generic/Unknown'))

    def UpdateLabel(self, data):
        label = data.cleanLabel
        label = '<color=red>!</color> %s' % label
        self.sr.label.text = label
        self.sr.node.label = label
        self.sr.label.Update()


class EventList(uicontrols.EventListCore):
    """
        This is the super class for list of events, the todo list and the updated list
    """
    __guid__ = 'uicls.EventList'

    def SetupScroll(self, *args):
        self.sr.eventScroll = uicontrols.Scroll(name='eventScroll', parent=self)
        self.sr.eventScroll.scrollEnabled = 0
        self.sr.eventScroll.multiSelect = 0

    def LoadScroll(self, scrolllist, *args):
        scrolllist = scrolllist[:self.maxEntries]
        self.sr.eventScroll.Load(contentList=scrolllist, headers=[], noContentHint='')

    def AddMoreContFill(self, *args):
        self.sr.backgroundFrame = uicontrols.BumpedUnderlay(parent=self.sr.moreCont, padding=(-1, -1, -1, -1))
        icon = uicontrols.Icon(icon='ui_38_16_229', parent=self.sr.moreCont, pos=(0, -3, 16, 16), align=uiconst.CENTERTOP, idx=0, ignoreSize=True)
        icon.OnClick = self.OnMoreClick

    def GetEventEntry(self, eventInfo, *args):
        showTag = sm.GetService('calendar').GetActiveTags()
        if showTag is not None and showTag & eventInfo.flag == 0:
            return
        icon, myResponse = sm.GetService('calendar').GetMyResponseIconFromID(eventInfo.eventID, long=0, getDeleted=eventInfo.isDeleted)
        hint = localization.GetByLabel(sm.GetService('calendar').GetResponseType().get(myResponse, 'UI/Generic/Unknown'))
        data = util.KeyVal()
        data.label = eventInfo.eventTitle
        data.eventInfo = eventInfo
        data.icon = icon
        data.hint = hint
        data.response = myResponse
        entry = listentry.Get(self.listentryClass, data=data)
        return entry

    def OnMoreClick(self, *args):
        sm.GetService('calendar').OpenSingleDayWnd(self.header, '', '', '', self.events, isADay=0, wndType=self.listType)


class UpdateEventsList(EventList):
    """
        This is the todo list, list of upcoming events you have not rejected
    """
    __guid__ = 'uicls.UpdateEventsList'

    def GetEventEntryTuple(self, eventKV, *args):
        """
            returns either None or a tuple where first item is what to sort by
            and second item is the entry
        """
        entry = self.GetEventEntry(eventKV)
        if entry is None:
            return
        return (eventKV.dateModified, entry)

    def GetSortOrder(self, *args):
        return 1


class CalendarListEntry(listentry.Generic):
    __guid__ = 'listentry.CalendarListEntry'
    __notifyevents__ = []
    TEXTMARGIN = 2

    def Startup(self, *args):
        self.sr.statusIconCont = uiprimitives.Container(name='statusIconCont', parent=self, align=uiconst.TOPLEFT, pos=(0, 0, 16, 16))
        self.sr.tagIconCont = uiprimitives.Container(name='statusIconCont', parent=self, align=uiconst.TOPRIGHT, pos=(0, 0, 16, 16))
        uicontrols.Frame(parent=self.sr.statusIconCont)
        listentry.Generic.Startup(self, args)
        self.sr.label.align = uiconst.TOPLEFT
        self.sr.label.top = self.TEXTMARGIN
        self.sr.timeLabel = uicontrols.EveLabelMedium(text='', parent=self, left=20, top=14, state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT, maxLines=1, color=(0.7, 0.7, 0.7, 0.75))
        self.sr.fill = uicontrols.Frame(parent=self, name='fill', frameConst=uiconst.FRAME_FILLED_SHADOW_CORNER0, color=(1.0, 1.0, 1.0, 0.05))
        sm.RegisterNotify(self)

    def Load(self, node):
        listentry.Generic.Load(self, node)
        self.sr.label.left = 20
        eventInfo = node.eventInfo
        hint = self.GetEventHint(eventInfo, node.response)
        self.hint = hint
        if eventInfo.importance > 0:
            label = self.sr.node.label
            newLabel = '<color=red>!</color> %s' % label
            self.sr.label.text = newLabel
        self.SetTime(eventInfo.eventDateTime - eveLocalization.GetTimeDelta() * const.SEC)
        self.sr.timeLabel.top = self.sr.label.top + self.sr.label.height
        self.LoadStatusIcon()
        sm.GetService('calendar').LoadTagIconInContainer(eventInfo.flag, self.sr.tagIconCont)
        self.sr.label.Update()

    def GetMenu(self, *args):
        eventInfo = self.sr.node.eventInfo
        m = sm.GetService('calendar').GetEventMenu(eventInfo, self.sr.node.response)
        return m

    def GetEventHint(self, eventInfo, myResponse, *args):
        hint = sm.GetService('calendar').GetEventHint(eventInfo, myResponse)
        return hint

    def _OnClose(self):
        sm.UnregisterNotify(self)

    def LoadStatusIcon(self, *args):
        data = self.sr.node
        uiutil.Flush(self.sr.statusIconCont)
        iconPath = data.icon
        hint = data.hint
        icon = uicontrols.Icon(icon=iconPath, parent=self.sr.statusIconCont, align=uiconst.CENTER, pos=(0, 2, 16, 16))
        icon.hint = hint

    def GetHeight(self, node, width):
        labelWidth, labelHeight = uicontrols.EveLabelMedium.MeasureTextSize(node.label)
        timeWidth, timeHeight = uicontrols.EveLabelMedium.MeasureTextSize(util.FmtDate(node.eventInfo.eventDateTime, 'ls'))
        return CalendarListEntry.TEXTMARGIN * 2 + labelHeight + timeHeight

    def SetTime(self, eventDateTime, *args):
        self.sr.timeLabel.text = util.FmtDate(eventDateTime, 'ls')

    def OnDblClick(self, *args):
        sm.GetService('calendar').OpenEventWnd(self.sr.node.eventInfo)


class CalendarUpdatedEntry(CalendarListEntry):
    __guid__ = 'listentry.CalendarUpdatedEntry'

    def GetEventHint(self, eventInfo, myResponse, *args):
        eventDateTime = util.FmtDate(eventInfo.eventDateTime, 'ls')
        lastUpdatedTime = util.FmtDate(eventInfo.dateModified, 'ls')
        hint = localization.GetByLabel('UI/Calendar/EventWindow/LastUpdateHint', eventDateTime=eventDateTime, eventTitle=eventInfo.eventTitle, lastUpdatedTime=lastUpdatedTime)
        return hint
