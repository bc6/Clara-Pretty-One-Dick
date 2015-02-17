#Embedded file name: twitch\__init__.py
"""Python layer for TwitchSDK integration.
Provides a more convenient interface than using the C++ integration
layer directory.
Raw access to the C++ integration layer is provided through `twitch.api`.
When more of the integration layer needs to be used, such as using metadata,
it should be exposed through this module.
Access to `twitch.api` should be limited to debugging.

Usage Tips
----------

You need to log in to start streaming.
If you stop the stream,
you need to log in again in order to start streaming again.
We can move this into a class to take care of it automatically.

If the window is resized when streaming,
the stream will automatically stop.
Trying to stream with an invalid window size will raise an error.
"""
import trinity
import urllib
import _twitch as api
__all__ = ['api',
 'login',
 'login_with_token',
 'start_stream',
 'stop_stream',
 'set_mic_volume',
 'set_playback_volume',
 'get_api_state',
 'is_recording',
 'is_valid_windowsize',
 'get_login_token']

def login(username, password, clientID, clientSecret):
    """Performs the login. """
    try:
        api.Login(username.encode('utf8'), password.encode('utf8'), str(clientID), str(clientSecret))
    except:
        password = '********'
        raise


def login_with_token(clientID, token):
    """Performs the login with a token."""
    api.LoginWithToken(str(clientID), str(token))


def start_stream(streamTitle, gameName, targetFps = 30, includeAudio = True):
    """Starts the stream. Must be logged in,
    and the window must be a value size."""
    api.SetGameName(gameName)
    api.StartStream(streamTitle.encode('utf8'), targetFps, includeAudio, trinity.device)


def stop_stream():
    api.StopStream()


def set_mic_volume(value):
    """Sets the volume of the recording from the microphone.
    
    :param value: Float 0 to 1.
    """
    api.SetVolume(api.AUDIO_DEVICE.RECORDER, value)


def set_playback_volume(value):
    """Sets the volume of the recording from the application.
    
    :param value: Float 0 to 1.
    """
    api.SetVolume(api.AUDIO_DEVICE.PLAYBACK, value)


def get_api_state():
    """Returns a tuple of the API's state value and name,
    such as `(1, 'INITIALIZED')`.
    Useful for debugging.
    """
    state = api.GetState()
    name = api.STATE.GetNameFromValue(state)
    return (state, name)


def is_recording():
    return api.GetRecordingState()[0]


def is_streaming():
    return api.GetState() >= api.STATE.STREAMING


def is_valid_windowsize(size = None):
    """Returns True if width and height are a multiple of 16.
    
    :param size: (width, height) tuple. If None, get trinity's current
      backbuffer width and height.
    """
    if size is None:
        params = trinity.device.GetPresentParameters()
        size = (params['BackBufferWidth'], params['BackBufferHeight'])
    width, height = size
    if width % 32 or height % 16:
        return False
    if width > 1920:
        return False
    if height > 1200:
        return False
    return True


def set_state_change_callback(callback):
    api.SetStateChangeCallback(callback)


def get_login_token():
    return api.GetLoginToken()
