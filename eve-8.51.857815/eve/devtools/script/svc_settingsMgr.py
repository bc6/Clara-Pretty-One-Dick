#Embedded file name: eve/devtools/script\svc_settingsMgr.py
"""Prefs.ini key/value inspector and editor
"""
import uiprimitives
import uicontrols
import os
import blue
import uix
import uiutil
import listentry
from service import *
import carbonui.const as uiconst

class PrefsEntry(listentry.Generic):
    """
    Custom listentry class with right click menus
    """
    __guid__ = 'listentry.PrefsEntry'

    def OnDblClick(self, *args):
        self.EditAttribute()

    def GetMenu(self):
        ret = [('Add Entry', self.AddEntry, ()), ('Modify Entry', self.EditAttribute, ()), ('Delete Entry', self.DeleteKey, ())]
        return ret

    def AddEntry(self):
        n = self.sr.node
        n.AddEntry()

    def EditAttribute(self):
        n = self.sr.node
        n.EditAttribute(n.key, n.value)

    def DeleteKey(self):
        n = self.sr.node
        n.DeleteKey(n.key)


class ValuePopup:
    """
    Custom one line popup that reformats all input into strings,  All other input dialogs 
    took only ints/floats or strings, not both.
    """
    __wndname__ = 'ValuePopup'

    def __init__(self, default = None, caption = None, label = None):
        if default is None:
            default = '0'
        if caption is None:
            caption = u'Type in name'
        if label is None:
            label = u'Type in name'
        format = [{'type': 'btline'},
         {'type': 'labeltext',
          'label': label,
          'text': '',
          'frame': 1,
          'labelwidth': 180},
         {'type': 'edit',
          'setvalue': '%s' % default,
          'key': 'qty',
          'label': '_hide',
          'required': 1,
          'frame': 1,
          'setfocus': 1,
          'selectall': 1},
         {'type': 'bbline'}]
        OKCANCEL = 1
        self.popup = uix.HybridWnd(format, caption, 1, None, OKCANCEL, None, minW=240, minH=80)

    def __getitem__(self, *args):
        return args

    def Wnd(self, *args):
        return self.popup


class AddPopup:
    """
    Custom two line input box to allow one step input of key/value pairs.
    """
    __wndname__ = 'AddPopup'

    def __init__(self, caption = None, labeltop = None, labelbtm = None):
        if caption is None:
            caption = u'Type in name'
        if labeltop is None:
            labeltop = u'Type in name'
        if labelbtm is None:
            labelbtm = u'Type in name'
        format = [{'type': 'btline'},
         {'type': 'labeltext',
          'label': labeltop,
          'text': '',
          'frame': 1,
          'labelwidth': 180},
         {'type': 'edit',
          'setvalue': '',
          'key': 'name',
          'label': '_hide',
          'required': 1,
          'frame': 1,
          'setfocus': 1,
          'selectall': 1},
         {'type': 'labeltext',
          'label': labelbtm,
          'text': '',
          'frame': 1,
          'labelwidth': 180},
         {'type': 'edit',
          'setvalue': '',
          'key': 'value',
          'label': '_hide',
          'required': 1,
          'frame': 1,
          'setfocus': 1,
          'selectall': 1},
         {'type': 'bbline'}]
        OKCANCEL = 1
        self.popup = uix.HybridWnd(format, caption, 1, None, OKCANCEL, None, minW=240, minH=80)

    def __getitem__(self, *args):
        return args

    def Wnd(self, *args):
        return self.popup


