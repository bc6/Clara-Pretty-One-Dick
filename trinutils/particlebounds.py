#Embedded file name: trinutils\particlebounds.py
import logging
import greatergranny.grannyutils as grannyutils
import remotefilecache
import uthread2 as ut
import trinutils.trinparser as trinparser
import yamlext
try:
    import blue
    import trinity
    import geo2
except ImportError:
    trinity = None
    blue = None
    geo2 = None

logger = logging.getLogger(__name__)

def YamlStrToTrinObj(yamlstr):
    """Returns a trinity object loaded from a yaml string and does some other
    cargo cult stuff (waits for resource loads,
    tests prune/pop on tr2effects, etc.)."""
    trinobj = trinparser.DictToTrinityParser(yamlext.loads(yamlstr))
    trinity.WaitForResourceLoads()
    return trinobj


class MeshLoadError(Exception):

    def __init__(self, meshpath):
        msg = 'Mesh failed to load: %s' % meshpath
        Exception.__init__(self, msg)


def HasParticleSystem(node):
    psys = node.Find('trinity.Tr2ParticleSystem')
    if psys:
        return True
    return False


def _GetMaxPartSize(et):
    if not et.mesh.geometry.isGood:
        raise MeshLoadError(et.mesh.geometryResPath)
    geoSize = et.mesh.geometry.GetBoundingBox(0)
    gs = geo2.Vec3Distance(geoSize[0], geoSize[1])
    for em in et.Find('trinity.Tr2DynamicEmitter'):
        for each in em.generators:
            if each.name == 'sizeDynamic' or each.name == 'size':
                return max(each.minRange + each.maxRange) * gs

    for em in et.Find('trinity.Tr2StaticEmitter'):
        for ps in em.Find('trinity.Tr2ParticleSystem'):
            for each in ps.elements:
                if each.name == 'size':
                    remotefilecache.prefetch_single_file(em.geometryResourcePath)
                    return grannyutils.GetMaxPartSize(blue.paths.ResolvePath(em.geometryResourcePath), each.usageIndex, em.meshIndex) * gs

    logger.warning('No Particle Emitters found for %s' % et.name)


class ParticleBoundsSimulation(object):

    def __init__(self, trinobj, pumpBlue = False, passes = 2, time = 3.0):
        trinity.WaitForResourceLoads()
        self._passes = passes
        self._time = time
        self.redNodeMutated = trinobj.CopyTo()
        self.redNodeCopy = trinobj.CopyTo()
        self.systems = self.redNodeMutated.Find('trinity.Tr2ParticleSystem')
        self.curveSets = self.redNodeMutated.Find('trinity.TriCurveSet')
        self.activeIndex = [0]
        self._ets = []
        self.started = [False]
        self._pumpBlue = pumpBlue
        self._CollectMeshes()

    def _CollectMeshes(self):

        def _FilterMesh(et):
            return isinstance(et.mesh, trinity.Tr2InstancedMesh) and ('unit_plane' or 'unitplane' in et.mesh.geometryResPath)

        def _CollectTransforms(tf, indices):
            if _FilterMesh(tf):
                self._ets.append({'et': tf,
                 'mesh': tf.mesh,
                 'min': (0.0, 0.0, 0.0),
                 'max': (0.0, 0.0, 0.0),
                 'partSize': _GetMaxPartSize(tf) / 2,
                 'hierarchy': indices})
            for ci in range(len(tf.children)):
                child = tf.children[ci]
                clst = list(indices)
                clst.append(ci)
                _CollectTransforms(child, clst)

        for ci in range(len(self.redNodeMutated.children)):
            child = self.redNodeMutated.children[ci]
            _CollectTransforms(child, [ci])

    def GetTrinobj(self):
        self.RunSimulation()
        self.FixPSBB()
        self._UpdateBoundingBox(False)
        return self.redNodeCopy

    def _PumpBlue(self):
        while self._pumpBlue:
            blue.os.Pump()
            ut.Yield()

    def _UpdateBoundingBox(self, update, sorting = True):
        for ps in self.systems:
            ps.updateBoundingBox = update
            ps.requiresSorting = sorting

    def _GetRedNodeCopyTransform(self, transformEntry):
        indices = transformEntry['hierarchy']
        tf = self.redNodeCopy
        for i in indices:
            tf = tf.children[i]

        return tf

    def FixPSBB(self):
        for d in self._ets:
            mps = d['partSize']
            tf = self._GetRedNodeCopyTransform(d)
            tf.mesh.minBounds = [d['min'][0] - mps, d['min'][1] - mps, d['min'][2] - mps]
            tf.mesh.maxBounds = [d['max'][0] + mps, d['max'][1] + mps, d['max'][2] + mps]

    def AccumulateBounds(self):
        for d in self._ets:
            ps = d['mesh'].instanceGeometryResource
            d['max'] = max(ps.aabbMax, d['max'])
            d['min'] = min(ps.aabbMin, d['min'])

    def RunSimulation(self):
        trinity.settings.SetValue('frustumCullingDisabled', 1)
        trinity.settings.SetValue('eveSpaceSceneVisibilityThreshold', 0)
        trinity.settings.SetValue('eveSpaceSceneLowDetailThreshold', 0)
        trinity.settings.SetValue('eveSpaceSceneMediumDetailThreshold', 0)
        ut.StartTasklet(self._PumpBlue)
        import sceneutils
        scene = sceneutils.GetOrCreateScene()
        scene.objects.append(self.redNodeMutated)
        self._UpdateBoundingBox(True)
        rj = trinity.CreateRenderJob('CallbackJob')
        projection = trinity.TriProjection()
        projection.PerspectiveFov(1, 1, 1, 10000000)
        rj.steps.append(trinity.TriStepSetProjection(projection))
        view = trinity.TriView()
        view.SetLookAtPosition((50000, 0, 0), (0, 0, 0), (0, 1, 0))
        rj.steps.append(trinity.TriStepSetView(view))
        rj.steps.append(trinity.TriStepUpdate(scene))
        rj.steps.append(trinity.TriStepRenderScene(scene))
        rj.steps.append(trinity.TriStepPythonCB(self.AccumulateBounds))
        rj.ScheduleRecurring()
        for i in range(self._passes):
            self.activeIndex[0] = i
            for cs in self.curveSets:
                cs.Play()

            for sys in self.systems:
                sys.ClearParticles()

            self.started[0] = True
            ut.SleepSim(self._time)

        rj.UnscheduleRecurring()
        self._pumpBlue = False
