#Embedded file name: eve/client/script/ui/login\intro.py
"""
This file runs the EVE Introduction when invoked from the Game UI service.
Prior to True Exploration (January 2009) this file ran a slideshow with
voiceovers provided by the now-defunct Slides service.
In order to move forward with the Audio2 renovations I've removed
the slideshow introduction. The plan as I know it is to eventually
run a movie using this window. Pursuant to this I've left the structure
of the code intact with some helpful comments.
"""
import uiprimitives
import uicontrols
import uthread
import blue
import uicls
import carbonui.const as uiconst
import localization

class Intro(uicls.LayerCore):
    __guid__ = 'form.Intro'
    __notifyevents__ = ['OnSetDevice']

    def OnCloseView(self):
        sm.GetService('viewState').LogInfo('intro.OnCloseView')
        self.movie.Pause()
        self.movie = None
        sm.GetService('audio').SendUIEvent('music_login_resume')
        sm.GetService('ui').ForceCursorUpdate()
        self.Flush()

    def OnOpenView(self):
        if not sm.GetService('connection').IsConnected():
            return
        self.opened = 0
        self.movie = None
        self.sr.movieCont = None
        self.sr.subtitleCont = None
        self.subtitles = None
        self.fadeTime = 125
        self.InitMovie()
        self.InitSubtitles()
        sm.StartService('audio').SendUIEvent('music_login_pause')
        self.PlayMovie()
        self.opened = 1

    def OnSetDevice(self):
        dimWidth, dimHeight = self.GetVideoDimensions(uicore.desktop.width, uicore.desktop.height, 1280, 720)
        self.movie.width = dimWidth
        self.movie.height = dimHeight

    def InitMovie(self):
        self.sr.movieCont = uiprimitives.Container(parent=self, name='movieCont', idx=0, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        moviePath = 'res:/video/origins_intro.bik'
        x, y, contWidth, contHeight = self.sr.movieCont.GetAbsolute()
        dimWidth, dimHeight = self.GetVideoDimensions(contWidth, contHeight, 1280, 720)
        self.movie = uiprimitives.VideoSprite(parent=self.sr.movieCont, pos=(0,
         0,
         dimWidth,
         dimHeight), align=uiconst.CENTER, videoPath=moviePath, videoAutoPlay=False)

    def PlayMovie(self):
        self.movie.Play()
        uthread.new(self.WatchMovie)

    def InitSubtitles(self):
        x, y, contWidth, contHeight = self.sr.movieCont.GetAbsolute()
        subsHeight = int(float(contHeight) * 0.1)
        self.sr.subtitleCont = uiprimitives.Container(parent=self.sr.movieCont, name='subtitleCont', idx=0, align=uiconst.TOBOTTOM, state=uiconst.UI_DISABLED, height=subsHeight)
        self.sr.subtitleCont.Flush()
        self.subtitles = []
        endPadding = 3 * self.fadeTime
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part1'), 2510, 4350 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part2'), 4955, 7090 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part3'), 15490, 19125 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part4'), 21925, 23425 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part5'), 24925, 27815 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part6'), 30320, 32120 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part7'), 33425, 37720 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part8'), 39775, 43745 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part9'), 44990, 47290 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part10'), 59755, 64690 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part11'), 66560, 69825 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part12'), 71490, 77490 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part13'), 79460, 81990 + self.fadeTime))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part14'), 82225, 86360 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part15'), 90160, 94590 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part16'), 97290, 100060 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part17'), 102760, 107690 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part18'), 118825, 124560 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part19'), 127160, 129590 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part20'), 132790, 137725 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part21'), 140660, 145060 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part22'), 146460, 149160 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part23'), 150325, 153525 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part24'), 155000, 157990 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part25'), 159660, 163725 + endPadding))
        self.subtitles.append((localization.GetByLabel('UI/Login/IntroMovie/OriginsMovieSubtitles/Part26'), 169360, 177360 + endPadding))

    def UpdateSubtitles(self):
        x, y, contWidth, contHeight = self.sr.movieCont.GetAbsolute()
        subsWidth = int(float(contWidth) * 0.6)
        currentTime = self.GetCurrentMovieTime()
        self.sr.subtitleCont.Flush()
        for subtitle in self.subtitles:
            if currentTime >= subtitle[1] and currentTime <= subtitle[2]:
                framesFromEnd = min(currentTime - subtitle[1], subtitle[2] - currentTime)
                alpha = min(1.0, float(framesFromEnd) / self.fadeTime)
                uicontrols.EveCaptionLarge(text='<center>%s' % subtitle[0], parent=self.sr.subtitleCont, color=(0.75,
                 0.75,
                 0.75,
                 alpha), align=uiconst.TOALL, bold=False, state=uiconst.UI_DISABLED)

    def GetCurrentMovieTime(self):
        currentFrame = self.movie.currentFrame
        fps = self.movie.videoFps
        if not fps:
            return 0
        return int(float(currentFrame) / float(fps) * 1000.0)

    def WatchMovie(self):
        while not self.destroyed:
            if getattr(self, 'movie', None):
                if self.movie.isFinished:
                    self.StopIntro()
                    return
                self.UpdateSubtitles()
            else:
                return
            blue.pyos.synchro.SleepWallclock(20)

    def GetVideoDimensions(self, contWidth, contHeight, vidResWidth, vidResHeight):
        dimWidth = vidResWidth
        dimHeight = vidResHeight
        contFactor = float(contWidth) / float(contHeight)
        vidResFactor = float(vidResWidth) / float(vidResHeight)
        if vidResFactor > contFactor:
            widthFactor = float(contWidth) / float(vidResWidth)
            dimWidth *= widthFactor
            dimHeight *= widthFactor
        elif vidResFactor < contFactor:
            heightFactor = float(contHeight) / float(vidResHeight)
            dimWidth *= heightFactor
            dimHeight *= heightFactor
        else:
            dimWidth = contWidth
            dimHeight = contHeight
        return (int(dimWidth), int(dimHeight))

    def StopIntro(self):
        settings.public.generic.Set('showintro2', 0)
        if sm.GetService('cc').GetCharactersToSelect():
            uthread.pool('viewState::ActivateView::charsel', sm.GetService('viewState').ActivateView, 'charsel')
        else:
            uthread.pool('viewState::ActivateView::charsel', sm.GetService('viewState').ActivateView, 'charactercreation')

    def OnEsc(self):
        sm.GetService('viewState').LogInfo('OnEsc called')
        self.StopIntro()
