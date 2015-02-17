#Embedded file name: crestclient\userClient.py
from crestClient import CrestUserBase, CONTENT_TYPE
import requests
import requests.auth
import hashlib
import base64

class CrestUserLogin(CrestUserBase):

    def __init__(self, username, password, server, scope, client, secret):
        self.username = username
        self.password = password
        self.server = server
        self.scope = scope
        self.client = client
        self.secret = secret
        self._InitSession()

    def _InitSession(self):
        """
        Authenticates with the server , stores the session.
        """
        self.session = requests.session()
        self.session.verify = False
        self.session.auth = CrestAuth(self.username, self.password, self.server, self.scope, self.client, self.secret)


class CrestAuth(requests.auth.AuthBase):
    """
    Custom requests authentication handler, talks with the SSO and negotiates a new auth token.
    """

    def __init__(self, username, password, server, scope, client, secret, character = None):
        self.server = server
        self.username = username
        self.password = password
        self.scope = scope
        self.client = client
        self.secret = secret
        self.character = character
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

    def hash_password(self):
        """
        Returns a CREST compatible password hash.
        """
        salt = unicode(self.username).strip().lower().encode('utf_16_le')
        value = hashlib.sha1(unicode(self.password).encode('utf_16_le') + salt)
        for i in xrange(1000):
            value = hashlib.sha1(value.digest() + salt)

        return base64.b64encode(value.digest())

    def get_authorization(self):
        """
        Calls the SSO and updates our authorization token.
        """
        root = requests.get(self.server).json()
        body = {'grant_type': 'password',
         'scope': self.scope,
         'username': self.username,
         'password': self.hash_password(),
         'character': self.character}
        headers = {'Content-Type': CONTENT_TYPE,
         'Accept': 'vnd.ccp.eve.AuthenticateResponse-v1',
         'Authorization': 'Basic %s' % base64.b64encode('%s:%s' % (self.client, self.secret))}
        response = requests.post(root['authEndpoint']['href'], data=body, headers=headers)
        self.authorization = 'Bearer ' + response.json()['access_token']
        return self.authorization
