import logging
import datetime

from pgdump.client import Client

log = logging.getLogger('pgdump')


def main():
    client = Client()
    for pod in client.pods_for_dump():
        name = pod.metadata.name
        namespace = pod.metadata.namespace
        container_name = pod.spec.containers[0].name

        try:
            pvc_name = pod.spec.volumes[0].persistent_volume_claim.claim_name
        except IndexError:
            log.error('Not found volumes[pod %s/%s]', namespace, name)
            continue
        except AttributeError:
            log.error('Invalid volume type[pod %s/%s]', namespace, name)
            continue

        # TODO check postgres version

        now = datetime.datetime.utcnow()
        today_str = now.strftime('%d.%m.%y')
        dump_filename = f'{container_name}.{today_str}.tar.gz'

        try:
            client.make_dump(name, namespace, filename=dump_filename)
        except Exception:
            log.exception('make dump problem [pod %s/%s]', namespace, name)
            continue


if __name__ == '__main__':
    main()
