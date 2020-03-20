from creme import compose
from creme import linear_model
from creme import preprocessing
import dill
import requests


if __name__ == '__main__':

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

    requests.post('http://localhost:5000/api/model', data=dill.dumps(model))
