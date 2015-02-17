#Embedded file name: eve/client/script/ui/shared/maps\map2D.py
import sys
import uicontrols
import uiprimitives
import uix
import uiutil
import mathUtil
import blue
import carbon.client.script.util.lg as lg
import trinity
import base
import uthread
import util
import math
from math import pi
import uicls
import carbonui.const as uiconst
import localization
import geo2
import carbon.common.script.util.mathUtil as mathUtil
from pychartdir import setLicenseCode, DrawArea
setLicenseCode('DIST-0000-05de-f7ec-ffbeURDT-232Q-M544-C2XM-BD6E-C452')
DRAW_REGIONS = 1
DRAW_CONSTELLATIONS = 2
DRAW_SOLARSYSTEMS = 3
DRAW_SOLARSYSTEM_INTERIOR = 4
FLIPMAP = -1

class Map2D(uiprimitives.Container):
    __guid__ = 'xtriui.Map2D'
    __nonpersistvars__ = []
    __notifyevents__ = ['OnDestinationSet']
    tooltipPositionRect = None

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.sr.sizefactor = None
        self.sr.sizefactorsize = None
        self.sr.marks = None
        self.Reset()
        self.overlays = uiprimitives.Container(name='overlays', parent=self, clipChildren=1, pos=(0, 0, 0, 0))
        self.sr.areas = uiprimitives.Container(name='areas', parent=self, clipChildren=1, pos=(0, 0, 0, 0))
        self.hilite = uiprimitives.Sprite(parent=self.overlays, pos=(0, 0, 16, 16), color=(1.0, 1.0, 1.0, 0.4), name='hilite', state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/Shared/circleThin16.png', align=uiconst.RELATIVE)
        self.imhere = uiprimitives.Container(name='imhere', parent=self.overlays, state=uiconst.UI_HIDDEN, align=uiconst.TOPLEFT, width=16, height=16)
        circle = uiprimitives.Sprite(parent=self.imhere, idx=0, pos=(0, 0, 16, 16), color=(1.0, 0.0, 0.0, 1.0), name='imhere_sprite', texturePath='res:/UI/Texture/Shared/circleThin16.png', align=uiconst.RELATIVE)
        self.destination = uiprimitives.Sprite(parent=self.overlays, pos=(0, 0, 16, 16), color=(1.0, 1.0, 0.0, 1.0), state=uiconst.UI_HIDDEN, name='destination', texturePath='res:/UI/Texture/Shared/circleThin16.png', align=uiconst.RELATIVE)
        self.sprite = uicontrols.Icon(name='mapsprite', parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 0.0))
        self.bgSprite = None
        self.dragging = 0
        self.ditherIn = 1
        self.dragAllowed = 0
        self.dataLayer = None
        self.dataToggle = 0
        self.dataArgs = {}
        self.dataLoaded = None
        self.needsize = None
        self.allowAbstract = 1
        self.fillSize = 0.8
        self.mouseHoverGroups = []
        self.cordsAsPortion = {}
        self.fov = None
        self.tempAngleFov = None

    def SetInfoMode(self):
        self.updatemylocationtimer = None
        uiutil.FlushList(self.imhere.children[1:])
        for each in self.children:
            if each.name == 'frame':
                each.Close()

    def MarkAreas(self, areas = []):
        uthread.pool('Map2D::_MarkAreas', self._MarkAreas, areas)

    def _MarkAreas(self, areas):
        size = self.absoluteRight - self.absoluteLeft
        uix.Flush(self.sr.areas)
        for area in areas:
            id, hint, (absX, absY, absZ), radius, color = area
            maxdist = self.GetMaxDist()
            sizefactor = size / 2 / maxdist * self.fillSize
            x = FLIPMAP * absX * sizefactor / float(size) + 0.5
            y = absZ * sizefactor / float(size) + 0.5
            rad = radius * sizefactor / float(size)
            mark = uiprimitives.Sprite(parent=self.sr.areas, name='area', left=int(int(x * size) - mark.width / 2), top=int(int(y * size) - mark.height / 2 + 1), width=int(rad * size * 2), height=int(rad * size * 2), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/circle_full.png', color=(1.0, 0.2, 0.2, 1.0))
            mark.sr.x = x
            mark.sr.y = y
            mark.sr.rad = rad

    def SetMarks(self, marks = []):
        uthread.pool('Map2D::SetMarks', self._SetMarks, marks)

    def _SetMarks(self, marks):
        if not uiutil.IsUnder(self, uicore.desktop):
            return
        for i in xrange(0, len(marks), 4):
            id = marks[i]
            hint = marks[i + 1]
            size = max(1, self.absoluteRight - self.absoluteLeft)
            x, y = self.GetCordsByKeyAsPortion(id, size)
            if x is None or y is None:
                return
            if self.sr.marks is None:
                self.sr.marks = uiprimitives.Container(name='marks', parent=self, align=uiconst.TOALL, pos=(0, 0, 0, 0), idx=0, state=uiconst.UI_DISABLED)
            mark = uiprimitives.Sprite(parent=self.sr.marks, name='area', left=x - mark.width / 2, top=y - mark.height / 2 + 1, width=128, height=128, state=uiconst.UI_PICKCHILDREN, texturePath='res:/UI/Texture/circle_full.png', color=(1.0, 1.0, 1.0, 0.21))
            if hint:
                uicontrols.EveLabelMedium(text=hint, parent=self.sr.marks, left=mark.left + mark.width, top=mark.top + 2, width=min(128, max(64, size - mark.left - mark.width)), state=uiconst.UI_NORMAL)

    def OnDestinationSet(self, destinationID, *args):
        if self is None or self.destroyed:
            return
        self.CheckDestination()

    def Reset(self):
        self.portion = 0.75
        self.areas = []
        self.orbs = []
        self.hilite = None
        self.imhere = None
        self.overlays = None
        self.lasthilite = None
        self.pickradius = 6
        self.mapitems = []
        self.outsideitems = []
        self.ids = None
        self.idlevel = None
        self.drawlevel = None
        self.clipped = 0
        self.updatemylocationtimer = None
        self.showingtempangle = None
        self.settings = None

    def _OnClose(self):
        sm.UnregisterNotify(self)
        self.updatemylocationtimer = None
        for each in self.overlays.children:
            if each.name == 'destinationline':
                if hasattr(each, 'renderObject') and each.renderObject and len(each.renderObject.children):
                    for _each in each.renderObject.children:
                        _each.object.numPoints = 0
                        del _each.object.vectorCurve.keys[:]
                        each.renderObject.children.remove(_each)

                each.renderObject = None
                each.Close()

        self.OnSelectItem = None
        self.Reset()

    def Draw(self, ids, idlevel, drawlevel, needsize, sprite = None, solarsystem = None):
        _settings = (ids,
         idlevel,
         drawlevel,
         needsize)
        if _settings == self.settings:
            return
        self.settings = _settings
        lg.Info('2Dmaps', 'Drawing map, ids/idlevel/drawlevel:', ids, idlevel, drawlevel)
        if drawlevel <= idlevel:
            return
        if drawlevel == DRAW_SOLARSYSTEM_INTERIOR and len(ids) > 1:
            ids = ids[:1]
        SIZE = needsize
        if sprite is None:
            sprite = self.sprite
        _ids = {}
        for id in ids:
            _ids[id] = ''

        ids = _ids.keys()
        endid = ''
        if len(ids) > 1:
            endid = '%s_' % ids[-1]
        self.ids = ids
        self.idlevel = idlevel
        self.drawlevel = drawlevel
        self.needsize = needsize
        imageid = '%s_%s_%s_%s_%s_%s' % (ids[0],
         '_' * max(0, len(ids) - 2),
         endid,
         idlevel,
         drawlevel,
         self.fillSize)
        imageid = imageid.replace('.', '')
        if self.drawlevel == DRAW_SOLARSYSTEM_INTERIOR:
            imageid += '_' + str(settings.user.ui.Get('solarsystemmapabstract', 0))
        lg.Info('2Dmaps', 'MapID is: %s' % imageid)
        for each in self.overlays.children:
            if each.name == 'destinationline':
                each.renderObject = None
                each.Close()

        self.cordsAsPortion = {}
        mapitems = self.mapitems = self.GetMapData(ids, idlevel, drawlevel)
        if drawlevel == 4:
            self.DrawSolarsystem(sprite, ids, imageid, mapitems, SIZE)
            self.CheckMyLocation(solarsystem=solarsystem)
            return
        connections, outsideitems = self.GetConnectionData(ids, idlevel, drawlevel)
        self.outsideitems = outsideitems
        minx = 1e+100
        maxx = -1e+100
        minz = 1e+100
        maxz = -1e+100
        for item in mapitems:
            minx = min(minx, item.x)
            maxx = max(maxx, item.x)
            minz = min(minz, item.z)
            maxz = max(maxz, item.z)

        mw = -minx + maxx
        mh = -minz + maxz
        if not (mw and mh):
            return
        SIZE = SIZE * 2
        drawarea = DrawArea()
        drawarea.setTransparentColor(-1)
        drawarea.setSize(SIZE, SIZE, 4278190080L)
        dotrad = [2,
         3,
         4,
         5,
         6][idlevel]
        sizefactor = min(SIZE / mw, SIZE / mh) * self.portion
        cords = {}
        for item in mapitems[:]:
            if item.groupID == const.groupRegion:
                if drawlevel != 1:
                    continue
            if item.groupID == const.groupConstellation:
                if drawlevel != 2:
                    continue
            x = int(item.x * sizefactor - int(minx * sizefactor) + (SIZE - mw * sizefactor) / 2)
            y = int(item.z * sizefactor - int(minz * sizefactor) + (SIZE - mh * sizefactor) / 2)
            cords[item.itemID] = (x,
             SIZE - y,
             dotrad,
             1,
             16777215)

        for item in self.outsideitems:
            x = int(item.x * sizefactor - int(minx * sizefactor) + (SIZE - mw * sizefactor) / 2)
            y = int(item.z * sizefactor - int(minz * sizefactor) + (SIZE - mh * sizefactor) / 2)
            cords[item.itemID] = (x,
             SIZE - y,
             dotrad,
             0,
             None)

        done = []
        i = 0
        lineWidth = 2.0
        for jumptype in connections:
            for pair in jumptype:
                fr, to = pair
                if (fr, to) in done:
                    continue
                if fr in cords and to in cords:
                    drawarea.line(cords[fr][0], cords[fr][1], cords[to][0], cords[to][1], [43520, 255, 16711680][i], lineWidth)
                    drawarea.line(cords[fr][0] + 1, cords[fr][1], cords[to][0] + 1, cords[to][1], [43520, 255, 16711680][i], lineWidth)
                    drawarea.line(cords[fr][0], cords[fr][1] + 1, cords[to][0], cords[to][1] + 1, [43520, 255, 16711680][i], lineWidth)

            i += 1

        for x, y, dotrad, cordtype, col in cords.itervalues():
            if cordtype == 0:
                dotrad = dotrad / 2
            drawarea.circle(x, y, dotrad, dotrad, 16777215, 16777215)

        self.areas = [ (cords[id][0],
         cords[id][1],
         cords[id][2],
         id) for id in cords.iterkeys() ]
        self.cordsAsPortion = {}
        for id in cords.iterkeys():
            self.cordsAsPortion[id] = (cords[id][0] / float(SIZE), cords[id][1] / float(SIZE))

        self.CheckMyLocation(solarsystem=solarsystem)
        self.CheckDestination()
        self.PlaceMap(sprite, drawarea, SIZE)

    def CheckDestination(self):
        if self is None or self.destroyed:
            return
        destination = sm.GetService('starmap').GetDestination()
        if destination and self.drawlevel == DRAW_SOLARSYSTEMS:
            x, y = self.GetCordsByKeyAsPortion(destination)
            if x is None or y is None:
                return
            self.destination.sr.x, self.destination.sr.y = x, y
            self.destination.state = uiconst.UI_DISABLED
            self.RefreshOverlays(1)
        else:
            for each in self.overlays.children:
                if each.name == 'destinationline':
                    each.renderObject = None
                    each.Close()

    def GetMapData(self, ids, idlevel, drawlevel):
        if idlevel != 3 and drawlevel != idlevel + 1:
            raise Exception('map2d.py GetMapData: Unexpected usage pattern for this function! idlevel: %i, drawLevel: %i' % (idlevel, drawlevel))
        if len(ids) != 1:
            raise Exception('map2d.py GetMapData: Unexpected usage pattern for this function! Many IDs:' + str(ids))
        if drawlevel == DRAW_REGIONS:
            return GetMap2DItemsForUniverse()
        elif drawlevel == DRAW_CONSTELLATIONS:
            return GetMap2DItemsForRegion(ids[0])
        elif drawlevel == DRAW_SOLARSYSTEMS:
            return GetMap2DItemsForConstellation(ids[0])
        else:
            return GetMap2DItemsForSolarSystem(ids[0])

    def GetConnectionData(self, ids, idlevel, drawlevel):
        if len(ids) != 1:
            raise Exception('unexpectedly many IDs passed to GetConnectionData: %s' % str(ids))
        if drawlevel == DRAW_REGIONS:
            return GetMap2DConnectionsForUniverse()
        if drawlevel == DRAW_CONSTELLATIONS:
            return GetMap2DConstellationConnectionsForRegion(ids[0])
        if drawlevel == DRAW_SOLARSYSTEMS:
            return GetMap2DConnectionsForConstellation(ids[0])
        raise Exception('map2D GetConnectionData unexpectedly asked for connections for drawlevel %i', drawlevel)

    def Width(self):
        return self.absoluteRight - self.absoluteLeft

    def Height(self):
        return self.absoluteBottom - self.absoluteTop

    def MyHierarchy(self):
        return (eve.session.regionid,
         eve.session.constellationid,
         eve.session.solarsystemid2,
         eve.session.stationid)

    def PlaceMap(self, sprite, drawArea, size):
        """ Attach the newly drawn map graphics to sprite """
        if self is None or self.destroyed:
            return
        hostBitmap = trinity.Tr2HostBitmap(size, size, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
        hostBitmap.LoadFromPngInMemory(drawArea.outPNG2())
        sprite.texture.atlasTexture = uicore.uilib.CreateTexture(size, size)
        sprite.texture.atlasTexture.CopyFromHostBitmap(hostBitmap)
        sprite.color.a = 1.0

    def CheckMyLocation(self, solarsystem = None):
        if self is None or self.destroyed:
            return
        self.updatemylocationtimer = None
        self.imhere.sr.x = self.imhere.sr.y = None
        self.imhere.state = uiconst.UI_HIDDEN
        self.destination.sr.x = self.destination.sr.y = None
        self.destination.state = uiconst.UI_HIDDEN
        destination = sm.GetService('starmap').GetDestination()
        if self.drawlevel < DRAW_SOLARSYSTEM_INTERIOR or eve.session.stationid:
            for locationID in self.cordsAsPortion.iterkeys():
                if locationID in self.MyHierarchy() or locationID == solarsystem:
                    self.imhere.sr.x, self.imhere.sr.y = self.cordsAsPortion[locationID]
                    self.imhere.state = uiconst.UI_DISABLED
                if destination and locationID == destination:
                    self.destination.sr.x, self.destination.sr.y = self.cordsAsPortion[locationID]
                    self.destination.state = uiconst.UI_DISABLED

        elif self.ids[0] == eve.session.solarsystemid2:
            self.updatemylocationtimer = base.AutoTimer(100, self.UpdateMyLocation)
            uthread.new(self.UpdateMyLocation)
        self.RefreshOverlays(1)

    def UpdateMyLocation(self):
        if not uiutil.IsUnder(self, uicore.desktop):
            return
        bp = sm.GetService('michelle').GetBallpark()
        if bp is None or self is None or self.destroyed:
            self.updatemylocationtimer = None
            return
        myball = bp.GetBall(eve.session.shipid)
        if myball is None:
            self.updatemylocationtimer = None
            return
        size = max(1, self.absoluteRight - self.absoluteLeft)
        if size == 1:
            size = max(1, self.absoluteRight - self.absoluteLeft)
        x = y = None
        if self.allowAbstract and settings.user.ui.Get('solarsystemmapabstract', 0):
            if not len(self.orbs):
                return
            x, y = self.GetAbstractPosition((myball.x, 0.0, myball.z), 1)
        elif self.sr.sizefactor is not None and self.sr.sizefactorsize is not None:
            maxdist = self.GetMaxDist()
            sizefactor = size / 2 / maxdist * self.fillSize
            x = FLIPMAP * myball.x * sizefactor / float(size) + 0.5
            y = -(myball.z * sizefactor) / float(size) + 0.5
        if x is not None and y is not None:
            self.imhere.sr.x = x
            self.imhere.sr.y = y
            self.imhere.state = uiconst.UI_DISABLED
        scene = sm.GetService('sceneManager').GetRegisteredScene('default')
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        if camera is None:
            return
        rot = geo2.QuaternionRotationGetYawPitchRoll(camera.rotationAroundParent)
        look = geo2.QuaternionRotationGetYawPitchRoll(camera.rotationOfInterest)
        if not self.fov:
            self.fov = Fov(parent=self.imhere)
        self.fov.SetRotation(rot[0] + look[0] - pi)
        actualfov = camera.fieldOfView * (uicore.desktop.width / float(uicore.desktop.height))
        degfov = actualfov - pi / 2
        self.fov.SetFovAngle(actualfov)
        if self.showingtempangle:
            if not self.tempAngleFov:
                self.tempAngleFov = Fov(parent=self.imhere, state=uiconst.UI_DISABLED, blendMode=trinity.TR2_SBM_ADDX2)
                self.tempAngleFov.SetColor((0.0, 0.3, 0.0, 1.0))
            self.tempAngleFov.display = True
            self.tempAngleFov.SetRotation(rot[0] + look[0] - pi)
            angle = self.showingtempangle
            self.tempAngleFov.SetFovAngle(angle)
        elif self.tempAngleFov:
            self.tempAngleFov.display = False
        self.RefreshOverlays()

    def SetTempAngle(self, angle):
        if self.imhere is None or self.imhere.destroyed or len(self.imhere.children) <= 1:
            return
        self.showingtempangle = angle

    def GetRegionColor(self, regionID):
        color = trinity.TriColor()
        color.SetHSV(float(regionID) * 21 % 360.0, 0.5, 0.8)
        color.a = 0.75
        return color

    def GetAbstractPosition(self, pos, asPortion = 0, size = None):
        if not len(self.orbs):
            return (None, None)
        dist = geo2.Vec3Length(pos)
        maxorb = None
        minorb = (0.0, 0)
        for orbdist, pixelrad, orbititem, SIZE in self.orbs:
            if orbdist < dist:
                minorb = (orbdist, pixelrad)
            elif orbdist > dist and maxorb is None:
                maxorb = (orbdist, pixelrad)

        mindist, minpixelrad = minorb
        distInPixels = minpixelrad
        if maxorb:
            maxdist, maxpixelrad = maxorb
            rnge = maxdist - mindist
            pixelrnge = maxpixelrad - minpixelrad
            posWithinRange = dist - mindist
            distInPixels += pixelrnge * (posWithinRange / rnge)
        sizefactor = float(distInPixels) / dist
        if asPortion:
            size = max(1, self.absoluteRight - self.absoluteLeft)
            return (float(size) / (FLIPMAP * pos[0] * sizefactor + SIZE / 2), float(size) / (pos[2] * sizefactor + SIZE / 2))
        return (int(FLIPMAP * pos[0] * sizefactor) + SIZE / 2, int(pos[2] * sizefactor) + SIZE / 2)

    def GetPick(self):
        areas = []
        size = max(1, self.absoluteRight - self.absoluteLeft)
        radius = 2
        isAbstract = self.allowAbstract and settings.user.ui.Get('solarsystemmapabstract', 0) == 1
        for locationID in self.cordsAsPortion.iterkeys():
            if len(self.mouseHoverGroups) and not isAbstract:
                locationrec = self.GetItemRecord(locationID)[0]
                if not locationrec or locationrec.groupID not in self.mouseHoverGroups:
                    continue
            x, y = self.GetCordsByKeyAsPortion(locationID, size)
            if x is None or y is None:
                continue
            if int(x - radius - 3) <= uicore.uilib.x - self.absoluteLeft <= int(x + radius + 3) and int(y - radius - 3) <= uicore.uilib.y - self.absoluteTop <= int(y + radius + 3):
                areas.append(locationID)

        return areas

    def GetItemRecord(self, getkey):
        for each in self.mapitems:
            if not hasattr(each, 'itemID'):
                continue
            if each.itemID == getkey:
                return (each, 1)

        for each in self.outsideitems:
            if not hasattr(each, 'itemID'):
                continue
            if each.itemID == getkey:
                return (each, 0)

        return (None, None)

    def GetCordsByKeyAsPortion(self, locationID, size = None):
        if size is None:
            return self.cordsAsPortion.get(locationID, (None, None))
        x, y = self.cordsAsPortion.get(locationID, (None, None))
        if x is not None and y is not None:
            return (int(x * size), int(y * size))
        return (None, None)

    def ToggleAbstract(self, setTo):
        uthread.new(self._ToggleAbstract, setTo)

    def _ToggleAbstract(self, setTo):
        settings.user.ui.Set('solarsystemmapabstract', setTo)
        self.settings = None
        self.Draw(self.ids, self.idlevel, self.drawlevel, self.needsize)

    def SetSelected(self, ids):
        if self is None or self.destroyed:
            return
        for each in self.overlays.children[:]:
            if each.name == 'selected':
                each.Close()

        for id in ids:
            x, y = self.GetCordsByKeyAsPortion(id)
            if x is not None and y is not None:
                newsel = uiprimitives.Container(parent=self.overlays, name='selected', align=uiconst.TOPLEFT, width=16, height=16, state=uiconst.UI_DISABLED)
                pointer = uiprimitives.Sprite(parent=newsel, pos=(0, 0, 16, 32), state=uiconst.UI_PICKCHILDREN, texturePath='res:/UI/Texture/Shared/circlePointerDown.png', color=(1.0, 1.0, 1.0, 0.4))
                newsel.sr.x = x
                newsel.sr.y = y

        self.RefreshOverlays(1)

    def _OnResize(self):
        if self.align == uiconst.TOTOP:
            self.height = self.absoluteRight - self.absoluteLeft
        elif self.align in (uiconst.TOLEFT, uiconst.TORIGHT):
            self.width = self.absoluteBottom - self.absoluteTop
        try:
            self.RefreshOverlays(1)
        except:
            sys.exc_clear()

    def RefreshOverlays(self, update = 0):
        if not uiutil.IsUnder(self, uicore.desktop):
            return
        if self is None or self.destroyed or not uicore.uilib:
            return
        size = self.absoluteRight - self.absoluteLeft
        for each in self.sr.areas.children:
            if not hasattr(each, 'sr') or getattr(each.sr, 'x', None) is None and getattr(each.sr, 'y', None) is None:
                continue
            each.width = each.height = int(each.sr.rad * size * 2)
            each.left = int(getattr(each.sr, 'x', 0) * size) - each.width / 2 + 1
            each.top = int(getattr(each.sr, 'y', 0) * size) - each.height / 2 + 1

        for each in self.overlays.children:
            if not hasattr(each, 'sr') or getattr(each.sr, 'x', None) is None and getattr(each.sr, 'y', None) is None:
                continue
            each.left = int(getattr(each.sr, 'x', 0) * size) - each.width / 2 + 1
            each.top = int(getattr(each.sr, 'y', 0) * size) - each.height / 2 + 1

    def OnClick(self, *args):
        areas = self.GetPick()
        if areas:
            self.OnSelectItem(self, areas[0])

    def OnMouseDown(self, *args):
        if self.dragAllowed:
            self.dragging = 1

    def OnMouseUp(self, *args):
        if self.dragging:
            self.left = max(-self.width + 24, min(self.parent.absoluteRight - self.parent.absoluteLeft - 24, self.left))
            self.top = max(-self.height + 24, min(self.parent.absoluteBottom - self.parent.absoluteTop - 24, self.top))
            uiutil.SetOrder(self, -1)
        self.dragging = 0

    def SetHint(self, hint):
        self.hilite.state = uiconst.UI_HIDDEN
        refresh = self.sr.hint != hint
        self.sr.hint = hint
        self.hilite.state = uiconst.UI_DISABLED
        if refresh:
            uicore.uilib.tooltipHandler.RefreshTooltipForOwner(self)

    def GetTooltipPosition(self):
        if self.tooltipPositionRect:
            return self.tooltipPositionRect

    def OnMouseMove(self, *args):
        if self.dragging:
            self.left = max(-self.width + 24, min(self.parent.absoluteRight - self.parent.absoluteLeft - 24, self.left))
            self.top = max(-self.height + 24, min(self.parent.absoluteBottom - self.parent.absoluteTop - 24, self.top))
            return
        areas = self.GetPick()
        if areas:
            if (areas[0], len(areas)) == self.lasthilite:
                return
            self.lasthilite = (areas[0], len(areas))
            x, y = self.GetCordsByKeyAsPortion(areas[0], self.absoluteRight - self.absoluteLeft)
            if x is not None and y is not None:
                self.hilite.left = x - self.hilite.width / 2
                self.hilite.top = y - self.hilite.height / 2 + 1
                self.hilite.state = uiconst.UI_DISABLED
                locStr = ''
                locStrList = []
                for id in areas:
                    datarec, datahint = self.GetDataArgs(id)
                    item, insider = self.GetItemRecord(id)
                    if item:
                        groupname = cfg.invgroups.Get(item.groupID).name
                        if item.itemName.lower().find(groupname.lower()) >= 0:
                            groupname = ''
                        locStrList.append(localization.GetByLabel('UI/Map/Map2D/hintMouseMoveFormating', locationName=item.itemName, dataHint=datahint, locationGroupName=groupname))
                        if not insider:
                            parent = sm.GetService('map').GetItem(item.locationID)
                            linkTo = '<br>'.join(locStrList)
                            locStrList = [localization.GetByLabel('UI/Map/Map2D/hintMouseMove', group=cfg.invgroups.Get(parent.groupID).name, parent=parent.itemName, linkTo=linkTo)]

                locStr = '<br>'.join(locStrList)
                self.SetHint(locStr)
                self.tooltipPositionRect = (uicore.uilib.x - 6,
                 uicore.uilib.y - 6,
                 12,
                 12)
                return
        self.SetHint('')
        self.hilite.state = uiconst.UI_HIDDEN
        self.lasthilite = None

    def OnMouseExit(self, *args):
        self.hilite.state = uiconst.UI_HIDDEN

    def GetMenu(self):
        m = []
        pick = self.GetPick()
        if len(pick) == 1:
            item, insider = self.GetItemRecord(pick[0])
            m += sm.GetService('menu').CelestialMenu(pick[0], item)
            m += self.GetDataMenu(pick[0])
        else:
            for itemID in pick:
                item, insider = self.GetItemRecord(itemID)
                if item:
                    submenu = sm.GetService('menu').CelestialMenu(itemID, item)
                    submenu += self.GetDataMenu(itemID)
                    if len(submenu):
                        if item.groupID == const.groupStation:
                            locationName = uix.EditStationName(item.itemName)
                        else:
                            locationName = item.itemName
                        groupname = cfg.invgroups.Get(item.groupID).name
                        if locationName.lower().find(groupname.lower()) >= 0:
                            groupname = ''
                        locationName = uiutil.MenuLabel('UI/Map/Map2D/menuLocationEntry', {'locationName': locationName,
                         'groupName': groupname})
                        m.append((locationName, submenu))

            m.sort()
        if not m:
            m = self.GetParentMenu()
        if self.drawlevel == DRAW_SOLARSYSTEM_INTERIOR:
            if self.allowAbstract:
                isAbstract = settings.user.ui.Get('solarsystemmapabstract', 0) == 1
                if isAbstract:
                    lbl = uiutil.MenuLabel('UI/Map/Map2D/menuShowNonAbstract')
                else:
                    lbl = uiutil.MenuLabel('UI/Map/Map2D/menuShowAbstract')
                m += [None, (lbl, self.ToggleAbstract, (not isAbstract,))]
        return m

    def GetParentMenu(self):
        return []

    def GetMaxDist(self):
        maxdist = 0.0
        for item in self.mapitems:
            pos = (item.x, 0.0, item.z)
            maxdist = max(maxdist, geo2.Vec3Length(pos))

        return maxdist

    def DrawSolarsystem(self, sprite, ids, imageid, mapitems, SIZE):
        if not len(mapitems):
            return
        planets = []
        stargates = []
        asteroidbelts = []
        for item in mapitems:
            if item.groupID == const.groupPlanet:
                planets.append(item)
            elif item.groupID == const.groupStargate:
                stargates.append(item)
            elif item.groupID == const.groupAsteroidBelt:
                asteroidbelts.append(item)

        drawarea = DrawArea()
        drawarea.setTransparentColor(-1)
        drawarea.setSize(SIZE, SIZE, 4278190080L)
        cords = {}
        sunID = None
        maxdist = 0.0
        for item in mapitems:
            pos = (item.x, 0.0, item.z)
            maxdist = max(maxdist, geo2.Vec3Length(pos))
            if item.groupID == const.groupSun:
                sunID = item.itemID
                radius = 3
                drawarea.circle(SIZE / 2, SIZE / 2, radius, radius, 10066329, 10066329)

        sizefactor = SIZE / 2 / maxdist * self.fillSize
        self.sr.sizefactor = sizefactor
        self.sr.sizefactorsize = SIZE
        if self.allowAbstract and settings.user.ui.Get('solarsystemmapabstract', 0):
            _planets = []
            for planet in planets:
                pos = (planet.x, planet.y, planet.z)
                dist = geo2.Vec3Length(pos)
                _planets.append([dist, planet])

            _planets = uiutil.SortListOfTuples(_planets)
            planet = _planets
        i = 1
        for item in planets:
            pos = (item.x, 0.0, item.z)
            dist = geo2.Vec3Length(pos)
            if self.allowAbstract and settings.user.ui.Get('solarsystemmapabstract', 0):
                planetscale = i * (maxdist / len(planets)) / dist
                pos = geo2.Vec3Scale(pos, planetscale)
            x = FLIPMAP * pos[0] * sizefactor + SIZE / 2
            y = pos[2] * sizefactor + SIZE / 2
            radius = 1
            cords[item.itemID] = (x, SIZE - y, radius)
            drawarea.circle(x, SIZE - y, radius, radius, 16777215, mathUtil.LtoI(4278190080L))
            self.AddChilds(x, y, radius, item.itemID, SIZE, drawarea, cords, item)
            i += 1

        self.orbs = []
        for orbit in planets:
            if orbit.itemID in cords:
                x, y, radius = cords[orbit.itemID]
                center = SIZE / 2
                frompos = geo2.Vector(float(center), 0.0, float(center))
                topos = geo2.Vector(float(x), 0.0, float(y))
                diff = topos - frompos
                rad = int(geo2.Vec3Length(diff))
                drawarea.circle(center, center, rad, rad, self.GetColorByGroupID(const.groupPlanet), mathUtil.LtoI(4278190080L))
                orbpos = (orbit.x, 0.0, orbit.z)
                orbdist = geo2.Vec3Length(orbpos)
                self.orbs.append([orbdist, (orbdist,
                  rad,
                  orbit,
                  SIZE)])

        self.orbs = uiutil.SortListOfTuples(self.orbs)
        for item in stargates:
            if self.allowAbstract and settings.user.ui.Get('solarsystemmapabstract', 0):
                if not len(self.orbs):
                    return
                x, y = self.GetAbstractPosition((item.x, 0.0, item.z))
            else:
                x = FLIPMAP * self.sr.sizefactor * item.x + self.sr.sizefactorsize / 2
                y = self.sr.sizefactor * item.z + self.sr.sizefactorsize / 2
            x += 6
            radius = 1
            drawarea.circle(x, SIZE - y, radius, radius, 0, self.GetColorByGroupID(const.groupStargate))
            cords[item.itemID] = (x, SIZE - y, radius)

        self.areas = [ (cords[id][0],
         cords[id][1],
         cords[id][2],
         id) for id in cords.iterkeys() ]
        self.cordsAsPortion = {}
        for id in cords.iterkeys():
            self.cordsAsPortion[id] = (cords[id][0] / float(SIZE), cords[id][1] / float(SIZE))

        if self.destroyed:
            return
        self.PlaceBackground('res:/UI/Texture/map_ssunderlay.png')
        self.PlaceMap(sprite, drawarea, SIZE)

    def AddChilds(self, parentX, parentY, parentRad, parentID, SIZE, draw, cords, parent, _x = None, _y = None):
        parentpos = geo2.Vector(parent.x, parent.y, parent.z)
        sorted = []
        allchilds = self.GetChilds(parentID, [], 0)
        for child in allchilds:
            childpos = geo2.Vector(child.x, child.y, child.z)
            diff = childpos - parentpos
            dist = geo2.Vec3Length(diff)
            sorted.append((dist, child))

        sorted = uiutil.SortListOfTuples(sorted)
        if self.allowAbstract and settings.user.ui.Get('solarsystemmapabstract', 0):
            done = []
            i = 1
            xi = 0
            for child in sorted:
                if child.itemID in done:
                    continue
                radius = 1
                step = max(12, radius * 4) - 2
                y = _y or parentY + parentRad + i * step
                x = _x or parentX + xi
                if y + step > SIZE:
                    i = 0
                    xi += step
                done.append(child.itemID)
                fill = self.GetColorByGroupID(child.groupID)
                draw.circle(x, SIZE - y, radius, radius, fill, fill)
                cords[child.itemID] = (x, SIZE - y, radius)
                i += 1

        else:
            for child in sorted:
                radius = 1
                pos = geo2.Vector(child.x, 0.0, child.z)
                pos = pos + (pos - parentpos) * max(1.0, 4096 / SIZE)
                x = FLIPMAP * pos.x * self.sr.sizefactor + SIZE / 2
                y = pos.z * self.sr.sizefactor + SIZE / 2
                fill = self.GetColorByGroupID(child.groupID)
                draw.circle(x, SIZE - y, radius, radius, fill, fill)
                cords[child.itemID] = (x, SIZE - y, radius)

    def GetChilds(self, parentID, childs, i):
        i += 1
        if i == 20 or len(childs) > 1000:
            return childs
        _childs = [ child for child in self.mapitems if child.orbitID == parentID and child not in childs ]
        if len(_childs):
            childs += _childs
            for granchild in _childs:
                childs = self.GetChilds(granchild.itemID, childs, i)

        return childs

    def GetColorByGroupID(self, groupID):
        col = {const.groupAsteroidBelt: 255,
         const.groupPlanet: 8947848,
         const.groupStargate: 34816,
         const.groupStation: 16724787}.get(groupID, 10066329)
        return col

    def GetDataArgs(self, locationID):
        if locationID in self.dataArgs:
            return self.dataArgs[locationID]
        return (None, '')

    def GetDataMenu(self, locationID):
        datarec, datahint = self.GetDataArgs(locationID)
        if not datarec:
            return []
        locationrec = self.GetItemRecord(locationID)[0]
        if not locationrec:
            return []
        return self.GetDataMenuExt(self, locationrec, datarec)

    def GetDataMenuExt(self, *args):
        return []

    def Fade(self, what, f, t):
        start, ndt = blue.os.GetWallclockTime(), 0.0
        while ndt != 1.0:
            ndt = min(blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime()) / 1000.0, 1.0)
            what.color.a = mathUtil.Lerp(f, t, ndt)
            blue.pyos.synchro.Yield()

    def PlaceBackground(self, imagepath):
        if self is None or self.destroyed:
            return
        imagepath = str(imagepath)
        if self.bgSprite is None:
            self.bgSprite = uiprimitives.Sprite(name='bgSprite', parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 1.0), texturePath=imagepath, filter=True)

    def OnSelectItem(self, _self, arg, *args):
        pass


