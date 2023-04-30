import customtkinter


__all__ = ["VideoControlsWidget"]


class VideoControlsWidget(customtkinter.CTkFrame):
    def __init__(self, callbacks, *args, **kwargs):
        super().__init__(*args, **kwargs)
        height = 20
        button_restart = customtkinter.CTkButton(master=self, width=28, height=height, text="⏮", command=lambda: callbacks["on_set_video_position"](0))
        button_restart.grid(row=0, column=0, padx=2)
        button_minus_10 = customtkinter.CTkButton(master=self, width=28, height=height, text="-10", command=lambda: callbacks["on_set_video_position"](-10, relative=True))
        button_minus_10.grid(row=0, column=1, padx=2)
        button_minus_1 = customtkinter.CTkButton(master=self, width=28, height=height, text="-1", command=lambda: callbacks["on_set_video_position"](-1, relative=True))
        button_minus_1.grid(row=0, column=2, padx=2)
        self.pause_button = customtkinter.CTkButton(master=self, width=28, height=height, text="⏸", command=lambda: callbacks["on_pause"]())
        self.pause_button.grid(row=0, column=3, padx=2)
        button_plus_1 = customtkinter.CTkButton(master=self, width=28, height=height, text="+1", command=lambda: callbacks["on_set_video_position"](1, relative=True))
        button_plus_1.grid(row=0, column=4, padx=2)
        button_plus_10 = customtkinter.CTkButton(master=self, width=28, height=height, text="+10", command=lambda: callbacks["on_set_video_position"](10, relative=True))
        button_plus_10.grid(row=0, column=5, padx=2)
        self.video_slider = customtkinter.CTkSlider(master=self, from_=0, to=100, command=lambda value: callbacks["on_set_video_position"](value, slider=True))
        self.video_slider.grid(row=0, column=6, padx=2)
        self.button_specify_frame_no = customtkinter.CTkButton(master=self, width=75, height=height, text="Frame No:", command=lambda: callbacks["on_specify_frame_no"]())
        self.button_specify_frame_no.grid(row=0, column=7, padx=2)
        self.label_fps = customtkinter.CTkLabel(master=self, width=50, height=height)
        self.label_fps.grid(row=0, column=8, padx=2)

    def pause(self, pause=True):
        button_text = "⏵" if pause else "⏸"
        self.pause_button.configure(text=button_text)

    def update_widget(self, current_frame_number, total_frame_number, video_fps):
        slider_position = current_frame_number / total_frame_number * 100
        self.video_slider.set(slider_position)
        self.button_specify_frame_no.configure(text=f"{current_frame_number} / {int(total_frame_number)}")
        self.label_fps.configure(text=f"{round(video_fps, 2)}fps")
