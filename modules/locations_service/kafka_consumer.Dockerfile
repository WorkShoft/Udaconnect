FROM python:3.7-alpine

WORKDIR .

RUN apk add --no-cache gcc musl-dev linux-headers geos libc-dev postgresql-dev
COPY kafka_service/requirements/base.txt base.txt
RUN pip install --upgrade pip
RUN pip install -r base.txt

COPY . .
CMD ["python", "-m", "kafka_service.kafka_consumer"]
