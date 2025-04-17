import sys
from startup.rabbitmq_docker_service import RabbitMqDockerService
from startup.mongodb_docker_service  import MongoDbDockerService
from startup.data_ingestion_service import DataIngestionService

if __name__ == '__main__':
    # Setup RabbitMQ docker
    rabbitmq = RabbitMqDockerService()
    rabbitmq.start()

    # Setup MongoDB docker
    mongodb = MongoDbDockerService()
    mongodb.start()

    route_ids = []
    if len(sys.argv) > 1:
        route_ids = list(set(int(i) for i in sys.argv[1].split(',')))

    print(f"Starting serving for routes: {route_ids}")

    # Data Ingestion Service
    data_ingestion_service = DataIngestionService()
    data_ingestion_service.ingest(route_ids=route_ids)