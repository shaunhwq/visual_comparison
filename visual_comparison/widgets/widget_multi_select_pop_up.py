import customtkinter


__all__ = ["MultiSelectPopUpWidget"]


class MultiSelectPopUpWidget(customtkinter.CTkToplevel):
    def __init__(self, all_options, current_options, app_callback):
        """
        :param all_options: All possible options
        :param current_options: Currently selected options
        :param app_callback: Callback called when confirm button is pressed. Pass a list of strings.
        """
        super().__init__()
        self.app_callback = app_callback

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
