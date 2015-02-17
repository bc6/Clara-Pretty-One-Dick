#Embedded file name: eve/devtools/script\windowMonitor.py
import form
import string
import carbonui.const as uiconst
import listentry
import uthread
import blue
import uicontrols
import uiprimitives

class WindowMonitor(uicontrols.Window):
    __guid__ = 'form.WindowMonitor'
    default_windowID = 'WindowMonitor'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.filePath = blue.paths.ResolvePathForWriting(u'settings:/windowmonitor.txt')
        self.SetCaption('Window Monitor')
        self.SetTopparentHeight(0)
        topCont = uiprimitives.Container(parent=self.sr.main, align=uiconst.TOALL, height=95)
        margin = 10
        self.openedScroll = uicontrols.Scroll(parent=topCont, padding=(margin,
         margin,
         margin,
         0), align=uiconst.TOLEFT, width=150)
        self.allWindowsScroll = uicontrols.Scroll(parent=topCont, padding=(0,
         margin,
         margin,
         0), align=uiconst.TOALL)
        self.messageScroll = uicontrols.Scroll(parent=self.sr.main, padding=(margin,
         0,
         margin,
         margin), align=uiconst.TOBOTTOM, height=50)
        self.messageScroll.Load(contentList=[], headers=[], scrollTo=0)
        midCont = uiprimitives.Container(parent=self.sr.main, align=uiconst.TOBOTTOM, padding=(0, 5, 0, 5), height=25)
        self.infoLabel = uicontrols.Label(text='', parent=midCont, align=uiconst.CENTERLEFT, left=margin, state=uiconst.UI_NORMAL)
        self.infoLabel.OnClick = self.OpenPrefs
        self.infoLabel.hint = 'Click to open windowmonitor save file location.'
        uicontrols.Button(parent=midCont, label='Clear', align=uiconst.TORIGHT, left=margin, func=self.Clear)
        self.DoSetup()

    def OpenPrefs(self, *args):
        blue.os.ShellExecute(blue.paths.ResolvePath(u'settings:/'))

    def DoSetup(self):
        registry = sm.GetService('registry')
        self.allWindows = [ wnd for wnd in dir(form) if wnd[0] != '_' ]
        self.InitOpenedWindows()
        self.messageScroll.Load(contentList=[], headers=[], scrollTo=0)
        self.RefreshUI()
        if type(registry.windows) is list or str(type(registry.windows)) == str(CallbackList):
            l = CallbackList([ w for w in registry.GetWindows() ], func=self.WindowAdded)
            registry.windows = l
        else:
            self.AddMessage("Could not initialise window monitor - monitoring won't work.")

    def InitOpenedWindows(self):
        self.openedWindows = []
        self.GetOpenedWindows()

    def GetOpenedWindows(self):
        self.LoadFromRegistry()
        self.LoadFromFile()
        self.SaveToFile()

    def WindowAdded(self, thing):
        formName = string.replace(thing.__guid__, 'form.', '')
        if formName in self.allWindows:
            if formName not in self.openedWindows:
                self.OpenedWindow(formName)
            else:
                self.AddMessage('form.' + formName + ' has already been opened')
        else:
            self.AddMessage('form.' + formName + ' not in found in form list')

    def OpenedWindow(self, formName):
        self.openedWindows.append(formName)
        self.SaveToFile()
        self.RefreshUI()
        self.AddMessage('form.' + formName + ' opened')
        if len(self.openedWindows) == 10:
            eve.Message('CustomNotify', {'notify': 'Achievement unlocked: Only Fools And Horses\n\n10 windows opened'})
        elif len(self.openedWindows) == 20:
            eve.Message('CustomNotify', {'notify': 'Achievement unlocked: Window Cleaner\n\n20 windows opened'})
        elif len(self.openedWindows) == 50:
            eve.Message('CustomNotify', {'notify': 'Achievement unlocked: Jolly Good Form\n\n50 windows opened'})
        elif len(self.openedWindows) == 100:
            eve.Message('CustomNotify', {'notify': 'Achievement unlocked: No More Easy Ones\n\n100 windows opened'})
        elif len(self.openedWindows) == 200:
            eve.Message('CustomNotify', {'notify': 'Achievement unlocked: Richard D James\n\n200 windows opened'})

    def RemoveOpenedWindow(self, formName):
        self.openedWindows.remove(formName)
        self.SaveToFile()
        self.RefreshUI()
        self.AddMessage('form.' + formName + ' removed from opened windows list')

    def RefreshUI(self):
        self.LoadOpenedScroll()
        self.UpdateInfoLabel()
        self.LoadAllWindowsScroll()

    def UpdateInfoLabel(self):
        self.infoLabel.text = 'You have opened ' + str(len(self.openedWindows)) + '/' + str(len(self.allWindows)) + ' windows.'
        self.SetCaption('Window Monitor - ' + str(len(self.openedWindows)) + '/' + str(len(self.allWindows)) + ' opened')

    def LoadOpenedScroll(self):
        msgs = []
        for n in self.openedWindows:
            msgs.append(listentry.Get('WindowMonitorEntry', {'text': n,
             'line': 1}))

        self.openedScroll.Load(contentList=msgs, headers=[], noContentHint='arse')
        self.openedScroll.Sort(by='text')

    def LoadAllWindowsScroll(self):
        msgs = []
        for n in self.allWindows:
            if n not in self.openedWindows:
                msgs.append(listentry.Get('WindowMonitorEntry', {'text': n,
                 'line': 1}))

        self.allWindowsScroll.Load(contentList=msgs, headers=[], noContentHint='arse')

    def AddMessage(self, message):
        msgs = []
        msgs.append(listentry.Get('Text', {'text': message,
         'line': 1}))
        self.messageScroll.AddEntries(0, msgs)

    def SaveToFile(self):
        textFile = open(self.filePath, 'w')
        lines = [ line + '\n' for line in self.openedWindows ]
        textFile.writelines(lines)
        textFile.close()

    def LoadFromRegistry(self):
        registry = sm.GetService('registry')
        for wnd in registry.windows:
            name = string.replace(wnd.__guid__, 'form.', '')
            if name in self.allWindows and name not in self.openedWindows:
                self.openedWindows.append(name)

    def LoadFromFile(self):
        try:
            textFile = open(self.filePath, 'r')
        except:
            return

        lines = [ l.strip() for l in textFile.readlines() ]
        textFile.close()
        for l in lines:
            if l in self.allWindows and l not in self.openedWindows:
                self.openedWindows.append(l)

    def Clear(self, *args):
        if sm.GetService('gameui').MessageBox('You will not be able to undo this!', 'Really clear opened windows?')[0] == 1:
            textFile = open(self.filePath, 'w')
            lines = ['']
            textFile.writelines(lines)
            self.DoSetup()

    def ToggleSelectedEntry(self, *args):
        selected = args[0]
        if selected is not None:
            if selected in self.openedWindows:
                self.RemoveOpenedWindow(selected)
            elif selected in self.allWindows:
                self.OpenedWindow(selected)


class WindowMonitorEntry(listentry.Text):
    __guid__ = 'listentry.WindowMonitorEntry'

    def Startup(self, *args):
        listentry.Text.Startup(self, *args)

    def GetMenu(self):
        m = []
        selected = self.sr.node.Get('text', None)
        m.append((selected, self.CopyText))
        m.append(None)
        try:
            window = form.__getattribute__(selected)
            filePath = window.ApplyAttributes.func_code.co_filename
            m.append((filePath, self.CopyPath))
        except:
            pass

        f = form.WindowMonitor.GetIfOpen().ToggleSelectedEntry
        m.append(('Toggle', f, (selected,)))
        return m

    def CopyPath(self):
        try:
            selected = self.sr.node.Get('text', None)
            window = form.__getattribute__(selected)
            filePath = window.ApplyAttributes.func_code.co_filename
            blue.pyos.SetClipboardData(filePath)
        except:
            pass


class CallbackList(list):

    def __init__(self, value = [], func = None):
        list.__init__(self, value)
        self.func = func

    def append(self, thing):
        try:
            uthread.new(self.func, thing)
        except Exception as e:
            print e
        finally:
            return list.append(self, thing)
