#Embedded file name: sensorsuite/overlay\const.py
from carbon.common.lib.const import SEC
SWEEP_CYCLE_TIME = long(12 * SEC)
SWEEP_LEAD_TIME = long(0 * SEC)
SWEEP_TAIL_TIME = long(0.5 * SEC)
SWEEP_START_GRACE_TIME_SEC = 5.0
SWEEP_START_GRACE_TIME = long(SWEEP_START_GRACE_TIME_SEC * SEC)
SUPPRESS_GFX_WARPING = 1
SUPPRESS_GFX_NO_UI = 2
