#Embedded file name: requests/packages/chardet\eucjpprober.py
import sys
from . import constants
from .mbcharsetprober import MultiByteCharSetProber
from .codingstatemachine import CodingStateMachine
from .chardistribution import EUCJPDistributionAnalysis
from .jpcntx import EUCJPContextAnalysis
from .mbcssm import EUCJPSMModel

class EUCJPProber(MultiByteCharSetProber):

    def __init__(self):
        MultiByteCharSetProber.__init__(self)
        self._mCodingSM = CodingStateMachine(EUCJPSMModel)
        self._mDistributionAnalyzer = EUCJPDistributionAnalysis()
        self._mContextAnalyzer = EUCJPContextAnalysis()
        self.reset()

    def reset(self):
        MultiByteCharSetProber.reset(self)
        self._mContextAnalyzer.reset()

    def get_charset_name(self):
        return 'EUC-JP'

    def feed(self, aBuf):
        aLen = len(aBuf)
        for i in range(0, aLen):
            codingState = self._mCodingSM.next_state(aBuf[i])
            if codingState == constants.eError:
                if constants._debug:
                    sys.stderr.write(self.get_charset_name() + ' prober hit error at byte ' + str(i) + '\n')
                self._mState = constants.eNotMe
                break
            elif codingState == constants.eItsMe:
                self._mState = constants.eFoundIt
                break
            elif codingState == constants.eStart:
                charLen = self._mCodingSM.get_current_charlen()
                if i == 0:
                    self._mLastChar[1] = aBuf[0]
                    self._mContextAnalyzer.feed(self._mLastChar, charLen)
                    self._mDistributionAnalyzer.feed(self._mLastChar, charLen)
                else:
                    self._mContextAnalyzer.feed(aBuf[i - 1:i + 1], charLen)
                    self._mDistributionAnalyzer.feed(aBuf[i - 1:i + 1], charLen)

        self._mLastChar[0] = aBuf[aLen - 1]
        if self.get_state() == constants.eDetecting and self._mContextAnalyzer.got_enough_data():
            if self.get_confidence() > constants.SHORTCUT_THRESHOLD:
                self._mState = constants.eFoundIt
        return self.get_state()

    def get_confidence(self):
        contxtCf = self._mContextAnalyzer.get_confidence()
        distribCf = self._mDistributionAnalyzer.get_confidence()
        return max(contxtCf, distribCf)
