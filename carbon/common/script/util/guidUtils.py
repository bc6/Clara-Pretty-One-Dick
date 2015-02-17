#Embedded file name: carbon/common/script/util\guidUtils.py
import zlib
import uuid

def MakeGUID():
    """
    Globally-Unique Identifier
    Generate a RFC 4122 128bit uuid, and return it as an integer
    """
    return uuid.uuid4().int


def MakePUID():
    """
    Pretty-Unique Identifier
    Generate a 128bit guid, turn it into a 256bit string, then hash it down to a 32bit value
    This is hardly cryptographically secure, but it's good enough for tools that need a "pretty unique" non-sequential identifer
    """
    uuidstr = uuid.uuid4().hex
    return zlib.crc32(uuidstr)


exports = {'util.MakeGUID': MakeGUID,
 'util.MakePUID': MakePUID}
