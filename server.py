from utils import CODES, COLOURS, HEADER_LENGTH, FORMAT
import threading
from types import SimpleNamespace
import selectors
import getpass
import socket
import random
import bcrypt
import argparse


class Server:

    def __init__(self, ip, port, password):
        self.ip = ip
        self.port = port
        self.password = password
        # self.own_client = User(None, ("", 0), "Server", "#000000")
        # self.own_client.is_logged_in = True
        self.users = []
        self.is_running = True

    def with_defaults():
        return Server("127.0.0.1", 55000, "")
        
    @staticmethod
    def new_client_has_connected(server_selector):
        events = server_selector.select(timeout=0)
        if events:
            return True
        return False
        
    def accept_connection(self):
        try:
            connection, address = self.server_socket.accept()
            return connection, address
        except BlockingIOError:
            return None, None
        except TimeoutError:
            return None, None
    
    def connect_new_client(self, client_selector):
        connection, address = self.accept_connection()
        if not connection:
            return
        connection.setblocking(False)
        print('accepted', connection, 'from', address)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        connection_data = SimpleNamespace(
            address=address, 
            bytes_read=b"", 
            bytes_to_write=b""
        )
        client_selector.register(connection, events, data=connection_data)
        
        if self.password:
            connection.send(b'SENDPASS\x00\x00\x00\x00')
        else:
            connection.send(b'AUTHSUCC\x00\x00\x00\x00')
        connection.close()
        client_selector.unregister(connection)
        self.users.append(SimpleNamespace(address=address))
        print(len(self.users))

    def start_listening(self):
        self.server_socket = socket.create_server((self.ip, self.port))
        self.server_socket.setblocking(False)
        client_selector = selectors.DefaultSelector()
        while self.is_running:
            self.connect_new_client(client_selector)

        self.server_socket.close()
        print("[SHUTDOWN] Server has shut down")

    def add_client(self, client):
        self.users.append(client)
        
    def shutdown(self):
        self.is_running = False
        print(f"[SHUTDOWN] Shutting down server")

    def receive_from_client(self, client):
        conn = client.connection
        addr = client.address
        is_connected = True
        while is_connected:
            # If client disconnects, close the thread.
            try:
                code = self.recv(conn).decode(FORMAT)
            except ConnectionResetError:
                is_connected = False
                continue
            # DISCONNECT
            if code == CODES["disconnect"]:
                is_connected = False
            # PASSWORD
            elif code == CODES["password"]:
                password = self.recv(conn)
                if bcrypt.checkpw(password, self.password_hash):  # Successful login
                    # Tell the client its colour and username.
                    self.send(conn, CODES["colour_success"])
                    self.send(conn, client.colour)
                    self.send(conn, CODES["username_success"])
                    self.send(conn, client.username)
                    # Display a login message to all clients except this one.
                    self.publish_message(
                        f"{client.username} has entered the chat.", self.own_client, exclude=[client])
                    # Log client in and send auth_success code so client can chat.
                    client.is_logged_in = True
                    self.send(conn, CODES["auth_success"])
                    print(f"[AUTHSUCCESS] Client {addr} authorized")
                else:  # Unsuccessful login
                    # Send auth_failure code (currently unused) and send_password code.
                    self.send(conn, CODES["auth_failure"])
                    self.send(conn, CODES["send_password"])
                    print(f"[AUTHFAILURE] Client {addr} unauthorized")
            # CHANGE USERNAME
            elif code == CODES["set_username"]:
                username = self.recv(conn).decode(FORMAT)
                taken_usernames = self.get_taken_usernames(client)
                if username in taken_usernames:
                    # Send back current username.
                    self.send(conn, CODES["username_failure"])
                    self.send(conn, client.username)
                elif username != client.username:
                    # Send back new username
                    self.send(conn, CODES["username_success"])
                    self.send(conn, username)
                    # Display status message to all clients except this one.
                    self.publish_message(
                        f"{client.username} changed their name to {username}.", self.own_client, exclude=[client])
                    client.username = username
            # MESSAGE
            elif code == CODES["message"]:
                message = self.recv(conn).decode(FORMAT)
                # If client is logged in, send the message to all clients.
                if client.is_logged_in:
                    self.publish_message(message, client)
            # DRAWING
            elif code == CODES["drawing"]:
                img_size = self.recv(conn).decode(FORMAT)
                img_data = self.recv(conn)
                # If client is logged in, send image to all clients.
                if client.is_logged_in:
                    self.publish_drawing(img_data, img_size, client)
            # SEND TAKEN COLOURS
            elif code == CODES["send_taken_colours"]:
                # Send back a comma-separated string of all taken colours.
                taken_colours = self.get_taken_colours(client)
                self.send(conn, CODES["taken_colours"])
                self.send(conn, ",".join(taken_colours))
            # CHANGE COLOUR
            elif code == CODES["set_colour"]:
                colour = self.recv(conn).decode(FORMAT)
                taken_colours = self.get_taken_colours(client)
                if colour in taken_colours:
                    # Send back colour taken code and client's current colour.
                    self.send(conn, CODES["colour_failure"])
                    self.send(conn, client.colour)
                else:
                    # Send back colour success code.
                    client.colour = colour
                    self.send(conn, CODES["colour_success"])
                    self.send(conn, colour)
        # Close connection and remove client from clients.
        conn.close()
        self.users.remove(client)
        print(f"[DISCONNECT] {addr} disconnected")
        print(f"[CONNECTIONS] {len(self.users)}")

    def get_taken_colours(self, client):
        return [c.colour for c in self.users if c != client]

    def get_taken_usernames(self, client):
        return [c.username for c in self.users if c != client]

    def publish_message(self, message, sender, exclude=()):
        for client in self.users:
            if client.is_logged_in and client not in exclude:
                self.send(client.connection, CODES["message"])
                self.send(client.connection, sender.username +
                          sender.colour + message)

    def publish_drawing(self, img_data, img_size, sender, exclude=()):
        for client in self.users:
            if client.is_logged_in and client not in exclude:
                conn = client.connection
                self.send(conn, CODES["drawing"])  # !DRAWING
                self.send(conn, sender.username + sender.colour +
                          img_size)  # tha_phat_rabbit#00ff00400x400
                self.send(conn, img_data)

    @staticmethod
    def send(recipient, message):
        # If message is not encoded, encode it.
        if not isinstance(message, bytes):
            message = bytes(message, FORMAT)
        # Create a header containing num of bytes in
        # message and pad header to a set length.
        header = bytes(f"{len(message):<{HEADER_LENGTH}}", FORMAT)
        recipient.send(header)
        recipient.send(message)
        if len(message) > 1000:
            print(
                F"[SENT] Header: {int(header)}, Message: {len(message)} (to {recipient.getpeername()[0]})")
        else:
            print(
                f"[SENT] Header: {int(header)}, Message: {message} (to {recipient.getpeername()[0]})")

    @staticmethod
    def recv(sender):
        header = b""
        while len(header) < HEADER_LENGTH:
            header += sender.recv(HEADER_LENGTH - len(header))
        bytes_to_recv = int(header)
        received = b""
        # Keep receiving until all bytes have been received.
        while len(received) < bytes_to_recv:
            received += sender.recv(bytes_to_recv - len(received))
        # If message is longer than 1000 bytes, print the length
        # rather than the entire message.
        if len(received) > 1000:
            print(
                f"[RECEIVED] Header: {bytes_to_recv}, Message: {len(received)} (from {sender.getpeername()[0]})")
        else:
            print(
                f"[RECEIVED] Header: {bytes_to_recv}, Message: {received} (from {sender.getpeername()[0]})")
        return received

    def connect_clients(self):
        is_running = True
        self.server.listen(20)  # Allow a queue of up to 20 connections
        print("[LISTENING] Listening for new connections")
        while is_running:
            try:
                # Accept new client.
                connection, address = self.server.accept()
            except KeyboardInterrupt:
                # Send disconnect message and close thread.
                for client in self.users:
                    self.send(client.connection, CODES["server_shutdown"])
                print("[CLOSING] Server is shutting down")
                is_running = False
                continue
            # Assign client a unique number when it connects.
            taken_usernames = [c.username for c in self.users]
            client_num = 1
            client_username = "Guest 1"
            while client_username in taken_usernames:
                client_num += 1
                client_username = f"Guest {client_num}"
            # Assign the client a random colour.
            taken_colours = [c.colour for c in self.users]
            available_colours = [
                colour for colour in COLOURS if colour not in taken_colours]
            client_colour = random.choice(available_colours)
            # Create ClientData object.
            client = User(connection, address,
                                client_username, client_colour)
            self.users.append(client)
            # Start new thread running receive_message to get messages from client.
            client_thread = threading.Thread(
                target=self.receive_from_client, args=(client,))
            client_thread.daemon = True  # Thread will close on exit
            client_thread.start()
            # Send a message to the client asking for a password
            self.send(connection, CODES["send_password"])
            print(f"[CONNECTED] {address[0]} connected to server")
            print(f"[CONNECTIONS] {len(self.users)}")

    # def start(self):
    #     print("[STARTING] Server is starting up")
    #     self.server = socket.create_server((self.ip, self.port))
    #     password = getpass.getpass("Server Password: ")
    #     self.password_hash = bcrypt.hashpw(
    #         password.encode(FORMAT), bcrypt.gensalt())
    #     self.connect_clients()


# def port_number_argparse_type(arg_value_string):
#     if not arg_value_string.isdigit():
#         raise argparse.ArgumentTypeError(
#             f"invalid port number: {arg_value_string}")
#     port_number = int(arg_value_string)
#     if port_number > 65535 or port_number < 1:
#         raise argparse.ArgumentTypeError(
#             f"invalid port number: {arg_value_string}")
#     return port_number


class PasswordPrompter:
    pass
