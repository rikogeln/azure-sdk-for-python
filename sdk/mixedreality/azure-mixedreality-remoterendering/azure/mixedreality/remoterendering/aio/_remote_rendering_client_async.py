# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import asyncio
import base64
import pickle
from typing import Any, Union

from _functools import partial
from azure.core.async_paging import AsyncItemPaged
from azure.core.credentials import AccessToken, AzureKeyCredential
from azure.core.pipeline.policies import AsyncBearerTokenCredentialPolicy
from azure.core.polling import AsyncLROPoller, AsyncPollingMethod
from azure.core.tracing.decorator_async import distributed_trace_async
from azure.mixedreality.authentication.shared._authentication_endpoint import \
    construct_endpoint_url
from azure.mixedreality.authentication.shared.aio._mixed_reality_token_credential import \
    get_mixedreality_credential
from azure.mixedreality.authentication.shared.aio._mixedreality_account_key_credential import \
    MixedRealityAccountKeyCredential
from azure.mixedreality.authentication.shared.aio._static_access_token_credential import \
    StaticAccessTokenCredential

from .._generated.aio import RemoteRenderingRestClient
from .._generated.models import (Conversion, ConversionSettings,
                                 ConversionStatus, CreateConversionSettings,
                                 CreateSessionSettings, SessionProperties,
                                 SessionSize, SessionStatus,
                                 UpdateSessionSettings)
from .._version import SDK_MONIKER


class RemoteRenderingPollingAsync(AsyncPollingMethod):
    """ABC class for remote rendering operations.
    """

    def __init__(self, account_id, is_terminated, polling_interval=5):
        # type: (string, bool, int) -> None
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
        # type: () -> Union[Conversion, SessionProperties]
        if not self.finished():
            return None
        return self._response

    def status(self):
        # type: () -> str
        return self._response.status

    def get_continuation_token(self):
        # type() -> str
        return base64.b64encode(pickle.dumps(self._response)).decode('ascii')

    @classmethod
    def from_continuation_token(cls, continuation_token, client, **kwargs):  # pylint: disable=W0221
        # type(str, RemoteRenderingClient, Any) -> Tuple
        initial_response = pickle.loads(
            base64.b64decode(continuation_token))  # nosec
        return client, initial_response, None


class ConversionPollingAsync(RemoteRenderingPollingAsync):
    def initialize(self, client, initial_response, deserialization_callback):
        # type: (Any, Any, Callable) -> None
        super().initialize(client, initial_response, deserialization_callback)
        self._query_status = partial(
            self._client.get_conversion, account_id=self._account_id, conversion_id=initial_response.id)


class SessionPollingAsync(RemoteRenderingPollingAsync):
    def initialize(self, client, initial_response, deserialization_callback):
        # type: (Any, Any, Callable) -> None
        super().initialize(client, initial_response, deserialization_callback)
        self._query_status = partial(
            self._client.get_session, account_id=self._account_id, session_id=initial_response.id)


