#Embedded file name: carbon/common/script/zaction\AnimationProcs.py
"""
Code required within Jessica to create and manage ActionProcs for Animation system.
"""
import blue
import yaml
from carbon.common.script.zaction.zactionCommon import ProcPropertyTypeDef, ProcTypeDef, ProcNameHelper
animInfoDict = None

def GetAnimInfo():
    global animInfoDict
    if animInfoDict is None:
        dataFile = blue.ResFile()
        dataFile.Open('res:/Animation/animInfo.yaml')
        animInfoDict = yaml.load(dataFile)
        dataFile.close()
    return animInfoDict


def GetAnimPropertyByName(animName, propertyName):
    animInfo = GetAnimInfo()
    anim = animInfo.get(animName, None)
    if anim is not None:
        return anim.get(propertyName, None)


def _AnimationProcNameHelper(name, procRow):
    propDict = {}
    animName = propDict.get('AnimName', 'None')
    duration = GetAnimPropertyByName(animName, 'duration')
    if duration is None:
        duration = 0.0
    displayName = 'PerformAnim ' + animName + ' for ' + str(duration) + ' sec'
    return displayName


def AnimationProcNameHelper(name):
    return lambda procRow: _AnimationProcNameHelper(name, procRow)


def GetControlParameters(propRow):
    validList = ['HeadLookWeight',
     'HeadBlendSpeed',
     'Aim_X',
     'Aim_Y',
     'AllowFidgets']
    retList = []
    for param in validList:
        retList.append((param, param, ''))

    retList.sort()
    return retList


