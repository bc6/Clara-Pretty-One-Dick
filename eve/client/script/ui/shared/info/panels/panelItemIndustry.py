#Embedded file name: eve/client/script/ui/shared/info/panels\panelItemIndustry.py
import const
import listentry
import localization
from carbonui.primitives.container import Container
from eve.client.script.ui.control.eveScroll import Scroll
from utillib import KeyVal

class PanelItemIndustry(Container):
    """
    Show info tab panel for item materials.
    """

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.typeID = attributes.typeID

    def Load(self):
        self.Flush()
        entries = []
        bpData = sm.GetService('blueprintSvc').GetBlueprintByProduct(self.typeID)
        if bpData and cfg.invtypes.Get(bpData.blueprintTypeID).published:
            entries.append(listentry.Get(decoClass=listentry.Header, data=KeyVal(label=localization.GetByLabel('UI/Industry/Blueprint'))))
            entries.append(listentry.Get(decoClass=listentry.Item, data=KeyVal(label=bpData.GetName(), typeID=bpData.blueprintTypeID, getIcon=1)))
        materials = cfg.invtypematerials.get(self.typeID)
        if materials:
            entries.append(listentry.Get(decoClass=listentry.Header, data=KeyVal(label=localization.GetByLabel('UI/Reprocessing/ReprocessedMaterials'))))
            for _, typeID, quantity in materials:
                entries.append(listentry.Get(decoClass=listentry.Item, data=KeyVal(label=localization.GetByLabel('UI/InfoWindow/TypeNameWithNumUnits', invType=typeID, qty=quantity), typeID=typeID, getIcon=1, quantity=quantity)))

        self.scroll = Scroll(parent=self, padding=const.defaultPadding)
        self.scroll.Load(contentList=entries)
