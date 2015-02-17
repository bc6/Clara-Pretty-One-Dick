#Embedded file name: carbonui/control/browser\browserEditBookMarksWindow.py
import carbonui.const as uiconst
import localization
from carbonui.control.window import WindowCoreOverride as Window
from carbonui.control.label import LabelOverride as Label
from carbonui.control.singlelineedit import SinglelineEditCoreOverride as SinglelineEdit
from carbonui.control.buttons import ButtonCoreOverride as Button
from carbonui.control.scroll import ScrollCoreOverride as Scroll
from carbonui.control.scrollentries import ScrollEntryNode, SE_GenericCore
from carbonui.primitives.container import Container
from carbon.common.script.util.commonutils import StripTags

class EditBookmarksWindowCore(Window):
    __guid__ = 'uicls.EditBookmarksWindowCore'
    default_windowID = 'EditBookmarks'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        name = attributes.bookmarkName
        url = attributes.url
        self.SetCaption(localization.GetByLabel('UI/Browser/EditBookmarks/Caption'))
        self.SetButtons(uiconst.OKCLOSE, okLabel=localization.GetByLabel('UI/Browser/EditBookmarks/Remove', selectedItems=0), okFunc=self.Remove, okModalResult=uiconst.ID_NONE)
        self.SetMinSize((256, 256))
        main = self.GetMainArea()
        main.clipChildren = 0
        Container(name='errorParent', parent=main, align=uiconst.TOBOTTOM, height=16, state=uiconst.UI_HIDDEN)
        toppar = Container(name='toppar', align=uiconst.TOTOP, height=66, parent=main, idx=0, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        c = Container(name='namecont', parent=toppar, align=uiconst.TOTOP, height=20, padBottom=5)
        label = Label(text=localization.GetByLabel('UI/Browser/EditBookmarks/Name'), fontsize=9, letterspace=2, state=uiconst.UI_DISABLED, parent=c, align=uiconst.CENTERLEFT, left=4)
        edit = SinglelineEdit(name='nameEdit', parent=c, align=uiconst.CENTERLEFT, width=150)
        edit.OnReturn = self.OnEnter
        self.nameEdit = edit
        c = Container(name='urlcont', parent=toppar, align=uiconst.TOTOP, height=20, padBottom=5)
        label2 = Label(text=localization.GetByLabel('UI/Browser/EditBookmarks/URL'), fontsize=9, letterspace=2, state=uiconst.UI_DISABLED, parent=c, align=uiconst.CENTERLEFT, left=4, uppercase=True)
        edit = SinglelineEdit(name='urlEdit', parent=c, align=uiconst.CENTERLEFT, width=150)
        edit.OnReturn = self.OnEnter
        self.urlEdit = edit
        self.nameEdit.left = self.urlEdit.left = max(35, label.textwidth + 6, label2.textwidth + 6)
        b = Button(parent=toppar, label=localization.GetByLabel('UI/Browser/EditBookmarks/Add'), func=self.OnEnter, align=uiconst.BOTTOMRIGHT)
        editBtn = Button(parent=toppar, label=localization.GetByLabel('UI/Browser/EditBookmarks/Edit'), pos=(b.width + const.defaultPadding,
         0,
         0,
         0), func=self.OnEdit, align=uiconst.BOTTOMRIGHT)
        editBtn.state = uiconst.UI_HIDDEN
        self.editBtn = editBtn
        name = StripTags(name).strip()
        if name:
            self.nameEdit.SetValue(name)
        if url:
            self.urlEdit.SetValue(url)
        self.scroll = Scroll(parent=main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        sm.GetService('sites')
        self.RefreshSites()

    def Confirm(self, *etc):
        pass

    def Remove(self, *etc):
        selected = self.scroll.GetSelected()
        if not len(selected):
            self.Error(localization.GetByLabel('UI/Browser/EditBookmarks/PleaseSelectSite'))
            return
        self.Error('')
        for entry in selected:
            sm.GetService('sites').RemoveBookmark(entry.retval)

        self.RefreshSites()

    def Error(self, error):
        ep = self.GetChild('errorParent')
        ep.Flush()
        if error:
            uicore.Message('error')
            t = Label(text=error, parent=ep, left=8, top=6, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, color=(1.0, 0.0, 0.0, 1.0))
            ep.state = uiconst.UI_DISABLED
            ep.height = t.height + t.top * 2
        else:
            ep.state = uiconst.UI_HIDDEN

    def OnEntryClick(self, node):
        kv = node.sr.node.retval
        self.nameEdit.SetValue(kv.name)
        self.urlEdit.SetValue(kv.url)
        self.oldEntry = kv
        self.editBtn.state = uiconst.UI_NORMAL
        self.Error(None)
        selected = self.scroll.GetSelected()
        self.SetButtons(uiconst.OKCLOSE, okLabel=localization.GetByLabel('UI/Browser/EditBookmarks/Remove', selectedItems=len(selected)), okFunc=self.Remove, okModalResult=uiconst.ID_NONE)

    def OnEdit(self, node, *args):
        if self.CheckEdit():
            sm.GetService('sites').EditBookmark(self.oldEntry, self.nameEdit.GetValue().strip(), self.urlEdit.GetValue().strip())
            self.oldName = self.nameEdit.GetValue().strip()
            self.oldUrl = self.urlEdit.GetValue().strip()
            self.RefreshSites()

    def OnEnter(self, *etc):
        if self.destroyed:
            return
        if self.CheckEdit():
            sm.GetService('sites').AddBookmark(self.nameEdit.GetValue().strip(), self.urlEdit.GetValue().strip())
            self.RefreshSites()

    def CheckEdit(self):
        nameValue = self.nameEdit.GetValue()
        urlValue = self.urlEdit.GetValue()
        if not nameValue.strip():
            self.Error(localization.GetByLabel('UI/Browser/EditBookmarks/PleaseChooseName'))
            return False
        if not urlValue.strip():
            self.Error(localization.GetByLabel('UI/Browser/EditBookmarks/PleaseEnterURL'))
            return False
        self.Error(None)
        return True

    def RefreshSites(self):
        self.selected = None
        scrolllist = []
        for bookmark in sm.GetService('sites').GetBookmarks():
            if bookmark is not None:
                label = localization.GetByLabel('UI/Browser/EditBookmarks/Row', name=bookmark.name, url=bookmark.url)
                scrolllist.append(ScrollEntryNode(decoClass=SE_GenericCore, label=label, retval=bookmark, OnClick=self.OnEntryClick))

        self.scroll.Load(contentList=scrolllist, headers=[localization.GetByLabel('UI/Browser/EditBookmarks/TableLabel'), localization.GetByLabel('UI/Browser/EditBookmarks/TableURL')], noContentHint=localization.GetByLabel('UI/Browser/EditBookmarks/NoBookmarksFound'))


class EditBookmarksWindowCoreOverride(EditBookmarksWindowCore):
    pass
