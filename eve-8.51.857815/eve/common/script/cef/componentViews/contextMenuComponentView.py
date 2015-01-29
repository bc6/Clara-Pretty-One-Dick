#Embedded file name: eve/common/script/cef/componentViews\contextMenuComponentView.py
from carbon.common.script.cef.baseComponentView import BaseComponentView

class ContextMenuComponentView(BaseComponentView):
    __guid__ = 'cef.ContextMenuComponentView'
    __COMPONENT_ID__ = const.cef.CONTEXT_MENU_COMPONENT_ID
    __COMPONENT_DISPLAY_NAME__ = 'Context Menu'
    __COMPONENT_CODE_NAME__ = 'contextMenu'
    __SHOULD_SPAWN__ = {'client': True}

    @classmethod
    def SetupInputs(cls):
        cls.RegisterComponent(cls)


ContextMenuComponentView.SetupInputs()
