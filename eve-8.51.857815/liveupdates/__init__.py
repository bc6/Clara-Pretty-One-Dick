#Embedded file name: liveupdates\__init__.py
"""
Live update system for EVE (and eventually DUST).
This allows a remote server to execute arbitrary code on a client.

Clients are responsible for listening to their own live udpate notification
mechanism (for EVE it is a Macho broadcast, for DUST it'd be something else).
The client mechanisms can be here,
or implemented with the application.
See `LiveUpdaterClientMixin` for a useful wrapper.

The broadcast mechanisms (on the server) can be inside this package,
or implemented with the application.

The basic common interface is described by `runcode`.
An extended version of this interface,
which assumes a certain serialization of arguments and return values,
is provided by `runcode_safeio`.
See the function docstrings for more info.

Code is executed in a specified module's namespace,
so subsequent code executions can rely on previous code executions.
Use this feature with care, however.
"""
import binascii
import cStringIO
import imp
import logging
import marshal
import sys
import traceback
import yaml
logger = logging.getLogger(__name__)
EVAL = 'EVAL'
EXEC = 'EXEC'
RESPONSE_KEYS = ('stdout', 'stderr', 'eval', 'exception', 'exceptionTrace')
BASE64_KEYS = ('stdout', 'stderr', 'eval')

def makemodule(name = 'liveupdateholder'):
    """Returns a new module with the given name, placed into sys.modules."""
    m = imp.new_module(name)
    sys.modules[m.__name__] = name
    return m


def runcode(code, module, mode = None):
    """Evals or execs a code string in the locals of a given module.
    
    :param code: Something that can be `exec`ed.
    :param module: A module object.
      The exec of the code will use the locals() of this module,
      and any eval'ed result will be stored in its `_` variable.
    :param mode: MODE const. Default to EXEC.
    :return: A dict limited to `RESPONSE_KEYS`.
      Keys that are not applicable will not be in the dict.
    
      "stdout" and "stderr" are the stdout and stderr during the exec.
      "eval" is the result if the execed or evaled code returned a result
      (exec may return a result if it is only one line).
      "exception" is the exception type if one was raised.
      "exceptionTrace" is the traceback string if an exception was raised.
    """
    if mode is None:
        mode = EXEC

    def displayhook(obj):
        """Custom displayhook for the exec in default(), which prevents
        assignment of the _ variable in the builtins and grabs the
        value of a single statement execution.
        """
        global evalresult
        if obj is not None:
            evalresult = obj

    evalresult = None
    ex = None
    exceptionTrace = None
    ioOut, ioErr = cStringIO.StringIO(), cStringIO.StringIO()
    try:
        tmp = (sys.stdout, sys.stderr)
        sys.stdout, sys.stderr = ioOut, ioErr
        save_displayhook = sys.displayhook
        sys.displayhook = displayhook
        logger.info('Going to %r into %r: %r', mode, module.__name__, code)
        try:
            if mode == EXEC:
                exec code in globals(), module.__dict__
            else:
                evalresult = eval(code, globals(), module.__dict__)
        finally:
            sys.stdout, sys.stderr = tmp
            sys.displayhook = save_displayhook

    except Exception as ex:
        exceptionTrace = ''.join(traceback.format_tb(sys.exc_info()[2]))

    evalresultstr = None
    if evalresult is not None:
        module.__dict__['_'] = evalresult
        evalresultstr = str(evalresult)
    data = {'stdout': ioOut.getvalue(),
     'stderr': ioErr.getvalue()}
    if evalresultstr:
        data['eval'] = evalresultstr
    if ex:
        data['exception'] = '{}: {}'.format(ex.__class__.__name__, ex)
        data['exceptionTrace'] = exceptionTrace
    return data


def runcode_safeio(code, module, mode = None, loads = marshal.loads, doBase64 = True):
    """Wrapper for `runcode` that handles serialization of inputs.
    `module` and `mode` are as they are for `runcode`.
    
    :param code: Exec'able object. Will be unmarshalled through
      `loads` param value.
    :return: See `runcode` for the resulting dictionary description.
      If `doBase64`, all keys that are present in the return value
      and in `BASE64_KEYS`
      will be base64 encoded for safe transport across the wire.
    """
    realcode = loads(code)
    data = runcode(realcode, module, mode)
    result = dict(data)
    if doBase64:
        for k in BASE64_KEYS:
            if k in result:
                result[k] = binascii.b2a_base64(result[k])

    return result


class LiveUpdaterClientMixin(object):
    """Wrapper around `runcode_safeio` for a stateful client object
    that caches the module code was executed in,
    handles some logging,
    and mirrors the set of assumptions for the EVE server side of
    live updates.
    """

    def __init__(self):
        self._module = makemodule()

    def HandlePayload(self, payload):
        """Executes arbitrary code on this client.
        Small wrapper around `runcode_safeio`.
        
        :key script: Contains yaml dumped python script.
        :key id: Id of the udpate.
        :key module: Name of the module to use the locals to execute under.
          If not found or None, use a synthetic module that is cached
          between calls.
        :key mode: Optional MODE constant.
        """
        logger.warn('Applying live update: %r', payload['id'])
        if 'module' in payload:
            module = __import__(payload['module'])
        else:
            module = self._module
        result = runcode_safeio(payload['script'], module, payload.get('mode'), loads=yaml.load, doBase64=False)
        logger.warn('Update %s applied. Contents:\n%s', payload['id'], result)
        if result.get('stdout'):
            logger.debug('stdout: %s', result['stdout'])
        if result.get('stderr'):
            logger.warn('stderr: %s', result['stderr'])
        if 'exceptionTrace' in result:
            logger.error('%s\n%s', result['exceptionTrace'], result['exception'])
        return result
