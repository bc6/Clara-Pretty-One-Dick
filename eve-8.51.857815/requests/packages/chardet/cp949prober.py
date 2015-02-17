#Embedded file name: requests/packages/chardet\cp949prober.py
from .mbcharsetprober import MultiByteCharSetProber
from .codingstatemachine import CodingStateMachine
from .chardistribution import EUCKRDistributionAnalysis
from .mbcssm import CP949SMModel

class CP949Prober(MultiByteCharSetProber):

    def __init__(self):
        MultiByteCharSetProber.__init__(self)
        self._mCodingSM = CodingStateMachine(CP949SMModel)
        self._mDistributionAnalyzer = EUCKRDistributionAnalysis()
        self.reset()

    def get_charset_name(self):
        return 'CP949'
