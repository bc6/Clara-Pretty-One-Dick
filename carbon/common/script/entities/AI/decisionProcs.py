#Embedded file name: carbon/common/script/entities/AI\decisionProcs.py
from carbon.common.script.zaction.zactionCommon import ProcPropertyTypeDef, ProcTypeDef

def ForceDecisionTreeToRootFunc(entID):
    decisionService = sm.GetService('decisionTreeClient')
    treeManager = decisionService.treeManager
    if treeManager:
        entity = sm.GetService('entityClient').FindEntityByID(entID)
        if entity:
            component = entity.GetComponent('decision')
            treeInstance = component.instances[const.ai.DECISION_BRAIN_INDEX]
            if treeInstance:
                treeNode = treeManager.GetTreeNodeByID(component.rootIDs[const.ai.DECISION_BRAIN_INDEX])
                treeInstance.ForceAction(treeNode)
                return True
    return False


def ActionPopupMenu(entID):
    entity = sm.GetService('entityClient').FindEntityByID(entID)
    if entity:
        perceptionComponent = entity.GetComponent('perception')
        if perceptionComponent:
            clientManager = sm.GetService('perceptionClient').GetPerceptionManager(session.worldspaceid)
            if clientManager:
                if clientManager.DropOneStimulusSimple('Interact', entID, session.charid, -1.0):
                    ForceDecisionTreeToRootFunc(session.charid)


ForceDecisionTreeToRootDef = ProcTypeDef(isMaster=False, procCategory='AI', description='Forces the AI decision tree evaluate from the root node. Will interrupt any waitfor procs')
AttemptAction = ProcTypeDef(isMaster=False, procCategory='AI', properties=[ProcPropertyTypeDef('NewAction', 'I', userDataType='ActionList', isPrivate=True)], description="Attempt to change the entity's ZAction to the selected action")
AttemptActionOnTarget = ProcTypeDef(isMaster=False, procCategory='AI', properties=[ProcPropertyTypeDef('NewAction', 'I', userDataType='ActionList', isPrivate=True, displayName='Attempt Action'), ProcPropertyTypeDef('Target', 'I', userDataType='AITarget', isPrivate=True, displayName='On Target')], description="Attempt to change the entity's ZAction to the selected action using the current target")
IsActionAvailable = ProcTypeDef(isMaster=False, isConditional=True, procCategory='AI', properties=[ProcPropertyTypeDef('NewAction', 'I', userDataType='ActionList', isPrivate=True)], description='Check if the Action is available')
IsActionAvailableOnTarget = ProcTypeDef(isMaster=False, isConditional=True, procCategory='AI', properties=[ProcPropertyTypeDef('NewAction', 'I', userDataType='ActionList', isPrivate=True, displayName='Attempt Action'), ProcPropertyTypeDef('Target', 'I', userDataType='AITarget', isPrivate=True, displayName='On Target')], description='Check if the action is available on the target')
PathSetTarget = ProcTypeDef(isMaster=False, procCategory='AI', properties=[ProcPropertyTypeDef('Target', 'I', userDataType='AITarget', isPrivate=True, displayName='Path to Target')], description="Path to a target entity's location. Will not follow the target")
ForceDecisionTreeToRoot = ForceDecisionTreeToRootDef
exports = {'actionProcTypes.ForceDecisionTreeToRoot': ForceDecisionTreeToRoot,
 'decisionProcs.ForceDecisionTreeToRoot': ForceDecisionTreeToRootFunc,
 'decisionProcs.ActionPopupMenu': ActionPopupMenu,
 'actionProcTypes.AttemptAction': AttemptAction,
 'actionProcTypes.AttemptActionOnTarget': AttemptActionOnTarget,
 'actionProcTypes.IsActionAvailable': IsActionAvailable,
 'actionProcTypes.IsActionAvailableOnTarget': IsActionAvailableOnTarget,
 'actionProcTypes.PathSetTarget': PathSetTarget}
