#Embedded file name: carbon/common/script/net\GPS.py
"""
G packet service interfaces for those who need'm.
Basically you have a full fledged uniform interface for all
the relevant shei e in yer standard packet based transport.
"""
import blue
import carbon.common.script.net.machobase as macho
import evecrypto.crypto as Crypto
import uthread
import sys
import util
import log
import types
import marshal
import const
import localization
Enter = blue.pyos.taskletTimer.EnterTasklet
Leave = blue.pyos.taskletTimer.ReturnFromTasklet
from carbon.common.script.net.GPSExceptions import *
from carbon.common.script.net.machoNetExceptions import UserRejectedByVIP
import socket
ClientConnectFailed = socket.error

def ClientConnectFailedString(e):
    return e.args[1]


def GetHostByName_Ex(host):
    return socket.gethostbyname_ex(host)[2]


def GetAddrInfo(host):
    return [ e[4][0] for e in socket.getaddrinfo(host, None) if e[0] == socket.AF_INET and not e[4][0].startswith('0.') ]


error = socket.error
gethostname = socket.gethostname
exports = {'gps.ClientConnectFailed': ClientConnectFailed,
 'gps.ClientConnectFailedString': ClientConnectFailedString}

class GPSTransportFactory(object):
    __guid__ = 'gps.GPSTransportFactory'

    def __init__(self, useacl = 0, name = '(unknown)'):
        self.useACL = useacl
        self.name = name

    def Listen(self, address):
        pass

    def Connect(self, address):
        pass


class GPSAddressable(object):
    """
        A GPSAddressable object represents something that has an address and thus
        useful functions that addresses generally need.
    
        The self.address variable must be set by the real class dude.
    """

    def GetAddress(self):
        """
            returns the transport's address
        """
        return self.address

    def GetESPAddress(self):
        """
            returns the transport's external address
        """
        return self.__GetPrefixedAddress('externalNetPrefix', natOffset=True)

    def GetExternalAddress(self):
        """
            returns the transport's external address
        """
        return self.__GetPrefixedAddress('externalNetPrefix')

    def GetInternalAddress(self):
        """
            returns the transport's internal address
        """
        return self.__GetPrefixedAddress('internalNetPrefix')

    def __GetPrefixedAddress(self, prefixWhat, natOffset = False):
        host, port = self.address.split(':')
        addresses = GetAddrInfo(host)
        find = [prefixWhat + '_' + macho.mode, prefixWhat, 'externalNetPrefix']
        for prefValue in find:
            prefix = str(prefs.GetValue(prefValue, ''))
            if prefix:
                break

        if prefix:
            if not prefs.GetValue('enableNewStyleNetworkPrefix', False):
                lastDot = addresses[0].rindex('.')
                ipaddress = prefix + addresses[0][lastDot + 1:]
                if len(ipaddress.split('.')) != 4:
                    raise RuntimeError('Configuration Error:  %s MUST contain precisely three dots' % prefixWhat)
            elif prefValue == 'externalNetPrefix_proxy':
                lastDot = addresses[0].rindex('.')
                lastBit = int(addresses[0][lastDot + 1:])
                if natOffset:
                    lastBit += int(prefs.GetValue('externalNetNatOffset', 0))
                ipaddress = prefix + str(lastBit)
                if len(ipaddress.split('.')) != 4:
                    raise RuntimeError('Configuration Error:  %s MUST contain precisely three dots' % prefixWhat)
            else:
                found = False
                for ipaddress in GetHostByName_Ex(''):
                    if ipaddress.startswith(prefix):
                        found = True
                        break

                if not found:
                    raise RuntimeError('Configuration Error:  unable to find IP for %s using prefix %s ' % (prefixWhat, prefix))
        elif len(addresses) == 1 or prefs.clusterMode not in ('LIVE', 'TEST'):
            addresses.sort()
            ipaddress = addresses[0]
        else:
            raise RuntimeError("Configuration Error:  Multiple potential %s addresses, couldn't determine which one to use." % prefixWhat)
        return '%s:%s' % (ipaddress, port)


