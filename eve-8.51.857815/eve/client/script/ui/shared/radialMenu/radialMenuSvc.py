#Embedded file name: eve/client/script/ui/shared/radialMenu\radialMenuSvc.py
import uix
import util
import carbon.common.script.sys.service as service
import uthread
import carbonui.const as uiconst
import state
import uicls
import base
import geo2
from eve.client.script.ui.shared.radialMenu import spaceRadialMenuFunctions

class RadialMenuSvc(service.Service):
    """
        Provides menus for the client.
    """
    __guid__ = 'svc.radialmenu'

    def Run(self, memStream = None):
        self.expandTimer = None

    def TryExpandActionMenu(self, itemID, clickedObject, *args, **kwargs):
        if uicore.uilib.Key(uiconst.VK_MENU) or uicore.uilib.Key(uiconst.VK_CONTROL):
            return 0
        isRadialMenuButtonActive = spaceRadialMenuFunctions.IsRadialMenuButtonActive()
        if not isRadialMenuButtonActive:
            return 0
        x = uicore.uilib.x
        y = uicore.uilib.y
        expandTime = settings.user.ui.Get('actionMenuExpandTime', 150)
        if expandTime:
            combatCmdLoaded = uicore.cmd.combatCmdLoaded
            if combatCmdLoaded and combatCmdLoaded.name == 'CmdOpenRadialMenu':
                noDelay = True
            else:
                noDelay = False
        else:
            noDelay = True
        if noDelay:
            uthread.new(self._TryExpandActionMenu, itemID, x, y, clickedObject, **kwargs)
        else:
            self.expandTimer = base.AutoTimer(int(expandTime), self._TryExpandActionMenu, itemID, x, y, clickedObject, **kwargs)
        return 1

    def _TryExpandActionMenu(self, itemID, x, y, clickedObject, **kwargs):
        if getattr(clickedObject, 'isDragObject', False):
            if x != uicore.uilib.x or y != uicore.uilib.y:
                return
        self.expandTimer = None
        if clickedObject.destroyed:
            return
        v = geo2.Vector(uicore.uilib.x - x, uicore.uilib.y - y)
        if int(geo2.Vec2Length(v) > 12):
            return
        self.ExpandActionMenu(itemID, x, y, clickedObject, **kwargs)

    def ExpandActionMenu(self, itemID, x, y, clickedObject, **kwargs):
        if util.IsCharacter(itemID):
            kwargs['charID'] = itemID
            slimItem = util.SlimItemFromCharID(itemID)
            if slimItem:
                itemID = slimItem.itemID
        else:
            slimItem = uix.GetBallparkRecord(itemID)
        isRadialMenuButtonActive = spaceRadialMenuFunctions.IsRadialMenuButtonActive()
        if not isRadialMenuButtonActive:
            return
        uix.Flush(uicore.layer.menu)
        radialMenuClass = kwargs.get('radialMenuClass', uicls.RadialMenuSpace)
        radialMenu = radialMenuClass(name='radialMenu', parent=uicore.layer.menu, state=uiconst.UI_HIDDEN, align=uiconst.TOPLEFT, updateDisplayName=True, slimItem=slimItem, itemID=itemID, x=x, y=y, clickedObject=clickedObject, **kwargs)
        uicore.layer.menu.radialMenu = radialMenu
        uicore.uilib.SetMouseCapture(radialMenu)
        isRadialMenuButtonActive = spaceRadialMenuFunctions.IsRadialMenuButtonActive()
        if not isRadialMenuButtonActive:
            radialMenu.Close()
            return
        sm.StartService('state').SetState(itemID, state.mouseOver, 0)
        radialMenu.state = uiconst.UI_NORMAL

    def GetRadialMenuOwner(self):
        radialMenu = getattr(uicore.layer.menu, 'radialMenu', None)
        if radialMenu and not radialMenu.destroyed:
            radialMenuOwner = getattr(radialMenu, 'clickedObject', None)
            if radialMenuOwner and not radialMenuOwner.destroyed:
                return radialMenuOwner
