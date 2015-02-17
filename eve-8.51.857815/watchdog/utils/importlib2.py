#Embedded file name: watchdog/utils\importlib2.py


def import_module(target, relative_to = None):
    target_parts = target.split('.')
    target_depth = target_parts.count('')
    target_path = target_parts[target_depth:]
    target = target[target_depth:]
    fromlist = [target]
    if target_depth and relative_to:
        relative_parts = relative_to.split('.')
        relative_to = '.'.join(relative_parts[:-(target_depth - 1) or None])
    if len(target_path) > 1:
        relative_to = '.'.join(filter(None, [relative_to]) + target_path[:-1])
        fromlist = target_path[-1:]
        target = fromlist[0]
    elif not relative_to:
        fromlist = []
    mod = __import__(relative_to or target, globals(), locals(), fromlist)
    return getattr(mod, target, mod)
