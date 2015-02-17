#Embedded file name: eve/devtools/script\form_sounds.py
import uicontrols
import blue
import os
import listentry
import audio2
import carbonui.const as uiconst
from service import *
import uiprimitives
BTNSIZE = 16

class InsiderSoundPlayer(uicontrols.Window):
    __guid__ = 'form.InsiderSoundPlayer'
    __neocommenuitem__ = (('Sound Player', 'InsiderSoundPlayer'), True, ROLE_GML)

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        w, h = (200, 300)
        self.HideMainIcon()
        self.SetTopparentHeight(0)
        self.SetMinSize([w, h])
        self.SetHeight(h)
        self.SetCaption('Sound Player')
        margin = const.defaultPadding
        self.sr.innermain = uiprimitives.Container(name='inner', left=margin, top=margin, parent=self.sr.main, pos=(0, 0, 0, 0))
        self.sr.bottomframe = uiprimitives.Container(name='bottom', align=uiconst.TOBOTTOM, parent=self.sr.innermain, height=BTNSIZE, left=margin, top=margin, clipChildren=1)
        self.sr.main = uiprimitives.Container(name='main', align=uiconst.TOALL, parent=self.sr.innermain, pos=(margin,
         margin,
         margin,
         margin))
        uicontrols.Frame(parent=self.sr.innermain, color=(1.0, 1.0, 1.0, 0.2), idx=0)
        uicontrols.Frame(parent=self.sr.main, color=(1.0, 1.0, 1.0, 0.2), idx=0)
        self.node = None
        self.InitButtons()
        self.InitScroll()

    def InitButtons(self):
        buttons = [['Play', self.SoundPlay, 'ui_38_16_228'], ['Stop', self.StopAllSounds, 'ui_38_16_111']]
        for button in buttons:
            hint, function, iconID = button
            btn = uiprimitives.Container(name=hint, align=uiconst.TOLEFT, width=BTNSIZE, left=const.defaultPadding, parent=self.sr.bottomframe)
            uicontrols.Frame(parent=btn, color=(1.0, 1.0, 1.0, 0.125))
            icon = uicontrols.Icon(icon=iconID, parent=btn, size=BTNSIZE, align=uiconst.CENTER)
            icon.OnClick = function
            icon.hint = hint
            icon.OnMouseEnter = (self.ShowSelected, icon, 1)
            icon.OnMouseExit = (self.ShowSelected, icon, 0)
            icon.sr.hilite = uiprimitives.Fill(parent=btn, name='hilite', state=uiconst.UI_HIDDEN)

        textWidth = 353
        self.textBlock = uiprimitives.Container(parent=self.sr.bottomframe, align=uiconst.TOLEFT, width=textWidth, left=const.defaultPadding)
        self.textTop = uicontrols.Label(text='', parent=self.textBlock, align=uiconst.TOALL, left=int(textWidth * 0.2) + const.defaultPadding, top=1, height=0, fontsize=10, letterspace=1, linespace=9, uppercase=1, state=uiconst.UI_NORMAL)
        self.textBtm = uicontrols.Label(text='', parent=self.textBlock, align=uiconst.TOALL, left=const.defaultPadding, height=0, top=1, fontsize=10, letterspace=1, linespace=9, uppercase=1, state=uiconst.UI_NORMAL)

    def ShowSelected(self, btn, toggle, *args):
        """
            This is the toggle function for the background highlights on the various
            buttons and icons.
        
            <toggle> defines the on/off value
            <btn> is the parent object that contains the hilite field
        """
        btn.sr.hilite.state = [uiconst.UI_HIDDEN, uiconst.UI_DISABLED][toggle]

    def SoundPlay(self, *args):
        """
            play the sound event
        """
        if self.node != None:
            sm.StartService('audio').SendUIEvent(self.node.filename)

    def StopAllSounds(self, *args):
        """
            Since we don't know what sounds are currently playing and some sound don\xb4t have 
            stop event tied to them we simply stop all sounds when the stop button is pressed.
        """
        audio2.StopAll()

    def GetFileListFromDirectories(self):
        """
            Populates the filelist on the right hand side from the source directory 'path'
        """
        soundFolder = 'res/audio/'
        soundUrlList = []
        for each in os.listdir(soundFolder):
            if '.txt' in each and each != 'Init.txt':
                self.ParseTxtFile(soundFolder + each, soundUrlList)

        for e in soundUrlList:
            yield e

    def ParseTxtFile(self, file, soundUrlList):
        """
            Parse each sound file and get the sound events from it
        """
        bf = blue.classes.CreateInstance('blue.ResFile')
        if not bf.Open(file):
            raise RuntimeError('Unable to open sound file %s' % file)
        myData = bf.Read()
        bf.Close()
        lines = myData.split('\r\n')
        if lines == None:
            return
        lines = lines[1:]
        for line in lines:
            if len(line) <= 0:
                break
            entries = line.split('\t')
            if len(entries) < 3:
                continue
            entry = entries[2].strip()
            if entry.startswith('music_') == False:
                soundUrlList.append((entry, file))

    def InitScroll(self):
        """
            Creates the scroll list
        """
        self.scroll = uicontrols.Scroll(parent=self.sr.main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        sounds = []
        for sound in self.GetFileListFromDirectories():
            sounds.append(listentry.Get('Generic', {'label': sound[0],
             'hint': sound[1],
             'filename': sound[0],
             'OnClick': self.ScrollClick,
             'OnDblClick': self.ScrollDblClick}))

        self.scroll.Load(contentList=sounds, headers=['Filename'], fixedEntryHeight=18)

    def ScrollClick(self, node, *args):
        self.node = node.sr.node

    def ScrollDblClick(self, node, *args):
        self.node = node.sr.node
        self.SoundPlay()
