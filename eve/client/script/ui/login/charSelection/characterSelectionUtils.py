#Embedded file name: eve/client/script/ui/login/charSelection\characterSelectionUtils.py
"""
    This file contains the UI Colors and some utility functions for the character selection screen
"""
import util
import uiprimitives
import uicontrols
import eve.client.script.ui.login.charSelection.characterSelectionColors as csColors
xmlNamespaces = {'atom': 'http://www.w3.org/2005/Atom',
 'media': 'http://search.yahoo.com/mrss/',
 'ccpmedia': 'http://ccp/media'}
adTrialTerm = 'Trial'
adMediumTerm = 'Medium'
adAdvancedTerm = 'Advanced'
WARNING_TIME = 5 * const.DAY
COLLAPSE_TIME = 0.3
FADE_ANIMATION_TIME = 0.3

def GetCharacterSelectionAdPageUrl(languageID):
    if boot.region == 'optic':
        pageUrl = sm.GetService('machoNet').GetGlobalConfig().get('CharacterSelectionAdPage')
        if not pageUrl:
            pageUrl = 'http://eve.tiancity.com/client'
    else:
        WEB_EVE = {'EN': 'http://newsfeed.eveonline.com/en-us/88/articles',
         'DE': 'http://newsfeed.eveonline.com/de-de/88/articles',
         'RU': 'http://newsfeed.eveonline.com/ru-ru/88/articles'}
        if languageID in WEB_EVE:
            pageUrl = WEB_EVE[languageID]
        else:
            pageUrl = WEB_EVE['EN']
    return pageUrl


def AddFrameWithFillAndGlow(parent, showFill = True, fillColor = csColors.OTHER_FILL, frameColor = csColors.OTHER_FRAME, glowColor = csColors.FRAME_GLOW_ACTIVE):
    if showFill:
        fill = uiprimitives.Fill(bgParent=parent, color=fillColor)
    else:
        fill = None
    normalFrame = uicontrols.Frame(parent=parent, color=frameColor)
    glowFrameTexturePath = 'res:/UI/Texture/classes/CharacterSelection/glowDotFrame.png'
    glowFrame = uicontrols.Frame(parent=parent, name='glowFrame', color=glowColor, frameConst=(glowFrameTexturePath,
     5,
     -2,
     0), padding=0)
    return (glowFrame, normalFrame, fill)


def SetColor(uiComponent, newColor, animate = False):
    if animate:
        uicore.animations.SpColorMorphTo(uiComponent, startColor=uiComponent.GetRGBA(), endColor=newColor, duration=FADE_ANIMATION_TIME)
    else:
        uiComponent.SetRGBA(*newColor)


def MakeTransparent(uiComponent, animate = False):
    if animate:
        uicore.animations.MorphScalar(uiComponent, 'opacity', startVal=uiComponent.opacity, endVal=0.0, duration=FADE_ANIMATION_TIME)
    else:
        uiComponent.opacity = 0


def SetEffectOpacity(uiComponent, newOpacity, animate = False):
    if animate:
        uicore.animations.MorphScalar(uiComponent, 'effectOpacity', startVal=uiComponent.effectOpacity, endVal=newOpacity, duration=FADE_ANIMATION_TIME)
    else:
        uiComponent.effectOpacity = newOpacity


def SetSaturation(uiComponent, newSaturation, animate = False):
    if animate:
        uicore.animations.MorphScalar(uiComponent, 'saturation', startVal=uiComponent.saturation, endVal=newSaturation, duration=FADE_ANIMATION_TIME)
    else:
        uiComponent.uiComponent = newSaturation
