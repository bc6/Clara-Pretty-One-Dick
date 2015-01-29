#Embedded file name: F:\depot\streams\olafurth_olafurth-pc_STABLE_2754\fsdSchemas\schemaOptimizer.py
import copy
import collections
import ctypes
import yaml
import validator
import persistence
import os
import schemaCompare
builtInCTypesObjectTypes = {'typeID': ctypes.c_uint32,
 'localizationID': ctypes.c_uint32,
 'bool': ctypes.c_ubyte}
subIndexOffsetLookupSchema = {'type': 'dict',
 'keyTypes': {'type': 'int',
              'min': 0},
 'valueTypes': {'type': 'object',
                'attributes': {'offset': {'type': 'int',
                                          'min': 0},
                               'size': {'type': 'int',
                                        'min': 0}}}}
FLOAT_PRECISION_DEFAULT = 'single'
fixedSizeTypes = set(['float',
 'int',
 'typeID',
 'localizationID',
 'vector2',
 'vector3',
 'vector4',
 'enum',
 'bool'])

class IndexingNotSupported(Exception):

    def __init__(self, schemaType):
        self.schemaType = schemaType

    def __str__(self):
        return 'Schema of type: "%s" does not support the "indexBy" attribute' % self.schemaType


def GetKeyHeaderSchema(keySchema):
    keyHeaderSchema = {'type': 'list',
     'itemTypes': {'type': 'object',
                   'attributes': collections.OrderedDict()}}
    attrs = keyHeaderSchema['itemTypes']['attributes']
    attrs['key'] = keySchema
    attrs['offset'] = {'type': 'int',
     'min': 0}
    return keyHeaderSchema


def GetKeyHeaderSchemaWithSize(keySchema):
    keyHeaderSchema = GetKeyHeaderSchema(keySchema)
    keyHeaderSchema['itemTypes']['attributes']['size'] = {'type': 'int',
     'min': 0}
    return keyHeaderSchema


def IsUsedInTarget(schema, target):
    usage = schema.get('usage', None)
    if usage is None or usage == target or target == validator.EDITOR:
        return True
    else:
        return False


def GetLargeEnoughUnsignedTypeForMaxValue(i):
    if i <= 255:
        return ctypes.c_ubyte
    elif i <= 65536:
        return ctypes.c_uint16
    else:
        return ctypes.c_uint32


def GetAttributesForTarget(schema, target):
    orderedAttributeList = []
    attributes = schema.get('attributes')
    for attr in attributes:
        if IsUsedInTarget(attributes[attr], target):
            orderedAttributeList.append(attr)

    return orderedAttributeList


def GetOptionalAttributesForTarget(schema, target):
    return list(OptionalAttributeIterator(schema, target))


def IsAttributeOptional(schema, attributeName):
    return schema['attributes'][attributeName].get('isOptional', False)


def OptionalAttributeIterator(schema, target):
    attributes = GetAttributesForTarget(schema, target)
    for attr in attributes:
        if IsAttributeOptional(schema, attr):
            yield attr


def OptionalAndVariableSizedAttributeIterator(schema, target):
    attributes = GetAttributesForTarget(schema, target)
    for attr in attributes:
        if IsAttributeOptional(schema, attr):
            yield attr
        elif not IsFixedSize(schema['attributes'][attr], target):
            yield attr


def FixedSizeAttributeIterator(schema, target):
    attributes = GetAttributesForTarget(schema, target)
    for attr in attributes:
        if IsAttributeOptional(schema, attr):
            continue
        elif not IsFixedSize(schema['attributes'][attr], target):
            continue
        yield attr


def IsFixedSize(schema, target):
    schemaType = schema['type']
    if schemaType in fixedSizeTypes:
        return True
    if schemaType == 'object':
        attributes = schema['attributes']
        for attr in attributes:
            if not IsUsedInTarget(attributes[attr], target):
                continue
            if attributes[attr].get('isOptional', False) or not IsFixedSize(attributes[attr], target):
                return False

        return True
    return False


