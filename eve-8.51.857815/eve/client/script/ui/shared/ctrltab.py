#Embedded file name: eve/client/script/ui/shared\ctrltab.py
import math
import uicontrols
import carbonui.const as uiconst
import uiprimitives
import uthread
import uiutil
import uicls
import localization
ICONWIDTH = 50
SPACINGWIDTH = 6
NUMCOLS = 5
BORDER = 5
BLOCKSIZE = ICONWIDTH + SPACINGWIDTH
FRAMECOLOR = (0.3, 0.3, 0.3, 0.5)
FILLCOLOR = (0.0, 0.0, 0.0, 0.8)
SELECTCOLOR = (0.5, 0.5, 0.5, 0.5)

class CtrlTabWindow(uicontrols.Window):
    __guid__ = 'form.CtrlTabWindow'
    default_windowID = 'CtrlTabWindow'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self._caption = self.name = 'CtrlTabWindow'
        self.HideHeader()
        self.SetWndIcon(None)
        self.SetTopparentHeight(0)
        self.SetMainIconSize(0)
        self.MakeUncollapseable()
        self.MakeUnpinable()
        self.MakeUnMinimizable()
        self.MakeUnResizeable()
        self.MakeUnKillable()
        self.HideUnderlay()
        self.MakeUnstackable()
        uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEDOWN, self.OnGlobalMouseDown)
        uicontrols.Frame(parent=self, color=FRAMECOLOR)
        uiprimitives.Fill(parent=self, color=FILLCOLOR)
        self.currOpenWindows = uicore.registry.GetWindows()[:]
        self.showOrHide = self.AllWindowsMinimized()
        self.selectionBoxIndex = None
        self.windowIcons = []
        self.showOrHideMessage = [localization.GetByLabel('UI/Common/Windows/HideWindows'), localization.GetByLabel('UI/Common/Windows/ShowWindows')][self.showOrHide]
        self.InitializeWindowIcons()
        self.numIcons = len(self.windowIcons)
        self.numRows = int(math.ceil(float(self.numIcons) / float(NUMCOLS)))
        if self.numRows > 1:
            self.xShift = 0
        else:
            self.xShift = (NUMCOLS - self.numIcons) * BLOCKSIZE / 2
        uthread.new(self.SetWindowSize)
        self.RenderIcons()
        self.sr.selectionBox = uiprimitives.Container(name='selectionBox', parent=self.sr.main, align=uiconst.RELATIVE, pos=(SPACINGWIDTH,
         SPACINGWIDTH,
         ICONWIDTH,
         ICONWIDTH))
        uiprimitives.Fill(parent=self.sr.selectionBox, color=SELECTCOLOR)
        self.sr.selectionBoxMouse = uiprimitives.Container(name='selectionBox', parent=self.sr.main, align=uiconst.RELATIVE, pos=(SPACINGWIDTH,
         SPACINGWIDTH,
         ICONWIDTH,
         ICONWIDTH), state=uiconst.UI_HIDDEN)
        uiprimitives.Fill(parent=self.sr.selectionBoxMouse, color=SELECTCOLOR)
        self.sr.windowText = uicontrols.EveLabelLarge(parent=self.sr.main, align=uiconst.TOBOTTOM, color=(1, 1, 1, 1), state=uiconst.UI_DISABLED, padding=BORDER)

    def SetWindowSize(self):
        """ Set the size of the window (for some reason this can not be done without threading) """
        self.width = BLOCKSIZE * NUMCOLS + SPACINGWIDTH + 2 * BORDER + 2
        self.height = BLOCKSIZE * self.numRows + 3 * BORDER + self.sr.windowText.height

    def InitializeWindowIcons(self):
        """ 
            Check what windows are currently open and create a dictionary 
            (self.windowIcons) containing their necessary information 
        """
        currOpenWindows = [ wnd for wnd in uicore.registry.GetWindows() if not isinstance(wnd, uicontrols.WindowStack) ]
        self.windowIcons = []
        i = 0
        for w in currOpenWindows:
            if not hasattr(w, 'iconNum') or w._caption == self._caption or not isinstance(w, uicontrols.Window):
                continue
            if w.iconNum is not None and not w.iconNum.startswith('c_'):
                iconNum = w.iconNum
            else:
                iconNum = 'ui_105_64_45'
            self.windowIcons.append({'id': i,
             'name': w.windowID,
             'caption': w._caption,
             'iconNum': iconNum})
            i += 1

        self.windowIcons.append({'id': len(self.windowIcons),
         'name': self.showOrHideMessage,
         'caption': self.showOrHideMessage,
         'iconNum': 'res:/UI/texture/WindowIcons/hidewindows.png',
         'isShowOrHideIcon': True})

    def RenderSelectionBox(self):
        """ Render the selection box controlled by the keyboard (ctrl+tab, ctrl+shift+tab) """
        self.sr.selectionBox.left, self.sr.selectionBox.top = self.IndexToPosition(self.selectionBoxIndex)

    def RenderSelectionBoxMouse(self):
        """ Render the selection box controlled by mouse hovering """
        self.sr.selectionBox.left, self.sr.selectionBox.top = self.IndexToPosition(self.selectionBoxIndex)

    def RenderIcons(self):
        """ Render all icons in its correct position """
        for i, w in enumerate(self.windowIcons):
            x, y = self.IndexToPosition(i)
            icon = uicontrols.Icon(icon=w['iconNum'], parent=self.sr.main, pos=(x,
             y,
             ICONWIDTH,
             ICONWIDTH), ignoreSize=1)
            icon.OnMouseEnter = (self.OnMouseEnterIcon, w)
            icon.OnMouseExit = self.OnMouseLeaveIcon
            icon.OnClick = (self.OnMouseClickIcon, w)

    def SetText(self, text):
        self.sr.windowText.text = '<center>' + text
        self.SetWindowSize()

    def OnMouseEnterIcon(self, icon):
        if icon['id'] != self.selectionBoxIndex:
            self.sr.selectionBoxMouse.state = uiconst.UI_NORMAL
            self.sr.selectionBoxMouse.left, self.sr.selectionBoxMouse.top = self.IndexToPosition(icon['id'])
            self.SetText(icon['caption'])

    def OnMouseLeaveIcon(self):
        self.sr.selectionBoxMouse.state = uiconst.UI_HIDDEN
        if self.selectionBoxIndex is not None:
            self.SetText(self.windowIcons[self.selectionBoxIndex]['caption'])

    def OnMouseClickIcon(self, icon):
        self.selectionBoxIndex = icon['id']
        self.ChooseHilited()

    def IndexToPosition(self, index):
        """ calculate correct (x,y) for an icon, given it's index """
        colNum = index % NUMCOLS
        rowNum = (index - colNum) / NUMCOLS
        xPos = self.xShift + SPACINGWIDTH + colNum * BLOCKSIZE + BORDER
        yPos = SPACINGWIDTH + rowNum * BLOCKSIZE + BORDER
        return (xPos, yPos)

    def Next(self):
        """ Select next icon. Fired by ctrl+shift+tab """
        self.Maximize()
        if self.selectionBoxIndex is None:
            self.selectionBoxIndex = 0
        else:
            self.selectionBoxIndex = self.selectionBoxIndex + 1
            if self.selectionBoxIndex >= self.numIcons:
                self.selectionBoxIndex = 0
        self.RenderSelectionBox()
        caption = self.windowIcons[self.selectionBoxIndex]['caption']
        if caption is None or len(caption) == 0:
            self.SetText(' ')
        else:
            self.SetText(self.windowIcons[self.selectionBoxIndex]['caption'])

    def Prev(self):
        """ Select previous icon. Fired by ctrl+shift+tab """
        self.Maximize()
        if self.selectionBoxIndex is None:
            self.selectionBoxIndex = self.numIcons - 1
        else:
            self.selectionBoxIndex = self.selectionBoxIndex - 1
            if self.selectionBoxIndex < 0:
                self.selectionBoxIndex = self.numIcons - 1
        self.RenderSelectionBox()
        caption = self.windowIcons[self.selectionBoxIndex]['caption']
        if caption is None or len(caption) == 0:
            self.SetText(' ')
        else:
            self.SetText(self.windowIcons[self.selectionBoxIndex]['caption'])

    def ChooseHilited(self):
        """ Perform the action associated with currently selected icon. Fired when ctrl+tab is released """
        winIcon = self.windowIcons[self.selectionBoxIndex]
        if 'isShowOrHideIcon' in winIcon:
            self.showOrHide = int(not self.showOrHide)
            if self.showOrHide:
                uicore.cmd.CmdMinimizeAllWindows()
            else:
                for w in self.currOpenWindows:
                    if not w.InStack() and not getattr(w, 'isImplanted', False):
                        uthread.new(w.Maximize)

        else:
            win = uicontrols.Window.GetIfOpen(windowID=winIcon['name'])
            self.currOpenWindows.remove(win)
            self.currOpenWindows.insert(0, win)
            win.Maximize()
        self.Close()

    def AllWindowsMinimized(self):
        """ 
            Check if all currently open windows are minimized, 
            given that they can be minimized and are not on stacks 
        """
        for w in self.currOpenWindows:
            if w.state != uiconst.UI_HIDDEN and w.sr.stack is None and w._minimizable:
                return False

        return True

    def OnGlobalMouseDown(self, downOn, *args, **kw):
        """ Close if a user clicks outside the window """
        if not uiutil.IsUnder(downOn, self.sr.main):
            self.Close()
