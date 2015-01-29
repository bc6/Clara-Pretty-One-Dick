#Embedded file name: eve/client/script/util\webutils.py
__author__ = 'aevar'
import sys
import urllib
import utillib as util
import log

class WebUtils:

    @staticmethod
    def GetWebRequestParameters():
        """
        returns a string containing client and system identifying parameters which can be used
        to deliver focused content based on server and language
        The string is delivered as so: "k1=v1&k2=v2&". It does not include the starting '?' or '&' symbol
        for a querystring. Also keep in mind that any parameters that come after this should not start with '&'
        
        You must be careful that there is no parameter clashing if you're already providing some yourself.
        
        example output: s=Tranquility&language_id=EN
        """
        details = {}
        try:
            details['s'] = util.GetServerName()
            details['language_id'] = prefs.GetValue('languageID', 'EN')
        except:
            log.LogException(toAlertSvc=0)
            sys.exc_clear()

        queryString = urllib.urlencode(details)
        return queryString
