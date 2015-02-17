#Embedded file name: carbon/common/script/cef/componentViews\apertureSubjectComponentView.py
from carbon.common.script.cef.baseComponentView import BaseComponentView

class ApertureSubjectComponentView(BaseComponentView):
    __guid__ = 'cef.ApertureSubjectComponentView'
    __COMPONENT_ID__ = const.cef.APERTURE_SUBJECT_COMPONENT_ID
    __COMPONENT_DISPLAY_NAME__ = 'Aperture Subject'
    __COMPONENT_CODE_NAME__ = 'apertureSubject'

    @classmethod
    def SetupInputs(cls):
        cls.RegisterComponent(cls)


ApertureSubjectComponentView.SetupInputs()
