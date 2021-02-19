"""
Chat App Server
2021
This program stores and runs the Server class for my Chat App.

`Github <https://www.github.com/CalebWebsterJCU/ChatApp>`_

Examples:
    Running server.py from command line::
    
        $ cd ChatApp
        $ python server.py
    
    Running an instance of Server::
        
        $ IP = ""
        $ PORT = 5000
        $ from server import Server
        $ Server(IP, PORT).start()

If you're running server.py on a hosting service, set IP to "",
otherwise use your PCs IP address.
"""

from utils import CODES, COLOURS, HEADER_LENGTH, FORMAT
import threading
import getpass
import socket
import random
import bcrypt

SERVER = ""
PORT = 5000


class ClientData:
    """
    A class to store data for a ChatApp client.
    
    Attributes:
        connection : socket
            client's socket used to send and receive messages
        address : str
            client's public IP address
        colour : str
            client's colour as a 6-character hexidecimal code (with #)
        username : str
            client's username. Initialized as f"Guest {number}"
        is_logged_in : bool
            whether or not the client can send and receive messages
    """
    
    def __init__(self, connection, address, username, colour):
        """
        Initialize attributes and store data for ClientData object.
        
        :param connection: client's socket, provided when client connects
        :type connection: socket.socket or None, in the case of server's client
        :param tuple address: tuple of client's public IP and port number
        :param str username: client's unique username
        :param str colour: client's unique colour
        """
        self.connection = connection
        self.address = address
        self.username = username
        self.colour = colour
        self.is_logged_in = False


class Server:
    """
    A class to store socket information and methods for a Chat App Server.
    
    Attributes:
        password_hash : str
            string of server's password, hashed with bcrypt
        server : socket.socket
            server's socket, used to send and receive messages
        own_client : ClientData
            server's own virtual "client" it uses to send status messages
        clients : list
            list of currently connected clients
    
    Methods:
        receive_from_client(self, client):
            Receive codes from client's socket and perform functions based on code.
        get_taken_colours(self, client):
            Get taken colours, excluding current client's colour.
        get_taken_usernames(self, client):
            Get taken colours, excluding current client's username.
        publish_message(self, message, sender, exclude=()):
            Send message information to all clients except excluded ones.
        publish_drawing(self, img_data, img_size, sender, exclude=()):
            Send drawing to all clients except excluded ones.
        send(recipient, message):
            Send a basic message to a connected client.
        recv(sender):
            Receive a basic message from a client.
        connect_clients(self):
            Listen on socket, accepting new clients and starting threads.
        start(self):
            Start server.
    """
    
    def __init__(self, server_ip, port):
        """
        Bind server socket to IP and port, get password, initialize own client.
        
        :param server_ip: IP address of server (leave blank if on hosting site)
        :param port: Port number to bind socket to
        """
        addr = (server_ip, port)
        # Get server's password using getpass and hash it using bcrypt.
        server_password = getpass.getpass("Server Password: ")
        self.password_hash = bcrypt.hashpw(server_password.encode(FORMAT), bcrypt.gensalt())
        # Create socket and bind IP and port to it.
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(addr)
        # Initialize server's "client", used to send status messages.
        self.own_client = ClientData(None, ("", 0), "Server", "#000000")
        self.own_client.is_logged_in = True
        self.clients = []
    
    def receive_from_client(self, client):
        """
        Receive codes from client's socket and perform functions based on code.
        
        :param ClientData client: object containing client's data
        
        This function runs on its own thread, separate from the rest of the
        program. A new thread is created for each client that connects.
        If code == DISCONNECT_MESSAGE, close the connection and remove client
        from self.clients.
        """
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
                    self.publish_message(f"{client.username} has entered the chat.", self.own_client, exclude=[client])
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
                    self.publish_message(f"{client.username} changed their name to {username}.", self.own_client, exclude=[client])
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
        self.clients.remove(client)
        print(f"[DISCONNECT] {addr} disconnected")
        print(f"[CONNECTIONS] {len(self.clients)}")
    
    def get_taken_colours(self, client):
        """Get taken colours, excluding current client's colour."""
        return [c.colour for c in self.clients if c != client]
    
    def get_taken_usernames(self, client):
        """Get taken colours, excluding current client's username."""
        return [c.username for c in self.clients if c != client]
    
    def publish_message(self, message, sender, exclude=()):
        """
        Send message information to all clients except excluded ones.
        
        :param str message: message to send
        :param ClientData sender: client that send the message
        :param list exclude: clients to not publish message to
        """
        for client in self.clients:
            if client.is_logged_in and client not in exclude:
                self.send(client.connection, CODES["message"])
                self.send(client.connection, sender.username + sender.colour + message)
    
    def publish_drawing(self, img_data, img_size, sender, exclude=()):
        """
        Send drawing to all clients except excluded ones.
        
        :param bytes img_data: raw data of image from dialogs.get_drawing
        :param str img_size: image size string of format: [width]x[height]
        :param ClientData sender: client that sent the message
        :param exclude: clients to not publish drawing to
        """
        for client in self.clients:
            if client.is_logged_in and client not in exclude:
                conn = client.connection
                self.send(conn, CODES["drawing"])  # !DRAWING
                self.send(conn, sender.username + sender.colour + img_size)  # tha_phat_rabbit#00ff00400x400
                self.send(conn, img_data)
    
    @staticmethod
    def send(recipient, message):
        """
        Send a basic message to a connected client.
        
        :param recipient: client to send message to
        :param message: message to send
        """
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
        """
        Receive a basic message from a client.
        
        :param socket.socket sender: client's socket to receive message from.
        :return: message that was received
        :rtype: bytes
        """
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
        Listen on socket, accepting new clients and starting threads.
        
        Client threads are daemon, so they will close when main program
        exits or the client disconnects.
        """
        is_running = True
        self.server.listen(20)  # Allow a queue of up to 20 connections
        print("[LISTENING] Listening for new connections")
        while is_running:
            try:
                # Accept new client.
                connection, address = self.server.accept()
            except KeyboardInterrupt:
                # Send disconnect message and close thread.
                for client in self.clients:
                    self.send(client.connection, CODES["server_shutdown"])
                print("[CLOSING] Server is shutting down")
                is_running = False
                continue
            # Assign client a unique number when it connects.
            taken_nums = [client.number for client in self.clients]
            client_num = 1
            while client_num in taken_nums:
                client_num += 1
            # Assign the client a random colour.
            taken_colours = [c.colour for c in self.clients]
            available_colours = [colour for colour in COLOURS if colour not in taken_colours]
            client_colour = random.choice(available_colours)
            # Create ClientData object.
            client = ClientData(connection, address, f"Guest {client_num}", client_colour)
            self.clients.append(client)
            # Start new thread running receive_message to get messages from client.
            client_thread = threading.Thread(target=self.receive_from_client, args=(client,))
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


if __name__ == '__main__':
    Server(SERVER, PORT).start()
