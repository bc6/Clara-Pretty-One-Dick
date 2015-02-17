#Embedded file name: eve/client/script/ui/util\eveOverrides.py
import carbonui.const as uiconst
from eve.client.script.ui.control.eveIcon import DraggableIcon
from eve.client.script.ui.util.uix import GetOwnerLogo, GetTechLevelIcon
from eve.client.script.ui.control.allUserEntries import AllUserEntries
from eve.client.script.ui.inflight.bracketsAndTargets.targetInBar import TargetInBar
from eve.client.script.ui.shared.item import InvItem
iconDict = {'listentry.PlaceEntry': 'res:/ui/Texture/WindowIcons/personallocations.png',
 'listentry.NoteItem': 'res:/ui/Texture/WindowIcons/note.png',
 'listentry.VirtualAgentMissionEntry': 'res:/ui/Texture/WindowIcons/journal.png',
 'listentry.FleetFinderEntry': 'res:/UI/Texture/WindowIcons/fleet.png',
 'listentry.DungeonTemplateEntry': 'ui_74_64_15',
 'listentry.FittingEntry': 'res:/ui/Texture/WindowIcons/fitting.png',
 'listentry.MailEntry': 'res:/UI/Texture/WindowIcons/evemail.png',
 'listentry.CorpAllianceEntry': 'res:/ui/Texture/WindowIcons/corporation.png',
 'listentry.QuickbarGroup': 'res:/ui/Texture/WindowIcons/smallfolder.png',
 'listentry.KillMail': 'res:/ui/Texture/WindowIcons/killreport.png',
 'listentry.KillMailCondensed': 'res:/ui/Texture/WindowIcons/killreport.png',
 'listentry.WarKillEntry': 'res:/UI/Texture/WindowIcons/wars.png',
 'listentry.WarEntry': 'res:/UI/Texture/WindowIcons/wars.png',
 'listentry.TutorialEntry': 'res:/UI/Texture/WindowIcons/tutorial.png',
 'listentry.CertEntry': 'res:/UI/Texture/WindowIcons/certificates.png',
 'listentry.CertEntryBasic': 'res:/UI/Texture/WindowIcons/certificates.png',
 'listentry.DroneMainGroup': 'res:/UI/Texture/WindowIcons/dronebay.png',
 'listentry.DroneSubGroup': 'res:/UI/Texture/WindowIcons/dronebay.png',
 'listentry.ChannelField': 'res:/ui/Texture/WindowIcons/chatchannel.png'}

def PrepareDrag_Override(dragContainer, dragSource, *args):
    from eve.client.script.ui.shared.inventory.treeData import TreeDataInv, TreeDataInvFolder
    dad = dragContainer
    x = 0
    y = 0
    iconSize = 64
    for node in dragContainer.dragData:
        guid = getattr(node, '__guid__', None)
        if guid:
            nameSpace, className = guid.split('.')
            ns = __import__(nameSpace)
            decoClass = getattr(ns, className, None)
        else:
            decoClass = None
        icon = DraggableIcon(align=uiconst.TOPLEFT, pos=(0, 0, 64, 64))
        icon.left = x * (iconSize + 10)
        icon.top = y * (iconSize + 10)
        if decoClass is not None and issubclass(decoClass, InvItem) or guid in ('xtriui.FittingSlot', 'xtriui.ModuleButton', 'xtriui.ShipUIModule'):
            isCopy = False
            if getattr(node, 'invtype', None) is not None:
                node.isBlueprint = node.invtype.Group().categoryID == const.categoryBlueprint
                if node.isBlueprint:
                    isCopy = node.rec.singleton == const.singletonBlueprintCopy
            typeID = node.rec.typeID
            MakeTypeIcon(icon, dad, typeID, iconSize, isCopy=isCopy)
        if guid in ('xtriui.TypeIcon', 'listentry.DraggableItem', 'uicls.GenericDraggableForTypeID', 'listentry.SkillTreeEntry', 'listentry.Item', 'listentry.ContractItemSelect', 'listentry.RedeemToken', 'listentry.FittingModuleEntry', 'listentry.KillItems', 'listentry.CustomsItem'):
            icon.LoadIconByTypeID(node.typeID)
        elif guid in AllUserEntries():
            charinfo = node.info or cfg.eveowners.Get(node.charID)
            GetOwnerLogo(icon, node.charID, iconSize, noServerCall=False)
        elif guid in iconDict:
            icon.LoadIcon(iconDict.get(guid))
        elif guid in ('listentry.QuickbarItem', 'listentry.GenericMarketItem', 'listentry.DirectionalScanResults', 'listentry.DroneEntry'):
            typeID = node.typeID
            MakeTypeIcon(icon, dad, typeID, iconSize)
        elif guid and guid.startswith('listentry.ContractEntry'):
            iconName = 'res:/ui/Texture/WindowIcons/contracts.png'
            if 'Auction' in guid:
                iconName = 'res:/ui/Texture/WindowIcons/contractAuction.png'
            elif 'ItemExchange' in guid:
                iconName = 'res:/ui/Texture/WindowIcons/contractItemExchange.png'
            elif 'Courier' in guid:
                iconName = 'res:/ui/Texture/WindowIcons/contractCourier.png'
            icon.LoadIcon(iconName)
        elif guid in ('xtriui.ListSurroundingsBtn', 'listentry.LocationTextEntry', 'listentry.LabelLocationTextTop', 'listentry.LocationGroup', 'listentry.LocationSearchItem'):
            icon.LoadIconByTypeID(node.typeID, itemID=node.itemID)
        elif guid == 'listentry.PaletteEntry':
            icon.LoadIconByTypeID(node.id, itemID=node.id)
        elif guid in ('listentry.SkillEntry', 'listentry.SkillQueueSkillEntry'):
            icon.LoadIconByTypeID(node.invtype.typeID)
        elif guid == 'neocom.BtnDataNode':
            icon.LoadIcon(node.iconPath)
        elif isinstance(node, (TreeDataInv, TreeDataInvFolder)):
            icon.LoadIcon(node.GetIcon())
        elif guid == 'listentry.RecruitmentEntry':
            corpID = node.corporationID
            GetOwnerLogo(icon, corpID, iconSize, noServerCall=False)
        elif guid == 'uiutil.InfoPanelDragData':
            icon.LoadIcon(node.infoPanelCls.default_iconTexturePath)
            icon.width = icon.height = 32
        elif guid == 'uicls.TargetInBar':
            icon.Flush()
            targetIcon = TargetInBar(align=uiconst.TOPLEFT, pos=(0, 0, 64, 64), parent=icon)
            targetIcon.updatedamage = True
            targetIcon.AddUIObjects(slimItem=node.slimItem(), itemID=node.itemID)
            if getattr(node, 'OnBeginMoveTarget', None):
                node.OnBeginMoveTarget()
        x += 1
        if x >= 3:
            x = 0
            y += 1
        dad.children.append(icon)
        icon.state = uiconst.UI_DISABLED
        if y > 2:
            break

    sm.GetService('audio').StartSoundLoop('DragDropLoop')
    dragContainer.dragSound = 'DragDropLoop'
    return (0, 0)


def MakeTypeIcon(icon, dad, typeID, iconSize, isCopy = False):
    techIcon = GetTechLevelIcon(None, typeID=typeID)
    if techIcon:
        techIcon.left = icon.left
        techIcon.top = icon.top
        dad.children.append(techIcon)
    icon.LoadIconByTypeID(typeID=typeID, size=iconSize, isCopy=isCopy)