def GetIndexableSchemasGenerator(schema):
    stack = [schema]
    while len(stack) > 0:
        currentSchema = stack.pop()
        currentSchemaType = currentSchema['type']
        for key in currentSchema:
            if key == 'indexBy':
                if currentSchemaType != 'dict':
                    raise IndexingNotSupported(currentSchemaType)
                yield currentSchema
            elif key in ('valueTypes', 'itemTypes'):
                stack.append(currentSchema[key])
            elif key == 'attributes':
                for attribute in currentSchema['attributes']:
                    stack.append(currentSchema['attributes'][attribute])

            elif key == 'optionTypes':
                for optionSchema in currentSchema['optionTypes']:
                    stack.append(optionSchema)

            elif key == 'schema':
                stack.append(currentSchema['schema'])


def GetEnumeratedIndexableSchemas(schema):
    enumeratedIndexableSchemas = {}
    for index, nestedSchema in enumerate(GetIndexableSchemasGenerator(schema)):
        enumeratedIndexableSchemas[index] = nestedSchema

    return enumeratedIndexableSchemas


def SetNestedIndexIdInformationToIndexableSchemas(idsToIndexableSchemaLists):
    for index, indexableSchemaList in idsToIndexableSchemaLists.iteritems():
        for indexableSchema in indexableSchemaList:
            indexableSchema['nestedIndexId'] = index


def GatherEqualIndexableSchemasToUniqueId(enumeratedIndexableSchemas):
    processedSchemas = []
    indexIdToSchemas = {}
    for index, indexableSchema in enumeratedIndexableSchemas.iteritems():
        schemaEqualToAnyProcessedSchema = [ schemaCompare.SchemasEqual(indexableSchema, s) for s in processedSchemas ]
        if not any(schemaEqualToAnyProcessedSchema):
            processedSchemas.append(indexableSchema)
            indexIdToSchemas[index] = [indexableSchema]
        else:
            i = schemaEqualToAnyProcessedSchema.index(True)
            indexIdToSchemas[i].append(indexableSchema)

    return indexIdToSchemas


def GetNestedIndexNamesAsList(schema):
    indexNames = schema['indexBy']
    if not isinstance(schema['indexBy'], list):
        indexNames = [indexNames]
    return indexNames


def GetNestedIndexNamesMappedToIndexId(enumeratedIndexableSchemas):
    indexNameToNestedIndexIds = {}
    for nestedIndexId, nestedDictSchema in enumeratedIndexableSchemas.iteritems():
        indexNames = GetNestedIndexNamesAsList(nestedDictSchema)
        for indexName in indexNames:
            if indexName not in indexNameToNestedIndexIds:
                indexNameToNestedIndexIds[indexName] = []
            indexNameToNestedIndexIds[indexName].append(nestedIndexId)

    return indexNameToNestedIndexIds


def SetNestedIndexIdInformationToRootSchema(schema):
    unOptimizedIdToSchemaLookup = GetEnumeratedIndexableSchemas(schema)
    idsToIndexableSchemaList = GatherEqualIndexableSchemasToUniqueId(unOptimizedIdToSchemaLookup)
    SetNestedIndexIdInformationToIndexableSchemas(idsToIndexableSchemaList)
    optimizedIdToSchemaLookup = {}
    for s in unOptimizedIdToSchemaLookup.values():
        optimizedIdToSchemaLookup[s['nestedIndexId']] = s

    schema['indexableSchemas'] = optimizedIdToSchemaLookup
    schema['indexNameToIds'] = GetNestedIndexNamesMappedToIndexId(optimizedIdToSchemaLookup)


def OptimizeDictSchema(schema, target, pathRoot):
    newSchema = {'type': 'dict',
     'keyTypes': OptimizeSchema(schema['keyTypes'], target, pathRoot),
     'valueTypes': OptimizeSchema(schema['valueTypes'], target, pathRoot)}
    if 'isOptional' in schema:
        newSchema['isOptional'] = schema['isOptional']
    requiresSizeLookup = False
    if schema.get('buildIndex', False) or schema.get('multiIndex', False):
        newSchema['buildIndex'] = True
        requiresSizeLookup = True
    if 'indexBy' in schema:
        requiresSizeLookup = True
        newSchema['indexBy'] = schema['indexBy']
    if 'multiIndex' in schema:
        newSchema['multiIndex'] = schema['multiIndex']
        newSchema['subIndexOffsetLookup'] = OptimizeSchema(subIndexOffsetLookupSchema, target, pathRoot)
        SetNestedIndexIdInformationToRootSchema(newSchema)
    if requiresSizeLookup:
        keyFooterSchema = GetKeyHeaderSchemaWithSize(schema['keyTypes'])
    else:
        keyFooterSchema = GetKeyHeaderSchema(schema['keyTypes'])
    newSchema['keyFooter'] = OptimizeSchema(keyFooterSchema, target, pathRoot)
    return newSchema


