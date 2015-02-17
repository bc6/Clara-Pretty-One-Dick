#Embedded file name: carbon/common/script/cef/componentViews\modifierComponentView.py
from carbon.common.script.cef.baseComponentView import BaseComponentView

class ModifierComponentView(BaseComponentView):
    __guid__ = 'cef.ModifierComponentView'
    __COMPONENT_ID__ = const.cef.MODIFIER_COMPONENT_ID
    __COMPONENT_DISPLAY_NAME__ = 'Modifier'
    __COMPONENT_CODE_NAME__ = 'modifier'

    @classmethod
    def SetupInputs(cls):
        cls.RegisterComponent(cls)


ModifierComponentView.SetupInputs()
