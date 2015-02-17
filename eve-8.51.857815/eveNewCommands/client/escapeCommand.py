#Embedded file name: eveNewCommands/client\escapeCommand.py
from eve.client.script.ui.view.viewStateConst import ViewState

class EscapeCommand:

    def __init__(self, viewStateSrvc, adaptor):
        self.viewStateSrvc = viewStateSrvc
        self.adaptor = adaptor

    def Execute(self):
        if self.HasModalsOrMenusToClose():
            self.CloseModalsAndMenus()
        elif self.adaptor.IsEscapeMenuActive():
            self.adaptor.HideEscapeMenu()
        elif self.HasSecondaryViewsToClose():
            self.CloseSecondaryViews()
        else:
            self.adaptor.ShowEscapeMenu()

    def HasModalsOrMenusToClose(self):
        if self.adaptor.IsDisconnectNoticeDisplayed() or self.adaptor.HasOpenMenuItems() or self.adaptor.HasCancellableModal() or self.adaptor.HasActiveLoading():
            return True
        else:
            return False

    def CloseModalsAndMenus(self):
        if self.HasModalsOrMenusToClose():
            if self.adaptor.HasOpenMenuItems():
                self.adaptor.ClearMenu()
            elif self.adaptor.HasCancellableModal():
                self.adaptor.CloseModalWithCancelResult()
            elif self.adaptor.HasActiveLoading():
                self.adaptor.HideAllLoading()
            return False
        else:
            return True

    def GetEscViews(self):
        return [ViewState.Login, ViewState.Intro]

    def GetIgnoredViews(self):
        return [ViewState.CharacterCreation]

    def HasSecondaryViewsToClose(self):
        viewName = self.viewStateSrvc.GetActiveViewName()
        if viewName in self.GetIgnoredViews():
            return False
        else:
            return viewName in self.GetEscViews() or self.viewStateSrvc.IsCurrentViewSecondary()

    def CloseSecondaryViews(self):
        viewName = self.viewStateSrvc.GetActiveViewName()
        if viewName in self.GetEscViews():
            self.viewStateSrvc.GetView(viewName).layer.OnEsc()
        elif self.viewStateSrvc.IsCurrentViewSecondary():
            self.viewStateSrvc.CloseSecondaryView(viewName)
