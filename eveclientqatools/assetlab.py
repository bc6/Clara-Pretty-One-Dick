#Embedded file name: eveclientqatools\assetlab.py
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.control.buttonGroup import ButtonGroup
import state
import geo2
import util
import math
import carbonui.const as uiconst

def DegToRad(angle):
    return angle * math.pi / 180.0


class AssetLabWindow(Window):
    default_caption = 'Asset Lab'
    default_windowID = 'assetLabWindow'
    default_width = 400
    default_height = 250
    default_topParentHeight = 0
    default_someValue = 10
    default_otherValue = 20

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.yaw = 0.0
        self.pitch = 0.0

        def GetModel():
            selectedID = sm.GetService('state').GetExclState(state.selected)
            ball = sm.GetService('michelle').GetBall(selectedID)
            return getattr(ball, 'model', None)

        def Start():
            self.scene = sm.GetService('space').GetScene()
            self.sunBallCache = self.scene.sunBall
            self.scene.sunBall = None
            self.scene.sunDirection = (0.0, 0.0, -1.0)
            model = GetModel()
            GoToX(model, 10000000000.0)

        Label(name='goLabel', parent=self.sr.main, align=uiconst.TOTOP, text='Fly')

        def GoToX(model, offset):
            print 'GoToX', offset
            model.translationCurve.gotoX = model.translationCurve.x + offset
            model.translationCurve.gotoY = model.translationCurve.y
            model.translationCurve.gotoZ = model.translationCurve.z
            print model.translationCurve.gotoX

        def FlyLeft(_):
            model = GetModel()
            GoToX(model, -10000000000.0)

        def FlyRight(_):
            model = GetModel()
            GoToX(model, +10000000000.0)

        buttonGroup = ButtonGroup(name='flyButtons', parent=self.sr.main, align=uiconst.TOTOP)
        buttonGroup.AddButton('Left', FlyLeft)
        buttonGroup.AddButton('Right', FlyRight)

        def Orbit():
            camera = sm.GetService('camera').spaceCamera
            camera.SetOrbit(self.yaw, self.pitch)

        Label(name='cameraLabel', parent=self.sr.main, align=uiconst.TOTOP, text='Camera Yaw')

        def Yaw(button):
            yawDeg = float(button.name.split('_')[0])
            self.yaw = DegToRad(yawDeg)
            Orbit()

        buttonGroup = ButtonGroup(name='yawButtons', parent=self.sr.main, align=uiconst.TOTOP)
        buttonGroup.AddButton('-135', Yaw)
        buttonGroup.AddButton('-90', Yaw)
        buttonGroup.AddButton('-45', Yaw)
        buttonGroup.AddButton('0', Yaw)
        buttonGroup.AddButton('45', Yaw)
        buttonGroup.AddButton('90', Yaw)
        buttonGroup.AddButton('135', Yaw)
        buttonGroup.AddButton('180', Yaw)
        Label(name='cameraLabel', parent=self.sr.main, align=uiconst.TOTOP, text='Camera Pitch')

        def Pitch(button):
            yawDeg = float(button.name.split('_')[0])
            self.pitch = -DegToRad(yawDeg)
            Orbit()

        buttonGroup = ButtonGroup(name='pitchButtons', parent=self.sr.main, align=uiconst.TOTOP)
        buttonGroup.AddButton('-89', Pitch)
        buttonGroup.AddButton('-45', Pitch)
        buttonGroup.AddButton('0', Pitch)
        buttonGroup.AddButton('45', Pitch)
        buttonGroup.AddButton('89', Pitch)
        Label(name='controlLabel', parent=self.sr.main, align=uiconst.TOTOP, text='Sunlight')

        def SunDirection(button):
            angle = float(button.name.split('_')[0])
            angleRad = DegToRad(-angle) - math.pi / 2.0
            self.scene.sunDirection = (math.cos(angleRad), 0.0, math.sin(angleRad))

        buttonGroup = ButtonGroup(name='sunlightButtons', parent=self.sr.main, align=uiconst.TOTOP)
        buttonGroup.AddButton('-135', SunDirection)
        buttonGroup.AddButton('-90', SunDirection)
        buttonGroup.AddButton('-45', SunDirection)
        buttonGroup.AddButton('0', SunDirection)
        buttonGroup.AddButton('45', SunDirection)
        buttonGroup.AddButton('90', SunDirection)
        buttonGroup.AddButton('135', SunDirection)
        buttonGroup.AddButton('180', SunDirection)
        Start()


def ShowAssetLabWindow():
    AssetLabWindow()
