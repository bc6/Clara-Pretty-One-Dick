#Embedded file name: carbon/client/script/util\logsvc.py
import service

class LoggingSvc(service.Service):
    """
    Use through the utility functions in the lg namespace:
    
    import lg
    lg.Info(channel, *blah)
    """
    __guid__ = 'svc.log'
    __exportedcalls__ = {'Log': []}

    def Run(self, *etc):
        service.Service.Run(self, *etc)
        self.channels = {}

    def Stop(self, *etc):
        service.Service.Stop(self, *etc)
        self.channels = None

    def Log(self, channelName, flag, *what):
        if self.channels is not None:
            if channelName not in self.channels:
                import log
                self.channels[channelName] = log.GetChannel('nonsvc.' + channelName)
            if self.channels[channelName].IsOpen(flag):
                try:
                    self.channels[channelName].Log(u' '.join(map(unicode, what)).replace('\x00', '\\x00'), flag, 3)
                except:
                    pass
