#Embedded file name: eve/devtools/script\svc_cameratools.py
import blue
import uthread
import service
import carbonui.const as uiconst
import uiprimitives
import uicontrols
CAMERA_FILENAME = 'c:\\temp\\camera.txt'

class InsiderCameraToolsWindow(uicontrols.Window):
    default_windowID = 'cameratools'


class InsiderCameraTools(service.Service):
    __module__ = __name__
    __exportedcalls__ = {}
    __notifyevents__ = ['ProcessRestartUI', 'Update']
    __dependencies__ = []
    __guid__ = 'svc.cameraTools'
    __servicename__ = 'cameraTools'
    __displayname__ = 'cameraTools'
    __neocommenuitem__ = (('Camera Tools', None), 'Show', service.ROLE_GML)
    __update_on_reload__ = 1

    def Run(self, memStream = None):
        self.wnd = None

    def Stop(self, memStream = None):
        self.Hide()
        service.Service.Stop(self, memStream)

    def Show(self):
        if self.wnd and 0:
            self.wnd.Maximize()
            return
        self.wnd = wnd = InsiderCameraToolsWindow.Open()
        self.wnd.SetWndIcon('41_13')
        self.wnd.SetTopparentHeight(0)
        self.wnd.SetCaption('Camera Tools')
        self.wnd.SetMinSize([180, 110])
        self.width = 180
        self.height = 110
        maincont = uiprimitives.Container(name='maincont', parent=wnd.sr.main, pos=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.saveBtn = uicontrols.Button(parent=maincont, name=u'SaveCamera', label=u'Save Camera orientation', pos=(45, 15, 0, 0), func=self.SaveCamera, align=uiconst.TOPLEFT)
        self.loadBtn = uicontrols.Button(parent=maincont, name=u'LoadCamera', label=u'Load Camera orientation', pos=(45, 45, 0, 0), func=self.LoadCamera, align=uiconst.TOPLEFT)
        self.edit = uicontrols.SinglelineEdit(name='edit', parent=maincont, pos=(45, 75, 140, 20), align=uiconst.TOPLEFT)
        try:
            f = open(CAMERA_FILENAME, 'r')
            f.close()
        except:
            self.loadBtn.state = uiconst.UI_DISABLED

        uthread.new(self.UpdateCameraInfo)

    def UpdateCameraInfo(self):
        while self.wnd and not self.wnd.destroyed:
            cameraInfo = self.GetCameraInfo()
            self.edit.SetText(cameraInfo)
            blue.pyos.synchro.SleepWallclock(1000)

    def Hide(self, *args):
        if self.wnd:
            self.wnd = None

    def ProcessRestartUI(self):
        if self.wnd:
            self.Hide()
            self.Show()

    def GetCameraInfo(self):
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        return '%.2f, %.3f, %.3f' % (camera.translationFromParent, camera.yaw, camera.pitch)

    def Load(self, key, *args):
        pass

    def Update(self, *args):
        pass

    def LoadCamera(self, *args):
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        viewSvc = sm.GetService('viewState')
        if not viewSvc.IsViewActive('inflight'):
            raise UserError('CustomInfo', {'info': 'You can only use this in space'})
        f = open(CAMERA_FILENAME, 'r')
        lst = f.read().strip().split(',')
        f.close()
        camera.translationFromParent = float(lst[0].strip())
        camera.SetOrbit(float(lst[1].strip()), float(lst[2].strip()))
        eve.Message('CustomNotify', {'notify': 'Camera settings have been loaded from %s' % CAMERA_FILENAME})

    def SaveCamera(self, *args):
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        viewSvc = sm.GetService('viewState')
        if not viewSvc.IsViewActive('inflight'):
            raise UserError('CustomInfo', {'info': 'You can only use this in space'})
        f = open(CAMERA_FILENAME, 'w')
        cameraInfo = self.GetCameraInfo()
        f.write(cameraInfo)
        f.close()
        eve.Message('CustomNotify', {'notify': 'Camera settings have been saved to %s' % CAMERA_FILENAME})
        self.loadBtn.state = uiconst.UI_NORMAL
