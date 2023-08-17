import PIL.Image
import customtkinter
import tkinter


__all__ = ["shift_widget_to_root_center", "set_appearance_mode_and_theme", "load_ctk_image", "create_tool_tip"]


def shift_widget_to_root_center(parent_widget, child_widget):
    # Make sure created widget is fully created
    parent_widget.update_idletasks()

    # Get Root Center
    parent_cx = parent_widget.winfo_x() + parent_widget.winfo_width() // 2
    parent_cy = parent_widget.winfo_y() + parent_widget.winfo_height() // 2

    # Get right offset for widget
    window_offset_x = parent_cx - child_widget.winfo_width() // 2
    window_offset_y = parent_cy - child_widget.winfo_height() // 2

    # Update position and refresh
    child_widget.geometry(f"+{window_offset_x}+{window_offset_y}")
    parent_widget.update_idletasks()


def set_appearance_mode_and_theme(mode: str, theme: str) -> None:
    """
    Sets customtkinter's mode and theme.
    :param mode: E.g. system, dark, light modes. Changes background to follow system or dark/light
    :param theme: Color of UI elements
    :return: None
    """
    customtkinter.set_appearance_mode(mode)
    customtkinter.set_default_color_theme(theme)


def load_ctk_image(image_path: str) -> customtkinter.CTkImage:
    "visual_comparison/widgets/assets/copy_icon.png"
    return customtkinter.CTkImage(PIL.Image.open(image_path))


class ToolTip(object):
    # https://stackoverflow.com/questions/20399243/display-message-when-hovering-over-something-with-mouse-cursor-in-python
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tip_window or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx()
        y = y + cy + self.widget.winfo_rooty()
        self.tip_window = tw = tkinter.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tkinter.Label(tw, text=self.text, justify=tkinter.LEFT, background="#ffffe0", relief=tkinter.SOLID, borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


def create_tool_tip(widget, text):
    tool_tip = ToolTip(widget)
    widget.bind('<Enter>', lambda event: tool_tip.showtip(text))
    widget.bind('<Leave>', lambda event: tool_tip.hidetip())
