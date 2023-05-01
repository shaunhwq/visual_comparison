import tkinter
from tkinter import filedialog
from typing import Optional
import dataclasses
import platform

import cv2
import numpy as np
import customtkinter

from .managers import ZoomManager, ContentManager
from .widgets import DisplayWidget, ControlButtonsWidget, MultiSelectPopUpWidget, PreviewWidget, get_user_input, VideoControlsWidget
from .enums import VCModes, VCState
from .utils import image_utils, file_utils, validate_int_str


@dataclasses.dataclass
class VCInternalState:
    MODE: VCModes = VCModes.Compare
    STATE: VCState = VCState.UPDATE_FILE
    METHOD: Optional[str] = None
    VIDEO_PAUSED: bool = False

    def reset(self):
        self.MODE = VCModes.Compare
        self.STATE = VCState.UPDATE_FILE
        self.METHOD = None
        self.VIDEO_PAUSED = False


class VisualComparisonApp(customtkinter.CTk):
    def __init__(self, root, src_folder_name="source"):
        super().__init__()

        # Maintains the selected method & function for the app
        self.app_status = VCInternalState()

        self.content_handler = ContentManager(root, src_folder_name)
        # configure window
        self.preview_widget = PreviewWidget(master=self)
        # File path completion for source folder

        src_file_paths = file_utils.complete_paths(root, src_folder_name, self.content_handler.files)
        self.preview_widget.populate_preview_window(src_file_paths, self.on_specify_index)
        self.preview_widget.grid(row=0, column=0)

        cb_callbacks = dict(
            on_prev=self.on_prev,
            on_next=self.on_next,
            on_specify_index=self.on_specify_index,
            on_select_methods=self.on_select_methods,
            on_save_image=self.on_save_image,
            on_copy_image=self.on_copy_image,
        )
        self.cb_widget = ControlButtonGroupWidget(master=self, callbacks=cb_callbacks)
        self.cb_widget.populate_methods_button(self.content_handler.current_methods, self.on_change_mode)
        self.cb_widget.populate_mode_button(VCModes, self.on_change_mode)
        self.cb_widget.grid(row=1, column=0)

        vc_callbacks = dict(
            on_set_video_position=self.on_set_video_position,
            on_pause=self.on_pause,
            on_specify_frame_no=self.on_specify_frame_no,
        )
        self.video_controls = VideoControlsWidget(master=self, callbacks=vc_callbacks)
        self.display_handler = DisplayWidget(self)
        self.display_handler.grid(row=3, column=0)

        self.images = None
        self.bind("a", self.on_prev)
        self.bind("d", self.on_next)
        self.bind("<Left>", self.on_prev)
        self.bind("<Right>", self.on_next)
        self.bind("<space>", self.on_pause)

        # Bind Ctrl C or Cmd C to copy image.
        bind_copy_cmd = "<M1-c>" if platform.system() == "Darwin" else "<Control-c>"
        self.bind(bind_copy_cmd, self.on_copy_image)
        bind_save_cmd = "<M1-s>" if platform.system() == "Darwin" else "<Control-s>"
        self.bind(bind_save_cmd, self.on_save_image)

        self.bind_methods_to_keys()

        self.zoom_manager = ZoomManager(self.display_handler)

    def bind_methods_to_keys(self):
        current_methods = self.content_handler.current_methods
        # Unbind all
        for i in range(9):
            self.unbind(str(i + 1))
            self.unbind(f"<KP_{i + 1}>")
        # Rebind current methods to number and num pad keys
        for i in range(min(len(current_methods), 9)):
            self.bind(str(i + 1), lambda event: self.on_change_mode(VCModes.Specific, current_methods[int(event.keysym) - 1]))
            self.bind(f"<KP_{i + 1}>", lambda event: self.on_change_mode(VCModes.Specific, current_methods[int(event.keysym.split("_")[1]) - 1]))

    def on_select_methods(self):
        def set_new_methods(new_methods):
            if len(new_methods) < 2:
                print(f"Please select more than 2 methods")
                return
            self.content_handler.current_methods = new_methods
            self.cb_widget.set_mode(VCModes.Compare)
            self.cb_widget.show_method_button(show=False)
            self.app_status.reset()
            self.cb_widget.populate_methods_button(new_methods, self.on_change_mode)
            self.bind_methods_to_keys()

        MultiSelectPopUpWidget(all_options=self.content_handler.methods, current_options=self.content_handler.current_methods, app_callback=set_new_methods)

    def on_pause(self, event=None):
        self.app_status.VIDEO_PAUSED = not self.app_status.VIDEO_PAUSED
        self.video_controls.pause(self.app_status.VIDEO_PAUSED)

    def on_specify_frame_no(self):
        self.app_status.VIDEO_PAUSED = True
        self.video_controls.pause()

        _, total_num_frames, _ = self.content_handler.get_video_position()

        user_input = get_user_input(
            text=f"Enter frame number in range [0, {total_num_frames}]",
            title="Specify frame number"
        )
        ret, desired_frame_no = validate_int_str(user_input)

        # Check valid str
        if not ret:
            return
        # Check valid index
        if not (0 <= desired_frame_no <= total_num_frames):
            return

        self.on_set_video_position(desired_frame_no)

    def on_set_video_position(self, value, relative=False, slider=False):
        curr, total, _ = self.content_handler.get_video_position()

        if slider:
            value = total * value / 100.
        if relative:
            value = curr + value - 1

        value = int(value)
        self.content_handler.set_video_position(value)
        self.video_controls.update_widget(*self.content_handler.get_video_position())
        # self.app_status.VIDEO_PAUSED = True
        ret, images = self.content_handler.read_frames()
        if ret:
            self.images = images

    def on_specify_index(self, index=None):
        if index is None:
            user_input = get_user_input(text="Enter an index:", title="Specify file index")
            ret, index = validate_int_str(user_input)
            if not ret:
                pass  # TODO: Add Invalid option error

        if self.content_handler.on_specify_index(value=index):
            self.preview_widget.highlight_selected(self.content_handler.current_index)
            self.app_status.STATE = VCState.UPDATE_FILE
        else:
            pass  # TODO: Add custom error msg

    def on_prev(self, event: Optional[tkinter.Event] = None):
        self.content_handler.on_prev()
        self.preview_widget.highlight_selected(self.content_handler.current_index)
        self.app_status.STATE = VCState.UPDATE_FILE

    def on_next(self, event: Optional[tkinter.Event] = None):
        self.content_handler.on_next()
        self.preview_widget.highlight_selected(self.content_handler.current_index)
        self.app_status.STATE = VCState.UPDATE_FILE

    def on_change_mode(self, mode, method=None):
        if method is None:
            method = self.content_handler.current_methods[0]

        # Double click on same button for example.
        if mode == VCModes.Compare:
            self.cb_widget.show_method_button(show=False)
        elif mode == VCModes.Concat:
            self.cb_widget.show_method_button(show=False)
        else:
            if method == self.app_status.METHOD and self.app_status.MODE == VCModes.Specific:
                self.cb_widget.show_method_button(show=False)
                self.cb_widget.set_method(VCModes.Compare)
                self.app_status.reset()
                return
            else:
                self.cb_widget.set_mode(VCModes.Specific)
                self.cb_widget.set_method(method)
                self.cb_widget.show_method_button(show=True)

        self.app_status.MODE = mode
        self.app_status.METHOD = method
        self.app_status.STATE = VCState.UPDATE_MODE

    def on_save_image(self, event=None):
        if hasattr(self, "output_image"):
            desired_path = filedialog.asksaveasfile(mode='w', defaultextension=".png").name
            print(desired_path)
            cv2.imwrite(desired_path, self.output_image)

    def on_copy_image(self, event=None):
        """Copy current contents of text_entry to clipboard."""
        if hasattr(self, "output_image"):
            image_utils.image_to_clipboard(self.output_image.copy())

    def display(self):
        # Read the files when changing method or files.
        if self.app_status.STATE == VCState.UPDATE_FILE or self.app_status.STATE == VCState.UPDATE_METHOD:
            self.title(self.content_handler.get_title())
            self.content_handler.load_files(self.content_handler.get_paths())
            self.display_handler.mouse_position = (0, 0)
            self.app_status.STATE = VCState.UPDATED
            self.app_status.VIDEO_PAUSED = False
            self.video_controls.pause(False)
            self.zoom_manager.reset()

        if not self.app_status.VIDEO_PAUSED:
            # Show or hide video controller
            if self.content_handler.has_video():
                if len(self.video_controls.grid_info()) == 0:
                    self.video_controls.grid(row=2, column=0, pady=2)
            else:
                self.video_controls.grid_forget()

            # Set video controller
            if self.content_handler.has_video():
                self.video_controls.update_widget(*self.content_handler.get_video_position())

            # Read images/videos
            ret, images = self.content_handler.read_frames()

            if not ret:
                self.app_status.VIDEO_PAUSED = True
                self.video_controls.pause(True)
                images = self.images
            else:
                self.images = images
        else:
            images = self.images

        # For visualization
        images = [img.copy() for img in images]
        current_methods = self.content_handler.current_methods

        title_positions = [image_utils.TextPosition.TOP_LEFT] * len(current_methods)
        if self.app_status.MODE == VCModes.Compare:
            title_positions = [image_utils.TextPosition.TOP_LEFT,
                               image_utils.TextPosition.TOP_RIGHT,
                               image_utils.TextPosition.BTM_LEFT,
                               image_utils.TextPosition.BTM_RIGHT]

        # Puts text in place
        for image, title, title_pos in zip(images, current_methods, title_positions):
            image_utils.put_text(image, title, title_pos)

        # Set to self.output image incase mouse is out of bounds
        if self.app_status.MODE == VCModes.Concat:
            comparison_img = np.hstack(images)
            self.cropped_image = self.zoom_manager.crop_regions(images)
            self.output_image = self.zoom_manager.draw_regions(comparison_img, num_images=len(images))

        elif self.app_status.MODE == VCModes.Specific:
            method_idx = current_methods.index(self.app_status.METHOD)
            comparison_img = images[method_idx]
            self.cropped_image = self.zoom_manager.crop_regions([comparison_img])
            self.output_image = self.zoom_manager.draw_regions(comparison_img)
        else:
            m_x, m_y = self.display_handler.mouse_position
            i_y, i_x = images[0].shape[:2]
            if 0 <= m_x < i_x and 0 <= m_y < i_y:
                comparison_img = image_utils.merge_multiple_images(images[:4], self.display_handler.mouse_position)
                self.cropped_image = self.zoom_manager.crop_regions([comparison_img])
                self.output_image = self.zoom_manager.draw_regions(comparison_img)

        # Cropped image is displayed below original image
        display_image = np.vstack([self.output_image, self.cropped_image]) if self.cropped_image is not None else self.output_image

        self.display_handler.update_image(display_image)

        # Refresh slower if in background to minimize cpu usage
        out_of_focus = self.focus_get() is None
        refresh_after = 500 if out_of_focus else 10
        self.after(refresh_after, self.display)
