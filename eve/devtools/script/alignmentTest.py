#Embedded file name: eve/devtools/script\alignmentTest.py
import carbonui.const as uiconst
import util
import uicls
import uiprimitives
import uicontrols

class Pars:

    def __init__(self, align, pos = None, padding = None, children = None):
        self.align = align
        self.pos = pos or (0, 0, 0, 0)
        self.padding = padding or (0, 0, 0, 0)
        self.children = children


class AlignmentTester(uicontrols.Window):
    __guid__ = 'form.AlignmentTester'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetWndIcon(None)
        self.SetTopparentHeight(0)
        btns = [('Previous', self.PrevCase, None), ('Next', self.NextCase, None)]
        btnGroup = uicontrols.ButtonGroup(btns=btns, parent=self.sr.main, line=True)
        self.main = uiprimitives.Container(parent=self.sr.main)
        self.InitCases()
        self.caseNum = attributes.caseNum or 0
        self.LoadCase()
        self.SetSize(500, 500)

    def LoadCase(self, labels = True):
        self.main.Flush()
        self.caseNum = util.Clamp(self.caseNum, 0, len(self.cases) - 1)
        self.UpdateCaption()
        case = self.cases[self.caseNum]
        self.colorFills = []
        for contParams in case:
            self.AddContainer(self.main, contParams, 0, label=labels)

        numConts = len(self.colorFills)
        for i, fill in enumerate(self.colorFills):
            hue = 0.1 * i
            while hue > 1:
                hue = hue - 1

            fill.color.SetRGB(*util.Color('BLUE').SetHSB(hue, 1.0, 0.8).SetAlpha(1.0).GetRGBA())

    def AddContainer(self, parent, contParams, level, label = True):
        cont = uiprimitives.Container(parent=parent, align=contParams.align, pos=contParams.pos, padding=contParams.padding)
        subCont = uiprimitives.Container(parent=cont, align=uiconst.TOALL)
        if label:
            uicontrols.Label(parent=cont, align=uiconst.CENTER, text=self.GetContText(cont, level), color=util.Color.WHITE)
        fill = uiprimitives.Fill(parent=cont)
        self.colorFills.append(fill)
        if contParams.children:
            for c in contParams.children:
                self.AddContainer(subCont, c, level + 1, label=label)

    def PrevCase(self, *args):
        self.caseNum -= 1
        self.LoadCase()

    def NextCase(self, *args):
        self.caseNum += 1
        self.LoadCase()

    def SetCase(self, case, labels = True):
        self.caseNum = case
        self.LoadCase(labels)

    def GetNumCases(self):
        return len(self.cases)

    def GetContText(self, cont, level):
        idx = cont.parent.children.index(cont)
        ret = '%s #%s' % (self.GetAlignmentText(cont.GetAlign()), idx)
        ret += '<br>pos: (%s, %s, %s, %s)' % (cont.left,
         cont.top,
         cont.width,
         cont.height)
        ret += '<br>pad: (%s, %s, %s, %s)' % (cont.padLeft,
         cont.padTop,
         cont.padRight,
         cont.padBottom)
        return ret

    def UpdateCaption(self):
        self.SetCaption('Alignment test: %s / %s' % (self.caseNum + 1, len(self.cases)))

    def GetAlignmentText(self, align):
        return {uiconst.TOLEFT: 'TOLEFT',
         uiconst.TOTOP: 'TOTOP',
         uiconst.TOBOTTOM: 'TOBOTTOM',
         uiconst.TORIGHT: 'TORIGHT',
         uiconst.TOALL: 'TOALL',
         uiconst.ABSOLUTE: 'ABSOLUTE',
         uiconst.RELATIVE: 'RELATIVE',
         uiconst.TOPLEFT: 'TOPLEFT',
         uiconst.TOPRIGHT: 'TOPRIGHT',
         uiconst.BOTTOMLEFT: 'BOTTOMLEFT',
         uiconst.BOTTOMRIGHT: 'BOTTOMRIGHT',
         uiconst.CENTERLEFT: 'CENTERLEFT',
         uiconst.CENTERRIGHT: 'CENTERRIGHT',
         uiconst.CENTERTOP: 'CENTERTOP',
         uiconst.CENTERBOTTOM: 'CENTERBOTTOM',
         uiconst.CENTER: 'CENTER'}[align]

    def InitCases(self):
        self.cases = []
        pos = (0, 0, 150, 150)
        self.cases.append((Pars(uiconst.TOPLEFT, pos),
         Pars(uiconst.TOPRIGHT, pos),
         Pars(uiconst.BOTTOMLEFT, pos),
         Pars(uiconst.BOTTOMRIGHT, pos),
         Pars(uiconst.CENTERLEFT, pos),
         Pars(uiconst.CENTERTOP, pos),
         Pars(uiconst.CENTERRIGHT, pos),
         Pars(uiconst.CENTERBOTTOM, pos),
         Pars(uiconst.CENTER, pos)))
        pos = (0, 0, 150, 150)
        padding = (25, 25, 0, 0)
        self.cases.append((Pars(uiconst.TOPLEFT, pos, padding),
         Pars(uiconst.TOPRIGHT, pos, padding),
         Pars(uiconst.BOTTOMLEFT, pos, padding),
         Pars(uiconst.BOTTOMRIGHT, pos, padding),
         Pars(uiconst.CENTERLEFT, pos, padding),
         Pars(uiconst.CENTERTOP, pos, padding),
         Pars(uiconst.CENTERRIGHT, pos, padding),
         Pars(uiconst.CENTERBOTTOM, pos, padding),
         Pars(uiconst.CENTER, pos, padding)))
        pos = (0, 0, 150, 150)
        padding = (0, 0, 25, 25)
        self.cases.append((Pars(uiconst.TOPLEFT, pos, padding),
         Pars(uiconst.TOPRIGHT, pos, padding),
         Pars(uiconst.BOTTOMLEFT, pos, padding),
         Pars(uiconst.BOTTOMRIGHT, pos, padding),
         Pars(uiconst.CENTERLEFT, pos, padding),
         Pars(uiconst.CENTERTOP, pos, padding),
         Pars(uiconst.CENTERRIGHT, pos, padding),
         Pars(uiconst.CENTERBOTTOM, pos, padding),
         Pars(uiconst.CENTER, pos, padding)))
        padding = (25, 25, 25, 25)
        self.cases.append((Pars(uiconst.TOPLEFT, pos, padding),
         Pars(uiconst.TOPRIGHT, pos, padding),
         Pars(uiconst.BOTTOMLEFT, pos, padding),
         Pars(uiconst.BOTTOMRIGHT, pos, padding),
         Pars(uiconst.CENTERLEFT, pos, padding),
         Pars(uiconst.CENTERTOP, pos, padding),
         Pars(uiconst.CENTERRIGHT, pos, padding),
         Pars(uiconst.CENTERBOTTOM, pos, padding),
         Pars(uiconst.CENTER, pos, padding)))
        self.cases.append((Pars(uiconst.ABSOLUTE, (100, 100, 100, 100)), Pars(uiconst.ABSOLUTE, (600, 100, 100, 100)), Pars(uiconst.ABSOLUTE, (100, 600, 100, 100))))
        padding = (25, 25, 25, 25)
        self.cases.append((Pars(uiconst.ABSOLUTE, (100, 100, 100, 100), padding), Pars(uiconst.ABSOLUTE, (600, 100, 100, 100), padding), Pars(uiconst.ABSOLUTE, (100, 600, 100, 100), padding)))
        pos = (0, 0, 100, 0)
        self.cases.append((Pars(uiconst.TOLEFT, pos), Pars(uiconst.TORIGHT, pos)))
        pos = (0, 0, 100, 0)
        padding = (25, 25, 0, 0)
        self.cases.append((Pars(uiconst.TOLEFT, pos, padding), Pars(uiconst.TORIGHT, pos, padding)))
        pos = (0, 0, 100, 0)
        padding = (0, 0, 25, 25)
        self.cases.append((Pars(uiconst.TOLEFT, pos, padding), Pars(uiconst.TORIGHT, pos, padding)))
        pos = (25, 25, 100, 25)
        padding = (25, 25, 25, 25)
        self.cases.append((Pars(uiconst.TOLEFT, pos, padding), Pars(uiconst.TORIGHT, pos, padding)))
        pos = (0, 0, 100, 0)
        self.cases.append((Pars(uiconst.TOLEFT, pos),
         Pars(uiconst.TOLEFT, pos),
         Pars(uiconst.TORIGHT, pos),
         Pars(uiconst.TORIGHT, pos)))
        self.cases.append((Pars(uiconst.TOLEFT, (25, 25, 100, 0)),
         Pars(uiconst.TOLEFT, (0, 0, 100, 0)),
         Pars(uiconst.TORIGHT, (25, 25, 100, 0)),
         Pars(uiconst.TORIGHT, (0, 0, 100, 0))))
        self.cases.append((Pars(uiconst.TOLEFT, (0, 0, 100, 0), (25, 25, 0, 0)),
         Pars(uiconst.TOLEFT, (0, 0, 100, 0)),
         Pars(uiconst.TORIGHT, (0, 0, 100, 0), (25, 25, 0, 0)),
         Pars(uiconst.TORIGHT, (0, 0, 100, 0))))
        self.cases.append((Pars(uiconst.TOLEFT, (0, 0, 100, 0), (0, 0, 25, 25)),
         Pars(uiconst.TOLEFT, (0, 0, 100, 0)),
         Pars(uiconst.TORIGHT, (0, 0, 100, 0), (0, 0, 25, 25)),
         Pars(uiconst.TORIGHT, (0, 0, 100, 0))))
        self.cases.append((Pars(uiconst.TOTOP, (0, 0, 0, 100)), Pars(uiconst.TOBOTTOM, (0, 0, 0, 100))))
        pos = (0, 0, 0, 100)
        padding = (25, 25, 25, 25)
        self.cases.append((Pars(uiconst.TOTOP, pos, padding), Pars(uiconst.TOBOTTOM, pos, padding)))
        pos = (25, 25, 25, 100)
        padding = (25, 25, 0, 0)
        self.cases.append((Pars(uiconst.TOTOP, pos, padding), Pars(uiconst.TOBOTTOM, pos, padding)))
        pos = (25, 25, 25, 100)
        padding = (0, 0, 25, 25)
        self.cases.append((Pars(uiconst.TOTOP, pos, padding), Pars(uiconst.TOBOTTOM, pos, padding)))
        pos = (0, 0, 0, 100)
        self.cases.append((Pars(uiconst.TOTOP, pos),
         Pars(uiconst.TOTOP, pos),
         Pars(uiconst.TOBOTTOM, pos),
         Pars(uiconst.TOBOTTOM, pos)))
        self.cases.append((Pars(uiconst.TOTOP, (25, 25, 0, 100)),
         Pars(uiconst.TOTOP, (0, 0, 0, 100)),
         Pars(uiconst.TOBOTTOM, (25, 25, 0, 100)),
         Pars(uiconst.TOBOTTOM, (0, 0, 0, 100))))
        padding = (25, 25, 0, 0)
        self.cases.append((Pars(uiconst.TOTOP, (0, 0, 0, 100), padding),
         Pars(uiconst.TOTOP, (0, 0, 0, 100)),
         Pars(uiconst.TOBOTTOM, (0, 0, 0, 100), padding),
         Pars(uiconst.TOBOTTOM, (0, 0, 0, 100))))
        padding = (0, 0, 25, 25)
        self.cases.append((Pars(uiconst.TOTOP, (0, 0, 0, 100), padding),
         Pars(uiconst.TOTOP, (0, 0, 0, 100)),
         Pars(uiconst.TOBOTTOM, (0, 0, 0, 100), padding),
         Pars(uiconst.TOBOTTOM, (0, 0, 0, 100))))
        self.cases.append((Pars(uiconst.TOALL),))
        self.cases.append((Pars(uiconst.TOALL, padding=(0, 0, 25, 25)),))
        self.cases.append((Pars(uiconst.TOALL, padding=(25, 25, 0, 0)),))
        self.cases.append((Pars(uiconst.TOALL, padding=(25, 25, 25, 25)),))
        self.cases.append((Pars(uiconst.TOALL, (25, 25, 25, 25), (25, 25, 0, 0)),))
        self.cases.append((Pars(uiconst.TOALL, (25, 25, 25, 25), (0, 0, 25, 25)),))
        self.cases.append((Pars(uiconst.TOALL, (25, 25, 25, 25), (25, 25, 25, 25)),))
        self.cases.append((Pars(uiconst.TOTOP, (0, 0, 0, 50)),
         Pars(uiconst.TOBOTTOM, (0, 0, 0, 50)),
         Pars(uiconst.TOLEFT, (0, 0, 50, 0)),
         Pars(uiconst.TORIGHT, (0, 0, 50, 0)),
         Pars(uiconst.TOALL)))
        padding = (25, 25, 25, 25)
        self.cases.append((Pars(uiconst.TOTOP, (0, 0, 0, 50), padding),
         Pars(uiconst.TOBOTTOM, (0, 0, 0, 50), padding),
         Pars(uiconst.TOLEFT, (0, 0, 50, 0), padding),
         Pars(uiconst.TORIGHT, (0, 0, 50, 0), padding),
         Pars(uiconst.TOALL, padding=padding)))
        padding = (25, 25, 25, 25)
        self.cases.append((Pars(uiconst.TOTOP, (25, 25, 25, 50), padding),
         Pars(uiconst.TOBOTTOM, (25, 25, 25, 50), padding),
         Pars(uiconst.TOLEFT, (25, 25, 50, 25), padding),
         Pars(uiconst.TORIGHT, (25, 25, 50, 25), padding),
         Pars(uiconst.TOALL, (25, 25, 25, 25), padding)))
        self.cases.append((Pars(uiconst.TOLEFT, (0, 0, 50, 0)),
         Pars(uiconst.TOTOP, (0, 0, 0, 50)),
         Pars(uiconst.TORIGHT, (0, 0, 50, 0)),
         Pars(uiconst.TOBOTTOM, (0, 0, 0, 50)),
         Pars(uiconst.TOLEFT, (0, 0, 50, 0)),
         Pars(uiconst.TOTOP, (0, 0, 0, 50)),
         Pars(uiconst.TORIGHT, (0, 0, 50, 0)),
         Pars(uiconst.TOBOTTOM, (0, 0, 0, 50)),
         Pars(uiconst.TOALL)))
        padding = (25, 25, 25, 25)
        self.cases.append((Pars(uiconst.TOLEFT, (0, 0, 50, 0), padding),
         Pars(uiconst.TOTOP, (0, 0, 0, 50), padding),
         Pars(uiconst.TORIGHT, (0, 0, 50, 0), padding),
         Pars(uiconst.TOBOTTOM, (0, 0, 0, 50), padding),
         Pars(uiconst.TOLEFT, (0, 0, 50, 0), padding),
         Pars(uiconst.TOTOP, (0, 0, 0, 50), padding),
         Pars(uiconst.TORIGHT, (0, 0, 50, 0), padding),
         Pars(uiconst.TOBOTTOM, (0, 0, 0, 50), padding),
         Pars(uiconst.TOALL, padding=padding)))
        padding = (25, 25, 25, 25)
        self.cases.append((Pars(uiconst.TOLEFT, (25, 25, 50, 25), padding),
         Pars(uiconst.TOTOP, (25, 25, 25, 50), padding),
         Pars(uiconst.TORIGHT, (25, 25, 50, 25), padding),
         Pars(uiconst.TOBOTTOM, (25, 25, 25, 50), padding),
         Pars(uiconst.TOLEFT, (25, 25, 50, 25), padding),
         Pars(uiconst.TOTOP, (25, 25, 25, 50), padding),
         Pars(uiconst.TORIGHT, (25, 25, 50, 25), padding),
         Pars(uiconst.TOBOTTOM, (25, 25, 25, 50), padding),
         Pars(uiconst.TOALL, (25, 25, 25, 25), padding)))
        self.cases.append((Pars(uiconst.TOLEFT, (0, 0, 100, 0), children=(Pars(uiconst.TOTOP, (0, 0, 0, 100)), Pars(uiconst.TOALL, (0, 0, 0, 100)))), Pars(uiconst.TORIGHT, (0, 0, 100, 0)), Pars(uiconst.TOALL, (0, 0, 0, 0), children=(Pars(uiconst.TOTOP, (0, 0, 0, 300)), Pars(uiconst.TOALL, children=(Pars(uiconst.TOPLEFT, (100, 100, 100, 100)),))))))
        padding = (0, 0, 25, 25)
        pos = (0, 0, 100, 100)
        childPos = (0, 0, 50, 50)
        childPad = (0, 0, 0, 0)
        childAlign = uiconst.BOTTOMLEFT
        self.cases.append((Pars(uiconst.TOPLEFT, pos, padding, children=(Pars(childAlign, childPos, childPad),)),
         Pars(uiconst.TOPRIGHT, pos, padding, children=(Pars(childAlign, childPos, childPad),)),
         Pars(uiconst.BOTTOMLEFT, pos, padding, children=(Pars(childAlign, childPos, childPad),)),
         Pars(uiconst.BOTTOMRIGHT, pos, padding, children=(Pars(childAlign, childPos, childPad),)),
         Pars(uiconst.CENTERLEFT, pos, padding, children=(Pars(childAlign, childPos, childPad),)),
         Pars(uiconst.CENTERTOP, pos, padding, children=(Pars(childAlign, childPos, childPad),)),
         Pars(uiconst.CENTERRIGHT, pos, padding, children=(Pars(childAlign, childPos, childPad),)),
         Pars(uiconst.CENTERBOTTOM, pos, padding, children=(Pars(childAlign, childPos, childPad),)),
         Pars(uiconst.CENTER, pos, padding, children=(Pars(childAlign, childPos, childPad),))))
