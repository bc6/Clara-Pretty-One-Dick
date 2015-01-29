#Embedded file name: carbonui/util\textLoadFlagTest.py
import carbonui.const as uiconst
import trinity
import blue
import os
from carbonui.primitives.line import Line
from carbonui.util.various_unsorted import SortListOfTuples
from carbonui.primitives.container import Container
from carbonui.control.window import WindowCoreOverride as Window
from carbonui.control.label import LabelOverride as Label, LabelCore
from carbonui.control.singlelineedit import SinglelineEditCoreOverride as SinglelineEdit
from carbonui.control.checkbox import CheckboxCoreOverride as Checkbox
from carbonui.control.combo import ComboCoreOverride as Combo
from carbonui.control.editPlainText import EditPlainTextCoreOverride as EditPlainText
loadFlags = (('FT_LOAD_DEFAULT', 0),
 ('FT_LOAD_NO_SCALE', 1),
 ('FT_LOAD_NO_HINTING', 2),
 ('FT_LOAD_RENDER', 4),
 ('FT_LOAD_NO_BITMAP', 8),
 ('FT_LOAD_VERTICAL_LAYOUT', 16),
 ('FT_LOAD_FORCE_AUTOHINT', 32),
 ('FT_LOAD_CROP_BITMAP', 64),
 ('FT_LOAD_PEDANTIC', 128),
 ('FT_LOAD_IGNORE_GLOBAL_ADVANCE_WIDTH', 512),
 ('FT_LOAD_NO_RECURSE', 1024),
 ('FT_LOAD_IGNORE_TRANSFORM', 2048),
 ('FT_LOAD_MONOCHROME', 4096),
 ('FT_LOAD_LINEAR_DESIGN', 8192),
 ('FT_LOAD_NO_AUTOHINT', 32768))
renderFlags = (('FT_RENDER_MODE_NORMAL', 0),
 ('FT_RENDER_MODE_LIGHT', 65536),
 ('FT_RENDER_MODE_MONO', 131072),
 ('FT_RENDER_MODE_LCD', 262144),
 ('FT_RENDER_MODE_LCD_V', 524288))
samplText = u'Lorem ipsum dolor sit amet, ius in mundi eleifend, errem bonorum no mea. Ea wisi praesent imperdiet sit. His at modo debet imperdiet, cum oratio viderer facilisi ex. Et ornatus electram mel. \nLOREM IPSUM DOLOR SIT AMET, IUS IN MUNDI ELEIFEND, ERREM BONORUM NO MEA. EA WISI PRAESENT IMPERDIET SIT. HIS AT MODO DEBET IMPERDIET, CUM ORATIO VIDERER FACILISI EX. ET ORNATUS ELECTRAM MEL. \n1234567890$%&@'
ANSI = ' '.join([ unichr(i) for i in xrange(0, 255) ])
CYRILLIC = ' '.join([ unichr(i) for i in xrange(1024, 1279) ])
CYRILLIC += ' '.join([ unichr(i) for i in xrange(1280, 1327) ])
CYRILLIC += ' '.join([ unichr(i) for i in xrange(11744, 11775) ])
CYRILLIC += ' '.join([ unichr(i) for i in xrange(42560, 42655) ])
STYLECLASSES = 'Style Classes'
CLIENTFONTS = 'Client Fonts'
WINDOWSFONTS = 'Windows Fonts'

