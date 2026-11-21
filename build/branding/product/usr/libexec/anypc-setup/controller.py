"""Navigate the offline GTK wizard with a standard Linux game controller."""

import os
import struct
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk


EVENT = struct.Struct("@llHHi")
DIRECTIONS = {544: "up", 545: "down", 546: "left", 547: "right"}
FOCUS = {"up": Gtk.DirectionType.UP, "down": Gtk.DirectionType.DOWN,
         "left": Gtk.DirectionType.LEFT, "right": Gtk.DirectionType.RIGHT}


class Controller:
    def __init__(self, window):
        self.window = window
        self.dialog = None
        self.inputs = {}
        self.discover()
        GLib.timeout_add_seconds(2, self.discover)

    def discover(self):
        for path in Path("/dev/input").glob("event*"):
            if path in self.inputs:
                continue
            try:
                dev = path.stat().st_rdev
                properties = Path(f"/run/udev/data/c{os.major(dev)}:{os.minor(dev)}").read_text()
                if "E:ID_INPUT_JOYSTICK=1" not in properties.splitlines():
                    continue
                fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            except OSError:
                continue
            self.inputs[path] = fd
            GLib.io_add_watch(fd, GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR, self.read, path)
        return GLib.SOURCE_CONTINUE

    def read(self, fd, condition, path):
        try:
            data = os.read(fd, EVENT.size * 32) if condition & GLib.IO_IN else b""
        except BlockingIOError:
            return GLib.SOURCE_CONTINUE
        except OSError:
            data = b""
        if not data:
            os.close(self.inputs.pop(path))
            return GLib.SOURCE_REMOVE
        for _, _, kind, code, value in EVENT.iter_unpack(data):
            if kind == 1 and value == 1:
                action = {304: "accept", 305: "back"}.get(code, DIRECTIONS.get(code))
            elif kind == 3 and code in (16, 17) and value:
                action = (("left", "right") if code == 16 else ("up", "down"))[value > 0]
            else:
                continue
            if action:
                self.navigate(action)
        return GLib.SOURCE_CONTINUE

    def navigate(self, action):
        window = self.dialog or self.window
        focus = window.get_focus()
        control = focus
        while control and not isinstance(control, (Gtk.ComboBox, Gtk.SpinButton)):
            control = control.get_parent()
        if action == "back":
            if self.dialog:
                self.dialog.response(Gtk.ResponseType.CANCEL)
            elif self.window.back_button.get_visible():
                self.window.back_button.clicked()
        elif action == "accept":
            if isinstance(focus, Gtk.Entry) and not isinstance(control, Gtk.SpinButton) and not self.dialog:
                self.keyboard(focus)
            elif isinstance(control, Gtk.ComboBox):
                control.set_active((control.get_active() + 1) % len(control.get_model()))
            elif focus:
                focus.activate()
            else:
                window.child_focus(Gtk.DirectionType.TAB_FORWARD)
        elif action in ("left", "right") and control:
            step = 1 if action == "right" else -1
            if isinstance(control, Gtk.ComboBox):
                control.set_active(max(0, min(len(control.get_model()) - 1, control.get_active() + step)))
            else:
                control.set_value(control.get_value() + step * control.get_adjustment().get_step_increment())
        elif not window.child_focus(FOCUS[action]):
            window.child_focus(Gtk.DirectionType.TAB_FORWARD if action in ("down", "right") else Gtk.DirectionType.TAB_BACKWARD)

    def keyboard(self, entry):
        ro = self.window.language
        dialog = Gtk.Dialog(title=("Keyboard", "Tastatură")[ro], transient_for=self.window, modal=True)
        self.dialog = dialog
        box = dialog.get_content_area()
        box.set_border_width(12)
        field = Gtk.Entry(text=entry.get_text(), visibility=entry.get_visibility(), editable=False)
        field.set_can_focus(False)
        box.pack_start(field, False, False, 5)
        grid = Gtk.Grid(column_spacing=3, row_spacing=3)
        box.pack_start(grid, False, False, 0)
        letters = []
        for row, chars in enumerate(("1234567890", "qwertyuiop", "asdfghjkl-", "zxcvbnm_@.")):
            for col, char in enumerate(chars):
                key = Gtk.Button(label=char)
                key.connect("clicked", lambda button: field.set_text(field.get_text() + button.get_label()))
                grid.attach(key, col, row, 1, 1)
                if char.isalpha():
                    letters.append(key)

        def change_case(*_):
            for key in letters:
                key.set_label(key.get_label().swapcase())

        shift = Gtk.Button(label="⇧")
        shift.connect("clicked", change_case)
        erase = Gtk.Button(label="⌫")
        erase.connect("clicked", lambda *_: field.set_text(field.get_text()[:-1]))
        grid.attach(shift, 0, 4, 2, 1)
        grid.attach(erase, 8, 4, 2, 1)
        dialog.add_button(("Cancel", "Anulează")[ro], Gtk.ResponseType.CANCEL)
        dialog.add_button(("Done", "Gata")[ro], Gtk.ResponseType.OK)
        dialog.show_all()
        grid.get_child_at(0, 0).grab_focus()
        if dialog.run() == Gtk.ResponseType.OK:
            entry.set_text(field.get_text())
        self.dialog = None
        dialog.destroy()
        entry.grab_focus()
