import os

in_cluster = os.environ.get('IN_CLUSTER', '1').lower() in ('1', 'true', 'yes')


pod_label_selector = 'pgdump=true'
dump_command = 'pg_dump --username={POSTGRES_USER} --dbname={POSTGRES_DB} --format=t --clean ' \
               '--file={PGDATA}/{filename}'

