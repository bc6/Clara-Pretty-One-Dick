#Embedded file name: initialloadingscreen\loadingscreen.py
import blue
import trinity
import random
import uthread2

class InitialLoadingScreen(object):

    def __init__(self):
        self.active = False

    def Show(self, width = 800, height = 600):
        displayMode = trinity.adapters.GetCurrentDisplayMode(0)
        trinity.app.width = width
        trinity.app.height = height
        trinity.app.left = (displayMode.width - trinity.app.width) / 2
        trinity.app.top = (displayMode.height - trinity.app.height) / 2
        trinity.app.windowed = True
        trinity.app.AdjustWindowForChange(True, True)
        trinity.app.Create()
        pp = {'BackBufferWidth': trinity.app.width,
         'BackBufferHeight': trinity.app.height,
         'Windowed': True,
         'EnableAutoDepthStencil': True,
         'AutoDepthStencilFormat': trinity.DEPTH_STENCIL_FORMAT.D24S8,
         'BackBufferFormat': trinity.PIXEL_FORMAT.B8G8R8A8_UNORM,
         'PresentationInterval': trinity.PRESENT_INTERVAL.IMMEDIATE}
        trinity.app.ChangeDevice(0, 0, 0, pp)
        self.renderjob = trinity.CreateRenderJob('LoadingScreen')
        scene = trinity.Tr2Sprite2dScene()
        scene.isFullscreen = True
        scene.clearBackground = True
        scene.backgroundColor = (0, 0, 0, 0)
        self.renderjob.Update(scene)
        self.renderjob.RenderScene(scene)
        self.renderjob.ScheduleRecurring()
        sprite = trinity.Tr2Sprite2d()
        sprite.displayWidth = 32
        sprite.displayHeight = 32
        sprite.spriteEffect = trinity.TR2_SFX_FILL
        sprite.color = (1, 1, 1, 1)
        scene.children.append(sprite)

        def loading_screen():
            x = 100
            dx = 4
            y = height * 2 / 3
            while self.active:
                sprite.displayX = x
                sprite.displayY = y
                x += dx
                if x > width - 100 - sprite.displayWidth:
                    dx = -dx
                if x < 100:
                    dx = -dx
                blue.synchro.Yield()

        self.active = True
        uthread2.StartTasklet(loading_screen)
        blue.os.Pump()
        blue.os.Pump()
        blue.os.Pump()

    def Hide(self):
        self.active = False
        self.renderjob.UnscheduleRecurring()
        self.renderjob = None
