#Embedded file name: eve/client/script/ui/control\fileDialog.py
import uiprimitives
import uicontrols
from eve.client.script.ui.control.entries import Generic
from ..util import uix2
import uiutil
import util
import blue
import carbonui.const as uiconst
import os
import ctypes
import localization

class FileDialogEntry(Generic):
    """ 
        A listentry for the file dialog 
    """
    __guid__ = 'listentry.FileDialog'

    def Startup(self, *args):
        Generic.Startup(self)
        self.sr.icon = uicontrols.Icon(icon='res:/ui/Texture/WindowIcons/smallfolder.png', parent=self, pos=(6, 0, 16, 16), ignoreSize=1)

    def Load(self, node):
        Generic.Load(self, node)
        if self.sr.node.isDir:
            self.sr.icon.state = uiconst.UI_DISABLED
        elif self.sr.icon:
            self.sr.icon.state = uiconst.UI_HIDDEN


class FileDialog(uicontrols.Window):
    """ 
        A modal window to open system files and folders 
    """
    __guid__ = 'form.FileDialog'
    default_path = None
    default_fileExtensions = None
    default_multiSelect = False
    default_selectionType = uix2.SEL_FILES

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        path = attributes.path
        fileExtensions = attributes.fileExtensions
        multiSelect = attributes.multiSelect or self.default_multiSelect
        selectionType = attributes.selectionType or self.default_selectionType
        self.SetWndIcon(None)
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        if not multiSelect:
            caption = {uix2.SEL_FILES: localization.GetByLabel('UI/Control/FileDialog/SelectFile'),
             uix2.SEL_FOLDERS: localization.GetByLabel('UI/Control/FileDialog/SelectFolder'),
             uix2.SEL_BOTH: localization.GetByLabel('UI/Control/FileDialog/SelectFileOrfolder')}.get(selectionType)
        else:
            caption = {uix2.SEL_FILES: localization.GetByLabel('UI/Control/FileDialog/SelectFiles'),
             uix2.SEL_FOLDERS: localization.GetByLabel('UI/Control/FileDialog/SelectFolders'),
             uix2.SEL_BOTH: localization.GetByLabel('UI/Control/FileDialog/SelectFilesOrFolders')}.get(selectionType)
        if fileExtensions:
            caption = localization.GetByLabel('UI/Control/FileDialog/CaptionWithFileExtensions', caption=caption, fileExtensions=localization.formatters.FormatGenericList(fileExtensions))
        self.SetCaption(caption)
        self.selectionType = selectionType
        if fileExtensions:
            self.fileExtensions = [ f.replace('.', '').lower() for f in fileExtensions ]
        else:
            self.fileExtensions = None
        topCont = uiprimitives.Container(name='topCont', parent=self.sr.main, align=uiconst.TOTOP, pos=(0, 0, 0, 40), padding=(0, 20, 0, 0))
        icon = uicontrols.Icon(icon='res:/ui/Texture/WindowIcons/smallfolder.png', parent=self.sr.main, pos=(3, 16, 28, 28), ignoreSize=1)
        self.sr.pathEdit = uicontrols.SinglelineEdit(name='currentLocationEdit', parent=topCont, pos=(38, 0, 290, 0), label=localization.GetByLabel('UI/Common/Location'))
        self.sr.pathEdit.OnReturn = self.OnPathEnteredIntoEdit
        options = self.GetAvailableDrives()
        self.sr.driveSelectCombo = uicontrols.Combo(parent=self.sr.main, label=localization.GetByLabel('UI/Control/FileDialog/Drive'), options=options, name='driveSelectCombo', select=None, callback=self.OnDriveSelected, pos=(340, 22, 0, 0), width=50, align=uiconst.TOPLEFT)
        if not options:
            self.sr.driveSelectCombo.state = uiconst.UI_HIDDEN
        btns = [[localization.GetByLabel('UI/Common/Buttons/OK'),
          self.OnOK,
          (),
          81], [localization.GetByLabel('UI/Common/Buttons/Cancel'),
          self.OnCancel,
          (),
          81]]
        self.sr.standardBtns = uicontrols.ButtonGroup(btns=btns, parent=self.sr.main)
        self.SetOKButtonState(enabled=self.selectionType != uix2.SEL_FILES)
        scrollCont = uiprimitives.Container(name='scrollCont', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(0, 0, 6, 6))
        self.sr.scroll = uicontrols.Scroll(parent=scrollCont, name='fileFolderScroll', padLeft=5)
        self.sr.scroll.multiSelect = multiSelect
        self.sr.scroll.OnSelectionChange = self.VerifySelectedEnties
        self.sr.scroll.Sort = lambda *args, **kw: None
        if path is None or not os.path.isdir(path):
            path = settings.user.ui.Get('fileDialogLastPath', blue.paths.ResolvePath(u'app:/'))
        self.LoadDirToScroll(path)

    def GetAvailableDrives(self):
        try:
            length = ctypes.windll.kernel32.GetLogicalDriveStringsA(0, '')
            buffer = ctypes.create_string_buffer(length + 1)
            length = ctypes.windll.kernel32.GetLogicalDriveStringsA(length, buffer)
            drives = buffer.raw[:length].split('\x00')
        except:
            eve.Message('FileDialogUnableToAccessDrives', {}, uiconst.OK)
            return None

        ret = []
        for i, d in enumerate(drives):
            if d:
                ret.append((d, i))

        return ret

    def Confirm(self):
        """
            This is executed when RETURN is pressed in a modal window
        """
        if len(self.GetSelected(multi=True)) > 0:
            self.OnDblClick()

    def OnDriveSelected(self, combo, drive, index):
        if os.path.isdir(drive):
            self.LoadDirToScroll(drive)
        else:
            eve.Message('FileDialogUnableToAccessDrive', {}, uiconst.OK)

    def OnPathEnteredIntoEdit(self):
        path = self.sr.pathEdit.GetValue()
        if os.path.isdir(path):
            self.LoadDirToScroll(path)

    def OnOK(self):
        selected = self.GetSelected()
        self.result = self.GetReturnValue()
        settings.user.ui.Set('fileDialogLastPath', self.lastEnteredPath)
        self.SetModalResult(1)

    def GetReturnValue(self):
        """
            Prepare return value, given the current selection. The return value is a keyval
            with two lists, "files" and "folders", each containing full file paths for the
            selected files/folders.
        """
        selected = self.GetSelected(multi=True)
        retval = util.KeyVal(files=[], folders=[])
        if len(selected) == 0 and self.selectionType != uix2.SEL_FILES:
            retval.folders.append(self.sr.pathEdit.GetValue())
        for s in selected:
            if s.isDir:
                if s.isFolderUp:
                    retval.folders.append(self.sr.pathEdit.GetValue())
                else:
                    retval.folders.append(s.filePath)
            else:
                retval.files.append(s.filePath)

        return retval

    def OnCancel(self):
        self.Close()

    def GetSelected(self, multi = False):
        """
            Get currently selected files/folders
        """
        selected = self.sr.scroll.GetSelected()
        if not selected:
            return []
        elif not multi:
            return selected[0]
        else:
            return selected

    def OnDblClick(self, *args):
        """
            An entry in the scroll double clicked
        """
        selected = self.GetSelected()
        if selected.isDir:
            self.LoadDirToScroll(selected.filePath)
            self.sr.scroll.SelectNode(self.sr.scroll.GetNode(0))
        else:
            self.OnOK()

    def VerifySelectedEnties(self, *args):
        """
            Check if the OK button should be enabled, given current selection in the scroll
            and current settings.
        """
        selected = self.GetSelected(multi=True)
        sm.ScatterEvent('OnFileDialogSelection', selected)
        for s in selected:
            if self._IsEntryInvalid(s):
                self.SetOKButtonState(enabled=False)
                return

        self.SetOKButtonState(enabled=True)

    def _IsEntryInvalid(self, entry):
        return entry.isFolderUp and self.selectionType == uix2.SEL_FILES or entry.isDir and self.selectionType == uix2.SEL_FILES or not entry.isDir and self.selectionType == uix2.SEL_FOLDERS

    def SetOKButtonState(self, enabled):
        btn = self.sr.standardBtns.GetBtnByLabel(localization.GetByLabel('UI/Common/Buttons/OK'))
        if enabled:
            btn.Enable()
        else:
            btn.Disable()

    def EntryShouldBeDisplayed(self, filePath, isDir):
        """
            Check if a file/folder should be displayed, given the current settings
        """
        if self.selectionType == uix2.SEL_FOLDERS and not isDir:
            return False
        extension = os.path.splitext(filePath)[1].replace('.', '').lower()
        if not isDir and self.fileExtensions and extension not in self.fileExtensions:
            return False
        return True

    def LoadDirToScroll(self, path):
        """ 
            Display the passed file path in the mainscroll
        """
        scrolllist = []
        path = os.path.abspath(path)
        try:
            fileList = os.listdir(path)
        except:
            eve.Message('FileDialogUnableToAccessFolder')
            return

        self.lastEnteredPath = path
        fileList.append('..')
        import listentry
        for f in fileList:
            f = unicode(f)
            data = util.KeyVal()
            data.label = u'<t>%s' % f
            data.hint = f
            data.filePath = os.path.join(path, f)
            data.isDir = os.path.isdir(data.filePath)
            data.OnDblClick = self.OnDblClick
            data.charIndex = f
            if not self.EntryShouldBeDisplayed(f, data.isDir):
                continue
            sortBy = f.lower()
            if data.isDir:
                if f == '..':
                    sortBy = '  ' + sortBy
                    data.isFolderUp = True
                else:
                    sortBy = ' ' + sortBy
            scrolllist.append((sortBy, listentry.Get('FileDialog', data=data)))

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        self.sr.scroll.Load(contentList=scrolllist, headers=['', localization.GetByLabel('UI/Common/Name')])
        self.sr.pathEdit.SetValue(path)
