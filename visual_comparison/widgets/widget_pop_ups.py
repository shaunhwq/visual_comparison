import os
import time
from typing import List, Any

import tkinter.ttk as ttk
import tkinter
from tkinter import filedialog
import customtkinter

from ..utils import validate_number_str, shift_widget_to_root_center


__all__ = [
    "MultiSelectPopUpWidget",
    "FilterRangePopup",
    "DataSelectionPopup",
    "MessageBoxPopup",
    "GetNumberBetweenRangePopup",
    "RootSelectionPopup",
    "ExportVideoPopup",
    "ExportSelectionPopup",
    "ProgressBarPopup"
]


# https://stackoverflow.com/questions/67543314/why-are-the-digit-values-in-the-tkinter-items-integers-and-not-strings-even-when
def _convert_stringval(value):
    """Converts a value to, hopefully, a more appropriate Python object."""
    if hasattr(value, 'typename'):
        value = str(value)
        try:
            value = int(value)
        except (ValueError, TypeError):
            pass
    return value


ttk._convert_stringval = _convert_stringval


class MultiSelectPopUpWidget(customtkinter.CTkToplevel):
    def __init__(self, all_options, current_options):
        """
        :param all_options: All possible options
        :param current_options: Currently selected options
        """
        super().__init__()
        reset_button = customtkinter.CTkButton(master=self, text="Reset", command=self._on_reset_pressed)
        reset_button.pack(padx=5, pady=5)
        ok_button = customtkinter.CTkButton(master=self, text="Confirm", command=self._on_ok_pressed)
        ok_button.pack(padx=5, pady=5)

        # Sort by current methods then remainder
        sorted_methods = list(current_options)
        method_set = set(current_options)
        for method in all_options:
            if method not in method_set:
                sorted_methods.append(method)

        self.checkboxes = []
        for i, method_name in enumerate(sorted_methods):
            checkbox = customtkinter.CTkCheckBox(master=self, text=method_name, command=self._on_checkbox_checked, onvalue=i + 1, offvalue=0)
            checkbox.pack()
            if i < len(current_options):
                checkbox.select()
            self.checkboxes.append(checkbox)

        self.return_value = []
        self.cancelled = True

        self.grab_set()  # make other windows not clickable
        self.update_idletasks()
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

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
        self.return_value = methods_to_display
        self.cancelled = False
        self.destroy()

    def get_input(self):
        self.master.wait_window(self)
        return self.cancelled, self.return_value


class FilterRangePopup(customtkinter.CTkToplevel):
    def __init__(self, title, values):
        super().__init__()
        self.values = values

        self.cancelled = True
        self.return_value = []

        self.geometry("345x200")
        self.title("Specify Range/Value")

        self.error_label = customtkinter.CTkLabel(self, text_color="red", text="", height=25)
        self.error_label.grid(row=0, column=0, sticky="nsew")
        title_label = customtkinter.CTkLabel(self, text=title)
        title_label.grid(row=1, column=0, sticky="nsew")

        tabview = customtkinter.CTkTabview(self, height=100, width=300)
        tabview.grid(row=2, column=0, padx=20, pady=(5, 20), sticky="nsew")
        tabview.columnconfigure(0, weight=1)
        tabview.add("Range")
        tabview.add("Equals")
        tabview.tab("Range").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        tabview.tab("Equals").grid_columnconfigure(0, weight=1)

        range_tab = tabview.tab("Range")
        self.lower_text_box = customtkinter.CTkEntry(range_tab, placeholder_text="Lower bound")
        self.lower_text_box.grid(row=0, column=0)
        self.upper_text_box = customtkinter.CTkEntry(range_tab, placeholder_text="Upper bound")
        self.upper_text_box.grid(row=0, column=1)
        range_ok_button = customtkinter.CTkButton(range_tab, command=lambda: self.on_ok_pressed("Range"), text="Ok")
        range_ok_button.grid(row=2, column=0, columnspan=2, pady=5)

        equals_tab = tabview.tab("Equals")
        self.equals_text_box = customtkinter.CTkEntry(equals_tab, placeholder_text="Equals to")
        self.equals_text_box.grid(row=0, column=0)
        equals_ok_button = customtkinter.CTkButton(equals_tab, command=lambda: self.on_ok_pressed("Equals"), text="Ok")
        equals_ok_button.grid(row=2, column=0, columnspan=2, pady=5)

        self.grab_set()  # make other windows not clickable
        self.update_idletasks()
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

    def on_ok_pressed(self, tab):
        if tab == "Range":
            l_ret, lower_val = validate_number_str(self.lower_text_box.get(), desired_type=float)
            u_ret, upper_val = validate_number_str(self.upper_text_box.get(), desired_type=float)
            if not (l_ret and u_ret):
                self.error_label.configure(text="Error parsing values")
                return
            if lower_val > upper_val:
                self.error_label.configure(text="Lower > Upper")
                return
            selected_idxs = [idx for idx, value in enumerate(self.values) if lower_val <= float(value) <= upper_val]
        elif tab == "Equals":
            ret, equals_val = validate_number_str(self.equals_text_box.get(), desired_type=float)
            if not ret:
                self.error_label.configure(text="Error parsing values")
                return
            selected_idxs = [idx for idx, value in enumerate(self.values) if equals_val == float(value)]
        else:
            raise NotImplementedError("Invalid tab option")

        self.return_value = selected_idxs
        self.cancelled = False
        self.destroy()

    def get_input(self):
        self.master.wait_window(self)
        return self.cancelled, self.return_value


