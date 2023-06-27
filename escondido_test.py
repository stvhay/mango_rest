import json
import os
import re
from dotenv import load_dotenv
import yaml

import pendulum
import mango_rest
from data_models import WatchList, WatchLists, PointList
import asyncio

def rql(device_name, point_name):
    return f'match(name,{point_name})&match(deviceName,{device_name})&sort(name)&limit(500)'

"""
Example YAML entry. This is a single element list with device_name, point_name, and tag defined:
- device_name: '*PCS'
  point_name: 'First Trip'
  tag: 'pcs_first_trip'
"""
def load_rql_data_from_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def save_rql_data_to_yaml(rql_data, file_path):
    with open(file_path, 'w') as file:
        yaml.dump(rql_data, file)

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
    pull_parameters = load_rql_data_from_yaml('rql_data.yaml')

    # activate the Mango clients
    clients = []
    for array in ["01", "02", "03"]:
        for core in ["01", "02", "03", "04"]:
            clients.append({
                "array": array,
                "core": core,
                "client": await mango_rest.MangoClient(f'https://sdge-escondido{array}-core{core}.fluenceenergy.com:9443', username, password).open()
            })

    # Run First Fault test and output TSV
    data_pulls = []
    for pull_parameter in pull_parameters:
        device_name = pull_parameter['device_name']
        point_name = pull_parameter['point_name']
        tag = pull_parameter['tag']
        for client_object in clients:
            data_pulls.append(pull(client_object, rql(device_name, point_name), tag=tag))
    await asyncio.gather(*data_pulls)

    # print headings and then data
    print('array\tcore\tmodule\tnode', end='')
    for pull_parameter in pull_parameters:
        print(f'\t{pull_parameter["tag"]}', end='')
    print()

    for client_object in clients:
        for columns in zip(client_object['modules'], client_object['nodes'], *([client_object[parameter['tag']] for parameter in pull_parameters])):
            print(f"{client_object['array']}", end='')
            print(f"\t{client_object['core']}", end='')
            for column in columns:
                print(f'\t{column}', end='')
            print()

# Run the event loop
asyncio.run(main())