ControlParameters = ('listMethod', GetControlParameters)
OrAllCondition = ProcTypeDef(isMaster=True, isConditional=True, procCategory='Condition', displayName=' Or All', properties=[ProcPropertyTypeDef('NegateAll', 'B', isPrivate=True, default=False)], description="Conditional procs can be used to modify the result of a conditional step or prereq container. Only a single Conditional proc will be respected, so don't use more than one. \n\nOr All: For all procs in this ProcContainer, evaluate to True if any of them returns True.\nThe Negate All option will cause this to evaluate True if any of them returns False.")
AndAllCondition = ProcTypeDef(isMaster=True, isConditional=True, procCategory='Condition', displayName=' And All', properties=[ProcPropertyTypeDef('NegateAll', 'B', isPrivate=True, default=False)], description="Conditional procs can be used to modify the result of a conditional step or prereq container. Only a single Conditional proc will be respected, so don't use more than one. \n\nAnd All: For all procs in this ProcContainer, evaluate to True if all of them return True. This is the default behavior for ProcContainers so... you may not even need this unless you use...\nThe Negate All option will cause this to evaluate True if all of them return False.")
NotCondition = ProcTypeDef(isMaster=True, isConditional=True, procCategory='Condition', displayName=' Not', properties=[], description="Conditional procs can be used to modify the result of a conditional step or prereq container. Only a single Conditional proc will be respected, so don't use more than one. \n\nNot: For all procs in this ProcContainer, evaluate to True if all of them return False. ")
XorCondition = ProcTypeDef(isMaster=True, isConditional=True, procCategory='Condition', displayName=' Xor', properties=[ProcPropertyTypeDef('NegateAll', 'B', isPrivate=True, default=False)], description="Conditional procs can be used to modify the result of a conditional step or prereq container. Only a single Conditional proc will be respected, so don't use more than one. \n\nXor: For all procs in this ProcContainer, evaluate to True if exactly one of them is True.\nThe Negate All option will cause this to evaluate True if not exactly one is True.")
ComplexCondition = ProcTypeDef(isMaster=True, isConditional=True, procCategory='Condition', displayName=' Complex Condition %(ConditionEvalString)s', properties=[ProcPropertyTypeDef('ConditionEvalString', 'S', isPrivate=True)], description="Conditional procs can be used to modify the result of a conditional step or prereq container. Only a single Conditional proc will be respected, so don't use more than one. \n\nComplex: The ConditionEvalString is a reverse polish notation string with ,&|! as delimiters. Specific procs are referenced by their proc IDs.\n\nFor example, if you want the condition to evaluate true if Proc 4 and Proc 11 are True or Proc 8  is False, then you would use the EvalString:\n4,11&8!|\n\nYes, we realize this is fugly, but until enough people are even using it that it matters, it's not really in the schedule to make the user interface for this especially usable.")
ChangeAction = ProcTypeDef(isMaster=True, procCategory='Action', displayName=ProcNameHelper('ChangeAction to %(NewAction)s'), properties=[ProcPropertyTypeDef('NewAction', 'I', userDataType='ActionChildrenAndSiblingsList', isPrivate=True)], description='Attempt to transition from the current action on this tree instance to another action in thesame tree. This requires valid availability on the action tree.\n\nThis will not allow you to begin actions on other trees. IE, buffs cannot start decision actions')
ExitAction = ProcTypeDef(isMaster=True, procCategory='Action', properties=[], description='Clear the current actions step stack causing this action to finish upon completion of the step.')
LogMessage = ProcTypeDef(isMaster=True, procCategory='General', properties=[ProcPropertyTypeDef('LogCategory', 'I', userDataType='LogCategory', isPrivate=True), ProcPropertyTypeDef('LogMessage', 'S', isPrivate=True)], description='Output a message to the log server.')
WaitForTime = ProcTypeDef(isMaster=True, procCategory='General', properties=[ProcPropertyTypeDef('Duration', 'F', isPrivate=True)], description='Hold the current step open for a fixed amount of time.')
CooldownForTime = ProcTypeDef(isMaster=True, isConditional=True, procCategory='General', properties=[ProcPropertyTypeDef('Duration', 'F', isPrivate=True)])
CreateProperty = ProcTypeDef(isMaster=False, isConditional=False, procCategory='General', properties=[ProcPropertyTypeDef('CreateName', 'S', isPrivate=True), ProcPropertyTypeDef('CreateType', 'S', userDataType='PropertyType', isPrivate=True), ProcPropertyTypeDef('CreateValue', 'S', isPrivate=True)], description='Create a public property in the Action PropertyList.')
WaitForever = ProcTypeDef(isMaster=True, procCategory='General', description='Hold the current step open forever. Note that this should only ever be used within a try block.')
LogPropertyList = ProcTypeDef(isMaster=True, procCategory='General', description='Output the entire contents of the current actions property list to the log server. Spammy.')
HasTargetList = ProcTypeDef(isMaster=True, procCategory='Target', isConditional=True, description='Returns True if the target list contains at least a single target.')
StartTargetAction = ProcTypeDef(isMaster=True, procCategory='Action', properties=[ProcPropertyTypeDef('TargetAction', 'I', userDataType='ActionList', isPrivate=False)], description='Starts an action in the action tree on the first entity in the target list.\n\nUseful for syncing actions.')
HasLockedTarget = ProcTypeDef(isMaster=True, procCategory='Target', isConditional=True, description='Returns true if a synced action has set a locked target.\n\nUseful for syncing actions.')
UseLockedTarget = ProcTypeDef(isMaster=True, procCategory='Target', description='Takes the current locked target it and places it in the TargetList property\n\nUseful for syncing actions.')
CanTargetStartAction = ProcTypeDef(isMaster=True, procCategory='Action', isConditional=True, properties=[ProcPropertyTypeDef('TargetAction', 'I', userDataType='ActionList', isPrivate=False)], description='Returns true if the target entity can validly request the specified action.\n\nUseful for syncing actions.')
CanLockedTargetStartAction = ProcTypeDef(isMaster=True, procCategory='Action', isConditional=True, properties=[ProcPropertyTypeDef('TargetAction', 'I', userDataType='ActionList', isPrivate=False)], description='Returns true if the locked target can validly request the specified action.\n\nUseful for syncing actions.')
PerformAnim = ProcTypeDef(isMaster=True, procCategory='Animation', displayName=AnimationProcNameHelper('%(AnimName)s'), properties=[ProcPropertyTypeDef('AnimName', 'S', userDataType='AnimationListDialogWrapper', isPrivate=True)], description='Will attempt to perform the specified animation request as defined in the animInfo.yaml')
SetPose = ProcTypeDef(isMaster=True, procCategory='Animation', displayName='SetPose %(AnimName)s', properties=[ProcPropertyTypeDef('AnimName', 'S', userDataType=None, isPrivate=True)])
PerformSyncAnim = ProcTypeDef(isMaster=True, procCategory='Animation', displayName='PerformSyncAnim %(AnimName)s', properties=[ProcPropertyTypeDef('AnimName', 'S', userDataType=None, isPrivate=True)])
FaceTarget = ProcTypeDef(isMaster=True, procCategory='Animation', description="Causes the current entity to turn and face it's target.")
IsFacingTarget = ProcTypeDef(isMaster=True, procCategory='Animation', isConditional=True, properties=[ProcPropertyTypeDef('TargetFacingAngle', 'F', isPrivate=True)], description="Returns true if the current entity is facing it's target.")
SetSyncAnimEntry = ProcTypeDef(isMaster=False, procCategory='Animation', displayName='SetSyncAnimEntry %(AnimName)s', properties=[ProcPropertyTypeDef('AnimName', 'S', userDataType=None, isPrivate=True)])
GetEntryFromAttacker = ProcTypeDef(isMaster=False, procCategory='Animation')
IsEntityInRange = ProcTypeDef(isMaster=False, isConditional=True, procCategory='Animation', properties=[ProcPropertyTypeDef('Range', 'F', userDataType=None, isPrivate=True)], description='Returns true if the target entity is within the specified range.')
SlaveMode = ProcTypeDef(isMaster=True, procCategory='Animation', properties=[ProcPropertyTypeDef('BoneName', 'S', userDataType=None, isPrivate=True)])
AlignToMode = ProcTypeDef(isMaster=True, procCategory='Animation')
PathToMode = ProcTypeDef(isMaster=True, procCategory='Animation', properties=[ProcPropertyTypeDef('PathDistance', 'F', userDataType=None, isPrivate=True)], description='Paths the requesting entity to within the specified distance of the ALIGN_POS.')
WanderMode = ProcTypeDef(isMaster=True, procCategory='Animation')
RestoreMoveMode = ProcTypeDef(isMaster=True, procCategory='Animation')
RestoreTargetMoveMode = ProcTypeDef(isMaster=True, procCategory='Animation')
SetControlParameter = ProcTypeDef(isMaster=False, procCategory='Animation', properties=[ProcPropertyTypeDef('Parameter', 'S', userDataType='ControlParameters', isPrivate=True), ProcPropertyTypeDef('Value', 'F', userDataType=None, isPrivate=True)])
exports = {'actionProperties.ControlParameters': ControlParameters,
 'actionProcTypes.OrAllCondition': OrAllCondition,
 'actionProcTypes.AndAllCondition': AndAllCondition,
 'actionProcTypes.NotCondition': NotCondition,
 'actionProcTypes.XorCondition': XorCondition,
 'actionProcTypes.ComplexCondition': ComplexCondition,
 'actionProcTypes.ChangeAction': ChangeAction,
 'actionProcTypes.ExitAction': ExitAction,
 'actionProcTypes.LogMessage': LogMessage,
 'actionProcTypes.WaitForTime': WaitForTime,
 'actionProcTypes.CooldownForTime': CooldownForTime,
 'actionProcTypes.CreateProperty': CreateProperty,
 'actionProcTypes.WaitForever': WaitForever,
 'actionProcTypes.LogPropertyList': LogPropertyList,
 'actionProcTypes.HasTargetList': HasTargetList,
 'actionProcTypes.StartTargetAction': StartTargetAction,
 'actionProcTypes.HasLockedTarget': HasLockedTarget,
 'actionProcTypes.UseLockedTarget': UseLockedTarget,
 'actionProcTypes.CanTargetStartAction': CanTargetStartAction,
 'actionProcTypes.CanLockedTargetStartAction': CanLockedTargetStartAction,
 'actionProcTypes.PerformAnim': PerformAnim,
 'actionProcTypes.SetPose': SetPose,
 'actionProcTypes.PerformSyncAnim': PerformSyncAnim,
 'actionProcTypes.FaceTarget': FaceTarget,
 'actionProcTypes.IsFacingTarget': IsFacingTarget,
 'actionProcTypes.SetSyncAnimEntry': SetSyncAnimEntry,
 'actionProcTypes.GetEntryFromAttacker': GetEntryFromAttacker,
 'actionProcTypes.IsEntityInRange': IsEntityInRange,
 'actionProcTypes.SlaveMode': SlaveMode,
 'actionProcTypes.AlignToMode': AlignToMode,
 'actionProcTypes.PathToMode': PathToMode,
 'actionProcTypes.WanderMode': WanderMode,
 'actionProcTypes.RestoreMoveMode': RestoreMoveMode,
 'actionProcTypes.RestoreTargetMoveMode': RestoreTargetMoveMode,
 'actionProcTypes.SetControlParameter': SetControlParameter}
