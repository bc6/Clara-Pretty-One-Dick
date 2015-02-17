#Embedded file name: eve/client/script/ui/shared\killReport.py
import sys
from eve.client.script.ui.control import entries as listentry
from eve.common.lib.appConst import defaultPadding, singletonBlueprintCopy
from eve.common.script.util.eveCommonUtils import GetPublicCrestUrl
import inventorycommon.const as inventoryConst
import localization
import uicontrols
import uiprimitives
import uix
import uiutil
import util
import carbonui.const as uiconst
import uicls
import log
import blue
import uthread
from collections import defaultdict

class KillReportWnd(uicontrols.Window):
    __guid__ = 'form.KillReportWnd'
    __notifyevents__ = []
    default_windowID = 'KillReportWnd'
    default_width = 650
    default_height = 640
    default_minSize = (default_width, default_height)
    default_iconNum = 'res:/UI/Texture/WindowICons/killreport.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        killmail = attributes.Get('killmail', None)
        self.windowID = attributes.windowID
        self.rawKillmail = None
        self.SetCaption(localization.GetByLabel('UI/Corporations/Wars/Killmails/KillReport'))
        self.SetTopparentHeight(0)
        self.SetHeaderIcon()
        settingsIcon = self.sr.headerIcon
        settingsIcon.state = uiconst.UI_NORMAL
        settingsIcon.GetMenu = self.GetSettingsMenu
        settingsIcon.expandOnLeft = 1
        settingsIcon.hint = localization.GetByLabel('UI/Common/Settings')
        self.ConstructLayout()
        self.LoadInfo(killmail)

    def ConstructLayout(self):
        topCont = uiprimitives.Container(name='topCont', parent=self.sr.main, align=uiconst.TOTOP, height=138, padding=defaultPadding)
        uiprimitives.Line(parent=topCont, align=uiconst.TOBOTTOM)
        topLeftCont = uiprimitives.Container(name='topLeftCont', parent=topCont, align=uiconst.TOLEFT, width=260, padLeft=defaultPadding)
        topRightCont = uiprimitives.Container(name='topRightCont', parent=topCont, align=uiconst.TOALL)
        self.guyCont = uiprimitives.Container(name='guyCont', parent=topLeftCont, align=uiconst.TOLEFT, width=128)
        self.shipCont = uiprimitives.Container(name='shipCont', parent=topLeftCont, align=uiconst.TOLEFT, width=128)
        self.infoCont = uiprimitives.Container(name='infoCont', parent=topRightCont, align=uiconst.TOALL, padLeft=6, padRight=4, clipChildren=True)
        victimCont = uiprimitives.Container(name='victimCont', parent=self.infoCont, align=uiconst.TOTOP, height=68)
        victimNameCont = uiprimitives.Container(name='victimNameCont', parent=victimCont, align=uiconst.TOTOP, height=24, clipChildren=True)
        victimCorpCont = uiprimitives.Container(name='victimCorpCont', parent=victimCont, align=uiconst.TOALL)
        self.victimCorpLogoCont = uiprimitives.Container(name='victimCorpLogoCont', parent=victimCorpCont, align=uiconst.TOLEFT, width=32)
        self.victimAllianceLogoCont = uiprimitives.Container(name='victimAllianceLogoCont', parent=victimCorpCont, align=uiconst.TOLEFT, width=32)
        victimCorpTextCont = uiprimitives.Container(name='victimCorpTextCont', parent=victimCorpCont, align=uiconst.TOALL, padLeft=defaultPadding)
        shipCont = uiprimitives.Container(name='damageCont', parent=self.infoCont, align=uiconst.TOTOP, height=32)
        dateCont = uiprimitives.Container(name='dateCont', parent=self.infoCont, align=uiconst.TOALL)
        self.victimName = uicontrols.EveCaptionSmall(text='', parent=victimNameCont, name='victimName', state=uiconst.UI_NORMAL)
        self.victimCorpName = uicontrols.EveLabelMedium(text='', parent=victimCorpTextCont, name='victimCorpName', align=uiconst.TOTOP, state=uiconst.UI_NORMAL, top=defaultPadding)
        self.victimAllianceName = uicontrols.EveLabelMedium(text='', parent=victimCorpTextCont, name='victimAllianceName', align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        self.shipName = uicontrols.EveLabelMedium(text='', parent=shipCont, name='shipName', state=uiconst.UI_NORMAL, autoFadeSides=True)
        self.killDate = uicontrols.EveLabelMedium(text='', parent=dateCont, name='killDate', autoFadeSides=True)
        self.locationName = uicontrols.EveLabelMedium(text='', parent=dateCont, name='locationName', top=14, state=uiconst.UI_NORMAL, autoFadeSides=True)
        infoCont = uiprimitives.Container(name='infoCont', parent=self.sr.main, align=uiconst.TOALL, padding=(defaultPadding,
         0,
         defaultPadding,
         defaultPadding))
        bottomLeftCont = uiprimitives.Container(name='bottomLeftCont', parent=infoCont, align=uiconst.TOLEFT, width=260, padLeft=defaultPadding)
        bottomRightCont = uiprimitives.Container(name='bottomRightCont', padLeft=4, parent=infoCont, align=uiconst.TOALL)
        killersCont = uiprimitives.Container(name='killersCont', parent=bottomLeftCont, align=uiconst.TOALL)
        self.killedOnBehalfCont = uiprimitives.Container(name='killedOnBehalfCont', parent=killersCont, align=uiconst.TOTOP, height=90)
        uicontrols.EveLabelLarge(text=localization.GetByLabel('UI/Corporations/Wars/Killmails/KilledOnBehalf'), parent=self.killedOnBehalfCont, align=uiconst.TOTOP)
        self.behalfCont = KilledOnBehalfContainer(name='behalfCont', parent=self.killedOnBehalfCont, align=uiconst.TOTOP)
        self.killedOnBehalfCont.display = False
        self.involvedParties = uicontrols.EveLabelLarge(text='', parent=killersCont, name='involvedParties', align=uiconst.TOTOP)
        self.damageTaken = uicontrols.EveLabelMedium(text='', parent=killersCont, name='damageTaken', align=uiconst.TOTOP, color=(1.0, 0.0, 0.0))
        finalBlowCont = uiprimitives.Container(name='finalBlowCont', parent=killersCont, align=uiconst.TOTOP, height=84, top=8)
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Corporations/Wars/Killmails/FinalBlow'), parent=finalBlowCont, align=uiconst.TOTOP)
        self.finalBlowCont = KillerContainer(name='topKiller', parent=finalBlowCont, align=uiconst.TOTOP)
        topDamageCont = uiprimitives.Container(name='topDamageCont', parent=killersCont, align=uiconst.TOTOP, height=94, top=12)
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Corporations/Wars/Killmails/TopDamage'), parent=topDamageCont, align=uiconst.TOTOP)
        self.topDamageCont = KillerContainer(name='topDamageCont', parent=topDamageCont, align=uiconst.TOTOP)
        self.killersScrollLine = uiprimitives.Line(parent=killersCont, align=uiconst.TOTOP, padBottom=6)
        self.killersScroll = uicls.ScrollContainer(name='killersScroll', parent=killersCont, align=uiconst.TOALL, alignMode=uiconst.TOTOP)
        self.loadingWheel = uicls.LoadingWheel(parent=killersCont, align=uiconst.CENTER, state=uiconst.UI_DISABLED, idx=0, top=50)
        self.loadingWheel.display = False
        itemsCont = uiprimitives.Container(name='itemsCont', parent=bottomRightCont, align=uiconst.TOALL)
        topItemsCont = uiprimitives.Container(name='topItemsCont', parent=itemsCont, align=uiconst.TOTOP, height=16, padBottom=defaultPadding)
        self.savefittingBtn = uicontrols.Button(label=localization.GetByLabel('UI/Corporations/Wars/Killmails/SaveFitting'), parent=topItemsCont, align=uiconst.TOPRIGHT, func=self.SaveFitting)
        uicontrols.EveLabelLarge(text=localization.GetByLabel('UI/Corporations/Wars/Killmails/FittingAndContent'), parent=topItemsCont, name='fittingLabel', align=uiconst.TOPLEFT)
        bottomItemsCont = uicontrols.ContainerAutoSize(name='bottomItemsCont', parent=itemsCont, align=uiconst.TOBOTTOM)
        allItemsCont = uiprimitives.Container(name='allItemsCont', parent=itemsCont, align=uiconst.TOALL)
        self.itemsScroll = uicontrols.Scroll(name='itemsScroll', parent=allItemsCont)
        totalLossCont = uiprimitives.Container(name='totalLossCont', parent=bottomItemsCont, align=uiconst.TOTOP, height=24)
        uicontrols.EveLabelLarge(text=localization.GetByLabel('UI/Corporations/Wars/Killmails/TotalWorth'), parent=totalLossCont, name='totalWorth', align=uiconst.TOPLEFT, top=2)
        self.totalWorthLabel = uicontrols.EveLabelLarge(text='', parent=totalLossCont, name='totalWorthLabel', align=uiconst.TOPRIGHT, top=2)
        self.totalPayoutCont = uicontrols.ContainerAutoSize(name='totalPayoutCont', parent=bottomItemsCont, align=uiconst.TOTOP)
        self.pendCont = uiprimitives.Container(name='pendCont', parent=self.totalPayoutCont, align=uiconst.TOTOP, height=14)
        uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Corporations/Wars/Killmails/PendInsurance'), parent=self.pendCont, name='totalLoss', align=uiconst.BOTTOMLEFT)
        self.pendLabel = uicontrols.EveLabelSmall(text='', parent=self.pendCont, name='pendLabel', align=uiconst.BOTTOMRIGHT, color=(1.0, 0.0, 0.0))
        self.lpCont = uiprimitives.Container(name='lpCont', parent=self.totalPayoutCont, align=uiconst.TOTOP, height=14)
        uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Corporations/Wars/Killmails/LPPaidOut'), parent=self.lpCont, name='totalLP', align=uiconst.BOTTOMLEFT)
        self.totalLPLabel = uicontrols.EveLabelSmall(text='', parent=self.lpCont, name='totalLPLabel', align=uiconst.BOTTOMRIGHT, color=(0.0, 1.0, 0.0))
        self.lpCont.display = False
        self.bountyCont = uiprimitives.Container(name='bountyCont', parent=self.totalPayoutCont, align=uiconst.TOTOP, height=14, display=False)
        uicontrols.EveLabelSmall(text=localization.GetByLabel('UI/Corporations/Wars/Killmails/BountyPaidOut'), parent=self.bountyCont, name='totalBounty', align=uiconst.BOTTOMLEFT)
        self.totalBountyLabel = uicontrols.EveLabelSmall(text='', parent=self.bountyCont, name='totalBountyLabel', align=uiconst.BOTTOMRIGHT, color=(0.0, 1.0, 0.0))
        self.bountyCont.display = False

    def LoadInfo(self, killmail):
        uthread.new(self.LoadInfo_thread, killmail)

    def LoadInfo_thread(self, killmail):
        self.guyCont.Flush()
        self.shipCont.Flush()
        self.victimAllianceLogoCont.Flush()
        self.victimCorpLogoCont.Flush()
        self.rawKillmail = killmail
        self.killmail = self.FormatKillMail(killmail)
        killmail = self.killmail
        self.attackers, self.items = util.GetKillMailInfo(self.rawKillmail)
        isCapsule = cfg.invtypes.Get(killmail.victimShipTypeID).groupID == inventoryConst.groupCapsule
        isShip = cfg.invtypes.Get(killmail.victimShipTypeID).categoryID == inventoryConst.categoryShip
        if len(self.items) and isShip and not isCapsule:
            self.savefittingBtn.display = True
        else:
            self.savefittingBtn.display = False
        if util.IsCharacter(killmail.victimCharacterID):
            victim = uicontrols.Icon(parent=self.guyCont, align=uiconst.TOPRIGHT, size=128, idx=0)
            sm.GetService('photo').GetPortrait(killmail.victimCharacterID, 128, victim)
            victim.OnClick = (self.OpenPortrait, killmail.victimCharacterID)
            victimHint = cfg.eveowners.Get(killmail.victimCharacterID).name
            dragHint = localization.GetByLabel('UI/Fitting/FittingWindow/FittingManagement/FittingIconHint')
        else:
            victim = uiutil.GetLogoIcon(itemID=killmail.victimCorporationID, parent=self.guyCont, acceptNone=False, align=uiconst.TOPRIGHT, height=128, width=128, state=uiconst.UI_NORMAL)
            victim.OnClick = (self.ShowInfo, killmail.victimCorporationID, inventoryConst.typeCorporation)
            victimHint = cfg.eveowners.Get(killmail.victimCorporationID).name
            dragHint = localization.GetByLabel('UI/Corporations/Wars/DragToShare')
        victim.GetDragData = self.GetKillDragData
        victim.hint = '%s<br>%s' % (victimHint, dragHint)
        ship = uicontrols.Icon(parent=self.shipCont, align=uiconst.TOPRIGHT, size=128, typeID=killmail.victimShipTypeID)
        ship.OnClick = (self.OpenPreview, killmail.victimShipTypeID)
        ship.GetDragData = self.GetKillDragData
        shipTechIcon = uiprimitives.Sprite(name='techIcon', parent=self.shipCont, width=16, height=16, idx=0)
        uix.GetTechLevelIcon(shipTechIcon, 0, killmail.victimShipTypeID)
        ship.hint = '%s<br>%s' % (cfg.invtypes.Get(killmail.victimShipTypeID).typeName, localization.GetByLabel('UI/Fitting/FittingWindow/FittingManagement/FittingIconHint'))
        victimCorpName = cfg.eveowners.Get(killmail.victimCorporationID).name
        victimCorpLabel = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=victimCorpName, info=('showinfo', inventoryConst.typeCorporation, killmail.victimCorporationID))
        self.victimCorpName.text = victimCorpLabel
        victimCorpLogo = uiutil.GetLogoIcon(itemID=killmail.victimCorporationID, parent=self.victimCorpLogoCont, acceptNone=False, align=uiconst.TOPRIGHT, height=32, width=32, state=uiconst.UI_NORMAL)
        victimCorpLogo.OnClick = (self.ShowInfo, killmail.victimCorporationID, inventoryConst.typeCorporation)
        victimCorpLogo.hint = victimCorpName
        victimCorpLogo.SetSize(32, 32)
        victimCorpNameTop = defaultPadding * 2
        if killmail.victimAllianceID:
            victimAllianceName = cfg.eveowners.Get(killmail.victimAllianceID).name
            victimAllianceLabel = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=victimAllianceName, info=('showinfo', inventoryConst.typeAlliance, killmail.victimAllianceID))
            self.victimAllianceName.text = victimAllianceLabel
            victimAllianceLogo = uiutil.GetLogoIcon(itemID=killmail.victimAllianceID, parent=self.victimAllianceLogoCont, acceptNone=False, align=uiconst.TOPRIGHT, height=32, width=32)
            victimAllianceLogo.OnClick = (self.ShowInfo, killmail.victimAllianceID, inventoryConst.typeAlliance)
            victimAllianceLogo.hint = victimAllianceName
            victimCorpNameTop = 0
        elif killmail.victimFactionID:
            victimFactionName = cfg.eveowners.Get(killmail.victimFactionID).name
            victimFactionLabel = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=victimFactionName, info=('showinfo', inventoryConst.typeFaction, killmail.victimFactionID))
            self.victimAllianceName.text = victimFactionLabel
            victimAllianceLogo = uiutil.GetLogoIcon(itemID=killmail.victimFactionID, parent=self.victimAllianceLogoCont, acceptNone=False, align=uiconst.TOPRIGHT, height=32, width=32)
            victimAllianceLogo.OnClick = (self.ShowInfo, killmail.victimFactionID, inventoryConst.typeFaction)
            victimAllianceLogo.hint = victimFactionName
            victimAllianceLogo.SetSize(32, 32)
            victimCorpNameTop = 0
        else:
            self.victimAllianceName.text = ''
            victimAllianceLogo = uiprimitives.Sprite(texturePath='res:/UI/Texture/defaultAlliance.dds', parent=self.victimAllianceLogoCont, align=uiconst.TOPLEFT, width=32, height=32, state=uiconst.UI_NORMAL)
            victimAllianceLogo.hint = localization.GetByLabel('UI/PeopleAndPlaces/OwnerNotInAnyAlliance', corpName=victimCorpName)
            victimAllianceLogo.SetAlpha(0.2)
        self.victimCorpName.top = victimCorpNameTop
        self.killDate.text = util.FmtDate(killmail.killTime, 'ss')
        self.locationName.text = self.GetLocation(killmail.solarSystemID)
        shipType = cfg.invtypes.Get(killmail.victimShipTypeID)
        shipName = shipType.typeName
        shipGroupID = shipType.groupID
        shipGroupName = cfg.invgroups.Get(shipGroupID).groupName
        shipLabel = localization.GetByLabel('UI/Corporations/Wars/Killmails/ShipInfo', showInfoName=shipName, info=('showinfo', killmail.victimShipTypeID), groupName=shipGroupName)
        if util.IsCharacter(killmail.victimCharacterID):
            victimName = cfg.eveowners.Get(killmail.victimCharacterID).name
            victimNameLabel = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=victimName, info=('showinfo', inventoryConst.typeCharacterAmarr, killmail.victimCharacterID))
            self.victimName.text = victimNameLabel
            self.shipName.text = shipLabel
        else:
            self.victimName.text = shipLabel
            self.shipName.text = ''
        self.damageTaken.text = localization.GetByLabel('UI/Corporations/Wars/Killmails/TotalDamage', damage=killmail.victimDamageTaken)
        if killmail.iskLost:
            worthText = util.FmtISK(killmail.iskLost, 0)
        else:
            worthText = localization.GetByLabel('UI/Common/Unknown')
        self.totalWorthLabel.text = worthText
        if self.rawKillmail.iskDestroyed is not None:
            lossText = util.FmtISK(self.rawKillmail.iskDestroyed, 0)
        else:
            lossText = localization.GetByLabel('UI/Common/Unknown')
        self.pendLabel.text = lossText
        if self.rawKillmail.bountyClaimed:
            bountyText = util.FmtISK(self.rawKillmail.bountyClaimed, 0)
            self.totalBountyLabel.text = bountyText
            self.bountyCont.display = True
        else:
            bountyText = None
            self.bountyCont.display = False
        if self.rawKillmail.loyaltyPoints is not None and self.rawKillmail.loyaltyPoints > 0:
            LPText = localization.GetByLabel('UI/LPStore/AmountLP', lpAmount=util.FmtAmt(self.rawKillmail.loyaltyPoints, showFraction=0))
            self.totalLPLabel.text = LPText
            self.lpCont.display = True
        else:
            LPText = None
            self.lpCont.display = False
        if bountyText is None and LPText is None:
            self.totalPayoutCont.display = False
        else:
            self.totalPayoutCont.display = True
        self._LoadItemsToScrollPanel(self.itemsScroll, self.GetItems())
        self.GetAttackers()
        self.DrawKillers()
        isKilledOnBehalf = False
        self.IsKilledOnBehalf(isKilledOnBehalf)

    def _LoadItemsToScrollPanel(self, scrollPanel, items):
        entries = []
        for slots, label, iconID in (('hiSlots', 'UI/Corporations/Wars/Killmails/HighPowerSlots', 293),
         ('medSlots', 'UI/Corporations/Wars/Killmails/MediumPowerSlots', 294),
         ('lowSlots', 'UI/Corporations/Wars/Killmails/LowPowerSlots', 295),
         ('rigs', 'UI/Corporations/Wars/Killmails/RigSlots', 3266),
         ('subSystems', 'UI/Corporations/Wars/Killmails/SubSystemSlots', 3756)):
            entries.extend(self._GetListEntriesForSlot(items[slots], label, iconID))

        for flag, label, iconID in ((inventoryConst.flagDroneBay, 'UI/Corporations/Wars/Killmails/DroneBay', 76), (inventoryConst.flagCargo, 'UI/Corporations/Wars/Killmails/CargoBay', 71), (inventoryConst.flagImplant, 'UI/Corporations/Wars/Killmails/Implants', 2224)):
            entries.extend(self._GetListEntriesForFlag(items['other'], flag, label, iconID))

        otherItems = []
        for flagID, items2 in items['other'].iteritems():
            if flagID in (inventoryConst.flagDroneBay, inventoryConst.flagCargo, inventoryConst.flagImplant):
                continue
            for item in items2:
                otherItems.extend(self._GetListEntriesForItem(item))

        if len(otherItems):
            entries.append(listentry.Get('ItemsHeader', {'label': 'Other',
             'iconID': 71}))
            entries.extend(otherItems)
        scrollPanel.Load(contentList=entries, headers=[], noContentHint=localization.GetByLabel('UI/Corporations/Assets/NoItemsFound'))

    def _GetListEntriesForSlot(self, items, label, iconID):
        if not len(items):
            return []
        entries = [listentry.Get('ItemsHeader', {'label': localization.GetByLabel(label),
          'iconID': iconID})]
        itemsByTypeID = {}
        for item in items:
            if item.typeID not in itemsByTypeID:
                itemsByTypeID[item.typeID] = item
            else:
                itemsByTypeID[item.typeID].qtyDestroyed += item.qtyDestroyed
                itemsByTypeID[item.typeID].qtyDropped += item.qtyDropped

        for item in itemsByTypeID.itervalues():
            entries.extend(self._GetListEntriesForItem(item))

        return entries

    def _GetListEntriesForFlag(self, items, flag, labelName, icon):
        entries = []
        if flag in items:
            label = localization.GetByLabel(labelName)
            entries.append(listentry.Get('ItemsHeader', {'label': label,
             'iconID': icon}))
            for item in items[flag]:
                entries.extend(self._GetListEntriesForItem(item))

        return entries

    def _GetListEntriesForItem(self, item, indented = False):
        entries = []
        if item.qtyDestroyed:
            destroyedData = self._MakeDestroyedEntryData(item, indented=indented)
            entries.append(listentry.Get('KillItems', data=destroyedData))
            if item.contents:
                for containerItem in item.contents:
                    entries.extend(self._GetListEntriesForItem(containerItem, indented=True))

        if item.qtyDropped:
            droppedData = self._MakeDroppedEntryData(item, indented=indented)
            entries.append(listentry.Get('KillItems', data=droppedData))
            if item.contents:
                for containerItem in item.contents:
                    entries.extend(self._GetListEntriesForItem(containerItem, indented=True))

        return entries

    def _MakeDroppedEntryData(self, item, indented = False):
        data = util.KeyVal()
        data.typeID = item.typeID
        data.qtyDestroyed = None
        data.qtyDropped = item.qtyDropped
        data.singleton = item.singleton
        data.flag = item.flag
        data.indented = indented
        return data

    def _MakeDestroyedEntryData(self, item, indented = False):
        data = util.KeyVal()
        data.typeID = item.typeID
        data.qtyDestroyed = item.qtyDestroyed
        data.qtyDropped = None
        data.singleton = item.singleton
        data.flag = item.flag
        data.indented = indented
        return data

    def DrawKillers(self):
        self.killersScroll.Flush()
        killmail = self.killmail
        topKiller = util.KeyVal()
        topKiller.killerID = killmail.finalCharacterID
        topKiller.killerCorporationID = killmail.finalCorporationID
        topKiller.killerAllianceID = killmail.finalAllianceID
        topKiller.killerShipTypeID = killmail.finalShipTypeID
        topKiller.killerWeaponTypeID = killmail.finalWeaponTypeID
        topKiller.killerSecurityStatus = killmail.finalSecurityStatus
        topKiller.killerDamageDone = killmail.finalDamageDone
        topKiller.killerFactionID = killmail.finalFactionID
        try:
            topKiller.percentage = float(killmail.finalDamageDone) / float(killmail.victimDamageTaken) * 100
        except ZeroDivisionError:
            topKiller.percentage = 0.0

        involvedParties = 1
        self.finalBlowCont.LoadInfo(topKiller)
        highestDamage, restOfAttackers = self.GetAttackers()
        if highestDamage.characterID:
            if topKiller.killerID != int(highestDamage.characterID):
                involvedParties += 1
        involvedParties += len(restOfAttackers)
        self.involvedParties.text = localization.GetByLabel('UI/Corporations/Wars/Killmails/InvolvedParties', parties=involvedParties)
        topDamage = self.GetKiller(highestDamage)
        self.topDamageCont.LoadInfo(topDamage)
        if len(restOfAttackers):
            self.loadingWheel.display = True
            self.killersScroll.state = uiconst.UI_NORMAL
            self.killersScrollLine.state = uiconst.UI_DISABLED
            idsToPrime = set()
            for k in restOfAttackers:
                if k.characterID:
                    idsToPrime.add(int(k.characterID))
                if k.corporationID:
                    idsToPrime.add(int(k.corporationID))
                if k.allianceID:
                    idsToPrime.add(int(k.allianceID))

            cfg.eveowners.Prime(idsToPrime)
            self.loadingWheel.display = False
            for killer in restOfAttackers:
                if self.destroyed:
                    break
                killerInfo = self.GetKiller(killer)
                killerCont = KillerContainer(parent=self.killersScroll, padBottom=8)
                killerCont.LoadInfo(killerInfo)
                blue.pyos.BeNice(100)

        else:
            self.killersScroll.state = uiconst.UI_HIDDEN
            self.killersScrollLine.state = uiconst.UI_HIDDEN

    def GetKiller(self, killer):
        killerInfo = util.KeyVal()
        if killer.characterID:
            killerInfo.killerID = int(killer.characterID)
        else:
            killerInfo.killerID = None
        killerInfo.killerCorporationID = killer.corporationID
        killerInfo.killerAllianceID = killer.allianceID
        if killer.shipTypeID:
            killerInfo.killerShipTypeID = int(killer.shipTypeID)
        else:
            killerInfo.killerShipTypeID = None
        if killer.weaponTypeID:
            killerInfo.killerWeaponTypeID = int(killer.weaponTypeID)
        else:
            killerInfo.killerWeaponTypeID = None
        killerInfo.killerSecurityStatus = killer.secStatusText
        killerInfo.killerDamageDone = killer.damageDone
        killerInfo.killerFactionID = killer.factionID
        try:
            killerInfo.percentage = float(killer.damageDone) / float(self.killmail.victimDamageTaken) * 100
        except ZeroDivisionError:
            killerInfo.percentage = 0

        return killerInfo

    def GetLocation(self, solarSystemID):
        try:
            sec, col = util.FmtSystemSecStatus(sm.GetService('map').GetSecurityStatus(solarSystemID), 1)
            col.a = 1.0
            securityLabel = "</b> <color=%s><hint='%s'>%s</hint></color>" % (util.StrFromColor(col), localization.GetByLabel('UI/Map/StarMap/SecurityStatus'), sec)
        except KeyError:
            log.LogException('Failed to get security status for item - displaying BROKEN')
            sys.exc_clear()
            securityLabel = ''

        solarSystem = cfg.mapSystemCache[solarSystemID]
        constellationID = solarSystem.constellationID
        regionID = solarSystem.regionID
        locationTrace = '<url=showinfo:%s//%s>%s</url>%s &lt; <url=showinfo:%s//%s>%s</url> &lt; <url=showinfo:%s//%s>%s</url>' % (inventoryConst.typeSolarSystem,
         solarSystemID,
         cfg.evelocations.Get(solarSystemID).locationName,
         securityLabel,
         inventoryConst.typeConstellation,
         constellationID,
         cfg.evelocations.Get(constellationID).locationName,
         inventoryConst.typeRegion,
         regionID,
         cfg.evelocations.Get(regionID).locationName)
        return locationTrace

    def FormatKillMail(self, killmail):
        km = util.KeyVal()
        km.killID = killmail.killID
        km.killTime = killmail.killTime
        km.solarSystemID = killmail.solarSystemID
        km.moonID = killmail.moonID
        km.victimCharacterID = killmail.victimCharacterID
        km.victimCorporationID = killmail.victimCorporationID
        km.victimFactionID = killmail.victimFactionID
        km.victimAllianceID = killmail.victimAllianceID
        km.victimShipTypeID = killmail.victimShipTypeID
        km.victimDamageTaken = killmail.victimDamageTaken
        km.finalCharacterID = killmail.finalCharacterID
        km.finalCorporationID = killmail.finalCorporationID
        km.finalAllianceID = killmail.finalAllianceID
        km.finalShipTypeID = killmail.finalShipTypeID
        km.finalWeaponTypeID = killmail.finalWeaponTypeID
        km.finalSecurityStatus = killmail.finalSecurityStatus
        km.finalDamageDone = killmail.finalDamageDone
        km.finalFactionID = killmail.finalFactionID
        km.warID = killmail.warID
        km.iskLost = killmail.iskLost or None
        return km

    def GetAttackers(self):
        self.attackers.sort(reverse=True)
        highestDamage = self.attackers[0][1]
        try:
            restOfAttackers = [ attacker for damage, attacker in self.attackers[1:] if not attacker.finalBlow ]
        except IndexError:
            restOfAttackers = []

        return (highestDamage, restOfAttackers)

    def IsKilledOnBehalf(self, isKilledOnBehalf):
        killRightSupplied = self.rawKillmail.killRightSupplied
        if killRightSupplied is not None:
            self.killedOnBehalfCont.display = True
            charID = killRightSupplied
            publicInfo = sm.GetService('corp').GetInfoWindowDataForChar(killRightSupplied)
            corpID = publicInfo.corpID
            allianceID = publicInfo.allianceID
            self.behalfCont.LoadInfo(charID, corpID, allianceID, None)
        else:
            self.killedOnBehalfCont.display = False

    def GetItems(self):
        ret = {'hiSlots': [],
         'medSlots': [],
         'lowSlots': [],
         'rigs': [],
         'subSystems': [],
         'other': defaultdict(list)}
        for item in self.items:
            loc = self.GetRack(item.flag)
            if loc is None:
                ret['other'][item.flag].append(item)
            else:
                ret[loc].append(item)

        return ret

    def GetRack(self, flagID):
        if inventoryConst.flagHiSlot0 <= flagID <= inventoryConst.flagHiSlot7:
            return 'hiSlots'
        if inventoryConst.flagMedSlot0 <= flagID <= inventoryConst.flagMedSlot7:
            return 'medSlots'
        if inventoryConst.flagLoSlot0 <= flagID <= inventoryConst.flagLoSlot7:
            return 'lowSlots'
        if inventoryConst.flagRigSlot0 <= flagID <= inventoryConst.flagRigSlot7:
            return 'rigs'
        if inventoryConst.flagSubSystemSlot0 <= flagID <= inventoryConst.flagSubSystemSlot7:
            return 'subSystems'

    def OpenPreview(self, typeID, *args):
        if util.IsPreviewable(typeID):
            sm.GetService('preview').PreviewType(typeID)

    def OpenPortrait(self, charID, *args):
        from eve.client.script.ui.shared.info.infoWindow import PortraitWindow
        PortraitWindow.CloseIfOpen()
        PortraitWindow.Open(charID=charID)

    def ShowInfo(self, itemID, typeID, *args):
        sm.GetService('info').ShowInfo(typeID, itemID)

    def SaveFitting(self, *args):
        sm.GetService('fittingSvc').DisplayFittingFromItems(self.rawKillmail.victimShipTypeID, self.items)

    def GetSettingsMenu(self, *args):
        m = [(uiutil.MenuLabel('UI/Control/Entries/CopyKillInfo'), self.GetCombatText, ()), (uiutil.MenuLabel('UI/Control/Entries/CopyExternalKillLink'), self.GetCrestUrl, ())]
        return m

    def GetCombatText(self, *args):
        killmail = util.CombatLog_CopyText(self.rawKillmail)
        blue.pyos.SetClipboardData(util.CleanKillMail(killmail))

    def GetCrestUrl(self, *args):
        crest_url = GetPublicCrestUrl('killmails', self.killmail.killID, util.GetKillReportHashValue(self.killmail))
        blue.pyos.SetClipboardData(crest_url)

    def GetKillDragData(self, *args):
        fakeNode = uiutil.Bunch()
        fakeNode.mail = self.rawKillmail
        fakeNode.__guid__ = 'listentry.KillMail'
        return [fakeNode]


