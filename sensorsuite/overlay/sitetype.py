#Embedded file name: sensorsuite/overlay\sitetype.py
ANOMALY = 1
SIGNATURE = 2
STATIC_SITE = 3
BOOKMARK = 4
CORP_BOOKMARK = 5
MISSION = 6
PERSONAL_SITE_TYPES = (BOOKMARK, CORP_BOOKMARK, MISSION)

def IsSiteInstantlyAccessible(siteData):
    return siteData.siteType in PERSONAL_SITE_TYPES
