#Embedded file name: eve/client/script/ui/services\bugReporting.py
"""
This file contains the interface class and the backend service for the
Bug-Reporting system.
"""
from eve.client.script.ui.control.eveLoadingWheel import LoadingWheel
from service import Service, ROLE_GML
import const
import httplib
import mimetypes
import blue
import json
import os
import uiprimitives
import uicontrols
import uthread
import log
import trinity
import subprocess
import util
import yaml
import zipfile
import login
import mimetools
import base
from cStringIO import StringIO
import gatekeeper
from eveexceptions.exceptionEater import ExceptionEater
import uicls
import carbonui.const as uiconst
import uiutil
from bugreporter import BugReporter, SendAttachmentError
LEFT_ARROW = 'res:/UI/Texture/BugReport_Arrow_Left.png'
RIGHT_ARROW = 'res:/UI/Texture/BugReport_Arrow_Right.png'
COLOR_GREEN = (0.0,
 1.0,
 0.0,
 1.0)
COLOR_RED = (1.0,
 0.0,
 0.0,
 1.0)
COLOR_BLUE = (0.0,
 0.0,
 1.0,
 1.0)
ARROW_HEIGHT = 28
BASEFONTSIZE = 18
NUMFONTSIZE = 26
BUGREPORT_SERVER = 'http://bugsservice.eveonline.com/api'
DEFECT_SERVER = 'evelogs'
DEFECT_SERVER_PATH = ''
SCREENSHOT_NAME = 'igbr_%s.jpg'
NUM_SCREENSHOTS = 3
SAVE_NAME = 'igbr_save_%s.yaml'

def HIWORD(f):
    return (f & 4294901760L) >> 16


def LOWORD(f):
    return f & 65535


def HIPART(f):
    return (f & 18446744069414584320L) >> 32


def LOPART(f):
    return f & 4294967295L


def DecodeDriverVersion(version):
    """
    Accepts a standard 64 bit windows DLL version number and returns a version string
    in the form [product].[version].[subVersion].[build]
    """
    try:
        highpart = HIPART(version)
        lowpart = LOPART(version)
        product = HIWORD(highpart)
        version = LOWORD(highpart)
        subVersion = HIWORD(lowpart)
        build = LOWORD(lowpart)
        return '%s.%s.%s.%s' % (product,
         version,
         subVersion,
         build)
    except:
        return ''


def AbsPath(path):
    return blue.paths.ResolvePathForWriting(path)