class KillItems(listentry.Generic):
    __guid__ = 'listentry.KillItems'
    isDragObject = True

    def Startup(self, *args):
        listentry.Generic.Startup(self, *args)
        self.bgColor = uiprimitives.Fill(bgParent=self, color=(0.0, 1.0, 0.0, 0.1), state=uiconst.UI_HIDDEN)
        qtyCont = uiprimitives.Container(name='qtyCont', parent=self, align=uiconst.TORIGHT, width=80, padRight=defaultPadding)
        self.itemCont = uiprimitives.Container(name='itemCont', parent=self, align=uiconst.TOALL, clipChildren=True)
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=self.itemCont, state=uiconst.UI_DISABLED, maxLines=1, align=uiconst.CENTERLEFT)
        self.sr.qtyLabel = uicontrols.EveLabelMedium(text='', parent=qtyCont, state=uiconst.UI_DISABLED, maxLines=1, align=uiconst.CENTERRIGHT)
        iconCont = uiprimitives.Container(parent=self.itemCont, pos=(16, 0, 24, 24), align=uiconst.CENTERLEFT)
        uiprimitives.Sprite(bgParent=iconCont, name='background', texturePath='res:/UI/Texture/classes/InvItem/bgNormal.png')
        self.sr.icon = uicontrols.Icon(parent=iconCont, pos=(0, 1, 24, 24), align=uiconst.TOPLEFT, idx=0)
        self.sr.techIcon = uiprimitives.Sprite(name='techIcon', parent=iconCont, left=0, width=12, height=12, idx=0)

    def Load(self, node):
        listentry.Generic.Load(self, node)
        self.sr.node = node
        data = node
        if node.indented:
            self.itemCont.padLeft = 16
        self.sr.node.typeID = int(node.typeID)
        self.typeID = int(data.typeID)
        qtyDestroyed = data.qtyDestroyed
        qtyDropped = data.qtyDropped
        singleton = data.singleton
        flag = data.flag
        typeName = cfg.invtypes.Get(self.typeID).typeName
        isCopy = False
        categoryID = cfg.invtypes.Get(self.typeID).categoryID
        if categoryID == inventoryConst.categoryBlueprint:
            self.sr.icon.top = 0
            if singleton == singletonBlueprintCopy:
                isCopy = True
                typeName += ' (%s)' % localization.GetByLabel('UI/Generic/Copy').lower()
            else:
                typeName += ' (%s)' % localization.GetByLabel('UI/Generic/Original').lower()
        self.sr.label.text = typeName
        if qtyDropped > 0:
            self.bgColor.state = uiconst.UI_DISABLED
            self.sr.qtyLabel.text = util.FmtAmt(qtyDropped)
        else:
            self.bgColor = uiconst.UI_HIDDEN
            self.sr.qtyLabel.text = util.FmtAmt(qtyDestroyed)
        self.sr.techIcon.state = uiconst.UI_HIDDEN
        if self.typeID:
            self.sr.icon.state = uiconst.UI_NORMAL
            if flag == inventoryConst.flagImplant:
                self.sr.icon.LoadIcon(cfg.invtypes.Get(self.typeID).iconID, ignoreSize=True)
            else:
                self.sr.icon.LoadIconByTypeID(typeID=self.typeID, size=24, ignoreSize=True, isCopy=isCopy)
            self.sr.icon.SetSize(24, 24)
            self.sr.label.left = self.height + 16
            techSprite = uix.GetTechLevelIcon(self.sr.techIcon, 1, self.typeID)
            techSprite.SetSize(12, 12)

    def GetHeight(self, *args):
        node, width = args
        node.height = 26
        return node.height

    def GetMenu(self):
        if self.typeID:
            return sm.GetService('menu').GetMenuFormItemIDTypeID(None, self.typeID, ignoreMarketDetails=0)
        return []

    def OnDblClick(self, *args):
        sm.GetService('info').ShowInfo(self.typeID)

    def GetDragData(self, *args):
        return [self.sr.node]


