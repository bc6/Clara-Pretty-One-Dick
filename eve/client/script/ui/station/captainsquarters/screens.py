#Embedded file name: eve/client/script/ui/station/captainsquarters\screens.py
import blue
import trinity
import carbonui.const as uiconst
import uiutil

def UpdateCQMainScreen(width, height, desktop, entityID):
    """
    Update function for the main CQ Screen. This function will block until the slideshow has completed.
    """
    sm.GetService('holoscreen').OnMainScreenDesktopCreated(desktop, entityID)
    while True:
        blue.pyos.synchro.SleepWallclock(1000)


def UpdatePIScreen(width, height, desktop, entityID):
    """
    Update function for the planetary interation screen. This function will block until the slideshow has completed.
    """
    sm.GetService('holoscreen').OnPIScreenDesktopCreated(desktop, entityID)
    while True:
        blue.pyos.synchro.SleepWallclock(1000)


def UpdateCorpFinderScreen(width, height, desktop, entityID):
    """
    Update function for the corp finder screen. This function will block until the slideshow has completed.
    """
    sm.GetService('holoscreen').OnCorpFinderScreenDesktopCreated(desktop, entityID)
    while True:
        blue.pyos.synchro.SleepWallclock(1000)


def UpdateStationLogo(width, height, desktop, entityID):
    """
    
    """
    desktop.Flush()
    desktop.renderObject.backgroundColor = (0, 0, 0, 0)
    corpID = eve.stationItem.ownerID
    logo = uiutil.GetLogoIcon(itemID=corpID, parent=desktop, acceptNone=False, state=uiconst.UI_DISABLED, width=128, height=128, align=uiconst.CENTER)
    trinity.WaitForResourceLoads()
    desktop.UpdateAlignmentAsRoot()


def SetupCqMainScreen(paramString):
    """
    Dynamic resource constructor for Captain's Quarters main screen in scene.
    Center Screen
    """
    if uicore.isRunning:
        return trinity.TriTextureRes()
    else:
        return blue.resMan.GetResource('res:/Graphics/Shared_Texture/Global/Screen_Center_Fallback.dds')


def SetupCqAgentFinderScreen(paramString):
    """
    Dynamic resource constructor for Captain's Quarters agent finder screen in scene.
    Left Screen
    """
    if uicore.isRunning:
        return trinity.TriTextureRes()
    else:
        return blue.resMan.GetResource('res:/Graphics/Shared_Texture/Global/Screen_Left_Fallback.dds')


def SetupCqPIScreen(paramString):
    """
    Dynamic resource constructor for Captain's Quarters planetary interaction screen in scene.
    Right Screen
    """
    if uicore.isRunning:
        return trinity.TriTextureRes()
    else:
        return blue.resMan.GetResource('res:/Graphics/Shared_Texture/Global/Screen_Right_Fallback.dds')


def SetupCqStationLogo(paramString):
    """
    Resource constructor for the station name decal object.
    """
    if uicore.isRunning:
        return trinity.TriTextureRes()
    else:
        return blue.resMan.GetResource('res:/UI/Texture/Corps/1_128_1.png')


LIVE_UPDATES = True
STATIC_IMAGE = False
AUTO_MIPMAP = True
NO_MIPMAPS = False
ARGB_FORMAT = trinity.PIXEL_FORMAT.B8G8R8A8_UNORM
XRGB_FORMAT = trinity.PIXEL_FORMAT.B8G8R8X8_UNORM
if blue.win32.IsTransgaming():
    AUTO_MIPMAP = False
CqMainScreen = (1408,
 792,
 XRGB_FORMAT,
 LIVE_UPDATES,
 AUTO_MIPMAP,
 UpdateCQMainScreen)
CqStationLogo = (128,
 128,
 ARGB_FORMAT,
 STATIC_IMAGE,
 AUTO_MIPMAP,
 UpdateStationLogo)
CqPIScreen = (594,
 792,
 XRGB_FORMAT,
 LIVE_UPDATES,
 AUTO_MIPMAP,
 UpdatePIScreen)
CqCorpFinderScreen = (594,
 792,
 XRGB_FORMAT,
 LIVE_UPDATES,
 AUTO_MIPMAP,
 UpdateCorpFinderScreen)
cqmainscreen = CqMainScreen
cqpiscreen = CqPIScreen
cqagentfinderscreen = CqCorpFinderScreen
stationlogo = CqStationLogo
exports = {'screens.cqmainscreen': cqmainscreen,
 'screens.cqpiscreen': cqpiscreen,
 'screens.cqagentfinderscreen': cqagentfinderscreen,
 'screens.stationlogo': stationlogo}