def OptimizeListSchema(schema, target, pathRoot):
    newSchema = {'type': 'list',
     'itemTypes': OptimizeSchema(schema['itemTypes'], target, pathRoot)}
    if 'size' in newSchema['itemTypes']:
        newSchema['fixedItemSize'] = newSchema['itemTypes']['size']
    if 'length' in schema:
        newSchema['length'] = schema['length']
    if 'isOptional' in schema:
        newSchema['isOptional'] = schema['isOptional']
    return newSchema


def OptimizeObjectSchema(schema, target, pathRoot):
    newSchema = {'type': 'object'}
    if 'isOptional' in schema:
        newSchema['isOptional'] = schema['isOptional']
    newSchema['attributes'] = collections.OrderedDict()
    newSchema['constantAttributeOffsets'] = {}
    newSchema['attributesWithVariableOffsets'] = []
    newSchema['optionalValueLookups'] = {}
    newSchema['size'] = 0
    currentOffset = 0
    optionalAttributeValue = 1
    attributeSchemas = schema['attributes']
    for attributeName in FixedSizeAttributeIterator(schema, target):
        optimizedAttributeSchema = OptimizeSchema(attributeSchemas[attributeName], target, pathRoot)
        knownSizeOfAttribute = optimizedAttributeSchema['size']
        newSchema['constantAttributeOffsets'][attributeName] = currentOffset
        newSchema['attributes'][attributeName] = optimizedAttributeSchema
        currentOffset += knownSizeOfAttribute

    newSchema['endOfFixedSizeData'] = currentOffset
    newSchema['size'] = currentOffset
    for attributeName in OptionalAndVariableSizedAttributeIterator(schema, target):
        if 'size' in newSchema:
            del newSchema['size']
        if IsAttributeOptional(schema, attributeName):
            newSchema['optionalValueLookups'][attributeName] = optionalAttributeValue
            optionalAttributeValue <<= 1
        optimizedAttributeSchema = OptimizeSchema(attributeSchemas[attributeName], target, pathRoot)
        newSchema['attributes'][attributeName] = optimizedAttributeSchema
        newSchema['attributesWithVariableOffsets'].append(attributeName)

    if optionalAttributeValue != 1:
        newSchema['maxBitFieldValue'] = optionalAttributeValue >> 1
    return newSchema


def OptimizeEnumSchema(schema, target, pathRoot):
    newSchema = {'type': 'enum'}
    maxEnumValue = max(schema['values'].values())
    newSchema['maxEnumValue'] = maxEnumValue
    newSchema['size'] = ctypes.sizeof(GetLargeEnoughUnsignedTypeForMaxValue(maxEnumValue))
    newSchema['values'] = schema['values']
    if 'readEnumValue' in schema:
        newSchema['readEnumValue'] = schema['readEnumValue']
    if 'isOptional' in schema:
        newSchema['isOptional'] = schema['isOptional']
    if 'default' in schema:
        newSchema['default'] = schema['default']
    return newSchema


def OptimizeIntSchema(schema, target, pathRoot):
    newSchema = {'type': 'int'}
    intType = ctypes.c_int32
    if 'min' in schema:
        newSchema['min'] = schema['min']
    if 'exclusiveMin' in schema:
        newSchema['exclusiveMin'] = schema['exclusiveMin']
    if 'max' in schema:
        newSchema['max'] = schema['max']
    if 'exclusiveMax' in schema:
        newSchema['exclusiveMax'] = schema['exclusiveMax']
    newSchema['size'] = ctypes.sizeof(intType)
    if 'isOptional' in schema:
        newSchema['isOptional'] = schema['isOptional']
    if 'default' in schema:
        newSchema['default'] = schema['default']
    return newSchema


def OptimizeFloatSchema(schema, target, pathRoot):
    newSchema = {'type': schema['type']}
    if 'isOptional' in schema:
        newSchema['isOptional'] = schema['isOptional']
    if 'precision' in schema:
        newSchema['precision'] = schema['precision']
    precision = schema.get('precision', FLOAT_PRECISION_DEFAULT)
    if precision == 'double':
        newSchema['size'] = ctypes.sizeof(ctypes.c_double)
    else:
        newSchema['size'] = ctypes.sizeof(ctypes.c_float)
    if 'default' in schema:
        newSchema['default'] = schema['default']
    return newSchema


