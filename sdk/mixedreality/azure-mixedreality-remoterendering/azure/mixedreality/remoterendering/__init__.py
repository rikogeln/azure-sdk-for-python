# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------

from ._version import VERSION

from .remote_rendering_client import RemoteRenderingClient
from ._generated.models import Conversion, ConversionSettings, ConversionInputSettings, ConversionOutputSettings, ConversionStatus
from ._generated.models import SessionProperties, SessionSize, SessionStatus

__all__ = [
    'RemoteRenderingClient',
    'ConversionSettings',
    'ConversionInputSettings',
    'ConversionOutputSettings',
    'Conversion',
    "ConversionStatus",
    "SessionProperties",
    "SessionSize",
    "SessionStatus"
]

__version__ = VERSION
