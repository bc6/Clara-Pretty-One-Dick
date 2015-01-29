#Embedded file name: eve/client/script/ui/login\antiaddiction.py
"""
Anti-addiction play time monitoring, as required by Chinese laws.
"""
import blue
import log
import uthread
import localization
import bluepy
historyVersion = 7

def OnLogin():
    """
    Check playing time limits for underage players in the Chinese server, to 
    comply with anti-addiction laws.  
    
    Called after successful login, but before char selection is entered.  
    
    If a player is eligible for anti-addiction control, game exit and related
    warnings are executed immediately or scheduled, depending on how longer
    the law allows her to play.
    """
    global _savePeriod
    global _displaySeconds
    global _watchSpan
    global _allowedTime
    global _schedule
    if boot.region != 'optic' or not AmIUnderage():
        return
    if prefs.GetValue('aaTestTimes', 0):
        _watchSpan = _testWatchSpan
        _allowedTime = _testAllowedTime
        _schedule = _testSchedule
        _savePeriod = _testSavePeriod
        _displaySeconds = True
    else:
        _watchSpan = _liveWatchSpan
        _allowedTime = _liveAllowedTime
        _schedule = _liveSchedule
        _savePeriod = _liveSavePeriod
        _displaySeconds = False
    sessionID = StartSession()
    uthread.worker('antiaddiction::EndSession', lambda : EndSessionWorker(sessionID))

    def ActionWrap(action, time):
        return lambda : action(time)

    t = TimeLeft()
    for time, action in _schedule:
        if t <= time:
            action(t)
            break
        else:
            Schedule(t - time, ActionWrap(action, time))


class Session:
    __guid__ = 'antiaddiction.Session'

    def __init__(self, sessionID, startTime, endTime):
        self.sessionID = sessionID
        self.start = startTime
        self.end = endTime

    def Save(self):
        return '%s:%s:%s' % (self.sessionID, self.start.Seconds(), self.end.Seconds())

    def Load(cls, s):
        sessionID, startSecs, endSecs = map(long, s.split(':'))
        return cls(sessionID, Seconds(startSecs), Seconds(endSecs))

    Load = classmethod(Load)

    def PreLoad(cls, r):
        sessionID, startSecs, endSecs = r
        return cls(sessionID, Seconds(int(str(startSecs)[0:11])), Seconds(int(str(endSecs)[0:11])))

    PreLoad = classmethod(PreLoad)

    def __repr__(self):
        return '<session %s (%s secs)>' % (self.sessionID, (self.end - self.start).Seconds())


def StartSession():
    h = LoginHistory(1)
    if h:
        sessionID = h[-1].sessionID + 1
    else:
        sessionID = 1
    SaveHistory(h + [Session(sessionID, Now(), Now())])
    return sessionID


def EndSessionWorker(sessionID):
    while True:
        EndSession(sessionID)
        blue.pyos.synchro.SleepWallclock(_savePeriod.Milliseconds())


def EndSession(sessionID):
    h = LoginHistory()
    for session in h:
        if session.sessionID == sessionID:
            session.end = Now()
            SaveHistory(h)
            break
    else:
        log.LogError('antiaddiction.EndSession: session not found')


def SaveHistory(h):
    settings.user.ui.Set(HistoryKey(), map(Session.Save, h))


def HistoryKey():
    return 'aaLoginHistory_%s' % historyVersion


def LoginHistory(init = 0):
    """
    Return a list of play session objects, each of which has the following 
    attributes:
        start:
            A timestamp representing the time this session was started.
        end:
            A timestamp representing the time this session finished.
            
    All times are clamped to be no older than eight hours ago.  Sessions older
    than that are deleted.
    """
    if init == 1:
        h = map(Session.PreLoad, GetAccruedTime())
    else:
        h = map(Session.Load, settings.user.ui.Get(HistoryKey(), []))
    for session in h[:]:
        if session.end < ForgetTime():
            h.remove(session)

    if h and h[0].start < ForgetTime():
        h[0].start = ForgetTime()
    return h


def KickPlayer():
    """
    Display a farewell message and exit the game.
    """
    Schedule(Seconds(20), bluepy.Terminate)
    eve.Message('AntiAddictionTimeExceeded', {'waitTime': WaitLeft().displayStr()})
    bluepy.Terminate()


