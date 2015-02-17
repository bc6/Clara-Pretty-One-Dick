#Embedded file name: eve/client/script/ui/services/menuSvcExtras\menuFunctions.py
import sys
import types
import uicontrols
import uiprimitives
import uix
import uiutil
import uicls
import util
import blue
import destiny
import carbonui.const as uiconst
import localization
import geo2
import const
import form
import log
from eve.client.script.ui.shared.activateMultiTraining import ActivateMultiTrainingWindow
from eveexceptions import UserError
CONTAINERGROUPS = (const.groupWreck,
 const.groupCargoContainer,
 const.groupSpawnContainer,
 const.groupSpewContainer,
 const.groupSecureCargoContainer,
 const.groupAuditLogSecureContainer,
 const.groupFreightContainer,
 const.groupDeadspaceOverseersBelongings,
 const.groupMissionContainer)

def AddHint(hint, where):
    hintobj = uiprimitives.Container(parent=where, name='hint', align=uiconst.TOPLEFT, width=200, height=16, idx=0, state=uiconst.UI_DISABLED)
    hintobj.hinttext = uicontrols.EveHeaderSmall(text=hint, parent=hintobj, top=4, state=uiconst.UI_DISABLED)
    border = uicontrols.Frame(parent=hintobj, frameConst=uiconst.FRAME_BORDER1_CORNER5, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 0.25))
    frame = uicontrols.Frame(parent=hintobj, color=(0.0, 0.0, 0.0, 0.75), frameConst=uiconst.FRAME_FILLED_CORNER4, state=uiconst.UI_DISABLED)
    if hintobj.hinttext.textwidth > 200:
        hintobj.hinttext.width = 200
        hintobj.hinttext.text = '<center>' + hint + '</center>'
    hintobj.width = max(56, hintobj.hinttext.textwidth + 16)
    hintobj.height = max(16, hintobj.hinttext.textheight + hintobj.hinttext.top * 2)
    hintobj.left = (where.width - hintobj.width) / 2
    hintobj.top = -hintobj.height - 4
    hintobj.hinttext.left = (hintobj.width - hintobj.hinttext.textwidth) / 2


def AwardDecoration(charIDs):
    if not charIDs:
        return
    if not type(charIDs) == list:
        charIDs = [charIDs]
    info, graphics = sm.GetService('medals').GetAllCorpMedals(session.corpid)
    options = [ (medal.title, medal.medalID) for medal in info ]
    if len(options) <= 0:
        raise UserError('MedalCreateToAward')
    cfg.eveowners.Prime(charIDs)
    hintLen = 5
    hint = ', '.join([ cfg.eveowners.Get(charID).name for charID in charIDs[:hintLen] ])
    if len(charIDs) > hintLen:
        hint += ', ...'
    ret = uix.ListWnd(options, 'generic', localization.GetByLabel('UI/Corporations/Common/AwardCorpMemberDecoration'), isModal=1, ordered=1, scrollHeaders=[localization.GetByLabel('UI/Inventory/InvItemNameShort')], hint=hint)
    if ret:
        medalID = ret[1]
        sm.StartService('medals').GiveMedalToCharacters(medalID, charIDs)


def GetOwnerLabel(ownerID):
    name = ''
    if ownerID is not None:
        try:
            name = ' (' + cfg.eveowners.Get(ownerID).name + ')    '
        except:
            sys.exc_clear()

    return str(ownerID) + name


def CopyItemIDAndMaybeQuantityToClipboard(invItem):
    txt = str(invItem.itemID)
    if invItem.stacksize > 1:
        txt = uiutil.MenuLabel('UI/Menusvc/ItemAndQuantityForClipboard', {'itemID': str(invItem.itemID),
         'quantity': invItem.stacksize})
    blue.pyos.SetClipboardData(txt)


def FindDist(currentDist, bookmark, ownBall, bp):
    dist = currentDist
    if bookmark and bookmark.locationID and bookmark.locationID == session.solarsystemid:
        if ownBall:
            myLoc = (ownBall.x, ownBall.y, ownBall.z)
        else:
            myLoc = None
        if (bookmark.typeID == const.typeSolarSystem or bookmark.itemID == bookmark.locationID) and bookmark.x is not None:
            location = None
            if hasattr(bookmark, 'locationType') and bookmark.locationType in ('agenthomebase', 'objective'):
                location = sm.GetService('agents').GetAgentMoniker(bookmark.agentID).GetEntryPoint()
            if location is None:
                location = (bookmark.x, bookmark.y, bookmark.z)
            if myLoc and location:
                dist = geo2.Vec3DistanceD(myLoc, location)
            else:
                dist = 0
        else:
            dist = 0.0
            if bookmark.itemID in bp.balls:
                b = bp.balls[bookmark.itemID]
                dist = b.surfaceDist
    return dist


