#Embedded file name: eve/client/script/ui/services\certificateSvc.py
"""
This file contains the client-side certificate service which provides
the UI with methods to check processed data on certificate relationships
request certificate issuance and perform visibility flag updates.
Dependencies:
machoNet config skillSvc service
"""
import service
import util
import localization
import const
from collections import defaultdict
import log
import fsdSchemas.binaryLoader as fsdBinaryLoader

class Certificate(object):

    def __init__(self, certificateID, groupID, nameID, descriptionID, skillTypes, recommendedFor):
        self.skillSvc = sm.GetService('skills')
        self.certificateID = certificateID
        self.groupID = groupID
        self.nameID = nameID
        self.descriptionID = descriptionID
        self._SetupSkills(skillTypes)
        self.recommendedFor = recommendedFor
        self.currentLevel = None

    def __str__(self):
        return 'Certificate: %s (%d)' % (self.GetName(), self.certificateID)

    def _SetupSkills(self, skillTypes):
        skills = {}
        for skillTypeID, level in skillTypes.iteritems():
            skills[skillTypeID] = {}
            skills[skillTypeID][1] = level.basic
            skills[skillTypeID][2] = level.standard
            skills[skillTypeID][3] = level.improved
            skills[skillTypeID][4] = level.advanced
            skills[skillTypeID][5] = level.elite

        self.skills = skills

    def GetName(self):
        return localization.GetByMessageID(self.nameID)

    def GetDescription(self):
        return localization.GetByMessageID(self.descriptionID)

    def GetLabel(self, level):
        if settings.user.ui.Get('masteries_skill_counter', True):
            return localization.GetByLabel('UI/InfoWindow/CertificateNameWithProgress', certificateName=self.GetName(), skillsTrained=self.CountCompletedSkills(level), skillsTotal=self.CountSkills(level))
        else:
            return self.GetName()

    def GetSkills(self):
        return self.skills

    def SkillsByTypeAndLevel(self, level):
        """
        Returns a list of all skills and their level that is needed to have for
        this certificate at a specific level. List of tuples (typeID, levelNeeded)
        """
        return [ (typeID, levelData[level]) for typeID, levelData in self.skills.iteritems() if levelData[level] > 0 ]

    def GetLevel(self):
        """
        Returns the certificate level the character has
        """
        if self.currentLevel is None:
            self.currentLevel = 0
            for i in xrange(5, 0, -1):
                for typeID in self.skills.iterkeys():
                    charLevel = self.skillSvc.MySkillLevel(typeID)
                    reqLevel = self.skills[typeID][i]
                    if reqLevel > 0 and charLevel < reqLevel:
                        break
                else:
                    self.currentLevel = i
                    break

        return self.currentLevel

    def HasAllSkills(self, level):
        for typeID, levels in self.skills.iteritems():
            if levels[level] > 0 and self.skillSvc.MySkillLevel(typeID) is None:
                return False

        return True

    def CountCompletedSkills(self, level):
        """
        Returns the number of skills that have been trained to the specified mastery level.
        """
        count = 0
        for typeID, levels in self.skills.iteritems():
            if levels[level] > 0 and self.skillSvc.MySkillLevel(typeID) >= levels[level]:
                count += 1

        return count

    def CountSkills(self, level):
        """
        Returns the total number of skills in this certificate mastery level.
        """
        count = 0
        for typeID, levels in self.skills.iteritems():
            if levels[level] > 0:
                count += 1

        return count

    def ClearCache(self):
        self.currentLevel = None


