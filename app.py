import enum
import scrollviewer
from PIL import Image
import os
import cv2
import glob
import argparse
import platform
import numpy as np
import customtkinter
import image_utils


class AppStatus(enum.Enum):
    UPDATE_MODE = enum.auto()
    UPDATE_FILE = enum.auto()
    UPDATE_METHOD = enum.auto()
    UPDATED = enum.auto()


class ModeMethodsControllerFrame(customtkinter.CTkFrame):
    def __init__(self, root, methods, files, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root = root
        self.methods = methods
        self.curr_methods = list(methods)
        self.files = files

        # Maintains the selected method & function for the app
        self.internal_state = {}
        self._reset_internal_state()
        self.update_status = AppStatus.UPDATE_FILE

        # For changing selected files & methods
        # TODO: Hardcoded source folder
        self.scroll_viewer = scrollviewer.ScrollViewer(os.path.join(root, "source"), files, self.on_specify_index, master=self)
        self.scroll_viewer.grid(row=0, column=0, columnspan=3)
        change_method_file_frame = customtkinter.CTkFrame(master=self)
        button_prev = customtkinter.CTkButton(master=change_method_file_frame, text="<", command=self.on_prev, width=30, height=25)
        button_prev.grid(row=1, column=0, padx=5)
        button_method = customtkinter.CTkButton(master=change_method_file_frame, text="Method:", command=self.on_select_methods, width=50, height=25)
        button_method.grid(row=1, column=1, padx=5)
        button_select_specific = customtkinter.CTkButton(master=change_method_file_frame, text="Idx:", command=self.on_specify_index, width=50, height=25)
        button_select_specific.grid(row=1, column=2, padx=5)
        button_next = customtkinter.CTkButton(master=change_method_file_frame, text=">", command=self.on_next, width=30, height=25)
        button_next.grid(row=1, column=3, padx=5)
        change_method_file_frame.grid(row=1, column=0)
        self.current_index = 0

        # For controlling modes
        self.modes = ["Compare", "Concat", "Specific"]
        modes_frame = customtkinter.CTkFrame(master=self)
        self.s_button_modes = customtkinter.CTkSegmentedButton(master=modes_frame, values=self.modes, command=lambda mode: self.on_change_mode(mode, self.curr_methods[0]))
        self.s_button_modes.pack()
        modes_frame.grid(row=1, column=1)

        # For changing to 'Specific' mode
        self.methods_frame = customtkinter.CTkFrame(master=self)
        self.s_button_methods = customtkinter.CTkSegmentedButton(master=self.methods_frame, values=self.curr_methods, command=lambda value: self.on_change_mode("Specific", value))
        self.s_button_methods.pack()

        self.bind_hotkeys()

    def _reset_internal_state(self):
        self.internal_state = {"mode": "Compare", "method": "None"}

    def get_window_title(self):
        title = f"[{self.current_index}/{len(self.files)}] {self.files[self.current_index]}"
        return title

    def get_paths(self):
        output_paths = []
        # TODO: Optimize. I think this is a O(n^2) method, if we use dict to map could reduce to O(n)
        for method in self.curr_methods:
            incomplete_path = os.path.join(self.root, method, self.files[self.current_index])
            completed_paths = glob.glob(incomplete_path + ".*")
            assert len(completed_paths) == 1, completed_paths
            output_paths.append(completed_paths[0])

        return output_paths

    def on_change_mode(self, mode, method):
        if mode == "Compare":
            self.methods_frame.grid_remove()
        elif mode == "Concat":
            self.methods_frame.grid_remove()
        else:
            if method == self.internal_state["method"] and self.internal_state["mode"] == "Specific":
                self.methods_frame.grid_remove()
                self.s_button_modes.set("Compare")
                self._reset_internal_state()
                return
            else:
                self.s_button_modes.set("Specific")
                self.s_button_methods.set(method)
                self.methods_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        self.internal_state = {"mode": mode, "method": method}
        self.update_status = AppStatus.UPDATE_MODE

    def on_specify_index(self, index=None):
        if index is None:
            dialog = customtkinter.CTkInputDialog(text="Enter an index:", title="Specify file index")
            # Prevent user interaction
            dialog.grab_set()
            dialog_str = dialog.get_input()

            if dialog_str == "" or dialog_str is None:
                print("Empty String")
                return
            try:
                value = int(dialog_str)
            except ValueError:
                print(f"Invalid option: {dialog_str}")
                return
        else:
            value = index
        if 0 <= value < len(self.files):
            self.current_index = value
        else:
            print(f"Value out of range: {value}")
        self.scroll_viewer.highlight_selected(self.current_index)
        self.update_status = AppStatus.UPDATE_FILE

    def on_prev(self):
        self.current_index = max(0, self.current_index - 1)
        self.scroll_viewer.highlight_selected(self.current_index)
        self.update_status = AppStatus.UPDATE_FILE

    def on_next(self):
        self.current_index = min(len(self.files) - 1, self.current_index + 1)
        self.scroll_viewer.highlight_selected(self.current_index)
        self.update_status = AppStatus.UPDATE_FILE

    def on_select_methods(self):
        def set_new_methods(new_methods):
            if len(new_methods) < 2:
                print(f"Please select more than 2 methods")
                return
            self.curr_methods = new_methods
            self.s_button_modes.set("Compare")
            self.methods_frame.grid_remove()
            self._reset_internal_state()
            self.s_button_methods.configure(values=new_methods, command=lambda value: self.on_change_mode(self.modes[2], value))
            self.bind_hotkeys()
            self.update_status = AppStatus.UPDATE_FILE.UPDATE_METHOD

        MethodsSelectionPopUp(all_methods=self.methods, current_methods=self.curr_methods, app_callback=set_new_methods)

    def bind_hotkeys(self):
        self.master.bind("a", lambda event: self.on_prev())
        self.master.bind("d", lambda event: self.on_next())

        for i in range(10):
            self.master.unbind(str(i))
        for i in range(len(self.curr_methods)):
            self.master.bind(str(i + 1), lambda event: self.on_change_mode("Specific", self.curr_methods[int(event.keysym) - 1]))


class MethodsSelectionPopUp(customtkinter.CTkToplevel):
    def __init__(self, all_methods, current_methods, app_callback):
        super().__init__()
        self.app_callback = app_callback

        reset_button = customtkinter.CTkButton(master=self, text="Reset", command=self._on_reset_pressed)
        reset_button.pack(padx=5, pady=5)
        ok_button = customtkinter.CTkButton(master=self, text="Confirm", command=self._on_ok_pressed)
        ok_button.pack(padx=5, pady=5)

        # Sort by current methods then remainder
        sorted_methods = list(current_methods)
        method_set = set(current_methods)
        for method in all_methods:
            if method not in method_set:
                sorted_methods.append(method)

        self.checkboxes = []
        for i, method_name in enumerate(sorted_methods):
            checkbox = customtkinter.CTkCheckBox(master=self, text=method_name, command=self._on_checkbox_checked, onvalue=i + 1, offvalue=0)
            checkbox.pack()
            if i < len(current_methods):
                checkbox.select()
            self.checkboxes.append(checkbox)

        # Prevent user interaction
        self.grab_set()

        self.mainloop()

    def _on_checkbox_checked(self):
        new_list = [checkbox for checkbox in self.checkboxes if checkbox.get()]
        remaining = [checkbox for checkbox in self.checkboxes if not checkbox.get()]
        remaining.sort(key=lambda checkbox: checkbox.cget("text"))
        new_list += remaining
        for checkbox in new_list:
            checkbox.pack_forget()
        for checkbox in new_list:
            checkbox.pack()
        self.checkboxes = new_list

    def _on_reset_pressed(self):
        self.checkboxes.sort(key=lambda checkbox: checkbox.cget("text"))
        for checkbox in self.checkboxes:
            checkbox.pack_forget()
        for checkbox in self.checkboxes:
            checkbox.pack()
        for checkbox in self.checkboxes:
            checkbox.deselect()

    def _on_ok_pressed(self):
        methods_to_display = [checkbox.cget("text") for checkbox in self.checkboxes if checkbox.get()]
        self.app_callback(methods_to_display)
        self.destroy()


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


class ContentComparisonApp(customtkinter.CTk):
    def __init__(self, root, src_folder_name="source"):
        super().__init__()
        # configure window
        methods, files = self.get_comparison_methods_files(root, src_folder_name)
        self.mode_methods_handler = ModeMethodsControllerFrame(root, methods, files, master=self)
        self.mode_methods_handler.grid(row=0, column=0)
        self.video_controller = customtkinter.CTkSlider(master=self, from_=0, to=100, width=720, command=self._on_video_controller_updated)
        self.display_handler = DisplayWindowFrame(self)
        self.display_handler.grid(row=2, column=0)

        self.content_loaders = None
        self.paused = False
        self.images = None
        self.bind("<space>", self._on_spacebar)

    def _on_video_controller_updated(self, value):
        video_position = None
        for cap in self.content_loaders:
            if not isinstance(cap, cv2.VideoCapture):
                continue

            if video_position is None:
                video_position = int(value / 100 * cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.set(cv2.CAP_PROP_POS_FRAMES, video_position)
            else:
                # Weird bug when setting video position. If no offset is done, will be out of sync
                # Seems like only occurs for larger frame positions. e.g. 0.2 * cv2.CAP_PROP_FRAME_COUNT
                cap.set(cv2.CAP_PROP_POS_FRAMES, video_position + 1)

    def _on_spacebar(self, event):
        self.paused = not self.paused

    @staticmethod
    def get_comparison_methods_files(root, src_folder_name):
        # Contains method name (folder name)
        methods = [folder for folder in os.listdir(root) if folder[0] != "."]
        if src_folder_name in methods:
            methods.insert(0, methods.pop(methods.index(src_folder_name)))

        assert len(methods) > 1, "Need more than 1 folder for comparison"

        # Finding common files for comparison, should have the same filename (without extension)
        common_files = None
        for folder in methods:
            folder_path = os.path.join(root, folder)
            file_paths = [os.path.splitext(file_path)[0] for file_path in os.listdir(folder_path) if file_path[0] != "."]
            common_files = set(file_paths) if common_files is None else common_files.intersection(set(file_paths))

        # Contains files with same names across all sub-directories for comparison
        assert common_files, "No files in common"
        common_files = list(common_files)
        common_files.sort()

        return methods, common_files

    def display(self):
        # Read the files when changing method or files.
        update_status = self.mode_methods_handler.update_status
        if update_status == AppStatus.UPDATE_FILE or update_status == AppStatus.UPDATE_METHOD:
            self.title(self.mode_methods_handler.get_window_title())
            self.content_loaders = []
            for file in self.mode_methods_handler.get_paths():
                extension = os.path.splitext(file)[-1].lower()
                if extension in {".jpg", ".png", ".hdr"}:
                    self.content_loaders.append(ImageCapture(file))
                elif extension in {".mp4"}:
                    self.content_loaders.append(cv2.VideoCapture(file))
                else:
                    raise NotImplementedError(f"Ext not supported: {extension} for file {file}")
            self.display_handler.mouse_position = (0, 0)
            self.mode_methods_handler.update_status = AppStatus.UPDATED
            self.paused = False

        # TODO: Add function for image manipulation
        if not self.paused:
            rets, images = [], []
            slider_set = False
            for cap in self.content_loaders:
                if isinstance(cap, cv2.VideoCapture) and not slider_set:
                    video_position = cap.get(cv2.CAP_PROP_POS_FRAMES)
                    video_length = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    self.video_controller.set(video_position / video_length * 100)
                    if len(self.video_controller.grid_info()) == 0:
                        self.video_controller.grid(row=1, column=0)
                    slider_set = True
                ret, frame = cap.read()
                rets.append(ret)
                images.append(frame)
            if not slider_set:
                self.video_controller.grid_forget()

            if not all(rets):
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

        if mode == "Compare":
            title_positions = [image_utils.TextPosition.TOP_LEFT,
                               image_utils.TextPosition.TOP_RIGHT,
                               image_utils.TextPosition.BTM_LEFT,
                               image_utils.TextPosition.BTM_RIGHT]
        elif mode == "Concat":
            title_positions = [image_utils.TextPosition.TOP_LEFT] * len(current_methods)
        elif mode == "Specific":
            title_positions = [image_utils.TextPosition.TOP_LEFT] * len(current_methods)
        else:
            raise NotImplementedError(f"Load image for mode not added: {mode}")

        # Load and resize the images
        labelled_imgs = []
        for image, title, title_pos in zip(images, current_methods, title_positions):
            image = image_utils.put_text(image, title, title_pos)
            labelled_imgs.append(image)
        images = labelled_imgs

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


class ImageCapture:
    """
    TODO: Handle HDR Reading too later?
    """
    def __init__(self, image_path):
        self.image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    def read(self):
        if self.image is None:
            return False, None
        return True, self.image.copy()


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
