#Embedded file name: eve/client/script/ui/control\infoIcon.py
from eve.client.script.ui.control.glowSprite import GlowSprite

class InfoIcon(GlowSprite):
    """Ready made Show info icon that selects icon depending on size. Build in linky
    arguments:
    - typeID (required)
    - itemID (optional)
    - abstratinfo (optional)
    - size (optional, default 16)"""
    __guid__ = 'uicontrols.InfoIcon'
    default_abstractinfo = None
    default_texturePath = 'res:/ui/Texture/Icons/38_16_208.png'
    default_typeID = None
    default_itemID = None
    default_width = 16
    default_height = 16

    def ApplyAttributes(self, attributes):
        GlowSprite.ApplyAttributes(self, attributes)
        self.itemID = attributes.get('itemID', self.default_itemID)
        self.typeID = attributes.get('typeID', self.default_typeID)
        self.abstractinfo = attributes.get('abstractinfo', self.default_abstractinfo)

    def OnClick(self, *args):
        self.ShowInfo(self.typeID, self.itemID, self.abstractinfo)

    def ShowInfo(self, typeID, itemID, abstractinfo, *args):
        sm.GetService('info').ShowInfo(typeID=typeID, itemID=itemID, abstractinfo=abstractinfo)

    def UpdateInfoLink(self, typeID, itemID, abstractinfo = None):
        self.OnClick = (self.ShowInfo,
         typeID,
         itemID,
         abstractinfo)


class MoreInfoIcon(GlowSprite):
    """
    A button-like icon whose sole purpose is displaying a mouse hint on hover (no click function)
    """
    default_width = 16
    default_height = 16
    default_texturePath = 'res:/ui/Texture/Icons/generic/more_info_16.png'

    def GetTooltipDelay(self):
        return 0

    def OnMouseDown(self, *args):
        pass

    def OnMouseUp(self, *args):
        pass
