#Embedded file name: carbon/common/script/cef/componentViews\hateComponentView.py
from carbon.common.script.cef.baseComponentView import BaseComponentView

class HateComponentView(BaseComponentView):
    __guid__ = 'cef.HateComponentView'
    __COMPONENT_ID__ = const.cef.HATE_COMPONENT_ID
    __COMPONENT_DISPLAY_NAME__ = 'Hate'
    __COMPONENT_CODE_NAME__ = 'hate'
    __COMPONENT_DEPENDENCIES__ = []

    @classmethod
    def SetupInputs(cls):
        cls.RegisterComponent(cls)


HateComponentView.SetupInputs()
