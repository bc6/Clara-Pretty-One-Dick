#Embedded file name: eve/client/script/ui/shared/fleet\fleetbroadcast.py
"""
The fleet broadcast view in the tactical panel.
Fleet broadcasts are shown in other places too (inflight brackets, overview, etc.). 
Those are not handled here.
"""
import blue
from eve.client.script.ui.control import entries as listentry
import uicontrols
import uix
import uiutil
import uthread
import util
import fleetbr
import math
import form
from fleetcommon import *
import carbonui.const as uiconst
import localization
from carbonui.primitives.container import Container
from carbonui.primitives.frame import Frame
from carbonui.primitives.fill import Fill
from carbonui.primitives.layoutGrid import LayoutGrid
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.colorPanel import ColorPanel

class FleetBroadcastView(Container):
    __guid__ = 'form.FleetBroadcastView'
    __notifyevents__ = ['OnFleetBroadcast_Local',
     'OnSpeakingEvent_Local',
     'OnFleetLootEvent_Local',
     'OnFleetBroadcastFilterChange',
     'OnFleetJoin_Local',
     'OnFleetLeave_Local',
     'OnFleetMemberChanged_Local']

    def PostStartup(self):
        sm.RegisterNotify(self)
        self.sr.broadcastHistory = []
        self.broadcastMenuItems = []
        header = self
        header.baseHeight = header.height
        self.panelHistory = Container(name='panelHistory', parent=self, left=const.defaultPadding, width=const.defaultPadding, top=const.defaultPadding, height=const.defaultPadding)
        historyType = settings.user.ui.Get('fleetHistoryFilter', 'all')
        comboPar = Container(parent=self.panelHistory, align=uiconst.TOTOP, height=36)
        ops = [(localization.GetByLabel('UI/Common/All'), 'all'),
         (localization.GetByLabel('UI/Fleet/FleetBroadcast/BroadcastHistory'), 'broadcasthistory'),
         (localization.GetByLabel('UI/Fleet/FleetBroadcast/VoiceHistory'), 'voicehistory'),
         (localization.GetByLabel('UI/Fleet/FleetBroadcast/MemberHistory'), 'memberhistory'),
         (localization.GetByLabel('UI/Fleet/FleetBroadcast/LootHistory'), 'loothistory')]
        self.combo = uicontrols.Combo(label=localization.GetByLabel('UI/Fleet/FleetBroadcast/Filters'), parent=comboPar, options=ops, name='filter', select=historyType, callback=self.LoadHistory, pos=(0, 12, 0, 0), width=110)
        self.clearBtn = uicontrols.Button(parent=comboPar, label=localization.GetByLabel('UI/Fleet/FleetBroadcast/ClearHistory'), func=self.OnClear, align=uiconst.BOTTOMRIGHT, top=const.defaultPadding)
        self.scrollHistory = uicontrols.Scroll(name='allHistoryScroll', parent=self.panelHistory, align=uiconst.TOALL)

    def ClearHistory(self, args):
        fleetSvc = sm.GetService('fleet')
        if args == 'broadcasthistory':
            fleetSvc.broadcastHistory = []
        elif args == 'voicehistory':
            fleetSvc.voiceHistory = []
        elif args == 'loothistory':
            fleetSvc.lootHistory = []
        elif args == 'memberhistory':
            fleetSvc.memberHistory = []
        elif args == 'all':
            fleetSvc.broadcastHistory = []
            fleetSvc.voiceHistory = []
            fleetSvc.lootHistory = []
            fleetSvc.memberHistory = []
        self.LoadHistory(self.combo, '', args)

    def Load(self, args):
        if not self.sr.Get('inited', 0):
            self.PostStartup()
            setattr(self.sr, 'inited', 1)
        self.LoadHistory(self.combo, '', self.combo.selectedValue)

    def LoadHistory(self, combo, label, value, *args):
        scrolllist = []
        headers = []
        hint = ''
        sp = self.scrollHistory.GetScrollProportion()
        self.scrollHistory.multiSelect = 1
        self.scrollHistory.OnChar = self.OnScrollHistoryChar
        if value == 'broadcasthistory':
            scrolllist, hint = self.LoadBroadcastHistory()
            self.scrollHistory.multiSelect = 0
            self.scrollHistory.OnChar = self.OnScrollBroadcastChar
        elif value == 'voicehistory':
            scrolllist, hint = self.LoadVoiceHistory()
        elif value == 'loothistory':
            scrolllist, hint = self.LoadLootHistory()
        elif value == 'memberhistory':
            scrolllist, hint = self.LoadMemberHistory()
        else:
            scrolllist, hint = self.LoadAllHistory()
        settings.user.ui.Set('fleetHistoryFilter', value)
        self.scrollHistory.Load(contentList=scrolllist, scrollTo=sp, headers=[], noContentHint=hint)

    def LoadAllHistory(self):
        allHistory = []
        broadcastHistory, hint = self.LoadBroadcastHistory()
        memberHistory, hint = self.LoadMemberHistory()
        voiceHistory, hint = self.LoadVoiceHistory()
        lootHistory, hint = self.LoadLootHistory()
        allHistory.extend(broadcastHistory)
        allHistory.extend(memberHistory)
        allHistory.extend(voiceHistory)
        allHistory.extend(lootHistory)
        allHistory.sort(key=lambda x: x.time, reverse=True)
        hint = localization.GetByLabel('UI/Fleet/FleetBroadcast/NoEventsYet')
        return (allHistory, hint)

    def LoadBroadcastHistory(self):
        scrolllist = []
        broadcastHistory = sm.GetService('fleet').GetBroadcastHistory()
        for kv in broadcastHistory:
            data = self.GetBroadcastListEntry(kv)
            data.Set('sort_%s' % localization.GetByLabel('UI/Common/DateWords/Time'), kv.time)
            data.time = kv.time
            data.OnClick = self.OnBroadcastClick
            scrolllist.append(listentry.Get(entryType=None, data=data, decoClass=BroadcastEntry))

        hint = localization.GetByLabel('UI/Fleet/FleetBroadcast/NoEventsYet')
        return (scrolllist, hint)

    def OnBroadcastClick(self, entry):
        data = entry.sr.node.data
        itemID = data.itemID
        if data.itemID == session.shipid or session.shipid is None or data.itemID is None or util.IsUniverseCelestial(data.itemID):
            return
        sm.GetService('menu').TacticalItemClicked(itemID)

    def LoadVoiceHistory(self):
        scrolllist = []
        voiceHistory = sm.GetService('fleet').GetVoiceHistory()
        for data in voiceHistory:
            data2 = self.GetVoiceListEntry(data)
            data2.Set('sort_%s' % localization.GetByLabel('UI/Common/DateWords/Time'), data.time)
            data2.time = data.time
            scrolllist.append(listentry.Get('Generic', data=data2))

        hint = localization.GetByLabel('UI/Fleet/FleetBroadcast/NoEventsYet')
        return (scrolllist, hint)

    def LoadLootHistory(self):
        scrolllist = []
        lootHistory = sm.GetService('fleet').GetLootHistory()
        for kv in lootHistory:
            label = localization.GetByLabel('UI/Fleet/FleetBroadcast/BroadcastEventLoot', time=kv.time, charID=kv.charID, item=kv.typeID, itemQuantity=kv.quantity)
            data = util.KeyVal(charID=kv.charID, label=label, GetMenu=self.GetLootMenu, data=kv)
            data.Set('sort_%s' % localization.GetByLabel('UI/Common/DateWords/Time'), kv.time)
            data.time = kv.time
            scrolllist.append(listentry.Get('Generic', data=data))

        hint = localization.GetByLabel('UI/Fleet/FleetBroadcast/NoEventsYet')
        return (scrolllist, hint)

    def LoadMemberHistory(self):
        scrolllist = []
        memberHistory = sm.GetService('fleet').GetMemberHistory()
        for kv in memberHistory:
            label = localization.GetByLabel('UI/Fleet/FleetBroadcast/Event', time=kv.time, eventLabel=kv.event)
            data = util.KeyVal(charID=kv.charID, label=label, GetMenu=self.GetMemberMenu, data=kv)
            data.Set('sort_%s' % localization.GetByLabel('UI/Common/DateWords/Time'), kv.time)
            data.time = kv.time
            scrolllist.append(listentry.Get('Generic', data=data))

        hint = localization.GetByLabel('UI/Fleet/FleetBroadcast/NoEventsYet')
        return (scrolllist, hint)

    def OpenSettings(self):
        form.BroadcastSettings.Open()

    def OnClear(self, *args):
        selectedValue = self.combo.selectedValue
        self.ClearHistory(selectedValue)

    def OnScrollHistoryChar(self, *args):
        """
        Needed to get regular OnChar behaviour if not broadcast history
        """
        uicontrols.ScrollCore.OnChar(self, *args)

    def OnScrollBroadcastChar(self, *args):
        """
        Needed for combat shortcuts to work while focus is on the scroll
        """
        return False

    def GetBroadcastListEntry(self, data):
        label = localization.GetByLabel('UI/Fleet/FleetBroadcast/Event', time=data.time, eventLabel=data.broadcastLabel)
        colorcoded = settings.user.ui.Get('fleet_broadcastcolor_%s' % data.name, None)
        data2 = util.KeyVal(charID=data.charID, label=label, GetMenu=self.GetBroadcastMenu, data=data, colorcoded=colorcoded)
        return data2

    def GetVoiceListEntry(self, data):
        eventText = localization.GetByLabel('UI/Fleet/FleetBroadcast/BroadcastEventSpeaking', charID=data.charID, channelName=data.channelName)
        label = localization.GetByLabel('UI/Fleet/FleetBroadcast/Event', time=data.time, eventLabel=eventText)
        data2 = util.KeyVal(channel=data.channelID, charID=data.charID, label=label, GetMenu=fleetbr.GetVoiceMenu)
        return data2

    def OnSpeakingEvent_Local(self, data):
        selectedValue = self.combo.selectedValue
        if selectedValue in ('voicehistory', 'all'):
            self.LoadHistory(self.combo, '', selectedValue)

    def OnFleetLootEvent_Local(self):
        selectedValue = self.combo.selectedValue
        if selectedValue in ('loothistory', 'all'):
            self.LoadHistory(self.combo, '', selectedValue)

    def OnFleetJoin_Local(self, rec):
        selectedValue = self.combo.selectedValue
        if selectedValue in ('memberhistory', 'all'):
            self.LoadHistory(self.combo, '', selectedValue)

    def OnFleetLeave_Local(self, rec):
        selectedValue = self.combo.selectedValue
        if selectedValue in ('memberhistory', 'all'):
            self.LoadHistory(self.combo, '', selectedValue)

    def OnFleetMemberChanged_Local(self, *args):
        selectedValue = self.combo.selectedValue
        if selectedValue in ('memberhistory', 'all'):
            self.LoadHistory(self.combo, '', selectedValue)

    def GetBroadcastMenu(self, entry):
        m = []
        data = entry.sr.node.data
        func = getattr(fleetbr, 'GetMenu_%s' % data.name, None)
        if func:
            m = func(data.charID, data.solarSystemID, data.itemID)
            m += [None]
        m += fleetbr.GetMenu_Member(data.charID)
        m += [None]
        m += fleetbr.GetMenu_Ignore(data.name)
        return m

    def GetLootMenu(self, entry):
        m = []
        data = entry.sr.node.data
        m += sm.GetService('menu').GetMenuFormItemIDTypeID(None, data.typeID, ignoreMarketDetails=0)
        m += [None]
        m += fleetbr.GetMenu_Member(data.charID)
        return m

    def GetMemberMenu(self, entry):
        m = []
        data = entry.sr.node.data
        m += fleetbr.GetMenu_Member(data.charID)
        return m

    def OnFleetBroadcast_Local(self, broadcast):
        self.RefreshBroadcastHistory()

    def OnFleetBroadcastFilterChange(self):
        self.RefreshBroadcastHistory()

    def RefreshBroadcastHistory(self):
        selectedValue = self.combo.selectedValue
        if selectedValue in ('broadcasthistory', 'all'):
            self.LoadHistory(self.combo, '', selectedValue)


