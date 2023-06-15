import json
import os
import re
from dotenv import load_dotenv

import pendulum
import mango_rest
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
    pull(clients, rql('*PCS', 'First Trip'), tag='first_trip')
    print('array\tcore\tmodule\tnode\tfirst_trip')
    for client_object in clients:
        array = client_object['array']
        core = client_object['core']
        for module, node, first_trip in zip(client_object['modules'], client_object['nodes'], client_object['first_trip']):
            print(f"{array}\t{core}\t{module}\t{node}\t{first_trip}")
