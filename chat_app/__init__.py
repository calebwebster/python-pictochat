# Tkinter may or may not be installed, but is not required to run server.
try:
    from chat_app.client import Client
except ModuleNotFoundError:
    print("[IMPORT FAILURE] Install additional modules to run Client.")
from chat_app.server import Server
