from config.resources import resource_file_path
from utils.docker_service_util import kill_container, start

MONGODB_CONTAINER_NAME = "mongodb-server"

def start_mongodb():
    log_file_name = "logs/mongodb.log"
    docker_compose_directory_path = resource_file_path("config/installation/mongodb")

    def test_connection_function():
        return True

    kill_container(MONGODB_CONTAINER_NAME)
    start(log_file_name, docker_compose_directory_path, test_connection_function, 1, 10)

def stop_mongodb():
    kill_container(MONGODB_CONTAINER_NAME)


if __name__ == '__main__':
    start_mongodb()
