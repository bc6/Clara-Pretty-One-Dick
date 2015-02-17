#Embedded file name: F:\depot\streams\olafurth_olafurth-pc_STABLE_2754\fsdSchemas\binaryRepresenter.py
import ctypes
import cStringIO
import schemaOptimizer
from path import FsdDataPathObject
import validator
import struct
import cPickle
from nestedIndexedOffsetData import IndexedOffsetData
uint32 = struct.Struct('I')
int32 = struct.Struct('i')
vector2_float = struct.Struct('ff')
vector2_double = struct.Struct('dd')
vector3_float = struct.Struct('fff')
vector3_double = struct.Struct('ddd')
vector4_float = struct.Struct('ffff')
vector4_double = struct.Struct('dddd')

def StringAsBinaryStringWithIndexedOffsetData(s, schema, path):
    return (uint32.pack(len(s)) + s, IndexedOffsetData())


def UnicodeStringAsBinaryStringWithIndexedOffsetData(s, schema, path):
    encodedString = s.encode('utf-8')
    return StringAsBinaryStringWithIndexedOffsetData(encodedString, schema, path)


def IntAsBinaryStringWithIndexedOffsetData(i, schema, path):
    intType = int32
    if 'min' in schema and schema['min'] >= 0 or 'exclusiveMin' in schema and schema['exclusiveMin'] >= -1:
        intType = uint32
    return (intType.pack(i), IndexedOffsetData())


def FloatAsBinaryStringWithIndexedOffsetData(f, schema, path):
    if schema.get('precision', 'single') == 'double':
        t = ctypes.c_double
    else:
        t = ctypes.c_float
    r = t(f)
    return (ctypes.string_at(ctypes.addressof(r), ctypes.sizeof(r)), IndexedOffsetData())


def Vector2AsBinaryStringWithIndexedOffsetData(v, schema, path):
    if schema.get('precision', 'single') == 'double':
        t = vector2_double
    else:
        t = vector2_float
    return (t.pack(*v), IndexedOffsetData())


def Vector3AsBinaryStringWithIndexedOffsetData(v, schema, path):
    if schema.get('precision', 'single') == 'double':
        t = vector3_double
    else:
        t = vector3_float
    return (t.pack(*v), IndexedOffsetData())


def Vector4AsBinaryStringWithIndexedOffsetData(v, schema, path):
    if schema.get('precision', 'single') == 'double':
        t = vector4_double
    else:
        t = vector4_float
    return (t.pack(*v), IndexedOffsetData())


def BoolAsBinaryStringWithIndexedOffsetData(v, schema, path):
    r = ctypes.c_ubyte(255 if v else 0)
    return (ctypes.string_at(ctypes.addressof(r), ctypes.sizeof(r)), IndexedOffsetData())


def EnumAsBinaryStringWithIndexedOffsetData(e, schema, path):
    maxEnumValue = max(schema['values'].values())
    enumType = schemaOptimizer.GetLargeEnoughUnsignedTypeForMaxValue(maxEnumValue)
    r = enumType(schema['values'][e])
    return (ctypes.string_at(ctypes.addressof(r), ctypes.sizeof(r)), IndexedOffsetData())


def ListAsBinaryStringWithIndexedOffsetData(l, schema, path):
    representation = cStringIO.StringIO()
    listLength = len(l)
    indexedOffsetDataForListItems = IndexedOffsetData()
    if 'length' not in schema:
        representation.write(uint32.pack(listLength))
    if 'fixedItemSize' in schema:
        for i, item in enumerate(l):
            b, indexedOffsetData = RepresentAsBinaryWithIndexedOffsetData(item, schema['itemTypes'], FsdDataPathObject('[%s]' % i, parent=path))
            representation.write(b)

    else:
        baseOffset = ctypes.sizeof(ctypes.c_uint32) * (listLength + 1)
        offset = baseOffset
        offsetArray = (ctypes.c_uint32 * listLength)()
        listData = cStringIO.StringIO()
        for i, item in enumerate(l):
            b, indexedOffsetData = RepresentAsBinaryWithIndexedOffsetData(item, schema['itemTypes'], FsdDataPathObject('[%s]' % i, parent=path))
            offsetArray[i] = offset
            offset += len(b)
            listData.write(b)
            if not indexedOffsetData.isEmpty():
                indexedOffsetData.AddOffset(offsetArray[i])
                indexedOffsetDataForListItems.AddNestedIndexedOffsetData(indexedOffsetData)

        offsetHeader = ctypes.string_at(ctypes.addressof(offsetArray), ctypes.sizeof(offsetArray))
        representation.write(offsetHeader)
        representation.write(listData.getvalue())
    return (representation.getvalue(), indexedOffsetDataForListItems)


