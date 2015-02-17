#Embedded file name: trinutils\__init__.py
"""Set of utilities for Trinity."""

def ReloadTextures(obj):
    reloadedpaths = set()
    for texresource in obj.Find('trinity.TriTexture2DParameter'):
        if texresource.resource and texresource.resourcePath.lower() not in reloadedpaths:
            texresource.resource.Reload()
            reloadedpaths.add(texresource.resourcePath.lower())
