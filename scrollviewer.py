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
import time


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
            if i < 101:
                button.grid(row=0, column=i)
            self.buttons.append(button)
        self.canvas_viewport = canvas_viewport
        self.scrollable_frame = scrollable_frame
        canvas_viewport.grid(row=0, sticky="nsew")

        self.view_index = 0
        self.highlight_selected(0)

    def place_objects(self, curr_idx, next_idx, display_radius=100):
        if curr_idx == next_idx:
            return

        curr_min = max(0, curr_idx - display_radius)
        curr_max = min(len(self.buttons), curr_idx + display_radius + 1)
        next_min = max(0, next_idx - display_radius)
        next_max = min(len(self.buttons), next_idx + display_radius + 1)

        curr_idxs = set(i for i in range(curr_min, curr_max))
        next_idxs = set(i for i in range(next_min, next_max))
        keep_idxs = curr_idxs.intersection(next_idxs)
        hide_idxs = curr_idxs - keep_idxs
        show_idxs = next_idxs - keep_idxs

        for idx in hide_idxs:
            self.buttons[idx].grid_forget()
        for idx in show_idxs:
            self.buttons[idx].grid(row=0, column=idx)

        # TODO: Optimize, only if selected index is close to 50 of the edges then update
        print(f"Hide: {len(hide_idxs)}, Show: {len(show_idxs)}, Keep: {len(keep_idxs)}")

        # TODO: Is this the right way?
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
            button_x_pos = button_x_pos
        else:
            raise NotImplementedError(f"Unknown position: {position}")

        canvas_width = self.canvas_viewport.bbox("all")[2]

        # Needs relative position [0, 1]
        new_canvas_pos_relative = button_x_pos / canvas_width

        self.canvas_viewport.xview("moveto", new_canvas_pos_relative)

    def highlight_selected(self, index):
        # TODO: Why click max value will set over?
        t1 = time.time()
        self.place_objects(self.view_index, index)
        print(f"{round((time.time() - t1) * 1000, 2)} ms")

        # Reset previous button
        prev_button = self.buttons[self.selected_idx]
        prev_button.configure(highlightbackground="black", borderwidth=0)

        # Set new button white border
        self.view_index = index
        self.selected_idx = index
        curr_button = self.buttons[self.selected_idx]
        curr_button.configure(highlightbackground="white", borderwidth=3)

        self.set_view_by_index(index)

    def _on_mousewheel(self, *args):
        if isinstance(args[0], tkinter.Event):
            event = args[0]
            direction = "left" if event.delta * -1 < 0 else "right"
            view_min, view_max = self.canvas_viewport.xview()
            #print(view_min, view_max)
            if view_min == 0 and direction == "left":
                # Need a self.view position also
                print("expanding view left")
                new_index = max(0, self.view_index - 50)
                if new_index != self.view_index:
                    self.place_objects(self.view_index, new_index)
                    self.set_view_by_index(max(0, self.view_index - 100), "left")
                    self.view_index = new_index
            elif view_max == 1.0 and direction == "right":
                print("expanding view right..")
                new_index = min(len(self.buttons) - 1, self.view_index + 50)
                if new_index != self.view_index and self.view_index + 100 < len(self.buttons):
                    print("Changing")
                    print(new_index, self.view_index)
                    self.place_objects(self.view_index, new_index)
                    self.set_view_by_index(min(len(self.buttons) - 1, self.view_index + 100), "right")
                    self.view_index = new_index
            else:
                print("Scroll")
                self.canvas_viewport.xview_scroll(-1 * int(event.delta), "units")
            print("Done")

    @staticmethod
    def _load_img_thumbnail(img_path, max_height=75):
        img = cv2.imread(img_path, -1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, _ = img.shape
        scale = max_height / h
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        return img
