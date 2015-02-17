#Embedded file name: signal.py
"""A dummy replacement for built-in 'signal' module on PS3."""
import sys
if sys.platform != 'PS3':
    raise RuntimeError('This is not the proper signal module!')
