#Embedded file name: eve/client/script/ui/station/medical\cloneStation.py
import blue
import uicls
import uthread
import functools
import uicontrols
import uiprimitives
import localization
import carbonui.const as uiconst
from carbonui.uicore import uicorebase as uicore
from carbonui.util.color import Color

class CloneStationWindow(uicontrols.Window):
    """
    Clone station window for updating which station a characters medical clone
    is located in. This can be used to remotely set the station but on a limited
    per character cooldown.
    
    This window and functionality can only be accessed while docked in a station.
    """
    __guid__ = 'form.CloneStationWindow'
    __notifyevents__ = ['OnSessionChanged']
    default_width = 600
    default_height = 100
    default_windowID = 'CloneStationWindow'
    default_topParentHeight = 0
    default_clipChildren = True
    default_isPinable = False
    LINE_COLOR = (1, 1, 1, 0.2)
    BLUE_COLOR = (0.0, 0.54, 0.8, 1.0)
    GREEN_COLOR = (0.0, 1.0, 0.0, 0.8)
    GRAY_COLOR = Color.GRAY5
    PADDING = 15

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.Layout()
        uthread.new(self.Reload)

    def Layout(self):
        """
        Setup UI controls for this window.
        """
        self.MakeUnMinimizable()
        self.HideHeader()
        self.MakeUnResizeable()
        self.container = uicontrols.ContainerAutoSize(parent=self.GetMainArea(), align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, padding=(self.PADDING,
         self.PADDING,
         self.PADDING,
         self.PADDING), callback=self.OnContainerResized)
        uicontrols.EveLabelLargeBold(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Medical/Clone/HomeStation'))
        uicontrols.EveLabelMedium(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Medical/Clone/HomeStationDescription'), color=self.GRAY_COLOR, padding=(0, 0, 0, 15))
        uiprimitives.Line(parent=self.container, align=uiconst.TOTOP, color=self.LINE_COLOR)
        self.local = uicontrols.ContainerAutoSize(parent=self.container, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN)
        self.remoteTitle = uicontrols.EveLabelLargeBold(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Medical/Clone/CorporationOffices'), padding=(0, 15, 0, 0))
        self.remoteText = uicontrols.EveLabelMedium(parent=self.container, align=uiconst.TOTOP, text=localization.GetByLabel('UI/Medical/Clone/CorporationOfficesDescription'), color=self.GRAY_COLOR, padding=(0, 0, 0, 0))
        self.remoteTimer = uicontrols.EveLabelMedium(parent=self.container, align=uiconst.TOTOP, text='', color=self.GRAY_COLOR, padding=(0, 0, 0, 15))
        self.remote = uicls.ScrollContainer(parent=self.container, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN)
        self.closeButton = uicontrols.Button(parent=self.container, label=localization.GetByLabel('UI/Generic/Cancel'), func=self.Close, align=uiconst.TOTOP, fontsize=13, padding=(220, 10, 220, 0))
        uicore.animations.FadeTo(self.container, startVal=0.0, endVal=1.0, duration=0.5)

    def OnSessionChanged(self, *args):
        self.Close()

    def OnContainerResized(self):
        """
        Callback for the parent auto resized container, we set the overall window height
        to fit the contents of the resizeable container here. This allows localized text
        to wrap around and push out the height of this window.
        """
        self.width = self.default_width
        self.height = self.container.height + self.PADDING * 2

    def Reload(self):
        """
        Refetch data and update the state of the window.
        """
        if self.destroyed:
            return
        self.local.DisableAutoSize()
        self.local.Flush()
        self.remote.Flush()
        self.homeStationID = sm.RemoteSvc('charMgr').GetHomeStation()
        stations, remoteStationDate = sm.GetService('corp').GetCorpStationManager().GetPotentialHomeStations()
        hasRemote = bool(len([ s for s in stations if s.isRemote ]))
        if hasRemote:
            self.remoteTitle.state = uiconst.UI_DISABLED
            self.remoteText.state = uiconst.UI_DISABLED
            self.remoteTimer.state = uiconst.UI_DISABLED
            if remoteStationDate and remoteStationDate > blue.os.GetWallclockTime():
                self.remote.state = uiconst.UI_DISABLED
                self.remote.opacity = 0.2
                self.remoteTimer.text = localization.GetByLabel('UI/Medical/Clone/NextRemoteChangeDate', nextDate=remoteStationDate)
            else:
                self.remote.state = uiconst.UI_PICKCHILDREN
                self.remote.opacity = 1.0
                self.remoteTimer.text = localization.GetByLabel('UI/Medical/Clone/NextRemoteChangeNow')
        else:
            self.remoteTitle.state = uiconst.UI_HIDDEN
            self.remoteText.state = uiconst.UI_HIDDEN
            self.remote.state = uiconst.UI_HIDDEN
            self.remoteTimer.state = uiconst.UI_HIDDEN
        uiprimitives.Line(parent=self.remote, align=uiconst.TOTOP, color=self.LINE_COLOR)
        for station in stations:
            self.AddStation(station.stationID, station.typeID, station.serviceMask, station.isRemote)

        self.remote.height = min(self.remote.mainCont.height + 45, 305)
        self.local.EnableAutoSize()

    def AddStation(self, stationID, typeID, serviceMask, isRemote):
        station = cfg.stations.Get(stationID)
        if isRemote:
            if stationID == session.hqID:
                title = localization.GetByLabel('UI/Medical/Clone/CorporationHeadquarters')
            else:
                title = localization.GetByLabel('UI/Medical/Clone/CorporationOffice')
            parent = self.remote
            color = self.BLUE_COLOR
        else:
            if stationID == session.stationid2:
                title = localization.GetByLabel('UI/Medical/Clone/ThisStation')
            else:
                title = localization.GetByLabel('UI/Medical/Clone/SchoolHeadquarters')
            parent = self.local
            color = self.GREEN_COLOR
        container = uicontrols.ContainerAutoSize(parent=parent, align=uiconst.TOTOP, alignMode=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, bgColor=(0.2, 0.2, 0.2, 0.3))
        container.DisableAutoSize()
        label = "<url=showinfo:%d//%d alt='%s'>%s</url>" % (station.stationTypeID,
         station.stationID,
         title,
         station.stationName)
        uicontrols.EveLabelMediumBold(parent=container, align=uiconst.TOTOP, text=title, padding=(7, 5, 0, 0), color=color)
        uicontrols.EveLabelMediumBold(parent=container, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, text=label, padding=(7, 0, 140, 5))
        if station.stationID != self.homeStationID:
            uicontrols.Button(parent=container, label=localization.GetByLabel('UI/Medical/Clone/SetHomeStationButton'), align=uiconst.CENTERRIGHT, fontsize=13, fixedwidth=140, fixedheight=30, pos=(5, 0, 0, 0), func=functools.partial(CloneStationWindow.SetStation, station.stationID, serviceMask, isRemote))
        else:
            uicontrols.EveLabelMediumBold(parent=container, align=uiconst.CENTERRIGHT, text=localization.GetByLabel('UI/Medical/Clone/CurrentHomeStation'), padding=(-15, 0, 0, 0))
        uiprimitives.Line(parent=parent, align=uiconst.TOTOP, color=self.LINE_COLOR)
        container.EnableAutoSize()

    @classmethod
    def SetStation(cls, stationID, *args):
        """
        Performs the work of setting a characters home station. This is a class method so we can have
        context menus call the same validation and remote call code without needing to open the UI.
        """
        if not session.stationid2:
            raise UserError('MustBeDocked')
        stations, remoteStationDate = sm.GetService('corp').GetCorpStationManager().GetPotentialHomeStations()
        try:
            station = next((station for station in stations if station.stationID == stationID))
        except StopIteration:
            raise UserError('InvalidHomeStation')

        if station.stationID == sm.RemoteSvc('charMgr').GetHomeStation():
            raise UserError('MedicalYouAlreadyHaveACloneContractAtThatStation')
        if station.isRemote and remoteStationDate is not None and remoteStationDate > blue.os.GetWallclockTime():
            raise UserError('HomeStationRemoteCooldown', {'nextDate': remoteStationDate})
        if station.isRemote:
            if eve.Message('AskAcceptRemoteCloneContractCost', {'cost': const.costCloneContract}, uiconst.YESNO) != uiconst.ID_YES:
                return
        elif eve.Message('AskAcceptCloneContractCost', {'cost': const.costCloneContract}, uiconst.YESNO) != uiconst.ID_YES:
            return
        if not session.stationid2:
            raise UserError('MustBeDocked')
        try:
            sm.GetService('corp').GetCorpStationManager().SetHomeStation(stationID)
        finally:
            CloneStationWindow.CloseIfOpen()

        sm.GetService('objectCaching').InvalidateCachedMethodCall('charMgr', 'GetHomeStation')
