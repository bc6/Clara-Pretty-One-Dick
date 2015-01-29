#Embedded file name: eve/client/script/ui/shared/maps\hexMap.py
"""
A hexagon representation of a sovreignty map where systems are sorted into 
hexagon shaped buckets/tiles and tiles colored according to the dominant alliance/faction in each tile
"""
import trinity
import math
import localization
from mapcommon import *
import geo2
Y_SCALE = 0.8660254037844386
MAP_HEIGHT = -100.0
TIED_TILE_COLOR = (0.4,
 0.4,
 0.4,
 1.0)
UNCLAIMED_TILE_COLOR = (0.1,
 0.1,
 0.1,
 1.0)

class HexMapController(object):
    """
    Controller for the political influence map in hexagonal form
    
    The controller maintains multiple layouts for different granularities of the map and constructs those
    only once and assigns systems to them with the help of a quadtree.
    
    When laying out the map the process is as follows:
        1. get the relevant systemID => sovID info if needed (for history display)
        2. update the systemInfoMap with correct sov info
        3. get the max.x layout
        4. for each tile in layout with any systems in it
            - find the most common sovID and resolve ties if required
            - get a HexGeom and set its values to the cache values and color of most common sovID
        5. hide the unused geoms (rest of the pool list)
        6. profit
    
    TODO: Support for edge highlighting and blinking need some further refinement and input for GD+UI design
    """

    def __init__(self, rootTransform, solarSystemGenerator):
        self.rootTransform = rootTransform
        self.baseTile = trinity.Load('res:/dx9/model/UI/HexTile.red')
        self.tilePool = []
        self.layoutCache = {}
        self.systemInfoMap = {}
        self.aabb = AABB()
        systems = []
        self.mapHeight = 0.0
        for systemID, system in solarSystemGenerator:
            scaledSystemPos = system.scaledCenter
            factionID = system.factionID
            systemInfo = HexSystemInfo(systemID, factionID, scaledSystemPos[0], scaledSystemPos[2])
            self.systemInfoMap[systemID] = systemInfo
            systems.append(systemInfo)
            self.aabb.IncludePoint(systemInfo.point)
            self.mapHeight = max(self.mapHeight, scaledSystemPos[1])

        self.systemQuadTree = QuadTree(systems, depth=6, aabb=self.aabb)
        self.centerPoint = self.systemQuadTree.center
        self.mapHeight *= 1.1
        self.legend = []
        self.CalculateHexagonParameters()
        self.nextTileNum = 0
        self.firstUnusedTileNum = None
        self.SetupScene()

    def __del__(self):
        self.highlightBinding = None
        del self.rootTransform.curveSets[:]
        self.rootTransform = None

    def SetupScene(self):
        curveSet = trinity.TriCurveSet()
        curveSet.name = 'HighlighCurveSet'
        curveSet.playOnLoad = False
        curveSet.Stop()
        curveSet.scaledTime = 0.0
        self.rootTransform.curveSets.append(curveSet)
        curve = trinity.TriScalarCurve()
        curve.value = 0.0
        curve.extrapolation = trinity.TRIEXT_CYCLE
        curveSet.curves.append(curve)
        curve.AddKey(0.0, 0.0, 0.0, 0.0, trinity.TRIINT_HERMITE)
        curve.AddKey(1.0, 1.0, 0.0, 0.0, trinity.TRIINT_HERMITE)
        curve.AddKey(2.0, 0.0, 0.0, 0.0, trinity.TRIINT_HERMITE)
        curve.Sort()
        self.highlightCurveSet = curveSet
        self.highlightCurve = curve
        curveSet.Play()

    def CalculateHexagonParameters(self):
        """
        Calculate the base bounding box for a tile along with each of the 6 vertices
        for intersection testing
        """
        mmin = trinity.TriVector(-1.0, 0.0, -0.866025447845459)
        mmax = trinity.TriVector(1.0, 0.0, 0.866025447845459)
        maxx = mmax.z / math.sin(math.radians(60.0))
        topRightX = math.cos(math.radians(60.0)) * maxx
        self.tileMin = Point(-maxx, mmin.z)
        self.tileMax = Point(maxx, mmax.z)
        self.hexPoints = (Point(topRightX, self.tileMax.y),
         Point(self.tileMax.x, 0.0),
         Point(topRightX, self.tileMin.y),
         Point(-topRightX, self.tileMin.y),
         Point(self.tileMin.x, 0.0),
         Point(-topRightX, self.tileMax.y))
        self.tileWidth = maxx * 2.0 * 0.75
        self.tileHeight = mmax.z * 2.0

    def GetNextGeom(self):
        if len(self.tilePool) > self.nextTileNum:
            nextTile = self.tilePool[self.nextTileNum]
        else:
            nextTile = HexGeom(self)
            self.tilePool.append(nextTile)
        self.nextTileNum += 1
        return nextTile

    def GetAdaptedTileAABB(self, tile):
        """return a transformed bounding box for a tile"""
        v = Point(tile.center[0], tile.center[2])
        return AABB(self.tileMin * tile.scale + v, self.tileMax * tile.scale + v)

    def GetAdaptedHexPoints(self, tile):
        """Return the hexagon vertices scaled and shifted to the 2d position tuple provided"""
        newPoints = []
        pos = Point(tile.center[0], tile.center[2])
        for point in self.hexPoints:
            newPoint = point * tile.scale + pos
            newPoints.append(newPoint)

        return newPoints

    def AssignSystemsToTile(self, tile):
        """
        Assign all systems overlaped by the tile to the tile
        """
        aabb = self.GetAdaptedTileAABB(tile)
        systemInfos = self.systemQuadTree.Hit(aabb)
        if len(systemInfos) > 0:
            hexVertices = self.GetAdaptedHexPoints(tile)
            for info in systemInfos:
                if self.PointWithinTile(info.point, hexVertices):
                    tile.systems[info.systemID] = info

    def PointWithinTile(self, point, vertices):
        """
        Test all the if point is on the "inside" of all the edges
        """
        numPoint = len(vertices)
        for i in xrange(numPoint):
            p0 = vertices[i]
            p1 = vertices[(i + 1) % numPoint]
            test = (point.y - p0.y) * (p1.x - p0.x) - (point.x - p0.x) * (p1.y - p0.y)
            if test > 0:
                return False

        return True

    def GetLayout(self, sizeX):
        """
        Generate a hex layout for size
        """
        if sizeX not in self.layoutCache:
            layout = []
            startX, startY = self.aabb.min.x, self.aabb.min.y
            sizeY = int(math.ceil(sizeX * Y_SCALE))
            scale = self.aabb.Width() / (sizeX - 1) / self.tileWidth
            sizeY = int(math.ceil(self.aabb.Height() / (self.tileHeight * scale))) + 1
            height = self.tileHeight * scale
            width = self.tileWidth * scale
            offset = -height * 0.5
            for y in xrange(sizeY):
                for x in xrange(sizeX):
                    tile = HexTile()
                    tile.scale = scale
                    shift = 0.0 if x % 2 == 0 else offset
                    tile.center = (startX + x * width, 0.0, startY + y * height + shift)
                    self.AssignSystemsToTile(tile)
                    layout.append(tile)

            self.layoutCache[sizeX] = layout
        return self.layoutCache[sizeX]

    def LayoutTiles(self, size, sovereigntyInfo, changeList, colorByStandings = False):
        """
        take a list of sov mappings from system to sovID and a map grid size
        and set the map
        """
        changedSystems = set([ info.solarSystemID for info in changeList ])
        for info in self.systemInfoMap.itervalues():
            if info.systemID in sovereigntyInfo:
                info.sovID = sovereigntyInfo[info.systemID]
            info.changed = info.systemID in changedSystems

        layout = self.GetLayout(size)
        self.nextTileNum = 0
        for i, tile in enumerate(layout):
            if tile.IsEmpty():
                continue
            tile.Update(colorByStandings)
            hex = self.GetNextGeom()
            hex.SetTile(tile)
            hex.index = i

        if self.firstUnusedTileNum is not None and self.firstUnusedTileNum > self.nextTileNum:
            for i in xrange(self.nextTileNum, self.firstUnusedTileNum):
                self.tilePool[i].Show(False)

        self.firstUnusedTileNum = self.nextTileNum
        self.currentLayout = layout
        self.currentSize = size
        if colorByStandings:
            self.legend = [LegendItem(0, localization.GetByLabel('UI/PeopleAndPlaces/GoodStanding'), trinity.TriColor(*COLOR_STANDINGS_GOOD), data=None), LegendItem(1, localization.GetByLabel('UI/PeopleAndPlaces/StandingNeutral'), trinity.TriColor(*COLOR_STANDINGS_NEUTRAL), data=None), LegendItem(2, localization.GetByLabel('UI/PeopleAndPlaces/BadStanding'), trinity.TriColor(*COLOR_STANDINGS_BAD), data=None)]
        else:
            legend = [ (tile.sovID, tile.color) for tile in self.currentLayout if tile.sovID is not None ]
            self.legend = [LegendItem(0, localization.GetByLabel('UI/Inflight/Brackets/SystemUnclaimed'), trinity.TriColor(*UNCLAIMED_TILE_COLOR), data=None), LegendItem(1, localization.GetByLabel('UI/Inflight/Brackets/SystemContested'), trinity.TriColor(*TIED_TILE_COLOR), data=None)]
            factions = []
            for sovID, color in set(legend):
                name = cfg.eveowners.Get(sovID).name
                factions.append(LegendItem(2, name, trinity.TriColor(*color), data=sovID))

            self.legend += factions
        self.highlightCurveSet.Play()

    def Enable(self, enable = True):
        self.rootTransform.display = enable

    def HighlightTiles(self, dataList, colorList):
        colors = [ (color.r,
         color.g,
         color.b,
         1.0) for color in colorList ]
        for geom in self.tilePool:
            geom.Highlight(False)
            if self.currentLayout[geom.index].sovID in dataList:
                geom.Highlight(True)
                continue
            c2 = self.currentLayout[geom.index].color
            for c1 in colors:
                if abs(c1[0] - c2[0]) < 0.01 and abs(c1[1] - c2[1]) < 0.01 and abs(c1[2] - c2[2]) < 0.01:
                    geom.Highlight(True)
                    break

    def EnableOutlines(self, enable):
        numTiles = len(self.currentLayout)
        for geom in self.tilePool:
            if not geom.tile.display:
                break
            if not enable:
                geom.SetOutlines(0)
                continue
            info = self.currentLayout[geom.index]
            if info.sovID is None:
                geom.SetOutlines(0)
            else:
                if geom.index % 2 == 0:
                    neighbors = [(32, geom.index + self.currentSize + 1),
                     (16, geom.index + self.currentSize),
                     (8, geom.index + self.currentSize - 1),
                     (4, geom.index - 1),
                     (2, geom.index - self.currentSize),
                     (1, geom.index + 1)]
                else:
                    neighbors = [(32, geom.index + 1),
                     (16, geom.index + self.currentSize),
                     (8, geom.index - 1),
                     (4, geom.index - self.currentSize - 1),
                     (2, geom.index - self.currentSize),
                     (1, geom.index - self.currentSize + 1)]
                tileIndex = 0
                for bit, index in neighbors:
                    if 0 <= index < numTiles:
                        neighborTile = self.currentLayout[index]
                        if neighborTile.color == info.color:
                            continue
                    tileIndex += bit

                geom.SetOutlines(tileIndex)


