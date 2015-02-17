#Embedded file name: clienteffects\__init__.py
EFFECT_METHOD = 'OnSpecialFX'

def SetEffect(sourceID, targetID, effectName, start, duration, repeat):
    sm.ScatterEvent(EFFECT_METHOD, sourceID, None, None, targetID, None, effectName, 0, start, 0, duration, repeat)


def StartShipEffect(sourceID, effectName, duration, repeat):
    SetEffect(sourceID, None, effectName, True, duration, repeat)


def StopShipEffect(sourceID, effectName):
    SetEffect(sourceID, None, effectName, False, None, None)


def StartStretchEffect(sourceID, targetID, effectName, duration, repeat):
    SetEffect(sourceID, targetID, effectName, True, duration, repeat)


def StopStretchEffect(sourceID, targetID, effectName):
    SetEffect(sourceID, targetID, effectName, False, None, None)
