#Embedded file name: eve/client/script/ui/services/menuSvcExtras\modelDebugFunctions.py
import uix
import log
import blue
import trinity
import eveclientqatools.blueobjectviewer as blueViewer
UNLOAD_MINIBALLS = 0
SHOW_RUNTIME_MINIBALL_DATA = 1
SHOW_EDITOR_MINIBALL_DATA = 2
SHOW_DESTINY_BALL = 3
SHOW_MODEL_SPHERE = 4
SHOW_BOUNDING_SPHERE = 5

def SaveRedFile(ball, graphicFile):
    dlgRes = uix.GetFileDialog(multiSelect=False, selectionType=uix.SEL_FOLDERS)
    if dlgRes is not None:
        path = dlgRes.Get('folders')[0]
        graphicFile = graphicFile.split('/')[-1]
        graphicFile = graphicFile.replace('.blue', '.red')
        savePath = path + '\\' + graphicFile
        trinity.Save(ball.model, savePath)
        log.LogError('GM menu: Saved object as:', savePath)


def GetGMModelInfoMenuItem(itemID = None):

    def GetModelHandler(*args):
        model = sm.StartService('michelle').GetBall(itemID).GetModel()
        blueViewer.Show(model)

    return ('Inspect model', GetModelHandler, (None,))


def GetGMBallsAndBoxesMenu(itemID = None, *args, **kwargs):
    spaceMgr = sm.StartService('space')
    partMenu = [('Stop partition box display ', spaceMgr.StopPartitionDisplayTimer, ()),
     None,
     ('Start partition box display limit = 0', spaceMgr.StartPartitionDisplayTimer, (0,)),
     ('Start partition box display limit = 1', spaceMgr.StartPartitionDisplayTimer, (1,)),
     ('Start partition box display limit = 2', spaceMgr.StartPartitionDisplayTimer, (2,)),
     ('Start partition box display limit = 3', spaceMgr.StartPartitionDisplayTimer, (3,)),
     ('Start partition box display limit = 4', spaceMgr.StartPartitionDisplayTimer, (4,)),
     ('Start partition box display limit = 5', spaceMgr.StartPartitionDisplayTimer, (5,)),
     ('Start partition box display limit = 6', spaceMgr.StartPartitionDisplayTimer, (6,)),
     ('Start partition box display limit = 7', spaceMgr.StartPartitionDisplayTimer, (7,)),
     None,
     ('Show single level', ChangePartitionLevel, (0,)),
     ('Show selected level and up', ChangePartitionLevel, (1,))]
    subMenu = [('Balls & Boxes', [('Hide ball info', ShowDestinyBalls, (itemID, UNLOAD_MINIBALLS)),
       ('Show Miniball Runtime Data', ShowDestinyBalls, (itemID, SHOW_RUNTIME_MINIBALL_DATA)),
       ('Show Miniball Editor Data', ShowDestinyBalls, (itemID, SHOW_EDITOR_MINIBALL_DATA)),
       None,
       ('Wireframe Destiny Ball', ShowDestinyBalls, (itemID, SHOW_DESTINY_BALL)),
       ('Wireframe BoundingSphere', ShowDestinyBalls, (itemID, SHOW_BOUNDING_SPHERE)),
       None,
       ('Partition', partMenu)]), ('Damage Locators', [('Toggle damage locators', ShowDamageLocators, (itemID,))])]
    return subMenu


def ChangePartitionLevel(level):
    settings.user.ui.Set('partition_box_showall', level)


def ShowDestinyBalls(itemID, showType):
    miniballObject = None
    scene = sm.GetService('sceneManager').GetRegisteredScene('default')
    nameOfMiniballs = 'miniballs_of_' + str(itemID)
    for each in scene.objects:
        if each.name == nameOfMiniballs:
            miniballObject = each
            break

    if miniballObject is not None:
        scene.objects.remove(miniballObject)
    if miniballObject and showType == UNLOAD_MINIBALLS:
        return
    ballpark = sm.StartService('michelle').GetBallpark()
    ball = ballpark.GetBall(itemID)
    if showType == SHOW_RUNTIME_MINIBALL_DATA:
        graphicObject = CreateMiniballObject(nameOfMiniballs, ball.miniBalls)
        graphicObject.translationCurve = ball
        graphicObject.rotationCurve = ball
        scene.objects.append(graphicObject)
    elif showType == SHOW_DESTINY_BALL:
        graphicObject = CreateRadiusObject(nameOfMiniballs, ball.radius)
        graphicObject.translationCurve = ball
        scene.objects.append(graphicObject)
    elif showType == SHOW_BOUNDING_SPHERE:
        graphicObject = CreateRadiusObject(nameOfMiniballs, ball.model.GetBoundingSphereRadius())
        pos = ball.model.GetBoundingSphereCenter()
        graphicObject.translation = (pos[0], pos[1], pos[2])
        graphicObject.translationCurve = ball
        scene.objects.append(graphicObject)


def ShowDamageLocators(itemID):
    ball = sm.StartService('michelle').GetBallpark().GetBall(itemID)
    ship = ball.model
    if not ship:
        return
    if getattr(ball, 'visualizingDamageLocators', False):
        toRemove = []
        for child in ship.children:
            if child.name == 'DamageLocatorVisualization':
                toRemove.append(child)
            elif child.name == 'ImpactDirectionVisualization':
                toRemove.append(child)

        for tr in toRemove:
            ship.children.remove(tr)

        setattr(ball, 'visualizingDamageLocators', False)
    else:
        scale = ship.boundingSphereRadius / 10
        for i in range(len(ship.damageLocators)):
            damageLocator = ship.damageLocators[i]
            sphere = trinity.Load('res:/model/global/damageLocator.red')
            sphere.translation = damageLocator[0]
            sphere.scaling = [scale, scale, scale]
            ship.children.append(sphere)
            impacDir = damageLocator[1]
            direction = trinity.Load('res:/model/global/impactDirection.red')
            direction.translation = damageLocator[0]
            direction.scaling = [scale, scale, scale]
            direction.rotation = impacDir
            ship.children.append(direction)

        setattr(ball, 'visualizingDamageLocators', True)


def CreateMiniballObject(name, miniballs):
    t = trinity.EveRootTransform()
    sphere = blue.resMan.LoadObject('res:/Model/Global/Miniball.red')
    if len(miniballs) > 0:
        for miniball in miniballs:
            mball = sphere.CopyTo()
            mball.translation = (miniball.x, miniball.y, miniball.z)
            r = miniball.radius * 2
            mball.scaling = (r, r, r)
            t.children.append(mball)

    t.name = name
    return t


def CreateRadiusObject(name, radius):
    t = trinity.EveRootTransform()
    t.name = name
    s = blue.resMan.LoadObject('res:/model/global/gridSphere.red')
    radius = radius * 2
    s.scaling = (radius, radius, radius)
    t.children.append(s)
    return t
