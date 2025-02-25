# LOG6953FE-STM-DT
LOG5953FE Project for a digital twin (DT) for the Société de Transport de Montréal (STM) bus routes monitoring

## Pre-Requisites

1. [Git](https://git-scm.com/)
2. [Python](https://www.python.org/)
3. [Jupyter](https://jupyter.org/)
4. [Docker](https://www.docker.com/)
5. [RabbitMQ](https://www.rabbitmq.com/)
6. [MongoDB](https://www.mongodb.com/)

## Run Digital Twin

- Navigate to the `root` folder of the project and run the command to install all Python dependencies:
```
pip install -r requirements.txt
```

- Then, navigate to the `software` folder and run the command to start all services:
```
python -m startup.start_all_services
```

## Authors

- [Vanny Katabarwa](mailto:vanny-nicole.kayirangwa-katabarwa@polymtl.ca?subject[Github]%LOG6953FE-STM-Digital%Twin)
- [Kerian Fiter](mailto:kerian.fiter@polymtl.ca?subject[Github]%LOG6953FE-STM-Digital%Twin)
- [Carlos Pambo](mailto:carlos.pambo@polymtl.ca?subject[Github]%LOG6953FE-STM-Digital%Twin)