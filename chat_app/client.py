from tkinter.messagebox import showwarning
from PIL import ImageTk, Image as Img
from tkinter import ttk
from tkinter import *
from utils import *
import threading
import socket
import os

SCROLL_SPEED = 0.05
SERVER = os.getenv("SERVER_ADDRESS")
ADDR = (SERVER, PORT)


class Client:
    
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect(ADDR)
        except ConnectionRefusedError:
            print("[CONNECTIONERROR] Could not connect to server")
            exit()
        self.posted_images = []
        self.draw_settings = {"brush_size": 1, "brush_colour": "black"}
        self.is_logged_in = False
        self.root = Tk()
        self.root.title("Client")
        self.root.geometry(f"+{567}+{210}")
        self.widgets = {}
        self.build_ui()
    
    def build_ui(self):
        top_frame = LabelFrame(self.root, bd=0, relief=SUNKEN)
        title_label = Label(top_frame, text="Chat App", font=LARGE_FONT)
        subtitle_label = Label(top_frame, bd=0, text='by Caleb Webster', font=TINY_FONT)
        colour_btn = Button(top_frame, width=3, command=self.set_colour, padx=5, pady=5)
        u_var = StringVar()
        u_var.trace("w", lambda *args: self.limit_username(u_var))
        username = Entry(top_frame, textvariable=u_var, width=15, bd=3, font=SMALL_FONT)
        username.bind("<Return>", self.set_username)
        login_button = Button(top_frame, text="Change Name", bd=3, font=SMALL_FONT, command=self.set_username)
        
        message_frame = LabelFrame(self.root, bd=3, relief=SUNKEN, pady=3)
        message_frame_inner, canvas, scrollbar = self.create_scrollable_frame(message_frame, 500)
        
        compose_frame = LabelFrame(self.root, bd=0)
        text_input = Entry(compose_frame, bd=3, font=SMALL_FONT, width=67)
        draw_button = Button(compose_frame, text="Draw", bd=3, font=SMALL_FONT, command=self.handle_send_drawing)
        send_button = Button(compose_frame, text="Send", bd=3, font=SMALL_FONT, command=self.handle_send_message)
        
        text_input.bind("<Return>", self.handle_send_message)
        text_input.insert(0, "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.")
        
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky=W + E)
        title_label.grid(row=0, column=0, padx=10)
        subtitle_label.grid(row=0, column=1, pady=(15, 0), padx=(0, 176))
        colour_btn.grid(row=0, column=2)
        username.grid(row=0, column=3, ipady=4, padx=10)
        login_button.grid(row=0, column=5)
        
        message_frame.grid(row=1, column=0, padx=10, sticky=W + E)
        
        compose_frame.grid(row=2, column=0, padx=10, pady=10, sticky=W + E)
        text_input.grid(row=0, column=0, sticky=E, ipady=4, padx=(0, 10))
        draw_button.grid(row=0, column=1, padx=(0, 10))
        send_button.grid(row=0, column=2)
        
        self.widgets["colour_btn"] = colour_btn
        self.widgets["username"] = username
        self.widgets["username_var"] = u_var
        self.widgets["login_button"] = login_button
        self.widgets["message_frame"] = message_frame
        self.widgets["message_frame_inner"] = message_frame_inner
        self.widgets["canvas"] = canvas
        self.widgets["scrollbar"] = scrollbar
        self.widgets["text_input"] = text_input
        self.widgets["send_button"] = send_button
    
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
        """Scroll through messages."""
        canvas = self.widgets["canvas"]
        # Event.delta will be either 120 or -120.
        # By finding the sign of event.delta, the
        # program can scroll the opposite direction.
        sign = event.delta // abs(event.delta)
        position = canvas.yview()[0] + -sign * SCROLL_SPEED
        canvas.yview("moveto", position)
        self.widgets["message_frame_inner"].update()
    
    @staticmethod
    def limit_username(username_text_var):
        username_text_var.set(username_text_var.get()[:15])
    
    def set_username(self, event=None):
        if event:
            pass
        username = self.widgets["username"].get()
        self.send(CODES["set_username"])
        self.send(username)
    
    def set_colour(self):
        self.send(CODES["send_taken_colours"])
    
    def handle_send_message(self, event=None):
        if event:
            pass
        message = self.widgets["text_input"].get()
        self.widgets["text_input"].delete(0, END)
        if message and self.is_logged_in:
            self.send(CODES["message"])
            self.send(message)
    
    def handle_send_drawing(self, event=None):
        if event:
            pass
        result = get_drawing(self.root, self.draw_settings, COLOURS + ["#000000"])
        if result:
            drawing, last_settings = result
            self.draw_settings = last_settings
            img_data = drawing.tobytes()
            self.send(CODES["drawing"])
            self.send(str(drawing.size[0]) + "x" + str(drawing.size[1]))
            self.send(img_data)
            # self.send(str(len(img_data)))
            # bytes_sent = 0
            # while bytes_sent < len(img_data):
            #     next_chunk = img_data[bytes_sent:bytes_sent + IMG_CHUNK_SIZE]
            #     self.send(next_chunk)
            #     bytes_sent += IMG_CHUNK_SIZE
    
    def send(self, message):
        # If message is not encoded, encode it.
        if not isinstance(message, bytes):
            message = bytes(message, FORMAT)
        # Create a header containing num of bytes in
        # message and pad header to a set length.
        header = bytes(f"{len(message):<{HEADER_LENGTH}}", FORMAT)
        self.client.send(header)
        self.client.send(message)
        if len(message) > 1000:
            print(F"[SENT] Header: {int(header)}, Message: {len(message)}")
        else:
            print(f"[SENT] Header: {int(header)}, Message: {message}")
    
    def recv(self):
        header = b""
        while len(header) < HEADER_LENGTH:
            header += self.client.recv(HEADER_LENGTH - len(header))
        bytes_to_recv = int(header)
        received = b""
        # Keep receiving until all bytes have been received.
        while len(received) < bytes_to_recv:
            received += self.client.recv(bytes_to_recv - len(received))
        # If message is longer than 1000 bytes, print the length
        # rather than the entire message.
        if len(received) > 1000:
            print(f"[RECEIVED] Header: {bytes_to_recv}, Message: {len(received)}")
        else:
            print(f"[RECEIVED] Header: {bytes_to_recv}, Message: {received}")
        return received
    
    def receive_from_server(self):
        while True:
            code = self.recv().decode(FORMAT)
            # PASSWORD
            if code == CODES["send_password"]:
                password = get_password(self.root)
                if password is None:
                    self.root.quit()
                else:
                    self.send(CODES["password"])
                    self.send(password)
            # AUTHENTICATION SUCCESS
            elif code == CODES["auth_success"]:
                self.is_logged_in = True
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
                message = self.recv().decode(FORMAT)
                colour_start = message.find("#")
                sender = message[:colour_start]
                colour = message[colour_start:colour_start + 7]
                text = message[colour_start + 7:].strip("\n")
                if self.is_logged_in:
                    self.display_message(text, sender, colour)
            # DRAWING
            elif code == CODES["drawing"]:
                extra_data = self.recv().decode(FORMAT)
                # data_length = int(self.recv().decode(FORMAT))
                
                colour_start = extra_data.find("#")
                sender = extra_data[:colour_start]
                colour = extra_data[colour_start:colour_start + 7]
                width, height = map(int, extra_data[colour_start + 7:].split("x"))
                
                # Receive image data until required length is met.
                # img_data = b""
                # while len(img_data) < data_length:
                #     img_piece = self.recv()
                #     img_data += img_piece
                img_data = self.recv()
                image_object = ImageTk.PhotoImage(Img.frombytes("RGB", (width, height), img_data))
                self.posted_images.append(image_object)
                self.display_drawing(image_object, sender, colour)
            # TAKEN COLOURS
            elif code == CODES["taken_colours"]:
                taken_string = self.recv()
                if taken_string == "none":
                    taken_colours = []
                else:
                    taken_colours = taken_string.split()
                colour = get_colour(self.root, COLOURS, taken_colours)
                if colour is not None:
                    self.send(CODES["set_colour"])
                    self.send(colour)
            # COLOUR FAILURE
            elif code == CODES["colour_success"]:
                new_colour = self.recv()
                self.widgets["colour_btn"].config(bg=new_colour)
            # COLOUR SUCCESS
            elif code == CODES["colour_failure"]:
                old_colour = self.recv()
                self.widgets["colour_btn"].config(bg=old_colour)
                showwarning("Colour Taken", "Sorry, someone took that colour\nwhile you were choosing.")
            # SERVER SHUTDOWN
            elif code == CODES["server_shutdown"]:
                self.root.quit()
                
    def display_message(self, text, sender, colour):
        inner_frame = self.widgets["message_frame_inner"]
        num_lines = find_num_lines(sender + text, 76, True)
        msg_widget = Text(inner_frame, width=76, height=num_lines, wrap=WORD, bd=0, bg="#ffffff", font=SMALL_FONT, padx=8, pady=6, highlightbackground=colour, highlightcolor=colour, highlightthickness=2)
        msg_widget.insert(1.0, text)
        if sender != "Server":
            msg_widget.insert(1.0, f"{sender}: ")
            msg_widget.tag_add(sender, "1.0", f"1.{len(sender) + 1}")
            msg_widget.tag_config(sender, foreground=colour, font=MEDIUM_FONT)
        msg_widget.config(state=DISABLED)
        msg_widget.bind("<MouseWheel>", self.scroll)
    
        msg_widget.pack(padx=6, pady=3)
        
        canvas = self.widgets["canvas"]

        if canvas.yview()[1] >= 0.9:
            canvas.after(10, self.scroll_down)
    
    def display_drawing(self, image, sender, colour):
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
    
    def scroll_down(self):
        canvas = self.widgets["canvas"]
        canvas.yview("moveto", 1)
    
    def start(self):
        print("[STARTING] Client is starting up")
        receive_thread = threading.Thread(target=self.receive_from_server)
        receive_thread.daemon = True  # Closes on program exit
        receive_thread.start()

        self.root.mainloop()
        try:
            self.send("!DISCONNECT")
        except ConnectionResetError:
            print("[SERVER SHUTDOWN] Server has closed")
