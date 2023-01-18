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

    def test_should_create_server_with_defaults(self):
        server = Server.with_defaults()
        self.assertEqual(server.ip, "127.0.0.1")
        self.assertEqual(server.port, 55000)
        self.assertEqual(server.password, "")
        self.assertEqual([], server.users)

    def test_should_connect_client(self):
        try:
            server = Server("127.0.0.1", 55555, "")
            server_thread = threading.Thread(target=server.start_listening)
            server_thread.start()

            client = socket.create_connection((server.ip, server.port), timeout=1)

            time.sleep(1)

            self.assertEqual(1, len(server.users))
            self.assertEqual(server.users[0].address, client.getsockname())
        except Exception as e:
            raise e
        finally:
            client.close()
            server.shutdown()
            server_thread.join()

    def test_should_connect_two_clients(self):
        print()
        try:
            server = Server("127.0.0.1", 55555, "")
            server_thread = threading.Thread(target=server.start_listening)
            server_thread.start()
            
            client1 = socket.create_connection((server.ip, server.port), timeout=1)
            client2 = socket.create_connection((server.ip, server.port), timeout=1)
            
            time.sleep(1)

            self.assertEqual(2, len(server.users))
            self.assertEqual(server.users[0].address, client1.getsockname())
            self.assertEqual(server.users[1].address, client2.getsockname())
        except Exception as e:
            raise e
        finally:
            client1.close()
            client2.close()
            server.shutdown()
            server_thread.join()
            
    def test_should_authenticate_client_when_password_empty(self):
        try:
            server = Server("127.0.0.1", 55555, "")
            server_thread = threading.Thread(target=server.start_listening)
            server_thread.start()

            client = socket.create_connection((server.ip, server.port), timeout=1)

            header_buffer = client.recv(12)
            message_code, message_length = struct.unpack("8sI", header_buffer)

            self.assertEqual("AUTHSUCC", message_code.decode())
            self.assertEqual(0, message_length)
        except Exception as e:
            raise e
        finally:
            client.close()
            server.shutdown()
            server_thread.join()
            
    def test_should_ask_client_for_password(self):
        try:
            server = Server("127.0.0.1", 55555, "password")
            server_thread = threading.Thread(target=server.start_listening)
            server_thread.start()

            client = socket.create_connection((server.ip, server.port), timeout=1)

            header_buffer = client.recv(12)
            message_code, message_length = struct.unpack("8sI", header_buffer)

            self.assertEqual("SENDPASS", message_code.decode())
            self.assertEqual(0, message_length)
        except Exception as e:
            raise e
        finally:
            client.close()
            server.shutdown()
            server_thread.join()


if __name__ == "__main__":
    unittest.main()
