import datetime
import logging

from pgdump.client import Client

logging.basicConfig(level=logging.INFO)


def main():
    client = Client()
    for pod in client.pods_for_dump():
        name = pod.metadata.name
        namespace = pod.metadata.namespace
        container_name = pod.spec.containers[0].name

        logging.info('processing pod %s/%s', namespace, name)

        try:
            logging.info('fetch pvc ...')
            pvc_name = pod.spec.volumes[0].persistent_volume_claim.claim_name
            logging.info('fount %s pvc', pvc_name)
        except IndexError:
            logging.error('Not found volumes[pod %s/%s]', namespace, name)
            continue
        except AttributeError:
            logging.error('Invalid volume type[pod %s/%s]', namespace, name)
            continue

        # TODO check postgres version

        logging.info('prepare to make dump')

        now = datetime.datetime.utcnow()
        today_str = now.strftime('%d.%m.%y')
        dump_filename = f'{container_name}.{today_str}.tar.gz'

        try:
            logging.info('make dump ....')
            client.make_dump(name, namespace, filename=dump_filename)
        except Exception:
            logging.exception('make dump problem [pod %s/%s]', namespace, name)
            continue

        logging.info('dump %s complete', dump_filename)


if __name__ == '__main__':
    main()