class HexSystemInfo(object):
    """
    Hold info about a solarsystem to be keep in a dict by systemID as well as in a quad tree
    for quick collision test with tiles.  Pretends to be an AABB with min and max points.
    """

    def __init__(self, systemID, sovID, x, y):
        self.systemID = systemID
        self.sovID = sovID
        self.point = Point(x, y)
        self.changed = False

    def GetPoint(self):
        return self.point

    min = property(GetPoint)
    max = property(GetPoint)


class HexGeom(object):
    """
    Graphical representation of a hexagon tile.
    These tiles get reused on different map scales.
    """

    def __init__(self, controller):
        self.controller = controller
        self.tile = controller.baseTile.CopyTo()
        parameters = self.tile.mesh.additiveAreas[0].effect.parameters
        self.color = [ p for p in parameters if p.name == 'DiffuseColor' ][0]
        self.highlight = [ p for p in parameters if p.name == 'Highlight' ][0]
        self.tileIndex = [ p for p in parameters if p.name == 'TileIndex' ][0]
        self.index = None
        controller.rootTransform.children.append(self.tile)
        self.highlightBinding = None

    def SetTile(self, tile):
        """Show or hide the entire tile"""
        self.Show()
        self.SetColor(tile.color)
        self.tile.translation = tile.center
        self.tile.scaling = (tile.scale, tile.scale, tile.scale)
        self.Flash(tile.changed)

    def Show(self, enable = True):
        """Show or hide the entire tile"""
        self.tile.display = enable

    def Highlight(self, enable = True):
        """Show or hide the entire tile"""
        if enable:
            self.highlight.value = 1.0
        else:
            self.highlight.value = 0.0

    def Flash(self, enable = True):
        """TODO: assign a scale curve to do color blinky fun"""
        if enable and self.highlightBinding is None:
            binding = trinity.TriValueBinding()
            binding.sourceAttribute = 'value'
            binding.destinationAttribute = 'value'
            binding.scale = 1.0
            binding.sourceObject = self.controller.highlightCurve
            binding.destinationObject = self.highlight
            self.highlightBinding = binding
        if enable:
            if self.highlightBinding not in self.controller.highlightCurveSet.bindings:
                self.controller.highlightCurveSet.bindings.append(self.highlightBinding)
        else:
            if self.highlightBinding in self.controller.highlightCurveSet.bindings:
                self.controller.highlightCurveSet.bindings.remove(self.highlightBinding)
            self.highlight.value = 0.0

    def SetOutlines(self, index):
        """set the tile index to get fancy outlines"""
        self.tileIndex.value = index

    def SetColor(self, color):
        """assign a rgba color value to tile fill and glow"""
        self.color.value = color


