#Embedded file name: F:\depot\streams\olafurth_olafurth-pc_STABLE_2754\fsdSchemas\validator.py
import re
import collections
import os
import yaml
try:
    import pyodbc
    dbConnectionForValidationAvailable = True
    dbConnections = {}
except ImportError:
    dbConnectionForValidationAvailable = False

CLIENT = 'Client'
SERVER = 'Server'
EDITOR = 'Editor'
ASCENDING = 'Ascending'
DESCENDING = 'Descending'
import persistence

class SchemaMismatch(Exception):

    def __init__(self, path, message):
        self.filePath = None
        self.path = path
        self.message = message

    def SetFilePath(self, filePath):
        self.filePath = filePath

    def __str__(self):
        if self.filePath is None:
            return self.message
        else:
            return self.filePath + ':\n\t' + self.message


class SchemaTypeError(SchemaMismatch):
    pass


class SchemaComparisonError(SchemaMismatch):
    pass


class SchemaObjectAttributeMissingError(SchemaMismatch):
    pass


class SchemaObjectAttributeNotInSchemaError(SchemaMismatch):
    pass


class ExternalReferenceError(SchemaMismatch):
    pass


class ValidationException(SchemaMismatch):

    def __init__(self, path, errors):
        self.filePath = None
        self.path = path
        self.message = '\n\t'.join([ str(error) for error in errors ])


class SchemaError(Exception):

    def __init__(self, path, message, node, data):
        self.path = path
        self.message = message
        self.node = node
        self.data = data

    def __str__(self):
        return self.message


def ListContainsType(errorList, errorType):
    match = [ e for e in errorList if isinstance(e, errorType) ]
    return len(match) > 0


def AllFloatValues(i):
    return all(map(lambda x: type(x) in (float, int, long), i))


def ValidateInt(schemaNode, o, path = 'root', state = {}):
    if type(o) not in (int, long):
        return [SchemaTypeError(path, '%s: Type Mismatch - should be an integer: %s' % (path, str(o)))]
    errors = []
    if 'min' in schemaNode:
        if o < schemaNode['min']:
            errors.append(SchemaComparisonError(path, '%s: Range mismatch - value %i is less than the minimum value of %i' % (path, o, schemaNode['min'])))
    elif 'exclusiveMin' in schemaNode:
        if o <= schemaNode['exclusiveMin']:
            errors.append(SchemaComparisonError(path, '%s: Range mismatch - value %i is less than or equal to the minimum value of %i' % (path, o, schemaNode['exclusiveMin'])))
    if 'max' in schemaNode:
        if o > schemaNode['max']:
            errors.append(SchemaComparisonError(path, '%s: Range mismatch - value %i is less than the maximum value of %i' % (path, o, schemaNode['max'])))
    elif 'exclusiveMax' in schemaNode:
        if o >= schemaNode['exclusiveMax']:
            errors.append(SchemaComparisonError(path, '%s: Range mismatch - value %i is less than or equal to the maximum value of %i' % (path, o, schemaNode['exclusiveMax'])))
    return errors


def ValidateTypeID(schemaNode, o, path = 'root', state = {}):
    errors = ValidateInt(schemaNode, o, path, state)
    if not ListContainsType(errors, SchemaTypeError) and o < 0:
        errors.append(SchemaComparisonError(path, '%s: Range Mismatch - typeIDs should be > 0, this is %i' % (path, o)))
    return errors


def ValidateLocalizationID(schemaNode, o, path = 'root', state = {}):
    errors = ValidateInt(schemaNode, o, path, state)
    if not ListContainsType(errors, SchemaTypeError) and o < 0:
        errors.append(SchemaComparisonError(path, '%s: Range Mismatch - typeIDs should be > 0, this is %i' % (path, o)))
    return errors


