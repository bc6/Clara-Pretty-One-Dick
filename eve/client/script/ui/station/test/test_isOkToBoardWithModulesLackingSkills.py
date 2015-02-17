#Embedded file name: eve/client/script/ui/station/test\test_isOkToBoardWithModulesLackingSkills.py
from unittest import TestCase
import mock
from itertoolsext import Bundle
carbonui = mock.Mock()
ID_YES = 100
YESNO = 1000
with mock.patch.dict('sys.modules', {'carbonui': carbonui,
 'carbonui.const': Bundle(ID_YES=ID_YES, YESNO=YESNO)}):
    from eve.client.script.ui.station.askForUndock import IsOkToBoardWithModulesLackingSkills
    import carbonui.const as uiconst
from testhelpers.evemocks import SettingsMock

class TestIsOkToBoardWithModulesLackingSkills(TestCase):

    def setUp(self):
        self._SetMessage(mock.Mock(return_value=uiconst.ID_YES))

    def _SetMessage(self, mockObject):
        self.message = mockObject

    def testWhenMessageIsSuppressedWeReturnTrue(self):
        with SettingsMock():
            settings.user.suppress.Set('suppress.AskUndockWithModulesLackingSkill', True)
            self.assertTrue(IsOkToBoardWithModulesLackingSkills(None, self.message))

    def testWhenDogmaGivesYouNoModulesYouDoNotHaveSkillsForWeReturnTrue(self):
        self.assertTrue(self._IsOk([]))

    def testWhenDogmaGivesUsModulesLackingSkillsWeAskIfWeWantToProceed(self):
        isOk = self._IsOk([1])
        self.message.assert_called_once_with('AskUndockWithModulesLackingSkill', {}, uiconst.YESNO, suppress=uiconst.ID_YES)
        self.assertTrue(isOk)

    def _IsOk(self, moduleIDs):
        with SettingsMock():
            dogmaLocation = Bundle(GetModulesLackingSkills=lambda : moduleIDs)
            isOk = IsOkToBoardWithModulesLackingSkills(dogmaLocation, self.message)
        return isOk
