#Embedded file name: carbon/client/script/entities/AI\AIDebugClient.py
"""
Debug drawing for AI
"""
import uicls
import carbonui.const as uiconst
import uiprimitives
import uicontrols

class AIDebugWindow(uicontrols.Window):
    """
    Debug window for AI
    """
    __guid__ = 'uicls.AIDebugWindow'
    default_windowID = 'AIDebugWindow'
    default_width = 325
    default_height = 125

    def ApplyAttributes(self, attributes):
        super(uicls.AIDebugWindow, self).ApplyAttributes(attributes)
        self.SetMinSize([self.default_width, self.default_height])
        self.SetCaption('AI Debug Window')
        self.sr.content.padding = 5
        self.perceptionClient = sm.GetService('perceptionClient')
        self.aimingClient = sm.GetService('aimingClient')
        clientContainer = uiprimitives.Container(parent=self.sr.content, align=uiconst.TOLEFT_PROP, width=0.5)
        uiprimitives.Line(parent=clientContainer, align=uiconst.TORIGHT)
        uicontrols.Label(parent=clientContainer, align=uiconst.TOTOP, text='----- CLIENT -----', pos=(0, 0, 0, 0), padding=(5, 5, 5, 5))
        uicontrols.Checkbox(parent=clientContainer, text='Perception', checked=self.perceptionClient.GetPerceptionManager(session.worldspaceid).IsDebugRendering(), callback=self.OnTogglePerception)
        uicontrols.Checkbox(parent=clientContainer, text='Aiming', checked=self.aimingClient.GetAimingManager(session.worldspaceid).IsDebugRendering(), callback=self.OnToggleAiming)
        uicontrols.Button(parent=clientContainer, align=uiconst.CENTERBOTTOM, label='Gaze at Nearest', func=self.GazeNearest, top=6)
        serverContainer = uiprimitives.Container(parent=self.sr.content, align=uiconst.TORIGHT_PROP, width=0.5)
        uicontrols.Label(parent=serverContainer, align=uiconst.TOTOP, text='----- SERVER -----', padding=(5, 5, 5, 5))
        uicontrols.Checkbox(parent=serverContainer, text='Perception', checked=self.perceptionClient.GetPerceptionManager(session.worldspaceid).IsDebugRenderingServer(), callback=self.OnTogglePerceptionServer)
        uicontrols.Checkbox(parent=serverContainer, text='Aiming', checked=self.aimingClient.GetAimingManager(session.worldspaceid).IsDebugRenderingServer(), callback=self.OnToggleAimingServer)
        uicontrols.Button(parent=serverContainer, align=uiconst.CENTERBOTTOM, label='Gaze at Nearest', func=self.GazeNearestServer, top=6)

    def OnTogglePerception(self, checkbox):
        checked = self.perceptionClient.GetPerceptionManager(session.worldspaceid).IsDebugRendering()
        if bool(checkbox.GetValue()) != checked:
            self.perceptionClient.GetPerceptionManager(session.worldspaceid).ToggleDebugRendering()

    def OnToggleAiming(self, checkbox):
        checked = self.aimingClient.GetAimingManager(session.worldspaceid).IsDebugRendering()
        if bool(checkbox.GetValue()) != checked:
            self.aimingClient.GetAimingManager(session.worldspaceid).ToggleDebugRendering()

    def GazeNearest(self, *args):
        self.aimingClient.GetAimingManager(session.worldspaceid).DebugGazeNearest()

    def OnTogglePerceptionServer(self, checkbox):
        if sm.GetService('entityClient').IsClientSideOnly(session.worldspaceid):
            return
        clientSetting = self.perceptionClient.GetPerceptionManager(session.worldspaceid).ToggleDebugRenderingServer()
        sm.RemoteSvc('perceptionServer').SetRenderDebugRequest(clientSetting)

    def OnToggleAimingServer(self, checkbox):
        if sm.GetService('entityClient').IsClientSideOnly(session.worldspaceid):
            return
        clientSetting = self.aimingClient.GetAimingManager(session.worldspaceid).ToggleDebugRenderingServer()
        sm.RemoteSvc('aimingServer').SetRenderDebugRequest(clientSetting)

    def GazeNearestServer(self, *args):
        if sm.GetService('entityClient').IsClientSideOnly(session.worldspaceid):
            return
        sm.RemoteSvc('aimingServer').DebugGazeNearest()
