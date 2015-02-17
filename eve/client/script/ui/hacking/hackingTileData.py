#Embedded file name: eve/client/script/ui/hacking\hackingTileData.py
import hackingUIConst

class TileData(object):
    """ Data object for a hacking game tile """
    __guid__ = 'hackingui.TileData'

    def __init__(self, id = None, type = None, subtype = None, coord = None, blocked = False, hidden = False, strength = 0, coherence = 0):
        self.id = id
        self.type = type
        self.subtype = subtype
        self.coord = coord
        self.blocked = blocked
        self.hidden = hidden
        self.strength = strength
        self.coherence = coherence
        self.distanceIndicator = 0
        self.neighbourTiles = []

    def Update(self, **kw):
        for key, value in kw.iteritems():
            setattr(self, key, value)

    def GetHexXY(self):
        hexX, hexY = self.coord
        if hexY % 2:
            hexX += 0.5
        return (hexX, hexY)

    def GetXY(self):
        """ Returns x and y position for this tile, calculated from hex coordinates """
        hexX, hexY = self.GetHexXY()
        x = hexX * hackingUIConst.GRID_X
        y = hexY * hackingUIConst.GRID_Y
        return (x, y)

    def SetNeighbours(self, neighbourTiles):
        self.neighbourTiles = neighbourTiles

    def GetNeighbours(self):
        return self.neighbourTiles

    def IsFlippable(self):
        """ Can this tile be flipped, given the current state of the board ? """
        for neighbour in self.neighbourTiles:
            if not neighbour.hidden and not neighbour.blocked:
                return True

        return False

    def __repr__(self):
        return 'id=%s, type=%s, subtype=%s, coord=%s, blocked=%s, hidden=%s, strength=%s, coherence=%s' % (self.id,
         self.type,
         self.subtype,
         self.coord,
         self.blocked,
         self.hidden,
         self.strength,
         self.coherence,
         self.distanceIndicator)
