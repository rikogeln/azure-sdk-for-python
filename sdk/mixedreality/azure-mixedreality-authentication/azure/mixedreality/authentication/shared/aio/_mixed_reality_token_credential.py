# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from azure.core.credentials import AccessToken
    from azure.core.credentials_async import AsyncTokenCredential

from .._static_access_token_credential import StaticAccessTokenCredential
from ...aio._client_async import MixedRealityStsClient

def get_mixedreality_credential_async(
    account_id: str,
    endpoint_url: str,
    credential: "AsyncTokenCredential",
    **kwargs):
        if isinstance(credential, StaticAccessTokenCredential):
            return credential

        return MixedRealityTokenCredential(
            account_id=account_id,
            endpoint_url=endpoint_url,
            credential=credential,
            **kwargs)


class MixedRealityTokenCredential(object):
    """ Represents a token credential that can be used to access a Mixed Reality service.
    This implements the TokenCredential protocol.

    :param str account_id: The Mixed Reality service account identifier.
    :param str endpoint_url: The Mixed Reality STS service endpoint.
    :param TokenCredential credential: The credential used to access the Mixed Reality service.
    """

    def __init__(self, account_id, endpoint_url, credential, **kwargs):
        self.stsClient = MixedRealityStsClient(
            account_id=account_id,
            endpoint_url=endpoint_url,
            credential=credential,
            **kwargs)

    async def get_token(self, *scopes: str, **kwargs: "Any") -> "AccessToken":
        return await self.stsClient.get_token(**kwargs)

    async def close(self) -> None:
        self.stsClient.close()

    async def __aenter__(self):
        await self.stsClient.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.stsClient.__aexit__()
