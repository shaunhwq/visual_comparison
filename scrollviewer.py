import os
import tkinter
import tkinter as tk
from tkinter import ttk
import PIL.Image
import customtkinter
import cv2
from PIL.ImageTk import PhotoImage
from concurrent.futures import ThreadPoolExecutor
import glob


class ScrollViewer(customtkinter.CTkFrame):
    def __init__(self, source_folder, common_files, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)

        paths = []
        for i in range(len(common_files)):
            uncomplete_path = os.path.join(source_folder, common_files[i]) + ".*"
            paths.append(glob.glob(uncomplete_path)[0])

        # Need to change to use glob to read later on because we will depend on the items in the set.
        paths.sort()
        with ThreadPoolExecutor() as executor:
            images = list(executor.map(self._load_img_thumbnail, paths))

        canvas_viewport = tk.Canvas(self, height=80, width=720)
        scrollable_frame = ttk.Frame(canvas_viewport)

        # When we add a new object the total frame will extend accordingly
        scrollable_frame.bind("<Configure>", lambda e: canvas_viewport.configure(scrollregion=canvas_viewport.bbox("all")))

        # Create viewport
        canvas_viewport.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Bind mousewheel to allow horizontal scrolling
        canvas_viewport.bind_all("<MouseWheel>", self._on_mousewheel)

        # TODO: Maximum scroll is somewhere around 30k pixels.
        self.selected_idx = 0
        self.buttons = []
        for i, image in enumerate(images):
            image_pil = PIL.Image.fromarray(image)
            photo_img = PhotoImage(image_pil)
            button = tk.Button(master=scrollable_frame, image=photo_img, command=lambda i=i: callback(i), borderwidth=0)
            button.image = photo_img
            button.pack(side="left")
            self.buttons.append(button)
        self.canvas_viewport = canvas_viewport
        canvas_viewport.grid(row=0, sticky="nsew")

        self.highlight_selected(0)

    def highlight_selected(self, index):
        # Reset previous button
        prev_button = self.buttons[self.selected_idx]
        prev_button.configure(highlightbackground="black", borderwidth=0)

        # Set new button white border
        self.selected_idx = index
        curr_button = self.buttons[self.selected_idx]
        curr_button.configure(highlightbackground="white", borderwidth=3)

        # Center button in widget. Needs relative position [0, 1]
        button_x_pos = curr_button.winfo_x()
        button_width = curr_button.winfo_width()
        button_x_pos -= 360 - button_width // 2 if button_x_pos > 360 else button_x_pos
        canvas_width = self.canvas_viewport.bbox("all")[2]
        new_canvas_pos_relative = button_x_pos / canvas_width
        self.canvas_viewport.xview("moveto", new_canvas_pos_relative)

    def _on_mousewheel(self, *args):
        if isinstance(args[0], tkinter.Event):
            event = args[0]
            self.canvas_viewport.xview_scroll(-1 * int(event.delta), "units")
        elif args[0] == "moveto":
            self.canvas_viewport.xview(*args)
            # TODO Get percentage and estimate overall position

    @staticmethod
    def _load_img_thumbnail(img_path, max_height=75):
        img = cv2.imread(img_path, -1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, _ = img.shape
        scale = max_height / h
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        return img