def DictAsBinaryStringWithIndexedOffsetData(d, schema, path):
    keySchema = schema['keyFooter']
    sortedKeyList = [ k for k in sorted(d.keys()) ]
    offsets = []
    indexedOffsetData = IndexedOffsetData()
    dataRepresentation = cStringIO.StringIO()
    offsetToData = 4
    includeDataItemSizeInKeyList = 'size' in keySchema['itemTypes']['attributes']
    for key in sortedKeyList:
        b, nestedOffsetData = RepresentAsBinaryWithIndexedOffsetData(d[key], schema['valueTypes'], FsdDataPathObject('[%s]' % key, parent=path))
        offset = dataRepresentation.tell()
        footerData = {'key': key,
         'offset': offset}
        if not nestedOffsetData.isEmpty():
            nestedOffsetData.AddOffset(offset + offsetToData)
            indexedOffsetData.AddNestedIndexedOffsetData(nestedOffsetData)
        if includeDataItemSizeInKeyList:
            footerData['size'] = len(b)
        offsets.append(footerData)
        dataRepresentation.write(b)

    offsetTable = RepresentAsBinary(offsets, keySchema, path)
    dictFooter = offsetTable + uint32.pack(len(offsetTable))
    binaryData = dataRepresentation.getvalue()
    if 'indexBy' in schema:
        for offset in offsets:
            indexedOffsetData.AddKeyOffsetSizeAndPathToNestedIndexId(offset['key'], offset['offset'], offset['size'], path, schema['nestedIndexId'])

    elif schema.get('multiIndex', False):
        offsetToIndexedOffset = 4 + len(binaryData)
        nestedOffsets = RepresentIndexedOffsetDataAsBinary(indexedOffsetData, schema, offsetToIndexedOffset)
        dictFooter = nestedOffsets + dictFooter
    return (uint32.pack(len(binaryData + dictFooter)) + binaryData + dictFooter, indexedOffsetData)


def RepresentIndexedOffsetDataAsBinary(indexedOffsetData, schema, offsetToAttribute):
    indexableSchemas = schema['indexableSchemas']
    offsetToIndexedOffsetData = offsetToAttribute
    binaryOffsetData = cStringIO.StringIO()
    offsetLookupTable = {}
    flattenedIndexedOffsetData = indexedOffsetData.Flatten()
    for nestedIndex, indexableSchema in indexableSchemas.iteritems():
        if nestedIndex not in flattenedIndexedOffsetData:
            recreatedOffsetData = []
        else:
            recreatedOffsetData = [ {'key': key,
             'offset': offset,
             'size': size} for key, offset, size, path in flattenedIndexedOffsetData[nestedIndex] ]
        b = RepresentAsBinary(recreatedOffsetData, indexableSchema['keyFooter'], None)
        binaryOffsetData.write(b)
        offsetLookupTable[nestedIndex] = {'offset': offsetToIndexedOffsetData,
         'size': len(b)}
        offsetToIndexedOffsetData += len(b)

    builtOffsetLookupTable = RepresentAsBinary(offsetLookupTable, schema['subIndexOffsetLookup'], None)
    return binaryOffsetData.getvalue() + builtOffsetLookupTable + uint32.pack(len(builtOffsetLookupTable))


