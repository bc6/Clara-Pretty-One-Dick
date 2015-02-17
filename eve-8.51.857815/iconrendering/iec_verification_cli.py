#Embedded file name: iconrendering\iec_verification_cli.py
import argparse
import datetime
import os
import sys
import time
import _appsetup
import devenv
import iconrendering
import imgdiff
import itertoolsext
import logging
import stdlogutils
L = logging.getLogger('iec_cli_%s' % os.getpid())
TOLERANCE = 0.01

def _Listdirs(folder):
    return [ path for path in (os.path.join(folder, d) for d in os.listdir(folder)) if os.path.isdir(path) ]


def GetLatestDirectory(searchpath):
    """Return most recent directory from ``searchpath``,
    based on modification time."""
    latestdir = itertoolsext.first(sorted(_Listdirs(searchpath), key=os.path.getmtime, reverse=True))
    return latestdir


def ParseOpts():
    p = argparse.ArgumentParser(description='Package up Icon Rendering output into various formats.')
    outdir = devenv.GetAppFolder(iconrendering.APPNAME)
    p.add_argument('--rootfolder', default=outdir, type=str, help='Source dir for IEC iconrendering output. Defaults to %s' % outdir)
    p.add_argument('--searchfolderGood', default='', type=str, help='Subfolder of rootfolder to search for latest known good.')
    p.add_argument('--subfolderCompare', default='', type=str, help='Subfolder of rootfolder that contains the files we want to compare with the known good.')
    return p.parse_args()


def GetAllDirectories(path):
    d = {}
    for dirpath, dirnames, filenames in os.walk(path):
        p = dirpath[len(path):]
        d[p] = (dirpath, dirnames, filenames)

    return d


def FindMissing(oldSequence, newSequence):
    added = [ x for x in newSequence if x not in oldSequence ]
    removed = [ x for x in oldSequence if x not in newSequence ]
    missing = []
    missing.extend(added)
    missing.extend(removed)
    return (missing, added, removed)


def GetDirectoryInfo(goodPath, comparePath):
    dirsGood = GetAllDirectories(goodPath)
    dirsComp = GetAllDirectories(comparePath)
    foldersMissing, foldersAdded, foldersRemoved = FindMissing(dirsGood, dirsComp)
    return (dirsGood,
     dirsComp,
     foldersMissing,
     foldersAdded,
     foldersRemoved)


def GetImgDiffError(file1, file2):
    diffResult = imgdiff.ImgDiff(file1, file2, normal=False, alpha=True)
    error = diffResult['Color']['MeanAbsoluteError']
    error += diffResult['Alpha']['MeanAbsoluteError']
    return error


def WriteDetails(text, sequence, f):
    if len(sequence) == 0:
        return
    f.write('=============================================================\n')
    f.write(text % len(sequence))
    for each in sequence:
        f.write(str(each))
        f.write('\n')


def Main():
    opts = ParseOpts()
    logging.basicConfig(level=logging.INFO, filename=stdlogutils.GetTimestampedFilename2(iconrendering.APPNAME), format=stdlogutils.Fmt.NTLM)
    streamh = logging.StreamHandler(sys.stdout)
    streamh.setFormatter(stdlogutils.Fmt.FMT_NTLM)
    L.addHandler(streamh)
    L.info('Starting iec verification.')
    try:
        knownGood = GetLatestDirectory(os.path.join(opts.rootfolder, opts.searchfolderGood))
    except:
        L.info('Could not find known good directory. Aborting')
        return

    compareTo = os.path.join(opts.rootfolder, opts.subfolderCompare)
    startTime = time.clock()
    L.info('Analyzing folder structure.')
    dirsGood, dirsComp, foldersMissing, foldersAdded, foldersRemoved = GetDirectoryInfo(knownGood, compareTo)
    filesAdded = []
    filesRemoved = []
    changedFiles = []
    sizeChanged = []
    for each in dirsComp:
        if each in foldersMissing:
            continue
        L.info('Comparing files in %s', each)
        dirpathGood, _, filenamesGood = dirsGood[each]
        dirpathComp, _, filenamesComp = dirsComp[each]
        missingEither, added, removed = FindMissing(filenamesGood, filenamesComp)
        filesAdded.extend(map(lambda x: os.path.join(each, x), added))
        filesRemoved.extend(map(lambda x: os.path.join(each, x), removed))
        for fn in filenamesComp:
            if fn in added:
                continue
            fnGood = os.path.join(dirpathGood, fn)
            fnCompare = os.path.join(dirpathComp, fn)
            try:
                error = GetImgDiffError(fnGood, fnCompare)
                if error > TOLERANCE:
                    changedFiles.append((os.path.join(each, fn), error))
            except imgdiff.SizeMismatch:
                sizeChanged.append(os.path.join(each, fn))
                L.error('Image size changed: %s', os.path.join(each, fn))

    endTime = time.clock()
    L.info('Icon verification finished in %d seconds.' % (endTime - startTime))
    L.info('A total of %d folders were added', len(foldersAdded))
    L.info('A total of %d folders were removed', len(foldersRemoved))
    L.info('A total of %d files were added', len(filesAdded))
    L.info('A total of %d files were removed', len(filesRemoved))
    L.info('A total of %d files have changed', len(changedFiles))
    L.info('A total of %d image sizes have changed', len(sizeChanged))

    def _writeDumpFile():
        dumpFile = os.path.join(opts.rootfolder, 'verificationDump_%s.txt' % datetime.datetime.now().strftime(iconrendering.TIMESTAMP_FORMAT))
        f = open(dumpFile, 'w')
        f.write('Detailed breakdown:\n')
        WriteDetails('A total of %d folders were added\n', foldersAdded, f)
        WriteDetails('A total of %d folders were removed\n', foldersRemoved, f)
        WriteDetails('A total of %d files were added\n', filesAdded, f)
        WriteDetails('A total of %d files were removed\n', filesRemoved, f)
        WriteDetails('A total of %d files have changed\n', changedFiles, f)
        WriteDetails('A total of %d image sizes have changed\n', sizeChanged, f)
        f.flush()
        f.close()

    _writeDumpFile()


if __name__ == '__main__':
    try:
        Main()
    except Exception:
        logging.getLogger().error('Unhandled error!', exc_info=True)
        raise
