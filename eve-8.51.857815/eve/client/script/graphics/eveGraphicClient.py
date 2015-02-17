#Embedded file name: eve/client/script/graphics\eveGraphicClient.py
"""
Adds functionality to the core graphic client.
Adds rendering scene to gameUI
"""
import blue
import svc
from sceneManager import SCENE_TYPE_INTERIOR

class EveGraphicClient(svc.graphicClient):
    __guid__ = 'svc.eveGraphicClient'
    __replaceservice__ = 'graphicClient'
    __dependencies__ = svc.graphicClient.__dependencies__[:]

    def _AppSetRenderingScene(self, scene):
        """
        Adds the scene to the renderjob
        """
        sceneManager = sm.GetService('sceneManager')
        sceneManager.SetSceneType(SCENE_TYPE_INTERIOR)
        sceneManager.SetActiveScene(scene)
