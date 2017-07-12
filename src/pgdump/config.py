import os

in_cluster = os.environ.get('IN_CLUSTER', '1').lower() in ('1', 'true', 'yes')


pod_label_selector = 'pgdump=true'
dump_command = 'pg_dump --username={POSTGRES_USER} --dbname={POSTGRES_DB} --format=t --clean ' \
               '--file={PGDATA}/{filename}'

ftp_image = 'flaky/k8s-ftp-backup:2'
ftp_server = os.environ['FTP_SERVER']
ftp_login = os.environ['FTP_LOGIN']
ftp_password = os.environ['FTP_PASSWORD']

max_backup_count = os.environ['MAX_BACKUP_COUNT']
