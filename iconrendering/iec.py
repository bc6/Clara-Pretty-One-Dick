#Embedded file name: iconrendering\iec.py
import os
import platform
import time
import yamlext
import osutils
DO_RENDER_ALL = 'All'
DO_RENDER_RENDERS = 'Renders'
DO_RENDER_TYPES32 = 'Types32'
DO_RENDER_TYPES64 = 'Types64'
DO_RENDER_ICONS = 'Icons'

def DoRender(mgr, takeonly = 'unknown', whatToRender = DO_RENDER_ALL, logger = None):
    """Call render manager ``mgr`` and actually perfom the rendering.
    
    ``numprocs`` and ``takeonly`` are only here for statistics gathering.
    
    :type logger: logging.Logger
    """
    starttime = time.clock()
    if whatToRender == DO_RENDER_ALL:
        mgr.RenderAll()
    elif whatToRender == DO_RENDER_ICONS:
        mgr.CopyIcons()
    elif whatToRender == DO_RENDER_RENDERS:
        mgr.RenderRenders()
    elif whatToRender == DO_RENDER_TYPES32:
        mgr.RenderTypes32()
    elif whatToRender == DO_RENDER_TYPES64:
        mgr.RenderTypes64()
    if hasattr(mgr, 'Stop'):
        mgr.Stop()
    timetaken = time.clock() - starttime
    try:
        WriteTimeTaken(timetaken, takeonly)
    except IOError:
        if logger:
            logger.error('Exception on calling WriteTimeTaken(%s, %s)' % (timetaken, takeonly))


def WriteTimeTaken(t, taken):
    """This is intended as a temporary implementation
    to get basic data from the system,
    as we don't know the optimal configuration for speed.
    """
    path = os.path.join('\\\\pondus\\scratch\\iconrendering', 'corebench.json')
    if not os.path.exists(path):
        yamlext.dumpfile({}, path)
    root = yamlext.loadfile(path) or {}
    sysinfo = root.setdefault(platform.node(), {})
    sysinfo['NumCores'] = osutils.NumberOfCPUs()
    runslist = sysinfo.setdefault('Runs', [])
    numprocs = 'n/a'
    thisrun = {'Procs': numprocs,
     'Time': t,
     'Taken': taken}
    runslist.append(thisrun)
    yamlext.dumpfile(root, path)
