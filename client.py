"""
Chat App Client
2021
This program stores and runs the Client class for my Chat App.

`Github <https://www.github.com/CalebWebsterJCU/ChatApp>`_

Examples:
    Running client.py from command line::
    
        $ cd ChatApp
        $ python client.py
    
    Running an instance of Client::
        
        $ IP = 45.79.236.224
        $ PORT = 5000
        $ from client import Client
        $ Client(IP, PORT).start()
"""

from tkinter.messagebox import showwarning
from PIL import ImageTk, Image as Img
from tkinter import ttk
from tkinter import *
from utils import *
import threading
import socket

SERVER = "45.79.236.224"
PORT = 5000
SCROLL_SPEED = 0.05


class Client:
    """
    A class to store socket information and methods for a Chat App client.
    
    Class Attributes:
        client : socket.socket
            stores client socket information, sends and receives data
        posted_images : list
            stores all images posted in chat (tkinter images must be
            globally accessible)
        draw_settings : dict
            stores the last used drawing settings (brush size and colour)
        root : Tk
            base tkinter window
        widgets : dict
            stores tkinter widgets as values with names as keys
    
    Methods:
        build_ui(self):
            Construct the main GUI for the Chat App client.
        create_scrollable_frame(self, frame_outer, height):
            Create Scrollable region inside a Frame or LabelFrame widget.
        scroll(self, event):
            Scroll through messages. SCROLL_SPEED determines speed.
        scroll_to_bottom(self):
            Scroll to bottom of message frame.
        enable_buttons(self):
            Enable buttons that were disabled before login.
        limit_username(username_text_var):
            Limit username input to 15 characters.
        set_username(self, event=None):
            Send username change request to server.
        set_colour(self):
            Send taken colours request to server.
        send_message(self, event=None):
            Get message from entry box and send it to server.
        send_drawing(self, event=None):
            Open draw dialog, capture image and send it to server.
        send(self, message):
            Send a message to the server.
        recv(self):
            Receive a message from the server.
        receive_from_server(self):
            Receive messages from server and perform function based on message code.
        display_message(self, text, sender, colour):
            Create a message widget inside scrollable frame.
        display_drawing(self, image, sender, colour):
            Create a label widget with an image inside scrollable frame.
        start(self):
            Start the client's listening thread and tkinter main loop.
    
    """
    
    def __init__(self, server_ip, port):
        """Connect client to server, initialize attributes, build tkinter UI."""
        addr = (server_ip, port)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect(addr)
        except ConnectionRefusedError:
            print("[CONNECTIONERROR] Could not connect to server")
            exit()
        self.posted_images = []
        self.draw_settings = {"brush_size": 1, "brush_colour": "black"}
        self.root = Tk()
        self.root.title("Client")
        self.root.geometry(f"+{567}+{210}")
        self.widgets = {}
        self.build_ui()
    
    def build_ui(self):
        """Construct the main GUI for the Chat App client."""
        # UPPER SECTION
        top_frame = LabelFrame(self.root, bd=0, relief=SUNKEN)
        title_label = Label(top_frame, text="Chat App", font=LARGE_FONT)
        subtitle_label = Label(top_frame, bd=0, text='by Caleb Webster', font=TINY_FONT)
        colour_btn = Button(top_frame, width=3, command=self.set_colour, padx=5, pady=5, state=DISABLED)
        u_var = StringVar()
        # Call limit_username whenever username variable changes.
        u_var.trace("w", lambda *args: self.limit_username(u_var))
        username_input = Entry(top_frame, textvariable=u_var, width=15, bd=3, font=SMALL_FONT)
        username_input.bind("<Return>", self.set_username)
        username_btn = Button(top_frame, text="Change Name", bd=3, font=SMALL_FONT, command=self.set_username, state=DISABLED)
        # MESSAGES BOX
        message_frame = LabelFrame(self.root, bd=3, relief=SUNKEN, pady=3)
        message_frame_inner, canvas, scrollbar = self.create_scrollable_frame(message_frame, 500)
        # LOWER FRAME
        compose_frame = LabelFrame(self.root, bd=0)
        text_input = Entry(compose_frame, bd=3, font=SMALL_FONT, width=67)
        draw_btn = Button(compose_frame, text="Draw", bd=3, font=SMALL_FONT, command=self.send_drawing, state=DISABLED)
        send_btn = Button(compose_frame, text="Send", bd=3, font=SMALL_FONT, command=self.send_message, state=DISABLED)
        
        text_input.bind("<Return>", self.send_message)
        
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky=W + E)
        title_label.grid(row=0, column=0, padx=10)
        subtitle_label.grid(row=0, column=1, pady=(15, 0), padx=(0, 176))
        colour_btn.grid(row=0, column=2)
        username_input.grid(row=0, column=3, ipady=4, padx=10)
        username_btn.grid(row=0, column=5)
        
        message_frame.grid(row=1, column=0, padx=10, sticky=W + E)
        
        compose_frame.grid(row=2, column=0, padx=10, pady=10, sticky=W + E)
        text_input.grid(row=0, column=0, sticky=E, ipady=4, padx=(0, 10))
        draw_btn.grid(row=0, column=1, padx=(0, 10))
        send_btn.grid(row=0, column=2)
        
        self.widgets["colour_btn"] = colour_btn
        self.widgets["username_input"] = username_input
        self.widgets["username_var"] = u_var
        self.widgets["username_btn"] = username_btn
        self.widgets["message_frame"] = message_frame
        self.widgets["message_frame_inner"] = message_frame_inner
        self.widgets["canvas"] = canvas
        self.widgets["text_input"] = text_input
        self.widgets["draw_btn"] = draw_btn
        self.widgets["send_btn"] = send_btn
    
    def create_scrollable_frame(self, frame_outer, height):
        """Create Scrollable region inside a Frame or LabelFrame widget."""
        canvas = Canvas(frame_outer, height=height, highlightthickness=0)
        frame_inner = Frame(canvas)
        scrollbar = ttk.Scrollbar(frame_outer, orient=VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        frame_inner.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        frame_inner.bind("<MouseWheel>", self.scroll)
        scrollbar.bind("<MouseWheel>", self.scroll)
        canvas.bind("<MouseWheel>", self.scroll)
        canvas.create_window((0, 0), window=frame_inner, anchor=N + W)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        return frame_inner, canvas, scrollbar
    
    def scroll(self, event):
        """Scroll through messages. SCROLL_SPEED determines speed."""
        canvas = self.widgets["canvas"]
        # Event.delta will be either 120 or -120.
        # By finding the sign of event.delta, the
        # program can scroll the opposite direction.
        sign = event.delta // abs(event.delta)
        position = canvas.yview()[0] + -sign * SCROLL_SPEED
        canvas.yview("moveto", position)
        self.widgets["message_frame_inner"].update()
    
    def scroll_to_bottom(self):
        """Scroll to bottom of message frame."""
        canvas = self.widgets["canvas"]
        canvas.yview("moveto", 1)
    
    def enable_buttons(self):
        """Enable buttons that were disabled before login."""
        self.widgets["colour_btn"].config(state=NORMAL)
        self.widgets["username_btn"].config(state=NORMAL)
        self.widgets["send_btn"].config(state=NORMAL)
        self.widgets["draw_btn"].config(state=NORMAL)
    
    @staticmethod
    def limit_username(username_text_var):
        """Limit username input to 15 characters."""
        username_text_var.set(username_text_var.get()[:15])
    
    def set_username(self, event=None):
        """Send username change request to server."""
        can_send = True
        # If send_message is called by pressing enter, find out if button is
        # disabled. If it is, don't send the message.
        if event and self.widgets["username_btn"]["state"] == DISABLED:
            can_send = False
        username = self.widgets["username_input"].get()
        if username and can_send:
            self.send(CODES["set_username"])
            self.send(username)
    
    def set_colour(self):
        """
        Send taken colours request to server.
        
        These taken colours will be used in the colour select dialog.
        The rest of the colour change process if handled in receive_from_server.
        """
        self.send(CODES["send_taken_colours"])
    
    def send_message(self, event=None):
        """Get message from entry box and send it to server."""
        can_send = True
        # If send_message is called by pressing enter, find out if button is
        # disabled. If it is, don't send the message.
        if event and self.widgets["send_btn"]["state"] == DISABLED:
            can_send = False
        message = self.widgets["text_input"].get()
        self.widgets["text_input"].delete(0, END)
        if message and can_send:
            self.send(CODES["message"])
            self.send(message)
    
    def send_drawing(self, event=None):
        """Open draw dialog, capture image and send it to server."""
        if event:
            pass
        result = get_drawing(self.root, self.draw_settings, COLOURS + ["#000000"])
        if result:
            drawing, last_settings = result
            # Save last used settings.
            self.draw_settings = last_settings
            # Convert image to raw data.
            img_data = drawing.tobytes()
            img_size = "{}x{}".format(*drawing.size)
            self.send(CODES["drawing"])
            self.send(img_size)
            self.send(img_data)
    
    def send(self, message):
        """
        Send a message to the server.
        
        :param str/bytes message: message to send
        
        To send a message, a header is first constructed that contains the
        length of the message to follow. Length of the header is determined by
        HEADER_LENGTH.
        """
        # If message is not encoded, encode it.
        if not isinstance(message, bytes):
            message = bytes(message, FORMAT)
        # Create a header containing num of bytes in
        # message and pad header to a set length.
        header = bytes(f"{len(message):<{HEADER_LENGTH}}", FORMAT)
        self.client.send(header)
        self.client.send(message)
        # If message is longer than 1000 bytes, print the length
        # rather than the entire message.
        if len(message) > 1000:
            print(F"[SENT] Header: {int(header)}, Message: {len(message)}")
        else:
            print(f"[SENT] Header: {int(header)}, Message: {message}")
    
    def recv(self):
        """
        Receive a message from the server.
        
        :return: message that was received.
        :rtype: bytes
        
        To avoid data loss, while loops are used to ensure all data is received.
        """
        # Receive header
        header = b""
        while len(header) < HEADER_LENGTH:
            header += self.client.recv(HEADER_LENGTH - len(header))
        bytes_to_recv = int(header)
        # Receive message
        received = b""
        while len(received) < bytes_to_recv:
            received += self.client.recv(bytes_to_recv - len(received))
        if len(received) > 1000:
            print(f"[RECEIVED] Header: {bytes_to_recv}, Message: {len(received)}")
        else:
            print(f"[RECEIVED] Header: {bytes_to_recv}, Message: {received}")
        return received
    
    def receive_from_server(self):
        """
        Receive messages from server and perform function based on message code.
        
        This function runs on a thread separate from the rest of the program and
        is the only function that can receive data from the server, because it's
        always running in the background and interferes with any other functions.
        """
        while True:
            code = self.recv().decode(FORMAT)
            # PASSWORD
            if code == CODES["send_password"]:
                # Get password from password dialog.
                password = get_password(self.root)
                if password is None:
                    self.root.quit()
                else:
                    self.send(CODES["password"])
                    self.send(password)
            # AUTHENTICATION SUCCESS
            elif code == CODES["auth_success"]:
                self.enable_buttons()
            # USERNAME SUCCESS
            elif code == CODES["username_success"]:
                new_username = self.recv().decode(FORMAT)
                self.widgets["username_var"].set(new_username)
            # USERNAME FAILURE
            elif code == CODES["username_failure"]:
                old_username = self.recv().decode(FORMAT)
                self.widgets["username_var"].set(old_username)
                showwarning("Username Taken", "Sorry, that username has already been taken.")
            # MESSAGE
            elif code == CODES["message"]:
                # Break message into parts. Message should be of the format:
                # [sender username]#[sender colour][message text]
                message = self.recv().decode(FORMAT)
                colour_start = message.find("#")
                sender = message[:colour_start]
                colour = message[colour_start:colour_start + 7]
                text = message[colour_start + 7:].strip("\n")
                self.display_message(text, sender, colour)
            # DRAWING
            elif code == CODES["drawing"]:
                extra_data = self.recv().decode(FORMAT)
                # Extract information from extra data. Extra data should be of the format:
                # [sender username]#[sender colour][width]x[height]
                colour_start = extra_data.find("#")
                sender = extra_data[:colour_start]
                colour = extra_data[colour_start:colour_start + 7]  # Colour is always 7 chars long, e.g. #000000
                img_size = extra_data[colour_start + 7:].split("x")
                width, height = int(img_size[0]), int(img_size[1])
                # Receive raw image data and construct an ImageTk object from it.
                img_data = self.recv()
                image_object = ImageTk.PhotoImage(Img.frombytes("RGB", (width, height), img_data))
                self.posted_images.append(image_object)
                self.display_drawing(image_object, sender, colour)
            # TAKEN COLOURS
            elif code == CODES["taken_colours"]:
                taken_string = self.recv().decode(FORMAT)
                taken_colours = taken_string.split(",")
                # Splitting an empty string returns [""] instead of [].
                if taken_colours[0] == "" and len(taken_colours) == 1:
                    taken_colours.pop(0)
                # Get new colour from colours dialog.
                new_colour = get_colour(self.root, COLOURS, taken_colours)
                if new_colour:
                    # Send change colour request to server.
                    self.send(CODES["set_colour"])
                    self.send(new_colour)
            # COLOUR FAILURE
            elif code == CODES["colour_success"]:
                # Receive client's new colour from server.
                new_colour = self.recv()
                # Colour management is handled on the server side,
                # only colour_btn background needs to be changed.
                self.widgets["colour_btn"].config(bg=new_colour)
            # COLOUR SUCCESS
            elif code == CODES["colour_failure"]:
                # Receive client's old colour from server.
                old_colour = self.recv()
                self.widgets["colour_btn"].config(bg=old_colour)
                # Show warning so user knows colour was taken. Since the
                # colour dialog disables taken colours, This only occurs
                # when a colour is taken while The user is choosing a colour.
                showwarning("Colour Taken", "Sorry, someone took that colour\nwhile you were choosing.")
            # SERVER SHUTDOWN
            elif code == CODES["server_shutdown"]:
                self.root.quit()
    
    def display_message(self, text, sender, colour):
        """
        Create a message widget inside scrollable frame.
        
        :param str text: message text
        :param str sender: sender's username
        :param str colour: sender's colour
        
        If scrollbar is lower than a certain threshold, scroll to bottom.
        """
        inner_frame = self.widgets["message_frame_inner"]
        # Call find_num_lines to calculate height of text widget with wrapping.
        num_lines = find_num_lines(sender + text, 76, True)
        msg_widget = Text(inner_frame, width=76, height=num_lines, wrap=WORD, bd=0, bg="#ffffff", font=SMALL_FONT, padx=8, pady=6, highlightbackground=colour, highlightcolor=colour, highlightthickness=2)
        msg_widget.insert(1.0, text)
        if sender != "Server":
            # If message was sent from a client, insert sender's name with a
            # different font and colour.
            msg_widget.insert(1.0, f"{sender}: ")
            msg_widget.tag_add(sender, "1.0", f"1.{len(sender) + 1}")
            msg_widget.tag_config(sender, foreground=colour, font=MEDIUM_FONT)
        # Disable text widget so that no more text can be entered.
        msg_widget.config(state=DISABLED)
        msg_widget.bind("<MouseWheel>", self.scroll)
        msg_widget.pack(padx=6, pady=3)
        # If the scrollbar is >= 90% of they way down the screen,
        # scroll to the bottom.
        canvas = self.widgets["canvas"]
        if canvas.yview()[1] >= 0.9:
            wait = 10  # Wait 10ms for widget to be loaded before scrolling
            canvas.after(wait, self.scroll_to_bottom)
    
    def display_drawing(self, image, sender, colour):
        """
        Create a label widget with an image inside scrollable frame.
        
        :param PhotoImage image: image to display
        :param str sender: sender's username
        :param str colour: sender's colour
        """
        inner_frame = self.widgets["message_frame_inner"]
        drawing_frame = Frame(inner_frame, bd=0, highlightbackground=colour, highlightthickness=2, highlightcolor=colour)
        sender_label = Label(drawing_frame, text=sender, fg=colour, font=MEDIUM_FONT, anchor=W, padx=5, bg="white")
        drawing_widget = Label(drawing_frame, image=image, bd=0)
        
        sender_label.bind("<MouseWheel>", self.scroll)
        drawing_frame.bind("<MouseWheel>", self.scroll)
        drawing_widget.bind("<MouseWheel>", self.scroll)
        
        drawing_frame.pack(padx=6, pady=3)
        sender_label.pack(fill=X, expand=True)
        drawing_widget.pack()
        
        canvas = self.widgets["canvas"]
        if canvas.yview()[1] >= 0.9:
            wait = 10
            canvas.after(wait, self.scroll_to_bottom)
    
    def start(self):
        """Start the client's listening thread and tkinter main loop."""
        print("[STARTING] Client is starting up")
        receive_thread = threading.Thread(target=self.receive_from_server)
        receive_thread.daemon = True  # Closes on program exit
        receive_thread.start()

        self.root.mainloop()
        try:
            self.send("!DISCONNECT")
        except ConnectionResetError:
            print("[SERVER SHUTDOWN] Server has closed")


if __name__ == '__main__':
    Client(SERVER, PORT).start()
