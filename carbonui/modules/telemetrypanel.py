#Embedded file name: carbonui/modules\telemetrypanel.py
import blue
import trinity
import uthread
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from carbonui.control.window import WindowCoreOverride as Window
from carbonui.control.buttons import ButtonCoreOverride as Button
from carbonui.control.checkbox import CheckboxCoreOverride as Checkbox

class TelemetryPanel(Window):
    __guid__ = 'form.TelemetryPanel'
    default_caption = 'Telemetry Panel'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        if hasattr(self, 'SetTopparentHeight'):
            self.SetTopparentHeight(0)
            self.container = Container(parent=self.sr.main, align=uiconst.TOALL)
        else:
            self.container = Container(parent=self.sr.content, align=uiconst.TOALL)
        from carbonui.primitives.gridcontainer import GridContainer
        self.optionsContainer = Container(parent=self.container, align=uiconst.TOTOP, height=40)
        self.cppCaptureChk = Checkbox(parent=self.optionsContainer, text='C++ capture', checked=blue.statistics.isCppCaptureEnabled, callback=self._OnCppCaptureChk, align=uiconst.TOTOP)
        self.gpuCaptureChk = Checkbox(parent=self.optionsContainer, text='GPU capture', checked=trinity.settings.GetValue('gpuTelemetryEnabled'), callback=self._OnGpuCaptureChk, align=uiconst.TOTOP)
        self.buttonContainer = GridContainer(parent=self.container, align=uiconst.TOALL, columns=2, rows=2)
        self.startBtn = Button(parent=self.buttonContainer, align=uiconst.TOALL, label='Start', func=self._Start)
        self.stopBtn = Button(parent=self.buttonContainer, align=uiconst.TOALL, label='Stop', func=self._Stop)
        self.pauseBtn = Button(parent=self.buttonContainer, align=uiconst.TOALL, label='Pause', func=self._Pause)
        self.resumeBtn = Button(parent=self.buttonContainer, align=uiconst.TOALL, label='Resume', func=self._Resume)
        uthread.new(self._CheckStatus)

    def _OnCppCaptureChk(self, checkbox):
        blue.statistics.isCppCaptureEnabled = checkbox.GetValue()

    def _OnGpuCaptureChk(self, checkbox):
        trinity.settings.SetValue('gpuTelemetryEnabled', checkbox.GetValue())

    def _Start(self, args):
        print 'Starting Telemetry'
        blue.statistics.StartTelemetry('localhost')

    def _Stop(self, args):
        print 'Stopping Telemetry'
        blue.statistics.StopTelemetry()

    def _Pause(self, args):
        print 'Pausing Telemetry'
        blue.statistics.PauseTelemetry()

    def _Resume(self, args):
        print 'Resuming Telemetry'
        blue.statistics.ResumeTelemetry()

    def _CheckStatus(self):
        while not self.destroyed:
            self.cppCaptureChk.SetChecked(blue.statistics.isCppCaptureEnabled, report=False)
            if blue.statistics.isTelemetryConnected:
                self.startBtn.Disable()
                self.stopBtn.Enable()
                if blue.statistics.isTelemetryPaused:
                    self.pauseBtn.Disable()
                    self.resumeBtn.Enable()
                else:
                    self.pauseBtn.Enable()
                    self.resumeBtn.Disable()
            else:
                self.startBtn.Enable()
                self.stopBtn.Disable()
                self.pauseBtn.Disable()
                self.resumeBtn.Disable()
            blue.synchro.SleepWallclock(500)
