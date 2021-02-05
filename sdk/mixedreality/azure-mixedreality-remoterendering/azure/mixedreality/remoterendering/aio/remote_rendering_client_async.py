# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import asyncio
import six

from azure.core.async_paging import AsyncItemPaged

from .._generated.aio import RemoteRenderingRestClient

from azure.mixedreality.authentication.aio import MixedRealityStsClient
from azure.mixedreality.authentication.shared.aio._mixed_reality_token_credential import get_mixedreality_credential
from azure.mixedreality.authentication.shared.aio._mixed_reality_token_credential import MixedRealityTokenCredential
from azure.mixedreality.authentication.shared.aio._mixedreality_account_key_credential import MixedRealityAccountKeyCredential
from azure.mixedreality.authentication.shared.aio._static_access_token_credential import StaticAccessTokenCredential
from azure.mixedreality.authentication.shared._authentication_endpoint import construct_endpoint_url

from azure.core.credentials import AccessToken
from azure.core.credentials import AzureKeyCredential

from azure.core.pipeline.policies import AsyncBearerTokenCredentialPolicy

from .._version import VERSION
from .._version import SDK_MONIKER

from .._generated.models import ConversionStatus
from .._generated.models import ConversionSettings
from .._generated.models import ConversionInputSettings
from .._generated.models import ConversionOutputSettings
from .._generated.models import CreateConversionSettings
from .._generated.models import Conversion

from .._generated.models import SessionSize
from .._generated.models import SessionProperties
from .._generated.models import SessionStatus
from .._generated.models import CreateSessionSettings
from .._generated.models import UpdateSessionSettings

from azure.core.polling import AsyncPollingMethod
from azure.core.polling import AsyncLROPoller
from _functools import partial
import time
import pickle
import base64
from typing import AsyncIterable

class RemoteRenderingPollingAsync(AsyncPollingMethod):
    """ABC class for remote rendering operations.
    """
    def __init__(self, account_id, is_terminated, polling_interval=5):
        # type: (bool, string, int) -> None
        self._account_id = account_id
        self._response = None
        self._client = None
        self._query_status = None
        self._is_terminated = is_terminated
        self._polling_interval = polling_interval

    async def _update_status(self):
        # type: () -> None
        if self._query_status is None:
            raise Exception("this poller has not been initialized")
        self._response = await self._query_status()  # pylint: disable=E1102

    def initialize(self, client, initial_response, deserialization_callback):
        # type: (Any, Any, Callable) -> None
        self._client = client
        self._response = initial_response

    async def run(self):
        # type: () -> None
        while not self.finished():
            await self._update_status()
            if not self.finished():
                await asyncio.sleep(self._polling_interval)

    def finished(self):
        # type: () -> bool
        if self._response.status is None:
            return False
        return self._is_terminated(self._response.status)

    def resource(self):
        # type: () -> Union[Conversion, Session] #TODO: fix type annotation
        if not self.finished():
            return None
        return self._response

    def status(self):
        # type: () -> str
        return self._response.status

    def get_continuation_token(self):
        # type() -> str
        import pickle
        return base64.b64encode(pickle.dumps(self._response)).decode('ascii')

    @classmethod
    def from_continuation_token(cls, continuation_token, client, **kwargs):  # pylint: disable=W0221
        # type(str, RemoteRenderingClient, Any) -> Tuple
        import pickle
        initial_response = pickle.loads(base64.b64decode(continuation_token))  # nosec
        return client, initial_response, None

class ConversionPollingAsync(RemoteRenderingPollingAsync):
    def initialize(self, client, initial_response, deserialization_callback):
        # type: (Any, Any, Callable) -> None
        super().initialize(client, initial_response, deserialization_callback)
        self._query_status = partial(self._client.get_conversion, account_id=self._account_id, conversion_id=initial_response.id)

class SessionPollingAsync(RemoteRenderingPollingAsync):
    def initialize(self, client, initial_response, deserialization_callback):
        # type: (Any, Any, Callable) -> None
        super().initialize(client, initial_response, deserialization_callback)
        self._query_status = partial(self._client.get_session, account_id=self._account_id, session_id=initial_response.id)