class FilterTextPopup(customtkinter.CTkToplevel):
    def __init__(self, display_text, strings_to_filter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Filter Text")

        self.strings_to_filter = strings_to_filter
        self.cancelled = True
        self.return_values = []

        display_label = customtkinter.CTkLabel(self, text=display_text)
        display_label.grid(row=0, column=0)

        selection_frame = customtkinter.CTkFrame(self)
        label = customtkinter.CTkLabel(selection_frame, text="Select where")
        label.grid(row=0, column=0)
        condition = ["contains", "does not contain", "matches"]
        self.condition_combo_box = customtkinter.CTkComboBox(selection_frame, values=condition)
        self.condition_combo_box.grid(row=0, column=1)
        self.entry_box = customtkinter.CTkEntry(selection_frame)
        self.entry_box.grid(row=0, column=2)
        selection_frame.grid(row=1, column=0)

        confirm_button = customtkinter.CTkButton(self, text="Confirm", command=self.on_confirm)
        confirm_button.grid(row=2, column=0)

        self.grab_set()  # make other windows not clickable
        self.update_idletasks()
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

    def on_confirm(self):
        condition = self.condition_combo_box.get()
        text = self.entry_box.get()

        if condition == "contains":
            selected_idxs = [idx for idx, s in enumerate(self.strings_to_filter) if text in s]
        elif condition == "does not contain":
            selected_idxs = [idx for idx, s in enumerate(self.strings_to_filter) if text not in s]
        elif condition == "matches":
            selected_idxs = [idx for idx, s in enumerate(self.strings_to_filter) if text == s]
        else:
            query_string = f"Select where {text} {condition} file"
            raise NotImplementedError(f"'{query_string}' operation not implemented")

        self.return_values = selected_idxs
        self.cancelled = False
        self.destroy()

    def get_input(self):
        self.master.wait_window(self)
        return self.cancelled, self.return_values


class DataSelectionPopup(customtkinter.CTkToplevel):
    def __init__(self, data: List[List], column_titles: List[str], text_width=400, number_width=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = list(data)
        self.column_titles = column_titles
        self.data_types = [type(val) for val in data[0]]

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        tree_frame = customtkinter.CTkFrame(self)
        # Create Tree for display
        tree = ttk.Treeview(tree_frame, columns=self.column_titles, show='headings')
        tree.grid(row=0, column=0, sticky="nsew")
        tree.columnconfigure(0, weight=1)
        for col_idx, (column, data_type) in enumerate(zip(self.column_titles, self.data_types)):
            tree.heading(column, text=column, command=lambda col_idx=col_idx: self.sort_rows(int(col_idx)))
            col_width = text_width if data_type is str else number_width
            tree.column(col_idx, width=col_width)
        # Create scrollbar
        vertical_scroll = customtkinter.CTkScrollbar(tree_frame, orientation="vertical", command=tree.yview)
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=vertical_scroll.set)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)

        self.tree = tree
        self.tree_add(list(data))
        self.refresh_title()
        self.col_sort_reverse = [False] * len(self.column_titles)

        # Feature buttons
        option_frame = customtkinter.CTkFrame(self)
        remove_row_button = customtkinter.CTkButton(option_frame, text="Remove Row", command=self.on_remove_row, height=25, width=75)
        remove_row_button.grid(row=1, column=0, padx=2, rowspan=2)
        col_option_label = customtkinter.CTkLabel(option_frame, text="Filter By:", height=25)
        col_option_label.grid(row=0, column=1, padx=2)
        self.col_options = customtkinter.CTkOptionMenu(option_frame, values=self.column_titles, command=self.filter_options, height=25, width=75)
        self.col_options.grid(row=1, column=1, padx=2)

        reset_button = customtkinter.CTkButton(option_frame, text="Reset", command=self.on_reset, height=25, width=75)
        reset_button.grid(row=1, column=2, padx=2, rowspan=2)
        option_frame.grid(row=1, column=0, pady=5, padx=5)

        confirm_button = customtkinter.CTkButton(self, text="Confirm", command=self.on_confirm, height=25)
        confirm_button.grid(row=2, column=0, pady=(0, 5))

        self.return_value = []
        self.cancelled = True

        self.grab_set()  # make other windows not clickable
        self.update_idletasks()
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

    def child_values(self, child):
        return self.tree.item(child)["values"]

    def tree_remove(self, children=None):
        if children is None:
            for child in self.tree.get_children():
                self.tree.delete(child)
        else:
            for child in children:
                self.tree.delete(child)

    def tree_add(self, items: List[List[Any]], position=tkinter.END):
        for item in items:
            self.tree.insert("", position, values=item)

    def filter_options(self, column):
        column_index = self.column_titles.index(column)
        data_type = self.data_types[column_index]
        data_to_filter = [self.child_values(child)[column_index] for child in self.tree.get_children()]

        self.grab_release()
        if data_type is int or data_type is float:
            popup = FilterRangePopup(f"Filtering {column}:", data_to_filter)
            is_cancelled, idxs = popup.get_input()
        elif data_type is str:
            popup = FilterTextPopup(f"Column: {column}", data_to_filter)
            is_cancelled, idxs = popup.get_input()
        else:
            raise NotImplementedError(f"Filtering option for data type {data_type} is not implemented")
        self.grab_set()

        if is_cancelled:
            return

        keep_idxs = set(idxs)
        idx_to_remove = [c for idx, c in enumerate(self.tree.get_children()) if idx not in keep_idxs]
        self.tree_remove(idx_to_remove)
        self.refresh_title()

    def sort_rows(self, col_idx):
        self.col_sort_reverse[col_idx] = not self.col_sort_reverse[col_idx]
        rows = [self.child_values(child) for child in self.tree.get_children()]
        data_type = self.data_types[col_idx]
        rows.sort(key=lambda row: data_type(row[col_idx]), reverse=self.col_sort_reverse[col_idx])
        self.tree_remove()
        self.tree_add(rows)

    def on_remove_row(self):
        self.tree_remove(self.tree.selection())
        self.refresh_title()

    def on_confirm(self):
        for child in self.tree.get_children():
            self.return_value.append([data_type(item) for data_type, item in zip(self.data_types, self.child_values(child))])
        self.cancelled = False
        self.destroy()

    def on_reset(self):
        self.tree_remove()
        self.tree_add(self.data)
        self.col_sort_reverse = [False] * len(self.column_titles)
        self.refresh_title()

    def refresh_title(self):
        self.title(f"Data Selection. Num Items: {len(self.tree.get_children())}")

    def get_input(self):
        self.master.wait_window(self)
        return self.cancelled, self.return_value