class GPSTransportAcceptor(GPSAddressable):
    __guid__ = 'gps.GPSTransportAcceptor'

    def __init__(self, useACL):
        self.useACL = useACL

    def CheckACL(self, address):
        if self.useACL:
            return sm.services['machoNet'].CheckACL(address)

    def Accept(self):
        return None

    def Close(self, reason = None, reasonCode = None, reasonArgs = {}):
        pass


class GPSTransport(GPSAddressable):
    __guid__ = 'gps.GPSTransport'
    __mandatory_fields__ = []

    def __init__(self, *args, **keywords):
        self.cryptoContext = Crypto.CryptoCreateContext()
        self.handShakePaddingLength = boot.GetValue('handShakePaddingLength', 64)
        self.handShake = None

    def Read(self):
        pass

    def Write(self, packet):
        pass

    def Close(self, reason = None, reasonCode = None, reasonArgs = {}):
        pass

    def IsClosed(self):
        return True

    def ApplyWithTimeout(self, func, args, timeout = 120, message = None):
        rts = [0]
        t = uthread.worker('machoNet::TimeoutWorker', self.TimeoutWorker, self, timeout, rts, message)
        try:
            ret = apply(func, args)
        finally:
            rts[0] = 1
            t.kill()

        return ret

    @staticmethod
    def TimeoutWorker(transport, secs, rts, message = None):
        try:
            blue.pyos.synchro.SleepWallclock(1000 * secs)
            if not rts[0]:
                transport.Close(*message)
        except TaskletExit:
            pass

    def HandleClientAuthentication(self, loggedOnUserCount, transportID, counter, sessionID, eveInVIP):
        """
        The (proxy) server-side of the client authentication protocol. 'loggedOnUserCouunt' is the number
        of users logged into entire cluster, 'transportID' ID of connecting transport, 'sessionID' is the
        transport's (fresh, new) sessionID, 'counter' the number of times the transport has entered the
        authentication protocol before this call.
        """
        timer = Enter('machoNet::GPS::HandleClientAuthentication')
        try:
            try:
                updateInfo = sm.GetService('machoNet').GetValidClientCodeHash()
            except:
                log.general.Log('Clienthash info not available', log.LGINFO)
                updateInfo = const.responseUnknown

            response = (170472,
             macho.version,
             loggedOnUserCount,
             boot.version,
             boot.build,
             str(boot.codename) + '@' + str(boot.region),
             updateInfo)
            self.UnEncryptedWrite(macho.Dumps(response))
            message = (localization.GetByLabel('/Carbon/GPS/ConnectionTimeoutClientNotCompatible'), 'HANDSHAKE_TIMEOUT_CLIENTCOMPATIBILITYHANDSHAKE')
            handshakeTimeout = prefs.GetValue('GpsCompatibilityHandshakeTimeout', 120) * (10 if counter else 1)
            log.general.Log('GPS[%d]: HandleClientAuthentication waiting for handshake (timeout=%ds, counter=%d)' % (transportID, handshakeTimeout, counter), log.LGINFO)
            response = macho.Loads(self.ApplyWithTimeout(self.UnEncryptedRead, (), message=message, timeout=handshakeTimeout))
            if '@' in response[5]:
                codename, region = response[5].split('@')
            else:
                codename, region = response[5], ''
            if str(boot.region) != region:
                if boot.role == 'client':
                    log.general.Log('Handshake Failed - Insecure Region Code Mismatch (common.ini:region) - Server: %s  - Client: %s' % (region, str(boot.region)), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleRegion'), 'HANDSHAKE_INCOMPATIBLEREGION')
                return 'ERR'
            if str(boot.codename) != codename:
                log.general.Log('Handshake Failed - Insecure Boot Code Name Mismatch (common.ini:codename) - Server: %s - Client: %s' % (codename, str(boot.codename)), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleRelease'), 'HANDSHAKE_INCOMPATIBLERELEASE')
                return 'ERR'
            if boot.version != response[3]:
                log.general.Log('Handshake Failed - Insecure Boot Version Mismatch (common.ini:version) - Server: %s - Client: %s' % (response[3], boot.version), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleVersion'), 'HANDSHAKE_INCOMPATIBLEVERSION')
                return 'ERR'
            if macho.version != response[1]:
                log.general.Log('Handshake Failed - Insecure Macho Version Mismatch - Server: %s - Client: %s' % (response[1], macho.version), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleProtocol'), 'HANDSHAKE_INCOMPATIBLEPROTOCOL')
                return 'ERR'
            if boot.build > response[4]:
                log.general.Log('Handshake Failed - Insecure Boot Build Mismatch (common.ini:build) - Server: %s - Client: %s' % (response[4], boot.build), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleBuild'), 'HANDSHAKE_INCOMPATIBLEBUILD')
                return 'ERR'
            log.general.Log('LLV Reading Client Crypto Context OR VIP Key OR Queue Check', log.LGINFO)
            vipKey = None
            message = (localization.GetByLabel('/Carbon/GPS/ConnectionTimeoutNoCompatibilityHandshake'), 'HANDSHAKE_TIMEOUT_CLIENTSECUREHANDSHAKE')
            clientCryptoContextPacket = macho.Loads(self.ApplyWithTimeout(self.UnEncryptedRead, (), message=message))
            if clientCryptoContextPacket[0] is None and clientCryptoContextPacket[1] == 'VK':
                vipKey = clientCryptoContextPacket[2]
            if clientCryptoContextPacket[0] is None and clientCryptoContextPacket[1] == 'VK':
                log.general.Log('LLV Reading Client Crypto Context OR Queue Check', log.LGINFO)
                message = (localization.GetByLabel('/Carbon/GPS/ConnectionTimeoutNoCompatibilityHandshake'), 'HANDSHAKE_TIMEOUT_CLIENTSECUREHANDSHAKE')
                clientCryptoContextPacket = macho.Loads(self.ApplyWithTimeout(self.UnEncryptedRead, (), message=message))
            if counter == 0:
                sm.GetService('machoNet').PutTransportInLogonQueue(transportID)
            logonQueuePosition = sm.GetService('machoNet').GetLogonQueuePosition(transportID, vipKey)
            if clientCryptoContextPacket[0] is None and clientCryptoContextPacket[1] == 'QC':
                if eveInVIP:
                    self.Close(localization.GetByLabel('/Carbon/GPS/NotAcceptingConnections'), 'ACL_NOTACCEPTING')
                    return 'OK'
                log.general.Log('Logon Queue Position Query - Complete', log.LGINFO)
                self.UnEncryptedWrite(macho.Dumps(logonQueuePosition))
                return 'OK'
            log.general.Log('LLV Reading Client Crypto Context', log.LGINFO)
            keyVersion, request = clientCryptoContextPacket
            if keyVersion != getattr(macho, 'publicKeyVersion', 'placebo'):
                log.general.Log('Handshake Failed - Public Key Mismatch - Public Key Version is %s but should be %s' % (keyVersion, getattr(macho, 'publicKeyVersion', 'placebo')), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatiblePublicKey'), 'HANDSHAKE_INCOMPATIBLEPUBLICKEY')
                return 'ERR'
            log.general.Log('LLV Initializing Crypto Context', log.LGINFO)
            request = self.cryptoContext.Initialize(request)
            if type(request) != types.DictType:
                self.Close('Handshake Failed - ' + request)
                return 'ERR'
            self.UnEncryptedWrite(macho.Dumps('OK CC'))
            passwordVersion = 0
            userName = None
            passwordVersionOK = False
            passwordVersionAttempteRemaining = 2
            while not passwordVersionOK:
                if passwordVersionAttempteRemaining < 1:
                    self.Close('Password version handshake failure')
                    return 'ERR'
                passwordVersionAttempteRemaining -= 1
                log.general.Log('LLV Reading Secure Client Handshake', log.LGINFO)
                message = (localization.GetByLabel('/Carbon/GPS/ConnectionTimeoutNoCompatibilityHandshake'), 'HANDSHAKE_TIMEOUT_CLIENTSECUREHANDSHAKE')
                clientChallenge, request2 = macho.Loads(self.ApplyWithTimeout(self.EncryptedRead, (), message=message))
                request.update(request2)
                log.general.Log('LLV Verifying Secure Client Handshake', log.LGINFO)
                for k in self.__mandatory_fields__:
                    if k not in request:
                        self.Close('Handshake corrupt, missing %s' % k)
                        return 'ERR'

                if passwordVersion == 0 or userName != request['user_name']:
                    passwordVersion = 2
                    userName = request['user_name']
                if passwordVersionAttempteRemaining == 1:
                    log.general.Log('LLV Writing password version', log.LGINFO)
                    self.EncryptedWrite(macho.Dumps(passwordVersion))
                if passwordVersion == 1:
                    if request['user_password'] is not None:
                        passwordVersionOK = True
                else:
                    passwordVersionOK = True

            log.general.Log('LLV Performing Version Check', log.LGINFO)
            if str(boot.region) != request['boot_region']:
                log.general.Log('Handshake Failed - Boot Region Mismatch - Boot Region is %s but should be %s' % (request['boot.region'], str(boot.region)), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleRegion'), 'HANDSHAKE_INCOMPATIBLEREGION')
                return 'ERR'
            if str(boot.codename) != request['boot_codename']:
                log.general.Log('Handshake Failed - Boot Code Name Mismatch - Boot Code Name is %s but should be %s' % (request['boot.codeName'], str(boot.codename)), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleRelease'), 'HANDSHAKE_INCOMPATIBLERELEASE')
                return 'ERR'
            if boot.version != request['boot_version']:
                log.general.Log('Handshake Failed - Boot Version Mismatch - Boot Version is %s but should be %s' % (request['boot.version'], boot.version), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleVersion'), 'HANDSHAKE_INCOMPATIBLEVERSION')
                return 'ERR'
            if macho.version != request['macho_version']:
                log.general.Log('Handshake Failed - Macho Version Mismatch - Macho Version is %s but should be %s' % (request['macho.version'], macho.version), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleProtocol'), 'HANDSHAKE_INCOMPATIBLEPROTOCOL')
                return 'ERR'
            if boot.build > request['boot_build']:
                log.general.Log('Handshake Failed - Boot Build Mismatch - Boot Build is %s but should be at least %s' % (request['boot.build'], boot.build), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleBuild'), 'HANDSHAKE_INCOMPATIBLEBUILD')
                return 'ERR'
            if len(clientChallenge) != self.handShakePaddingLength:
                self.Close(localization.GetByLabel('/Carbon/GPS/IncorrentHandshakePadding', current=len(clientChallenge), expected=self.handShakePaddingLength))
                return 'ERR'
            handShakeHash = Crypto.CryptoHash(clientChallenge)
            try:
                globalConfig = sm.GetService('machoNet').GetGlobalConfig()
            except:
                log.LogException()
                globalConfig = {}

            log.general.Log('LLV Generating Server Challenge', log.LGINFO)
            dict = {'challenge_responsehash': handShakeHash,
             'macho_version': macho.version,
             'boot_version': boot.version,
             'boot_build': boot.build,
             'boot_codename': str(boot.codename),
             'boot_region': str(boot.region),
             'cluster_usercount': loggedOnUserCount,
             'proxy_nodeid': sm.GetService('machoNet').GetNodeID(),
             'user_logonqueueposition': logonQueuePosition,
             'config_vals': globalConfig}
            serverChallenge = Crypto.GetRandomBytes(self.handShakePaddingLength)
            log.general.Log('LLV Crypting Server Challenge', log.LGINFO)
            import handshake
            code = marshal.dumps(handshake.GetHandshakeFunc())
            ch = (serverChallenge,
             Crypto.Sign(code),
             {},
             dict)
            log.general.Log('LLV Writing Server Challenge', log.LGINFO)
            self.EncryptedWrite(macho.Dumps(ch))
            if not request['user_name'] or not (request['user_password'] or request['user_password_hash']) or logonQueuePosition > 1:
                return 'OK'
            if vipKey and vipKey != Crypto.CryptoHash(util.CaseFold(request['user_name'] or '')):
                self.Close(localization.GetByLabel('/Carbon/GPS/HandshakeFailedVIPKey'))
                return 'ERR'
            log.general.Log('LLV Reading Client Challenge-Response', log.LGINFO)
            message = (localization.GetByLabel('/Carbon/GPS/ConnectionTimeoutClientTimeout'), 'HANDSHAKE_TIMEOUT_CLIENTRESPONSETOSERVERCHALLENGE')
            challengeResponse, funcOutput, funcResult = macho.Loads(self.ApplyWithTimeout(self.EncryptedRead, (), message=message))
            if challengeResponse != Crypto.CryptoHash(serverChallenge):
                self.Close(localization.GetByLabel('/Carbon/GPS/HandshakeFailedHashMismatch'))
                return 'ERR'
            verification = handshake.Verify(funcOutput, funcResult, request)
            if verification is not None:
                self.Close(localization.GetByLabel('/Carbon/GPS/HandshakeFailedVerificationFailure', verification=verification), 'HANDSHAKE_FAILEDVERIFICATION')
                return 'ERR'
            request['handshakefunc_output'] = funcOutput
            request['handshakefunc_result'] = funcResult
            try:
                authenticationResult = sm.GetService('machoNet').Authenticate(self, request, sessionID)
                request.update(authenticationResult)
            except UserRejectedByVIP:
                if not sm.GetService('machoNet').IsClusterShuttingDown():
                    log.general.Log("Handshake Failed - VIP Check - The cluster is running in VIP mode, and you're not kewl", log.LGINFO)
                self.Close(localization.GetByLabel('/Carbon/GPS/NotAcceptingConnections'), 'ACL_NOTACCEPTING')
                return 'OK'
            except UserError as e:
                self.Close(e.msg, e.msg, e.dict)
                return 'ERR'
            except RuntimeError as e:
                self.Close(e.msg, e.msg, e.dict)
                return 'ERR'
            except Exception:
                log.LogException('Handshake Failed - Server Failure')
                self.Close(localization.GetByLabel('/Carbon/GPS/HandshakeFailedServerFailure'))
                return 'ERR'

            authenticationResult['live_updates'] = sm.GetService('liveUpdateMgr').GetLiveUpdates(request)
            authenticationResult['client_hash'] = sm.GetService('machoNet').GetValidClientCodeHash()
            log.general.Log('LLV Writing Server Challenge-Response-Ack', log.LGINFO)
            self.EncryptedWrite(macho.Dumps(authenticationResult))
            log.general.Log('LLV Succeeded', log.LGINFO)
            self.handShake = request
            return request
        finally:
            Leave(timer)

    def Authenticate(self, username, password, token):
        """
        The client-side of the client authentication protocol. 'token' is an SSO auth token or None,
        """
        timer = Enter('machoNet::GPS::Authenticate')
        try:
            message = (localization.GetByLabel('/Carbon/GPS/ConnectionTimeoutNoCompatibilityHandshake'), 'HANDSHAKE_TIMEOUT_FAILEDSERVERINITIATECOMPATIBILITYHANDSHAKE')
            response = macho.Loads(self.ApplyWithTimeout(self.UnEncryptedRead, (), message=message))
            insecresp = {'macho_version': response[1],
             'cluster_usercount': response[2],
             'boot_version': response[3],
             'boot_build': response[4],
             'update_info': response[6]}
            if '@' in response[5]:
                insecresp['boot_codename'], insecresp['boot_region'] = response[5].split('@')
            else:
                insecresp['boot_codename'], insecresp['boot_region'] = response[5], ''
            if str(boot.region) != insecresp['boot_region']:
                log.general.Log('Handshake Failed - Insecure Boot Region Mismatch (common.ini:region) - Server: %s  - Client: %s' % (insecresp['boot_region'], str(boot.region)), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleRegion'), 'HANDSHAKE_INCOMPATIBLEREGION')
                raise GPSTransportClosed(localization.GetByLabel('/Carbon/GPS/IncompatibleRegion'), 'HANDSHAKE_INCOMPATIBLEREGION', machoVersion=response[1], version=response[3], build=response[4], codename=insecresp['boot_codename'], region=insecresp['boot_region'], loggedOnUserCount=response[2])
            if str(boot.codename) != insecresp['boot_codename']:
                log.general.Log('Handshake Failed - Insecure Boot Code Name Mismatch  (common.ini:codename) - Server: %s - Client: %s' % (insecresp['boot_codename'], str(boot.codename)), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleRelease'), 'HANDSHAKE_INCOMPATIBLERELEASE')
                raise GPSTransportClosed(localization.GetByLabel('/Carbon/GPS/IncompatibleRelease'), 'HANDSHAKE_INCOMPATIBLERELEASE', machoVersion=response[1], version=response[3], build=response[4], codename=insecresp['boot_codename'], region=insecresp['boot_region'], loggedOnUserCount=response[2])
            if boot.version != response[3]:
                log.general.Log('Handshake Failed - Insecure Boot Version Mismatch (common.ini:version) - Server: %s - Client: %s' % (response[3], boot.version), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleVersion'), 'HANDSHAKE_INCOMPATIBLEVERSION')
                raise GPSTransportClosed(localization.GetByLabel('/Carbon/GPS/IncompatibleVersion'), 'HANDSHAKE_INCOMPATIBLEVERSION', machoVersion=response[1], version=response[3], build=response[4], codename=insecresp['boot_codename'], region=insecresp['boot_region'], loggedOnUserCount=response[2])
            if macho.version != response[1]:
                log.general.Log('Handshake Failed - Insecure Macho Version Mismatch - Server: %s - Client: %s' % (response[1], macho.version), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleProtocol'), 'HANDSHAKE_INCOMPATIBLEPROTOCOL')
                raise GPSTransportClosed(localization.GetByLabel('/Carbon/GPS/IncompatibleProtocol'), 'HANDSHAKE_INCOMPATIBLEPROTOCOL', machoVersion=response[1], version=response[3], build=response[4], codename=insecresp['boot_codename'], region=insecresp['boot_region'], loggedOnUserCount=response[2])
            if boot.build < response[4]:
                log.general.Log('Handshake Failed - Insecure Boot Build Mismatch (common.ini:build) - Server: %s - Client: %s' % (response[4], boot.build), log.LGERR)
                self.Close(localization.GetByLabel('/Carbon/GPS/IncompatibleBuild'), 'HANDSHAKE_INCOMPATIBLEBUILD')
                raise GPSTransportClosed(localization.GetByLabel('/Carbon/GPS/IncompatibleBuild'), 'HANDSHAKE_INCOMPATIBLEBUILD', machoVersion=response[1], version=response[3], build=response[4], codename=insecresp['boot_codename'], region=insecresp['boot_region'], loggedOnUserCount=response[2])
            request = (170472,
             macho.version,
             0,
             boot.version,
             boot.build,
             str(boot.codename) + '@' + str(boot.region))
            self.UnEncryptedWrite(macho.Dumps(request))
            if username:
                self.UnEncryptedWrite(macho.Dumps((None, 'VK', Crypto.CryptoHash(util.CaseFold(username)))))
            if username is None:
                self.UnEncryptedWrite(macho.Dumps((None, 'QC')))
                message = (localization.GetByLabel('/Carbon/GPS/ConnectionTimeoutNoCompatibilityHandshake'), 'HANDSHAKE_TIMEOUT_FAILEDSERVERINITIATECOMPATIBILITYHANDSHAKE')
                logonQueuePosition = macho.Loads(self.ApplyWithTimeout(self.UnEncryptedRead, (), message=message))
                sm.GetService('machoNet').SetLogonQueuePosition(logonQueuePosition)
                return insecresp
            log.general.Log('LLV Initializing Crypto Context', log.LGINFO)
            request = self.cryptoContext.Initialize()
            if type(request) != types.DictType:
                log.general.Log('LLV Crypto Init Context failure: ' + request, log.LGERR)
                self.Close('Crypto Initialization Failure')
                raise GPSTransportClosed(localization.GetByLabel('/Carbon/GPS/IncompatibleBuild'), 'HANDSHAKE_INCOMPATIBLEBUILD', loggedOnUserCount=response[2])
            log.general.Log('LLV Sending Encrypted Session Key', log.LGINFO)
            self.UnEncryptedWrite(macho.Dumps((getattr(macho, 'publicKeyVersion', 'placebo'), request)))
            message = (localization.GetByLabel('/Carbon/GPS/ConnectionTimeoutClientNotCompatible'), 'HANDSHAKE_TIMEOUT_CLIENTCOMPATIBILITYHANDSHAKE')
            macho.Loads(self.ApplyWithTimeout(self.UnEncryptedRead, (), message=message))
            log.general.Log('LLV Generating Secure Client Handshake', log.LGINFO)
            affiliateID = 0
            try:
                aidfile = blue.ResFile()
                if aidfile.Open('res:/aid.txt'):
                    affiliateID = int(str(aidfile.Read()))
                else:
                    log.general.Log('No aid.txt file present in res directory.', log.LGINFO)
            except StandardError:
                log.general.Log('No affiliate ID present, or failed to read aid.txt', log.LGERR)
                sys.exc_clear()

            dict = {'macho_version': macho.version,
             'boot_version': boot.version,
             'boot_build': boot.build,
             'boot_codename': str(boot.codename),
             'boot_region': str(boot.region),
             'user_name': username,
             'user_password': None,
             'user_password_hash': macho.PasswordHash(username, password),
             'user_languageid': prefs.GetValue('languageID', 'EN'),
             'user_affiliateid': affiliateID,
             'user_sso_token': token}
            clientChallenge = Crypto.GetRandomBytes(self.handShakePaddingLength)
            log.general.Log('LLV Writing Secure Client Handshake', log.LGINFO)
            self.EncryptedWrite(macho.Dumps((clientChallenge, dict)))
            log.general.Log('LLV Reading password version', log.LGINFO)
            message = (localization.GetByLabel('/Carbon/GPS/ConnectionTimeoutServerTimeout'), 'HANDSHAKE_TIMEOUT_SERVERSECUREHANDSHAKE')
            passwordVersion = macho.Loads(self.ApplyWithTimeout(self.EncryptedRead, (), message=message))
            if passwordVersion == 1:
                dict['user_password'] = password
                dict['user_password_hash'] = None
                log.general.Log('LLV Writing Secure Client Handshake (Attempt 2)', log.LGINFO)
                self.EncryptedWrite(macho.Dumps((clientChallenge, dict)))
            log.general.Log('LLV Reading Crypted Server Handshake', log.LGINFO)
            message = (localization.GetByLabel('/Carbon/GPS/ConnectionTimeoutServerTimeout'), 'HANDSHAKE_TIMEOUT_SERVERSECUREHANDSHAKE')
            serverChallenge, signedFunc, context, response = macho.Loads(self.ApplyWithTimeout(self.EncryptedRead, (), message=message))
            log.general.Log('LLV Verifying Response Hash', log.LGINFO)
            if response['challenge_responsehash'] != Crypto.CryptoHash(clientChallenge):
                self.Close("Server response signature incorrect, the server's crypto hash wasn't correct")
                raise GPSTransportClosed("Server response signature incorrect, the server's crypto hash wasn't correct", loggedOnUserCount=response[2])
            if response.get('user_logonqueueposition', 0) >= 2:
                sm.GetService('machoNet').SetLogonQueuePosition(response['user_logonqueueposition'])
                raise UserError('AutLogonFailureTotalUsers', {'position': response['user_logonqueueposition']})
            try:
                sm.GetService('machoNet').UpdateGlobalConfig(response.get('config_vals', {}))
            except:
                log.LogException()

            outputBuffer, funcResult = self.__Execute(signedFunc, context)
            log.general.Log('LLV Writing Secure Challenge-Response', log.LGINFO)
            self.EncryptedWrite(macho.Dumps((Crypto.CryptoHash(serverChallenge), outputBuffer, funcResult)))
            log.general.Log('LLV Reading Ack to Challenge-Response', log.LGINFO)
            message = (localization.GetByLabel('/Carbon/GPS/ConnectionTimeoutChallengeFailure'), 'HANDSHAKE_TIMEOUT_SERVERRESPONSETOCLIENTCHALLENGE')
            crAck = macho.Loads(self.ApplyWithTimeout(self.EncryptedRead, (), message=message))
            if not crAck:
                self.Close("Server didn't ACK our Challenge-Response")
                raise GPSTransportClosed(localization.GetByLabel('/Carbon/GPS/ChallengeResponseNotAcknowledged'), loggedOnUserCount=response[2])
            response.update(crAck)
            if 'live_updates' in response:
                live_updates = response['live_updates']
                del response['live_updates']
                for theUpdate in live_updates:
                    sm.ScatterEvent('OnLiveClientUpdate', theUpdate.code)

            log.general.Log('LLV Succeeded', log.LGINFO)
            self.handShake = response
            return response
        finally:
            Leave(timer)

    def __Execute(self, signedFunc, context):
        marshaled, verified = Crypto.Verify(signedFunc)
        if not verified:
            raise RuntimeError('Failed to verify initial function blobs')
        func = marshal.loads(marshaled)

        class WriteBuffer:

            def __init__(self):
                self.buffer = ''

            def write(self, text):
                self.buffer += text

        output = WriteBuffer()
        temp = sys.stdout
        temp2 = sys.stderr
        sys.stdout = output
        sys.stderr = output
        try:
            if macho.mode != 'client':
                raise RuntimeError('H4x0r won by calling GPS::__Execute on the server :(')
            funcResult = eval(func, globals(), context)
        except:
            funcResult = {}
            import traceback
            exctype, exc, tb = sys.exc_info()
            try:
                traceback.print_exception(exctype, exc, tb)
            finally:
                exctype = None
                exc = None
                tb = None

            sys.exc_clear()
        finally:
            sys.stdout = temp
            sys.stderr = temp2

        return (output.buffer, funcResult)

    def EncryptedRead(self):
        cryptedPacket = self.UnEncryptedRead()
        return self.cryptoContext.SymmetricDecryption(cryptedPacket)

    def EncryptedWrite(self, packet, header = None):
        encryptedPacket = self.cryptoContext.SymmetricEncryption(packet)
        return self.UnEncryptedWrite(encryptedPacket, header)

    def CreateClosedPacket(self, reason, reasonCode = None, reasonArgs = {}, exception = None):
        msg = 'Creating Closed Packet: ' + reason
        if exception:
            msg += ' exception:' + repr(exception)
        log.general.Log(msg, log.LGINFO)
        etype = GPSRemoteTransportClosed
        etype = GPSTransportClosed
        exception = None
        packet = macho.Dumps(etype(reason, reasonCode, reasonArgs, exception=exception))
        return self.cryptoContext.OptionalSymmetricEncryption(packet)
