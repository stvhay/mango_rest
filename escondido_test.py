import json
import os
import re
from dotenv import load_dotenv

import pendulum
import mango_rest
from data_models import WatchList, WatchLists, PointList
import asyncio

def rql(device_name, point_name):
    return f'match(name,{point_name})&match(deviceName,{device_name})&sort(name)&limit(500)'

async def pull(client_object, query, tag='values'):
    c = client_object['client']
    pl = await c.pointquery(query)
    dt_end = pendulum.now()
    dt_begin = dt_end.subtract(seconds=10)

    query_params = {
        "bookend": True,
        "from": dt_begin.isoformat(), 
        "to": dt_end.isoformat()
    }
    point_xids = [point.xid for point in pl.items]  # from a point list
    point_device_names = [point.deviceName for point in pl.items]
    client_object['modules'] = [re.match(r'.*Module (\d\d).*', device_name)[1] for device_name in point_device_names]
    client_object['nodes'] = [re.match(r'.*Node (\d\d).*', device_name)[1] for device_name in point_device_names]

    # Multiple Arrays
    response = await c.get(f'/rest/latest/point-values/multiple-arrays/time-period/{",".join(point_xids)}', params=query_params)
    response_data = response.json()
    client_object[tag] = [metrics[-1]['value'] for xid, metrics in response_data.items()]



async def main():
    # initialize from .env
    load_dotenv()
    username = os.getenv('username')
    password = os.getenv('password')

    # activate the Mango clients
    print("Activating Mango Clients...")
    clients = []
    for array in ["01", "02", "03"]:
        for core in ["01", "02", "03", "04"]:
            clients.append({
                "array": array,
                "core": core,
                "client": await mango_rest.MangoClient(f'https://sdge-escondido{array}-core{core}.fluenceenergy.com:9443', username, password).open()
            })

    print("Beginning Data Pull...")
    # Run First Fault test and output TSV
    await asyncio.gather(
        *[pull(client_object, rql('*PCS', 'First Trip'),                     tag='pcs_first_trip')              for client_object in clients],
        *[pull(client_object, rql('*PCS', 'Firmware Version'),               tag='pcs_firmware_version')        for client_object in clients],
        *[pull(client_object, rql('*PCS', 'Config Version'),                 tag='pcs_config_version')          for client_object in clients],
        *[pull(client_object, rql('*', 'Node Current State'),                tag='node_current_state')          for client_object in clients],
        *[pull(client_object, rql('*BMS', '0045 - First fault code'),        tag='bms_first_fault_code')        for client_object in clients],
        *[pull(client_object, rql('*BMS', '0020 - Number of total strings'), tag='bms_number_of_total_strings') for client_object in clients],
        *[pull(client_object, rql('*BMS', '0060 - Hardware version'),        tag='bms_hardware_version')        for client_object in clients],
        *[pull(client_object, rql('*BMS', '0061 - Software version'),        tag='bms_software_version')        for client_object in clients]
    )

    print('array\tcore\tmodule\tnode\tnode_current_state\tpcs_first_trip\tpcs_firmware_version\tpcs_config_version\tbms_first_fault_code\tbms_number_of_total_strings\tbms_hardware_version\tbms_software_version')
    for client_object in clients:
        array = client_object['array']
        core = client_object['core']
        for (
            module,
            node,
            node_current_state,
            pcs_first_trip,
            pcs_firmware_version,
            pcs_config_version,
            bms_first_fault_code,
            bms_number_of_total_strings,
            bms_hardware_version,
            bms_software_version,
        ) in zip(
            client_object['modules'],
            client_object['nodes'],
            client_object['node_current_state'],
            client_object['pcs_first_trip'],
            client_object['pcs_firmware_version'],
            client_object['pcs_config_version'],
            client_object['bms_first_fault_code'],
            client_object['bms_number_of_total_strings'],
            client_object['bms_hardware_version'],
            client_object['bms_software_version'],
        ):
            print(
                f"{array}\t{core}\t{module}\t{node}\t{node_current_state}\t{pcs_first_trip}\t{pcs_firmware_version}\t{pcs_config_version}\t{bms_first_fault_code}\t{bms_number_of_total_strings}\t{bms_hardware_version}\t{bms_software_version}"
            )

# Run the event loop
asyncio.run(main())
