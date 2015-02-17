#Embedded file name: F:\depot\streams\olafurth_olafurth-pc_STABLE_2754\fsdSchemas\loaders\__init__.py
import ctypes
import fsdSchemas.schemaOptimizer as schemaOptimizer
import fsdSchemas.predefinedStructTypes as structTypes
import struct

def readIntFromBinaryStringAtOffset(binaryString, offsetToValue):
    return structTypes.uint32.unpack_from(binaryString, offsetToValue)[0]


def readIntFromFileAtOffset(fileObject, offsetToValue):
    fileObject.seek(offsetToValue)
    return structTypes.uint32.unpack_from(fileObject.read(4), 0)[0]


def readBinaryDataFromFileAtOffset(fileObject, offsetToData, sizeOfData):
    fileObject.seek(offsetToData)
    return fileObject.read(sizeOfData)


class VectorLoader(object):

    def __init__(self, data, offset, schema, path, extraState):
        self.schema = schema
        single_precision = schema.get('precision', 'single') == 'single'
        schemaType = schema['type']
        if schemaType == 'vector4':
            if single_precision:
                t = structTypes.vector4_float
            else:
                t = structTypes.vector4_double
        elif schemaType == 'vector3':
            if single_precision:
                t = structTypes.vector3_float
            else:
                t = structTypes.vector3_double
        elif single_precision:
            t = structTypes.vector2_float
        else:
            t = structTypes.vector2_double
        self.data = t.unpack_from(data, offset)

    def __getitem__(self, key):
        if 'aliases' in self.schema and key in self.schema['aliases']:
            return self.data[self.schema['aliases'][key]]
        return self.data[key]

    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except (IndexError, KeyError) as e:
            raise AttributeError(str(e))


def Vector4FromBinaryString(data, offset, schema, path, extraState):
    if 'aliases' in schema:
        return VectorLoader(data, offset, schema, path, extraState)
    elif schema.get('precision', 'single') == 'double':
        return structTypes.vector4_double.unpack_from(data, offset)
    else:
        return structTypes.vector4_float.unpack_from(data, offset)


def Vector3FromBinaryString(data, offset, schema, path, extraState):
    if 'aliases' in schema:
        return VectorLoader(data, offset, schema, path, extraState)
    elif schema.get('precision', 'single') == 'double':
        return structTypes.vector3_double.unpack_from(data, offset)
    else:
        return structTypes.vector3_float.unpack_from(data, offset)


def Vector2FromBinaryString(data, offset, schema, path, extraState):
    if 'aliases' in schema:
        return VectorLoader(data, offset, schema, path, extraState)
    elif schema.get('precision', 'single') == 'double':
        return structTypes.vector2_double.unpack_from(data, offset)
    else:
        return structTypes.vector2_float.unpack_from(data, offset)


def StringFromBinaryString(data, offset, schema, path, extraState):
    count = structTypes.uint32.unpack_from(data, offset)[0]
    return struct.unpack_from(str(count) + 's', data, offset + 4)[0]


def UnicodeStringFromBinaryString(data, offset, schema, path, extraState):
    nonUnicodeString = StringFromBinaryString(data, offset, schema, path, extraState)
    return nonUnicodeString.decode('utf-8')


def EnumFromBinaryString(data, offset, schema, path, extraState):
    enumType = schemaOptimizer.GetLargeEnoughUnsignedTypeForMaxValue(schema['maxEnumValue'])
    dataValue = ctypes.cast(ctypes.byref(data, offset), ctypes.POINTER(enumType)).contents.value
    if schema.get('readEnumValue', False):
        return dataValue
    for k, v in schema['values'].iteritems():
        if v == dataValue:
            return k


def BoolFromBinaryString(data, offset, schema, path, extraState):
    return structTypes.byte.unpack(data[offset])[0] == 255


def IntFromBinaryString(data, offset, schema, path, extraState):
    if 'min' in schema and schema['min'] >= 0 or 'exclusiveMin' in schema and schema['exclusiveMin'] >= -1:
        return structTypes.uint32.unpack_from(data, offset)[0]
    else:
        return structTypes.int32.unpack_from(data, offset)[0]


def FloatFromBinaryString(data, offset, schema, path, extraState):
    if schema.get('precision', 'single') == 'double':
        return structTypes.cdouble.unpack_from(data, offset)[0]
    else:
        return structTypes.cfloat.unpack_from(data, offset)[0]


def UnionFromBinaryString(data, offset, schema, path, extraState):
    typeIndex = structTypes.uint32.unpack_from(data, offset)[0]
    return extraState.RepresentSchemaNode(data, offset + 4, path, schema['optionTypes'][typeIndex])
