#Embedded file name: carbon/common/script/zaction\MovementProcs.py
"""
Code required within Jessica to create and manage ActionProcs for movement system.
"""
import zaction
FollowMode = zaction.ProcTypeDef(isMaster=True, procCategory='Movement', properties=[zaction.ProcPropertyTypeDef('FOLLOW_RANGE', 'F', userDataType=None, isPrivate=True), zaction.ProcPropertyTypeDef('FOLLOW_TELEPORT_ON_STUCK', 'B', userDataType=None, isPrivate=True), zaction.ProcPropertyTypeDef('FOLLOW_MIN_RANGE', 'F', userDataType=None, isPrivate=True)])
IsInMovementMode = zaction.ProcTypeDef(isMaster=True, isConditional=True, procCategory='Movement', displayName='Is in movement mode', properties=[zaction.ProcPropertyTypeDef('evaluateTo', 'B', userDataType=None, isPrivate=True, displayName='Evaluate To True', default=True), zaction.ProcPropertyTypeDef('moveModeName', 'S', userDataType=None, isPrivate=True, displayName='Move Mode Name')], description='Validates if we are in a movement mode.')
TargetedJumpMode = zaction.ProcTypeDef(isMaster=True, procCategory='Movement', displayName='Targeted Jump', description='Initiates a targeted jump movement mode.')
HasTargetedJumpModeJumped = zaction.ProcTypeDef(isMaster=True, isConditional=True, procCategory='Movement', displayName='Has targeted jump mode jumped', properties=[zaction.ProcPropertyTypeDef('evaluateTo', 'B', userDataType=None, isPrivate=True, displayName='Evaluate To True', default=True)], description='Validates if the targeted jump mode has jumped.')
IsWaitingForMoveModeActivation = zaction.ProcTypeDef(isMaster=True, isConditional=True, procCategory='Movement', displayName='Is Wating For Move Mode Activation', properties=[zaction.ProcPropertyTypeDef('evaluateTo', 'B', userDataType=None, isPrivate=True, displayName='Evaluate To True', default=True)], description='Check to see if the current entity move mode manager needs to activate a move mode.')
exports = {'actionProcTypes.FollowMode': FollowMode,
 'actionProcTypes.IsInMovementMode': IsInMovementMode,
 'actionProcTypes.TargetedJumpMode': TargetedJumpMode,
 'actionProcTypes.HasTargetedJumpModeJumped': HasTargetedJumpModeJumped,
 'actionProcTypes.IsWaitingForMoveModeActivation': IsWaitingForMoveModeActivation}
