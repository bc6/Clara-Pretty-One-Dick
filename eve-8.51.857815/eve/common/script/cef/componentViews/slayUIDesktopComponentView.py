#Embedded file name: eve/common/script/cef/componentViews\slayUIDesktopComponentView.py
from carbon.common.script.cef.baseComponentView import BaseComponentView

class SlayUIDesktopComponentView(BaseComponentView):
    __guid__ = 'cef.SlayUIDesktopComponentView'
    __COMPONENT_ID__ = const.cef.SLAYUIDESKTOP_COMPONENT_ID
    __COMPONENT_DISPLAY_NAME__ = 'SlayUIDesktop'
    __COMPONENT_CODE_NAME__ = 'SlayUIDesktopComponent'
    UI_DESKTOP_NAME = 'SlayUIDesktopName'

    @classmethod
    def SetupInputs(cls):
        cls.RegisterComponent(cls)


SlayUIDesktopComponentView.SetupInputs()
