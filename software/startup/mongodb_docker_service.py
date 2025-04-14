import logging
from config.resources import resource_file_path
from startup.docker_service import DockerService


class MongoDbDockerService(DockerService):

    def __init__(self, container_name: str = "mongodb", log_file_name:str=None, directory_path=None):
        log_file_name = "./logs/mongodb.log" if not log_file_name else log_file_name
        docker_compose_directory_path = resource_file_path("config/installation/mongodb") if not directory_path else directory_path
        super().__init__(container_name, docker_compose_directory_path, log_file_name, logging.getLogger("MongoDBService"))

