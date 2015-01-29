#Embedded file name: eve/client/script/ui/shared\sovereigntyEntry.py
from eve.client.script.ui.shared.stateFlag import AddAndSetFlagIcon
import uiprimitives
import uicontrols
import uthread
import uix
import carbonui.const as uiconst
import uiutil
import util
import uicls
from sovereignty import SovereigntyTab
COLOR = (1.0, 1.0, 1.0, 0.5)

class SovereigntyEntry(uicontrols.SE_BaseClassCore):
    """
    This class is for entries in sov dashboard
    """
    __guid__ = 'listentry.SovereigntyEntry'
    __nonpersistvars__ = ['selection', 'id']

    def Startup(self, *etc):
        uiprimitives.Line(parent=self, align=uiconst.TOBOTTOM, color=uiconst.ENTRY_LINE_COLOR)
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=self, left=6, align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, idx=0, maxLines=1)
        self.icon = uiprimitives.Container(name='icon', parent=self, align=uiconst.TOPLEFT, padding=(0, 0, 0, 0), pos=(0, 0, 14, 14), state=uiconst.UI_DISABLED)
        self.sr.loss = uiprimitives.Fill(parent=self, padTop=1, padBottom=1, color=(1.0, 0.0, 0.0, 0.25))

    def Load(self, node):
        self.sr.node = node
        self.sr.label.left = 16
        self.sr.label.text = node.label
        self.locationID = ''
        self.locationID = node.locationID
        self.allianceID = node.allianceID
        self.corpID = node.Get('corpID', None)
        self.scope = node.scope
        self.regionID = node.regionID
        AddAndSetFlagIcon(parentCont=self.icon, flag=node.flag, top=3, left=4)
        if node.loss is True:
            self.sr.loss.state = uiconst.UI_DISABLED
        else:
            self.sr.loss.state = uiconst.UI_HIDDEN

    def GetHeight(_self, *args):
        node, width = args
        node.height = uix.GetTextHeight(node.label, maxLines=1) + 1
        return node.height

    def OnMouseHover(self, *args):
        uthread.new(self.SetHint)

    def OnDblClick(self, *args):
        if self.scope != SovereigntyTab.SolarSystem:
            self.DrillToLocation()

    def SetHint(self, *args):
        pass

    def ShowInfo(self, *args):
        pass

    def GetMenu(self):
        m = []
        mm = []
        mmm = []
        if self.locationID:
            if self.regionID is None:
                label = ''
                if self.scope == SovereigntyTab.SolarSystem:
                    label = None
                    mm += sm.GetService('menu').CelestialMenu(self.locationID)
                    m.append((uiutil.MenuLabel('UI/Common/LocationTypes/System'), mm))
                if self.scope == SovereigntyTab.World:
                    label = uiutil.MenuLabel('UI/Common/LocationTypes/Region')
                    mm += sm.GetService('menu').CelestialMenu(self.locationID)
                    m.append((label, mm))
                elif self.scope == SovereigntyTab.Region:
                    label = uiutil.MenuLabel('UI/Common/LocationTypes/Constellation')
                    mm += sm.GetService('menu').CelestialMenu(self.locationID)
                    m.append((label, mm))
                elif self.scope == SovereigntyTab.Constellation:
                    label = uiutil.MenuLabel('UI/Common/LocationTypes/System')
                    mm += sm.GetService('menu').CelestialMenu(self.locationID)
                    m.append((label, mm))
                m.append(None)
                if label is not None:
                    if label == uiutil.MenuLabel('UI/Common/LocationTypes/System'):
                        viewLabel = uiutil.MenuLabel('UI/Common/LocationTypes/ViewSystem')
                    elif label == uiutil.MenuLabel('UI/Common/LocationTypes/Constellation'):
                        viewLabel = uiutil.MenuLabel('UI/Common/LocationTypes/ViewConstellation')
                    else:
                        viewLabel = uiutil.MenuLabel('UI/Common/LocationTypes/ViewRegion')
                    m.append([viewLabel, self.DrillToLocation])
            else:
                mm += sm.GetService('menu').CelestialMenu(self.locationID)
                m.append((uiutil.MenuLabel('UI/Common/LocationTypes/System'), mm))
                mmm += sm.GetService('menu').CelestialMenu(self.regionID)
                m.append((uiutil.MenuLabel('UI/Common/LocationTypes/Region'), mmm))
                m.append(None)
            if self.allianceID is not None:
                if util.IsFaction(self.allianceID):
                    m.append([uiutil.MenuLabel('UI/Sovereignty/ShowInfoOnFaction'), self.ShowInfoOnSovHolder, (const.typeFaction, self.allianceID)])
                else:
                    m.append([uiutil.MenuLabel('UI/Sovereignty/ShowInfoOnAlliance'), self.ShowInfoOnSovHolder, (const.typeAlliance, self.allianceID)])
            elif self.corpID is not None:
                m.append([uiutil.MenuLabel('UI/Sovereignty/ShowInfoOnCorporation'), self.ShowInfoOnSovHolder, (const.typeCorporation, self.corpID)])
            return m
        else:
            return

    def DrillToLocation(self):
        systemID = None
        constellationID = None
        regionID = None
        if self.scope in (SovereigntyTab.Constellation, SovereigntyTab.Changes):
            systemID = self.locationID
            constellationID = sm.GetService('map').GetParent(systemID)
            regionID = sm.GetService('map').GetParent(constellationID)
        if self.scope == SovereigntyTab.Region:
            constellationID = self.locationID
            regionID = sm.GetService('map').GetParent(constellationID)
        if self.scope == SovereigntyTab.World:
            regionID = self.locationID
        location = (systemID, constellationID, regionID)
        sm.GetService('sov').GetSovOverview(location)

    def ShowInfoOnSovHolder(self, typeID, allianceID):
        """show info on alliance, faction or if in changes region as well"""
        sm.StartService('info').ShowInfo(typeID, allianceID)


