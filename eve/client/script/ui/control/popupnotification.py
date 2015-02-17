#Embedded file name: eve/client/script/ui/control\popupnotification.py
"""
Simple notififcation window
"""
import uiprimitives
import uicontrols
import uiutil
import carbonui.const as uiconst
import uthread
import blue
import localization

class PopupNotification(uiprimitives.Container):
    __guid__ = 'xtriui.PopupNotification'

    def Startup(self):
        self.state = uiconst.UI_NORMAL
        self.shouldKill = False
        sub = uiprimitives.Container(name='sub', parent=self, align=uiconst.TOALL, pos=(0, 0, 0, 0), state=uiconst.UI_DISABLED)
        uicontrols.Frame(parent=self)
        uiprimitives.Fill(parent=self, color=(0, 0, 0, 1), idx=-1, state=uiconst.UI_DISABLED)
        closex = uicontrols.Icon(icon='ui_38_16_220', parent=self, idx=0, state=uiconst.UI_NORMAL, align=uiconst.TOPRIGHT)
        closex.OnClick = self.CloseNotification
        closex.sr.hint = localization.GetByLabel('UI/Common/CloseNotification')
        iconCont = uiprimitives.Container(name='iconCont', parent=sub, align=uiconst.TOLEFT, pos=(0, 0, 60, 0))
        textCont = uiprimitives.Container(name='textCont', parent=sub, align=uiconst.TOALL, pos=(0, 0, 0, 0), state=uiconst.UI_NORMAL)
        self.sr.icon = uicontrols.Icon(parent=iconCont, icon='50_11', pos=(-2, 2, 64, 64), align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED)
        self.sr.headerText = uicontrols.EveLabelSmall(text='', parent=textCont, padTop=12, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, bold=True)
        self.sr.text1 = uicontrols.EveLabelMedium(text='', parent=textCont, state=uiconst.UI_DISABLED, align=uiconst.TOTOP, padding=(0, -2, 4, 0))
        self.sr.text2 = uicontrols.EveLabelMedium(text='', parent=textCont, state=uiconst.UI_HIDDEN, align=uiconst.TOTOP, padding=(0, -2, 4, 0))
        self.sr.text3 = uicontrols.EveLabelMedium(text='', parent=textCont, state=uiconst.UI_HIDDEN, align=uiconst.TOTOP, padding=(0, -2, 4, 0))

    def Load(self, data, *args):
        iconNum = getattr(data, 'iconNum', None)
        if iconNum:
            self.sr.icon.LoadIcon(iconNum)
        headerText = getattr(data, 'headerText', '')
        self.sr.headerText.text = headerText
        totalHeight = self.sr.headerText.padTop + self.sr.headerText.textheight + self.sr.headerText.padBottom
        text1 = getattr(data, 'text1', '')
        self.sr.text1.text = text1
        totalHeight += self.sr.text1.padTop + self.sr.text1.textheight + self.sr.text1.padBottom
        text2 = getattr(data, 'text2', '')
        if text2:
            self.sr.text2.state = uiconst.UI_DISABLED
            self.sr.text2.text = text2
            totalHeight += self.sr.text2.padTop + self.sr.text2.textheight + self.sr.text2.padBottom
        else:
            self.sr.text2.state = uiconst.UI_HIDDEN
        text3 = getattr(data, 'text3', '')
        if text3:
            self.sr.text3.state = uiconst.UI_DISABLED
            self.sr.text3.text = text3
            totalHeight += self.sr.text3.padTop + self.sr.text3.textheight + self.sr.text3.padBottom
        else:
            self.sr.text3.state = uiconst.UI_HIDDEN
        self.height = max(self.height, totalHeight + 6)
        time = getattr(data, 'time', 10000)
        uthread.new(self.Kill, time)

    def Kill(self, time = 10000):
        blue.pyos.synchro.SleepWallclock(time)
        if not self or self.destroyed:
            return
        if uicore.uilib.mouseOver == self or uiutil.IsUnder(uicore.uilib.mouseOver, self):
            self.shouldKill = True
            return
        self.CloseNotification()

    def CloseNotification(self, *args):
        self.state = uiconst.UI_HIDDEN
        self.Close()

    def OnMouseExit(self, *args):
        if self.shouldKill:
            self.CloseNotification()
