#Embedded file name: eve/client/script/ui/control\listwindow.py
import uiprimitives
import uicontrols
import uiutil
import util
import sys
from eve.client.script.ui.control import entries as listentry
import log
import carbonui.const as uiconst
import weakref
import localization

class ListWindow(uicontrols.Window):
    __guid__ = 'form.ListWindow'
    __nonpersistvars__ = ['scroll',
     'listentry',
     'result',
     'listtype',
     'minChoices',
     'maxChoices']
    default_minSize = (128, 240)
    default_width = 256
    default_height = 128

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        lst = attributes.get('lst', [])
        self.listtype = attributes.get('listtype')
        self.ordered = attributes.get('ordered', False)
        caption = attributes.get('caption')
        self.minChoices = attributes.get('minChoices', 1)
        self.maxChoices = attributes.get('maxChoices', 1)
        initChoices = attributes.get('initChoices', [])
        validator = attributes.get('validator')
        scrollHeaders = attributes.get('scrollHeaders')
        iconMargin = attributes.get('iconMargin')
        lstDataIsGrouped = attributes.get('lstDataIsGrouped')
        self.noContentHint = attributes.get('noContentHint')
        if validator is not None:
            self.customValidator = weakref.proxy(validator)
        self.selecting = 0
        self.result = None
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        uiprimitives.Container(name='errorParent', parent=self.sr.main, align=uiconst.TOBOTTOM, height=16, state=uiconst.UI_HIDDEN)
        uiprimitives.Container(name='hintparent', parent=self.sr.main, align=uiconst.TOTOP, height=16, state=uiconst.UI_HIDDEN)
        self.scroll = uicontrols.Scroll(parent=self.sr.main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding + 2))
        self.scroll.sr.iconMargin = iconMargin
        self.scroll.multiSelect = self.maxChoices > 1
        self.MakeUnMinimizable()
        self.SetCaption(caption or localization.GetByLabel('UI/Control/ListWindow/PickOne'))
        if not lstDataIsGrouped:
            self.GenerateList(lst, self.ordered, scrollHeaders)
        else:
            self.GenerateGroupedList(lst, self.ordered, scrollHeaders)
        for each in initChoices or []:
            for entry in self.scroll.GetNodes():
                if entry.listvalue == each:
                    self.scroll.SelectNode(entry)
                    break

        self.RefreshSelection()

    def SetSize(self, width, height, *args):
        if not self or self.destroyed:
            return
        minw, minh = self.minsize
        self.width = max(width, minw)
        self.height = max(height, minh)

    def Cancel(self, *etc):
        if getattr(self, 'isModal', None):
            self.SetModalResult(uiconst.ID_CANCEL)
        else:
            self.Close()

    def SetResult(self, result):
        self.result = result

    def ClickOK(self, *args):
        self.Confirm()

    def DblClickEntry(self, entry, *args):
        if entry.confirmOnDblClick:
            self.scroll.SelectNode(entry.sr.node)
            self.RefreshSelection()
            self.Confirm()

    def ClickEntry(self, *args):
        self.RefreshSelection()

    def GetError(self, checkNumber = 1):
        result = []
        for entry in self.scroll.GetSelected():
            if entry.listvalue:
                result.append(entry.listvalue)

        if hasattr(self, 'customValidator'):
            ret = self.customValidator and self.customValidator(result) or ''
            if ret:
                return ret
        try:
            if checkNumber:
                if self.maxChoices and len(result) > self.maxChoices:
                    return localization.GetByLabel('UI/Control/ListWindow/SelectTooManyError', num=self.maxChoices)
                if len(result) < self.minChoices:
                    if self.minChoices == self.maxChoices:
                        label = localization.GetByLabel('UI/Control/ListWindow/MustSelectError', num=self.minChoices)
                    else:
                        label = localization.GetByLabel('UI/Control/ListWindow/SelectTooFewError', num=self.minChoices)
                    return label
        except ValueError as e:
            log.LogException()
            sys.exc_clear()
            return

        return ''

    def Confirm(self, *etc):
        if not self.isModal:
            return
        self.Error(self.GetError())
        if not self.GetError():
            self.result = [ entry.listvalue for entry in self.scroll.GetSelected() ]
            if self.maxChoices == 1:
                self.result = self.result[0]
            self.SetModalResult(uiconst.ID_OK)

    def Error(self, error):
        ep = uiutil.GetChild(self, 'errorParent')
        ep.Flush()
        if error:
            t = uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Control/ListWindow/DisplayError', errorMessage=error), top=-3, parent=ep, width=self.minsize[0] - 32, state=uiconst.UI_DISABLED, color=(1.0, 0.0, 0.0, 1.0), align=uiconst.CENTER)
            ep.state = uiconst.UI_DISABLED
            ep.height = t.height + 8
        else:
            ep.state = uiconst.UI_HIDDEN

    def RefreshSelection(self):
        self.Error(self.GetError())

    def SetHint(self, hint):
        hp = uiutil.GetChild(self, 'hintparent')
        hp.Flush()
        if hint:
            t = uicontrols.EveLabelMedium(text=hint, parent=hp, top=-3, width=self.minsize[0] - 32, state=uiconst.UI_DISABLED, align=uiconst.CENTER)
            hp.state = uiconst.UI_PICKCHILDREN
            hp.height = t.height + 8
        else:
            hp.state = uiconst.UI_HIDDEN

    def GenerateList(self, lst, ordered = 0, scrollHeaders = []):
        if ordered == 1:

            def Compare(a, b):
                a, b = a[0], b[0]
                try:
                    a = a.lower()
                except:
                    pass

                try:
                    b = b.lower()
                except:
                    pass

                return cmp(a, b)

            lst.sort(Compare)
        _height = 16
        scrolllist = []
        for info in lst:
            height, entry = self.AddEntry(info)
            _height = max(height, _height)
            scrolllist.append(entry)

        self.scroll.Load(contentList=scrolllist, headers=scrollHeaders, noContentHint=self.noContentHint)

    def GenerateGroupedList(self, lst, ordered = 0, scrollHeaders = []):
        if ordered == 1:
            lst.sort(self.GroupItemCompare)
        rootnode = util.KeyVal()
        rootnode.groupItems = lst
        scrolllist = self.GetGroupData(rootnode)
        _height = 24
        self.scroll.Load(contentList=scrolllist, headers=scrollHeaders, noContentHint=self.noContentHint)

    def AddEntry(self, info):
        confirmOnDblClick = self.minChoices == self.maxChoices == 1
        if self.listtype in ('character', 'corporation', 'alliance', 'faction', 'owner'):
            typeinfo = None
            if info[2]:
                typeinfo = cfg.invtypes.Get(info[2])
            if typeinfo is None:
                owner = cfg.eveowners.GetIfExists(info[1])
                if owner:
                    typeinfo = cfg.invtypes.Get(owner.typeID)
            if typeinfo is not None:
                charID = info[1]
                if util.IsCharacter(charID) and util.IsNPC(charID):
                    entryType = 'AgentEntry'
                else:
                    entryType = 'User'
                return (40, listentry.Get(entryType, {'charID': charID,
                  'OnDblClick': self.DblClickEntry,
                  'OnClick': self.ClickEntry,
                  'dblconfirm': confirmOnDblClick}))
        else:
            if self.listtype in ('pickStation',):
                data = info
                data.confirmOnDblClick = confirmOnDblClick
                data.OnDblClick = self.DblClickEntry
                data.OnClick = self.ClickEntry
                return (32, listentry.Get('Generic', data=data))
            if self.listtype == 'generic':
                name, listvalue = info
                data = util.KeyVal()
                data.confirmOnDblClick = confirmOnDblClick
                data.label = name
                data.listvalue = info
                data.OnDblClick = self.DblClickEntry
                data.OnClick = self.ClickEntry
                return (32, listentry.Get('Generic', data=data))
        name, itemID, typeID = info
        data = util.KeyVal()
        data.confirmOnDblClick = confirmOnDblClick
        data.label = name
        data.itemID = itemID
        data.typeID = typeID
        data.listvalue = [name, itemID, typeID]
        data.isStation = self.listtype == 'station'
        data.getIcon = self.listtype == 'item'
        data.OnDblClick = self.DblClickEntry
        data.OnClick = self.ClickEntry
        return (24, listentry.Get('Generic', data=data))

    def GetGroupData(self, nodedata, newItems = 0):
        if not nodedata.groupItems:
            return []
        if self.ordered:
            nodedata.groupItems.sort(self.GroupItemCompare)
        confirmOnDblClick = self.minChoices == self.maxChoices == 1
        scrolllist = []
        for subnode in nodedata.groupItems:
            if subnode.get('groupItems', None) is not None:
                if not hasattr(subnode, 'GetSubContent'):
                    subnode.GetSubContent = self.GetGroupData
                scrolllist.append(listentry.Get('Group', data=subnode))
            else:
                subnode.OnDblClick = self.DblClickEntry
                subnode.OnClick = self.ClickEntry
                subnode.confirmOnDblClick = confirmOnDblClick
                subnode.isStation = self.listtype == 'station'
                subnode.getIcon = self.listtype == 'item'
                scrolllist.append(listentry.Get('Generic', data=subnode))

        return scrolllist

    def GroupItemCompare(self, a, b):
        a = a.label or a[0]
        b = b.label or b[0]
        try:
            a = a.lower()
        except:
            pass

        try:
            b = b.lower()
        except:
            pass

        return cmp(a, b)