class HeaderEntry(uicontrols.SE_BaseClassCore):
    """
    This class is for header entries in sov dashboard
    """
    __guid__ = 'listentry.HeaderEntry'
    default_showHilite = False

    def Startup(self, *etc):
        uiprimitives.Line(parent=self, align=uiconst.TOBOTTOM, color=uiconst.ENTRY_LINE_COLOR)
        self.container = uiprimitives.Container(name='container', parent=self)
        self.industry = uiprimitives.Container(name='industry', parent=self, align=uiconst.TORIGHT, pos=(0, 0, 88, 0), padRight=7)
        self.military = uiprimitives.Container(name='military', parent=self, align=uiconst.TORIGHT, pos=(0, 0, 88, 0), padRight=8)
        self.claimTime = uiprimitives.Container(name='claimTime', parent=self, align=uiconst.TORIGHT, pos=(0, 0, 88, 0), padRight=8)
        self.system = uiprimitives.Container(name='solarsystem', parent=self, padLeft=4)
        self.systemHeader = uicontrols.EveLabelSmall(text='', parent=self.system, left=0, top=4, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0, maxLines=1)
        self.claimTimeHeader = uicontrols.EveLabelSmall(text='', parent=self.claimTime, left=0, top=4, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0, maxLines=1)
        self.militaryHeader = uicontrols.EveLabelSmall(text='', parent=self.military, left=0, top=4, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0, maxLines=1)
        self.industryHeader = uicontrols.EveLabelSmall(text='', parent=self.industry, left=0, top=4, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0, maxLines=1)

    def Load(self, node):
        self.sr.node = node
        self.militaryHeader.text = node.militaryHeader
        self.systemHeader.text = node.systemHeader
        self.claimTimeHeader.text = node.claimTimeHeader
        self.industryHeader.text = node.industryHeader


