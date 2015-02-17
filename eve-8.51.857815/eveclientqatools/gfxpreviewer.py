#Embedded file name: eveclientqatools\gfxpreviewer.py
import trinity
import uicontrols
import uiprimitives
import carbonui.const as uiconst
import evespacescene

class ToolsWindow(object):

    def __init__(self, name, caption):
        self._name = name
        self._windowID = 'ToolsWindow_ ' + name
        self._components = []
        self._caption = caption
        self._minWidth = 340
        self._onCloseHandler = None

    def SetCaption(self, caption):
        self._caption = caption

    def AddComponent(self, component):
        self._components.append(component)

    def Show(self):
        uicontrols.Window.CloseIfOpen(windowID=self._windowID)
        wnd = uicontrols.Window.Open(windowID=self._windowID)
        wnd.SetTopparentHeight(0)
        wnd.SetMinSize([self._minWidth, 100])
        wnd.SetCaption(self._caption)
        wnd._OnClose = self._OnClose
        main = wnd.GetMainArea()
        for i in range(len(self._components)):
            height = self._components[i].GetHeight()
            cont = uiprimitives.Container(parent=main, align=uiconst.TOTOP, height=height, padTop=0)
            compName = self._windowID + '_comp' + str(i)
            self._components[i].Show(cont, compName, self._windowID)

    def SetOnCloseHandler(self, handler):
        self._onCloseHandler = handler

    def _OnClose(self):
        if self._onCloseHandler is not None:
            self._onCloseHandler()


class ReportComponent(object):

    def __init__(self):
        self._height = 20
        self._alignment = uiconst.TOLEFT

    def SetHeight(self, height):
        self._height = height

    def GetHeight(self):
        return self._height

    def Show(self, parent, name, windowID):
        pass


class RadioButtonRibbon(ReportComponent):

    def __init__(self, groupID = 'radioGroup', itemWidth = 200):
        ReportComponent.__init__(self)
        self.buttons = []
        self.eventFunction = None
        self.SetHeight(20)
        self._itemWidth = itemWidth
        self._groupID = groupID

    def AddButton(self, text, id):
        self.buttons.append((text, id))

    def Show(self, parent, name, windowID):
        first = True
        for text, id in self.buttons:
            uicontrols.Checkbox(parent=parent, text=text, groupname=self._groupID, align=self._alignment, checked=first, callback=self._radioButtonsChanged, retval=id, width=self._itemWidth)
            first = False

    def SetHandler(self, function):
        self.eventFunction = function

    def _radioButtonsChanged(self, button):
        id = button.data['value']
        if self.eventFunction is not None:
            self.eventFunction(id)


class TextEditComp(ReportComponent):

    def __init__(self):
        ReportComponent.__init__(self)
        self._handler = None
        self._textBox = None
        self._text = ''

    def SetHandler(self, handler):
        self._handler = handler

    def SetText(self, text):
        self._text = text
        if self._textBox is not None:
            self._textBox.SetValue(unicode(text))

    def _textChanged(self, text):
        self._text = text
        if self._handler is not None:
            self._handler(text)

    def Show(self, parent, name, windowID):
        self._textBox = uicontrols.SinglelineEdit(parent=parent, align=self._alignment, OnChange=self._textChanged, setvalue=self._text, width=300)


class ButtonRibbon(ReportComponent):

    def __init__(self):
        ReportComponent.__init__(self)
        self.buttons = []
        self.buttonHandlers = {}
        self.SetHeight(20)

    def AddButton(self, text, handler):
        self.buttons.append((text, handler))
        self.buttonHandlers[text] = handler

    def _buttonEvent(self, *args):
        button, = args
        eventFunction = self.buttonHandlers[button.name]
        if eventFunction is not None:
            eventFunction()

    def _createButton(self, container, text):
        uicontrols.Button(parent=container, align=self._alignment, label=text, name=text, func=self._buttonEvent)

    def Show(self, parent, name, windowID):
        for text, eventFun in self.buttons:
            self._createButton(parent, text)


