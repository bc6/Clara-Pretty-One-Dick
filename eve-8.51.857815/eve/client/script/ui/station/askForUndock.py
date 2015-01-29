#Embedded file name: eve/client/script/ui/station\askForUndock.py
import carbonui.const as uiconst

def IsOkToBoardWithModulesLackingSkills(dogmaLocation, Message):
    if settings.user.suppress.Get('suppress.AskUndockWithModulesLackingSkill', None) is None:
        if dogmaLocation.GetModulesLackingSkills():
            if Message('AskUndockWithModulesLackingSkill', {}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
                return False
    return True
