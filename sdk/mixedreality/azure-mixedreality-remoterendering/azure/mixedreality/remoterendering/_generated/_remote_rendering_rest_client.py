# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------

from typing import TYPE_CHECKING

from azure.core import PipelineClient
from msrest import Deserializer, Serializer

if TYPE_CHECKING:
    # pylint: disable=unused-import,ungrouped-imports
    from typing import Any, Optional

from ._configuration import RemoteRenderingRestClientConfiguration
from .operations import RemoteRenderingRestClientOperationsMixin
from . import models


class RemoteRenderingRestClient(RemoteRenderingRestClientOperationsMixin):
    """Describing the `Azure Remote Rendering <https://docs.microsoft.com/azure/remote-rendering/>`_ REST API for rendering sessions and asset conversions. 

All requests to these APIs must be authenticated using the Secure Token Service as described in the `Azure Remote rendering documentation chapter about authentication <https://docs.microsoft.com/azure/remote-rendering/how-tos/tokens>`_.

    :param str base_url: Service URL
    """

    def __init__(
        self,
        base_url=None,  # type: Optional[str]
        **kwargs  # type: Any
    ):
        # type: (...) -> None
        if not base_url:
            base_url = 'https://remoterendering.westus2.mixedreality.azure.com'
        self._config = RemoteRenderingRestClientConfiguration(**kwargs)
        self._client = PipelineClient(base_url=base_url, config=self._config, **kwargs)

        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)


    def close(self):
        # type: () -> None
        self._client.close()

    def __enter__(self):
        # type: () -> RemoteRenderingRestClient
        self._client.__enter__()
        return self

    def __exit__(self, *exc_details):
        # type: (Any) -> None
        self._client.__exit__(*exc_details)
