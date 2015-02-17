#Embedded file name: fsdlite\indexer.py
import re

def index(obj, indexes):
    indexed = {}
    if indexes:
        results = from_primitives(obj, compile_indexes(indexes))
        for key, value in results:
            indexed.setdefault(key, set()).add(value)

    return indexed


def from_primitives(data, indexes, path = None):
    results = match_indexes(indexes, path)
    if isinstance(data, dict):
        for key, value in data.iteritems():
            results += from_primitives(value, indexes, path + '.' + str(key) if path else str(key))

    elif isinstance(data, list):
        for key, value in enumerate(data):
            results += from_primitives(value, indexes, path)

    else:
        results += match_indexes(indexes, path + '.' + str(data) if path else str(data))
    return results


def match_indexes(indexes, path):
    results = []
    for pattern in indexes:
        match = pattern.match(path or '')
        if match:
            for key, value in match.groupdict().iteritems():
                results.append((key, value))

    return results


def compile_indexes(indexes):
    return [ re.compile(r) for r in indexes or [] ]