def GetContentType(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


class BugReportingService(Service):
    """
    Bugreporting Service, responsible for gathering the data needed and sending
    it to the bug-reporting system through a web-service.
    """
    __guid__ = 'svc.bugReporting'
    __startupdependencies__ = ['machoNet']

    def __init__(self, *args):
        Service.__init__(self)
        self.dxDiagFileName = None
        self.categories = None
        self.startStages = None
        self.fixInStages = None
        self.assignees = None
        self.priorities = None
        self.severities = None
        self.serverUrl = ''
        self.windowsUserName = ''
        self.charName = ''
        self.userName = ''
        self.bugReportServer = None
        self.screenshots = []
        self.wnd = None
        self.categories = None

    def StartCreateBugReport(self):
        self.OpenWindow()

    def OpenWindow(self):
        self.Init()
        self.wnd = BugReportingWindow.Open()

    def Init(self):
        self.screenshots = []
        self.bugReportServer = self.machoNet.GetGlobalConfig().get('bugReporting_BugReportServer', BUGREPORT_SERVER)
        self.bugReporter = BugReporter(self.bugReportServer, os.path.join(blue.paths.ResolvePath('cache:'), 'IGBR'))
        self.LogNotice('Opening bug reporting', self.userName, self.charName)
        if session.charid:
            self.charName = cfg.eveowners.Get(session.charid).name
        self.userName = settings.public.ui.Get('username', '')
        try:
            self.windowsUserName = os.environ.get('USERNAME')
        except:
            self.LogError('Unable to get windows username from environment')

        self.collectedData = None
        self.collectedFiles = None
        self.outputFolder = ''
        self.settingsFolder = 'settings:/../../'
        self.outputFolder = self.settingsFolder + u'IGBR/'
        try:
            os.mkdir(AbsPath(self.outputFolder))
        except:
            pass

        if self.dxDiagFileName is None and not blue.win32.IsTransgaming():
            self.dxDiagFileName = AbsPath(self.outputFolder + 'dxdiag.txt')
            try:
                os.remove(self.dxDiagFileName)
            except OSError:
                pass

            try:
                self.LogInfo('Getting DXDiag info...')
                subprocess.Popen(['dxdiag.exe', '/t', self.dxDiagFileName])
            except:
                self.dxDiagFileName = None

    def SaveToDisk(self, data):
        data['screenshots'] = self.screenshots
        f = open(AbsPath(self.outputFolder + self.GetSaveName()), 'w')
        yaml.dump(data, f)
        f.close()

    def GetSaveName(self):
        name = SAVE_NAME
        name = name % 'bugreport'
        return name

    def LoadFromDisk(self):
        path = AbsPath(self.outputFolder + self.GetSaveName())
        self.LogInfo('Loading data from disk', path)
        try:
            f = open(path, 'r')
        except:
            raise UserError('CustomInfo', {'info': 'No saved data found.'})

        data = yaml.load(f, Loader=yaml.CLoader)
        f.close()
        self.screenshots = data.get('screenshots', [])
        return data

    def CollectData(self):
        serverInfo = login.GetServerInfo()
        serverVersion, serverBuild = sm.RemoteSvc('cache').GetServerVersionAndBuild()
        collectedData = {'title': None,
         'description': None,
         'reproSteps': None,
         'session': str(session),
         'clientDateTime': util.FmtDate(blue.os.GetWallclockTime()),
         'clientVersion': boot.keyval['version'].split('=', 1)[1],
         'clientBuild': boot.build,
         'clientBranch': boot.branch,
         'serverName': serverInfo.name,
         'serverVersion': serverVersion,
         'serverBuild': serverBuild,
         'serverEspUrl': serverInfo.espUrl,
         'memoryFree': blue.os.GlobalMemoryStatus()[1][2] / 1024}
        bitCount = 32
        if blue.win32.GetNativeSystemInfo().get('ProcessorArchitecture', '') == 'PROCESSOR_ARCHITECTURE_AMD64':
            bitCount = 64
        deviceSvc = sm.GetService('device')
        adapters = trinity.adapters
        adapter = deviceSvc.GetAdapters()[deviceSvc.GetSettings().Get('Adapter')][0]
        ident = adapters.GetAdapterInfo(adapters.DEFAULT_ADAPTER)
        driverVersion = DecodeDriverVersion(ident.driverVersion)
        shaderVersion = adapters.GetShaderVersion(adapters.DEFAULT_ADAPTER)
        computerInfo = {'memoryPhysical': blue.os.GlobalMemoryStatus()[1][1] / 1024,
         'cpuArchitecture': blue.pyos.GetEnv().get('PROCESSOR_ARCHITECTURE', None),
         'cpuIdentifier': blue.pyos.GetEnv().get('PROCESSOR_IDENTIFIER', None),
         'cpuLevel': int(blue.pyos.GetEnv().get('PROCESSOR_LEVEL', 0)),
         'cpuRevision': int(blue.pyos.GetEnv().get('PROCESSOR_REVISION', 0), 16),
         'cpuCount': int(blue.pyos.GetEnv().get('NUMBER_OF_PROCESSORS', 0)),
         'cpuMHz': int(round(blue.os.GetCycles()[1] / 1000.0, 1)),
         'cpuBitCount': bitCount,
         'osMajorVersion': blue.os.osMajor,
         'osMinorVersion': blue.os.osMinor,
         'osBuild': blue.os.osBuild,
         'osPatch': blue.os.osPatch,
         'osPlatform': blue.os.osPlatform,
         'videoCardAdapter': adapter,
         'videoCardIdentifier': ident.deviceIdentifier[1:-1],
         'videoCardVertexShader': shaderVersion,
         'videoCardPixelShader': shaderVersion,
         'videoDriverVersion': driverVersion}
        try:
            driverInfo = ident.GetDriverInfo()
            computerInfo['videoDriverVersion'] = driverInfo.driverVersionString
            computerInfo['videoDriverDate'] = driverInfo.driverDate
            computerInfo['videoDriverVendor'] = driverInfo.driverVendor
            computerInfo['videoIsOptimus'] = 'Yes' if driverInfo.isOptimus else 'No'
            computerInfo['videoIsAmdDynamicSwitchable'] = 'Yes' if driverInfo.isAmdDynamicSwitchable else 'No'
        except RuntimeError:
            pass

        collectedData.update({'computerInfo': computerInfo})
        collectedFiles = self.GetAttachments()
        self.collectedData = util.KeyVal(data=collectedData, files=collectedFiles)
        return self.collectedData

    def GetScreenshotPath(self, n):
        if n is not None and n < len(self.screenshots):
            fileName = self.screenshots[n]
        else:
            fileName = self.outputFolder + SCREENSHOT_NAME % blue.os.GetTime()
        return fileName

    def GetScreenshot(self, n = None):
        if n > NUM_SCREENSHOTS - 1 or n is None and len(self.screenshots) >= NUM_SCREENSHOTS:
            raise UserError('CustomInfo', {'info': 'You have reached the maximum number of screenshots. Please delete a screenshot before grabbing abother one.'})
        fileName = self.GetScreenshotPath(n)
        self.LogInfo('Getting screenshot number', n, 'to', fileName, '...')
        self.wnd.HideAll()
        blue.pyos.synchro.SleepWallclock(300)
        trinity.SaveRenderTarget(AbsPath(fileName))
        if n is not None and n < len(self.screenshots):
            self.screenshots[n] = fileName
        else:
            n = len(self.screenshots)
            self.screenshots.append(fileName)
        self.LogInfo('Screenshot has been captured. I now have', len(self.screenshots), 'screenshots')
        self.wnd.Show()
        self.wnd.DoEditScreenshot(n)
        self.wnd.UpdateScreenshotButtons()

    def DeleteScreenshot(self, n):
        fileName = self.screenshots[n]
        del self.screenshots[n]
        try:
            os.remove(fileName)
        except OSError:
            pass

        self.wnd.UpdateScreenshotButtons()

    def GetAttachments(self):
        """
        Attach a file to the data to be send back to the bug-reporting backend.
        Note that the data isn"t processed until the SendBug command is given.
        """
        self.LogInfo('Getting Attachments...')
        files = []
        screenShots = []
        logs = None
        try:
            processHealthSvc = sm.GetService('processHealth')
            data = processHealthSvc.GetAllLogs()
            files.append(('processHealth.txt', data))
        except:
            log.LogException('Error getting processhealth data for bug reporting. Skipping.')

        try:
            data = sm.GetService('monitor').GetInMemoryLogs()
            logs = ('logs.txt', data)
            files.append(logs)
        except:
            log.LogException('Error getting logs for bug reporting. Skipping.')

        for i, fileName in enumerate(self.screenshots):
            try:
                with open(AbsPath(fileName), 'rb') as ssfile:
                    data = ssfile.read()
            except IOError:
                data = ''

            f = (SCREENSHOT_NAME % i, data)
            files.append(f)
            screenShots.append(f)

        try:
            data = sm.GetService('monitor').GetMethodCalls()
            files.append(('methodcalls.txt', data))
        except:
            log.LogException('Error getting method call timers for bug reporting. Skipping.')

        try:
            f = open(prefs.ini.filename, 'rb')
            data = f.read()
            f.close()
            files.append((os.path.basename(prefs.ini.filename), data))
        except:
            log.LogException('Error getting prefs for bug reporting. Skipping.')

        allSettings = {}
        try:
            for settingsType in ('public', 'user', 'char'):
                allSettings[settingsType] = getattr(settings, settingsType).datastore

            data = yaml.dump(allSettings)
            files.append(('settings.yaml', data))
        except:
            log.LogException('Error getting settings for bug reporting. Skipping.')

        try:
            if self.dxDiagFileName:
                i = 0
                data = ''
                while i < 30:
                    try:
                        f = open(self.dxDiagFileName, 'r')
                        data = f.read()
                        f.close()
                        if len(data) == 0:
                            raise IOError
                        break
                    except IOError:
                        i += 1
                        blue.pyos.synchro.SleepWallclock(1000)

                else:
                    self.LogError('Failed to get DXDiag file after 30 seconds', self.dxDiagFileName)
                    self.dxDiagFileName = None

                files.append(('dxdiag.txt', data))
        except:
            log.LogException('Error getting DxDiag for bug reporting. Skipping.')

        ZIP_FILENAME = 'igbr.zip'
        zipName = AbsPath(self.outputFolder + ZIP_FILENAME)
        with zipfile.ZipFile(zipName, 'w', zipfile.ZIP_DEFLATED) as zipDataFile:
            for fileName, data in files:
                if not fileName.lower().endswith('.jpg'):
                    zipDataFile.writestr(fileName, data)

        zipData = open(zipName, 'rb').read()
        self.LogInfo('Done Getting Attachments!')
        ret = screenShots + [logs]
        ret += [(ZIP_FILENAME, zipData)]
        return ret

    def GetLabelsForIssue(self, categoryID):
        ret = []
        categoryName = self.GetCategoryName(categoryID).lower()
        if 'localization' in categoryName:
            language = {'EN': 'English',
             'RU': 'Russian',
             'ZH': 'Chinese',
             'JA': 'Japanese'}.get(session.languageID, None)
            if language is not None:
                ret.append(language)
        if 'graphic' in categoryName:
            ret.append(trinity.platform)
        return ret

    def SendDefectOrBugReport(self, data):
        ret = self.CollectData()
        computer = self._GetComputerInfo(ret, ret.data['computerInfo'])
        sessionInfo = self._GetSessionInfo(self._GetEspUrl(ret))
        data['ServerName'] = ret.data['serverName']
        try:
            data['Title'] = data['Title'].encode('UTF-8')
            data['Description'] = data['Description'].encode('UTF-8')
            data['ReproductionSteps'] = data['ReproductionSteps'].encode('UTF-8')
        except Exception:
            self.LogError('For some reason I do not particularly care about failing to encode title, description or reproductionSteps')

        category = data['Category']
        labels = self.GetLabelsForIssue(category)
        return self.bugReporter.SendBugReport(category, data['Title'], data['Description'], data['ReproductionSteps'], sessionInfo, computer, session.userid, labels, ret.data['serverName'], GetServerVersion(ret.data['serverBuild'], ret.data['serverVersion']), ret.files)

    def _GetComputerInfo(self, ret, computerInfo):
        computer = 'Trinity platform: %(triPlatform)s\r\nOS: %(os)s.%(osminor)s, build: %(build)s, %(servicepack)s%(tg)s\r\nVideo Card: %(videocard)s (Driver: %(driverversion)s, Released: %(driverdate)s)\r\nIs Optimus: %(isoptimus)s\r\nIs AMD Dynamic Switchable: %(isamddynamicswitchable)s\r\nCPU: %(cpu)s @ %(ghz).2f GHz (%(numcpu)s CPUs)\r\nMemory: %(mem)s MB (%(memfree)s MB available)' % {'triPlatform': trinity.platform,
         'os': computerInfo.get('osMajorVersion', '-'),
         'tg': ' (MAC)' if blue.win32.IsTransgaming() else '',
         'osminor': computerInfo.get('osMinorVersion', '-'),
         'build': computerInfo.get('osBuild', '-'),
         'servicepack': computerInfo.get('osPatch', '-'),
         'videocard': computerInfo.get('videoCardAdapter', '-'),
         'driverversion': computerInfo.get('videoDriverVersion', '-'),
         'driverdate': computerInfo.get('videoDriverDate', '-'),
         'drivervendor': computerInfo.get('videoDriverVendor', '-'),
         'isoptimus': computerInfo.get('videoIsOptimus', '-'),
         'isamddynamicswitchable': computerInfo.get('videoIsAmdDynamicSwitchable', '-'),
         'cpu': computerInfo.get('cpuIdentifier', '-'),
         'ghz': int(computerInfo.get('cpuMHz', 0)) / 1024.0,
         'numcpu': computerInfo.get('cpuCount', '-'),
         'mem': int(computerInfo.get('memoryPhysical', 0)) / 1024,
         'memfree': int(ret.data.get('memoryFree', 0)) / 1024}
        return computer

    def _GetSessionInfo(self, espUrl):
        sessionInfo = ['Character: {charname} ({charid})'.format(charname=self.charName, charid=session.charid), 'Solar System: {solarsystemname} ({solarsystemid})'.format(solarsystemname=cfg.evelocations.Get(session.solarsystemid2).name, solarsystemid=session.solarsystemid2)]
        cohorts = []
        with ExceptionEater('Error getting cohorts on bugreport generation'):
            cohorts = gatekeeper.character.GetCohorts()
        if len(cohorts) > 0:
            sessionInfo.append('Cohort IDs: {cohorts}'.format(cohorts=', '.join(map(str, cohorts))))
        if len(espUrl) > 0:
            sessionInfo.append(espUrl)
        return '\n'.join(sessionInfo)

    def _GetEspUrl(self, ret):
        espUrl = ''
        if session.role & ROLE_GML > 0:
            espUrl = 'ESP: http://%(serverEspUrl)s %(serverName)s' % {'serverName': ret.data['serverName'],
             'serverEspUrl': ret.data['serverEspUrl']}
        return espUrl

    def SendBugReport(self, contentType, body):
        result = True
        h = httplib.HTTPSConnection(self.bugReportServer)
        h.putrequest('POST', '/subbugclient.asp')
        h.putheader('content-type', contentType)
        h.putheader('content-length', str(len(body)))
        h.endheaders()
        h.send(body)
        response = h.getresponse()
        if response.status == httplib.OK:
            resp = response.read()
            if resp != 'OK':
                eve.Message('CustomInfo', {'info': 'An error was encountered in sending the bug report to the server: <b>%s</b>' % resp})
                return False
            eve.Message('CustomInfo', {'info': 'Your bug report has been submitted. Thank you.<br><br><a href=shellexec:https://%s/mybugreports.asp>You can view your bug reports here</a>' % self.bugReportServer})
        else:
            txt = 'Server error in sending bug-report to the bug-reporting server. Response is %s' % response.read()
            log.LogException(txt)
            eve.Message('CustomInfo', {'info': txt})
            result = False
        h.close()
        return result

    def GetContentType(self, filename):
        """
        Guess the content-type of a file given the filename.
        Default to application/octet-stream if no info can be gathered from the filename.
        """
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def GetDefault(self, key, default = None):
        v = prefs.GetValue('bugReporting_%s' % key, None)
        if v:
            return v
        return default

    def GetCategories(self):
        if self.categories is None:
            self.categories = self.bugReporter.GetCategories()
        return self.categories[:]

    def GetCategoryName(self, categoryID):
        for name, _categoryID in self.GetCategories():
            if _categoryID == categoryID:
                return name


class BugReportingWindow(uicontrols.Window):
    """
    Bugreporting Window, responsible for displaying the fetched data by the
    BugReportingService and triggering the sending of the data.
    """
    __guid__ = 'form.BugReportingWindow'
    default_windowID = 'BugReportingWindow'
    default_iconNum = 'res:/UI/Texture/WindowIcons/repairshop.png'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.service = sm.GetService('bugReporting')
        self.service.Init()
        self.screenshotWindow = None
        self.RegisterPositionTraceKeyEvents()
        windowHeight = 430
        caption = 'Report Bug'
        self.SetTopparentHeight(0)
        self.SetCaption(caption)
        self.SetMinSize((680, windowHeight))
        self.height = windowHeight
        self.btns = uicontrols.ButtonGroup(btns=[('SEND',
          self.ClickSend,
          (),
          84)], line=1)
        self.sr.main.children.append(self.btns)
        self.mainCont = uiprimitives.Container(parent=self.sr.main, name='mainCont', padding=const.defaultPadding)
        self.loadingWheel = LoadingWheel(parent=self.mainCont, align=uiconst.CENTER, width=64, height=64)
        uthread.new(self.FinishSettingUp)

    def FinishSettingUp(self):
        if not self or self.destroyed:
            return
        self.service.bugReporter.IsBugsServiceOnline()
        if not self or self.destroyed:
            return
        self.mainCont.opacity = 1.0
        self.loadingWheel.Close()
        self.ConstructMainCont()
        categories = self.service.GetCategories()
        categories.insert(0, ['Select Category', ''])
        self.categoryCombo.LoadOptions(categories)

    def HideAll(self):
        self.Hide()
        if self.screenshotWindow:
            self.screenshotWindow.Close()

    def GetScreenshot(self, n):
        """
        Getting the data for the bug report
        """
        self.service.GetScreenshot(n)

    def ConstructMainCont(self):
        """
        Construct the main container of the window.
        """
        comboHeight = 20
        helpTextHeight = 30
        titleAlign = uiconst.TOPLEFT
        titleCont = uiprimitives.Container(name='titleCont', parent=self.mainCont, align=uiconst.TOTOP, height=36)
        self.titleEdit = c = uicontrols.SinglelineEdit(parent=titleCont, name='titleEdit', align=titleAlign, width=250, top=12, height=20, label='Title')
        buttonCont = uiprimitives.Container(name='buttonCont', parent=self.mainCont, align=uiconst.TOBOTTOM, height=20, top=0)
        disclaimerCont = uiprimitives.Container(name='disclaimerCont', parent=self.mainCont, align=uiconst.TOBOTTOM, height=helpTextHeight, top=5)
        categoryCont = uiprimitives.Container(name='categoryCont', parent=self.mainCont, align=uiconst.TOBOTTOM, height=comboHeight, top=5)
        reproStepsCont = uiprimitives.Container(name='reproStepsCont', parent=self.mainCont, align=uiconst.TOBOTTOM, height=100, top=20)
        descriptionCont = uiprimitives.Container(name='descriptionCont', parent=self.mainCont, align=uiconst.TOALL, height=5, top=0)
        uicontrols.EveLabelSmall(text='Description', parent=descriptionCont, left=2)
        desc = ''
        self.descriptionEdit = uicls.EditPlainText(name='descriptionEdit', setvalue=desc, parent=descriptionCont, maxLength=2900, top=12)
        uicontrols.EveLabelSmall(text='Reproduction Steps', parent=reproStepsCont, left=2)
        self.reproStepsEdit = uicls.EditPlainText(name='reproStepsEdit', setvalue='', parent=reproStepsCont, maxLength=2900, top=12)
        l = 0
        self.categoryCombo = c = uicontrols.Combo(label='Category', parent=categoryCont, name='categoryCombo', width=110, options=[])
        l += c.width
        self.editScreenshotButtons = []
        self.takeScreenshotButtons = []
        for i in xrange(NUM_SCREENSHOTS):
            c = uicontrols.Button(name='editscreenshot_%s' % i, label='Edit screenshot %s' % (i + 1), parent=buttonCont, func=self.EditScreenshot, align=uiconst.TOLEFT)
            self.editScreenshotButtons.append(c)

        for i in xrange(NUM_SCREENSHOTS):
            c = uicontrols.Button(name='newscreenshot_%s' % i, label='New screenshot %s' % (i + 1), parent=buttonCont, func=self.NewScreenshot, align=uiconst.TOLEFT)
            c.hint = 'You can also take a new screenshot by pressing CTRL+ALT+SHIFT+P'
            self.takeScreenshotButtons.append(c)

        self.UpdateScreenshotButtons()
        self.saveToDiskButton = uicontrols.Button(label='Save', parent=buttonCont, func=self.SaveToDisk, align=uiconst.TORIGHT)
        self.loadFromDiskButton = uicontrols.Button(label='Load', parent=buttonCont, func=self.LoadFromDisk, align=uiconst.TORIGHT)

    def UpdateScreenshotButtons(self):
        for i, c in enumerate(self.editScreenshotButtons):
            c.state = uiconst.UI_HIDDEN

        for i, c in enumerate(self.takeScreenshotButtons):
            c.state = uiconst.UI_HIDDEN

        i = -1
        numScreenshots = len(self.service.screenshots)
        for i in xrange(numScreenshots):
            self.editScreenshotButtons[i].state = uiconst.UI_NORMAL

        if i == -1:
            self.takeScreenshotButtons[0].state = uiconst.UI_NORMAL
        elif i < NUM_SCREENSHOTS - 1:
            self.takeScreenshotButtons[i + 1].state = uiconst.UI_NORMAL

    def ChangeRemember(self, *args):
        checked = self.rememberCheck.GetValue()
        prefs.SetValue('bugReporting_Remember', checked)
        if checked:
            prefs.SetValue('bugReporting_FixInStage', self.fixInCombo.GetValue())
            prefs.SetValue('bugReporting_StartStage', self.stageCombo.GetValue())
        else:
            prefs.DeleteValue('bugReporting_FixInStage')
            prefs.DeleteValue('bugReporting_StartStage')

    def EnableSendButton(self, enable):
        try:
            btn = uiutil.GetChild(self.btns, 'SEND_Btn')
            if enable:
                btn.Enable()
            else:
                btn.Disable()
        except:
            pass

    def ClickSend(self, *args):
        uthread.new(self.DoClickSend)

    def FormatString(self, txt):
        txt = txt.replace('<br>', '\r\n')
        return txt

    def GetDataFromForm(self):
        title = self.titleEdit.GetValue().strip()
        description = self.descriptionEdit.GetValue(html=0).strip()
        reproSteps = self.reproStepsEdit.GetValue(html=0).strip()
        category = self.categoryCombo.GetValue()
        description = self.FormatString(description)
        reproSteps = self.FormatString(reproSteps)
        data = {'Title': title,
         'Description': description,
         'ReproductionSteps': reproSteps,
         'Category': category}
        return data

    def DoClickSend(self):
        self.EnableSendButton(False)
        data = self.GetDataFromForm()
        if '' in (data['Title'], data['Description'], data['ReproductionSteps']) or not data['Category']:
            self.EnableSendButton(True)
            eve.Message('CustomInfo', {'info': 'All fields must be filled out'})
            return
        data['ClientBuildNumber'] = boot.build
        if len(self.service.screenshots) == 0:
            ret = eve.Message('CustomQuestion', {'header': 'A picture is worth...',
             'question': 'You have not included a screenshot in your bug report.<br>A screenshot can go a long way to explain what the bug is all about.<br><br>Would you like to grab a screenshot to attach with your bug report?'}, uiconst.YESNO)
            if ret == uiconst.ID_YES:
                self.EnableSendButton(True)
                uthread.new(self.GetScreenshot, None)
                return
        progressTxt = 'Sending Bug Report'
        result = False
        self.loadingWheel = LoadingWheel(parent=self.sr.main, align=uiconst.CENTER, width=64, height=64)
        self.mainCont.opacity = 0.3
        try:
            result = self.service.SendDefectOrBugReport(data)
        except SendAttachmentError:
            log.LogException()
            eve.Message('CustomNotify', {'notify': 'The bug report was successfully sent but there was an error adding the attachments'})
            result = True
        except Exception as e:
            log.LogException()
            self.EnableSendButton(True)
            self.mainCont.opacity = 1.0
            self.loadingWheel.Close()
            eve.Message('CustomInfo', {'info': 'An unknown error occurred when sending bug report.<br>Details: <br> %s' % e})

        if result:
            self.Close()
        else:
            self.EnableSendButton(True)

    def NewScreenshot(self, button):
        n = int(button.name.split('_')[1])
        self.GetScreenshot(n)

    def EditScreenshot(self, button):
        n = int(button.name.split('_')[1])
        self.DoEditScreenshot(n)

    def DoEditScreenshot(self, n):
        self.screenshotWindow = ScreenshotEditingWnd.Open(n=n, service=self.service)

    def ClearLogs(self, *args):
        sm.GetService('monitor').ClearLogInMemory()

    def ViewLogs(self, *args):
        sm.GetService('monitor').ShowLogTab()

    def CopyException(self, *args):
        logs = blue.logInMemory.GetEntries()
        lastException = ''
        for l in logs:
            if 'EXCEPTION END' in l[4]:
                lastException = l[4]
                break

        if len(lastException):
            inf = 'Most recent exception has been copied to the clipboard'
            lastException = lastException.replace('\n', '\r\n')
            lastException = lastException.replace('<', '&lt;')
            blue.pyos.SetClipboardData(lastException)
        else:
            inf = 'No exceptions in the logs'
        eve.Message('CustomNotify', {'notify': inf})

    def SaveToDisk(self, *args):
        data = self.GetDataFromForm()
        self.service.SaveToDisk(data)
        eve.Message('CustomNotify', {'notify': 'Your Bug Report has been saved to disk. To continue working on it later click Load.'})

    def LoadFromDisk(self, *args):
        ret = eve.Message('CustomQuestion', {'header': 'Load from disk',
         'question': 'Would you like to load up saved bug reporting data from disk and lose what you currently have written?'}, uiconst.YESNO)
        if ret != uiconst.ID_YES:
            return
        data = self.service.LoadFromDisk()
        self.titleEdit.SetValue(data.get('Title', ''))
        self.descriptionEdit.SetValue(data.get('Description', ''))
        self.reproStepsEdit.SetValue(data.get('ReproductionSteps', ''))
        self.categoryCombo.SelectItemByValue(data.get('Category', None))
        self.UpdateScreenshotButtons()

    def RegisterPositionTraceKeyEvents(self):
        self.keyDownCookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_KEYDOWN, self.OnGlobalKeyDownCallback)

    def OnGlobalKeyDownCallback(self, wnd, eventID, (vkey, flag)):
        if self.destroyed:
            return False
        ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        alt = uicore.uilib.Key(uiconst.VK_MENU)
        p = uicore.uilib.Key(uiconst.VK_P)
        if ctrl and alt and shift and p:
            uthread.new(self.GetScreenshot, None)
        return True


