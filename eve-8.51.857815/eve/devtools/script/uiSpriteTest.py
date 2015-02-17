#Embedded file name: eve/devtools/script\uiSpriteTest.py
import carbonui.const as uiconst
import blue
import uicls
import uix
import trinity
import form
import uiprimitives
import uicontrols

class UISpriteTest(uicontrols.Window):
    """ An Insider window for demoing and testing sprite capabilites """
    __guid__ = 'form.UISpriteTest'
    __notifyevents__ = ['OnFileDialogSelection']
    default_width = 625
    default_height = 500
    default_minSize = (default_width, default_height)
    default_windowID = 'UISpriteTest'
    COLUMN_WIDTH = 120

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetCaption('UI Sprite Test')
        if hasattr(self, 'SetTopparentHeight'):
            self.SetTopparentHeight(0)
        self.textureSetFunc = None
        self.bottomCont = uiprimitives.Container(name='bottomCont', parent=self.sr.main, align=uiconst.TOBOTTOM_PROP, padding=(5, 0, 5, 0), height=0.6)
        self.topCont = uiprimitives.Container(name='topCont', parent=self.sr.main, align=uiconst.TOALL, padding=(3, 3, 3, 3))
        self.topLeftCont = uiprimitives.Container(name='topLeftCont', parent=self.topCont, align=uiconst.TOLEFT, width=90)
        self.topRightCont = uiprimitives.Container(name='topRightCont', parent=self.topCont, align=uiconst.TOALL)
        primaryCont = uiprimitives.Container(parent=self.topLeftCont, align=uiconst.TOTOP, height=self.topLeftCont.width)
        uicontrols.Button(name='closePrimaryBtn', parent=primaryCont, label='<color=red>X', align=uiconst.TOPRIGHT, func=self.OnClosePrimaryBtnClick, fixedwidth=20, alwaysLite=True, top=-3, left=-3)
        self.primaryTextureSprite = uiprimitives.Sprite(name='primaryTextureSprite', parent=primaryCont, align=uiconst.TOALL)
        uicontrols.Button(name='loadPrimaryTextureBtn', parent=self.topLeftCont, label='Load primary', align=uiconst.TOTOP, func=self.OnLoadPrimaryTextureBtnClicked)
        uicontrols.Button(name='switchBtn', parent=self.topLeftCont, label='Switch', align=uiconst.TOTOP, func=self.OnSwitchBtnClick, padding=(0, 8, 0, 5), alwaysLite=True)
        secondaryCont = uiprimitives.Container(parent=self.topLeftCont, align=uiconst.TOTOP, height=self.topLeftCont.width, padTop=10)
        uicontrols.Button(name='closeSecondaryBtn', parent=secondaryCont, label='<color=red>X', align=uiconst.TOPRIGHT, func=self.OnCloseSecondaryBtnClick, fixedwidth=20, alwaysLite=True, top=-3, left=-3)
        self.secondaryTextureSprite = uiprimitives.Sprite(name='secondaryTextureSprite', parent=secondaryCont, align=uiconst.TOALL)
        uicontrols.Button(name='loadSecondaryTextureBtn', parent=self.topLeftCont, label='Load secondary', align=uiconst.TOTOP, func=self.OnLoadSecondaryTextureBtnClicked)
        self.mainSprite = uiprimitives.Sprite(name='mainSprite', parent=self.topRightCont, align=uiconst.CENTER, width=128, height=128)
        sizeCont = uiprimitives.Container(parent=self.topRightCont, align=uiconst.TOPRIGHT, pos=(5, 5, 60, 50))
        self.mainSpriteWidthEdit = uicontrols.SinglelineEdit(parent=sizeCont, name='mainSpriteWidthEdit', align=uiconst.TOTOP, label='width', ints=(1, 1024), setvalue=self.mainSprite.width, padTop=10, OnChange=self.OnMainSpriteWidthHeightChange)
        self.mainSpriteHeightEdit = uicontrols.SinglelineEdit(parent=sizeCont, name='mainSpriteHeightEdit', align=uiconst.TOTOP, label='height', ints=(1, 1024), setvalue=self.mainSprite.height, padTop=15, OnChange=self.OnMainSpriteWidthHeightChange)
        uicontrols.Button(parent=self.topRightCont, align=uiconst.BOTTOMRIGHT, label='Animate', func=self.OpenAnimationWindow, top=20)
        uicontrols.Button(parent=self.topRightCont, align=uiconst.BOTTOMRIGHT, label='Copy to clipboard', func=self.CopyCodeToClipboard, top=0)
        uiprimitives.Line(parent=self.bottomCont, align=uiconst.TOTOP)
        self.ConstructColorColumn()
        self.ConstructBlendModeColumn()
        self.ConstructSpriteEffectColumn()
        self.ConstructGlowColumn()
        self.ConstructShadowColumn()
        self.SetPrimaryPath(settings.user.ui.Get('UISpriteTestPrimaryTexturePath', None))
        self.SetSecondaryPath(settings.user.ui.Get('UISpriteTestSecondaryTexturePath', None))

    def ConstructColorColumn(self):
        colorCont = uiprimitives.Container(parent=self.bottomCont, align=uiconst.TOLEFT, width=self.COLUMN_WIDTH)
        uiprimitives.Line(parent=colorCont, align=uiconst.TORIGHT, padLeft=6)
        uicontrols.Label(parent=colorCont, text='color', align=uiconst.TOTOP)
        self.colorSliders = self.GetColorSliders(colorCont, self.OnColorValueChanged)

    def ConstructBlendModeColumn(self):
        blendModeCont = uiprimitives.Container(parent=self.bottomCont, align=uiconst.TOLEFT, width=self.COLUMN_WIDTH)
        uiprimitives.Line(parent=blendModeCont, align=uiconst.TORIGHT)
        uicontrols.Label(parent=blendModeCont, align=uiconst.TOTOP, text='blendMode')
        for constName in dir(trinity):
            if not constName.startswith('TR2_SBM_'):
                continue
            constVal = getattr(trinity, constName)
            uicontrols.Checkbox(parent=blendModeCont, text=constName, align=uiconst.TOTOP, configName='blendModeGroup', groupname='blendModeGroup', checked=constVal == uiprimitives.Sprite.default_blendMode, callback=self.OnBlendModeRadioChanged, retval=constVal)

    def ConstructSpriteEffectColumn(self):
        spriteEffectCont = uiprimitives.Container(parent=self.bottomCont, align=uiconst.TOLEFT, width=self.COLUMN_WIDTH)
        uiprimitives.Line(parent=spriteEffectCont, align=uiconst.TORIGHT)
        uicontrols.Label(parent=spriteEffectCont, text='spriteEffect', align=uiconst.TOTOP)
        for constName in dir(trinity):
            if not constName.startswith('TR2_SFX_'):
                continue
            constVal = getattr(trinity, constName)
            uicontrols.Checkbox(parent=spriteEffectCont, text=constName, align=uiconst.TOTOP, configName='spriteEffectGroup', groupname='spriteEffectGroup', checked=constVal == uiprimitives.Sprite.default_spriteEffect, callback=self.OnSpriteEffectRadioChanged, retval=constVal)

    def ConstructGlowColumn(self):
        glowCont = uiprimitives.Container(parent=self.bottomCont, align=uiconst.TOLEFT, width=self.COLUMN_WIDTH, padLeft=5)
        uiprimitives.Line(parent=glowCont, align=uiconst.TORIGHT, padLeft=6)
        uicontrols.Label(parent=glowCont, text='Glow:', align=uiconst.TOTOP, padBottom=-5)
        uicls.Slider(parent=glowCont, displayName='glowFactor', align=uiconst.TOTOP, minValue=0, maxValue=1.0, startVal=uiprimitives.Sprite.default_glowFactor, height=20, labeltab=0, onsetvaluefunc=self.OnGlowFactorSlider)
        uicls.Slider(parent=glowCont, displayName='glowExpand', align=uiconst.TOTOP, minValue=0, maxValue=30.0, startVal=uiprimitives.Sprite.default_glowExpand, height=20, labeltab=0, onsetvaluefunc=self.OnGlowExpandSlider)
        uicontrols.Label(parent=glowCont, text='glowColor:', align=uiconst.TOTOP, padTop=15, padBottom=-5)
        self.glowColorSliders = self.GetColorSliders(glowCont, self.OnGlowColorValueChanged)

    def ConstructShadowColumn(self):
        shadowCont = uiprimitives.Container(parent=self.bottomCont, align=uiconst.TOLEFT, width=self.COLUMN_WIDTH, padLeft=5)
        uicontrols.Label(parent=shadowCont, text='shadowOffset:', align=uiconst.TOTOP, padBottom=-5)
        defaultX, defaultY = uiprimitives.Sprite.default_shadowOffset
        self.shadowOffsetXSlider = uicls.Slider(parent=shadowCont, displayName='x', align=uiconst.TOTOP, minValue=0, maxValue=50.0, startVal=defaultX, height=20, labeltab=0, onsetvaluefunc=self.OnShadowOffsetSlider)
        self.shadowOffsetYSlider = uicls.Slider(parent=shadowCont, displayName='y', align=uiconst.TOTOP, minValue=0, maxValue=50.0, startVal=defaultY, height=20, labeltab=0, onsetvaluefunc=self.OnShadowOffsetSlider)
        uicontrols.Label(parent=shadowCont, text='shadowColor:', align=uiconst.TOTOP, padTop=15, padBottom=-5)
        self.shadowColorSliders = self.GetColorSliders(shadowCont, self.OnShadowColorValueChanged)

    def OnSwitchBtnClick(self, *args):
        primary = self.mainSprite.GetTexturePath()
        secondary = self.mainSprite.GetSecondaryTexturePath()
        self.SetPrimaryPath(secondary)
        self.SetSecondaryPath(primary)

    def OnClosePrimaryBtnClick(self, *args):
        self.SetPrimaryPath(None)

    def OnCloseSecondaryBtnClick(self, *args):
        self.SetSecondaryPath(None)

    def OnMainSpriteWidthHeightChange(self, *args):
        self.mainSprite.width = self.mainSpriteWidthEdit.GetValue()
        self.mainSprite.height = self.mainSpriteHeightEdit.GetValue()

    def GetColorSliders(self, parent, callback):
        sliders = []
        for colName in ('R', 'G', 'B', 'A'):
            slider = uicls.Slider(parent=parent, displayName=colName, align=uiconst.TOTOP, minValue=0, maxValue=1.0, startVal=1.0, height=20, labeltab=0, onsetvaluefunc=callback)
            sliders.append(slider)

        return sliders

    def OnColorValueChanged(self, *args):
        if not hasattr(self, 'colorSliders'):
            return
        self.mainSprite.SetRGBA(*[ slider.value for slider in self.colorSliders ])

    def OnGlowFactorSlider(self, slider):
        self.mainSprite.glowFactor = slider.value

    def OnGlowExpandSlider(self, slider):
        self.mainSprite.glowExpand = slider.value

    def OnBlurFactorSlider(self, slider):
        self.mainSprite.blurFactor = slider.value

    def OnShadowOffsetSlider(self, slider):
        try:
            self.mainSprite.shadowOffset = (self.shadowOffsetXSlider.value, self.shadowOffsetYSlider.value)
        except:
            pass

    def OnGlowColorValueChanged(self, *args):
        if not hasattr(self, 'glowColorSliders'):
            return
        self.mainSprite.glowColor = tuple([ slider.value for slider in self.glowColorSliders ])

    def OnShadowColorValueChanged(self, *args):
        if not hasattr(self, 'shadowColorSliders'):
            return
        self.mainSprite.shadowColor = tuple([ slider.value for slider in self.shadowColorSliders ])

    def OnBlendModeRadioChanged(self, button):
        self.mainSprite.blendMode = button.data['value']

    def OnSpriteEffectRadioChanged(self, button):
        self.mainSprite.spriteEffect = button.data['value']

    def OnSpriteEffectCombo(self, combo, label, value):
        self.mainSprite.spriteEffect = value

    def OnLoadPrimaryTextureBtnClicked(self, *args):
        self.textureSetFunc = self.SetPrimaryPath
        resPath = self.GetFilePathThroughFileDialog()
        if resPath:
            self.SetPrimaryPath(resPath)

    def OnLoadSecondaryTextureBtnClicked(self, *args):
        self.textureSetFunc = self.SetSecondaryPath
        resPath = self.GetFilePathThroughFileDialog()
        if resPath:
            self.SetSecondaryPath(resPath)

    def SetPrimaryPath(self, resPath):
        self.primaryTextureSprite.SetTexturePath(resPath)
        self.mainSprite.SetTexturePath(resPath)
        settings.user.ui.Set('UISpriteTestPrimaryTexturePath', resPath)

    def SetSecondaryPath(self, resPath):
        self.secondaryTextureSprite.SetTexturePath(resPath)
        self.mainSprite.SetSecondaryTexturePath(resPath)
        settings.user.ui.Set('UISpriteTestSecondaryTexturePath', resPath)

    def GetFilePathThroughFileDialog(self):
        wnd = form.FileDialog.Open(path=blue.paths.ResolvePath('res:/UI/Texture'), multiSelect=False, selectionType=uix.SEL_FILES)
        wnd.width = 400
        wnd.height = 400
        if wnd.ShowModal() == 1:
            return str(wnd.result.files[0])
        else:
            return None

    def OnFileDialogSelection(self, selected):
        if not selected:
            return
        entry = selected[0]
        if entry.isDir:
            return
        self.textureSetFunc(str(entry.filePath))

    def OpenAnimationWindow(self, *args):
        form.UIAnimationTest.Open(animObj=self.mainSprite)

    def CopyCodeToClipboard(self, *args):

        def AddArg(argName, value = None):
            value = value or repr(getattr(self.mainSprite, argName))
            return '%s=%s,\n\t' % (argName, value.replace("'", '"').replace('\\\\', '\\'))

        ret = 'uiprimitives.Sprite(\n\t'
        ret += AddArg('parent', 'uicore.desktop')
        ret += AddArg('width')
        ret += AddArg('height')
        if self.mainSprite.GetTexturePath():
            _, path = self.mainSprite.GetTexturePath().split('res')
            ret += AddArg('texturePath', repr('res:%s' % path))
        if self.mainSprite.GetSecondaryTexturePath():
            _, path = self.mainSprite.GetSecondaryTexturePath().split('res')
            ret += AddArg('textureSecondaryPath', repr('res:%s' % path))
        ret += AddArg('color', repr(self.mainSprite.GetRGBA()))
        ret += AddArg('blendMode')
        ret += AddArg('glowFactor')
        ret += AddArg('glowExpand')
        ret += AddArg('glowColor')
        ret += AddArg('shadowOffset')
        ret += AddArg('shadowColor')
        ret += AddArg('spriteEffect')
        ret += ')'
        blue.pyos.SetClipboardData(ret)
