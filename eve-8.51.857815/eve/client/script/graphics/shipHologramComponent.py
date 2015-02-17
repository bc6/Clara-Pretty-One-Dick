#Embedded file name: eve/client/script/graphics\shipHologramComponent.py
import service
import trinity
import util
import geo2

class ShipHologramComponent:
    """
        Client-side ship hologram CEF component.
    """
    __guid__ = 'component.shipHologram'

    def __init__(self):
        self.positionOffset = (0, 0.7, 0)
        self.spotlightOrigin = (0, 0.05, 0)
        self.color = (1, 0.7, 0.5)
        self.shipTargetSize = 0.5
        self.graphicLoaded = False


class ShipHologramComponentManager(service.Service):
    """
        Client-side ship hologram CEF component factory.
    """
    __guid__ = 'svc.shipHologram'
    __displayname__ = 'Ship Hologram Component Client Service'
    __componentTypes__ = ['shipHologram']
    __notifyevents__ = ['OnActiveShipModelChange', 'ProcessActiveShipChanged']
    __dependencies__ = []

    def __init__(self):
        service.Service.__init__(self)
        self.entities = []

    def Run(self, *etc):
        service.Service.Run(self, *etc)
        self.activeShipModel = None
        self.activeShipID = None

    def CreateComponent(self, name, state):
        """
            Creates ship hologram component from the given state.
        """
        component = ShipHologramComponent()
        if 'positionOffset' in state:
            component.positionOffset = util.UnpackStringToTuple(state['positionOffset'])
        if 'spotlightOrigin' in state:
            component.spotlightOrigin = util.UnpackStringToTuple(state['spotlightOrigin'])
        if 'color' in state:
            component.color = util.UnpackStringToTuple(state['color'])
        if 'shipTargetSize' in state:
            component.shipTargetSize = state['shipTargetSize']
        return component

    def PrepareComponent(self, sceneID, entityID, component):
        """
            Gets called in order to prepare a component. No other components can be referred to
        """
        pass

    def SetupComponent(self, entity, component):
        """
            Gets called in order to setup a component. All other components can be referred to
        """
        interiorPlaceableComponent = entity.GetComponent('interiorPlaceable')
        hologramComponent = entity.GetComponent('shipHologram')
        if interiorPlaceableComponent is not None and hologramComponent is not None:
            hologramComponent.graphicLoaded = True
            self.SetShipModel(entity)

    def RegisterComponent(self, entity, component):
        """
            Gets called in order to register a component. The component can be searched for prior to this point.
        """
        self.entities.append(entity)

    def UnRegisterComponent(self, entity, component):
        """
            Unregisters ship hologram component: removes trinity object from the scene.
        """
        self.entities.remove(entity)
        hologramComponent = entity.GetComponent('shipHologram')
        if hologramComponent is None or not hologramComponent.graphicLoaded:
            return
        interiorPlaceable = entity.GetComponent('interiorPlaceable')
        if interiorPlaceable is None:
            return
        visualModel = interiorPlaceable.renderObject.placeableRes.visualModel
        if visualModel is None:
            return
        for each in visualModel.meshes:
            if each.name == 'shipHologramMesh':
                visualModel.meshes.remove(each)
                break

    def UpdateShipModels(self, shipModel, activeShipID = None):
        if activeShipID is None:
            activeShipID = util.GetActiveShip()
        self.activeShipModel = shipModel
        self.activeShipID = activeShipID
        for each in self.entities:
            self.SetShipModel(each)

    def CalculateModelScale(self, component, boundingRadius, shipID):
        scale = component.shipTargetSize / boundingRadius
        extraScaling = 1.0
        if boundingRadius > 1000.0:
            boundingRadius = 1000.0
        if boundingRadius < 30.0:
            boundingRadius = 30.0
        scale *= 0.6 + 0.4 * boundingRadius / 970.0
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        if getattr(dogmaLocation.GetDogmaItem(shipID), 'groupID', None) == const.groupCapsule:
            extraScaling = 0.6
        return (scale, extraScaling)

    def SetShipModel(self, entity):
        hologramComponent = entity.GetComponent('shipHologram')
        if hologramComponent is None or not hologramComponent.graphicLoaded:
            return
        interiorPlaceable = entity.GetComponent('interiorPlaceable')
        if interiorPlaceable is None:
            return
        effect = trinity.Load('res:/graphics/interior/effect/hologram/shipHologramEffect.red')
        targetPlaceable = interiorPlaceable.renderObject
        targetPlaceable.isUnique = True
        targetPlaceable.BindLowLevelShaders()
        targetVisual = targetPlaceable.placeableRes.visualModel
        mesh = None
        for each in targetVisual.meshes:
            if each.name == 'shipHologramMesh':
                mesh = each
                break

        if mesh is not None:
            targetVisual.meshes.remove(mesh)
        targetPlaceable.BoundingBoxReset()
        if self.activeShipModel is None:
            return
        if self.activeShipID is None:
            return
        mesh = trinity.Tr2Mesh()
        mesh.name = 'shipHologramMesh'
        mesh.geometryResPath = self.activeShipModel.mesh.GetGeometryResPath()
        maxIndex = 0
        for area in self.activeShipModel.mesh.opaqueAreas:
            maxIndex = max(maxIndex, area.index)

        for area in self.activeShipModel.mesh.decalAreas:
            maxIndex = max(maxIndex, area.index)

        for area in self.activeShipModel.mesh.transparentAreas:
            maxIndex = max(maxIndex, area.index)

        meshArea = trinity.Tr2MeshArea()
        meshArea.effect = effect
        meshArea.count = maxIndex + 1
        mesh.transparentAreas.append(meshArea)
        effect.BindLowLevelShader([])
        bbMinOriginal, bbMaxOriginal = targetVisual.GetBoundingBoxInLocalSpace()
        scale, extra = self.CalculateModelScale(hologramComponent, self.activeShipModel.boundingSphereRadius, self.activeShipID)
        param = effect.parameters['ScalingAndOffset']
        x = param.x = hologramComponent.positionOffset[0]
        y = param.y = hologramComponent.positionOffset[1]
        z = param.z = hologramComponent.positionOffset[2]
        param.w = scale * extra
        param = effect.parameters['Color']
        param.x = hologramComponent.color[0]
        param.y = hologramComponent.color[1]
        param.z = hologramComponent.color[2]
        param = effect.parameters['SpotlightOrigin']
        param.x = hologramComponent.spotlightOrigin[0]
        param.y = hologramComponent.spotlightOrigin[1]
        param.z = hologramComponent.spotlightOrigin[2]
        targetVisual.meshes.append(mesh)
        trinity.WaitForResourceLoads()
        bbMin, bbMax = self.activeShipModel.GetLocalBoundingBox()
        maxBounds = max(abs(bbMin[0]), max(bbMax[0], max(abs(bbMin[2]), bbMax[2])))
        bbMin = (-maxBounds, bbMin[2], -maxBounds)
        bbMax = (maxBounds, bbMax[2], maxBounds)
        bbMin = geo2.Vec3Scale(bbMin, scale)
        bbMax = geo2.Vec3Scale(bbMax, scale)
        bbMin = geo2.Vec3Add(bbMin, (x, y, z))
        bbMax = geo2.Vec3Add(bbMax, (x, y, z))
        bbMin = geo2.Min(bbMin, bbMinOriginal)
        bbMax = geo2.Max(bbMax, bbMaxOriginal)
        targetPlaceable.BoundingBoxOverride(bbMin, bbMax)

    def OnActiveShipModelChange(self, model, shipID):
        self.UpdateShipModels(model, shipID)

    def ProcessActiveShipChanged(self, shipID, oldShipID):
        self.activeShipID = shipID
        self.activeShipModel = None
