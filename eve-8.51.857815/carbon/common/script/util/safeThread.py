#Embedded file name: carbon/common/script/util\safeThread.py
"""
This class is designed to be the parent class of a service running a utility loop.
It does the following:
     1: Execute the SafeThreadLoop function in a separate thread infinitely until a termination indication is given
     2: IF DEBUG MODE IS ENABLED
         1: Provide debug information to Jessica about the nature of the exception
         2: Halt _ALL_ threads in the process and set a pdb trace as close as possible to the exception
             i: context of the exception is preserved since this class is extended
             ii: NEW: the utility thread can restart itself, resetting all vital data, and continuing execution after debuging
         3: Loop the provided function infinitely until an exception or termination call
"""
from timerstuff import ClockThis
import uthread
import blue
import debug
import sys
import traceback
import log
import const

class SafeThread(object):
    """
        Creates a thread, loops, calling a function in that thread infinitely until the class is ordered to stop execution.
        Provides extra debuging ability to Jessica in Debug mode.
        Preserves context of exceptions for easier debuging
    """
    __guid__ = 'safeThread.SafeThread'
    KILL_ME = 145686248
    MAX_REPAIR_ATTEMPTS = 10

    def init(self, uniqueIDstring):
        """ The startup function for SafeThread.  Call explicitly in __init__ for child class
        *First parameter is a string - a unique identifier for this thread"""
        args = blue.pyos.GetArg()[1:]
        if ('/debug' in args or '/jessica' in args) and not prefs.GetValue('neverDebug', False):
            self.__debugging = False
            self.MAX_REPAIR_ATTEMPTS = 1000
        else:
            self.__debugging = False
        self.uniqueIDstring = uniqueIDstring
        self.__killLoop = True
        self.__thread = None
        self.__active = False
        self.rep = True
        self.repairCount = 0
        self.__sleepTime = None

    def __MainLoop(self):
        """ This function operates in it's own thread, outside of the rest of the class. """
        blue.pyos.synchro.Yield()
        try:
            while self.__killLoop == False:
                now = blue.os.GetWallclockTime()
                if self.__debugging:
                    try:
                        if ClockThis(self.uniqueIDstring + '::SafeThreadLoop', self.SafeThreadLoop, now) == self.KILL_ME:
                            self.__killLoop = True
                    except SystemExit:
                        raise
                    except TaskletExit:
                        self.__killLoop = True
                    except Exception as inst:
                        self.__killLoop = True
                        print 'SafeThread.__MainLoop - Unhandled Exception: ' + self.uniqueIDstring
                        print 'Repair attempts remaining:', self.MAX_REPAIR_ATTEMPTS - self.repairCount - 1, '\n'
                        log.LogException()
                        print traceback.print_tb(sys.exc_info()[2])
                        print inst
                        print inst.__doc__
                        debug.startDebugging()
                        uthread.new(self.__RestoreSafeThreadLoop)

                else:
                    try:
                        if ClockThis(self.uniqueIDstring + '::SafeThreadLoop', self.SafeThreadLoop, now) == self.KILL_ME:
                            self.__killLoop = True
                    except SystemExit:
                        raise
                    except TaskletExit:
                        self.__killLoop = True
                    except Exception as e:
                        self.__killLoop = True
                        print 'SafeThread.__MainLoop - Unhandled Exception: ' + self.uniqueIDstring, '\n    Debug mode is off, skipping straight to repair'
                        print 'Repair attempts remaining:', self.MAX_REPAIR_ATTEMPTS - self.repairCount - 1, '\n'
                        print traceback.print_tb(sys.exc_info()[2])
                        log.LogException()
                        uthread.new(self.__RestoreSafeThreadLoop)
                        self.__thread = None
                        self.__active = False
                        self.__killLoop = True
                        raise e

                blue.pyos.synchro.SleepWallclock(self.__sleepTime)

            self.__thread = None
            self.__active = False
        except AttributeError:
            sys.exc_clear()

    def SafeThreadLoop(self, now):
        """ Virtual function to be implemented by child class.
        This function is the funcion which is called in the looping mechanism for this class """
        print 'ERROR: Please implement the virtual SafeThreadLoop function'
        return self.KILL_ME

    def KillLoop(self):
        """ the mainLoop will do the actual termination, this just flags the termination
        termination is not immediate, termination occurs at the END of the current loop """
        self.__killLoop = True

    def Disabledebugging(self):
        """ toggle debugging off
        toggle is not immediate, debugging stops at the BEGINING of the NEXT loop """
        self.__debugging = False

    def Enabledebugging(self):
        """ toggle debugging on
        toggle is not immediate, debugging starts at the BEGINING of the NEXT loop """
        self.__debugging = True

    def LaunchSafeThreadLoop_MS(self, sleepTime = 16):
        """ This function initializes the SafeThreadLoop function in a repetative loop
        Call this function when the utility loop is supposed to begin. """
        if self.__active == False:
            self.__sleepTime = sleepTime
            self.__active = True
            self.__killLoop = False
            self.__thread = uthread.new(self.__MainLoop)
            self.__thread.context = self.uniqueIDstring
        else:
            log.LogError('ERROR: This class is already looping SafeThreadLoop function', self)

    def LaunchSafeThreadLoop_BlueTime(self, sleepTime = const.ONE_TICK):
        self.LaunchSafeThreadLoop_MS(sleepTime / const.MSEC)

    def __RestoreSafeThreadLoop(self):
        """ This function attempts to recover SafeThreadLoop function and resume the loop
        this MUST be called as a new thread separate from the loop execution thread, or there will be no progress. """
        if self.repairCount < self.MAX_REPAIR_ATTEMPTS:
            self.repairCount += 1
            self.__WaitForRestart()
            if self.rep:
                self.RepairMe()
            self.LaunchSafeThreadLoop_MS(self.__sleepTime)

    def __WaitForRestart(self):
        """ This function stalls until the current thread for the SafeThreadLoop terminates. """
        while self.__active == True or self.__killLoop == False or self.__thread is not None:
            blue.pyos.synchro.SleepUntilWallclock(blue.os.GetWallclockTimeNow() + 100 * const.MSEC)

    def RepairMe(self):
        """ Virtual repair function.
        This function should be extended by the child class, and equipped to handle restarting the thread. """
        pass


def SleepAndCallAtTime(launchTime, function, *args, **kwargs):
    """
    Makes the current thread sleep and call a function after a specific period of time.
    """
    if blue.os.GetWallclockTimeNow() < launchTime:
        blue.pyos.synchro.SleepUntilWallclock(launchTime)
    else:
        blue.pyos.synchro.Yield()
    function(*args, **kwargs)


def DoMethodLater(waitDuration, launchFunction, *args, **kwargs):
    """
    Launches a new thread. On the new thread, it sleeps for 'waitTime' and then calls 'launchFunction' with the specified arguments.
    waitDuration is in blue time!
    """
    launchTime = blue.os.GetWallclockTime() + waitDuration
    uthread.worker(('doMethodLater-' + launchFunction.__name__), SleepAndCallAtTime, launchTime, launchFunction, *args, **kwargs)


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('safeThread', globals())
