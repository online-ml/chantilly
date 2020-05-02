FROM python:3.7

RUN mkdir /app
WORKDIR /app
ADD . /app/
RUN pip install --upgrade pip
RUN pip install chantilly[redis] gunicorn[gevent]

ENV SECRET_KEY keep_it_secret_keep_it_safe
ENV STORAGE_BACKEND redis
ENV REDIS_HOST redis
ENV REDIS_PORT 6379
ENV REDIS_DB 0

EXPOSE 5000
ENTRYPOINT ["gunicorn", "-k", "gevent", "-w", "4", "-b", "0.0.0.0:5000", "chantilly:create_app()"]
