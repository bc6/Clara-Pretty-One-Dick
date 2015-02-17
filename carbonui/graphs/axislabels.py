#Embedded file name: carbonui/graphs\axislabels.py
import trinity
from carbonui.primitives.container import Container
import carbonui.const as uiconst

class VerticalAxisLabels(Container):
    default_name = 'verticalaxislabels'
    default_align = uiconst.TOALL

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.maxValue = attributes.get('maxValue', 0)
        self.labelclass = attributes.get('labelClass', None)
        self.fontsize = attributes.get('fontsize', None)
        self.step = attributes.get('step', 32)
        self.count = attributes.get('count', 1)
        if not self.fontsize:
            self.fontsize = self.labelclass.default_fontsize
        self.Build()

    def Build(self):
        width, height = self.GetAbsoluteSize()
        y = height - self.step - self.fontsize * 2 / 3
        for i in xrange(self.count):
            labelValue = self.maxValue / float(self.count) * (i + 1)
            self.labelclass(parent=self, text=str(labelValue), top=y, fontsize=self.fontsize)
            y -= self.step

    def Rebuild(self):
        self.Flush()
        self.Build()