def CopyFunctions(class_, locals):
    for name, fn in class_.__dict__.iteritems():
        if type(fn) is type(CopyFunctions):
            if name in locals:
                raise RuntimeError, 'What are you trying to do here?'
            locals[name] = fn


class BroadcastSettings(uicontrols.Window):
    __guid__ = 'form.BroadcastSettings'
    default_windowID = 'broadcastsettings'
    default_width = 320

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.scope = 'all'
        self.SetCaption(localization.GetByLabel('UI/Fleet/FleetBroadcast/BroadcastSettings'))
        self.SetMinSize([300, 200])
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.sr.main.left = self.sr.main.width = self.sr.main.top = self.sr.main.height = const.defaultPadding
        uicontrols.EveLabelMedium(text=localization.GetByLabel('UI/Fleet/FleetBroadcast/BroadcastSettingsHelp'), parent=self.sr.main, align=uiconst.TOTOP, left=20, state=uiconst.UI_NORMAL)
        Container(name='push', parent=self.sr.main, align=uiconst.TOTOP, height=6)
        self.sr.scrollBroadcasts = uicontrols.Scroll(name='scrollBroadcasts', parent=self.sr.main)
        self.sr.scrollBroadcasts.multiSelect = 0
        self.LoadFilters()

    def LoadFilters(self):
        scrolllist = []
        history = sm.GetService('fleet').broadcastHistory
        for name, labelName in fleetbr.broadcastNames.iteritems():
            data = util.KeyVal()
            if name == 'Event':
                rngName = ''
            else:
                rng = fleetbr.GetBroadcastWhere(name)
                rngName = fleetbr.GetBroadcastWhereName(rng)
            n = len([ b for b in history if b.name == name or name == 'Event' and b.name not in fleetbr.types.keys() ])
            data.label = localization.GetByLabel(labelName)
            data.props = None
            data.checked = bool(settings.user.ui.Get('listenBroadcast_%s' % name, True))
            data.cfgname = name
            data.retval = None
            data.hint = '%s:<br>%s' % (localization.GetByLabel('UI/Fleet/FleetBroadcast/RecipientRange'), rngName)
            data.colorcoded = settings.user.ui.Get('fleet_broadcastcolor_%s' % name, None)
            data.OnChange = self.Filter_OnCheckBoxChange
            scrolllist.append(listentry.Get(entryType=None, data=data, decoClass=BroadcastSettingsEntry))

        self.sr.scrollBroadcasts.sr.id = 'scrollBroadcasts'
        self.sr.scrollBroadcasts.Load(contentList=scrolllist)

    def Filter_OnCheckBoxChange(self, cb):
        sm.GetService('fleet').SetListenBroadcast(cb.data['key'], cb.checked)


