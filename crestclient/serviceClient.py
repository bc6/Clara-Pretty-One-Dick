#Embedded file name: crestclient\serviceClient.py
from crestClient import CrestUserBase, CONTENT_TYPE
import requests
import requests.auth
import base64

class CrestServiceSso(CrestUserBase):
    """
    Crest service session , auth with clientID and secret
    """

    def __init__(self, clientID, clientSecret, server, scope, verify = False, authUrl = None):
        super(CrestServiceSso, self).__init__()
        self.clientID = clientID
        self.clientSecret = clientSecret
        self.server = server
        self.scope = scope
        self.session = requests.session()
        self.authUrl = authUrl
        self.session.verify = verify
        self.session.auth = CrestServiceAuth(self.clientID, self.clientSecret, self.server, self.scope, authUrl)


class CrestServiceAuth(requests.auth.AuthBase):
    """
    called if the sso rejects our existing token , we use the refresh token to get a new one
    """

    def __init__(self, client, secret, server, scope, authUrl):
        self.clientID = client
        self.clientSecret = secret
        self.server = server
        self.scope = scope
        self.authUrl = authUrl
        self.authorization = None

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
        Calls the SSO and updates our authorization token.
        """
        if self.authUrl:
            authUrl = self.authUrl
        else:
            root = requests.get(self.server).json()
            authUrl = root['authEndpoint']['href']
        body = {'grant_type': 'client_credentials',
         'scope': self.scope}
        headers = {'Content-Type': CONTENT_TYPE,
         'Accept': 'vnd.ccp.eve.AuthenticateResponse-v1',
         'Authorization': 'Basic %s' % base64.b64encode('%s:%s' % (self.clientID, self.clientSecret))}
        response = requests.post(authUrl, data=body, headers=headers)
        self.authorization = 'Bearer ' + response.json()['access_token']
        return self.authorization
