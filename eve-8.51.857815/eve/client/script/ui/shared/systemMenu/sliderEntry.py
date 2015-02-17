#Embedded file name: eve/client/script/ui/shared/systemMenu\sliderEntry.py
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from eve.client.script.ui.control.eveLabel import EveLabelSmall
import uicontrols

class SliderEntry(Container):
    default_align = uiconst.TOTOP
    default_height = 10
    default_state = uiconst.UI_PICKCHILDREN
    default_padLeft = 6
    default_padTop = 1
    default_padRight = 6
    default_padBottom = 0
    BASESIZE = 10

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        sliderWidth = attributes.sliderWidth or 100
        config = attributes.config
        sliderParent = Container(name=config[0] + '_slider_sub', parent=self, align=uiconst.TOPRIGHT, pos=(0,
         0,
         sliderWidth,
         self.BASESIZE))
        slider = uicontrols.Slider(parent=sliderParent, width=self.BASESIZE, height=self.BASESIZE, name=config[0], hint=attributes.hint)
        if attributes.header:
            self.headerLabel = EveLabelSmall(text=attributes.header, parent=self, padRight=sliderWidth + 6, state=uiconst.UI_PICKCHILDREN, align=uiconst.TOTOP)
            self.headerLabel.OnSizeChanged = self.OnHeaderSizeChanged
        slider.GetSliderValue = attributes.GetSliderValue
        slider.SetSliderLabel = attributes.SetSliderLabel
        slider.GetSliderHint = attributes.GetSliderHint
        slider.EndSetSliderValue = attributes.EndSliderValue
        slider.Startup(config[0], attributes.minval, attributes.maxval, config)

    def OnHeaderSizeChanged(self, *args, **kwds):
        self.height = max(self.BASESIZE, self.headerLabel.textheight)
