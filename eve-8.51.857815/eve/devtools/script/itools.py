#Embedded file name: eve/devtools/script\itools.py
revision = 5
import os
import types

def relpath(target, base = os.curdir):
    """
    Return a relative path to the target from either the current dir or an optional base dir.
    Base can be a directory specified either as absolute or relative to current dir.
    """
    if not os.path.exists(target):
        raise OSError, 'Target does not exist: ' + target
    if not os.path.isdir(base):
        raise OSError, 'Base is not a directory or does not exist: ' + base
    base_list = os.path.abspath(base).split(os.sep)
    target_list = os.path.abspath(target).split(os.sep)
    if base_list[0].lower() != target_list[0].lower():
        raise OSError, 'Target is on a different drive to base. Target: ' + target_list[0].lower() + ', base: ' + base_list[0].lower()
    for i in range(min(len(base_list), len(target_list))):
        if base_list[i].lower() != target_list[i].lower():
            break
    else:
        i += 1

    rel_list = [os.pardir] * (len(base_list) - i) + target_list[i:]
    return os.path.join(*rel_list)


def walktree(dir, filecallback, dircallback = None, recursive = True):
    files = os.listdir(dir)
    for file in files:
        entry = os.path.join(dir, file)
        if os.path.isdir(entry):
            if recursive:
                walktree(entry, filecallback, dircallback)
        elif callable(filecallback):
            filecallback(entry)

    if callable(dircallback):
        dircallback(dir)


def itertree(dir, files = True, dirs = False, recursive = True):
    files = os.listdir(dir)
    for file in files:
        entry = os.path.join(dir, file)
        if os.path.isdir(entry):
            if recursive:
                for x in itertree(entry, files, dirs):
                    yield x

            if dirs:
                yield (1, entry)
        elif files:
            yield (0, entry)


def listify(arg):
    if type(arg) != types.ListType:
        return [arg]
    return arg


exports = {'itools.relpath': relpath,
 'itools.walktree': walktree,
 'itools.itertree': itertree,
 'itools.listify': listify}
