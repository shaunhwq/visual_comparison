from typing import List, Union

from PIL import Image
from PIL.ImageTk import PhotoImage
import tkinter
import customtkinter
import cv2

from ..utils import shift_widget_to_root_center


__all__ = [
    "SearchGridPopup",
]


class SearchGridPopup(customtkinter.CTkToplevel):
    def __init__(self, images, width: int, height: int, callback, default_value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry(f"{width}x{height}")

        # Internal variables
        self.images = images
        self.width = width
        self.previous_width = width
        self.rows = []
        def destroy_callback(index: int):
            # Basically want to destroy the popup when we click.
            self._unbound_to_mousewheel()
            self.destroy()
            callback(index)
        self.callback = destroy_callback

        # Create widget objects
        self.title("Grid Preview")
        self.width_dropdown = customtkinter.CTkComboBox(self, values=["75", "100", "125"])
        self.width_dropdown.set(str(default_value))
        self.width_dropdown.configure(command=lambda value: self.populate_preview_window(row_height=value))
        self.width_dropdown.pack()
        self.canvas_viewport = tkinter.Canvas(self, height=height, width=width)
        self.canvas_viewport.pack(fill=customtkinter.BOTH, expand=True)
        self.scrollable_frame = customtkinter.CTkFrame(self.canvas_viewport)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas_viewport.configure(scrollregion=self.canvas_viewport.bbox("all")))
        self.canvas_viewport.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Misc stuff for all popups
        self.update_idletasks()
        self.grab_set()  # make other windows not clickable
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

        # Various binds for quality of life
        self.bind("<Escape>", lambda _: self.destroy())
        self.bind("<Configure>", self.on_resize)
        self._bound_to_mousewheel()

        # Create buttons and wait for user to click
        self.populate_preview_window(row_height=self.width_dropdown.get())
        self.master.wait_window(self)

    def on_resize(self, event):
        self.width = event.width

    def _bound_to_mousewheel(self):
        if self.tk.call("tk", "windowingsystem") == "x11":
            self.canvas_viewport.bind_all("<Button-4>", self._on_mousewheel)
            self.canvas_viewport.bind_all("<Button-5>", self._on_mousewheel)
        else:
            self.canvas_viewport.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self):
        self.canvas_viewport.unbind_all("<MouseWheel>")
        if self.tk.call("tk", "windowingsystem") == "x11":
            self.canvas_viewport.unbind_all("<Button-4>")
            self.canvas_viewport.unbind_all("<Button-5>")
        else:
            self.canvas_viewport.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, *args):
        if isinstance(args[0], tkinter.Event):
            event = args[0]

            if event.num == 4:
                event.delta = 1
            if event.num == 5:
                event.delta = -1

            scroll_amount = int(-1 * event.delta / abs(event.delta))
            self.canvas_viewport.yview_scroll(scroll_amount, "units")

    def populate_preview_window(
        self,
        border: int = 2,
        row_height: Union[str, int] = 75,
    ) -> None:
        """
        Load content
        :param images: List of images to place in button
        :param callback: Callback for button when clicked
        :param row_height: Height of each row in the image
        """
        # Destroy previous buttons
        row_height = int(row_height)
        for row in self.rows:
            row.destroy()
        self.update_idletasks()
        self.rows = []

        # Recreate buttons
        # Each row are frames, buttons stored in frame. If button size exceeds width of popup, then create another row.
        first_row = customtkinter.CTkFrame(master=self.scrollable_frame)
        first_row.grid(row=0)
        self.rows = [first_row]
        row_count, row_width = 0, 0

        for i, image in enumerate(self.images):
            # Resize image to new size if not there yet
            h, w, c = image.shape
            if h != row_height:
                scale = row_height / h
                button_image = cv2.resize(image, (int(w * scale), int(h * scale)))
            else:
                button_image = image

            # Check to ensure row does not overspill
            h, w, c = button_image.shape
            if row_width + w > self.width:
                row = customtkinter.CTkFrame(master=self.scrollable_frame)
                row.grid(row=len(self.rows))
                self.rows.append(row)
                row_count, row_width = 0, 0
                continue

            # Create button under the row
            image_pil = Image.fromarray(button_image)
            photo_img = PhotoImage(image_pil)
            button = tkinter.Button(master=self.rows[-1], image=photo_img, command=lambda i=i: self.callback(i), borderwidth=0)
            button.image = photo_img
            button.grid(row=0, column=row_count, padx=0, pady=0)

            # Update row variables
            row_count += 1
            row_width += w + border * 2
