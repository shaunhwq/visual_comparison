import os
import time
import tkinter
from tkinter import filedialog
from typing import Optional
import dataclasses
import platform
from threading import Thread

import cv2
import numpy as np
import customtkinter
from tqdm import tqdm

from .managers import ZoomManager, ContentManager, VideoWriter, FastLoadChecker, IconManager
from .widgets import DisplayWidget, ControlButtonsWidget, PreviewWidget, VideoControlsWidget
from .widgets import MultiSelectPopUpWidget, DataSelectionPopup, MessageBoxPopup, GetNumberBetweenRangePopup, RootSelectionPopup, ExportVideoPopup, ExportSelectionPopup, ProgressBarPopup, SettingsPopupWidget
from .enums import VCModes, VCState
from .utils import image_utils, set_appearance_mode_and_theme, file_reader, is_window_in_background
from .configurations import read_config, parse_config, config_info


@dataclasses.dataclass
class VCInternalState:
    MODE: VCModes = VCModes.Compare
    STATE: VCState = VCState.UPDATE_FILE
    METHOD: Optional[str] = None
    VIDEO_PAUSED: bool = False
    VIDEO_PLAYBACK_RATE: float = 1.0

    def reset(self):
        self.MODE = VCModes.Compare
        self.STATE = VCState.UPDATE_FILE
        self.METHOD = None
        self.VIDEO_PAUSED = False


