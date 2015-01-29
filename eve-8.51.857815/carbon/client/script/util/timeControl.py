#Embedded file name: carbon/client/script/util\timeControl.py
"""
Provides a simple UI window for diagnostic tweaking of time-related behaviours.

# PK: Diagnostics to control time, especially variable-vs-fixed ticking. (2010/03)

As used by 'insider.py'
"""
import uiprimitives
import uicontrols
import uicls
import carbonui.const as uiconst
import blue
import trinity

class TimeControlWindow(uicontrols.Window):
    """A diagnostic window for testing time-based behaviour.
    
    UI-code copied from http://eve/w/index.php?title=UI_Beginners_Guide&oldid=24620#UI_controls
    """
    __guid__ = 'uicls.TimeControlWindow'
    default_width = 300
    default_height = 250
    default_caption = 'Time Control Window'
    default_minSize = (300, 250)
    default_windowID = 'TimeControlWindow'
    showTimeGraphs = False

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        if hasattr(self, 'SetTopparentHeight'):
            self.SetTopparentHeight(0)
        self.topCont = uiprimitives.Container(parent=self.sr.content, name='topCont', align=uiconst.TOTOP, height=200)
        self.topLeftCont = uiprimitives.Container(parent=self.topCont, name='topLeftCont', align=uiconst.TOLEFT, width=120, padding=(3, 20, 3, 3))
        self.topRightCont = uiprimitives.Container(parent=self.topCont, name='topRightCont', align=uiconst.TOALL, padding=(3, 10, 3, 3))
        self.mainCont = uiprimitives.Container(parent=self.sr.main, name='mainCont')
        self.ConstructTopLeftCont()
        self.ConstructTopRightCont()

    def ConstructTopLeftCont(self):
        uiprimitives.Line(parent=self.topLeftCont, align=uiconst.TORIGHT)
        uicontrols.Label(parent=self.topLeftCont, text='Select clock:', align=uiconst.TOTOP)
        uicontrols.Checkbox(parent=self.topLeftCont, text='Actual', groupname='clockGroup', align=uiconst.TOTOP, checked=not blue.os.useSmoothedDeltaT, callback=self.OnClockRadioButtonsChanged, retval=False)
        uicontrols.Checkbox(parent=self.topLeftCont, text='Smoothed', groupname='clockGroup', align=uiconst.TOTOP, checked=blue.os.useSmoothedDeltaT, callback=self.OnClockRadioButtonsChanged, retval=True)
        uicontrols.Label(parent=self.topLeftCont, align=uiconst.TOTOP, text='Time Scaler:', pos=(0, 0, 0, 0))
        uicontrols.SinglelineEdit(parent=self.topLeftCont, name='timeScaler', align=uiconst.TOTOP, floats=(0.0, 100.0), setvalue=blue.os.timeScaler, OnChange=self.OnTimeScalerChanged, pos=(0, 0, 20, 12))

    def OnTimeScalerChanged(self, value):
        if value:
            blue.os.timeScaler = float(value)

    def OnClockRadioButtonsChanged(self, button):
        blue.os.useSmoothedDeltaT = button.data['value']

    def ConstructTopRightCont(self):
        cont = uiprimitives.Container(parent=self.topRightCont, align=uiconst.TOTOP, height=70, padTop=12, padBottom=10)
        uicontrols.Label(parent=cont, align=uiconst.TOTOP, text='Slug Min Time:', pos=(0, 0, 0, 0))
        uicontrols.SinglelineEdit(parent=cont, name='slugMinEdit', align=uiconst.TOTOP, ints=(0, 1000), setvalue=int(blue.os.slugTimeMinMs), OnChange=self.OnSlugMinChanged, pos=(0, 0, 100, 12))
        uicontrols.Label(parent=cont, align=uiconst.TOTOP, text='Slug Max Time:', pos=(0, 0, 0, 0))
        uicontrols.SinglelineEdit(parent=cont, name='slugMaxEdit', align=uiconst.TOTOP, ints=(0, 1000), setvalue=int(blue.os.slugTimeMaxMs), OnChange=self.OnSlugMaxChanged, pos=(0, 0, 100, 12))
        uicontrols.Checkbox(parent=self.topRightCont, text='Use Simple Loop', align=uiconst.TOTOP, checked=blue.os.useSimpleCatchupLoop, callback=self.OnSimpleLoopChanged, padBottom=10)
        uicontrols.Checkbox(parent=self.topRightCont, text='Show Time Graphs', align=uiconst.TOTOP, checked=self.showTimeGraphs, callback=self.OnTimeGraphsChanged, padBottom=10)

    def OnSlugMinChanged(self, value):
        if value:
            blue.os.slugTimeMinMs = float(value)

    def OnSlugMaxChanged(self, value):
        if value:
            blue.os.slugTimeMaxMs = float(value)

    def OnSimpleLoopChanged(self, checkBox):
        blue.os.useSimpleCatchupLoop = checkBox.GetValue()
        blue.os.useNominalDeltaT = not blue.os.useSimpleCatchupLoop

    def OnTimeGraphsChanged(self, checkBox):
        print 'OnTimeGraphsChanged', checkBox
        timerList = ['Blue/actualDeltaT', 'Blue/smoothedDeltaT', 'Blue/usedDeltaT']
        if checkBox.GetValue():
            trinity.graphs.SetEnabled(True)
            fn = trinity.graphs.AddGraph
            seq = timerList
        else:
            fn = trinity.graphs.RemoveGraph
            seq = reversed(timerList)
        map(fn, seq)
        self.showTimeGraphs = checkBox.GetValue()

    def ConstructMainCont(self):
        uiprimitives.Line(parent=self.mainCont, align=uiconst.TOTOP)
        self.mainSprite = uiprimitives.Sprite(parent=self.mainCont, name='mainSprite', pos=(0, 0, 128, 128), align=uiconst.CENTER, texturePath='res:/UI/Texture/corpLogoLibs/logolib0101.dds')
