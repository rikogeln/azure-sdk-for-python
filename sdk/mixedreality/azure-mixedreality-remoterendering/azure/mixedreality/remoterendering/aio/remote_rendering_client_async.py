# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

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
        authentication_policy = BearerTokenCredentialPolicy(credential, [endpoint_url + '/.default'])

        self._account_id = account_id

        self._client = RemoteRenderingRestClient(
            base_url=remote_rendering_endpoint,
            authentication_policy = authentication_policy,
            sdk_moniker=SDK_MONIKER,
            **kwargs)

