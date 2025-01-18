import ipaddress
import json
import os
from dataclasses import field
from pathlib import Path
from typing import List

from pydantic import BaseModel

SHARED_SECRET = "r00tmeKey"
CONFIG_FILE = Path("config.json")
SCREENSHOT_PATH = None


class Server(BaseModel):
    ip: str
    port: int = 65444
    mac_address: str = ""
    country: str = ""
    city: str = ""
    zipcode: str = ""
    isp: str = ""
    last_connected: str = ""
    status: str = "Offline"

    def to_table_row(self):
        """Converts the Server object into a row for the server table."""
        return [
            self.ip,
            self.port,
            self.mac_address,
            self.country,
            self.city,
            self.zipcode,
            self.isp,
            self.last_connected,
            self.status,
        ]


class SearchServer(BaseModel):
    start_ip: str = "192.168.1.1"
    end_ip: str = "192.168.1.255"


class Config(BaseModel):
    search_server: SearchServer = SearchServer()
    server_default_port: int = 65444
    last_servers: List[Server] = field(default_factory=list)
    selected_server: Server = Server(ip="")

    def server_is_selected(self) -> bool:
        """
        Checks if a valid server is selected.

        Returns:
            bool: True if the selected server has a valid non-loopback IP address, False otherwise.
        """
        try:
            ip = ipaddress.ip_address(self.selected_server.ip.strip())
            return not ip.is_loopback
        except ValueError:
            return False

    def update_server(
        self, ip: str = None, server: Server = None, **updates
    ) -> bool:
        """
        Updates a server in the last_servers list by IP or the server object.

        Args:
            ip (str): The IP address of the server to update.
            server (Server): The server object to search for.
            **updates: Additional attributes to update on the server.

        Returns:
            bool: True if the server was updated, False otherwise.
        """
        for index, existing_server in enumerate(self.last_servers):
            if (ip and existing_server.ip == ip) or (
                server and existing_server == server
            ):
                # Update attributes
                for key, value in updates.items():
                    if hasattr(existing_server, key):
                        setattr(existing_server, key, value)

                # Optionally, replace the object entirely
                self.last_servers[index] = existing_server
                return True
        return False


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return Config(**json.load(f))
        except ValueError:
            return save_config()
    else:
        return save_config()


def save_config(_config: Config = Config()) -> Config:
    with open(CONFIG_FILE, "w") as f:
        f.write(json.dumps(_config.model_dump(), indent=4))
        return _config


config: Config = load_config()
