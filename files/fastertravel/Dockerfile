FROM ubuntu:24.04@sha256:b359f1067efa76f37863778f7b6d0e8d911e3ee8efa807ad01fbf5dc1ef9006b

ADD --chmod=0755 --checksum=sha256:c125df9762b0c7233459087bb840c0e5dbfc4d9690ee227f1ed8994f4d51d2e0 \
    https://raw.githubusercontent.com/reproducible-containers/repro-sources-list.sh/v0.1.4/repro-sources-list.sh \
    /usr/local/bin/repro-sources-list.sh
RUN repro-sources-list.sh

RUN apt-get update && apt-get install -y python3 tar

ADD --checksum=sha256:0542edbb5ce0d6987de6a37caa2bbc52a42445ec094fb9ba3e605534af5dd898 \
    https://github.com/caddyserver/caddy/releases/download/v2.9.1/caddy_2.9.1_linux_amd64.tar.gz \
    /tmp/caddy.tar.gz
RUN tar -xzf /tmp/caddy.tar.gz -C /usr/local/bin/ caddy && rm /tmp/caddy.tar.gz && chmod +x /usr/local/bin/caddy

COPY Caddyfile /etc/caddy/Caddyfile

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . .

EXPOSE 5000

CMD ["sh", "-c", "python3 /app/app.py & /usr/local/bin/caddy run --config /etc/caddy/Caddyfile"]