def ValidateFloat(schemaNode, o, path = 'root', state = {}):
    errors = []
    if type(o) not in (float, int, long):
        return [SchemaTypeError(path, '%s: Type Mismatch - should be a float' % path)]
    if 'min' in schemaNode:
        if o < schemaNode['min']:
            errors.append(SchemaComparisonError(path, '%s: Range mismatch - value %.1g is less than the minimum value of %.1g' % (path, o, schemaNode['min'])))
    elif 'exclusiveMin' in schemaNode:
        if o <= schemaNode['exclusiveMin']:
            errors.append(SchemaComparisonError(path, '%s: Range mismatch - value %.1g is less than or equal to the minimum value of %.1g' % (path, o, schemaNode['exclusiveMin'])))
    if 'max' in schemaNode:
        if o > schemaNode['max']:
            errors.append(SchemaComparisonError(path, '%s: Range mismatch - value %.1g is less than the maximum value of %.1g' % (path, o, schemaNode['max'])))
    elif 'exclusiveMax' in schemaNode:
        if o >= schemaNode['exclusiveMax']:
            errors.append(SchemaComparisonError(path, '%s: Range mismatch - value %.1g is less than or equal to the maximum value of %.1g' % (path, o, schemaNode['exclusiveMax'])))
    return errors


def ValidateBool(schemaNode, o, path = 'root', state = {}):
    errors = []
    if type(o) is not bool:
        errors.append(SchemaTypeError(path, '%s: Type Mismatch - should be a bool' % path))
    return errors


def ValidateCommonStringAttributes(schemaNode, o, path):
    typeName = 'string'
    if isinstance(o, unicode):
        typeName = 'unicode'
    errors = []
    if 'length' in schemaNode:
        if len(o) != schemaNode['length']:
            errors.append(SchemaComparisonError(path, "%s: Length mismatch - %s '%s' should be %i characters long" % (path,
             typeName,
             o.encode('utf-8'),
             schemaNode['length'])))
    if 'minLength' in schemaNode:
        if len(o) < schemaNode['minLength']:
            errors.append(SchemaComparisonError(path, "%s: Length mismatch - %s '%s' should be at least %i characters long" % (path,
             typeName,
             o.encode('utf-8'),
             schemaNode['minLength'])))
    if 'maxLength' in schemaNode:
        if len(o) > schemaNode['maxLength']:
            errors.append(SchemaComparisonError(path, "%s: Length mismatch - %s '%s' should be at most %i characters long" % (path,
             typeName,
             o.encode('utf-8'),
             schemaNode['maxLength'])))
    if 'regex' in schemaNode:
        if isinstance(o, unicode):
            regex = re.compile(schemaNode['regex'], re.UNICODE)
        else:
            regex = re.compile(schemaNode['regex'])
        if not regex.match(o):
            errors.append(SchemaComparisonError(path, "%s: Regex mismatch - %s '%s' does not match the regex '%s'" % (path,
             typeName,
             o.encode('utf-8'),
             schemaNode['regex'].encode('utf-8'))))
    return errors


def ValidateString(schemaNode, o, path = 'root', state = {}):
    if type(o) is not str:
        return [SchemaTypeError(path, '%s: Type Mismatch - should be a string' % path)]
    return ValidateCommonStringAttributes(schemaNode, o, path)


def ValidateUnicode(schemaNode, o, path = 'root', state = {}):
    if type(o) not in (unicode, str):
        return [SchemaTypeError(path, '%s: Type Mismatch - should be unicode' % path)]
    return ValidateCommonStringAttributes(schemaNode, o, path)


def ValidateResPath(schemaNode, o, path = 'root', state = {}):
    errors = ValidateString(schemaNode, o, path, state)
    if not ListContainsType(errors, SchemaTypeError):
        if not o.startswith('res:/'):
            errors.append(SchemaComparisonError(path, "%s: Type Mismatch - resPaths should start with 'res:/' - %s" % (path, o)))
        if 'extensions' in schemaNode:
            fileName, fileExtension = os.path.splitext(o)
            fileExtension = fileExtension[1:]
            if fileExtension not in schemaNode['extensions']:
                supportedExtension = ', '.join([ "'%s'" % extension for extension in schemaNode['extensions'] ])
                errors.append(SchemaComparisonError(path, '%s: Type Mismatch - this resPath supports the following extensions: %s - %s' % (path, supportedExtension, o)))
        if ' ' in o:
            errors.append(SchemaComparisonError(path, '%s: Type Mismatch - resPaths should not contain spaces - %s' % (path, o)))
        if '\\' in o:
            errors.append(SchemaComparisonError(path, '%s: Type Mismatch - resPaths should not contain backslashes - %s' % (path, o)))
    return errors


