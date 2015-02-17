#Embedded file name: eve/client/script/util\publicQaToolsClient.py
import service

class PublicQaToolsClient(service.Service):
    __exportedcalls__ = {}
    __guid__ = 'svc.publicQaToolsClient'
    __servicename__ = 'publicQaToolsClient'
    __displayname__ = 'Public QA Tools Client'
    __dependencies__ = []
    __notifyevents__ = []
    __exportedcalls__ = {'MoveMeTo': [service.ROLE_IGB]}
    allowedSlashCommands = ['/moveme', '/copyskills']

    def MoveMeTo(self, destination, *args):
        try:
            sm.GetService('sessionMgr').PerformSessionChange('MoveMeTo', sm.RemoteSvc('publicQaToolsServer').MoveMeTo, destination)
        except UserError as e:
            if e.msg == 'SystemCheck_TransferFailed_Loading':
                eve.Message('CustomNotify', {'notify': 'Spooling up system. Please wait.'})
                blue.pyos.synchro.SleepSim(10000)
                sm.GetService('sessionMgr').PerformSessionChange('MoveMeTo', sm.RemoteSvc('publicQaToolsServer').MoveMeTo, destination)
            else:
                raise

    def SlashCmd(self, commandLine):
        sm.RemoteSvc('publicQaToolsServer').SlashCmd(commandLine)

    def CommandAllowed(self, commandLine):
        commandLine = commandLine.lower()
        for command in self.allowedSlashCommands:
            if commandLine.startswith(command):
                return True

        return False
