#Embedded file name: carbon/common/script/cef/componentViews\selectionComponentView.py
from carbon.common.script.cef.baseComponentView import BaseComponentView

class SelectionComponentView(BaseComponentView):
    __guid__ = 'cef.SelectionComponentView'
    __COMPONENT_ID__ = const.cef.SELECTION_COMPONENT_ID
    __COMPONENT_DISPLAY_NAME__ = 'Selection'
    __COMPONENT_CODE_NAME__ = 'selectionComponent'

    @classmethod
    def SetupInputs(cls):
        cls.RegisterComponent(cls)


SelectionComponentView.SetupInputs()
