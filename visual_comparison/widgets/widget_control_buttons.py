import customtkinter
from ..enums import VCModes
from .. import utils
from ..managers import IconManager


__all__ = ["ControlButtonsWidget"]


class ControlButtonsWidget(customtkinter.CTkFrame):
    def __init__(self, icon_manager: IconManager, callbacks, ctk_corner_radius, *args, **kwargs):
        super().__init__(*args, **kwargs)

        frame_00 = customtkinter.CTkFrame(master=self)
        button_prev = customtkinter.CTkButton(master=frame_00, text="<", command=callbacks["on_prev_file"], width=30, height=29, corner_radius=ctk_corner_radius)
        button_prev.grid(row=0, column=0, padx=(5, 2))
        button_search = customtkinter.CTkButton(master=frame_00, width=25, height=25, command=callbacks["on_search"], text="", image=icon_manager.search_icon, corner_radius=ctk_corner_radius)
        utils.create_tool_tip(button_search, "Search")
        button_search.grid(row=0, column=1, padx=(0, 2))
        button_search_grid = customtkinter.CTkButton(master=frame_00, width=25, height=25, command=callbacks["on_search_grid"], text="", image=icon_manager.search_grid_icon, corner_radius=ctk_corner_radius)
        utils.create_tool_tip(button_search_grid, "Search Grid")
        button_search_grid.grid(row=0, column=2, padx=(0, 2))
        button_next = customtkinter.CTkButton(master=frame_00, text=">", command=callbacks["on_next_file"], width=30, height=29, corner_radius=ctk_corner_radius)
        button_next.grid(row=0, column=3, padx=(0, 5))

        button_filter = customtkinter.CTkButton(master=frame_00, width=25, height=25, command=callbacks["on_filter_files"], text="", image=icon_manager.filter_icon, corner_radius=ctk_corner_radius)
        utils.create_tool_tip(button_filter, "Filter")
        button_filter.grid(row=0, column=4, padx=5)

        button_prev_method = customtkinter.CTkButton(master=frame_00, text="<", command=callbacks["on_prev_method"], width=30, height=29, corner_radius=ctk_corner_radius)
        button_prev_method.grid(row=0, column=5, padx=(5, 2))
        button_method = customtkinter.CTkButton(master=frame_00, text="Method:", command=callbacks["on_select_methods"], width=50, height=29, corner_radius=ctk_corner_radius)
        button_method.grid(row=0, column=6, padx=(0, 2))
        button_next_method = customtkinter.CTkButton(master=frame_00, text=">", command=callbacks["on_next_method"], width=30, height=29, corner_radius=ctk_corner_radius)
        button_next_method.grid(row=0, column=7, padx=(0, 5))

        frame_00.grid(row=0, column=0, padx=10)

        # For controlling modes
        frame_01 = customtkinter.CTkFrame(master=self)
        self.modes_button = customtkinter.CTkSegmentedButton(master=frame_01, corner_radius=ctk_corner_radius)
        self.modes_button.pack()
        frame_01.grid(row=0, column=1, padx=10)

        # For exporting and copying files
        frame_02 = customtkinter.CTkFrame(master=self)
        self.button_export = customtkinter.CTkButton(master=frame_02, width=25, height=25, command=callbacks["on_export"], text="", image=icon_manager.export_icon, corner_radius=ctk_corner_radius)
        utils.create_tool_tip(self.button_export, "Export")
        self.button_export.grid(row=0, column=0, padx=5)
        self.default_button_color = self.button_export.cget("fg_color")
        button_copy = customtkinter.CTkButton(master=frame_02, width=25, height=25, command=callbacks["on_copy_image"], text="", image=icon_manager.copy_icon, corner_radius=ctk_corner_radius)
        utils.create_tool_tip(button_copy, "Copy")
        button_copy.grid(row=0, column=1, padx=5)
        button_change_dir = customtkinter.CTkButton(master=frame_02, width=25, height=25, command=callbacks["on_change_dir"], text="", image=icon_manager.folder_icon, corner_radius=ctk_corner_radius)
        utils.create_tool_tip(button_change_dir, "Change Directory")
        button_change_dir.grid(row=0, column=2, padx=5)
        button_settings = customtkinter.CTkButton(master=frame_02, width=25, height=25, command=callbacks["on_change_settings"], text="", image=icon_manager.settings_icon, corner_radius=ctk_corner_radius)
        utils.create_tool_tip(button_settings, "Settings")
        button_settings.grid(row=0, column=3, padx=5)
        frame_02.grid(row=0, column=2, padx=10)

        # For changing to 'Specific' mode
        frame_10 = customtkinter.CTkFrame(master=self)
        self.methods_button = customtkinter.CTkSegmentedButton(master=frame_10, corner_radius=ctk_corner_radius)  # Populate later
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
        color = self.button_export.cget("fg_color")
        new_color = "red" if self.default_button_color == color else self.default_button_color
        self.button_export.configure(fg_color=new_color)
