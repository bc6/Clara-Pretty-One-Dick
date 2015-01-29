#Embedded file name: eve/client/script/environment\nodemanager.py


def FindNodes(source, name, typename):
    nodes = []
    if source.__typename__ == 'List':
        thingsToSearch = source
    else:
        thingsToSearch = [source]
    for item in thingsToSearch:
        tr = item.Find(typename)
        matches = [ t for t in tr if t.name.startswith(name) ]
        nodes.extend(matches)

    return nodes


def FindNode(source, name, typename):
    tr = source.Find(typename)
    for t in tr:
        if t.name.startswith(name):
            return t
