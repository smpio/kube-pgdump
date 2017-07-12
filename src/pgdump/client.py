import kubernetes.client
import kubernetes.client.rest

from pgdump import config


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
        return self.v1.connect_get_namespaced_pod_exec(name=name, namespace=namespace, command=command,
                                                       stderr=True, stdin=True, stdout=True, tty=False)

    def get_pod_envs(self, name, namespace):
        result = dict()

        for row in self._run_command_in_pod(name, namespace, ['printenv']).split('\n'):
            row = row.replace('\r', '')
            if not row:
                continue
            key, value = row.split('=')
            result[key] = value

        return result

    def make_dump(self, name, namespace, filename):
        envs = self.get_pod_envs(name, namespace)
        dump_command = config.dump_command.format(filename=filename, **envs).split(' ')
        result = self._run_command_in_pod(name, namespace, dump_command)
        # success dump command not return data
        if result:
            raise Exception(result)
