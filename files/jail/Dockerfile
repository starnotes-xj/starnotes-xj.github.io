FROM ubuntu:22.04

RUN apt-get update && apt-get install -y python3 openssh-server && \
    mkdir /var/run/sshd && \
    chmod -x /etc/update-motd.d/* && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN printf '%s\n' '#!/bin/bash' 'exec /usr/bin/python3 /home/cpctf-jail/jail.py' > /usr/local/bin/jailsh && \
    chmod 755 /usr/local/bin/jailsh

RUN useradd -m -s /usr/local/bin/jailsh cpctf-jail && \
    echo 'cpctf-jail:cpctf2026' | chpasswd && \
    touch /home/cpctf-jail/.hushlogin && \
    chown cpctf-jail:cpctf-jail /home/cpctf-jail/.hushlogin

WORKDIR /home/cpctf-jail
COPY jail.py /home/cpctf-jail/jail.py

RUN mkdir -p /flag && \
    echo "CPCTF{REDACTED}" > /flag/flag.txt && \
    chown -R root:root /flag && \
    chmod 555 /flag && \
    chmod 444 /flag/flag.txt && \
    chown -R root:root /home/cpctf-jail && \
    chmod 555 /home/cpctf-jail && \
    chmod 444 /home/cpctf-jail/jail.py

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
