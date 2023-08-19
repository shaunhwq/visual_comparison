import os
import PIL.Image
import customtkinter


__all__ = ["IconManager"]


class IconManager:
    def __init__(self, icon_assets_path):
        self.icon_assets_path = icon_assets_path
        assert os.path.isdir(self.icon_assets_path), "Unable to find icon assets"

        self.copy_icon = self.load_ctk_image(os.path.join(icon_assets_path, "copy_icon.png"))
        self.export_icon = self.load_ctk_image(os.path.join(icon_assets_path, "export_icon.png"))
        self.folder_icon = self.load_ctk_image(os.path.join(icon_assets_path, "folder_icon.png"))
        self.restore_icon = self.load_ctk_image(os.path.join(icon_assets_path, "restore_icon.png"))
        self.settings_icon = self.load_ctk_image(os.path.join(icon_assets_path, "settings_icon.png"))

    @staticmethod
    def load_ctk_image(image_path: str) -> customtkinter.CTkImage:
        return customtkinter.CTkImage(PIL.Image.open(image_path))
