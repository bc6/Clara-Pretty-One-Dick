#Embedded file name: eve/devtools/script\colors.py
"""
An insider tool for picking a color.
"""
import uiprimitives
import uicontrols
import carbonui.const as uiconst
import uicls
import re
import blue

class ColorPicker(uicontrols.Window):
    """Main function for the insider color picker; creates all containers and has main functions (update, re-color, copy)."""
    __guid__ = 'form.UIColorPicker'
    default_windowID = 'UIColorPicker'
    default_width = 600
    default_height = 500
    default_topParentHeight = 0
    default_minSize = (default_width, default_height)
    default_caption = 'Color Picker'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.redColor = 1.0
        self.blueColor = 0.0
        self.greenColor = 0.0
        self.alphaColor = 1.0
        self.topContainer = uiprimitives.Container(parent=self.sr.main, name='top container', pos=(0, 0, 0, 225), padding=(0, 0, 0, 0), align=uiconst.TOTOP)
        self.topLeftContainer = uiprimitives.Container(parent=self.topContainer, name='top left', pos=(0, 0, 500, 0), padding=(10, 10, 10, 10), align=uiconst.TOLEFT)
        for i in xrange(40):
            self.mainColorDisplay = uicls.ColorTable(parent=self.topLeftContainer, name='main color display', pos=(0,
             0,
             0,
             +5), padding=(0, 0, 0, 0), align=uiconst.TOTOP, greyFactor=0.5 + (1.0 - i * (1.0 / 40.0)) * 0.5, onClicked=self.PickColorMain)

        self.topRightContainer = uiprimitives.Container(parent=self.topContainer, name='top right', pos=(0, 0, 75, 0), padding=(0, 10, 10, 10), align=uiconst.TOLEFT)
        self.colorBarDisplay = []
        for i in xrange(40):
            self.colorBarDisplay.append(uicls.ColorBar(parent=self.topRightContainer, name='color bar', state=uiconst.UI_NORMAL, pos=(0,
             0,
             0,
             +5), padding=(20, 0, 25, 0), align=uiconst.TOTOP, redColor=self.redColor, greenColor=self.greenColor, blueColor=self.blueColor, position=1 - i / 40.0, onClicked=self.PickColorSide))

        self.bottomContainer = uiprimitives.Container(parent=self.sr.main, name='bottom container', pos=(0, 0, 0, 225), padding=(0, 0, 0, 0), align=uiconst.TOTOP)
        self.colorPreview = uiprimitives.Container(parent=self.bottomContainer, name='color preview', pos=(10, 25, 175, 175), padding=(0, 0, 0, 0), align=uiconst.TOPLEFT)
        self.colorPreviewFill = uiprimitives.Fill(parent=self.colorPreview, name='color preview fill', align=uiconst.TOALL, color=(self.redColor,
         self.greenColor,
         self.blueColor,
         self.alphaColor))
        self.colorValues = uiprimitives.Container(parent=self.bottomContainer, name='color texts', pos=(225, 0, 300, 250), align=uiconst.TOPLEFT)
        uicontrols.Label(parent=self.colorValues, name='color text label', text='RGB', pos=(75, 0, 100, 25), align=uiconst.TOPLEFT)
        self.colorRed = uicontrols.SinglelineEdit(parent=self.colorValues, name='red color', setvalue=str(self.redColor), pos=(35, 25, 125, 50), align=uiconst.TOPLEFT, OnChange=self.UpdateFromEdit)
        uicontrols.Label(parent=self.colorValues, name='color text label', text='Red:', pos=(0, 25, 100, 50), align=uiconst.TOPLEFT)
        self.colorGreen = uicontrols.SinglelineEdit(parent=self.colorValues, name='green color', setvalue=str(self.greenColor), pos=(35, 65, 125, 50), align=uiconst.TOPLEFT, OnChange=self.UpdateFromEdit)
        uicontrols.Label(parent=self.colorValues, name='green color label', text='Green:', pos=(0, 65, 100, 50), align=uiconst.TOPLEFT)
        self.colorBlue = uicontrols.SinglelineEdit(parent=self.colorValues, name='blue color', setvalue=str(self.blueColor), pos=(35, 105, 125, 50), align=uiconst.TOPLEFT, OnChange=self.UpdateFromEdit)
        uicontrols.Label(parent=self.colorValues, name='blue color label', text='Blue:', pos=(0, 105, 100, 50), align=uiconst.TOPLEFT)
        self.colorAlpha = uicontrols.SinglelineEdit(parent=self.colorValues, name='alpha field', setvalue=str(self.alphaColor), pos=(35, 145, 125, 50), align=uiconst.TOPLEFT, OnChange=self.UpdateFromEdit)
        uicontrols.Label(parent=self.colorValues, name='alpha label', text='Alpha:', pos=(0, 145, 100, 50), align=uiconst.TOPLEFT)
        self.hexes = uicontrols.SinglelineEdit(parent=self.colorValues, name='hex field', pos=(35, 185, 125, 50), align=uiconst.TOPLEFT, OnChange=self.UpdateHexFromEdit)
        uicontrols.Label(parent=self.colorValues, name='hex label', text='Hex:', pos=(0, 185, 100, 50), align=uiconst.TOPLEFT)
        self.buttons = uiprimitives.Container(parent=self.bottomContainer, name='color texts', pos=(400, 0, 300, 250), align=uiconst.TOPLEFT)
        self.rgbaButton = uicontrols.Button(parent=self.buttons, label='Copy RGBA', pos=(50, 75, 100, 50), align=uiconst.TOPLEFT, func=self.RgbaToClipBoard, args=())
        self.hexButton = uicontrols.Button(parent=self.buttons, label='Copy HEX', pos=(50, 125, 100, 50), align=uiconst.TOPLEFT, func=self.HexToClipBoard, args=())
        self.ConvertToHex(self.redColor, self.greenColor, self.blueColor)

    def UpdateFromEdit(self, *args):
        self.redColor = self.colorRed.text
        self.greenColor = self.colorGreen.text
        self.blueColor = self.colorBlue.text
        self.alphaColor = self.colorAlpha.text
        try:
            redColor = float(self.redColor)
            greenColor = float(self.greenColor)
            blueColor = float(self.blueColor)
            alphaColor = float(self.alphaColor)
        except ValueError:
            return

        self.colorPreviewFill.color = (redColor,
         greenColor,
         blueColor,
         alphaColor)
        self.ConvertToHex(redColor, greenColor, blueColor)

    def UpdateHexFromEdit(self, *args):
        if re.search('[a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]', self.hexes.text):
            self.ConvertToRgb(self.hexes.text)

    def PickColorMain(self, redFactor, greenFactor, blueFactor, *args):
        self.colorRed.SetText(redFactor)
        self.colorGreen.SetText(greenFactor)
        self.colorBlue.SetText(blueFactor)
        self.redColor = float(redFactor)
        self.greenColor = float(greenFactor)
        self.blueColor = float(blueFactor)
        self.alphaColor = float(self.colorAlpha.text)
        self.colorPreviewFill.color = (self.redColor,
         self.greenColor,
         self.blueColor,
         self.alphaColor)
        for colorBar in self.colorBarDisplay:
            colorBar.ReColor(redFactor, greenFactor, blueFactor)

        self.ConvertToHex(redFactor, greenFactor, blueFactor)

    def PickColorSide(self, redFactor, greenFactor, blueFactor, *args):
        self.colorRed.SetText(redFactor)
        self.colorGreen.SetText(greenFactor)
        self.colorBlue.SetText(blueFactor)
        self.alphaColor = float(self.colorAlpha.text)
        self.colorPreviewFill.color = (redFactor,
         greenFactor,
         blueFactor,
         self.alphaColor)
        self.ConvertToHex(redFactor, greenFactor, blueFactor)

    def ConvertToHex(self, redFactor, greenFactor, blueFactor):
        redFactor = min(1.0, max(0.0, redFactor))
        greenFactor = min(1.0, max(0.0, greenFactor))
        blueFactor = min(1.0, max(0.0, blueFactor))
        redColor = int(round(redFactor * 255, 0))
        greenColor = int(round(greenFactor * 255, 0))
        blueColor = int(round(blueFactor * 255, 0))
        self.hexes.SetText('%02x%02x%02x' % (redColor, greenColor, blueColor))

    def ConvertToRgb(self, hexValue):
        color = len(hexValue)
        rgb = tuple((int(hexValue[i:i + color / 3], 16) for i in range(0, color, color / 3)))
        self.redColor = rgb[0] / 255.0
        self.greenColor = rgb[1] / 255.0
        self.blueColor = rgb[2] / 255.0
        redColor = float(self.redColor)
        greenColor = float(self.greenColor)
        blueColor = float(self.blueColor)
        alphaColor = float(self.alphaColor)
        self.colorRed.SetText(redColor)
        self.colorGreen.SetText(greenColor)
        self.colorBlue.SetText(blueColor)
        self.colorPreviewFill.color = (redColor,
         greenColor,
         blueColor,
         alphaColor)

    def HexToClipBoard(self):
        blue.pyos.SetClipboardData(str(self.hexes.text))

    def RgbaToClipBoard(self):
        blue.pyos.SetClipboardData('({red}, {green}, {blue}, {alpha})'.format(red=self.redColor, green=self.greenColor, blue=self.blueColor, alpha=self.alphaColor))


