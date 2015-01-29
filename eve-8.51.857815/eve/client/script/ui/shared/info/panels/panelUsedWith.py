#Embedded file name: eve/client/script/ui/shared/info/panels\panelUsedWith.py
from carbonui.primitives.container import Container
from eve.client.script.ui.control.eveScroll import Scroll
import const
from utillib import KeyVal

class PanelUsedWith(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.typeID = attributes.typeID
        self.isInitialized = False

    def Load(self):
        if self.isInitialized:
            return
        self.scroll = Scroll(name='scroll', parent=self, padding=const.defaultPadding)
        scrolllist = self.GetScrollList(self.typeID)
        self.scroll.Load(fixedEntryHeight=27, contentList=scrolllist)
        self.isInitialized = True

    def GetScrollList(self, data, *args):
        scrolllist = []
        usedWith = sm.GetService('info').GetUsedWithTypeIDs(self.typeID)
        typeIDs = []
        for typeID in usedWith:
            typeObj = cfg.invtypes.Get(typeID)
            if typeID in cfg.invmetatypes:
                typeIDs.append(cfg.invmetatypes.Get(typeID))
            else:
                typeIDs.append(KeyVal(typeID=typeID, metaGroupID=1))

        scrolllist, _ = sm.GetService('info').GetTypesSortedByMetaScrollList(typeIDs)
        return scrolllist
