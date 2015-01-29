#Embedded file name: carbon/common/script/entities/AI\aimingProcs.py
"""
Code required within Jessica to create and manage ActionProcs for the aiming system.
"""
from carbon.common.script.zaction.zactionCommon import ProcPropertyTypeDef, ProcTypeDef

def GetAITargetList(propRow):
    retList = []
    for target in const.aiming.AIMING_VALID_TARGETS.values():
        name = target[const.aiming.AIMING_VALID_TARGETS_FIELD_NAME]
        clientServerFlag = target[const.aiming.AIMING_VALID_TARGETS_FIELD_CLIENTSERVER_FLAG]
        if clientServerFlag != const.aiming.AIMING_CLIENTSERVER_FLAG_BOTH:
            name = name + const.aiming.AIMING_CLIENTSERVER_FLAGS[clientServerFlag]
        retList.append((name, target[const.aiming.AIMING_VALID_TARGETS_FIELD_ID], ''))

    return retList


AITarget = ('listMethod', GetAITargetList)
TargetSelect = ProcTypeDef(isMaster=False, procCategory='AI', properties=[ProcPropertyTypeDef('Target', 'I', userDataType='AITarget', isPrivate=True, displayName='Set Target'),
 ProcPropertyTypeDef('Candidate', 'I', userDataType='AICandidate', isPrivate=True, displayName='From Candidate List'),
 ProcPropertyTypeDef('Subject', 'I', userDataType='AISubject', isPrivate=True, displayName='Where Subject is'),
 ProcPropertyTypeDef('Confidence', 'I', userDataType='AIConfidence', isPrivate=True, displayName='If Confidence >='),
 ProcPropertyTypeDef('ConfidenceWeight', 'B', userDataType=None, isPrivate=True, displayName='Confidence weighting'),
 ProcPropertyTypeDef('DistanceNearest', 'B', userDataType=None, isPrivate=True, displayName='Pick Nearest'),
 ProcPropertyTypeDef('DistanceMin', 'F', userDataType=None, isPrivate=True, displayName='Minimum distance'),
 ProcPropertyTypeDef('DistanceOptimal', 'F', userDataType=None, isPrivate=True, displayName='Optimal distance'),
 ProcPropertyTypeDef('Tags', 'S', userDataType=None, isPrivate=True, displayName='Tags')], description='Select a target if possible.')
TargetSelectable = ProcTypeDef(isMaster=False, isConditional=True, procCategory='AI', properties=[ProcPropertyTypeDef('Target', 'I', userDataType='AITarget', isPrivate=True, displayName='Set Target'),
 ProcPropertyTypeDef('Candidate', 'I', userDataType='AICandidate', isPrivate=True, displayName='From Candidate List'),
 ProcPropertyTypeDef('Subject', 'I', userDataType='AISubject', isPrivate=True, displayName='Where Subject is'),
 ProcPropertyTypeDef('Confidence', 'I', userDataType='AIConfidence', isPrivate=True, displayName='If Confidence >='),
 ProcPropertyTypeDef('ConfidenceWeight', 'B', userDataType=None, isPrivate=True, displayName='Confidence weighting'),
 ProcPropertyTypeDef('DistanceNearest', 'B', userDataType=None, isPrivate=True, displayName='Pick Nearest'),
 ProcPropertyTypeDef('DistanceMin', 'F', userDataType=None, isPrivate=True, displayName='Minimum distance'),
 ProcPropertyTypeDef('DistanceOptimal', 'F', userDataType=None, isPrivate=True, displayName='Optimal distance'),
 ProcPropertyTypeDef('Tags', 'S', userDataType=None, isPrivate=True, displayName='Tags')], description='Test if a target would be selected. No target is selected')
TargetClear = ProcTypeDef(isMaster=False, procCategory='AI', properties=[ProcPropertyTypeDef('Target', 'I', userDataType='AITarget', isPrivate=True)], description='Clears the target')
TargetPreventSelect = ProcTypeDef(isMaster=False, procCategory='AI', properties=[ProcPropertyTypeDef('Target', 'I', userDataType='AITarget', isPrivate=True), ProcPropertyTypeDef('Time', 'F', userDataType=None, isPrivate=True, displayName='Time in secs')], description='Prevents re-selection of the current target for a period of time')
TargetIsSelected = ProcTypeDef(isMaster=False, isConditional=True, procCategory='AI', properties=[ProcPropertyTypeDef('Target', 'I', userDataType='AITarget', isPrivate=True)], description='Do we have a target')
TargetPreventListClearAll = ProcTypeDef(isMaster=False, procCategory='AI', properties=[ProcPropertyTypeDef('Target', 'I', userDataType='AITarget', isPrivate=True)], description='Clear the prevent selection list')
TargetSelectedEntity = ProcTypeDef(isMaster=False, procCategory='AI', properties=[ProcPropertyTypeDef('Target', 'I', userDataType='AITarget', isPrivate=True)], description="Target the player's selected entity. Used by head tracking")
TargetSelectFromHate = ProcTypeDef(isMaster=False, procCategory='AI', properties=[ProcPropertyTypeDef('Target', 'I', userDataType='AITarget', isPrivate=True, displayName='Set Target')], description='Select a target from the hate list.')
exports = {'actionProperties.AITarget': AITarget,
 'actionProcTypes.TargetSelect': TargetSelect,
 'actionProcTypes.TargetSelectable': TargetSelectable,
 'actionProcTypes.TargetClear': TargetClear,
 'actionProcTypes.TargetPreventSelect': TargetPreventSelect,
 'actionProcTypes.TargetIsSelected': TargetIsSelected,
 'actionProcTypes.TargetPreventListClearAll': TargetPreventListClearAll,
 'actionProcTypes.TargetSelectedEntity': TargetSelectedEntity,
 'actionProcTypes.TargetSelectFromHate': TargetSelectFromHate}
