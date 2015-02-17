#Embedded file name: carbon/common/script/entities/AI\hateProcs.py
"""
Code required within Jessica to create and manage ActionProcs for Hate system.
"""
from carbon.common.script.zaction.zactionCommon import ProcTypeDef
HateTarget = ProcTypeDef(isMaster=False, procCategory='AI', description='Increase my hatred of my target')
HateMe = ProcTypeDef(isMaster=False, procCategory='AI', description="Increase the target's hatred of me")
HateRemoveTarget = ProcTypeDef(isMaster=False, procCategory='AI', description='Remove target from my hate list')
HateRemoveMeFromAll = ProcTypeDef(isMaster=False, procCategory='AI', description="Removes all other's hatred of me")
HateRemoveAllFromMe = ProcTypeDef(isMaster=False, procCategory='AI', description='Removes all my hatred of others')
exports = {'actionProcTypes.HateTarget': HateTarget,
 'actionProcTypes.HateMe': HateMe,
 'actionProcTypes.HateRemoveTarget': HateRemoveTarget,
 'actionProcTypes.HateRemoveMeFromAll': HateRemoveMeFromAll,
 'actionProcTypes.HateRemoveAllFromMe': HateRemoveAllFromMe}