class IndexEntry(uicontrols.SE_BaseClassCore):
    """
    This class is for index entries in sov dashboard
    """
    __guid__ = 'listentry.IndexEntry'

    def Startup(self, *etc):
        uiprimitives.Line(parent=self, align=uiconst.TOBOTTOM, color=uiconst.ENTRY_LINE_COLOR)
        self.container = uiprimitives.Container(name='container', parent=self)
        self.system = uiprimitives.Container(name='solarsystem', parent=self)
        self.industry = uiprimitives.Container(name='industry', parent=self, align=uiconst.TORIGHT, pos=(0, 0, 88, 10), padding=(0, 3, 8, 4))
        self.military = uiprimitives.Container(name='military', parent=self, align=uiconst.TORIGHT, pos=(0, 0, 88, 10), padding=(0, 3, 8, 4))
        self.claimTime = uiprimitives.Container(name='claimTime', parent=self, align=uiconst.TORIGHT, pos=(0, 0, 88, 10), padding=(0, 3, 8, 4))
        self.location = uicontrols.EveLabelMedium(text='', parent=self.system, left=6, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0, maxLines=1)
        uicontrols.Frame(parent=self.claimTime, color=COLOR)
        self.claimTimeBars = []
        for i in xrange(5):
            f = uiprimitives.Fill(parent=self.claimTime, name='claimTime%d' % i, align=uiconst.TOPLEFT, color=COLOR, pos=(2 + i * 17,
             2,
             16,
             6))
            self.claimTimeBars.append(f)

        uicontrols.Frame(parent=self.military, color=COLOR)
        self.militaryBars = []
        for i in xrange(5):
            f = uiprimitives.Fill(parent=self.military, name='military%d' % i, align=uiconst.TOPLEFT, color=COLOR, pos=(2 + i * 17,
             2,
             16,
             6))
            self.militaryBars.append(f)

        uicontrols.Frame(parent=self.industry, color=COLOR)
        self.industryBars = []
        for i in xrange(5):
            f = uiprimitives.Fill(parent=self.industry, name='industry%d' % i, align=uiconst.TOPLEFT, color=COLOR, pos=(2 + i * 17,
             2,
             16,
             6))
            self.industryBars.append(f)

    def Load(self, node):
        if self.sr.node.Get('selected', 0):
            self.Select()
        else:
            self.Deselect()
        self.sr.node = node
        self.location.text = node.label
        self.locationID = node.locationID
        self.scope = node.scope
        self.DrawLevels(self.industryBars, const.attributeDevIndexIndustrial, node.industrialPoints)
        self.DrawLevels(self.militaryBars, const.attributeDevIndexMilitary, node.militaryPoints)
        self.DrawLevels(self.claimTimeBars, const.attributeDevIndexSovereignty, node.claimedFor * const.DAY / const.SEC)

    def DrawLevels(self, bars, indexID = None, value = None):
        indexInfo = sm.GetService('sov').GetIndexLevel(value, indexID)
        for i in xrange(5):
            fill = bars[i]
            fill.color.SetRGB(1.0, 1.0, 1.0, 0.5)
            if indexInfo.level > i:
                fill.state = uiconst.UI_DISABLED
            else:
                fill.state = uiconst.UI_HIDDEN

    def OnDblClick(self, *args):
        if self.scope != SovereigntyTab.SolarSystem:
            self.DrillToLocation()

    def GetMenu(self):
        m = []
        mm = []
        if self.locationID:
            label = ''
            if self.scope == SovereigntyTab.SolarSystem:
                label = None
                mm += sm.GetService('menu').CelestialMenu(self.locationID)
                m.append((uiutil.MenuLabel('UI/Common/LocationTypes/System'), mm))
            if self.scope == SovereigntyTab.World:
                label = uiutil.MenuLabel('UI/Common/LocationTypes/Region')
                mm += sm.GetService('menu').CelestialMenu(self.locationID)
                m.append((label, mm))
            elif self.scope == SovereigntyTab.Region:
                label = uiutil.MenuLabel('UI/Common/LocationTypes/Constellation')
                mm += sm.GetService('menu').CelestialMenu(self.locationID)
                m.append((label, mm))
            elif self.scope == SovereigntyTab.Constellation:
                label = uiutil.MenuLabel('UI/Common/LocationTypes/System')
                mm += sm.GetService('menu').CelestialMenu(self.locationID)
                m.append((label, mm))
            m.append(None)
            if label is not None:
                if label == uiutil.MenuLabel('UI/Common/LocationTypes/System'):
                    viewLabel = uiutil.MenuLabel('UI/Common/LocationTypes/ViewSystem')
                elif label == uiutil.MenuLabel('UI/Common/LocationTypes/Constellation'):
                    viewLabel = uiutil.MenuLabel('UI/Common/LocationTypes/ViewConstellation')
                else:
                    viewLabel = uiutil.MenuLabel('UI/Common/LocationTypes/ViewRegion')
                m.append([viewLabel, self.DrillToLocation])
            return m
        else:
            return

    def DrillToLocation(self):
        systemID = None
        constellationID = None
        regionID = None
        if self.scope == SovereigntyTab.Constellation:
            systemID = self.locationID
            constellationID = sm.GetService('map').GetParent(systemID)
            regionID = sm.GetService('map').GetParent(constellationID)
        if self.scope == SovereigntyTab.Region:
            constellationID = self.locationID
            regionID = sm.GetService('map').GetParent(constellationID)
        if self.scope == SovereigntyTab.World:
            regionID = self.locationID
        location = (systemID, constellationID, regionID)
        sm.GetService('sov').GetSovOverview(location)


class FWHeaderEntry(uicontrols.SE_BaseClassCore):
    """
    This class is for FW system header entries in sov dashboard
    """
    __guid__ = 'listentry.FWHeaderEntry'

    def ApplyAttributes(self, attributes):
        uicontrols.SE_BaseClassCore.ApplyAttributes(self, attributes)
        uiprimitives.Line(parent=self, align=uiconst.TOBOTTOM, color=uiconst.ENTRY_LINE_COLOR)
        self.container = uiprimitives.Container(name='container', parent=self)
        self.upgrades = uiprimitives.Container(name='upgrades', parent=self, align=uiconst.TORIGHT, pos=(0,
         0,
         280,
         0), padRight=8)
        self.system = uiprimitives.Container(name='solarsystem', parent=self, padLeft=4, padRight=4, clipChildren=True)
        self.systemHeader = uicontrols.EveLabelSmall(text='', parent=self.system, left=0, top=4, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0, maxLines=1)
        self.upgradesHeader = uicontrols.EveLabelSmall(text='', parent=self.upgrades, left=0, top=4, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0, maxLines=1)

    def Load(self, node):
        self.systemHeader.text = node.systemHeader
        self.upgradesHeader.text = node.upgradesHeader


