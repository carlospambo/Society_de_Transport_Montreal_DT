
from startup.rabbitmq_service import RabbitMQService
from startup.mongodb_service  import MongoDBService
# from startup.scheduler_service import SchedulerService
from startup.rest_api import start_api
from startup.route_service import start_route_service_update


if __name__ == '__main__':
    # RabbitMQ
    rabbitmq = RabbitMQService()
    rabbitmq.start()

    # MongoDB
    mongodb = MongoDBService()
    mongodb.start()

    # # API
    # start_api()

    # Routing Service
    start_route_service_update()

    # # Scheduler
    # service = SchedulerService()
    # service.start()