def ValidateVector2(schemaNode, o, path = 'root', state = {}):
    if type(o) not in (tuple, list):
        return [SchemaTypeError(path, '%s: Type Mismatch - should be a vector2' % path)]
    errors = []
    if len(o) != 2:
        errors.append(SchemaComparisonError(path, '%s: Length Mismatch - should be a vector2' % path))
    if not AllFloatValues(o):
        errors.append(SchemaComparisonError(path, '%s: Type Mismatch - should be a vector2 (contents are not all numeric!)' % path))
    return errors


def ValidateVector3(schemaNode, o, path = 'root', state = {}):
    if type(o) not in (tuple, list):
        return [SchemaTypeError(path, '%(path)s: Type Mismatch - should be a vector3: (%(repr)s)' % {'path': path,
          'repr': repr(o)})]
    errors = []
    if len(o) != 3:
        errors.append(SchemaComparisonError(path, '%s: Length Mismatch - should be a vector3' % path))
    if not AllFloatValues(o):
        errors.append(SchemaComparisonError(path, '%s: Type Mismatch - should be a vector3 (contents are not all numeric!)' % path))
    return errors


def ValidateVector4(schemaNode, o, path = 'root', state = {}):
    if type(o) not in (tuple, list):
        return [SchemaTypeError(path, '%s: Type Mismatch - should be a vector4' % path)]
    errors = []
    if len(o) != 4:
        errors.append(SchemaComparisonError(path, '%s: Length Mismatch - should be a vector4' % path))
    if not AllFloatValues(o):
        errors.append(SchemaComparisonError(path, '%s: Type Mismatch - should be a vector4 (contents are not all numeric!)' % path))
    return errors


def ValidateObject(schemaNode, o, path = 'root', state = {}):
    errors = []
    if type(o) is not dict:
        return [SchemaTypeError(path, '%s: Type Mismatch - should be an object' % path)]
    for attrName, attrValue in schemaNode.get('attributes').iteritems():
        if not attrValue.get('generatedData', False) and not attrValue.get('isOptional', False) and attrName not in o:
            errors.append(SchemaObjectAttributeMissingError(path, "%s: Attribute Mismatch - required attribute '%s' is missing!" % (path, attrName)))
        if attrName in o:
            errors.extend(Validate(attrValue, o[attrName], path + '.%s' % attrName, state))

    for attrName in o:
        if attrName not in schemaNode.get('attributes'):
            errors.append(SchemaObjectAttributeNotInSchemaError(path, "%s: Attribute Mismatch - attribute '%s' does not exist in the schema!" % (path, attrName)))

    return errors


def ValidateList(schemaNode, o, path = 'root', state = {}):
    try:
        it = enumerate(o)
    except TypeError:
        return [SchemaTypeError(path, '%s: Type Mismatch - should be itterable' % path)]

    sortKey = schemaNode.get('sortKey', None)
    sortOrder = schemaNode.get('sortOrder', ASCENDING)
    originalLast = object()
    last = originalLast
    errors = []
    listOutOfOrder = False
    for index, i in it:
        if last is not originalLast:
            compare1 = last
            compare2 = i
            if sortKey is not None:
                if sortKey not in last:
                    return [SchemaObjectAttributeMissingError(path + '[%i]' % (index - 1), "%s: Sort Attribute Missing - required attribute '%s' is missing!" % (path + '[%i]' % (index - 1), sortKey))]
                if sortKey not in i:
                    return [SchemaObjectAttributeMissingError(path + '[%i]' % index, "%s: Sort Attribute Missing - required attribute '%s' is missing!" % (path + '[%i]' % index, sortKey))]
                compare1 = last[sortKey]
                compare2 = i[sortKey]
            if sortOrder not in (ASCENDING, DESCENDING):
                errors.append(SchemaError(path, "sortOrder attribute in schema must be either '%s' or '%s', not %s" % (ASCENDING, DESCENDING, sortOrder), schemaNode, o))
            if sortOrder == ASCENDING and not listOutOfOrder:
                if compare1 >= compare2:
                    errors.append(SchemaComparisonError(path + '[%i]' % index, '%s: Order Error! Sort key: %s. List should be sorted ASCENDING. %s >= %s!' % (path + '[%i]' % index,
                     sortKey,
                     str(compare1),
                     str(compare2))))
                    listOutOfOrder = True
            elif sortOrder == DESCENDING and not listOutOfOrder:
                if compare1 <= compare2:
                    errors.append(SchemaComparisonError(path + '[%i]' % index, '%s: Order Error! Sort key: %s. List should be sorted DESCENDING. %s <= %s!' % (path + '[%i]' % index,
                     sortKey,
                     str(compare1),
                     str(compare2))))
                    listOutOfOrder = True
        errors.extend(Validate(schemaNode.get('itemTypes'), i, path + '[%i]' % index, state))
        last = i

    return errors


