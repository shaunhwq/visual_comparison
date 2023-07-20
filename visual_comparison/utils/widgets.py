import customtkinter


__all__ = ["shift_widget_to_root_center", "set_appearance_mode_and_theme"]


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
