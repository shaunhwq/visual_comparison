import customtkinter
import argparse
from visual_comparison import VisualComparisonApp


if __name__ == "__main__":
    # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_appearance_mode("System")
    # Themes: "blue" (standard), "green", "dark-blue"
    customtkinter.set_default_color_theme("dark-blue")

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, help="Path to root directory", default=None)
    parser.add_argument("--preview_folder", type=str, help="Folder to preview", default=None)
    opt = parser.parse_args()

    app = VisualComparisonApp(root=opt.root, preview_folder=opt.preview_folder)
    app.after(200, app.display)
    app.mainloop()
