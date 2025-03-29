import logging
from config.resources import resource_file_path
from startup.docker_service import DockerService


class MongoDbDockerService(DockerService):

    def __init__(self, container_name: str = "mongodb", log_file_name: str=None, directory_path=None):
        super().__init__(container_name, logging.getLogger("MongoService"))
        self.log_file_name = "./logs/mongodb.log" if not log_file_name else log_file_name
        self.docker_compose_directory_path = resource_file_path("config/installation/mongodb") if not directory_path else directory_path


    def start(self):
        if self.is_container_running():
            self.logger.info("Container is running, skipping container kill step ...")
        else:
            self.start_container(self.log_file_name, self.docker_compose_directory_path)


    def stop(self):
        self.kill_container()