#Embedded file name: carbon/common/script/net\crestExceptions.py
"""
    CREST specific exception. Included here in common because we want to add them
    to the whitelist
"""
import exceptions

class CrestSessionExists(Exception):
    """
    This exception is raised on SOLs when a MachoSession exists that we just tried to create for CREST
        - It is whitelisted to be machonet transported
        - It stores the oldProxyID of the old session
    """

    def __init__(self, oldProxyID = None):
        super(CrestSessionExists, self).__init__()
        self.oldProxyID = oldProxyID


class CrestSessionNeedsUsurpError(Exception):
    """ Raised to signal that the framework needs to perform session usurpation and reattempt the call
        tokenToBlacklist is the token that should be deemed invalid
    """

    def __init__(self, sidToTokenMapToBlacklist):
        super(CrestSessionNeedsUsurpError, self).__init__()
        self.sidToTokenMapToBlacklist = sidToTokenMapToBlacklist


exceptions.CrestSessionExists = CrestSessionExists
exceptions.CrestSessionNeedsUsurpError = CrestSessionNeedsUsurpError