def StreamSortedIndexToFile(fileObjectOut, keyValueAndMaybeIndexedOffsetData, totalCount, schema, embedSchema = False):
    keyFooterSchema = schema['keyFooter']
    if 'fixedItemSize' not in keyFooterSchema:
        raise ValueError('keys must have a known size to stream the index')
    startingOffset = 0
    if embedSchema:
        schemaToRepresent = {}
        schemaToRepresent.update(schema)
        if schema['valueTypes']['type'] == 'binary' and 'schema' in schema['valueTypes']:
            schemaToRepresent['valueTypes'] = schema['valueTypes']['schema']
        fileObjectOut.write(RepresentSchemaAsBinary(schemaToRepresent))
        startingOffset = fileObjectOut.tell()
    fileObjectOut.write(uint32.pack(0))
    footerList = []
    path = FsdDataPathObject('[Stream]')
    offset = 0
    lengthOfFileObjectHeader = 4
    indexedOffsetDataForStream = IndexedOffsetData()
    for d in keyValueAndMaybeIndexedOffsetData:
        key, value = d[:2]
        indexedOffsetDataContainedInKeyValueSet = len(d) == 3
        prebuiltIndexedOffsetData = d[2] if indexedOffsetDataContainedInKeyValueSet else IndexedOffsetData()
        currentFilePos = fileObjectOut.tell()
        pathToValues = FsdDataPathObject('[%s]' % key, path)
        b, indexedOffsetData = RepresentAsBinaryWithIndexedOffsetData(value, schema['valueTypes'], pathToValues)
        fileObjectOut.write(b)
        footer = {'key': key,
         'offset': offset}
        if schema.get('buildIndex', False):
            footer['size'] = len(b)
        footerList.append(footer)
        if not prebuiltIndexedOffsetData.isEmpty():
            prebuiltIndexedOffsetData.AddOffset(offset + lengthOfFileObjectHeader)
            indexedOffsetDataForStream.AddNestedIndexedOffsetData(prebuiltIndexedOffsetData)
        if not indexedOffsetData.isEmpty():
            indexedOffsetData.AddOffset(offset + lengthOfFileObjectHeader)
            indexedOffsetDataForStream.AddNestedIndexedOffsetData(indexedOffsetData)
        offset += fileObjectOut.tell() - currentFilePos

    if 'multiIndex' in schema:
        multiIndexAttributes = RepresentIndexedOffsetDataAsBinary(indexedOffsetDataForStream, schema, fileObjectOut.tell() - startingOffset)
        fileObjectOut.write(multiIndexAttributes)
    primaryIndexAsBinary = RepresentAsBinary(footerList, keyFooterSchema, FsdDataPathObject('<Footer>', path))
    fileObjectOut.write(primaryIndexAsBinary)
    fileObjectOut.write(uint32.pack(len(primaryIndexAsBinary)))
    totalFileObjectSize = fileObjectOut.tell() - startingOffset
    fileObjectOut.seek(startingOffset)
    fileObjectOut.write(uint32.pack(totalFileObjectSize - 4))


def ObjectAsBinaryStringWithIndexedOffsetData(o, schema, path):
    representation = cStringIO.StringIO()
    attributesByOffset = [ (off, attr) for attr, off in schema['constantAttributeOffsets'].iteritems() ]
    attributesByOffset.sort()
    indexedOffsetDataForObjectAttributes = IndexedOffsetData()
    for offset, attr in attributesByOffset:
        b, indexedOffsetData = RepresentAsBinaryWithIndexedOffsetData(o[attr], schema['attributes'][attr], FsdDataPathObject('.%s' % attr, parent=path))
        representation.write(b)
        if not indexedOffsetData.isEmpty():
            indexedOffsetData.AddOffset(offset)
            indexedOffsetDataForObjectAttributes.AddNestedIndexedOffsetData(indexedOffsetData)

    if 'size' in schema:
        return (representation.getvalue(), indexedOffsetDataForObjectAttributes)
    variableAndOptionalAttributeOrder = schema['attributesWithVariableOffsets'][:]
    optionalAttributesField = 0
    for i in schema['optionalValueLookups']:
        if i in o:
            optionalAttributesField |= schema['optionalValueLookups'][i]
        else:
            variableAndOptionalAttributeOrder.remove(i)

    offsets = (ctypes.c_uint32 * len(variableAndOptionalAttributeOrder))()
    attributesWithOffsets = cStringIO.StringIO()
    for i, attr in enumerate(variableAndOptionalAttributeOrder):
        offsets[i] = attributesWithOffsets.tell()
        b, indexedOffsetData = RepresentAsBinaryWithIndexedOffsetData(o[attr], schema['attributes'][attr], FsdDataPathObject('.%s' % attr, parent=path))
        attributesWithOffsets.write(b)
        if not indexedOffsetData.isEmpty():
            indexedOffsetData.AddOffset(offsets[i] + representation.tell())
            indexedOffsetDataForObjectAttributes.AddNestedIndexedOffsetData(indexedOffsetData)

    offsetToListData = len(uint32.pack(optionalAttributesField)) + len(ctypes.string_at(ctypes.addressof(offsets), ctypes.sizeof(offsets)))
    indexedOffsetDataForObjectAttributes.AddOffset(offsetToListData)
    representation.write(uint32.pack(optionalAttributesField))
    representation.write(ctypes.string_at(ctypes.addressof(offsets), ctypes.sizeof(offsets)))
    representation.write(attributesWithOffsets.getvalue())
    return (representation.getvalue(), indexedOffsetDataForObjectAttributes)


