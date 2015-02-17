#Embedded file name: iconrendering\camera_util.py
"""
The methods here are copied verbatim from the corified photo service.
"""
import geo2
import trinity
from math import sin, tan
GETPHOTO_ANGLE = (0.3, -0.3, 0.0)
GETPHOTO_VIEW_UP = (0.0, 1.0, 0.0)
GETPHOTO_FOV = 1.0
GETPHOTO_BACKCLIP = 500000.0
GETPHOTO_PROJECTION = (GETPHOTO_FOV,
 1.0,
 1.0,
 GETPHOTO_BACKCLIP)

def _GetViewMatrixFromAngle(cameraAngle, lookAt, cameraDistance):
    """
    Given a LookAt point, camera distance and direction (angle), return
    a (view_eye, view_at, view_up) tuple of geo2.Vectors
    """
    view_at = geo2.Vector(lookAt[0], lookAt[1], lookAt[2])
    view_eye = geo2.Vector(0.0, 0.0, 1.0)
    angleTransform = geo2.MatrixRotationYawPitchRoll(cameraAngle[0], cameraAngle[1], cameraAngle[2])
    view_eye = geo2.Vec3TransformCoord(view_eye, angleTransform)
    view_eye = geo2.Vector(*view_eye)
    view_eye = view_eye * cameraDistance + view_at
    return (view_eye, view_at, geo2.Vector(*GETPHOTO_VIEW_UP))


def _SphericalFit(radius, fov = GETPHOTO_FOV, fudge = 1.15):
    """
    Given a radius, calculate at what distance the camera needs to be, to fit the
    whole sphere in it's field of view.
    """
    alpha = fov / 2.0
    return radius / sin(alpha) * fudge


def _GetViewAndProjectionUsingProjectedBoundingBox(calculateProjectedBoundingBox, scene = None, boundingSphereRadius = None, boundingSphereCenter = None, boundingBoxMin = None, boundingBoxMax = None, cameraAngle = None):
    """
    Fits an object in frame with view and projection matrices. We first do a rough fit
    using either the bounding sphere or bounding box. We then "zoom in" to the point where
    the projected bounding box fills 90% of the image.
    """
    cameraAngle = cameraAngle or GETPHOTO_ANGLE
    if boundingSphereRadius:
        radius = boundingSphereRadius
        center = boundingSphereCenter if boundingSphereCenter else (0.0, 0.0, 0.0)
    else:
        center = geo2.Vec3Add(boundingBoxMin, boundingBoxMax)
        center = geo2.Vec3Scale(center, 0.5)
        radius = geo2.Vec3Length(geo2.Vec3Subtract(boundingBoxMax, boundingBoxMin))
    dist = _SphericalFit(radius)
    viewEyeAtUp = _GetViewMatrixFromAngle(cameraAngle, center, dist)
    projTransform = geo2.MatrixPerspectiveFovRH(*GETPHOTO_PROJECTION)
    viewTransform = geo2.MatrixLookAtRH(*viewEyeAtUp)
    combinedTransform = viewTransform
    combinedTransform = geo2.MatrixMultiply(combinedTransform, projTransform)
    safeMin, safeMax = calculateProjectedBoundingBox(combinedTransform)
    deltaX = safeMax[0] - safeMin[0]
    deltaY = safeMax[1] - safeMin[1]
    scalingFactor = 0.9 * (2.0 / max(deltaX, deltaY))
    try:
        if scene.backgroundEffect is not None:
            params = scene.backgroundEffect.Find(['trinity.Tr2FloatParameter'])
            for param in params:
                if param.name == 'ProjectionScaling':
                    param.value = scalingFactor

    except AttributeError:
        pass

    offsetX = -1 * scalingFactor * (safeMin[0] + safeMax[0]) / 2.0
    offsetY = -1 * scalingFactor * (safeMin[1] + safeMax[1]) / 2.0
    scale = 1.0 / tan(GETPHOTO_FOV / 2.0) * scalingFactor
    zn = 1.0
    zf = dist + radius * 2
    t = zn * (1 - offsetY) / scale
    b = -t * (1 + offsetY) / (1 - offsetY)
    r = zn * (1 - offsetX) / scale
    l = -r * (1 + offsetX) / (1 - offsetX)
    projection = trinity.TriProjection()
    projection.PerspectiveOffCenter(l, r, b, t, zn, zf)
    view = trinity.TriView()
    view.SetLookAtPosition(*viewEyeAtUp)
    return (view, projection)


