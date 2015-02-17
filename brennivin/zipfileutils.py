#Embedded file name: brennivin\zipfileutils.py
"""
Utilities for working with zip files.

Members
=======

.. class:: ZipFile()

   ``zipfile.ZipFile`` with a context manager (2.6 does not have a context manager.
   Use if your code needs a ZipFile context manager and must run under 2.6.

"""
import os as _os
import zipfile as _zipfile
from zipfile import ZipFile
if not hasattr(ZipFile, '__enter__'):

    class ZipFile27(ZipFile):

        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.close()


    ZipFile = ZipFile27
from . import dochelpers, osutils

class FileComparisonError(Exception):
    pass


ALL = dochelpers.pretty_func(lambda _: True, 'ALL')
NONE = dochelpers.pretty_func(lambda _: False, 'NONE')

def write_files(fullpaths, zfile, include = ALL, exclude = NONE, subdir = None, rootpath = None):
    """
    Zip files to a zip stream.
    See :func:`zip_dir` for arguments.
    
    :param fullpaths: Absolute paths to files to zip.
    :param subdir: See :func:`zip_dir`. Only valid if rootpath is also
      specified.
    :param rootpath: If provided,
      paths in the archive will be relative to this.
      Ie, passing in a branch's root and the absolute paths to files in the
      branch would make the paths in the archive be relative
      to the branch root.
    :type zfile: zipfile.ZipFile
    """
    for path in fullpaths:
        if include(path) and not exclude(path):
            arcname = None
            if rootpath:
                arcname = _os.path.relpath(path, rootpath)
                if subdir:
                    arcname = _os.path.join(subdir, arcname)
            zfile.write(path, arcname)


def write_dir(rootpath, zfile, include = ALL, exclude = NONE, subdir = None):
    """
    Zip all files under ``rootpath`` to a zip stream.
    See :func:`zip_dir` for arguments.
    
    :type zfile: zipfile.ZipFile
    """
    write_files(osutils.iter_files(rootpath), zfile, include, exclude, subdir, rootpath)


def zip_dir(rootdir, outfile, include = ALL, exclude = NONE, subdir = None):
    """Zip all files under the root directory to a zip file at ``outfile``.
    
    :param outfile: Path to zipfile, or :class:`ZipFile` stream.
    :param include: Include only files that this function returns True for.
    :param exclude: Include no files that this function returns True for.
    :param subdir: If provided, nest the ``rootdir`` under this folder in
      the archive. For example, zipping the directory ``spam`` with the files
      ``/spam/eggs/ham.txt`` and ``subdir`` of ``foo``
      would yield the archive file ``foo/eggs/ham.txt``.
    """
    outdir = _os.path.dirname(outfile)
    if not _os.path.exists(outdir):
        _os.makedirs(outdir)
    with ZipFile(outfile, 'w', _zipfile.ZIP_DEFLATED) as zfile:
        write_dir(rootdir, zfile, include, exclude, subdir)


def is_inside_zipfile(filepath):
    """
    Iterates up a directory tree checking at each level if the path exists.
    If a subpath exists and points to a zipfile, return true
    
    :param filepath: Fully qualified path to a file
    """
    folderpath, filename = _os.path.split(filepath)
    is_zip = False
    while folderpath and filename:
        if _os.path.exists(folderpath):
            if _zipfile.is_zipfile(folderpath):
                is_zip = True
            break
        folderpath, filename = _os.path.split(folderpath)

    return is_zip


def _sorted_infolist(zippath):
    return sorted(_zipfile.ZipFile(zippath).infolist(), key=lambda zi: zi.filename)


def compare_zip_files(z1, z2):
    """Compares the contents of two zip files
    (file paths and crcs).
    
    :return: None if they are the same.
    :raise FileComparisonError: If the files are different.
      Message contains a string summarizing the difference.
    """
    f1infos = _sorted_infolist(z1)
    f2infos = _sorted_infolist(z2)
    f1names = [ f.filename for f in f1infos ]
    f2names = [ f.filename for f in f2infos ]
    if f1names != f2names:
        raise FileComparisonError('File lists differ: %s, %s' % (f1names, f2names))
    for f1i, f2i in zip(f1infos, f2infos):
        if f1i.CRC != f2i.CRC:
            raise FileComparisonError('%s CRCs different.' % f1i.filename)
