#Embedded file name: eve/client/script/ui/shared/twitch\twitchStreaming.py
from eve.client.script.ui.control.eveWindow import Window
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.container import Container
import carbonui.const as uiconst
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from localization import GetByLabel
from eve.client.script.ui.control.buttonGroup import ButtonGroup
from eve.client.script.ui.control.eveLabel import EveLabelSmall, EveCaptionMedium, EveCaptionSmall, Label
import twitch
from carbonui.primitives.line import Line
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from eve.client.script.ui.control.eveCombo import Combo
from eve.client.script.ui.control.buttons import ButtonIcon
import blue
from eve.client.script.ui.control.eveLoadingWheel import LoadingWheel
from carbonui.primitives.gradientSprite import GradientSprite
from math import pi
from utillib import KeyVal
from carbonui.control.baselink import BaseLinkCore
from carbon.common.script.sys.service import ROLE_PROGRAMMER
from carbonui.const import ANIM_REPEAT, ANIM_WAVE
import uthread
from eve.client.script.ui.shared.neocom.neocom.neocomCommon import BTNTYPE_TWITCH
LABELWIDTH = 80
COLOR_STOPPED = (0.243,
 0.251,
 0.259,
 1.0)
COLOR_STREAMING = (0.682,
 0.0,
 0.0,
 1.0)
TWITCH_URL = 'http://www.twitch.tv'
PASSWORD_IF_HAS_TOKEN = '**********'

