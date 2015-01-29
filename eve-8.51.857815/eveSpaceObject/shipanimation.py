#Embedded file name: eveSpaceObject\shipanimation.py
__author__ = 'logi'
import shipmode.data as stancedata
shipAnimationStates = 'res:/dx9/model/states/ship.red'
stanceAnimations = {stancedata.shipStanceSpeed: ('speedMode', 'SpeedModeLoop'),
 stancedata.shipStanceSniper: ('sniperMode', 'SniperModeLoop'),
 stancedata.shipStanceDefense: ('normal', 'NormalLoop')}

def SetShipAnimationStance(ship, stanceID):
    if stanceID not in stanceAnimations:
        return False
    state, defaultAnimation = stanceAnimations[stanceID]
    if ship.animationSequencer is not None:
        ship.animationSequencer.defaultAnimation = defaultAnimation
    return True


def GetAnimationStateFromStance(stanceID):
    if stanceID in stanceAnimations:
        state, defaultAnimation = stanceAnimations[stanceID]
        return state
    return 'normal'


def TriggerStanceAnimation(shipModel, stanceID):
    SetShipAnimationStance(shipModel, stanceID)
    shipModel.animationSequencer.GoToState(GetAnimationStateFromStance(stanceID))


def SetUpAnimation(model, stanceID, trinity):
    if model.animationSequencer is None:
        model.animationSequencer = trinity.Load(shipAnimationStates)
    state = GetAnimationStateFromStance(stanceID)
    model.animationSequencer.GoToState(state)
