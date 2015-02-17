#Embedded file name: eve/client/script/ui/control\buttonGroup.py
import carbonui.const as uiconst
from carbonui.primitives.line import Line
from carbonui.primitives.container import Container
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui import eveFontConst
from eve.client.script.ui.control.eveWindowUnderlay import LineUnderlay

class ButtonGroup(Container):
    """ A group of standard buttons without any selection state """
    __guid__ = 'uicontrols.ButtonGroup'
    default_align = uiconst.TOBOTTOM
    default_state = uiconst.UI_PICKCHILDREN
    default_name = 'btnsmainparent'
    default_subalign = uiconst.CENTER
    default_valign = False
    default_line = False
    default_unisize = True
    default_fixedWidth = False
    default_btns = None
    default_fontsize = eveFontConst.EVE_SMALL_FONTSIZE
    default_fontStyle = None
    default_fontFamily = None
    default_fontPath = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.btns = attributes.get('btns', self.default_btns)
        self.subalign = attributes.get('subalign', self.default_subalign)
        self.valign = attributes.get('valign', self.default_valign)
        self.line = attributes.get('line', self.default_line)
        self.idx = attributes.get('idx', self.default_idx)
        self.unisize = attributes.get('unisize', self.default_unisize)
        self.fixedWidth = attributes.get('fixedWidth', self.default_fixedWidth)
        self.fontStyle = attributes.get('fontStyle', self.default_fontStyle)
        self.fontFamily = attributes.get('fontFamily', self.default_fontFamily)
        self.fontPath = attributes.get('fontPath', self.default_fontPath)
        self.fontsize = attributes.get('fontsize', self.default_fontsize)
        self.Prepare_Appearance_()
        if self.btns:
            for btnData in self.btns:
                self.AddButton(*btnData)

    def Prepare_Appearance_(self):
        self.subpar = Container(parent=self, name='btns', state=uiconst.UI_PICKCHILDREN, align=self.subalign)
        if self.line:
            LineUnderlay(parent=self, colorType=uiconst.COLORTYPE_UIHILIGHT, align=uiconst.TOTOP)

    def AddButton(self, label, func, args = None, fixedWidth = None, isModalResult = False, isDefault = False, isCancel = False, hint = None):
        if not self.fixedWidth:
            fixedWidth = None
        newbtn = Button(parent=self.subpar, label=label, func=func, args=args, btn_modalresult=isModalResult, btn_default=isDefault, btn_cancel=isCancel, fixedwidth=fixedWidth, name='%s_Btn' % label, fontStyle=self.fontStyle, fontFamily=self.fontFamily, fontPath=self.fontPath, fontsize=self.fontsize, hint=hint)
        self.sr.Set('%s_Btn' % label, newbtn)
        self.ResetLayout()
        return newbtn

    def FlushButtons(self):
        self.subpar.Flush()

    def ResetLayout(self):
        """
        recalculating the width and placement of buttons after button hans been added
        """
        maxWidth = 0
        for btn in self.subpar.children:
            maxWidth = max(btn.width, maxWidth)

        leftCount = 0
        topCount = 0
        for btn in self.subpar.children:
            if not btn.display:
                continue
            if self.unisize:
                btn.width = maxWidth
            if self.valign:
                btn.align = uiconst.CENTERTOP
                btn.left = 0
                btn.top = topCount
                topCount += btn.height + 4
            else:
                btn.align = uiconst.TOPLEFT
                btn.left = leftCount
                btn.top = 0
                leftCount += btn.width + 4

        if self.valign:
            self.subpar.width = maxWidth
            self.subpar.height = topCount - 4
        elif self.subpar.children:
            self.subpar.width = leftCount - 4
            self.subpar.height = self.subpar.children[0].height
        if self.align not in uiconst.AFFECTEDBYPUSHALIGNMENTS:
            self.width = self.subpar.width
            self.height = self.subpar.height + 8
        elif self.align in (uiconst.TOTOP, uiconst.TOBOTTOM):
            self.height = self.subpar.height + 8
        elif self.align in (uiconst.TOLEFT, uiconst.TORIGHT):
            self.width = self.subpar.width

    def GetMinimumSize(self):
        return (self.subpar.width, self.subpar.height)

    def GetBtnByLabel(self, btnLabel):
        """
        get button by name. send in label of button
        """
        return self.sr.Get('%s_Btn' % btnLabel)

    def GetBtnByIdx(self, idx):
        """
        get button by index. send in button index
        """
        return self.subpar.children[idx]
