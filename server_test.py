import unittest
import struct
import time
import sys
import socket
import threading
from server import Server
from server import PasswordPrompter


class TestServer(unittest.TestCase):

    def test_one_plus_one_equals_two(self):
        self.assertEqual(1 + 1, 2)

    def client_connection_is_made(self, server):
        return socket.create_connection((server.ip, server.port), timeout=1)

    def does_client_receive_auth_success_message(self, client):
        header_buffer = client.recv(12)
        message_code, message_length = struct.unpack("8sI", header_buffer)
        return message_code.decode() == "AUTHSUCC"

    def does_client_receive_password_request_message(self, client):
        header_buffer = client.recv(12)
        message_code, message_length = struct.unpack("8sI", header_buffer)
        return message_code.decode() == "SENDPASS"

    def client_provides_correct_password(self, client, server):
        client.send(struct.pack("8sI", b"PASSWORD", len(server.password.encode())))
        client.send(server.password.encode())

    def start_server_in_thread_and_do_callback(self, server, callback):
        server_thread = None
        try:
            server_thread = threading.Thread(target=server.start_listening)
            server_thread.start()

            callback(server)
        except Exception as e:
            raise Exception
        finally:
            if server:
                server.shutdown()
            if server_thread:
                server_thread.join()

    def test_should_connect_client(self):
        server = Server("127.0.0.1", 55555, "")
        def callback(server):
            client = self.client_connection_is_made(server)
            client.close()
        self.start_server_in_thread_and_do_callback(server, callback)

    def test_should_authenticate_client_when_password_empty(self):
        server = Server("127.0.0.1", 55555, "")
        def callback(server):
            client = self.client_connection_is_made(server)
            self.assertTrue(self.does_client_receive_auth_success_message(client))
        self.start_server_in_thread_and_do_callback(server, callback)

    def test_should_connect_two_clients(self):
        password = "passywordy"
        server = Server("127.0.0.1", 55555, password)
        def callback(server):
            first_client = self.client_connection_is_made(server)
            self.assertTrue(self.does_client_receive_password_request_message(first_client))
            self.client_provides_correct_password(first_client, server)
            # self.does_client_receive_auth_success_message(first_client)
            second_client = self.client_connection_is_made(server)
            self.client_provides_correct_password(second_client, server)
        self.start_server_in_thread_and_do_callback(server, callback)
            
    def test_should_ask_client_for_password(self):
        server = Server("127.0.0.1", 55555, "password")
        def callback(server):
            client = self.client_connection_is_made(server)
            self.assertTrue(self.does_client_receive_password_request_message(client))
        self.start_server_in_thread_and_do_callback(server, callback)

if __name__ == "__main__":
    unittest.main()