class ColorBar(uiprimitives.Container):
    """Generates a color bar of a given value and approuching white/black on either end."""
    __guid__ = 'uicls.ColorBar'

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.position = attributes.position
        self.PickColorSide = attributes.onClicked
        self.fill = uiprimitives.Fill(parent=self, align=uiconst.TOALL)
        self.ReColor(attributes.redColor, attributes.greenColor, attributes.blueColor)
        self.OnClick = self.PickColor

    def PickColor(self, *args):
        self.PickColorSide(self.redColor, self.greenColor, self.blueColor)

    def ReColor(self, redFactor, greenFactor, blueFactor):
        self.redColor = float(self.GetSlideValue(redFactor, self.position))
        self.greenColor = float(self.GetSlideValue(greenFactor, self.position))
        self.blueColor = float(self.GetSlideValue(blueFactor, self.position))
        self.fill.color = (self.redColor,
         self.greenColor,
         self.blueColor,
         1)

    def GetSlideValue(self, color, position):
        if position > 0.5:
            return color + (position - 0.5) / 0.5 * (1 - color)
        elif position < 0.5:
            return position / 0.5 * color
        else:
            return color


class ColorTable(uiprimitives.Container):
    """Generates a color palette table."""
    __guid__ = 'uicls.ColorTable'

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.PickColorMain = attributes.onClicked
        for i in xrange(100):
            currentVal = i / 100.0
            c = uiprimitives.Container(parent=self, state=uiconst.UI_NORMAL, align=uiconst.TOLEFT, width=5)
            redColor = self.GetRedColor(currentVal)
            greenColor = self.GetGreenColor(currentVal)
            blueColor = self.GetBlueColor(currentVal)
            redFactor = 1 - attributes.greyFactor + redColor * (attributes.greyFactor - (1 - attributes.greyFactor))
            greenFactor = 1 - attributes.greyFactor + greenColor * (attributes.greyFactor - (1 - attributes.greyFactor))
            blueFactor = 1 - attributes.greyFactor + blueColor * (attributes.greyFactor - (1 - attributes.greyFactor))
            uiprimitives.Fill(parent=c, align=uiconst.TOALL, color=(redFactor,
             greenFactor,
             blueFactor,
             1.0))
            c.OnClick = (self.PickColorMain,
             redFactor,
             greenFactor,
             blueFactor)

    def GetRedColor(self, position):
        if position <= 0.167 or position > 0.833:
            return 1.0
        if position > 0.333 and position <= 0.667:
            return 0.0
        if position > 0.167 and position <= 0.333:
            return 1 - (position - 0.167) / 0.166
        if position > 0.667 and position <= 0.833:
            return (position - 0.667) / 0.16599999999999993

    def GetGreenColor(self, position):
        if position > 0.167 and position <= 0.5:
            return 1.0
        if position > 0.667:
            return 0.0
        if position <= 0.167:
            return position / 0.167
        if position > 0.5 and position <= 0.667:
            return 1 - (position - 0.5) / 0.16700000000000004

    def GetBlueColor(self, position):
        if position > 0.5 and position <= 0.833:
            return 1.0
        if position <= 0.333:
            return 0.0
        if position > 0.333 and position <= 0.5:
            return (position - 0.333) / 0.16699999999999998
        if position > 0.833:
            return 1 - (position - 0.833) / 0.16700000000000004