class RemoteRenderingClient(object):
    """A client for the Azure Remote Rendering Service.

    This client offers functionality to convert assets to the format expected by the runtime, and also to manage the
    lifetime of remote rendering sessions.

    :param str remote_rendering_endpoint:
        The rendering service endpoint. This determines the region in which the rendering session is created and asset
        conversions are performed.
    :param str account_id: The Azure Remote Rendering account identifier.
    :param str account_domain:
        The Azure Remote Rendering account domain. For example, for an account created in the eastus region, this will
        have the form "eastus.mixedreality.azure.com"
    :param Union[TokenCredential, AzureKeyCredential, AccessToken] credential: Authentication for the Azure Remote
        Rendering account. Can be of the form of an AzureKeyCredential, TokenCredential or an AccessToken acquired from
        the Mixed Reality Secure Token Service (STS).
    """

    def __init__(self,
                 remote_rendering_endpoint: str,
                 account_id: str,
                 account_domain: str,
                 credential: Union["TokenCredential", AzureKeyCredential, AccessToken],
                 **kwargs) -> None:
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
            credential = MixedRealityAccountKeyCredential(
                account_id=account_id, account_key=credential)

        endpoint_url = kwargs.pop(
            'authentication_endpoint_url', construct_endpoint_url(account_domain))

        # otherwise assume it is a TokenCredential and simply pass it through
        credential = get_mixedreality_credential(
            account_id=account_id, account_domain=account_domain, credential=credential, endpoint_url=endpoint_url)
        authentication_policy = AsyncBearerTokenCredentialPolicy(
            credential, [endpoint_url + '/.default'])

        self._account_id = account_id

        self._client = RemoteRenderingRestClient(
            base_url=remote_rendering_endpoint,
            authentication_policy=authentication_policy,
            sdk_moniker=SDK_MONIKER,
            **kwargs)

    @distributed_trace_async
    async def begin_asset_conversion(self,
                                     conversion_id: str,
                                     conversion_options: ConversionSettings,
                                     **kwargs) -> AsyncLROPoller[Conversion]:
        """
        Start a new asset conversion with the given options.
        :param str conversion_id:
            An ID uniquely identifying the conversion for the remote rendering account. The ID is case sensitive, can
            contain any combination of alphanumeric characters including hyphens and underscores, and cannot contain
            more than 256 characters.
        :param conversion_options: ~azure.mixedreality.remoterendering.ConversionSettings
        :return: A poller for the created asset conversion
        :rtype: ~azure.core.polling.LROPoller
        """
        polling_method = ConversionPollingAsync(account_id=self._account_id, is_terminated=lambda status: status in [
            ConversionStatus.FAILED,
            ConversionStatus.SUCCEEDED
        ])
        initial_state = await self._client.create_conversion(account_id=self._account_id,
                                                             conversion_id=conversion_id,
                                                             body=CreateConversionSettings(
                                                                 settings=conversion_options),
                                                             **kwargs)
        return AsyncLROPoller(client=self._client,
                              initial_response=initial_state,
                              deserialization_callback=None,
                              polling_method=polling_method)

    # TODO: do we support creating a conversion without a poller?

    #    @distributed_trace_async
    #    async def start_asset_conversion(self,
    #                                     conversion_id: str,
    #                                     conversion_options: ConversionSettings,
    #                                     **kwargs) -> Conversion:
    #        return await self._client.create_conversion(account_id=self._account_id,
    #                                                    conversion_id=conversion_id,
    #                                                    body=CreateConversionSettings(
    #                                                        settings=conversion_options),
    #                                                    **kwargs)

    @distributed_trace_async
    async def get_asset_conversion(self, conversion_id: str, **kwargs) -> Conversion:
        """
        Retrieve the state of a previously created conversion.
        :param str conversion_id:
            The identifier of the conversion to retrieve.
        :return: Information about the ongoing conversion process.
        :rtype: ~azure.mixedreality.remoterendering.Conversion
        """
        return await self._client.get_conversion(account_id=self._account_id, conversion_id=conversion_id, **kwargs)

    @distributed_trace_async
    async def list_asset_conversions(self, **kwargs) -> AsyncItemPaged[Conversion]:
        """
        Gets conversions for the remote rendering account.
        :return: AsyncItemPaged[:class:'~azure.mixedreality.remoterendering.Conversion']
        :rtype:  ~azure.core.paging.AsyncItemPaged
        """
        return self._client.list_conversions(account_id=self._account_id, **kwargs)

    @distributed_trace_async
    async def begin_rendering_session(self,
                                      session_id: str,
                                      # TODO: investigate "extendable enum" here (tiny?)
                                      size: SessionSize,
                                      max_lease_time_minutes: int,
                                      **kwargs) -> AsyncLROPoller[SessionProperties]:
        """
        :param str session_id: An ID uniquely identifying the rendering session for the given account. The ID is case
            sensitive, can contain any combination of alphanumeric characters including hyphens and underscores, and
            cannot contain more than 256 characters.
        :param size: Size of the server used for the rendering session. Remote Rendering with Standard size server has
            a maximum scene size of 20 million polygons. Remote Rendering with Premium size does not enforce a hard
            maximum, but performance may be degraded if your content exceeds the rendering capabilities of the service.
        :param int max_lease_time_minutes: The time in minutes the session will run after reaching the 'Ready' state.
        :type size: str or ~azure.mixedreality.remoterendering.SessionSize
        """
        polling_method = SessionPollingAsync(account_id=self._account_id, is_terminated=lambda status: status in [
            SessionStatus.ERROR,
            SessionStatus.STOPPED,
            SessionStatus.EXPIRED,
            SessionStatus.READY
        ])
        settings = CreateSessionSettings(
            size=size, max_lease_time_minutes=max_lease_time_minutes)
        initial_state = await self._client.create_session(account_id=self._account_id,
                                                          session_id=session_id,
                                                          body=settings,
                                                          **kwargs)
        return AsyncLROPoller(client=self._client,
                              initial_response=initial_state,
                              deserialization_callback=None,
                              polling_method=polling_method)

    @distributed_trace_async
    async def get_rendering_session(self, session_id: str, **kwargs) -> SessionProperties:
        '''
        Returns the properties of a previously generated rendering session.
        :param str session_id: The identifier of the rendering session.
        :return: Properties of the rendering session
        :rtype:  ~azure.mixedreality.remoterendering.SessionProperties
        '''
        return await self._client.get_session(self._account_id, session_id=session_id, **kwargs)

    @distributed_trace_async
    async def update_rendering_session(self,
                                       session_id: str,
                                       max_lease_time_minutes: int,
                                       **kwargs) -> SessionProperties:
        """
        Extend the lease time of an already existing rendering session.
        :param str session_id: The identifier of the session to be extended.
        :param int max_lease_time_minutes: The new lease time of the rendering session. Has to be strictly larger than
            the previous lease time.
        :return: None
        :rtype: None
        """
        return await self._client.update_session(account_id=self._account_id,
                                                 session_id=session_id,
                                                 body=UpdateSessionSettings(
                                                     max_lease_time_minutes=max_lease_time_minutes),
                                                 **kwargs)

    @distributed_trace_async
    async def stop_rendering_session(self, session_id: str, **kwargs) -> None:
        """
        :param str session_id: The identifier of the session to be stopped.
        :return: None
        :rtype: None
        """
        return await self._client.stop_session(account_id=self._account_id, session_id=session_id, **kwargs)

    @distributed_trace_async
    async def list_rendering_sessions(
            self,
            **kwargs) -> AsyncItemPaged[SessionProperties]:
        # type: (...) -> AsyncItemPaged[SessionProperties]
        """
        List rendering sessions in the 'Ready' or 'Starting' state. Does not return stopped or failed rendering
            sessions.
        :rtype: ~azure.core.async_paging.AsyncItemPaged[~azure.mixedreality.remoterendering.SessionProperties]
        """
        return self._client.list_sessions(account_id=self._account_id, **kwargs)

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "RemoteRenderingClient":
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *args) -> None:
        await self._client.__aexit__(*args)
