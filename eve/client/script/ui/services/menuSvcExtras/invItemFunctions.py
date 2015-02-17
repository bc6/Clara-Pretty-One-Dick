#Embedded file name: eve/client/script/ui/services/menuSvcExtras\invItemFunctions.py
from collections import defaultdict
from inventorycommon.util import IsModularShip, IsShipFittingFlag
import uicontrols
import util
import blue
import form
import destiny
import carbonui.const as uiconst
import const
import uix
import localization
import dbutil
from eveexceptions import UserError

def LaunchSMAContents(invItem):
    bp = sm.GetService('michelle').GetBallpark()
    myShipBall = bp.GetBall(session.shipid)
    if myShipBall and myShipBall.mode == destiny.DSTBALL_WARP:
        raise UserError('ShipInWarp')
    sm.GetService('gameui').GetShipAccess().LaunchFromContainer(invItem.locationID, invItem.itemID)


def Jettison(invItems):
    if eve.Message('ConfirmJettison', {}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
        return
    ids = []
    for invItem in invItems:
        ids += [invItem.itemID]

    ship = sm.StartService('gameui').GetShipAccess()
    if ship:
        ship.Jettison(ids)


def Refine(invItems):
    if not session.stationid:
        return
    sm.StartService('reprocessing').ReprocessDlg(invItems)


def RefineToHangar(invItems):
    if not session.stationid:
        return
    sm.StartService('reprocessing').ReprocessDlg(invItems)


def TrainNow(invItems):
    if len(invItems) > 1:
        eve.Message('TrainMoreTheOne')
        return
    InjectSkillIntoBrain(invItems)
    blue.pyos.synchro.SleepWallclock(500)
    sm.GetService('skillqueue').TrainSkillNow(invItems[0].typeID, 1)


def InjectSkillIntoBrain(invItems):
    sm.StartService('skills').InjectSkillIntoBrain(invItems)


def PlugInImplant(invItems):
    if eve.Message('ConfirmPlugInImplant', {}, uiconst.OKCANCEL) != uiconst.ID_OK:
        return
    for invItem in invItems:
        sm.StartService('godma').GetSkillHandler().CharAddImplant(invItem.itemID)


def ConsumeBooster(invItems):
    if type(invItems) is not list:
        invItems = [invItems]
    for invItem in invItems:
        sm.StartService('godma').GetSkillHandler().CharUseBooster(invItem.itemID, invItem.locationID)


def AssembleShip(invItems):
    """
        We loop over the ships and create a list of itemIDs which we send to server to singletonize. On the first item that is a tech3
        ship we open up the modular assembly window and return, that is not singletonizing any other ship that was in the list.
    """
    itemIDs = []
    for item in invItems:
        invItem = invItems[0]
        if IsModularShip(invItem.typeID):
            if session.stationid is None:
                eve.Message('CantAssembleModularShipInSpace')
                return
            wndName = 'assembleWindow_%s' % item.itemID
            wnd = form.AssembleShip.GetIfOpen(windowID=wndName)
            if wnd is None:
                wnd = form.AssembleShip.Open(windowID=wndName, ship=invItem)
            else:
                wnd.Maximize()
            return
        itemIDs.append(item.itemID)

    sm.StartService('gameui').GetShipAccess().AssembleShip(itemIDs)


def RigFittingCheck(invItem):
    moduleEffects = cfg.dgmtypeeffects.get(invItem.typeID, [])
    for mEff in moduleEffects:
        if mEff.effectID == const.effectRigSlot:
            if eve.Message('RigFittingInfo', {}, uiconst.OKCANCEL) != uiconst.ID_OK:
                return 0

    return 1


def CheckItemsInSamePlace(invItems):
    if len(invItems) == 0:
        return
    locationID = invItems[0].locationID
    flag = invItems[0].flagID
    ownerID = invItems[0].ownerID
    for item in invItems:
        if item.locationID != locationID or item.flagID != flag or item.ownerID != ownerID:
            raise UserError('ItemsMustBeInSameHangar')
        locationID = item.locationID
        ownerID = item.ownerID
        flag = item.flagID


def CheckIfLockableBlueprint(invItem):
    isLockable = False
    if invItem.categoryID == const.categoryBlueprint and invItem.singleton and invItem.ownerID == session.corpid:
        if session.corprole & const.corpRoleDirector == const.corpRoleDirector:
            if invItem.flagID in [const.flagHangar] + list(const.flagCorpSAGs):
                rows = sm.StartService('corp').GetMyCorporationsOffices().SelectByUniqueColumnValues('officeID', [invItem.locationID])
                if rows and len(rows) and rows[0].officeID == invItem.locationID:
                    if not sm.GetService('corp').IsItemLocked(invItem):
                        isLockable = True
    return bool(isLockable)


def CheckIfUnlockableBlueprint(invItem):
    isUnlockable = False
    if invItem.categoryID == const.categoryBlueprint and invItem.singleton and invItem.ownerID == session.corpid:
        if session.corprole & const.corpRoleDirector == const.corpRoleDirector:
            if invItem.flagID in [const.flagHangar] + list(const.flagCorpSAGs):
                rows = sm.StartService('corp').GetMyCorporationsOffices().SelectByUniqueColumnValues('officeID', [invItem.locationID])
                if rows and len(rows) and rows[0].officeID == invItem.locationID:
                    if sm.GetService('corp').IsItemLocked(invItem):
                        isUnlockable = True
    return bool(isUnlockable)


def CheckIfInHangarOrCorpHangarAndCanTake(invItem):
    canTake = False
    corpMember = False
    stationID = None
    bp = sm.StartService('michelle').GetBallpark()
    if invItem.ownerID == session.charid:
        if util.IsStation(invItem.locationID) and invItem.flagID == const.flagHangar:
            canTake = True
        elif bp is not None and invItem.flagID == const.flagHangar and invItem.locationID in bp.slimItems and bp.slimItems[invItem.locationID].groupID == const.groupPersonalHangar:
            canTake = True
    elif session.solarsystemid and bp is not None and invItem.locationID in bp.slimItems and invItem.ownerID == bp.slimItems[invItem.locationID].ownerID:
        corpMember = True
    elif invItem.ownerID == session.corpid and not util.IsNPC(invItem.ownerID):
        stationID = None
        rows = sm.StartService('corp').GetMyCorporationsOffices().SelectByUniqueColumnValues('officeID', [invItem.locationID])
        if rows and len(rows):
            for row in rows:
                if invItem.locationID == row.officeID:
                    stationID = row.stationID
                    break

    if stationID is not None or corpMember:
        flags = [const.flagHangar] + list(const.flagCorpSAGs)
        if invItem.flagID in flags:
            if stationID is not None and stationID == session.hqID:
                roles = session.rolesAtHQ
            elif stationID is not None and stationID == session.baseID:
                roles = session.rolesAtBase
            else:
                roles = session.rolesAtOther
            if invItem.ownerID == session.corpid or corpMember:
                rolesByFlag = {const.flagHangar: const.corpRoleHangarCanTake1,
                 const.flagCorpSAG2: const.corpRoleHangarCanTake2,
                 const.flagCorpSAG3: const.corpRoleHangarCanTake3,
                 const.flagCorpSAG4: const.corpRoleHangarCanTake4,
                 const.flagCorpSAG5: const.corpRoleHangarCanTake5,
                 const.flagCorpSAG6: const.corpRoleHangarCanTake6,
                 const.flagCorpSAG7: const.corpRoleHangarCanTake7}
                roleRequired = rolesByFlag[invItem.flagID]
                if roleRequired & roles == roleRequired:
                    canTake = True
    return bool(canTake)


def CheckSameStation(invItem):
    inSameLocation = 0
    if session.stationid2:
        if invItem.locationID == session.stationid2:
            inSameLocation = 1
        elif util.IsPlayerItem(invItem.locationID):
            if 'stationID' in invItem.__columns__:
                if invItem.stationID == session.stationid2:
                    inSameLocation = 1
            else:
                inSameLocation = 1
        else:
            office = sm.StartService('corp').GetOffice_NoWireTrip()
            if office is not None:
                if invItem.locationID == office.itemID:
                    inSameLocation = 1
    return inSameLocation


def CheckSameLocation(invItem):
    inSameLocation = 0
    if session.stationid:
        if invItem.locationID == session.stationid:
            inSameLocation = 1
        elif util.IsPlayerItem(invItem.locationID):
            inSameLocation = 1
        else:
            office = sm.StartService('corp').GetOffice_NoWireTrip()
            if office is not None:
                if invItem.locationID == office.itemID:
                    inSameLocation = 1
    if invItem.locationID == session.shipid and invItem.flagID != const.flagShipHangar:
        inSameLocation = 1
    elif session.solarsystemid and invItem.locationID == session.solarsystemid:
        inSameLocation = 1
    return inSameLocation


def InvalidateItemLocation(ownerID, stationID, flag, invCacheSvc):
    if ownerID == session.corpid:
        which = 'offices'
        if flag == const.flagCorpMarket:
            which = 'deliveries'
        sm.services['objectCaching'].InvalidateCachedMethodCall('corpmgr', 'GetAssetInventoryForLocation', session.corpid, stationID, which)
    else:
        sm.services['objectCaching'].InvalidateCachedMethodCall('stationSvc', 'GetStation', stationID)
        invCacheSvc.GetInventory(const.containerGlobal).InvalidateStationItemsCache(stationID)


def DeliverToCorpHangarFolder(invItemAndFlagList, invCacheSvc):
    if len(invItemAndFlagList) == 0:
        return
    invItems = []
    itemIDs = []
    for item in invItemAndFlagList:
        invItems.append(item[0])
        itemIDs.append(item[0].itemID)

    CheckItemsInSamePlace(invItems)
    fromID = invItems[0].locationID
    doSplit = bool(uicore.uilib.Key(uiconst.VK_SHIFT) and len(invItemAndFlagList) == 1 and invItemAndFlagList[0][0].stacksize > 1)
    stationID = invCacheSvc.GetStationIDOfItem(invItems[0])
    if stationID is None:
        raise UserError('CanOnlyDoInStations')
    ownerID = invItems[0].ownerID
    flag = invItems[0].flagID
    deliverToFlag = invItemAndFlagList[0][1]
    qty = None
    if doSplit:
        invItem = invItems[0]
        ret = uix.QtyPopup(invItem.stacksize, 1, 1, None, localization.GetByLabel('UI/Inventory/ItemActions/DivideItemStack'))
        if ret is not None:
            qty = ret['qty']
    invCacheSvc.GetInventoryMgr().DeliverToCorpHangar(fromID, stationID, itemIDs, qty, ownerID, deliverToFlag)
    InvalidateItemLocation(ownerID, stationID, flag, invCacheSvc)
    if ownerID == session.corpid:
        sm.ScatterEvent('OnCorpAssetChange', invItems, stationID)


def DeliverToCorpMember(invItems, invCacheSvc):
    if len(invItems) == 0:
        return
    CheckItemsInSamePlace(invItems)
    corpMemberIDs = sm.GetService('corp').GetMemberIDs()
    cfg.eveowners.Prime(corpMemberIDs)
    memberslist = []
    for memberID in corpMemberIDs:
        if util.IsDustCharacter(memberID):
            continue
        who = cfg.eveowners.Get(memberID)
        memberslist.append([who.ownerName, memberID, who.typeID])

    doSplit = uicore.uilib.Key(uiconst.VK_SHIFT) and len(invItems) == 1 and invItems[0].stacksize > 1
    stationID = invCacheSvc.GetStationIDOfItem(invItems[0])
    if stationID is None:
        raise UserError('CanOnlyDoInStations')
    ownerID = invItems[0].ownerID
    flagID = invItems[0].flagID
    itemIDs = [ item.itemID for item in invItems ]
    res = uix.ListWnd(memberslist, 'character', localization.GetByLabel('UI/Corporations/Common/SelectCorpMember'), localization.GetByLabel('UI/Corporations/Common/SelectCorpMemberToDeliverTo'), 1)
    if res:
        corporationMemberID = res[1]
        qty = None
        if doSplit:
            invItem = invItems[0]
            ret = uix.QtyPopup(invItem.stacksize, 1, 1, None, localization.GetByLabel('UI/Inventory/ItemActions/DivideItemStack'))
            if ret is not None:
                qty = ret['qty']
        invCacheSvc.GetInventoryMgr().DeliverToCorpMember(corporationMemberID, stationID, itemIDs, qty, ownerID, flagID)
        InvalidateItemLocation(ownerID, stationID, flagID, invCacheSvc)
        if ownerID == session.corpid:
            sm.ScatterEvent('OnCorpAssetChange', invItems, stationID)


def SplitStack(invItems, invCacheSvc):
    if len(invItems) != 1:
        raise UserError('CannotPerformOnMultipleItems')
    invItem = invItems[0]
    ret = uix.QtyPopup(invItem.stacksize, 1, 1, None, localization.GetByLabel('UI/Inventory/ItemActions/DivideItemStack'))
    if ret is not None:
        qty = ret['qty']
        stationID = invCacheSvc.GetStationIDOfItem(invItem)
        if stationID is None:
            raise UserError('CanOnlyDoInStations')
        flag = invItem.flagID
        invCacheSvc.GetInventoryMgr().SplitStack(stationID, invItem.itemID, qty, invItem.ownerID)
        InvalidateItemLocation(invItem.ownerID, stationID, flag, invCacheSvc)
        if invItem.ownerID == session.corpid:
            invItem.quantity = invItem.quantity - qty
            sm.ScatterEvent('OnCorpAssetChange', [invItem], stationID)


def LockDownBlueprint(invItem, invCacheSvc):
    dlg = form.VoteWizardDialog.Open()
    stationID = invCacheSvc.GetStationIDOfItem(invItem)
    blueprints = invCacheSvc.GetInventory(const.containerGlobal).ListStationBlueprintItems(invItem.locationID, stationID, True)
    description = None
    for blueprint in blueprints:
        if blueprint.itemID != invItem.itemID:
            continue
        description = localization.GetByLabel('UI/Corporations/Votes/ProposeLockdownDescription', blueprintLocation=stationID, efficiencyLevel=blueprint.materialLevel, productivityLevel=blueprint.productivityLevel)
        break

    dlg.voteType = const.voteItemLockdown
    dlg.voteTitle = localization.GetByLabel('UI/Corporations/Votes/LockdownItem', blueprint=invItem.typeID)
    dlg.voteDescription = description or dlg.voteTitle
    dlg.voteDays = 1
    dlg.itemID = invItem.itemID
    dlg.typeID = invItem.typeID
    dlg.flagInput = invItem.flagID
    dlg.locationID = stationID
    dlg.GoToStep(len(dlg.steps))
    dlg.ShowModal()


def UnlockBlueprint(invItem, invCacheSvc):
    voteCases = sm.GetService('corp').GetVoteCasesByCorporation(session.corpid, 2)
    voteCaseIDByItemToUnlockID = {}
    if voteCases and len(voteCases):
        for voteCase in voteCases.itervalues():
            if voteCase.voteType in [const.voteItemUnlock] and voteCase.endDateTime > blue.os.GetWallclockTime() - const.DAY:
                options = sm.GetService('corp').GetVoteCaseOptions(voteCase.voteCaseID, voteCase.corporationID)
                if len(options):
                    for option in options.itervalues():
                        if option.parameter:
                            voteCaseIDByItemToUnlockID[option.parameter] = voteCase.voteCaseID

    if invItem.itemID in voteCaseIDByItemToUnlockID:
        raise UserError('CustomInfo', {'info': localization.GetByLabel('UI/Corporations/Common/UnlockCorpVoteAlreadyExists')})
    sanctionedActionsInEffect = sm.GetService('corp').GetSanctionedActionsByCorporation(session.corpid, 1)
    sanctionedActionsByLockedItemID = dbutil.CIndexedRowset(sanctionedActionsInEffect.header, 'parameter')
    for sanctionedActionInEffect in sanctionedActionsInEffect.itervalues():
        if sanctionedActionInEffect.voteType in [const.voteItemLockdown] and sanctionedActionInEffect.parameter and sanctionedActionInEffect.inEffect:
            sanctionedActionsByLockedItemID[sanctionedActionInEffect.parameter] = sanctionedActionInEffect

    if invItem.itemID not in sanctionedActionsByLockedItemID:
        raise UserError('CustomInfo', {'info': localization.GetByLabel('UI/Corporations/Common/CannotUnlockNoLockdownSanctionedAction')})
    dlg = form.VoteWizardDialog.Open()
    stationID = invCacheSvc.GetStationIDOfItem(invItem)
    blueprints = invCacheSvc.GetInventory(const.containerGlobal).ListStationBlueprintItems(invItem.locationID, stationID, True)
    description = None
    for blueprint in blueprints:
        if blueprint.itemID != invItem.itemID:
            continue
        description = localization.GetByLabel('UI/Corporations/Votes/ProposeLockdownDescription', blueprintLocation=stationID, efficiencyLevel=blueprint.materialLevel, productivityLevel=blueprint.productivityLevel)
        break

    dlg.voteType = const.voteItemUnlock
    dlg.voteTitle = localization.GetByLabel('UI/Corporations/Votes/UnlockItem', blueprint=invItem.typeID)
    dlg.voteDescription = description or dlg.voteTitle
    dlg.voteDays = 1
    dlg.itemID = invItem.itemID
    dlg.typeID = invItem.typeID
    dlg.flagInput = invItem.flagID
    dlg.locationID = stationID
    dlg.GoToStep(len(dlg.steps))
    dlg.ShowModal()


def ALSCLock(invItems, invCacheSvc):
    if len(invItems) < 1:
        return
    container = invCacheSvc.GetInventoryFromId(invItems[0].locationID)
    container.ALSCLockItems([ i.itemID for i in invItems ])


def ALSCUnlock(invItems, invCacheSvc):
    if len(invItems) < 1:
        return
    container = invCacheSvc.GetInventoryFromId(invItems[0].locationID)
    container.ALSCUnlockItems([ i.itemID for i in invItems ])


def GetContainerContents(invItem, invCacheSvc):
    hasFlag = invItem.categoryID == const.categoryShip
    name = cfg.invtypes.Get(invItem.typeID).name
    stationID = invCacheSvc.GetStationIDOfItem(invItem)
    DoGetContainerContents(invItem.itemID, stationID, hasFlag, name, invCacheSvc)


def DoGetContainerContents(itemID, stationID, hasFlag, name, invCacheSvc):
    contents = invCacheSvc.GetInventoryMgr().GetContainerContents(itemID, stationID)
    lst = []
    for c in contents:
        flag = c.flagID
        if flag == const.flagPilot:
            continue
        locationName = util.GetShipFlagLocationName(flag)
        t = cfg.invtypes.Get(c.typeID)
        if hasFlag:
            txt = '%s<t>%s<t>%s<t>%s' % (t.name,
             cfg.invgroups.Get(t.groupID).name,
             locationName,
             c.stacksize)
        else:
            txt = '%s<t>%s<t>%s' % (t.name, cfg.invgroups.Get(t.groupID).name, c.stacksize)
        lst.append([txt, c.itemID, c.typeID])

    if hasFlag:
        hdr = [localization.GetByLabel('UI/Inventory/InvItemNameShort'),
         localization.GetByLabel('UI/Inventory/ItemGroup'),
         localization.GetByLabel('UI/Common/Location'),
         localization.GetByLabel('UI/Common/Quantity')]
    else:
        hdr = [localization.GetByLabel('UI/Inventory/InvItemNameShort'), localization.GetByLabel('UI/Inventory/ItemGroup'), localization.GetByLabel('UI/Common/Quantity')]
    hint1 = localization.GetByLabel('UI/Menusvc/ItemsInContainerHint')
    hint2 = localization.GetByLabel('UI/Menusvc/ItemsInContainerHint2', containerName=name)
    uix.ListWnd(lst, 'item', hint1, hint=hint2, isModal=0, minChoices=0, scrollHeaders=hdr, minw=500, windowName='containerContents')


def CheckLocked(func, invItemsOrIDs, invCacheSvc):
    if not len(invItemsOrIDs):
        return
    if type(invItemsOrIDs[0]) == int or not hasattr(invItemsOrIDs[0], 'itemID'):
        ret = func(invItemsOrIDs)
    else:
        lockedItems = []
        try:
            for item in invItemsOrIDs:
                if invCacheSvc.IsItemLocked(item.itemID):
                    continue
                if invCacheSvc.TryLockItem(item.itemID):
                    lockedItems.append(item)

            if not len(lockedItems):
                eve.Message('BusyItems')
                return
            ret = func(lockedItems)
        finally:
            for invItem in lockedItems:
                invCacheSvc.UnlockItem(invItem.itemID)

    return ret


def RepackageItemsInStation(invItems, invCacheSvc):
    if eve.Message('ConfirmRepackageItem', {}, uiconst.YESNO) != uiconst.ID_YES:
        return
    validIDsByStationID = defaultdict(list)
    insuranceQ_OK = 0
    insuranceContracts = None
    checksToSkip = set()
    godma = sm.GetService('godma')
    for invItem in invItems:
        skipThis = False
        itemState = godma.GetItem(invItem.itemID)
        if itemState and (itemState.damage or invItem.categoryID in (const.categoryShip, const.categoryDrone) and itemState.armorDamage):
            eve.Message('CantRepackageDamagedItem')
            continue
        if invItem.categoryID == const.categoryShip:
            if insuranceContracts is None:
                insuranceContracts = sm.StartService('insurance').GetContracts()
            if not insuranceQ_OK and invItem.itemID in insuranceContracts:
                if eve.Message('RepairUnassembleVoidsContract', {}, uiconst.YESNO) != uiconst.ID_YES:
                    continue
                insuranceQ_OK = 1
            if invCacheSvc.IsInventoryPrimedAndListed(invItem.itemID):
                inv = invCacheSvc.GetInventoryFromId(invItem.itemID)
                dogmaStaticMgr = sm.GetService('clientDogmaStaticSvc')
                for item in [ i for i in inv.List() if IsShipFittingFlag(i.flagID) ]:
                    if dogmaStaticMgr.TypeHasEffect(item.typeID, const.effectRigSlot):
                        if eve.Message('ConfirmRepackageSomethingWithUpgrades', {'what': (const.UE_LOCID, invItem.itemID)}, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
                            checksToSkip.add('ConfirmRepackageSomethingWithUpgrades')
                        else:
                            skipThis = True
                            break

                if skipThis:
                    continue
        stationID = invCacheSvc.GetStationIDOfItem(invItem)
        if stationID is not None:
            validIDsByStationID[stationID].append((invItem.itemID, invItem.locationID))

    if len(validIDsByStationID) == 0:
        return
    try:
        sm.RemoteSvc('repairSvc').DisassembleItems(dict(validIDsByStationID), list(checksToSkip))
    except UserError as e:
        if cfg.messages[e.msg].dialogType == 'question' and eve.Message(e.msg, e.dict, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            checksToSkip.add(e.msg)
            return sm.RemoteSvc('repairSvc').DisassembleItems(dict(validIDsByStationID), list(checksToSkip))
        raise


def Break(invItems, invCacheSvc):
    ok = 0
    validIDs = []
    for invItem in invItems:
        if ok or eve.Message('ConfirmBreakCourierPackage', {}, uiconst.OKCANCEL) == uiconst.ID_OK:
            validIDs.append(invItem.itemID)
            ok = 1

    for itemID in validIDs:
        invCacheSvc.GetInventoryFromId(itemID).BreakPlasticWrap()


def CompressItem(item, locationItem, invCacheSvc):
    minQuantity = sm.GetService('godma').GetTypeAttribute(item.typeID, const.attributeCompressionQuantityNeeded)
    if minQuantity < 1:
        raise RuntimeError('Dogma attribute compressionQuantityNeeded not found or invalid')
    if item.stacksize < minQuantity:
        messageParams = {'typeName': cfg.invtypes.Get(item.typeID).typeName,
         'size': int(minQuantity)}
        eve.Message('SizeInvalidForCompression', messageParams)
        return
    if locationItem.groupID == const.groupCapitalIndustrialShip:
        invCacheSvc.GetInventoryMgr().CompressItem(item.itemID)
    elif locationItem.groupID == const.groupCompressionArray:
        invCacheSvc.GetInventoryFromId(item.locationID).CompressItem(item.itemID)
    else:
        raise RuntimeError('Invalid location to compress in')
    if item.ownerID == session.corpid:
        ownerID = session.corpid
    else:
        ownerID = session.charid
    InvalidateItemLocation(ownerID, item.locationID, item.flagID, invCacheSvc)
    if item.ownerID == session.corpid:
        sm.ScatterEvent('OnCorpAssetChange', item, item.locationID)


def TrashInvItems(invItems, invCacheSvc):
    if len(invItems) == 0:
        return
    CheckItemsInSamePlace(invItems)
    if len(invItems) == 1:
        question = 'ConfirmTrashingSin'
        itemWithQuantity = cfg.FormatConvert(const.UE_TYPEIDANDQUANTITY, invItems[0].typeID, invItems[0].stacksize)
        args = {'itemWithQuantity': itemWithQuantity}
    else:
        question = 'ConfirmTrashingPlu'
        report = ''
        for item in invItems:
            report += '<t>- %s<br>' % cfg.FormatConvert(const.UE_TYPEIDANDQUANTITY, item.typeID, item.stacksize)

        args = {'items': report}
    if eve.Message(question, args, uiconst.YESNO) != uiconst.ID_YES:
        return
    stationID = invCacheSvc.GetStationIDOfItem(invItems[0])
    windows = ['sma',
     'corpHangar',
     'drones',
     'shipCargo']
    for item in invItems:
        if hasattr(item, 'categoryID'):
            isShip = item.categoryID == const.categoryShip
        else:
            isShip = cfg.invtypes.Get(item.typeID).categoryID == const.categoryShip
        if isShip:
            for window in windows:
                uicontrols.Window.CloseIfOpen(windowID='%s_%s' % (window, item.itemID))

    errors = invCacheSvc.GetInventoryMgr().TrashItems([ item.itemID for item in invItems ], stationID if stationID else invItems[0].locationID)
    if errors:
        for e in errors:
            eve.Message(e)

        return
    isCorp = invItems[0].ownerID == session.corpid
    InvalidateItemLocation([session.charid, session.corpid][isCorp], stationID, invItems[0].flagID, invCacheSvc)
    if isCorp:
        sm.ScatterEvent('OnCorpAssetChange', invItems, stationID)
