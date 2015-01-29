#Embedded file name: iconrendering\icons_cli.py
"""
Commandline interface for image rendering.
"""
import logging
import argparse
import os
import sys
import shutil
import string
import _appsetup
import devenv
import fsdauthoringutils
import osutils
import stdlogutils
import ccpp4
import imgdiff
import iconrendering
import iconrendering.inventory_map as inventory
import iconrendering.rendermanagement as rendermanagement
L = logging.getLogger('iec_cli_%s' % os.getpid())
DEBUG = False
CLEANUP = False
CHECKOUT = False
TOLERANCE = 0.01
RENDER_PATH = os.path.abspath(os.path.join(devenv.EVEROOT, 'client/res/UI/Texture/Icons/renders/'))

def GetTmpRenderPath():
    return RENDER_PATH + '_tmp'


def ParseOpts():
    parser = argparse.ArgumentParser(description='Render icons for assets. These are the icons used by the client.\nWhen rendering you can specify --checkout argument to actually check out files from Perforce and update them.\nWithout that flag renders will go into a temporary folder in path: %s\n\nBy default all icons are rendered, the --respath argument can be used to render a single asset.\nFor debugging purposes --takeonly can be used to limit the number of assets that gets rendered\n.' % GetTmpRenderPath())
    parser.add_argument('--debug', default=DEBUG, action='store_true', help='Output debug information.')
    parser.add_argument('--takeonly', type=int, default=0, help='Only render this many of each type. Useful when debugging.')
    parser.add_argument('--branch', type=int, default=1, help='BranchID for static data versioning. 1=DEV, 2=STAGING, 3=RELEASE, 301=DEVDEMO. Defaults to 1. See zstatic.branches.')
    parser.add_argument('--checkout', default=CHECKOUT, help='Choose whether to check out the changes made.Defaults to False.')
    parser.add_argument('--cleanup', default=CLEANUP, help='Choose whether to delete the output render folder.Defaults to False.')
    parser.add_argument('--respath', default='', help='Only generate icons related to a specific graphic resource path.')
    parser.add_argument('--dna', default='', help='Only generate icons related to a specific dna of the form hull:faction:race.')
    return parser.parse_args()


def Main():
    opts = ParseOpts()
    loglevel = logging.DEBUG if opts.debug else logging.INFO
    logging.basicConfig(level=loglevel, filename=stdlogutils.GetTimestampedFilename2(iconrendering.APPNAME), format=stdlogutils.Fmt.NTLM)
    streamh = logging.StreamHandler(sys.stdout)
    streamh.setFormatter(stdlogutils.Fmt.FMT_NTLM)
    L.addHandler(streamh)
    iconFolder = RENDER_PATH
    renderFolder = GetTmpRenderPath()
    if os.path.exists(renderFolder):
        osutils.SafeRmTree(renderFolder)
    resmapper = fsdauthoringutils.GraphicsCache(devenv.EVEROOT)
    invmapper = inventory.InventoryMapper(opts.branch)
    _appsetup.CreateTrinityApp()
    mgr = rendermanagement.RenderManager(resmapper, invmapper, L, renderFolder, opts.takeonly)
    if opts.respath or opts.dna:
        mgr.RenderSingle(resPath=opts.respath, dnaString=opts.dna)
    else:
        mgr.RenderNPCStations()
        mgr.RenderInGameIcons()
    if opts.checkout:
        L.debug('P4 Checkout started.')
        p4 = ccpp4.P4Init()
    before = GetFiles(iconFolder)
    after = GetFiles(renderFolder)
    added = list(after.difference(before))
    deleted = list(before.difference(after))
    filesToCompare = list(after.intersection(before))
    changed = []
    for fileName in filesToCompare:
        iconPath = os.path.join(iconFolder, fileName)
        renderPath = os.path.join(renderFolder, fileName)
        diffResult = imgdiff.ImgDiff(iconPath, renderPath, normal=False, alpha=False)
        error = diffResult['Color']['MeanAbsoluteError']
        if error > TOLERANCE:
            changed.append(fileName)

    if opts.checkout:
        for fileName in added + changed:
            iconPath = os.path.join(iconFolder, fileName)
            renderPath = os.path.join(renderFolder, fileName)
            L.debug('P4 Edit or Add: %s', fileName)
            p4.EditOrAdd(iconPath)
            shutil.copy(renderPath, iconPath)

        allfiles = added + changed
        GetPath = lambda fileName: os.path.join(iconFolder, fileName)
        if not (opts.takeonly or opts.respath):
            for deletedFile in deleted:
                L.debug('P4 Deleting: %s', deletedFile)
                p4.run_delete(GetPath(deletedFile))

            allfiles = allfiles + deleted
        osfiles = map(GetPath, allfiles)
        depotFiles = map(lambda wh: wh['depotFile'], p4.run_where(osfiles))
        if len(depotFiles):
            c = p4.Change(description='Ingame Icon generation.', files=depotFiles, save=False)
            changeno = p4.SaveChange(c)
        L.debug('P4 Checkout done.')
    if opts.cleanup:
        osutils.SafeRmTree(renderFolder)
    sys.exit(0)


def GetFiles(root):
    return set(map(string.lower, os.listdir(root)))


if __name__ == '__main__':
    try:
        Main()
    except Exception:
        logging.getLogger().error('Unhandled error!', exc_info=True)
        raise
