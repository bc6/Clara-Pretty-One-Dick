#Embedded file name: crestclient\tokenClient.py
from crestClient import CrestUserBase
import requests
import requests.auth

class CrestUserSso(CrestUserBase):
    """
    Crest user session , authenticated with an existing token
    """

    def __init__(self, token, server, verify = False, language = 'EN'):
        super(CrestUserSso, self).__init__(language)
        self.session = requests.session()
        self.server = server
        self.session.verify = verify
        self.session.keep_alive = False
        self.session.auth = CrestRefreshAuth(token)


class CrestRefreshAuth(requests.auth.AuthBase):
    """
    called if the sso rejects our existing token , we use the refresh token to get a new one
    """

    def __init__(self, token):
        self.authorization = 'Bearer ' + token

    def __call__(self, request):
        if self.authorization:
            request.headers['Authorization'] = self.authorization
        request.register_hook('response', self.handle_response)
        return request

    def handle_response(self, response, **kwargs):
        """
        Checks for an authorized response and fetches a new token from the SSO.
        """
        if response.status_code == requests.codes.unauthorized:
            response.content
            response.raw.release_conn()
            response.request.headers['Authorization'] = self.get_authorization()
            new_response = response.connection.send(response.request, **kwargs)
            new_response.history.append(response)
            return new_response
        return response

    def get_authorization(self):
        """
        No refresh needed for now , token is valid for 24 hours
        """
        return self.authorization
