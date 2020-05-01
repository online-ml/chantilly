FROM python:3.7

RUN mkdir /app
WORKDIR /app
ADD . /app/
RUN pip install git+https://github.com/creme-ml/chantilly

EXPOSE 5000
CMD ["chantilly", "run"]