def BinaryStringAsBinaryStringWithIndexedOffsetData(o, schema, path):
    return (o, IndexedOffsetData())


def UnionAsBinaryStringWithIndexedOffsetData(o, schema, path):
    representation = cStringIO.StringIO()
    for idx, possibleSchemaType in enumerate(schema['optionTypes']):
        if len(validator.Validate(possibleSchemaType, o)) == 0:
            binaryIndex = uint32.pack(idx)
            representation.write(binaryIndex)
            itemRepresentation, indexedOffsetData = RepresentAsBinaryWithIndexedOffsetData(o, possibleSchemaType, FsdDataPathObject('<%s>' % possibleSchemaType['type'], parent=path))
            if not indexedOffsetData.isEmpty():
                indexedOffsetData.AddOffset(len(binaryIndex))
            representation.write(itemRepresentation)
            return (representation.getvalue(), indexedOffsetData)

    raise ValueError('Could not represent %s as any type in union' % str(o))


builtInRepresenters = {'enum': EnumAsBinaryStringWithIndexedOffsetData,
 'bool': BoolAsBinaryStringWithIndexedOffsetData,
 'vector4': Vector4AsBinaryStringWithIndexedOffsetData,
 'vector3': Vector3AsBinaryStringWithIndexedOffsetData,
 'vector2': Vector2AsBinaryStringWithIndexedOffsetData,
 'float': FloatAsBinaryStringWithIndexedOffsetData,
 'int': IntAsBinaryStringWithIndexedOffsetData,
 'typeID': IntAsBinaryStringWithIndexedOffsetData,
 'localizationID': IntAsBinaryStringWithIndexedOffsetData,
 'string': StringAsBinaryStringWithIndexedOffsetData,
 'resPath': StringAsBinaryStringWithIndexedOffsetData,
 'list': ListAsBinaryStringWithIndexedOffsetData,
 'dict': DictAsBinaryStringWithIndexedOffsetData,
 'object': ObjectAsBinaryStringWithIndexedOffsetData,
 'binary': BinaryStringAsBinaryStringWithIndexedOffsetData,
 'union': UnionAsBinaryStringWithIndexedOffsetData,
 'unicode': UnicodeStringAsBinaryStringWithIndexedOffsetData}

def RepresentAsBinaryWithIndexedOffsetData(o, schema, path):
    schemaType = schema.get('type')
    if schemaType in builtInRepresenters:
        data, indexedDictOffsets = builtInRepresenters[schemaType](o, schema, path)
        return (data, indexedDictOffsets)
    raise NotImplementedError("Type '%s' does not have a binary representation implementation" % schemaType)


def RepresentAsBinary(o, schema, path = None):
    if path is None:
        path = FsdDataPathObject('<root>')
    binaryData = RepresentAsBinaryWithIndexedOffsetData(o, schema, path)[0]
    return binaryData


def RepresentSchemaAsBinary(schema):
    binarySchema = cPickle.dumps(schema)
    return uint32.pack(len(binarySchema)) + binarySchema


def RepresentAsBinaryWithEmbeddedSchema(o, schema, path = None):
    return RepresentSchemaAsBinary(schema) + RepresentAsBinary(o, schema, path)
