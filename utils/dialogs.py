from tkinter.simpledialog import Dialog
from utils import SMALL_FONT
from PIL import ImageGrab
from tkinter import *
import math


class PasswordDialog(Dialog):
    
    def __init__(self, parent, title="", icon=""):
        
        self.message_label = None
        self.password_entry = None
        
        Toplevel.__init__(self, parent)
        
        self.withdraw()
        
        if parent.winfo_viewable():
            self.transient(parent)
        
        if title:
            self.title(title)
        
        if icon:
            self.iconbitmap(icon)
        
        self.parent = parent
        
        self.result = None
        
        body = Frame(self, padx=15, pady=15)
        
        self.initial_focus = self.body(body)
        
        body.pack()
        
        self.buttonbox()
        
        if not self.initial_focus:
            self.initial_focus = self
        
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        
        if self.parent is not None:
            win_x = parent.winfo_rootx() + 250
            win_y = parent.winfo_rooty() + 200
            self.geometry(f"+{win_x}+{win_y}")
        
        self.deiconify()  # become visible now
        
        self.initial_focus.focus_set()
        
        # wait for window to appear on screen before calling grab_set
        # self.wait_visibility()
        self.grab_set()
        self.wait_window(self)
    
    def body(self, master):
        message_label = Label(master, text="Enter password to access chat room.")
        password_entry = Entry(master, width=27, bd=1, show="\u2022", relief=SOLID, font=("Consolas", 10))  # show="" to reset
        
        message_label.pack(pady=(0, 15))
        password_entry.pack(ipady=1, ipadx=1)
        
        self.message_label = message_label
        self.password_entry = password_entry
        
        return password_entry
    
    def buttonbox(self):
        ok_btn = Button(self, text="OK", width=7, command=self.ok, default=ACTIVE)
        exit_btn = Button(self, text="EXIT", width=7, command=self.cancel)
        
        ok_btn.pack(side=LEFT, padx=(18, 0), pady=(5, 15))
        exit_btn.pack(side=RIGHT, padx=(0, 18), pady=(5, 15))
        
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
    
    def validate(self):
        return True
    
    def apply(self):
        self.result = self.password_entry.get()
        return True


class ColourDialog(Dialog):
    
    def __init__(self, parent, colours, taken_colours, title="", icon=""):
        
        self.colours = colours
        self.taken_colours = taken_colours
        self.colour = None
        
        Toplevel.__init__(self, parent)
        
        self.withdraw()
        
        if parent.winfo_viewable():
            self.transient(parent)
        
        if title:
            self.title(title)
        
        if icon:
            self.iconbitmap(icon)
        
        self.parent = parent
        
        self.result = None
        
        body = Frame(self)
        
        self.initial_focus = self.body(body)
        
        body.pack(side=LEFT, padx=10, pady=10)
        
        self.buttonbox()
        
        if not self.initial_focus:
            self.initial_focus = self
        
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        
        if self.parent is not None:
            win_x = parent.winfo_rootx() + 215
            win_y = parent.winfo_rooty() + 100
            self.geometry(f"+{win_x}+{win_y}")
        
        self.deiconify()  # become visible now
        
        self.initial_focus.focus_set()
        
        # wait for window to appear on screen before calling grab_set
        # self.wait_visibility()
        self.grab_set()
        self.wait_window(self)
    
    def body(self, master):
        row = 0
        column = 0
        # Create buttons for each colour
        for colour in self.colours:
            colour_btn = Button(master, bg=colour, width=2, font=("Consolas", 6), padx=5, pady=5)
            colour_btn.colour = colour
            colour_btn.bind("<ButtonRelease-1>", self.select_colour)
            # Disable button if its colour is being used by another client.
            if colour in self.taken_colours:
                colour_btn.config(state=DISABLED, text="X")
            colour_btn.grid(row=row, column=column, padx=2, pady=2)
            # Wrap buttons to 10 rows.
            column += 1
            if column == 10:
                column = 0
                row += 1
        return 0
    
    def select_colour(self, event):
        button = event.widget
        x = button.winfo_rootx()
        y = button.winfo_rooty()
        # Check if mouse is on the button when released.
        if (x < event.x_root < x + button.winfo_width()) and (y < event.y_root < y + button.winfo_height()):
            if button["state"] != DISABLED:
                self.colour = button.colour
                self.ok()
    
    def buttonbox(self):
        self.bind("<Escape>", self.cancel)
    
    def validate(self):
        
        return True
    
    def apply(self):
        if self.validate():
            self.result = self.colour
        return True


