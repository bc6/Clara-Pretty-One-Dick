#Embedded file name: carbon/common/script/net\StacklessSocketServer.py
"""
  Define stackless extensions for the SocketServer functionality
"""
import SocketServer
import uthread

class UThreadingMixIn:
    """Mix-in class to handle each request in a new tasklet."""
    __guid__ = 'StacklessSocketServer.UThreadingMixIn'

    def process_request_tasklet(self, request, client_address):
        """Same as in BaseServer but as a tasklet.
        
        In addition, exception handling is done here.
        
        """
        try:
            self.finish_request(request, client_address)
            self.close_request(request)
        except:
            self.handle_error(request, client_address)
            self.close_request(request)

    def process_request(self, request, client_address):
        """Start a new tasklet to process the request."""
        t = uthread.new(self.process_request_tasklet, request, client_address)
        t.run()


class UThreadingTCPServer(UThreadingMixIn, SocketServer.TCPServer):
    __guid__ = 'StacklessSocketServer.UThreadingTCPServer'
