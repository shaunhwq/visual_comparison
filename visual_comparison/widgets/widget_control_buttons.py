import customtkinter
from ..enums import VCModes


__all__ = ["ControlButtonsWidget"]


class ControlButtonsWidget(customtkinter.CTkFrame):
    def __init__(self, callbacks, *args, **kwargs):
        super().__init__(*args, **kwargs)

        frame_00 = customtkinter.CTkFrame(master=self)
        button_prev = customtkinter.CTkButton(master=frame_00, text="<", command=callbacks["on_prev_file"], width=30, height=25)
        button_prev.grid(row=0, column=0, padx=(5, 2))
        button_select_specific = customtkinter.CTkButton(master=frame_00, text="File Idx:", command=callbacks["on_specify_index"], width=50, height=25)
        button_select_specific.grid(row=0, column=1, padx=(0, 2))
        button_next = customtkinter.CTkButton(master=frame_00, text=">", command=callbacks["on_next_file"], width=30, height=25)
        button_next.grid(row=0, column=2, padx=(0, 5))

        button_search = customtkinter.CTkButton(master=frame_00, text="Filter:", command=callbacks["on_filter_files"], width=50, height=25)
        button_search.grid(row=0, column=3, padx=5)

        button_prev_method = customtkinter.CTkButton(master=frame_00, text="<", command=callbacks["on_prev_method"], width=30, height=25)
        button_prev_method.grid(row=0, column=4, padx=(5, 2))
        button_method = customtkinter.CTkButton(master=frame_00, text="Method:", command=callbacks["on_select_methods"], width=50, height=25)
        button_method.grid(row=0, column=5, padx=(0, 2))
        button_next_method = customtkinter.CTkButton(master=frame_00, text=">", command=callbacks["on_next_method"], width=30, height=25)
        button_next_method.grid(row=0, column=6, padx=(0, 5))

        frame_00.grid(row=0, column=0, padx=10)

        # For controlling modes
        frame_01 = customtkinter.CTkFrame(master=self)
        self.modes_button = customtkinter.CTkSegmentedButton(master=frame_01)
        self.modes_button.pack()
        frame_01.grid(row=0, column=1, padx=10)

        # For exporting and copying files
        frame_02 = customtkinter.CTkFrame(master=self)
        self.button_export = customtkinter.CTkButton(master=frame_02, width=50, height=25, command=callbacks["on_export"], text="Export")
        self.button_export.grid(row=0, column=0, padx=5)
        self.default_button_color = self.button_export.cget("fg_color")
        button_copy = customtkinter.CTkButton(master=frame_02, width=50, height=25, command=callbacks["on_copy_image"], text="Copy")
        button_copy.grid(row=0, column=1, padx=5)
        button_change_dir = customtkinter.CTkButton(master=frame_02, width=50, height=25, command=callbacks["on_change_dir"], text="Change Dir")
        button_change_dir.grid(row=0, column=2, padx=5)
        button_settings = customtkinter.CTkButton(master=frame_02, width=50, height=25, command=callbacks["on_change_settings"], text="Settings")
        button_settings.grid(row=0, column=3, padx=5)
        frame_02.grid(row=0, column=2, padx=10)

        # For changing to 'Specific' mode
        frame_10 = customtkinter.CTkFrame(master=self)
        self.methods_button = customtkinter.CTkSegmentedButton(master=frame_10)  # Populate later
        self.methods_button.pack()
        self.method_frame = frame_10

    def show_method_button(self, show=True):
        if show:
            self.method_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        else:
            self.method_frame.grid_remove()

    def populate_methods_button(self, methods, callback):
        self.methods_button.configure(values=methods, command=lambda value: callback(VCModes.Specific, value))

    def set_method(self, method):
        self.methods_button.set(method)

    def populate_mode_button(self, modes, callback):
        mode_names = [e.name for e in modes]
        ref_dict = {e.name: e for e in modes}
        self.modes_button.configure(values=mode_names, command=lambda mode_str: callback(ref_dict[mode_str]))

    def set_mode(self, mode_enum):
        self.modes_button.set(mode_enum.name)

    def toggle_export_button(self):
        text = self.button_export.cget("text")

        if text == "Export":
            text, fg_color = "Stop", "red"
        elif text == "Stop":
            text, fg_color = "Export", self.default_button_color
        else:
            raise NotImplementedError(f"Unknown export button text: {text}")

        self.button_export.configure(text=text, fg_color=fg_color)
