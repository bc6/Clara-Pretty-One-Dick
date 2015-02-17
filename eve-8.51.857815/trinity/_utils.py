#Embedded file name: trinity\_utils.py
import sys
import blue

def Quit(msg):
    try:
        import log
        log.Quit(msg)
    except ImportError:
        sys.stderr.write(msg + '\n')
        sys.exit(4)


def AssertNotOnProxyOrServer():
    try:
        cmdlineargs = blue.pyos.GetArg()
        if boot.role in ('server', 'proxy') and '/jessica' not in cmdlineargs and '/minime' not in cmdlineargs:
            raise RuntimeError("Don't import trinity on the proxy or server")
    except NameError:
        pass
