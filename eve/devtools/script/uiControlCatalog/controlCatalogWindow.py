#Embedded file name: eve/devtools/script/uiControlCatalog\controlCatalogWindow.py
from eve.client.script.ui.control.eveWindow import Window
from carbonui.control.dragResizeCont import DragResizeCont
import carbonui.const as uiconst
from carbonui.control.scrollContainer import ScrollContainer
import controlData
from carbonui.primitives.gradientSprite import GradientSprite
from carbonui.primitives.container import Container
from eve.client.script.ui.control.eveEditPlainText import EditPlainText
from eve.client.script.ui.control.buttons import ToggleButtonGroup
from eve.client.script.ui.control.buttonGroup import ButtonGroup
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from eve.client.script.ui.control.eveLabel import EveLabelSmall, Label
import uthread
import blue
import os
import log
import math
from eve.client.script.ui.control.treeViewEntry import TreeViewEntry

class ControlCatalogWindow(Window):
    default_windowID = 'ControlCatalogWindow'
    default_topParentHeight = 0
    default_caption = 'UI Control Catalog'
    default_width = 900
    default_height = 800

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.entriesByID = {}
        self.currClassData = None
        self.currSampleNum = 1
        self.numSamples = 0
        uthread.new(self.ConstuctLayout)

    def ConstuctLayout(self):
        self.leftCont = DragResizeCont(name='leftCont', parent=self.sr.main, align=uiconst.TOLEFT_PROP, settingsID='ControlCatalogWindowLeftCont')
        self.infoCont = ContainerAutoSize(name='infoCont', parent=self.sr.main, align=uiconst.TOTOP, padding=6)
        self.topCont = DragResizeCont(name='topCont', parent=self.sr.main, align=uiconst.TOTOP_PROP, settingsID='ControlCatalogWindowSampleCont', minSize=0.3, maxSize=0.9, defaultSize=0.5, clipChildren=True)
        tabCont = ContainerAutoSize(name='tabCont', parent=self.topCont.mainCont, align=uiconst.TOBOTTOM)
        self.mainButtonGroup = ButtonGroup(name='mainButtonGroup', parent=self.sr.main)
        self.editCont = Container(name='editCont', parent=self.sr.main)
        GradientSprite(bgParent=self.leftCont, rotation=0, rgbData=[(0, (1.0, 1.0, 1.3))], alphaData=[(0.8, 0.0), (1.0, 0.05)])
        self.controlScroll = ScrollContainer(parent=self.leftCont)
        self.PopulateScroll()
        self.leftButtonGroup = ButtonGroup(name='leftButtonGroup', parent=self.leftCont, idx=0)
        self.ConstructLeftButtonGroup()
        self.classNameLabel = Label(parent=self.infoCont, align=uiconst.TOTOP, fontsize=15, bold=True)
        self.classDocLabel = EveLabelSmall(parent=self.infoCont, align=uiconst.TOTOP)
        GradientSprite(align=uiconst.TOTOP, parent=self.infoCont, rotation=-math.pi / 2, height=16, padding=(-4, -10, -4, 0), rgbData=[(0, (1.0, 1.0, 1.3))], alphaData=[(0.0, 0.0), (1.0, 0.03)])
        GradientSprite(align=uiconst.TOTOP, parent=tabCont, state=uiconst.UI_DISABLED, rotation=math.pi / 2, height=16, padding=(-4, 0, -4, -10), rgbData=[(0, (1.0, 1.0, 1.3))], alphaData=[(0.0, 0.0), (1.0, 0.03)])
        self.sampleNameLabel = EveLabelSmall(parent=tabCont, align=uiconst.TOTOP, padBottom=5)
        self.tabs = ToggleButtonGroup(parent=Container(parent=tabCont, align=uiconst.TOTOP, height=16), align=uiconst.CENTER, height=16, callback=self.OnTabSelected)
        sampleParent = Container(name='sampleParent', parent=self.topCont.mainCont, clipChildren=True)
        self.sampleCont = ContainerAutoSize(name='sampleCont', parent=sampleParent, align=uiconst.CENTER)
        self.codeEdit = EditPlainText(parent=self.editCont, align=uiconst.TOALL, fontcolor=(1, 1, 1, 1), ignoreTags=True)
        self.codeEdit.OnKeyDown = self.OnCodeEditKeyDown
        self.ConstructMainButtonGroup()
        uthread.new(self._SpyOnSampleCodeReloadThread)

    def OnSampleFileReload(self, path):
        """ Reload window content on sample code file changes """
        self.PopulateScroll()
        self.SetSelectedControl(self.currClassData)

    def _SpyOnSampleCodeReloadThread(self):
        """ Hook up reload event when control sample files get changed """
        try:
            from eve.common.modules.sake.platform.win32.win32api import Waitables
            from eve.common.modules.sake.autocompile import SpyFolder

            class ControlCatalogSpyFolder(SpyFolder):

                def __init__(self, callback, *args, **kw):
                    SpyFolder.__init__(self, *args, **kw)
                    self.callback = callback

                def ProcessFolder(self, path):
                    try:
                        self.callback(path)
                    except Exception as e:
                        log.LogException(e)

            spy = ControlCatalogSpyFolder(self.OnSampleFileReload, Waitables(), (os.path.dirname(__file__),))
            while not self.destroyed:
                spy.waitables.Wait(0)
                blue.pyos.synchro.Sleep(50)

        except ImportError:
            pass

    def ConstructLeftButtonGroup(self):
        for label, func in (('Browse', self.BrowseControls),):
            self.leftButtonGroup.AddButton(label, func)

    def ConstructMainButtonGroup(self):
        for label, func, hint in (('Reload', self.ReloadSamples, 'Reload all sample code [ctrl+s]'), ('Edit module', self.OpenModuleCodeInEditor, 'Open module containing class in editor'), ('Edit samples', self.OpenSampleCodeInEditor, 'Open sample code in editor')):
            self.mainButtonGroup.AddButton(label, func, hint=hint)

    def OpenSampleCodeInEditor(self, *args):
        self.currClassData.OpenSampleCodeInEditor()

    def BrowseControls(self, *args):
        controlData.BrowseControls()

    def OpenModuleCodeInEditor(self, *args):
        self.currClassData.OpenModuleCodeInEditor()

    def PopulateScroll(self):
        self.controlScroll.Flush()
        for data in controlData.GetControlData():
            TreeViewEntry(parent=self.controlScroll, data=data, eventListener=self)
            if self.currClassData and self.currClassData.GetID() == data.GetID():
                self.currClassData = data

    def RegisterID(self, entry, entryID):
        if entryID in self.entriesByID:
            raise ValueError('Same entry registered again: %s' % entryID)
        self.entriesByID[entryID] = entry

    def UnregisterID(self, entryID):
        self.entriesByID.pop(entryID)

    def OnTreeViewClick(self, selected):
        if selected.data.HasChildren():
            selected.ToggleChildren()
        else:
            for entry in self.entriesByID.values():
                entry.UpdateSelectedState((selected.data.GetID(),))

            self.currSampleNum = 1
            self.SetSelectedControl(selected.data)

    def SetSelectedControl(self, data):
        self.codeEdit.Clear()
        self.sampleCont.Flush()
        self.codeEdit.SetText(data.GetCode(), html=False)
        self.currClassData = data
        self.UpdateInfoCont()
        self.ReloadSamples()

    def UpdateInfoCont(self):
        cls = self.currClassData.GetBaseClass()
        self.classNameLabel.text = '<center>' + cls.__module__ + '.' + cls.__name__
        doc = cls.__doc__ or ''
        self.classDocLabel.text = '<center>' + doc.strip()
        if 'depricated' in doc.lower():
            self.classNameLabel.text = '<color=red>' + self.classNameLabel.text
            self.classDocLabel.text = '<color=red>' + self.classDocLabel.text

    def GetCodeText(self):
        return self.codeEdit.GetAllText()

    def ReloadSamples(self, *args):
        numSamples = controlData.GetNumSamples(self.GetCodeText())
        if numSamples != self.numSamples:
            self.numSamples = numSamples
            self.ReconstructTabs()
        self.tabs.SelectByID(self.currSampleNum)

    def ReconstructTabs(self):
        self.tabs.ClearButtons()
        for i in xrange(1, self.numSamples + 1):
            self.tabs.AddButton(i, 'Sample %s' % i)

        self.tabs.width = self.numSamples * 65

    def OnTabSelected(self, sampleNum):
        self.currSampleNum = sampleNum
        self.ReloadCurrentSample()

    def ReloadCurrentSample(self):
        self.sampleCont.Flush()
        uicore.animations.FadeTo(self.sampleCont, 0.0, 1.0, 0.1)
        if self.numSamples:
            exec (self.GetCodeText() + '\n', globals())
            exec 'Sample%s(parent=self.sampleCont)' % self.currSampleNum
            sampleName = None
            exec 'sampleName = Sample%s.__doc__' % self.currSampleNum
            if sampleName:
                self.sampleNameLabel.Show()
                self.sampleNameLabel.text = '<center>' + sampleName
            else:
                self.sampleNameLabel.Hide()
                self.sampleNameLabel.text = ''

    def OnCodeEditKeyDown(self, key, flag):
        if uicore.uilib.Key(uiconst.VK_CONTROL) and key == uiconst.VK_S:
            self.ReloadSamples()
        else:
            return EditPlainText.OnKeyDown(self.codeEdit, key, flag)
