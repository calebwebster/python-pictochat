from utils import CODES, COLOURS, HEADER_LENGTH, PORT, FORMAT
import threading
import getpass
import socket
import random
import bcrypt

SERVER = ""
ADDR = (SERVER, PORT)


class ClientData:
    
    def __init__(self, connection, address, number):
        self.connection = connection
        self.address = address
        self.colour = "#000000"
        self.username = f"Guest {number}"
        self.is_logged_in = False


class Server:
    
    def __init__(self):
        self.password_hash = bcrypt.hashpw(getpass.getpass("Server Password: ").encode(FORMAT), bcrypt.gensalt())
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(ADDR)
        self.own_client = ClientData(None, None, 0)
        self.own_client.username = "Server"
        self.own_client.is_logged_in = True
        self.clients = []
    
    def receive_message(self, client):
        """
        While a client is connected, Receive a message from client's socket.
        
        :param ClientData client: object containing client's data
        
        If message == DISCONNECT_MESSAGE, close the connection and remove from
        self.clients. If not, publish the message.
        """
        conn = client.connection
        addr = client.address
        is_connected = True
        while is_connected:
            try:
                code = self.recv(conn).decode(FORMAT)
            except ConnectionResetError:
                is_connected = False
                continue
            
            if code == CODES["disconnect"]:
                is_connected = False
            elif code == CODES["password"]:
                password = self.recv(conn)
                if bcrypt.checkpw(password, self.password_hash):
                    # Assign the client a random colour.
                    taken_colours = [c.colour for c in self.clients]
                    available_colours = [colour for colour in COLOURS if colour not in taken_colours]
                    rand_colour = random.choice(available_colours)
                    client.colour = rand_colour
                    self.send(conn, CODES["colour_success"])
                    self.send(conn, rand_colour)
                    self.send(conn, CODES["username_success"])
                    self.send(conn, client.username)
                    # Display a login message.
                    self.publish_message(f"{client.username} has entered the chat.", self.own_client, exclude=client)
                    client.is_logged_in = True
                    self.send(conn, CODES["auth_success"])
                    print(f"[AUTHSUCCESS] Client {addr} authorized")
                else:
                    self.send(conn, CODES["auth_failure"])
                    self.send(conn, CODES["send_password"])
                    print(f"[AUTHFAILURE] Client {addr} unauthorized")
            elif code == CODES["set_username"]:
                username = self.recv(conn).decode(FORMAT)
                taken_usernames = [c.username for c in self.clients if c != client]
                if username in taken_usernames:
                    self.send(conn, CODES["username_failure"])
                    self.send(conn, client.username)
                elif username != client.username:
                    self.send(conn, CODES["username_success"])
                    self.send(conn, username)
                    self.publish_message(f"{client.username} changed their name to {username}.", self.own_client, exclude=client)
                    client.username = username
                    client.username = username
            elif code == CODES["message"]:
                message = self.recv(conn).decode(FORMAT)
                # Send the message to all clients
                self.publish_message(message, client)
            elif code == CODES["drawing"]:
                img_size = self.recv(conn).decode(FORMAT)
                # data_length = int(self.recv(conn).decode(FORMAT))
                # Receive image data until required length is met.
                # img_data = b""
                # while len(img_data) < data_length:
                #     img_piece = self.recv(conn)
                #     img_data += img_piece
                img_data = self.recv(conn)
                # Send image data to all clients.
                self.publish_drawing(img_data, img_size, client)
            elif code == CODES["send_taken_colours"]:
                taken_colours = [c.colour for c in self.clients if c != client]
                self.send(conn, CODES["taken_colours"])
                
                if taken_colours:
                    self.send(conn, ",".join(taken_colours))
                else:
                    self.send(conn, "none")
            elif code == CODES["set_colour"]:
                colour = self.recv(conn).decode(FORMAT)
                taken_colours = [c.colour for c in self.clients if c != client]
                
                if colour in taken_colours:
                    # Send back colour taken code and client's current colour.
                    self.send(conn, CODES["colour_failure"])
                    self.send(conn, client.colour)
                else:
                    # Send back colour success code.
                    client.colour = colour
                    self.send(conn, CODES["colour_success"])
                    self.send(conn, colour)
        conn.close()
        self.clients.remove(client)
        print(f"[DISCONNECT] {addr} disconnected")
        print(f"[CONNECTIONS] {len(self.clients)}")
    
    def publish_message(self, message, sender, exclude=None):
        for client in self.clients:
            if client.is_logged_in and client != exclude:
                self.send(client.connection, CODES["message"])
                self.send(client.connection, sender.username + sender.colour + message)
    
    def publish_drawing(self, img_data, img_size, sender):
        for client in self.clients:
            if client.is_logged_in:
                conn = client.connection
                self.send(conn, CODES["drawing"])  # !DRAWING
                self.send(conn, sender.username + sender.colour + img_size)  # tha_phat_rabbit#00ff00400x400
                # self.send(conn, str(len(img_data)))
                # bytes_sent = 0
                # while bytes_sent < len(img_data):
                #     next_chunk = img_data[bytes_sent:bytes_sent + IMG_CHUNK_SIZE]
                #     self.send(conn, next_chunk)
                #     bytes_sent += IMG_CHUNK_SIZE
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
            print(F"[SENT] Header: {int(header)}, Message: {len(message)} (to {recipient.getpeername()[0]})")
        else:
            print(f"[SENT] Header: {int(header)}, Message: {message} (to {recipient.getpeername()[0]})")
    
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
            print(f"[RECEIVED] Header: {bytes_to_recv}, Message: {len(received)} (from {sender.getpeername()[0]})")
        else:
            print(f"[RECEIVED] Header: {bytes_to_recv}, Message: {received} (from {sender.getpeername()[0]})")
        return received
    
    def connect_clients(self):
        """
        Listen on socket and, while true, accept new clients and start threads.
        
        Client threads are daemon, so they will close when main program exits.
        Assign each new client the next colour from the colour wheel.
        """
        is_running = True
        self.server.listen(20)
        print("[LISTENING] Listening for new connections")
        while is_running:
            try:
                # Accept new client.
                connection, address = self.server.accept()
            except KeyboardInterrupt:
                for client in self.clients:
                    self.send(client.connection, CODES["server_shutdown"])
                print("[CLOSING] Server is shutting down")
                is_running = False
                continue
            client = ClientData(connection, address, len(self.clients) + 1)
            self.clients.append(client)
            # Start new thread running receive_message to get messages from client.
            client_thread = threading.Thread(target=self.receive_message, args=(client,))
            client_thread.daemon = True  # Thread will close on exit
            client_thread.start()
            # Send a message to the client asking for a password
            self.send(connection, CODES["send_password"])
            print(f"[CONNECTED] {address[0]} connected to server")
            print(f"[CONNECTIONS] {len(self.clients)}")
    
    def start(self):
        """Start server."""
        print("[STARTING] Server is starting up")
        self.connect_clients()