def OptimizeVectorSchema(schema, target, pathRoot):
    newSchema = {'type': schema['type']}
    if 'aliases' in schema:
        newSchema['aliases'] = schema['aliases']
    if 'isOptional' in schema:
        newSchema['isOptional'] = schema['isOptional']
    if 'precision' in schema:
        newSchema['precision'] = schema['precision']
    if schema['type'] == 'vector2':
        itemCount = 2
    elif schema['type'] == 'vector3':
        itemCount = 3
    elif schema['type'] == 'vector4':
        itemCount = 4
    precision = schema.get('precision', FLOAT_PRECISION_DEFAULT)
    if precision == 'double':
        newSchema['size'] = ctypes.sizeof(ctypes.c_double * itemCount)
    else:
        newSchema['size'] = ctypes.sizeof(ctypes.c_float * itemCount)
    return newSchema


def OptimizeBinarySchema(schema, target, pathRoot):
    newSchema = {'type': schema['type']}
    if 'schema' in schema:
        dataSchema = OptimizeSchema(schema['schema'], target, pathRoot)
        newSchema['schema'] = dataSchema
        if 'size' in dataSchema:
            newSchema['size'] = dataSchema['size']
        if 'isOptional' in dataSchema:
            newSchema['isOptional'] = dataSchema['isOptional']
    return newSchema


def OptimizeUnionSchema(schema, target, pathRoot):
    newSchema = {'type': schema['type'],
     'optionTypes': []}
    for unionType in schema['optionTypes']:
        dataSchema = OptimizeSchema(unionType, target, pathRoot)
        newSchema['optionTypes'].append(dataSchema)

    return newSchema


builtInSchemaOptimizationFunctions = {'dict': OptimizeDictSchema,
 'list': OptimizeListSchema,
 'object': OptimizeObjectSchema,
 'enum': OptimizeEnumSchema,
 'int': OptimizeIntSchema,
 'vector2': OptimizeVectorSchema,
 'vector3': OptimizeVectorSchema,
 'vector4': OptimizeVectorSchema,
 'binary': OptimizeBinarySchema,
 'float': OptimizeFloatSchema,
 'union': OptimizeUnionSchema}

def LoadReferencedSchema(reference, pathRoot):
    schemaFilePath = reference.get('schemaFile')
    schemaName = reference.get('schema')
    print 'loading', schemaName, 'from', schemaFilePath
    if pathRoot is None:
        raise Exception('Could not optimize schema without a path root with which to load referenced schemas')
    with open(os.path.join(pathRoot, schemaFilePath), 'r') as schemaFile:
        schemas = persistence.LoadSchema(schemaFile)['schemas']
        schema = schemas[schemaName]
    return schema


def OptimizeSchema(schema, target, pathRoot = None):
    reference = schema.get('schemaReference', None)
    if reference is not None:
        schema = LoadReferencedSchema(reference, pathRoot)
    schemaType = schema.get('type')
    if schemaType in builtInSchemaOptimizationFunctions:
        return builtInSchemaOptimizationFunctions[schemaType](schema, target, pathRoot)
    else:
        newSchema = {'type': schemaType}
        if 'isOptional' in schema:
            newSchema['isOptional'] = schema['isOptional']
        if 'default' in schema:
            newSchema['default'] = schema['default']
        if schemaType in builtInCTypesObjectTypes:
            newSchema['size'] = ctypes.sizeof(builtInCTypesObjectTypes[schemaType])
        return newSchema


def orderedDict_representer(dumper, data):
    mappingSequence = []
    n = yaml.MappingNode(u'tag:yaml.org,2002:map', mappingSequence, flow_style=False)
    dumper.represented_objects[id(data)] = n
    for item_key, item_value in data.iteritems():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)
        mappingSequence.append((node_key, node_value))

    return n


class SafeSchemaRepresenter(yaml.SafeDumper):
    pass


SafeSchemaRepresenter.add_representer(collections.OrderedDict, orderedDict_representer)

def PersistOptimizedSchema(schema):
    return yaml.dump(schema, Dumper=SafeSchemaRepresenter)
