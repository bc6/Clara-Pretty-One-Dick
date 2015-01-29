#Embedded file name: spacecomponents/client/components\behavior.py
from spacecomponents.common.componentConst import BEHAVIOR
from spacecomponents.common.components.component import Component
import logging
logger = logging.getLogger(__name__)

class Behavior(Component):
    pass


def GetComponent(itemId):
    bp = sm.GetService('michelle').GetBallpark()
    component = bp.componentRegistry.GetComponentForItem(itemId, BEHAVIOR)
    return component


def EnableDebugging(itemID):
    logger.warning('Enabling debug for item %s', itemID)
    try:
        from eve.devtools.script.behaviortools.clientdebugadaptors import updateListener
        updateListener.TryConnectDebugger(itemID)
    except:
        logger.exception('Unable to load the Client Behavior Debugger module')


def DisableDebugging(itemID):
    try:
        from eve.devtools.script.behaviortools.clientdebugadaptors import updateListener
        updateListener.TryDisconnectDebugger(itemID)
    except:
        logger.exception('Unable to disconnect Client Behavior Debugger module')


def GetBehaviorGMMenu(slimItem):
    itemID = slimItem.itemID
    menu = []
    try:
        from eve.devtools.script.behaviortools.clientdebugadaptors import updateListener
        menu.append(None)
        if not updateListener.HasDebugger(itemID):
            menu.append(('Enable Behavior Debugger', EnableDebugging, [itemID]))
        else:
            menu.append(('Disable Behavior Debugger', DisableDebugging, [itemID]))
    except:
        pass

    return menu
