# coding: utf-8

# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
from colorama import init, Style, Fore
init()

from azure.identity import DefaultAzureCredential
from azure.learnappconfig import AppConfigurationClient
from azure.core.exceptions import ResourceNotFoundError

def main():
    endpoint = os.environ['API-LEARN_ENDPOINT']
    credentials = DefaultAzureCredential()
    client = AppConfigurationClient(endpoint, credentials)

    try:
        color_setting = client.get_configuration_setting(os.environ['API-LEARN_SETTING_COLOR_KEY'])
        color = color_setting.value.upper()
        text_setting = client.get_configuration_setting(os.environ['API-LEARN_SETTING_TEXT_KEY'])
        greeting = text_setting.value
    except ResourceNotFoundError:
        color = 'RED'
        greeting = 'Default greeting'

    color = getattr(Fore, color)
    print(f'{color}{greeting}{Style.RESET_ALL}')