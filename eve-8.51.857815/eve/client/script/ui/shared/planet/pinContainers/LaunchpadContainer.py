#Embedded file name: eve/client/script/ui/shared/planet/pinContainers\LaunchpadContainer.py
"""
This file contains the pin container classes; the ones that appear when a pin on the
surface of a planet is clicked. All containers derive from the BasePinContainer class.
"""
import carbonui.const as uiconst
import uiprimitives
import util
import localization
from .BasePinContainer import BasePinContainer
from .StorageFacilityContainer import StorageFacilityContainer
from .. import planetCommon

class LaunchpadContainer(StorageFacilityContainer):
    __guid__ = 'planet.ui.LaunchpadContainer'
    default_name = 'LaunchpadContainer'

    def ApplyAttributes(self, attributes):
        BasePinContainer.ApplyAttributes(self, attributes)

    def _GetActionButtons(self):
        btns = [util.KeyVal(id=planetCommon.PANEL_LAUNCH, panelCallback=self.PanelLaunch), util.KeyVal(id=planetCommon.PANEL_STORAGE, panelCallback=self.PanelShowStorage)]
        btns.extend(BasePinContainer._GetActionButtons(self))
        return btns

    def PanelLaunch(self):
        """
        Launch some commodities into space!
        """
        bp = sm.GetService('michelle').GetBallpark()
        text = None
        if bp is not None and not self.pin.IsInEditMode():
            customsOfficeIDs = sm.GetService('planetInfo').GetOrbitalsForPlanet(sm.GetService('planetUI').planetID, const.groupPlanetaryCustomsOffices)
            if len(customsOfficeIDs) > 0:
                try:
                    customsOfficeID = None
                    for ID in customsOfficeIDs:
                        customsOfficeID = ID
                        break

                    sm.GetService('planetUI').OpenPlanetCustomsOfficeImportWindow(customsOfficeID, self.pin.id)
                    self.CloseByUser()
                    return
                except UserError as e:
                    if e.msg == 'ShipCloaked':
                        text = localization.GetByLabel('UI/PI/Common/CannotAccessLaunchpadWhileCloaked')
                    else:
                        message = cfg.GetMessage(e.msg)
                        text = message.text

        if text is None:
            if self.pin.IsInEditMode():
                text = localization.GetByLabel('UI/PI/Common/CustomsOfficeNotBuilt')
            else:
                solarSystemID = sm.GetService('planetUI').GetCurrentPlanet().solarSystemID
                if solarSystemID == session.locationid:
                    text = localization.GetByLabel('UI/PI/Common/CannotAccessLaunchpadNotThere')
                else:
                    text = localization.GetByLabel('UI/PI/Common/CannotAccessLaunchpadLocation')
        cont = uiprimitives.Container(parent=self.actionCont, pos=(0, 0, 0, 0), align=uiconst.TOTOP, state=uiconst.UI_HIDDEN)
        editBox = self._DrawEditBox(cont, text)
        cont.height = editBox.height + 4
        return cont
