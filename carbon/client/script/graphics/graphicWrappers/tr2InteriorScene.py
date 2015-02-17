#Embedded file name: carbon/client/script/graphics/graphicWrappers\tr2InteriorScene.py
import blue
import decometaclass
import cef
import geo2
import trinity
import prepassConversion
import yaml
ENLIGHTEN_BUILD_WAIT_TIME = 200
INTERIOR_RES_PATH = const.res.INTERIOR_RES_PATH
INTERIOR_REFMAP_PATH = 'res:/Graphics/Interior/StaticEnvmaps/'

class Tr2InteriorScene(decometaclass.WrapBlueClass('trinity.Tr2InteriorScene')):
    __guid__ = 'graphicWrappers.Tr2InteriorScene'

    @staticmethod
    def Wrap(triObject, resPath):
        Tr2InteriorScene(triObject)
        triObject.objects = {}
        triObject.systemParentName = {}
        triObject.systemNames = {}
        triObject.id = ''
        triObject.cellData = {}
        return triObject

    def SetID(self, id):
        self.id = id

    def _SortCells(self):
        listToSort = list(self.cells)
        listToSort.sort(lambda x, y: x.name < y.name)
        self.cells.removeAt(-1)
        self.cells.extend(listToSort)

    def _SortSystems(self, cell):
        listToSort = list(cell.systems)
        listToSort.sort(lambda x, y: x.systemID < y.systemID)
        cell.systems.removeAt(-1)
        cell.systems.extend(listToSort)
        for i, system in enumerate(cell.systems):
            system.SetSystemInCellIdx(i)

    def _GetCell(self, cellName):
        """
        Finds and returns a cell by a specified name and if it can't will add it before returning
        """
        for cell in self.cells:
            if cell.name == cellName:
                return cell

        cell = trinity.Tr2InteriorCell()
        cell.name = cellName
        cell.shProbeResPath = INTERIOR_RES_PATH + str(self.id) + '_' + cellName + '.shp'
        cell.reflectionMapPath = INTERIOR_REFMAP_PATH + 'Cube_%s_%s.dds' % (self.id, cellName)
        self.cells.append(cell)
        self._SortCells()
        self._LoadUVData(cellName)
        return cell

    def _RemoveCellIfEmpty(self, cell):
        if cell in self.cells:
            if not cell.systems and not cell.probeVolumes:
                self.cells.remove(cell)

    def _RemoveSystemIfEmpty(self, system):
        cellName = self.systemParentName.get(system, None)
        if cellName:
            cell = self._GetCell(cellName)
            if not system.statics:
                cell.RemoveSystem(system)
                self._RemoveCellIfEmpty(cell)

    def _GetSystem(self, cell, systemName):
        """
        Retrieves the x'th system from the past in cell and if it can't
        will add systems till it reaches len(x+1) and returns it
        """
        systemNames = self.systemNames.get(cell.name, None)
        if systemNames is None:
            systemNames = []
            self.systemNames[cell.name] = systemNames
        if systemName not in systemNames:
            systemNames.append(systemName)
        systemNum = systemNames.index(systemName)
        while len(cell.systems) < systemNum + 1:
            newSystem = trinity.Tr2InteriorEnlightenSystem()
            newSystem.bounceScale = 1.0
            newSystem.systemID = hash(cell.name)
            newSystem.radSystemPath = INTERIOR_RES_PATH + str(self.id) + '_' + cell.name + '.rad'
            try:
                path = INTERIOR_RES_PATH + str(self.id) + '_' + cell.name + '.yaml'
                if blue.paths.exists(path):
                    rf = blue.ResFile()
                    rf.Open(path)
                    yamlStr = rf.read()
                    rf.close()
                    data = yaml.load(yamlStr)
                    newSystem.irradianceScale = data['irradianceScale']
                    newSystem.bounceScale = data['bounceScale']
            except:
                pass

            cell.systems.append(newSystem)
            newSystem.SetSystemInCellIdx(cell.systems.index(newSystem))
            self._SortSystems(cell)
            self.systemParentName[newSystem] = cell.name

        return cell.systems[systemNum]

    def AddStatic(self, staticObj, cellName = 'DefaultCell', systemName = 0, id = None):
        """
        Adds a static object to the specified interior cell & system
        """
        prepassConversion.AddPrepassAreasToStatic(staticObj)
        self.RemoveStatic(staticObj)
        cell = self._GetCell(cellName)
        system = self._GetSystem(cell, systemName)
        system.AddStatic(staticObj)
        self.objects[staticObj] = system
        if id is None:
            id = staticObj.objectID
        uvData = self.cellData.get(cellName, {}).get(id, None)
        if uvData:
            staticObj.SetInstanceData(*uvData)

    def RemoveStatic(self, staticObj):
        """
        Removes a static object if its been already added
        """
        system = self.objects.get(staticObj, None)
        if system:
            system.RemoveStatic(staticObj)
            self.objects[staticObj] = None
            self._RemoveSystemIfEmpty(system)

    def AddLight(self, lightObj):
        """
        Adds a light to the scene
        """
        self.RemoveLight(lightObj)
        self.AddLightSource(lightObj)
        try:
            import wx
            triPanel = wx.FindWindowByName('TrinityPanel')
            if triPanel:
                triPanel.PopulateLights()
                triPanel.PopulateLights()
        except:
            pass

    def RemoveLight(self, lightObj):
        """
        Removes a light if its been already added
        """
        if lightObj in self.lights:
            self.RemoveLightSource(lightObj)
            try:
                import wx
                triPanel = wx.FindWindowByName('TrinityPanel')
                if triPanel:
                    triPanel.PopulateLights()
                    triPanel.PopulateLights()
            except:
                pass

    def AddPhysicalPortal(self, portalObj):
        """
        Adds a physical portal to the scene
        """
        if portalObj in self.portals:
            self.RemovePhysicalPortal(portalObj)
        self.portals.append(portalObj)

    def RemovePhysicalPortal(self, portalObj):
        """
        Removes the portal if its already been added
        """
        if portalObj in self.portals:
            self.portals.remove(portalObj)

    def AddOccluder(self, occluderObj, cellName = ''):
        """
        Adds an occluder to the scene
        """
        cell = self._GetCell(cellName)
        if occluderObj in cell.occluders:
            self.RemoveOccluder(occluderObj)
        cell.occluders.append(occluderObj)

    def RemoveOccluder(self, occluderObj):
        """
        Removes the occluder if its already been added
        """
        cell = self._GetCell(occluderObj.cellName)
        if occluderObj in cell.occluders:
            cell.occluders.remove(occluderObj)

    def AddProbeVolume(self, probeObj, cellName = ''):
        """
        Adds a probevolume to the scene
        """
        cell = self._GetCell(cellName)
        if probeObj in cell.probeVolumes:
            self.RemoveProbeVolume(probeObj)
        cell.probeVolumes.append(probeObj)

    def RemoveProbeVolume(self, probeObj):
        """
        Removes the probevolume if its already been added
        """
        cell = self._GetCell(probeObj.cellName)
        if probeObj in cell.probeVolumes:
            cell.probeVolumes.remove(probeObj)

    def AddAvatarToScene(self, avatar):
        """
        Adds a avatar to the scene
        """
        self.AddDynamicToScene(avatar)

    def RemoveAvatarFromScene(self, avatar):
        """
        Removes a avatar from the scene
        """
        self.RemoveDynamicFromScene(avatar)

    def AddDynamicToScene(self, obj):
        """
        Adds a dynamic object to the interior scene
        """
        prepassConversion.AddPrepassAreasToDynamic(obj)
        if type(obj) is trinity.Tr2IntSkinnedObject:
            obj.visualModel.ResetAnimationBindings()
        self.AddDynamic(obj)
        return obj

    def RemoveDynamicFromScene(self, obj):
        """
        Removes a dynamic object from the interior scene
        """
        if obj in self.dynamics:
            self.RemoveDynamic(obj)

    def AddCurveSetToScene(self, curveSet):
        """
        Adds a curve set to the scene.
        """
        self.curveSets.append(curveSet)

    def RemoveCurveSetFromScene(self, curveSet):
        """
        Removes a curve set from the scene.
        """
        self.curveSets.remove(curveSet)

    def Refresh(self):
        pass

    def BuildEnlightenScene(self):
        trinity.WaitForResourceLoads()
        import CCP_P4 as p4
        import os
        for cell in self.cells:
            p4.PrepareFileForSave(blue.paths.ResolvePathForWriting(cell.shProbeResPath))
            for system in cell.systems:
                p4.PrepareFileForSave(blue.paths.ResolvePathForWriting(system.radSystemPath))

            cell.RebuildInternalData()
            lightVolumeRes = [ int(v) + 1 for v in geo2.Vec3Subtract(cell.maxBounds, cell.minBounds) ]
            cell.BuildLightVolume(*lightVolumeRes)
            uvResPath = 'res:/interiorCache/' + str(self.id) + '_' + str(cell.name) + '.uv'
            uvFileName = blue.paths.ResolvePathForWriting(uvResPath)
            p4.PrepareFileForSave(uvFileName)

        import app.Interior.EnlightenBuildProgressDialog as progress
        dlg = progress.EnlightenBuildDialog()
        if dlg.BuildEnlighten(self):
            self.SaveEnlighten()
            revisionsDB = INTERIOR_RES_PATH + str(self.id) + '.revisions'
            revisionsDB = blue.paths.ResolvePathForWriting(revisionsDB)
            p4.PrepareFileForSave(revisionsDB)
            currentRevs = sm.GetService('jessicaWorldSpaceClient').GetWorldSpace(self.id).GetWorldSpaceSpawnRevisionsList()
            if not os.access(revisionsDB, os.F_OK):
                file = open(revisionsDB, 'w')
                yaml.dump(currentRevs, file)
                file.close()
            else:
                with open(revisionsDB, 'w') as DB:
                    yaml.dump(currentRevs, DB)
        p4.AddFilesToP4()
        for cell in self.cells:
            self._SaveUVData(cell, cell.name)

    def _SaveUVData(self, cell, cellName):
        import selectionTypes
        self.cellData[cellName] = {}
        cellData = self.cellData[cellName]
        for system in cell.systems:
            for static in system.statics:
                spawnID = cef.Spawn.GetByRecipeID(selectionTypes.replaceObjects[static].recipeID).spawnID
                cellData[spawnID] = (static.uvLinearTransform, static.uvTranslation, static.instanceInSystemIdx)

        marshalData = blue.marshal.Save(cellData)
        import CCP_P4 as p4
        import os
        fileName = blue.paths.ResolvePathForWriting(INTERIOR_RES_PATH + str(self.id) + '_' + str(cellName) + '.uv')
        p4.PrepareFileForSave(fileName)
        if not os.path.exists(blue.paths.ResolvePathForWriting(INTERIOR_RES_PATH)):
            os.makedirs(blue.paths.ResolvePathForWriting(INTERIOR_RES_PATH))
        file = open(fileName, 'wb')
        file.write(marshalData)
        file.close()
        p4.AddFilesToP4()

    def _LoadUVData(self, cellName):
        filePath = INTERIOR_RES_PATH + str(self.id) + '_' + str(cellName) + '.uv'
        if blue.paths.exists(filePath):
            file = blue.ResFile()
            file.open(filePath)
            marshalData = file.read()
            file.close()
            self.cellData[cellName] = blue.marshal.Load(marshalData)
        else:
            self.cellData[cellName] = {}

    def RemoveSkyboxTexture(self):
        self.backgroundEffect = None
        self.backgroundCubemapPath = ''

    def SetSkyboxTexture(self, texturePath):
        self.backgroundEffect = trinity.Tr2Effect()
        texture = trinity.TriTextureCubeParameter()
        texture.name = 'EnvMap1'
        texture.resourcePath = texturePath
        self.backgroundEffect.resources.append(texture)
        self.backgroundEffect.effectFilePath = 'res:/Graphics/Effect/Managed/Interior/Static/EnvironmentCubemap.fx'
        self.backgroundCubemapPath = str(texturePath)

    def GetBoundingBox(self):
        minBB = (99999999.9, 99999999.9, 99999999.9)
        maxBB = (-99999999.9, -99999999.9, -99999999.9)
        for cell in self.cells:
            minBB = geo2.Vec3Minimize(minBB, cell.minBounds)
            maxBB = geo2.Vec3Maximize(maxBB, cell.maxBounds)

        return (minBB, maxBB)
