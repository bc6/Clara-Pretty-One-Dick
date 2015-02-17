#Embedded file name: iconrendering\packaging_cli.py
import argparse
import contextlib
import glob
import logging
import os
import shutil
import stat
import sys
import tempfile
from collections import namedtuple
pkgspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if pkgspath not in sys.path:
    sys.path.append(pkgspath)
import itertoolsext
import osutils
import stdlogutils
import zipfileutils
import iconrendering
L = logging.getLogger('iec_cli_%s' % os.getpid())
IEC_DEFAULT_PATH = '\\\\JENKINS-T02\\iconrendering\\release\\good'
IMAGE_SET_DEFAULT_PATH = os.path.join('..', '..', 'eve', 'web', 'image', 'ProjectFiles', 'MinimalImageSet')
IMAGE_SET_DEFAULT_PATH_ZH = os.path.join('..', '..', 'eve', 'web', 'image', 'ProjectFiles', 'MinimalImageSet.ZH')
BASE_RES_PATH = os.path.join('..', '..', 'eve', 'client', 'res')
CUSTOM_ICON_FILE = '3rdPartyIcons.txt'
ALLIANCE_SRCDIR = 'Alliances'
ALLIANCE_COMPLETE_SRCDIR = 'AlliancesComplete'
CHARACTERS_SRCDIR = 'Characters'
TYPES_DUMMY_SRCDIR = 'Types'
RENDERS_DUMMY_SRCDIR = 'Renders'
CORPORATIONS_DIR = 'Corporations'
ICONS_DIR = 'Icons'
TYPES_DIR = 'Types'
RENDERS_DIR = 'Renders'
IMAGE_SET_ALL = 'ImageSet'
IMAGE_SET_COMPLETE = 'ImageSetComplete'
IMAGE_SET_MINIMAL = 'ImageSetMinimal'
IMAGE_SET_ALLIANCES = 'ImageSetAlliances'
IEC_ALL = 'IEC'
IEC_TYPES = 'IECTypes'
IEC_ICONS = 'IECIcons'
IEC_RENDERS = 'IECRenders'

def ParseOpts():
    p = argparse.ArgumentParser(description='Package up Icon Rendering output into various formats.')
    p.add_argument('outdir', help='Destination directory.')
    p.add_argument('deco', help='Injected into the name of the output file.')
    choices = [IEC_ALL, IMAGE_SET_ALL]
    choices.extend(GetRecipes('').keys())
    p.add_argument('collection', choices=choices, help='Specify which image collections to build. %s generates all IEC zip files. %s generates Alliances and Complete ImageSet zip files.' % (IEC_ALL, IMAGE_SET_ALL))
    p.add_argument('--iecsource', '-e', metavar='DIRPATH', default=None, type=str, help='Source dir for IEC iconrendering output.')
    p.add_argument('--imagesetsource', '-m', metavar='DIRPATH', default=None, type=str, help='Source dir for MinimalImageSet data.')
    p.add_argument('--debug', '-d', action='store_true', help='Output debug information and preserve temporary folder.')
    p.add_argument('--zh', '-z', action='store_true', help='ImageSet zip files are generated for china.')
    return p.parse_args()


image_collection = namedtuple('image_collection', ['filename', 'dirs'])

def GetWhitelistedItems(whitelist_path, whitelist_file, destination_prefix):
    l = []
    old_dir = os.getcwd()
    destination_path = destination_prefix
    with open(whitelist_file, 'r') as f:
        os.chdir(whitelist_path)
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == ':':
                destination_path = os.path.join(destination_prefix, line[1:])
                continue
            for each in glob.glob(line):
                src_path = os.path.abspath(each)
                l.append((src_path, destination_path))

    os.chdir(old_dir)
    return l


def GetRecipes(name_deco, iec_dir = IEC_DEFAULT_PATH, image_set_dir = IMAGE_SET_DEFAULT_PATH):
    alliance_srcdir = os.path.join(image_set_dir, ALLIANCE_SRCDIR)
    alliance_complete_srcdir = os.path.join(image_set_dir, ALLIANCE_COMPLETE_SRCDIR)
    characters_srcdir = os.path.join(image_set_dir, CHARACTERS_SRCDIR)
    types_dummy_srcdir = os.path.join(image_set_dir, TYPES_DUMMY_SRCDIR)
    renders_dummy_srcdir = os.path.join(image_set_dir, RENDERS_DUMMY_SRCDIR)
    corporations_dir = os.path.join(image_set_dir, CORPORATIONS_DIR)
    icons_dir = os.path.join(iec_dir, ICONS_DIR)
    types_dir = os.path.join(iec_dir, TYPES_DIR)
    renders_dir = os.path.join(iec_dir, RENDERS_DIR)
    icon_dirs = [(icons_dir, 'Icons')]
    icon_dirs.extend(GetWhitelistedItems(BASE_RES_PATH, CUSTOM_ICON_FILE, 'Icons'))
    return {IMAGE_SET_COMPLETE: image_collection(filename='ImageSet-Complete-%s.zip' % name_deco, dirs=((alliance_srcdir, 'ImageSet\\Alliances'),
                          (characters_srcdir, 'ImageSet\\Characters'),
                          (corporations_dir, 'ImageSet\\Corporations'),
                          (renders_dir, 'ImageSet\\Renders'),
                          (types_dir, 'ImageSet\\Types'),
                          (renders_dummy_srcdir, 'ImageSet\\Renders'),
                          (types_dummy_srcdir, 'ImageSet\\Types'))),
     IMAGE_SET_MINIMAL: image_collection(filename='ImageSet-Minimal-%s.zip' % name_deco, dirs=((alliance_srcdir, 'ImageSet\\Alliances'),
                         (characters_srcdir, 'ImageSet\\Characters'),
                         (corporations_dir, 'ImageSet\\Corporations'),
                         (renders_dummy_srcdir, 'ImageSet\\Renders'),
                         (types_dummy_srcdir, 'ImageSet\\Types'))),
     IMAGE_SET_ALLIANCES: image_collection(filename='ImageSet-Alliances-%s.zip' % name_deco, dirs=((alliance_complete_srcdir, 'Alliances'), (alliance_srcdir, 'Alliances'))),
     IEC_TYPES: image_collection(filename='%sTypes.zip' % name_deco, dirs=((types_dir, 'Types'),)),
     IEC_ICONS: image_collection(filename='%sIcons.zip' % name_deco, dirs=icon_dirs),
     IEC_RENDERS: image_collection(filename='%sRenders.zip' % name_deco, dirs=((renders_dir, 'Renders'),))}


