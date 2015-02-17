#Embedded file name: carbonui/graphs\grid.py
import trinity
from carbonui.primitives.container import Container
from carbonui.primitives.vectorline import VectorLine
import carbonui.const as uiconst

class Grid(Container):
    default_name = 'grid'
    default_align = uiconst.TOALL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.maxValue = attributes.get('maxValue', 0)
        self.step = attributes.get('step', 32)
        self.count = attributes.get('count', 1)
        self.Build()

    def Build(self):
        width, height = self.GetAbsoluteSize()
        y = height - self.step
        for i in xrange(int(self.count)):
            VectorLine(parent=self, align=uiconst.TOALL, translationFrom=(0, y), translationTo=(width, y), color=(1, 1, 1, 0.15), spriteEffect=trinity.TR2_SFX_FILL)
            y -= self.step

    def Rebuild(self):
        self.Flush()
        self.Build()
