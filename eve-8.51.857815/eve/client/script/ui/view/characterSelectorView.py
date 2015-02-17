#Embedded file name: eve/client/script/ui/view\characterSelectorView.py
from viewstate import View
from eve.client.script.ui.login.charsel import CharSelection
from eve.client.script.ui.login.charSelection.characterSelection import CharacterSelection

class CharacterSelectorView(View):
    __guid__ = 'viewstate.CharacterSelectorView'
    __notifyevents__ = []
    __dependencies__ = ['menu', 'tutorial']
    __layerClass__ = CharacterSelection
    __progressText__ = 'UI_CHARSEL_ENTERINGCHARSEL'

    def LoadView(self, **kwargs):
        """Called when the view is loaded"""
        View.LoadView(self, **kwargs)

    def UnloadView(self):
        """Used for cleaning up after the view has served its purpose"""
        View.UnloadView(self)
