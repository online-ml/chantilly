import bisect
import collections
import time


TRIPS = [
    ({'time': 0}, 2),
    ({'time': 1}, 5),
    ({'time': 2}, 2),
    ({'time': 3}, 1),
    ({'time': 4}, 2),
]


class Trip(collections.namedtuple('Time', 'info duration')):
    """Utility class for playing nice with bisect."""

    @property
    def departure_time(self):
        return self.info['time']

    @property
    def arrival_time(self):
        return self.departure_time + self.duration

    def __lt__(self, other):
        return self.duration < other.duration


def retrace_events(trips):

    ongoing = []

    for x, y in trips:

        trip = Trip(x, y)

        while ongoing:

            # Look at the oldest trip in the queue
            old_trip = ongoing[0]

            # Don't do anything if the trip is still ongoing
            if old_trip.arrival_time > trip.departure_time:
                break

            # Reveal the duration and pop the trip from the queue
            yield old_trip
            del ongoing[0]

        yield Trip(trip.info, None)
        bisect.insort(ongoing, trip)

    yield from ongoing


if __name__ == '__main__':

    # Use the first trip's departure time as a reference time
    now = TRIPS[0][0]['time']

    for trip in retrace_events(iter(TRIPS)):

        if trip.duration is None:
            time.sleep(trip.departure_time - now)
            now = trip.departure_time
            print('PREDICT', now)
            continue

        time.sleep(trip.arrival_time - now)
        now = trip.arrival_time
        print('LEARN', now)
