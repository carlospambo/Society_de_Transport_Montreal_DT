
from startup.rabbitmq_service import RabbitMQService
from startup.mongodb_service  import MongoDBService
from startup.http_rest_api import start_http_api
from startup.stm_api_service import StmApiService


if __name__ == '__main__':
    # RabbitMQ
    rabbitmq = RabbitMQService()
    rabbitmq.start()

    # MongoDB
    mongodb = MongoDBService()
    mongodb.start()

    # # API
    # start_api()

    # STM API Service
    service = StmApiService()
    service.start()