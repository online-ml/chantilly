<p align="center">
  <img height="200px" src="https://docs.google.com/drawings/d/e/2PACX-1vQ0AFza3nHkrhe0Fam_NAZF5wgGzskKTV5To4cfHAmrCuhr3cZnJiZ3pD1OfXVP72A435b5IlsduoQC/pub?w=580&h=259" alt="chantilly_logo">
</p>

<p align="center">
  <b>chantilly</b> is a tool for deploying <a href="https://www.wikiwand.com/en/Online_machine_learning">online machine learning</a> models built with <a href="https://github.com/creme-ml/creme">creme</a> into production. It takes care of building API routes, monitoring performance, and alerting when things go wrong.</b>.
</p>

## Setup

### MacOS

**InfluxDB**

```sh
brew install influxdb
influxd -config /usr/local/etc/influxdb.conf
```

**chantilly**

```sh
pip install git+https://github.com/creme-ml/chantilly
env FLASK_APP=chantilly
flask run
```
