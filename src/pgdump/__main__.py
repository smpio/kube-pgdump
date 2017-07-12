import datetime
import logging

from pgdump.client import Client
from pgdump import config

log = logging.getLogger(__name__)


def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.NOTSET)
    client = Client()
    for pod in client.pods_for_dump():
        name = pod.metadata.name
        namespace = pod.metadata.namespace
        template_hash = pod.metadata.labels.get('pod-template-hash')
        if template_hash and template_hash in name:
            display_name = name.split(f'-{template_hash}', 1)[0]
        else:
            display_name = name

        log.debug('processing pod %s/%s', namespace, name)

        try:
            log.debug('fetch pvc ...')
            pvc_name = pod.spec.volumes[0].persistent_volume_claim.claim_name
            log.debug('fount %s pvc', pvc_name)
        except IndexError:
            log.error('Not found volumes[pod %s/%s]', namespace, name)
            continue
        except AttributeError:
            log.error('Invalid volume type[pod %s/%s]', namespace, name)
            continue

        # TODO check postgres version

        log.debug('prepare to make dump')

        now = datetime.datetime.utcnow()
        now_str = now.strftime('%d.%m.%y-%H:%M:%S')
        dump_filename = f'{now_str}.tar.gz'

        try:
            log.debug('make dump ....')
            client.make_dump(name, namespace, filename=dump_filename)
        except Exception:
            log.exception('make dump problem [pod %s/%s]', namespace, name)
            continue

        log.debug('dump %s complete', dump_filename)

        log.debug('create transfer pod')

        mount_path = '/backup'
        backup_pod_name = f'{display_name}-backup'

        client.create_pod({
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': backup_pod_name,
                'namespace': namespace
            },
            'spec': {
                'containers': [
                    {
                        'name': 'main',
                        'image': config.ftp_image,
                        'imagePullPolicy': 'Always',
                        'env': [
                            {'name': 'FTP_SERVER', 'value': config.ftp_server},
                            {'name': 'FTP_LOGIN', 'value': config.ftp_login},
                            {'name': 'FTP_PASSWORD', 'value': config.ftp_password},
                            {'name': 'FTP_WORKDIR', 'value': f'/{namespace}/{display_name}'},
                            {'name': 'MAX_BACKUP_COUNT', 'value': config.max_backup_count},
                            {'name': 'DUMP_FILENAME', 'value': f'{mount_path}/{dump_filename}'},
                            {'name': 'FTP_NET_LIMIT', 'value': config.ftp_speed_limit},
                        ],
                        'volumeMounts': [
                            {
                                'mountPath': mount_path,
                                'name': 'backup-data',
                            }
                        ]
                    },
                ],
                'restartPolicy': 'Never',
                'volumes': [
                    {
                        'name': 'backup-data',
                        'persistentVolumeClaim': {
                            'claimName': pvc_name
                        }
                     },
                ]
            },
        })

        client.wait_for_pod(backup_pod_name, namespace)
        log.debug('fetch log')
        pod_logs = client.get_pod_log(backup_pod_name, namespace)
        if 'copy dump succes' in pod_logs:
            log.info('copy dump success')
        else:
            log.error(pod_logs)

        client.delete_pod(backup_pod_name, namespace)


if __name__ == '__main__':
    main()
