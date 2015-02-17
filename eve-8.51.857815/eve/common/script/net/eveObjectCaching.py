#Embedded file name: eve/common/script/net\eveObjectCaching.py
"""
Implements an object caching service for Macho
TODO: invalidate method call caches
"""
import service
import svc
globals().update(service.consts)

class EveObjectCachingSvc(svc.objectCaching):
    __guid__ = 'svc.eveObjectCaching'
    __replaceservice__ = 'objectCaching'
    __cachedsessionvariables__ = ['regionid',
     'constellationid',
     'stationid',
     'solarsystemid',
     'locationid',
     'languageID']