class Fov(uiprimitives.Transform):
    __guid__ = 'uicls.Map2dFov'
    default_name = 'fov'
    default_left = 0
    default_top = 0
    default_width = 128
    default_height = 128
    default_align = uiconst.CENTER
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        uiprimitives.Transform.ApplyAttributes(self, attributes)
        blendMode = attributes.get('blendMode', trinity.TR2_SBM_BLEND)
        self.angle = math.pi
        self.color = (1.0, 1.0, 1.0, 0.5)
        self.polygon = uicls.Polygon(parent=self, align=uiconst.TOALL, blendMode=trinity.TR2_SBM_ADD)
        self.RenderGradient()

    def RenderGradient(self):
        self.polygon.Flush()
        directionAngle = math.pi / 2
        fromDeg = directionAngle - self.angle / 2
        toDeg = directionAngle + self.angle / 2
        numSegments = 40
        segmentStep = (toDeg - fromDeg) / float(numSegments)
        c = self.color
        innerColor = c
        outerColor = (c[0],
         c[1],
         c[2],
         0.0)
        radius = 50
        ro = self.polygon.GetRenderObject()
        for i in xrange(numSegments + 1):
            a = fromDeg + i * segmentStep
            x = math.cos(a)
            y = -math.sin(a)
            innerVertex = trinity.Tr2Sprite2dVertex()
            innerVertex.position = (self.width / 2 * uicore.desktop.dpiScaling, self.height / 2 * uicore.desktop.dpiScaling)
            innerVertex.color = innerColor
            ro.vertices.append(innerVertex)
            outerVertex = trinity.Tr2Sprite2dVertex()
            outerVertex.position = ((self.width / 2 + radius * x) * uicore.desktop.dpiScaling, (self.height / 2 + radius * y) * uicore.desktop.dpiScaling)
            outerVertex.color = outerColor
            ro.vertices.append(outerVertex)

        for i in xrange(numSegments * 2):
            triangle = trinity.Tr2Sprite2dTriangle()
            triangle.index0 = i
            triangle.index1 = i + 1
            triangle.index2 = i + 2
            ro.triangles.append(triangle)

    def SetColor(self, color):
        self.color = color
        self.RenderGradient()

    def SetFovAngle(self, angle):
        self.angle = angle
        self.RenderGradient()


