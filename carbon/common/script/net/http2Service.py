#Embedded file name: carbon/common/script/net\http2Service.py
"""
http2 service module
A service for plugging together cherrypy ESP web app and WSGIService http server.

Note that this is far from being complete. It's merely a step in migrating our vast
amount of server pages to a brave new future.

"""
import service, macho

class CherryServer(service.Service):
    __guid__ = 'svc.http2'
    __startupdependencies__ = ['machoNet', 'WSGIService']
    __exportedcalls__ = {}
    __configvalues__ = {}
    __notifyevents__ = []

    def Run(self, memStream = None):
        self.servers = []
        if not prefs.GetValue('http2', 1):
            self.LogNotice('http2 service not booting up CherryPy ESP app because prefs.http2=0')
            return
        from httpServer import InitializeEspApp
        cherryTree = InitializeEspApp()
        transport_key = 'tcp:raw:http2' if prefs.GetValue('httpServerMode', 'ccp').lower() == 'ccp' else 'tcp:raw:http'
        port = self.machoNet.GetBasePortNumber() + macho.offsetMap[macho.mode][transport_key]
        server = self.WSGIService.StartServer(cherryTree, port)
        self.servers.append(server)
        self.LogNotice('CherryPy ESP app server running on port %s' % port)

    def Stop(self, memStream):
        for server in self.servers:
            self.WSGIService.StopServer(server)
