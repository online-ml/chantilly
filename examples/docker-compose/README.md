## Example usage with Docker Compose

Warning: this is still work in progress!

This directory is an example of how to use [Docker Compose](https://docs.docker.com/compose/) to deploy a chantilly instance. The [Dockerfile](Dockerfile) file contains the commands that are ran to install Python, chantilly, and [Gunicorn](https://docs.gunicorn.org/en/stable/index.html). It then runs a Chantilly instance via Gunicorn and exposes port `5000`. The [docker-compose.yml](docker-compose.yml) runs this Dockerfile along with a Redis instance.

The whole setup can be started via the following command:

```sh
> docker-compose up -d
```

This will run the whole stack in the background. The Chantilly instance is now accessible at [`localhost:5000`](http://localhost:8080).

You can run the `test.py` script to set a flavor, upload a model, and train the model with some observations in order that everything is working as intented. Note that this script requires having `creme`, `dill`, and `requests` installed.

```sh
> python test.py
```

You can also navigate to [`localhost:5000/api/stats`](http://localhost:5000/api/stats) and verify the output.

Now that this is working locally, it can be deployed to a remote machine. Having things nice and tidily configured via Docker Compose is helpful because it simplifies deployment.
