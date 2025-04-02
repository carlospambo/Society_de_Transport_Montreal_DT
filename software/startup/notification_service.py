import logging
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

from config.config import config_logger, load_config

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

class NotificationService():

    def __init__(self, smtp_host:str, port:int, sender:str, password:str, clients:str=None):
        self.logger = logging.getLogger("NotificationService")
        self.smtp_host = smtp_host
        self.port = port
        self.sender = sender
        self.password = password
        self.server = None
        self.clients = clients.split(',') if clients is not None else []


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

    def build_message(self, events:list) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["Subject"] = "[Action Required] for Société de Transport de Montréal Bus Fleet Digital Twin"
        msg["From"] = self.sender
        msg.attach(MIMEText(self._build_message_body(events), "html"))
        return msg


    def send_alert(self, events:list, receivers=None):

        try:
            receivers = receivers if receivers is not None else self.clients
            message = self.build_message(events)

            for receiver in receivers:
                message["To"] = receiver
                message["Bcc"] = receiver
                self._connect_and_send(message)

        except Exception as e:
            self.logger.error(f"Error attempting to send email to: {receivers}.\nException: {str(e)}")