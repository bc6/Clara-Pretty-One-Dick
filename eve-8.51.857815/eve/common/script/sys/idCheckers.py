#Embedded file name: eve/common/script/sys\idCheckers.py


def IsRegion(itemID):
    return itemID >= 10000000 and itemID < 20000000


def IsConstellation(itemID):
    return itemID >= 20000000 and itemID < 30000000


def IsSolarSystem(itemID):
    return itemID >= 30000000 and itemID < 40000000


def IsCelestial(itemID):
    return itemID >= 40000000 and itemID < 50000000


def IsStation(itemID):
    return itemID >= 60000000 and itemID < 64000000
