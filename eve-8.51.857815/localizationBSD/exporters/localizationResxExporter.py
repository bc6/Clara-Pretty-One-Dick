#Embedded file name: localizationBSD/exporters\localizationResxExporter.py
import localizationExporter
from . import LocalizationExporterError
import xml.etree.ElementTree
import os
import codecs
import cStringIO
import zipfile

def XMLPrettyPrintFromList(stringList, tab = '\t', nextLine = '\n'):
    """
        Custom function for format the xml string (list) into format where:
        xml tag can be followed by next line characters if the tag is not followed by string/text/characters;
        xml tag can be prepended with tabs if the tag is not preceeded by string/text/characters.
        NOTE: the function will overwrite stringList entries.
        parameters:
            stringList    - list containing xml broken down into tokens/substrings. As returned by xml.etree.ElementTree.tostringlist function.
            tab           - tab character/string to prepend a tag with. Not used is set to None.
            nextLine      - next line character/string to append to a tag. Not used is set to None.
                            NOTE: use "
    " for formatting into a text file string
        returns:
            flattened and formatted xml string
        """
    listLen = len(stringList)
    currentLevel = 0
    newTokens = {}
    for index, aToken in enumerate(stringList):
        if aToken[0:1] == '<' and aToken[0:2] != '</' and aToken[0:2] != '<!':
            currentLevel += 1
        if aToken[-1:] == '>' and nextLine:
            if index + 1 < listLen and stringList[index + 1][0:1] == '<':
                newTokens[index] = aToken + nextLine if index not in newTokens else newTokens[index] + nextLine
        if aToken[0:1] == '<' and currentLevel > 1 and tab:
            if index - 1 >= 0 and stringList[index - 1][-1:] == '>':
                tabString = ''.join([ tab for x in range(currentLevel - 1) ])
                newTokens[index] = tabString + aToken if index not in newTokens else tabString + newTokens[index]
        if aToken[-2:] == '/>' or aToken[0:2] == '</':
            currentLevel -= 1

    for index, newToken in newTokens.iteritems():
        stringList[index] = newToken

    return ''.join(stringList)