class LoadFlagTester(Window):
    __guid__ = 'uicls.LoadFlagTester'
    default_topParentHeight = 0
    default_windowID = 'LoadFlagTester'
    default_caption = 'Font Browser'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.SetMinSize((500, 300))
        main = self.GetMainArea()
        main.clipChildren = True
        options = Container(parent=main, align=uiconst.TOLEFT, width=180, padTop=4, padLeft=5)
        fontsParent = Container(parent=options)
        flagsParent = Container(parent=options)
        tabs = uicontrols.TabGroup(parent=options, tabs=[('Fonts',
          fontsParent,
          self,
          'properties'), ('Load Flags',
          flagsParent,
          self,
          'flags')], padBottom=6, idx=0)
        for each in (STYLECLASSES, CLIENTFONTS, WINDOWSFONTS):
            Checkbox(parent=fontsParent, text='Browse ' + each, groupname='browseType', checked=each == STYLECLASSES, callback=self.OnBrowseTypeChange, retval=each)

        import uicls
        clientLabelClasses = []
        for className, cls in uicls.__dict__.iteritems():
            try:
                if issubclass(cls, LabelCore) and cls is not LabelCore and getattr(cls, '__guid__', None) is not None:
                    clientLabelClasses.append((className, (className, cls)))
            except:
                pass

        clientLabelClasses = SortListOfTuples(clientLabelClasses)
        self.styleClassesLabel = Label(parent=fontsParent, text='Style Classes', align=uiconst.TOTOP, padTop=10)
        self.styleClassesCombo = Combo(parent=fontsParent, align=uiconst.TOTOP, options=clientLabelClasses, callback=self.OnStyleClassChange)
        clientFaces = []
        clientFonts = os.listdir(blue.paths.ResolvePathForWriting(u'res:') + '\\UI\\Fonts')
        clientFonts.sort()
        for fontName in clientFonts:
            if fontName.lower().endswith('.ttf') or fontName.lower().endswith('.otf'):
                clientFaces.append((fontName, 'res:/UI/Fonts/' + fontName))

        self.clientFontsLabel = Label(parent=fontsParent, text='Client Fonts', align=uiconst.TOTOP, padTop=10)
        self.clientFontsCombo = typeFaceCombo = Combo(parent=fontsParent, align=uiconst.TOTOP, options=clientFaces, callback=self.OnTypeFaceChange)
        windowsFaces = []
        windowsFonts = os.listdir(blue.win32.SHGetFolderPath(blue.win32.CSIDL_FONTS))
        windowsFonts.sort()
        for fontName in windowsFonts:
            if fontName.lower().endswith('.ttf') or fontName.lower().endswith('.otf'):
                windowsFaces.append((fontName, blue.win32.SHGetFolderPath(blue.win32.CSIDL_FONTS) + '\\' + fontName))

        self.windowsFontsLabel = Label(parent=fontsParent, text='Windows Fonts', align=uiconst.TOTOP, padTop=10)
        self.windowsFontsCombo = typeFaceCombo = Combo(parent=fontsParent, align=uiconst.TOTOP, options=windowsFaces, callback=self.OnTypeFaceChange)
        Label(parent=fontsParent, text='Fontsize', align=uiconst.TOTOP, padTop=10)
        self.fontSizeEdit = SinglelineEdit(ints=(6, 128), parent=fontsParent, align=uiconst.TOTOP, OnChange=self.OnFontSizeChange, setvalue=unicode(Label.default_fontsize))
        Label(parent=fontsParent, text='Letterspace', align=uiconst.TOTOP, padTop=10)
        self.letterSpaceEdit = SinglelineEdit(ints=(-10, 10), parent=fontsParent, align=uiconst.TOTOP, OnChange=self.OnLetterSpaceChange, setvalue=unicode(Label.default_letterspace))
        Label(parent=fontsParent, text='LineSpacing', align=uiconst.TOTOP, padTop=10)
        self.lineSpacingEdit = SinglelineEdit(floats=(-1.0, 1.0, 2), parent=fontsParent, align=uiconst.TOTOP, OnChange=self.OnLineSpacingChange, setvalue=unicode(0.0))
        current = trinity.fontMan.loadFlag
        self.loadFlagCheckBoxes = []
        for flagName, flagValue in loadFlags:
            active = current & flagValue == flagValue
            cb = Checkbox(parent=flagsParent, align=uiconst.TOTOP, text=flagName.replace('FT_LOAD_', ''), callback=self.OnLoadFlagChange, retval=flagValue, checked=active)
            cb.flagName = flagName
            cb.flagValue = flagValue
            self.loadFlagCheckBoxes.append(cb)

        Label(parent=flagsParent, text='Render flags', align=uiconst.TOTOP, padTop=10)
        self.renderFlagCheckBoxes = []
        for flagName, flagValue in renderFlags:
            active = current & flagValue == flagValue
            cb = Checkbox(parent=flagsParent, align=uiconst.TOTOP, text=flagName.replace('FT_RENDER_MODE_', ''), groupname='renderFlag', callback=self.OnRenderFlagChange, retval=flagValue, checked=active)
            cb.flagName = flagName
            cb.flagValue = flagValue
            self.renderFlagCheckBoxes.append(cb)

        sampleSelectionParent = Container(parent=main, align=uiconst.TOTOP, height=38, padTop=20)
        Line(parent=main, align=uiconst.TOTOP, padTop=10, padRight=10, padLeft=10)
        self.sampleCombo = Combo(parent=sampleSelectionParent, align=uiconst.TOPLEFT, width=100, left=10, options=[('Lorem...', samplText), ('Ansi charset', ANSI), ('Cyrillic charset', CYRILLIC)], callback=self.OnSampleComboChange)
        orlabel = Label(parent=sampleSelectionParent, text='-or-', left=self.sampleCombo.left + self.sampleCombo.width + 5)
        self.sampleInput = EditPlainText(parent=sampleSelectionParent, align=uiconst.TOALL, padLeft=140, padRight=10, text='asdf sfdasfasfdasfd safd')
        self.sampleInput.OnChange = self.OnCustomTextChange
        self.samples = []
        for typeFace in clientFonts[:1]:
            sampl = Label(parent=main, align=uiconst.TOTOP, text=samplText, padding=10)
            self.samples.append(sampl)

        self.LoadBrowseType(STYLECLASSES)

    def OnBrowseTypeChange(self, checkBox, *args):
        self.LoadBrowseType(checkBox.data['value'])

    def LoadBrowseType(self, browseType):
        if browseType == STYLECLASSES:
            self.windowsFontsCombo.Hide()
            self.windowsFontsLabel.Hide()
            self.clientFontsCombo.Hide()
            self.clientFontsLabel.Hide()
            self.styleClassesLabel.Show()
            self.styleClassesCombo.Show()
            current = self.styleClassesCombo.GetValue()
            self.LoadFontClass(current)
        elif browseType == CLIENTFONTS:
            self.windowsFontsCombo.Hide()
            self.windowsFontsLabel.Hide()
            self.styleClassesLabel.Hide()
            self.styleClassesCombo.Hide()
            self.clientFontsCombo.Show()
            self.clientFontsLabel.Show()
            current = self.clientFontsCombo.GetValue()
            self.LoadFontPath(current)
        elif browseType == WINDOWSFONTS:
            self.styleClassesLabel.Hide()
            self.styleClassesCombo.Hide()
            self.clientFontsCombo.Hide()
            self.clientFontsLabel.Hide()
            self.windowsFontsCombo.Show()
            self.windowsFontsLabel.Show()
            current = self.windowsFontsCombo.GetValue()
            self.LoadFontPath(current)

    def OnLoadFlagChange(self, checkBox):
        self.UpdateFlags()

    def OnRenderFlagChange(self, checkBox):
        self.UpdateFlags()

    def UpdateFlags(self):
        loadFlag = 0
        for cb in self.loadFlagCheckBoxes:
            if cb.GetValue():
                loadFlag = loadFlag | cb.flagValue

        for cb in self.renderFlagCheckBoxes:
            if cb.GetValue():
                loadFlag = loadFlag | cb.flagValue
                break

        trinity.fontMan.loadFlag = loadFlag
        for sampl in self.samples:
            sampl.text = sampl.text

    def OnFontSizeChange(self, text):
        try:
            newFontSize = int(text)
            for sampl in self.samples:
                sampl.fontsize = newFontSize

        except:
            pass

    def OnLetterSpaceChange(self, text):
        try:
            newLetterSpace = int(text)
            for sampl in self.samples:
                sampl.letterspace = newLetterSpace

        except:
            pass

    def OnLineSpacingChange(self, text):
        try:
            newLineSpacing = float(text)
            for sampl in self.samples:
                sampl.lineSpacing = newLineSpacing

        except:
            pass

    def OnStyleClassChange(self, combo, header, value):
        self.LoadFontClass(value)

    def LoadFontClass(self, fontClass):
        for sampl in self.samples:
            sampl.fontPath = fontClass.default_fontPath
            sampl.fontFamily = fontClass.default_fontFamily
            sampl.fontStyle = fontClass.default_fontStyle

        self.fontSizeEdit.SetValue(fontClass.default_fontsize)
        self.letterSpaceEdit.SetValue(fontClass.default_letterspace)
        self.lineSpacingEdit.SetValue(fontClass.default_lineSpacing)

    def OnTypeFaceChange(self, combo, header, value):
        self.LoadFontPath(value)

    def LoadFontPath(self, fontPath):
        for sampl in self.samples:
            sampl.fontPath = fontPath

    def OnSampleComboChange(self, combo, header, value):
        for sampl in self.samples:
            sampl.text = value

    def OnCustomTextChange(self, *args):
        current = self.sampleInput.GetValue()
        for sampl in self.samples:
            sampl.text = current
