FROM python:3.7-buster

WORKDIR .

COPY requirements/base.txt base.txt
COPY requirements/grpc.txt grpc.txt
RUN pip install --upgrade pip
RUN pip install -r base.txt
RUN pip install -r grpc.txt

EXPOSE 5005

COPY . .
CMD ["python", "-m", "grpc_server.main"]
