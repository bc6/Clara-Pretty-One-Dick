#Embedded file name: ccpProfile\__init__.py
"""Decorators for profiling functions.
Swaps implementations based on available modules,
falling back to a noop implementation.
"""
try:
    from . import blueTaskletImplementation as implementation
except (ImportError, AttributeError):
    from . import noopImplementation as implementation

Timer = implementation.Timer
TimerPush = implementation.TimerPush
TimedFunction = implementation.TimedFunction
PushTimer = implementation.PushTimer
PopTimer = implementation.PopTimer
CurrentTimer = implementation.CurrentTimer
EnterTasklet = implementation.EnterTasklet
ReturnFromTasklet = implementation.ReturnFromTasklet