class VisualComparisonApp(customtkinter.CTk):
    def __init__(self, root=None, preview_folder=None, config_path="visual_comparison/config.ini", assets_path="visual_comparison/assets/"):
        super().__init__()

        self.config_path = config_path
        self.configurations = parse_config(read_config(config_path))

        set_appearance_mode_and_theme(self.configurations["Appearance"]["mode"], self.configurations["Appearance"]["theme"])

        self.root = root
        self.preview_folder = preview_folder

        # Maintains the selected method & function for the app
        self.app_status = VCInternalState()
        self.content_handler: Optional[ContentManager] = None
        self.images = None
        self.fast_load_checker = FastLoadChecker()
        self.icon_manager = IconManager(icon_assets_path=os.path.join(assets_path, "icons"))

        # Create Preview Window
        self.preview_widget = PreviewWidget(master=self)
        self.preview_widget.grid(row=0, column=0)

        # Create Control Buttons
        cb_callbacks = dict(
            on_prev_file=self.on_prev_file,
            on_specify_index=self.on_specify_index,
            on_next_file=self.on_next_file,
            on_filter_files=self.on_filter_files,
            on_prev_method=self.on_prev_method,
            on_select_methods=self.on_select_methods,
            on_next_method=self.on_next_method,
            on_export=self.on_export,
            on_copy_image=self.on_copy_image,
            on_change_dir=self.on_change_dir,
            on_change_settings=self.on_change_settings,
        )
        self.cb_widget = ControlButtonsWidget(master=self, icon_manager=self.icon_manager, callbacks=cb_callbacks)
        self.cb_widget.populate_mode_button(VCModes, self.on_change_mode)
        self.cb_widget.set_mode(VCModes.Compare)
        self.cb_widget.grid(row=1, column=0)

        # Create Video Control Buttons
        vc_callbacks = dict(
            on_set_video_position=self.on_set_video_position,
            on_pause=self.on_pause,
            on_specify_frame_no=self.on_specify_frame_no,
            on_change_playback_rate=self.on_change_playback_rate,
        )
        self.video_controls = VideoControlsWidget(master=self, callbacks=vc_callbacks)
        self.video_writer = None  # For exporting video (custom)
        self.video_writer_options = {}

        # Create Display Window
        self.display_handler = DisplayWidget(master=self)
        self.display_handler.grid(row=3, column=0)
        self.zoom_manager = ZoomManager(self.display_handler)

        # File changing bindings
        self.bind_keys_to_buttons()
        # Bind Ctrl C or Cmd C to copy image.
        bind_copy_cmd = "<M1-c>" if platform.system() == "Darwin" else "<Control-c>"
        self.bind(bind_copy_cmd, self.on_copy_image)
        bind_export_cmd = "<M1-s>" if platform.system() == "Darwin" else "<Control-s>"
        self.bind(bind_export_cmd, self.on_export)

        # Get Data
        ret = False
        while not ret:
            ret = self.load_content()

        self.preview_widget.populate_preview_window(self.content_handler.thumbnails, self.on_specify_index)
        self.cb_widget.populate_methods_button(self.content_handler.current_methods, self.on_change_mode)

        self.bind_methods_to_keys()

    def load_content(self):
        popup = RootSelectionPopup(self.root, self.preview_folder)
        cancelled, ret_vals = popup.get_input()
        if cancelled:
            return False

        root_folder, preview_folder = ret_vals
        content_handler = ContentManager(root=root_folder, preview_folder=preview_folder)

        if len(content_handler.methods) <= 1:
            msg_popup = MessageBoxPopup("Root folder must contain more than 1 sub folder")
            msg_popup.wait()
            return False
        if len(content_handler.files) == 0:
            msg_popup = MessageBoxPopup("There are no common files in all sub folders")
            msg_popup.wait()
            return False

        self.content_handler = content_handler
        self.root = root_folder
        self.preview_folder = preview_folder
        return True

    def on_change_playback_rate(self, new_rate):
        if new_rate == "Max":
            self.app_status.VIDEO_PLAYBACK_RATE = self.configurations["Functionality"]["max_fps"]
        else:
            # Strip 'x' at the back e.g. 1.5x, 1x, 2x -> 1.5, 1, 2
            new_rate = new_rate[:-1]
            self.app_status.VIDEO_PLAYBACK_RATE = float(new_rate)

    def on_change_settings(self):
        self.on_pause(paused=True)
        settings_popup = SettingsPopupWidget(self.config_path, config_info, self.icon_manager)
        is_cancelled, new_config = settings_popup.get_input()

        if is_cancelled:
            return

        prev_config = self.configurations
        self.configurations = new_config
        self.bind_keys_to_buttons(prev_config)
        set_appearance_mode_and_theme(new_config["Appearance"]["mode"], new_config["Appearance"]["theme"])

    def on_change_dir(self):
        self.on_pause(paused=True)

        ret = self.load_content()
        if not ret:
            return

        # Setting app states and files
        self.cb_widget.set_mode(VCModes.Compare)
        self.cb_widget.show_method_button(show=False)
        self.app_status.reset()

        # Destroy and re-create preview widget TODO: Try reuse
        self.preview_widget.destroy()
        self.preview_widget = PreviewWidget(master=self)
        self.preview_widget.grid(row=0, column=0)
        self.preview_widget.populate_preview_window(self.content_handler.thumbnails, self.on_specify_index)
        self.on_specify_index(0)

        self.cb_widget.populate_methods_button(self.content_handler.current_methods, self.on_change_mode)
        self.bind_methods_to_keys()

    def on_prev_method(self, event=None):
        methods = self.content_handler.current_methods
        current_idx = methods.index(self.app_status.METHOD) if self.app_status.METHOD is not None else 0
        desired_index = (current_idx - 1) % len(methods)
        self.on_change_mode(VCModes.Specific, methods[desired_index])

    def on_next_method(self, event=None):
        methods = self.content_handler.current_methods
        current_idx = methods.index(self.app_status.METHOD) if self.app_status.METHOD is not None else 0
        desired_index = (current_idx + 1) % len(methods)
        self.on_change_mode(VCModes.Specific, methods[desired_index])

    def bind_keys_to_buttons(self, prev_config=None) -> None:
        """
        :param prev_config: Previous configuration. Will unbind if present
        :return: None
        """
        # Unbind if present
        if prev_config is not None:
            self.unbind(prev_config["Keybindings"]["prev_file"])
            self.unbind(prev_config["Keybindings"]["next_file"])
            self.unbind(prev_config["Keybindings"]["prev_file_alternate"])
            self.unbind(prev_config["Keybindings"]["next_file_alternate"])
            self.unbind(prev_config["Keybindings"]["pause_video"])
            self.unbind(prev_config["Keybindings"]["prev_method"])
            self.unbind(prev_config["Keybindings"]["next_method"])
            self.unbind(prev_config["Keybindings"]["prev_method_alternate"])
            self.unbind(prev_config["Keybindings"]["next_method_alternate"])
            self.unbind(prev_config["Keybindings"]["skip_to_1_frame_before"])
            self.unbind(prev_config["Keybindings"]["skip_to_1_frame_after"])
            self.unbind(prev_config["Keybindings"]["skip_to_10_frame_before"])
            self.unbind(prev_config["Keybindings"]["skip_to_10_frame_after"])

        # Bind Keys to buttons
        self.bind(self.configurations["Keybindings"]["prev_file"], self.on_prev_file)
        self.bind(self.configurations["Keybindings"]["next_file"], self.on_next_file)
        self.bind(self.configurations["Keybindings"]["prev_file_alternate"], self.on_prev_file)
        self.bind(self.configurations["Keybindings"]["next_file_alternate"], self.on_next_file)
        self.bind(self.configurations["Keybindings"]["pause_video"], self.on_pause)
        self.bind(self.configurations["Keybindings"]["prev_method"], self.on_prev_method)
        self.bind(self.configurations["Keybindings"]["next_method"], self.on_next_method)
        self.bind(self.configurations["Keybindings"]["prev_method_alternate"], self.on_prev_method)
        self.bind(self.configurations["Keybindings"]["next_method_alternate"], self.on_next_method)
        self.bind(self.configurations["Keybindings"]["skip_to_1_frame_before"], lambda event: self.on_set_video_position(-1, relative=True))
        self.bind(self.configurations["Keybindings"]["skip_to_1_frame_after"], lambda event: self.on_set_video_position(1, relative=True))
        self.bind(self.configurations["Keybindings"]["skip_to_10_frame_before"], lambda event: self.on_set_video_position(-10, relative=True))
        self.bind(self.configurations["Keybindings"]["skip_to_10_frame_after"], lambda event: self.on_set_video_position(10, relative=True))

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
        self.on_pause(paused=True)

        popup = MultiSelectPopUpWidget(all_options=self.content_handler.methods, current_options=self.content_handler.current_methods)
        is_cancelled, new_methods = popup.get_input()

        if is_cancelled:
            return

        if len(new_methods) < 2:
            msg_popup = MessageBoxPopup("Please select more than 2 methods")
            msg_popup.wait()
            return
        self.content_handler.current_methods = new_methods
        self.cb_widget.set_mode(VCModes.Compare)
        self.cb_widget.show_method_button(show=False)
        self.app_status.reset()
        self.cb_widget.populate_methods_button(new_methods, self.on_change_mode)
        self.bind_methods_to_keys()

    def on_filter_files(self):
        self.on_pause(paused=True)

        # Prepare data for populating popup
        row = max(self.content_handler.data, key=lambda row: len(row[1]))
        text_width = int(400./55 * len(row[1])) + 25  # Number of pixels for width
        num_titles = max(len(d) for d in self.content_handler.data)
        titles = self.content_handler.data_titles[: num_titles]

        # Get data from popup
        popup = DataSelectionPopup(self.content_handler.data, column_titles=titles, text_width=text_width)
        is_cancelled, rows = popup.get_input()

        if is_cancelled:
            return

        if len(rows) == 0:
            msg_popup = MessageBoxPopup("No items selected. Ignoring selection")
            msg_popup.wait()
            return

        # Setting app states and files
        self.content_handler.current_files = [r[1] for r in rows]
        self.content_handler.current_index = 0
        self.cb_widget.set_mode(VCModes.Compare)
        self.cb_widget.show_method_button(show=False)
        self.app_status.reset()

        # Destroy and re-create preview widget TODO: Try reuse
        self.preview_widget.destroy()
        self.preview_widget = PreviewWidget(master=self)
        self.preview_widget.grid(row=0, column=0)
        selected_thumbnails = [self.content_handler.thumbnails[r[0]] for r in rows]
        self.preview_widget.populate_preview_window(selected_thumbnails, self.on_specify_index)
        self.on_specify_index(0)

    def on_pause(self, event=None, paused=None):
        new_pause_status = not self.app_status.VIDEO_PAUSED if paused is None else paused
        self.app_status.VIDEO_PAUSED = new_pause_status
        self.video_controls.pause(new_pause_status)

    def on_specify_frame_no(self):
        self.on_pause(paused=True)

        _, total_num_frames, _ = self.content_handler.get_video_position()

        popup = GetNumberBetweenRangePopup(
            text=f"Enter frame number in range [0, {total_num_frames}]",
            title="Specify frame number",
            desired_type=int,
            lower_bound=0,
            upper_bound=total_num_frames
        )
        is_cancelled, desired_frame_no = popup.get_input()
        if is_cancelled:
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

        ret, images = self.content_handler.read_frames()
        if ret:
            self.images = images

    def on_specify_index(self, index=None):
        self.on_pause(paused=True)

        upper_bound = len(self.content_handler.current_files) - 1
        if index is None:
            popup = GetNumberBetweenRangePopup(
                text=f"Enter an index betweeen [0, {len(self.content_handler.current_files) - 1}]",
                title="Specify file index",
                desired_type=int,
                lower_bound=0,
                upper_bound=upper_bound,
            )
            is_cancelled, index = popup.get_input()
            if is_cancelled:
                return

        # Need to verify when on_specify_index is called with not None index
        ret = self.content_handler.on_specify_index(value=index)
        if not ret:
            message = f"Index {index} not in range [0, {upper_bound}]"
            msg_popup = MessageBoxPopup(message)
            msg_popup.wait()
            return

        self.preview_widget.highlight_selected(self.content_handler.current_index)
        self.app_status.STATE = VCState.UPDATE_FILE

    def on_prev_file(self, event: Optional[tkinter.Event] = None):
        self.content_handler.on_prev()
        self.preview_widget.highlight_selected(self.content_handler.current_index)
        self.app_status.STATE = VCState.UPDATE_FILE
        self.fast_load_checker.update()

    def on_next_file(self, event: Optional[tkinter.Event] = None):
        self.content_handler.on_next()
        self.preview_widget.highlight_selected(self.content_handler.current_index)
        self.app_status.STATE = VCState.UPDATE_FILE
        self.fast_load_checker.update()

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

    def on_export(self, event: Optional[tkinter.Event] = None) -> None:
        """
        Handle button event for image/video export functionality. Changes to stop button if writing custom videos.
        :param event: Tkinter event, passed by self.bind.
        :return: None
        """
        if not hasattr(self, "display_image"):
            msg_popup = MessageBoxPopup("self.display_image does not exist")
            msg_popup.wait()
            return

        # When stop is clicked. Export Button changes to a stop button when writing to video.
        if self.video_writer is not None:
            self.reset_video_writer()
            return

        self.on_pause(paused=True)

        export_select_popup = ExportSelectionPopup()
        is_cancelled, export_format = export_select_popup.get_input()
        if is_cancelled:
            return

        if export_format == "Image":
            self.export_image()
            return
        if export_format != "Video":
            raise NotImplementedError(f"Unknown option when selecting export options: {export_format}")

        height, width = self.display_image.shape[:2]
        if self.content_handler.has_video():
            _, _, video_fps = self.content_handler.get_video_position()
        else:
            video_fps = self.configurations["Functionality"]["max_fps"]

        export_video_popup = ExportVideoPopup(
            file_name=os.path.splitext(self.content_handler.current_files[self.content_handler.current_index])[0],
            img_width=width,
            img_height=height,
            video_fps=video_fps if self.content_handler.has_video() else self.configurations["Functionality"]["max_fps"],
        )
        is_cancelled, video_export_options = export_video_popup.get_input()
        if is_cancelled:
            return

        export_type = video_export_options["export_type"]
        export_path = video_export_options["export_path"]
        if export_type == "Fixed (Concatenated)":
            if not self.content_handler.has_video():
                msg_popup = MessageBoxPopup("Current file is not a video, can't export in Concatenate mode")
                msg_popup.wait()
                self.focus_get()
                return
            Thread(target=lambda: self.export_fixed_video(export_path)).start()
        elif export_type == "Custom":
            self.video_writer = VideoWriter(export_path, width, height, video_export_options["export_fps"])
            self.video_writer_options = video_export_options.get("export_options", {})
            self.cb_widget.toggle_export_button()
        else:
            raise NotImplementedError(f"Unknown export type: {export_type}")
        self.focus_get()

    def export_image(self):
        file_name = os.path.splitext(self.content_handler.current_files[self.content_handler.current_index])[0]
        dialog_result = filedialog.asksaveasfile(mode='w', initialfile=file_name, defaultextension=".png")
        if dialog_result is None:
            # Cancelled
            return
        try:
            cv2.imwrite(dialog_result.name, self.display_image)
        except cv2.error as e:
            msg_popup = MessageBoxPopup(e)
            msg_popup.wait()

    def export_fixed_video(self, file_path):
        # Check video extension
        file_extension = os.path.splitext(file_path)[-1]
        if file_extension != ".mp4":
            msg_popup = MessageBoxPopup(f"Unsupported file extension: {file_extension}")
            msg_popup.wait()
            return

        # Get video information
        video_position, video_length, video_fps = self.content_handler.get_video_position()
        caps = self.content_handler.content_loaders
        current_methods = self.content_handler.current_methods
        width = int(caps[0].get(cv2.CAP_PROP_FRAME_WIDTH) * len(caps))
        height = int(caps[0].get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Reset video and export
        self.content_handler.set_video_position(0)
        writer = VideoWriter(output_path=file_path, width=width, height=height, fps=video_fps)

        # Create progress bars
        pbar_popup = ProgressBarPopup(total=video_length, desc="Exporting video...")
        pbar_tqdm = tqdm(total=video_length, desc="Exporting video...")

        # Write file
        while True:
            ret, images = self.content_handler.read_frames()
            if not ret:
                break

            # Puts text in place
            title_positions = [image_utils.TextPosition.TOP_LEFT] * len(current_methods)
            for image, title, title_pos in zip(images, current_methods, title_positions):
                image_utils.put_text(image, title, title_pos)

            writer.write_image(np.hstack(images))

            # Update progress bars
            pbar_popup.update_widget(1)
            pbar_tqdm.update(1)

        writer.release()
        pbar_popup.destroy()

        # Reset video back to original state
        self.content_handler.set_video_position(video_position)

    def on_copy_image(self, event: Optional[tkinter.Event] = None) -> None:
        """
        Saves currently displayed image to clipboard, can be pasted elsewhere.
        :param event: Tkinter event, passed by self.bind.
        :return: None
        """
        if hasattr(self, "display_image"):
            image_utils.image_to_clipboard(self.display_image)

    def display(self):
        start_time = time.time()

        # Fast loading - Activates if change file button is held repeatedly (a, d, <, > keys)
        # Prevents very long load times when has many videos/images to load and want to use buttons to switch quickly
        if self.fast_load_checker.check(threshold_ms=self.configurations["Display"]["fast_loading_threshold_ms"]) and self.app_status.STATE == VCState.UPDATE_FILE:
            cap = file_reader.read_media_file(self.content_handler.get_paths()[0])
            ret, display_image = cap.read()
            self.display_handler.update_image(display_image, self.configurations["Display"]["interpolation_type"])
            self.after(self.get_sleep_time_ms(start_time), self.display)
            return

        # Read the files when changing method or files.
        if self.app_status.STATE == VCState.UPDATE_FILE or self.app_status.STATE == VCState.UPDATE_METHOD:
            self.title(self.content_handler.get_title())
            self.content_handler.load_files(self.content_handler.get_paths())
            self.display_handler.mouse_position = (0, 0)
            self.app_status.STATE = VCState.UPDATED
            self.on_pause(paused=False)
            self.zoom_manager.reset()

        # Show or hide video controller
        if self.content_handler.has_video():
            if len(self.video_controls.grid_info()) == 0:
                self.video_controls.grid(row=2, column=0, pady=2)
        else:
            if len(self.video_controls.grid_info()) != 0:
                self.video_controls.grid_forget()

        # Set video controller
        if self.content_handler.has_video() and not self.app_status.VIDEO_PAUSED:
            self.video_controls.update_widget(*self.content_handler.get_video_position())

        # Read images/videos
        if not self.content_handler.has_video():
            ret, images = self.content_handler.read_frames()
        elif self.app_status.VIDEO_PAUSED:
            images = self.images
        else:
            ret, images = self.content_handler.read_frames()
            if not ret:
                self.on_pause(paused=True)
                images = self.images
            else:
                self.images = images

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
            self.cropped_image = self.zoom_manager.crop_regions(images, self.configurations["Zoom"]["interpolation_type"])
            self.output_image = self.zoom_manager.draw_regions(comparison_img, num_images=len(images))

        elif self.app_status.MODE == VCModes.Specific:
            method_idx = current_methods.index(self.app_status.METHOD)
            comparison_img = images[method_idx]
            self.cropped_image = self.zoom_manager.crop_regions([comparison_img], self.configurations["Zoom"]["interpolation_type"])
            self.output_image = self.zoom_manager.draw_regions(comparison_img)
        else:
            m_x, m_y = self.display_handler.mouse_position
            i_y, i_x = images[0].shape[:2]
            if 0 <= m_x < i_x and 0 <= m_y < i_y:
                comparison_img = image_utils.merge_multiple_images(images[:4], self.display_handler.mouse_position)
                self.cropped_image = self.zoom_manager.crop_regions([comparison_img], self.configurations["Zoom"]["interpolation_type"])
                self.output_image = self.zoom_manager.draw_regions(comparison_img)
            elif self.app_status.STATE == VCState.UPDATE_MODE:
                self.app_status.STATE = VCState.UPDATED
                self.display_handler.mouse_position = (0, 0)

        # Cropped image is displayed below original image
        display_image = np.vstack([self.output_image, self.cropped_image]) if self.cropped_image is not None else self.output_image

        # For copy/save functionality
        self.display_image = display_image

        # For exporting video (custom)
        if self.video_writer is not None:
            self.handle_custom_video_writing(display_image)

        self.display_handler.update_image(display_image, self.configurations["Display"]["interpolation_type"])

        # Decide how long to sleep before calling next cycle of self.display
        self.after(self.get_sleep_time_ms(start_time), self.display)

    def reset_video_writer(self):
        self.video_writer.release()
        self.video_writer = None
        self.video_writer_options = {}
        self.cb_widget.toggle_export_button()

    def handle_custom_video_writing(self, img_to_write):
        # Draw Cursor
        cv2.circle(img_to_write, self.display_handler.mouse_position, 4, (0, 0, 0), -1)
        cv2.circle(img_to_write, self.display_handler.mouse_position, 2, (255, 255, 255), -1)

        if self.content_handler.has_video():
            video_position, video_length, _ = self.content_handler.get_video_position()

            # Write video frame on image
            if self.video_writer_options.get("render_playback_bar", None):
                h, w = img_to_write.shape[: 2]
                cv2.line(img_to_write, (0, h - 2), (w, h - 2), (0, 0, 0), 5)
                cv2.line(img_to_write, (0, h - 2), (int(w * video_position / video_length), h - 2), (255, 255, 255), 3)

            # Show playback progress on video
            if self.video_writer_options.get("render_video_frames_num", None):
                image_utils.put_text(img_to_write, str(video_position), image_utils.TextPosition.MIDDLE_LEFT, fg_color=(255, 255, 255))
                image_utils.put_text(img_to_write, str(video_length), image_utils.TextPosition.MIDDLE_RIGHT, fg_color=(255, 255, 255))

        ret = self.video_writer.write_image(img_to_write)
        if not ret:
            self.reset_video_writer()
            msg_popup = MessageBoxPopup("Video writing stopped because image size has changed")
            msg_popup.wait()

        # Inform user that it is still recording
        image_utils.put_text(img_to_write, "Recording", image_utils.TextPosition.TOP_CENTER, fg_color=(0, 0, 255))

    def get_sleep_time_ms(self, start_time: float):
        """
        Time to sleep = 500ms if its in background and reduce_cpu_usage_in_background is True.

        Otherwise, it will calculate the time to sleep to achieve the desired fps.

        Desired fps depends on whether it is doing an image or video comparison. If displaying images, it uses max_fps.
        For videos, it depends on the video fps and video playback rate.

        :param start_time: time.time() from start of self.display
        :return: Time to sleep in ms
        """
        in_background = is_window_in_background(self)
        if in_background and self.configurations["Functionality"]["reduce_cpu_usage_in_background"]:
            return 500

        # Calculate T = 1/f, time budget for video playback
        target_fps = self.configurations["Functionality"]["max_fps"]
        if self.content_handler.has_video():
            target_fps = self.content_handler.get_video_position()[2] * self.app_status.VIDEO_PLAYBACK_RATE
            target_fps = min(target_fps, self.configurations["Functionality"]["max_fps"])
        target_period_s = 1.0 / target_fps

        # Find offset time
        actual_fps = self.video_controls.get_playback_fps()
        offset_period_s = (1 / actual_fps) - (1 / target_fps)
        offset_period_s = np.clip(offset_period_s, -0.01, 0.01)

        # Find time to sleep such that program achieves desired fps
        time_elapsed_s = time.time() - start_time
        time_to_sleep_ms = (target_period_s - time_elapsed_s - offset_period_s) * 1000
        time_to_sleep_ms = max(1, int(round(time_to_sleep_ms, 0)))

        # self.after does not accept values < 1
        assert time_to_sleep_ms >= 1, "Sleep time cannot be below 1"

        return time_to_sleep_ms
