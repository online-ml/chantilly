# Predicting taxi trip durations

In this example we'll build a model to predict the duration of taxi trips in the city of New-York. To make things realistic, we'll run a simulation where the taxis leave and arrive in the order as given in the dataset. Indeed, we can reproduce a live workload from a historical dataset, therefore producing an environment which is very close to what happens in a production setting.

Before running the simulation, we will run an instance of `chantilly`. For the purpose of this example, we'll assume that chantilly is being served in one command-line session, while we run the rest of the commands in another session.

```sh
> chantilly run
```

Let's now create a model using `creme`. Simply run the following snippet in a Python interpreter.

```python
from creme import compose
from creme import linear_model
from creme import preprocessing


def parse(trip):
    import datetime as dt
    trip['pickup_datetime'] = dt.datetime.fromisoformat(trip['pickup_datetime'])
    return trip


def distances(trip):
    import math
    lat_dist = trip['dropoff_latitude'] - trip['pickup_latitude']
    lon_dist = trip['dropoff_longitude'] - trip['pickup_longitude']
    return {
        'manhattan_distance': abs(lat_dist) + abs(lon_dist),
        'euclidean_distance': math.sqrt(lat_dist ** 2 + lon_dist ** 2)
    }


def datetime_info(trip):
    import calendar
    return {
        calendar.day_name[trip['pickup_datetime'].weekday()]: True,
        'hour': trip['pickup_datetime'].hour
    }


model = compose.FuncTransformer(parse)
model |= compose.FuncTransformer(distances) + compose.FuncTransformer(datetime_info)
model |= preprocessing.StandardScaler()
model |= linear_model.LinearRegression()
```

The required modules are imported within each function for serialization reasons.

We can now upload the model to the `chantilly` instance with an API call, for example via the [`requests`](https://requests.readthedocs.io/en/master/) library. Again, in this example we're assuming that `chantilly` is being ran locally, which means it is accessible at address `http://127.0.0.1:5000`.

```python
import dill
import requests

requests.post('http://127.0.0.1:5000/api/model', data=dill.dumps(model))
```

Note that we use [`dill`](https://dill.readthedocs.io/en/latest/dill.html) to serialize the model, and not [`pickle`](https://docs.python.org/3/library/pickle.html) which is part of Python's standard library. The reason why is because `dill` is able to serialize a whole session, and therefore deals with custom functions and module imports.

We are now all set to run the simulation.

```sh
> python simulate.py
```

This will produce the following output:

```sh
#0000000 departs at 2016-01-01 00:00:17
#0000001 departs at 2016-01-01 00:00:53
#0000002 departs at 2016-01-01 00:01:01
#0000003 departs at 2016-01-01 00:01:14
#0000004 departs at 2016-01-01 00:01:20
#0000005 departs at 2016-01-01 00:01:33
#0000006 departs at 2016-01-01 00:01:37
#0000007 departs at 2016-01-01 00:01:47
#0000008 departs at 2016-01-01 00:02:06
#0000009 departs at 2016-01-01 00:02:45
#0000010 departs at 2016-01-01 00:03:02
#0000006 arrives at 2016-01-01 00:03:31 - average error: 0:01:54
#0000011 departs at 2016-01-01 00:03:31
#0000012 departs at 2016-01-01 00:03:35
#0000013 departs at 2016-01-01 00:04:42
#0000014 departs at 2016-01-01 00:04:57
#0000015 departs at 2016-01-01 00:05:07
#0000016 departs at 2016-01-01 00:05:08
#0000017 departs at 2016-01-01 00:05:18
#0000018 departs at 2016-01-01 00:05:35
#0000019 departs at 2016-01-01 00:05:39
#0000003 arrives at 2016-01-01 00:05:54 - average error: 0:03:17
#0000020 departs at 2016-01-01 00:06:04
#0000021 departs at 2016-01-01 00:06:12
#0000022 departs at 2016-01-01 00:06:22
```
