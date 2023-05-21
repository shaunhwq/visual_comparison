from typing import List

import numpy as np
import tkinter
import customtkinter
from tkinter import ttk
import PIL.Image
from PIL.ImageTk import PhotoImage

from ..utils import file_utils


__all__ = ["PreviewWidget"]


class PreviewWidget(customtkinter.CTkFrame):
    def __init__(self, *args, **kwargs):
        """
        A complex widget to allow users to preview images/videos. When clicked, callback is called with the id of the
        clicked button.

        As we might have to load a large number of images (e.g. 10k images), tkinter is unable to display all of them.
        Thus, we need to load them in batches.
        """
        super().__init__(*args, **kwargs)

        self.canvas_viewport = tkinter.Canvas(self, height=80, width=720)
        self.scrollable_frame = ttk.Frame(self.canvas_viewport)

        # When we add a new object the total frame will extend accordingly
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas_viewport.configure(scrollregion=self.canvas_viewport.bbox("all")))

        # Create viewport
        self.canvas_viewport.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Bind mousewheel to allow horizontal scrolling
        # https://stackoverflow.com/questions/17355902/tkinter-binding-mousewheel-to-scrollbar
        self.scrollable_frame.bind('<Enter>', self._bound_to_mousewheel)
        self.scrollable_frame.bind('<Leave>', self._unbound_to_mousewheel)

        self.selected_idx = 0
        self.view_radius = 100
        self.view_index = -1000

        self.buttons = []

        self.canvas_viewport.grid(row=0, sticky="nsew")

    def _bound_to_mousewheel(self, event):
        self.canvas_viewport.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.canvas_viewport.unbind_all("<MouseWheel>")

    def populate_preview_window(self, images: List[np.array], callback) -> None:
        """
        Load content
        :param images: List of images to place in button
        :param callback: Callback for button when clicked
        :return:
        """
        # Destroy any existing buttons, for changing directories
        for button in self.buttons:
            button.destroy()

        # Create buttons
        for i, image in enumerate(images):
            image_pil = PIL.Image.fromarray(image)
            photo_img = PhotoImage(image_pil)
            button = tkinter.Button(master=self.scrollable_frame, image=photo_img, command=lambda i=i: callback(i), borderwidth=0)
            button.image = photo_img
            self.buttons.append(button)

        # Visualize
        self.highlight_selected(0)

    def get_index_min_max(self, index):
        minimum = max(0, index - self.view_radius)
        maximum = min(len(self.buttons), index + self.view_radius + 1)
        return minimum, maximum

    def place_objects(self, curr_idx, next_idx):
        if curr_idx == next_idx:
            return

        curr_min, curr_max = self.get_index_min_max(curr_idx)
        next_min, next_max = self.get_index_min_max(next_idx)

        curr_idxs = set(i for i in range(curr_min, curr_max))
        next_idxs = set(i for i in range(next_min, next_max))
        keep_idxs = curr_idxs.intersection(next_idxs)
        hide_idxs = curr_idxs - keep_idxs
        show_idxs = next_idxs - keep_idxs

        # Hacky way of fixing issue #1, somehow it occurs when number of items is reduced too much?
        # Anyway, not removing some items does not hit the 30+k pixel limit for the widget.
        if len(show_idxs) > 0 and max(show_idxs) != len(self.buttons) - 1:
            for idx in hide_idxs:
                self.buttons[idx].grid_forget()
        for idx in show_idxs:
            self.buttons[idx].grid(row=0, column=idx)

        self.scrollable_frame.update_idletasks()

    def set_view_by_index(self, index, position="center"):
        button = self.buttons[index]
        # Center button in widget.
        button_x_pos = button.winfo_x()
        button_width = button.winfo_width()

        if position == "center":
            button_x_pos -= 360 - button_width // 2 if button_x_pos > 360 else button_x_pos
        elif position == "right":
            button_x_pos -= 720 - button_width if button_x_pos > 720 else button_x_pos
        elif position == "left":
            pass
        else:
            raise NotImplementedError(f"Unknown position: {position}")

        canvas_width = self.canvas_viewport.bbox("all")[2]

        # Needs relative position [0, 1]
        new_canvas_pos_relative = button_x_pos / canvas_width

        self.canvas_viewport.xview("moveto", new_canvas_pos_relative)

    def highlight_selected(self, index):
        # TODO: Why click max value will set over?
        view_min, view_max = self.get_index_min_max(self.view_index)
        if not view_min + 10 <= self.selected_idx < view_max - 10:
            # print("Updating objects")
            self.place_objects(self.view_index, index)
            self.view_index = index

        # Reset previous button
        prev_button = self.buttons[self.selected_idx]
        prev_button.configure(highlightbackground="black", borderwidth=0)

        # Set new button white border
        self.selected_idx = index
        curr_button = self.buttons[self.selected_idx]
        curr_button.configure(highlightbackground="white", borderwidth=3)

        self.set_view_by_index(index)

    def _on_mousewheel(self, *args):
        if isinstance(args[0], tkinter.Event):
            event = args[0]
            direction = "left" if event.delta * -1 < 0 else "right"
            view_min, view_max = self.canvas_viewport.xview()

            if view_min == 0 and direction == "left":
                # 50 So still got some space for scrolling
                new_index = max(0, self.view_index - 50)
                if new_index != self.view_index:
                    self.place_objects(self.view_index, new_index)
                    self.set_view_by_index(max(0, self.view_index - self.view_radius), "left")
                    self.view_index = new_index

            elif view_max == 1.0 and direction == "right":
                # 50 So still got some space for scrolling
                new_index = min(len(self.buttons) - 1, self.view_index + 50)
                if new_index != self.view_index and self.view_index + self.view_radius < len(self.buttons):
                    self.place_objects(self.view_index, new_index)
                    self.set_view_by_index(min(len(self.buttons) - 1, self.view_index + self.view_radius), "right")
                    self.view_index = new_index
            else:
                self.canvas_viewport.xview_scroll(-1 * int(event.delta), "units")