import collections
Map2DItemInfoType = collections.namedtuple('Map2DItemInfoType', ['itemID',
 'typeID',
 'locationID',
 'itemName',
 'groupID',
 'x',
 'y',
 'z'])
Map2DCelestialItemInfoType = collections.namedtuple('Map2DItemInfoType', ['itemID',
 'typeID',
 'orbitID',
 'orbitIndex',
 'celestialIndex',
 'locationID',
 'itemName',
 'groupID',
 'x',
 'y',
 'z'])

def GetMap2DConnectionsForUniverse():
    connections = []
    for regionID, regionData in cfg.mapRegionCache.iteritems():
        if regionID > const.mapWormholeRegionMin:
            continue
        for neighbourID in regionData.neighbours:
            connections.append((regionID, neighbourID))

    return ((connections, [], []), [])


def GetMap2DConstellationConnectionsForRegion(regionID):
    """
    Gets all the connections between constellations within a regionID
    connections to constellations outside of the region are listed as "items"
    in the last list.
    """
    connectionsToOtherRegions = []
    connectionsWithinRegion = []
    externalItems = []
    regionInfo = cfg.mapRegionCache[regionID]
    constellationsInRegion = set(regionInfo.constellationIDs)
    for constellationID in constellationsInRegion:
        constellation = cfg.mapConstellationCache[constellationID]
        for neighbourID in constellation.neighbours:
            if neighbourID not in constellationsInRegion:
                nei = cfg.mapConstellationCache[neighbourID]
                i = Map2DItemInfoType(itemID=neighbourID, locationID=nei.regionID, itemName=localization.GetByMessageID(nei.nameID), groupID=const.groupConstellation, typeID=const.typeConstellation, x=nei.center.x, y=nei.center.y, z=nei.center.z)
                externalItems.append(i)
                connectionsToOtherRegions.append((constellationID, neighbourID))
            else:
                connectionsWithinRegion.append((constellationID, neighbourID))

    return ((connectionsToOtherRegions, connectionsWithinRegion, []), externalItems)


