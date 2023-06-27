import json
import os
import re
from dotenv import load_dotenv

import pendulum
import mango_rest_sync as mango_rest
from data_models import WatchList, WatchLists, PointList

def rql(device_name, point_name):
    return f'match(name,{point_name})&match(deviceName,{device_name})&sort(name)&limit(500)'

def pull(clients, query, tag='values'):
    for client_object in clients:
        c = client_object['client']
        pl = c.pointquery(query)
        dt_end = pendulum.now()
        dt_begin = dt_end.subtract(seconds=10)

        query_params = {
            "bookend": True,
            "from": dt_begin.isoformat(), 
            "to": dt_end.isoformat()
        }
        point_xids = [ point.xid for point in pl.items ]      # from a point list
        point_device_names = [ point.deviceName for point in pl.items ]
        client_object['modules'] = [ re.match(r'.*Module (\d\d).*', device_name)[1] for device_name in point_device_names ]
        client_object['nodes'] = [ re.match(r'.*Node (\d\d).*', device_name)[1] for device_name in point_device_names ]

        # Multiple Arrays
        response = c.get(f'/rest/latest/point-values/multiple-arrays/time-period/{",".join(point_xids)}', params=query_params).json()
        client_object[tag] = [ metrics[-1]['value'] for xid, metrics in response.items() ]



def test_first_fault(clients):
    device_name = '*PCS'
    point_name = 'First Trip'
    query = rql(device_name, point_name)
    pull(clients, query)

if __name__ ==  '__main__':
    # initialize from .env
    load_dotenv()
    username = os.getenv('username')
    password = os.getenv('password')

    # activate the Mango clients
    clients = []
    for array in ["01", "02", "03"]:
        for core in ["01", "02", "03", "04"]:
            clients.append({
                "array": array,
                "core": core,
                "client": mango_rest.MangoClient(f'https://sdge-escondido{array}-core{core}.fluenceenergy.com:9443', username, password).open()
            })

    # Run First Fault test and output TSV
    # test_first_fault(clients)
    pull(clients, rql('*PCS', 'First Trip'), tag='pcs_first_trip')
    pull(clients, rql('*PCS', 'Firmware Version'), tag='pcs_firmware_version')
    pull(clients, rql('*PCS', 'Config Version'), tag='pcs_config_version')
    pull(clients, rql('*', 'Node Current State'), tag='node_current_state')
    pull(clients, rql('*BMS', '0045 - First fault code'), tag='bms_first_fault_code')
    pull(clients, rql('*BMS', '0020 - Number of total strings'), tag='bms_number_of_total_strings')
    pull(clients, rql('*BMS', '0060 - Hardware version'), tag='bms_hardware_version')
    pull(clients, rql('*BMS', '0061 - Software version'), tag='bms_software_version')
    
    print('array\tcore\tmodule\tnode\tnode_current_state\tpcs_first_trip\tpcs_firmware_version\tpcs_config_version\tbms_first_fault_code\tbms_number_of_total_strings\tbms_hardware_version\tbms_software_version')
    for client_object in clients:
        array = client_object['array']
        core = client_object['core']
        for module, node, node_current_state, pcs_first_trip, pcs_firmware_version, pcs_config_version, bms_first_fault_code, bms_number_of_total_strings, bms_hardware_version, bms_software_version in \
                zip(client_object['modules'], 
                client_object['nodes'], 
                client_object['node_current_state'], 
                client_object['pcs_first_trip'], 
                client_object['pcs_firmware_version'],
                client_object['pcs_config_version'],
                client_object['bms_first_fault_code'], 
                client_object['bms_number_of_total_strings'],
                client_object['bms_hardware_version'],
                client_object['bms_software_version']):
            print(f"{array}\t{core}\t{module}\t{node}\t{node_current_state}\t{pcs_first_trip}\t{pcs_firmware_version}\t{pcs_config_version}\t{bms_first_fault_code}\t{bms_number_of_total_strings}\t{bms_hardware_version}\t{bms_software_version}")
