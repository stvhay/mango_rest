import json
import os
from dotenv import load_dotenv

import pendulum
import mango_rest
from data_models import WatchList, WatchLists, PointList


def test_print(title, func, raw=False):
    result = func()
    print('-'*80)
    print(title)
    print('-'*80)
    if not raw:
        print(result.json(indent=2))
    else:
        print(json.dumps(result.json(), indent=2))
    print()
    return result


if __name__ == '__main__':
    load_dotenv()
    mango_url = os.getenv('mango_url')
    username = os.getenv('username')
    password = os.getenv('password')

    with mango_rest.MangoClient(mango_url, username, password) as c:
        # Get Watchlist list or Watchlist items
        wls = test_print("Watchlists", c.watchlists)
        wl = test_print("Watchlist", lambda: c.watchlist(wls.items[0].xid))

        # Dynamic points list
        rql = 'match(name,JVM*)&match(deviceName,*)&sort(name)&limit(200)'
        pl = test_print("Dynamic Watchlist", lambda: c.pointquery(rql))

        # Get metrics/values
        hours = 6
        dt_end = pendulum.now()
        dt_begin = dt_end.subtract(hours=hours)
        query_params = {
            "bookend": True,
            "from": dt_begin.isoformat(), 
            "to": dt_end.isoformat()
        }
        # point_xids = [ point.xid for point in wl.points ]     # from a watch list
        point_xids = [ point.xid for point in pl.items ]      # from a point list

        # Single Array
        func_single = lambda: c.get(f'/rest/latest/point-values/single-array/time-period/{",".join(point_xids)}', params=query_params)
        v_single = test_print("Point Values (Single Array)", func_single, raw=True)

        # Multiple Arrays
        func_multiple = lambda: c.get(f'/rest/latest/point-values/multiple-arrays/time-period/{",".join(point_xids)}', params=query_params)
        v_multiple = test_print("Point Values (Multiple Arrays)", func_multiple, raw=True)

    # Plot from Multiple
    import plotext as plt
    num_plots = len(v_multiple.json())
    plt.clf()
    plot_num = 1
    for point_name, values in v_multiple.json().items():
        x, y = zip(*((value['timestamp'], value['value']) for value in values))
        plt.xlabel('timestamp')
        plt.plot(x, y, label=point_name)
    plt.show()



