# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------

from datetime import datetime

from msrest import Serializer
from azure.core.tracing.decorator import distributed_trace
from ._generated import RemoteRenderingRestClient
from ._generated.models import ConversionSettings
from ._generated.models import ConversionInputSettings
from ._generated.models import ConversionOutputSettings
from ._generated.models import CreateConversionSettings
from ._generated.models import ConversionStatus
from ._generated.models import Conversion

from ._generated.models import SessionStatus
from ._generated.models import CreateSessionSettings
from ._generated.models import UpdateSessionSettings

from _functools import partial
import time
import pickle
import base64

from azure.core.credentials import AccessToken
from azure.core.pipeline.policies import BearerTokenCredentialPolicy

from azure.core.polling import LROPoller, NoPolling, PollingMethod
from azure.core.polling.base_polling import LROBasePolling

# from ._models import ConfigurationSetting
from ._version import VERSION

# TODO: factor out/check if this is really the right way to go
# taken from: \sdk\communication\azure-communication-administration\azure\communication\administration\_polling.py
class RemoteRenderingPolling(PollingMethod):
    """ Abstract base class for polling.
    """
    def __init__(self, account_id, is_terminated, polling_interval=5):
        # type: (bool, int) -> None
        self._account_id = account_id
        self._response = None
        self._client = None
        self._query_status = None
        self._is_terminated = is_terminated
        self._polling_interval = polling_interval

    def _update_status(self):
        # type: () -> None
        if self._query_status is None:
            raise Exception("this poller has not been initialized")
        self._response = self._query_status()  # pylint: disable=E1102

    def initialize(self, client, initial_response, deserialization_callback):
        # type: (Any, Any, Callable) -> None
        self._client = client
        self._response = initial_response

    def run(self):
        # type: () -> None
        while not self.finished():
            self._update_status()
            if not self.finished():
                time.sleep(self._polling_interval)

    def finished(self):
        # type: () -> bool
        if self._response.status is None:
            return False
        return self._is_terminated(self._response.status)

    def resource(self):
        # type: () -> Union[PhoneNumberReservation, PhoneNumberRelease]
        if not self.finished():
            return None
        return self._response

    def status(self):
        # type: () -> str
        return self._response.status

    def get_continuation_token(self):
        # type() -> str
        # TODO: rikogeln what is the continuation token for
        return base64.b64encode(pickle.dumps(self._response)).decode('ascii')

    # TODO: do we need the from_continuation_token function?
    @classmethod
    def from_continuation_token(cls, continuation_token, client, **kwargs):  # pylint: disable=W0221
        # type(str, PhoneNumberAdministrationClient, Any) -> Tuple
        initial_response = pickle.loads(base64.b64decode(continuation_token))  # nosec
        return client, initial_response, None

class ConversionPolling(RemoteRenderingPolling):
    def initialize(self, client, initial_response, deserialization_callback):
        # type: (Any, Any, Any, Callable) -> None
        super().initialize(client, initial_response, deserialization_callback)
        self._query_status = partial(self._client.get_conversion, account_id=self._account_id, conversion_id=initial_response.id)

class SessionPolling(RemoteRenderingPolling):
    def initialize(self, client, initial_response, deserialization_callback):
        # type: (Any, Any, Any, Callable) -> None
        super().initialize(client, initial_response, deserialization_callback)
        self._query_status = partial(self._client.get_session, account_id=self._account_id, session_id=initial_response.id)

class StsBearerToken(object): #todo: how to implement a token credential
    def __init__(self, token):
        # type: (str) -> None

        #TODO: what will we do with expires_on?
        # expires_on is seconds since epoch arrpythonsdk\lib\site-packages\azure\core\pipeline\policies\_authentication.py 
        expires_on = time.time() + 60*60 #1h expires on - should we parse this from the sts jwt token?
        self._token = AccessToken(token= token, expires_on=expires_on)

    def get_token(self):
        return self._token

    def expires_on(self):
        return None

class RemoteRenderingClient(object):
    """A Client for the RemoteRendering Service.
    
    :param str service_url: The URL for the service.
    :param srt sts token: A valid STS token for the account.
    """

    def __init__(self, service_url, account_id, sts_token, **kwargs):
        # type: (str, str, str) -> None

        # TODO: figure out if bearerTokenCredential policy is the default or if i have to change stuff around
        # TODO: why do i need to set the credential AND the policy? allegedly the policy is default?
        credential = StsBearerToken(token = sts_token)
        tokenPolicy = BearerTokenCredentialPolicy(credential = credential)

        # TODO: figure out if the default is sensible
        # user_agent_moniker = "RemoteRenderingPythonClient/{}".format(VERSION)

        # TODO: # (should we verify that this is str a guid?)
        self._account_id = account_id

        self._client = RemoteRenderingRestClient(
            base_url=service_url,
            # credential_scopes=[account_url.strip("/") + "/.default"], #TODO: do i need a scope? is this OAUTH only?
            authentication_policy = tokenPolicy,
            # sdk_moniker=user_agent_moniker,
            **kwargs)

# look at communication\azure-communication-administration\azure\communication\administration\_phone_number_administration_client.py

    def begin_asset_conversion(self, conversion_id, conversion_options, **kwargs):

        initial_state = self._client.create_conversion(self._account_id, conversion_id, CreateConversionSettings(settings=conversion_options))
        polling_method = ConversionPolling(account_id = self._account_id, is_terminated=lambda status: status in [
                ConversionStatus.FAILED,
                ConversionStatus.SUCCEEDED
            ] )
        return LROPoller(client=self._client,
                         initial_response=initial_state,
                         deserialization_callback=None,
                         polling_method=polling_method)


    # should this return a AssetConversionTask? 
    # should this return a azure.core.polling.LROPoller of
    def start_conversion(self, conversion_id, conversion_options, **kwargs):
        conversion = self._client.create_conversion(self._account_id, conversion_id, CreateConversionSettings(settings=conversion_options))
        return conversion

    #todo: should this be called AssetConversion? AssetConversionTask? 
    #TODO: forward kwargs
    def get_conversion(self, conversion_id):
        conversion = self._client.get_conversion(self._account_id, conversion_id)
        return conversion

    # TODO: type annotations
    def get_conversions(self, **kwargs):
        return self._client.list_conversions(self._account_id)

    def begin_rendering_session(self, session_id, size, lease_time_minutes):
        settings = CreateSessionSettings(size=size, max_lease_time_minutes=lease_time_minutes)
        initial_state =  self._client.create_session(account_id=self._account_id, session_id=session_id, body=settings)
        polling_method = SessionPolling(account_id = self._account_id, is_terminated=lambda status: status in [
                SessionStatus.EXPIRED,
                SessionStatus.ERROR,
                SessionStatus.READY
            ] )
        return LROPoller(client=self._client,
                         initial_response=initial_state,
                         deserialization_callback=None,
                         polling_method=polling_method)

    def stop_rendering_session(self, session_id):
        self._client.stop_session(self._account_id, session_id)
    
    def get_rendering_session(self, session_id):
        return self._client.get_session(self._account_id, session_id)

    def extend_rendering_session(self, session_id, lease_time_minutes):
        return self._client.update_session(self._account_id, session_id, UpdateSessionSettings(max_lease_time_minutes=lease_time_minutes))

    def get_sessions(self, **kwargs):
        return self._client.list_sessions(self._account_id)
