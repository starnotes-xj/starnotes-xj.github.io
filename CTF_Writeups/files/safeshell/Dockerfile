FROM ubuntu:latest

RUN apt-get update && apt-get install -y socat python3 python3-pycryptodome

WORKDIR /app
COPY app.py .
ENTRYPOINT [ "socat", "tcp-listen:5000,reuseaddr,fork", "exec:python3 /app/app.py" ]