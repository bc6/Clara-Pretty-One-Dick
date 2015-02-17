#Embedded file name: crestclient\crestClient.py
import requests
import requests.auth
import hashlib
import base64
import json
import time
import logging
from requests.exceptions import SSLError, ConnectionError
from errors import BadRequestException, ForbiddenException, ServiceUnavailableException
log = logging.getLogger('crestClient')
CONTENT_TYPE = 'application/x-www-form-urlencoded'
POST_CONTENT = 'application/json'
SAFE_RETRY_ERRORS = [requests.codes.service_unavailable,
 requests.codes.bad_gateway,
 requests.codes.gateway_timeout,
 requests.codes.request_timeout]
SAFE_RETRY_METHODS = ['GET', 'PUT', 'DELETE']
MAX_RETRIES = 3
SUCCESS_CODES = [requests.codes.ok, requests.codes.created]
APPLICATION_ERRORS = [requests.codes.service_unavailable,
 requests.codes.bad_gateway,
 requests.codes.gateway_timeout,
 requests.codes.request_timeout]
USER_ERRORS = [requests.codes.unauthorized,
 requests.codes.forbidden,
 requests.codes.not_found,
 requests.codes.conflict]

class CrestClient(object):

    def __init__(self):
        pass


class CrestUserBase(object):

    def __init__(self, languague = 'EN'):
        self.language = languague

    def Get(self, uri, accept = None, returnHeader = False, retries = 0, **kwargs):
        """
        Sends a Get request to the server, tries to return json
        """
        headers = self._handle_headers(accept, uri)
        try:
            response = self.session.get(uri, headers=headers, **kwargs)
            return self._handle_response(response, returnHeader=returnHeader)
        except ConnectionError as e:
            if retries < MAX_RETRIES:
                return self.Get(uri, accept=accept, returnHeader=returnHeader, retries=(retries + 1), **kwargs)
            log.error(str(e))
            raise ServiceUnavailableException(str(e))

    def Post(self, uri, content = None, payload = None, returnHeader = False, retries = 0, **kwargs):
        """
        sends a Post request to the server, tries to return json
        """
        headers = self._handle_post_headers(content, uri)
        json_payload = json.dumps(payload)
        try:
            return self._handle_response(self.session.post(uri, json_payload, headers=headers), returnHeader=returnHeader)
        except ConnectionError as e:
            if retries < MAX_RETRIES:
                return self.Post(uri, content=content, payload=payload, returnHeader=returnHeader, retries=(retries + 1), **kwargs)
            log.error(str(e))
            raise ServiceUnavailableException(str(e))

    def _handle_response(self, response, returnHeader = False, retry = 0):
        """
        Handle the reponse from the server , retry if it is safe else pass on the exception
        returnHeader decides if we should return the response headers, mostly needed for location in post requests
        """
        if response.request.method in SAFE_RETRY_METHODS and response.status_code in SAFE_RETRY_ERRORS and retry < MAX_RETRIES:
            response.raw.release_conn()
            log.info('Retry : sleeping for %s secs' % (retry * 3 + 1))
            time.sleep(retry * 3 + 1)
            return self._handle_response(response.connection.send(response.request), returnHeader=returnHeader, retry=retry + 1)
        return self._return_response(response, returnHeader)

    def _return_response(self, response, returnHeader = False):
        """
        returns the response object if the call was successful else raises the appropriate error
        """
        if response.status_code in SUCCESS_CODES:
            try:
                if returnHeader:
                    return (response.headers, response.json())
                return response.json()
            except ValueError:
                if returnHeader:
                    return (response.headers, {'text': response.text})
                else:
                    return {'text': response.text}

        elif response.status_code in APPLICATION_ERRORS:
            raise ServiceUnavailableException(response.text)
        elif response.status_code in USER_ERRORS:
            raise ForbiddenException(response.text)
        else:
            raise BadRequestException(response.text)

    def _handle_headers(self, accept, uri):
        """
        create correct headers for Get requests
        """
        headers = {}
        headers.update(self.session.headers)
        if accept:
            headers['Accept'] = 'application/%s+json' % accept
        else:
            log.error('Accept MimeType missing in request for %s' % uri)
        headers['X-CCP-Strict'] = '1'
        headers['Content-Type'] = CONTENT_TYPE
        headers['Accept-Language'] = self.language
        return headers

    def _handle_post_headers(self, content, uri):
        """
        Create correct headers for post requests
        """
        headers = {}
        headers.update(self.session.headers)
        if content:
            headers['Content-Type'] = 'application/%s+json' % content
        else:
            log.error('Content MimeType missing in request for %s' % uri)
            headers['Content-Type'] = POST_CONTENT
        headers['X-CCP-Strict'] = '1'
        return headers
