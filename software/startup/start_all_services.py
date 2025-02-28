
import sys
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

    # HTTP RESTful API
    # start_http_api()

    route_ids = []
    if sys.argv[1]: # extract parameters values
        route_ids = int_list = [int(i) for i in sys.argv[1].split(',')]

    # STM API Service
    service = StmApiService()
    service.start(route_ids)