class UpgradeEntry(uicontrols.SE_BaseClassCore):
    """
    This class is for upgrade entries in sov dashboard
    """
    __guid__ = 'listentry.UpgradeEntry'

    def ApplyAttributes(self, attributes):
        uicontrols.SE_BaseClassCore.ApplyAttributes(self, attributes)
        uiprimitives.Line(parent=self, align=uiconst.TOBOTTOM, color=uiconst.ENTRY_LINE_COLOR)
        self.container = uiprimitives.Container(name='container', parent=self)
        self.system = uiprimitives.Container(name='solarsystem', parent=self)
        self.upgrades = uiprimitives.Container(name='upgrades', parent=self, align=uiconst.TORIGHT, pos=(0,
         0,
         280,
         10), padding=(0, 3, 8, 4))
        self.location = uicontrols.EveLabelMedium(text='', parent=self.system, left=6, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0, maxLines=1)
        self.upgradeBars = []
        uicontrols.Frame(bgParent=self.upgrades, color=COLOR)
        barCont = uiprimitives.Container(parent=self.upgrades, padding=1)
        for i in xrange(5):
            f = uiprimitives.Fill(parent=barCont, name='upgrades%d' % i, align=uiconst.TOLEFT_PROP, color=COLOR, width=0.2, padding=1)
            self.upgradeBars.append(f)

    def Load(self, node):
        self.location.text = node.label
        self.locationID = node.locationID
        self.scope = node.scope
        self.DrawLevels(self.upgradeBars, const.attributeDevIndexUpgrade, node.upgradePoints)

    def DrawLevels(self, bars, indexID = None, value = None):
        indexInfo = sm.GetService('sov').GetIndexLevel(value, indexID)
        level = indexInfo.level
        for i in xrange(5):
            fill = bars[i]
            if level > i:
                fill.state = uiconst.UI_DISABLED
                fill.color.SetRGB(1.0, 1.0, 1.0, 0.5)
                fill.width = 0.2
            elif level == i and indexInfo.remainder:
                fill.state = uiconst.UI_DISABLED
                fill.color.SetRGB(0.5, 0.5, 0.5, 0.5)
                fill.width = 0.2 * (1.0 - indexInfo.remainder)
            else:
                fill.state = uiconst.UI_HIDDEN

    def OnDblClick(self, *args):
        if self.scope != SovereigntyTab.SolarSystem:
            self.DrillToLocation()

    def GetMenu(self):
        m = []
        mm = []
        if self.locationID:
            label = ''
            if self.scope == SovereigntyTab.SolarSystem:
                label = None
                mm += sm.GetService('menu').CelestialMenu(self.locationID)
                m.append((uiutil.MenuLabel('UI/Common/LocationTypes/System'), mm))
            if self.scope == SovereigntyTab.World:
                label = uiutil.MenuLabel('UI/Common/LocationTypes/Region')
                mm += sm.GetService('menu').CelestialMenu(self.locationID)
                m.append((label, mm))
            elif self.scope == SovereigntyTab.Region:
                label = uiutil.MenuLabel('UI/Common/LocationTypes/Constellation')
                mm += sm.GetService('menu').CelestialMenu(self.locationID)
                m.append((label, mm))
            elif self.scope == SovereigntyTab.Constellation:
                label = uiutil.MenuLabel('UI/Common/LocationTypes/System')
                mm += sm.GetService('menu').CelestialMenu(self.locationID)
                m.append((label, mm))
            m.append(None)
            if label is not None:
                if label == uiutil.MenuLabel('UI/Common/LocationTypes/System'):
                    viewLabel = 'UI/Common/LocationTypes/ViewSystem'
                elif label == uiutil.MenuLabel('UI/Common/LocationTypes/Constellation'):
                    viewLabel = 'UI/Common/LocationTypes/ViewConstellation'
                else:
                    viewLabel = 'UI/Common/LocationTypes/ViewRegion'
                m.append([viewLabel, self.DrillToLocation])
            return m
        else:
            return

    def DrillToLocation(self):
        systemID = None
        constellationID = None
        regionID = None
        if self.scope == SovereigntyTab.Constellation:
            systemID = self.locationID
            constellationID = sm.GetService('map').GetParent(systemID)
            regionID = sm.GetService('map').GetParent(constellationID)
        if self.scope == SovereigntyTab.Region:
            constellationID = self.locationID
            regionID = sm.GetService('map').GetParent(constellationID)
        if self.scope == SovereigntyTab.World:
            regionID = self.locationID
        location = (systemID, constellationID, regionID)
        sm.GetService('sov').GetSovOverview(location)
