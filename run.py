import customtkinter
import argparse
from visual_comparison import VisualComparisonApp


if __name__ == "__main__":
    # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_appearance_mode("System")
    # Themes: "blue" (standard), "green", "dark-blue"
    customtkinter.set_default_color_theme("dark-blue")

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, help="Path to root directory", required=True)
    parser.add_argument("--source_folder", type=str, help="Name of source folder", default="source")
    opt = parser.parse_args()

    app = VisualComparisonApp(root=opt.root, src_folder_name=opt.source_folder)
    app.after(200, app.display)
    app.mainloop()
