#Embedded file name: eveplanet\taxRate.py
import weakref
from collections import defaultdict
import eve.common.lib.appConst as const
STANDING_ATTRIBUTES = [(const.contactHighStanding, 'standingHigh'),
 (const.contactGoodStanding, 'standingGood'),
 (const.contactNeutralStanding, 'standingNeutral'),
 (const.contactBadStanding, 'standingBad'),
 (const.contactHorribleStanding, 'standingHorrible')]

class TaxRates(defaultdict):

    def __init__(self, **kwargs):
        self.defaultTaxRate = 0.0
        self.update(kwargs)

    def __missing__(self, key):
        return self.defaultTaxRate


class TaxRateCalculator(object):

    def __init__(self, registry):
        self.registry = weakref.proxy(registry)
        self.allowAlliance = True
        self.allowStandings = True
        self.requiredStanding = None
        self.taxRates = TaxRates()

    def SetAccessControl(self, allowAlliance, allowStandings, standingLevel):
        self.allowAlliance = allowAlliance
        self.allowStandings = allowStandings
        self.requiredStanding = standingLevel

    def SetTaxRate(self, **taxRates):
        self.taxRates = TaxRates(**taxRates)

    def GetTaxRates(self):
        return self.taxRates

    def Calculate(self, orbital, fromCharID, fromCorpID):
        taxRate = {}
        taxRate.update(self._GetTaxForPlayerOwned(fromCharID, fromCorpID, orbital.ownerID))
        if taxRate and self._IsHighSecurity():
            taxRate.update(self._GetConcordTax(orbital, fromCharID))
        return taxRate

    def _GetConcordTax(self, orbital, charID):
        taxReduction = self.registry.GetTaxReduction(charID)
        return {const.ownerCONCORD: taxReduction * self.registry.GetDefaultTaxRate(orbital.itemID)}

    def _GetTaxForPlayerOwned(self, fromCharID, fromCorpID, orbitalOwnerID):
        taxRate = None
        if self._IsSameCorp(fromCorpID, orbitalOwnerID):
            taxRate = self.taxRates['corporation']
        elif self.allowAlliance and self._IsSameAlliance(fromCorpID, orbitalOwnerID):
            taxRate = self.taxRates['alliance']
        elif self.allowStandings:
            standing = self._GetStanding(fromCharID, orbitalOwnerID)
            if self._HasStanding(standing):
                taxRate = self._GetTaxRateForStanding(standing)
        if taxRate is not None:
            return {orbitalOwnerID: taxRate}
        return {}

    def _GetAllianceID(self, fromCorpID):
        return self.registry.GetAllianceIDForCorporation(fromCorpID)

    def _GetStanding(self, fromCharID, toCorpID):
        return self.registry.GetStanding(toCorpID, fromCharID)

    def _HasStanding(self, standing):
        return standing > self.requiredStanding - 0.1

    def _IsSameAlliance(self, fromCorpID, toCorpID):
        fromAllianceID = self._GetAllianceID(fromCorpID)
        toAllianceID = self._GetAllianceID(toCorpID)
        return fromAllianceID == toAllianceID and fromAllianceID is not None

    def _IsSameCorp(self, fromCorpID, toCorpID):
        return fromCorpID == toCorpID and fromCorpID is not None

    def _IsHighSecurity(self):
        return self.registry.IsHighSecurity()

    def _GetTaxRateForStanding(self, standing):
        lowestStanding = const.contactHorribleStanding
        for standingStep, taxRate in STANDING_ATTRIBUTES:
            if lowestStanding < standingStep <= standing:
                return self.taxRates.get(taxRate)


class NPCTaxRateCalculator(object):

    def __init__(self, taxRate):
        self.taxRate = taxRate

    def Calculate(self, orbital, *args):
        return {orbital.ownerID: self.taxRate}
