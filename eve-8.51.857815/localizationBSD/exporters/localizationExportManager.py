#Embedded file name: localizationBSD/exporters\localizationExportManager.py
from .. import const as localizationBSDConst
from . import LocalizationExporterError
from localization.logger import LogError
import blue
import uthread
import log
import carbon.backend.script.bsdWrappers.bsdUtil as bsdUtil
import localizationPickleExporter
import localizationIntFileExporter
import localizationScaleformFileExporter
import localizationXMLResourceExporter
import localizationResxExporter
import localizationYamlFileExporter

class LocalizationExportManager(object):
    """
    Class that knows what utility functions to call to export each export type defined in
    Project settings on the content DB
    """
    _EXPORTERS_MAP = {'.pickle': localizationPickleExporter.LocalizationPickleExporter,
     '.int': localizationIntFileExporter.LocalizationIntFileExporter,
     '.xml': localizationXMLResourceExporter.LocalizationXMLResourceExporter,
     '.resx': localizationResxExporter.LocalizationResxExporter,
     'vita': localizationScaleformFileExporter.LocalizationScaleformFileExporter,
     'yaml': localizationYamlFileExporter.LocalizationYamlFileExporter}

    @classmethod
    def GetExportTypes(cls):
        exporterTypes = []
        for exporterName, exporter in cls._EXPORTERS_MAP.iteritems():
            exporterTypes.append((exporterName, exporter.EXPORT_DESCRIPTION))

        return exporterTypes

    @classmethod
    def GetResourceNamesForAllProjects(cls):
        """
        Return every exporters' list of files (file paths) that they generate.
        returns:
            dictionary containing lists of files, keyed by projectID
        """
        return cls._CallMethodOnAllProjects(exporterMethodName='GetResourceNamesWithProjectSettings')

    @classmethod
    def GetResourceNamesForProject(cls, projectID):
        """
        Return specific project's exporter's list of files (file paths) that it generates.
        returns:
            lists of files
        """
        return cls._CallMethodOnProject(projectID, exporterMethodName='GetResourceNamesWithProjectSettings')

    @classmethod
    def ExportAllProjects(cls, notificationFunction = None, **kwargs):
        """
        Execute exports for all projects.
        It is up to each exporter to select what data to export, but currently all exporters select submitted only data.
        parameters:
            notificationFunction - function must implement interface that has notificationParam parameter
            additionalSettings   - optional parameters to be passed to exporters. The allowed list of params depends on implementation of an exporter.
        returns:
            lists of files that were generated, in a dictionary, keyed by projectID
        throws:
            will NOT throw any errors and will instead log everything. This is done so that the export manager can export the max number of projects
        """
        return cls._CallMethodOnAllProjects(internalMethod=cls._ExportOneProject, notificationFunction=notificationFunction, additionalSettings=kwargs)

    @classmethod
    def ExportProject(cls, projectID, **kwargs):
        """
        Execute export for specified project.
        It is up to each exporter to select what data to export, but currently all exporters select submitted only data.
        parameters:
            projectID            - specified project
            additionalSettings   - dictionary of optional parameters to be passed to exporters. The allowed list of params depends on implementation of an exporter.
        returns:
            lists of files that were generated
        """
        return cls._CallMethodOnProject(projectID, internalMethod=cls._ExportOneProject, additionalSettings=kwargs)

    @classmethod
    def _GetAllProjectsData(cls):
        dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
        getSubmittedOnly = 1
        projectSettings = dbzlocalization.Projects_Select(getSubmittedOnly)
        projectList = bsdUtil.MakeRowDicts(projectSettings, projectSettings.columns)
        return projectList

    @classmethod
    def _GetProjectData(cls, projectID):
        dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
        getSubmittedOnly = 1
        projectSettings = dbzlocalization.Projects_SelectByID(getSubmittedOnly, projectID)
        projectList = bsdUtil.MakeRowDicts(projectSettings, projectSettings.columns)
        if len(projectList) != 1:
            LogError("ExportManager's ExportProject method tried to retrieve project of projectID (%s) and instead got result set of (%s) elements." % (projectID, len(projectList)))
            return None
        projectDict = projectList[0]
        return projectDict

    @classmethod
    def _ExportOneProject(cls, projectDict, additionalSettings):
        """
        parameters
            projectDict          - dictionary of project parameters/settings
            additionalSettings   - dictionary of optional parameters to be passed to exporters. The allowed list of params depends on implementation of an exporter.
        """
        returnValue = cls._ExecuteExporterMethod(projectDict, 'ExportWithProjectSettings', additionalSettings)
        if returnValue is None:
            LogError("ExportManager's Export Project failed to export projectID (%s). Check project settings." % projectDict[localizationBSDConst.COLUMN_PROJECT_ID])
        return returnValue

    @classmethod
    def _ExecuteExporterMethod(cls, projectDict, methodName, additionalSettings):
        """
        Correct projectDict parameters and resolve methodName
        parameters:
            methodName           - name of the method to call on an exporter
            additionalSettings   - dictionary of optional parameters to be passed to exporters. The allowed list of params depends on implementation of an exporter.
        returns:
            tuple with : exporter function based on methodName, projectID and modified/corrected project dictionary 
        """
        returnValue = None
        exportTypeName = projectDict[localizationBSDConst.COLUMN_EXPORT_NAME]
        projectID = projectDict[localizationBSDConst.COLUMN_PROJECT_ID]
        exportLocation = projectDict[localizationBSDConst.COLUMN_EXPORT_LOCATION]
        exportFileName = projectDict[localizationBSDConst.COLUMN_EXPORT_FILE_NAME]
        if all([exportTypeName, exportLocation, exportFileName]):
            newProjectDict = {}
            for key, value in projectDict.iteritems():
                if key == localizationBSDConst.COLUMN_PROJECT_ID:
                    continue
                if key == localizationBSDConst.COLUMN_EXPORT_LOCATION:
                    value = cls._ResolveInternalPaths(value)
                newProjectDict[key] = value

            if additionalSettings is not None:
                for key, value in additionalSettings.iteritems():
                    newProjectDict[key] = value

            try:
                exporterMethod = getattr(cls._EXPORTERS_MAP[exportTypeName], methodName)
            except (KeyError, AttributeError):
                raise LocalizationExporterError('ExportManager was asked to export using methodName (%s) on invalid Exporter. For projectID (%s); exportTypeName (%s). Check _EXPORTERS_MAP variable.' % (methodName, projectID, exportTypeName))

            returnValue = exporterMethod(projectID, **newProjectDict)
        else:
            raise LocalizationExporterError('ExportManager was asked to export using methodName (%s) with missing exportTypeName Exporter setting. For projectID (%s); exportTypeName (%s). Check Project settings.' % (methodName, projectID, exportTypeName))
        return returnValue

    @classmethod
    def _ResolveInternalPaths(cls, exportLocation):
        """
        Resolve/expand internal path name passed for this project
        """
        if exportLocation and exportLocation.startswith('root:/'):
            exportLocation = blue.paths.ResolvePath(exportLocation)
        return exportLocation

    @classmethod
    def _CallMethodOnAllProjects(cls, internalMethod = None, exporterMethodName = None, notificationFunction = None, additionalSettings = None):
        """
        parameters
            internalMethod       - internal method to call
            notificationFunction - function called after call to an exporter.
                                   This function must implement interface that has notificationParam parameter.
                                   The notificationParam has the same structure as the return value below:
                                     dictionary containing result to the internalMethod call, keyed by projectID
            additionalSettings   - dictionary of optional parameters to be passed to exporters. The allowed list of params depends on implementation of an exporter.
        returns:
            dictionary containing result to the internalMethod call, keyed by projectID
        throws:
            will NOT throw any errors and will instead log everything. This is done so that the export manager can export the max number of projects
        """
        returnDict = {}
        projectsEntries = cls._GetAllProjectsData()
        for index, projectDict in projectsEntries.iteritems():
            if projectDict[localizationBSDConst.COLUMN_EXPORT_NAME] is not None:
                try:
                    if internalMethod:
                        try:
                            returnValue = internalMethod(projectDict, additionalSettings)
                        except:
                            log.LogException()
                            continue

                    elif exporterMethodName:
                        returnValue = cls._ExecuteExporterMethod(projectDict, exporterMethodName, additionalSettings)
                except Exception as e:
                    log.LogTraceback('Export Manager caught the error: ' + repr(e))
                    continue

                returnDict[projectDict[localizationBSDConst.COLUMN_PROJECT_ID]] = returnValue
                if notificationFunction is not None:
                    notificationParam = {projectDict[localizationBSDConst.COLUMN_PROJECT_ID]: returnValue}
                    uthread.new(notificationFunction, notificationParam).context = 'localizationExportManager::notificationCallback'

        return returnDict

    @classmethod
    def _CallMethodOnProject(cls, projectID, internalMethod = None, exporterMethodName = None, additionalSettings = None):
        """
        parameters
            projectID            - project to call this method on
            internalMethod       - internal method to call
            additionalSettings   - dictionary of optional parameters to be passed to exporters. The allowed list of params depends on implementation of an exporter.
        """
        projectDict = cls._GetProjectData(projectID)
        if projectDict:
            returnValue = None
            if internalMethod:
                returnValue = internalMethod(projectDict, additionalSettings)
            elif exporterMethodName:
                returnValue = cls._ExecuteExporterMethod(projectDict, exporterMethodName, additionalSettings)
            return returnValue
        else:
            return
