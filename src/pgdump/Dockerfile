FROM debian:jessie-slim

RUN apt-get update \
    && apt-get install -y lftp curl


ENV KUBE_VERSION v1.6.4

RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/${KUBE_VERSION}/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl && mv ./kubectl /usr/local/bin/kubectl

COPY pgdump.sh /pgdump.sh

RUN chmod +x /pgdump.sh

CMD ["/pgdump.sh"]
