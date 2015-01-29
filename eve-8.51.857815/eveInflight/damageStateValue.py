#Embedded file name: eveInflight\damageStateValue.py
from math import sqrt, exp
import blue
import dogma.const as dogmaConst

def CalculateCurrentDamageStateValues(damageState, time):
    ret = []
    shieldValues = damageState[0]
    if isinstance(shieldValues, (list, tuple)):
        now = blue.os.GetSimTime()
        num, tau = shieldValues[:2]
        sq = sqrt(num)
        eToX = exp((time - now) / dogmaConst.dgmTauConstant / tau)
        shieldHealth = (1.0 + (sq - 1.0) * eToX) ** 2
        ret.append(shieldHealth)
    else:
        ret.append(None)
    ret = ret + list(damageState[-2:])
    return ret
