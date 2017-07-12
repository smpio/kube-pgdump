#!/usr/bin/env bash

set -e

function run_lftp {
    lftp -u ${FTP_LOGIN},${FTP_PASSWORD} -e "set ftp:ssl-allow no;${1}quit;" ${FTP_SERVER} ${@:2}
}

while [ "$(run_lftp "cd ${FTP_WORKDIR};ls -tr;" | grep "tar\.gz$" | wc -l)" -ge "${MAX_BACKUP_COUNT}" ]; do
    filename=$(run_lftp "cd ${FTP_WORKDIR};ls -1qtr;" | grep "tar\.gz$" | head -1);
    run_lftp "rm ${FTP_WORKDIR}/${filename};";
done

run_lftp "cd ${FTP_WORKDIR}/;put ${DUMP_FILENAME};"

echo -e "copy dump success"