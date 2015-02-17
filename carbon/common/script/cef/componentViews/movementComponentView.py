#Embedded file name: carbon/common/script/cef/componentViews\movementComponentView.py
from carbon.common.script.cef.baseComponentView import BaseComponentView

class MovementComponentView(BaseComponentView):
    __guid__ = 'cef.MovementComponentView'
    __COMPONENT_ID__ = const.cef.MOVEMENT_COMPONENT_ID
    __COMPONENT_DISPLAY_NAME__ = 'Movement'
    __COMPONENT_CODE_NAME__ = 'movement'
    __COMPONENT_DEPENDENCIES__ = [const.cef.POSITION_COMPONENT_ID]

    @classmethod
    def SetupInputs(cls):
        cls.RegisterComponent(cls)


MovementComponentView.SetupInputs()
