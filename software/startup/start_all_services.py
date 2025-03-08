
import sys
from startup.rabbitmq_docker_service import RabbitMqDockerService
from startup.mongodb_docker_service  import MongoDbDockerService
from startup.http_rest_api import start_http_api
from startup.api_service import ApiService


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
    if len(sys.argv) > 1:
        route_ids = list(set(int(i) for i in sys.argv[1].split(',')))

    # STM API Service
    service = ApiService()
    service.start(route_ids)
