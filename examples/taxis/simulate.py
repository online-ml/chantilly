import datetime as dt
import json
import time

from creme import datasets
from creme import metrics
from creme import stream
import requests


SPEED_UP = 5  # Increase this to make the simulation go faster


def sleep(td: dt.timedelta):
    if td.seconds >= 0:
        time.sleep(td.seconds / SPEED_UP)


class colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'


if __name__ == '__main__':

    # Use the first trip's departure time as a reference time
    taxis = datasets.Taxis()
    now = next(iter(taxis))[0]['pickup_datetime']
    mae = metrics.MAE()
    host = 'http://localhost:5000'
    predictions = {}

    for trip_no, trip, duration in stream.simulate_qa(
        taxis,
        moment='pickup_datetime',
        delay=lambda _, duration: dt.timedelta(seconds=duration)
    ):

        trip_no = str(trip_no).zfill(len(str(taxis.n_samples)))

        # Taxi trip starts

        if duration is None:

            # Wait
            sleep(trip['pickup_datetime'] - now)
            now = trip['pickup_datetime']

            # Ask chantilly to make a prediction
            r = requests.post(host + '/api/predict', json={
                'id': trip_no,
                'features': {**trip, 'pickup_datetime': trip['pickup_datetime'].isoformat()}
            })

            # Store the prediction
            predictions[trip_no] = r.json()['prediction']

            print(colors.GREEN + f'#{trip_no} departs at {now}' + colors.ENDC)
            continue

        # Taxi trip ends

        # Wait
        arrival_time = trip['pickup_datetime'] + dt.timedelta(seconds=duration)
        sleep(arrival_time - now)
        now = arrival_time

        # Ask chantilly to update the model
        requests.post(host + '/api/learn', json={'id': trip_no, 'target': duration})

        # Update the metric
        mae.update(y_true=duration, y_pred=predictions.pop(trip_no))

        msg = f'#{trip_no} arrives at {now} - average error: {dt.timedelta(seconds=mae.get())}'
        print(colors.BLUE + msg + colors.ENDC)
