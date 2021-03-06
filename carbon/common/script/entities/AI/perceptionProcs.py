#Embedded file name: carbon/common/script/entities/AI\perceptionProcs.py
import perception
from carbon.common.script.zaction.zactionCommon import ProcTypeDef, ProcPropertyTypeDef

def GetAICandidateList(propRow):
    retList = []
    for candidate in perception.Target.GetMyRows(_getDeleted=False):
        retList.append((candidate.targetName, candidate.targetID, ''))

    return retList


def GetAIConfidenceList(propRow):
    retList = []
    for confidence in const.perception.PERCEPTION_CONFIDENCE_VALUES:
        retList.append((confidence.confidenceName, confidence.confidenceID, ''))

    retList.sort(key=lambda row: row[1])
    return retList


def GetAISubjectList(propRow):
    retList = []
    for subject in perception.Subject.GetMyRows(_getDeleted=False):
        retList.append((subject.subjectName, subject.subjectID, ''))

    return retList


def GetAIStimTypeList(propRow):
    retList = []
    for stimType in perception.StimType.GetMyRows(_getDeleted=False):
        retList.append((stimType.stimTypeName, stimType.stimTypeID, ''))

    return retList


AICandidate = ('listMethod', GetAICandidateList)
AIConfidence = ('listMethod', GetAIConfidenceList)
AISubject = ('listMethod', GetAISubjectList)
AIStimType = ('listMethod', GetAIStimTypeList)
DropStimulus = ProcTypeDef(isMaster=False, procCategory='AI', properties=[ProcPropertyTypeDef('StimType', 'I', userDataType='AIStimType', isPrivate=True, displayName='Stimulus type'), ProcPropertyTypeDef('Range', 'F', userDataType=None, isPrivate=True, displayName='Range (-1 for default)'), ProcPropertyTypeDef('SwapTarget', 'B', userDataType=None, isPrivate=True, displayName='Drop from target')])
exports = {'actionProperties.AICandidate': AICandidate,
 'actionProperties.AIConfidence': AIConfidence,
 'actionProperties.AISubject': AISubject,
 'actionProperties.AIStimType': AIStimType,
 'actionProcTypes.DropStimulus': DropStimulus}
