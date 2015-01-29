#Embedded file name: evegraphics\utils.py


def BlockStarfieldOnLionOSX():
    import blue
    if not blue.win32.IsTransgaming():
        return False
    si = blue.win32.TGGetSystemInfo()
    if 'platform_minor_version' not in si:
        return False
    if int(si['platform_minor_version']) <= 7:
        return True
    return False


def GetResPathFromGraphicID(graphicID):
    if graphicID is None:
        return
    graphicInfo = cfg.graphics.GetIfExists(graphicID)
    if graphicInfo is None:
        return
    return getattr(graphicInfo, 'graphicFile', None)


def IsValidSOFDNA(dna):
    sp = dna.split(':')
    if len(sp) < 3:
        return False
    return True


def BuildSOFDNAFromTypeID(typeID):
    """
    This method generates an SOF DNA string from the provided typeID
    """
    if typeID is None:
        return
    typeInfo = cfg.invtypes.GetIfExists(typeID)
    if typeInfo is None:
        return
    extTypeInfo = typeInfo.GetFSDType(typeID)
    dnaAddition = getattr(extTypeInfo, 'sofDnaAddition', None)
    perTypeFaction = getattr(extTypeInfo, 'sofFactionName', None)
    return BuildSOFDNAFromGraphicID(typeInfo.GraphicID(), dnaAddition=dnaAddition, perTypeFaction=perTypeFaction)


def CombineSOFDNA(sofHullName, sofFactionName, sofRaceName, sofAddition = None):
    dna = sofHullName + ':' + sofFactionName + ':' + sofRaceName
    if sofAddition is not None:
        dna += ':' + sofAddition
    return dna


def BuildSOFDNAFromGraphicID(graphicID, dnaAddition = None, perTypeFaction = None):
    """
    This method generates an SOF DNA string from the provided graphicID
    """
    if graphicID is None:
        return
    graphicInfo = cfg.graphics.GetIfExists(graphicID)
    if graphicInfo is None:
        return
    hull = getattr(graphicInfo, 'sofHullName', None)
    faction = getattr(graphicInfo, 'sofFactionName', None)
    race = getattr(graphicInfo, 'sofRaceName', None)
    if hull is None or faction is None or race is None:
        return
    if perTypeFaction is not None:
        faction = perTypeFaction
    return CombineSOFDNA(hull, faction, race, dnaAddition)


def BuildShipEffectSoundNameFromGraphicID(graphicID, effect, start):
    """
    This method generates a WWISE sound string to be played for onship effects
    """
    if graphicID is None:
        return
    graphicInfo = cfg.graphics.GetIfExists(graphicID)
    if graphicInfo is None:
        return
    hull = getattr(graphicInfo, 'sofHullName', None)
    if hull is None:
        return
    result = effect + '_' + hull
    if start:
        result += '_play'
    else:
        result += '_stop'
    return result


def GetPreviewScenePath(raceID):
    import const
    sceneGraphicIDs = {const.raceCaldari: 20409,
     const.raceMinmatar: 20410,
     const.raceGallente: 20411,
     const.raceAmarr: 20412}
    gfxID = sceneGraphicIDs.get(raceID, 20413)
    return GetResPathFromGraphicID(gfxID)


class DummyGroup(object):

    def __init__(self):
        self._d = {}

    def Get(self, key, default = None):
        return self._d.get(key, default)

    def Set(self, key, val):
        self._d[key] = val


def GetDnaFromResPath(respath):
    lowerCaseResPath = respath.lower()
    prefix = 'res:/dx9/model/ship/'
    if not lowerCaseResPath.startswith(prefix):
        raise RuntimeError
    lowerCaseResPath = lowerCaseResPath[len(prefix):]
    parts = lowerCaseResPath.split('/')
    if len(parts) < 4:
        raise RuntimeError
    race = parts[0]
    if len(parts) == 5:
        faction = parts[3]
        ship = parts[4]
        ship = ship.replace('_' + faction, '')
    else:
        faction = race + 'base'
        ship = parts[3]
    ship = ship.split('.')[0]
    dna = '%s:%s:%s' % (ship, faction, race)
    return dna
