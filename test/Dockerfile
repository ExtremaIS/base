FROM python:3.9-buster

ARG TERM=xterm
ENV TERM=${TERM}

RUN apt-get update \
 && apt-get upgrade --yes \
 && apt-get install --yes sudo \
 && echo "docker ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/docker \
 && pip install --no-cache-dir pexpect \
 && useradd \
      --create-home \
      --shell /bin/bash \
      --groups "adm,staff,sudo" \
      "docker" \
 && rm -rf /var/lib/apt/lists/*

USER docker
WORKDIR /home/docker
