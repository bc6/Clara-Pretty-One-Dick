#Embedded file name: localizationBSD\__init__.py
from . import util, const

def _HasBsdWrappers():
    try:
        import bsdWrappers
        return True
    except ImportError:
        return False


if _HasBsdWrappers():
    from wrappers import AuthoringValidationError
    from wrappers.message import Message
    from wrappers.messageGroup import MessageGroup
    from wrappers.messageText import MessageText
    from wrappers.project import Project
    from wrappers.wordMetaData import WordMetaData
    from wrappers.wordProperty import WordProperty
    from wrappers.wordType import WordType
