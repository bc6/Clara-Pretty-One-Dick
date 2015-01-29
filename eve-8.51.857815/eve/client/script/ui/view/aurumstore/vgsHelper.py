#Embedded file name: eve/client/script/ui/view/aurumstore\vgsHelper.py
import localization
from eve.client.script.ui.services.evePhotosvc import NONE_PATH

def FormatAUR(amount):
    return localization.GetByLabel('UI/VirtualGoodsStore/FormatAUR', amount=amount)


def LoadImageToSprite(sprite, imageUrl, defaultImageUrl = 'res:/UI/Texture/Vgs/missing_image.png'):
    """ Load an offer image in to a sprite. Block until the image has loaded in to the sprite texture. """
    texture, w, h = (None, 0, 0)
    if imageUrl:
        texture, w, h = sm.GetService('photo').GetTextureFromURL(imageUrl, retry=False)
    if texture is None or texture.resPath == NONE_PATH:
        texture, w, h = sm.GetService('photo').GetTextureFromURL(defaultImageUrl, retry=False)
    sprite.texture = texture
    sprite.width = w
    sprite.height = h
