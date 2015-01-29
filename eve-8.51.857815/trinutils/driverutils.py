#Embedded file name: trinutils\driverutils.py
import trinity

class CannotIdentifyDriverException(Exception):

    def __init__(self, vendor, description = 'NA'):
        msg = str("Unable to retrieve info from %s card. Please ensure that you're using the right drivers or graphics card. /nDriver Description: %s" % (vendor, description))
        super(Exception, self).__init__(self, msg)


def GetDriverVersion():
    adapter = trinity.adapters.GetAdapterInfo(trinity.adapters.DEFAULT_ADAPTER)
    if 'nvidia' not in adapter.description.lower():
        raise CannotIdentifyDriverException('Unknown', adapter.description)
    try:
        info = adapter.GetDriverInfo()
    except trinity.ALError:
        raise CannotIdentifyDriverException('NVidia', adapter.description)

    def getDriverVersionNumber(driverInfo):
        verInfo = driverInfo.driverVersionString.replace('.', '')
        return int(verInfo[-5:])

    return getDriverVersionNumber(info)
