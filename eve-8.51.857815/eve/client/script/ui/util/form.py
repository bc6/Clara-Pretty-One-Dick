#Embedded file name: eve/client/script/ui/util\form.py
import service
import uiprimitives
import uicontrols
import uix
import uiutil
import log
import types
import carbonui.const as uiconst
import localization
from eve.client.script.ui.control.eveEditPlainText import EditPlainText

class Form(service.Service):
    """
        Code that creates UI elements from the format structure passed to a hybrid window.
        
        A sample format structure: 
        format = [
            {"type": "header", "text": "The amazing heading"},
            {"type": "edit", "setvalue": "Hell yeah!", "key":"theEdit", "label":"Put text here", "required":True, "maxlength":100},
            {"type": "data", "data" : {"thisIs": ["some extra data returned by the form"], "and": "thenSome"}},
            {"type": "errorcheck", "errorcheck" : self.ErrorCheckFunctionThatReturnsErrorStringOrEmptyString},
            {"type": "btline"},
        ]
        
        The supported types are:
        - errorcheck (validation function for form data)
        - data (additional data that will be sent by the form)
        - tab (create a tab in a tabbed form)
        - push (vertical spacing)
        - btline / bbline (horizontal line)
        - header (text heading)
        - labeltext (label text)
        - text (normal single- or multiline non-editable text)
        - edit (a single line text edit)
        - textedit (editable multi-line textbox)
        - checkbox (Checkbox field) 
        - combo (combo box)
        - btnonly (a button)
        
        There are a few parameters that work for all types such as "setfocus" (see below)
    """
    __guid__ = 'svc.form'
    __exportedcalls__ = {'GetForm': [],
     'ProcessForm': []}
    __servicename__ = 'form'
    __displayname__ = 'Form Service'
    __dependencies__ = []

    def __init__(self):
        service.Service.__init__(self)

    def GetForm(self, format, parent):
        _form, retfields, reqresult, panels, errorcheck, refresh = self._GetForm(format, parent)
        if _form.align == uiconst.TOALL:
            _form.SetSize(0, 0)
            _form.SetPosition(0, 0)
            _form.padding = const.defaultPadding
        elif _form.align in (uiconst.TOTOP, uiconst.TOBOTTOM):
            _form.SetPosition(0, 0)
            _form.width = 0
            _form.padding = const.defaultPadding
        elif _form.align in (uiconst.TOLEFT, uiconst.TORIGHT):
            _form.SetPosition(0, 0)
            _form.height = 0
            _form.padding = const.defaultPadding
        else:
            _form.left = _form.top = const.defaultPadding
        return (_form,
         retfields,
         reqresult,
         panels,
         errorcheck,
         refresh)

    def _GetForm(self, format, parent, retfields = [], reqresult = [], errorcheck = None, tabpanels = [], tabgroup = [], refresh = [], wipe = 1):
        if not uiutil.IsUnder(parent, uicore.desktop):
            log.LogTraceback('Form parent MUST be hooked on the desktop; it is impossible to know the real dimensions of stuff within otherwise.')
        self.retfields = retfields
        self.reqresult = reqresult
        self.errorcheck = errorcheck
        self.tabpanels = tabpanels
        self.tabgroup = tabgroup
        self.refresh = refresh
        if not isinstance(parent, FormWnd):
            log.LogTraceback('Incompatible formparent, please change it to xtriui.FormWnd')
        self.parent = parent
        self.parent.sr.panels = {}
        self.parent.sr.focus = None
        if wipe:
            self.retfields = []
            self.reqresult = []
            self.tabpanels = []
            self.tabgroup = []
            self.refresh = []
        for each in format:
            self.type = each
            typeName = self.type['type']
            self.leftPush = self.type.get('labelwidth', 0) or 80
            self.code = None
            if typeName == 'errorcheck':
                self.AddErrorcheck()
                continue
            elif typeName == 'data':
                self.AddData()
                continue
            elif typeName == 'tab':
                self.AddTab()
                continue
            elif typeName in ('btline', 'bbline'):
                self.AddLine()
                continue
            elif typeName == 'push':
                self.AddPush()
            elif typeName == 'header':
                self.AddHeader()
            elif typeName == 'labeltext':
                self.AddLabeltext()
            elif typeName == 'text':
                self.AddText()
            elif typeName == 'edit':
                self.AddEdit()
            elif typeName == 'textedit':
                self.AddTextedit()
            elif typeName == 'checkbox':
                self.AddCheckbox()
            elif typeName == 'combo':
                self.AddCombo()
            elif typeName == 'btnonly':
                self.AddBtnonly()
            else:
                log.LogWarn('Unknown fieldtype in form generator')
                continue
            if self.type.has_key('key'):
                if self.code:
                    self.retfields.append([self.code, self.type])
                    self.parent.sr.Set(self.type['key'], self.code)
                else:
                    self.parent.sr.Set(self.type['key'], self.new)
            if self.type.get('required', 0) == 1:
                self.reqresult.append([self.code, self.type])
            if self.type.get('selectall', 0) == 1 and getattr(self.code, 'SelectAll', None):
                self.code.SelectAll()
            if self.type.get('setfocus', 0) == 1:
                self.parent.sr.focus = self.code
            if self.type.has_key('stopconfirm') and hasattr(self.code, 'stopconfirm'):
                self.code.stopconfirm = self.type['stopconfirm']
            if self.type.get('frame', 0) == 1:
                idx = 0
                for child in self.new.children:
                    if child.name.startswith('Line'):
                        idx += 1

                uiprimitives.Container(name='leftpush', parent=self.new, align=uiconst.TOLEFT, width=6, idx=idx)
                uiprimitives.Container(name='rightpush', parent=self.new, align=uiconst.TORIGHT, width=6, idx=idx)
                uiprimitives.Line(parent=self.new, align=uiconst.TOLEFT, idx=idx)
                uiprimitives.Line(parent=self.new, align=uiconst.TORIGHT, idx=idx)

        if wipe and len(self.tabgroup):
            tabs = uicontrols.TabGroup(name='tabparent', parent=self.parent, idx=0)
            tabs.Startup(self.tabgroup, 'hybrid')
            maxheight = 0
            for panel in self.tabpanels:
                maxheight = max(maxheight, panel.height)

            self.parent.height = maxheight + tabs.height
        else:
            if len(self.tabpanels):
                for each in self.tabpanels:
                    each.state = uiconst.UI_HIDDEN

                self.tabpanels[0].state = uiconst.UI_PICKCHILDREN
            uix.RefreshHeight(self.parent)
        uicore.registry.SetFocus(self)
        return (self.parent,
         self.retfields,
         self.reqresult,
         self.tabpanels,
         self.errorcheck,
         self.refresh)

    def AddErrorcheck(self):
        """
             errorcheck (validation function for form data)
            
             PARAMS:
                - errorcheck [func]: an error check function that should return en empty string on OK,
                  or an error message string otherwise
        """
        self.errorcheck = self.type['errorcheck']

    def AddData(self):
        """
             data (additional data that will be sent by the form)
             
             PARAMS:
                - data [any] : the additional data sent by the form
        """
        self.retfields.append(self.type['data'])

    def AddTab(self):
        """
             tab (create a tab in a tabbed form)
             
             PARAMS:
                - tabtext [str]        : tab label
                - format [list]        : a format list such as those passed to a form
                - key [str]            : a unique name for the tab panel, passed on to it's parent
                - panelvisible [bool]  : is the tab panel visible (default False)
                - tabvisible [bool]    : is the tab visible (default False)
        """
        _form, _retfield, _required, _tabpanels, _errorcheck, _refresh = self._GetForm(self.type['format'], FormWnd(name='form', align=uiconst.TOTOP, parent=self.parent), self.retfields, self.reqresult, self.errorcheck, self.tabpanels, self.tabgroup, self.refresh, 0)
        if self.type.has_key('key'):
            self.parent.sr.panels[self.type['key']] = _form
        if self.type.get('panelvisible', 0):
            _form.state = uiconst.UI_PICKCHILDREN
        else:
            _form.state = uiconst.UI_HIDDEN
        if self.type.has_key('tabvisible'):
            if self.type['tabvisible'] == 1:
                self.tabgroup.append([self.type['tabtext'],
                 _form,
                 self,
                 None])
        else:
            self.tabgroup.append([self.type['tabtext'],
             _form,
             self,
             None])

    def AddPush(self):
        """
             push (vertical spacing)
             
             PARAMS:
                - height [int]: The height of the spacing
        """
        self.new = uiprimitives.Container(name='push', parent=self.parent, align=uiconst.TOTOP, height=self.type.get('height', 6))

    def AddLine(self):
        """
             btline / bbline (horizontal line)
            
             PARAMS:
                - None
        """
        uiprimitives.Line(parent=self.parent, align=uiconst.TOTOP)

    def AddHeader(self):
        """
             header (text heading)
            
             PARAMS:
                - height [int]    : text container height (not font height)
                - text [str]      : heading text
                - hideLine [bool] : if True, heading line is hidden
        """
        self.new = uiprimitives.Container(name='headerField', parent=self.parent, align=uiconst.TOTOP)
        header = uicontrols.EveLabelSmall(text=self.type.get('text', ''), parent=self.new, name='header', padding=(7, 3, 7, 3), align=uiconst.TOTOP, state=uiconst.UI_NORMAL, bold=True)
        self.new.height = max(self.type.get('height', 17), header.textheight + header.padTop * 2)
        self.refresh.append((self.new, header))
        if not self.type.get('hideLine', False):
            uiprimitives.Line(parent=self.new, align=uiconst.TOTOP, padLeft=-6, padRight=-6, idx=0)
            uiprimitives.Line(parent=self.new, align=uiconst.TOBOTTOM, padLeft=-6, padRight=-6, idx=0)

    def AddLabeltext(self):
        """
             labeltext (label text)
             
             PARAMS:
                - height [int]    : text container height (not font height)
                - label [str]     : label text 
                - text [str]      : same as label
        """
        self.new = uiprimitives.Container(name='labeltextField', parent=self.parent, align=uiconst.TOTOP, height=self.type.get('height', 20))
        text = uicontrols.EveLabelMedium(text=self.type.get('text', ''), parent=self.new, align=uiconst.TOTOP, name='text', padding=(self.leftPush,
         3,
         0,
         0), state=uiconst.UI_NORMAL)
        label = self.type.get('label', '')
        if label and label != '_hide':
            label = uicontrols.EveLabelSmall(text=label, parent=self.new, name='label', left=7, width=self.leftPush - 6, top=5)
            self.refresh.append((self.new, text, label))
        else:
            self.refresh.append((self.new, text))

    def AddText(self):
        """
             text (normal single- or multiline text)
             
             PARAMS:
                - height [int]    : text container height (not font height)
                - text [str]      : the actual text
                - fontsize [int]  : font size
                - tabstops [list] : list of tab stops for tab aligned text
                - left [int]      : left of the text
        """
        left = self.type.get('left', 0)
        self.new = uiprimitives.Container(name='textField', parent=self.parent, align=uiconst.TOTOP, height=self.type.get('height', 20), padding=(left,
         0,
         0,
         0))
        fontsize = self.type.get('fontsize', 12)
        text = uicontrols.Label(text=self.type.get('text', ''), parent=self.new, align=uiconst.TOTOP, name='text', padding=(0, 3, 0, 3), fontsize=fontsize, maxLines=1 if bool(self.type.get('tabstops', [])) else None, state=uiconst.UI_NORMAL, tabs=self.type.get('tabstops', []))
        self.new.height = max(self.new.height, int(text.textheight + 6))
        self.refresh.append((self.new, text))

    def AddEdit(self):
        """    
             edit (a single line text edit)
             
             PARAMS:
                - width [int]                  : edit width
                - setvalue [str]               : initial default text
                - label [str]                  : edit box label
                - text [str]                   : same as label (depreciated)
                - intonly [bool]               : if true, only integers can be input
                - floatonly [bool]             : if true, only float numbers can be input
                - maxlength [int]              : maximum number of characters
                - passwordChar [bool]          : if true, characters are replaced by password characters
                - readOnly [bool]              : if true, input is disabled
                - autoselect [bool]            : if true, the whole input gets selected when the edit gets focus
                - OnReturn [func]              : a callback for when RETURN is pressed
                - unusedkeydowncallback [func] : a callback for when an unused global key is pressed (depreciated)
                - onanychar [func]             : a callback for when any character is input
        """
        self.new = uiprimitives.Container(name='editField', parent=self.parent, align=uiconst.TOTOP)
        config = 'edit_%s' % self.type['key']
        self.code = uicontrols.SinglelineEdit(name=config, parent=self.new, setvalue=self.type.get('setvalue', ''), padding=(self.leftPush,
         2,
         0,
         2), ints=self.type.get('intonly', None), floats=self.type.get('floatonly', None), align=uiconst.TOTOP, maxLength=self.type.get('maxlength', None) or self.type.get('maxLength', None), passwordCharacter=self.type.get('passwordChar', None), readonly=self.type.get('readonly', 0), autoselect=self.type.get('autoselect', 0), isTypeField=self.type.get('isTypeField', False), isCharacterField=self.type.get('isCharacterField', False))
        self.new.height = self.code.height + self.code.padTop * 4
        width = self.type.get('width', None)
        if width:
            self.code.SetAlign(uiconst.TOLEFT)
            self.code.width = width
        if self.type.has_key('OnReturn'):
            self.code.data = {'key': self.type['key']}
            self.code.OnReturn = self.type['OnReturn']
        if self.type.has_key('unusedkeydowncallback'):
            self.code.OnUnusedKeyDown = self.type['unusedkeydowncallback']
        if self.type.has_key('onanychar'):
            self.code.OnAnyChar = self.type['onanychar']
        label = self.type.get('label', '')
        text = self.type.get('text', None)
        caption = text or label
        if label == '_hide':
            self.code.padLeft = 0
        elif caption:
            l = uicontrols.EveLabelSmall(text=caption, align=uiconst.CENTERLEFT, parent=self.new, name='label', left=7, width=self.leftPush - 6)

    def AddTextedit(self):
        """
             textedit (editable multi-line textbox)
             
             PARAMS:
                - height [int]            : text container height (not font height)
                - setvalue [str]          : initial text in edit
                - text [str]              : same as setvalue
                - label [str]             : text edit label. If set to "_hide", it gets hidden and the edit is moved accordingly
                - maxlength [int]         : maximum number of input characters
                - showAttribPanel [bool]  : the text attribute panel is shown (default False)
                - readonly [bool]         : text is read only (default False)
                - hidebackground [bool]   : hide textbox background (default False)
        """
        self.new = uiprimitives.Container(name='texteditField', parent=self.parent, align=uiconst.TOTOP, height=self.type.get('height', 68))
        self.code = EditPlainText(setvalue=self.type.get('setvalue', '') or self.type.get('text', ''), parent=self.new, padding=(self.leftPush,
         2,
         0,
         2), readonly=self.type.get('readonly', 0), showattributepanel=self.type.get('showAttribPanel', 0), maxLength=self.type.get('maxlength', None) or self.type.get('maxLength', None))
        label = self.type.get('label', '')
        if label == '_hide':
            self.code.padLeft = 0
        elif label:
            uicontrols.EveLabelSmall(text=label, parent=self.new, name='label', left=7, width=self.leftPush - 6, top=5)

    def AddCheckbox(self):
        """
             checkbox (Checkbox field) 
             
             PARAMS:
                - text [str]       : label text
                - setvalue [bool]  : sets the checkbox to checked/unchecked
                - group [str]      : creates a group of checkboxes, turning them into radiobuttons
                - onchange [func]  : an OnChange callback
                - showpanel [bool] : ???
                - hidden [bool]    : if true, the checkbox is hidden
                - name             : name of the checkbox
        """
        self.new = uiprimitives.Container(name='checkboxCont', parent=self.parent, align=uiconst.TOTOP, pos=(0, 0, 0, 18))
        self.code = uicontrols.Checkbox(text=self.type.get('text', ''), parent=self.new, configName=self.type.get('name', 'none'), retval=self.type['key'], checked=self.type.get('setvalue', 0), groupname=self.type.get('group', None), callback=self.parent.OnCheckboxChange)
        self.code.data = {}
        onchange = self.type.get('OnChange', None) or self.type.get('onchange', None)
        if onchange:
            self.code.data = {'key': self.type['key'],
             'callback': onchange}
        if self.type.has_key('showpanel'):
            self.code.data['showpanel'] = self.type['showpanel']
        if self.code.sr.label:
            self.refresh.append((self.code, self.code.sr.label))
        if self.type.get('hidden', 0):
            self.code.state = uiconst.UI_HIDDEN

    def AddCombo(self):
        """
            combo (combo box)
            
            PARAMS:
               - height [int]       : container height
               - width [int]        : combo box width
               - label [str]        : combo label text (if set to "_hide", it's hidden)
               - options [list]     : a list of combo options as accepted by uicontrols.Combo()
               - key [str]          : config name of the combo (default "combo")
               - select [str]       : default selected option
               - callback [func]    : callback function when a new option is selected
        """
        self.new = uiprimitives.Container(name='comboField', parent=self.parent, align=uiconst.TOTOP, height=self.type.get('height', 20))
        options = self.type.get('options', [(localization.GetByLabel('UI/Common/None'), None)])
        self.code = uicontrols.Combo(label='', parent=self.new, options=options, name=self.type.get('key', 'combo'), select=self.type.get('setvalue', ''), padding=(self.leftPush,
         2,
         0,
         2), align=uiconst.TOTOP, callback=self.type.get('callback', None), labelleft=self.leftPush)
        self.new.height = self.code.height + self.code.padTop * 4
        width = self.type.get('width', None)
        if width:
            self.code.SetAlign(uiconst.TOLEFT)
            self.code.width = width
        label = self.type.get('label', '')
        if label == '_hide':
            self.code.padLeft = 0
        else:
            uicontrols.EveLabelSmall(text=label, parent=self.new, name='label', left=7, width=self.leftPush - 6, align=uiconst.CENTERLEFT)

    def AddBtnonly(self):
        """
             btnonly (button field)
             
             PARAMS:
                - height [int]      : container height (default 20)
                - uniSize [bool]    : if true, all buttons have same size (default True)
                - buttons [list]    : a list of dictionaries, each describing a button (params documented below)
            
                BUTTON PARAMS:
                    - align [str]            : can be either "left" or "right" (default "right")
                    - caption [str]          : button caption
                    - function [func]        : button OnClick callback
                    - btn_modalresult [bool] : does this button generate a modal window result (default False)
                    - btn_default [bool]     : if true, this button is the default value (when RETURN is pressed) (default False)
                    - btn_cancel [bool]      : if true, this button cancels the current form (default False)
        """
        self.new = uiprimitives.Container(name='btnonly', parent=self.parent, align=uiconst.TOTOP, height=self.type.get('height', 20))
        btns = []
        align = uiconst.TORIGHT
        for wantedbtn in self.type['buttons']:
            if wantedbtn.has_key('align'):
                al = {'left': uiconst.CENTERLEFT,
                 'right': uiconst.CENTERRIGHT}
                align = al.get(wantedbtn['align'], uiconst.CENTERRIGHT)
            btns.append([wantedbtn['caption'],
             wantedbtn['function'],
             wantedbtn.get('args', 'self'),
             None,
             wantedbtn.get('btn_modalresult', 0),
             wantedbtn.get('btn_default', 0),
             wantedbtn.get('btn_cancel', 0)])

        btns = uicontrols.ButtonGroup(btns=btns, subalign=align, line=0, parent=self.new, align=uiconst.TOTOP, unisize=self.type.get('uniSize', 1))

    def ProcessForm(self, retfields, required, errorcheck = None):
        result = {}
        for each in retfields:
            if type(each) == dict:
                result.update(each)
                continue
            value = each[0].GetValue()
            if each[1]['type'] == 'checkbox' and each[1].has_key('group') and value == 1:
                result[each[1]['group']] = each[1]['key']
            else:
                result[each[1]['key']] = value

        if errorcheck:
            hint = errorcheck(result)
            if hint == 'silenterror':
                return
            if hint:
                eve.Message('CustomInfo', {'info': hint})
                return
        if len(required):
            for each in required:
                retval = each[0].GetValue()
                if retval is None or retval == '' or type(retval) in types.StringTypes and retval.strip() == '':
                    fieldname = ''
                    if each[1].has_key('label'):
                        fieldname = each[1]['label']
                        if fieldname == '_hide':
                            fieldname = each[1]['key']
                    else:
                        fieldname = each[1]['key']
                    eve.Message('MissingRequiredField', {'fieldname': fieldname})
                    return
                if each[1]['type'] == 'checkbox' and each[1].has_key('group'):
                    if each[1]['group'] not in result:
                        eve.Message('MissingRequiredField', {'fieldname': each[1]['group']})
                        return

        return result


class FormWnd(uiprimitives.Container):
    __guid__ = 'xtriui.FormWnd'

    def _OnClose(self):
        uiprimitives.Container._OnClose(self)
        windowKeys = self.sr.panels.keys()
        for key in windowKeys:
            if not self.sr.panels.has_key(key):
                continue
            wnd = self.sr.panels[key]
            del self.sr.panels[key]
            if wnd is not None and not wnd.destroyed:
                wnd.Close()

    def ShowPanel(self, panelkey):
        for key in self.sr.panels:
            self.sr.panels[key].state = uiconst.UI_HIDDEN

        self.sr.panels[panelkey].state = uiconst.UI_NORMAL

    def OnCheckboxChange(self, sender, *args):
        if sender.data.has_key('callback'):
            sender.data['callback'](sender)
        if sender.data.has_key('showpanel') and self.sr.panels.has_key(sender.data['showpanel']):
            self.ShowPanel(sender.data['showpanel'])

    def OnChange(self, *args):
        pass
