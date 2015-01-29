#Embedded file name: eve/client/script/ui/inflight\radialMenuScanner.py
import blue
from eve.client.script.ui.shared.radialMenu.radialMenuUtils import SimpleRadialMenuAction, RadialMenuOptionsInfo
from eve.client.script.ui.inflight.radialMenuShipUI import RadialMenuShipUI

def OpenProbeScanner():
    from eve.client.script.ui.inflight.scanner import Scanner
    wnd = Scanner.Open()


def OpenDirectionalScanner():
    from eve.client.script.ui.inflight.scannerFiles.directionalScanner import DirectionalScanner
    DirectionalScanner.Open()


def OpenMoonScanner():
    from eve.client.script.ui.inflight.scannerFiles.moonScanner import MoonScanner
    MoonScanner.Open()


class RadialMenuScanner(RadialMenuShipUI):

    def ApplyAttributes(self, attributes):
        RadialMenuShipUI.ApplyAttributes(self, attributes)

    def GetMyActions(self, *args):
        """
            returns either None (if something failed) or a KeyVal with the menu option info for the
            The menu option info consists of:
                allWantedMenuOptions =  a list of all options we that should be in the radial menu
                activeSingleOptions =   a dictionary with all the avaible clickable options. The key is the labelpath and the value is
                                        the menu option keyval which contains the callback and arguments among other things
                inactiveSingleOptions = a set of menu options(labelpath) that we want in our radial menu but are not available (and are therefore greyed out)
                activeRangeOptions =    a dictionary with all the available range options. The key is the labelpath and the value is
                                         the menu option keyval which contains the callback, rangeOptions and default distance among other things
                inactiveRangeOptions =  a set with all the range options(labelpath) we want, but are not available
        
        
        SimpleRadialMenuAction in activeSingleOptions need to have at least "option1" textpath, and a function it should call.
        (for the RadialMenuSpace class, this is built from the info from the menu service, and the func depends on which 
        option is available. For simple case, just give the function you want to use.
        ) 
        
        """
        iconOffset = 1
        allWantedMenuOptions = [SimpleRadialMenuAction(option1='UI/Inflight/Scanner/MoonAnalysis', func=OpenMoonScanner, iconPath='res:/UI/Texture/Icons/moonscan.png', iconOffset=iconOffset),
         SimpleRadialMenuAction(option1='UI/Inflight/Scanner/DirectionalScan', func=OpenDirectionalScanner, iconPath='res:/UI/Texture/Icons/d-scan.png', iconOffset=iconOffset, commandName='OpenDirectionalScanner'),
         SimpleRadialMenuAction(option1='', func=None, iconPath='', iconOffset=iconOffset),
         SimpleRadialMenuAction(option1='UI/Inflight/Scanner/ProbeScanner', func=OpenProbeScanner, iconPath='res:/UI/Texture/Icons/probe_scan.png', iconOffset=iconOffset, commandName='OpenScanner')]
        activeSingleOptions = {menuAction.option1Path:menuAction for menuAction in allWantedMenuOptions if menuAction.option1Path}
        optionsInfo = RadialMenuOptionsInfo(allWantedMenuOptions=allWantedMenuOptions, activeSingleOptions=activeSingleOptions)
        return optionsInfo