def ValidateDict(schemaNode, o, path = 'root', state = {}):
    if type(o) not in (dict, collections.OrderedDict, collections.defaultdict):
        return [SchemaTypeError(path, '%s: Type Mismatch - should be itterable' % path)]
    errors = []
    for dictKey, dictValue in o.iteritems():
        errors.extend(Validate(schemaNode['keyTypes'], dictKey, path + '<%s>' % str(dictKey), state))
        errors.extend(Validate(schemaNode['valueTypes'], dictValue, path + '[%s]' % str(dictKey), state))

    return errors


def ValidateEnum(schemaNode, o, path = 'root', state = {}):
    if o not in schemaNode.get('values', {}):
        return [SchemaTypeError(path, '%s: Enum value not found in schema: %s' % (path, repr(o)))]
    return []


def ValidateUnion(schemaNode, o, path = 'root', state = {}):
    for s in schemaNode['optionTypes']:
        validationErrors = Validate(s, o, path, state)
        if len(validationErrors) == 0:
            break
    else:
        return [SchemaTypeError(path, '%s: Did not match any of the possible schema types: %s' % (path, repr(o)))]

    return []


builtInValdationFunctions = {'int': ValidateInt,
 'typeID': ValidateTypeID,
 'localizationID': ValidateTypeID,
 'float': ValidateFloat,
 'vector2': ValidateVector2,
 'vector3': ValidateVector3,
 'vector4': ValidateVector4,
 'dict': ValidateDict,
 'list': ValidateList,
 'object': ValidateObject,
 'enum': ValidateEnum,
 'string': ValidateString,
 'unicode': ValidateUnicode,
 'resPath': ValidateResPath,
 'bool': ValidateBool,
 'union': ValidateUnion}

def GetSetOfKeysFromBSDTable(cursor, key, table):
    setOfKeys = set()
    tableRow = cursor.execute('SELECT tableID from zsystem.tablesEx where fullName = ?', table)
    tableID = tableRow.fetchone().tableID
    sqlStatement = '\n        select t.%(key)s as thisKey\n        from zstatic.SubmittedRevisions(?) r \n        inner join %(table)s t on t.dataID = r.dataID' % {'key': key,
     'table': table}
    try:
        rows = cursor.execute(sqlStatement, tableID)
    except pyodbc.ProgrammingError:
        print sqlStatement
        raise

    for r in rows:
        setOfKeys.add(r.thisKey)

    return setOfKeys


