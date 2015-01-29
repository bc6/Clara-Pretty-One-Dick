#Embedded file name: eve/client/script/ui/shared/maps\label.py
import uicontrols
import uiprimitives
import telemetry
import uthread
import trinity
import xtriui
import blue
import uicls
import carbonui.const as uiconst
import uiutil
import fontConst
NEUTRAL_COLOR = (1.0, 1.0, 1.0, 0.5)
HIGHLIGHT_COLOR = (1.0, 1.0, 1.0, 0.5)

class MapLabel(uiprimitives.Bracket):
    __guid__ = 'xtriui.MapLabel'
    default_opacity = 0.0
    default_state = uiconst.UI_PICKCHILDREN
    preFullAlpha = None

    @telemetry.ZONE_METHOD
    def Startup(self, name, itemID, typeID, tracker, cloud, mylocation = None):
        self.trackTransform = tracker
        self.sr.cloud = cloud
        self.sr.id = itemID
        self.sr.typeID = typeID
        self.name = name
        if name in ('', 'myDest', 'myloc'):
            uicore.animations.FadeTo(self, startVal=0.0, endVal=1.0, duration=0.1)
            return
        frame = None
        if itemID > 0:
            if typeID == const.typeConstellation:
                label = xtriui.ParentLabel(text='<b>' + name + '</b>', parent=self, left=154, top=4, fontsize=12, uppercase=1, state=uiconst.UI_NORMAL)
                frame = uicontrols.Frame(parent=self, align=uiconst.RELATIVE)
            else:
                label = xtriui.ParentLabel(text=name, parent=self, left=154, letterspace=1, fontsize=9, uppercase=1, align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL)
                label.top = -label.textheight / 2
        else:
            label = xtriui.ParentLabel(text=name, parent=self, left=154, top=7, letterspace=1, fontsize=9, uppercase=1, state=uiconst.UI_NORMAL)
        if not mylocation:
            if self.sr.id < 0:
                label.color.SetRGB(1.0, 0.96, 0.78, 1.0)
        if typeID != const.typeSolarSystem:
            label.left = (self.width - label.width) / 2
        if frame:
            frame.left = label.left - 5
            frame.width = label.width + 10
            frame.top = label.top - 3
            frame.height = label.height + 6
        label.state = uiconst.UI_NORMAL
        uicore.animations.FadeTo(self, startVal=0.0, endVal=1.0, duration=0.1)
        return self

    def OnMouseEnter(self, *args):
        return
        self.ShowFullAlpha()
        if self.sr.id > 0:
            sm.GetService('starmap').UpdateLines(self.sr.id)

    def ShowFullAlpha(self):
        if self.preFullAlpha is None:
            self.preFullAlpha = self.children[0].color.a
        self.children[0].color.a = 1.0

    def OnMouseExit(self, *args):
        return
        if self.sr.id > 0:
            if self.sr.typeID == const.typeConstellation:
                sm.GetService('starmap').UpdateLines(None)
        self.ResetFullAlpha()

    def ResetFullAlpha(self):
        if self.preFullAlpha is not None:
            self.children[0].color.a = self.preFullAlpha
            self.preFullAlpha = None

    def OnClick(self, *args):
        sm.GetService('starmap').SetInterest(self.sr.id)

    def GetMenu(self):
        starmap = sm.GetService('starmap')
        m = []
        if self.sr.id >= 0:
            m += starmap.GetItemMenu(self.sr.id)
        else:
            m.append((self.name, sm.GetService('info').ShowInfo, (self.sr.typeID, self.sr.id)))
            m.append((uiutil.MenuLabel('UI/Map/StarMap/CenterOnScreen'), starmap.SetInterest, (self.sr.id, 1)))
        return m

    def OnMouseWheel(self, *etc):
        lib = uicore.uilib
        camera = sm.GetService('sceneManager').GetRegisteredCamera('starmap')
        if hasattr(camera, 'translationCurve'):
            targetTrans = camera.translationCurve.GetVectorAt(blue.os.GetSimTime()).z * (1.0 + -lib.dz * 0.001)
            if targetTrans < 2.0:
                targetTrans = 2.0
            if targetTrans > 10000.0:
                targetTrans = 10000.0
            camera.translationCurve.keys[1].value.z = targetTrans
        uthread.new(sm.GetService('starmap').CheckLabelDist)


