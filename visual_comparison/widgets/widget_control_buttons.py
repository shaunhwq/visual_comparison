import customtkinter
from ..enums import VCModes


__all__ = ["ControlButtonsWidget"]


class ControlButtonsWidget(customtkinter.CTkFrame):
    def __init__(self, callbacks, *args, **kwargs):
        super().__init__(*args, **kwargs)

        frame_00 = customtkinter.CTkFrame(master=self)
        button_prev = customtkinter.CTkButton(master=frame_00, text="<", command=callbacks["on_prev"], width=30, height=25)
        button_prev.grid(row=1, column=0, padx=5)
        button_method = customtkinter.CTkButton(master=frame_00, text="Method:", command=callbacks["on_select_methods"], width=50, height=25)
        button_method.grid(row=1, column=1, padx=5)
        button_select_specific = customtkinter.CTkButton(master=frame_00, text="Idx:", command=callbacks["on_specify_index"], width=50, height=25)
        button_select_specific.grid(row=1, column=2, padx=5)
        button_next = customtkinter.CTkButton(master=frame_00, text=">", command=callbacks["on_next"], width=30, height=25)
        button_next.grid(row=1, column=3, padx=5)
        frame_00.grid(row=0, column=0, padx=20)

        # For controlling modes
        frame_01 = customtkinter.CTkFrame(master=self)
        self.modes_button = customtkinter.CTkSegmentedButton(master=frame_01)
        self.modes_button.pack()
        frame_01.grid(row=0, column=1, padx=20)

        # For saving and copying files
        frame_02 = customtkinter.CTkFrame(master=self)
        button_save = customtkinter.CTkButton(master=frame_02, width=75, height=25, command=callbacks["on_save_image"], text="Save")
        button_save.grid(row=0, column=0, padx=5)
        button_copy = customtkinter.CTkButton(master=frame_02, width=75, height=25, command=callbacks["on_copy_image"], text="Copy")
        button_copy.grid(row=0, column=1, padx=5)
        frame_02.grid(row=0, column=2, padx=20)

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


