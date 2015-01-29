#Embedded file name: requests/packages/chardet\gb2312prober.py
from .mbcharsetprober import MultiByteCharSetProber
from .codingstatemachine import CodingStateMachine
from .chardistribution import GB2312DistributionAnalysis
from .mbcssm import GB2312SMModel

class GB2312Prober(MultiByteCharSetProber):

    def __init__(self):
        MultiByteCharSetProber.__init__(self)
        self._mCodingSM = CodingStateMachine(GB2312SMModel)
        self._mDistributionAnalyzer = GB2312DistributionAnalysis()
        self.reset()

    def get_charset_name(self):
        return 'GB2312'
