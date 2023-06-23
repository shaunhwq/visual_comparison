import time
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
        playback_speeds = ["1x", "1.5x", "2x", "3x", "4x", "Max"]
        playback_button = customtkinter.CTkOptionMenu(self, width=50, height=height, values=playback_speeds, command=callbacks["on_change_playback_rate"])
        playback_button.grid(row=0, column=8, padx=2)
        self.label_fps = customtkinter.CTkLabel(master=self, width=180, height=height)
        self.label_fps.grid(row=0, column=9, padx=2)

        # To calculate playback fps
        self.last_called = [time.time()]

    def pause(self, pause=True):
        button_text = "⏵" if pause else "⏸"
        self.pause_button.configure(text=button_text)
        self.last_called = []

    def get_playback_fps(self):
        if len(self.last_called) == 0:
            return 60.0
        time_diff_s = self.last_called[-1] - self.last_called[0]
        playback_fps = -1 if time_diff_s == 0 else len(self.last_called) / time_diff_s
        return playback_fps

    def update_widget(self, current_frame_number, total_frame_number, video_fps):
        slider_position = current_frame_number / total_frame_number * 100
        self.video_slider.set(slider_position)
        self.button_specify_frame_no.configure(text=f"{current_frame_number} / {int(total_frame_number)}")

        self.last_called.append(time.time())
        if len(self.last_called) > 15:
            self.last_called.pop(0)
        playback_fps = self.get_playback_fps()
        self.label_fps.configure(text=f"Vid: {round(video_fps, 1)}fps | Play: {round(playback_fps, 1)}fps")
