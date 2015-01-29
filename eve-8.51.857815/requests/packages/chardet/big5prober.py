#Embedded file name: requests/packages/chardet\big5prober.py
from .mbcharsetprober import MultiByteCharSetProber
from .codingstatemachine import CodingStateMachine
from .chardistribution import Big5DistributionAnalysis
from .mbcssm import Big5SMModel

class Big5Prober(MultiByteCharSetProber):

    def __init__(self):
        MultiByteCharSetProber.__init__(self)
        self._mCodingSM = CodingStateMachine(Big5SMModel)
        self._mDistributionAnalyzer = Big5DistributionAnalysis()
        self.reset()

    def get_charset_name(self):
        return 'Big5'
