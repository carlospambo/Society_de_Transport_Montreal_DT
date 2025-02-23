from logging import Logger

import docker
import os
import subprocess
import time

DEFAULT_DOCKER_COMPOSE_COMMAND = "docker compose up --detach --build"

class DockerService:

    def __init__(self, container_name: str, logger: Logger, verbose: bool = True):
        self._container_name = container_name
        self.verbose = verbose
        self._l = logger


    def kill_container(self):
        self._l.info("Searching for container with the name: " + self._container_name)
        client = docker.from_env()
        try:
            container = client.containers.get(self._container_name)
            self._l.info(f"Container status: {container.status}")

            if container.status == "running":
                self._l.info("Container is running. Issuing kill request.")
                container.kill()

                self._l.info(client.containers.get(self._container_name).status)
            assert client.containers.get(self._container_name).status != "running"

        except (docker.errors.NotFound, docker.errors.APIError) as x:
            self._l.error(f"Exception in attempt to kill container: {str(x)}")

        finally:
            client.close()


    def start_container(self, log_file_path, docker_compose_directory_path, test_connection_function, sleep_time, max_attempts):
        self._l.info(f"Log will be stored in: {os.path.abspath(log_file_path)}")

        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        with open(log_file_path, "wt") as f:
            self._l.info(f"Running docker-compose command: {DEFAULT_DOCKER_COMPOSE_COMMAND}")

            proc = subprocess.run(DEFAULT_DOCKER_COMPOSE_COMMAND, cwd=docker_compose_directory_path, shell=True, stdout=f)
            if proc.returncode == 0:
                self._l.info("docker-compose successful.")
            else:
                self._l.info(f"docker-composed failed: {str(proc.returncode)}")
                return False
            service_ready = False
            attempts = max_attempts

            while service_ready is False and attempts > 0:
                r = test_connection_function()
                if r is True:
                    self._l.info("Service is ready")
                    service_ready = True
                else:
                    attempts -= 1
                    self._l.info("Service is not ready yet. Attempts remaining:" + str(attempts))
                    if attempts > 0:
                        time.sleep(sleep_time)