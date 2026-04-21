FROM python:3.14.2-alpine3.23@sha256:7af51ebeb83610fb69d633d5c61a2efb87efa4caf66b59862d624bb6ef788345

RUN pip install pycryptodome
RUN mkdir /app
WORKDIR /app
COPY app.py .
ENTRYPOINT [ "python3", "/app/app.py" ]