class DrawDialog(Dialog):
    
    def __init__(self, parent, brush_size, brush_colour, colours, title="", icon=""):
        
        self.canvas = None
        self.body_frame = None
        self.colour_btn = None
        self.eraser_btn = None
        self.size_up_btn = None
        self.brush_size_canvas = None
        self.size_down_btn = None
        self.undo_btn = None
        self.redo_btn = None
        self.clear_btn = None
        self.send_btn = None
        self.close_btn = None
        self.drawing = None
        
        self.last_x = 0
        self.last_y = 0
        # Load stored settings for brush size and colour
        self.brush_size = brush_size
        self.brush_colour = brush_colour
        self.eraser_is_active = False
        
        self.current_actions = []  # Current set of actions being displayed on the canvas
        self.all_actions = []  # History of actions, used for redoing undone actions
        self.new_action = []  # New action that will be added to actions on button release
        
        self.colours = colours
        
        Toplevel.__init__(self, parent)
        
        self.withdraw()
        
        if parent.winfo_viewable():
            self.transient(parent)
        
        if title:
            self.title(title)
        
        if icon:
            self.iconbitmap(icon)
        
        self.parent = parent
        
        self.result = None
        
        body = Frame(self)

        self.initial_focus = self.body(body)
        
        body.pack(side=RIGHT, padx=10, pady=10)
        
        self.buttonbox()
        
        if not self.initial_focus:
            self.initial_focus = self
        
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        
        if self.parent is not None:
            win_x = parent.winfo_rootx() - 25
            win_y = parent.winfo_rooty() + 70
            self.geometry(f"+{win_x}+{win_y}")
        
        self.deiconify()  # become visible now
        
        self.initial_focus.focus_set()
        
        # wait for window to appear on screen before calling grab_set
        # self.wait_visibility()
        self.grab_set()
        self.wait_window(self)
    
    def body(self, master):
        self.canvas = Canvas(master, width=700, height=400, bg="white")
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.draw_dot)
        self.canvas.bind("<ButtonPress-1>", self.store_mouse_xy, add="+")
        self.canvas.bind("<B1-Motion>", self.draw_line)
        self.canvas.bind("<ButtonRelease-1>", self.save_action)
        self.body_frame = master
        return 0
    
    def store_mouse_xy(self, event):
        self.last_x = event.x
        self.last_y = event.y
        
    def draw_dot(self, event):
        if self.eraser_is_active:
            fill = "white"
        else:
            fill = self.brush_colour
        # Draw an oval with coordinates on either side of cursor location.
        half_size = self.brush_size / 2
        x1, y1 = event.x + half_size, event.y + half_size
        x2, y2 = event.x - half_size, event.y - half_size
        oval_id = self.canvas.create_oval(x1, y1, x2, y2, fill=fill, outline=fill)
        # Store data for actions.
        self.new_action.append({"type": "oval", "id": oval_id, "coords": [x1, y1, x2, y2], "fill": fill})
        if fill != "white":
            self.send_btn.config(state=NORMAL)
    
    def draw_line(self, event):
        if self.eraser_is_active:
            fill = "white"
        else:
            fill = self.brush_colour
        # Draw a line between last coordinates and current coordinates.
        x1, y1, x2, y2 = self.last_x, self.last_y, event.x, event.y
        line_id = self.canvas.create_line((x1, y1, x2, y2), fill=fill, width=self.brush_size, capstyle=ROUND)
        # Store data for actions.
        self.new_action.append({"type": "line", "id": line_id, "coords": [x1, y1, x2, y2], "width": self.brush_size, "fill": fill})
        if fill != "white":
            self.send_btn.config(state=NORMAL)
        # Store current coordinates for next line.
        self.store_mouse_xy(event)
    
    def save_action(self, event):
        assert event
        # Save new action to actions and clear new action.
        # Committing a new action disables redo, so all_actions
        # is set to equal current_actions.
        self.current_actions.append(self.new_action.copy())
        self.new_action.clear()
        self.all_actions = self.current_actions.copy()
        # Disable/enable buttons
        self.undo_btn.config(state=NORMAL)
        self.redo_btn.config(state=DISABLED)
    
    def undo(self):
        # Remove last action from actions and delete shapes.
        for a in self.current_actions.pop(-1):
            self.canvas.delete(a["id"])
        # Disable/enable buttons
        self.redo_btn.config(state=NORMAL)
        if len(self.current_actions) < 1:
            self.undo_btn.config(state=DISABLED)
    
    def redo(self):
        # Add the last undone action from all_actions to current_actions.
        self.current_actions.append(self.all_actions[len(self.current_actions)].copy())
        for a in self.current_actions[-1]:
            # Re-create line or oval on canvas, setting new shape id.
            if a["type"] == "line":
                action_id = self.canvas.create_line(a["coords"], fill=a["fill"], width=a["width"], capstyle=ROUND)
            else:  # a["type"] == "oval"
                action_id = self.canvas.create_oval(a["coords"], fill=a["fill"], outline=a["fill"])
            a["id"] = action_id
        # Disable/enable buttons
        self.undo_btn.config(state=NORMAL)
        if self.current_actions == self.all_actions:
            self.redo_btn.config(state=DISABLED)
    
    def change_colour(self):
        new_colour = get_colour(self, self.colours, [])
        self.brush_colour = new_colour
        self.colour_btn.config(bg=new_colour)
    
    def toggle_eraser(self):
        if not self.eraser_is_active:
            self.eraser_is_active = True
            # Disable colour button.
            self.colour_btn.config(state=DISABLED, text="X")
            self.eraser_btn.config(fg="red")
        else:
            self.eraser_is_active = False
            # Disable colour button.
            self.colour_btn.config(state=NORMAL, text="")
            self.eraser_btn.config(fg="black")
    
    def change_size(self, amount):
        self.brush_size += amount
        if self.brush_size < 1:  # Brush size can't be < 1
            self.brush_size = 1
        # Display the brush size indicator on the small canvas by creating
        # an oval the same size in the center of said canvas.
        self.brush_size_canvas.delete("all")
        w = self.brush_size_canvas.winfo_width()
        h = self.brush_size_canvas.winfo_height()
        # If indicator is being displayed on dialog load, w and h will be 1
        # instead of actual value. Access the custom future attributes instead.
        if w == 1 and h == 1:
            w, h, = self.brush_size_canvas.future_width, self.brush_size_canvas.future_height
        half_size = self.brush_size / 2
        # Create oval.
        x1, y1 = math.ceil(w / 2) + half_size, math.ceil(h / 2) + half_size
        x2, y2 = math.ceil(w / 2) - half_size, math.ceil(h / 2) - half_size
        self.brush_size_canvas.create_oval(x1, y1, x2, y2, fill="black")
        # Disable/enable buttons
        if self.brush_size == 1:
            self.size_down_btn.config(state=DISABLED)
        else:
            self.size_down_btn.config(state=NORMAL)
    
    def clear_canvas(self):
        self.canvas.delete("all")
        # Disable undo and redo buttons.
        self.undo_btn.config(state=DISABLED)
        self.redo_btn.config(state=DISABLED)
    
    def grab_image(self):
        body = self.body_frame
        # Capture an image from the top-left to the
        # bottom-right corner of the canvas.
        x1 = self.winfo_rootx() + body.winfo_x() + 2  # Extra numbers for padding
        y1 = self.winfo_rooty() + body.winfo_y() + 2
        x2 = x1 + self.canvas.winfo_width() - 4
        y2 = y1 + self.canvas.winfo_height() - 4
        img = ImageGrab.grab().crop((x1, y1, x2, y2))
        return img
    
    def buttonbox(self):
        button_frame = Frame(self)
        self.colour_btn = Button(button_frame, bg=self.brush_colour, bd=3, font=SMALL_FONT, width=7, command=self.change_colour)
        self.eraser_btn = Button(button_frame, text="Eraser", bd=3, font=SMALL_FONT, width=7, command=self.toggle_eraser)
        self.size_up_btn = Button(button_frame, text="Size +", bd=3, font=SMALL_FONT, width=7, command=lambda: self.change_size(1))
        self.brush_size_canvas = Canvas(button_frame, width=73, height=73, bg="white")
        self.brush_size_canvas.future_width = 77
        self.brush_size_canvas.future_height = 77
        self.size_down_btn = Button(button_frame, text="Size -", bd=3, font=SMALL_FONT, width=7, command=lambda: self.change_size(-1))
        self.undo_btn = Button(button_frame, text="Undo", bd=3, font=SMALL_FONT, width=7, command=self.undo, state=DISABLED)
        self.redo_btn = Button(button_frame, text="Redo", bd=3, font=SMALL_FONT, width=7, command=self.redo, state=DISABLED)
        self.clear_btn = Button(button_frame, text="Clear", bd=3, font=SMALL_FONT, width=7, command=self.clear_canvas)
        self.send_btn = Button(button_frame, text="Send", bd=3, font=SMALL_FONT, width=7, command=self.ok, default=ACTIVE, state=DISABLED)
        self.close_btn = Button(button_frame, text="Close", bd=3, font=SMALL_FONT, width=7, command=self.cancel)

        button_frame.pack()
        self.colour_btn.pack()
        self.eraser_btn.pack()
        self.size_up_btn.pack()
        self.brush_size_canvas.pack()
        self.size_down_btn.pack()
        self.undo_btn.pack()
        self.redo_btn.pack()
        self.clear_btn.pack()
        self.send_btn.pack()
        self.close_btn.pack()
        
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        
        self.change_size(0)
    
    def validate(self):
        
        return True
    
    def apply(self):
        if self.validate():
            # Export the created image and the last used settings
            self.result = (self.grab_image(), {"brush_size": self.brush_size, "brush_colour": self.brush_colour})
        return True


def get_password(root):
    return PasswordDialog(parent=root, title="Enter Password").result


def get_colour(root, colours, taken):
    return ColourDialog(parent=root, colours=colours, taken_colours=taken, title="Select Colour").result


def get_drawing(root, last_settings, colours):
    return DrawDialog(parent=root, brush_size=last_settings["brush_size"], brush_colour=last_settings["brush_colour"], colours=colours, title="Create Drawing").result
