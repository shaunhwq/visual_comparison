import os

import cv2
import numpy as np

from ..utils import image_conversions


__all__ = ["read_media_file", "ImageCapture", "VideoCapture"]


def read_media_file(file_path, metadata):
    ext = os.path.splitext(os.path.basename(file_path))[-1].lower()
    if ext in {".png", ".jpg", ".tif"}:
        capture_obj = ImageCapture(file_path, metadata)
    elif ext in {".mp4", ".avi"}:
        capture_obj = VideoCapture(file_path, metadata)
    else:
        raise NotImplementedError(f"Unsupported ext for loading image thumbnail: {ext}")
    return capture_obj


class ImageCapture:
    """
    TODO: Handle HDR Reading too later?
    """
    def __init__(self, image_path, metadata):
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        max_img_val = np.iinfo(image.dtype).max
        if max_img_val != 255:
            image = (image.astype(np.float32) / max_img_val * 255.0).clip(0, 255).astype(np.uint8)

        self.image = image
        self.metadata = metadata

    def read(self):
        if self.image is None:
            return False, None

        return True, self.image.copy()

    def release(self):
        pass


class VideoCapture:
    def __init__(self, video_path, metadata=None):
        self.cap = cv2.VideoCapture(video_path)
        self.metadata = metadata

    def __getattr__(self, item):
        def method(*args, **kwargs):
            return getattr(self.cap, item)(*args, **kwargs)
        return method

    def is_h264_bt709(self):
        if self.metadata is None:
            return False

        codec_name, color_space = self.metadata.get("codec_name", None), self.metadata.get("color_space", None)
        return color_space == "bt709" and codec_name == "h264"

    def retrieve(self, *args, **kwargs):
        ret, image = self.cap.retrieve(*args, **kwargs)

        if not ret:
            return ret, image
        if image is None:
            return ret, image
        if self.metadata is None:
            return ret, image
        if not self.is_h264_bt709():
            return ret, image

        return ret, image_conversions.rectify_h264_bt709_video(image)

    def read(self, *args, **kwargs):
        ret, image = self.cap.read(*args, **kwargs)

        if not ret:
            return ret, image
        if image is None:
            return ret, image
        if self.metadata is None:
            return ret, image
        if not self.is_h264_bt709():
            return ret, image

        return ret, image_conversions.rectify_h264_bt709_video(image)