class HexTile(object):
    """
    A logical hexagon instance keeping track of sovereighnty ID and systems mapped min.y it.
    These units don't get resused when changing scale rather they serve as a script for
    reconfiguring the HexGeoms.
    """

    def __init__(self):
        self.center = None
        self.color = None
        self.sovID = None
        self.systems = {}
        self.changed = False

    def IsEmpty(self):
        """True if tile contains no systems"""
        return len(self.systems) == 0

    def Update(self, colorByStandings = False):
        """
        Update the dominant faction/alliance ID and get the color.
        This expects the controller to allready have updated all relevant sovIDs for systems
        sovID and color updated
        Checks if any systems is marked as changed and marks the tile accordingly
        """
        alliances = {}
        self.changed = False
        starmap = sm.GetService('starmap')
        for info in self.systems.itervalues():
            if info.changed:
                self.changed = True
            if info.sovID is None:
                continue
            if info.sovID not in alliances:
                alliances[info.sovID] = 0
            alliances[info.sovID] += 1

        histogram = [ (count, sovID) for sovID, count in alliances.iteritems() if sovID is not None ]
        histogram.sort()
        if len(histogram) == 0:
            self.sovID = None
            self.color = UNCLAIMED_TILE_COLOR
        elif len(histogram) == 1 or histogram[-1][0] != histogram[-2][0]:
            self.sovID = histogram[-1][1]
            if colorByStandings:
                c = starmap.GetColorByStandings(self.sovID)
                color = (c[0],
                 c[1],
                 c[2],
                 1.0)
            else:
                c = starmap.GetFactionOrAllianceColor(self.sovID)
                color = (c.r,
                 c.g,
                 c.b,
                 1.0)
            self.color = color
        elif histogram[-1][0] == histogram[-2][0]:
            self.sovID == None
            self.color = TIED_TILE_COLOR
        else:
            self.sovID == None
            self.color = UNCLAIMED_TILE_COLOR

    def __repr__(self):
        return 'HexTile(sov=%s center=%s color=%s systems=%s)' % (str(self.sovID),
         str(self.center),
         str(self.color),
         str([ i for i in self.systems ]))


