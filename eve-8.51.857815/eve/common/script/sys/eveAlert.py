#Embedded file name: eve/common/script/sys\eveAlert.py
import svc

class Alert(svc.alert):
    __guid__ = 'svc.eveAlert'
    __replaceservice__ = 'alert'

    def _GetSessionInfo(self):
        """Returns userID, charID, solarSystemID2, stationID"""
        if session:
            return (session.userid,
             session.charid,
             session.solarsystemid2,
             session.stationid)
        return (None, None, None, None)