class Certificates(service.Service):
    __notifyevents__ = ['OnGodmaSkillTrained']
    __guid__ = 'svc.certificates'
    __servicename__ = 'certificates'
    __displayname__ = 'Certificate Service'
    __startupdependencies__ = ['settings', 'godma']

    def __init__(self):
        service.Service.__init__(self)
        self.certificates = {}
        fsdCertificates = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/certificates.static', 'res:/staticdata/certificates.schema', optimize=False)
        for key, value in fsdCertificates.iteritems():
            if hasattr(value, 'recommendedFor'):
                recommendedFor = value.recommendedFor
            else:
                recommendedFor = []
            self.certificates[key] = Certificate(key, value.groupID, value.nameID, value.descriptionID, value.skillTypes, recommendedFor)

    def OnGodmaSkillTrained(self, skillID):
        for certificate in self.certificates.itervalues():
            certificate.ClearCache()

    def GetCertificate(self, certificateID):
        return self.certificates[certificateID]

    def GetAllCertificatesByCategoryID(self):
        return self._GroupByCategoryID(self.certificates.values())

    def GetMyCertificates(self):
        myCertificates = {}
        for certificateID, certificate in self.certificates.iteritems():
            if certificate.GetLevel() > 0:
                myCertificates[certificateID] = certificate

        return myCertificates

    def GetMyCertificatesByCategoryID(self):
        certs = self.GetMyCertificates().values()
        return self._GroupByCategoryID(certs)

    def _GroupByCategoryID(self, certificates):
        ret = defaultdict(list)
        for cert in certificates:
            ret[cert.groupID].append(cert)

        return ret

    def GetCurrCharMasteryLevel(self, shipTypeID):
        """
        Get mastery level for current character for ship typeID passed in
        """
        for i in xrange(5, 0, -1):
            certificates = self.GetCertificatesForShipByMasteryLevel(shipTypeID, i)
            levels = set()
            for certificate in certificates:
                levels.add(certificate.GetLevel())

            for level in levels:
                if level < i:
                    break
                else:
                    return i

        return 0

    def GetMasteryIconForLevel(self, masteryLevel):
        if masteryLevel == 0:
            return 'res:/UI/Texture/Classes/Mastery/masterySmall0.png'
        if masteryLevel == 1:
            return 'res:/UI/Texture/Classes/Mastery/masterySmall1.png'
        if masteryLevel == 2:
            return 'res:/UI/Texture/Classes/Mastery/masterySmall2.png'
        if masteryLevel == 3:
            return 'res:/UI/Texture/Classes/Mastery/masterySmall3.png'
        if masteryLevel == 4:
            return 'res:/UI/Texture/Classes/Mastery/masterySmall4.png'
        if masteryLevel == 5:
            return 'res:/UI/Texture/Classes/Mastery/masterySmall5.png'

    def GetCertificatesForShipByMasteryLevel(self, typeID, masteryLevel):
        """ Returns the list of certificates that form the mastery level requested """
        fsdType = cfg.fsdTypeOverrides.Get(typeID)
        if hasattr(fsdType, 'masteries'):
            certificates = fsdType.masteries.get(masteryLevel - 1, [])
            return [ self.certificates[certificateID] for certificateID in certificates ]
        return []

    def GetTrainingTimeForSkills(self, skills):
        """
        Given a dictionary of (skillID, level) this returns the total training time required.
        """
        skillSvc = sm.GetService('skills')
        trainingTime = 0
        for skillID, level in skills.iteritems():
            try:
                myLevel = skillSvc.GetMySkillsFromTypeID(skillID).skillLevel
            except AttributeError:
                myLevel = 0

            for i in xrange(int(myLevel) + 1, int(level) + 1):
                trainingTime += skillSvc.GetRawTrainingTimeForSkillLevel(skillID, i)

        return trainingTime

    def GetShipTrainingTimeForMasteryLevel(self, typeID, masteryLevel):
        """
        Returns the total training time required to reach the specified mastery level.
        """
        skills = {}
        for certificate in self.GetCertificatesForShipByMasteryLevel(typeID, masteryLevel):
            for skillID, level in certificate.SkillsByTypeAndLevel(masteryLevel):
                skills[skillID] = max(skills.get(skillID, 0), level)

        return self.GetTrainingTimeForSkills(skills)

    def GetCertificateTrainingTimeForMasteryLevel(self, certificateID, masteryLevel):
        """
        Returns the total training time required to achieve a certificate mastery level.
        """
        certificate = self.certificates[certificateID]
        skills = {}
        for skillID, level in certificate.SkillsByTypeAndLevel(masteryLevel):
            skills[skillID] = max(skills.get(skillID, 0), level)

        return self.GetTrainingTimeForSkills(skills)

    def GetCertificateRecommendationsFromCertificateID(self, certificateID):
        """
            returns a list of shipTypeIDs which are associated with this certificates
            use:    recommendedFor = GetCertificateRecommendationsFromCertificateID(certificateID)
            pre:    certificateID is a valid a valid certificateID
            post:   recommendedFor is a list of shipTypeIDs for which the certificate is recommended
        """
        return self.certificates[certificateID].recommendedFor

    def GetCertificateLabel(self, certificateID):
        certificate = self.certificates[certificateID]
        levelDict = {1: 'UI/Certificates/CertificateGrades/Grade1',
         2: 'UI/Certificates/CertificateGrades/Grade2',
         3: 'UI/Certificates/CertificateGrades/Grade3',
         4: 'UI/Certificates/CertificateGrades/Grade4',
         5: 'UI/Certificates/CertificateGrades/Grade5'}
        levelPath = levelDict.get(certificate.GetLevel())
        level = localization.GetByLabel(levelPath)
        return (certificate.GetName(), level, certificate.GetDescription())
