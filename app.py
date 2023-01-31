import argparse
import numpy as np
import customtkinter
import image_utils
from content_manager import ContentManager
from widget_mode_methods import ModeMethodsControllerFrame, AppStatus
from widget_display import DisplayWindowFrame


class ContentComparisonApp(customtkinter.CTk):
    def __init__(self, root, src_folder_name="source"):
        super().__init__()
        self.content_handler = ContentManager(root, src_folder_name)
        # configure window
        self.mode_methods_handler = ModeMethodsControllerFrame(root, self.content_handler.methods, self.content_handler.files, master=self)
        self.mode_methods_handler.grid(row=0, column=0)
        self.video_controller = customtkinter.CTkSlider(master=self, from_=0, to=100, width=720, command=self.content_handler.set_video_position)
        self.display_handler = DisplayWindowFrame(self)
        self.display_handler.grid(row=2, column=0)

        self.paused = False
        self.images = None
        self.bind("<space>", self.on_space_pressed)

    def on_space_pressed(self, event):
        self.paused = not self.paused

    def display(self):
        # Read the files when changing method or files.
        update_status = self.mode_methods_handler.update_status
        if update_status == AppStatus.UPDATE_FILE or update_status == AppStatus.UPDATE_METHOD:
            self.title(self.mode_methods_handler.get_window_title())

            self.content_handler.load_files(self.mode_methods_handler.get_paths())

            self.display_handler.mouse_position = (0, 0)
            self.mode_methods_handler.update_status = AppStatus.UPDATED
            self.paused = False

        if not self.paused:
            # Show or hide video controller
            if self.content_handler.has_video():
                if len(self.video_controller.grid_info()) == 0:
                    self.video_controller.grid(row=1, column=0)
            else:
                self.video_controller.grid_forget()

            # Set video controller
            slider_position = self.content_handler.get_video_position()
            self.video_controller.set(slider_position)

            # Read images/videos
            ret, images = self.content_handler.read_frames()

            if not ret:
                self.paused = True
                images = self.images
            else:
                self.images = images
        else:
            images = self.images

        images = [img.copy() for img in images]
        mode = self.mode_methods_handler.internal_state["mode"]
        method = self.mode_methods_handler.internal_state.get("method", None)
        current_methods = self.mode_methods_handler.curr_methods

        assert mode in {"Compare", "Concat", "Specific"}, f"Load image for mode not added: {mode}"

        title_positions = [image_utils.TextPosition.TOP_LEFT] * len(current_methods)
        if mode == "Compare":
            title_positions = [image_utils.TextPosition.TOP_LEFT,
                               image_utils.TextPosition.TOP_RIGHT,
                               image_utils.TextPosition.BTM_LEFT,
                               image_utils.TextPosition.BTM_RIGHT]

        # Puts text in place
        for image, title, title_pos in zip(images, current_methods, title_positions):
            image_utils.put_text(image, title, title_pos)

        # Set to self.output image incase mouse is out of bounds
        if mode == "Concat":
            self.output_image = np.hstack(images)
        elif mode == "Specific":
            method_idx = current_methods.index(method)
            self.output_image = images[method_idx]
        else:
            m_x, m_y = self.display_handler.mouse_position
            i_y, i_x = images[0].shape[:2]
            if 0 <= m_x < i_x and 0 <= m_y < i_y:
                self.output_image = image_utils.merge_multiple_images(images[:4], self.display_handler.mouse_position)

        self.display_handler.update_image(self.output_image)
        self.after(10, self.display)


# TODO: Add comments for some of the functions should help with readability
# TODO: Add logger
if __name__ == "__main__":
    # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_appearance_mode("System")
    # Themes: "blue" (standard), "green", "dark-blue"
    customtkinter.set_default_color_theme("dark-blue")

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, help="Path to root directory", required=True)
    opt = parser.parse_args()

    app = ContentComparisonApp(root=opt.root)
    app.after(200, app.display)
    app.mainloop()
