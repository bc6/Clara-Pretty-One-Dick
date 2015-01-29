#Embedded file name: carbonui/control\image.py
import carbonui.const as uiconst
import uthread
import copy
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.fill import Fill
from carbonui.control.menuLabel import MenuLabel
from carbonui.util.various_unsorted import MapIcon
from carbonui.control.baselink import BaseLinkCoreOverride as BaseLink

class ImageCore(Container):

    def Load(self, attrs, *args):
        self.Flush()
        self.hint = attrs.alt or ''
        self.attrs = copy.copy(attrs)
        self.width = attrs.width
        self.height = attrs.height
        self.left = getattr(attrs, 'pictureLeft', 0)
        self.top = getattr(attrs, 'pictureTop', 0)
        if getattr(self.attrs, 'loadlater', 0):
            uthread.new(self.LoadImage)
        attrs.size = int(getattr(attrs, 'size', 128))
        self.LoadAttrs(self.attrs)
        if getattr(attrs, 'bgcolor', None):
            Fill(parent=self, color=attrs.bgcolor)
        if not getattr(self.attrs, 'a', None):
            self.cursor = uiconst.UICURSOR_DEFAULT
        else:
            self.cursor = uiconst.UICURSOR_SELECT
        self.state = uiconst.UI_NORMAL
        self.loaded = 1

    def LoadAttrs(self, attrs):
        src = attrs.src
        if attrs.texture:
            sprite = Sprite(parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
            sprite.rectWidth = attrs.width
            sprite.rectHeight = attrs.height
            sprite.texture = attrs.texture
        elif src.startswith('icon:'):
            uthread.new(self.LoadIcon)

    def OnClick(self, *args):
        if getattr(self.attrs, 'a', None):
            BaseLink().ClickLink(self, self.attrs.a.href.replace('&amp;', '&'))

    def GetMenu(self):
        m = []
        if getattr(self, 'attrs', None) and getattr(self.attrs, 'src', None) and self.attrs.src:
            src = self.attrs.src
            m += [(MenuLabel('UI/Common/ReloadImage'), self.Reload)]
            if getattr(self.attrs, 'a', None):
                m += self.GetLinkMenu(self, self.attrs.a.href)
        return m

    def OnMouseMove(self, *args):
        if getattr(self, 'attrs', None) and getattr(self.attrs, 'areamap', None):
            url = self.GetLink()
            if url:
                self.cursor = uiconst.UICURSOR_SELECT
            else:
                self.cursor = uiconst.UICURSOR_DEFAULT

    def Reload(self, *args):
        if getattr(self, 'attrs', None):
            self.Load(self.attrs)

    def LoadImage(self, *args):
        if not getattr(self, 'attrs', None):
            return
        browserImageSvc = sm.GetServiceIfRunning('browserImage')
        if not browserImageSvc:
            return
        texture, tWidth, tHeight = browserImageSvc.GetTextureFromURL(getattr(self.attrs, 'src', ''), getattr(self.attrs, 'currentURL', ''), fromWhere='Img::Load')
        if texture:
            sprite = Sprite(parent=self, align=uiconst.TOALL, pos=(0, 0, 0, 0))
            sprite.rectWidth = tWidth
            sprite.rectHeight = tHeight
            sprite.rectTop = 0
            sprite.rectLeft = 0
            sprite.texture = texture
            sprite.state = uiconst.UI_DISABLED

    def LoadIcon(self, *args):
        sprite = Sprite(parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED, idx=0, pos=(0, 0, 0, 0))
        if not hasattr(self, 'attrs'):
            return
        icon = self.attrs.src[5:]
        if isinstance(icon, unicode):
            icon = icon.encode('ascii', 'xmlcharrefreplace')
        MapIcon(sprite, icon, ignoreSize=True)

    def GetLink(self):
        aL, aT, aW, aH = self.GetAbsolute()
        for each in self.attrs.areamap:
            if each['x0'] <= uicore.uilib.x - aL <= each['x1'] and each['y0'] <= uicore.uilib.y - aT <= each['y1']:
                return each['url']


class ImageCoreOverride(ImageCore):
    pass
