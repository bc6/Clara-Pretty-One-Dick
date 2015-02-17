#Embedded file name: eve/client/script/ui/inflight\radialMenuCamera.py
import uicontrols
import carbonui.const as uiconst
import uicls
from eve.client.script.ui.shared.radialMenu.radialMenuUtils import SimpleRadialMenuAction, RadialMenuOptionsInfo
from eve.client.script.ui.inflight.radialMenuShipUI import RadialMenuShipUI

class RadialMenuCamera(RadialMenuShipUI):
    __guid__ = 'uicls.RadialMenuCamera'

    def GetMyActions(self, *args):
        iconOffset = 1
        allWantedMenuOptions = []
        if sm.GetService('targetTrackingService').GetActiveTrackingState() is not False:
            allWantedMenuOptions.append(SimpleRadialMenuAction(option1='UI/Inflight/Camera/TurnTrackingOff', func=self.DisableTracking, iconPath='res:/UI/Texture/classes/CameraRadialMenu/trackingOff_ButtonIcon.png', commandName='CmdToggleTrackSelectedItem'))
        else:
            allWantedMenuOptions.append(SimpleRadialMenuAction(option1='UI/Inflight/Camera/TurnTrackingOn', func=self.EnableTracking, iconPath='res:/UI/Texture/classes/CameraRadialMenu/trackingOn_ButtonIcon.png', iconOffset=iconOffset, commandName='CmdToggleTrackSelectedItem'))
        allWantedMenuOptions.extend([SimpleRadialMenuAction(option1='UI/Inflight/Camera/CustomTrackingPosition', func=self.UseCustomPosition, iconPath='res:/UI/Texture/classes/CameraRadialMenu/customTracking_ButtonIcon.png', iconOffset=iconOffset, commandName='CmdTrackingCameraCustomPosition')])
        allWantedMenuOptions.append(SimpleRadialMenuAction(option1='UI/Inflight/Camera/ResetCamera', func=self.ResetCamera, iconPath='res:/UI/Texture/classes/CameraRadialMenu/resetCamera_ButtonIcon.png', iconOffset=iconOffset))
        allWantedMenuOptions.append(SimpleRadialMenuAction(option1='UI/Inflight/Camera/CenterOnscreenPosition', func=self.UseCenterPosition, iconPath='res:/UI/Texture/classes/CameraRadialMenu/centerTracking_ButtonIcon.png', iconOffset=iconOffset, commandName='CmdTrackingCameraCenterPosition'))
        activeSingleOptions = {menuAction.option1Path:menuAction for menuAction in allWantedMenuOptions}
        optionsInfo = RadialMenuOptionsInfo(allWantedMenuOptions=allWantedMenuOptions, activeSingleOptions=activeSingleOptions)
        return optionsInfo

    def UseCustomPosition(self):
        sm.GetService('targetTrackingService').SetCenteredTrackingState(False)
        self.EnableTracking()

    def UseCenterPosition(self):
        sm.GetService('targetTrackingService').SetCenteredTrackingState(True)
        self.EnableTracking()

    def ResetCamera(self):
        sm.GetService('camera').ResetCamera()

    def EnableTracking(self):
        sm.GetService('targetTrackingService').EnableTrackingCamera()

    def DisableTracking(self):
        sm.GetService('targetTrackingService').DisableTrackingCamera()
