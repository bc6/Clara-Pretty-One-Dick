#Embedded file name: trinutils\wip.py
import json
import os
try:
    import blue, trinity
except ImportError:
    blue, trinity = (None, None)

import devenv
import preferences
import qthelpers as qth
import trinutils.sceneutils as sceneutils
import trailertools.fiscontrolpanel as fcp
APPNAME = 'JessicaWIP'

def _InitPrefs(appname):
    path = devenv.GetPrefsFilename(appname, prefsname='prefs.json', makedirs=True)
    prefs = preferences.Pickled(path, dump=json.dump, load=json.load)
    return (prefs, os.path.dirname(path))


PREFS, APPPATH = _InitPrefs(APPNAME)
WIP_SCENE = os.path.join(APPPATH, 'wip.red')

def _SetupFisScene():
    trinity.settings.SetValue('frustumCullingDisabled', 1)
    sceneutils.CreateBackgroundLandscape(sceneutils.GetOrCreateScene(), 0.0001, 0.0001)
    fcp.Run()


def _SaveScene(filename):
    s2 = sceneutils.FindScene()
    if not s2:
        raise IOError(filename)
    trinity.Save(s2, filename)


def _LoadScene(filename):
    trinity.device.scene = trinity.Load(filename, nonCached=False)
    if not trinity.device.scene:
        raise IOError(filename)


def SnapshotSave(wipscene = WIP_SCENE):
    _SaveScene(wipscene)
    print 'Scene saved... %s' % wipscene


def SnapshotLoad(wipscene = WIP_SCENE, doSetupFisScene = False):
    _LoadScene(wipscene)
    if doSetupFisScene:
        _SetupFisScene()
    print 'Scene loaded... %s' % wipscene


def SceneSave():
    redfile = qth.GetSaveFileFromDialog(parent=None, caption='Save scene to .red file', filefilter='*.red', prefs=PREFS)
    if redfile:
        SnapshotSave(redfile)


def SceneLoad():
    redfile = qth.GetFileFromDialog(parent=None, caption='Load scene from .red file', filefilter='*.red', prefs=PREFS)
    if redfile:
        SnapshotLoad(redfile, doSetupFisScene=True)
