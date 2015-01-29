#Embedded file name: eveclientqatools\corpseviewer.py
import eveclientqatools.gfxpreviewer as previewer
import util
import eve.client.script.environment.spaceObject.corpse as corpse
import evespacescene

class CorpsePreviewer(previewer.AssetPreviewer):
    sources = ['graphicID', 'resPath', 'typeID']
    supportedTypes = evespacescene.EVESPACE_TRINITY_CLASSES

    def __init__(self, sceneManager):
        previewer.AssetPreviewer.__init__(self, sceneManager)

    def ShowUI(self):
        window = previewer.ToolsWindow('CorpsePreview', 'Corpse Preview')
        window.SetOnCloseHandler(self.Cleanup)
        self.SetSourceType('resPath')
        blueprint = util.KeyVal(gender=corpse.GENDER_MALE, color=corpse.COLOR_DARK, variation=0)

        def _previewSource():
            path = corpse.GetCorpsePath(blueprint.gender, blueprint.color, blueprint.variation)
            self.PreviewResource(path)

        def _gender(val):
            blueprint.gender = val
            _previewSource()

        def _color(val):
            blueprint.color = val
            _previewSource()

        def _variation(val):
            blueprint.variation = val
            _previewSource()

        buttons = previewer.ButtonRibbon()
        buttons.AddButton('Preview', _previewSource)
        buttons.AddButton('Toggle Scene Display', self._toggleHideSceneObjects)
        buttons.AddButton('Clear', self.Clear)
        window.AddComponent(buttons)
        radioGroup = previewer.RadioButtonRibbon('gender')
        radioGroup.AddButton('male', corpse.GENDER_MALE)
        radioGroup.AddButton('female', corpse.GENDER_FEMALE)
        radioGroup.SetHandler(_gender)
        window.AddComponent(radioGroup)
        radioGroup = previewer.RadioButtonRibbon('color')
        radioGroup.AddButton('dark', corpse.COLOR_DARK)
        radioGroup.AddButton('mid', corpse.COLOR_MID)
        radioGroup.AddButton('light', corpse.COLOR_LIGHT)
        radioGroup.SetHandler(_color)
        window.AddComponent(radioGroup)
        radioGroup = previewer.RadioButtonRibbon('variation')
        radioGroup.AddButton('Variation 0', 0)
        radioGroup.AddButton('Variation 1', 1)
        radioGroup.AddButton('Variation 2', 2)
        radioGroup.AddButton('Variation 3', 3)
        radioGroup.SetHandler(_variation)
        window.AddComponent(radioGroup)
        textOut = previewer.TextEditComp()
        textOut.SetText('(info)')
        self._messageFunc = textOut.SetText
        window.AddComponent(textOut)
        window.Show()
        self._toggleHideSceneObjects()
        _previewSource()
