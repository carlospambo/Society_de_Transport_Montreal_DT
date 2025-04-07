import traceback
import json
import logging
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

from config.config import config_logger, load_config
from communication.protocol import ROUTING_KEY_STM_NOTIFICATION
from communication.rpc_server import RPCServer

config_logger("config/logging.conf")

class VehicleStopStatus(Enum):
    INCOMING_AT	= 1
    STOPPED_AT	= 2
    IN_TRANSIT_TO = 3

    def __str__(self):
        return f"{self.name}"

    @classmethod
    def parse(cls, value: int) -> "VehicleStopStatus":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid VehicleStopStatus value: {value}")


class OccupancyStatus(Enum):
    EMPTY = 1
    MANY_SEATS_AVAILABLE = 2
    FEW_SEATS_AVAILABLE = 3
    STANDING_ROOM_ONLY = 4
    CRUSHED_STANDING_ROOM_ONLY = 5
    FULL = 6
    NOT_ACCEPTING_PASSENGERS = 7

    def __str__(self):
        return f"{self.name}"

    @classmethod
    def parse(cls, value: int) -> "OccupancyStatus":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid OccupancyStatus value: {value}")


class NotificationService(RPCServer):

    def __init__(self, smtp_host:str=None, port:int=None, sender:str=None, password:str=None, clients:str=None, rabbitmq_config:dict=None):
        default_config = load_config("config/startup.conf")
        self.logger = logging.getLogger("NotificationService")

        if rabbitmq_config is None:
            self.logger.debug("RabbitMQ config value is empty, reverting to default configs.")
            rabbitmq_config = default_config['rabbitmq']

        self.smtp_host = smtp_host if smtp_host is not None else default_config['notification']['smtp_host']
        self.port = port if port is not None else default_config['notification']['port']
        self.sender = sender if sender is not None else default_config['notification']['sender']
        self.password = password if password is not None else default_config['notification']['password']
        if clients is not None:
            self.clients = clients.split(',')
        elif default_config['notification']['clients'] is not None:
            self.clients = default_config['notification']['clients'].split(',')
        else:
            self.clients = []
        self.server = None
        super().__init__(**rabbitmq_config)


    def complete_setup(self):
        # Subscribe to any message coming from the STM Telemetry Validation.
        self.subscribe(routing_key=ROUTING_KEY_STM_NOTIFICATION, on_message_callback=self.send_alert)
        self.logger.info("NotificationService setup complete.")


    def _connect_and_send(self, message:MIMEMultipart):
        try :
            self.server = smtplib.SMTP(self.smtp_host, self.port)
            self.server.starttls()
            self.server.login(self.sender, self.password)
            self.server.sendmail(self.sender, message['To'], message.as_string())

        except Exception as e:
            self.logger.error(f"Error connecting to SMTP server: {str(e)}")
        finally:
            self.server.quit()


    @staticmethod
    def _build_table_row(event:dict) -> str:
        utc_time = datetime.fromtimestamp(event['timestamp'], timezone.utc)
        local_time = utc_time.astimezone()
        local_time = local_time.strftime("%Y-%m-%d %H:%M:%S")

        return f"""
            <tr>
                <td align="center" style="padding: 5px;">{event['vehicle.trip.trip_id']}</td>
                <td align="center" style="padding: 5px;">{event['vehicle.trip.route_id']}</td>
                <td align="center" style="padding: 5px;">{local_time}</td>
                <td align="center" style="padding: 5px;">{event['vehicle.current_bus_stop']}</td>
                <td align="center" style="padding: 5px;">{VehicleStopStatus.parse(event['vehicle.current_status'])}</td>
                <td align="center" style="padding: 5px;">{OccupancyStatus.parse(event['vehicle.occupancy_status'])}</td>
            </tr>
        """

    def _build_message_body(self, events:list) -> str:
        bus_lines = []
        rows = ""
        for e in events:
            rows += self._build_table_row(e)
            bus_lines.append(int(e['vehicle.trip.route_id']))
        bus_lines = set(bus_lines)

        return f"""
            <body style="font-family: 'Poppins', Arial, sans-serif">
                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                    <tr>
                        <td align="center" style="padding: 20px;">
                            <table class="content" width="600" border="0" cellspacing="0" cellpadding="0" style="border-collapse: collapse; border: 1px solid #cccccc;">
                                <!-- Header -->
                                <tr>
                                    <td class="header" style="background-color: #345C72; padding: 40px; text-align: center; color: white; font-size: 24px;">
                                        Société de Transport de Montréal Bus Fleet Digital Twin
                                    </td>
                                </tr>
                
                                <!-- Body -->
                                <tr>
                                    <td class="body" style="padding: 20px; text-align: left; font-size: 16px; line-height: 1.6;">
                                        Good day Operations Team, <br><br>
                                        This email outlines the need for immediate corrective actions regarding telemetry data for the following bus lines:
                                        <br>
                                        <strong> {", ".join(str(x) for x in bus_lines)}</strong>.
                                        <br><br>
                                        Here is a summary of the issues that required <strong>immediate</strong> actions: <br><br>
                
                                        <table width="100%" border="1" cellspacing="1" cellpadding="1">
                                            <tr>
                                                <th>Trip-Id</th>
                                                <th>Line</th>
                                                <th>Timestamp</th>
                                                <th>Bus-Stop</th>
                                                <th>Status</th>
                                                <th>Occupancy</th>
                                            </tr>
                                            {rows}
                                        </table>
                                    </td>
                                </tr>
                
                                <tr>
                                    <td class="body" style="padding-left: 20px; text-align: left; font-size: 16px; line-height: 1.6;">
                                        Please prioritize taking actions to remediate issue(s), if need be confirm the readings of the bus driver. <br><br>
                                        Regards <br><br>
                                    </td>
                                </tr>
                
                                <!-- Footer -->
                                <tr>
                                    <td class="footer" style="background-color: #333333; padding: 40px; text-align: center; color: white; font-size: 14px;">
                                        Copyright &copy; 2025 | LOG6953FE - Digital Twin Engineering
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
                </body>
        """

    def _build_messages(self, events:list) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["Subject"] = "[Action Required] for Société de Transport de Montréal Bus Fleet Digital Twin"
        msg["From"] = self.sender
        msg.attach(MIMEText(self._build_message_body(events), "html"))
        return msg


    def send_alert(self, channel, method, properties, json_payload:str):
        self.logger.debug(f"Received JSON payload: {json_payload}")

        try:
            payload_dict = json.loads(json_payload)
            if 'data' not in payload_dict:
                self.logger.debug("Service received empty payload to be processed")
                return

            events = payload_dict['data']['events'] if 'events' in payload_dict['data'] else []
            receivers = payload_dict['data']['receivers'] if payload_dict['data']['receivers'] is not None else self.clients
            message = self._build_messages(events)

            for receiver in receivers:
                message["To"] = receiver
                message["Bcc"] = receiver
                self._connect_and_send(message)

        except Exception as e:
            traceback.print_tb(e.__traceback__)
            self.logger.error(f"Error attempting to send email: {str(e)}")


if __name__ == '__main__':
    service = NotificationService()