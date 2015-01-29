#Embedded file name: iconrendering\iec_cli.py
"""
Commandline interface for image rendering.
"""
import argparse
import logging
import os
import sys
import _appsetup
import devenv
import osutils
import fsdauthoringutils
import stdlogutils
import iconrendering
import iconrendering.iec as iec
import iconrendering.inventory_map as inventory
import iconrendering.rendermanagement as rendermanagement
L = logging.getLogger('iec_cli_%s' % os.getpid())
DEBUG = False

def ParseOpts():
    o = argparse.ArgumentParser()
    outdir = devenv.GetAppFolder(iconrendering.APPNAME)
    o.add_argument('outfolder', help='Output folder relative to output root directory.')
    choices = [iec.DO_RENDER_ALL,
     iec.DO_RENDER_ICONS,
     iec.DO_RENDER_RENDERS,
     iec.DO_RENDER_TYPES32,
     iec.DO_RENDER_TYPES64]
    o.add_argument('imagebatch', choices=choices, help='Specify which part of the iec to render/generate.')
    o.add_argument('--removedir', default=False, action='store_true', help='Remove/replace destination folder if it already exists.')
    o.add_argument('--outroot', default=outdir, help='Root output directory. Defaults to %s' % outdir)
    o.add_argument('--debug', default=DEBUG, help='Output debug information.')
    o.add_argument('--takeonly', type=int, help='Only render this many of each type. Useful when debugging.')
    o.add_argument('--branch', type=int, default=3, help='BranchID for static data versioning. 1=DEV, 2=STAGING, 3=RELEASE, 301=DEVDEMO. Defaults to 3. See zstatic.branches.')
    return o.parse_args()


def Main():
    opts = ParseOpts()
    loglevel = logging.DEBUG if opts.debug else logging.INFO
    logging.basicConfig(level=loglevel, filename=stdlogutils.GetTimestampedFilename2(iconrendering.APPNAME), format=stdlogutils.Fmt.NTLM)
    streamh = logging.StreamHandler(sys.stdout)
    streamh.setFormatter(stdlogutils.Fmt.FMT_NTLM)
    L.addHandler(streamh)
    out = os.path.join(opts.outroot, opts.outfolder)
    if opts.removedir:
        osutils.SafeRmTree(out)
    resmapper = fsdauthoringutils.GraphicsCache(devenv.EVEROOT)
    invmapper = inventory.InventoryMapper(opts.branch)
    _appsetup.CreateTrinityApp()
    mgr = rendermanagement.RenderManager(resmapper, invmapper, L, out, opts.takeonly)
    iec.DoRender(mgr, opts.takeonly, whatToRender=opts.imagebatch, logger=L)
    sys.exit(0)


if __name__ == '__main__':
    try:
        Main()
    except Exception:
        logging.getLogger().error('Unhandled error!', exc_info=True)
        raise
