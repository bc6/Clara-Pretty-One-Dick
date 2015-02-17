#Embedded file name: eve/client/script/ui/shared/inventory\invCommon.py
CONTAINERGROUPS = (const.groupCargoContainer,
 const.groupSecureCargoContainer,
 const.groupAuditLogSecureContainer,
 const.groupFreightContainer)

def SortData(data):
    data.sort(key=lambda x: x.GetLabel().lower())
