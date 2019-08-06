from frolvlad/alpine-python2

WORKDIR /marathon-deploy
COPY ./ /marathon-deploy
COPY ./vivint.crt /usr/local/share/ca-certificates/cert.crt

RUN pip install requests jinja2 prettytable && \
    apk update && apk add curl ca-certificates bash git openssh && \
    update-ca-certificates --fresh > /dev/null 2>&1 && \
    rm -rf /var/cache/apk/*

ENV REQUESTS_CA_BUNDLE=/usr/local/share/ca-certificates/cert.crt
