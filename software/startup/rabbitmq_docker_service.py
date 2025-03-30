import logging
import requests
from config.resources import resource_file_path
from startup.docker_service import DockerService


class RabbitMqDockerService(DockerService):

    def __init__(self, container_name:str="rabbitmq", log_file_name:str=None, directory_path=None):
        log_file_name = "./logs/rabbitmq.log" if not log_file_name else log_file_name
        docker_compose_directory_path = resource_file_path("config/installation/rabbitmq") if not directory_path else directory_path
        super().__init__(container_name, docker_compose_directory_path, log_file_name, logging.getLogger('RabbitMQService'), self.test_connection_function)


    def test_connection_function(self):
        try:
            req = requests.get("http://localhost:15672/api/overview", auth=('log6953fe', 'log6953fe'))
            if req.status_code == 200:
                self.logger.info(f"{self.container_name} ready:\n {req.text}")
                return True

        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"{self.container_name} not ready - Exception: {e.__class__.__name__}")

        return False