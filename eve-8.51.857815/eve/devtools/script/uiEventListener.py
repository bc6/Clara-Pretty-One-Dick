#Embedded file name: eve/devtools/script\uiEventListener.py
"""
An insider tool that makes it easy to see what the heck is going on with input events
"""
import uiprimitives
import uicontrols
import carbonui.const as uiconst
import blue
import uiutil
import util
import uthread
import form
import trinity
from .uiEventListenerConsts import wmConst

class UIEventListener(uicontrols.Window):
    """ An Insider window which makes it easy to debug UI events """
    __guid__ = 'form.UIEventListener'
    default_windowID = 'UIEventListener'
    default_width = 450
    default_height = 300
    default_topParentHeight = 0
    default_minSize = (default_width, default_height)
    default_caption = 'UI Event Listener'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.tabs = uicontrols.TabGroup(parent=self.sr.maincontainer)
        self.windowsEventPanel = WindowsEventPanel(parent=self.sr.maincontainer)
        self.uiEventPanel = UIEventPanel(parent=self.sr.maincontainer)
        self.uiGlobalEventPanel = UIGlobalEventPanel(parent=self.sr.maincontainer)
        self.shortcutPanel = UIShortcutPanel(parent=self.sr.maincontainer)
        self.helpPanel = HelpPanel(parent=self.sr.maincontainer)
        tabs = (util.KeyVal(name='windowsEvents', label='Windows events', panel=self.windowsEventPanel),
         util.KeyVal(name='uiEvents', label='UI events', panel=self.uiEventPanel),
         util.KeyVal(name='uiGlobalEvents', label='UI global events', panel=self.uiGlobalEventPanel),
         util.KeyVal(name='shortcuts', label='Shortcuts', panel=self.shortcutPanel),
         util.KeyVal(name='help', label='Help', panel=self.helpPanel))
        self.tabs.LoadTabs(tabs)


class BaseEventPanel(uiprimitives.Container):
    __guid__ = 'uiEventListener.BaseEventPanel'

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.events = []
        self.settingsName = self.__guid__.split('.')[1] + 'ignoreEvents'
        settings.user.ui.Set(self.settingsName, self.default_ignoreEvents)
        self.ignoreEvents = settings.user.ui.Get(self.settingsName, self.default_ignoreEvents)
        self.updatePending = False
        self.showMax = 100
        self.scrollUpdateRequested = False
        self.isPaused = False
        self.rightCont = uiprimitives.Container(name='rightCont', parent=self, align=uiconst.TORIGHT, width=150, padding=3)
        uicontrols.Label(parent=self.rightCont, align=uiconst.TOTOP, text='<color=red>IGNORE LIST</color>')
        uicontrols.Label(parent=self.rightCont, align=uiconst.TOBOTTOM, text='Right-click logged entries to add that event type to ignore')
        self.ignoreScroll = uicontrols.Scroll(parent=self.rightCont, align=uiconst.TOALL)
        self._UpdateIgnoreScroll()
        btns = (('Clear', self.ResetEventData, ()), ('<color=green>Pause logging</color>', self.PauseResumeLogging, ()))
        btnGroup = uicontrols.ButtonGroup(parent=self, btns=btns)
        self.pauseResumeBtn = btnGroup.GetBtnByIdx(1)
        self.scroll = uicontrols.Scroll(parent=self, align=uiconst.TOALL, padding=3)
        uthread.new(self._UpdateScrollThread)

    def OnTabSelect(self):
        self.UpdateScroll()

    def ResetEventData(self):
        self.events = []
        self.scroll.Clear()

    def PauseResumeLogging(self):
        self.isPaused = not self.isPaused
        if self.isPaused:
            label = '<color=yellow>Resume logging</color>'
        else:
            label = '<color=green>Pause logging</color>'
        self.pauseResumeBtn.SetLabel(label)

    def AddEvent(self, **kw):
        time = self._GetTimestampText()
        event = util.KeyVal(**kw)
        if event.id not in self.ignoreEvents:
            self.events.insert(0, (time, event))
            self.UpdateScroll()

    def UpdateScroll(self):
        if not self.display:
            return
        self.scrollUpdateRequested = True

    def _UpdateScrollThread(self):
        """
        This mechanism makes sure we don't update the scroll too frequently
        """
        updateDelay = 200
        while not self.destroyed:
            if self.scrollUpdateRequested:
                self._UpdateScroll()
                self.scrollUpdateRequested = False
                blue.synchro.SleepWallclock(updateDelay)
            else:
                blue.synchro.Yield()

    def _UpdateScroll(self):
        if self.isPaused:
            return
        wndAbove = uiutil.GetWindowAbove(uicore.uilib.mouseOver)
        if isinstance(wndAbove, form.UIEventListener) and uicore.uilib.rightbtn:
            return
        scrolllist = []
        lastTime = None
        for time, event in self.events[:self.showMax]:
            if lastTime == time:
                time = ''
            else:
                lastTime = time
            label = time + '<t>' + self.GetScrollLabel(event)
            scrolllist.append(uicontrols.ScrollEntryNode(decoClass=uicontrols.SE_GenericCore, label=label, fontsize=14, event=event, OnGetMenu=self.GetScrollEntryMenu))

        self.scroll.Load(contentList=scrolllist, headers=self.SCROLL_HEADERS, ignoreSort=True)

    def GetScrollEntryMenu(self, entry):
        return (('Add to ignore', self.AddEventToIgnore, (entry,)),)

    def _UpdateIgnoreScroll(self):
        scrolllist = []
        for id, name in self.ignoreEvents.iteritems():
            scrolllist.append(uicontrols.ScrollEntryNode(decoClass=uicontrols.SE_GenericCore, label=name, id=id, fontsize=14, OnMouseDown=self.RemoveEventFromIgnore))

        self.ignoreScroll.Load(contentList=scrolllist)

    def AddEventToIgnore(self, entry):
        event = entry.sr.node.event
        self.ignoreEvents[event.id] = event.name
        settings.user.ui.Set(self.settingsName, self.ignoreEvents)
        self._UpdateIgnoreScroll()

    def RemoveEventFromIgnore(self, entry):
        node = entry.sr.node
        if node.id in self.ignoreEvents:
            self.ignoreEvents.pop(node.id)
            settings.user.ui.Set(self.settingsName, self.ignoreEvents)
        self._UpdateIgnoreScroll()

    def _GetTimestampText(self):
        year, month, weekday, day, hour, minute, second, msec = blue.os.GetTimeParts(blue.os.GetWallclockTime())
        return '%02i:%02i:%02i.%03i' % (hour,
         minute,
         second,
         msec)


