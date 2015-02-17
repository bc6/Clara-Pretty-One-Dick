#Embedded file name: eve/client/script/ui/control\colorPanel.py
from carbonui.primitives.layoutGrid import LayoutGrid
from carbonui.primitives.container import Container
from carbonui.primitives.frame import Frame
from carbonui.primitives.fill import Fill
import carbonui.const as uiconst

class ColorPanel(LayoutGrid):

    def ApplyAttributes(self, attributes):
        LayoutGrid.ApplyAttributes(self, attributes)
        self.columns = 5
        self.cellPadding = 1
        self.cellSpacing = 1
        self.margin = (2, 2, 2, 2)
        self.addClear = attributes.get('addClear', True)
        self.colorList = attributes['colorList']
        self.callback = attributes.callback
        currentColor = attributes.currentColor
        colorPos = (0, 0, 10, 10)
        for eachColor in self.colorList:
            if eachColor == currentColor:
                c = Container(name='colorFill', pos=colorPos, align=uiconst.NOALIGN, state=uiconst.UI_NORMAL)
                Frame(parent=c, name='selectedColorFrame', color=(1, 1, 1, 0.75))
                Fill(parent=c, name='colorFill', color=eachColor, padding=1)
            else:
                c = Fill(name='colorFill', pos=colorPos, color=eachColor, align=uiconst.NOALIGN, state=uiconst.UI_NORMAL)
            c.OnClick = (self.callback, eachColor)
            self.AddCell(cellObject=c, colSpan=1, cellPadding=1)

        if self.addClear:
            c = Frame(name='colorFill', pos=colorPos, color=(1, 1, 1, 0.2), align=uiconst.NOALIGN, state=uiconst.UI_NORMAL)
            c.OnClick = (self.callback, None)
            self.AddCell(cellObject=c, colSpan=1)
