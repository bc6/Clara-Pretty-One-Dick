#Embedded file name: eve/client/script/ui/control\damageGaugeContainers.py
"""
    this file contains containers that display 4 damage types
"""
from eve.client.script.ui.control import entries as listentry
from carbonui.primitives.container import Container
import carbonui.const as uiconst
from eve.client.script.ui.control.gauge import Gauge
from eve.client.script.ui.control.eveIcon import Icon

class DamageGaugeContainer(Container):
    """
        This is a container that has 4 sections, one for each of the damage types.
    """
    iconSize = 24
    containerPadding = 4
    showIcon = True
    gaugeHeight = 16
    gaugeTopOffset = 7
    damageTypesAndColors = [('em', (0.1, 0.37, 0.55, 1.0)),
     ('thermal', (0.55, 0.1, 0.1, 1.0)),
     ('kinetic', (0.45, 0.45, 0.45, 1.0)),
     ('explosive', (0.55, 0.37, 0.1, 1.0))]

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.innerContainers = {}
        for damageType, color in self.damageTypesAndColors:
            container = Container(parent=self, name='container_%s' % damageType, width=0.25, align=uiconst.TOLEFT_PROP, padding=(self.containerPadding,
             0,
             self.containerPadding,
             0), state=uiconst.UI_NORMAL)
            self.innerContainers[damageType] = container
            self.AddGaugeAndIconToContainer(container, damageType, color=color)
            if damageType == 'explosive':
                container.SetAlign(uiconst.TOALL)
                container.width = 0

    def AddGaugeAndIconToContainer(self, container, damageType, color):
        iconCont = Container(parent=container, name='iconCont', width=self.iconSize, align=uiconst.TOLEFT, state=uiconst.UI_DISABLED)
        icon = Icon(parent=iconCont, pos=(0,
         0,
         self.iconSize,
         self.iconSize), align=uiconst.CENTERLEFT, idx=0, ignoreSize=True, state=uiconst.UI_DISABLED)
        if not self.showIcon:
            iconCont.display = False
        gauge = Gauge(parent=container, name='gauge_%s' % damageType, value=0.0, color=color, gaugeHeight=self.gaugeHeight, align=uiconst.TOALL, pos=(0,
         self.gaugeTopOffset,
         0,
         0), state=uiconst.UI_DISABLED, gradientBrightnessFactor=1.5)
        container.gauge = gauge
        container.icon = icon
        setattr(self, 'gauge_%s' % damageType, gauge)

    def LoadInfo(self, damageInfo, onClickFunc):
        for attributeInfo in damageInfo:
            self.UpdateGauge(attributeInfo, False, onClickFunc)

    def GetContainerForDamageType(self, damageType):
        return self.innerContainers[damageType]

    def UpdateGauge(self, info, animate = False, onClickFunc = None):
        if info is None:
            return
        dmgType = info['dmgType']
        container = self.GetContainerForDamageType(dmgType)
        if container is None:
            return
        if onClickFunc:
            container.OnClick = (onClickFunc, info['attributeID'])
        gauge = container.gauge
        gauge.SetValue(info['value'], animate=animate)
        gauge.SetValueText(text=info['valueText'])
        iconID = info.get('iconID')
        if iconID is not None:
            container.icon.LoadIcon(iconID, ignoreSize=True)
        text = info.get('text')
        if text is not None:
            container.hint = text


class DamageGaugeContainerFitting(DamageGaugeContainer):
    """
        This is a container that has 4 sections, one for each of the damage types. It's used in the Fitting window
    """
    containerPadding = 3
    showIcon = False
    gaugeHeight = 16
    gaugeTopOffset = 8


class DamageEntry(listentry.Generic):

    def Startup(self, *args):
        listentry.Generic.Startup(self, *args)
        self.height = 30
        self.damageContainer = DamageGaugeContainer(parent=self)

    def Load(self, node):
        node.selectable = False
        self.damageContainer.LoadInfo(node.attributeInfoList, node.OnClick)

    def GetHeight(self, *args):
        node, width = args
        node.height = 30
        return node.height

    @classmethod
    def GetCopyData(cls, node):
        damageTextList = []
        for info in node.attributeInfoList:
            text = '%s\t%s' % (info['text'], info['valueText'])
            damageTextList.append(text)

        return '\n'.join(damageTextList)
