#Embedded file name: eveexceptions\exceptionEater.py
"""
    Authors:   Brian Bosse (ported into package by Charles)
    Created:   30May2011
    Project:   Eve

    Description: This class exists to wrap up a block of code in such a way that any exception
                 thrown from it will be logged and eaten, allowing flow to continue uninterrupted.

                 This is useful in cases where it's absolutely critical that a sequence of events
                 are all tried, regardless of the success of the previous tasks.
"""
import logging

class ExceptionEater(object):

    def __init__(self, message = '', channel = None):
        """
        :param message: formatted string to display with exception
        :param channel: the channel name to output too
        """
        self.message = message
        self.channel = channel

    def __enter__(self):
        pass

    def __exit__(self, eType, eVal, tb):
        if eType is not None:
            logger = None
            if self.channel:
                logger = logging.getLogger(self.channel)
            else:
                logger = logging.getLogger(__name__)
            logger.exception(self.message)
        return True
