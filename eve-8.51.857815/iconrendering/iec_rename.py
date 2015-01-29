#Embedded file name: iconrendering\iec_rename.py
"""
Commandline interface for image rendering.
"""
import argparse
import datetime
import logging
import os
import sys
import _appsetup
import devenv
import iconrendering
DEBUG = False

def ParseOpts():
    o = argparse.ArgumentParser()
    rootdir = devenv.GetAppFolder(iconrendering.APPNAME)
    o.add_argument('srcfolder', help='Source folder relative to root directory. Root defaults to %s' % rootdir)
    o.add_argument('dstfolder', help='Output folder relative to root directory. Root defaults to %s' % rootdir)
    o.add_argument('--rootfolder', '-o', default=rootdir, help='Root output directory. Defaults to %s' % rootdir)
    o.add_argument('--dstrootfolder', default='', help='')
    o.add_argument('--timestampout', default=False, action='store_true', help='If present, append a timestamp to the outdir.')
    return o.parse_args()


def Main():
    opts = ParseOpts()
    folderNameOrg = os.path.join(opts.rootfolder, opts.srcfolder)
    folderNameDst = os.path.join(opts.rootfolder, opts.dstfolder)
    if opts.timestampout:
        folderNameDst += '_' + datetime.datetime.now().strftime(iconrendering.TIMESTAMP_FORMAT)
    if opts.dstrootfolder != '':
        dstRoot = os.path.join(opts.rootfolder, opts.dstrootfolder)
        if not os.path.exists(dstRoot):
            os.mkdir(dstRoot)
    os.rename(folderNameOrg, folderNameDst)
    sys.exit(0)


if __name__ == '__main__':
    try:
        Main()
    except Exception:
        logging.getLogger().error('Unhandled error!', exc_info=True)
        raise
