import unittest
import socket
import psutil
import select
from new_server import NewServer
import threading
import time


class NewServerTest(unittest.TestCase):

    @staticmethod
    def is_server_listening(server):
        if [
            conn for conn in psutil.net_connections()
            if conn.laddr == (server.ip, server.port)
            and conn.status == "LISTEN"
        ]:
            return True
        return False

    @staticmethod
    def wait_for_server_to_start(server):
        while not server.socket:
            pass

    @staticmethod
    def is_client_awaiting_acceptance(server):
        readable, writeable, in_error = select.select(
            [server.socket],
            [],
            [],
            0
        )
        if readable:
            return True
        return False

    @staticmethod
    def is_client_connected(client, server):
        if [
            conn for conn in psutil.net_connections()
            if conn.raddr == (server.ip, server.port)
            and conn.laddr == client.getsockname()
        ]:
            return True
        return False

    def start_server_in_thread_and_do_callback(self, server, callback):
        server_thread = threading.Thread(target=server.start_listening)
        server_thread.start()
        self.wait_for_server_to_start(server)

        callback(server)

        server.shutdown()
        server_thread.join()


    def test_should_create_server(self):
        server = NewServer("127.0.0.1", 55555)
        self.assertEqual("127.0.0.1", server.ip)
        self.assertEqual(55555, server.port)

    def test_should_start_server(self):
        server = NewServer("127.0.0.1", 55555)
        def callback(server):
            self.assertTrue(self.is_server_listening(server))
        self.start_server_in_thread_and_do_callback(server, callback)

    def test_should_connect_client(self):
        server = NewServer("127.0.0.1", 55555)
        def callback(server):
            client = socket.create_connection((server.ip, server.port), timeout=1)
            self.assertTrue(self.is_client_connected(client, server))
            self.assertFalse(self.is_client_awaiting_acceptance(server))
            client.close()
        self.start_server_in_thread_and_do_callback(server, callback)


    