class RemoteRenderingClient(object):
    def __init__(self, remote_rendering_endpoint, account_id, account_domain, credential, **kwargs) -> None:
        self._account_id = account_id

        if not remote_rendering_endpoint:
            raise ValueError("remote_rendering_endpoint can not be None")

        if not account_id:
            raise ValueError("account_id can not be None")

        if not account_domain:
            raise ValueError("account_domain can not be None")

        if not credential:
            raise ValueError("credential can not be None")

        if isinstance(credential, AccessToken):
            credential = StaticAccessTokenCredential(credential)

        if isinstance(credential, AzureKeyCredential):
            credential = MixedRealityAccountKeyCredential(account_id=account_id, account_key=credential)

        endpoint_url = kwargs.pop('authentication_endpoint_url', construct_endpoint_url(account_domain))

        # otherwise assume it is a TokenCredential and simply pass it through
        credential = get_mixedreality_credential(account_id=account_id, account_domain=account_domain, credential= credential, endpoint_url=endpoint_url)
        authentication_policy = AsyncBearerTokenCredentialPolicy(credential, [endpoint_url + '/.default'])

        self._account_id = account_id

        self._client = RemoteRenderingRestClient(
            base_url=remote_rendering_endpoint,
            authentication_policy = authentication_policy,
            sdk_moniker=SDK_MONIKER,
            **kwargs)

    #TODO: do we support creating a conversion without a poller?
    async def start_asset_conversion(self, conversion_id, conversion_options,**kwargs):
        # AsyncLROPoller
        return await self._client.create_conversion(account_id= self._account_id, conversion_id= conversion_id, body=  CreateConversionSettings(settings=conversion_options), **kwargs)
    
    async def get_asset_conversion(self, conversion_id, **kwargs):
        return await self._client.get_conversion(account_id=self._account_id, conversion_id=conversion_id, **kwargs)

    async def begin_asset_conversion(self, conversion_id, conversion_options, **kwargs):
        polling_method = ConversionPollingAsync(account_id = self._account_id, is_terminated=lambda status: status in [
            ConversionStatus.FAILED,
            ConversionStatus.SUCCEEDED
        ] )
        initial_state = await self._client.create_conversion(account_id= self._account_id, conversion_id= conversion_id, body=  CreateConversionSettings(settings=conversion_options), **kwargs)
        return AsyncLROPoller(client= self._client, 
            initial_response= initial_state, 
            deserialization_callback=None, 
            polling_method= polling_method)

    async def list_asset_conversions(self, **kwargs) -> AsyncIterable["models.ConversionList"]: #TODO: type annotations
        return self._client.list_conversions(account_id= self._account_id)

    async def begin_rendering_session(self, session_id: str, size: SessionSize,  lease_time_minutes: int, **kwargs) ->AsyncLROPoller[SessionProperties]:
        polling_method = SessionPollingAsync(account_id = self._account_id, is_terminated=lambda status: status in [
            SessionStatus.ERROR,
            SessionStatus.STOPPED,
            SessionStatus.EXPIRED,
            SessionStatus.READY
        ] )
        settings = CreateSessionSettings(size=size, max_lease_time_minutes=lease_time_minutes)
        initial_state = await self._client.create_session(account_id=self._account_id, session_id=session_id, body=settings, **kwargs)
        return AsyncLROPoller(client= self._client, 
            initial_response= initial_state, 
            deserialization_callback=None, 
            polling_method= polling_method)

    async def get_rendering_session(self, session_id: str, **kwargs):
        return await self._client.get_session(self._account_id, session_id=session_id, **kwargs)

    async def extend_rendering_session(self, session_id, lease_time_minutes) -> SessionProperties:
        return await self._client.update_session(self._account_id, session_id, UpdateSessionSettings(max_lease_time_minutes=lease_time_minutes))

    async def stop_rendering_session(self, session_id: str, **kwargs) -> None:
        return await self._client.stop_session(account_id=self._account_id, session_id=session_id, **kwargs)

    # TODO: type annotations?
    async def list_rendering_sessions(self, **kwargs):
        return self._client.list_sessions(account_id= self._account_id)

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "RemoteRenderingClient":
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args) -> None:
        await self._client.__aexit__(*args)