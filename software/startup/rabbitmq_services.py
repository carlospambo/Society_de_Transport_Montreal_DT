import requests

from software.config import resource_file_path
from software.utils.docker_service_util import kill_container, start

container_name = "rabbitmq-server"

def start_rabbitmq():
    log_file_name = "logs/rabbitmq.log"
    docker_compose_directory_path = resource_file_path("config/rabbitmq")

    def test_connection_function():
        try:
            r = requests.get("http://localhost:15672/api/overview", auth=('log6953fe', 'log6953fe'))
            if r.status_code == 200:
                print(f"{container_name} ready:\n {r.text}")
                return True

        except requests.exceptions.ConnectionError as x:
            print(f"{container_name} not ready - Exception: {x.__class__.__name__}")
        return False

    kill_container(container_name)
    start(log_file_name, docker_compose_directory_path, test_connection_function, 1, 10)


def stop_rabbitmq():
    kill_container(container_name)

if __name__ == '__main__':
    start_rabbitmq()