def ValidateReference(schemaNode, o, path, state):
    referenceInfo = schemaNode.get('reference')
    if not state.get('validateReferences', False):
        return []
    if 'database' in referenceInfo and dbConnectionForValidationAvailable:
        serverDB = (referenceInfo['server'], referenceInfo['database'])
        if serverDB in dbConnections:
            connection, cursor = dbConnections[serverDB]
        else:
            try:
                print 'Connecting to DB'
                connection = pyodbc.connect('DRIVER={SQL Server};SERVER=%s;DATABASE=%s;Trusted_Connection=yes' % serverDB)
                cursor = connection.cursor()
                dbConnections[serverDB] = (connection, cursor)
            except pyodbc.Error:
                print 'ERROR: Could not connect to server %s and database %s to validate external reference. It may be that you do not have domain account access to read this DB.' % serverDB
                connection = None
                cursor = None
                dbConnections[serverDB] = (None, None)
                return []

        if connection is None:
            return []
        if 'cachedKeySets' not in state:
            state['cachedKeySets'] = {}
        cachedKey = (referenceInfo['key'], referenceInfo['table'])
        if cachedKey not in state['cachedKeySets']:
            setOfKeys = GetSetOfKeysFromBSDTable(cursor, referenceInfo['key'], referenceInfo['table'])
            state['cachedKeySets'][cachedKey] = setOfKeys
        else:
            setOfKeys = state['cachedKeySets'][cachedKey]
        if o not in setOfKeys:
            errorString = '%(path)s: ' + referenceInfo['errorMessage']
            return [ExternalReferenceError(path, errorString % {'path': path,
              'key': str(o),
              'server': referenceInfo['server'],
              'database': referenceInfo['database'],
              'table': referenceInfo['table']})]
    elif 'schema' in referenceInfo and 'branchRoot' in state:
        if 'openSchemas' not in state:
            state['openSchemas'] = {}
            state['openData'] = {}
        otherSchemaPath = os.path.abspath(os.path.join(state['branchRoot'], referenceInfo['schema']))
        if 'schemaCache' in state and otherSchemaPath in state['schemaCache']:
            otherSchema = state['schemaCache'].Get(otherSchemaPath)
        elif otherSchemaPath not in state['openSchemas']:
            with open(otherSchemaPath, 'r') as otherSchemaFile:
                otherSchema = state['openSchemas'][otherSchemaPath] = persistence.LoadSchema(otherSchemaFile)
        else:
            otherSchema = state['openSchemas'][otherSchemaPath]
        editorSchema = persistence.GetEditorSchema(otherSchema)
        editorFile = otherSchema['editorFile'] % {'key': o}
        fullEditorFilePath = os.path.abspath(os.path.join(state['branchRoot'], editorFile))
        if 'dataCache' in state and fullEditorFilePath in state['dataCache']:
            otherData = state['dataCache'].Get(fullEditorFilePath)
        elif fullEditorFilePath not in state['openData']:
            with open(fullEditorFilePath, 'r') as otherDataFile:
                otherData = state['openData'][fullEditorFilePath] = yaml.load(otherDataFile)
        else:
            otherData = state['openData'][fullEditorFilePath]
        if o not in otherData:
            errorString = '%(path)s: ' + referenceInfo['errorMessage']
            return [ExternalReferenceError(path, errorString % {'path': path,
              'key': str(o),
              'dataFile': fullEditorFilePath})]
    return []


def Validate(schemaNode, o, path = 'root', state = {}):
    nodeType = schemaNode.get('type', None)
    if nodeType is None:
        return [SchemaError(path, "%s: Could not find a 'type' for the schema node" % path, schemaNode, o)]
    errors = []
    if schemaNode.get('generatedData', False):
        return errors
    if 'reference' in schemaNode:
        errors.extend(ValidateReference(schemaNode, o, path, state))
    if nodeType in state.get('overrides', {}):
        errors.extend(state.get('overrides', {})[nodeType](schemaNode, o, path, state))
    elif nodeType in builtInValdationFunctions:
        errors.extend(builtInValdationFunctions[nodeType](schemaNode, o, path, state))
    else:
        return [SchemaError(path, "%s: Could not find a known 'type' for the schema node: %s" % (path, nodeType), schemaNode, o)]
    return errors


def ValidateWithExceptions(schemaNode, o, path = 'root', state = {}, showOnlyFirstError = True):
    errors = Validate(schemaNode, o, path, state)
    if len(errors):
        if showOnlyFirstError:
            raise ValidationException(path, [errors[0]])
        else:
            raise ValidationException(path, errors)