class ParentLabel(uicontrols.Label):
    __guid__ = 'xtriui.ParentLabel'

    def OnMouseEnter(self, *etc):
        self.parent.OnMouseEnter(*etc)

    def OnMouseExit(self, *etc):
        self.parent.OnMouseExit(*etc)

    def OnClick(self, *etc):
        self.parent.OnClick(*etc)

    def OnMouseWheel(self, *etc):
        self.parent.OnMouseWheel(self, *etc)

    def GetMenu(self, *etc):
        return self.parent.GetMenu(*etc)


class TransformableLabel(object):
    __guid__ = 'xtriui.TransformableLabel'
    __persistvars__ = ['shader']

    def __init__(self, text, parent, size = 72, shadow = 0, hspace = 8):
        self.transform = trinity.EveTransform()
        self.transform.mesh = trinity.Tr2Mesh()
        self.transform.mesh.geometryResPath = 'res:/Model/Global/zsprite.gr2'
        self.transform.modifier = 1
        self.measurer = trinity.Tr2FontMeasurer()
        self.measurer.limit = 0
        fontFamily = uicore.font.GetFontFamilyBasedOnClientLanguageID()[fontConst.STYLE_DEFAULT]
        self.measurer.font = fontFamily[2]
        self.measurer.fontSize = size
        self.measurer.letterSpace = hspace
        self.measurer.AddText(text.upper())
        height = self.measurer.ascender - self.measurer.descender
        width = self.measurer.cursorX
        self.measurer.CommitText(0, self.measurer.ascender)
        self.transform.scaling = (width, height, 0)
        area = trinity.Tr2MeshArea()
        self.transform.mesh.transparentAreas.append(area)
        area.effect = self.effect = trinity.Tr2Effect()
        sampler = list(self.effect.samplerOverrides.GetDefaultValue())
        sampler[0] = 'DiffuseMapSampler'
        sampler[1] = trinity.TRITADDRESS_CLAMP
        sampler[2] = trinity.TRITADDRESS_CLAMP
        self.effect.samplerOverrides.append(tuple(sampler))
        self.effect.effectFilePath = 'res:/Graphics/Effect/Managed/Space/SpecialFX/TextureColor.fx'
        diffuseColor = trinity.Tr2Vector4Parameter()
        diffuseColor.name = 'DiffuseColor'
        self.effect.parameters.append(diffuseColor)
        self.diffuseColor = diffuseColor
        self.diffuseMap = trinity.TriTexture2DParameter()
        self.diffuseMap.name = 'DiffuseMap'
        self.effect.resources.append(self.diffuseMap)
        parent.children.append(self.transform)
        trinity.device.RegisterResource(self)
        self.OnCreate(trinity.device)

    def SetDiffuseColor(self, color):
        """
        The texture is multiplied by the diffuse color
        color: rbga value (yes HDR is possible)
        """
        self.diffuseColor.value = color

    def SetHighlight(self, highlight):
        """
        Sets or disables highlighting of the label
        highlight: True if enabling highlight else False
        """
        if highlight:
            self.diffuseColor.value = HIGHLIGHT_COLOR
        else:
            self.diffuseColor.value = NEUTRAL_COLOR

    def SetDisplay(self, display):
        """
        Toggle whether to display or not
        display: True to display False if not
        """
        self.transform.display = display

    def OnInvalidate(self, level):
        pass

    def OnCreate(self, dev):
        if self.diffuseMap is None:
            return
        if self.diffuseMap.resource is not None and self.diffuseMap.resource.isGood:
            return
        height = self.measurer.ascender - self.measurer.descender
        width = self.measurer.cursorX
        tr = trinity.TriTextureRes(width, height, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM, trinity.BUFFER_USAGE_FLAGS.CPU_WRITE)
        self.measurer.DrawToTexture(tr)
        self.diffuseMap.SetResource(tr)
