# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------

import base64
import pickle
import time
from typing import TYPE_CHECKING

from _functools import partial
from azure.core.credentials import AccessToken, AzureKeyCredential
from azure.core.pipeline.policies import BearerTokenCredentialPolicy
from azure.core.polling import LROPoller, PollingMethod
from azure.core.tracing.decorator import distributed_trace
from azure.mixedreality.authentication.shared._authentication_endpoint import \
    construct_endpoint_url
from azure.mixedreality.authentication.shared._mixed_reality_token_credential import \
    get_mixedreality_credential
from azure.mixedreality.authentication.shared._mixedreality_account_key_credential import \
    MixedRealityAccountKeyCredential
from azure.mixedreality.authentication.shared._static_access_token_credential import \
    StaticAccessTokenCredential

from ._generated import RemoteRenderingRestClient
# TODO: do i need these for type checking?
from ._generated.models import (Conversion, ConversionSettings,
                                ConversionStatus, CreateConversionSettings,
                                CreateSessionSettings, SessionProperties,
                                SessionStatus, UpdateSessionSettings)
from ._version import SDK_MONIKER

if TYPE_CHECKING:
    # pylint: disable=unused-import,ungrouped-imports
    from typing import Any, Union

    from azure.core.credentials import TokenCredential


# TODO: factor out/check if this is really the right way to go
# taken from: \sdk\communication\azure-communication-administration\azure\communication\administration\_polling.py
class RemoteRenderingPolling(PollingMethod):
    """ Abstract base class for polling.
    """

    def __init__(self, account_id, is_terminated, polling_interval=5):
        # type: (str, bool, int) -> None
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
        # type: () -> Union[Conversion, SessionProperties]  #TODO: fix type annotation - to i need ~...?
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
        # type(str, RemoteRenderingClient, Any) -> Tuple
        initial_response = pickle.loads(
            base64.b64decode(continuation_token))  # nosec
        return client, initial_response, None


class ConversionPolling(RemoteRenderingPolling):
    def initialize(self, client, initial_response, deserialization_callback):
        # type: (Any, Any, Any, Callable) -> None
        super().initialize(client, initial_response, deserialization_callback)
        self._query_status = partial(
            self._client.get_conversion, account_id=self._account_id, conversion_id=initial_response.id)


class SessionPolling(RemoteRenderingPolling):
    def initialize(self, client, initial_response, deserialization_callback):
        # type: (Any, Any, Any, Callable) -> None
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

    def __init__(self, remote_rendering_endpoint, account_id, account_domain, credential, **kwargs):
        # type: (str, str, str, Union[TokenCredential, AzureKeyCredential, AccessToken], Any) -> None

        # TODO: verify the above type annotation is correct
        # TODO: should credential be called credential because of AccessToken
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
        authentication_policy = BearerTokenCredentialPolicy(
            credential, [endpoint_url + '/.default'])

        self._account_id = account_id

        self._client = RemoteRenderingRestClient(
            base_url=remote_rendering_endpoint,
            authentication_policy=authentication_policy,
            sdk_moniker=SDK_MONIKER,
            **kwargs)

# TODO: remove notes for where i got the code from
# look at communication\azure-communication-administration\azure\communication\administration\
# _phone_number_administration_client.py

    def begin_asset_conversion(self, conversion_id, conversion_options, **kwargs):
        # type: (str, ConversionSettings, Any) -> ~azure.core.polling.LROPoller
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
        # TODO: question: can/should we specify the return type like: LROPoller[Conversion] ?
        #       (be more concrete of the type)
        # TODO: question: is the return type ~azure.mixedreality.remoterendering.ConversionSettings correct?
        initial_state = self._client.create_conversion(
            account_id=self._account_id,
            conversion_id=conversion_id,
            body=CreateConversionSettings(settings=conversion_options),
            **kwargs)
        polling_method = ConversionPolling(account_id=self._account_id, is_terminated=lambda status: status in [
            ConversionStatus.FAILED,
            ConversionStatus.SUCCEEDED
        ])
        return LROPoller(client=self._client,
                         initial_response=initial_state,
                         deserialization_callback=None,
                         polling_method=polling_method)

    # TODO: do i need a method which can wrap a poller around an existing Conversion?
    # TODO: question: should i expose a start method like the one below which returns the Conversion without a poller?
