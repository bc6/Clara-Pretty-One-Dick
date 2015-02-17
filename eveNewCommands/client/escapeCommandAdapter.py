#Embedded file name: eveNewCommands/client\escapeCommandAdapter.py
from carbonui.control.menu import HasContextMenu, CloseContextMenus
from eveNewCommands.client.abstractEscapeCommandAdaptor import AbstractEscapeCommandAdapter
import carbonui.const as uiconst
import uthread

class EscapeCommandAdapter(AbstractEscapeCommandAdapter):

    def HasOpenMenuItems(self):
        return HasContextMenu()

    def ClearMenu(self):
        CloseContextMenus()

    def CloseModalWithCancelResult(self):
        modalResult = uicore.registry.GetModalResult(uiconst.ID_CANCEL, 'btn_cancel')
        uicore.registry.GetModalWindow().SetModalResult(modalResult)

    def ShowEscapeMenu(self):
        systemMenu = uicore.layer.systemmenu
        sm.GetService('uipointerSvc').HidePointer()
        uthread.new(systemMenu.OpenView)

    def HideEscapeMenu(self):
        systemMenu = uicore.layer.systemmenu
        sm.GetService('uipointerSvc').ShowPointer()
        uthread.new(systemMenu.CloseMenu)

    def IsEscapeMenuActive(self):
        systemMenu = uicore.layer.systemmenu
        return systemMenu.isopen

    def HideAllLoading(self):
        uthread.new(sm.GetService('loading').HideAllLoad)

    def IsDisconnectNoticeDisplayed(self):
        return sm.GetService('gameui').HasDisconnectionNotice()

    def HasCancellableModal(self):
        return uicore.registry.GetModalResult(uiconst.ID_CANCEL, 'btn_cancel') is not None

    def HasActiveLoading(self):
        return uicore.layer.loading.state == uiconst.UI_NORMAL
