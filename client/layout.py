from config import *

import PySimpleGUI as sg

sg.theme("Default1")
combo_times = [
    f"{h:02}:{m:02} AM"
    for h in range(1, 13)
    for m in (i for i in range(0, 60, 5))
] + [
    f"{h:02}:{m:02} PM"
    for h in range(1, 13)
    for m in (i for i in range(0, 60, 5))
]

process_tabs = [
    sg.Tab(
        "Manage",
        [
            [
                sg.TabGroup(
                    [
                        [
                            sg.Tab(
                                "Processes",
                                [
                                    [
                                        sg.Col(
                                            expand_x=True,
                                            layout=[
                                                [
                                                    sg.Text("Search: "),
                                                    sg.Input(
                                                        key="process_search",
                                                        expand_x=True,
                                                        expand_y=True,
                                                    ),
                                                    sg.Button(
                                                        key="Search Process",
                                                        image_filename="static/search.png",
                                                    ),
                                                ]
                                            ],
                                        ),
                                        sg.Col(
                                            expand_x=True,
                                            element_justification="right",
                                            layout=[
                                                [
                                                    sg.Button(
                                                        key="Refresh Processes",
                                                        image_filename="static/refresh.png",
                                                    ),
                                                    sg.Button(
                                                        key="Kill Selected Process",
                                                        image_filename="static/remove.png",
                                                    ),
                                                ]
                                            ],
                                        ),
                                    ],
                                    [
                                        sg.Table(
                                            values=[["", "", ""]],
                                            headings=["PID", "Name", "User"],
                                            key="process_table",
                                            enable_events=True,
                                            expand_x=True,
                                            expand_y=True,
                                        )
                                    ],
                                ],
                            ),
                            sg.Tab(
                                "Services",
                                [
                                    [
                                        sg.Col(
                                            expand_x=True,
                                            layout=[
                                                [
                                                    sg.Text("Search: "),
                                                    sg.Input(
                                                        key="service_search",
                                                        expand_x=True,
                                                        expand_y=True,
                                                    ),
                                                    sg.Button(
                                                        key="Search Service",
                                                        image_filename="static/search.png",
                                                    ),
                                                ]
                                            ],
                                        ),
                                        sg.Col(
                                            expand_x=True,
                                            element_justification="right",
                                            layout=[
                                                [
                                                    sg.Button(
                                                        key="Refresh Services",
                                                        image_filename="static/refresh.png",
                                                    ),
                                                    sg.Button(
                                                        key="Stop Selected Service",
                                                        image_filename="static/remove.png",
                                                    ),
                                                ]
                                            ],
                                        ),
                                    ],
                                    [
                                        sg.Table(
                                            values=[["", "", ""]],
                                            headings=[
                                                "Name",
                                                "Status",
                                                "Display Name",
                                            ],
                                            key="service_table",
                                            enable_events=True,
                                            expand_x=True,
                                            expand_y=True,
                                            auto_size_columns=True,
                                        )
                                    ],
                                ],
                            ),
                            sg.Tab(
                                "Screenshots",
                                [
                                    [
                                        sg.Col(
                                            [
                                                [
                                                    sg.Combo(
                                                        [],
                                                        key="window_list",
                                                        readonly=True,
                                                        expand_x=True,
                                                        expand_y=True,
                                                        size=(80, 1),
                                                    ),
                                                    sg.Button(
                                                        key="Refresh Windows",
                                                        image_filename="static/refresh.png",
                                                    ),
                                                    sg.Button(
                                                        key="Take Screenshot",
                                                        image_filename="static/screenshot.png",
                                                    ),
                                                    sg.Button(
                                                        key="Save Screenshot",
                                                        image_filename="static/save.png",
                                                    ),
                                                ],
                                                [
                                                    sg.Image(
                                                        key="screenshot_preview",
                                                        expand_y=True,
                                                    )
                                                ],
                                            ]
                                        )
                                    ]
                                ],
                            ),
                            sg.Tab(
                                "Keylogger",
                                [
                                    [
                                        sg.Col(
                                            [
                                                [
                                                    sg.Button(
                                                        key="Start Keylogger",
                                                        image_filename="static/play.png",
                                                    ),
                                                    sg.Button(
                                                        key="Stop Keylogger",
                                                        image_filename="static/stop.png",
                                                        disabled=True,
                                                    ),
                                                    sg.Button(
                                                        key="refresh_keylogger_logs",
                                                        image_filename="static/refresh.png",
                                                    ),
                                                ]
                                            ],
                                            justification="right",
                                            element_justification="right",
                                        )
                                    ],
                                    [
                                        sg.Multiline(
                                            key="key_logs",
                                            size=(40, 10),
                                            disabled=True,
                                            expand_y=True,
                                            expand_x=True,
                                        )
                                    ],
                                ],
                            ),
                            sg.Tab(
                                "Internet Scheduler",
                                [
                                    [
                                        sg.Frame(
                                            "Schedule Internet Restriction",
                                            layout=[
                                                [
                                                    sg.Radio(
                                                        "Recurring Days",
                                                        "schedule_type",
                                                        default=True,
                                                        size=(20, 1),
                                                        key="recurring_days",
                                                        enable_events=True,
                                                    ),
                                                    sg.Combo(
                                                        [
                                                            "All",
                                                            "Monday",
                                                            "Tuesday",
                                                            "Wednesday",
                                                            "Thursday",
                                                            "Friday",
                                                            "Saturday",
                                                            "Sunday",
                                                        ],
                                                        key="day_picker",
                                                        default_value="All",
                                                        size=(10, 1),
                                                        readonly=True,
                                                    ),
                                                ],
                                                [
                                                    sg.Radio(
                                                        "Specific Date",
                                                        "schedule_type",
                                                        size=(20, 1),
                                                        key="specific_date",
                                                        enable_events=True,
                                                    ),
                                                    sg.Input(
                                                        key="specific_date_picker",
                                                        size=(12, 1),
                                                        disabled=True,
                                                    ),
                                                    sg.CalendarButton(
                                                        "Select Date",
                                                        target="specific_date_picker",
                                                        format="%Y-%m-%d",
                                                        disabled=True,
                                                    ),
                                                ],
                                                [
                                                    sg.Text("Start Time"),
                                                    sg.Combo(
                                                        combo_times,
                                                        key="start_time_picker",
                                                        size=(10, 1),
                                                        readonly=True,
                                                    ),
                                                    sg.Text("End Time"),
                                                    sg.Combo(
                                                        combo_times,
                                                        key="end_time_picker",
                                                        size=(10, 1),
                                                        readonly=True,
                                                    ),
                                                    sg.Button(
                                                        key="Add Schedule",
                                                        image_filename="static/save.png",
                                                    ),
                                                    sg.Button(
                                                        key="Remove Selected Schedule",
                                                        image_filename="static/remove.png",
                                                    ),
                                                    sg.Button(
                                                        key="Refresh Schedules",
                                                        image_filename="static/refresh.png",
                                                    ),
                                                ],
                                            ],
                                            expand_x=True,
                                        )
                                    ],
                                    [
                                        sg.Table(
                                            values=[["", "", "", ""]],
                                            headings=[
                                                "Type",
                                                "Day/Date",
                                                "Start",
                                                "End",
                                            ],
                                            key="schedule_table",
                                            expand_x=True,
                                            expand_y=True,
                                            auto_size_columns=True,
                                        )
                                    ],
                                ],
                            ),
                            sg.Tab(
                                "Console",
                                [
                                    [
                                        sg.Multiline(
                                            expand_y=True,
                                            expand_x=True,
                                            autoscroll=True,
                                            key="console_output",
                                            disabled=True,
                                        )
                                    ],
                                    [
                                        sg.Input(
                                            expand_x=True,
                                            key="console_input",
                                            focus=True,
                                            enable_events=True,
                                        )
                                    ],
                                ],
                            ),
                            sg.Tab(
                                "File Browser",
                                [
                                    [
                                        sg.Col(
                                            [
                                                [
                                                    sg.Text(
                                                        "Current Directory:"
                                                    ),
                                                    sg.InputText(
                                                        "/",
                                                        key="current_dir",
                                                        expand_x=True,
                                                    ),
                                                    sg.Button(
                                                        key="back_directory",
                                                        image_filename="static/back.png",
                                                    ),
                                                    sg.Button(
                                                        key="List Directory",
                                                        image_filename="static/next.png",
                                                    ),
                                                    sg.Button(
                                                        key="Refresh Directory",
                                                        image_filename="static/refresh.png",
                                                    ),
                                                ],
                                                [
                                                    sg.Listbox(
                                                        [],
                                                        size=(80, 20),
                                                        key="file_list",
                                                        enable_events=True,
                                                        expand_y=True,
                                                        expand_x=True,
                                                    )
                                                ],
                                                [
                                                    sg.Text("Selected File: "),
                                                    sg.Input(
                                                        "",
                                                        key="download_status",
                                                        readonly=True,
                                                    ),
                                                    sg.Button(
                                                        key="Download Selected File",
                                                        image_filename="static/save.png",
                                                        disabled=True,
                                                    ),
                                                ],
                                            ],
                                            expand_x=True,
                                        )
                                    ]
                                ],
                            ),
                            sg.Tab(
                                "Logs",
                                [
                                    [
                                        sg.Col(
                                            [
                                                [
                                                    sg.Combo(
                                                        [
                                                            "Info",
                                                            "Debug",
                                                            "Warning",
                                                        ],
                                                        default_value="Info",
                                                        key="log_level",
                                                        readonly=True,
                                                        expand_x=True,
                                                        expand_y=True,
                                                        size=(80, 1),
                                                    ),
                                                    sg.Button(
                                                        key="Refresh Logs",
                                                        image_filename="static/refresh.png",
                                                    ),
                                                    sg.Button(
                                                        key="Set Log Level",
                                                        image_filename="static/save.png",
                                                    ),
                                                    sg.Button(
                                                        key="Clear Logs",
                                                        image_filename="static/remove.png",
                                                    ),
                                                ]
                                            ]
                                        )
                                    ],
                                    [
                                        sg.Multiline(
                                            key="log_viewer",
                                            disabled=True,
                                            expand_y=True,
                                            expand_x=True,
                                        )
                                    ],
                                ],
                            ),
                        ]
                    ],
                    expand_x=True,
                    expand_y=True,
                )
            ]
        ],
    )
]