def TimeWarning(timeLeft):
    """
    An ostensible, but intrusive, warning that play time is running out.  
    
    This is only shown right when her time is running out, so she can leave her
    char in safety.
    """
    accruedTime = _allowedTime - timeLeft
    eve.Message('AntiAddictionTimeWarning', {'accruedTime': accruedTime.displayStr(),
     'timeLeft': timeLeft.displayStr()})


def TimeNotify(timeLeft):
    """
    An unobtrusive, but easy to miss, warning that accrued time is building up.
    
    The player will get other warning(s) later, so it's better to risk that she 
    misses this one than to annoy her.  We are required by law to always 
    display this, though, so we can't use a supressable dialog.
    """
    accruedTime = _allowedTime - timeLeft
    eve.Message('AntiAddictionTimeNotify', {'accruedTime': accruedTime.displayStr()})


def TimeLeft():
    """
    The time this playing session can last before the player is kicked.
    """
    history = LoginHistory()
    accrued = SumTimes(map(SessionDuration, history))
    for start, duration in Blanks(history):
        accrued += duration
        excess = accrued - _allowedTime
        if excess > NoTime():
            return start - ForgetTime() + (duration - excess)


def Blanks(history):
    """
    Generate the lapses of time that the player spent *out* of the game in the 
    latest _watchSpan, as (start, duration) pairs.
    """
    last = ForgetTime()
    for session in history:
        yield (last, session.start - last)
        last = session.end

    yield (last, Now() - last)


def SumTimes(times):
    return reduce(Time.__add__, times, NoTime())


def SessionDuration(s):
    return s.end - s.start


def Now():
    return BlueTime(blue.os.GetWallclockTime())


def WaitLeft():
    """
    The time the player must wait before she can play again.
    
    Note: This assumes that the player can't play right away.  Don't call this
    otherwise.
    """
    return LoginHistory()[0].start - ForgetTime()


def ForgetTime():
    return Now() - _watchSpan


def Schedule(time, action):

    def f():
        blue.pyos.synchro.SleepWallclock(time.Milliseconds())
        action()

    uthread.new(f)


def AmIUnderage():
    return sm.RemoteSvc('authentication').AmUnderage()


def GetAccruedTime():
    return sm.RemoteSvc('authentication').AccruedTime()


def NoTime():
    return Time(0)


def Seconds(s):
    return Time(s)


def Minutes(m):
    return Seconds(m * 60)


def Hours(h):
    return Minutes(h * 60)


def BlueTime(bt):
    """
    Get a Time corresponding to the return value of blue.os.GetWallclockTime().
    
    Note: This may lose precision (up to one second, at the time of this
    writing.)  
    """
    return Time(bt // 10000000)


class Time:
    """
    Convenience class for instants and time spans.
    """
    __guid__ = 'util.Time'

    def __init__(self, secs):
        self._secs = secs

    def Milliseconds(self):
        return self._secs * 1000

    def Seconds(self):
        return self._secs

    def Minutes(self):
        return self.Seconds() // 60

    def Hours(self):
        return self.Minutes() // 60

    def __add__(self, other):
        return Time(self._secs + other._secs)

    def __sub__(self, other):
        return Time(self._secs - other._secs)

    def __cmp__(self, other):
        return cmp(self._secs, other._secs)

    def displayStr(self):
        """
        Localized display string suitable to show onscreen.
        """
        timeVal = self.Seconds() * const.SEC
        showTo = 'minute'
        if _displaySeconds:
            showTo = 'second'
        return localization.formatters.FormatTimeIntervalWritten(timeVal, showFrom='year', showTo=showTo)

    def __repr__(self):
        label = localization.GetByLabel('/Carbon/UI/Common/DateTimeQuantity/DateTimeShort3Elements', value1=int(self.Hours()), value2=int(self.Minutes() % 60), value3=int(self.Seconds() % 60))
        return '<Time: %s>' % label


_liveWatchSpan = Hours(24)
_testWatchSpan = Minutes(24)
_liveAllowedTime = Hours(3)
_testAllowedTime = Minutes(3)
_liveSchedule = [(NoTime(), lambda blah: KickPlayer()),
 (Minutes(5), TimeWarning),
 (Minutes(15), TimeWarning),
 (Hours(1), TimeWarning),
 (Hours(2), TimeWarning)]
_testSchedule = [(NoTime(), lambda blah: KickPlayer()),
 (Seconds(5), TimeWarning),
 (Seconds(15), TimeWarning),
 (Minutes(1), TimeWarning),
 (Minutes(2), TimeWarning)]
_liveSavePeriod = Minutes(1)
_testSavePeriod = Seconds(1)
import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('antiaddiction', locals())
