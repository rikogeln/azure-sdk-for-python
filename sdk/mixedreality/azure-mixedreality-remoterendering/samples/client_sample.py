# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
import uuid 
import time

from azure.mixedreality.remoterendering import RemoteRenderingClient
from azure.mixedreality.remoterendering import ConversionInputSettings
from azure.mixedreality.remoterendering import ConversionOutputSettings
from azure.mixedreality.remoterendering import ConversionSettings
from azure.mixedreality.remoterendering import ConversionStatus
from azure.mixedreality.remoterendering import SessionSize
from azure.mixedreality.remoterendering import SessionStatus

if __name__ == '__main__':
    account_id = os.environ.get("ARR_ACCOUNT_ID", None)
    if not account_id:
        raise ValueError("Set ARR_ACCOUNT_ID env before run this sample.")

    arr_endpoint = os.environ.get("ARR_ENDPOINT", None)
    if not arr_endpoint:
        raise ValueError("Set ARR_ENDPOINT env before run this sample.")

    sts_token = os.environ.get("ARR_STS_TOKEN", None)
    if not sts_token:
        raise ValueError("Set ARR_STS_TOKEN env before run this sample.")

    client = RemoteRenderingClient(service_url=arr_endpoint, account_id=account_id, sts_token=sts_token)

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

    conversionOperation = client.begin_asset_conversion(conversion_id= conversion_id, conversion_options= options)
    print("conversion with id:'",conversion_id,"' created")
    conversion = conversionOperation.result()
    print("conversion with id:'",conversion_id,"' finished with result:'", conversion.status,"'")
    if(conversion.status == ConversionStatus.SUCCEEDED):
        print(conversion.output.output_asset_uri)

    session_id = str(uuid.uuid4())
    print("starting session with id:'",session_id,"'")
    sessionOperation = client.begin_rendering_session(session_id, SessionSize.STANDARD, 5)
    session = sessionOperation.result()
    print("session with id:'",session.id,"' created. LeaseTime:'",session.max_lease_time_minutes,"'")
    print(session)

    session = client.extend_rendering_session(session_id, 10)
    print("session with id:'",session_id,"' updated")
    print("session with id:'",session.id,"' created. LeaseTime:'",session.max_lease_time_minutes,"'")

    client.stop_rendering_session(session_id)
    print("session with id:'",session_id,"' stopped")

    s = client.get_rendering_session(session_id)
    while not(s.status == SessionStatus.STOPPED or s.status == SessionStatus.EXPIRED):
        s = client.get_rendering_session(session_id)
        print("session still running after stop")
        time.sleep(5)

    print("listing sessions for account: '",account_id,"'")
    print("sessions:")
    pageable = client.get_sessions()
    for s in pageable:
        print("\t session:  id:'",s.id,"' status'",s.status,"'", s.creation_time.strftime("%m/%d/%Y, %H:%M:%S"))
        client.stop_rendering_session(s.id)

    #print("listing conversions for account: '",account_id,"'")
    #print("conversion:")
    #pageable = client.get_conversions()
    #for c in pageable:
    #    print("\t conversion:  id:'",c.id,"' status'",c.status,"'", c.creation_time.strftime("%m/%d/%Y, %H:%M:%S"))
    #    if(c.status == ConversionStatus.SUCCEEDED):
    #        print("\t\toutput: '",c.output.output_asset_uri,"'")

    