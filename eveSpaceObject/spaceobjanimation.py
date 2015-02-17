#Embedded file name: eveSpaceObject\spaceobjanimation.py
import shipmode.data as stancedata
STATE_MACHINE_SHIP_STANDARD = 'shipStandard'
STATE_MACHINE_SHIP_STANCE = 'shipStance'
STATE_MACHINE_SHIP_LOOP = 'shipLoop'
stanceAnimations = {stancedata.shipStanceSpeed: 'speed',
 stancedata.shipStanceSniper: 'sniper',
 stancedata.shipStanceDefense: 'defense'}

def GetStateMachine(model, name):
    if model.animationSequencer is None:
        return
    for stateMachine in model.animationSequencer.stateMachines:
        if stateMachine.name == name:
            return stateMachine


def SetShipAnimationStance(ship, stanceID):
    if stanceID not in stanceAnimations:
        return False
    if ship.animationSequencer is None:
        return False
    state = stanceAnimations[stanceID]
    ship.animationSequencer.GoToState(state)
    return True


def GetAnimationStateFromStance(stanceID):
    if stanceID in stanceAnimations:
        return stanceAnimations[stanceID]
    return 'normal'


def SetUpAnimation(model, stateMachinePath, trinity):
    if model.animationSequencer is None:
        model.animationSequencer = trinity.EveAnimationSequencer()
    stateMachine = trinity.Load(stateMachinePath)
    model.animationSequencer.stateMachines.append(stateMachine)


def LoadAnimationStates(animationStateList, graphicStatesData, model, trinity):
    for sid in animationStateList:
        path = graphicStatesData[sid].file
        SetUpAnimation(model, path, trinity)


def LoadAnimationStatesFromFiles(animationStateFiles, model, trinity):
    for path in animationStateFiles:
        SetUpAnimation(model, path, trinity)


def TriggerDefaultStates(model):
    if not hasattr(model, 'animationSequencer'):
        return
    for stateMachine in model.animationSequencer.stateMachines:
        if len(stateMachine.defaultState) > 1:
            model.animationSequencer.GoToState(stateMachine.defaultState)
