import logging
import docker
import os
import subprocess
import time

DEFAULT_DOCKER_COMPOSE_COMMAND = "docker compose up --detach --build"

logging.basicConfig(level=logging.INFO)


def kill_container(container_name):
    logging.info("Searching for container with the name: " + container_name)
    client = docker.from_env()

    try:
        container = client.containers.get(container_name)
        print("Container status: " + container.status)
        if container.status == "running":
            print("Container is running. Issuing kill request.")
            container.kill()
            print(client.containers.get(container_name).status)
        assert client.containers.get(container_name).status != "running"
    except (errors.NotFound, errors.APIError) as x:
        print("Exception in attempt to kill container: " + str(x))
    finally:
        client.close()


def start(log_file_path, docker_compose_directory_path, test_connection_function, sleep_time, max_attempts):
    print("Log will be stored in: " + os.path.abspath(log_file_path))

    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    with open(log_file_path, "wt") as f:
        print(f"Running docker-compose command: {DEFAULT_DOCKER_COMPOSE_COMMAND}")
        proc = subprocess.run(DEFAULT_DOCKER_COMPOSE_COMMAND, cwd=docker_compose_directory_path, shell=True, stdout=f)
        if proc.returncode == 0:
            print("docker-compose successful.")
        else:
            print("docker-composed failed:" + str(proc.returncode))
            return False
        service_ready = False
        attempts = max_attempts

        while service_ready is False and attempts > 0:
            r = test_connection_function()
            if r is True:
                print("Service is ready")
                service_ready = True
            else:
                attempts -= 1
                print("Service is not ready yet. Attempts remaining:" + str(attempts))
                if attempts > 0:
                    time.sleep(sleep_time)