class ItemsHeader(listentry.Header):
    __guid__ = 'listentry.ItemsHeader'

    def Startup(self, *args):
        listentry.Header.Startup(self, *args)
        self.sr.icon = uicontrols.Icon(parent=self, pos=(0, 0, 24, 24), align=uiconst.CENTERLEFT, idx=0, ignoreSize=True)

    def Load(self, node):
        listentry.Header.Load(self, node)
        self.sr.label.left = 30
        self.sr.icon.LoadIcon(node.iconID, ignoreSize=True)

    def GetHeight(self, *args):
        node, width = args
        node.height = 27
        return node.height


class KillerContainer(uiprimitives.Container):
    __guid__ = 'uicls.KillerContainer'
    default_height = 66
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.killerID = attributes.get('killerID', None)
        self.ConstructLayout()

    def ConstructLayout(self):
        iconCont = uiprimitives.Container(name='iconCont', parent=self, align=uiconst.TOLEFT, width=96)
        self.killerCont = uiprimitives.Container(name='killerCont', parent=iconCont, align=uiconst.TOLEFT, width=64, padTop=1, padBottom=1, state=uiconst.UI_NORMAL)
        self.shipCont = uiprimitives.Container(name='shipCont', parent=iconCont, align=uiconst.TOPRIGHT, width=32, height=32, top=1)
        uiprimitives.Sprite(bgParent=self.shipCont, name='shipBackground', texturePath='res:/UI/Texture/classes/InvItem/bgNormal.png')
        self.weaponCont = uiprimitives.Container(name='weaponCont', parent=iconCont, align=uiconst.BOTTOMRIGHT, width=32, height=32, top=1)
        uiprimitives.Sprite(bgParent=self.weaponCont, name='weaponBackground', texturePath='res:/UI/Texture/classes/InvItem/bgNormal.png')
        self.textCont = uiprimitives.Container(name='textCont', parent=self, align=uiconst.TOALL, padLeft=defaultPadding)
        self.nameLabel = uicontrols.EveLabelSmall(text='', parent=self.textCont, maxLines=1, align=uiconst.TOTOP, top=-1, state=uiconst.UI_NORMAL)
        self.corpLabel = uicontrols.EveLabelSmall(text='', parent=self.textCont, maxLines=1, align=uiconst.TOTOP, top=-1, state=uiconst.UI_NORMAL)
        self.allianceLabel = uicontrols.EveLabelSmall(text='', parent=self.textCont, maxLines=1, align=uiconst.TOTOP, top=-1, state=uiconst.UI_NORMAL)
        self.damageLabel = uicontrols.EveLabelSmall(text='', parent=self.textCont, maxLines=1, align=uiconst.TOBOTTOM)

    def LoadInfo(self, killer):
        self.killerCont.Flush()
        self.shipCont.Flush()
        self.weaponCont.Flush()
        self.allianceLabel.text = ''
        self.damageLabel.text = ''
        nameHint = ''
        killerLogo = uiprimitives.Sprite(parent=self.killerCont, align=uiconst.TOALL, idx=0, texturePath='res:/UI/Texture/silhouette_64.png')
        if killer.killerID:
            sm.GetService('photo').GetPortrait(killer.killerID, 64, killerLogo)
            killerLogo.OnClick = (self.ShowInfo, killer.killerID, inventoryConst.typeCharacterAmarr)
            killerLogo.hint = cfg.eveowners.Get(killer.killerID).name
        if killer.killerShipTypeID:
            shipLogo = uicontrols.Icon(parent=self.shipCont, align=uiconst.TOPRIGHT, size=32, typeID=killer.killerShipTypeID, ignoreSize=True)
            shipLogo.OnClick = (self.ShowInfo, None, killer.killerShipTypeID)
            shipTechIcon = uiprimitives.Sprite(name='techIcon', parent=self.shipCont, width=12, height=12, idx=0)
            shipTechSprite = uix.GetTechLevelIcon(shipTechIcon, 0, killer.killerShipTypeID)
            if shipTechSprite:
                shipTechSprite.SetSize(12, 12)
            shipLogo.hint = cfg.invtypes.Get(killer.killerShipTypeID).typeName
        if killer.killerWeaponTypeID:
            weaponLogo = uicontrols.Icon(parent=self.weaponCont, align=uiconst.TOPRIGHT, size=32, typeID=killer.killerWeaponTypeID, ignoreSize=True)
            weaponLogo.OnClick = (self.ShowInfo, None, killer.killerWeaponTypeID)
            techIcon = uiprimitives.Sprite(name='techIcon', parent=self.weaponCont, width=12, height=12, idx=0)
            techSprite = uix.GetTechLevelIcon(techIcon, 0, killer.killerWeaponTypeID)
            if techSprite:
                techSprite.SetSize(12, 12)
            self.damageLabel.text = localization.GetByLabel('UI/Corporations/Wars/Killmails/DamageDone', damage=killer.killerDamageDone, percentage=killer.percentage)
            weaponLogo.hint = '%s<br>%s' % (cfg.invtypes.Get(killer.killerWeaponTypeID).typeName, self.damageLabel.text)
        if killer.killerID:
            self.nameLabel.text = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=cfg.eveowners.Get(killer.killerID).name, info=('showinfo', inventoryConst.typeCharacterAmarr, killer.killerID))
            nameHint = '%s<br>%s' % (cfg.eveowners.Get(killer.killerID).name, cfg.eveowners.Get(killer.killerCorporationID).name)
        else:
            self.nameLabel.text = cfg.invtypes.Get(killer.killerShipTypeID).typeName
        self.corpLabel.text = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=cfg.eveowners.Get(killer.killerCorporationID).name, info=('showinfo', inventoryConst.typeCorporation, killer.killerCorporationID))
        if killer.killerAllianceID:
            self.allianceLabel.text = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=cfg.eveowners.Get(killer.killerAllianceID).name, info=('showinfo', inventoryConst.typeAlliance, killer.killerAllianceID))
            nameHint += '<br>%s' % cfg.eveowners.Get(killer.killerAllianceID).name
        elif killer.killerFactionID:
            self.allianceLabel.text = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=cfg.eveowners.Get(killer.killerFactionID).name, info=('showinfo', inventoryConst.typeFaction, killer.killerFactionID))
            nameHint += '<br>%s' % cfg.eveowners.Get(killer.killerFactionID).name
        killerLogo.hint = nameHint

    def ShowInfo(self, itemID, typeID, *args):
        sm.GetService('info').ShowInfo(typeID, itemID)