class TwitchStreaming(Window):
    __guid__ = 'form.TwitchStreaming'
    __notifyevents__ = ['OnTwitchStreamingStateChange']
    default_topParentHeight = 0
    default_windowID = 'Twitch'
    default_captionLabelPath = 'Tooltips/Neocom/Twitch'
    default_descriptionLabelPath = 'Tooltips/Neocom/Twitch_description'
    default_iconNum = 'res:/UI/Texture/windowIcons/twitch.png'
    default_fixedWidth = 260
    default_fixedHeight = 440

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.streamBtn = None
        self.topCont = ContainerAutoSize(name='topCont', parent=self.sr.main, align=uiconst.TOTOP, padding=(10, 10, 10, 0))
        self.loginCont = Container(name='loginCont', parent=self.sr.main, align=uiconst.TOTOP, height=120, padding=5)
        self.settingsCont = ContainerAutoSize(name='settingsCont', parent=self.sr.main, align=uiconst.TOTOP, padding=5)
        self.ConstructTopCont()
        self.ConstructLoginCont()
        self.ConstructSettingsCont()
        self.ConstructBottomButtons()
        self.bottomGradient = GradientSprite(bgParent=self.btnGroup, rotation=-pi / 2, rgbData=[(0, (0.3, 0.3, 0.3))], alphaData=[(0, 0.3), (0.9, 0.0)])
        self.UpdateState()
        self.CheckEnableStreamBtn()
        if bool(session.role & ROLE_PROGRAMMER):
            self.debugLabel = Label(parent=self.topCont, align=uiconst.TOPLEFT, top=120)

    def ConstructTopCont(self):
        Sprite(name='twitchLogo', parent=self.topCont, texturePath='res:/UI/Texture/Classes/Twitch/logo.png', pos=(0, 0, 200, 69))
        self.stateIcon = TwitchStateIcon(parent=self.topCont, align=uiconst.TOPLEFT, pos=(0, 80, 32, 32), func=self.OnStateIconClick, controller=self)
        self.loadingWheel = LoadingWheel(parent=self.topCont, align=uiconst.TOPLEFT, pos=(-16, 64, 64, 64), opacity=0.0)
        self.stateLabel = EveCaptionMedium(parent=self.topCont, pos=(40, 87, 210, 0))

    def OnStateIconClick(self):
        blue.os.ShellExecute(self.GetTwitchChannelURL())

    def GetTwitchChannelURL(self):
        return '%s/%s' % (TWITCH_URL, self.usernameCont.GetValue())

    def ConstructLoginCont(self):
        Line(parent=self.loginCont, align=uiconst.TOTOP, padBottom=10, opacity=0.1)
        EveCaptionSmall(parent=self.loginCont, align=uiconst.TOTOP, text=GetByLabel('UI/Twitch/LoginCaption'))
        twitchSvc = sm.GetService('twitch')
        username = twitchSvc.GetUsername()
        if username is None or not twitchSvc.HasToken():
            password = None
        else:
            password = PASSWORD_IF_HAS_TOKEN
        self.usernameCont = EditWithLabel(parent=self.loginCont, text=GetByLabel('UI/Login/Username'), value=username, OnChange=self.CheckEnableStreamBtn)
        self.passwordCont = EditWithLabel(parent=self.loginCont, text=GetByLabel('UI/Login/Password'), OnReturn=self.StartStream, OnChange=self.CheckEnableStreamBtn, OnSetFocus=self.OnPasswordContFocus)
        self.passwordCont.edit.SetPasswordChar(u'\u2022')
        self.passwordCont.edit.SetValue(password)
        Label(parent=self.loginCont, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, padding=(LABELWIDTH,
         7,
         0,
         0), text=GetByLabel('UI/Twitch/SignupLink'), fontsize=10)
        Line(parent=self.loginCont, align=uiconst.TOBOTTOM, idx=0, opacity=0.1)

    def ConstructSettingsCont(self):
        EveCaptionSmall(parent=self.settingsCont, align=uiconst.TOTOP, text=GetByLabel('UI/Twitch/StreamSettings'))
        title = sm.GetService('twitch').GetTitle()
        self.streamTitleCont = EditWithLabel(parent=self.settingsCont, text=GetByLabel('UI/Twitch/StreamTitle'), value=title, OnReturn=self.StartStream)
        self.resolutionCombo = ComboWithLabel(name='resolutionCombo', parent=self.settingsCont, text=GetByLabel('UI/Twitch/Resolution'), options=sm.GetService('twitch').GetResolutionOptions(), callback=self.OnResolutionCombo)
        currResolution = (uicore.desktop.width, uicore.desktop.height)
        self.resolutionCombo.combo.SelectItemByValue(currResolution)
        self.fpsCombo = ComboWithLabel(name='resolutionCombo', parent=self.settingsCont, text=GetByLabel('UI/Twitch/Framerate'), options=sm.GetService('twitch').GetFramerateOptions(), select=sm.GetService('twitch').GetFPS())

    def ConstructBottomButtons(self):
        self.btnGroup = ButtonGroup(parent=self.sr.main, idx=0, line=False)
        self.btnGroup.AddButton(GetByLabel('UI/Generic/Close'), self.CloseByUser)
        self.streamBtn = self.btnGroup.AddButton(GetByLabel('UI/Twitch/StartStream'), self.StartStream)

    def UpdateState(self):
        state, stateName = twitch.get_api_state()
        if state <= twitch.api.STATE.FOUND_INGEST_SERVER:
            text = GetByLabel('UI/Twitch/StreamingInactive')
            btnLabel = GetByLabel('UI/Twitch/StartStream')
            btnFunc = self.StartStream
            color = COLOR_STOPPED
            self.EnableInputFields()
        elif state == twitch.api.STATE.STREAMING:
            text = GetByLabel('UI/Twitch/StreamingToTwitch')
            btnLabel = GetByLabel('UI/Twitch/StopStream')
            btnFunc = self.StopStream
            color = COLOR_STREAMING
            self.DisableInputFields()
            uicore.animations.FadeTo(self.stateLabel, 0.7, 1.2, loops=ANIM_REPEAT, curveType=ANIM_WAVE, duration=3.6)
        else:
            raise RuntimeError('unhandled state: %s (%s)' % (state, stateName))
        self.stateIcon.icon.SetRGBA(*color)
        self.stateLabel.text = text
        self.stateLabel.SetRGBA(*color)
        self.streamBtn.SetLabel(btnLabel)
        self.streamBtn.func = btnFunc

    def CheckEnableStreamBtn(self, *args):
        if not self.streamBtn:
            return
        if self.IsUsernameOrPasswordBlank():
            self.streamBtn.Disable()
        else:
            self.streamBtn.Enable()

    def OnPasswordContFocus(self, *args):
        self.passwordCont.edit.SetValue(u'')

    def IsUsernameOrPasswordBlank(self):
        return not self.usernameCont.GetValue() or not self.passwordCont.GetValue()

    def GetInputFields(self):
        return (self.loginCont, self.settingsCont)

    def EnableInputFields(self):
        for uiObj in self.GetInputFields():
            uiObj.Enable()
            uiObj.opacity = 1.0

    def DisableInputFields(self):
        for uiObj in self.GetInputFields():
            uiObj.Disable()
            uiObj.opacity = 0.3

    def StartStream(self, *args):
        username = str(self.usernameCont.GetValue())
        password = str(self.passwordCont.GetValue(raw=True))
        if not username or not password:
            return
        self.UpdateResolution()
        try:
            self.ShowLoading()
            if password == PASSWORD_IF_HAS_TOKEN:
                password = None
            title = self.streamTitleCont.GetValue()
            fps = self.fpsCombo.GetValue()
            sm.GetService('twitch').StartStream(username, password, title, fps)
            self.passwordCont.edit.SetValue(PASSWORD_IF_HAS_TOKEN)
            self.usernameCont.SetCorrect()
            self.passwordCont.SetCorrect()
        except Exception as e:
            self.passwordCont.edit.SetValue(u'')
            self.usernameCont.SetIncorrect()
            self.passwordCont.SetIncorrect()
            if str(e) != 'TTV_EC_API_REQUEST_FAILED':
                raise
        finally:
            self.HideLoading(delay=3000)
            self.UpdateState()

    def StopStream(self, *args):
        try:
            self.ShowLoading()
            sm.GetService('twitch').StopStream()
        finally:
            self.HideLoading()

        self.UpdateState()

    def OnResolutionCombo(self, combo, label, resolution):
        self.UpdateResolution()

    def UpdateResolution(self):
        """ Set client resolution to whatever is selected from combo box """
        width, height = self.resolutionCombo.GetValue()
        deviceSvc = sm.GetService('device')
        settings = deviceSvc.GetSettings().copy()
        if settings.BackBufferWidth == width and settings.BackBufferHeight == height:
            return
        settings.BackBufferWidth = width
        settings.BackBufferHeight = height
        deviceSvc.SetDevice(settings, userModified=True)

    def ShowLoading(self):
        self.streamBtn.Disable()
        uicore.animations.FadeOut(self.stateIcon)
        uicore.animations.FadeOut(self.stateLabel)
        uicore.animations.FadeIn(self.loadingWheel, timeOffset=0.3)

    def HideLoading(self, delay = None):
        uicore.animations.FadeOut(self.loadingWheel)
        uicore.animations.FadeIn(self.stateIcon, timeOffset=0.3)
        uicore.animations.FadeIn(self.stateLabel, timeOffset=0.6)
        if delay:
            uthread.new(self.EnableStreamBtnWithDelay, delay)
        else:
            self.streamBtn.Enable()

    def EnableStreamBtnWithDelay(self, delay):
        blue.synchro.SleepWallclock(delay)
        self.streamBtn.Enable()

    def OnTwitchStreamingStateChange(self, state):
        self.UpdateState()
        if bool(session.role & ROLE_PROGRAMMER):
            _, stateName = twitch.get_api_state()
            self.debugLabel.text = 'DEBUG INFO: %s' % stateName

    def GetNeocomButtonType(self):
        return BTNTYPE_TWITCH


