import sys
import os
import time
import subprocess
import traceback
from startup.rabbitmq_docker_service import RabbitMqDockerService
from startup.mongodb_docker_service  import MongoDbDockerService
from startup.telemetry_validation_service import TelemetryValidationService


if __name__ == '__main__':
    # Setup RabbitMQ docker
    rabbitmq = RabbitMqDockerService()
    rabbitmq.start()

    # Setup MongoDB docker
    mongodb = MongoDbDockerService()
    mongodb.start()

    service = TelemetryValidationService()
    service.complete_setup()

    while True:
        try:
            service.start_serving()
        except KeyboardInterrupt:
            exit(0)

        except Exception as e:
            print(f"The following exception occurred: {e}")
            traceback.print_tb(e.__traceback__)
            exit(0)

    # # Get the parent directory. Should be the root of the repository
    # parent_dir = os.path.dirname(os.getcwd())
    #
    # # The root of the repo should contain the 'software' folder. Otherwise, something went wrong.
    # assert os.path.exists(os.path.join(parent_dir, 'software')), 'software folder not found in the repository root'
    # software_dir = os.path.join(parent_dir, 'software')
    # assert os.path.exists(software_dir), 'stm_dt/software directory not found'
    # startup_dir = os.path.join(software_dir, 'startup')
    # assert os.path.exists(startup_dir), 'stm_dt/software/startup directory not found'
    # sys.path.append(startup_dir)
    #
    # service_proc = subprocess.Popen([sys.executable, "startup/telemetry_validation_service.py"])
    # time.sleep(5)
    #
    # print(f"TelemetryValidationService --> {service_proc.pid}")
    #
    # # Check if the process is still running
    # assert service_proc.poll() is None, "TelemetryValidationService process has terminated"