class KilledOnBehalfContainer(uiprimitives.Container):
    __guid__ = 'uicls.KilledOnBehalfContainer'
    default_height = 64
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.ConstructLayout()

    def ConstructLayout(self):
        uiprimitives.Fill(bgParent=self, color=(1.0, 0.0, 0.0, 0.2))
        uicontrols.Frame(parent=self, color=(1.0, 0.0, 0.0, 0.2))
        iconCont = uiprimitives.Container(name='iconCont', parent=self, align=uiconst.TOLEFT, width=96)
        self.behalfCont = uiprimitives.Container(name='behalfCont', parent=iconCont, align=uiconst.TOLEFT, width=64, state=uiconst.UI_NORMAL)
        self.corpCont = uiprimitives.Container(name='corpCont', parent=iconCont, align=uiconst.TOPRIGHT, width=32, height=32)
        self.allianceCont = uiprimitives.Container(name='allianceCont', parent=iconCont, align=uiconst.BOTTOMRIGHT, width=32, height=32)
        theRestCont = uiprimitives.Container(name='textCont', parent=self, align=uiconst.TOALL, padLeft=defaultPadding)
        self.textCont = uicontrols.ContainerAutoSize(parent=theRestCont, name='textCont', align=uiconst.CENTERLEFT)
        self.nameLabel = uicontrols.EveLabelSmall(text='', parent=self.textCont, maxLines=1, align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        self.corpLabel = uicontrols.EveLabelSmall(text='', parent=self.textCont, maxLines=1, align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL, top=13)
        self.allianceLabel = uicontrols.EveLabelSmall(text='', parent=self.textCont, maxLines=1, align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL, top=26)

    def LoadInfo(self, behalfID, corpID, allianceID = None, factionID = None):
        self.behalfCont.Flush()
        self.corpCont.Flush()
        self.allianceCont.Flush()
        self.allianceLabel.text = ''
        nameHint = ''
        behalfName = cfg.eveowners.Get(behalfID).name
        corpName = cfg.eveowners.Get(corpID).name
        self.allianceLabel.display = True
        behalfLogo = uiprimitives.Sprite(parent=self.behalfCont, align=uiconst.TOALL, idx=0, texturePath='res:/UI/Texture/silhouette_64.png')
        if behalfID:
            sm.GetService('photo').GetPortrait(behalfID, 64, behalfLogo)
            behalfLogo.OnClick = (self.ShowInfo, behalfID, inventoryConst.typeCharacterAmarr)
            behalfLogo.hint = cfg.eveowners.Get(behalfID).name
        if behalfID:
            self.nameLabel.text = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=cfg.eveowners.Get(behalfID).name, info=('showinfo', inventoryConst.typeCharacterAmarr, behalfID))
            nameHint = '%s<br>%s' % (behalfName, corpName)
        corpLogo = uiutil.GetLogoIcon(itemID=corpID, parent=self.corpCont, acceptNone=False, align=uiconst.TOPRIGHT, height=32, width=32, state=uiconst.UI_NORMAL)
        corpLogo.OnClick = (self.ShowInfo, corpID, inventoryConst.typeCorporation)
        corpLogo.hint = corpName
        corpLogo.SetSize(32, 32)
        self.corpLabel.text = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=corpName, info=('showinfo', inventoryConst.typeCorporation, corpID))
        if allianceID:
            allianceName = cfg.eveowners.Get(allianceID).name
            self.allianceLabel.text = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=allianceName, info=('showinfo', inventoryConst.typeAlliance, allianceID))
            nameHint += '<br>%s' % allianceName
            allianceLogo = uiutil.GetLogoIcon(itemID=allianceID, parent=self.allianceCont, acceptNone=False, align=uiconst.TOPRIGHT, height=32, width=32)
            allianceLogo.OnClick = (self.ShowInfo, allianceID, inventoryConst.typeAlliance)
            allianceLogo.hint = allianceName
        else:
            self.allianceLabel.text = ''
            allianceLogo = uiprimitives.Sprite(texturePath='res:/UI/Texture/defaultAlliance.dds', parent=self.allianceCont, align=uiconst.TOPLEFT, width=32, height=32, state=uiconst.UI_NORMAL)
            allianceLogo.hint = localization.GetByLabel('UI/PeopleAndPlaces/OwnerNotInAnyAlliance', corpName=corpName)
            allianceLogo.SetAlpha(0.3)
            self.allianceLabel.display = False
        behalfLogo.hint = nameHint

    def ShowInfo(self, itemID, typeID, *args):
        sm.GetService('info').ShowInfo(typeID, itemID)
