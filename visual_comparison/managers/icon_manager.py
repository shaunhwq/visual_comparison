import os
import PIL.Image
import customtkinter


__all__ = ["IconManager"]


class IconManager:
    def __init__(self, icon_assets_path):
        self.icon_assets_path = icon_assets_path

        self.copy_icon = self.load_ctk_image("copy_icon.png")
        self.export_icon = self.load_ctk_image("export_icon.png")
        self.folder_icon = self.load_ctk_image("folder_icon.png")
        self.restore_icon = self.load_ctk_image("restore_icon.png")
        self.settings_icon = self.load_ctk_image("settings_icon.png")
        self.filter_icon = self.load_ctk_image("filter_icon.png")
        self.search_icon = self.load_ctk_image("search_icon.png")

    def load_ctk_image(self, image_name: str) -> customtkinter.CTkImage:
        image_path = os.path.join(self.icon_assets_path, image_name)
        assert os.path.isfile(image_path), "Unable to find icon assets"

        return customtkinter.CTkImage(PIL.Image.open(image_path))
