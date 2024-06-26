import customtkinter
import tkinter
import tkinter.ttk as ttk


__all__ = [
    "shift_widget_to_root_center",
    "set_appearance_mode_and_theme",
    "create_tool_tip",
    "is_window_in_background",
    "set_tkinter_widgets_appearance_mode",
]


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
        self.tip_window = tw = customtkinter.CTkToplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = customtkinter.CTkLabel(tw, text=self.text)
        label.pack(padx=5)

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


def create_tool_tip(widget, text):
    tool_tip = ToolTip(widget)
    widget.bind('<Enter>', lambda event: tool_tip.showtip(text))
    widget.bind('<Leave>', lambda event: tool_tip.hidetip())


def is_window_in_background(window):
    try:
        return window.focus_displayof() is None
    except KeyError as e:
        return True


def set_tkinter_widgets_appearance_mode(ctk_root) -> None:
    """
    Sets appearance mode of tkinter objects to match the color scheme of customtkinter objects
    :param ctk_root: customtkinter.CTk() object
    """
    bg_color = ctk_root._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"])
    text_color = ctk_root._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkLabel"]["text_color"])
    selected_color = ctk_root._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

    # bg color is light and selected color is either blue or dark-blue
    if bg_color in ["gray86", "gray90"] and selected_color in ["#3a7ebf", "#3B8ED0"]:
        selected_color = "royal blue"

    tree_style = ttk.Style()
    tree_style.theme_use('default')
    tree_style.configure("Treeview", background=bg_color, foreground=text_color, fieldbackground=bg_color, borderwidth=0.5, font=('Calibri', 10, 'bold'))
    tree_style.map('Treeview', background=[('selected', bg_color)], foreground=[('selected', selected_color)])
    tree_style.configure("Treeview.Heading", background=bg_color, foreground=text_color, fieldbackground=bg_color, borderwidth=0.5)
    tree_style.map('Treeview.Heading', background=[('selected', bg_color)], foreground=[('selected', selected_color)])
