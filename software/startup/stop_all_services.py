
from startup.rabbitmq_service import RabbitMQService
from startup.mongodb_service  import MongoDBService

if __name__ == '__main__':
    rabbitmq = RabbitMQService()
    rabbitmq.stop()

    mongodb = MongoDBService()
    mongodb.stop()