def GetViewAndProjectionUsingMeshGeometry(geometry, geometryMeshIdx = 0, scene = None, boundingSphereRadius = None, boundingSphereCenter = None, boundingBoxMin = None, boundingBoxMax = None, cameraAngle = None):
    """
    Fits an object in frame with view and projection matrices. The camera will "zoom in"
    to the tightest possible fit of the model's mesh. Needs either bounding sphere or
    bounding box information as a basis to work from. Bounding Sphere is preferred (see
    comments in source code for a better explanation).
    """

    def calculateProjectedBoundingBox(combinedTransform):
        """
        Project each vertex in the mesh to screen space and calculate it's
        projected bounding box
        """
        return geometry.CalculateBoundingBoxFromTransform(geometryMeshIdx, combinedTransform)

    return _GetViewAndProjectionUsingProjectedBoundingBox(calculateProjectedBoundingBox, scene, boundingSphereRadius=boundingSphereRadius, boundingSphereCenter=boundingSphereCenter, boundingBoxMin=boundingBoxMin, boundingBoxMax=boundingBoxMax, cameraAngle=cameraAngle)


def GetViewAndProjectionUsingBoundingBox(boundingBoxMin = None, boundingBoxMax = None, scene = None, cameraAngle = None):
    """
    Fits an object in frame with view and projection matrices. The picture will be
    focused on the bounding box' center and the camera will "zoom in" to the tightest
    possible bounding box fit.
    """

    def calculateProjectedBoundingBox(combinedTransform):
        """
        Project each vertex in the bounding box to screen space and calculate
        it's projected bounding box
        """
        edges = []
        edges.append(geo2.Vector(boundingBoxMin[0], boundingBoxMin[1], boundingBoxMin[2]))
        edges.append(geo2.Vector(boundingBoxMin[0], boundingBoxMin[1], boundingBoxMax[2]))
        edges.append(geo2.Vector(boundingBoxMin[0], boundingBoxMax[1], boundingBoxMin[2]))
        edges.append(geo2.Vector(boundingBoxMin[0], boundingBoxMax[1], boundingBoxMax[2]))
        edges.append(geo2.Vector(boundingBoxMax[0], boundingBoxMin[1], boundingBoxMin[2]))
        edges.append(geo2.Vector(boundingBoxMax[0], boundingBoxMin[1], boundingBoxMax[2]))
        edges.append(geo2.Vector(boundingBoxMax[0], boundingBoxMax[1], boundingBoxMin[2]))
        edges.append(geo2.Vector(boundingBoxMax[0], boundingBoxMax[1], boundingBoxMax[2]))
        for i, edge in enumerate(edges):
            edge = geo2.Vector(*geo2.Vec3TransformCoord(edge, combinedTransform))
            if i == 0:
                safeMin = geo2.Vector(*edge)
                safeMax = geo2.Vector(*edge)
            else:
                safeMin.x = min(safeMin.x, edge[0])
                safeMin.y = min(safeMin.y, edge[1])
                safeMin.z = min(safeMin.z, edge[2])
                safeMax.x = max(safeMax.x, edge[0])
                safeMax.y = max(safeMax.y, edge[1])
                safeMax.z = max(safeMax.z, edge[2])

        return (safeMin, safeMax)

    return _GetViewAndProjectionUsingProjectedBoundingBox(calculateProjectedBoundingBox, scene, boundingBoxMin=boundingBoxMin, boundingBoxMax=boundingBoxMax, cameraAngle=cameraAngle, boundingSphereRadius=None, boundingSphereCenter=None)


def GetViewAndProjectionUsingBoundingSphere(boundingSphereRadius, boundingSphereCenter = None, cameraAngle = None, distanceOverride = None, fov = GETPHOTO_FOV):
    """
    Returns view and projection matrices that frame the bounding sphere.
    """
    cameraAngle = cameraAngle or GETPHOTO_ANGLE
    boundingSphereCenter = boundingSphereCenter or (0.0, 0.0, 0.0)
    dist = distanceOverride if distanceOverride else _SphericalFit(boundingSphereRadius, fov)
    projection = trinity.TriProjection()
    projection.PerspectiveFov(fov, 1.0, 1.0, GETPHOTO_BACKCLIP)
    view = trinity.TriView()
    view.SetLookAtPosition(*_GetViewMatrixFromAngle(cameraAngle, boundingSphereCenter, dist))
    return (view, projection)
