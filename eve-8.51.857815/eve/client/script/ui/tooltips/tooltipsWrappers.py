#Embedded file name: eve/client/script/ui/tooltips\tooltipsWrappers.py
"""
Tooltip wrappers for common tooltips layouts
"""
from eve.client.script.ui.control.tooltips import TooltipPanel
import carbonui.const as uiconst

class TooltipBaseWrapper(object):
    tooltipPointer = None

    def __init__(self, *args, **optionalKeywordArguments):
        self.tooltipPointer = optionalKeywordArguments.get('tooltipPointer', None)

    def GetProperty(self, propertyName):
        return getattr(self, '_' + propertyName)

    def SetProperty(self, propertyName, value, callback):
        if getattr(self, '_' + propertyName) != value:
            setattr(self, '_' + propertyName, value)
            if callback:
                callback()


class TooltipHeaderDescriptionWrapper(TooltipBaseWrapper):

    def __init__(self, header, description, *args, **kwds):
        TooltipBaseWrapper.__init__(self, *args, **kwds)
        self._headerText = header
        self._descriptionText = description
        self.tooltipPanel = None

    headerText = property(lambda self: self.GetProperty('headerText'), lambda self, value: self.SetProperty('headerText', value, self.UpdateHeader))
    descriptionText = property(lambda self: self.GetProperty('descriptionText'), lambda self, value: self.SetProperty('descriptionText', value, self.UpdateDescription))

    def CreateTooltip(self, parent, owner, idx):
        self.tooltipPanel = TooltipPanel(parent=parent, owner=owner, idx=idx)
        self.tooltipPanel.LoadGeneric1ColumnTemplate()
        self.labelObj = self.tooltipPanel.AddLabelMedium(text=self._headerText, bold=True, colSpan=self.tooltipPanel.columns - 1)
        if self.descriptionText:
            self.descrObj = self.CreateDescriptionObject()
        else:
            self.descrObj = None
        return self.tooltipPanel

    def CreateDescriptionObject(self):
        self.descrObj = self.tooltipPanel.AddLabelMedium(text=self._descriptionText, align=uiconst.TOPLEFT, wrapWidth=200, colSpan=self.tooltipPanel.columns, color=(0.6, 0.6, 0.6, 1))

    def UpdateHeader(self):
        if self.tooltipPanel and not self.tooltipPanel.destroyed and not self.tooltipPanel.beingDestroyed:
            self.labelObj.text = self._headerText

    def UpdateDescription(self):
        if not self.tooltipPanel or self.tooltipPanel.destroyed or self.tooltipPanel.beingDestroyed:
            return
        if self.descrObj is None:
            self.descrObj = self.CreateDescriptionObject()
        else:
            self.descrObj.text = self._descriptionText
