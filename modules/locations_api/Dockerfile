FROM python:3.7-alpine

WORKDIR .

RUN apk add --no-cache gcc musl-dev linux-headers geos libc-dev postgresql-dev
COPY requirements/base.txt base.txt
RUN pip install --upgrade pip
RUN pip install -r base.txt

EXPOSE 5001

COPY . .
CMD ["python", "wsgi.py"]