#
    # @distributed_trace
    # def start_asset_conversion(self, conversion_id, conversion_options, **kwargs):
    #     # type: (str, ConversionSettings, Any) -> ~azure.mixedreality.remoterendering.Conversion
    #     """
    #     Start a new asset conversion with the given options
    #     :param str conversion_id:
    #         An ID uniquely identifying the conversion for the remote rendering account. The ID is case sensitive, can
    #         contain any combination of alphanumeric characters including hyphens and underscores, and cannot contain
    #         more than 256 characters.
    #     :param conversion_options: ~azure.mixedreality.remoterendering.ConversionSettings
    #     :return: A poller for the created asset conversion
    #     :rtype:  ~azure.mixedreality.remoterendering.Conversion
    #     """
    #     conversion = self._client.create_conversion(
    #         account_id=self._account_id,
    #         conversion_id=conversion_id,
    #         body=CreateConversionSettings(settings=conversion_options),
    #         **kwargs)
    #     return conversion

    @distributed_trace
    def get_asset_conversion(self, conversion_id, **kwargs):
        # type: (str, Any) -> ~azure.mixedreality.remoterendering.Conversion
        """
        Retrieve the state of a previously created conversion.
        :param str conversion_id:
            The identifier of the conversion to retrieve.
        :return: Information about the ongoing conversion process.
        :rtype: ~azure.mixedreality.remoterendering.Conversion
        """
        conversion = self._client.get_conversion(
            account_id=self._account_id, conversion_id=conversion_id, **kwargs)
        return conversion

    # TODO: question: what is the return type here?
    # should i expose ~azure.mixedreality.remoterendering.ConversionList in the module? or wrap this somehow like
    # _sdk\communication\azure-communication-chat\azure\communication\chat\_chat_thread_client.py

    @distributed_trace
    def list_asset_conversions(self, **kwargs):
        # type: (Any) -> ItemPaged[~azure.mixedreality.remoterendering.Conversion]
        """
        Gets conversions for the remote rendering account.
        :return: ItemPaged[:class:'~azure.mixedreality.remoterendering.Conversion']
        :rtype:  ~azure.core.paging.ItemPaged
        """
        return self._client.list_conversions(account_id=self._account_id, **kwargs)

    @distributed_trace
    def begin_rendering_session(self, session_id, size, max_lease_time_minutes, **kwargs):
        # type: (str, Union[str, SessionSize], int, Any) -> ~azure.core.polling.LROPoller
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
        settings = CreateSessionSettings(
            size=size, max_lease_time_minutes=max_lease_time_minutes)
        initial_state = self._client.create_session(
            account_id=self._account_id,
            session_id=session_id,
            body=settings,
            **kwargs)
        polling_method = SessionPolling(account_id=self._account_id, is_terminated=lambda status: status in [
            SessionStatus.EXPIRED,
            SessionStatus.ERROR,
            SessionStatus.STOPPED,
            SessionStatus.READY
        ])
        return LROPoller(client=self._client,
                         initial_response=initial_state,
                         deserialization_callback=None,
                         polling_method=polling_method,
                         **kwargs)

    @distributed_trace
    def get_rendering_session(self, session_id, **kwargs):
        # type: (str)-> ~azure.mixedreality.remoterendering.SessionProperties
        '''
        Returns the properties of a previously generated rendering session.
        :param str session_id: The identifier of the rendering session.
        :return: Properties of the rendering session
        :rtype:  ~azure.mixedreality.remoterendering.SessionProperties
        '''
        return self._client.get_session(
            account_id=self._account_id,
            session_id=session_id,
            **kwargs)

    @distributed_trace
    def stop_rendering_session(self, session_id, **kwargs):
        # type:  (str, Any) -> None
        """
        :param str session_id: The identifier of the session to be stopped.
        :return: None
        :rtype: None
        """
        self._client.stop_session(
            account_id=self._account_id, session_id=session_id, **kwargs)

    @distributed_trace
    def update_rendering_session(self, session_id, max_lease_time_minutes, **kwargs):
        # type: (str, int) -> None
        """
        Extend the lease time of an already existing rendering session.
        :param str session_id: The identifier of the session to be extended.
        :param int max_lease_time_minutes: The new lease time of the rendering session. Has to be strictly larger than
            the previous lease time.
        :return: None
        :rtype: None
        """
        return self._client.update_session(account_id=self._account_id,
                                           session_id=session_id,
                                           body=UpdateSessionSettings(
                                               max_lease_time_minutes=max_lease_time_minutes),
                                           **kwargs)

    @distributed_trace
    def list_rendering_sessions(self, **kwargs):
        # type: (Any) -> ItemPaged[~azure.mixedreality.remoterendering.SessionProperties]
        """
        List rendering sessions in the 'Ready' or 'Starting' state. Does not return stopped or failed rendering
            sessions.
        :return: ItemPaged[:class:'~azure.mixedreality.remoterendering.Conversion']
        :rtype:  ~azure.core.paging.ItemPaged
        """
        return self._client.list_sessions(account_id=self._account_id, **kwargs)

    def close(self):
        # type: () -> None
        self._client.close()

    def __enter__(self):
        # type: () -> RemoteRenderingClient
        self._client.__enter__()  # pylint:disable=no-member
        return self

    def __exit__(self, *args):
        # type: (*Any) -> None
        self._client.__exit__(*args)  # pylint:disable=no-member
