#Embedded file name: probescanning\scanHandler.py
import logging
from collections import namedtuple
from probescanning.const import probeResultPerfect, probeStateIdle, probeScanGroupAnomalies
from results import ResultsHistory
CurrentScan = namedtuple('CurrentScan', ['startTime', 'duration', 'probeIDs'])

class ScanHandler(object):

    def __init__(self, scanSvc, ScatterEvent, resultFilter):
        self.logger = logging.getLogger('probescanning-scanHandler')
        self.currentScan = None
        self.resultsIgnored = set()
        self.resultsHistory = ResultsHistory()
        self.resultFilter = resultFilter
        self.scanningProbes = None
        self.scanSvc = scanSvc
        self.ScatterEvent = ScatterEvent

    def OnSystemScanStarted(self, startTime, durationMs, probes):
        self.logger.debug('OnSystemScanStarted. startTime = %s, durationMs = %s', startTime, durationMs)
        self.currentScan = CurrentScan(startTime=startTime, duration=durationMs, probeIDs=self.scanSvc.SetProbesAsScanning(probes))

    def NotifyResult(self, hasPerfectResult):
        if hasPerfectResult:
            self.scanSvc.audio.SendUIEvent(unicode('wise:/msg_scanner_positive_play'))
        else:
            self.scanSvc.audio.SendUIEvent(unicode('wise:/msg_scanner_partial_play'))

    def HasPerfectResults(self, results):
        return results and any((result.certainty >= probeResultPerfect for result in results))

    def OnSystemScanStopped(self, probes, results, absentTargets):
        self.logger.debug('OnSystemScanStopped probes = %s, results = %s', probes, results)
        for pID in probes:
            self.scanSvc.UpdateProbeState(pID, probeStateIdle, 'OnSystemScanStopped', notify=False)

        self.StopScanning()
        self.resultsHistory.RegisterResults(results)
        self.NotifyResult(self.HasPerfectResults(results))
        if absentTargets:
            self.ClearResults(*absentTargets)

    def InjectResults(self, results):
        self.resultsHistory.RegisterResults(results, incrimentScanNumber=False)
        self.ScatterEvent('OnRefreshScanResults')

    def GetCurrentScan(self):
        return self.currentScan

    def ClearResults(self, *targets):
        """
        Clears results manually from the scanner.
        Will clear the result from cache and ignore list as well as the last result list.
        Subsequenct scans will pick the target up again if it still exits.
        """
        for targetID in targets:
            if targetID in self.resultsIgnored:
                self.resultsIgnored.remove(targetID)

        self.resultsHistory.ClearResults(*targets)
        self.ScatterEvent('OnRefreshScanResults')

    def IgnoreOtherResults(self, *targets):
        for result in self.resultsHistory.LastResultIterator():
            if result['id'] not in targets:
                self.resultsIgnored.add(result['id'])

        self.ScatterEvent('OnRefreshScanResults')

    def ShowIgnoredResult(self, targetID):
        if targetID in self.resultsIgnored:
            self.resultsIgnored.remove(targetID)
            self.ScatterEvent('OnRefreshScanResults')

    def ClearIgnoredResults(self):
        self.resultsIgnored = set()
        self.ScatterEvent('OnRefreshScanResults')

    def IgnoreResult(self, *targets):
        for targetID in targets:
            self.resultsIgnored.add(targetID)

        self.ScatterEvent('OnRefreshScanResults')

    def GetScanResults(self):
        """ Returns the latest known scan results. """
        return self.resultsHistory.GetLastResults()

    def SetProbesAsScanning(self, probeIDs):
        self.scanningProbes = probeIDs

    def StopScanning(self):
        self.currentScan = None
        self.scanningProbes = None

    def GetScanningProbes(self):
        return self.scanningProbes

    def IsScanning(self):
        return bool(self.scanningProbes)

    def GetIgnoredResults(self):
        return self.resultsIgnored

    def GetResultsHistory(self):
        return self.resultsHistory

    def GetResults(self):
        """
            Returns you the latest results and how much has been ignored and filtered out
        """
        ignored = 0
        filtered = 0
        anomaliesFiltered = 0
        results = []
        for result in self.resultsHistory.LastResultIterator():
            if result['id'] in self.resultsIgnored:
                ignored += 1
                continue
            if result['scanGroupID'] == probeScanGroupAnomalies:
                if not self.resultFilter.IsShowingAnomalies():
                    anomaliesFiltered += 1
                    continue
            elif self.resultFilter.IsFiltered(result):
                filtered += 1
                continue
            results.append(result)

        return (results,
         ignored,
         filtered,
         anomaliesFiltered)
