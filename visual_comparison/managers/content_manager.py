import os

import cv2

from ..utils import file_utils


__all__ = ["ContentManager"]


class ImageCapture:
    """
    TODO: Handle HDR Reading too later?
    """
    def __init__(self, image_path):
        self.image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    def read(self):
        if self.image is None:
            return False, None
        return True, self.image.copy()


class ContentManager:
    def __init__(self, root, src_folder_name):
        self.methods = file_utils.get_folders(root, src_folder_name)
        self.files = file_utils.get_filenames(root, self.methods)

        self.content_loaders = None
        self.video_indices = []

        self.current_index = 0
        self.current_methods = list(self.methods)

    def load_files(self, paths):
        self.content_loaders = []
        self.video_indices = []
        for file_idx, file in enumerate(paths):
            extension = os.path.splitext(file)[-1].lower()
            if extension in {".jpg", ".png", ".hdr"}:
                self.content_loaders.append(ImageCapture(file))
            elif extension in {".mp4"}:
                self.content_loaders.append(cv2.VideoCapture(file))
                self.video_indices.append(file_idx)
            else:
                raise NotImplementedError(f"Ext not supported: {extension} for file {file}")

    def has_video(self):
        return len(self.video_indices) != 0

    def set_video_position(self, value):
        if not self.has_video():
            return

        first_cap = self.content_loaders[self.video_indices[0]]
        video_position = int(value / 100 * first_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        for video_idx in self.video_indices:
            cap = self.content_loaders[video_idx]
            cap.set(cv2.CAP_PROP_POS_FRAMES, video_position)

    def get_video_position(self):
        if not self.has_video():
            return 0

        cap = self.content_loaders[self.video_indices[0]]
        video_position = cap.get(cv2.CAP_PROP_POS_FRAMES)
        video_length = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        return video_position / video_length * 100

    def read_frames(self):
        outputs = [cap.read() for cap in self.content_loaders]
        rets = [out[0] for out in outputs]
        frames = [out[1] for out in outputs]
        return all(rets), frames
