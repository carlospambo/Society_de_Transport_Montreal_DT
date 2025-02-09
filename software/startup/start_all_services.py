
from rabbitmq_services import start_rabbitmq
from mongodb_services import start_mongodb

if __name__ == '__main__':
    start_rabbitmq()
    start_mongodb()

