
import sys
from startup.rabbitmq_docker_service import RabbitMqDockerService
from startup.mongodb_docker_service  import MongoDbDockerService
from startup.http_rest_api import start_http_api
from startup.stm_api_service import StmApiService


if __name__ == '__main__':
    # RabbitMQ
    rabbitmq = RabbitMqDockerService()
    rabbitmq.start()

    # MongoDB
    mongodb = MongoDbDockerService()
    mongodb.start()

    # HTTP RESTful API
    # start_http_api()

    route_ids = []
    if sys.argv[1]: # extract parameters values
        route_ids = list(set(int(i) for i in sys.argv[1].split(',')))

    # STM API Service
    service = StmApiService()
    service.start(route_ids)
