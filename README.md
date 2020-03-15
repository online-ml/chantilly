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

**InfluxDB**

```sh
> brew install influxdb
> influxd -config /usr/local/etc/influxdb.conf
```

**Grafana**

```sh
> docker run -p 3000:3000 --env GF_SECURITY_ADMIN_USER=admin --env GF_SECURITY_ADMIN_PASSWORD=admin grafana/grafana
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
```

## Roadmap

- **HTTP long polling**: clients can interact with `creme` over a straightforward HTTP protocol. Therefore the speed bottleneck comes from the web requests, not from the machine learning. We would like to provide a way to interact with `chantilly` via long-polling. This means that a single connection can be used to process multiple predictions and model updates, which reduces the overall latency.

## Related projects

- [Cortex](https://github.com/cortexlabs/cortex)
- [Clipper](https://github.com/ucbrise/clipper)
