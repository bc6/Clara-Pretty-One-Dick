#Embedded file name: eve/client/script/ui/shared\gauge.py
import uiprimitives
YELLOWY = 0.5625
YELLOWMIN = 0.497
YELLOWMAX = 0.206
YELLOWRANGE = YELLOWMAX - YELLOWMIN

class Gauge(uiprimitives.Container):
    __guid__ = 'xtriui.Gauge'
    __nonpersistvars__ = ['gaugemin', 'gaugerange']

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.SetType('yellow')

    def SetType(self, gaugetype):
        if gaugetype == 'yellow':
            self.control.model.areas[0].areaTextures[2].scaling.x = 0.3
            self.control.model.areas[0].areaTextures[2].translation.y = YELLOWY
            self.gaugemin = YELLOWMIN
            self.gaugerange = YELLOWRANGE
        else:
            raise RuntimeError('Unknown gauge type!', gaugetype)

    def SetProportion(self, proportion):
        self.control.model.areas[0].areaTextures[2].translation.x = self.gaugemin + self.gaugerange * proportion
