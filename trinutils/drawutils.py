#Embedded file name: trinutils\drawutils.py
try:
    import trinity
except ImportError:
    trinity = None

LINESET_FXPATH = 'res:/Graphics/Effect/Managed/Space/SpecialFX/Lines.fx'
WHITE = (1, 1, 1, 1)
RED = (1, 0, 0, 1)

def GetMarkerCoordinates(scale):
    """Returns a list of xyz triples for a given marker size."""
    return [(scale, 0.0, 0.0),
     (-scale, 0.0, 0.0),
     (0.0, scale, 0.0),
     (0.0, -scale, 0.0),
     (0.0, 0.0, scale),
     (0.0, 0.0, -scale),
     (scale, scale, 0.0),
     (-scale, scale, 0.0),
     (scale, -scale, 0.0),
     (-scale, -scale, 0.0),
     (0.0, scale, scale),
     (0.0, -scale, scale),
     (0.0, scale, -scale),
     (0.0, -scale, -scale),
     (scale, 0.0, scale),
     (scale, 0.0, -scale),
     (-scale, 0.0, scale),
     (-scale, 0.0, -scale)]


def CreateLineSet(name = None):
    """Creates and returns an `EveLineSet` with the standard lineset effect.
    """
    lineset = trinity.EveLineSet()
    if name is not None:
        lineset.name = name
    lineset.effect = trinity.Tr2Effect()
    lineset.effect.effectFilePath = LINESET_FXPATH
    return lineset


def CreateMarker(lineset, markerCoordinates, position, color = RED):
    """Creates a marker at `position` on the given `lineset` with the given
    `color` and `markerCoordinates` (see `GetMarkerCoordinates`).
    """
    for entry in markerCoordinates:
        offsetLocation = (position[0] + entry[0], position[1] + entry[1], position[2] + entry[2])
        lineset.AddLine(position, color, offsetLocation, color)

    lineset.SubmitChanges()
