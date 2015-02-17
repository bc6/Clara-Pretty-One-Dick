#Embedded file name: eve/client/script/ui/shared/neocom/corporation\corp_ui_member_newroles.py
from carbonui.primitives.container import Container
from localization import GetByLabel

class CorpRolesNew(Container):
    __guid__ = 'form.CorpRolesNew'
    __nonpersistvars__ = []

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)

    def Load(self, populateView = 1, *args):
        sm.GetService('corpui').LoadTop('res:/ui/Texture/WindowIcons/corporationmembers.png', GetByLabel('UI/Corporations/Common/Members'))