def AddToQuickBar(typeID, parent = 0):
    sm.GetService('marketutils').AddTypeToQuickBar(typeID, parent)


def RemoveFromQuickBar(node):
    current = settings.user.ui.Get('quickbar', {})
    parent = node.parent
    typeID = node.typeID
    toDelete = None
    for dataID, data in current.items():
        if parent == data.parent and type(data.label) == types.IntType:
            if data.label == typeID:
                toDelete = dataID
                break

    if toDelete:
        del current[toDelete]
    settings.user.ui.Set('quickbar', current)
    sm.ScatterEvent('OnMarketQuickbarChange')


def TryLookAt(itemID):
    slimItem = uix.GetBallparkRecord(itemID)
    if not slimItem:
        return
    try:
        sm.GetService('camera').LookAt(itemID)
    except Exception as e:
        sys.exc_clear()


def ToggleLookAt(itemID):
    bp = sm.GetService('michelle').GetBallpark()
    if bp:
        ball = bp.GetBall(session.shipid)
        if ball and ball.mode == destiny.DSTBALL_WARP:
            return
    if sm.GetService('camera').LookingAt() == itemID and itemID != session.shipid:
        TryLookAt(session.shipid)
    else:
        TryLookAt(itemID)


def AbandonLoot(wreckID):
    """
        This will call the server and have it abandon the wreck, The server will update the
        Slim item and that will propagate back to the client..
    """
    twit = sm.GetService('michelle')
    localPark = twit.GetBallpark()
    allowedGroup = None
    if wreckID in localPark.slimItems:
        allowedGroup = localPark.slimItems[wreckID].groupID
    if eve.Message('ConfirmAbandonLoot', {'type': (const.UE_GROUPID, allowedGroup)}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
        return
    remotePark = sm.GetService('michelle').GetRemotePark()
    if remotePark is not None:
        remotePark.CmdAbandonLoot([wreckID])


def AbandonAllLoot(wreckID):
    """
        This will call the server and have it abandon the wreck, The server will update the
        Slim item and that will propagate back to the client..
    """
    twit = sm.GetService('michelle')
    localPark = twit.GetBallpark()
    remotePark = twit.GetRemotePark()
    if remotePark is None:
        return
    wrecks = []
    allowedGroup = None
    if wreckID in localPark.slimItems:
        allowedGroup = localPark.slimItems[wreckID].groupID
    if eve.Message('ConfirmAbandonLootAll', {'type': (const.UE_GROUPID, allowedGroup)}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
        return
    bp = sm.GetService('michelle').GetBallpark()
    for itemID, slimItem in localPark.slimItems.iteritems():
        if slimItem.groupID == allowedGroup:
            if bp.HaveLootRight(itemID) and not bp.IsAbandoned(itemID):
                wrecks.append(itemID)

    if remotePark is not None:
        remotePark.CmdAbandonLoot(wrecks)


def Eject():
    if eve.Message('ConfirmEject', {}, uiconst.YESNO) == uiconst.ID_YES:
        ship = sm.StartService('gameui').GetShipAccess()
        if ship:
            if session.stationid:
                eve.Message('NoEjectingToSpaceInStation')
            else:
                log.LogNotice('Ejecting from ship', session.shipid)
                sm.ScatterEvent('OnBeforeActiveShipChanged', None, util.GetActiveShip())
                sm.StartService('sessionMgr').PerformSessionChange('eject', ship.Eject)


def Board(itemID):
    ship = sm.StartService('gameui').GetShipAccess()
    if ship:
        log.LogNotice('Boarding ship', itemID)
        sm.ScatterEvent('OnBeforeActiveShipChanged', itemID, util.GetActiveShip())
        sm.StartService('sessionMgr').PerformSessionChange('board', ship.Board, itemID, session.shipid or session.stationid)
        shipItem = sm.StartService('godma').GetItem(session.shipid)
        if shipItem and shipItem.groupID != const.groupRookieship:
            sm.StartService('tutorial').OpenTutorialSequence_Check(uix.insuranceTutorial)


def BoardSMAShip(structureID, shipID):
    ship = sm.StartService('gameui').GetShipAccess()
    if ship:
        log.LogNotice('Boarding SMA ship', structureID, shipID)
        sm.ScatterEvent('OnBeforeActiveShipChanged', shipID, util.GetActiveShip())
        sm.StartService('sessionMgr').PerformSessionChange('board', ship.BoardStoredShip, structureID, shipID)
        shipItem = sm.StartService('godma').GetItem(session.shipid)
        if shipItem and shipItem.groupID != const.groupRookieship:
            sm.StartService('tutorial').OpenTutorialSequence_Check(uix.insuranceTutorial)


def SafeLogoff():
    shipAccess = sm.GetService('gameui').GetShipAccess()
    failedConditions = shipAccess.SafeLogoff()
    if failedConditions:
        eve.Message('CustomNotify', {'notify': '<br>'.join([localization.GetByLabel('UI/Inflight/SafeLogoff/ConditionsFailedHeader')] + [ localization.GetByLabel(error) for error in failedConditions ])})


def AskNewContainerPassword(invCacheSvc, id_, desc, which = 1, setnew = '', setold = ''):
    container = invCacheSvc.GetInventoryFromId(id_)
    wndFormat = []
    if container.HasExistingPasswordSet(which):
        wndFormat.append({'type': 'edit',
         'setvalue': setold or '',
         'labelwidth': 48,
         'label': localization.GetByLabel('UI/Menusvc/OldPassword'),
         'key': 'oldpassword',
         'maxlength': 16,
         'setfocus': 1,
         'passwordChar': '*'})
    wndFormat.append({'type': 'edit',
     'setvalue': setnew or '',
     'labelwidth': 48,
     'label': localization.GetByLabel('UI/Menusvc/NewPassword'),
     'key': 'newpassword',
     'maxlength': 16,
     'passwordChar': '*'})
    wndFormat.append({'type': 'edit',
     'setvalue': '',
     'labelwidth': 48,
     'label': localization.GetByLabel('UI/Menusvc/ConfirmPassword'),
     'key': 'conpassword',
     'maxlength': 16,
     'passwordChar': '*'})
    retval = uix.HybridWnd(wndFormat, desc, icon=uiconst.QUESTION, minW=300, minH=75)
    if retval:
        old = retval['oldpassword'] or None if 'oldpassword' in retval else None
        new = retval['newpassword'] or None
        con = retval['conpassword'] or None
        if new is None or len(new) < 3:
            eve.Message('MinThreeLetters')
            return AskNewContainerPassword(id_, desc, which, new, old)
        if new != con:
            eve.Message('NewPasswordMismatch')
            return AskNewContainerPassword(id_, desc, which, new, old)
        container.SetPassword(which, old, new)


def ConfigureALSC(itemID, invCacheSvc):
    container = invCacheSvc.GetInventoryFromId(itemID)
    config = container.ALSCConfigGet()
    defaultLock = bool(config & const.ALSCLockAddedItems)
    containerOwnerID = container.GetItem().ownerID
    if util.IsCorporation(containerOwnerID):
        if charsession.corprole & const.corpRoleEquipmentConfig == 0:
            raise UserError('PermissionDeniedNeedEquipRole', {'corp': (const.UE_OWNERID, containerOwnerID)})
    else:
        userDefaultLock = settings.user.ui.Get('defaultContainerLock_%s' % itemID, None)
        if userDefaultLock:
            defaultLock = True if userDefaultLock == const.flagLocked else False
    configSettings = [(const.ALSCPasswordNeededToOpen, localization.GetByLabel('UI/Menusvc/ContainerPasswordForOpening')),
     (const.ALSCPasswordNeededToLock, localization.GetByLabel('UI/Menusvc/ContainerPasswordForLocking')),
     (const.ALSCPasswordNeededToUnlock, localization.GetByLabel('UI/Menusvc/ContainerPasswordForUnlocking')),
     (const.ALSCPasswordNeededToViewAuditLog, localization.GetByLabel('UI/Menusvc/ContainerPasswordForViewingLog'))]
    formFormat = []
    formFormat.append({'type': 'header',
     'text': localization.GetByLabel('UI/Menusvc/ContainerDefaultLocked'),
     'frame': 1})
    formFormat.append({'type': 'checkbox',
     'setvalue': defaultLock,
     'key': const.ALSCLockAddedItems,
     'label': '',
     'text': localization.GetByLabel('UI/Menusvc/ALSCLocked'),
     'frame': 1})
    formFormat.append({'type': 'btline'})
    formFormat.append({'type': 'push'})
    formFormat.append({'type': 'header',
     'text': localization.GetByLabel('UI/Menusvc/ContainerPasswordRequiredFor'),
     'frame': 1})
    for value, settingName in configSettings:
        formFormat.append({'type': 'checkbox',
         'setvalue': value & config == value,
         'key': value,
         'label': '',
         'text': settingName,
         'frame': 1})

    formFormat.append({'type': 'btline'})
    formFormat.append({'type': 'push'})
    retval = uix.HybridWnd(formFormat, localization.GetByLabel('UI/Menusvc/ContainerConfigurationHeader'), 1, None, uiconst.OKCANCEL, unresizeAble=1, minW=300)
    if retval is None:
        return
    settings.user.ui.Delete('defaultContainerLock_%s' % itemID)
    newconfig = 0
    for k, v in retval.iteritems():
        newconfig |= k * v

    if config != newconfig:
        container.ALSCConfigSet(newconfig)


def RetrievePasswordALSC(itemID, invCacheSvc):
    container = invCacheSvc.GetInventoryFromId(itemID)
    formFormat = []
    formFormat.append({'type': 'header',
     'text': localization.GetByLabel('UI/Menusvc/RetrieveWhichPassword'),
     'frame': 1})
    formFormat.append({'type': 'push'})
    formFormat.append({'type': 'btline'})
    configSettings = [[const.SCCPasswordTypeGeneral, localization.GetByLabel('UI/Menusvc/GeneralPassword')], [const.SCCPasswordTypeConfig, localization.GetByLabel('UI/Menusvc/RetrievePasswordConfiguration')]]
    for value, settingName in configSettings:
        formFormat.append({'type': 'checkbox',
         'setvalue': value & const.SCCPasswordTypeGeneral == value,
         'key': value,
         'label': '',
         'text': settingName,
         'frame': 1,
         'group': 'which_password'})

    formFormat.append({'type': 'btline'})
    retval = uix.HybridWnd(formFormat, localization.GetByLabel('UI/Commands/RetrievePassword'), 1, None, uiconst.OKCANCEL)
    if retval is None:
        return
    container.RetrievePassword(retval['which_password'])


def SetName(invOrSlimItem, invCacheSvc):
    invCacheSvc.TryLockItem(invOrSlimItem.itemID, 'lockItemRenaming', {'itemType': invOrSlimItem.typeID}, 1)
    try:
        cfg.evelocations.Prime([invOrSlimItem.itemID])
        try:
            setval = cfg.evelocations.Get(invOrSlimItem.itemID).name
        except:
            setval = ''
            sys.exc_clear()

        maxLength = 100
        categoryID = cfg.invtypes.Get(invOrSlimItem.typeID).Group().Category().id
        if categoryID == const.categoryShip:
            maxLength = 20
        elif categoryID == const.categoryStructure:
            maxLength = 32
        nameRet = uiutil.NamePopup(localization.GetByLabel('UI/Menusvc/SetName'), localization.GetByLabel('UI/Menusvc/TypeInNewName'), setvalue=setval, maxLength=maxLength)
        if nameRet:
            invCacheSvc.GetInventoryMgr().SetLabel(invOrSlimItem.itemID, nameRet.replace('\n', ' '))
            sm.ScatterEvent('OnItemNameChange')
    finally:
        invCacheSvc.UnlockItem(invOrSlimItem.itemID)


def ActivatePlex(itemID):
    wnd = form.ActivatePlexWindow.Open(itemID=itemID)
    if wnd and not wnd.destroyed:
        wnd.itemID = itemID
    wnd.ModalPosition()


def ApplyAurumToken(item, qty):
    if item.typeID == const.typePilotLicence and boot.region == 'optic':
        conversionRate = const.chinaPlex2AurExchangeRatio
    else:
        conversionRate = sm.GetService('clientDogmaStaticSvc').GetTypeAttribute2(item.typeID, const.attributeAurumConversionRate)
    totalAurum = conversionRate * qty
    headerLabel = localization.GetByLabel('UI/Menusvc/ConvertAurumQuestionHeader')
    bodyLabel = localization.GetByLabel('UI/Menusvc/ConvertAurumQuestionBody', typeName=cfg.invtypes.Get(item.typeID).typeName, quantity=qty, totalAurum=totalAurum)
    if eve.Message('CustomQuestion', {'header': headerLabel,
     'question': bodyLabel}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
        return
    accountUrl = sm.GetService('vgsService').GetStore().GetAccount().GetTransactionHref()
    if item.typeID == const.typePilotLicence:
        sm.GetService('invCache').GetInventoryMgr().ConvertPlexToCurrency(item.itemID, qty, accountUrl)
    else:
        sm.GetService('invCache').GetInventoryMgr().ConvertAurTokenToCurrency(item.itemID, qty, accountUrl)


def ActivateCharacterReSculpt(itemID):
    dialogParams = {'charName': cfg.eveowners.Get(session.charid).name}
    if eve.Message('ActivateCharacterReSculpt', dialogParams, uiconst.YESNO) == uiconst.ID_YES:
        sm.RemoteSvc('userSvc').ActivateCharacterReSculpt(itemID)


def ActivateMultiTraining(itemID):
    wnd = ActivateMultiTrainingWindow.Open(itemID=itemID)
    if wnd and not wnd.destroyed:
        wnd.itemID = itemID
    wnd.ModalPosition()


def SelfDestructShip(pickid):
    if eve.Message('ConfirmSelfDestruct', {}, uiconst.YESNO) == uiconst.ID_YES:
        ship = sm.StartService('gameui').GetShipAccess()
        if ship and not session.stationid:
            log.LogNotice('Self Destruct for', session.shipid)
            sm.StartService('sessionMgr').PerformSessionChange('selfdestruct', ship.SelfDestruct, pickid)


def DeclareWar():
    dlg = form.CorporationOrAlliancePickerDailog.Open(warableEntitysOnly=True)
    dlg.ShowModal()
    againstID = dlg.ownerID
    if not againstID:
        return
    DeclareWarAgainst(againstID)


def DeclareWarAgainst(againstID):
    cost = sm.GetService('war').GetCostOfWarAgainst(againstID)
    allianceLabel = localization.GetByLabel('UI/Common/Alliance')
    svc = sm.GetService('alliance') if session.allianceid else sm.GetService('corp')
    messageName = 'WarDeclareConfirmAlliance' if session.allianceid is not None else 'WarDeclareConfirmCorporation'
    if eve.Message(messageName, {'against': cfg.eveowners.Get(againstID).ownerName,
     'price': util.FmtISK(cost, showFractionsAlways=0)}, uiconst.YESNO) == uiconst.ID_YES:
        svc.DeclareWarAgainst(againstID, cost)


def TransferOwnership(itemID):
    """Transfer ownership of a sovereignty structure to a new owner"""
    members = sm.GetService('alliance').GetMembers()
    twit = sm.GetService('michelle')
    remotePark = twit.GetRemotePark()
    localPark = twit.GetBallpark()
    if itemID not in localPark.slimItems:
        return
    oldOwnerID = localPark.slimItems[itemID].ownerID
    owners = {member.corporationID for member in members.itervalues()}
    if len(owners):
        cfg.eveowners.Prime(owners)
    tmplist = []
    for member in members.itervalues():
        if oldOwnerID != member.corporationID:
            tmplist.append((cfg.eveowners.Get(member.corporationID).ownerName, member.corporationID))

    ret = uix.ListWnd(tmplist, 'generic', localization.GetByLabel('UI/Corporations/Common/SelectCorporation'), None, 1)
    if ret is not None and len(ret):
        newOwnerID = ret[1]
        if remotePark is not None:
            remotePark.CmdChangeStructureOwner(itemID, oldOwnerID, newOwnerID)


def TransferCorporationOwnership(itemID):
    """ Orbitals can be transferred to anyone, including corps outside your alliance. """
    michelle = sm.GetService('michelle')
    remotePark = michelle.GetRemotePark()
    localPark = michelle.GetBallpark()
    if itemID not in localPark.slimItems or remotePark is None:
        return
    oldOwnerID = localPark.slimItems[itemID].ownerID
    name = uiutil.NamePopup(localization.GetByLabel('UI/Corporations/Common/TransferOwnership'), localization.GetByLabel('UI/Corporations/Common/TransferOwnershipLabel'))
    if name is None:
        return
    owner = uix.SearchOwners(searchStr=name, groupIDs=[const.groupCorporation], hideNPC=True, notifyOneMatch=True, searchWndName='AddToBlockSearch')
    if owner is None or owner == oldOwnerID:
        return
    remotePark.CmdChangeStructureOwner(itemID, oldOwnerID, owner)