def GetMap2DConnectionsForConstellation(constellationID):
    """
    Gets all the connections of systems to other systems within the region 
    and also connections that go outside the region or constellation.
    """
    connectionsToOtherRegions = []
    connectionsToOtherConstellations = []
    connectionsWithinConstellation = []
    externalItems = []
    constellationInfo = cfg.mapConstellationCache[constellationID]
    systemsInConstellation = set(constellationInfo.solarSystemIDs)
    regionInfo = cfg.mapRegionCache[constellationInfo.regionID]
    systemsInRegion = set(regionInfo.solarSystemIDs)
    for solarSystemID in systemsInConstellation:
        ssInfo = cfg.mapSystemCache[solarSystemID]
        for neighbour in ssInfo.neighbours:
            neighbourID = neighbour.solarSystemID
            if neighbourID in systemsInConstellation:
                connectionsWithinConstellation.append((solarSystemID, neighbourID))
            else:
                nei = cfg.mapSystemCache[neighbourID]
                externalItems.append(Map2DItemInfoType(itemID=neighbourID, locationID=nei.constellationID, itemName=localization.GetByMessageID(nei.nameID), groupID=const.groupSolarSystem, typeID=const.typeSolarSystem, x=nei.center.x, y=nei.center.y, z=nei.center.z))
                if neighbourID not in systemsInRegion:
                    connectionsToOtherRegions.append((solarSystemID, neighbourID))
                elif neighbourID not in systemsInConstellation:
                    connectionsToOtherConstellations.append((solarSystemID, neighbourID))

    return ((connectionsToOtherRegions, connectionsToOtherConstellations, connectionsWithinConstellation), externalItems)


