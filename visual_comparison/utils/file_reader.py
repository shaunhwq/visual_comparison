import os

import cv2
import numpy as np


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
    def __init__(self, video_path, metadata):
        self.cap = cv2.VideoCapture(video_path)
        self.metadata = metadata

        codec_name, color_space = metadata.get("codec_name", None), metadata.get("color_space", None)
        self.is_h264_bt709 = color_space == "bt709" and codec_name == "h264"

    @staticmethod
    def rectify_h264_bt709_video(bgr_image: np.array) -> np.array:
        """
        Rectifies BT709 h264 videos (Issue with OpenCV)
        """
        out_img = np.zeros_like(bgr_image, dtype=np.float32)
        out_img[:, :, 2] = 1.086275 * bgr_image[:, :, 2] - 0.073168 * bgr_image[:, :, 1] - 0.013231 * bgr_image[:, :, 0]
        out_img[:, :, 1] = 0.096685 * bgr_image[:, :, 2] + 0.844783 * bgr_image[:, :, 1] + 0.058408 * bgr_image[:, :, 0]
        out_img[:, :, 0] = -0.013428 * bgr_image[:, :, 2] - 0.027936 * bgr_image[:, :, 1] + 1.04124 * bgr_image[:, :, 0]
        return np.clip(out_img, 0, 255).astype(np.uint8)

    def __getattr__(self, item):
        def method(*args, **kwargs):
            return getattr(self.cap, item)(*args, **kwargs)
        return method

    def retrieve(self, *args, **kwargs):
        ret, image = self.cap.retrieve(*args, **kwargs)
        if self.is_h264_bt709:
            print("[Retrieve] Rectifying image...")
            image = self.rectify_h264_bt709_video(image)

        return ret, image

    def read(self, *args, **kwargs):
        ret, image = self.cap.read(*args, **kwargs)

        if not ret:
            return ret, image
        if image is None:
            return ret, image
        if not self.is_h264_bt709:
            return ret, image

        return ret, self.rectify_h264_bt709_video(image)
