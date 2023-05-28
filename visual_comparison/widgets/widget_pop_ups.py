from typing import List, Any

import tkinter.ttk as ttk
import tkinter
import customtkinter

from ..utils import validate_float_str, shift_widget_to_root_center


__all__ = ["MultiSelectPopUpWidget", "FilterRangePopup", "DataSelectionPopup"]


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

        # Prevent user interaction
        self.grab_set()

        self.mainloop()
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

        self.update_idletasks()
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

    def on_ok_pressed(self, tab):
        if tab == "Range":
            l_ret, lower_val = validate_float_str(self.lower_text_box.get())
            u_ret, upper_val = validate_float_str(self.upper_text_box.get())
            if not (l_ret and u_ret):
                self.error_label.configure(text="Error parsing values")
                return
            if lower_val > upper_val:
                self.error_label.configure(text="Lower > Upper")
                return
            selected_idxs = [idx for idx, value in enumerate(self.values) if lower_val <= float(value) <= upper_val]
        elif tab == "Equals":
            ret, equals_val = validate_float_str(self.equals_text_box.get())
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

        if data_type is int or data_type is float:
            popup = FilterRangePopup(f"Filtering {column}:", data_to_filter)
            is_cancelled, idxs = popup.get_input()
        elif data_type is str:
            popup = FilterTextPopup(f"Column: {column}", data_to_filter)
            is_cancelled, idxs = popup.get_input()
        else:
            raise NotImplementedError(f"Filtering option for data type {data_type} is not implemented")

        if is_cancelled:
            return

        keep_idxs = set(idxs)
        idx_to_remove = [c for idx, c in enumerate(self.tree.get_children()) if idx not in keep_idxs]
        self.tree_remove(idx_to_remove)
        self.refresh_title()

    def sort_rows(self, col_idx):
        self.col_sort_reverse[col_idx] = not self.col_sort_reverse[col_idx]
        rows = [self.child_values(child) for child in self.tree.get_children()]
        rows.sort(key=lambda row: row[col_idx], reverse=self.col_sort_reverse[col_idx])
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
