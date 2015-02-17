#Embedded file name: eve/client/script/ui/shared/inventory\invContainers.py
import uiprimitives
import uicontrols
import carbonui.const as uiconst
import uiutil
import invCtrl
import invCont
import crimewatchConst

class _BaseCelestialContainer(invCont._InvContBase):
    __guid__ = 'invCont._BaseCelestialContainer'
    __invControllerClass__ = None

    def ApplyAttributes(self, attributes):
        invCont._InvContBase.ApplyAttributes(self, attributes)
        if self.invController.IsLootable():
            self.CheckCanTakeItems = sm.GetService('crimewatchSvc').CheckCanTakeItems
            self.restrictedFrame = uicontrols.Frame(parent=self, color=crimewatchConst.Colors.Yellow.GetRGBA(), state=uiconst.UI_HIDDEN)
            self.restrictedButtonFill = uiprimitives.Fill(color=crimewatchConst.Colors.Suspect.GetRGBA(), opacity=0.3, name='criminalRestrictionFill', state=uiconst.UI_HIDDEN)
            self.restrictedButton = None
            uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEMOVE, self._EnforceLootableContainerRestrictions)

    def RegisterSpecialActionButton(self, button):
        """
        hooking up the retricted UI to the loot all button
        """
        if self.invController.IsLootable():
            if button.func.__name__ == 'LootAll':
                self.restrictedButton = button
                self.restrictedButtonFill.SetParent(button, 0)

    def _EnforceLootableContainerRestrictions(self, *args):
        if not self or self.destroyed:
            return False
        isAccessRestricted = False
        if uicore.uilib.mouseOver in (self, self.restrictedButton) or uiutil.IsUnder(uicore.uilib.mouseOver, self) or uiutil.IsUnder(uicore.uilib.mouseOver, self.restrictedButton):
            if not self.CheckCanTakeItems(self.invController.itemID):
                isAccessRestricted = True
        if isAccessRestricted:
            self.restrictedFrame.Show()
            self.restrictedButtonFill.Show()
        else:
            self.restrictedFrame.Hide()
            self.restrictedButtonFill.Hide()
        return True


class ShipCargo(invCont._InvContBase):
    __guid__ = 'invCont.ShipCargo'
    __invControllerClass__ = invCtrl.ShipCargo


class POSRefinery(_BaseCelestialContainer):
    """ POS Refinery """
    __guid__ = 'invCont.POSRefinery'
    __invControllerClass__ = invCtrl.POSRefinery


class POSCompression(_BaseCelestialContainer):
    """ POS compression """
    __guid__ = 'invCont.POSCompression'
    __invControllerClass__ = invCtrl.POSCompression


class POSStructureCharges(_BaseCelestialContainer):
    """ A POS structure charges container """
    __guid__ = 'invCont.POSStructureCharges'
    __invControllerClass__ = invCtrl.POSStructureCharges


class POSStructureChargeCrystal(POSStructureCharges):
    """ A POS structure crystal charge container """
    __guid__ = 'invCont.POSStructureChargeCrystal'
    __invControllerClass__ = invCtrl.POSStructureChargeCrystal


class POSStructureChargesStorage(_BaseCelestialContainer):
    """ Charges storage for a POS structure"""
    __guid__ = 'invCont.POSStructureChargesStorage'
    __invControllerClass__ = invCtrl.POSStructureChargesStorage


class POSStrontiumBay(_BaseCelestialContainer):
    """ A POS control tower strontium bay """
    __guid__ = 'invCont.POSStrontiumBay'
    __invControllerClass__ = invCtrl.POSStrontiumBay


class POSFuelBay(_BaseCelestialContainer):
    """ A POS control tower fuel bay """
    __guid__ = 'invCont.POSFuelBay'
    __invControllerClass__ = invCtrl.POSFuelBay


class POSJumpBridge(_BaseCelestialContainer):
    """ A POS Jump bridge """
    __guid__ = 'invCont.POSJumpBridge'
    __invControllerClass__ = invCtrl.POSJumpBridge


class POSShipMaintenanceArray(_BaseCelestialContainer):
    """ A POS Ship maintenance array """
    __guid__ = 'invCont.POSShipMaintenanceArray'
    __invControllerClass__ = invCtrl.POSShipMaintenanceArray


class POSSilo(_BaseCelestialContainer):
    """ A POS Silo """
    __guid__ = 'invCont.POSSilo'
    __invControllerClass__ = invCtrl.POSSilo


class POSMobileReactor(_BaseCelestialContainer):
    """ A POS Mobile reactor """
    __guid__ = 'invCont.POSMobileReactor'
    __invControllerClass__ = invCtrl.POSMobileReactor


class POSConstructionPlatform(_BaseCelestialContainer):
    """ A POS construction platform """
    __guid__ = 'invCont.POSConstructionPlatform'
    __invControllerClass__ = invCtrl.POSConstructionPlatform


class POSPersonalHangar(_BaseCelestialContainer):
    __guid__ = 'invCont.POSPersonalHangar'
    __invControllerClass__ = invCtrl.POSPersonalHangar


class ItemWreck(_BaseCelestialContainer):
    """ Ship wreck """
    __guid__ = 'invCont.ItemWreck'
    __invControllerClass__ = invCtrl.ItemWreck


class ItemFloatingCargo(_BaseCelestialContainer):
    """ Cargo container floating in space """
    __guid__ = 'invCont.ItemFloatingCargo'
    __invControllerClass__ = invCtrl.ItemFloatingCargo


class ItemSiphonPseudoSilo(_BaseCelestialContainer):
    """ POS resource siphoner """
    __guid__ = 'invCont.ItemSiphonPseudoSilo'
    __invControllerClass__ = invCtrl.ItemSiphonPseudoSilo


