#Embedded file name: codereloading.py
import __builtin__
import inspect
import logging
import sys
import traceback
import blue
import stateholder
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def _OnFileReloaded(filename, module):
    sm = getattr(__builtin__, 'sm', None)
    if sm is None:
        logger.warn('sm not defined, cannot reload services.')
        return
    guids = [ cls.__guid__[4:] for name, cls in inspect.getmembers(module, inspect.isclass) if getattr(cls, '__guid__', '').startswith('svc.') ]
    sm.Reload(set(guids))
    reloadHook = getattr(module, '__SakeReloadHook', None)
    if reloadHook is not None:
        reloadHook()
    print 'Reloaded', filename


def _OnFileReloadFailed(filename, exc_info):
    sys.stderr.write('Failed to reload: %s\n' % filename)
    traceback.print_exception(*exc_info)


def InstallSakeAutocompiler():
    """Installs the sake autocompiler.
    No nasty! But we aren't reloading services through servicemanager
    anymore. Is this OK? Who knows!
    
    This should be safe to do this early.
    sake doesn't rely on carbon,
    and it will only reload already loaded modules.
    """
    if not getattr(stateholder, 'sakeInstallationAttempted', False):
        if prefs.clusterMode == 'LOCAL' and not blue.pyos.packaged:
            try:
                from eve.common.modules.sake.toolkit import Spy
                spy = Spy()
                spy.on_file_reloaded.connect(_OnFileReloaded)
                spy.on_file_reload_failed.connect(_OnFileReloadFailed)
                logger.info('Installed sake AutoCompiler.')
            except Exception:
                logger.exception('sake AutoCompiler failed to install.')

        else:
            logger.info('Skipping sake AutoCompiler installation.')
        stateholder.sakeInstallationAttempted = True
    else:
        logger.info('Tried to install sake AutoCompiler but already installed.')
