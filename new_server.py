import socket

class NewServer:

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = None

    def accept_connection(self):
        try:
            connection, address = self.socket.accept()
            print("Accepted connection from", address)
            return connection, address
        except BlockingIOError:
            return None, None
    
    def start_listening(self):
        self.is_running = True
        self.socket = socket.create_server((self.ip, self.port))
        self.socket.setblocking(False)
        while self.is_running:
            connection, address = self.accept_connection()
            if not connection:
                continue
            connection.close()
        self.socket.close()

    def shutdown(self):
        self.is_running = False