class BroadcastSettingsEntry(listentry.Checkbox):
    colorList = [(1.0, 0.7, 0.0),
     (1.0, 0.35, 0.0),
     (0.75, 0.0, 0.0),
     (0.1, 0.6, 0.1),
     (0.0, 0.63, 0.57),
     (0.2, 0.5, 1.0),
     (0.0, 0.15, 0.6),
     (0.0, 0.0, 0.0),
     (0.7, 0.7, 0.7)]

    def Startup(self, *args):
        listentry.Checkbox.Startup(self, *args)
        colorPicker = Container(parent=self, pos=(0, 0, 27, 20), name='colorPicker', state=uiconst.UI_NORMAL, align=uiconst.CENTERRIGHT, idx=0)
        arrow = Sprite(parent=colorPicker, pos=(0, 0, 16, 16), name='arrow', align=uiconst.CENTERRIGHT, texturePath='res:/ui/texture/icons/38_16_229.png', color=(1, 1, 1, 0.5), state=uiconst.UI_DISABLED)
        self.colorCont = Container(parent=colorPicker, name='colorCont', pos=(2, 0, 10, 10), align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED)
        Frame(parent=self.colorCont, name='colorFrame', color=(1, 1, 1, 0.2))
        self.colorFill = Fill(parent=self.colorCont, color=(0, 0, 0, 0))
        colorPicker.LoadTooltipPanel = self.LoadColorTooltipPanel
        colorPicker.GetTooltipPointer = self.GetColorTooltipPointer
        colorPicker.GetTooltipDelay = self.GetTooltipDelay

    def Load(self, node):
        listentry.Checkbox.Load(self, node)
        if node.colorcoded:
            fillColor = node.colorcoded + (1,)
            self.colorFill.SetRGBA(*fillColor)

    def GetColorTooltipPointer(self):
        return uiconst.POINT_LEFT_2

    def GetTooltipDelay(self):
        return 50

    def LoadColorTooltipPanel(self, tooltipPanel, *args):
        currentColor = self.sr.node.colorcoded
        tooltipPanel.state = uiconst.UI_NORMAL
        tooltipPanel.margin = (2, 2, 2, 2)

        def SetBroadcastTypeColorFromPanel(color):
            self.SetBroadcastTypeColor(color, tooltipPanel)

        colorPanel = ColorPanel(callback=SetBroadcastTypeColorFromPanel, currentColor=currentColor, colorList=self.colorList)
        tooltipPanel.AddLabelSmall(text=localization.GetByLabel('UI/Mail/Select Color'))
        tooltipPanel.AddCell(cellObject=colorPanel)

    def SetBroadcastTypeColor(self, color, tooltipPanel):
        settings.user.ui.Set('fleet_broadcastcolor_%s' % self.sr.node.cfgname, color)
        if color:
            self.colorFill.SetRGB(*color)
            self.colorFill.display = True
        else:
            self.colorFill.display = False
        self.sr.node.colorcoded = color
        sm.ScatterEvent('OnFleetBroadcastFilterChange')
        tooltipPanel.Close()

    def _OnResize(self):
        w, h = self.GetAbsoluteSize()
        availableWidth = w - self.sr.label.left - self.colorCont.width - 10
        textwidth = self.sr.label.textwidth
        if textwidth > availableWidth:
            fadeEnd = availableWidth
            self.sr.label.SetRightAlphaFade(fadeEnd, maxFadeWidth=20)
        else:
            self.sr.label.SetRightAlphaFade(0, maxFadeWidth=0)


class BroadcastEntry(listentry.Generic):

    def Startup(self, *args):
        listentry.Generic.Startup(self, *args)
        self.colorcodedFill = Fill(bgParent=self, color=(0, 0, 0, 0))

    def Load(self, node):
        listentry.Generic.Load(self, node)
        if node.colorcoded:
            fillColor = node.colorcoded + (0.25,)
            self.colorcodedFill.SetRGB(*fillColor)