class MessageBoxPopup(customtkinter.CTkToplevel):
    def __init__(self, message, title="Warning", display_time_ms=3000, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(title)

        label = customtkinter.CTkLabel(self, wraplength=300, text=message)
        label.grid(row=0, column=0, padx=20, pady=20)
        self.close_button = customtkinter.CTkButton(self, command=self.destroy)
        self.close_button.grid(row=1, column=0, pady=(0, 20))

        self.display_time_ms = display_time_ms
        self.start_time = time.time()
        self.button_update_time_ms = 100

        self.after(self.button_update_time_ms, self.update_close_button)
        self.after(display_time_ms, self.destroy)
        self.bind("<FocusOut>", self._on_lose_focus)

        self.update_idletasks()
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

    def _on_lose_focus(self, event):
        self.destroy()

    def update_close_button(self):
        time_left_ms = self.display_time_ms - (time.time() - self.start_time) * 1000
        time_left_s = int(time_left_ms / 1000) + 1
        self.close_button.configure(text=f"Closing ({time_left_s}s)")
        self.after(self.button_update_time_ms, self.update_close_button)

    def wait(self):
        self.master.wait_window(self)
        self.master.focus_set()


class GetNumberBetweenRangePopup(customtkinter.CTkToplevel):
    def __init__(self, text, title, desired_type, lower_bound=float("-inf"), upper_bound=float("inf"), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(title)
        if not (desired_type is int or desired_type is float):
            raise ValueError("desired_type should be either int or float")

        self.desired_type = desired_type
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

        prompt_label = customtkinter.CTkLabel(self, text=text, wraplength=300)
        prompt_label.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        self.entry = customtkinter.CTkEntry(self)
        self.entry.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20))
        confirm_button = customtkinter.CTkButton(self, text="Confirm", command=self.on_confirm)
        confirm_button.grid(row=2, column=0, padx=20, pady=(0, 20))
        cancel_button = customtkinter.CTkButton(self, text="Cancel", command=self.destroy)
        cancel_button.grid(row=2, column=1, padx=(0, 20), pady=(0, 20))

        self.return_value = None
        self.cancelled = True

        self.grab_set()  # make other windows not clickable
        self.update_idletasks()
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

    def on_confirm(self):
        user_input = self.entry.get()
        ret, value = validate_number_str(user_input, desired_type=self.desired_type)

        if not ret:
            self.grab_release()
            msg_popup = MessageBoxPopup(f"Unable to cast '{user_input}' to {self.desired_type.__name__}")
            msg_popup.wait()
            self.grab_set()
            return

        # Check valid index
        if not (self.lower_bound <= value <= self.upper_bound):
            self.grab_release()
            msg_popup = MessageBoxPopup(f"Index {value} not in range [{self.lower_bound}, {self.upper_bound}]")
            msg_popup.wait()
            self.grab_set()
            return

        self.return_value = value
        self.cancelled = False
        self.destroy()

    def get_input(self):
        self.master.wait_window(self)
        return self.cancelled, self.return_value


