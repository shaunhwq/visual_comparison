import time


__all__ = ["FastLoadChecker"]


class FastLoadChecker:
    def __init__(self):
        self.prev_called_time = 0
        self.curr_called_time = 1000

    def update(self):
        """
        Call this when button is pressed
        """
        self.prev_called_time = self.curr_called_time
        self.curr_called_time = time.time()

    def check(self, threshold_ms) -> bool:
        """
        Checks if it requires fast loading
        :return:
        """
        time_between_calls_ms = (self.curr_called_time - self.prev_called_time) * 1000
        time_since_last_press = (time.time() - self.curr_called_time) * 1000
        return time_between_calls_ms < threshold_ms and time_since_last_press < threshold_ms