class AABB(object):
    """Simple axis-aligned bounding box for collision testing in a QuadTree"""

    def __init__(self, minPoint = None, maxPoint = None):
        if minPoint is None:
            self.min = Point()
        else:
            self.min = minPoint
        if maxPoint is None:
            self.max = Point()
        else:
            self.max = maxPoint

    def Width(self):
        return self.max.x - self.min.x

    def Height(self):
        return self.max.y - self.min.y

    def IncludePoint(self, point):
        """Grows the aabb to include the point if required"""
        self.min.x = min(self.min.x, point.x)
        self.min.y = min(self.min.y, point.y)
        self.max.x = max(self.max.x, point.x)
        self.max.y = max(self.max.y, point.y)

    def Center(self):
        return (self.min + self.max) * 0.5

    def __repr__(self):
        return '(%f, %f, %f, %f)' % (self.min.x,
         self.min.y,
         self.max.x,
         self.max.y)


class Point(object):
    """A 2D simple point structure"""

    def __init__(self, x = 0, y = 0):
        self.x = x
        self.y = y

    def __mul__(self, scalar):
        return Point(self.x * scalar, self.y * scalar)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def __repr__(self):
        return '(%f, %f)' % (self.x, self.y)


class QuadTree(object):
    """An implementation of a quad-tree.
    
    This QuadTree started life as a version of [1] but found a life of its own
    when I realised it wasn't doing what I needed. It is intended for static
    geometry, ie, items such as the landscape that don't move.
    
    This implementation inserts items at the current level if they overlap all
    4 sub-quadrants, otherwise it inserts them recursively into the one or two
    sub-quadrants that they overlap.
    
    Items being stored in the tree must possess the following attributes:
    
        min.x - the x coordinate of the min.x edge of the item's bounding box.
        min.y - the y coordinate of the min.y edge of the item's bounding box.
        max.x - the x coordinate of the max.x edge of the item's bounding box.
        max.y - the y coordinate of the max.y edge of the item's bounding box.
    
        where min.x < max.x and min.y < max.y
        
    ...and they must be hashable.
    
    Acknowledgements:
    [1] http://mu.arete.cc/pcr/syntax/quadtree/1/quadtree.py
    """

    def __init__(self, items, depth = 8, aabb = None):
        """Creates a quad-tree.
        
        items:
            A sequence of items to store in the quad-tree. Note that these
            items must possess min.x, min.y, max.x and max.y attributes.
        
        depth:
            The maximum recursion depth.
        
        aabb:
            The bounding rectangle of all of the items in the quad-tree. For
            internal use only.
        """
        self.nw = self.ne = self.se = self.sw = None
        depth -= 1
        if depth == 0:
            self.items = items
            return
        if aabb is None:
            aabb = AABB()
            aabb.min.x = min((item.min.x for item in items))
            aabb.min.y = min((item.min.y for item in items))
            aabb.max.x = max((item.max.x for item in items))
            aabb.max.y = max((item.max.y for item in items))
        self.center = center = aabb.Center()
        self.items = []
        nw_items = []
        ne_items = []
        se_items = []
        sw_items = []
        for item in items:
            in_nw = item.min.x <= center.x and item.min.y <= center.y
            in_sw = item.min.x <= center.x and item.max.y >= center.y
            in_ne = item.max.x >= center.x and item.min.y <= center.y
            in_se = item.max.x >= center.x and item.max.y >= center.y
            if in_nw and in_ne and in_se and in_sw:
                self.items.append(item)
            else:
                if in_nw:
                    nw_items.append(item)
                if in_ne:
                    ne_items.append(item)
                if in_se:
                    se_items.append(item)
                if in_sw:
                    sw_items.append(item)

        if nw_items:
            self.nw = QuadTree(nw_items, depth, AABB(Point(aabb.min.x, aabb.min.y), Point(center.x, center.y)))
        if ne_items:
            self.ne = QuadTree(ne_items, depth, AABB(Point(center.x, aabb.min.y), Point(aabb.max.x, center.y)))
        if se_items:
            self.se = QuadTree(se_items, depth, AABB(Point(center.x, center.y), Point(aabb.max.x, aabb.max.y)))
        if sw_items:
            self.sw = QuadTree(sw_items, depth, AABB(Point(aabb.min.x, center.y), Point(center.x, aabb.max.y)))

    def Overlaps(self, rect, item):
        """does item rectangle intersect with node rectangle"""
        return rect.max.x >= item.min.x and rect.min.x <= item.max.x and rect.max.y >= item.min.y and rect.min.y <= item.max.y

    def Hit(self, rect):
        """
        Returns the items that overlap a bounding rectangle.
        
        Returns the set of all items in the quad-tree that overlap with a
        bounding rectangle.
        
        rect:
            The bounding rectangle being tested against the quad-tree. This
            must possess min and max Point attributes.
        """
        hits = set((item for item in self.items if self.Overlaps(rect, item)))
        if self.nw and rect.min.x <= self.center.x and rect.min.y <= self.center.y:
            hits |= self.nw.Hit(rect)
        if self.sw and rect.min.x <= self.center.x and rect.max.y >= self.center.y:
            hits |= self.sw.Hit(rect)
        if self.ne and rect.max.x >= self.center.x and rect.min.y <= self.center.y:
            hits |= self.ne.Hit(rect)
        if self.se and rect.max.x >= self.center.x and rect.max.y >= self.center.y:
            hits |= self.se.Hit(rect)
        return hits
