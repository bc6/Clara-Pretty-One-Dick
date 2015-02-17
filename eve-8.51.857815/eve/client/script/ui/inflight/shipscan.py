#Embedded file name: eve/client/script/ui/inflight\shipscan.py
import uiprimitives
import uicontrols
import uix
import util
from eve.client.script.ui.control import entries as listentry
import carbonui.const as uiconst
import localization

class ShipScan(uicontrols.Window):
    __guid__ = 'form.ShipScan'
    default_windowID = 'shipscan'
    default_iconNum = 'res:/ui/Texture/WindowIcons/shipScan.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        shipID = attributes.shipID
        self.SetMinSize([200, 200])
        self.SetWndIcon(self.iconNum, mainTop=-13)
        self.DefineButtons(uiconst.CLOSE)
        self.sr.capacityText = uicontrols.EveHeaderSmall(text=' ', name='capacityText', parent=self.sr.topParent, left=8, top=4, align=uiconst.TOPRIGHT, state=uiconst.UI_DISABLED)
        self.sr.gaugeParent = uiprimitives.Container(name='gaugeParent', align=uiconst.TOPRIGHT, parent=self.sr.topParent, left=const.defaultPadding, height=7, width=100, state=uiconst.UI_DISABLED, top=self.sr.capacityText.top + self.sr.capacityText.textheight + 1)
        uicontrols.Frame(parent=self.sr.gaugeParent, color=(0.5, 0.5, 0.5, 0.3))
        self.sr.gauge = uiprimitives.Container(name='gauge', align=uiconst.TOLEFT, parent=self.sr.gaugeParent, state=uiconst.UI_PICKCHILDREN, width=0)
        uiprimitives.Fill(parent=self.sr.gaugeParent, color=(0.0, 0.521, 0.67, 0.1), align=uiconst.TOALL)
        uiprimitives.Fill(parent=self.sr.gauge, color=(0.0, 0.521, 0.67, 0.6))
        self.sr.scroll = uicontrols.Scroll(parent=self.sr.main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        t = uicontrols.EveHeaderSmall(text=localization.GetByLabel('UI/Ship/ShipScan/hdrModulesFitted'), parent=self.sr.topParent, left=8, state=uiconst.UI_DISABLED, align=uiconst.BOTTOMLEFT)
        self.LoadResult(*attributes.results)

    def LoadResult(self, capacitorCharge, capacitorCapacity, moduleList):
        total, full = capacitorCapacity, capacitorCharge
        if total:
            proportion = min(1.0, max(0.0, full / float(total)))
        else:
            proportion = 1.0
        self.sr.gauge.width = int(proportion * self.sr.gaugeParent.width)
        units = cfg.dgmunits.Get(const.unitCapacitorUnits).displayName
        self.sr.capacityText.text = localization.GetByLabel('UI/Ship/ShipScan/CapacityResults', full=full, total=total, units=units)
        scrolllist = []
        for info in moduleList:
            if type(info) == type(()):
                typeID, quantity = info
            else:
                typeID, quantity = info.typeID, info.stacksize
            invtype = cfg.invtypes.Get(typeID)
            if invtype.categoryID == const.categoryCharge:
                quantity = 1
            for i in range(quantity):
                data = util.KeyVal()
                data.label = invtype.name
                data.itemID = None
                data.typeID = typeID
                data.getIcon = 1
                scrolllist.append(listentry.Get('Item', data=data))

        self.sr.scroll.Load(contentList=scrolllist)
        if len(scrolllist) == 0:
            self.SetHint(localization.GetByLabel('UI/Ship/ShipScan/hintNoModulesDetected'))
        else:
            self.SetHint(None)

    def SetHint(self, hintstr = None):
        if self.sr.scroll:
            self.sr.scroll.ShowHint(hintstr)


class CargoScan(uicontrols.Window):
    __guid__ = 'form.CargoScan'
    default_windowID = 'cargoScan'
    default_iconNum = 'res:/ui/Texture/WindowIcons/cargoScan.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        shipID = attributes.shipID
        cargoList = attributes.cargoList
        bp = sm.GetService('michelle').GetBallpark()
        if not bp:
            return
        slimItem = bp.slimItems[shipID]
        shipName = uix.GetSlimItemName(slimItem)
        self.SetCaption(localization.GetByLabel('UI/Ship/ShipScan/ShipNameCargo', shipName=shipName, cargoListLen=len(cargoList)))
        self.SetMinSize([200, 200])
        self.SetWndIcon(self.iconNum, mainTop=-13)
        self.DefineButtons(uiconst.CLOSE)
        self.sr.scroll = uicontrols.Scroll(parent=self.sr.main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        t = uicontrols.EveHeaderSmall(text=localization.GetByLabel('UI/Ship/ShipScan/hdrCargoScan'), parent=self.sr.topParent, left=8, state=uiconst.UI_DISABLED, align=uiconst.BOTTOMLEFT)

    def ShowInfo(self, typeID, isCopy):
        abstractInfo = util.KeyVal(categoryID=const.categoryBlueprint, isCopy=isCopy)
        sm.GetService('info').ShowInfo(typeID)

    def LoadResult(self, cargoList):
        scrolllist = []
        for typeID, quantity in cargoList:
            invType = cfg.invtypes.Get(typeID)
            qty = quantity if quantity > 0 else 1
            data = util.KeyVal()
            isCopy = False
            param = {'qty': qty,
             'typeID': typeID}
            if invType.categoryID == const.categoryBlueprint:
                if quantity == -const.singletonBlueprintCopy:
                    typeName = 'UI/Ship/ShipScan/BlueprintCopy'
                    quantity = 1
                    isCopy = True
                else:
                    typeName = 'UI/Ship/ShipScan/BlueprintOriginal'
            else:
                typeName = 'UI/Ship/ShipScan/FoundTypes'
            data.label = localization.GetByLabel(typeName, **param)
            data.itemID = None
            data.typeID = typeID
            data.isCopy = isCopy
            data.getIcon = True
            if invType.categoryID == const.categoryBlueprint:
                data.abstractinfo = util.KeyVal(categoryID=const.categoryBlueprint, isCopy=data.isCopy)
            scrolllist.append(listentry.Get('Item', data=data))

        self.sr.scroll.Load(contentList=scrolllist, noContentHint=localization.GetByLabel('UI/Ship/ShipScan/NoBookmarksFound'))
