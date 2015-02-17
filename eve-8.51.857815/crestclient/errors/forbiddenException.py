#Embedded file name: crestclient/errors\forbiddenException.py
from baseException import CrestClientBaseException

class ForbiddenException(CrestClientBaseException):

    def __init__(self, message):
        super(ForbiddenException, self).__init__(message, 403)