class WindowsEventPanel(BaseEventPanel):
    """ Raw windows events  """
    __guid__ = 'uiEventListener.WindowsEventPanel'
    SCROLL_HEADERS = ['time',
     'msgID',
     'wParam',
     'lParam',
     'details']
    default_ignoreEvents = {wmConst.WM_MOUSEMOVE: 'WM_MOUSEMOVE',
     wmConst.WM_NCHITTEST: 'WM_NCHITTEST',
     wmConst.WM_GETDLGCODE: 'WM_GETDLGCODE'}

    def ApplyAttributes(self, attributes):
        BaseEventPanel.ApplyAttributes(self, attributes)
        self.leftCont = uiprimitives.Container(name='leftCont', parent=self, align=uiconst.TOLEFT, width=100)
        trinity.app.eventHandler = self.OnAppEvent

    def OnAppEvent(self, msgID, wParam, lParam):
        uicore.uilib.OnAppEvent(msgID, wParam, lParam)
        msgName = wmConst().GetMSGName(msgID)
        self.AddEvent(id=msgID, name=msgName, wParam=wParam, lParam=lParam)

    def _OnClose(self):
        trinity.app.eventHandler = uicore.uilib.OnAppEvent

    def GetScrollLabel(self, event):
        if event.name is None:
            event.name = '<color=red>%s</color>' % hex(event.id).upper()
        details = self.GetDetails(event.id, event.wParam, event.lParam)
        label = '%s<t>%s<t>%s<t>%s' % (event.name,
         hex(event.wParam).upper(),
         hex(event.lParam).upper(),
         details)
        return label

    def GetDetails(self, msgID, wParam, lParam):
        """
        Get more useful details for specific message types
        """
        if msgID in (wmConst.WM_KEYDOWN,
         wmConst.WM_KEYUP,
         wmConst.WM_SYSKEYDOWN,
         wmConst.WM_SYSKEYUP):
            vk = uicore.cmd.GetKeyNameFromVK(wParam)
            if msgID == wmConst.WM_KEYDOWN:
                repeatCount = lParam & 65535
                if repeatCount > 1:
                    vk += ', repeatCount=%s' % repeatCount
            return vk
        if msgID == wmConst.WM_CHAR:
            return unichr(wParam)
        if msgID in (wmConst.WM_XBUTTONDOWN, wmConst.WM_XBUTTONUP):
            if wParam & 65536:
                return 'XBUTTON1'
            else:
                return 'XBUTTON2'
        return '-'


