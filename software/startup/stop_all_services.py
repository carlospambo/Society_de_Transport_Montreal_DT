
from startup.rabbitmq_service import RabbitMqDockerService
from startup.mongodb_service  import MongoDbDockerService


if __name__ == '__main__':
    rabbitmq = RabbitMqDockerService()
    rabbitmq.stop()

    mongodb = MongoDbDockerService()
    mongodb.stop()