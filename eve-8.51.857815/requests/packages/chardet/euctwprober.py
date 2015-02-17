#Embedded file name: requests/packages/chardet\euctwprober.py
from .mbcharsetprober import MultiByteCharSetProber
from .codingstatemachine import CodingStateMachine
from .chardistribution import EUCTWDistributionAnalysis
from .mbcssm import EUCTWSMModel

class EUCTWProber(MultiByteCharSetProber):

    def __init__(self):
        MultiByteCharSetProber.__init__(self)
        self._mCodingSM = CodingStateMachine(EUCTWSMModel)
        self._mDistributionAnalyzer = EUCTWDistributionAnalysis()
        self.reset()

    def get_charset_name(self):
        return 'EUC-TW'
