import logging
from config.resources import resource_file_path
from startup.docker_service import DockerService


class MongoDBService(DockerService):

    def __init__(self, container_name: str = "mongodb", log_file_name: str=None, directory_path=None, verbose: bool = True):
        super().__init__(container_name, logging.getLogger("MongoService"), verbose)
        self._log_file_name = "./logs/mongodb.log" if not log_file_name else log_file_name
        self._docker_compose_directory_path = resource_file_path("config/installation/mongodb") if not directory_path else directory_path

    def _test_connection_function(self) -> bool:
        return True

    def start(self):
        self.kill_container()
        self.start_container(self._log_file_name, self._docker_compose_directory_path, self._test_connection_function, 1, 10)

    def stop(self):
        self.kill_container()


if __name__ == '__main__':
    mongodb = MongoDBService()
    mongodb.start()