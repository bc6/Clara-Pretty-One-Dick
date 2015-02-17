#Embedded file name: eve/client/script/ui/control\historyBuffer.py
import collections

class HistoryBuffer:
    """ A class designed to hold browsing history for windows """

    def __init__(self, maxLen = None):
        self.maxLen = maxLen
        self.deque = collections.deque(maxlen=self.maxLen)
        self.idx = None

    def Append(self, data):
        if len(self.deque) and self.idx is not None:
            self.deque = collections.deque(list(self.deque)[:self.idx + 1], maxlen=self.maxLen)
        if not len(self.deque) or data != self.deque[-1]:
            self.deque.append(data)
        self.idx = len(self.deque) - 1

    def GoBack(self):
        if self.IsBackEnabled():
            self.idx -= 1
            return self.deque[self.idx]

    def GoForward(self):
        if self.IsForwardEnabled():
            self.idx += 1
            return self.deque[self.idx]

    def IsBackEnabled(self):
        return len(self.deque) > 1 and self.idx > 0

    def IsForwardEnabled(self):
        return len(self.deque) > 1 and self.idx < len(self.deque) - 1

    def UpdateCurrent(self, value):
        self.deque[self.idx] = value

    def IsEmpty(self):
        return len(self.deque) == 0
