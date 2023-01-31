import customtkinter
import cv2
import platform
import image_utils
from PIL import Image


class DisplayWindowFrame(customtkinter.CTkFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.image_label = customtkinter.CTkLabel(master=self, text="", width=720, height=1280)
        self.image_label.grid(row=0, column=0)
        self.mouse_position = (0, 0)
        self.image_label.bind("<Motion>", self.on_mouse_move)
        self.scale = 1

    def update_image(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, _ = image.shape
        # Different systems have different borders which use part of the screen for their display (dock etc)
        h_multiplier = 0.75 if platform.system() == "Darwin" else 0.8
        screen_h, screen_w = self.master.winfo_screenheight() * h_multiplier, self.master.winfo_screenwidth()
        if w > screen_w or h > screen_h:
            self.scale = 1 / max(w / screen_w, h / screen_h)
            image = image_utils.resize_scale(image, scale=self.scale)
            h, w, _ = image.shape
        else:
            self.scale = 1
        pil_image = Image.fromarray(image)
        ctk_image = customtkinter.CTkImage(light_image=pil_image, size=(w, h))
        self.image_label.configure(image=ctk_image, width=w, height=h)

    def on_mouse_move(self, event):
        self.mouse_position = (int(event.x / self.scale), int(event.y / self.scale))