class RootSelectionPopup(customtkinter.CTkToplevel):
    def __init__(self, root=None, selected_folder=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.title("Select root folder and folder for preview")

        tree_frame = customtkinter.CTkFrame(self, width=500)
        # Create Tree for display
        tree = ttk.Treeview(tree_frame, columns=["column"], show='headings')
        tree.heading("column", text="Click To Select Root Folder", command=self.on_select_clicked)
        tree.column("column", width=500)
        tree.columnconfigure(0, weight=1)
        tree.grid(row=0, column=0, sticky="nsew")
        self.display_tree = tree

        # Create scrollbar
        vertical_scroll = customtkinter.CTkScrollbar(tree_frame, orientation="vertical", command=tree.yview)
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=vertical_scroll.set)
        tree_frame.grid(row=0, column=0, sticky="nsew")

        tree_frame.columnconfigure(0, weight=1)

        confirm_button = customtkinter.CTkButton(self, text="Confirm", command=self.on_confirm)
        confirm_button.grid(row=1, column=0, padx=20, pady=20)

        self.cancelled = True
        self.return_value = []

        self.grab_set()  # make other windows not clickable
        self.update_idletasks()
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

        if selected_folder is not None and root is None:
            self.create_popup(f"Specified folder '{selected_folder}' without specifying root. Ignoring...")
        if root is not None:
            self.on_select_clicked(root, selected_folder)

    def on_select_clicked(self, desired_dir=None, selected_folder=None):
        # Get desired directory
        if desired_dir is None:
            current_folder = self.display_tree.heading("column")['text']
            ask_dir_args = dict(initialdir=current_folder) if os.path.isdir(current_folder) else {}
            desired_dir = filedialog.askdirectory(**ask_dir_args)
        # Check desired sub dir
        if desired_dir == "":
            return
        if not os.path.isdir(desired_dir):
            self.create_popup(f"Path must point to root dir: '{desired_dir}'")
            return

        # Get Sub folders
        sub_folders = [folder for folder in os.listdir(desired_dir) if os.path.isdir(os.path.join(desired_dir, folder))]
        # Check sub folders
        if len(sub_folders) == 0:
            self.create_popup("No sub folders found. Search again")
            return

        # Set display to match selection
        self.display_tree.heading("column", text=desired_dir)
        for child in self.display_tree.get_children():
            self.display_tree.delete(child)
        for folder in sub_folders:
            self.display_tree.insert("", tkinter.END, values=[folder])
            if selected_folder == folder:
                self.display_tree.selection_add(self.display_tree.get_children()[-1])

        if selected_folder is None:
            self.display_tree.selection_add(self.display_tree.get_children()[0])

    def on_confirm(self):
        root_folder = self.display_tree.heading("column")['text']
        selected_child = self.display_tree.selection()

        # Check selected options
        if len(selected_child) == 0:
            self.create_popup("Please select a folder to preview")
            return
        if len(selected_child) > 1:
            self.create_popup("Can only preview a single folder")
            return
        if not os.path.isdir(root_folder):
            self.create_popup("Invalid folder selection try again")
            return

        selected_folder_name = self.display_tree.item(selected_child[0])["values"][0]
        self.cancelled = False
        self.return_value = [root_folder, selected_folder_name]
        self.destroy()

    def create_popup(self, text):
        self.grab_release()
        msg_popup = MessageBoxPopup(text)
        msg_popup.wait()
        self.grab_set()

    def get_input(self):
        self.master.wait_window(self)
        return self.cancelled, self.return_value


