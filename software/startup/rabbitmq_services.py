import requests
from config.resources import resource_file_path
from utils.docker_service_util import kill_container, start

RABBITMQ_CONTAINER_NAME = "rabbitmq-server"

def start_rabbitmq():
    log_file_name = "logs/rabbitmq.log"
    docker_compose_directory_path = resource_file_path("config/installation/rabbitmq")

    def test_connection_function():
        try:
            r = requests.get("http://localhost:15672/api/overview", auth=('log6953fe', 'log6953fe'))
            if r.status_code == 200:
                print(f"{RABBITMQ_CONTAINER_NAME} ready:\n {r.text}")
                return True

        except requests.exceptions.ConnectionError as x:
            print(f"{RABBITMQ_CONTAINER_NAME} not ready - Exception: {x.__class__.__name__}")
        return False

    kill_container(RABBITMQ_CONTAINER_NAME)
    start(log_file_name, docker_compose_directory_path, test_connection_function, 1, 10)


def stop_rabbitmq():
    kill_container(RABBITMQ_CONTAINER_NAME)

if __name__ == '__main__':
    start_rabbitmq()