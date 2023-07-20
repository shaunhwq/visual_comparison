import argparse

from visual_comparison import VisualComparisonApp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, help="Path to root directory", default=None)
    parser.add_argument("--preview_folder", type=str, help="Folder to preview", default=None)
    parser.add_argument("--config_path", type=str, help="Path to configuration file", default="visual_comparison/config.ini")
    opt = parser.parse_args()

    app = VisualComparisonApp(root=opt.root, preview_folder=opt.preview_folder, config_path=opt.config_path)
    app.after(200, app.display)
    app.mainloop()
