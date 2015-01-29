#Embedded file name: carbon/common/script/cef/componentViews\jessicaTextComponentView.py
from carbon.common.script.cef.baseComponentView import BaseComponentView

class JessicaTextComponentView(BaseComponentView):
    __guid__ = 'cef.JessicaTextComponentView'
    __COMPONENT_ID__ = const.cef.JESSICA_TEXT_COMPONENT_ID
    __COMPONENT_DISPLAY_NAME__ = 'Jessica Text'
    __COMPONENT_CODE_NAME__ = 'jessicaText'

    @classmethod
    def SetupInputs(cls):
        cls.RegisterComponent(cls)


JessicaTextComponentView.SetupInputs()
