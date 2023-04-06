import customtkinter
import widget_scrollviewer
import enum
import os
import glob


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
        self.scroll_viewer = widget_scrollviewer.ScrollViewer(os.path.join(root, "source"), files, self.on_specify_index, master=self)
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
        self.master.bind("<Left>", lambda event: self.on_prev())
        self.master.bind("d", lambda event: self.on_next())
        self.master.bind("<Right>", lambda event: self.on_next())

        for i in range(10):
            self.master.unbind(str(i))
        for i in range(min(len(self.curr_methods), 9)):
            # Bind number keys
            self.master.bind(str(i + 1), lambda event: self.on_change_mode("Specific", self.curr_methods[int(event.keysym) - 1]))
            # Bind keypad
            self.master.bind(f"<KP_{i + 1}>", lambda event: self.on_change_mode("Specific", self.curr_methods[int(event.keysym.split("_")[1]) - 1]))


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