def GetMap2DItemsForUniverse():
    items = []
    for regionID, regionData in cfg.mapRegionCache.iteritems():
        if regionID > const.mapWormholeRegionMin:
            continue
        i = Map2DItemInfoType(itemID=regionID, locationID=9, itemName=localization.GetByMessageID(regionData.nameID), groupID=const.groupRegion, typeID=const.typeRegion, x=regionData.center.x, y=regionData.center.y, z=regionData.center.z)
        items.append(i)

    return items


def GetMap2DItemsForRegion(regionID):
    """
    Get an item for the region itself, as well as items for all the constellations within the region
    """
    items = []
    regionData = cfg.mapRegionCache[regionID]
    items.append(Map2DItemInfoType(itemID=regionID, locationID=9, itemName=localization.GetByMessageID(regionData.nameID), groupID=const.groupRegion, typeID=const.typeRegion, x=regionData.center.x, y=regionData.center.y, z=regionData.center.z))
    for constellationID in regionData.constellationIDs:
        constellationData = cfg.mapConstellationCache[constellationID]
        items.append(Map2DItemInfoType(itemID=constellationID, locationID=constellationData.regionID, itemName=localization.GetByMessageID(constellationData.nameID), groupID=const.groupConstellation, typeID=const.typeConstellation, x=constellationData.center.x, y=constellationData.center.y, z=constellationData.center.z))

    return items


