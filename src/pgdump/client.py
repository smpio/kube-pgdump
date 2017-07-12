import time
import logging

import kubernetes.client
import kubernetes.client.rest

from pgdump import config

log = logging.getLogger(__name__)


class Client:

    def __init__(self):
        if config.in_cluster:
            kubernetes.config.load_incluster_config()

        else:
            kubernetes.config.load_kube_config()

        self.v1 = kubernetes.client.CoreV1Api()

    def pods_for_dump(self):
        return self.v1.list_pod_for_all_namespaces(label_selector=config.pod_label_selector).items

    def _run_command_in_pod(self, name, namespace, command):
        log.debug('Running cmd %s on pod %s/%s', ' '.join(command), namespace, name)
        return self.v1.connect_get_namespaced_pod_exec(name=name, namespace=namespace, command=command,
                                                       stderr=True, stdin=True, stdout=True, tty=False)

    def get_pod_envs(self, name, namespace):
        log.debug('Parse environment vars on pod %s/%s', namespace, name)
        result = dict()

        for row in self._run_command_in_pod(name, namespace, ['printenv']).split('\n'):
            row = row.replace('\r', '')
            if not row:
                continue
            key, value = row.split('=')
            result[key] = value

        return result

    def make_dump(self, name, namespace, filename):
        log.debug('Start making dump on pod %s/%s', namespace, name)
        envs = self.get_pod_envs(name, namespace)
        dump_command = config.dump_command.format(filename=filename, **envs).split(' ')
        result = self._run_command_in_pod(name, namespace, dump_command)
        # success dump command not return data
        if result:
            raise Exception(result)

    def wait_for_pod(self, name, namespace):
        log.debug('Waiting for pod %s/%s', namespace, name)
        while True:
            pod = self.v1.read_namespaced_pod(name, namespace)
            if pod.status.phase in ('Succeeded', 'Failed'):
                return pod
            time.sleep(3)

    def create_pod(self, body):
        name = body['metadata']['name']
        namespace = body['metadata']['namespace']

        while True:
            try:
                log.debug('Creating pod %s/%s', namespace, name)
                return self.v1.create_namespaced_pod(namespace, body)
            except kubernetes.client.rest.ApiException as e:
                if e.status == 409:
                    log.debug('Pod %s/%s already exists', namespace, name)
                    self.delete_pod(name, namespace, ignore_non_exists=True)
                    time.sleep(3)
                else:
                    raise e

    def delete_pod(self, name, namespace, ignore_non_exists=False):
        log.debug('Deleting pod %s/%s', namespace, name)
        try:
            return self.v1.delete_namespaced_pod(name, namespace, {})
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404 and ignore_non_exists:
                log.debug('Pod %s/%s does not exist', namespace, name)
            else:
                raise e

    def get_pod_log(self, name, namespace):
        return self.v1.read_namespaced_pod_log(name, namespace)
