# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
FILE: remote_rendering_client_sample.py
DESCRIPTION:
    These samples demonstrate creating a remote rendering client, converting an asset into the format used in rendering
    sessions, listing created asset conversions, starting a rendering session, extending the lifetime of a rendering 
    session, stopping a rendering session and listing rendering sessions.

USAGE:
    python remote_rendering_client_sample.py
    Set the environment variables with your own values before running the sample:
    ARR_SERVICE_ENDPOINT - the endpoint of the Azure Remote Rendering service in the desired region.
        e.g. "https://remoterendering.eastus.mixedreality.azure.com" for the East US region
        Supported regions can be found at https://docs.microsoft.com/en-us/azure/remote-rendering/reference/regions
    ARR_ACCOUNT_DOMAIN - the Remote Rendering account domain. e.g. "eastus.mixedreality.azure.com"
    ARR_ACCOUNT_ID - the Remote Rendering account identifier.
    ARR_ACCOUNT_KEY - the Remore Rendering account primary or secondary key.
"""

import os
import time
import uuid

from azure.core.credentials import AzureKeyCredential
from azure.mixedreality.remoterendering import (ConversionInputSettings,
                                                ConversionOutputSettings,
                                                ConversionSettings,
                                                ConversionStatus,
                                                Conversion,
                                                RemoteRenderingClient,
                                                SessionSize, SessionStatus)

arr_endpoint = os.environ.get("ARR_ENDPOINT", None)
if not arr_endpoint:
    raise ValueError(
        "Set ARR_SERVICE_ENDPOINT env before run this sample.")

account_id = os.environ.get("ARR_ACCOUNT_ID", None)
if not account_id:
    raise ValueError("Set ARR_ACCOUNT_ID env before run this sample.")

account_domain = os.environ.get("ARR_ACCOUNT_DOMAIN", None)
if not account_domain:
    raise ValueError("Set ARR_ACCOUNT_DOMAIN env before run this sample.")

account_key = os.environ.get("ARR_ACCOUNT_KEY", None)
if not account_key:
    raise ValueError("Set ARR_ACCOUNT_KEY env before run this sample.")

# use AzureKeyCredentials to authenticate to the service - other auth options include AAD and getting
# STS token using the mixed reality STS client (TODO: link when sts client is merged)
key_credential = AzureKeyCredential(account_key)

client = RemoteRenderingClient(remote_rendering_endpoint=arr_endpoint,
                               account_id=account_id, account_domain=account_domain, credential=key_credential)


def perform_asset_conversion():
    # a UUID is a good conversion ID - guaranteed to be unique on our accoount
    conversion_id = str(uuid.uuid4())

    input_settings = ConversionInputSettings(
        storage_container_uri="https://arrrunnerteststorage.blob.core.windows.net/arrinput",
        relative_input_asset_path="box.fbx",
        blob_prefix="input")
    output_settings = ConversionOutputSettings(
        storage_container_uri="https://arrrunnerteststorage.blob.core.windows.net/arroutput",
        blob_prefix=conversion_id)
    options = ConversionSettings(
        input_location=input_settings, output_location=output_settings)

    conversion_poller = client.begin_asset_conversion(
        conversion_id=conversion_id, conversion_options=options)
    print("conversion with id:", conversion_id,
          "created. Waiting for completion.")
    conversion = conversion_poller.result()
    print("conversion with id:", conversion_id,
          "finished with result:", conversion.status)
    if(conversion.status == ConversionStatus.SUCCEEDED):
        print(conversion.output.output_asset_uri)

    # we can also get the status of an individual asset conversion like this:
    conversion = client.get_asset_conversion(conversion_id)
    print("individual conversion retrieved with id:", conversion.id)
    print("\tconversion status:", conversion.status)


def list_all_asset_conversions():
    print("listing conversions for remote rendering account: ", account_id)
    print("conversions:")
    for c in client.list_asset_conversions():
        print("\t conversion:  id:", c.id, "status:", c.status,
              "creation time:", c.creation_time.strftime("%m/%d/%Y, %H:%M:%S"))
        if(c.status == ConversionStatus.SUCCEEDED):
            print("\t\tconversion result URI:", c.output.output_asset_uri)


def demonstrate_rendering_session_lifecycle():

    session_id = str(uuid.uuid4())
    print("starting rendering session with id:", session_id)
    session_poller = client.begin_rendering_session(
        session_id=session_id, size=SessionSize.STANDARD, max_lease_time_minutes=5)
    print("rendering session with id:", session_id,
          "created. Waiting for session to be ready.")
    session = session_poller.result()
    print("session with id:", session.id, "is ready. max_lease_time_minutes:",
          session.max_lease_time_minutes)

    # one can now connect to the rendering session using the runtime SDK on a Hololens 2
    print(session)

    # we can also get the properties of an individual session by id:
    session = client.get_rendering_session(session_id)
    print(session)

    # if the session should run longer than initially requested we can extend the lifetime of the session
    session = client.update_rendering_session(
        session_id=session_id, max_lease_time_minutes=10)
    print("session with id:", session.id, "updated. New lease time:",
          session.max_lease_time_minutes, "minutes")

    # once we do not need the session anymore we can stop the session
    client.stop_rendering_session(session_id)
    print("session with id:", session_id, "stopped")


def list_all_rendering_sessions():
    print("listing sessions for account:", account_id)
    print("sessions:")
    rendering_sessions = client.list_rendering_sessions()
    for session in rendering_sessions:
        print("\t session:  id:", session.id, "status:", session.status,
              "creation time:", session.creation_time.strftime("%m/%d/%Y, %H:%M:%S"))


if __name__ == '__main__':
    perform_asset_conversion()
    list_all_asset_conversions()
    demonstrate_rendering_session_lifecycle()
    list_all_rendering_sessions()
