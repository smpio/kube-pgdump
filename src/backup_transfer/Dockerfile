FROM debian:wheezy

RUN apt-get update \
    && apt-get install -y lftp

COPY ftp_transfer.sh /ftp_transfer.sh

RUN chmod +x /ftp_transfer.sh

CMD ["/ftp_transfer.sh"]