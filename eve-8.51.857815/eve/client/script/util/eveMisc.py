#Embedded file name: eve/client/script/util\eveMisc.py
import sys
import uthread
import carbonui.const as uiconst
import util

def LaunchFromShip(items, whoseBehalfID = None, ignoreWarning = False, maxQty = None):
    """
    Try and launch the given items from the player's ship into space.
    
    pre: items is a sequence of objects that have 
             - an itemID attribute, and
             - a quantity attribute (optional, defaults to 1).
             
         whoseBehalfID is the ownerID of the owner in behalf of whom the item
         is being launched (either the player's char or his corp, AFAIK.)
         
         If ignoreWarning is true, the server will not request player 
         confirmation on LaunchCPWarning conditions. I don't know what's that;
         grep for it in the server/script tree if you're interested. 
        
    post: If the server raises no UserErrors, some of given items are launched 
          from the ship. In (and only in) this case:
          
              - The number of items launched is limited by the player's skill 
                (or whatever game logic constraints apply). 
          
              - If some of the items couldn't be launched, the player will be 
                notified of the errors involved.  Note that these notifications 
                will *not* kill the current uthread!  
                
                If more than one notifications have identical arguments, only
                one of them will be displayed, and the rest will be ignored.               
                
                Since the notifications will be almost instantaneous, the 
                player will probably only see the last one in the notification
                area, but he can still check the others in the ingame logger. 
              
              An OnItemLaunch(ids) event will be scattered, where ids is a
              dictionary that maps each old itemID to a sequence containing 
              either
                  - nothing, if this particular item could not be launched,
                  - the id of the launched item (ie. it was a singleton), or
                  - the ids of any new items that have been created (ie. a 
                    stack was split into singleton(s) when some or all of its
                    .stacksize was launched).
              
          If the server raises LaunchCPWarning UserError, the player will be
          presented with the corresponding confirmation dialog. If he accepts, 
          the call will be retried with ignoreWarning set to True.
          
          If the server raises any other UserError, it is just re-raised here.
    """
    oldItems = []
    drones = False
    for item in items:
        if getattr(item, 'categoryID', 0) == const.categoryDrone:
            drones = True
        qty = getattr(item, 'quantity', 0)
        if qty < 0:
            oldItems.insert(0, (item.itemID, 1))
        elif qty > 0:
            if maxQty is not None:
                qty = min(qty, maxQty)
            oldItems.append((item.itemID, qty))

    try:
        if drones:
            ret = sm.StartService('gameui').GetShipAccess().LaunchDrones(oldItems, whoseBehalfID, ignoreWarning)
        else:
            ret = sm.StartService('gameui').GetShipAccess().Drop(oldItems, whoseBehalfID, ignoreWarning)
    except UserError as e:
        if e.msg in ('LaunchCPWarning', 'LaunchUpgradePlatformWarning'):
            reply = eve.Message(e.msg, e.dict, uiconst.YESNO)
            if reply == uiconst.ID_YES:
                LaunchFromShip(items, whoseBehalfID, ignoreWarning=True)
            sys.exc_clear()
            return
        raise e

    newIDs = {}
    errorByLabel = {}
    for itemID, seq in ret.iteritems():
        newIDs[itemID] = []
        for each in seq:
            if type(each) is tuple:
                errorByLabel[each[0]] = each
            else:
                newIDs[itemID].append(each)

    sm.ScatterEvent('OnItemLaunch', newIDs)

    def raise_(e):
        raise e

    for error in errorByLabel.itervalues():
        uthread.new(raise_, UserError(*error))


def IsItemOfRepairableType(item):
    """
        Returns if an item is repairable. Repairable items are:
            * Singletons
            * In a certain list of categories
             OR
            * Singletons
            * In a certain list of groups
            
        ARGUMENTS:
            item            An inventory item. Should be a wrapper object from
                            the inventory system, NOT an item ID.
    """
    return item.singleton and (item.categoryID in (const.categoryDeployable,
     const.categoryShip,
     const.categoryDrone,
     const.categoryStructure,
     const.categoryModule) or item.groupID in (const.groupCargoContainer,
     const.groupSecureCargoContainer,
     const.groupAuditLogSecureContainer,
     const.groupFreightContainer,
     const.groupTool))


def CSPAChargedActionForMany(message, obj, function, *args):
    try:
        func = getattr(obj, function)
        return func(*args)
    except UserError as e:
        if e.msg == 'ContactCostNotApprovedForMany':
            listOfMessage = e.dict['costNotApprovedFor']
            totalCost = 0
            totalApprovedCost = 0
            listingOutPlayers = []
            for each in listOfMessage:
                totalCost += each['totalCost']
                totalApprovedCost += each['approvedCost']
                charID = each['charID']
                listingOutPlayers.append('%s : %s' % (cfg.eveowners.Get(charID).name, util.FmtISK(each['totalCost'])))

            namelist = '<br>'.join(listingOutPlayers)
            if eve.Message(message, {'amountISK': util.FmtISK(totalCost),
             'namelist': namelist}, uiconst.YESNO) != uiconst.ID_YES:
                return None
            kwArgs = {'approvedCost': totalCost}
            return apply(getattr(obj, function), args, kwArgs)
        raise


def CSPAChargedAction(message, obj, function, *args):
    """
        Perform a CSPA charged action, ask for approval of charges if needed
    """
    try:
        return apply(getattr(obj, function), args)
    except UserError as e:
        if e.msg == 'ContactCostNotApproved':
            info = e.args[1]
            if eve.Message(message, {'amount': info['totalCost'],
             'amountISK': info['totalCostISK']}, uiconst.YESNO) != uiconst.ID_YES:
                return None
            kwArgs = {'approvedCost': info['totalCost']}
            return apply(getattr(obj, function), args, kwArgs)
        raise


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('util', globals())
