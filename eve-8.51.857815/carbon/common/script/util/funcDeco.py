#Embedded file name: carbon/common/script/util\funcDeco.py
"""
Function Decorators
The decision was finally that Eve would rather not use function decorators, because they preferred a greater level of fine tune control.
Our code did not require that level of fine tuning, and so we prefer to use function decorators for easier development of code.

The function decorators defined in Eve originally did not conform to the standard python syntax for function decorators.
Thus, the ones we wish to keep are re-written here, according to the syntax.

Future function decorators that are safe for global use should be placed here.
Unless Eve adopts the use of function decorators, this code will be used exclusively in Wod.
"""
import uthread, blue, types

def CallInNewThread(context = None, returnValue = None):
    """
        Causes the function to be called in a separate thread whenever it is called.
        Attach the given context to that thread context for clarity in the profiler.
        This function returns a function decorator, which can be used to decorate a function.
        Syntax is:
            @funcDeco.CallInNewThreadWithContext(context="ContextString")
            def MyFunc():
                ' This is the standard method, which you manually define the context '
        - or -
            @funcDeco.CallInNewThreadWithContext()
            def MyFunc():
                ' This is not recommended, the context will be assigned the current tasklet, which may or may not be the right context. '
        
        The returnValue parameter specified what should be returned when the function itself 
        it first called and can be used when some specific return value is expected. Note that 
        any return value from the spawned worker thread will be simply igonred.
    """

    def ContextThread(f):
        """ Causes the function to be called in a separate thread whenever it is called. """
        if context is not None:
            if context.startswith('^'):
                fullContext = context
            else:
                fullContext = '^%s::%s' % (context, f.__name__)
        else:
            fullContext = f.__name__

        def deco(*args, **kw):
            uthread.worker(fullContext, f, *args, **kw)
            return returnValue

        return deco

    return ContextThread


def Memoized(minutes):
    """
    Make a function that remembers the return value of previous calls for each
    given set of arguments for either a specified or infinite amount of minutes.
    
    It is assumed that the given function is supposed to always return the same
    values if you call it with the same arguments.
    """
    memo = {}
    time = 1099511627776L

    def deco(fn):

        def inner_deco(*args, **kwargs):
            key = (str(args), str(kwargs))
            if key not in memo or memo[key][1] + time < blue.os.GetWallclockTime():
                memo[key] = (fn(*args, **kwargs), blue.os.GetWallclockTime())
            return memo[key][0]

        return inner_deco

    if isinstance(minutes, (types.FunctionType, types.MethodType)):
        return deco(minutes)
    time = minutes * const.MIN
    return deco


def ClearMemoized(function):
    """Clears all cached values from a function implementing the Memoized
    decorator.
    @type function: function or instancemethod
    @return: True if successful, False if the function is not clearable
    @rtype: bool
    @raise: NameError, AttributeError, KeyError, TypeError or ValueError
    """
    if hasattr(function, 'func_closure'):
        if len(function.func_closure) > 1:
            if hasattr(function.func_closure[0], 'cell_contents'):
                for key in function.func_closure[0].cell_contents.keys():
                    del function.func_closure[0].cell_contents[key]

                return True
    return False


exports = {'funcDeco.CallInNewThread': CallInNewThread,
 'util.Memoized': Memoized,
 'util.ClearMemoized': ClearMemoized}
import unittest

class TestCallInNewThread(unittest.TestCase):
    THREAD_CONTEXT = 'testContext'

    def setUp(self):
        mock.SetUp(self, globals())

        def mockWorker(funcContext, func, *args, **kwargs):
            self.workerCalled = True
            self.workerContext = funcContext

        self.workerCalled = False
        uthread.worker = mockWorker
        self.value = 'none'
        self.SetUpThreadedFunctions()

    def tearDown(self):
        mock.TearDown(self)

    def SetUpThreadedFunctions(self):
        """
            We cannot define these functions until after self.setUp has mocked uthread,
            or else uthread module is "real" and these functions actually are called in a separate thread.
            This is only the case for this unit test, CallInNewThread is fine to use directly on member functions in normal code.
        """

        def NonThreaded():
            self.value = 'non'

        def UglyThreaded():
            """ Do not decorate your functions using this syntax. """
            self.value = 'ugly'

        UglyThreaded = CallInNewThread()(UglyThreaded)

        @CallInNewThread()
        def NiceThreaded():
            """ When neccessary, decorate your functions using the @ syntax. """
            self.value = 'nice'

        @CallInNewThread(self.THREAD_CONTEXT)
        def ContextThread():
            """ Provide a context to the thread, so that the profiler keeps track of the resource usage correctly. """
            self.value = 'contexted'

        @CallInNewThread()
        def NonContextThread():
            """ It is possible to use the default context, but it is preferred if you give it the correct context. """
            self.value = 'non-contexted'

        self.NonThreaded = NonThreaded
        self.UglyThreaded = UglyThreaded
        self.NiceThreaded = NiceThreaded
        self.ContextThread = ContextThread
        self.NonContextThread = NonContextThread

    def testNonThreaded(self):
        """ Functions as we normally understand them, they are executed immediately when called. """
        self.NonThreaded()
        self.assertTrue(self.value == 'non', 'NonThreaded should immediately change the value')
        self.assertTrue(not self.workerCalled, 'uthread.worker was called, a thread was queued that should not have been.')

    def testUglyThreaded(self):
        """
            Functions which use the "old" method of function decorators, ie:
            UglyThreaded = funcDeco.CallInNewThread()(UglyThreaded)
            Note, this works, it is just ugly and the fact that it is called in a thread is
              hidden by the implementation of the function iself (since it has to come after the implementation)
        """
        self.UglyThreaded()
        self.assertTrue(self.value == 'none', 'UglyThreaded should not immediately change the value')
        self.assertTrue(self.workerCalled, 'uthread.worker was not called, and thus the thread is not queued.')

    def testNiceThreaded(self):
        """
            Functions which use the "new" method of function decorators, ie:
            @funcDeco.CallInNewThread()
            Note, this is the way we should be using these function decorators whenever possible.
        """
        self.NiceThreaded()
        self.assertTrue(self.value == 'none', 'NiceThreaded should not immediately change the value')
        self.assertTrue(self.workerCalled, 'uthread.worker was not called, and thus the thread is not queued.')

    def testContextGeneration(self):
        """ Functions using CallInNewThread context variable should automatically have their context correctly attached to the thread. """
        self.ContextThread()
        self.assertTrue(self.value == 'none', 'PRECONDITION: ThreadContext should not immediately change the value')
        self.assertTrue(self.workerCalled, 'PRECONDITION: uthread.worker was not called, and thus the thread is not queued.')
        expectedContext = '^%s::ContextThread' % self.THREAD_CONTEXT
        self.assertTrue(self.workerContext == expectedContext, 'The context thread was not assembled correctly.\nExpected:\n%s\nActual:\n%s' % (expectedContext, self.workerContext))

    def testContextGeneration_Default(self):
        """ Functions using CallInNewThread context variable should automatically have their context correctly attached to the thread. """
        self.NonContextThread()
        self.assertTrue(self.value == 'none', 'PRECONDITION: ThreadContext should not immediately change the value')
        self.assertTrue(self.workerCalled, 'PRECONDITION: uthread.worker was not called, and thus the thread is not queued.')
        expectedContext = 'NonContextThread'
        self.assertTrue(self.workerContext == expectedContext, 'The default context thread is incorrect.\nExpected:\n%s\nActual:\n%s' % (expectedContext, self.workerContext))
