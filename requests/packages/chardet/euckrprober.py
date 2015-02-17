#Embedded file name: requests/packages/chardet\euckrprober.py
from .mbcharsetprober import MultiByteCharSetProber
from .codingstatemachine import CodingStateMachine
from .chardistribution import EUCKRDistributionAnalysis
from .mbcssm import EUCKRSMModel

class EUCKRProber(MultiByteCharSetProber):

    def __init__(self):
        MultiByteCharSetProber.__init__(self)
        self._mCodingSM = CodingStateMachine(EUCKRSMModel)
        self._mDistributionAnalyzer = EUCKRDistributionAnalysis()
        self.reset()

    def get_charset_name(self):
        return 'EUC-KR'
