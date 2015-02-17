#Embedded file name: eve/devtools/script\cycleNebulaPanel.py
import uicontrols
import uiprimitives
import carbonui.const as uiconst
import walk
import os
NEBULA_RES_PATH = 'res:/dx9/scene/universe/'
PANEL_HEIGHT = 150
PANEL_WIDTH = 250

class CycleNebulaPanel(uicontrols.Window):
    default_width = PANEL_WIDTH
    default_height = PANEL_HEIGHT
    default_minSize = (default_width, default_height)
    default_maxSize = (default_width, default_height)

    def ApplyAttributes(self, attributes):
        super(CycleNebulaPanel, self).ApplyAttributes(attributes)
        self.sr.topParent.height = 0
        parent = self.GetMainArea()
        parent.SetAlign(uiconst.CENTER)
        parent.padding = 5
        parent.SetSize(PANEL_WIDTH, PANEL_HEIGHT)
        self.nebulaPaths = []
        self.currentNebulaIndex = 0
        self.currentNebulaPath = None
        self.sceneResourceIndex = 0
        self.SetupNebulas()
        topCont = uiprimitives.Container(parent=parent, align=uiconst.TOALL, top=30)
        self.currentNebulaPathLabel = uicontrols.Label(parent=topCont, text='Current nebula: ', align=uiconst.TOTOP)
        self.comboBox = uicontrols.Combo(name='nebulaComboBox', parent=topCont, label='', options=[ (nebulaPath, index) for index, nebulaPath in enumerate(self.nebulaPaths) ], callback=self.ComboboxSelection, select=self.currentNebulaIndex, align=uiconst.TOTOP)
        self.nextNebulaButton = uicontrols.Button(parent=topCont, label='Next', align=uiconst.CENTERRIGHT, func=self.IncrementNebulaIndex)
        self.prevNebulaButton = uicontrols.Button(parent=topCont, label='Previous', align=uiconst.CENTERLEFT, func=self.DecrementNebulaIndex)

    def SetupNebulas(self):
        res = walk.walk(NEBULA_RES_PATH)
        for dirpath, dirnames, filenames in res:
            for filename in filenames:
                if not filename.lower().endswith(('_blur.dds', '_refl.dds')):
                    if '.dds' in filename.lower():
                        resPath = os.path.join(dirpath, filename).replace('\\', '/')
                        self.nebulaPaths.append(str(resPath.lower()))

        scene = sm.GetService('sceneManager').GetActiveScene()
        for i, resource in enumerate(scene.backgroundEffect.resources):
            if resource.name == 'NebulaMap':
                self.currentNebulaPath = resource.resourcePath.replace('\\', '/')
                self.sceneResourceIndex = i
                break

        if self.currentNebulaPath is not None:
            self.currentNebulaIndex = self.nebulaPaths.index(self.currentNebulaPath)

    def IncrementNebulaIndex(self, args):
        self.currentNebulaIndex = (self.currentNebulaIndex + 1) % len(self.nebulaPaths)
        self.SetNebulaOnScene()

    def DecrementNebulaIndex(self, args):
        self.currentNebulaIndex = (self.currentNebulaIndex - 1) % len(self.nebulaPaths)
        self.SetNebulaOnScene()

    def ComboboxSelection(self, boBox, key, value):
        self.currentNebulaIndex = value
        self.SetNebulaOnScene()

    def SetNebulaOnScene(self):
        self.currentNebulaPath = self.nebulaPaths[self.currentNebulaIndex]
        self.comboBox.SetValue(self.currentNebulaIndex)
        scene = sm.GetService('sceneManager').GetActiveScene()
        scene.backgroundEffect.resources[self.sceneResourceIndex].resourcePath = self.currentNebulaPath
        scene.envMapResPath = self.currentNebulaPath[:-4] + '_refl.dds'
        scene.envMap1ResPath = self.currentNebulaPath
        scene.envMap2ResPath = self.currentNebulaPath[:-4] + '_blur.dds'