class StationContainer(_BaseCelestialContainer):
    """ A station container """
    __guid__ = 'invCont.StationContainer'
    __invControllerClass__ = invCtrl.StationContainer


class ShipMaintenanceBay(_BaseCelestialContainer):
    """ Ship maintenance bay """
    __guid__ = 'invCont.ShipMaintenanceBay'
    __invControllerClass__ = invCtrl.ShipMaintenanceBay


class ShipDroneBay(invCont._InvContBase):
    __guid__ = 'invCont.ShipDroneBay'
    __invControllerClass__ = invCtrl.ShipDroneBay


class ShipFuelBay(invCont._InvContBase):
    __guid__ = 'invCont.ShipFuelBay'
    __invControllerClass__ = invCtrl.ShipFuelBay


class ShipOreHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipOreHold'
    __invControllerClass__ = invCtrl.ShipOreHold


class ShipGasHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipGasHold'
    __invControllerClass__ = invCtrl.ShipGasHold


class ShipMineralHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipMineralHold'
    __invControllerClass__ = invCtrl.ShipMineralHold


class ShipSalvageHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipSalvageHold'
    __invControllerClass__ = invCtrl.ShipSalvageHold


class ShipShipHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipShipHold'
    __invControllerClass__ = invCtrl.ShipShipHold


class ShipSmallShipHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipSmallShipHold'
    __invControllerClass__ = invCtrl.ShipSmallShipHold


class ShipMediumShipHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipMediumShipHold'
    __invControllerClass__ = invCtrl.ShipMediumShipHold


class ShipLargeShipHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipLargeShipHold'
    __invControllerClass__ = invCtrl.ShipLargeShipHold


class ShipIndustrialShipHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipIndustrialShipHold'
    __invControllerClass__ = invCtrl.ShipIndustrialShipHold


class ShipAmmoHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipAmmoHold'
    __invControllerClass__ = invCtrl.ShipAmmoHold


class ShipCommandCenterHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipCommandCenterHold'
    __invControllerClass__ = invCtrl.ShipCommandCenterHold


class ShipPlanetaryCommoditiesHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipPlanetaryCommoditiesHold'
    __invControllerClass__ = invCtrl.ShipPlanetaryCommoditiesHold


class ShipFleetHangar(_BaseCelestialContainer):
    __guid__ = 'invCont.ShipFleetHangar'
    __invControllerClass__ = invCtrl.ShipFleetHangar


class ShipQuafeHold(invCont._InvContBase):
    __guid__ = 'invCont.ShipQuafeHold'
    __invControllerClass__ = invCtrl.ShipQuafeHold


class StationCorpDeliveries(invCont._InvContBase):
    __guid__ = 'invCont.StationCorpDeliveries'
    __invControllerClass__ = invCtrl.StationCorpDeliveries


class StationOwnerView(invCont._InvContBase):
    __guid__ = 'invCont.StationOwnerView'
    __invControllerClass__ = invCtrl.StationOwnerView

    def _GetInvController(self, attributes):
        return self.__invControllerClass__(itemID=attributes.itemID, ownerID=attributes.ownerID)


class StationItems(invCont._InvContBase):
    """ View of hangar floor, including all items but ships """
    __guid__ = 'invCont.StationItems'
    __invControllerClass__ = invCtrl.StationItems
    __notifyevents__ = invCont._InvContBase.__notifyevents__ + ['OnItemNameChange']

    def OnItemNameChange(self, *args):
        self.Refresh()


class StationShips(invCont._InvContBase):
    """ View of hangar floor, ships only """
    __guid__ = 'invCont.StationShips'
    __invControllerClass__ = invCtrl.StationShips
    __notifyevents__ = invCont._InvContBase.__notifyevents__ + ['OnItemNameChange', 'ProcessActiveShipChanged']

    def OnItemNameChange(self, *args):
        self.Refresh()

    def ProcessActiveShipChanged(self, shipID, oldShipID):
        self.Refresh()


class StationCorpMember(invCont._InvContBase):
    __guid__ = 'invCont.StationCorpMember'
    __invControllerClass__ = invCtrl.StationCorpMember

    def ApplyAttributes(self, attributes):
        invCont._InvContBase.ApplyAttributes(self, attributes)
        sm.GetService('invCache').InvalidateLocationCache((const.containerHangar, self.invController.ownerID))

    def _GetInvController(self, attributes):
        return self.__invControllerClass__(itemID=attributes.itemID, ownerID=attributes.ownerID)

    def Refresh(self):
        sm.GetService('invCache').InvalidateLocationCache((const.containerHangar, self.invController.ownerID))
        invCont._InvContBase.Refresh(self)


class StationCorpHangar(invCont._InvContBase):
    __guid__ = 'invCont.StationCorpHangar'
    __invControllerClass__ = invCtrl.StationCorpHangar

    def _GetInvController(self, attributes):
        return self.__invControllerClass__(itemID=attributes.itemID, divisionID=attributes.divisionID)


class POSCorpHangar(invCont._InvContBase):
    __guid__ = 'invCont.POSCorpHangar'
    __invControllerClass__ = invCtrl.POSCorpHangar

    def _GetInvController(self, attributes):
        return self.__invControllerClass__(itemID=attributes.itemID, divisionID=attributes.divisionID)


class SpaceComponentInventory(_BaseCelestialContainer):
    """ An inventory part of a space component """
    __guid__ = 'invCont.SpaceComponentInventory'
    __invControllerClass__ = invCtrl.SpaceComponentInventory
