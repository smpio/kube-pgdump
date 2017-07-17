#!/usr/bin/env bash

set -ex
PGDUMP_LABEL_SELECTOR="pgdump=true"

function run_lftp {
    lftp -u ${FTP_LOGIN},${FTP_PASSWORD} -e "set ftp:ssl-allow no;${1}quit;" ${FTP_SERVER} ${@:2}
}

function get_env_var {
    kubectl -n $1 exec $2 -- printenv | grep "${3}=" | sed  "s/${3}=//g"
}

for pod_path in $(kubectl get pod -l "${PGDUMP_LABEL_SELECTOR}" --all-namespaces | awk '{if ($4=="Running") printf ("%s/%s\n",$1,$2) }'); do
     IFS=/ read namespace pod_name <<< "${pod_path}"

     pguser=$(get_env_var $namespace $pod_name POSTGRES_USER)
     pgdb=$(get_env_var $namespace $pod_name POSTGRES_DB)

     deployment_name=$(echo $pod_name | rev | cut -d- -f3- | rev)

     ftp_workdir="/${namespace}/${deployment_name:=${pod_name}}"

     run_lftp "mkdir -fp ${ftp_workdir};" || true

     while [ "$(run_lftp "cd ${ftp_workdir};ls -tr;" | grep "tar\.gz$" | wc -l)" -ge "${MAX_BACKUP_COUNT}" ]; do
        filename=$(run_lftp "cd ${ftp_workdir};ls -1qtr;" | grep "tar\.gz$" | head -1);
        run_lftp "rm ${ftp_workdir}/${filename};";
     done

     now=$(date -u +"%d.%m.%y-%k:%M")
     dump_name="${now}.tar.gz"

     kubectl -n ${namespace} exec -ti ${pod_name} -- pg_dump --username=${pguser:=postgres} --dbname=${pgdb:=postgres} --format=t --clean \
     | curl --limit-rate ${RATE_LIMIT} -T - ftp://${FTP_LOGIN}:${FTP_PASSWORD}@${FTP_SERVER}${ftp_workdir}/${dump_name}
done