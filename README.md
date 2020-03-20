<p align="center">
  <img height="200px" src="https://docs.google.com/drawings/d/e/2PACX-1vQ0AFza3nHkrhe0Fam_NAZF5wgGzskKTV5To4cfHAmrCuhr3cZnJiZ3pD1OfXVP72A435b5IlsduoQC/pub?w=580&h=259" alt="chantilly_logo">
</p>

<p align="center">
  <b>chantilly</b> is a tool for deploying <a href="https://www.wikiwand.com/en/Online_machine_learning">online machine learning</a> models built with <a href="https://github.com/creme-ml/creme">creme</a> into production. It takes care of building API routes, visualizing activity, monitoring performance, and alerting you if something goes wrong.
</p>

## Installation

```sh
> pip install git+https://github.com/creme-ml/chantilly
```

## Usage

```sh
> chantilly run
```

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

## Similar alternatives

Most machine learning deployment tools only support making predictions with a trained model. They don't cater to online models which can be updated on the fly. However, some of them are very interesting and are very much worth looking into!

- [Cortex](https://github.com/cortexlabs/cortex)
- [Clipper](https://github.com/ucbrise/clipper)
