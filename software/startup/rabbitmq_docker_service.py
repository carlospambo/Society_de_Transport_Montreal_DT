import logging
import requests
from config.resources import resource_file_path
from startup.docker_service import DockerService


class RabbitMqDockerService(DockerService):

    def __init__(self, container_name:str = "rabbitmq", log_file_name = None, verbose:bool = True):
        super().__init__(container_name, logging.getLogger('RabbitMQService'), verbose)
        self._log_file_name = "./logs/rabbitmq.log" if not log_file_name else log_file_name
        self._docker_compose_directory_path = resource_file_path("config/installation/rabbitmq")


    def _test_connection_function(self):
        try:
            r = requests.get("http://localhost:15672/api/overview", auth=('log6953fe', 'log6953fe'))
            if r.status_code == 200:
                print(f"{self._container_name} ready:\n {r.text}")
                return True

        except requests.exceptions.ConnectionError as x:
            print(f"{self._container_name} not ready - Exception: {x.__class__.__name__}")
        return False


    def start(self):
        self.kill_container()
        self.start_container(self._log_file_name, self._docker_compose_directory_path, self._test_connection_function, 1, 10)


    def stop(self):
        self.kill_container()


if __name__ == '__main__':
    service = RabbitMqDockerService()
    service.start()