class ScreenshotEditingWnd(uicontrols.Window):
    __guid__ = 'form.ScreenshotEditingWnd'
    default_windowID = 'ScreenshotEditingWnd'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.SetCaption('Screenshot Editor')
        self.SetTopparentHeight(0)
        self.MakeUnstackable()
        self.NoSeeThrough()
        self.service = attributes['service']
        self.n = attributes['n']
        self.screenshotPath = sm.GetService('bugReporting').GetScreenshotPath(self.n)
        self.service.LogInfo('Screenshot editing window using screenshot from', self.screenshotPath)
        w = h = 0
        try:
            surface = trinity.Tr2HostBitmap()
            surface.CreateFromFile(self.screenshotPath)
            w, h = surface.width, surface.height
        except:
            log.LogException()

        self.screenshotWidth = w or uicore.desktop.width
        self.screenshotHeight = h or uicore.desktop.height
        self.screenShotScaling = None
        maxWidth = max(self.screenshotWidth / 2, 720)
        self.SetMinSize([maxWidth, self.screenshotHeight / 2])
        topCont = uiprimitives.Container(name='topCont', parent=self.sr.main, align=uiconst.TOTOP, height=30, padding=const.defaultPadding)
        self.layoutAreaParent = uiprimitives.Container(parent=self.sr.main, padding=10)
        self.layoutAreaParent._OnSizeChange_NoBlock = self.RecalcLayout
        self.layoutArea = uiprimitives.Container(parent=self.layoutAreaParent, align=uiconst.CENTER, width=self.screenshotWidth / 4, height=self.screenshotHeight / 4)
        self.overlays = uiprimitives.Container(name='overlays', parent=self.layoutArea, align=uiconst.TOALL, clipChildren=True)
        self.screenshotSprite = uiprimitives.Sprite(name='screenshotSprite', parent=self.layoutArea, texturePath=self.screenshotPath, align=uiconst.TOALL, padding=0)
        self.screenshotSprite.ReloadTexture()
        uicontrols.Button(label='Save', parent=topCont, func=self.SaveScreenshot, left=8, align=uiconst.CENTERRIGHT)
        fb = uicontrols.Button(label='Add Frame', func=self.AddFrame, parent=topCont, left=8, align=uiconst.CENTERLEFT)
        cfb = uicontrols.Button(label='Add Crop Frame', func=self.AddCropFrame, parent=topCont, left=fb.left + fb.width + 8, align=uiconst.CENTERLEFT)
        la = uicontrols.Button(label='Add Left Arrow', func=self.AddLeftArrowFrame, parent=topCont, left=cfb.left + cfb.width + 8, align=uiconst.CENTERLEFT)
        ra = uicontrols.Button(label='Add Right Arrow', func=self.AddRightArrowFrame, parent=topCont, left=la.left + la.width + 8, align=uiconst.CENTERLEFT)
        tc = uicontrols.Button(label='Add Text', func=self.AddTextFrame, parent=topCont, left=ra.left + ra.width + 8, align=uiconst.CENTERLEFT)
        cb = uicontrols.Button(label='New', func=self.NewScreenshot, parent=topCont, left=tc.left + tc.width + 20, align=uiconst.CENTERLEFT)
        cb = uicontrols.Button(label='Delete', func=self.DeleteScreenshot, parent=topCont, left=cb.left + cb.width + 8, align=uiconst.CENTERLEFT)
        self.UpdateLayoutArea()

    def UpdateLayoutArea(self):
        prevScaling = self.screenShotScaling
        areaWidth, areaHeight = self.layoutAreaParent.GetAbsoluteSize()
        xFitScale = areaWidth / float(self.screenshotWidth)
        yFitScale = areaHeight / float(self.screenshotHeight)
        self.screenShotScaling = scaling = min(xFitScale, yFitScale)
        self.layoutArea.width = int(self.screenshotWidth * scaling)
        self.layoutArea.height = int(self.screenshotHeight * scaling)
        if prevScaling and prevScaling != scaling:
            for overlay in self.overlays.children:
                overlay.UpdateProportionalPosition(scaling)

    def NewScreenshot(self, *args):
        self.service.GetScreenshot(self.n)

    def DeleteScreenshot(self, *args):
        self.service.DeleteScreenshot(self.n)
        self.Close()

    def AddTextFrame(self, *args):
        initFontsize = int(BASEFONTSIZE * self.screenShotScaling)
        initWidth = int(200 * self.screenShotScaling)
        initHeight = int(32 * self.screenShotScaling)
        initLeft = int(self.screenshotWidth * 0.5 * self.screenShotScaling) - initWidth / 2
        initTop = int(self.screenshotHeight * 0.5 * self.screenShotScaling) - initHeight / 2
        uicls.MoveableTextRect(name='Text', parent=self.overlays, pos=(initLeft,
         initTop,
         initWidth,
         initHeight), idx=0, showControls=True, fontsize=initFontsize)

    def AddRightArrowFrame(self, *args):
        initWidth = int(ARROW_HEIGHT * 2 * self.screenShotScaling)
        initHeight = int(ARROW_HEIGHT * self.screenShotScaling)
        initLeft = int(self.screenshotWidth * 0.5 * self.screenShotScaling)
        initTop = int(self.screenshotHeight * 0.5 * self.screenShotScaling)
        container = uicls.MoveableRect(name='Arrow', parent=self.overlays, pos=(initLeft,
         initTop,
         initWidth,
         initHeight), showControls=False, idx=0)
        icon = uiprimitives.Sprite(label='arrow', parent=container, texturePath=RIGHT_ARROW, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        container.AddColorObject(icon)
        container.ChangeColor(COLOR_GREEN)

    def AddLeftArrowFrame(self, *args):
        initWidth = int(ARROW_HEIGHT * 2 * self.screenShotScaling)
        initHeight = int(ARROW_HEIGHT * self.screenShotScaling)
        initLeft = int(self.screenshotWidth * 0.5 * self.screenShotScaling)
        initTop = int(self.screenshotHeight * 0.5 * self.screenShotScaling)
        container = uicls.MoveableRect(name='Arrow', parent=self.overlays, pos=(initLeft,
         initTop,
         initWidth,
         initHeight), showControls=False, idx=0)
        icon = uiprimitives.Sprite(label='arrow', parent=container, texturePath=LEFT_ARROW, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        container.AddColorObject(icon)
        container.ChangeColor(COLOR_GREEN)

    def AddCropFrame(self, *args):
        for each in self.overlays.children[:]:
            if each.name == 'cropFrame':
                each.Close()

        initLeft = int(self.screenshotWidth * 0.25 * self.screenShotScaling)
        initTop = int(self.screenshotHeight * 0.25 * self.screenShotScaling)
        initWidth = int(self.screenshotWidth * 0.5 * self.screenShotScaling)
        initHeight = int(self.screenshotHeight * 0.5 * self.screenShotScaling)
        uicls.MoveableRect(name='Crop', parent=self.overlays, pos=(initLeft,
         initTop,
         initWidth,
         initHeight), maskColor=(0, 0, 0, 0.75), showControls=True)

    def AddFrame(self, *args):
        initLeft = int((self.screenshotWidth - 200) * self.screenShotScaling) / 2
        initTop = int((self.screenshotHeight - 200) * self.screenShotScaling) / 2
        initWidth = int(200 * self.screenShotScaling)
        initHeight = int(200 * self.screenShotScaling)
        uicls.MoveableRect(parent=self.overlays, name='Frame', pos=(initLeft,
         initTop,
         initWidth,
         initHeight), showFrame=True, showControls=True, idx=0)

    def Clear(self, *args):
        self.overlays.Flush()

    def SaveScreenshot(self, *args):
        self.Hide()
        baseTexture = trinity.Tr2RenderTarget(self.screenshotWidth, self.screenshotHeight, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
        renderJob = trinity.CreateRenderJob()
        desktop = uiprimitives.UIRoot(name='screenshot', width=self.screenshotWidth, height=self.screenshotHeight, renderTarget=baseTexture, renderJob=renderJob)
        cropProportion = None
        for each in self.overlays.children:
            if each.name == 'Crop':
                cropProportion = each.proportionalPosition

        self.overlays.SetParent(desktop)
        self.screenshotSprite.SetParent(desktop)
        for overlay in self.overlays.children:
            overlay.UpdateProportionalPosition(1.0)

        desktop.UpdateAlignment()
        blue.pyos.synchro.Yield()
        renderJob.ScheduleOnce()
        renderJob.WaitForFinish()
        blue.pyos.synchro.Yield()
        path = AbsPath(self.screenshotPath)
        if cropProportion:
            cl, cr, ct, cb = cropProportion
            cr = min(1.0, cr)
            cb = min(1.0, cb)
            bmp = trinity.Tr2HostBitmap(baseTexture)
            bmp.Crop(int(cl * self.screenshotWidth), int(ct * self.screenshotHeight), int(cr * self.screenshotWidth), int(cb * self.screenshotHeight))
            bmp.Save(path)
        else:
            trinity.Tr2HostBitmap(baseTexture).Save(path)
        desktop.Close()
        self.CloseByUser()

    def OnScale_(self, *args):
        pass

    def RecalcLayout(self, *args):
        self.UpdateLayoutArea()


class MoveableRect(uiprimitives.Container):
    __guid__ = 'uicls.MoveableRect'
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    CONTROLS = (('topleft', uiconst.TOPLEFT),
     ('topright', uiconst.TOPRIGHT),
     ('bottomright', uiconst.BOTTOMRIGHT),
     ('bottomleft', uiconst.BOTTOMLEFT))

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        self.modifyThread = None
        self.frame = None
        self.colorObjects = []
        self.color = COLOR_GREEN
        self.controls = uiprimitives.Container(parent=self, state=uiconst.UI_PICKCHILDREN)
        if attributes.showControls:
            for cornerName, align in self.CONTROLS:
                scalePoint = uiprimitives.Fill(parent=self.controls, align=align, color=(1, 1, 1, 1), pos=(0, 0, 10, 10), state=uiconst.UI_NORMAL, name=cornerName)
                scalePoint.OnMouseDown = (self.StartScaling, scalePoint)
                scalePoint.OnMouseUp = (self.EndScaling, scalePoint)
                self.AddColorObject(scalePoint)

        self.maskColor = attributes.maskColor
        if self.maskColor:
            self.UpdateMask()
        if attributes.showFrame:
            self.frame = uicontrols.Frame(parent=self, frameConst=uiconst.FRAME_BORDER2_CORNER3)
            self.AddColorObject(self.frame)
        self.UpdateColor()
        self.RegisterProportionalValues()

    def AddColorObject(self, obj):
        self.colorObjects.append(obj)
        self.UpdateColor()

    def StartScaling(self, obj, *args):
        startProps = (obj.name,
         uicore.uilib.x,
         uicore.uilib.y,
         self.left,
         self.top,
         self.width,
         self.height)
        self.modifyThread = base.AutoTimer(1, self.ModifyRect, startProps)

    def EndScaling(self, obj, *args):
        self.modifyThread = None

    def OnMouseDown(self, *args):
        startProps = ('move',
         uicore.uilib.x,
         uicore.uilib.y,
         self.left,
         self.top,
         self.width,
         self.height)
        self.modifyThread = base.AutoTimer(1, self.ModifyRect, startProps)

    def OnMouseUp(self, *args):
        self.modifyThread = None

    def ModifyRect(self, startProps, *args):
        side, cursorX, cursorY, l, t, w, h = startProps
        dx = uicore.uilib.x - cursorX
        dy = uicore.uilib.y - cursorY
        if side == 'move':
            self.left = max(0, l + dx)
            self.top = max(0, t + dy)
        else:
            if 'left' in side:
                self.width = max(16, w - dx)
                self.left = max(0, min(l + dx, l + w - 16))
            else:
                self.width = max(16, w + dx)
            if 'top' in side:
                self.height = max(16, h - dy)
                self.top = max(0, min(t + dy, t + h - 16))
            else:
                self.height = max(16, h + dy)
        if self.maskColor:
            self.UpdateMask()
        self.RegisterProportionalValues()

    def RegisterProportionalValues(self):
        parWidth, parHeight = self.parent.GetAbsoluteSize()
        pl = self.left / float(parWidth)
        pr = (self.left + self.width) / float(parWidth)
        pt = self.top / float(parHeight)
        pb = (self.top + self.height) / float(parHeight)
        self.proportionalPosition = (pl,
         pr,
         pt,
         pb)

    def UpdateProportionalPosition(self, newScaling):
        parWidth, parHeight = self.parent.GetAbsoluteSize()
        pl, pr, pt, pb = self.proportionalPosition
        self.left = int(pl * parWidth)
        self.top = int(pt * parHeight)
        self.width = int((pr - pl) * parWidth)
        self.height = int((pb - pt) * parHeight)
        if newScaling == 1.0 and getattr(self, 'numLabel', None):
            self.numLabel.useSizeFromTexture = True
            self.numLabel.Layout()
            self.numLabel.top = -self.numLabel.textheight - 2
        if self.maskColor:
            self.UpdateMask()

    def UpdateMask(self):
        maskFills = getattr(self, 'maskFills', None)
        if not maskFills:
            self.maskFills = []
            for i in xrange(4):
                self.maskFills.append(uiprimitives.Fill(parent=self, color=self.maskColor, align=uiconst.TOPLEFT))

        self.maskFills[0].top = -uicore.desktop.height
        self.maskFills[0].height = uicore.desktop.height
        self.maskFills[0].left = -uicore.desktop.width
        self.maskFills[0].width = uicore.desktop.width * 2
        self.maskFills[1].top = self.height
        self.maskFills[1].height = uicore.desktop.height
        self.maskFills[1].left = -uicore.desktop.width
        self.maskFills[1].width = uicore.desktop.width * 2
        self.maskFills[2].top = 0
        self.maskFills[2].height = self.height
        self.maskFills[2].left = -uicore.desktop.width
        self.maskFills[2].width = uicore.desktop.width
        self.maskFills[3].top = 0
        self.maskFills[3].height = self.height
        self.maskFills[3].left = self.width
        self.maskFills[3].width = uicore.desktop.width

    def OnMouseEnter(self, *args):
        self.ShowControls()
        self.mouseOverThread = base.AutoTimer(1, self.CheckMouseOver)

    def CheckMouseOver(self, *args):
        if self.destroyed:
            self.mouseOverThread = None
            return
        mo = uicore.uilib.mouseOver
        if mo is self or uiutil.IsUnder(mo, self) or self.modifyThread:
            return
        self.mouseOverThread = None
        self.HideControls()

    def ShowControls(self):
        self.controls.Show()

    def HideControls(self):
        self.controls.Hide()

    def Numberate(self, *args):
        currentNumbers = []
        for each in self.parent.children:
            autoNumber = getattr(each, 'autoNumber', None)
            if autoNumber is not None:
                currentNumbers.append(autoNumber)

        tryNum = 1
        while tryNum in currentNumbers:
            tryNum += 1

        self.AssignNumber(tryNum)

    def AssignNumber(self, number):
        if getattr(self, 'numLabel', None) is None:
            self.numLabel = uicontrols.Label(parent=self, fontsize=NUMFONTSIZE, align=uiconst.TOPRIGHT, bold=1)
            self.numLabel.useSizeFromTexture = False
            self.numLabel._OnSizeChange_NoBlock = self.OnNumberSizeChange
        self.autoNumber = number
        self.numLabel.text = unicode(number)
        self.AddColorObject(self.numLabel)

    def OnNumberSizeChange(self, *args):
        screenShotWindow = uiutil.GetWindowAbove(self)
        if screenShotWindow:
            self.numLabel.displayWidth = self.numLabel.textwidth * screenShotWindow.screenShotScaling
            self.numLabel.displayHeight = self.numLabel.textheight * screenShotWindow.screenShotScaling
            self.numLabel.top = -self.ReverseScaleDpi((self.numLabel.textheight + 2) * screenShotWindow.screenShotScaling)

    def GetMenu(self, *args):
        m = [('Delete %s' % self.name, self.Delete), ('Numberate', self.Numberate)]
        if self.maskColor:
            return m
        m = m + [None,
         ('RED', self.ChangeColor, ((1, 0, 0, 1),)),
         ('GREEN', self.ChangeColor, ((0, 1, 0, 1),)),
         ('BLUE', self.ChangeColor, ((0, 0, 1, 1),))]
        return m

    def Delete(self, *args):
        uthread.new(self.Close)

    def UpdateColor(self):
        self.ChangeColor(self.color)

    def ChangeColor(self, color):
        self.color = color
        for each in self.colorObjects:
            each.SetRGB(*color)


class MoveableTextRect(MoveableRect):
    __guid__ = 'uicls.MoveableTextRect'
    DEFAULTTEXT = 'Double click to edit'
    CONTROLS = ()

    def ApplyAttributes(self, attributes):
        uicls.MoveableRect.ApplyAttributes(self, attributes)
        self.textEdit = None
        self.underlay = uiprimitives.Fill(parent=self)
        self.sampleText = uicontrols.Label(parent=self, left=8, top=8, text=self.DEFAULTTEXT, fontsize=BASEFONTSIZE)
        self.sampleText.useSizeFromTexture = False
        self.sampleText._OnSizeChange_NoBlock = self.OnTextSizeChange
        self.UpdateColor()
        self.OnTextSizeChange()

    def OnTextSizeChange(self, *args):
        screenShotWindow = uiutil.GetWindowAbove(self)
        if screenShotWindow:
            self.sampleText.displayWidth = self.sampleText.textwidth * screenShotWindow.screenShotScaling
            self.sampleText.displayHeight = self.sampleText.textheight * screenShotWindow.screenShotScaling
            self.width = self.ReverseScaleDpi(self.sampleText.displayWidth) + 16
            self.height = self.ReverseScaleDpi(self.sampleText.displayHeight) + 16

    def OnDblClick(self, *args):
        self.sampleText.Hide()
        setValue = ''
        if self.sampleText.text != self.DEFAULTTEXT:
            setValue = self.sampleText.text
        self.width = 200
        self.height = 100
        self.textEdit = uicls.EditPlainText(parent=self, align=uiconst.TOALL, idx=0, pos=(0, 0, 0, 0))
        self.textEdit.HideBackground()
        self.textEdit.RemoveActiveFrame()
        uicore.registry.SetFocus(self.textEdit)
        self.textEdit.SetValue(setValue, cursorPos=len(setValue))
        self.sr.cookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEDOWN, self.OnGlobalMouseDown)

    def OnGlobalMouseDown(self, *args):
        mo = uicore.uilib.mouseOver
        if mo is self or uiutil.IsUnder(mo, self):
            return True
        if self.textEdit:
            val = self.textEdit.GetValue()
            self.sampleText.Show()
            self.sampleText.text = val or self.DEFAULTTEXT
            self.textEdit.Close()
            self.textEdit = None
        return False

    def ChangeColor(self, color):
        uicls.MoveableRect.ChangeColor(self, color)
        if getattr(self, 'sampleText', None):
            self.sampleText.SetTextColor(color)
            self.underlay.SetRGB(*color)
            self.underlay.color.a = 0.1

    def UpdateProportionalPosition(self, newScaling):
        parWidth, parHeight = self.parent.GetAbsoluteSize()
        pl, pr, pt, pb = self.proportionalPosition
        self.left = int(pl * parWidth)
        self.top = int(pt * parHeight)
        if newScaling == 1.0:
            self.sampleText.useSizeFromTexture = True
            self.sampleText.Layout()
            self.width = self.sampleText.textwidth + 16
            self.height = self.sampleText.textheight + 16


def GetServerVersion(serverBuild, serverVersion):
    return '%s - %s.%s' % (boot.codename, serverVersion, serverBuild)
