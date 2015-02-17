#Embedded file name: requests/packages/chardet\mbcharsetprober.py
import sys
from . import constants
from .charsetprober import CharSetProber

class MultiByteCharSetProber(CharSetProber):

    def __init__(self):
        CharSetProber.__init__(self)
        self._mDistributionAnalyzer = None
        self._mCodingSM = None
        self._mLastChar = [0, 0]

    def reset(self):
        CharSetProber.reset(self)
        if self._mCodingSM:
            self._mCodingSM.reset()
        if self._mDistributionAnalyzer:
            self._mDistributionAnalyzer.reset()
        self._mLastChar = [0, 0]

    def get_charset_name(self):
        pass

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
                    self._mDistributionAnalyzer.feed(self._mLastChar, charLen)
                else:
                    self._mDistributionAnalyzer.feed(aBuf[i - 1:i + 1], charLen)

        self._mLastChar[0] = aBuf[aLen - 1]
        if self.get_state() == constants.eDetecting and self._mDistributionAnalyzer.got_enough_data():
            if self.get_confidence() > constants.SHORTCUT_THRESHOLD:
                self._mState = constants.eFoundIt
        return self.get_state()

    def get_confidence(self):
        return self._mDistributionAnalyzer.get_confidence()