class EditWithLabel(Container):
    default_align = uiconst.TOTOP
    default_height = 20
    default_padTop = 8

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.label = EveLabelSmall(text=attributes.text, parent=self, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, width=LABELWIDTH)
        self.edit = SinglelineEdit(name='passwordEdit', parent=self, maxLength=64, align=uiconst.TOLEFT, padLeft=LABELWIDTH, width=140, setvalue=attributes.value, OnReturn=attributes.OnReturn, OnChange=attributes.OnChange, OnSetFocus=attributes.OnSetFocus)
        self.incorrectFill = GradientSprite(bgParent=self.edit, opacity=0.0, rgbData=[(0, (0.55, 0.0, 0.0))], alphaData=[(0, 0.5),
         (0.949, 0.75),
         (0.95, 1.0),
         (1.0, 1.0)])

    def GetValue(self, *args, **kwds):
        return self.edit.GetValue(*args, **kwds)

    def SetIncorrect(self):
        uicore.animations.FadeIn(self.incorrectFill)

    def SetCorrect(self):
        uicore.animations.FadeOut(self.incorrectFill)


class ComboWithLabel(Container):
    default_align = uiconst.TOTOP
    default_height = 20
    default_padTop = 8

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.label = EveLabelSmall(text=attributes.text, parent=self, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, width=LABELWIDTH)
        self.combo = Combo(name='passwordEdit', parent=self, align=uiconst.TOLEFT, padLeft=LABELWIDTH, options=attributes.options, callback=attributes.callback, select=attributes.select, width=140)

    def GetValue(self):
        return self.combo.GetValue()


class TwitchStateIcon(ButtonIcon):
    default_name = 'TwitchStateIcon'
    default_texturePath = 'res:/UI/Texture/Classes/Twitch/icon.png'
    default_iconSize = 32
    default_hint = GetByLabel('UI/Twitch/OpenChannelHint')
    isDragObject = True

    def ApplyAttributes(self, attributes):
        ButtonIcon.ApplyAttributes(self, attributes)
        self.controller = attributes.controller

    def GetDragData(self, *args):
        url = self.controller.GetTwitchChannelURL()
        entry = KeyVal(__guid__='TextLink', url=url, dragDisplayText=url, displayText=url)
        return [entry]

    @classmethod
    def PrepareDrag(cls, *args):
        return BaseLinkCore.PrepareDrag(*args)