class ExportVideoPopup(customtkinter.CTkToplevel):
    def __init__(self, file_name, img_width, img_height, video_fps=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.title("File Export Configuration")

        max_length = max(len(file_name), len(os.getcwd()))
        text_width = int(400./55 * max_length) + 25  # Number of pixels for width

        folder_label = customtkinter.CTkLabel(self, width=80, height=25, text="Folder:", anchor="w")
        folder_label.grid(row=0, column=0, pady=(20, 0), padx=10)
        self.folder_button = customtkinter.CTkButton(self, width=text_width, height=25, text=os.getcwd(), command=self.on_change_dir)
        self.folder_button.grid(row=0, column=1, pady=(20, 0), padx=10)

        file_label = customtkinter.CTkLabel(self, width=80, height=25, text="File name:", anchor="w")
        file_label.grid(row=1, column=0, padx=10)
        self.file_name_entry = customtkinter.CTkEntry(self, width=text_width, height=25)
        self.file_name_entry.insert(0, file_name)
        self.file_name_entry.grid(row=1, column=1, padx=10)

        dimensions_label = customtkinter.CTkLabel(self, width=80, height=25, text="Dimensions:", anchor="w")
        dimensions_label.grid(row=2, column=0, padx=10)
        dimensions_text = customtkinter.CTkEntry(self, width=text_width, height=25)
        dimensions_text.insert(0, f"{img_width}(width) x {img_height}(height)")
        dimensions_text.grid(row=2, column=1, padx=10)
        dimensions_text.configure(state="disabled")

        fps_label = customtkinter.CTkLabel(self, width=80, height=25, text="FPS:", anchor="w")
        fps_label.grid(row=3, column=0, padx=10)
        self.fps_entry = customtkinter.CTkEntry(self, width=text_width, height=25)
        self.fps_entry.insert(0, str(video_fps) if video_fps is not None else "Not Applicable")
        self.fps_entry.grid(row=3, column=1, padx=10)

        export_type_label = customtkinter.CTkLabel(self, width=80, height=25, text="Export Type:", anchor="w")
        export_type_label.grid(row=4, column=0, padx=10)
        self.export_options = customtkinter.CTkOptionMenu(self, width=text_width, height=25, values=["Fixed (Concatenated)", "Custom"], command=self.on_export_options_changed)
        self.export_options.grid(row=4, column=1, padx=10)

        other_options_label = customtkinter.CTkLabel(self, width=80, height=25, text="Other Options:", anchor="w")
        other_options_label.grid(row=5, column=0, padx=10)
        self.checkbox_options_frame = customtkinter.CTkFrame(self)
        self.render_video_frames_num_checkbox = customtkinter.CTkCheckBox(self.checkbox_options_frame, text_width // 2, height=25, text="Render Video Frame Num")
        self.render_video_frames_num_checkbox.grid(row=0, column=1)
        self.render_playback_bar_checkbox = customtkinter.CTkCheckBox(self.checkbox_options_frame, text_width // 2, height=25, text="Render Playback Bar")
        self.render_playback_bar_checkbox.grid(row=0, column=2)

        exit_buttons_frame = customtkinter.CTkFrame(self)
        cancel_button = customtkinter.CTkButton(exit_buttons_frame, height=25, width=50, text="Cancel", command=self.destroy)
        cancel_button.grid(row=0, column=0)
        confirm_button = customtkinter.CTkButton(exit_buttons_frame, height=25, width=50, text="Confirm", command=self.on_confirm)
        confirm_button.grid(row=0, column=1)
        exit_buttons_frame.grid(row=6, column=0, columnspan=3, pady=20)

        self.cancelled = True
        self.return_value = {}

        self.grab_set()  # make other windows not clickable
        self.update_idletasks()
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

    def on_export_options_changed(self, value):
        if value == "Custom":
            self.checkbox_options_frame.grid(row=5, column=1, padx=10)
        else:
            self.checkbox_options_frame.grid_forget()

    def on_change_dir(self):
        current_dir = self.folder_button.cget("text")
        desired_path = filedialog.askdirectory(initialdir=current_dir)
        if desired_path != "":
            self.folder_button.configure(text=desired_path)

    def on_confirm(self):
        # Ensure path does not exist
        export_path = os.path.join(self.folder_button.cget("text"), self.file_name_entry.get()) + ".mp4"
        if os.path.exists(export_path):
            self.grab_release()
            msg_popup = MessageBoxPopup("Path exists, please choose another name")
            msg_popup.wait()
            self.grab_set()
            return

        self.cancelled = False
        self.return_value = dict(
            export_path=os.path.join(self.folder_button.cget("text"), self.file_name_entry.get()) + ".mp4",
            export_type=self.export_options.get(),
            export_fps=float(self.fps_entry.get()),
        )

        # If exporting as custom, add options
        if self.export_options.get() == "Custom":
            self.return_value["export_options"] = {
                "render_video_frames_num": self.render_video_frames_num_checkbox.get(),
                "render_playback_bar": self.render_playback_bar_checkbox.get(),
            }

        self.destroy()

    def get_input(self):
        self.master.wait_window(self)
        return self.cancelled, self.return_value


class ExportSelectionPopup(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Export To")

        self.options = customtkinter.CTkSegmentedButton(self, values=["Image", "Video"])
        self.options.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        self.options.set("Image")

        cancel_button = customtkinter.CTkButton(self, height=25, width=50, text="Cancel", command=self.destroy)
        cancel_button.grid(row=1, column=0, padx=20, pady=(0, 20))
        confirm_button = customtkinter.CTkButton(self, height=25, width=50, text="Confirm", command=self.on_confirm)
        confirm_button.grid(row=1, column=1, padx=(0, 20), pady=(0, 20))

        self.cancelled = True
        self.return_value = None

        self.grab_set()  # make other windows not clickable
        self.update_idletasks()
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

    def on_confirm(self):
        self.cancelled = False
        self.return_value = self.options.get()
        self.destroy()

    def get_input(self):
        self.master.wait_window(self)
        return self.cancelled, self.return_value


class ProgressBarPopup(customtkinter.CTkToplevel):
    def __init__(self, desc, total, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Progress Bar")
        self.total = total
        self.start_time = time.time()
        self.count = 0

        desc_label = customtkinter.CTkLabel(self, text=desc)
        desc_label.grid(row=0, column=0)
        self.time_left_label = customtkinter.CTkLabel(self, text="")
        self.time_left_label.grid(row=1, column=0)
        self.progress_bar = customtkinter.CTkProgressBar(self, width=200)
        self.progress_bar.grid(row=2, column=0)

        self.grab_set()  # make other windows not clickable
        self.update_idletasks()
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

    def update_widget(self, n):
        self.count += n
        time_elapsed_s = time.time() - self.start_time
        rate = self.count / time_elapsed_s
        remaining_time_s = (self.total - self.count) / rate
        self.time_left_label.configure(text=f"{round(remaining_time_s, 2)}s remaining")
        self.progress_bar.set(self.count / self.total)
