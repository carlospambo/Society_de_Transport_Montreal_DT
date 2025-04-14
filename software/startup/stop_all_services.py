
from startup.rabbitmq_docker_service import RabbitMqDockerService
from startup.mongodb_docker_service  import MongoDbDockerService

if __name__ == '__main__':
    rabbitmq = RabbitMqDockerService()
    rabbitmq.stop()

    mongodb = MongoDbDockerService()
    mongodb.stop()