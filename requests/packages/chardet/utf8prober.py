#Embedded file name: requests/packages/chardet\utf8prober.py
from . import constants
from .charsetprober import CharSetProber
from .codingstatemachine import CodingStateMachine
from .mbcssm import UTF8SMModel
ONE_CHAR_PROB = 0.5

class UTF8Prober(CharSetProber):

    def __init__(self):
        CharSetProber.__init__(self)
        self._mCodingSM = CodingStateMachine(UTF8SMModel)
        self.reset()

    def reset(self):
        CharSetProber.reset(self)
        self._mCodingSM.reset()
        self._mNumOfMBChar = 0

    def get_charset_name(self):
        return 'utf-8'

    def feed(self, aBuf):
        for c in aBuf:
            codingState = self._mCodingSM.next_state(c)
            if codingState == constants.eError:
                self._mState = constants.eNotMe
                break
            elif codingState == constants.eItsMe:
                self._mState = constants.eFoundIt
                break
            elif codingState == constants.eStart:
                if self._mCodingSM.get_current_charlen() >= 2:
                    self._mNumOfMBChar += 1

        if self.get_state() == constants.eDetecting:
            if self.get_confidence() > constants.SHORTCUT_THRESHOLD:
                self._mState = constants.eFoundIt
        return self.get_state()

    def get_confidence(self):
        unlike = 0.99
        if self._mNumOfMBChar < 6:
            for i in range(0, self._mNumOfMBChar):
                unlike = unlike * ONE_CHAR_PROB

            return 1.0 - unlike
        else:
            return unlike
