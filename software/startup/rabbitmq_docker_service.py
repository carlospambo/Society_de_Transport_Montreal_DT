import logging
import requests
from config.resources import resource_file_path
from startup.docker_service import DockerService


class RabbitMqDockerService(DockerService):

    def __init__(self, container_name:str = "rabbitmq", log_file_name = None):
        super().__init__(container_name, logging.getLogger('RabbitMQService'))
        self.log_file_name = "./logs/rabbitmq.log" if not log_file_name else log_file_name
        self.docker_compose_directory_path = resource_file_path("config/installation/rabbitmq")


    def test_connection_function(self):
        try:
            r = requests.get("http://localhost:15672/api/overview", auth=('log6953fe', 'log6953fe'))
            if r.status_code == 200:
                self.logger.info(f"{self.container_name} ready:\n {r.text}")
                return True

        except requests.exceptions.ConnectionError as x:
            self.logger.error(f"{self.container_name} not ready - Exception: {x.__class__.__name__}")
        return False


    def start(self):
        if self.is_container_running():
            self.logger.info("Container is running, skipping kill step ...")
        else:
            self.start_container(self.log_file_name, self.docker_compose_directory_path, self.test_connection_function, 1, 10)


    def stop(self):
        self.kill_container()