from typing import Tuple, Dict, Any

import customtkinter

from visual_comparison.utils import shift_widget_to_root_center
from ..configurations import read_config, write_config, parse_config
from .widget_pop_ups import MessageBoxPopup
from ..managers import IconManager


__all__ = ["SettingsPopupWidget"]


class SettingsPopupWidget(customtkinter.CTkToplevel):
    def __init__(self, configuration_path, configuration_info, icon_manager: IconManager, ctk_corner_radius, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Settings")

        self.configuration_path = configuration_path
        self.configuration_info = configuration_info
        self.ctk_corner_radius = ctk_corner_radius

        label_width = 80
        input_obj_width = 200
        height = 25

        tabview = customtkinter.CTkTabview(self, height=100, width=300, corner_radius=ctk_corner_radius)
        tabview.grid(row=0, column=0, padx=20, pady=(5, 20), sticky="nsew")
        tabview.columnconfigure(0, weight=1)

        self.ctk_objects = {}
        current_configuration = read_config(configuration_path)

        # Automatically creates the objects in the Settings popup
        for section_name in current_configuration.sections():
            # Create a new tab for each section of the configuration
            tabview.add(section_name)
            tabview.tab(section_name).grid_columnconfigure(0, weight=1)
            tab = tabview.tab(section_name)

            # Populate the tab with CTK Widgets, depending on the configuration_options
            for i, key in enumerate(current_configuration.options(section_name)):
                pady = 5 if i == 0 else (0, 5)
                label = customtkinter.CTkLabel(master=tab, width=label_width, height=height, text=key)
                label.grid(row=i, column=0, padx=20, pady=pady)

                desired_ctk_obj = configuration_info[section_name][key]["obj"]
                if desired_ctk_obj == "options":
                    ctk_obj = customtkinter.CTkOptionMenu(master=tab, width=input_obj_width, height=height, values=configuration_info[section_name][key]["values"], corner_radius=ctk_corner_radius)
                    ctk_obj.set(current_configuration[section_name][key])
                    ctk_obj.grid(row=i, column=1, padx=(0, 20), pady=pady)
                elif desired_ctk_obj == "entry":
                    ctk_obj = customtkinter.CTkEntry(master=tab, width=input_obj_width, height=height, corner_radius=ctk_corner_radius)
                    ctk_obj.insert(0, current_configuration[section_name][key])
                    ctk_obj.grid(row=i, column=1, padx=(0, 20), pady=pady)
                else:
                    raise NotImplementedError(f"Check configuration_options. Unknown obj: '{desired_ctk_obj}'")

                # Set width and height to same dim to make a square button
                reset_default_button = customtkinter.CTkButton(
                    master=tab,
                    width=height,
                    height=height,
                    image=icon_manager.restore_icon,
                    fg_color="gray", text="",
                    command=lambda params=(section_name, key): self.on_restore_to_default(*params),
                    corner_radius=ctk_corner_radius,
                )
                reset_default_button.grid(row=i, column=2, padx=(0, 20), pady=pady)

                # Write to storage for later. Use this format because it is easier
                self.ctk_objects[f"{section_name}_{key}"] = ctk_obj

        # Confirmation and Cancel Buttons
        button_frame = customtkinter.CTkFrame(self, height=height, width=100)
        cancel_button = customtkinter.CTkButton(master=button_frame, height=25, width=50, text="Cancel", command=self.destroy, corner_radius=ctk_corner_radius)
        cancel_button.grid(row=0, column=0, padx=20)
        all_defaults_button = customtkinter.CTkButton(master=button_frame, height=25, width=50, text="Default (all)", command=self.on_restore_all_to_defaults, corner_radius=ctk_corner_radius)
        all_defaults_button.grid(row=0, column=1, padx=(0, 20))
        confirm_button = customtkinter.CTkButton(master=button_frame, height=25, width=50, text="Confirm", command=self.on_confirm, corner_radius=ctk_corner_radius)
        confirm_button.grid(row=0, column=2, padx=(0, 20))
        button_frame.grid(row=1, column=0, pady=(0, 20))

        self.return_value = None
        self.cancelled = True

        self.update_idletasks()
        self.grab_set()  # make other windows not clickable
        shift_widget_to_root_center(parent_widget=self.master, child_widget=self)

    def on_restore_all_to_defaults(self):
        for section in self.configuration_info.keys():
            for key in self.configuration_info[section].keys():
                self.on_restore_to_default(section, key)

        self.grab_release()
        msg_popup = MessageBoxPopup(f"Reset all settings to defaults", self.ctk_corner_radius)
        msg_popup.wait()
        self.grab_set()

    def on_restore_to_default(self, section, key):
        default_value = str(self.configuration_info[section][key]["default"])
        ctk_object = self.ctk_objects[f"{section}_{key}"]

        if isinstance(ctk_object, customtkinter.CTkOptionMenu):
            ctk_object.set(default_value)
        elif isinstance(ctk_object, customtkinter.CTkEntry):
            ctk_object.delete(0, len(ctk_object.get()))
            ctk_object.insert(0, default_value)
        else:
            raise NotImplementedError(f"Unable to reset to default for object type: '{ctk_object}'")

    def on_confirm(self) -> None:
        """
        Read configuration, writes to .ini file, and parses it (so it is immediately usable)
        :return: None
        """
        # Update configuration and write to file
        config_parser = read_config(self.configuration_path)
        for section in config_parser.sections():
            for key in config_parser[section]:
                config_parser[section][key] = self.ctk_objects[f"{section}_{key}"].get()

        try:
            parsed_config = parse_config(config_parser)
        except Exception as e:
            self.grab_release()
            msg_popup = MessageBoxPopup(f"ValueError occurred when parsing: {e}", self.ctk_corner_radius)
            msg_popup.wait()
            self.grab_set()
            return

        write_config(self.configuration_path, config_parser)

        self.cancelled = False
        self.return_value = parsed_config

        self.destroy()

    def get_input(self) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
        """
        Waits for user until settings window is closed either by cancelling or confirming.
        :return: bool, dict. Dictionary is a parsed version of .ini file.
        """
        self.master.wait_window(self)
        return self.cancelled, self.return_value
