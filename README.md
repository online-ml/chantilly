<p align="center">
  <img height="200px" src="https://docs.google.com/drawings/d/e/2PACX-1vQ0AFza3nHkrhe0Fam_NAZF5wgGzskKTV5To4cfHAmrCuhr3cZnJiZ3pD1OfXVP72A435b5IlsduoQC/pub?w=580&h=259" alt="chantilly_logo">
</p>

<p align="center">
  <code>chantilly</code> is a tool for deploying <a href="https://www.wikiwand.com/en/Online_machine_learning">online machine learning</a> models built with <a href="https://github.com/creme-ml/creme"><code>creme</code></a>.
</p>

## Installation

```sh
> pip install git+https://github.com/creme-ml/chantilly
```

## User guide

### Running the server

Once you've followed the installation step, you'll get access to the `chantilly` CLI. You can see the available commands by running `chantilly --help`. You can start a server with the `run` command:

```sh
> chantilly run
```

This will start a [Flask](https://flask.palletsprojects.com/en/1.0.x/) server with all the necessary routes for uploading a model, training it, making predictions with it, and monitoring it. By default, the server will be accessible at [`localhost:5000`](http://localhost:5000), which is what we will be using in the rest of the examples in the user guide. You can run `chantilly routes` in order to see all the available routes.

### Uploading a model

You can upload a `creme` model by sending a POST request to the `@/api/model` route. Because `chantilly` uses [`dill`](https://github.com/uqfoundation/dill) for serialization, you'll have to use that too. For instance:

```py
from creme import compose
from creme import linear_model
from creme import preprocessing
import dill
import requests

model = compose.Pipeline(
    preprocessing.StandardScaler(),
    linear_model.LinearRegression()
)

requests.post('http://localhost:5000/api/model', data=dill.dumps(model))
```

Likewise, the model can be retrieved by sending a GET request to `@/api/model`:

```py
r = requests.get('http://localhost:5000/api/model')
model = pickle.loads(r.content)
```

Note that `chantilly` only supports models that implement `fit_one` and either one of `predict_one` and `predict_proba_one`.

### Making a prediction

Predictions can be obtained by sending a POST request to `@/api/predict`. The payload you send has to contain a field named `features`. The value of this field will be passed to the `predict_one` method of the model you uploaded earlier on. If the model you provided `predict_proba_one` then that will be used instead. Here is an example:

```py
r = requests.post('http://localhost:5000/api/predict', json={
    'id': 42,
    'features': {
        'shop': 'Ikea',
        'item': 'Dombäs',
        'date': '2020-03-22T10:42:29Z'
    }
})

print(r.json()['prediction'])
```

Note that in the previous snippet we've also provided an `id` field. This field is optional. If is is provided, then the features will be stored by the `chantilly` server, along with the prediction. This allows not having to provide the features again when you want to update the model later on.

### Updating the model

The model can be updated by sending a POST request to `@/api/learn`. If you've provided an ID in an earlier call to `@/api/predict`, then you only have to provide said ID along with the ground truth:

```py
requests.post('http://localhost:5000/api/learn', json={
    'id': 42,
    'ground_truth': 10.21
})
```

However, if you haven't passed an ID earlier on, then you have to provide the features yourself:

```py
requests.post('http://localhost:5000/api/learn', json={
    'features': {
        'shop': 'Ikea',
        'item': 'Dombäs',
        'date': '2020-03-22T10:42:29Z'
    },
    'ground_truth': 10.21
})
```

Note that the `id` field will have precedence in case both of `id` and `features` are provided.

### Monitoring metrics

You can access the current metrics via a GET request to the `@/api/metrics` route.

Additionally, you can access a stream of metric updates by using the `@/api/stream/metrics`. This is a streaming route which implements [server-sent events (SSE)](https://www.wikiwand.com/en/Server-sent_events). As such it will notify listeners every time the metrics are updates. For instance, you can use the [`sseclient`](https://github.com/btubbs/sseclient) library to monitor the metrics from a Python script:

```py
import json
import sseclient

messages = sseclient.SSEClient('http://localhost:5000/api/stream/metrics')

for msg in messages:
    metrics = json.loads(msg.data)
    print(metrics)
```

You can use the following piece of JavaScript to do the same thing in a browser:

```js
var es = new EventSource('http://localhost:5000/api/stream/metrics');
es.onmessage = e => {
    var metrics = JSON.parse(e.data);
    console.log(metrics)
};
```

### Monitoring events

You can also listen to all the prediction and learning events via the `@/api/stream/events` route. This will yield SSE events with an event name attached, which is either 'predict' or 'learn'. From a Python interpreter, you can do the following:

```py
import json
import sseclient

messages = sseclient.SSEClient('http://localhost:5000/api/stream/events')

for msg in messages:
    metrics = json.loads(msg.data)
    print(msg.event, metrics)
```

In JavaScript, you can you use the [`addEventListener`](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener) method:

```js
var es = new EventSource('http://localhost:5000/api/stream/events');

es.addEventListener('learn', = e => {
    var data = JSON.parse(e.data);
    console.log(data.features, data.prediction, data.ground_truth)
};

es.addEventListener('predict', = e => {
    var data = JSON.parse(e.data);
    console.log(data.features, data.prediction)
};
```

### Visual monitoring

A live dashboard is accessible if you navigate to [`localhost:5000`](http://localhost:5000) in your browser.

<p align="center">
  <img src="demo.gif" alt="demo">
</p>

Under the hood the dashboard is simply listening to streaming routes of the API.

### Deployment

Essentially, `chantilly` is just a Flask application. Therefore, it allows the same [deployment options](https://flask.palletsprojects.com/en/1.1.x/deploying/) as any other Flask application.

## Examples

- [New-York city taxi trips 🚕](examples/taxis)

## Development

```sh
> git clone https://github.com/creme-ml/chantilly
> cd chantilly
> pip install -e ".[dev]"
> python setup.py develop
> make test
> export FLASK_ENV=development
> chantilly run
```

## Roadmap

- **HTTP long polling**: Currently, clients can interact with `creme` over a straightforward HTTP protocol. Therefore the speed bottleneck comes from the web requests, not from the machine learning. We would like to provide a way to interact with `chantilly` via long-polling. This means that a single connection can be used to process multiple predictions and model updates, which reduces the overall latency.
- **Scaling**: At the moment `chantilly` is designed to be run as a single server. Ideally we want to allow `chantilly` in a multi-server environment. Predictions are simple to scale because the model can be used concurrently. However, updating the model concurrently leads to [reader-write problems](https://www.wikiwand.com/en/Readers%E2%80%93writers_problem). We have some ideas in the pipe, but this is going to need some careful thinking.
- **Grafana dashboard**: The current dashboard is a quick-and-dirty proof of concept. In the long term, we would like to provide a straighforward way to connect with a [Grafana](https://grafana.com/) instance without having to get your hands dirty. Ideally, we would like to use SQLite as a data source for simplicity reasons. However, The Grafana team [has not planned](https://github.com/grafana/grafana/issues/1542#issuecomment-425684417) to add support for SQLite. Instead, they encourage users to use [plugins](https://grafana.com/docs/grafana/latest/plugins/developing/datasources/). We might also look into [Prometheus](https://prometheus.io/) and [InfluxDB](https://www.influxdata.com/).
- **Support more paradigms**: For the moment we cater to regression and classification models. In the future we also want to support other paradigms, such as time series forecasting and recommender systems.

## Technical stack

- [Flask](https://flask.palletsprojects.com/en/1.1.x/) for the web server.
- [dill](https://dill.readthedocs.io/en/latest/dill.html) for model serialization.
- [marshmallow](https://marshmallow.readthedocs.io/en/stable/) for the API input validation.
- [Vue.js](https://vuejs.org/), [Chart.js](https://www.chartjs.org/), and [Moment.js](https://momentjs.com/) for the web interface.

## Similar alternatives

Most machine learning deployment tools only support making predictions with a trained model. They don't cater to online models which can be updated on the fly. Nonetheless, some of them are quite interesting and are very much worth looking into!

- [Cortex](https://github.com/cortexlabs/cortex)
- [Clipper](https://github.com/ucbrise/clipper)
