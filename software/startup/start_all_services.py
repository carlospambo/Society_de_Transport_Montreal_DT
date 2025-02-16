
from startup.rabbitmq_services import start_rabbitmq
from startup.mongodb_services  import start_mongodb

if __name__ == '__main__':
    start_rabbitmq()
    start_mongodb()