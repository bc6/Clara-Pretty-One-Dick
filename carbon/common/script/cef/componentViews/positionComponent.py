#Embedded file name: carbon/common/script/cef/componentViews\positionComponent.py
from carbon.common.script.cef.baseComponentView import BaseComponentView

class PositionComponentView(BaseComponentView):
    __guid__ = 'cef.PositionComponentView'
    __COMPONENT_ID__ = const.cef.POSITION_COMPONENT_ID
    __COMPONENT_DISPLAY_NAME__ = 'Position'
    __COMPONENT_CODE_NAME__ = 'position'
    __DESCRIPTION__ = 'Maintains the position and rotation of the entity'
    POS = 'position'
    ROT = 'rotation'

    @classmethod
    def SetupInputs(cls):
        cls.RegisterComponent(cls)
        cls._AddInput(cls.POS, None, cls.RUNTIME, const.cef.COMPONENTDATA_NON_PRIMITIVE_TYPE, displayName='Position')
        cls._AddInput(cls.ROT, None, cls.RUNTIME, const.cef.COMPONENTDATA_NON_PRIMITIVE_TYPE, displayName='Rotation')


PositionComponentView.SetupInputs()
