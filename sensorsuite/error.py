#Embedded file name: sensorsuite\error.py


class InvalidClientStateError(Exception):
    """
    This is used to indicate that the scene for some reason is no longer in a valid state.
    That generally means we should abort what we are doing and clean up
    """
    pass
