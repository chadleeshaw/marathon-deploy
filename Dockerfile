from frolvlad/alpine-python3

WORKDIR /marathon-deploy
COPY ./ /marathon-deploy
COPY ./cert.crt /usr/local/share/ca-certificates/cert.crt

RUN pip install -r requirements.txt&& \
    apk update && apk add curl ca-certificates bash git openssh && \
    update-ca-certificates --fresh > /dev/null 2>&1 && \
    rm -rf /var/cache/apk/*

ENV REQUESTS_CA_BUNDLE=/usr/local/share/ca-certificates/cert.crt
