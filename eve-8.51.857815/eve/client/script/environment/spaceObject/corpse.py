#Embedded file name: eve/client/script/environment/spaceObject\corpse.py
from eve.client.script.environment.spaceObject.spaceObject import SpaceObject
from eve.client.script.paperDoll.commonClientFunctions import GetSkinTypeOrToneColorVariation
import eve.common.lib.appConst as const
import evegraphics.utils as gfxutils
import random
GENDER_FEMALE = 0
GENDER_MALE = 1
COLOR_LIGHT = 0
COLOR_MID = 1
COLOR_DARK = 2
corpseColorVariations = [COLOR_DARK, COLOR_MID, COLOR_LIGHT]
CORPSE_COLOR_COUNT = len(corpseColorVariations)
CORPSE_VARIATION_COUNT = 4
corpseGraphicsIDs = {GENDER_MALE: {COLOR_DARK: [20371,
                            20375,
                            20378,
                            20381],
               COLOR_MID: [20373,
                           20376,
                           20379,
                           20382],
               COLOR_LIGHT: [20374,
                             20377,
                             20380,
                             20383]},
 GENDER_FEMALE: {COLOR_DARK: [20358,
                              20361,
                              20365,
                              20368],
                 COLOR_MID: [20359,
                             20362,
                             20366,
                             20369],
                 COLOR_LIGHT: [20360,
                               20363,
                               20367,
                               20370]}}
skinToColorMapping = {'c0': COLOR_LIGHT,
 'c1': COLOR_LIGHT,
 'c2': COLOR_LIGHT,
 'c3': COLOR_LIGHT,
 'c4': COLOR_LIGHT,
 'c5': COLOR_LIGHT,
 'c6': COLOR_LIGHT,
 'c7': COLOR_LIGHT,
 'c8': COLOR_LIGHT,
 'c9': COLOR_MID,
 'c10': COLOR_MID,
 'c11': COLOR_MID,
 'c12': COLOR_MID,
 'c13': COLOR_DARK,
 'c14': COLOR_DARK,
 'civire': COLOR_LIGHT,
 'deteis': COLOR_LIGHT,
 'achura': COLOR_LIGHT,
 'sebiestor': COLOR_LIGHT,
 'vherokior': COLOR_LIGHT,
 'khanid': COLOR_LIGHT,
 'amarr': COLOR_LIGHT,
 'gallente': COLOR_LIGHT,
 'jinmei': COLOR_LIGHT,
 'intaki': COLOR_LIGHT,
 'nikunni': COLOR_MID,
 'brutor': COLOR_DARK}

def GetCorpseColor(charID):
    dnaRow = sm.RemoteSvc('paperDollServer').GetPaperDollData(charID)
    skin = GetSkinTypeOrToneColorVariation(dnaRow)
    if skin is None:
        r = random.Random()
        return r.choice(corpseColorVariations)
    skin = skin.split('_')[0]
    if skin in skinToColorMapping:
        return skinToColorMapping[skin]


def GetCorpseVariation():
    r = random.Random()
    return r.randrange(0, CORPSE_VARIATION_COUNT)


def GetCorpsePath(gender, color, variation):
    graphicID = corpseGraphicsIDs[gender][color][variation]
    return gfxutils.GetResPathFromGraphicID(graphicID)


def GetCorpsePathForCharacter(charID, variation = None):
    gender = GENDER_FEMALE
    if cfg.eveowners.Get(charID).gender:
        gender = GENDER_MALE
    color = GetCorpseColor(charID)
    if variation is None:
        variation = GetCorpseVariation()
    return GetCorpsePath(gender, color, variation)


def GetRandomCorpsePath(gender, seed = None):
    r = random.Random(seed)
    corpseVariation = r.randrange(0, CORPSE_VARIATION_COUNT)
    color = r.choice(corpseColorVariations)
    return GetCorpsePath(gender, color, corpseVariation)


class Corpse(SpaceObject):

    def LoadModel(self, fileName = None, loadedModel = None):
        gender = GENDER_FEMALE
        if self.typeID != const.typeCorpseFemale:
            gender = GENDER_MALE
        path = GetRandomCorpsePath(gender, self.id)
        SpaceObject.LoadModel(self, path)

    def Explode(self):
        if self.model is None:
            return
        explosionURL = 'res:/Model/Effect3/capsule_explosion.red'
        return SpaceObject.Explode(self, explosionURL)
