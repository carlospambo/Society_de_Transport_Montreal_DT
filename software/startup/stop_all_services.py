
from rabbitmq_services import stop_rabbitmq
from mongodb_services import stop_mongodb

if __name__ == '__main__':
    stop_mongodb()
    stop_rabbitmq()
