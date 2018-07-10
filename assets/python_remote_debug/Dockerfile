FROM python:2.7

ENV TERM xterm
ENV TINI_VERSION v0.18.0

WORKDIR /root/

RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests \
    openssh-server \
    sudo \
    vim \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

copy ["assets/python_remote_debug/sudoers", "/etc/sudoers"]

RUN mkdir -p /var/run/sshd && \
    mkdir /root/.ssh && chmod 700 /root/.ssh && \
    touch /root/.ssh/authorized_keys

COPY ["Pipfile*", "/root/"]

RUN pip install pipenv setuptools && \
    pipenv install --system

ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

EXPOSE 22
ENTRYPOINT ["/tini", "--"]
CMD ["/usr/sbin/sshd", "-D", "-e"]