main_layout = [
    sg.Tab(
        "Servers",
        [
            [
                sg.Text("Search for Servers:"),
                sg.InputText(
                    config.search_server.start_ip, key="start_ip", size=(15, 1)
                ),
                sg.Text("to"),
                sg.InputText(
                    config.search_server.end_ip, key="end_ip", size=(15, 1)
                ),
                sg.Button(
                    key="Scan Network", image_filename="static/search.png"
                ),
                sg.Button(
                    key="Stop Scanning",
                    image_filename="static/stop.png",
                    disabled=True,
                ),
                sg.Button(
                    key="Reset Search History",
                    image_filename="static/clear.png",
                    disabled=False,
                ),
            ],
            [
                sg.Table(
                    values=(
                        [
                            server.to_table_row()
                            for server in config.last_servers
                        ]
                        if config.last_servers
                        else [["" for _ in range(9)]]
                    ),
                    headings=[
                        "Ip Address",
                        "Server Port",
                        "Mac Address",
                        "Country",
                        "City",
                        "Zip",
                        "Isp",
                        "Last Connected",
                        "Status",
                    ],
                    key="server_table",
                    bind_return_key=True,
                    expand_x=True,
                    expand_y=True,
                )
            ],
        ],
    )
]


layout = [
    [sg.StatusBar("Disconnected", key="status_bar", size=(20, 1))],
    [
        sg.TabGroup([main_layout, process_tabs], expand_x=True, expand_y=True),
    ],
]
window = sg.Window(
    title="Zed Guardian Client v0.1",
    icon="static/guardian.ico",
    size=(1024, 800),
    resizable=True,
    layout=layout,
    return_keyboard_events=True,
)