class SettingsMgr(uicontrols.Window):
    """
    Window class to manage the display and manage the scroll list and associated options.
    The main methods are AddEntry() for creation, EditAttribute() for modification and 
    DeleteKey() for removal. Open() opens the current prefs.ini file.
    """
    __guid__ = 'form.SettingsMgr'
    __neocommenuitem__ = (('Settings Manager', 'SettingsMgr'), True, ROLE_GMH)

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.prefs = prefs
        self.SetCaption('Settings Manager')
        self.SetMinSize([320, 300])
        self.SetWndIcon(None)
        self.SetTopparentHeight(0)
        margin = const.defaultPadding
        main = uiprimitives.Container(name='main', parent=uiutil.GetChild(self, 'main'), pos=(margin,
         margin,
         margin,
         margin))
        uicontrols.Frame(parent=main, color=(1.0, 1.0, 1.0, 0.2), idx=0)
        bottom = uiprimitives.Container(name='btm', parent=main, height=45, align=uiconst.TOBOTTOM)
        btns = [['Refresh',
          self.Refresh,
          None,
          81],
         ['Add',
          self.AddEntry,
          None,
          81],
         ['Modify',
          self.EditAttribute,
          None,
          81],
         ['Delete',
          self.DeleteKey,
          None,
          81],
         ['Open',
          self.OpenPrefs,
          True,
          81]]
        btn = uicontrols.ButtonGroup(btns=btns, parent=bottom)
        push = uiprimitives.Container(parent=bottom, align=uiconst.TOLEFT, width=2)
        push = uiprimitives.Container(parent=bottom, align=uiconst.TOTOP, height=margin)
        locstr = '\xe2\x80\xa2 Current file location...'
        text = uicontrols.Label(text=locstr, parent=bottom, align=uiconst.TOTOP, height=18, fontsize=10, letterspace=1, linespace=9, uppercase=1, state=uiconst.UI_NORMAL)
        text.OnClick = (self.OpenPrefs, False)
        text.GetMenu = self.TextMenu
        text.hint = 'The current location for the prefs.ini is:<br><br>%s<br><br><b>Click</b> to open.' % self.prefs.ini.filename
        uiprimitives.Container(name='div', parent=main, height=0, align=uiconst.TOTOP)
        self.scroll = uicontrols.Scroll(parent=main)
        self.scroll.sr.id = 'PrefsScroll'
        self.Refresh()

    def Refresh(self, *args):
        contentList = []
        p = self.prefs.GetKeys()
        p.sort()
        for key in p:
            value = self.prefs.GetValue(key)
            contentList.append(listentry.Get('PrefsEntry', {'label': u'%s<t>%s' % (key, value),
             'key': key,
             'value': value,
             'AddEntry': self.AddEntry,
             'EditAttribute': self.EditAttribute,
             'DeleteKey': self.DeleteKey}))

        for key, value in sm.GetService('machoNet').GetGlobalConfig().iteritems():
            contentList.append(listentry.Get('Generic', {'label': u'zsystem.clientConfig: %s<t>%s' % (key, value)}))

        self.scroll.Load(contentList=contentList, headers=['Key', 'Value'], fixedEntryHeight=18)
        self.scroll.Sort('Key')

    def GetNode(self, *args):
        node = self.scroll.GetSelected()
        if not node:
            return (None, None)
        node = node[0]
        return (node.key, node.value)

    def AddEntry(self, *args):
        a = AddPopup(caption='Prefs.ini', labeltop='Name', labelbtm='Value')
        ret = a.Wnd()
        if ret:
            prefs.SetValue(ret['name'], ret['value'])
            self.Refresh()

    def EditAttribute(self, k = None, v = None):
        if k is None or v is None:
            k, v = self.GetNode()
            if k is None or v is None:
                return
        a = ValuePopup(default=v, caption='Prefs.ini', label="Set value for '%s'" % k)
        ret = a.Wnd()
        if ret:
            newValue = ret['qty']
            prefs.SetValue(k, newValue)
            self.Refresh()

    def DeleteKey(self, k = None):
        if k is None:
            k, v = self.GetNode()
            if k is None or v is None:
                return
        header = 'Delete entry?'
        question = "Are you sure you wish to <b>permanently delete</b> the '%s' entry from your prefs.ini?" % k
        if eve.Message('CustomQuestion', {'header': header,
         'question': question}, uiconst.YESNO) == uiconst.ID_YES:
            prefs.DeleteValue(k)
            self.Refresh()

    def OpenPrefs(self, prefs = True, *args):
        if not prefs:
            blue.os.ShellExecute(os.path.dirname(self.prefs.ini.filename))
        else:
            blue.os.ShellExecute(self.prefs.ini.filename)

    def TextMenu(self, *args):
        m = []

        def Copy(obj):
            blue.pyos.SetClipboardData(obj)

        m.append(('Copy File Location', Copy, (self.prefs.ini.filename,)))
        m.append(('Copy Directory', Copy, (os.path.dirname(self.prefs.ini.filename),)))
        return m