class LocalizationResxExporter(localizationExporter.LocalizationExporterBase):
    """
    Exports language data into .resx (xml) file, that is then used by Web applications to load language strings.
    The data doesn't include metadata and metadata related content. This is used by non-game clients.
    """
    EXPORT_DESCRIPTION = 'Exports language data into .resx (xml) file, that is then used by Web applications to load language strings.\nWhere:\nexportLocation    - location of folder under which the resource resx file is created\nexportFileName    - name of the language resource file to write (excluding extension).'
    FILE_EXT = '.resx'
    RESX_ROOT = 'root'
    RESX_HEADER = 'placeholderHeaderElement'
    RESX_MESSAGE = 'data'
    RESX_TEXT = 'value'
    RESX_LABEL = 'name'
    GROUP_SEPARATOR = '_'
    NEXTLINE = '\r\n'
    headerXML = '\n  <xsd:schema id="root" xmlns="" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:msdata="urn:schemas-microsoft-com:xml-msdata">\n    <xsd:import namespace="http://www.w3.org/XML/1998/namespace" />\n    <xsd:element name="root" msdata:IsDataSet="true">\n      <xsd:complexType>\n        <xsd:choice maxOccurs="unbounded">\n          <xsd:element name="metadata">\n            <xsd:complexType>\n              <xsd:sequence>\n                <xsd:element name="value" type="xsd:string" minOccurs="0" />\n              </xsd:sequence>\n              <xsd:attribute name="name" use="required" type="xsd:string" />\n              <xsd:attribute name="type" type="xsd:string" />\n              <xsd:attribute name="mimetype" type="xsd:string" />\n              <xsd:attribute ref="xml:space" />\n            </xsd:complexType>\n          </xsd:element>\n          <xsd:element name="assembly">\n            <xsd:complexType>\n              <xsd:attribute name="alias" type="xsd:string" />\n              <xsd:attribute name="name" type="xsd:string" />\n            </xsd:complexType>\n          </xsd:element>\n          <xsd:element name="data">\n            <xsd:complexType>\n              <xsd:sequence>\n                <xsd:element name="value" type="xsd:string" minOccurs="0" msdata:Ordinal="1" />\n                <xsd:element name="comment" type="xsd:string" minOccurs="0" msdata:Ordinal="2" />\n              </xsd:sequence>\n              <xsd:attribute name="name" type="xsd:string" use="required" msdata:Ordinal="1" />\n              <xsd:attribute name="type" type="xsd:string" msdata:Ordinal="3" />\n              <xsd:attribute name="mimetype" type="xsd:string" msdata:Ordinal="4" />\n              <xsd:attribute ref="xml:space" />\n            </xsd:complexType>\n          </xsd:element>\n          <xsd:element name="resheader">\n            <xsd:complexType>\n              <xsd:sequence>\n                <xsd:element name="value" type="xsd:string" minOccurs="0" msdata:Ordinal="1" />\n              </xsd:sequence>\n              <xsd:attribute name="name" type="xsd:string" use="required" />\n            </xsd:complexType>\n          </xsd:element>\n        </xsd:choice>\n      </xsd:complexType>\n    </xsd:element>\n  </xsd:schema>\n  <resheader name="resmimetype">\n    <value>text/microsoft-resx</value>\n  </resheader>\n  <resheader name="version">\n    <value>2.0</value>\n  </resheader>\n  <resheader name="reader">\n    <value>System.Resources.ResXResourceReader, System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089</value>\n  </resheader>\n  <resheader name="writer">\n    <value>System.Resources.ResXResourceWriter, System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089</value>\n  </resheader>\n'.replace('\n', '\r\n')

    @classmethod
    def ExportWithProjectSettings(cls, projectID, exportLocation, exportFileName, getSubmittedOnly = True, bsdBranchID = None, **kwargs):
        """
        Execute this export method for specified project, with project settings provided.
        Method queries the DB and writes language data into .resx file in the specified folder
        NOTE: inherited from LocalizationExporterBase
        parameters:
            projectID         - ID of specific project to select data for. This identifies what content will be exported.
            exportLocation    - location of folder under which the resource xml file is created
            exportFileName    - name of the language resource file(s) to write. (excluding extension)
            getSubmittedOnly  - flag to indicate if need to write submitted only BSD entries.
        
        returns:
            list of new file paths
        """
        if not exportLocation or not exportFileName:
            raise LocalizationExporterError('Filepath strings are incomplete. exportLocation, exportFileName: %s, %s.' % (exportLocation, exportFileName))
        exportedFilenames = []
        elementsList = cls._CreateXMLElements(projectID, getSubmittedOnly, bsdBranchID)
        for languageID, rootElement in elementsList:
            if languageID == 'en-us':
                exportedFilename = os.path.join(exportLocation, exportFileName + cls.FILE_EXT)
            else:
                exportedFilename = os.path.join(exportLocation, exportFileName + '.' + languageID + cls.FILE_EXT)
            try:
                textsXMLStringList = [ token.decode('utf-8') for token in xml.etree.ElementTree.tostringlist(rootElement, encoding='utf-8') ]
            except TypeError as anError:
                raise TypeError(anError.args, "Is there perhaps an attribute on XML Element with None value or non-string type value? ElementTree doesn't like that.")

            textsXMLString = XMLPrettyPrintFromList(textsXMLStringList, tab='\t', nextLine=cls.NEXTLINE)
            headerTag = '<' + cls.RESX_HEADER + ' />'
            index = textsXMLString.find(headerTag)
            xmlVersion = '<?xml version="1.0" encoding="utf-8"?>' + cls.NEXTLINE
            newXMLString = xmlVersion + textsXMLString[0:index] + cls.headerXML + textsXMLString[index + len(headerTag):]
            fileObj = codecs.open(exportedFilename, encoding='utf-8', mode='w')
            fileObj.write(newXMLString)
            fileObj.close()
            exportedFilenames.append(exportedFilename)

        return exportedFilenames

    @classmethod
    def ExportWithProjectSettingsToZipFileObject(cls, projectID, fileObject, exportFileName, getSubmittedOnly = True, bsdBranchID = None):
        """
        Generate resx files and put them into file object / stream passed as parameter, while returning zip file object.
        parameters:
            projectID         - ID of specific project to select data for. This identifies what content will be exported.
            fileObject        - file-like object that zipfile will use to write data to
            exportFileName    - first characters of every filename generated
            getSubmittedOnly  - flag to indicate if need to write submitted only BSD entries.
                                If True is passed, only submitted BSD entries are written into
                                pickles. Otherwise, latest submitted and unsubmitted BSD 
                                entries are written into pickles.
            bsdBranchID       - Specify from which BSD branch you want to export. Defaults to None.
                                Uses whatever is the branch set for the database you are exporting from if set to None.
        returns:
            zip file object, list of new pickle files
        """
        exportedFilenames = []
        zipDataFile = zipfile.ZipFile(fileObject, 'w')
        resxDataDict = cls._WriteLocalizationDataToDicts(getSubmittedOnly, projectID, bsdBranchID)
        for languageID, data in resxDataDict.iteritems():
            if languageID == 'en-us':
                exportedFilename = exportFileName + cls.FILE_EXT
            else:
                exportedFilename = exportFileName + '.' + languageID + cls.FILE_EXT
            zipDataFile.writestr(exportedFilename, data.getvalue())
            data.close()
            exportedFilenames.append(exportedFilename)

        zipDataFile.close()
        return (zipDataFile, exportedFilenames)

    @classmethod
    def _WriteLocalizationDataToDicts(cls, getSubmittedOnly, projectID, bsdBranchID = None):
        ret = {}
        elementsList = cls._CreateXMLElements(projectID, getSubmittedOnly, bsdBranchID)
        for languageID, rootElement in elementsList:
            try:
                textsXMLStringList = [ token.decode('utf-8') for token in xml.etree.ElementTree.tostringlist(rootElement, encoding='utf-8') ]
            except TypeError as anError:
                raise TypeError(anError.args, "Is there perhaps an attribute on XML Element with None value or non-string type value? ElementTree doesn't like that.")

            textsXMLString = XMLPrettyPrintFromList(textsXMLStringList, tab='\t', nextLine=cls.NEXTLINE)
            headerTag = '<' + cls.RESX_HEADER + ' />'
            index = textsXMLString.find(headerTag)
            xmlVersion = '<?xml version="1.0" encoding="utf-8"?>' + cls.NEXTLINE
            newXMLString = xmlVersion + textsXMLString[0:index] + cls.headerXML + textsXMLString[index + len(headerTag):]
            s = cStringIO.StringIO()
            s.write(newXMLString.encode('utf-8'))
            ret[languageID] = s

        return ret

    @classmethod
    def _CreateXMLElements(cls, projectID, getSubmittedOnly, bsdBranchID = None):

        def _FormatFullPath(pathString):
            return pathString.replace('/', cls.GROUP_SEPARATOR)

        elementsList = []
        exportData = cls._GetLocalizationMessageDataForExport(projectID, getSubmittedOnly, bsdBranchID)
        messagesDict = exportData[1]
        languageCodesResultSet = exportData[2]
        for languageRow in languageCodesResultSet:
            languageID = languageRow.languageID
            rootElement = xml.etree.ElementTree.Element(tag=cls.RESX_ROOT)
            elementsList.append((languageID, rootElement))
            rootElement.append(xml.etree.ElementTree.Comment(text='Microsoft ResX Schema. Generated file'))
            rootElement.append(xml.etree.ElementTree.Element(tag=cls.RESX_HEADER))
            for messageID, messageObj in sorted(messagesDict.iteritems(), key=lambda x: x[1].labelPath):
                labelPath = messageObj.labelPath if messageObj.labelPath is not None else ''
                textRow = messageObj.GetTextRow(languageID)
                if textRow is not None and textRow.text is not None:
                    textElement = xml.etree.ElementTree.Element(tag=cls.RESX_TEXT)
                    textElement.text = textRow.text
                    messageElement = xml.etree.ElementTree.Element(tag=cls.RESX_MESSAGE, attrib={cls.RESX_LABEL: _FormatFullPath(labelPath)})
                    messageElement.append(textElement)
                    rootElement.append(messageElement)

        return elementsList

    @classmethod
    def GetResourceNamesWithProjectSettings(cls, projectID, exportLocation, exportFileName, getSubmittedOnly = True, **kwargs):
        """
        Queries DB for enabled languages and returns list of files that ExportWithProjectSettings
        is expected to generate.
        NOTE: inherited from LocalizationExporterBase
        parameters:
            projectID         - ID of specific project to select data for. This identifies what content will be exported.
            exportLocation    - location of folder under which the resource xml file is created
            exportFileName    - name of the language resource file(s) to write. (excluding extension)
            getSubmittedOnly  - flag to indicate if need to write submitted only BSD entries.
            
        returns:
            list of new file paths
        """
        dbzlocalization = sm.GetService('DB2').GetSchema('zlocalization')
        languageCodesResultSet = dbzlocalization.Languages_SelectByProject(1 if getSubmittedOnly else 0, projectID)
        return [ os.path.join(exportLocation, exportFileName + '_' + languageRow.languageID + cls.FILE_EXT) for languageRow in languageCodesResultSet ]
