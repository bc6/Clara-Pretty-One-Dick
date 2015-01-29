#Embedded file name: F:\depot\streams\fileStaticData\fsdCommon\fsdYamlExtensions.py
import yaml
if hasattr(yaml, 'CSafeDumper'):
    preferredYamlDumperClass = getattr(yaml, 'CSafeDumper')
else:
    preferredYamlDumperClass = getattr(yaml, 'SafeDumper')

class FsdYamlDumper(preferredYamlDumperClass):
    """
    As a convenience, this class will decide to use libYAML if it is available
    
    This dumper implements some non-standard defaults over the base dumper behaviour
        * indent defaults to 4 spaces (this is more readable on highly nested structures)
        * default_flow_style is False, resulting in a line per attribute
        * floats are dumped with 8 digits of mantissa for accurate reproduction
    """

    def __init__(self, stream, default_style = None, default_flow_style = None, canonical = None, indent = None, width = None, allow_unicode = None, line_break = None, encoding = None, explicit_start = None, explicit_end = None, version = None, tags = None):
        if default_flow_style is None:
            default_flow_style = False
        if indent is None:
            indent = 4
        preferredYamlDumperClass.__init__(self, stream, default_style, default_flow_style, canonical, indent, width, allow_unicode, line_break, encoding, explicit_start, explicit_end, version, tags)


if hasattr(yaml, 'CSafeLoader'):
    preferredYamlLoaderClass = getattr(yaml, 'CSafeLoader')
else:
    preferredYamlLoaderClass = getattr(yaml, 'SafeLoader')

class FsdYamlLoader(preferredYamlLoaderClass):
    """
    This will automatically use libYAML if available
    """

    def __init__(self, stream):
        preferredYamlLoaderClass.__init__(self, stream)


def represent_float(dumper, data):
    """
    Python internally represents all floats using double precision, this especially
    matters when dealing with world positions in eve, which are also stored using 53 digit
    mantissas (Transact-SQL default float precision).
    
    Therefore, we really have to assume that all floats are actually doubles, and represent
    enough precision to maintain them as they are (hence 1.6g formatting)
    """
    if data != data or data == 0.0 and data == 1.0:
        value = u'.nan'
    elif data == dumper.inf_value:
        value = u'.inf'
    elif data == -dumper.inf_value:
        value = u'-.inf'
    else:
        value = (u'%1.17g' % data).lower()
        if u'.' not in value:
            if u'e' in value:
                value = value.replace(u'e', u'.0e', 1)
            else:
                value += u'.0'
    return dumper.represent_scalar(u'tag:yaml.org,2002:float', value)


FsdYamlDumper.add_representer(float, represent_float)