def GetPackagesToProcess(opts):
    if opts.collection == IEC_ALL:
        return (IEC_TYPES, IEC_RENDERS, IEC_ICONS)
    if opts.collection == IMAGE_SET_ALL:
        return (IMAGE_SET_ALLIANCES, IMAGE_SET_COMPLETE)
    return (opts.collection,)


def _Listdirs(folder):
    return [ path for path in (os.path.join(folder, d) for d in os.listdir(folder)) if os.path.isdir(path) ]


def GetLatestIECDirectory(searchpath = IEC_DEFAULT_PATH):
    """Return most recent directory from ``searchpath``,
    based on modification time."""
    latestdir = itertoolsext.first(sorted(_Listdirs(searchpath), key=os.path.getmtime, reverse=True))
    return latestdir


def _RmTree(directory):
    """Wrapper for shutil.rmtree but supports deleting read-only files.
    
    Read-only files happen often for this CLI because e.g. Perforce folders
    are merged in.
    """

    def on_rm_error(func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        os.remove(path)

    shutil.rmtree(directory, onerror=on_rm_error)


@contextlib.contextmanager
def DirectoryStaged(doCleanup = True):
    """Context manager that stages ``src``
    into a temporary directory that is returned,
    and cleans it up on __exit__ unless ``doCleanup`` is False."""
    dst = tempfile.mkdtemp('staged')
    _RmTree(dst)
    try:
        yield dst
    finally:
        if doCleanup:
            _RmTree(dst)


def CopyFileTo(sourcePath, srcFilePath, dstroot):
    relfp = os.path.relpath(srcFilePath, sourcePath)
    dstfp = os.path.join(dstroot, relfp)
    if not os.path.exists(os.path.dirname(dstfp)):
        os.makedirs(os.path.dirname(dstfp))
    shutil.copy(srcFilePath, dstfp)
    if not os.access(dstfp, os.W_OK):
        os.chmod(dstfp, stat.S_IWRITE)


def CopyFolderContent(src, dstroot):
    for fp in osutils.FindFiles(src):
        CopyFileTo(src, fp, dstroot)


def ProcessPackage(recipe, stagingdir, destfile):
    for src, dest in recipe:
        L.debug('Copying %s to %s', src, dest)
        destpath = os.path.join(stagingdir, dest)
        if os.path.isdir(src):
            CopyFolderContent(src, destpath)
        else:
            CopyFileTo(os.path.dirname(src), src, destpath)

    L.debug('Creating zip file %s', destfile)
    zipfileutils.zip_dir(stagingdir, destfile)
    L.debug('Finished processing package.')


def Main():
    opts = ParseOpts()
    loglevel = logging.DEBUG if opts.debug else logging.INFO
    logging.basicConfig(level=loglevel, filename=stdlogutils.GetTimestampedFilename2(iconrendering.APPNAME), format=stdlogutils.Fmt.NTLM)
    streamh = logging.StreamHandler(sys.stdout)
    streamh.setFormatter(stdlogutils.Fmt.FMT_NTLM)
    L.addHandler(streamh)
    outdir = os.path.abspath(opts.outdir)
    name_deco = opts.deco
    iec_dir = opts.iecsource or GetLatestIECDirectory()
    if opts.zh:
        imageset_dir = opts.imagesetsource or IMAGE_SET_DEFAULT_PATH_ZH
    else:
        imageset_dir = opts.imagesetsource or IMAGE_SET_DEFAULT_PATH
    recipes = GetRecipes(name_deco, iec_dir, imageset_dir)
    L.debug('Outdir is: %s', outdir)
    for package in GetPackagesToProcess(opts):
        with DirectoryStaged(not opts.debug) as stagingdir:
            if opts.debug:
                L.debug('Using staging directory: %s', stagingdir)
            recipe = recipes[package]
            destfile = os.path.join(outdir, recipe.filename)
            if opts.debug:
                L.debug('Generating %s as %s.', package, destfile)
            ProcessPackage(recipe.dirs, stagingdir, destfile)

    sys.exit(0)


if __name__ == '__main__':
    Main()