class RowContainer(ReportComponent):

    def __init__(self):
        ReportComponent.__init__(self)
        self.items = []

    def AddComponent(self, component):
        self.items.append(component)

    def Show(self, parent, name, windowID):
        for item in self.items:
            item.Show(parent, name, windowID)


class AssetPreviewer(object):
    sources = ['graphicID', 'resPath', 'typeID']
    supportedTypes = evespacescene.EVESPACE_TRINITY_CLASSES

    def __init__(self, sceneManager):
        self._sceneManager = sceneManager
        self.sourceType = 'graphicID'
        self.graphicID = -1
        self.typeID = -1
        self.resPath = ''
        self.resource = None
        self._displayObjects = True
        self._messageFunc = None

    def Clear(self):
        self.graphicID = -1
        self.typeID = -1
        self.resPath = ''
        if self.resource is not None:
            scene = self._sceneManager.GetRegisteredScene('default')
            scene.objects.fremove(self.resource)
            self.resource = None

    def _getResourceFromTypeID(self, typeID):
        invType = cfg.invtypes.Get(typeID)
        graphicID = getattr(invType, 'graphicID', None)
        if graphicID is None:
            self._showMessage('Could not get graphicID from typeID ' + str(typeID))
            return
        return self._getResourceFromGraphicID(graphicID)

    def _getResourceFromGraphicID(self, graphicID):
        graphicInfo = cfg.graphics.GetIfExists(graphicID)
        resPath = getattr(graphicInfo, 'graphicFile', None)
        if resPath is None:
            self._showMessage('Could not get resPath from graphicID ' + str(graphicID))
            return
        return self._getResourceFromResPath(resPath)

    def _getResourceFromResPath(self, path):
        res = trinity.Load(path)
        if getattr(res, '__bluetype__', None) not in AssetPreviewer.supportedTypes:
            self._showMessage('resPath ' + path + ' does not contain a supported resource.')
            return
        return res

    def Cleanup(self):
        self.Clear()
        if not self._displayObjects:
            self._toggleHideSceneObjects()

    def SetSourceType(self, type):
        self.sourceType = type

    def PreviewResource(self, source):
        self.Clear()
        if self.sourceType == 'typeID':
            self.resource = self._getResourceFromTypeID(long(source))
        elif self.sourceType == 'graphicID':
            self.resource = self._getResourceFromGraphicID(long(source))
        else:
            self.resource = self._getResourceFromResPath(source)
        if self.resource is None:
            return
        scene = self._sceneManager.GetRegisteredScene('default')
        scene.objects.append(self.resource)
        self._showMessage(self.sourceType + ' ' + source + ' loaded successfully.')

    def _showMessage(self, text):
        if self._messageFunc is None:
            print text
        else:
            self._messageFunc(text)

    def _toggleHideSceneObjects(self):
        self._displayObjects = not self._displayObjects
        scene = self._sceneManager.GetRegisteredScene('default')
        for obj in scene.objects:
            if obj is not self.resource:
                obj.display = self._displayObjects

    def ShowUI(self):
        window = ToolsWindow('AssetPreview', 'Graphic Asset Preview')
        window.SetOnCloseHandler(self.Cleanup)
        source = ['']

        def updateSource(text):
            source[0] = text

        def _previewSource():
            self.PreviewResource(source[0])

        buttons = ButtonRibbon()
        buttons.AddButton('Preview', _previewSource)
        buttons.AddButton('Toggle Scene Display', self._toggleHideSceneObjects)
        buttons.AddButton('Clear', self.Clear)
        window.AddComponent(buttons)
        radioGroup = RadioButtonRibbon()
        radioGroup.AddButton('graphicID', 'graphicID')
        radioGroup.AddButton('resPath', 'resPath')
        radioGroup.AddButton('typeID', 'typeID')
        radioGroup.SetHandler(self.SetSourceType)
        window.AddComponent(radioGroup)
        infoText = TextEditComp()
        infoText.SetText('id or path to load')
        infoText.SetHandler(updateSource)
        window.AddComponent(infoText)
        textOut = TextEditComp()
        textOut.SetText('(info)')
        self._messageFunc = textOut.SetText
        window.AddComponent(textOut)
        window.Show()
