from .config_routes import command_ask_gpt, command_throw_error, config_group_command
from .events import on_start_config_http_client
from .fsm import OngoingFSM, SearchFSM
from .ongoing_routes import ongoing_command
from .ptk_lib import Application
from .search_routes import search_command

# main APP entrypoint
APP = Application(
    routes=[
        search_command,
        SearchFSM,
        ongoing_command,
        OngoingFSM,
        config_group_command,
        command_ask_gpt,
        command_throw_error,
    ],
    on_startup=[on_start_config_http_client],
)
