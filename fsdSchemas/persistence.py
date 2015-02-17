#Embedded file name: F:\depot\streams\olafurth_olafurth-pc_STABLE_2754\fsdSchemas\persistence.py
import yaml
import collections
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fsdCommon.pathSpecifiers import PathConditional

def orderedDict_constructor(loader, node):
    value = collections.OrderedDict()
    for k, v in node.value:
        value[loader.construct_object(k)] = loader.construct_object(v)

    return value


class SafeSchemaLoader(yaml.SafeLoader):
    pass


SafeSchemaLoader.add_constructor(u'tag:yaml.org,2002:map', orderedDict_constructor)

def LoadSchema(fileStream):
    return yaml.load(fileStream, Loader=SafeSchemaLoader)


def GetEditorSchema(schema):
    if 'editorFileSchema' in schema:
        editorSchema = schema['editorFileSchema']
        return schema['schemas'][editorSchema]


def GetUnOptimizedRuntimeSchema(schema):
    if 'runtimeSchema' in schema:
        runtimeSchema = schema['runtimeSchema']
        return schema['schemas'][runtimeSchema]


def GetSchemaByFilePath(schema, filePath):
    if 'validationPaths' in schema:
        for pathSpecifier, sKey in schema['validationPaths'].iteritems():
            if PathConditional(pathSpecifier).Matches(filePath):
                return schema['schemas'][sKey]


def GetNewIDForSchemaObject(schemaNode):
    return None
