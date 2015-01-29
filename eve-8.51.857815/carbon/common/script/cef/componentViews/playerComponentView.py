#Embedded file name: carbon/common/script/cef/componentViews\playerComponentView.py
from carbon.common.script.cef.baseComponentView import BaseComponentView

class PlayerComponentView(BaseComponentView):
    """
    This component should not be attached in static data.
    It is only for players, and players are never static data.
    """
    __guid__ = 'cef.PlayerComponentView'
    __COMPONENT_ID__ = const.cef.PLAYER_COMPONENT_ID
    __COMPONENT_DISPLAY_NAME__ = 'Player'
    __COMPONENT_CODE_NAME__ = 'player'

    @classmethod
    def SetupInputs(cls):
        cls.RegisterComponent(cls)


PlayerComponentView.SetupInputs()
