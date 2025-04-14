from logging import Logger

import docker
from docker.errors import NotFound, APIError
import os
import subprocess
import time

DEFAULT_DOCKER_COMPOSE_COMMAND = "docker compose up --detach --build"

class DockerService:

    def __init__(self, container_name:str, docker_compose_directory_path:str, log_file_name:str, logger: Logger, test_connection_function=None):
        self.container_name = container_name
        self.docker_compose_directory_path = docker_compose_directory_path
        self.log_file_name = log_file_name
        self.logger = logger
        self.test_connection_function = test_connection_function


    def is_container_running(self):
        running_status = False
        client = docker.from_env()
        try:
            container = client.containers.get(self.container_name)
            self.logger.info(f"Container status: {container.status}")

            if container.status == "running":
                running_status = True

        except (NotFound, APIError) as x:
            self.logger.error(f"Exception in attempt to check status container: {str(x)}")

        finally:
            client.close()

        return running_status


    def kill_container(self):
        self.logger.info("Searching for container with the name: " + self.container_name)
        client = docker.from_env()
        try:
            container = client.containers.get(self.container_name)
            self.logger.info(f"Container status: {container.status}")

            if container.status == "running":
                self.logger.info("Container is running. Issuing kill request.")
                container.kill()

                self.logger.info(client.containers.get(self.container_name).status)
            assert client.containers.get(self.container_name).status != "running"

        except (NotFound, APIError) as x:
            self.logger.error(f"Exception in attempt to kill container: {str(x)}")

        finally:
            client.close()


    def start_container(self, sleep_time:int=1, max_attempts:int=10):
        self.logger.info(f"Log will be stored in: {os.path.abspath(self.log_file_name)}")

        os.makedirs(os.path.dirname(self.log_file_name), exist_ok=True)

        with open(self.log_file_name, "wt") as f:
            self.logger.info(f"Running docker-compose command: {DEFAULT_DOCKER_COMPOSE_COMMAND}")

            proc = subprocess.run(DEFAULT_DOCKER_COMPOSE_COMMAND, cwd=self.docker_compose_directory_path, shell=True, stdout=f)
            if proc.returncode == 0:
                self.logger.info("docker-compose successful.")
            else:
                self.logger.info(f"docker-composed failed: {str(proc.returncode)}")
                return False
            service_ready = False
            attempts = max_attempts

            while service_ready is False and attempts > 0:
                if self.test_connection_function is not None:
                    r = self.test_connection_function()
                    if r is True:
                        self.logger.info("Service is ready")
                        service_ready = True
                    else:
                        attempts -= 1
                        self.logger.info("Service is not ready yet. Attempts remaining:" + str(attempts))
                        if attempts > 0:
                            time.sleep(sleep_time)
                else:
                    self.logger.info("Empty test_connection_function provided")
                    self.logger.info("Service is ready")
                    service_ready = True


    def start(self):
        if self.is_container_running():
            self.logger.info(f"Container: '{self.container_name}' is running, skipping container kill step ...")
        else:
            self.start_container()


    def stop(self):
        self.kill_container()