def GetMap2DItemsForConstellation(constellationID):
    items = []
    constellationData = cfg.mapConstellationCache[constellationID]
    items.append(Map2DItemInfoType(itemID=constellationID, locationID=constellationData.regionID, itemName=localization.GetByMessageID(constellationData.nameID), groupID=const.groupConstellation, typeID=const.typeConstellation, x=constellationData.center.x, y=constellationData.center.y, z=constellationData.center.z))
    for solarSystemID in constellationData.solarSystemIDs:
        solarSystemData = cfg.mapSystemCache[solarSystemID]
        items.append(Map2DItemInfoType(itemID=solarSystemID, locationID=solarSystemData.constellationID, itemName=localization.GetByMessageID(solarSystemData.nameID), groupID=const.groupSolarSystem, typeID=const.typeSolarSystem, x=solarSystemData.center.x, y=solarSystemData.center.y, z=solarSystemData.center.z))

    return items


def GetMap2DItemsForSolarSystem(solarSystemID):
    items = []
    try:
        ssContents = cfg.mapSolarSystemContentCache[solarSystemID]
    except (IndexError, KeyError):
        return []

    sm.GetService('map').GetSolarsystemItems(solarSystemID)
    for stargateID, stargate in ssContents.stargates.iteritems():
        items.append(Map2DCelestialItemInfoType(itemID=stargateID, orbitID=1, orbitIndex=1, locationID=solarSystemID, celestialIndex=0, itemName=cfg.evelocations.Get(stargateID).locationName, groupID=const.groupStargate, typeID=stargate.typeID, x=stargate.position.x, y=stargate.position.y, z=stargate.position.z))

    for planetID, planet in ssContents.planets.iteritems():
        items.append(Map2DCelestialItemInfoType(itemID=planetID, orbitID=1, orbitIndex=1, locationID=solarSystemID, celestialIndex=planet.celestialIndex, itemName=cfg.evelocations.Get(planetID).locationName, groupID=const.groupPlanet, typeID=planet.typeID, x=planet.position.x, y=planet.position.y, z=planet.position.z))
        asteroidBelts = getattr(planet, 'asteroidBelts', {})
        for asteroidBeltID, asteroidBelt in asteroidBelts.iteritems():
            items.append(Map2DCelestialItemInfoType(itemID=asteroidBeltID, orbitID=planetID, orbitIndex=1, celestialIndex=planet.celestialIndex, locationID=solarSystemID, itemName=cfg.evelocations.Get(asteroidBeltID).locationName, groupID=9, typeID=asteroidBelt.typeID, x=asteroidBelt.position.x, y=asteroidBelt.position.y, z=asteroidBelt.position.z))

        npcStations = getattr(planet, 'npcStations', {})
        for npcStationID, npcStation in npcStations.iteritems():
            items.append(Map2DCelestialItemInfoType(itemID=npcStationID, orbitID=planetID, orbitIndex=1, celestialIndex=planet.celestialIndex, locationID=solarSystemID, itemName=cfg.evelocations.Get(npcStationID).locationName, groupID=const.groupStation, typeID=npcStation.typeID, x=npcStation.position.x, y=npcStation.position.y, z=npcStation.position.z))

        moons = getattr(planet, 'moons', {})
        for moonID, moon in moons.iteritems():
            items.append(Map2DCelestialItemInfoType(itemID=moonID, orbitID=planetID, orbitIndex=1, locationID=solarSystemID, celestialIndex=planet.celestialIndex, itemName=cfg.evelocations.Get(moonID).locationName, groupID=const.groupMoon, typeID=moon.typeID, x=moon.position.x, y=moon.position.y, z=moon.position.z))
            asteroidBelts = getattr(moon, 'asteroidBelts', {})
            for asteroidBeltID, asteroidBelt in asteroidBelts.iteritems():
                items.append(Map2DCelestialItemInfoType(itemID=asteroidBeltID, orbitID=moonID, orbitIndex=1, celestialIndex=planet.celestialIndex, locationID=solarSystemID, itemName=cfg.evelocations.Get(asteroidBeltID).locationName, groupID=9, typeID=asteroidBelt.typeID, x=asteroidBelt.position.x, y=asteroidBelt.position.y, z=asteroidBelt.position.z))

            npcStations = getattr(moon, 'npcStations', {})
            for npcStationID, npcStation in npcStations.iteritems():
                items.append(Map2DCelestialItemInfoType(itemID=npcStationID, orbitID=planetID, orbitIndex=1, celestialIndex=planet.celestialIndex, locationID=solarSystemID, itemName=cfg.evelocations.Get(npcStationID).locationName, groupID=const.groupStation, typeID=npcStation.typeID, x=npcStation.position.x, y=npcStation.position.y, z=npcStation.position.z))

    return items
