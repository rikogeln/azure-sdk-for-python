# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
import uuid 
import time

from azure.core.credentials import AzureKeyCredential

from azure.mixedreality.remoterendering.aio import RemoteRenderingClient
from azure.mixedreality.remoterendering import ConversionInputSettings
from azure.mixedreality.remoterendering import ConversionOutputSettings
from azure.mixedreality.remoterendering import ConversionSettings
from azure.mixedreality.remoterendering import ConversionStatus

from azure.mixedreality.remoterendering import SessionSize
from azure.mixedreality.remoterendering import SessionStatus
from azure.mixedreality.remoterendering import SessionProperties

import asyncio

async def main():
    arr_endpoint = os.environ.get("ARR_ENDPOINT", None)
    if not arr_endpoint:
        raise ValueError("Set ARR_SERVICE_ENDPOINT env before run this sample.")

    account_id = os.environ.get("ARR_ACCOUNT_ID", None)
    if not account_id:
        raise ValueError("Set ARR_ACCOUNT_ID env before run this sample.")

    account_domain = os.environ.get("ARR_ACCOUNT_DOMAIN", None)
    if not account_domain:
        raise ValueError("Set ARR_ACCOUNT_DOMAIN env before run this sample.")

    account_key = os.environ.get("ARR_ACCOUNT_KEY", None)
    if not account_key:
        raise ValueError("Set ARR_ACCOUNT_KEY env before run this sample.")

    key_credential = AzureKeyCredential(account_key)

    client = RemoteRenderingClient(remote_rendering_endpoint=arr_endpoint, account_id=account_id, account_domain=account_domain, credential=key_credential )

    conversion_id = str(uuid.uuid4())

#todo: use dram connected account here

    input_settings = ConversionInputSettings(
        storage_container_uri="https://arrrunnerteststorage.blob.core.windows.net/arrinput", 
        relative_input_asset_path="box.fbx", 
        blob_prefix="input")
    output_settings = ConversionOutputSettings(
        storage_container_uri="https://arrrunnerteststorage.blob.core.windows.net/arroutput", 
        blob_prefix=conversion_id)

    options = ConversionSettings(input_location = input_settings, output_location=output_settings)
    #output = ConversionOutputSettings()
    
    #conv = client.begin_asset_conversion(conversion_id, conversion_options = options)
    #print(conv)
    #conv = client.get_conversion(conversion_id)
    #print(conv)
    #print("end")

    # conversion = client.get_conversion("2f815485-640b-4543-a589-5d741afdca2d")

    # TODO: async with begin polling method 
    # example here is not exactly fitting our use case with getting the initial state 
    # should begin_... be async or not? 
    async with client:
        #conversion = await client.start_conversion(conversion_id= conversion_id, conversion_options= options)
        # print("conversion started:", conversion_id)
        # conversionPoller = await client.begin_asset_conversion(conversion_id= conversion_id, conversion_options= options)
        #await conversionPoller.wait()
        #print("conversion finished:", conversion_id)

        #print("listing conversions for account: '",account_id,"'")
        #print("conversions:")
        #conversions = await client.get_conversions()
        #async for conversion in conversions:
        #    print("\t conversion:  id:'",conversion.id,"' status'",conversion.status,"'", conversion.creation_time.strftime("%m/%d/%Y, %H:%M:%S"))

        session_id = str(uuid.uuid4())
        sessionPoller = await client.begin_rendering_session(session_id=session_id, size=SessionSize.STANDARD, lease_time_minutes= 5)
        #print("starting session:", session_id)
        #await sessionPoller.wait()
        #session = await sessionPoller.result()

        #session = await client.extend_rendering_session(session_id, 10)
        #print("session with id:'",session.id,"' updated. LeaseTime:'",session.max_lease_time_minutes,"'")

        #await client.stop_rendering_session(session_id)
        #print("session with id:'",session_id,"' stopped")

        #s = await client.get_rendering_session(session_id)
        #while not(s.status == SessionStatus.STOPPED or s.status == SessionStatus.EXPIRED):
        #    s = await client.get_rendering_session(session_id)
        #    print("session still running after stop")
        #    time.sleep(5)

        print("listing sessions for account: '",account_id,"'")
        print("sessions:")
        pageable = await client.list_rendering_sessions()
        async for s in pageable:
            print("\t session:  id:'",s.id,"' status'",s.status,"'", s.creation_time.strftime("%m/%d/%Y, %H:%M:%S"))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())