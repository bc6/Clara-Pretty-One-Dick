#Embedded file name: crestclient/errors\baseException.py


class CrestClientBaseException(Exception):

    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '%d - %s' % (self.status_code, self.message)
