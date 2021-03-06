#Embedded file name: carbon/client/script/world\gameWorldClient.py
import GameWorld

class GameWorldClient(GameWorld.GameWorldService):
    __guid__ = 'svc.gameWorldClient'

    def Run(self, *etc):
        GameWorld.GameWorldService.Run(self)

    def GetGameWorldType(self):
        return GameWorld.GameWorldClient

    def OnLoadEntityScene(self, sceneID):
        GameWorld.GameWorldService.OnLoadEntityScene(self, sceneID)