class UIEventPanel(BaseEventPanel):
    """ Basic UI input events such as OnClick or OnKeyDown """
    __guid__ = 'uiEventListener.UIEventPanel'
    SCROLL_HEADERS = ['time',
     'eventID',
     'object name',
     'object id',
     'class',
     'args',
     'param']
    default_ignoreEvents = {uiconst.UI_MOUSEENTER: 'OnMouseEnter',
     uiconst.UI_MOUSEEXIT: 'OnMouseExit',
     uiconst.UI_MOUSEHOVER: 'OnMouseHover',
     uiconst.UI_MOUSEMOVE: 'OnMouseMove'}

    def ApplyAttributes(self, attributes):
        BaseEventPanel.ApplyAttributes(self, attributes)
        self.realEventHandler = uicore.uilib._TryExecuteHandler
        uicore.uilib._TryExecuteHandler = self._TryExecuteHandler

    def _TryExecuteHandler(self, eventID, obj, eventArgs = None, param = None):
        handlerObj = self.realEventHandler(eventID, obj, eventArgs, param)
        if handlerObj:
            name = uicore.uilib.EVENTMAP[eventID]
            self.AddEvent(id=eventID, name=name, obj=obj, eventArgs=eventArgs, param=param)

    def _OnClose(self):
        uicore.uilib._TryExecuteHandler = self.realEventHandler

    def GetScrollLabel(self, event):
        return '%s<t>%s<t>%s<t>%s<t>%s<t>%s' % (event.name,
         event.obj.name,
         hex(id(event.obj)).upper(),
         event.obj.__guid__,
         event.eventArgs,
         event.param)


class UIGlobalEventPanel(BaseEventPanel):
    """ Global UI events, registered through uilib.RegisterForTriUIEvents """
    __guid__ = 'uiEventListener.UIGlobalEventPanel'
    SCROLL_HEADERS = ['time',
     'eventID',
     'called function',
     'winParams',
     'args',
     'kw']
    default_ignoreEvents = {}

    def ApplyAttributes(self, attributes):
        BaseEventPanel.ApplyAttributes(self, attributes)
        self.realEventHandler = uicore.uilib.CheckCallbacks
        uicore.uilib.CheckCallbacks = self.CheckCallbacks

    def CheckCallbacks(self, obj, msgID, param):
        callbackDict = uicore.uilib._triuiRegsByMsgID.get(msgID, {})
        for cookie, (wr, args, kw) in callbackDict.items():
            func = wr()
            name = uicore.uilib.EVENTMAP.get(msgID, '<color=red>%s</color>' % msgID)
            self.AddEvent(id=msgID, name=name, func=func, winParams=param, args=args, kw=kw)

        self.realEventHandler(obj, msgID, param)

    def _OnClose(self):
        uicore.uilib.CheckCallbacks = self.realEventHandler

    def GetScrollLabel(self, event):
        func = event.func
        if func:
            func = '%s.%s' % (func.im_class.__guid__, func.im_func.func_name)
        return '%s<t>%s<t>%s<t>%s<t>%s' % (event.name,
         func,
         event.winParams,
         event.args,
         event.kw)


class UIShortcutPanel(BaseEventPanel):
    """ Game shortcuts """
    __guid__ = 'uiEventListener.UIShortcutPanel'
    SCROLL_HEADERS = ['time', 'name']
    default_ignoreEvents = {}
    __notifyevents__ = ('OnCommandExecuted',)

    def ApplyAttributes(self, attributes):
        BaseEventPanel.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)

    def OnCommandExecuted(self, name):
        self.AddEvent(id=name, name=name)

    def GetScrollLabel(self, event):
        return event.name


class HelpPanel(uiprimitives.Container):
    __guid__ = 'uiEventListener.HelpPanel'

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        text = '\n<b>Windows events:</b> These are raw operating system events that are cought by trinity and forwarded to uicore.uilib (uilib.py) where they are processed and used to execute UI events, UI global events and shortcuts.\n\n<b>UI events:</b> UI events coming from uilib are handled by bound methods, defined in UI classes. To catch one of those events, simply define the appropriately named method within your class (OnClick for example). The meaning of the arguments passed on to the event handlers differ between events.    \n\n<b>UI global events:</b> In some cases it can be useful to listen to global events. For example, a container might be interested to know when the mouse is clicked, regardless of what is being clicked. This can be achieved by registering an event listener through uicore.uilib.RegisterForTriuiEvents\n\n<b>Shortcuts:</b> Shortcut key commands are handled in uicore.cmd (command.py and game specific file such as evecommands.py). \n'
        uicontrols.Label(parent=self, align=uiconst.TOALL, text=text, padding=10, fontsize=13)
