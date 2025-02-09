import requests

from software.config import resource_file_path
from utils.docker_service_util import kill_container, start

container_name = "mongodb-server"

def start_mongodb():
    log_file_name = "logs/mongodb.log"
    docker_compose_directory_path = resource_file_path("config/mongodb")

    def test_connection_function():
        # TODO
        return False

    kill_container(container_name)
    start(log_file_name, docker_compose_directory_path, test_connection_function, 1, 10)


def stop_mongodb():
    kill_container(container_name)

if __name__ == '__main__':
    start_mongodb()