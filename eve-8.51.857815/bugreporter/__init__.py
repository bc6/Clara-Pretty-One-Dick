#Embedded file name: bugreporter\__init__.py
"""
BugReporter handles communciation with the bugs service through the bugs service
REST api. 
"""
from bugreporter.util import GuessMimeType
import httplib2
import json
import mimetools
import logging
from cStringIO import StringIO

class BugReporter(object):

    def __init__(self, serverUrl, cacheFolder = None):
        if cacheFolder is None:
            cacheFolder = '.cache'
        self.cacheFolder = cacheFolder
        self.logger = logging.getLogger(__name__)
        self.baseUrl = serverUrl

    def GetCategories(self):
        ret = []
        for each in self._HttpGet('category')['categories']:
            ret.append((each['value'], each['id']))

        return ret

    def SendBugReport(self, categoryName, title, description, reproSteps, sessionInfo, computerInfo, userID, labels, server, build, files):
        data = self._GetData(categoryName, title, description, reproSteps, sessionInfo, computerInfo, userID, labels, server, build)
        response = self._HttpPost('issue', data)
        issueID = response['id']
        self._SendAttachments(issueID, files)
        return response

    def IsBugsServiceOnline(self):
        try:
            return self._HttpGet('status')['isOnline']
        except KeyError:
            return False
        except Exception:
            logging.exception('Bugs service not answering IsOnline')
            return False

    def _SendAttachments(self, issueID, files):
        try:
            for fileName, fileData in files:
                contentType, buffer = self._MultipartEncode(fileName, fileData)
                self._Request('attachment/{}'.format(issueID), 'POST', body=buffer, contentType=contentType)

        except Exception as e:
            self.logger.exception(e.message, *e.args)
            raise SendAttachmentError()

    def _MultipartEncode(self, fileName, fileData):
        boundary = mimetools.choose_boundary()
        buf = self._GetBufferForFile(boundary, fileData, fileName)
        contentType = self._GetContentTypeForFile(boundary)
        return (contentType, buf)

    def _GetContentTypeForFile(self, boundary):
        contentType = 'multipart/form-data; boundary={}'.format(boundary)
        return contentType

    def _GetBufferForFile(self, boundary, fileData, fileName):
        buf = StringIO()
        buf.write('--%s\r\n' % boundary)
        buf.write('Content-Disposition: form-data; name="File"; filename="%s"\r\n' % (fileName,))
        buf.write('Content-Type: %s\r\n' % GuessMimeType(fileName))
        buf.write('\r\n' + fileData + '\r\n')
        buf.write('--{}--\r\n'.format(boundary))
        buf = buf.getvalue()
        return buf

    def _GetData(self, categoryID, title, description, reproSteps, sessionInfo, computerInfo, userID, labels, server, build):
        description = '{} \n\nSession Info:\n{}'.format(description, sessionInfo)
        return {'categoryID': str(categoryID),
         'summary': title,
         'description': description,
         'reproductionSteps': reproSteps,
         'computerInfo': computerInfo,
         'originalReporterId': '{}'.format(userID),
         'Server': server,
         'Build': build,
         'labels': labels}

    def _HttpGet(self, urlAddition):
        return json.loads(self._Request(urlAddition, 'GET'))

    def _HttpPost(self, urlAddition, data):
        return json.loads(self._Request('issue', 'POST', json.dumps(data)))

    def _Request(self, urlAddition, method, body = None, contentType = None):
        self.logger.info("making a '%s' call to the bugs service '%s'", method, urlAddition)
        h = httplib2.Http(self.cacheFolder)
        url = '{}/{}'.format(self.baseUrl, urlAddition)
        if contentType is None:
            contentType = 'application/json'
        resp, content = h.request(url, method, body, headers={'content-type': contentType})
        self.CheckResponse(resp, method)
        return content

    def CheckResponse(self, resp, method):
        if method == 'POST' and resp['status'] not in ('200', '201'):
            self.logger.error('Error from bugs service: response: {}, status: {}'.format(resp, resp['status']))
            raise RuntimeError('Unexpected error from the bugs service')


class SendAttachmentError(Exception):
    pass


def SendTestBugReport(serverUrl):
    bugReporter = BugReporter(serverUrl, '.cache')
    categoryName, categoryID = bugReporter.GetCategories()[0]
    response = bugReporter.SendBugReport(categoryID, 'title', 'description', 'repro steps', 'sessionInfo', 'computerInfo', 'charID', ['UI'], [])
    print "Bug Report successfully created '{}'".format(response['self'])


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        SendTestBugReport(sys.argv[1])
