#Embedded file name: requests/packages/chardet\sbcharsetprober.py
import sys
from . import constants
from .charsetprober import CharSetProber
from .compat import wrap_ord
SAMPLE_SIZE = 64
SB_ENOUGH_REL_THRESHOLD = 1024
POSITIVE_SHORTCUT_THRESHOLD = 0.95
NEGATIVE_SHORTCUT_THRESHOLD = 0.05
SYMBOL_CAT_ORDER = 250
NUMBER_OF_SEQ_CAT = 4
POSITIVE_CAT = NUMBER_OF_SEQ_CAT - 1

class SingleByteCharSetProber(CharSetProber):

    def __init__(self, model, reversed = False, nameProber = None):
        CharSetProber.__init__(self)
        self._mModel = model
        self._mReversed = reversed
        self._mNameProber = nameProber
        self.reset()

    def reset(self):
        CharSetProber.reset(self)
        self._mLastOrder = 255
        self._mSeqCounters = [0] * NUMBER_OF_SEQ_CAT
        self._mTotalSeqs = 0
        self._mTotalChar = 0
        self._mFreqChar = 0

    def get_charset_name(self):
        if self._mNameProber:
            return self._mNameProber.get_charset_name()
        else:
            return self._mModel['charsetName']

    def feed(self, aBuf):
        if not self._mModel['keepEnglishLetter']:
            aBuf = self.filter_without_english_letters(aBuf)
        aLen = len(aBuf)
        if not aLen:
            return self.get_state()
        for c in aBuf:
            order = self._mModel['charToOrderMap'][wrap_ord(c)]
            if order < SYMBOL_CAT_ORDER:
                self._mTotalChar += 1
            if order < SAMPLE_SIZE:
                self._mFreqChar += 1
                if self._mLastOrder < SAMPLE_SIZE:
                    self._mTotalSeqs += 1
                    if not self._mReversed:
                        i = self._mLastOrder * SAMPLE_SIZE + order
                        model = self._mModel['precedenceMatrix'][i]
                    else:
                        i = order * SAMPLE_SIZE + self._mLastOrder
                        model = self._mModel['precedenceMatrix'][i]
                    self._mSeqCounters[model] += 1
            self._mLastOrder = order

        if self.get_state() == constants.eDetecting:
            if self._mTotalSeqs > SB_ENOUGH_REL_THRESHOLD:
                cf = self.get_confidence()
                if cf > POSITIVE_SHORTCUT_THRESHOLD:
                    if constants._debug:
                        sys.stderr.write('%s confidence = %s, we have awinner\n' % (self._mModel['charsetName'], cf))
                    self._mState = constants.eFoundIt
                elif cf < NEGATIVE_SHORTCUT_THRESHOLD:
                    if constants._debug:
                        sys.stderr.write('%s confidence = %s, below negativeshortcut threshhold %s\n' % (self._mModel['charsetName'], cf, NEGATIVE_SHORTCUT_THRESHOLD))
                    self._mState = constants.eNotMe
        return self.get_state()

    def get_confidence(self):
        r = 0.01
        if self._mTotalSeqs > 0:
            r = 1.0 * self._mSeqCounters[POSITIVE_CAT] / self._mTotalSeqs / self._mModel['mTypicalPositiveRatio']
            r = r * self._mFreqChar / self._mTotalChar
            if r >= 1.0:
                r = 0.99
        return r
