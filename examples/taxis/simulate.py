import time

from creme import stream


TRIPS = [
    ({'time': 0}, 2),
    ({'time': 1}, 5),
    ({'time': 2}, 2),
    ({'time': 3}, 1),
    ({'time': 4}, 2),
]


if __name__ == '__main__':

    # Use the first trip's departure time as a reference time
    now = TRIPS[0][0]['time']

    for i, trip, delay in stream.simulate_qa(TRIPS, moment='time', delay=lambda _, delay: delay):

        # Question
        if delay is None:
            time.sleep(trip['time'] - now)
            now = trip['time']
            print('PREDICT', now)
            continue

        # Answer
        arrival_time = trip['time'] + delay
        time.sleep(arrival_time - now)
        now = arrival_time
        print('LEARN', now)
