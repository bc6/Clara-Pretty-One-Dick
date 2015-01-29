#Embedded file name: carbon/common/lib\markers.py
import sys
import blue
import bluepy
GetCurrent = blue.pyos.taskletTimer.GetCurrent
ClockThis = sys.ClockThis

def Mark(context, function, *args, **kw):
    """
    Mark(context, function, ...) -> value
    Marks the current execution context (tasklet timer context string). CPU and memory
    usage in 'function' will be associated with the new context.
    
    The Mark function will return the value from 'function'.
    """
    return ClockThis(context, function, *args, **kw)


def PushMark(context):
    """
    PushMark(context) -> None
    Sets a context string to the current execution. Complement with PopMark plz.
    """
    return bluepy.PushTimer(context)


PopMark = bluepy.PopTimer
