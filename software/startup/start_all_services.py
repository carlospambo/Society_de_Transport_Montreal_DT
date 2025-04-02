
import sys
from startup.rabbitmq_docker_service import RabbitMqDockerService
from startup.mongodb_docker_service  import MongoDbDockerService
from startup.routing_service import RoutingService
from communication.protocol import EXECUTION_INTERVAL

if __name__ == '__main__':
    # RabbitMQ
    rabbitmq = RabbitMqDockerService()
    rabbitmq.start()

    # MongoDB
    mongodb = MongoDbDockerService()
    mongodb.start()

    route_ids = []
    if len(sys.argv) > 1:
        route_ids = list(set(int(i) for i in sys.argv[1].split(',')))

    print(f"Starting serving for routes: {route_ids}")

    # STM API Service
    service = RoutingService()
    service.start(execution_interval=EXECUTION_INTERVAL, route_ids=route_ids)